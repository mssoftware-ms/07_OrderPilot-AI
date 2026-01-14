"""
Signal Generator Indicator Snapshot - Indicator Extraction for Trade Logging.

Refactored from signal_generator.py.

Contains:
- extract_indicator_snapshot: Extracts all indicators from DataFrame for trade logging
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

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

        # Extract all indicators using helper methods
        ema_data = self._extract_ema_indicators(current, price)
        rsi_data = self._extract_rsi_indicators(current)
        macd_data = self._extract_macd_indicators(current)
        bb_data = self._extract_bollinger_bands(current, price)
        atr_data = self._extract_atr_indicators(current, price)
        adx_data = self._extract_adx_indicators(current)
        volume_data = self._extract_volume_indicators(current)
        timestamp = self._extract_timestamp(current)

        return IndicatorSnapshot(
            timestamp=timestamp,
            current_price=price if price else None,
            **ema_data,
            **rsi_data,
            **macd_data,
            **bb_data,
            **atr_data,
            **adx_data,
            **volume_data,
        )

    def _get_indicator_value(self, row: pd.Series, *names: str) -> Optional[Any]:
        """Get indicator value trying multiple column names."""
        for name in names:
            val = row.get(name)
            if val is not None:
                return val
        return None

    def _extract_ema_indicators(self, row: pd.Series, price: float) -> dict:
        """Extract EMA indicators and calculate distance."""
        ema20 = self._get_indicator_value(row, "ema_20", "EMA_20")
        ema50 = self._get_indicator_value(row, "ema_50", "EMA_50")
        ema200 = self._get_indicator_value(row, "ema_200", "EMA_200")

        ema20_dist = None
        if ema20 and price:
            ema20_dist = ((price - ema20) / ema20) * 100

        return {
            "ema_20": float(ema20) if ema20 else None,
            "ema_50": float(ema50) if ema50 else None,
            "ema_200": float(ema200) if ema200 else None,
            "ema_20_distance_pct": float(ema20_dist) if ema20_dist else None,
        }

    def _extract_rsi_indicators(self, row: pd.Series) -> dict:
        """Extract RSI indicators and determine state."""
        rsi = self._get_indicator_value(row, "rsi_14", "RSI_14", "rsi")

        rsi_state = None
        if rsi is not None:
            if rsi > 70:
                rsi_state = "OVERBOUGHT"
            elif rsi < 30:
                rsi_state = "OVERSOLD"
            else:
                rsi_state = "NEUTRAL"

        return {
            "rsi_14": float(rsi) if rsi is not None else None,
            "rsi_state": rsi_state,
        }

    def _extract_macd_indicators(self, row: pd.Series) -> dict:
        """Extract MACD indicators and determine crossover."""
        macd = self._get_indicator_value(row, "macd", "MACD")
        macd_signal = self._get_indicator_value(row, "macd_signal", "MACD_signal")
        macd_hist = self._get_indicator_value(row, "macd_hist", "MACD_hist")

        macd_crossover = None
        if macd is not None and macd_signal is not None:
            macd_crossover = "BULLISH" if macd > macd_signal else "BEARISH"

        return {
            "macd_line": float(macd) if macd is not None else None,
            "macd_signal": float(macd_signal) if macd_signal is not None else None,
            "macd_histogram": float(macd_hist) if macd_hist is not None else None,
            "macd_crossover": macd_crossover,
        }

    def _extract_bollinger_bands(self, row: pd.Series, price: float) -> dict:
        """Extract Bollinger Bands and calculate %B and width."""
        bb_upper = self._get_indicator_value(row, "bb_upper", "BB_upper")
        bb_middle = self._get_indicator_value(row, "bb_middle", "BB_middle")
        bb_lower = self._get_indicator_value(row, "bb_lower", "BB_lower")

        bb_pct_b = None
        bb_width = None
        if bb_upper and bb_lower and bb_middle and price:
            if bb_upper != bb_lower:
                bb_pct_b = (price - bb_lower) / (bb_upper - bb_lower)
                bb_width = (bb_upper - bb_lower) / bb_middle

        return {
            "bb_upper": float(bb_upper) if bb_upper else None,
            "bb_middle": float(bb_middle) if bb_middle else None,
            "bb_lower": float(bb_lower) if bb_lower else None,
            "bb_pct_b": float(bb_pct_b) if bb_pct_b is not None else None,
            "bb_width": float(bb_width) if bb_width is not None else None,
        }

    def _extract_atr_indicators(self, row: pd.Series, price: float) -> dict:
        """Extract ATR and calculate percentage."""
        atr = self._get_indicator_value(row, "atr_14", "ATR_14", "atr")

        atr_pct = None
        if atr and price:
            atr_pct = (atr / price) * 100

        return {
            "atr_14": float(atr) if atr else None,
            "atr_percent": float(atr_pct) if atr_pct else None,
        }

    def _extract_adx_indicators(self, row: pd.Series) -> dict:
        """Extract ADX and directional indicators."""
        adx = self._get_indicator_value(row, "adx_14", "ADX_14", "adx")
        plus_di = self._get_indicator_value(row, "plus_di", "+DI")
        minus_di = self._get_indicator_value(row, "minus_di", "-DI")

        return {
            "adx_14": float(adx) if adx else None,
            "plus_di": float(plus_di) if plus_di else None,
            "minus_di": float(minus_di) if minus_di else None,
        }

    def _extract_volume_indicators(self, row: pd.Series) -> dict:
        """Extract volume and calculate ratio."""
        volume = row.get("volume")
        volume_sma = row.get("volume_sma_20")

        volume_ratio = None
        if volume and volume_sma and volume_sma > 0:
            volume_ratio = volume / volume_sma

        return {
            "volume": float(volume) if volume else None,
            "volume_sma_20": float(volume_sma) if volume_sma else None,
            "volume_ratio": float(volume_ratio) if volume_ratio else None,
        }

    def _extract_timestamp(self, row: pd.Series) -> datetime:
        """Extract and parse timestamp."""
        timestamp = row.get("timestamp")
        if timestamp is None:
            return datetime.now(timezone.utc)
        elif isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp)
        return timestamp
