"""Trade Logger State - Enums and Simple Dataclasses.

Refactored from 735 LOC monolith using composition pattern.

Module 1/4 of trade_logger.py split.

Contains:
- TradeOutcome enum (WIN, LOSS, BREAKEVEN, OPEN)
- ExitReason enum (STOP_LOSS, TAKE_PROFIT, etc.)
- IndicatorSnapshot dataclass
- MarketContext dataclass
- SignalDetails dataclass
- TrailingStopHistory dataclass
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum


class TradeOutcome(str, Enum):
    """Ergebnis eines Trades."""

    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    OPEN = "OPEN"  # Trade noch offen


class ExitReason(str, Enum):
    """Grund für Trade-Exit."""

    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    SIGNAL_EXIT = "SIGNAL_EXIT"  # Von ExitTrigger - Signal-basierter Exit
    SIGNAL_REVERSAL = "SIGNAL_REVERSAL"  # Alias für Kompatibilität
    SESSION_END = "SESSION_END"
    MANUAL = "MANUAL"  # Von ExitTrigger
    MANUAL_CLOSE = "MANUAL_CLOSE"  # Alias für Kompatibilität
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"  # Von ExitTrigger
    MAX_DAILY_LOSS = "MAX_DAILY_LOSS"  # Alias für Kompatibilität
    BOT_STOPPED = "BOT_STOPPED"


@dataclass
class IndicatorSnapshot:
    """Snapshot aller Indikator-Werte zu einem Zeitpunkt."""

    timestamp: datetime

    # Trend Indikatoren
    ema_20: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    ema_20_distance_pct: float | None = None  # Preis-Abstand zu EMA20 in %

    # Momentum
    rsi_14: float | None = None
    rsi_state: str | None = None  # OVERBOUGHT, OVERSOLD, NEUTRAL
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    macd_crossover: str | None = None  # BULLISH, BEARISH, NONE

    # Volatility
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_pct_b: float | None = None  # 0-1 Position in Bollinger Bands
    bb_width: float | None = None
    atr_14: float | None = None
    atr_percent: float | None = None  # ATR als % vom Preis

    # Trend Strength
    adx_14: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None

    # Volume
    volume: float | None = None
    volume_sma_20: float | None = None
    volume_ratio: float | None = None  # Aktuelles Volume / SMA

    # Price Action
    current_price: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class MarketContext:
    """Marktkontext zum Zeitpunkt des Trades."""

    regime: str  # STRONG_TREND_BULL, STRONG_TREND_BEAR, CHOP_RANGE, etc.
    regime_confidence: float | None = None

    # Multi-Timeframe Trends
    trend_1d: str | None = None  # BULLISH, BEARISH, NEUTRAL
    trend_4h: str | None = None
    trend_1h: str | None = None
    trend_5m: str | None = None

    # Support/Resistance
    nearest_support: float | None = None
    nearest_resistance: float | None = None
    distance_to_support_pct: float | None = None
    distance_to_resistance_pct: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return asdict(self)


@dataclass
class SignalDetails:
    """Details zur Signal-Generierung."""

    direction: str  # LONG, SHORT
    confluence_score: int  # 0-5
    conditions_met: list[str] = field(default_factory=list)
    conditions_failed: list[str] = field(default_factory=list)

    # AI Validation (wenn aktiviert)
    ai_enabled: bool = False
    ai_confidence: int | None = None
    ai_approved: bool | None = None
    ai_reasoning: str | None = None
    ai_setup_type: str | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return asdict(self)


@dataclass
class TrailingStopHistory:
    """Historie der Trailing-Stop Anpassungen."""

    timestamp: datetime
    old_sl: float
    new_sl: float
    trigger_price: float
    reason: str = "price_moved_favorably"

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result
