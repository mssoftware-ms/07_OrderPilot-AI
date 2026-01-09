"""MarketContext Factories - Factory functions for creating market context objects.

Module 7/8 of market_context.py split.

This module contains:
- create_empty_context: Create empty MarketContext for initialization
- create_indicator_snapshot_from_df: Create IndicatorSnapshot from pandas DataFrame
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .market_context_indicators import IndicatorSnapshot
from .market_context_main import MarketContext

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


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
