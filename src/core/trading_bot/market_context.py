"""
MarketContext - Single Source of Truth für alle Analyse-Konsumenten.

Dieses Modul definiert das kanonische Datenmodell, das von:
- Trading-Engine (Auto-Trade)
- AI Analyse Popup (Overview/Deep)
- Chatbot (Q&A + Chart-Zeichnung)

identisch verwendet wird.

Phase 1 der Bot-Integration: Canonical MarketContext.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class RegimeType(str, Enum):
    """Marktregime-Typen für Regime-Gates."""

    STRONG_TREND_BULL = "STRONG_TREND_BULL"
    WEAK_TREND_BULL = "WEAK_TREND_BULL"
    STRONG_TREND_BEAR = "STRONG_TREND_BEAR"
    WEAK_TREND_BEAR = "WEAK_TREND_BEAR"
    CHOP_RANGE = "CHOP_RANGE"
    VOLATILITY_EXPLOSIVE = "VOLATILITY_EXPLOSIVE"
    NEUTRAL = "NEUTRAL"


class TrendDirection(str, Enum):
    """Trend-Richtung für Multi-Timeframe Analyse."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class LevelType(str, Enum):
    """Typ eines Support/Resistance Levels."""

    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"
    PIVOT = "PIVOT"
    SWING_LOW = "SWING_LOW"
    SWING_HIGH = "SWING_HIGH"
    EMA_SUPPORT = "EMA_SUPPORT"
    EMA_RESISTANCE = "EMA_RESISTANCE"
    VOLUME_NODE = "VOLUME_NODE"


class LevelStrength(str, Enum):
    """Stärke eines Levels basierend auf Touches/Confluence."""

    WEAK = "WEAK"        # 1-2 touches
    MODERATE = "MODERATE"  # 3-4 touches
    STRONG = "STRONG"    # 5+ touches
    KEY_LEVEL = "KEY_LEVEL"  # Confluence von mehreren Methoden


class SignalStrength(str, Enum):
    """Signal-Stärke für Entry/Exit."""

    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class SetupType(str, Enum):
    """Erkannte Setup-Typen."""

    BREAKOUT = "BREAKOUT"
    PULLBACK = "PULLBACK"
    SFP = "SFP"  # Swing Failure Pattern
    MEAN_REVERSION = "MEAN_REVERSION"
    TREND_CONTINUATION = "TREND_CONTINUATION"
    RANGE_BOUNCE = "RANGE_BOUNCE"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# CANDLE SUMMARY
# =============================================================================


@dataclass
class CandleSummary:
    """
    Zusammenfassung der letzten Candle(s) für Context.

    Enthält OHLCV + abgeleitete Metriken.
    """

    timestamp: datetime
    timeframe: str  # "5m", "1h", "4h", "1d"

    # OHLCV
    open: float
    high: float
    low: float
    close: float
    volume: float

    # Abgeleitete Metriken
    body_size: float | None = None  # |close - open|
    body_percent: float | None = None  # body_size / price * 100
    upper_wick: float | None = None
    lower_wick: float | None = None
    is_bullish: bool | None = None
    is_doji: bool | None = None  # body < 10% of range

    # Range
    range_high_low: float | None = None  # high - low
    range_percent: float | None = None  # range / close * 100

    def __post_init__(self) -> None:
        """Berechne abgeleitete Metriken."""
        if self.open and self.close and self.high and self.low:
            self.body_size = abs(self.close - self.open)
            self.body_percent = (self.body_size / self.close) * 100 if self.close else None
            self.is_bullish = self.close > self.open

            if self.is_bullish:
                self.upper_wick = self.high - self.close
                self.lower_wick = self.open - self.low
            else:
                self.upper_wick = self.high - self.open
                self.lower_wick = self.close - self.low

            self.range_high_low = self.high - self.low
            self.range_percent = (self.range_high_low / self.close) * 100 if self.close else None

            # Doji: Body < 10% der Range
            if self.range_high_low > 0:
                self.is_doji = self.body_size < (self.range_high_low * 0.1)
            else:
                self.is_doji = True

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


# =============================================================================
# INDICATOR SNAPSHOT (erweitert)
# =============================================================================


