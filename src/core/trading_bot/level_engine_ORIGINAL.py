"""
LevelEngine v2 - Support/Resistance Level Detection.

Deterministisches Level-Erkennungssystem für:
- Support/Resistance Zonen
- Swing Highs/Lows
- Key Levels (Tages-, Wochen-, Monats-Hochs/Tiefs)
- Pivot Points
- Volume-basierte Levels (VWAP, POC)

Phase 2.3 der Bot-Integration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ENUMS
class LevelType(Enum):
    """Typ des Levels."""
    SUPPORT = "support"
    RESISTANCE = "resistance"
    PIVOT = "pivot"
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"
    DAILY_HIGH = "daily_high"
    DAILY_LOW = "daily_low"
    WEEKLY_HIGH = "weekly_high"
    WEEKLY_LOW = "weekly_low"
    VWAP = "vwap"
    POC = "poc"  # Point of Control (Volume Profile)


class LevelStrength(Enum):
    """Stärke des Levels."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    KEY = "key"  # Besonders wichtiges Level


class DetectionMethod(Enum):
    """Methode zur Level-Erkennung."""
    SWING = "swing"  # Swing High/Low based
    PIVOT = "pivot"  # Pivot Points (PP, R1, S1, etc.)
    CLUSTER = "cluster"  # Price clustering
    VOLUME = "volume"  # Volume-based (POC, VAH, VAL)
    FRACTAL = "fractal"  # Fractal-based detection
    MANUAL = "manual"  # Manuell hinzugefügt


# DATA CLASSES
@dataclass
class Level:
    """
    Einzelnes Level (Support/Resistance/Pivot etc.).

    Repräsentiert eine Zone, nicht nur einen Preis-Punkt.
    """
    id: str  # Unique ID
    level_type: LevelType
    price_low: float  # Untere Grenze der Zone
    price_high: float  # Obere Grenze der Zone
    strength: LevelStrength
    method: DetectionMethod
    timeframe: str
    touches: int = 1  # Wie oft wurde das Level getestet
    broken: bool = False  # Wurde das Level durchbrochen
    first_touch: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_touch: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    label: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def price_mid(self) -> float:
        """Mittelpunkt der Zone."""
        return (self.price_low + self.price_high) / 2

    @property
    def zone_width(self) -> float:
        """Breite der Zone in absoluten Zahlen."""
        return self.price_high - self.price_low

    @property
    def zone_width_pct(self) -> float:
        """Breite der Zone in Prozent des Mittelpreises."""
        return (self.zone_width / self.price_mid) * 100 if self.price_mid > 0 else 0

    def contains_price(self, price: float) -> bool:
        """Prüft ob ein Preis in der Zone liegt."""
        return self.price_low <= price <= self.price_high

    def is_near(self, price: float, tolerance_pct: float = 0.5) -> bool:
        """Prüft ob ein Preis in der Nähe der Zone liegt."""
        tolerance = self.price_mid * (tolerance_pct / 100)
        return (self.price_low - tolerance) <= price <= (self.price_high + tolerance)

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "id": self.id,
            "type": self.level_type.value,
            "price_low": self.price_low,
            "price_high": self.price_high,
            "price_mid": self.price_mid,
            "strength": self.strength.value,
            "method": self.method.value,
            "timeframe": self.timeframe,
            "touches": self.touches,
            "broken": self.broken,
            "label": self.label,
            "zone_width_pct": round(self.zone_width_pct, 4),
        }


