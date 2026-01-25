"""Regime Parameter Optimization Thread - v2.0 (Optuna TPE Only).

Fast TPE-based optimization using RegimeOptimizer with 5-component RegimeScore.
Fully compatible with JSON v2 format.

Features:
- Optuna TPE-based optimization (10-100x faster than grid search)
- 5-component RegimeScore (Separability, Coherence, Fidelity, Boundary, Coverage)
- ADX/DI-based regime detection (matching original regime_engine.py)
- JSON v2 format support with intelligent parameter mapping
- Progress reporting with ETA
- Result ranking and storage

JSON v2 Parameter Mapping (ADX/DI-based):
    Indicators:
        STRENGTH_ADX_period -> adx_period
        MOMENTUM_RSI_period -> rsi_period
        VOLATILITY_ATR_period -> atr_period

    Thresholds (from regimes):
        ADX trending threshold (BULL/BEAR) -> adx_trending_threshold
        ADX weak threshold (SIDEWAYS) -> adx_weak_threshold
        DI difference threshold -> di_diff_threshold
        RSI strong bull/bear -> rsi_strong_bull/rsi_strong_bear
        ATR move percentages -> strong_move_pct/extreme_move_pct
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

            # Import required types (ADX/DI-based)
            from src.core.regime_optimizer import (
                AllParamRanges, ADXParamRanges, RSIParamRanges,
                ATRParamRanges, ParamRange, OptimizationConfig
            )

            # Convert param_grid to structured param_ranges
            ranges_dict = self._convert_param_grid_to_ranges_v2()

            # Build AllParamRanges with intelligent defaults for missing params
            param_ranges = self._build_param_ranges_with_defaults(
                ranges_dict, ADXParamRanges, RSIParamRanges, ATRParamRanges, ParamRange
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
        """Convert JSON v2 param_grid to ADX/DI-based optimizer format.

        JSON v2 Format:
            {
                "STRENGTH_ADX_period": [10, 14, 20],
                "MOMENTUM_RSI_period": [12, 14, 16],
                "VOLATILITY_ATR_period": [10, 14, 20],
                "BULL_adx_min": [20, 25, 30],
                "SIDEWAYS_adx_max": [15, 18, 20]
            }

        Optimizer Format (ADX/DI-based):
            {
                "adx_period": {"min": 10, "max": 20, "step": 1},
                "adx_trending_threshold": {"min": 20, "max": 30, "step": 1},
                "adx_weak_threshold": {"min": 15, "max": 20, "step": 1},
                "di_diff_threshold": {"min": 3, "max": 10, "step": 1},
                "rsi_period": {"min": 12, "max": 16, "step": 1},
                ...
            }

        Returns:
            Dict with optimizer parameter names and ranges
        """
        # JSON v2 -> Optimizer parameter name mapping
        INDICATOR_MAPPING = {
            "STRENGTH_ADX_period": "adx_period",
            "MOMENTUM_RSI_period": "rsi_period",
            "VOLATILITY_ATR_period": "atr_period",
        }

        # Collect threshold ranges
        adx_trending_ranges = []  # BULL/BEAR adx_min
        adx_weak_ranges = []  # SIDEWAYS adx_max
        rsi_bull_ranges = []  # RSI strong bull
        rsi_bear_ranges = []  # RSI strong bear

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
                step = 10
            else:
                step = 1

            range_dict = {"min": min_val, "max": max_val, "step": step}

            # Map indicators directly
            if param_key in INDICATOR_MAPPING:
                mapped_key = INDICATOR_MAPPING[param_key]
                param_ranges[mapped_key] = range_dict
                continue

            # Collect ADX trending thresholds (BULL/BEAR adx_min)
            if ("BULL" in param_key or "BEAR" in param_key) and "_adx_min" in param_key:
                adx_trending_ranges.append(range_dict)
                continue

            # Collect ADX weak thresholds (SIDEWAYS adx_max)
            if "SIDEWAYS" in param_key and "_adx_max" in param_key:
                adx_weak_ranges.append(range_dict)
                continue

            # Collect DI difference thresholds
            if "di_diff" in param_key.lower():
                param_ranges["di_diff_threshold"] = range_dict
                continue

            # Collect RSI strong bull thresholds
            if "rsi_strong_bull" in param_key.lower() or ("BULL" in param_key and "rsi" in param_key.lower()):
                rsi_bull_ranges.append(range_dict)
                continue

            # Collect RSI strong bear thresholds
            if "rsi_strong_bear" in param_key.lower() or ("BEAR" in param_key and "rsi" in param_key.lower()):
                rsi_bear_ranges.append(range_dict)
                continue

            # Collect ATR move percentages
            if "strong_move_pct" in param_key.lower():
                param_ranges["strong_move_pct"] = range_dict
                continue
            if "extreme_move_pct" in param_key.lower():
                param_ranges["extreme_move_pct"] = range_dict
                continue

        # Average ADX trending thresholds
        if adx_trending_ranges:
            avg_min = sum(r["min"] for r in adx_trending_ranges) / len(adx_trending_ranges)
            avg_max = sum(r["max"] for r in adx_trending_ranges) / len(adx_trending_ranges)
            param_ranges["adx_trending_threshold"] = {
                "min": avg_min,
                "max": avg_max,
                "step": 1
            }

        # Average ADX weak thresholds
        if adx_weak_ranges:
            avg_min = sum(r["min"] for r in adx_weak_ranges) / len(adx_weak_ranges)
            avg_max = sum(r["max"] for r in adx_weak_ranges) / len(adx_weak_ranges)
            param_ranges["adx_weak_threshold"] = {
                "min": avg_min,
                "max": avg_max,
                "step": 1
            }

        # Average RSI thresholds
        if rsi_bull_ranges:
            avg_min = sum(r["min"] for r in rsi_bull_ranges) / len(rsi_bull_ranges)
            avg_max = sum(r["max"] for r in rsi_bull_ranges) / len(rsi_bull_ranges)
            param_ranges["rsi_strong_bull"] = {
                "min": avg_min,
                "max": avg_max,
                "step": 1
            }

        if rsi_bear_ranges:
            avg_min = sum(r["min"] for r in rsi_bear_ranges) / len(rsi_bear_ranges)
            avg_max = sum(r["max"] for r in rsi_bear_ranges) / len(rsi_bear_ranges)
            param_ranges["rsi_strong_bear"] = {
                "min": avg_min,
                "max": avg_max,
                "step": 1
            }

        logger.info(f"Converted v2 param_grid to ADX/DI-based ranges: {param_ranges}")
        return param_ranges

    def _build_param_ranges_with_defaults(
        self, ranges_dict, ADXParamRanges, RSIParamRanges, ATRParamRanges, ParamRange
    ):
        """Build AllParamRanges with intelligent defaults for missing parameters.

        Required parameters from RegimeOptimizer (ADX/DI-based):
        - adx_period, adx_trending_threshold, adx_weak_threshold, di_diff_threshold
        - rsi_period, rsi_strong_bull, rsi_strong_bear
        - atr_period, strong_move_pct, extreme_move_pct

        Args:
            ranges_dict: Extracted ranges from JSON v2
            ADXParamRanges, RSIParamRanges, ATRParamRanges: Pydantic classes

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

        # Build AllParamRanges with ADX/DI-based parameters
        param_ranges = AllParamRanges(
            adx=ADXParamRanges(
                period=get_range("adx_period", 10, 25, 1),
                trending_threshold=get_range("adx_trending_threshold", 20, 35, 1),
                weak_threshold=get_range("adx_weak_threshold", 15, 25, 1),
                di_diff_threshold=get_range("di_diff_threshold", 3, 10, 1),
            ),
            rsi=RSIParamRanges(
                period=get_range("rsi_period", 9, 21, 1),
                strong_bull=get_range("rsi_strong_bull", 50, 65, 1),
                strong_bear=get_range("rsi_strong_bear", 35, 50, 1),
            ),
            atr=ATRParamRanges(
                period=get_range("atr_period", 10, 20, 1),
                strong_move_pct=get_range("strong_move_pct", 1.0, 2.5, 0.1),
                extreme_move_pct=get_range("extreme_move_pct", 2.0, 4.0, 0.5),
            ),
        )

        logger.info("Built AllParamRanges with ADX/DI-based defaults for missing parameters")
        return param_ranges