@dataclass
class IndicatorSnapshot:
    """
    Snapshot aller Indikator-Werte zu einem Zeitpunkt.

    Erweitert gegenüber trade_logger.py um:
    - Trend-Alignment Score
    - Momentum-State
    - Volatility-State
    """

    timestamp: datetime
    timeframe: str = "5m"

    # === TREND INDIKATOREN ===
    ema_9: float | None = None
    ema_20: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    ema_20_distance_pct: float | None = None  # Preis-Abstand zu EMA20 in %
    ema_50_distance_pct: float | None = None

    # Trend-State basierend auf EMA-Stacking
    trend_alignment: str | None = None  # ALIGNED_BULL, ALIGNED_BEAR, MIXED

    # === MOMENTUM ===
    rsi_14: float | None = None
    rsi_state: str | None = None  # OVERBOUGHT, OVERSOLD, NEUTRAL
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    macd_crossover: str | None = None  # BULLISH, BEARISH, NONE
    macd_histogram_trend: str | None = None  # INCREASING, DECREASING, FLAT

    # Stochastic (optional)
    stoch_k: float | None = None
    stoch_d: float | None = None
    stoch_state: str | None = None  # OVERBOUGHT, OVERSOLD, NEUTRAL

    # === VOLATILITÄT ===
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_pct_b: float | None = None  # 0-1 Position in Bollinger Bands
    bb_width: float | None = None
    bb_squeeze: bool | None = None  # Width unter historischem Durchschnitt

    atr_14: float | None = None
    atr_percent: float | None = None  # ATR als % vom Preis
    volatility_state: str | None = None  # LOW, NORMAL, HIGH, EXTREME

    # === TREND STRENGTH ===
    adx_14: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None
    di_crossover: str | None = None  # BULLISH, BEARISH, NONE

    # === VOLUME ===
    volume: float | None = None
    volume_sma_20: float | None = None
    volume_ratio: float | None = None  # Aktuelles Volume / SMA
    volume_state: str | None = None  # LOW, NORMAL, HIGH

    # === PRICE ACTION ===
    current_price: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    price_change_24h_pct: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result

    def get_momentum_score(self) -> float:
        """
        Berechnet einen Momentum-Score von -1 (bearish) bis +1 (bullish).
        """
        score = 0.0
        count = 0

        # RSI Beitrag
        if self.rsi_14 is not None:
            if self.rsi_14 > 70:
                score += 1.0
            elif self.rsi_14 > 50:
                score += 0.5
            elif self.rsi_14 < 30:
                score -= 1.0
            elif self.rsi_14 < 50:
                score -= 0.5
            count += 1

        # MACD Beitrag
        if self.macd_histogram is not None:
            if self.macd_histogram > 0:
                score += 0.5 if self.macd_histogram_trend == "INCREASING" else 0.25
            else:
                score -= 0.5 if self.macd_histogram_trend == "DECREASING" else -0.25
            count += 1

        return score / count if count > 0 else 0.0


# =============================================================================
# LEVEL (Support/Resistance Zone)
# =============================================================================


@dataclass
class Level:
    """
    Einzelnes Support/Resistance Level.

    Wird von LevelEngine erzeugt und von Chart/Chatbot/Bot konsumiert.
    """

    level_id: str  # Unique ID für Referenzierung
    level_type: LevelType

    # Preis-Range (Zone statt exakter Linie)
    price_low: float
    price_high: float

    # Stärke und Metadata
    strength: LevelStrength = LevelStrength.MODERATE
    touches: int = 0  # Wie oft wurde das Level getestet
    last_touch: datetime | None = None

    # Kontext
    timeframe: str = "5m"  # Auf welchem TF erkannt
    method: str = "pivot"  # pivot, swing, volume_profile, etc.

    # Für Chatbot-Tags
    label: str | None = None  # z.B. "Daily Support", "Weekly Resistance"

    # Berechnet
    is_key_level: bool = False  # Confluence von mehreren Methoden
    distance_from_price_pct: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        if self.last_touch:
            result["last_touch"] = self.last_touch.isoformat()
        result["level_type"] = self.level_type.value
        result["strength"] = self.strength.value
        return result

    def to_chat_tag(self) -> str:
        """
        Erzeugt Chatbot-Tag Format.

        z.B. "[#Support Zone; 91038-91120]"
        """
        type_str = "Support" if self.level_type in [LevelType.SUPPORT, LevelType.SWING_LOW] else "Resistance"
        return f"[#{type_str} Zone; {self.price_low:.0f}-{self.price_high:.0f}]"

    @property
    def midpoint(self) -> float:
        """Mittelpunkt der Zone."""
        return (self.price_low + self.price_high) / 2


