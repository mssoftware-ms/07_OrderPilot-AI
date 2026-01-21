"""Pattern Recognition for Market Analysis.

Detects chart patterns, market structure, and volatility regimes
to inform AI-based strategy generation.

Phase 6: AI Analysis Integration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Enums & Models
# ─────────────────────────────────────────────────────────────────


class PatternType(str, Enum):
    """Chart pattern types."""

    # Reversal Patterns
    HEAD_AND_SHOULDERS = "head_and_shoulders"
    INVERSE_HEAD_AND_SHOULDERS = "inverse_head_and_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"

    # Continuation Patterns
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    WEDGE_RISING = "wedge_rising"
    WEDGE_FALLING = "wedge_falling"

    # Candlestick Patterns
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    DOJI = "doji"
    ENGULFING_BULL = "engulfing_bull"
    ENGULFING_BEAR = "engulfing_bear"


class MarketPhase(str, Enum):
    """Market structure phases."""

    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    CHOPPY = "choppy"
    TRANSITION = "transition"


class VolatilityRegime(str, Enum):
    """Volatility regimes."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class Pattern:
    """Detected chart pattern."""

    type: PatternType
    confidence: float  # 0.0 - 1.0
    start_idx: int  # Index in DataFrame
    end_idx: int
    description: str
    metadata: dict[str, Any] | None = None


class MarketStructure(BaseModel):
    """Market structure analysis."""

    phase: MarketPhase = Field(description="Current market phase")
    confidence: float = Field(ge=0, le=1, description="Confidence in phase detection")
    trend_strength: float = Field(ge=0, le=1, description="Trend strength (ADX-like)")
    support_levels: list[float] = Field(default_factory=list, description="Key support levels")
    resistance_levels: list[float] = Field(default_factory=list, description="Key resistance levels")
    notes: str = Field(default="", description="Additional observations")


class VolatilityAnalysis(BaseModel):
    """Volatility regime analysis."""

    regime: VolatilityRegime = Field(description="Current volatility regime")
    atr_percentile: float = Field(ge=0, le=100, description="ATR percentile (0-100)")
    recent_volatility: float = Field(ge=0, description="Recent volatility measure")
    trend: str = Field(description="Volatility trend: increasing, decreasing, stable")


# ─────────────────────────────────────────────────────────────────
# Pattern Recognizer
# ─────────────────────────────────────────────────────────────────


