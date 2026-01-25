"""Regime Parameter Optimization Thread - v2.0 (Optuna TPE Only).

Fast TPE-based optimization using RegimeOptimizer with 5-component RegimeScore.
Fully compatible with JSON v2 format.

Features:
- Optuna TPE-based optimization (10-100x faster than grid search)
- 5-component RegimeScore (Separability, Coherence, Fidelity, Boundary, Coverage)
- JSON v2 format support with intelligent parameter mapping
- Progress reporting with ETA
- Result ranking and storage

JSON v2 Parameter Mapping:
    Indicators:
        STRENGTH_ADX_period -> adx_period
        TREND_FILTER_period -> sma_slow_period
        MOMENTUM_RSI_period -> rsi_period
        VOLATILITY_ATR_period -> (used as bb_period fallback)

    Thresholds (from regimes):
        Multiple ADX thresholds -> adx_threshold (avg)
        Multiple RSI thresholds -> rsi_sideways_low/high (avg)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal

from src.core import RegimeOptimizer, RegimeOptimizationConfig, RegimeResultsManager

logger = logging.getLogger(__name__)


class RegimeOptimizationThread(QThread):
    """Background thread for Optuna TPE regime optimization.

    Signals:
        progress: (current, total, message)
        result_ready: (result_dict) - emitted for each trial
        finished_with_results: (results_list) - emitted at end
        error: (error_message)
    """

    progress = pyqtSignal(int, int, str)
    result_ready = pyqtSignal(dict)
    finished_with_results = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(
        self,
        df: pd.DataFrame,
        config_template_path: str,
        param_grid: Dict[str, List[Any]],
        scope: str = "entry",
        max_trials: int = 150
    ):
        """Initialize regime optimization thread.

        Args:
            df: OHLCV DataFrame for backtesting
            config_template_path: Path to base JSON regime config (v2 format)
            param_grid: Dict mapping parameter paths to value lists (from JSON v2)
                Example: {
                    "STRENGTH_ADX_period": [10, 14, 20],
                    "BULL_adx_min": [20, 25, 30]
                }
            scope: Regime scope ("entry", "exit", "in_trade")
            max_trials: Maximum number of optimization trials
        """
        super().__init__()
        self.df = df.copy()
        self.config_template_path = config_template_path
        self.param_grid = param_grid
        self.scope = scope
        self.max_trials = max_trials
        self._stop_requested = False

        # Calculate total combinations (for progress bar)
        self.total_combinations = 1
        for values in param_grid.values():
            self.total_combinations *= len(values)

    def request_stop(self):
        """Request graceful stop of optimization."""
        self._stop_requested = True
        logger.info("Regime optimization stop requested")

    def run(self):
        """Execute Optuna TPE regime optimization."""
        try:
            total_start = time.perf_counter()
            logger.info(
                f"Starting Optuna regime optimization: max_trials={min(self.total_combinations, self.max_trials)}, "
                f"scope={self.scope}"
            )

            # Import required types
            from src.core.regime_optimizer import (
                AllParamRanges, ADXParamRanges, SMAParamRanges,
                RSIParamRanges, BBParamRanges, ParamRange, OptimizationConfig
            )

            # Convert param_grid to structured param_ranges
            ranges_dict = self._convert_param_grid_to_ranges_v2()

            # Build AllParamRanges with intelligent defaults for missing params
            param_ranges = self._build_param_ranges_with_defaults(
                ranges_dict, ADXParamRanges, SMAParamRanges, RSIParamRanges, BBParamRanges, ParamRange
            )

            # Create Optuna config
            config = OptimizationConfig(
                max_trials=min(self.total_combinations, self.max_trials),
                n_jobs=1,  # Single-threaded for Qt compatibility
            )

            # Create optimizer
            optimizer = RegimeOptimizer(
                data=self.df.copy(),
                param_ranges=param_ranges,
                config=config
            )

            # Create results manager
            results_manager = RegimeResultsManager()

            # Register progress callback
            def on_trial_complete(study, trial):
                current = len(study.trials)
                total = config.max_trials
                best_score = study.best_value if study.best_trial else 0

                # Emit progress every 5 trials to reduce UI overhead
                if current % 5 == 0 or current == total or current <= 3:
                    self.progress.emit(
                        current,
                        total,
                        f"Trial {current}/{total} | Best: {best_score:.1f}"
                    )

                return self._stop_requested  # Return True to stop optimization

            # Run optimization
            optimization_results = optimizer.optimize(callbacks=[on_trial_complete])

            # Add all results to RegimeResultsManager
            for result in optimization_results:
                results_manager.add_result(
                    score=result.score,
                    params=result.params.model_dump(),
                    metrics=result.metrics.model_dump(),
                    timestamp=result.timestamp.isoformat()
                )

            # Rank results
            results_manager.rank_results()

            # Convert to UI-compatible format
            results = []
            for regime_result in results_manager.results:
                # Ensure params and metrics are dicts (not Pydantic models)
                params_dict = regime_result.params if isinstance(regime_result.params, dict) else {}
                metrics_dict = regime_result.metrics if isinstance(regime_result.metrics, dict) else {}

                ui_result = {
                    'score': int(regime_result.score),
                    'params': params_dict,
                    'metrics': metrics_dict,
                    'timestamp': datetime.fromisoformat(regime_result.timestamp),
                    'rank': regime_result.rank,
                    'trial_number': regime_result.rank,  # Use rank as trial number
                    'config': None,  # Not needed for Optuna results
                    'regime_history': None,
                }
                results.append(ui_result)

                # NOTE: Don't emit individual results here - causes 150x table rebuilds!
                # Progress updates come from on_trial_complete callback during optimization
                # Final results are emitted via finished_with_results below

            total_elapsed = time.perf_counter() - total_start
            logger.info(
                f"Regime optimization complete: {len(results)} results in {total_elapsed:.1f}s "
                f"({total_elapsed/len(results):.2f}s per trial)"
            )

            # Emit all results
            self.finished_with_results.emit(results)

        except Exception as e:
            error_msg = f"Regime optimization failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)

    def _convert_param_grid_to_ranges_v2(self) -> Dict[str, Dict[str, Any]]:
        """Convert JSON v2 param_grid to optimizer-compatible format with intelligent mapping.

        JSON v2 Format:
            {
                "STRENGTH_ADX_period": [10, 14, 20],
                "TREND_FILTER_period": [100, 150, 200],
                "BULL_adx_min": [20, 25, 30],
                "BEAR_adx_min": [20, 25, 30]
            }

        Optimizer Format:
            {
                "adx_period": {"min": 10, "max": 20, "step": 1},
                "sma_slow_period": {"min": 100, "max": 200, "step": 10},
                "adx_threshold": {"min": 20, "max": 30, "step": 1}  # avg of all ADX thresholds
            }

        Returns:
            Dict with optimizer parameter names and ranges
        """
        # JSON v2 -> Optimizer parameter name mapping
        INDICATOR_MAPPING = {
            "STRENGTH_ADX_period": "adx_period",
            "TREND_FILTER_period": "sma_slow_period",
            "MOMENTUM_RSI_period": "rsi_period",
            "VOLATILITY_ATR_period": "atr_period",  # Keep separate for now
        }

        # Collect all threshold ranges for averaging
        adx_threshold_ranges = []
        rsi_low_ranges = []
        rsi_high_ranges = []

        param_ranges = {}

        for param_path, values in self.param_grid.items():
            if not values:
                continue

            param_key = param_path.replace(".", "_")
            min_val = min(values)
            max_val = max(values)

            # Detect step based on type and value range
            if isinstance(min_val, float) or isinstance(max_val, float):
                step = 0.1
            elif max_val - min_val >= 100:
                step = 10  # Large ranges use step=10
            else:
                step = 1

            range_dict = {"min": min_val, "max": max_val, "step": step}

            # Map indicators directly
            if param_key in INDICATOR_MAPPING:
                mapped_key = INDICATOR_MAPPING[param_key]
                param_ranges[mapped_key] = range_dict
                continue

            # Collect ADX thresholds for averaging
            if "_adx_min" in param_key or "_adx_max" in param_key:
                adx_threshold_ranges.append(range_dict)
                continue

            # Collect RSI thresholds
            if "_rsi_min" in param_key:
                rsi_high_ranges.append(range_dict)
                continue
            if "_rsi_max" in param_key:
                rsi_low_ranges.append(range_dict)
                continue

        # Average ADX thresholds
        if adx_threshold_ranges:
            avg_min = sum(r["min"] for r in adx_threshold_ranges) / len(adx_threshold_ranges)
            avg_max = sum(r["max"] for r in adx_threshold_ranges) / len(adx_threshold_ranges)
            param_ranges["adx_threshold"] = {
                "min": avg_min,
                "max": avg_max,
                "step": 1
            }

        # Average RSI thresholds
        if rsi_low_ranges:
            avg_min = sum(r["min"] for r in rsi_low_ranges) / len(rsi_low_ranges)
            avg_max = sum(r["max"] for r in rsi_low_ranges) / len(rsi_low_ranges)
            param_ranges["rsi_sideways_low"] = {
                "min": avg_min,
                "max": avg_max,
                "step": 1
            }

        if rsi_high_ranges:
            avg_min = sum(r["min"] for r in rsi_high_ranges) / len(rsi_high_ranges)
            avg_max = sum(r["max"] for r in rsi_high_ranges) / len(rsi_high_ranges)
            param_ranges["rsi_sideways_high"] = {
                "min": avg_min,
                "max": avg_max,
                "step": 1
            }

        logger.info(f"Converted v2 param_grid to ranges: {param_ranges}")
        return param_ranges

    def _build_param_ranges_with_defaults(
        self, ranges_dict, ADXParamRanges, SMAParamRanges, RSIParamRanges, BBParamRanges, ParamRange
    ):
        """Build AllParamRanges with intelligent defaults for missing parameters.

        Required parameters from RegimeOptimizer:
        - adx_period, adx_threshold
        - sma_fast_period, sma_slow_period
        - rsi_period, rsi_sideways_low, rsi_sideways_high
        - bb_period, bb_std_dev, bb_width_percentile

        Args:
            ranges_dict: Extracted ranges from JSON v2
            ADXParamRanges, SMAParamRanges, etc.: Pydantic classes

        Returns:
            AllParamRanges instance
        """
        from src.core.regime_optimizer import AllParamRanges

        # Helper to get range with default fallback
        def get_range(key: str, default_min: float, default_max: float, default_step: float) -> ParamRange:
            if key in ranges_dict:
                r = ranges_dict[key]
                return ParamRange(min=r["min"], max=r["max"], step=r["step"])
            else:
                logger.warning(
                    f"Parameter '{key}' not found in JSON v2, using default: "
                    f"min={default_min}, max={default_max}"
                )
                return ParamRange(min=default_min, max=default_max, step=default_step)

        # Build AllParamRanges
        param_ranges = AllParamRanges(
            adx=ADXParamRanges(
                period=get_range("adx_period", 10, 25, 1),
                threshold=get_range("adx_threshold", 20, 35, 1)
            ),
            sma_fast=SMAParamRanges(
                period=get_range("sma_fast_period", 20, 50, 5)  # Default: 20-50
            ),
            sma_slow=SMAParamRanges(
                period=get_range("sma_slow_period", 100, 200, 10)
            ),
            rsi=RSIParamRanges(
                period=get_range("rsi_period", 9, 21, 1),
                sideways_low=get_range("rsi_sideways_low", 35, 45, 1),
                sideways_high=get_range("rsi_sideways_high", 55, 65, 1)
            ),
            bb=BBParamRanges(
                period=get_range("bb_period", 15, 25, 1),  # Default BB period
                std_dev=get_range("bb_std_dev", 1.5, 2.5, 0.1),
                width_percentile=get_range("bb_width_percentile", 20, 40, 5)
            )
        )

        logger.info("Built AllParamRanges with defaults for missing parameters")
        return param_ranges
