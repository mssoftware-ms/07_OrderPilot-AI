"""Backtest Harness for Tradingbot (REFACTORED).

Main backtesting class that provides:
- Deterministic backtesting
- Multi-timeframe data support
- Event-by-event simulation
- Comprehensive metrics collection

REFACTORED: Split into focused helper modules using composition pattern.
- backtest_types.py: Data types (BacktestMode, BacktestConfig, etc.)
- backtest_simulator.py: BacktestSimulator + ReleaseGate
- backtest_harness_data_loader.py: Historical data loading
- backtest_harness_runner.py: Main backtest loop
- backtest_harness_bar_processor.py: Bar processing + 3 state methods
- backtest_harness_execution.py: Order execution + position management
- backtest_harness_helpers.py: Calculation utilities
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pandas as pd

from .backtest_simulator import BacktestSimulator
from .backtest_types import (
    BacktestMode,
    BacktestConfig,
    BacktestTrade,
    BacktestState,
    BacktestResult,
)
from .config import FullBotConfig

# Import helpers
from .backtest_harness_data_loader import BacktestHarnessDataLoader
from .backtest_harness_runner import BacktestHarnessRunner
from .backtest_harness_bar_processor import BacktestHarnessBarProcessor
from .backtest_harness_execution import BacktestHarnessExecution
from .backtest_harness_helpers import BacktestHarnessHelpers

if TYPE_CHECKING:
    from .bot_controller import BotController

logger = logging.getLogger(__name__)


class BacktestHarness:
    """Main backtest harness for tradingbot (REFACTORED).

    Runs event-by-event backtests with full bot simulation.
    """

    def __init__(
        self,
        bot_config: FullBotConfig,
        backtest_config: BacktestConfig,
        data_provider: Callable[[str, datetime, datetime, str], pd.DataFrame] | None = None
    ):
        """Initialize backtest harness.

        Args:
            bot_config: Bot configuration
            backtest_config: Backtest configuration
            data_provider: Function to fetch historical data
        """
        self.bot_config = bot_config
        self.backtest_config = backtest_config
        self._data_provider = data_provider

        # Initialize components
        self._seed = backtest_config.get_seed()
        self._simulator = BacktestSimulator(
            slippage_pct=backtest_config.slippage_pct,
            commission_pct=backtest_config.commission_pct,
            seed=self._seed
        )

        self._state = BacktestState(capital=backtest_config.initial_capital)
        self._data: pd.DataFrame | None = None

        # Bot components (lazy initialized)
        self._feature_engine = None
        self._regime_engine = None
        self._entry_scorer = None
        self._exit_checker = None
        self._trailing_manager = None
        self._no_trade_filter = None
        self._strategy_selector = None

        # Create helpers (composition pattern)
        self._data_loader = BacktestHarnessDataLoader(self)
        self._runner = BacktestHarnessRunner(self)
        self._bar_processor = BacktestHarnessBarProcessor(self)
        self._execution = BacktestHarnessExecution(self)
        self._helpers = BacktestHarnessHelpers(self)

        logger.info(
            f"BacktestHarness initialized: {backtest_config.symbol} "
            f"from {backtest_config.start_date} to {backtest_config.end_date}, "
            f"seed={self._seed}"
        )

    def _init_bot_components(self) -> None:
        """Initialize bot components."""
        from .feature_engine import FeatureEngine
        from .regime_engine import RegimeEngine
        from .entry_exit_engine import EntryScorer, ExitSignalChecker, TrailingStopManager
        from .no_trade_filter import NoTradeFilter
        from .strategy_selector import StrategySelector

        self._feature_engine = FeatureEngine()
        self._regime_engine = RegimeEngine()
        self._entry_scorer = EntryScorer()
        self._exit_checker = ExitSignalChecker()
        self._trailing_manager = TrailingStopManager(
            activation_pct=self.bot_config.risk.trailing_activation_pct
        )
        self._no_trade_filter = NoTradeFilter(self.bot_config.risk)
        self._strategy_selector = StrategySelector()

    # === Data Loading (Delegiert) ===

    def load_data(self) -> pd.DataFrame:
        """Load historical data for backtest (delegiert)."""
        return self._data_loader.load_data()

    # === Main Runner (Delegiert) ===

    def run(self) -> BacktestResult:
        """Run the backtest (delegiert)."""
        return self._runner.run()
