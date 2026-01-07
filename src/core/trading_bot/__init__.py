"""
Trading Bot Package - Automatischer Daytrading Bot für Bitunix BTCUSDT

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
"""

from .bot_config import BotConfig, AIConfig, SessionConfig
from .trade_logger import TradeLogger, TradeLogEntry, IndicatorSnapshot
from .signal_generator import SignalGenerator, TradeSignal, SignalDirection
from .risk_manager import RiskManager, RiskCalculation
from .position_monitor import PositionMonitor, MonitoredPosition, ExitResult
from .ai_validator import AISignalValidator, AIValidation, ValidationLevel
from .bot_engine import TradingBotEngine, BotState, BotStatistics

__all__ = [
    # Config
    "BotConfig",
    "AIConfig",
    "SessionConfig",
    # Logging
    "TradeLogger",
    "TradeLogEntry",
    "IndicatorSnapshot",
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
]
