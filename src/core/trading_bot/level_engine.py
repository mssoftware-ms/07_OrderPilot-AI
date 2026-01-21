"""Level Engine - Refactored Main Orchestrator.

Refactored from 797 LOC monolith using composition pattern.

Module 4/4 - Main Orchestrator.

Delegates to 3 specialized helper modules:
- LevelEngineDetection: Swing, Pivot, Cluster, Daily H/L detection
- LevelEngineProcessing: Merge, Strength, Classify, Select

Provides:
- LevelEngine.detect_levels(): Main orchestration method
- Singleton pattern: get_level_engine()
- Convenience function: detect_levels()
"""

from __future__ import annotations

import hashlib
import logging
import threading
from typing import List, Optional

import pandas as pd

from src.core.trading_bot.level_engine_state import (
    DetectionMethod,
    Level,
    LevelEngineConfig,
    LevelsResult,
    LevelStrength,
    LevelType,
)
from src.core.trading_bot.level_engine_detection import LevelEngineDetection
from src.core.trading_bot.level_engine_processing import LevelEngineProcessing

logger = logging.getLogger(__name__)


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

        # Instantiate helper modules (composition pattern)
        self._detection = LevelEngineDetection(parent=self)
        self._processing = LevelEngineProcessing(parent=self)

    def detect_levels(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        timeframe: str = "5m",
        current_price: Optional[float] = None,
    ) -> LevelsResult:
        """
        Erkennt Levels aus DataFrame.

        Orchestrates 8 detection/processing steps:
            1. Calculate ATR (delegates to _detection)
            2. Swing High/Low detection (delegates to _detection)
            3. Pivot Points (delegates to _detection)
            4. Cluster detection (delegates to _detection)
            5. Daily H/L (delegates to _detection)
            6. Merge overlapping (delegates to _processing)
            7. Calculate strength (delegates to _processing)
            8. Classify as Support/Resistance (delegates to _processing)

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

            levels: List = []

            # Current price from last close if not provided
            if current_price is None:
                current_price = float(df["close"].iloc[-1])

            # 1. Calculate ATR for zone width (delegates to _detection)
            atr = self._detection.calculate_atr(df)

            # 2. Swing High/Low Detection (delegates to _detection)
            swing_levels = self._detection.detect_swing_levels(df, timeframe, atr)
            levels.extend(swing_levels)

            # 3. Pivot Points (delegates to _detection)
            if self.config.include_pivots:
                pivot_levels = self._detection.calculate_pivot_points(df, timeframe)
                levels.extend(pivot_levels)

            # 4. Cluster Detection (delegates to _detection)
            cluster_levels = self._detection.detect_clusters(df, timeframe, atr)
            levels.extend(cluster_levels)

            # 5. Historical Highs/Lows (delegates to _detection)
            if self.config.include_daily_hl:
                daily_levels = self._detection.detect_daily_hl(df, timeframe)
                levels.extend(daily_levels)

            # 6. Merge overlapping levels (delegates to _processing)
            levels = self._processing.merge_overlapping_levels(levels)

            # 7. Calculate strength (delegates to _processing)
            levels = self._processing.calculate_level_strength(levels, df)

            # 8. Classify as Support/Resistance (delegates to _processing)
            levels = self._processing.classify_levels(levels, current_price)

            # Sort and limit
            levels = sorted(levels, key=lambda l: l.price_mid)
            if len(levels) > self.config.max_levels:
                # Keep strongest levels (delegates to _processing)
                levels = self._processing.select_top_levels(levels, current_price)

            logger.debug(f"Detected {len(levels)} levels for {symbol} {timeframe}")

            return LevelsResult(
                levels=levels,
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
            )

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


# Re-export für backward compatibility
__all__ = [
    # Main class and functions
    "LevelEngine",
    "get_level_engine",
    "reset_level_engine",
    "detect_levels",
    # Re-exported from level_engine_state for convenience
    "Level",
    "LevelEngineConfig",
    "LevelsResult",
    "LevelType",
    "LevelStrength",
    "DetectionMethod",
]
