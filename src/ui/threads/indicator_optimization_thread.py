"""Indicator Optimization Thread for background processing.

This thread runs indicator parameter optimization in the background using the
CLI orchestrator for catalog-based optimization with regime filtering and composite scoring.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class IndicatorOptimizationThread(QThread):
    """Background thread for indicator parameter optimization using CLI orchestrator.

    Uses the IndicatorOptimizationOrchestrator from tools/optimize_indicators.py
    which provides:
    - Catalog-based parameter ranges from indicator_catalog.yaml
    - Grid search with itertools.product for exhaustive combinations
    - Regime compatibility filtering (0-1 scores)
    - Constraint validation ("fast < slow")
    - Composite scoring: Sharpe 30%, Win Rate 25%, Profit Factor 25%, Max DD 20%
    - Top-N selection with thresholds

    Signals:
        finished: Emitted when optimization completes with results list
        progress: Emitted during processing (percentage, status message)
        error: Emitted on errors (error message)
    """

    finished = pyqtSignal(list)  # List[Dict] of optimization results
    progress = pyqtSignal(int, str)  # (percentage: int, message: str)
    error = pyqtSignal(str)  # error message

    def __init__(
        self,
        selected_indicators: List[str],
        param_ranges: Dict[str, Dict[str, int]],  # Not used - kept for API compatibility
        json_config_path: str,  # Not used - will generate configs
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        preset: str = "balanced",
        parent=None
    ):
        """Initialize optimization thread.

        Args:
            selected_indicators: List of indicator types to optimize (e.g. ['RSI', 'MACD', 'ADX'])
            param_ranges: DEPRECATED - parameter ranges now come from catalog
            json_config_path: DEPRECATED - configs will be generated
            symbol: Trading symbol (e.g. 'AAPL', 'BTC/USD')
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital for backtest
            preset: Grid search preset ('quick_scan', 'balanced', 'exhaustive')
            parent: Parent QObject
        """
        super().__init__(parent)
        self.selected_indicators = selected_indicators
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.preset = preset

        self.results: List[Dict[str, Any]] = []
        self._stop_requested = False

    def stop(self):
        """Request thread to stop."""
        self._stop_requested = True
        logger.info("Optimization stop requested")

    def run(self):
        """Main optimization loop - runs in background thread using CLI orchestrator."""
        try:
            logger.info(f"Starting CLI-based optimization for {len(self.selected_indicators)} indicators")

            # Import orchestrator components
            from tools.optimize_indicators import IndicatorOptimizationOrchestrator
            from src.core.tradingbot.indicator_grid_search import GridSearchConfig

            # Initialize orchestrator with catalog
            orchestrator = IndicatorOptimizationOrchestrator(
                catalog_path="config/indicator_catalog.yaml"
            )

            # Generate sample data for optimization
            # In production, this would load real market data
            sample_data = orchestrator._generate_sample_data(bars=1000)

            # Total regimes to test (4: R1_trend, R2_range, R3_breakout, R4_volatile)
            regimes = ["R1_trend", "R2_range", "R3_breakout", "R4_volatile"]
            total_regimes = len(regimes)
            current_regime_idx = 0

            # Store all results across regimes
            all_results = []

            # Optimize each regime
            for regime_id in regimes:
                if self._stop_requested:
                    logger.info("Optimization stopped by user request")
                    return

                current_regime_idx += 1
                regime_progress_base = int((current_regime_idx - 1) / total_regimes * 100)

                self.progress.emit(
                    regime_progress_base,
                    f"Optimizing {regime_id} ({current_regime_idx}/{total_regimes})..."
                )

                # Generate regime labels for this regime
                regime_labels = orchestrator._generate_sample_regime_labels(
                    sample_data, regime_id
                )

                # Set data in optimizer
                orchestrator.optimizer.set_data(sample_data, regime_labels)

                # Configure grid search with regime filtering
                config = GridSearchConfig(
                    preset=self.preset,
                    filter_by_regime=regime_id,
                    min_compatibility_score=0.7
                )

                logger.info(f"Running optimization for {regime_id} with preset '{self.preset}'")

                # Run batch optimization
                try:
                    optimization_results = orchestrator.optimizer.optimize_batch(
                        indicator_types=self.selected_indicators,
                        regime_id=regime_id,
                        config=config,
                        top_n_per_indicator=3
                    )

                    # Convert optimization results to UI format
                    for indicator_type, scores in optimization_results.items():
                        for score in scores:
                            # Convert IndicatorScore to dict format
                            result_dict = {
                                'indicator': indicator_type,
                                'params': score.parameters,
                                'regime': regime_id,
                                'score': score.composite_score * 100,  # Convert 0-1 to 0-100
                                'win_rate': score.win_rate,
                                'profit_factor': score.profit_factor,
                                'total_trades': score.total_trades,
                                'avg_return': score.avg_return * 100,  # Convert to percentage
                                'sharpe_ratio': score.sharpe_ratio,
                                'max_drawdown': score.max_drawdown
                            }
                            all_results.append(result_dict)

                except Exception as e:
                    logger.error(f"Optimization failed for {regime_id}: {e}", exc_info=True)
                    # Continue with next regime

                # Update progress
                regime_progress_end = int(current_regime_idx / total_regimes * 100)
                self.progress.emit(
                    regime_progress_end,
                    f"Completed {regime_id} - {len(all_results)} results so far"
                )

            # Store results
            self.results = all_results

            # Sort by score (descending)
            self.results.sort(key=lambda x: x['score'], reverse=True)

            # Emit completion signal
            logger.info(f"Optimization completed: {len(self.results)} total results")
            self.finished.emit(self.results)

        except Exception as e:
            error_msg = f"Optimization error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
