"""OrderPilot-AI Tradingbot Module.

Provides automated trading capabilities with:
- State machine-based operation
- Rule-based and LLM-assisted decisions
- Multiple trailing stop strategies
- Daily strategy selection with walk-forward validation
- Feature and regime engines for data pipeline

Usage:
    from src.core.tradingbot import BotController, FullBotConfig

    config = FullBotConfig.create_default("BTC/USD", MarketType.CRYPTO)
    bot = BotController(config)
    await bot.start()
"""

from .config import (
    BotConfig,
    FullBotConfig,
    KIMode,
    LLMPolicyConfig,
    MarketType,
    RiskConfig,
    TrailingMode,
    TradingEnvironment,
)
from .feature_engine import FeatureEngine
from .models import (
    BotAction,
    BotDecision,
    FeatureVector,
    LLMBotResponse,
    OrderIntent,
    PositionState,
    RegimeState,
    RegimeType,
    Signal,
    SignalType,
    StrategyProfile,
    TradeSide,
    TrailingState,
    VolatilityLevel,
)
from .no_trade_filter import FilterReason, FilterResult, NoTradeFilter, TradingSession
from .regime_engine import RegimeEngine
from .state_machine import (
    BotState,
    BotStateMachine,
    BotTrigger,
    InvalidTransitionError,
    StateMachineError,
    StateTransition,
)
from .strategy_catalog import (
    EntryRule,
    ExitRule,
    StrategyCatalog,
    StrategyDefinition,
    StrategyType,
)
from .strategy_evaluator import (
    PerformanceMetrics,
    RobustnessGate,
    StrategyEvaluator,
    TradeResult,
    WalkForwardConfig,
    WalkForwardResult,
)
from .strategy_selector import (
    SelectionResult,
    SelectionSnapshot,
    StrategySelector,
)
from .entry_exit_engine import (
    EntryExitEngine,
    EntryScoreResult,
    EntryScorer,
    ExitReason,
    ExitSignalChecker,
    ExitSignalResult,
    TrailingStopManager,
    TrailingStopResult,
)
from .execution import (
    ExecutionGuardrails,
    OrderExecutor,
    OrderResult,
    OrderStatus,
    OrderType,
    PaperExecutor,
    PositionSizeResult,
    PositionSizer,
    RiskLimits,
    RiskManager,
    RiskState,
)
from .llm_integration import (
    LLMBudgetState,
    LLMCallRecord,
    LLMCallType,
    LLMIntegration,
    LLMPromptBuilder,
    LLMResponseValidator,
)
from .backtest_harness import (
    BacktestConfig,
    BacktestHarness,
    BacktestMode,
    BacktestResult,
    BacktestSimulator,
    BacktestState,
    BacktestTrade,
    ReleaseGate,
)

__all__ = [
    # Config
    "BotConfig",
    "FullBotConfig",
    "KIMode",
    "LLMPolicyConfig",
    "MarketType",
    "RiskConfig",
    "TrailingMode",
    "TradingEnvironment",
    # Engines
    "FeatureEngine",
    "RegimeEngine",
    # Filters
    "FilterReason",
    "FilterResult",
    "NoTradeFilter",
    "TradingSession",
    # Models
    "BotAction",
    "BotDecision",
    "FeatureVector",
    "LLMBotResponse",
    "OrderIntent",
    "PositionState",
    "RegimeState",
    "RegimeType",
    "Signal",
    "SignalType",
    "StrategyProfile",
    "TradeSide",
    "TrailingState",
    "VolatilityLevel",
    # State Machine
    "BotState",
    "BotStateMachine",
    "BotTrigger",
    "InvalidTransitionError",
    "StateMachineError",
    "StateTransition",
    # Strategy Catalog
    "EntryRule",
    "ExitRule",
    "StrategyCatalog",
    "StrategyDefinition",
    "StrategyType",
    # Strategy Evaluator
    "PerformanceMetrics",
    "RobustnessGate",
    "StrategyEvaluator",
    "TradeResult",
    "WalkForwardConfig",
    "WalkForwardResult",
    # Strategy Selector
    "SelectionResult",
    "SelectionSnapshot",
    "StrategySelector",
    # Entry/Exit Engine
    "EntryExitEngine",
    "EntryScoreResult",
    "EntryScorer",
    "ExitReason",
    "ExitSignalChecker",
    "ExitSignalResult",
    "TrailingStopManager",
    "TrailingStopResult",
    # Execution Layer
    "ExecutionGuardrails",
    "OrderExecutor",
    "OrderResult",
    "OrderStatus",
    "OrderType",
    "PaperExecutor",
    "PositionSizeResult",
    "PositionSizer",
    "RiskLimits",
    "RiskManager",
    "RiskState",
    # LLM Integration
    "LLMBudgetState",
    "LLMCallRecord",
    "LLMCallType",
    "LLMIntegration",
    "LLMPromptBuilder",
    "LLMResponseValidator",
    # Backtest & QA
    "BacktestConfig",
    "BacktestHarness",
    "BacktestMode",
    "BacktestResult",
    "BacktestSimulator",
    "BacktestState",
    "BacktestTrade",
    "ReleaseGate",
]
