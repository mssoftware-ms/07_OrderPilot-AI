"""Type definitions for Visible Chart Entry Analyzer.

Contains data classes for entry events, analysis results,
and configuration objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EntrySide(str, Enum):
    """Entry direction."""

    LONG = "long"
    SHORT = "short"


class RegimeType(str, Enum):
    """Market regime classification.

    9-Level Regime Hierarchy (JSON v2.0):
    Priority 100: STRONG_TF - Extreme trend (ADX > 40, DI diff > 20)
    Priority 95:  STRONG_BULL - Strong uptrend with RSI confirmation
    Priority 94:  STRONG_BEAR - Strong downtrend with RSI confirmation
    Priority 85:  TF - Trend Following (ADX > 25)
    Priority 82:  BULL_EXHAUSTION - Uptrend exhaustion warning
    Priority 81:  BEAR_EXHAUSTION - Downtrend exhaustion warning
    Priority 80:  BULL - Uptrend (DI+ > DI-)
    Priority 79:  BEAR - Downtrend (DI- > DI+)
    Priority 50:  SIDEWAYS - Range/neutral market

    Additional states:
    - HIGH_VOL: High volatility
    - SQUEEZE: Low volatility compression
    - NO_TRADE: Avoid trading
    - UNKNOWN: Regime not determined
    """

    # 9-Level Regime Hierarchy (from JSON v2.0)
    STRONG_TF = "STRONG_TF"
    STRONG_BULL = "STRONG_BULL"
    STRONG_BEAR = "STRONG_BEAR"
    TF = "TF"
    BULL_EXHAUSTION = "BULL_EXHAUSTION"
    BEAR_EXHAUSTION = "BEAR_EXHAUSTION"
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"

    # Additional states
    HIGH_VOL = "HIGH_VOL"
    SQUEEZE = "SQUEEZE"
    NO_TRADE = "NO_TRADE"
    UNKNOWN = "UNKNOWN"

    # Legacy aliases for backwards compatibility
    TREND_UP = "BULL"
    TREND_DOWN = "BEAR"
    RANGE = "SIDEWAYS"

    @classmethod
    def from_string(cls, regime_id: str) -> "RegimeType":
        """Convert string regime ID to RegimeType enum.

        Handles dynamic regime names by pattern matching.

        Args:
            regime_id: Regime ID string (e.g., "STRONG_TF", "BULL", "MY_BULL_REGIME")

        Returns:
            Matching RegimeType enum value.
        """
        if not regime_id:
            return cls.UNKNOWN

        # Direct match first
        regime_upper = regime_id.upper()
        try:
            return cls(regime_upper)
        except ValueError:
            pass

        # Pattern matching for dynamic names
        id_lower = regime_id.lower()

        # Strong trend patterns
        if "strong" in id_lower and "tf" in id_lower:
            return cls.STRONG_TF
        if "strong" in id_lower and "bull" in id_lower:
            return cls.STRONG_BULL
        if "strong" in id_lower and "bear" in id_lower:
            return cls.STRONG_BEAR

        # Exhaustion patterns
        if "exhaust" in id_lower and "bull" in id_lower:
            return cls.BULL_EXHAUSTION
        if "exhaust" in id_lower and "bear" in id_lower:
            return cls.BEAR_EXHAUSTION

        # Trend following
        if id_lower in ("tf", "trend_following", "trend"):
            return cls.TF

        # Basic directional
        if "bull" in id_lower or "long" in id_lower or "up" in id_lower:
            return cls.BULL
        if "bear" in id_lower or "short" in id_lower or "down" in id_lower:
            return cls.BEAR

        # Sideways / Range
        if any(pat in id_lower for pat in ["sideways", "range", "neutral", "flat"]):
            return cls.SIDEWAYS

        # High volatility
        if "vol" in id_lower and "high" in id_lower:
            return cls.HIGH_VOL

        # Squeeze
        if "squeeze" in id_lower or "compress" in id_lower:
            return cls.SQUEEZE

        # Fallback
        return cls.UNKNOWN


@dataclass
class EntryEvent:
    """A detected entry signal in the visible chart.

    Attributes:
        timestamp: Unix timestamp of the candle.
        side: LONG (green) or SHORT (red).
        confidence: Score 0.0-1.0 indicating signal strength.
        price: Price at entry point (candle close or custom).
        reason_tags: List of reasons for the signal.
        regime: Market regime at the time of signal.
    """

    timestamp: int
    side: EntrySide
    confidence: float
    price: float
    reason_tags: list[str] = field(default_factory=list)
    regime: RegimeType = RegimeType.RANGE

    def to_chart_marker(self) -> dict[str, Any]:
        """Convert to TradingView Lightweight Charts marker format.

        Returns:
            Dict with time, position, color, shape, text for chart rendering.
        """
        is_long = self.side == EntrySide.LONG

        return {
            "time": self.timestamp,
            "position": "belowBar" if is_long else "aboveBar",
            "color": "#22c55e" if is_long else "#ef4444",  # green / red
            "shape": "arrowUp" if is_long else "arrowDown",
            "text": f"{self.side.value.upper()} ({self.confidence:.0%})",
            "size": 2,
        }


@dataclass
class VisibleRange:
    """Visible chart time range.

    Attributes:
        from_ts: Start timestamp (Unix seconds).
        to_ts: End timestamp (Unix seconds).
        from_idx: Logical bar index start (optional).
        to_idx: Logical bar index end (optional).
    """

    from_ts: int
    to_ts: int
    from_idx: int | None = None
    to_idx: int | None = None

    @property
    def duration_seconds(self) -> int:
        """Duration of visible range in seconds."""
        return self.to_ts - self.from_ts

    @property
    def duration_minutes(self) -> int:
        """Duration of visible range in minutes."""
        return self.duration_seconds // 60


@dataclass
class IndicatorSet:
    """Optimized indicator configuration.

    Represents a set of indicators with parameters
    selected by the optimizer for a specific regime.
    """

    name: str
    regime: RegimeType
    score: float
    parameters: dict[str, Any] = field(default_factory=dict)
    families: list[str] = field(default_factory=list)
    description: str = ""

    def to_display_dict(self) -> dict[str, Any]:
        """Convert to display format for UI."""
        return {
            "name": self.name,
            "regime": self.regime.value,
            "score": f"{self.score:.2f}",
            "families": ", ".join(self.families),
            "parameters": self.parameters,
        }


@dataclass
class AnalysisResult:
    """Result of visible chart analysis.

    Contains all entry signals, the active indicator set,
    and analysis metadata.
    """

    entries: list[EntryEvent] = field(default_factory=list)
    active_set: IndicatorSet | None = None
    alternative_sets: list[IndicatorSet] = field(default_factory=list)
    regime: RegimeType = RegimeType.RANGE
    visible_range: VisibleRange | None = None
    analysis_time_ms: float = 0.0
    candle_count: int = 0
    candles: list[dict] | None = None

    @property
    def long_count(self) -> int:
        """Number of LONG entries."""
        return sum(1 for e in self.entries if e.side == EntrySide.LONG)

    @property
    def short_count(self) -> int:
        """Number of SHORT entries."""
        return sum(1 for e in self.entries if e.side == EntrySide.SHORT)

    @property
    def signal_rate_per_hour(self) -> float:
        """Signals per hour based on visible range."""
        if not self.visible_range or self.visible_range.duration_seconds == 0:
            return 0.0
        hours = self.visible_range.duration_seconds / 3600
        return len(self.entries) / hours if hours > 0 else 0.0