@dataclass
class LevelsResult:
    """Ergebnis der Level-Analyse."""
    levels: List[Level]
    symbol: str
    timeframe: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    current_price: Optional[float] = None

    @property
    def support_levels(self) -> List[Level]:
        """Nur Support-Levels (unter aktuellem Preis)."""
        if self.current_price is None:
            return [l for l in self.levels if l.level_type in (LevelType.SUPPORT, LevelType.SWING_LOW)]
        return [l for l in self.levels if l.price_mid < self.current_price]

    @property
    def resistance_levels(self) -> List[Level]:
        """Nur Resistance-Levels (über aktuellem Preis)."""
        if self.current_price is None:
            return [l for l in self.levels if l.level_type in (LevelType.RESISTANCE, LevelType.SWING_HIGH)]
        return [l for l in self.levels if l.price_mid > self.current_price]

    @property
    def key_levels(self) -> List[Level]:
        """Nur Key Levels (strength=KEY)."""
        return [l for l in self.levels if l.strength == LevelStrength.KEY]

    def get_nearest_support(self, price: Optional[float] = None) -> Optional[Level]:
        """Findet nächstes Support-Level unter dem Preis."""
        price = price or self.current_price
        if price is None:
            return None
        supports = [l for l in self.levels if l.price_mid < price]
        if not supports:
            return None
        return max(supports, key=lambda l: l.price_mid)

    def get_nearest_resistance(self, price: Optional[float] = None) -> Optional[Level]:
        """Findet nächstes Resistance-Level über dem Preis."""
        price = price or self.current_price
        if price is None:
            return None
        resistances = [l for l in self.levels if l.price_mid > price]
        if not resistances:
            return None
        return min(resistances, key=lambda l: l.price_mid)

    def get_top_n(self, n: int = 5, sort_by: str = "strength") -> List[Level]:
        """
        Gibt die Top-N wichtigsten Levels zurück.

        Args:
            n: Anzahl der Levels
            sort_by: Sortierkriterium ("strength", "touches", "proximity")
        """
        if sort_by == "strength":
            strength_order = {LevelStrength.KEY: 4, LevelStrength.STRONG: 3,
                           LevelStrength.MODERATE: 2, LevelStrength.WEAK: 1}
            sorted_levels = sorted(self.levels, key=lambda l: strength_order.get(l.strength, 0), reverse=True)
        elif sort_by == "touches":
            sorted_levels = sorted(self.levels, key=lambda l: l.touches, reverse=True)
        elif sort_by == "proximity" and self.current_price:
            sorted_levels = sorted(self.levels, key=lambda l: abs(l.price_mid - self.current_price))
        else:
            sorted_levels = self.levels

        return sorted_levels[:n]

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "current_price": self.current_price,
            "total_levels": len(self.levels),
            "support_count": len(self.support_levels),
            "resistance_count": len(self.resistance_levels),
            "key_levels_count": len(self.key_levels),
            "levels": [l.to_dict() for l in self.levels],
        }

    def to_tag_format(self) -> str:
        """
        Konvertiert zu Tag-Format für Chatbot.

        Format: [#Support Zone; 91038-91120] etc.
        """
        tags = []
        for level in self.get_top_n(10):
            type_tag = "Support" if level.price_mid < (self.current_price or 0) else "Resistance"
            if level.strength == LevelStrength.KEY:
                type_tag = f"Key {type_tag}"
            tags.append(f"[#{type_tag} Zone; {level.price_low:.2f}-{level.price_high:.2f}]")
        return " ".join(tags)


# CONFIGURATION
@dataclass
class LevelEngineConfig:
    """Konfiguration für LevelEngine."""

    # Swing Detection
    swing_lookback: int = 10  # Bars links/rechts für Swing High/Low
    min_swing_touches: int = 2  # Min. Touches für valides Level

    # Zone Width
    zone_width_atr_mult: float = 0.3  # Zone-Breite als Vielfaches von ATR
    min_zone_width_pct: float = 0.1  # Minimale Zone-Breite in %
    max_zone_width_pct: float = 2.0  # Maximale Zone-Breite in %

    # Clustering
    cluster_threshold_pct: float = 0.5  # Preise innerhalb X% werden geclustert
    min_cluster_size: int = 3  # Minimum Punkte für einen Cluster

    # Strength Calculation
    strong_touch_threshold: int = 3  # Touches für "STRONG"
    key_touch_threshold: int = 5  # Touches für "KEY"

    # Filtering
    max_levels: int = 20  # Maximum Levels pro Analyse
    proximity_merge_pct: float = 0.3  # Levels innerhalb X% werden gemerged

    # Pivot Points
    include_pivots: bool = True
    pivot_type: str = "standard"  # standard, fibonacci, woodie, camarilla

    # Historical Levels
    include_daily_hl: bool = True
    include_weekly_hl: bool = True
    daily_lookback: int = 5  # Tage für Daily H/L
    weekly_lookback: int = 4  # Wochen für Weekly H/L


