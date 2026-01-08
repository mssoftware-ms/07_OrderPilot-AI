"""
Trading Bot Package - Automatischer Daytrading Bot (Unified)

Dieses Modul stellt einen automatischen Trading Bot bereit, der:
- Nur im Paper-Modus arbeitet (Sicherheit!)
- Multi-Timeframe Analyse durchführt
- Confluence-basierte Entry/Exit Signale generiert
- ATR-basierte SL/TP mit Trailing Stop verwendet
- Optional AI-Validierung für Signale nutzt
- Detailliertes Trade-Logging für jeden Trade

Komponenten:
- BotConfig: Zentrale Konfiguration
- TradeLogger: Detailliertes Logging pro Trade
- SignalGenerator: Technische Signal-Generierung
- RiskManager: SL/TP Berechnung + Position Sizing
- PositionMonitor: Echtzeit-Überwachung + Trailing Stop
- AISignalValidator: Optional LLM-basierte Validierung
- TradingBotEngine: Haupt-Orchestrierung (State Machine)

Phase 1 Integration (MarketContext as Single Source of Truth):
- MarketContext: Kanonisches Datenmodell für alle Konsumenten
- MarketContextBuilder: Baut Context aus Rohdaten
- MarketContextCache: TTL + Hash-basierter Cache
- DataPreflightService: Zentralisierte Datenqualitätsprüfung

Phase 2 Integration (Regime & Levels):
- RegimeDetectorService: Markt-Regime Erkennung (Trend/Range/Volatile)
- LevelEngine: Support/Resistance Level Detection

Phase 3 Integration (Entry/Exit Engines):
- EntryScoreEngine: Normalisierter Entry-Score (0-1)
- TriggerExitEngine: Entry-Trigger + Exit-Management
- LeverageRulesEngine: Dynamisches Leverage-Regelwerk

Phase 4 Integration (LLM Validation):
- LLMValidationService: Quick→Deep LLM Validation
- Veto/Boost System, keine Trade-Ausführung durch LLM
"""

from .bot_config import BotConfig, AIConfig, SessionConfig
from .trade_logger import TradeLogger, TradeLogEntry
from .signal_generator import SignalGenerator, TradeSignal, SignalDirection
from .risk_manager import RiskManager, RiskCalculation
from .position_monitor import PositionMonitor, MonitoredPosition, ExitResult
from .ai_validator import AISignalValidator, AIValidation, ValidationLevel
from .bot_engine import TradingBotEngine, BotState, BotStatistics

# Phase 1 - MarketContext Integration
from .market_context import (
    MarketContext,
    IndicatorSnapshot,
    CandleSummary,
    Level,
    LevelsSnapshot,
    SignalSnapshot,
    RegimeType,
    TrendDirection,
    LevelType,
    LevelStrength,
    SignalStrength,
    SetupType,
    create_empty_context,
)
from .market_context_builder import (
    MarketContextBuilder,
    MarketContextBuilderConfig,
    build_market_context,
)
from .market_context_cache import (
    MarketContextCache,
    CacheConfig,
    CacheStats,
    get_global_cache,
    get_cached_context,
)
from .data_preflight import (
    DataPreflightService,
    PreflightResult,
    PreflightConfig,
    PreflightStatus,
    run_preflight,
    quick_validate,
)

# Phase 2 - Regime Detection
from .regime_detector import (
    RegimeDetectorService,
    RegimeResult,
    RegimeConfig,
    get_regime_detector,
    detect_regime,
)

# Phase 2.3 - Level Engine
from .level_engine import (
    LevelEngine,
    LevelEngineConfig,
    Level,
    LevelsResult,
    LevelType,
    LevelStrength,
    DetectionMethod,
    get_level_engine,
    detect_levels,
)

# Phase 3.1 - Entry Score Engine
from .entry_score_engine import (
    EntryScoreEngine,
    EntryScoreConfig,
    EntryScoreResult,
    ComponentScore,
    GateResult,
    ScoreDirection,
    ScoreQuality,
    GateStatus,
    get_entry_score_engine,
    calculate_entry_score,
    load_entry_score_config,
    save_entry_score_config,
)

