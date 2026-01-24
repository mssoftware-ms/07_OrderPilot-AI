"""Entry Analyzer - Indicator Optimization Worker V2 (Stage 2).

Background worker thread for Stage 2 indicator optimization:
- Per-regime optimization (uses only regime-specific bar indices)
- Per-signal-type optimization (entry_long, entry_short, exit_long, exit_short)
- Parallel/sequential execution based on configuration
- Progress reporting and result emission
- Graceful stop support

Date: 2026-01-24
Stage: 2 (Indicator Optimization)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IndicatorOptimizationWorkerV2(QThread):
    """Background worker for Stage 2 indicator optimization.

    Runs optimization for each enabled signal type sequentially:
    1. Filter chart data to regime-specific bars
    2. For each signal type:
       - Test all selected indicators with parameter ranges
       - Calculate metrics (win rate, profit factor, sharpe, etc.)
       - Emit best result for signal type
    3. Emit final results when complete

    Signals:
        progress: (signal_type, current, total, best_score)
        result_ready: (signal_type, result_dict)
        finished: (all_results_dict)
        error: (error_message)
    """

    progress = pyqtSignal(str, int, int, float)  # signal_type, current, total, best_score
    result_ready = pyqtSignal(str, dict)  # signal_type, result
    finished = pyqtSignal(dict)  # all_results per signal type
    error = pyqtSignal(str)

    def __init__(self, config: dict, parent: Any = None) -> None:
        """Initialize worker with optimization configuration.

        Args:
            config: Dictionary with:
                - regime: str (BULL, BEAR, SIDEWAYS)
                - bar_indices: list[int] (regime-specific bar indices)
                - signal_types: list[str] (enabled signal types)
                - indicators: list[str] (selected indicators)
                - param_ranges: dict (parameter ranges per indicator)
                - symbol: str
                - timeframe: str
                - candles: list[dict] (full chart data)
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        self._stop_requested = False

    def run(self) -> None:
        """Execute optimization in background thread.

        Main workflow:
        1. Filter candles to regime bars
        2. For each signal type:
           - Optimize each indicator
           - Emit progress and results
        3. Emit final results
        """
        try:
            regime = self.config["regime"]
            bar_indices = self.config["bar_indices"]
            signal_types = self.config["signal_types"]
            indicators = self.config["indicators"]
            param_ranges = self.config["param_ranges"]
            candles = self.config["candles"]

            logger.info(
                f"Starting Stage 2 optimization: {regime} regime, "
                f"{len(bar_indices)} bars, {len(signal_types)} signal types, "
                f"{len(indicators)} indicators"
            )

            # Filter candles to regime bars
            regime_candles = [candles[i] for i in bar_indices if i < len(candles)]

            if not regime_candles:
                self.error.emit(f"No candles found for {regime} regime bars")
                return

            logger.info(f"Filtered to {len(regime_candles)} regime-specific candles")

            # Results storage
            all_results = {}

            # Optimize each signal type
            for signal_type in signal_types:
                if self._stop_requested:
                    logger.info("Optimization stopped by user")
                    break

                logger.info(f"Optimizing {signal_type}...")

                # Optimize this signal type
                signal_results = self._optimize_signal_type(
                    signal_type=signal_type,
                    regime_candles=regime_candles,
                    indicators=indicators,
                    param_ranges=param_ranges,
                )

                all_results[signal_type] = signal_results

                # Emit best result for this signal type
                if signal_results:
                    best_result = max(signal_results, key=lambda r: r.get("score", 0.0))
                    self.result_ready.emit(signal_type, best_result)

            # Emit final results
            self.finished.emit(all_results)

        except Exception as e:
            logger.exception("Stage 2 optimization failed")
            self.error.emit(str(e))

    def _optimize_signal_type(
        self,
        signal_type: str,
        regime_candles: list[dict],
        indicators: list[str],
        param_ranges: dict,
    ) -> list[dict]:
        """Optimize indicators for one signal type.

        Args:
            signal_type: Signal type (entry_long, entry_short, exit_long, exit_short)
            regime_candles: Filtered candles for regime
            indicators: List of indicator names to test
            param_ranges: Parameter ranges per indicator

        Returns:
            List of result dictionaries with scores and metrics
        """
        results = []
        total_combinations = self._count_total_combinations(indicators, param_ranges)
        current = 0

        logger.info(f"{signal_type}: Testing {total_combinations} parameter combinations")

        for indicator in indicators:
            if self._stop_requested:
                break

            if indicator not in param_ranges:
                logger.warning(f"No parameter ranges for {indicator}, skipping")
                continue

            # Get parameter combinations for this indicator
            param_combinations = self._generate_param_combinations(param_ranges[indicator])

            logger.debug(f"{signal_type}/{indicator}: {len(param_combinations)} combinations")

            best_score = 0.0

            for params in param_combinations:
                if self._stop_requested:
                    break

                current += 1

                # Simulate optimization (placeholder)
                # TODO: Replace with actual indicator optimization logic
                result = self._test_indicator_params(
                    indicator=indicator,
                    params=params,
                    signal_type=signal_type,
                    regime_candles=regime_candles,
                )

                results.append(result)

                # Update best score
                if result["score"] > best_score:
                    best_score = result["score"]

                # Emit progress every 10 trials
                if current % 10 == 0 or current == total_combinations:
                    self.progress.emit(signal_type, current, total_combinations, best_score)

        logger.info(f"{signal_type}: Completed {len(results)} tests")
        return results

    def _count_total_combinations(self, indicators: list[str], param_ranges: dict) -> int:
        """Count total parameter combinations across all indicators.

        Args:
            indicators: List of indicator names
            param_ranges: Parameter ranges per indicator

        Returns:
            Total number of combinations
        """
        total = 0
        for indicator in indicators:
            if indicator in param_ranges:
                combinations = self._generate_param_combinations(param_ranges[indicator])
                total += len(combinations)
        return total

    def _generate_param_combinations(self, ranges: dict) -> list[dict]:
        """Generate all parameter combinations from ranges.

        Args:
            ranges: Dictionary with param_name -> {min, max, step}

        Returns:
            List of parameter dictionaries
        """
        import itertools

        # Extract parameter names and values
        param_names = list(ranges.keys())
        param_values = []

        for param_name in param_names:
            param_range = ranges[param_name]
            min_val = param_range["min"]
            max_val = param_range["max"]
            step = param_range["step"]

            # Generate values for this parameter
            values = []
            current = min_val
            while current <= max_val:
                values.append(current)
                current += step

            param_values.append(values)

        # Generate all combinations
        combinations = []
        for combo in itertools.product(*param_values):
            param_dict = {param_names[i]: combo[i] for i in range(len(param_names))}
            combinations.append(param_dict)

        return combinations

    def _test_indicator_params(
        self,
        indicator: str,
        params: dict,
        signal_type: str,
        regime_candles: list[dict],
    ) -> dict:
        """Test indicator with specific parameters.

        Placeholder for actual optimization logic.
        TODO: Integrate with IndicatorSetOptimizer or BacktestEngine

        Args:
            indicator: Indicator name (RSI, MACD, etc.)
            params: Parameter dictionary
            signal_type: Signal type being tested
            regime_candles: Candles for regime

        Returns:
            Result dictionary with metrics
        """
        import random

        # Simulate calculation (placeholder)
        # TODO: Replace with actual indicator evaluation
        score = random.uniform(30.0, 90.0)
        win_rate = random.uniform(0.4, 0.8)
        profit_factor = random.uniform(1.0, 3.0)
        sharpe_ratio = random.uniform(0.5, 2.5)
        trades = random.randint(5, 50)

        result = {
            "indicator": indicator,
            "params": params,
            "signal_type": signal_type,
            "score": score,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "trades": trades,
            "regime": self.config["regime"],
        }

        return result

    def stop(self) -> None:
        """Request graceful stop of optimization.

        Sets internal flag, worker will stop at next checkpoint.
        """
        self._stop_requested = True
        logger.info("Stop requested for Stage 2 optimization")
