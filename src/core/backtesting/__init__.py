"""Backtesting Module for OrderPilot-AI.

Provides comprehensive backtesting capabilities:

1. Backtrader Integration (existing):
   - BacktestEngine: Backtrader-basiertes Backtesting
   - BacktestConfig: Konfiguration für Backtrader

2. Replay-Based Backtesting (new):
   - ReplayMarketDataProvider: Candle-by-Candle Replay
   - MTFResampler: Multi-Timeframe Resampling (No-Leak)
   - ExecutionSimulator: Realistische Ausführung (Fees, Slippage, Leverage)

3. Result Models:
   - BacktestResult: Umfassendes Ergebnis-Modell
   - BacktestMetrics: Performance-Metriken
   - Trade: Einzelner Trade mit Details
"""

# Backtrader Integration (existing)
from .backtrader_integration import (
    BacktestConfig,
    BacktestEngine,
    BacktestResultLegacy,
    BACKTRADER_AVAILABLE,
)

# Import new comprehensive BacktestResult from models
from src.core.models.backtest_models import (
    BacktestMetrics,
    BacktestResult,
    Bar,
    EquityPoint,
    Trade,
    TradeSide,
)

# Replay-Based Backtesting (new)
from .replay_provider import (
    ReplayMarketDataProvider,
    CandleIterator,
    CandleSnapshot,
)

from .mtf_resampler import (
    MTFResampler,
    ResampledBar,
    TIMEFRAME_MINUTES,
)

from .execution_simulator import (
    ExecutionSimulator,
    SimulatedFill,
    SimulatedOrder,
    FeeModel,
    SlippageModel,
    OrderSide,
    OrderType,
    FillStatus,
)

from .config import (
    ExecutionConfig,
    BacktestConfig as ReplayBacktestConfig,
    BatchConfig,
    WalkForwardConfig,
    SearchMethod,
    SlippageMethod,
)

# Runners (new)
from .backtest_runner import (
    BacktestRunner,
    BacktestState,
    OpenPosition,
    TradeStatus,
)

from .batch_runner import (
    BatchRunner,
    BatchRunResult,
    BatchSummary,
)

from .walk_forward_runner import (
    WalkForwardRunner,
    FoldResult,
    WalkForwardSummary,
)

__all__ = [
    # === Backtrader Engine (existing) ===
    'BacktestConfig',
    'BacktestEngine',
    'BACKTRADER_AVAILABLE',

    # === Comprehensive Result Models ===
    'BacktestResult',
    'BacktestMetrics',
    'Bar',
    'Trade',
    'TradeSide',
    'EquityPoint',

    # === Replay-Based Backtesting (new) ===
    # Replay Provider
    'ReplayMarketDataProvider',
    'CandleIterator',
    'CandleSnapshot',

    # MTF Resampler
    'MTFResampler',
    'ResampledBar',
    'TIMEFRAME_MINUTES',

    # Execution Simulator
    'ExecutionSimulator',
    'SimulatedFill',
    'SimulatedOrder',
    'FeeModel',
    'SlippageModel',
    'OrderSide',
    'OrderType',
    'FillStatus',

    # Configuration
    'ExecutionConfig',
    'ReplayBacktestConfig',
    'BatchConfig',
    'WalkForwardConfig',
    'SearchMethod',
    'SlippageMethod',

    # === Runners (new) ===
    'BacktestRunner',
    'BacktestState',
    'OpenPosition',
    'TradeStatus',
    'BatchRunner',
    'BatchRunResult',
    'BatchSummary',
    'WalkForwardRunner',
    'FoldResult',
    'WalkForwardSummary',

    # Legacy (deprecated)
    'BacktestResultLegacy',
]
