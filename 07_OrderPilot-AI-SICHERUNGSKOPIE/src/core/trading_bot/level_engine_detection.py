"""Level Engine Detection Methods - Swing, Pivot, Cluster, Daily H/L.

Refactored from 797 LOC monolith using composition pattern.

Module 2/4 of level_engine.py split.

Contains:
- _calculate_atr(): ATR calculation for zone width
- _detect_swing_levels(): Swing High/Low detection
- _calculate_pivot_points(): Pivot Points (PP, R1, R2, S1, S2)
- _detect_clusters(): Price clustering (congestion zones)
- _detect_daily_hl(): Daily Highs/Lows
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import numpy as np
import pandas as pd

from src.core.trading_bot.level_engine_state import (
    DetectionMethod,
    Level,
    LevelStrength,
    LevelType,
)

logger = logging.getLogger(__name__)


class LevelEngineDetection:
    """Helper für Level Detection Methods."""

    def __init__(self, parent):
        """
        Args:
            parent: LevelEngine Instanz
        """
        self.parent = parent

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Berechnet ATR für Zone-Breite."""
        try:
            import talib

            atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=period)
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
        except (ImportError, Exception):
            # Pandas fallback
            high = df["high"]
            low = df["low"]
            close = df["close"].shift(1)
            tr = pd.concat(
                [high - low, (high - close).abs(), (low - close).abs()], axis=1
            ).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0

    def detect_swing_levels(
        self,
        df: pd.DataFrame,
        timeframe: str,
        atr: float,
    ) -> List[Level]:
        """Erkennt Swing Highs und Swing Lows."""
        levels = []
        lookback = self.parent.config.swing_lookback

        if len(df) < lookback * 2 + 1:
            return levels

        highs = df["high"].values
        lows = df["low"].values

        # Swing Highs
        for i in range(lookback, len(df) - lookback):
            is_swing_high = True
            for j in range(1, lookback + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_swing_high = False
                    break

            if is_swing_high:
                price = float(highs[i])
                zone_width = max(
                    atr * self.parent.config.zone_width_atr_mult,
                    price * self.parent.config.min_zone_width_pct / 100,
                )
                zone_width = min(
                    zone_width, price * self.parent.config.max_zone_width_pct / 100
                )

                level_id = self.parent._generate_level_id(
                    price, LevelType.SWING_HIGH, timeframe
                )
                levels.append(
                    Level(
                        id=level_id,
                        level_type=LevelType.SWING_HIGH,
                        price_low=price - zone_width / 2,
                        price_high=price + zone_width / 2,
                        strength=LevelStrength.WEAK,
                        method=DetectionMethod.SWING,
                        timeframe=timeframe,
                        first_touch=df.index[i]
                        if hasattr(df.index[i], "isoformat")
                        else datetime.now(timezone.utc),
                    )
                )

        # Swing Lows
        for i in range(lookback, len(df) - lookback):
            is_swing_low = True
            for j in range(1, lookback + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_swing_low = False
                    break

            if is_swing_low:
                price = float(lows[i])
                zone_width = max(
                    atr * self.parent.config.zone_width_atr_mult,
                    price * self.parent.config.min_zone_width_pct / 100,
                )
                zone_width = min(
                    zone_width, price * self.parent.config.max_zone_width_pct / 100
                )

                level_id = self.parent._generate_level_id(
                    price, LevelType.SWING_LOW, timeframe
                )
                levels.append(
                    Level(
                        id=level_id,
                        level_type=LevelType.SWING_LOW,
                        price_low=price - zone_width / 2,
                        price_high=price + zone_width / 2,
                        strength=LevelStrength.WEAK,
                        method=DetectionMethod.SWING,
                        timeframe=timeframe,
                        first_touch=df.index[i]
                        if hasattr(df.index[i], "isoformat")
                        else datetime.now(timezone.utc),
                    )
                )

        return levels

    def calculate_pivot_points(
        self,
        df: pd.DataFrame,
        timeframe: str,
    ) -> List[Level]:
        """Berechnet Pivot Points (PP, R1, R2, S1, S2)."""
        levels = []

        if len(df) < 2:
            return levels

        # Use previous period's H/L/C
        prev_high = float(df["high"].iloc[-2])
        prev_low = float(df["low"].iloc[-2])
        prev_close = float(df["close"].iloc[-2])

        # Standard Pivot Point
        pp = (prev_high + prev_low + prev_close) / 3

        # Support and Resistance levels
        r1 = 2 * pp - prev_low
        s1 = 2 * pp - prev_high
        r2 = pp + (prev_high - prev_low)
        s2 = pp - (prev_high - prev_low)

        # Zone width based on range
        range_val = prev_high - prev_low
        zone_width = range_val * 0.05  # 5% of range

        pivot_data = [
            (pp, LevelType.PIVOT, "PP"),
            (r1, LevelType.RESISTANCE, "R1"),
            (r2, LevelType.RESISTANCE, "R2"),
            (s1, LevelType.SUPPORT, "S1"),
            (s2, LevelType.SUPPORT, "S2"),
        ]

        for price, level_type, label in pivot_data:
            level_id = self.parent._generate_level_id(price, level_type, timeframe)
            levels.append(
                Level(
                    id=level_id,
                    level_type=level_type,
                    price_low=price - zone_width,
                    price_high=price + zone_width,
                    strength=LevelStrength.MODERATE,
                    method=DetectionMethod.PIVOT,
                    timeframe=timeframe,
                    label=label,
                )
            )

        return levels

    def detect_clusters(
        self,
        df: pd.DataFrame,
        timeframe: str,
        atr: float,
    ) -> List[Level]:
        """Erkennt Preis-Cluster (Konsolidierungszonen)."""
        levels = []

        if len(df) < 20:
            return levels

        # Get all high and low prices
        prices = pd.concat([df["high"], df["low"]]).values
        prices = np.sort(prices)

        # Cluster nearby prices
        threshold = np.mean(prices) * (self.parent.config.cluster_threshold_pct / 100)
        clusters = []
        current_cluster = [prices[0]]

        for i in range(1, len(prices)):
            if prices[i] - current_cluster[-1] <= threshold:
                current_cluster.append(prices[i])
            else:
                if len(current_cluster) >= self.parent.config.min_cluster_size:
                    clusters.append(current_cluster)
                current_cluster = [prices[i]]

        if len(current_cluster) >= self.parent.config.min_cluster_size:
            clusters.append(current_cluster)

        # Convert clusters to levels
        for cluster in clusters:
            price_mid = np.mean(cluster)
            price_low = min(cluster)
            price_high = max(cluster)

            # Ensure minimum zone width
            zone_width = price_high - price_low
            if zone_width < atr * self.parent.config.zone_width_atr_mult:
                expansion = (
                    atr * self.parent.config.zone_width_atr_mult - zone_width
                ) / 2
                price_low -= expansion
                price_high += expansion

            level_id = self.parent._generate_level_id(
                price_mid, LevelType.SUPPORT, timeframe
            )
            levels.append(
                Level(
                    id=level_id,
                    level_type=LevelType.SUPPORT,  # Will be classified later
                    price_low=price_low,
                    price_high=price_high,
                    strength=LevelStrength.WEAK,
                    method=DetectionMethod.CLUSTER,
                    timeframe=timeframe,
                    touches=len(cluster),
                )
            )

        return levels

    def detect_daily_hl(
        self,
        df: pd.DataFrame,
        timeframe: str,
    ) -> List[Level]:
        """Erkennt tägliche Hochs und Tiefs."""
        levels = []

        if len(df) < 24:  # Mindestens 1 Tag Daten
            return levels

        try:
            # Group by date
            df_copy = df.copy()
            if not isinstance(df_copy.index, pd.DatetimeIndex):
                return levels

            df_copy["date"] = df_copy.index.date
            daily = (
                df_copy.groupby("date")
                .agg(
                    {
                        "high": "max",
                        "low": "min",
                    }
                )
                .tail(self.parent.config.daily_lookback)
            )

            avg_daily_range = (daily["high"] - daily["low"]).mean()
            zone_width = avg_daily_range * 0.02  # 2% of daily range

            for date, row in daily.iterrows():
                # Daily High
                level_id = self.parent._generate_level_id(
                    row["high"], LevelType.DAILY_HIGH, timeframe
                )
                levels.append(
                    Level(
                        id=level_id,
                        level_type=LevelType.DAILY_HIGH,
                        price_low=row["high"] - zone_width,
                        price_high=row["high"] + zone_width,
                        strength=LevelStrength.MODERATE,
                        method=DetectionMethod.SWING,
                        timeframe=timeframe,
                        label=f"D-High {date}",
                    )
                )

                # Daily Low
                level_id = self.parent._generate_level_id(
                    row["low"], LevelType.DAILY_LOW, timeframe
                )
                levels.append(
                    Level(
                        id=level_id,
                        level_type=LevelType.DAILY_LOW,
                        price_low=row["low"] - zone_width,
                        price_high=row["low"] + zone_width,
                        strength=LevelStrength.MODERATE,
                        method=DetectionMethod.SWING,
                        timeframe=timeframe,
                        label=f"D-Low {date}",
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to detect daily H/L: {e}")

        return levels
