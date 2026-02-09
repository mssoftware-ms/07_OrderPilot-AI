"""Market Context Detectors - Regime and Level Detection.

Handles:
- Regime detection (trend strength + direction)
- Trend detection (MTF alignment)
- Level detection (Support/Resistance from swing highs/lows + EMAs)

Module 3/4 of market_context_builder.py split (Lines 489-733, 739-761)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pandas as pd

from .market_context import (
    Level,
    LevelsSnapshot,
    LevelStrength,
    LevelType,
    RegimeType,
    TrendDirection,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .market_context_builder import MarketContextBuilderConfig


class RegimeDetector:
    """
    Detects market regime (trend strength + direction).

    Uses EMA alignment and ADX for regime classification.
    """

    def __init__(self, config: "MarketContextBuilderConfig"):
        """
        Initialize regime detector.

        Args:
            config: MarketContextBuilderConfig instance
        """
        self.config = config

    def detect_regime(
        self, df: pd.DataFrame
    ) -> tuple[RegimeType, float, str]:
        """
        Erkennt das Marktregime.

        Returns:
            Tuple von (RegimeType, confidence, reason)
        """
        if df.empty:
            return RegimeType.NEUTRAL, 0.0, "No data"

        current = df.iloc[-1]

        ema20 = current.get("ema_20")
        ema50 = current.get("ema_50")
        adx = current.get("adx_14")
        atr_pct = current.get("atr_percent")

        # Check for explosive volatility first
        if atr_pct and atr_pct > self.config.volatility_extreme_atr_pct:
            return (
                RegimeType.VOLATILITY_EXPLOSIVE,
                0.9,
                f"ATR% = {atr_pct:.2f}% > {self.config.volatility_extreme_atr_pct}%",
            )

        # Need EMAs for trend detection
        if not all([ema20, ema50]):
            return RegimeType.NEUTRAL, 0.3, "Missing EMA data"

        reasons = []
        confidence = 0.5

        # Trend Direction
        if ema20 > ema50:
            direction = "BULL"
            reasons.append(f"EMA20 ({ema20:.2f}) > EMA50 ({ema50:.2f})")
        elif ema20 < ema50:
            direction = "BEAR"
            reasons.append(f"EMA20 ({ema20:.2f}) < EMA50 ({ema50:.2f})")
        else:
            direction = "RANGE"
            reasons.append("EMA20 ≈ EMA50")

        # Trend Strength (ADX)
        if adx:
            if adx > self.config.adx_strong_threshold:
                strength = "STRONG"
                confidence += 0.3
                reasons.append(f"ADX ({adx:.1f}) > {self.config.adx_strong_threshold}")
            elif adx > self.config.adx_weak_threshold:
                strength = "WEAK"
                confidence += 0.1
                reasons.append(f"ADX ({adx:.1f}) > {self.config.adx_weak_threshold}")
            else:
                strength = "CHOP"
                confidence -= 0.1
                reasons.append(f"ADX ({adx:.1f}) < {self.config.adx_weak_threshold}")
        else:
            strength = "UNKNOWN"

        # Determine Regime
        if direction == "BULL":
            if strength == "STRONG":
                regime = RegimeType.STRONG_TREND_BULL
            else:
                regime = RegimeType.WEAK_TREND_BULL
        elif direction == "BEAR":
            if strength == "STRONG":
                regime = RegimeType.STRONG_TREND_BEAR
            else:
                regime = RegimeType.WEAK_TREND_BEAR
        else:
            regime = RegimeType.CHOP_RANGE

        # Override to CHOP if ADX very low
        if adx and adx < self.config.adx_weak_threshold:
            regime = RegimeType.CHOP_RANGE
            confidence = max(0.3, confidence - 0.2)

        return regime, min(1.0, max(0.0, confidence)), "; ".join(reasons)

    def detect_trend(self, df: pd.DataFrame) -> TrendDirection:
        """Erkennt Trend-Richtung aus EMAs."""
        if df.empty:
            return TrendDirection.NEUTRAL

        current = df.iloc[-1]
        ema20 = current.get("ema_20")
        ema50 = current.get("ema_50")

        if ema20 and ema50:
            if ema20 > ema50:
                return TrendDirection.BULLISH
            elif ema20 < ema50:
                return TrendDirection.BEARISH

        return TrendDirection.NEUTRAL

    def calculate_mtf_alignment(self, trends: dict[str, TrendDirection]) -> float:
        """
        Berechnet Multi-Timeframe Alignment Score.

        Args:
            trends: Dict of timeframe -> TrendDirection

        Returns:
            Score von -1 (alle bearish) bis +1 (alle bullish)
        """
        if not trends:
            return 0.0

        scores = [self._trend_to_score(t) for t in trends.values()]
        return sum(scores) / len(scores)

    @staticmethod
    def _trend_to_score(trend: TrendDirection | None) -> float:
        """Konvertiert Trend zu Score."""
        if trend == TrendDirection.BULLISH:
            return 1.0
        elif trend == TrendDirection.BEARISH:
            return -1.0
        return 0.0

    def determine_volatility_state(self, atr_pct: float) -> str:
        """Bestimmt Volatilitäts-Zustand."""
        if atr_pct >= self.config.volatility_extreme_atr_pct:
            return "EXTREME"
        elif atr_pct >= self.config.volatility_high_atr_pct:
            return "HIGH"
        elif atr_pct < 1.0:
            return "LOW"
        return "NORMAL"


class LevelDetector:
    """
    Detects Support/Resistance levels.

    Uses swing highs/lows and EMA levels.
    """

    def __init__(self, config: "MarketContextBuilderConfig"):
        """
        Initialize level detector.

        Args:
            config: MarketContextBuilderConfig instance
        """
        self.config = config

    def detect_levels(
        self,
        df: pd.DataFrame,
        symbol: str,
        current_price: float,
        timeframe: str,
    ) -> LevelsSnapshot:
        """
        Erkennt Support/Resistance Levels.

        Basis-Implementierung mit Pivot Points.
        Wird in Phase 2 durch LevelEngine v2 ersetzt.

        Args:
            df: DataFrame with indicators
            symbol: Trading symbol
            current_price: Current market price
            timeframe: Timeframe

        Returns:
            LevelsSnapshot with detected levels
        """
        timestamp = datetime.now(timezone.utc)

        if df.empty or current_price <= 0:
            return LevelsSnapshot(
                timestamp=timestamp,
                symbol=symbol,
                current_price=current_price,
            )

        supports = []
        resistances = []

        # Get ATR for zone width
        atr = df["atr_14"].iloc[-1] if "atr_14" in df.columns else current_price * 0.01
        zone_width = atr * self.config.level_zone_atr_mult

        # Find Swing Highs/Lows
        lookback = self.config.pivot_lookback
        highs = df["high"].values
        lows = df["low"].values

        for i in range(lookback, len(df) - lookback):
            # Swing High
            if highs[i] == max(highs[i - lookback : i + lookback + 1]):
                level = Level(
                    level_id=f"swing_high_{i}",
                    level_type=LevelType.SWING_HIGH,
                    price_low=highs[i] - zone_width,
                    price_high=highs[i] + zone_width,
                    strength=LevelStrength.MODERATE,
                    touches=1,
                    timeframe=timeframe,
                    method="swing",
                )
                if highs[i] > current_price:
                    resistances.append(level)
                else:
                    supports.append(level)

            # Swing Low
            if lows[i] == min(lows[i - lookback : i + lookback + 1]):
                level = Level(
                    level_id=f"swing_low_{i}",
                    level_type=LevelType.SWING_LOW,
                    price_low=lows[i] - zone_width,
                    price_high=lows[i] + zone_width,
                    strength=LevelStrength.MODERATE,
                    touches=1,
                    timeframe=timeframe,
                    method="swing",
                )
                if lows[i] < current_price:
                    supports.append(level)
                else:
                    resistances.append(level)

        # Add EMA levels
        for ema_col in ["ema_20", "ema_50", "ema_200"]:
            if ema_col in df.columns:
                ema_value = df[ema_col].iloc[-1]
                if pd.notna(ema_value):
                    level_type = LevelType.EMA_SUPPORT if ema_value < current_price else LevelType.EMA_RESISTANCE
                    level = Level(
                        level_id=f"{ema_col}_level",
                        level_type=level_type,
                        price_low=ema_value - zone_width * 0.5,
                        price_high=ema_value + zone_width * 0.5,
                        strength=LevelStrength.MODERATE,
                        timeframe=timeframe,
                        method="ema",
                        label=ema_col.upper(),
                    )
                    if ema_value < current_price:
                        supports.append(level)
                    else:
                        resistances.append(level)

        # Sort by distance to current price
        supports.sort(key=lambda l: current_price - l.midpoint)
        resistances.sort(key=lambda l: l.midpoint - current_price)

        # Calculate distance from price
        for level in supports + resistances:
            level.distance_from_price_pct = abs(
                (level.midpoint - current_price) / current_price * 100
            )

        # Get top N
        key_supports = supports[: self.config.top_n_levels]
        key_resistances = resistances[: self.config.top_n_levels]

        return LevelsSnapshot(
            timestamp=timestamp,
            symbol=symbol,
            current_price=current_price,
            support_levels=supports,
            resistance_levels=resistances,
            key_supports=key_supports,
            key_resistances=key_resistances,
            nearest_support=supports[0] if supports else None,
            nearest_resistance=resistances[0] if resistances else None,
        )
