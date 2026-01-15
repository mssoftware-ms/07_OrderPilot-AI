"""
Bot Configuration - Zentrale Konfiguration für den Trading Bot

Enthält alle konfigurierbaren Parameter für:
- Trading (Symbol, Leverage, Paper-Mode)
- Risk Management (SL/TP Multiplier, Max Loss)
- Trailing Stop
- Signal Generation (Confluence Score)
- AI Validation
- Session Management
- Logging
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Literal


@dataclass
class SessionConfig:
    """Konfiguration für Trading-Sessions (optional für Daytrading-Grenzen)."""

    enabled: bool = False  # Default: 24/7 (BTC handelt rund um die Uhr)
    start_utc: str = "08:00"  # Session Start (wenn aktiviert)
    end_utc: str = "22:00"  # Session Ende (London/NY Overlap)
    close_at_end: bool = True  # Position am Session-Ende schließen


@dataclass
class AIConfig:
    """
    Konfiguration für AI-basierte Signal-Validierung.

    WICHTIG: Provider und Model werden aus QSettings geladen!
             Einstellbar über: File -> Settings -> AI
             KEINE hardcodierten Modelle hier!
    """

    enabled: bool = False  # WICHTIG: Default FALSE um Kosten zu sparen!
    confidence_threshold: int = 70  # Minimum Confidence Score (0-100)
    fallback_to_technical: bool = True  # Trade ohne AI wenn API down
    min_confluence_for_ai: int = 4  # Minimum Confluence für AI-Call


@dataclass
class LoggingConfig:
    """Konfiguration für Trade-Logging."""

    enabled: bool = True
    log_directory: Path = field(default_factory=lambda: Path("logs/trades"))
    log_format: Literal["json", "markdown", "both"] = "both"
    include_chart_snapshot: bool = True  # Screenshot des Charts speichern
    include_indicator_values: bool = True  # Alle Indikator-Werte loggen
    include_market_context: bool = True  # Regime, Timeframes etc.
    retention_days: int = 90  # Logs nach X Tagen löschen (0 = nie)


@dataclass
class BotConfig:
    """
    Zentrale Bot-Konfiguration.

    WICHTIG: paper_mode ist IMMER True und kann NICHT geändert werden!
    Dies ist eine Sicherheitsmaßnahme um versehentliches Live-Trading zu verhindern.
    """

    # === TRADING ===
    symbol: str = "BTCUSDT"
    leverage: int = 10  # 10x Hebel

    # SICHERHEIT: Paper-Mode ist IMMER aktiv!
    # Dieses Feld existiert nur zur Dokumentation und wird IGNORIERT
    _paper_mode_locked: bool = field(default=True, repr=False)

    @property
    def paper_mode(self) -> bool:
        """Paper-Mode ist IMMER True - keine Ausnahmen!"""
        return True

    # === RISK MANAGEMENT ===
    risk_per_trade_percent: Decimal = field(
        default_factory=lambda: Decimal("1.0")
    )  # 1% Risiko pro Trade
    max_daily_loss_percent: Decimal = field(
        default_factory=lambda: Decimal("3.0")
    )  # 3% max Tagesverlust
    max_position_size_btc: Decimal = field(
        default_factory=lambda: Decimal("0.1")
    )  # Max 0.1 BTC pro Trade

    # === SL/TP (ATR-basiert) ===
    sl_atr_multiplier: Decimal = field(
        default_factory=lambda: Decimal("1.5")
    )  # Stop Loss: 1.5 * ATR
    tp_atr_multiplier: Decimal = field(
        default_factory=lambda: Decimal("2.0")
    )  # Take Profit: 2.0 * ATR

    # === TRAILING STOP ===
    trailing_stop_enabled: bool = True
    trailing_stop_atr_multiplier: Decimal = field(
        default_factory=lambda: Decimal("1.0")
    )  # Trailing: 1.0 * ATR Abstand
    trailing_stop_activation_percent: Decimal = field(
        default_factory=lambda: Decimal("0.5")
    )  # Aktivierung bei 0.5% Profit

    # === SIGNAL GENERATION ===
    min_confluence_score: int = 3  # Mindestens 3 von 5 Bedingungen müssen erfüllt sein
    require_regime_alignment: bool = True  # Regime muss zum Signal passen

    # === TIMING ===
    analysis_interval_seconds: int = 60  # Hauptanalyse alle 60 Sekunden
    position_check_interval_ms: int = 1000  # SL/TP Check jede Sekunde
    macro_update_interval_minutes: int = 60  # 1D/4h Daten alle 60 Min
    trend_update_interval_minutes: int = 15  # 4h/1h Daten alle 15 Min

    # === SUB-CONFIGS ===
    session: SessionConfig = field(default_factory=SessionConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        # Stelle sicher dass Log-Verzeichnis existiert
        if self.logging.enabled:
            self.logging.log_directory.mkdir(parents=True, exist_ok=True)

        # Validiere Werte - großzügige Grenzen, User entscheidet
        if self.min_confluence_score < 1:
            raise ValueError("min_confluence_score muss mindestens 1 sein")

        if self.leverage < 1 or self.leverage > 1000:
            raise ValueError("leverage muss zwischen 1 und 1000 liegen")

        if self.ai.confidence_threshold < 0 or self.ai.confidence_threshold > 100:
            raise ValueError("ai.confidence_threshold muss zwischen 0 und 100 liegen")

    def to_dict(self) -> dict:
        """Konvertiert Config zu Dictionary (für Logging)."""
        return {
            "symbol": self.symbol,
            "leverage": self.leverage,
            "paper_mode": self.paper_mode,  # Immer True
            "risk_per_trade_percent": str(self.risk_per_trade_percent),
            "max_daily_loss_percent": str(self.max_daily_loss_percent),
            "sl_atr_multiplier": str(self.sl_atr_multiplier),
            "tp_atr_multiplier": str(self.tp_atr_multiplier),
            "trailing_stop_enabled": self.trailing_stop_enabled,
            "trailing_stop_atr_multiplier": str(self.trailing_stop_atr_multiplier),
            "min_confluence_score": self.min_confluence_score,
            "analysis_interval_seconds": self.analysis_interval_seconds,
            "session": {
                "enabled": self.session.enabled,
                "start_utc": self.session.start_utc,
                "end_utc": self.session.end_utc,
                "close_at_end": self.session.close_at_end,
            },
            "ai": {
                "enabled": self.ai.enabled,
                "confidence_threshold": self.ai.confidence_threshold,
                "min_confluence_for_ai": self.ai.min_confluence_for_ai,
                "_note": "Provider und Model werden aus QSettings geladen (File -> Settings -> AI)",
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> BotConfig:
        """Erstellt Config aus Dictionary."""
        # Kopie erstellen um Original nicht zu verändern
        data = data.copy()

        # Entferne read-only Properties
        data.pop("paper_mode", None)

        session_data = data.pop("session", {})
        ai_data = data.pop("ai", {})
        logging_data = data.pop("logging", {})

        # Konvertiere Decimal-Felder
        decimal_fields = [
            "risk_per_trade_percent",
            "max_daily_loss_percent",
            "max_position_size_btc",
            "sl_atr_multiplier",
            "tp_atr_multiplier",
            "trailing_stop_atr_multiplier",
            "trailing_stop_activation_percent",
        ]

        for field_name in decimal_fields:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = Decimal(data[field_name])

        return cls(
            **data,
            session=SessionConfig(**session_data) if session_data else SessionConfig(),
            ai=AIConfig(**ai_data) if ai_data else AIConfig(),
            logging=LoggingConfig(**logging_data)
            if logging_data
            else LoggingConfig(),
        )


# Default-Konfiguration für schnellen Start
DEFAULT_CONFIG = BotConfig()
