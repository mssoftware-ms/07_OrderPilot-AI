"""MarketContext Candles - Candle summary data models.

Module 2/8 of market_context.py split.

This module contains:
- CandleSummary: OHLCV data with derived metrics (body size, wicks, range)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


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