# =============================================================================
# LEVELS SNAPSHOT
# =============================================================================


@dataclass
class LevelsSnapshot:
    """
    Snapshot aller erkannten Levels zu einem Zeitpunkt.

    Enthält Support/Resistance Zonen sortiert nach Relevanz.
    """

    timestamp: datetime
    symbol: str
    current_price: float

    # Alle Levels
    support_levels: list[Level] = field(default_factory=list)
    resistance_levels: list[Level] = field(default_factory=list)

    # Key Levels (Top-N nach Stärke/Nähe)
    key_supports: list[Level] = field(default_factory=list)
    key_resistances: list[Level] = field(default_factory=list)

    # Nächste Levels (für schnellen Zugriff)
    nearest_support: Level | None = None
    nearest_resistance: Level | None = None

    # Range-Detektion
    in_range: bool = False
    range_high: float | None = None
    range_low: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "current_price": self.current_price,
            "support_levels": [l.to_dict() for l in self.support_levels],
            "resistance_levels": [l.to_dict() for l in self.resistance_levels],
            "key_supports": [l.to_dict() for l in self.key_supports],
            "key_resistances": [l.to_dict() for l in self.key_resistances],
            "nearest_support": self.nearest_support.to_dict() if self.nearest_support else None,
            "nearest_resistance": self.nearest_resistance.to_dict() if self.nearest_resistance else None,
            "in_range": self.in_range,
            "range_high": self.range_high,
            "range_low": self.range_low,
        }

    def get_chat_tags(self) -> list[str]:
        """Erzeugt alle Chatbot-Tags für die Key Levels."""
        tags = []
        for level in self.key_supports[:3]:  # Top 3 Supports
            tags.append(level.to_chat_tag())
        for level in self.key_resistances[:3]:  # Top 3 Resistances
            tags.append(level.to_chat_tag())
        return tags


# =============================================================================
# SIGNAL SNAPSHOT
# =============================================================================


@dataclass
class SignalSnapshot:
    """
    Snapshot eines Trading-Signals.

    Enthält Entry-Score, Confluence, Setup-Typ und Gate-Status.
    """

    timestamp: datetime
    symbol: str
    timeframe: str

    # === DIRECTION & STRENGTH ===
    direction: TrendDirection  # BULLISH, BEARISH, NEUTRAL
    strength: SignalStrength = SignalStrength.NONE

    # === ENTRY SCORE (0-100) ===
    entry_score: float = 0.0
    entry_score_components: dict[str, float] = field(default_factory=dict)

    # === CONFLUENCE (0-5) ===
    confluence_score: int = 0
    confluence_conditions_met: list[str] = field(default_factory=list)
    confluence_conditions_failed: list[str] = field(default_factory=list)

    # === SETUP TYPE ===
    setup_type: SetupType = SetupType.UNKNOWN
    setup_confidence: float = 0.0

    # === REGIME GATES ===
    regime_allows_entry: bool = True
    regime_gate_reason: str | None = None  # z.B. "CHOP_RANGE: nur Breakout erlaubt"

    # === TRIGGER ===
    trigger_type: str | None = None  # "breakout", "pullback", "sfp_reclaim"
    trigger_price: float | None = None
    trigger_confirmed: bool = False

    # === TARGETS ===
    suggested_entry: float | None = None
    suggested_sl: float | None = None
    suggested_tp: float | None = None
    risk_reward_ratio: float | None = None

    # === AI VALIDATION (später in Phase 4) ===
    ai_validated: bool = False
    ai_confidence: float | None = None
    ai_approved: bool | None = None
    ai_reasoning: str | None = None
    ai_veto: bool = False
    ai_boost: float | None = None  # Multiplikator für Score

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["direction"] = self.direction.value
        result["strength"] = self.strength.value
        result["setup_type"] = self.setup_type.value
        return result

    @property
    def is_tradeable(self) -> bool:
        """Prüft ob Signal tradeable ist (alle Gates passiert)."""
        return (
            self.strength in [SignalStrength.MODERATE, SignalStrength.STRONG]
            and self.regime_allows_entry
            and self.confluence_score >= 3
            and not self.ai_veto
        )

    def get_final_score(self) -> float:
        """
        Berechnet finalen Score inkl. AI-Boost.

        Returns:
            Score von 0-100
        """
        score = self.entry_score

        # AI Boost/Penalty
        if self.ai_boost is not None:
            score *= self.ai_boost

        # Confluence Bonus
        if self.confluence_score >= 4:
            score *= 1.1
        elif self.confluence_score >= 5:
            score *= 1.2

        return min(100.0, max(0.0, score))


