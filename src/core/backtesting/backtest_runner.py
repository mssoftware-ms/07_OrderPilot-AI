"""BacktestRunner - Core Engine für Single-Run Backtesting.

Refactored from 832 LOC monolith using composition pattern.

Module 6/6 (Main Orchestrator).

Thin orchestration layer that ties all modules together:
- BacktestRunnerLoop: Main execution loop
- BacktestRunnerPositions: Position management
- BacktestRunnerSignals: Signal generation/execution
- BacktestRunnerMetrics: Metrics calculation
- BacktestRunner (this): Thin Orchestrator

Public API:
- run(): Führt Backtest durch
- stop(): Stoppt laufenden Backtest
- set_progress_callback(): Progress-Updates
- set_signal_callback(): Custom Signal-Logik

Usage (Simplified API):
    runner = BacktestRunner(config, signal_callback=my_callback)
    result = await runner.run()

Usage (Full API):
    runner = BacktestRunner(config, replay_provider, mtf_resampler, execution_sim)
    runner.set_signal_callback(my_callback)
    result = await runner.run()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Optional

# Re-export State classes
from .backtest_runner_state import BacktestState, OpenPosition, TradeStatus

# Import helper modules
from .backtest_runner_loop import BacktestRunnerLoop
from .backtest_runner_positions import BacktestRunnerPositions
from .backtest_runner_signals import BacktestRunnerSignals
from .backtest_runner_metrics import BacktestRunnerMetrics

if TYPE_CHECKING:
    from .config import BacktestConfig, BacktestResult, CandleSnapshot
    from .execution_simulator import ExecutionSimulator
    from .mtf_resampler import MTFResampler
    from .replay_provider import ReplayMarketDataProvider

logger = logging.getLogger(__name__)


class BacktestRunner:
    """
    Core Engine für Single-Run Backtesting.

    Features:
    - Candle-by-Candle Replay (via ReplayProvider)
    - MTF Support (via MTFResampler)
    - Signal Generation (via Callback oder Strategy)
    - Trade Execution (via ExecutionSimulator)
    - Risk Management (Max Daily Loss, Max Trades, Loss Streak Cooldown)
    - Performance Metrics (Win Rate, PF, Sharpe, Drawdown, R-Multiples, etc.)

    Architektur (Composition Pattern):
    - BacktestRunnerLoop: Main execution loop
    - BacktestRunnerPositions: Position management
    - BacktestRunnerSignals: Signal generation/execution
    - BacktestRunnerMetrics: Metrics calculation
    - BacktestRunner (this): Thin Orchestrator
    """

    def __init__(
        self,
        config: "BacktestConfig",
        replay_provider: Optional["ReplayMarketDataProvider"] = None,
        mtf_resampler: Optional["MTFResampler"] = None,
        execution_sim: Optional["ExecutionSimulator"] = None,
        *,
        signal_callback: Optional[Callable] = None,
    ):
        """Initialize BacktestRunner.

        Supports two usage patterns:

        1. Simplified API (components created automatically):
           runner = BacktestRunner(config, signal_callback=my_callback)

        2. Full API (components provided):
           runner = BacktestRunner(config, replay_provider, mtf_resampler, execution_sim)
           runner.set_signal_callback(my_callback)

        Args:
            config: Backtest-Konfiguration
            replay_provider: Replay Provider für OHLCV-Daten (optional - auto-created if None)
            mtf_resampler: MTF Resampler für Multi-Timeframe Daten (optional - auto-created if None)
            execution_sim: Execution Simulator für Order-Ausführung (optional - auto-created if None)
            signal_callback: Signal callback function (keyword-only)
        """
        self.config = config

        # Create components if not provided (simplified API)
        self.replay_provider = replay_provider or self._create_replay_provider()
        self.mtf_resampler = mtf_resampler or self._create_mtf_resampler()
        self.execution_sim = execution_sim or self._create_execution_sim()

        # State (wird in run() initialisiert)
        self.state: BacktestState | None = None

        # Callbacks
        self.progress_callback: Callable[[int, str], None] | None = None
        self.signal_callback: Callable | None = signal_callback

        # Stop Flag
        self._stop_requested = False

        # Helper modules (composition pattern)
        self._loop_helper = BacktestRunnerLoop(parent=self)
        self._positions_helper = BacktestRunnerPositions(parent=self)
        self._signals_helper = BacktestRunnerSignals(parent=self)
        self._metrics_helper = BacktestRunnerMetrics(parent=self)

        logger.info(f"BacktestRunner initialized: {config.symbol} | {config.start_date} - {config.end_date}")

    def _create_replay_provider(self) -> "ReplayMarketDataProvider":
        """Create default ReplayMarketDataProvider."""
        from .replay_provider import ReplayMarketDataProvider
        return ReplayMarketDataProvider(history_window=200)

    def _create_mtf_resampler(self) -> "MTFResampler":
        """Create default MTFResampler based on config."""
        from .mtf_resampler import MTFResampler
        # Default timeframes for trading bot
        timeframes = getattr(self.config, 'mtf_timeframes', ["5m", "15m", "1h", "4h"])
        return MTFResampler(timeframes=timeframes, history_bars_per_tf=100)

    def _create_execution_sim(self) -> "ExecutionSimulator":
        """Create default ExecutionSimulator based on config."""
        from .execution_simulator import ExecutionSimulator, ExecutionConfig
        exec_config = ExecutionConfig(
            fee_rate_maker=getattr(self.config, 'fee_rate_maker', 0.0002),
            fee_rate_taker=getattr(self.config, 'fee_rate_taker', 0.0005),
            slippage_bps=getattr(self.config, 'slippage_bps', 5),
        )
        return ExecutionSimulator(config=exec_config)

    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Setzt Callback für Progress-Updates (0-100, message)."""
        self.progress_callback = callback

    def set_signal_callback(
        self,
        callback: Callable[["CandleSnapshot", list["CandleSnapshot"], dict], dict | None],
    ) -> None:
        """Setzt Callback für Signal-Generierung.

        Callback bekommt: (candle, history_1m, mtf_data)
        Callback gibt zurück: Signal-Dict oder None
        """
        self.signal_callback = callback

    async def run(self) -> "BacktestResult":
        """Führt den Backtest durch (delegiert zu loop_helper)."""
        return await self._loop_helper.run()

    def stop(self) -> None:
        """Stoppt den laufenden Backtest."""
        self._stop_requested = True
        logger.info("Stop requested")


# Re-export für backward compatibility
__all__ = [
    "BacktestRunner",
    "BacktestState",
    "OpenPosition",
    "TradeStatus",
]