class PatternRecognizer:
    """Detect market patterns for regime classification.

    Usage:
        recognizer = PatternRecognizer()
        patterns = recognizer.detect_chart_patterns(df)
        structure = recognizer.detect_market_structure(df)
        volatility = recognizer.classify_volatility_regime(df)
    """

    def __init__(self, lookback_periods: int = 50) -> None:
        """Initialize pattern recognizer.

        Args:
            lookback_periods: Number of periods to analyze for patterns.
        """
        self.lookback_periods = lookback_periods

    def detect_chart_patterns(self, df: pd.DataFrame) -> list[Pattern]:
        """Detect chart patterns in OHLCV data.

        Args:
            df: DataFrame with columns: open, high, low, close, volume

        Returns:
            List of detected patterns.
        """
        if len(df) < self.lookback_periods:
            logger.warning("Insufficient data for pattern detection")
            return []

        patterns = []

        # Detect double top/bottom
        patterns.extend(self._detect_double_patterns(df))

        # Detect triangles
        patterns.extend(self._detect_triangles(df))

        # Detect candlestick patterns
        patterns.extend(self._detect_candlestick_patterns(df))

        # Detect flags and wedges
        patterns.extend(self._detect_flags_wedges(df))

        logger.info("Detected %d patterns", len(patterns))
        return patterns

    def detect_market_structure(self, df: pd.DataFrame) -> MarketStructure:
        """Detect market structure and phase.

        Args:
            df: DataFrame with OHLCV data.

        Returns:
            MarketStructure with phase and key levels.
        """
        if len(df) < 20:
            return MarketStructure(
                phase=MarketPhase.CHOPPY,
                confidence=0.5,
                trend_strength=0.0,
                notes="Insufficient data for structure analysis",
            )

        # Calculate trend strength using linear regression
        closes = df["close"].values[-self.lookback_periods :]
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)

        # Normalize slope to trend strength
        price_range = closes.max() - closes.min()
        trend_strength = min(abs(slope) / (price_range / len(closes)), 1.0)

        # Determine phase
        phase = self._classify_market_phase(df, slope, trend_strength)

        # Find support/resistance levels
        support, resistance = self._find_key_levels(df)

        # Calculate confidence based on consistency
        confidence = self._calculate_structure_confidence(df, phase)

        return MarketStructure(
            phase=phase,
            confidence=confidence,
            trend_strength=trend_strength,
            support_levels=support,
            resistance_levels=resistance,
            notes=f"Slope: {slope:.4f}, Strength: {trend_strength:.2f}",
        )

    def classify_volatility_regime(self, df: pd.DataFrame) -> VolatilityAnalysis:
        """Classify volatility regime.

        Args:
            df: DataFrame with OHLCV data.

        Returns:
            VolatilityAnalysis with regime classification.
        """
        if len(df) < 20:
            return VolatilityAnalysis(
                regime=VolatilityRegime.NORMAL,
                atr_percentile=50.0,
                recent_volatility=0.0,
                trend="unknown",
            )

        # Calculate ATR-based volatility
        atr = self._calculate_atr(df)
        atr_percentile = self._calculate_percentile(atr.values, atr.iloc[-1])

        # Classify regime
        regime = self._classify_volatility_regime(atr_percentile)

        # Detect trend in volatility
        vol_trend = self._detect_volatility_trend(atr)

        return VolatilityAnalysis(
            regime=regime,
            atr_percentile=atr_percentile,
            recent_volatility=float(atr.iloc[-1]),
            trend=vol_trend,
        )

    # ─────────────────────────────────────────────────────────────────
    # Pattern Detection Methods
    # ─────────────────────────────────────────────────────────────────

    def _detect_double_patterns(self, df: pd.DataFrame) -> list[Pattern]:
        """Detect double top and double bottom patterns."""
        patterns = []
        highs = df["high"].values[-self.lookback_periods :]
        lows = df["low"].values[-self.lookback_periods :]

        # Find local extrema
        high_peaks = self._find_peaks(highs, threshold=0.02)
        low_peaks = self._find_peaks(-lows, threshold=0.02)

        # Check for double tops (two peaks at similar levels)
        for i in range(len(high_peaks) - 1):
            for j in range(i + 1, min(i + 5, len(high_peaks))):
                peak1_idx, peak1_val = high_peaks[i]
                peak2_idx, peak2_val = high_peaks[j]

                # Check if peaks are similar (within 2%)
                if abs(peak1_val - peak2_val) / peak1_val < 0.02:
                    confidence = 0.7 + (0.3 * (1 - abs(peak1_val - peak2_val) / peak1_val / 0.02))
                    patterns.append(
                        Pattern(
                            type=PatternType.DOUBLE_TOP,
                            confidence=min(confidence, 1.0),
                            start_idx=len(df) - self.lookback_periods + peak1_idx,
                            end_idx=len(df) - self.lookback_periods + peak2_idx,
                            description=f"Double top at {peak1_val:.2f}",
                            metadata={"peak1": peak1_val, "peak2": peak2_val},
                        )
                    )

        # Check for double bottoms
        for i in range(len(low_peaks) - 1):
            for j in range(i + 1, min(i + 5, len(low_peaks))):
                peak1_idx, peak1_val = low_peaks[i]
                peak2_idx, peak2_val = low_peaks[j]

                if abs(peak1_val - peak2_val) / abs(peak1_val) < 0.02:
                    confidence = 0.7 + (0.3 * (1 - abs(peak1_val - peak2_val) / abs(peak1_val) / 0.02))
                    patterns.append(
                        Pattern(
                            type=PatternType.DOUBLE_BOTTOM,
                            confidence=min(confidence, 1.0),
                            start_idx=len(df) - self.lookback_periods + peak1_idx,
                            end_idx=len(df) - self.lookback_periods + peak2_idx,
                            description=f"Double bottom at {-peak1_val:.2f}",
                            metadata={"trough1": -peak1_val, "trough2": -peak2_val},
                        )
                    )

        return patterns

    def _detect_triangles(self, df: pd.DataFrame) -> list[Pattern]:
        """Detect triangle patterns (ascending, descending, symmetrical)."""
        patterns = []
        highs = df["high"].values[-self.lookback_periods :]
        lows = df["low"].values[-self.lookback_periods :]

        # Find trend lines for highs and lows
        high_slope = self._fit_trendline(highs)
        low_slope = self._fit_trendline(lows)

        # Classify triangle type based on slopes
        if abs(high_slope) < 0.001 and low_slope > 0.005:
            # Ascending triangle (flat top, rising bottom)
            patterns.append(
                Pattern(
                    type=PatternType.ASCENDING_TRIANGLE,
                    confidence=0.7,
                    start_idx=len(df) - self.lookback_periods,
                    end_idx=len(df) - 1,
                    description="Ascending triangle (bullish continuation)",
                    metadata={"high_slope": high_slope, "low_slope": low_slope},
                )
            )
        elif high_slope < -0.005 and abs(low_slope) < 0.001:
            # Descending triangle (declining top, flat bottom)
            patterns.append(
                Pattern(
                    type=PatternType.DESCENDING_TRIANGLE,
                    confidence=0.7,
                    start_idx=len(df) - self.lookback_periods,
                    end_idx=len(df) - 1,
                    description="Descending triangle (bearish continuation)",
                    metadata={"high_slope": high_slope, "low_slope": low_slope},
                )
            )
        elif high_slope < -0.002 and low_slope > 0.002:
            # Symmetrical triangle (converging lines)
            patterns.append(
                Pattern(
                    type=PatternType.SYMMETRICAL_TRIANGLE,
                    confidence=0.6,
                    start_idx=len(df) - self.lookback_periods,
                    end_idx=len(df) - 1,
                    description="Symmetrical triangle (neutral, breakout pending)",
                    metadata={"high_slope": high_slope, "low_slope": low_slope},
                )
            )

        return patterns

    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> list[Pattern]:
        """Detect single and multi-candle patterns."""
        patterns = []

        if len(df) < 3:
            return patterns

        # Get last few candles
        recent = df.tail(3)

        # Hammer (bullish reversal)
        last = recent.iloc[-1]
        body = abs(last["close"] - last["open"])
        total_range = last["high"] - last["low"]
        lower_shadow = min(last["open"], last["close"]) - last["low"]

        if total_range > 0:
            if lower_shadow > 2 * body and body / total_range < 0.3:
                patterns.append(
                    Pattern(
                        type=PatternType.HAMMER,
                        confidence=0.75,
                        start_idx=len(df) - 1,
                        end_idx=len(df) - 1,
                        description="Hammer (potential bullish reversal)",
                    )
                )

        # Doji (indecision)
        if body / total_range < 0.1 and total_range > 0:
            patterns.append(
                Pattern(
                    type=PatternType.DOJI,
                    confidence=0.6,
                    start_idx=len(df) - 1,
                    end_idx=len(df) - 1,
                    description="Doji (market indecision)",
                )
            )

        # Engulfing patterns (requires 2 candles)
        if len(recent) >= 2:
            prev = recent.iloc[-2]
            curr = recent.iloc[-1]

            prev_body = abs(prev["close"] - prev["open"])
            curr_body = abs(curr["close"] - curr["open"])

            # Bullish engulfing
            if (
                prev["close"] < prev["open"]
                and curr["close"] > curr["open"]
                and curr["open"] < prev["close"]
                and curr["close"] > prev["open"]
                and curr_body > prev_body
            ):
                patterns.append(
                    Pattern(
                        type=PatternType.ENGULFING_BULL,
                        confidence=0.8,
                        start_idx=len(df) - 2,
                        end_idx=len(df) - 1,
                        description="Bullish engulfing (strong reversal signal)",
                    )
                )

            # Bearish engulfing
            if (
                prev["close"] > prev["open"]
                and curr["close"] < curr["open"]
                and curr["open"] > prev["close"]
                and curr["close"] < prev["open"]
                and curr_body > prev_body
            ):
                patterns.append(
                    Pattern(
                        type=PatternType.ENGULFING_BEAR,
                        confidence=0.8,
                        start_idx=len(df) - 2,
                        end_idx=len(df) - 1,
                        description="Bearish engulfing (strong reversal signal)",
                    )
                )

        return patterns

    def _detect_flags_wedges(self, df: pd.DataFrame) -> list[Pattern]:
        """Detect flag and wedge patterns."""
        patterns = []

        if len(df) < 20:
            return patterns

        # Analyze recent trend before potential flag
        closes = df["close"].values[-self.lookback_periods :]
        trend_slope = self._fit_trendline(closes[-20:])

        # Check for consolidation after strong move
        recent_range = closes[-10:].max() - closes[-10:].min()
        prior_range = closes[-20:-10].max() - closes[-20:-10].min()

        if recent_range < prior_range * 0.5:
            # Consolidation detected, check trend direction
            if trend_slope > 0.01:
                patterns.append(
                    Pattern(
                        type=PatternType.BULL_FLAG,
                        confidence=0.65,
                        start_idx=len(df) - 20,
                        end_idx=len(df) - 1,
                        description="Bull flag (bullish continuation)",
                        metadata={"trend_slope": trend_slope},
                    )
                )
            elif trend_slope < -0.01:
                patterns.append(
                    Pattern(
                        type=PatternType.BEAR_FLAG,
                        confidence=0.65,
                        start_idx=len(df) - 20,
                        end_idx=len(df) - 1,
                        description="Bear flag (bearish continuation)",
                        metadata={"trend_slope": trend_slope},
                    )
                )

        return patterns

    # ─────────────────────────────────────────────────────────────────
    # Market Structure Methods
    # ─────────────────────────────────────────────────────────────────

    def _classify_market_phase(
        self, df: pd.DataFrame, slope: float, trend_strength: float
    ) -> MarketPhase:
        """Classify market phase based on trend analysis."""
        # Strong trending conditions
        if trend_strength > 0.6:
            return MarketPhase.TRENDING_UP if slope > 0 else MarketPhase.TRENDING_DOWN

        # Check for ranging behavior
        closes = df["close"].values[-self.lookback_periods :]
        price_range = closes.max() - closes.min()
        avg_price = closes.mean()

        # If price stays within tight range, it's ranging
        if price_range / avg_price < 0.03:
            return MarketPhase.RANGING

        # Check choppiness (frequent direction changes)
        changes = np.diff(closes)
        direction_changes = np.sum(np.diff(np.sign(changes)) != 0)
        change_ratio = direction_changes / len(changes)

        if change_ratio > 0.4:
            return MarketPhase.CHOPPY

        # Default to transition
        return MarketPhase.TRANSITION

    def _find_key_levels(
        self, df: pd.DataFrame
    ) -> tuple[list[float], list[float]]:
        """Find support and resistance levels."""
        highs = df["high"].values[-self.lookback_periods :]
        lows = df["low"].values[-self.lookback_periods :]

        # Find peaks for resistance
        resistance_peaks = self._find_peaks(highs, threshold=0.02)
        resistance = [val for _, val in resistance_peaks[-3:]]

        # Find troughs for support
        support_peaks = self._find_peaks(-lows, threshold=0.02)
        support = [-val for _, val in support_peaks[-3:]]

        return sorted(support, reverse=True), sorted(resistance)

    def _calculate_structure_confidence(
        self, df: pd.DataFrame, phase: MarketPhase
    ) -> float:
        """Calculate confidence in structure detection."""
        # Base confidence
        confidence = 0.6

        # Increase if data is sufficient
        if len(df) >= self.lookback_periods:
            confidence += 0.1

        # Increase for clear trending phases
        if phase in [MarketPhase.TRENDING_UP, MarketPhase.TRENDING_DOWN]:
            closes = df["close"].values[-20:]
            # Check for consistent direction
            direction = 1 if phase == MarketPhase.TRENDING_UP else -1
            consistency = np.mean(np.sign(np.diff(closes)) == direction)
            confidence += consistency * 0.3

        return min(confidence, 1.0)

    # ─────────────────────────────────────────────────────────────────
    # Volatility Methods
    # ─────────────────────────────────────────────────────────────────

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def _calculate_percentile(self, values: np.ndarray, current: float) -> float:
        """Calculate percentile of current value in historical distribution."""
        if len(values) == 0:
            return 50.0

        percentile = (np.sum(values <= current) / len(values)) * 100
        return float(percentile)

    def _classify_volatility_regime(self, atr_percentile: float) -> VolatilityRegime:
        """Classify volatility regime based on ATR percentile."""
        if atr_percentile < 25:
            return VolatilityRegime.LOW
        elif atr_percentile < 75:
            return VolatilityRegime.NORMAL
        elif atr_percentile < 90:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME

    def _detect_volatility_trend(self, atr: pd.Series) -> str:
        """Detect trend in volatility."""
        if len(atr) < 10:
            return "unknown"

        recent = atr.tail(10).values
        slope = np.polyfit(np.arange(len(recent)), recent, 1)[0]

        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"

    # ─────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────

    def _find_peaks(
        self, values: np.ndarray, threshold: float = 0.02
    ) -> list[tuple[int, float]]:
        """Find local peaks in a series.

        Args:
            values: Array of values.
            threshold: Minimum peak prominence (as fraction of value).

        Returns:
            List of (index, value) tuples for peaks.
        """
        peaks = []
        for i in range(1, len(values) - 1):
            if values[i] > values[i - 1] and values[i] > values[i + 1]:
                # Check prominence
                prominence = min(values[i] - values[i - 1], values[i] - values[i + 1])
                if prominence / values[i] > threshold:
                    peaks.append((i, values[i]))

        return peaks

    def _fit_trendline(self, values: np.ndarray) -> float:
        """Fit linear trendline and return slope.

        Args:
            values: Array of values.

        Returns:
            Slope of fitted line (normalized).
        """
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)

        # Normalize by average value
        avg_val = np.mean(values)
        if avg_val != 0:
            slope = slope / avg_val

        return float(slope)