# =============================================================================
# MARKET CONTEXT (Single Source of Truth)
# =============================================================================


@dataclass
class MarketContext:
    """
    Kanonischer MarketContext - Single Source of Truth.

    Wird von Trading-Engine, AI Analyse Popup und Chatbot
    identisch verwendet.

    Enthält:
    - Regime + Confidence
    - Multi-Timeframe Trends
    - Indikatoren (via IndicatorSnapshot)
    - Levels (via LevelsSnapshot)
    - Aktives Signal (via SignalSnapshot)
    - Candle-Daten (via CandleSummary)

    Wird pro Symbol/Timeframe erzeugt und gecached.
    """

    # === IDENTIFIKATION ===
    symbol: str
    timeframe: str  # Primary timeframe
    timestamp: datetime
    context_id: str = ""  # Unique Hash für Caching/Audit

    # === REGIME ===
    regime: RegimeType = RegimeType.NEUTRAL
    regime_confidence: float = 0.0  # 0-1
    regime_reason: str | None = None  # z.B. "EMA20 > EMA50, ADX > 30"

    # === MULTI-TIMEFRAME TRENDS ===
    trend_1d: TrendDirection | None = None
    trend_4h: TrendDirection | None = None
    trend_1h: TrendDirection | None = None
    trend_15m: TrendDirection | None = None
    trend_5m: TrendDirection | None = None

    # Trend-Alignment Score (-1 bis +1)
    mtf_alignment_score: float = 0.0
    mtf_aligned: bool = False  # Alle TFs in gleicher Richtung

    # === INDIKATOR SNAPSHOTS ===
    indicators_5m: IndicatorSnapshot | None = None
    indicators_1h: IndicatorSnapshot | None = None
    indicators_4h: IndicatorSnapshot | None = None
    indicators_1d: IndicatorSnapshot | None = None

    # === LEVELS ===
    levels: LevelsSnapshot | None = None

    # Quick Access
    nearest_support: float | None = None
    nearest_resistance: float | None = None
    distance_to_support_pct: float | None = None
    distance_to_resistance_pct: float | None = None

    # === AKTIVES SIGNAL ===
    signal: SignalSnapshot | None = None

    # === CANDLE DATA ===
    current_candle: CandleSummary | None = None
    previous_candles: list[CandleSummary] = field(default_factory=list)

    # === PRICE & VOLATILITY ===
    current_price: float = 0.0
    price_24h_change_pct: float = 0.0
    atr_pct: float = 0.0  # ATR als % vom Preis
    volatility_state: str = "NORMAL"  # LOW, NORMAL, HIGH, EXTREME

    # === DATA QUALITY ===
    data_fresh: bool = True
    data_freshness_seconds: int = 0
    data_quality_issues: list[str] = field(default_factory=list)

    # === METADATA ===
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = 60  # Cache TTL
    source: str = "market_context_builder"

    def __post_init__(self) -> None:
        """Generiere Context-ID falls nicht gesetzt."""
        if not self.context_id:
            self.context_id = self._generate_context_id()

    def _generate_context_id(self) -> str:
        """
        Generiert einzigartigen Hash für diesen Context.

        Basiert auf Symbol, TF, Timestamp und Key-Werten.
        """
        key_data = {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "regime": self.regime.value if isinstance(self.regime, RegimeType) else self.regime,
            "price": self.current_price,
        }
        hash_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """
        Konvertiert zu Dictionary (für JSON Export/AI Prompts).
        """
        import numpy as np
        import pandas as pd

        def convert_value(v: Any) -> Any:
            # Handle pandas Timestamp first (before datetime check)
            if isinstance(v, pd.Timestamp):
                return v.isoformat()
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, Enum):
                return v.value
            # Handle numpy types
            if isinstance(v, (np.integer, np.floating)):
                return v.item()
            if isinstance(v, np.ndarray):
                return v.tolist()
            if hasattr(v, "to_dict"):
                return v.to_dict()
            if isinstance(v, dict):
                return {k: convert_value(val) for k, val in v.items()}
            if isinstance(v, list):
                return [convert_value(item) for item in v]
            return v

        result = {}
        for key, value in asdict(self).items():
            result[key] = convert_value(value)

        return result

    def to_json(self, indent: int = 2) -> str:
        """Konvertiert zu JSON String."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_ai_prompt_context(self) -> dict:
        """
        Erzeugt kompaktes Context-Dict für AI Prompts.

        Enthält nur die relevanten Felder, keine Rohdaten.
        """
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_price": self.current_price,
            "regime": {
                "type": self.regime.value if isinstance(self.regime, RegimeType) else self.regime,
                "confidence": self.regime_confidence,
                "reason": self.regime_reason,
            },
            "trends": {
                "1d": self.trend_1d.value if self.trend_1d else None,
                "4h": self.trend_4h.value if self.trend_4h else None,
                "1h": self.trend_1h.value if self.trend_1h else None,
                "5m": self.trend_5m.value if self.trend_5m else None,
                "alignment_score": self.mtf_alignment_score,
                "aligned": self.mtf_aligned,
            },
            "levels": {
                "nearest_support": self.nearest_support,
                "nearest_resistance": self.nearest_resistance,
                "distance_to_support_pct": self.distance_to_support_pct,
                "distance_to_resistance_pct": self.distance_to_resistance_pct,
            },
            "volatility": {
                "atr_pct": self.atr_pct,
                "state": self.volatility_state,
            },
            "indicators_5m": self._get_key_indicators(self.indicators_5m),
            "signal": self._get_signal_summary(),
            "data_quality": {
                "fresh": self.data_fresh,
                "issues": self.data_quality_issues,
            },
        }

    def _get_key_indicators(self, snapshot: IndicatorSnapshot | None) -> dict | None:
        """Extrahiert Key-Indikatoren aus Snapshot."""
        if not snapshot:
            return None
        return {
            "rsi": snapshot.rsi_14,
            "rsi_state": snapshot.rsi_state,
            "macd_crossover": snapshot.macd_crossover,
            "adx": snapshot.adx_14,
            "bb_pct_b": snapshot.bb_pct_b,
            "volume_ratio": snapshot.volume_ratio,
        }

    def _get_signal_summary(self) -> dict | None:
        """Extrahiert Signal-Zusammenfassung."""
        if not self.signal:
            return None
        return {
            "direction": self.signal.direction.value,
            "strength": self.signal.strength.value,
            "entry_score": self.signal.entry_score,
            "confluence_score": self.signal.confluence_score,
            "setup_type": self.signal.setup_type.value,
            "regime_allows_entry": self.signal.regime_allows_entry,
            "is_tradeable": self.signal.is_tradeable,
        }

    def is_valid_for_trading(self) -> tuple[bool, list[str]]:
        """
        Prüft ob Context für Trading geeignet ist.

        Returns:
            Tuple von (is_valid, list_of_issues)
        """
        issues = []

        # Data Quality
        if not self.data_fresh:
            issues.append(f"Data not fresh ({self.data_freshness_seconds}s old)")

        if self.data_quality_issues:
            issues.extend(self.data_quality_issues)

        # Price Sanity
        if self.current_price <= 0:
            issues.append("Invalid current price")

        # Indicators vorhanden
        if not self.indicators_5m:
            issues.append("Missing 5m indicators")

        # Regime bekannt
        if self.regime == RegimeType.NEUTRAL and self.regime_confidence < 0.5:
            issues.append("Regime unclear")

        return len(issues) == 0, issues

    @property
    def is_bullish_regime(self) -> bool:
        """Prüft ob bullishes Regime."""
        return self.regime in [RegimeType.STRONG_TREND_BULL, RegimeType.WEAK_TREND_BULL]

    @property
    def is_bearish_regime(self) -> bool:
        """Prüft ob bearishes Regime."""
        return self.regime in [RegimeType.STRONG_TREND_BEAR, RegimeType.WEAK_TREND_BEAR]

    @property
    def is_ranging_regime(self) -> bool:
        """Prüft ob Range/Chop Regime."""
        return self.regime == RegimeType.CHOP_RANGE


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_empty_context(symbol: str, timeframe: str = "5m") -> MarketContext:
    """
    Erzeugt leeren MarketContext.

    Nützlich für Initialisierung oder Fehlerfall.
    """
    return MarketContext(
        symbol=symbol,
        timeframe=timeframe,
        timestamp=datetime.now(timezone.utc),
        data_fresh=False,
        data_quality_issues=["Empty context - no data loaded"],
    )


def create_indicator_snapshot_from_df(
    df: "pd.DataFrame",  # type: ignore
    timeframe: str = "5m",
) -> IndicatorSnapshot | None:
    """
    Erzeugt IndicatorSnapshot aus DataFrame.

    Erwartet DataFrame mit Spalten: ema_20, ema_50, rsi_14, etc.

    Args:
        df: DataFrame mit Indikatoren
        timeframe: Timeframe der Daten

    Returns:
        IndicatorSnapshot oder None bei Fehler
    """
    if df is None or df.empty:
        return None

    try:
        current = df.iloc[-1]
        timestamp = current.name if hasattr(current.name, "isoformat") else datetime.now(timezone.utc)

        # RSI State bestimmen
        rsi = current.get("rsi_14")
        rsi_state = None
        if rsi is not None:
            if rsi > 70:
                rsi_state = "OVERBOUGHT"
            elif rsi < 30:
                rsi_state = "OVERSOLD"
            else:
                rsi_state = "NEUTRAL"

        # MACD Crossover
        macd_line = current.get("macd_line")
        macd_signal = current.get("macd_signal")
        macd_crossover = None
        if macd_line is not None and macd_signal is not None:
            if macd_line > macd_signal:
                macd_crossover = "BULLISH"
            elif macd_line < macd_signal:
                macd_crossover = "BEARISH"
            else:
                macd_crossover = "NONE"

        # Volume State
        volume_ratio = current.get("volume_ratio")
        volume_state = None
        if volume_ratio is not None:
            if volume_ratio > 2.0:
                volume_state = "HIGH"
            elif volume_ratio < 0.5:
                volume_state = "LOW"
            else:
                volume_state = "NORMAL"

        # Volatility State
        atr_pct = current.get("atr_percent")
        volatility_state = None
        if atr_pct is not None:
            if atr_pct > 5.0:
                volatility_state = "EXTREME"
            elif atr_pct > 3.0:
                volatility_state = "HIGH"
            elif atr_pct < 1.0:
                volatility_state = "LOW"
            else:
                volatility_state = "NORMAL"

        return IndicatorSnapshot(
            timestamp=timestamp,
            timeframe=timeframe,
            ema_20=current.get("ema_20"),
            ema_50=current.get("ema_50"),
            ema_200=current.get("ema_200"),
            ema_20_distance_pct=current.get("ema_20_distance_pct"),
            rsi_14=rsi,
            rsi_state=rsi_state,
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_histogram=current.get("macd_histogram"),
            macd_crossover=macd_crossover,
            bb_upper=current.get("bb_upper"),
            bb_middle=current.get("bb_middle"),
            bb_lower=current.get("bb_lower"),
            bb_pct_b=current.get("bb_pct_b"),
            bb_width=current.get("bb_width"),
            atr_14=current.get("atr_14"),
            atr_percent=atr_pct,
            volatility_state=volatility_state,
            adx_14=current.get("adx_14"),
            plus_di=current.get("plus_di"),
            minus_di=current.get("minus_di"),
            volume=current.get("volume"),
            volume_sma_20=current.get("volume_sma_20"),
            volume_ratio=volume_ratio,
            volume_state=volume_state,
            current_price=current.get("close"),
        )
    except Exception as e:
        logger.error(f"Error creating IndicatorSnapshot from DataFrame: {e}")
        return None