# LEVEL ENGINE
class LevelEngine:
    """
    Level Detection Engine v2.

    Deterministische Erkennung von Support/Resistance Levels.

    Usage:
        engine = LevelEngine()
        result = engine.detect_levels(df, "BTCUSD", "5m")

        # Get key levels
        key_levels = result.key_levels

        # Get nearest support
        support = result.get_nearest_support(current_price)
    """

    def __init__(self, config: LevelEngineConfig | None = None):
        self.config = config or LevelEngineConfig()
        self._lock = threading.RLock()

    def detect_levels(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        timeframe: str = "5m",
        current_price: Optional[float] = None,
    ) -> LevelsResult:
        """
        Erkennt Levels aus DataFrame.

        Args:
            df: DataFrame mit OHLCV-Daten
            symbol: Trading-Symbol
            timeframe: Timeframe
            current_price: Aktueller Preis (für Support/Resistance Klassifizierung)

        Returns:
            LevelsResult mit erkannten Levels
        """
        with self._lock:
            if df is None or df.empty:
                logger.warning("Empty DataFrame for level detection")
                return LevelsResult(levels=[], symbol=symbol, timeframe=timeframe)

            levels: List[Level] = []

            # Current price from last close if not provided
            if current_price is None:
                current_price = float(df["close"].iloc[-1])

            # Calculate ATR for zone width
            atr = self._calculate_atr(df)

            # 1. Swing High/Low Detection
            swing_levels = self._detect_swing_levels(df, timeframe, atr)
            levels.extend(swing_levels)

            # 2. Pivot Points
            if self.config.include_pivots:
                pivot_levels = self._calculate_pivot_points(df, timeframe)
                levels.extend(pivot_levels)

            # 3. Cluster Detection (price congestion)
            cluster_levels = self._detect_clusters(df, timeframe, atr)
            levels.extend(cluster_levels)

            # 4. Historical Highs/Lows
            if self.config.include_daily_hl:
                daily_levels = self._detect_daily_hl(df, timeframe)
                levels.extend(daily_levels)

            # 5. Merge overlapping levels
            levels = self._merge_overlapping_levels(levels)

            # 6. Calculate strength
            levels = self._calculate_level_strength(levels, df)

            # 7. Classify as Support/Resistance
            levels = self._classify_levels(levels, current_price)

            # 8. Sort and limit
            levels = sorted(levels, key=lambda l: l.price_mid)
            if len(levels) > self.config.max_levels:
                # Keep strongest levels
                levels = self._select_top_levels(levels, current_price)

            logger.debug(f"Detected {len(levels)} levels for {symbol} {timeframe}")

            return LevelsResult(
                levels=levels,
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
            )

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
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
            tr = pd.concat([
                high - low,
                (high - close).abs(),
                (low - close).abs()
            ], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0

    def _detect_swing_levels(
        self,
        df: pd.DataFrame,
        timeframe: str,
        atr: float,
    ) -> List[Level]:
        """Erkennt Swing Highs und Swing Lows."""
        levels = []
        lookback = self.config.swing_lookback

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
                    atr * self.config.zone_width_atr_mult,
                    price * self.config.min_zone_width_pct / 100
                )
                zone_width = min(zone_width, price * self.config.max_zone_width_pct / 100)

                level_id = self._generate_level_id(price, LevelType.SWING_HIGH, timeframe)
                levels.append(Level(
                    id=level_id,
                    level_type=LevelType.SWING_HIGH,
                    price_low=price - zone_width / 2,
                    price_high=price + zone_width / 2,
                    strength=LevelStrength.WEAK,
                    method=DetectionMethod.SWING,
                    timeframe=timeframe,
                    first_touch=df.index[i] if hasattr(df.index[i], 'isoformat') else datetime.now(timezone.utc),
                ))

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
                    atr * self.config.zone_width_atr_mult,
                    price * self.config.min_zone_width_pct / 100
                )
                zone_width = min(zone_width, price * self.config.max_zone_width_pct / 100)

                level_id = self._generate_level_id(price, LevelType.SWING_LOW, timeframe)
                levels.append(Level(
                    id=level_id,
                    level_type=LevelType.SWING_LOW,
                    price_low=price - zone_width / 2,
                    price_high=price + zone_width / 2,
                    strength=LevelStrength.WEAK,
                    method=DetectionMethod.SWING,
                    timeframe=timeframe,
                    first_touch=df.index[i] if hasattr(df.index[i], 'isoformat') else datetime.now(timezone.utc),
                ))

        return levels

    def _calculate_pivot_points(
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
            level_id = self._generate_level_id(price, level_type, timeframe)
            levels.append(Level(
                id=level_id,
                level_type=level_type,
                price_low=price - zone_width,
                price_high=price + zone_width,
                strength=LevelStrength.MODERATE,
                method=DetectionMethod.PIVOT,
                timeframe=timeframe,
                label=label,
            ))

        return levels

    def _detect_clusters(
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
        threshold = np.mean(prices) * (self.config.cluster_threshold_pct / 100)
        clusters = []
        current_cluster = [prices[0]]

        for i in range(1, len(prices)):
            if prices[i] - current_cluster[-1] <= threshold:
                current_cluster.append(prices[i])
            else:
                if len(current_cluster) >= self.config.min_cluster_size:
                    clusters.append(current_cluster)
                current_cluster = [prices[i]]

        if len(current_cluster) >= self.config.min_cluster_size:
            clusters.append(current_cluster)

        # Convert clusters to levels
        for cluster in clusters:
            price_mid = np.mean(cluster)
            price_low = min(cluster)
            price_high = max(cluster)

            # Ensure minimum zone width
            zone_width = price_high - price_low
            if zone_width < atr * self.config.zone_width_atr_mult:
                expansion = (atr * self.config.zone_width_atr_mult - zone_width) / 2
                price_low -= expansion
                price_high += expansion

            level_id = self._generate_level_id(price_mid, LevelType.SUPPORT, timeframe)
            levels.append(Level(
                id=level_id,
                level_type=LevelType.SUPPORT,  # Will be classified later
                price_low=price_low,
                price_high=price_high,
                strength=LevelStrength.WEAK,
                method=DetectionMethod.CLUSTER,
                timeframe=timeframe,
                touches=len(cluster),
            ))

        return levels

    def _detect_daily_hl(
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
            daily = df_copy.groupby("date").agg({
                "high": "max",
                "low": "min",
            }).tail(self.config.daily_lookback)

            avg_daily_range = (daily["high"] - daily["low"]).mean()
            zone_width = avg_daily_range * 0.02  # 2% of daily range

            for date, row in daily.iterrows():
                # Daily High
                level_id = self._generate_level_id(row["high"], LevelType.DAILY_HIGH, timeframe)
                levels.append(Level(
                    id=level_id,
                    level_type=LevelType.DAILY_HIGH,
                    price_low=row["high"] - zone_width,
                    price_high=row["high"] + zone_width,
                    strength=LevelStrength.MODERATE,
                    method=DetectionMethod.SWING,
                    timeframe=timeframe,
                    label=f"D-High {date}",
                ))

                # Daily Low
                level_id = self._generate_level_id(row["low"], LevelType.DAILY_LOW, timeframe)
                levels.append(Level(
                    id=level_id,
                    level_type=LevelType.DAILY_LOW,
                    price_low=row["low"] - zone_width,
                    price_high=row["low"] + zone_width,
                    strength=LevelStrength.MODERATE,
                    method=DetectionMethod.SWING,
                    timeframe=timeframe,
                    label=f"D-Low {date}",
                ))

        except Exception as e:
            logger.warning(f"Failed to detect daily H/L: {e}")

        return levels

    def _merge_overlapping_levels(self, levels: List[Level]) -> List[Level]:
        """Merged überlappende Levels."""
        if len(levels) < 2:
            return levels

        # Sort by price
        levels = sorted(levels, key=lambda l: l.price_mid)
        merged = [levels[0]]

        for current in levels[1:]:
            last = merged[-1]

            # Check if overlapping or very close
            threshold = last.price_mid * (self.config.proximity_merge_pct / 100)
            if current.price_low <= last.price_high + threshold:
                # Merge: expand zone, keep stronger method/type
                new_low = min(last.price_low, current.price_low)
                new_high = max(last.price_high, current.price_high)
                new_touches = last.touches + current.touches

                # Keep stronger level type
                strength_order = {LevelStrength.KEY: 4, LevelStrength.STRONG: 3,
                                LevelStrength.MODERATE: 2, LevelStrength.WEAK: 1}
                if strength_order.get(current.strength, 0) > strength_order.get(last.strength, 0):
                    last.strength = current.strength

                last.price_low = new_low
                last.price_high = new_high
                last.touches = new_touches
            else:
                merged.append(current)

        return merged

    def _calculate_level_strength(
        self,
        levels: List[Level],
        df: pd.DataFrame,
    ) -> List[Level]:
        """Berechnet Stärke basierend auf Touches."""
        for level in levels:
            # Count how many times price touched this zone
            touches = 0
            for _, row in df.iterrows():
                if level.contains_price(row["high"]) or level.contains_price(row["low"]):
                    touches += 1

            level.touches = max(level.touches, touches)

            # Determine strength
            if level.touches >= self.config.key_touch_threshold:
                level.strength = LevelStrength.KEY
            elif level.touches >= self.config.strong_touch_threshold:
                level.strength = LevelStrength.STRONG
            elif level.touches >= 2:
                level.strength = LevelStrength.MODERATE
            else:
                level.strength = LevelStrength.WEAK

        return levels

    def _classify_levels(
        self,
        levels: List[Level],
        current_price: float,
    ) -> List[Level]:
        """Klassifiziert Levels als Support oder Resistance."""
        for level in levels:
            # Skip already classified pivot levels
            if level.level_type in (LevelType.PIVOT, LevelType.DAILY_HIGH, LevelType.DAILY_LOW,
                                    LevelType.WEEKLY_HIGH, LevelType.WEEKLY_LOW, LevelType.VWAP):
                continue

            if level.price_mid < current_price:
                level.level_type = LevelType.SUPPORT
            else:
                level.level_type = LevelType.RESISTANCE

        return levels

    def _select_top_levels(
        self,
        levels: List[Level],
        current_price: float,
    ) -> List[Level]:
        """Wählt die wichtigsten Levels aus."""
        # Separate supports and resistances
        supports = [l for l in levels if l.price_mid < current_price]
        resistances = [l for l in levels if l.price_mid >= current_price]

        # Sort by strength and proximity
        strength_order = {LevelStrength.KEY: 4, LevelStrength.STRONG: 3,
                        LevelStrength.MODERATE: 2, LevelStrength.WEAK: 1}

        supports.sort(key=lambda l: (-strength_order.get(l.strength, 0), -l.price_mid))
        resistances.sort(key=lambda l: (-strength_order.get(l.strength, 0), l.price_mid))

        # Take half from each side
        half = self.config.max_levels // 2
        selected = supports[:half] + resistances[:half]

        return sorted(selected, key=lambda l: l.price_mid)

    @staticmethod
    def _generate_level_id(price: float, level_type: LevelType, timeframe: str) -> str:
        """Generiert eindeutige Level-ID."""
        data = f"{price:.2f}:{level_type.value}:{timeframe}"
        return hashlib.md5(data.encode()).hexdigest()[:12]


# SINGLETON & CONVENIENCE FUNCTIONS
_global_engine: LevelEngine | None = None
_global_engine_lock = threading.Lock()


def get_level_engine(config: LevelEngineConfig | None = None) -> LevelEngine:
    """
    Gibt globale LevelEngine-Instanz zurück (Singleton).

    Usage:
        engine = get_level_engine()
        result = engine.detect_levels(df, "BTCUSD", "5m")
    """
    global _global_engine

    with _global_engine_lock:
        if _global_engine is None:
            _global_engine = LevelEngine(config)

        return _global_engine


def reset_level_engine() -> None:
    """Setzt globale Engine zurück."""
    global _global_engine

    with _global_engine_lock:
        _global_engine = None


def detect_levels(
    df: pd.DataFrame,
    symbol: str = "UNKNOWN",
    timeframe: str = "5m",
    current_price: Optional[float] = None,
) -> LevelsResult:
    """
    Convenience-Funktion für Level-Erkennung.

    Usage:
        result = detect_levels(df, "BTCUSD", "5m")
        support = result.get_nearest_support()
    """
    engine = get_level_engine()
    return engine.detect_levels(df, symbol, timeframe, current_price)
