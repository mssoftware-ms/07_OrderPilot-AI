"""Regime Parameter Optimization Thread.

Simulates different regime parameter combinations and evaluates their performance
on historical chart data.

Features:
- Grid search over parameter ranges (DEPRECATED - use Optuna TPE)
- Optuna TPE-based optimization (NEW - 10-100x faster)
- Backtesting with regime detection
- Evaluation metrics (accuracy, stability, switches)
- Progress reporting
- Result ranking

Migration Status:
- ✅ New: RegimeOptimizer (Optuna TPE-based)
- ⚠️ Deprecated: Old grid search code (kept as fallback)
- 🔄 Use USE_OPTUNA_TPE flag to switch
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from itertools import product
from typing import Dict, List, Any
import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal

from src.core.tradingbot.regime_engine_json import RegimeEngineJSON
from src.core.indicators.engine import IndicatorEngine
from src.core import RegimeOptimizer, RegimeOptimizationConfig, RegimeResultsManager

logger = logging.getLogger(__name__)

# Feature Flag: Enable Optuna TPE optimization
USE_OPTUNA_TPE = True  # Set to False to use old grid search


class RegimeOptimizationThread(QThread):
    """Background thread for regime parameter optimization.

    Performs grid search over parameter combinations and evaluates
    regime detection quality on historical data.

    Signals:
        progress: (current, total, message)
        result_ready: (result_dict)
        finished_with_results: (results_list)
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
        scope: str = "entry"
    ):
        """Initialize regime optimization thread.

        Args:
            df: OHLCV DataFrame for backtesting
            config_template_path: Path to base JSON regime config
            param_grid: Dict mapping parameter paths to value lists
                Example: {
                    "adx.period": [10, 14, 20],
                    "adx.threshold": [17, 25, 40],
                    "rsi.period": [9, 14, 21]
                }
            scope: Regime scope ("entry", "exit", "in_trade")
        """
        super().__init__()
        self.df = df.copy()
        self.config_template_path = config_template_path
        self.param_grid = param_grid
        self.scope = scope
        self._stop_requested = False
        self._last_backtest_timing: dict | None = None
        self._timing_totals = self._init_timing_totals()
        self.timing_summary: dict | None = None
        self.timing_summary_text = ""

        # Calculate total combinations
        self.total_combinations = 1
        for values in param_grid.values():
            self.total_combinations *= len(values)

    @staticmethod
    def _init_timing_totals() -> dict:
        """Initialize timing counters for performance analysis."""
        return {
            "config_s": 0.0,
            "backtest_s": 0.0,
            "metrics_s": 0.0,
            "score_s": 0.0,
            "total_eval_s": 0.0,
            "config_write_s": 0.0,
            "classify_s": 0.0,
            "classify_calls": 0,
            "backtest_loop_s": 0.0,
        }

    def _accumulate_timings(self, timings: dict) -> None:
        """Accumulate timing totals for optimization analysis."""
        self._timing_totals["config_s"] += timings.get("config_s", 0.0)
        self._timing_totals["backtest_s"] += timings.get("backtest_s", 0.0)
        self._timing_totals["metrics_s"] += timings.get("metrics_s", 0.0)
        self._timing_totals["score_s"] += timings.get("score_s", 0.0)
        self._timing_totals["total_eval_s"] += timings.get("total_eval_s", 0.0)
        self._timing_totals["config_write_s"] += timings.get("config_write_s", 0.0)
        self._timing_totals["classify_s"] += timings.get("classify_s", 0.0)
        self._timing_totals["classify_calls"] += timings.get("classify_calls", 0)
        self._timing_totals["backtest_loop_s"] += timings.get("backtest_loop_s", 0.0)

    def _finalize_timing_summary(self, total_s: float, combos_tested: int) -> None:
        """Build and store a timing summary for UI and logs."""
        totals = self._timing_totals
        avg_per_combo = total_s / combos_tested if combos_tested else 0.0
        classify_calls = totals["classify_calls"] or 1
        classify_avg_ms = (totals["classify_s"] / classify_calls) * 1000.0
        backtest_pct = (totals["backtest_s"] / total_s) if total_s > 0 else 0.0

        self.timing_summary = {
            "total_s": total_s,
            "combos_tested": combos_tested,
            "avg_per_combo_s": avg_per_combo,
            "backtest_s": totals["backtest_s"],
            "backtest_pct": backtest_pct,
            "classify_calls": totals["classify_calls"],
            "classify_avg_ms": classify_avg_ms,
            "config_s": totals["config_s"],
            "metrics_s": totals["metrics_s"],
            "score_s": totals["score_s"],
        }

        self.timing_summary_text = (
            f"Timing: total {total_s:.1f}s | avg/combo {avg_per_combo:.2f}s | "
            f"backtest {totals['backtest_s']:.1f}s ({backtest_pct:.0%}) | "
            f"classify avg {classify_avg_ms:.1f}ms"
        )

        logger.info(
            "Optimization timing summary: total=%.2fs combos=%d avg=%.3fs "
            "backtest=%.2fs (%.0f%%) classify_avg=%.2fms",
            total_s,
            combos_tested,
            avg_per_combo,
            totals["backtest_s"],
            backtest_pct * 100.0,
            classify_avg_ms,
        )

    def request_stop(self):
        """Request graceful stop of optimization."""
        self._stop_requested = True
        logger.info("Regime optimization stop requested")

    def run(self):
        """Execute regime parameter optimization.

        Uses Optuna TPE if USE_OPTUNA_TPE=True (recommended),
        otherwise falls back to grid search (deprecated).
        """
        if USE_OPTUNA_TPE:
            logger.info("Using Optuna TPE-based optimization (10-100x faster)")
            self._run_optuna_optimization()
        else:
            logger.warning("Using DEPRECATED grid search. Set USE_OPTUNA_TPE=True for better performance.")
            self._run_grid_search_optimization()

    def _run_optuna_optimization(self):
        """Execute Optuna TPE-based optimization (NEW)."""
        try:
            total_start = time.perf_counter()
            logger.info(
                f"Starting Optuna regime optimization: max_trials={self.total_combinations}, "
                f"scope={self.scope}"
            )

            # Import required types
            from src.core.regime_optimizer import (
                AllParamRanges, ADXParamRanges, SMAParamRanges,
                RSIParamRanges, BBParamRanges, ParamRange, OptimizationConfig
            )

            # Convert param_grid to structured param_ranges
            ranges_dict = self._convert_param_grid_to_ranges()

            # Build structured AllParamRanges from flat dict
            param_ranges = AllParamRanges(
                adx=ADXParamRanges(
                    period=ParamRange(**ranges_dict.get("adx_period", {"min": 10, "max": 30, "step": 1})),
                    threshold=ParamRange(**ranges_dict.get("adx_threshold", {"min": 20, "max": 35, "step": 1}))
                ),
                sma_fast=SMAParamRanges(
                    period=ParamRange(**ranges_dict.get("sma_fast_period", {"min": 20, "max": 100, "step": 1}))
                ),
                sma_slow=SMAParamRanges(
                    period=ParamRange(**ranges_dict.get("sma_slow_period", {"min": 100, "max": 300, "step": 1}))
                ),
                rsi=RSIParamRanges(
                    period=ParamRange(**ranges_dict.get("rsi_period", {"min": 10, "max": 20, "step": 1})),
                    sideways_low=ParamRange(**ranges_dict.get("rsi_sideways_low", {"min": 30, "max": 45, "step": 1})),
                    sideways_high=ParamRange(**ranges_dict.get("rsi_sideways_high", {"min": 55, "max": 70, "step": 1}))
                ),
                bb=BBParamRanges(
                    period=ParamRange(**ranges_dict.get("bb_period", {"min": 15, "max": 30, "step": 1})),
                    std_dev=ParamRange(**ranges_dict.get("bb_std_dev", {"min": 1.5, "max": 3.0, "step": 0.5})),
                    width_percentile=ParamRange(**ranges_dict.get("bb_width_percentile", {"min": 10, "max": 40, "step": 1}))
                )
            )

            # Create Optuna config
            config = OptimizationConfig(
                max_trials=min(self.total_combinations, 150),  # Cap at 150 trials
                n_jobs=1,  # Single-threaded for Qt compatibility
            )

            # Create optimizer with correct argument order
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

                self.progress.emit(
                    current,
                    total,
                    f"Trial {current}/{total} | Best: {best_score:.1f}"
                )

                # Emit individual result
                result_dict = {
                    'params': trial.params,
                    'score': int(trial.value) if trial.value else 0,
                    'metrics': trial.user_attrs.get('metrics', {}),
                    'timestamp': datetime.utcnow(),
                    'trial_number': trial.number,
                }
                self.result_ready.emit(result_dict)

                return self._stop_requested  # Return True to stop optimization

            # Run optimization
            study = optimizer.optimize(callback=on_trial_complete)

            # Get all results and rank them
            all_results = []
            for trial in study.trials:
                if trial.state != 1:  # COMPLETE
                    continue
                all_results.append({
                    'score': trial.value,
                    'params': trial.params,
                    'metrics': trial.user_attrs.get('metrics', {}),
                })

            # Sort and rank
            ranked_results = results_manager.sort_and_rank(all_results)

            # Convert to old result format for UI compatibility
            results = self._convert_optuna_results_to_grid_format(study, ranked_results)

            total_elapsed = time.perf_counter() - total_start
            self._finalize_timing_summary(total_elapsed, len(results))

            best_score = study.best_value if study.best_trial else 0
            logger.info(
                f"Optuna optimization complete: {len(results)} trials, "
                f"best_score={best_score:.1f}"
            )

            self.finished_with_results.emit(results)

        except Exception as e:
            error_msg = f"Optuna regime optimization failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)

    def _run_grid_search_optimization(self):
        """Execute grid search optimization (DEPRECATED)."""
        try:
            total_start = time.perf_counter()
            logger.info(
                f"Starting regime optimization: {self.total_combinations} combinations, "
                f"scope={self.scope}"
            )

            results = []
            current = 0
            self._timing_totals = self._init_timing_totals()

            # Reduce verbose logging during optimization (significant I/O cost)
            engine_logger = logging.getLogger("src.core.tradingbot.regime_engine_json")
            indicators_logger = logging.getLogger("src.core.indicators.engine")
            prev_engine_level = engine_logger.level
            prev_indicators_level = indicators_logger.level
            engine_logger.setLevel(logging.WARNING)
            indicators_logger.setLevel(logging.WARNING)

            # Generate all parameter combinations
            param_names = list(self.param_grid.keys())
            param_values = [self.param_grid[name] for name in param_names]

            try:
                for combo in product(*param_values):
                    if self._stop_requested:
                        logger.info("Optimization stopped by user")
                        break

                    current += 1

                    # Create parameter dict from combination
                    params = dict(zip(param_names, combo))

                    # Emit progress
                    param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                    self.progress.emit(current, self.total_combinations, f"Testing: {param_str}")

                    # Evaluate this parameter combination
                    try:
                        result = self._evaluate_params(params)
                        results.append(result)
                        self.result_ready.emit(result)
                    except Exception as e:
                        logger.error(f"Error evaluating params {params}: {e}")
                        # Continue with next combination
            finally:
                engine_logger.setLevel(prev_engine_level)
                indicators_logger.setLevel(prev_indicators_level)

            # Sort results by composite score
            results.sort(key=lambda x: x['score'], reverse=True)

            total_elapsed = time.perf_counter() - total_start
            self._finalize_timing_summary(total_elapsed, current)
            logger.info(f"Regime optimization complete: {len(results)} results")
            self.finished_with_results.emit(results)

        except Exception as e:
            error_msg = f"Regime optimization failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)

    def _evaluate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single parameter combination.

        Args:
            params: Parameter dictionary

        Returns:
            Result dict with metrics and parameters
        """
        # 1. Create modified config with these parameters
        t0 = time.perf_counter()
        config_dict = self._create_config_with_params(params)
        t1 = time.perf_counter()

        # 2. Run regime detection on entire DataFrame
        regime_history = self._backtest_regimes(config_dict)
        t2 = time.perf_counter()

        # 3. Calculate evaluation metrics
        metrics = self._calculate_metrics(regime_history)
        t3 = time.perf_counter()

        # 4. Calculate composite score
        score = self._calculate_composite_score(metrics)
        t4 = time.perf_counter()

        timings = {
            "config_s": t1 - t0,
            "backtest_s": t2 - t1,
            "metrics_s": t3 - t2,
            "score_s": t4 - t3,
            "total_eval_s": t4 - t0,
        }

        if self._last_backtest_timing:
            timings.update(self._last_backtest_timing)

        self._accumulate_timings(timings)

        return {
            'params': params,
            'config': config_dict,
            'regime_history': regime_history,
            'metrics': metrics,
            'score': int(score),  # Integer score
            'timings': timings,
            'timestamp': datetime.utcnow()
        }

    def _create_config_with_params(self, params: Dict[str, Any]) -> dict:
        """Create JSON config dict with modified parameters.

        Args:
            params: Parameters to override (path notation)
                Example: {"adx.period": 20, "adx.threshold": 30}

        Returns:
            Modified config dict
        """
        # Load base config
        import json
        from pathlib import Path

        with open(self.config_template_path, 'r') as f:
            config = json.load(f)

        # Apply parameter overrides
        for param_path, value in params.items():
            parts = param_path.split('.')

            if len(parts) == 2:
                # indicator.param (e.g., "adx.period")
                indicator_type = parts[0].upper()
                param_name = parts[1]

                # Find and update indicator
                for ind in config['indicators']:
                    if ind['type'].upper() == indicator_type or ind['id'].lower() == parts[0].lower():
                        ind['params'][param_name] = value
                        logger.debug(f"Updated {ind['id']}.{param_name} = {value}")
                        break

            elif len(parts) == 3 and parts[0] == 'regime':
                # regime.regime_id.threshold (e.g., "regime.strong_uptrend.adx_threshold")
                regime_id = parts[1]
                threshold_name = parts[2]

                # Find and update regime condition
                for regime in config['regimes']:
                    if regime['id'] == regime_id:
                        # Update threshold in conditions
                        # This requires traversing the condition tree
                        self._update_regime_threshold(regime['conditions'], threshold_name, value)
                        break

        return config

    def _update_regime_threshold(self, conditions: dict, threshold_name: str, value: Any):
        """Recursively update threshold in condition tree.

        Args:
            conditions: Condition dict (recursive structure)
            threshold_name: Name of threshold to update (e.g., "adx_threshold")
            value: New threshold value
        """
        if 'all' in conditions:
            for cond in conditions['all']:
                self._update_regime_threshold(cond, threshold_name, value)
        elif 'any' in conditions:
            for cond in conditions['any']:
                self._update_regime_threshold(cond, threshold_name, value)
        elif 'left' in conditions and 'right' in conditions:
            # Leaf condition
            indicator_id = conditions['left'].get('indicator_id', '')

            # Check if this condition matches the threshold
            if threshold_name in indicator_id or threshold_name.replace('_threshold', '') in indicator_id:
                if 'value' in conditions['right']:
                    conditions['right']['value'] = value
                    logger.debug(f"Updated regime threshold {threshold_name} = {value}")
                elif 'min' in conditions['right'] or 'max' in conditions['right']:
                    # For 'between' operators, update both bounds proportionally
                    if 'min' in conditions['right']:
                        conditions['right']['min'] = value
                    if 'max' in conditions['right']:
                        conditions['right']['max'] = value

    def _backtest_regimes(self, config_dict: dict) -> List[Dict[str, Any]]:
        """Backtest regime detection on historical data.

        Args:
            config_dict: JSON config dictionary

        Returns:
            List of regime periods with timestamps and regime names
        """
        # Save config to temp file
        import tempfile
        import json

        write_start = time.perf_counter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f)
            temp_config_path = f.name
        write_elapsed = time.perf_counter() - write_start

        try:
            # Initialize regime engine
            engine = RegimeEngineJSON()

            # Iterate through DataFrame and detect regimes
            regime_history = []
            current_regime = None
            regime_start_idx = 0

            # Sample every N bars to speed up (optional, for large datasets)
            sample_rate = max(1, len(self.df) // 500)  # Max 500 regime checks
            classify_total = 0.0
            classify_calls = 0
            loop_start = time.perf_counter()

            for idx in range(0, len(self.df), sample_rate):
                # Get data up to this point
                data_window = self.df.iloc[:idx+1]

                if len(data_window) < 50:  # Need minimum bars for indicators
                    continue

                try:
                    # Classify regime
                    classify_start = time.perf_counter()
                    state = engine.classify_from_config(
                        data=data_window,
                        config_path=temp_config_path,
                        scope=self.scope
                    )
                    classify_total += time.perf_counter() - classify_start
                    classify_calls += 1

                    regime_name = state.regime_label

                    # Check for regime change
                    if regime_name != current_regime:
                        # End previous regime
                        if current_regime is not None:
                            regime_history.append({
                                'regime': current_regime,
                                'start_idx': regime_start_idx,
                                'end_idx': idx - sample_rate,
                                'start_time': self.df.index[regime_start_idx],
                                'end_time': self.df.index[idx - sample_rate],
                                'duration_bars': (idx - sample_rate) - regime_start_idx,
                                'confidence': state.regime_confidence
                            })

                        # Start new regime
                        current_regime = regime_name
                        regime_start_idx = idx

                except Exception as e:
                    logger.debug(f"Regime detection failed at idx {idx}: {e}")
                    continue

            # Add final regime
            if current_regime is not None:
                regime_history.append({
                    'regime': current_regime,
                    'start_idx': regime_start_idx,
                    'end_idx': len(self.df) - 1,
                    'start_time': self.df.index[regime_start_idx],
                    'end_time': self.df.index[-1],
                    'duration_bars': len(self.df) - 1 - regime_start_idx,
                    'confidence': 0.5  # Default for last regime
                })

            loop_elapsed = time.perf_counter() - loop_start
            self._last_backtest_timing = {
                "config_write_s": write_elapsed,
                "classify_s": classify_total,
                "classify_calls": classify_calls,
                "backtest_loop_s": loop_elapsed,
            }

            return regime_history

        finally:
            # Cleanup temp file
            import os
            try:
                os.unlink(temp_config_path)
            except:
                pass

    def _calculate_metrics(self, regime_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate evaluation metrics for regime history.

        Args:
            regime_history: List of regime periods

        Returns:
            Dict with metrics:
                - regime_count: Number of distinct regimes
                - avg_duration: Average regime duration (bars)
                - stability_score: How stable regimes are (0-1)
                - switch_count: Number of regime switches
                - coverage: % of chart covered by regimes
        """
        if not regime_history:
            return {
                'regime_count': 0,
                'avg_duration': 0.0,
                'stability_score': 0.0,
                'switch_count': 0,
                'coverage': 0.0
            }

        # 1. Regime count (distinct regime types)
        regime_types = set([r['regime'] for r in regime_history])
        regime_count = len(regime_types)

        # 2. Average duration
        durations = [r['duration_bars'] for r in regime_history]
        avg_duration = sum(durations) / len(durations)

        # 3. Stability score (longer regimes = more stable)
        # Normalize to 0-1: longer average duration = higher score
        # Assume 100 bars = max stable duration for normalization
        stability_score = min(avg_duration / 100.0, 1.0)

        # 4. Switch count (fewer switches = better)
        switch_count = len(regime_history) - 1  # Transitions between regimes

        # 5. Coverage (% of bars covered by regimes)
        total_bars = len(self.df)
        covered_bars = sum(durations)
        coverage = (covered_bars / total_bars) * 100 if total_bars > 0 else 0.0

        return {
            'regime_count': regime_count,
            'avg_duration': avg_duration,
            'stability_score': stability_score,
            'switch_count': switch_count,
            'coverage': coverage
        }

    def _calculate_composite_score(self, metrics: Dict[str, float]) -> float:
        """Calculate composite score from metrics.

        Weighting:
            - Stability: 40% (longer regimes = better)
            - Coverage: 30% (more of chart covered = better)
            - Regime Count: 20% (moderate diversity = better, 3-5 optimal)
            - Switch Count: 10% (fewer switches = better)

        Args:
            metrics: Evaluation metrics

        Returns:
            Composite score (0-100)
        """
        # 1. Stability score (already 0-1)
        stability_score = metrics['stability_score']

        # 2. Coverage score (0-100 → 0-1)
        coverage_score = min(metrics['coverage'] / 100.0, 1.0)

        # 3. Regime count score (optimal = 3-5 regimes)
        regime_count = metrics['regime_count']
        if regime_count == 0:
            regime_score = 0.0
        elif 3 <= regime_count <= 5:
            regime_score = 1.0  # Optimal
        elif regime_count < 3:
            regime_score = regime_count / 3.0  # Too few
        else:
            regime_score = max(0.0, 1.0 - (regime_count - 5) * 0.1)  # Too many

        # 4. Switch count score (fewer = better, normalized to 0-1)
        # Assume 50 switches = 0 score, 0 switches = 1.0 score
        switch_count = metrics['switch_count']
        switch_score = max(0.0, 1.0 - (switch_count / 50.0))

        # Composite score (weighted)
        composite = (
            stability_score * 0.40 +
            coverage_score * 0.30 +
            regime_score * 0.20 +
            switch_score * 0.10
        )

        return composite * 100  # 0-100 scale

    # ========== OPTUNA INTEGRATION HELPERS ==========

    def _convert_param_grid_to_ranges(self) -> Dict[str, Dict[str, Any]]:
        """Convert old param_grid format to ParamRange-compatible format.

        Old format (grid):
            {"adx.period": [10, 14, 20], "adx.threshold": [17, 25, 40]}
            {"bb_std_dev": [1.5, 2.0, 2.5, 3.0]}

        New format (ParamRange dict):
            {
                "adx_period": {"min": 10, "max": 20, "step": 1},
                "adx_threshold": {"min": 17, "max": 40, "step": 1},
                "bb_std_dev": {"min": 1.5, "max": 3.0, "step": 0.1}
            }

        Returns:
            Param ranges dict with underscore keys for AllParamRanges construction
        """
        param_ranges = {}

        for param_path, values in self.param_grid.items():
            if not values:
                continue

            # Convert dotted path to underscore (adx.period -> adx_period)
            param_key = param_path.replace(".", "_")

            min_val = min(values)
            max_val = max(values)

            # Detect type and calculate appropriate step
            if isinstance(min_val, float) or isinstance(max_val, float):
                # Float parameter: Use 0.1 as default step
                step = 0.1
            else:
                # Integer parameter: Use 1 as step
                step = 1

            # Create range with min/max/step (ParamRange fields)
            param_ranges[param_key] = {
                "min": min_val,
                "max": max_val,
                "step": step,
            }

        logger.info(f"Converted param_grid to ranges: {param_ranges}")
        return param_ranges

    def _convert_optuna_results_to_grid_format(
        self,
        study,
        best_result
    ) -> List[Dict[str, Any]]:
        """Convert Optuna study results to old grid search result format.

        Args:
            study: Optuna study object
            best_result: RegimeResult object

        Returns:
            List of result dicts compatible with UI
        """
        results = []

        for trial in study.trials:
            if trial.state != 1:  # COMPLETE
                continue

            result = {
                'params': trial.params,
                'score': int(trial.value),
                'metrics': trial.user_attrs.get('metrics', {}),
                'timestamp': datetime.utcnow(),
                'trial_number': trial.number,
                'config': None,  # Not stored in Optuna trials
                'regime_history': None,  # Not stored in Optuna trials
                'timings': {
                    'total_eval_s': trial.duration.total_seconds() if trial.duration else 0.0
                }
            }

            results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)

        logger.info(f"Converted {len(results)} Optuna trials to grid format")
        return results
