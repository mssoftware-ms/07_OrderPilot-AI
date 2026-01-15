"""
Signal Generator Indicator Snapshot - Indicator Extraction for Trade Logging.

Refactored from signal_generator.py.

Contains:
- extract_indicator_snapshot: Extracts all indicators from DataFrame for trade logging
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .signal_generator import SignalGenerator
    from .trade_logger import IndicatorSnapshot


class SignalGeneratorIndicatorSnapshot:
    """Helper for indicator snapshot extraction."""

    def __init__(self, parent: SignalGenerator):
        self.parent = parent

    def extract_indicator_snapshot(self, df: pd.DataFrame) -> "IndicatorSnapshot":
        """
        Extrahiert Indikator-Snapshot aus DataFrame.

        Für Trade-Logging.
        """
        from .trade_logger import IndicatorSnapshot

        if df.empty:
            return IndicatorSnapshot(timestamp=datetime.now(timezone.utc))

        current = df.iloc[-1]
        price = float(current.get("close", 0))

        # EMA Werte
        ema20 = current.get("ema_20") or current.get("EMA_20")
        ema50 = current.get("ema_50") or current.get("EMA_50")
        ema200 = current.get("ema_200") or current.get("EMA_200")

        ema20_dist = None
        if ema20 and price:
            ema20_dist = ((price - ema20) / ema20) * 100

        # RSI
        rsi = current.get("rsi_14") or current.get("RSI_14") or current.get("rsi")
        rsi_state = None
        if rsi is not None:
            if rsi > 70:
                rsi_state = "OVERBOUGHT"
            elif rsi < 30:
                rsi_state = "OVERSOLD"
            else:
                rsi_state = "NEUTRAL"

        # MACD
        macd = current.get("macd") or current.get("MACD")
        macd_signal = current.get("macd_signal") or current.get("MACD_signal")
        macd_hist = current.get("macd_hist") or current.get("MACD_hist")

        macd_crossover = None
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                macd_crossover = "BULLISH"
            else:
                macd_crossover = "BEARISH"

        # Bollinger Bands
        bb_upper = current.get("bb_upper") or current.get("BB_upper")
        bb_middle = current.get("bb_middle") or current.get("BB_middle")
        bb_lower = current.get("bb_lower") or current.get("BB_lower")

        bb_pct_b = None
        bb_width = None
        if bb_upper and bb_lower and bb_middle and price:
            if bb_upper != bb_lower:
                bb_pct_b = (price - bb_lower) / (bb_upper - bb_lower)
                bb_width = (bb_upper - bb_lower) / bb_middle

        # ATR
        atr = current.get("atr_14") or current.get("ATR_14") or current.get("atr")
        atr_pct = None
        if atr and price:
            atr_pct = (atr / price) * 100

        # ADX
        adx = current.get("adx_14") or current.get("ADX_14") or current.get("adx")
        plus_di = current.get("plus_di") or current.get("+DI")
        minus_di = current.get("minus_di") or current.get("-DI")

        # Volume
        volume = current.get("volume")
        volume_sma = current.get("volume_sma_20")
        volume_ratio = None
        if volume and volume_sma and volume_sma > 0:
            volume_ratio = volume / volume_sma

        # Timestamp
        timestamp = current.get("timestamp")
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return IndicatorSnapshot(
            timestamp=timestamp,
            ema_20=float(ema20) if ema20 else None,
            ema_50=float(ema50) if ema50 else None,
            ema_200=float(ema200) if ema200 else None,
            ema_20_distance_pct=float(ema20_dist) if ema20_dist else None,
            rsi_14=float(rsi) if rsi is not None else None,
            rsi_state=rsi_state,
            macd_line=float(macd) if macd is not None else None,
            macd_signal=float(macd_signal) if macd_signal is not None else None,
            macd_histogram=float(macd_hist) if macd_hist is not None else None,
            macd_crossover=macd_crossover,
            bb_upper=float(bb_upper) if bb_upper else None,
            bb_middle=float(bb_middle) if bb_middle else None,
            bb_lower=float(bb_lower) if bb_lower else None,
            bb_pct_b=float(bb_pct_b) if bb_pct_b is not None else None,
            bb_width=float(bb_width) if bb_width is not None else None,
            atr_14=float(atr) if atr else None,
            atr_percent=float(atr_pct) if atr_pct else None,
            adx_14=float(adx) if adx else None,
            plus_di=float(plus_di) if plus_di else None,
            minus_di=float(minus_di) if minus_di else None,
            volume=float(volume) if volume else None,
            volume_sma_20=float(volume_sma) if volume_sma else None,
            volume_ratio=float(volume_ratio) if volume_ratio else None,
            current_price=price if price else None,
        )