# Phase 3.4-3.5 - Trigger & Exit Engine
from .trigger_exit_engine import (
    TriggerExitEngine,
    TriggerExitConfig,
    TriggerResult,
    ExitLevels,
    ExitSignal,
    TriggerType,
    ExitType,
    TriggerStatus,
    get_trigger_exit_engine,
    load_trigger_exit_config,
    save_trigger_exit_config,
)

# Phase 3.6 - Leverage Rules Engine
from .leverage_rules import (
    LeverageRulesEngine,
    LeverageRulesConfig,
    LeverageResult,
    AssetTier,
    LeverageAction,
    get_leverage_rules_engine,
    calculate_leverage,
    load_leverage_config,
    save_leverage_config,
)

# Phase 4 - LLM Validation Service
from .llm_validation_service import (
    LLMValidationService,
    LLMValidationConfig,
    LLMValidationResult,
    LLMAction,
    ValidationTier,
    get_llm_validation_service,
    validate_signal,
    load_llm_validation_config,
    save_llm_validation_config,
)

__all__ = [
    # Config
    "BotConfig",
    "AIConfig",
    "SessionConfig",
    # Logging
    "TradeLogger",
    "TradeLogEntry",
    # Signal
    "SignalGenerator",
    "TradeSignal",
    "SignalDirection",
    # Risk
    "RiskManager",
    "RiskCalculation",
    # Monitor
    "PositionMonitor",
    "MonitoredPosition",
    "ExitResult",
    # AI
    "AISignalValidator",
    "AIValidation",
    "ValidationLevel",
    # Engine
    "TradingBotEngine",
    "BotState",
    "BotStatistics",
    # === Phase 1: MarketContext ===
    # Context Schema
    "MarketContext",
    "IndicatorSnapshot",
    "CandleSummary",
    "Level",
    "LevelsSnapshot",
    "SignalSnapshot",
    # Enums
    "RegimeType",
    "TrendDirection",
    "LevelType",
    "LevelStrength",
    "SignalStrength",
    "SetupType",
    # Builder
    "MarketContextBuilder",
    "MarketContextBuilderConfig",
    "build_market_context",
    "create_empty_context",
    # Cache
    "MarketContextCache",
    "CacheConfig",
    "CacheStats",
    "get_global_cache",
    "get_cached_context",
    # Preflight
    "DataPreflightService",
    "PreflightResult",
    "PreflightConfig",
    "PreflightStatus",
    "run_preflight",
    "quick_validate",
    # === Phase 2: Regime Detection ===
    "RegimeDetectorService",
    "RegimeResult",
    "RegimeConfig",
    "get_regime_detector",
    "detect_regime",
    # === Phase 2.3: Level Engine ===
    "LevelEngine",
    "LevelEngineConfig",
    "Level",
    "LevelsResult",
    "LevelType",
    "LevelStrength",
    "DetectionMethod",
    "get_level_engine",
    "detect_levels",
    # === Phase 3.1: Entry Score Engine ===
    "EntryScoreEngine",
    "EntryScoreConfig",
    "EntryScoreResult",
    "ComponentScore",
    "GateResult",
    "ScoreDirection",
    "ScoreQuality",
    "GateStatus",
    "get_entry_score_engine",
    "calculate_entry_score",
    "load_entry_score_config",
    "save_entry_score_config",
    # === Phase 3.4-3.5: Trigger & Exit Engine ===
    "TriggerExitEngine",
    "TriggerExitConfig",
    "TriggerResult",
    "ExitLevels",
    "ExitSignal",
    "TriggerType",
    "ExitType",
    "TriggerStatus",
    "get_trigger_exit_engine",
    "load_trigger_exit_config",
    "save_trigger_exit_config",
    # === Phase 3.6: Leverage Rules ===
    "LeverageRulesEngine",
    "LeverageRulesConfig",
    "LeverageResult",
    "AssetTier",
    "LeverageAction",
    "get_leverage_rules_engine",
    "calculate_leverage",
    "load_leverage_config",
    "save_leverage_config",
    # === Phase 4: LLM Validation Service ===
    "LLMValidationService",
    "LLMValidationConfig",
    "LLMValidationResult",
    "LLMAction",
    "ValidationTier",
    "get_llm_validation_service",
    "validate_signal",
    "load_llm_validation_config",
    "save_llm_validation_config",
]
