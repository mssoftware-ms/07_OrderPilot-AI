"""Indicator Optimization Thread for background processing.

Runs indicator parameter optimization in the background with:
- Entry/Exit mode selection
- Long/Short side selection
- Chart data support
- Regime-based scoring (0-100)

REFACTORED (Phase 3.2.3):
- Split into 3 modules for maintainability
- Composition pattern for phase handling and result processing
- All PyQt6 signals remain in this core thread class
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal

# Import signal generator registry
from src.strategies.signal_generators import SignalGeneratorRegistry

# Import helper classes (composition pattern)
from .indicator_optimization_phases import OptimizationPhaseHandler
from .indicator_optimization_results import OptimizationResultsProcessor

logger = logging.getLogger(__name__)


class IndicatorOptimizationThread(QThread):
    """Background thread for indicator parameter optimization.

    Tests individual indicators with different parameter sets across
    different market regimes to find optimal configurations.

    Uses composition pattern with helper classes:
    - OptimizationPhaseHandler: Regime detection, parameter generation, indicator calculation
    - OptimizationResultsProcessor: Scoring, metrics, proximity calculations

    Signals:
        finished: Emitted when optimization completes with results list
        progress: Emitted during processing (percentage, status message)
        error: Emitted on errors (error message)
        regime_history_ready: Emitted when regime detection is complete with regime boundaries
    """

    finished = pyqtSignal(list)  # List[Dict] of optimization results
    progress = pyqtSignal(int, str)  # (percentage: int, message: str)
    error = pyqtSignal(str)  # error message
    regime_history_ready = pyqtSignal(list)  # List[Dict] of regime changes

    def __init__(
        self,
        selected_indicators: List[str],
        param_ranges: Dict[str, Dict[str, int]],
        json_config_path: Optional[str] = None,  # Regime config for JSON-based regime detection
        symbol: str = "",
        start_date: datetime = None,
        end_date: datetime = None,
        initial_capital: float = 10000.0,
        test_type: str = "entry",  # "entry" or "exit"
        trade_side: str = "long",  # "long" or "short"
        chart_data: Optional[pd.DataFrame] = None,
        data_timeframe: Optional[str] = None,
        parent=None
    ):
        """Initialize optimization thread.

        Args:
            selected_indicators: List of indicator types to optimize (e.g. ['RSI', 'MACD', 'ADX'])
            param_ranges: Parameter ranges for each indicator
            json_config_path: Path to JSON regime config (required for regime labels)
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            test_type: "entry" or "exit" - what phase to optimize
            trade_side: "long" or "short" - which trade direction
            chart_data: Pre-loaded chart data (optional)
            data_timeframe: Timeframe of chart data (e.g. "15m")
            parent: Parent QObject
        """
        super().__init__(parent)
        self.selected_indicators = selected_indicators
        self.param_ranges = param_ranges
        self.json_config_path = json_config_path
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.test_type = test_type
        self.trade_side = trade_side
        self.chart_data = chart_data
        self.data_timeframe = data_timeframe

        self.results: List[Dict[str, Any]] = []
        self._stop_requested = False

        # Initialize signal generator registry (Strategy Pattern)
        self._signal_registry = SignalGeneratorRegistry()

        # Composition: Helper classes for phase handling and result processing
        self.phase_handler = OptimizationPhaseHandler(self)
        self.results_processor = OptimizationResultsProcessor(self)

    def stop(self):
        """Request thread to stop."""
        self._stop_requested = True
        logger.info("Optimization stop requested")

    def run(self):
        """Main optimization loop - runs in background thread.

        Orchestrates optimization phases:
        1. Load/use chart data
        2. Detect regimes (delegates to phase_handler)
        3. Build regime history (delegates to phase_handler)
        4. Generate parameter combinations (delegates to phase_handler)
        5. Loop over indicators/params/regimes:
           - Calculate indicator (delegates to phase_handler)
           - Score indicator (delegates to results_processor)
        6. Emit results via signals

        All signal emissions happen in this method (not in helper classes).
        """
        try:
            logger.info(
                f"Starting optimization: {self.test_type} {self.trade_side} for "
                f"{len(self.selected_indicators)} indicators"
            )

            # Import required modules
            from src.backtesting.engine import BacktestEngine
            engine = BacktestEngine()

            # Load or use chart data
            if self.chart_data is not None:
                df = self.chart_data.copy()
                logger.info(
                    f"Using chart data: {len(df)} candles, "
                    f"timeframe={self.data_timeframe}"
                )
            else:
                df = engine.data_loader.load_data(
                    self.symbol, self.start_date, self.end_date
                )
                logger.info(f"Loaded {len(df)} candles from database")

            if df.empty:
                self.error.emit("No data available for optimization")
                return

            # Detect regimes across the data (JSON-based) - DELEGATES
            self.progress.emit(5, "Detecting market regimes...")
            if not self.json_config_path:
                raise RuntimeError(
                    "No regime config provided. Load a JSON regime config before optimization."
                )
            regime_labels = self.phase_handler.detect_regimes(df)

            # Build regime history (track regime changes for visualization) - DELEGATES
            regime_history = self.phase_handler.build_regime_history(df, regime_labels)
            logger.info(f"Detected {len(regime_history)} regime changes")

            # Emit regime history for visualization - SIGNAL EMISSION
            self.regime_history_ready.emit(regime_history)

            # Get unique regimes
            unique_regimes = sorted(set(regime_labels))
            logger.info(f"Found {len(unique_regimes)} unique regimes: {unique_regimes}")

            # Generate parameter combinations - DELEGATES
            param_combinations = self.phase_handler.generate_parameter_combinations()

            # Calculate REAL total: sum of all parameter lists across all indicators × regimes
            total_param_count = sum(len(params) for params in param_combinations.values())
            total_combinations = total_param_count * len(unique_regimes)

            logger.info(
                f"Testing {total_param_count} parameter combinations "
                f"({len(param_combinations)} indicators) across {len(unique_regimes)} regimes = "
                f"{total_combinations} total tests"
            )

            all_results = []
            completed = 0

            # Test each parameter combination in each regime
            for indicator_type in self.selected_indicators:
                if self._stop_requested:
                    return

                for params in param_combinations.get(indicator_type, []):
                    if self._stop_requested:
                        return

                    # Calculate indicator - DELEGATES
                    indicator_df = self.phase_handler.calculate_indicator(
                        df, indicator_type, params
                    )

                    # Test in each regime
                    for regime in unique_regimes:
                        if self._stop_requested:
                            return

                        completed += 1
                        progress_pct = int(completed / total_combinations * 100)

                        # Emit progress - SIGNAL EMISSION
                        self.progress.emit(
                            progress_pct,
                            f"Testing {indicator_type}{params} in {regime} "
                            f"({completed}/{total_combinations})"
                        )

                        # Filter data for this regime (align indices after dropna)
                        aligned_mask = regime_labels.loc[indicator_df.index] == regime
                        regime_df = indicator_df[aligned_mask]

                        if len(regime_df) < 10:  # Skip if too few bars
                            continue

                        # Score this indicator for this regime - DELEGATES
                        score_data = self.results_processor.score_indicator(
                            regime_df,
                            indicator_type,
                            params,
                            regime
                        )

                        if score_data:
                            all_results.append(score_data)

            # Sort by score (descending)
            all_results.sort(key=lambda x: x['score'], reverse=True)

            self.results = all_results
            logger.info(f"Optimization completed: {len(self.results)} results")

            # Emit results - SIGNAL EMISSION
            self.finished.emit(self.results)

        except Exception as e:
            error_msg = f"Optimization error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Emit error - SIGNAL EMISSION
            self.error.emit(error_msg)
