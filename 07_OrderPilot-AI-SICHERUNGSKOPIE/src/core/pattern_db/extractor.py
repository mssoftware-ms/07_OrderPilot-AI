"""Pattern Extractor for OHLC Data.

Extracts sliding window patterns from historical OHLC data
for vector embedding and similarity search.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

import numpy as np

from src.core.market_data.types import HistoricalBar

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """A trading pattern extracted from OHLC data."""

    # Pattern identification
    symbol: str
    timeframe: str
    start_time: datetime
    end_time: datetime

    # Normalized OHLC data (window_size x 4)
    ohlc_normalized: np.ndarray

    # Raw values for context
    open_prices: list[float]
    high_prices: list[float]
    low_prices: list[float]
    close_prices: list[float]
    volumes: list[float]

    # Pattern metadata
    window_size: int
    price_change_pct: float  # % change from start to end
    volatility: float  # Standard deviation of returns
    trend_direction: str  # "up", "down", "sideways"
    volume_trend: str  # "increasing", "decreasing", "stable"

    # Outcome (for labeled patterns)
    outcome_bars: int = 0  # How many bars forward to measure outcome
    outcome_return_pct: float = 0.0  # Return after outcome_bars
    outcome_max_drawdown_pct: float = 0.0  # Max drawdown in outcome period
    outcome_label: str = ""  # "win", "loss", "neutral"

    # Additional metadata
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert pattern to dictionary for storage."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "window_size": self.window_size,
            "price_change_pct": self.price_change_pct,
            "volatility": self.volatility,
            "trend_direction": self.trend_direction,
            "volume_trend": self.volume_trend,
            "outcome_bars": self.outcome_bars,
            "outcome_return_pct": self.outcome_return_pct,
            "outcome_max_drawdown_pct": self.outcome_max_drawdown_pct,
            "outcome_label": self.outcome_label,
            "open_first": self.open_prices[0] if self.open_prices else 0,
            "close_last": self.close_prices[-1] if self.close_prices else 0,
            **self.metadata,
        }


class PatternExtractor:
    """Extracts trading patterns from OHLC data using sliding windows."""

    def __init__(
        self,
        window_size: int = 20,
        step_size: int = 1,
        outcome_bars: int = 5,
        min_volatility: float = 0.001,
    ):
        """Initialize pattern extractor.

        Args:
            window_size: Number of bars per pattern (default: 20 = ~20 min for 1Min data)
            step_size: Step between windows (1 = every bar, 5 = every 5th bar)
            outcome_bars: Bars forward to measure outcome
            min_volatility: Minimum volatility to include pattern
        """
        self.window_size = window_size
        self.step_size = step_size
        self.outcome_bars = outcome_bars
        self.min_volatility = min_volatility

    def extract_patterns(
        self,
        bars: list[HistoricalBar],
        symbol: str,
        timeframe: str,
    ) -> Iterator[Pattern]:
        """Extract patterns from a list of bars.

        Args:
            bars: List of historical bars
            symbol: Trading symbol
            timeframe: Timeframe string (e.g., "1Min")

        Yields:
            Pattern objects
        """
        if len(bars) < self.window_size + self.outcome_bars:
            logger.warning(f"Not enough bars for {symbol}: {len(bars)} < {self.window_size + self.outcome_bars}")
            return

        # Sort bars by timestamp
        sorted_bars = sorted(bars, key=lambda b: b.timestamp)

        # Extract patterns with sliding window
        for i in range(0, len(sorted_bars) - self.window_size - self.outcome_bars, self.step_size):
            window_bars = sorted_bars[i:i + self.window_size]
            outcome_bars = sorted_bars[i + self.window_size:i + self.window_size + self.outcome_bars]

            pattern = self._create_pattern(
                window_bars=window_bars,
                outcome_bars=outcome_bars,
                symbol=symbol,
                timeframe=timeframe,
            )

            if pattern and pattern.volatility >= self.min_volatility:
                yield pattern

    def _create_pattern(
        self,
        window_bars: list[HistoricalBar],
        outcome_bars: list[HistoricalBar],
        symbol: str,
        timeframe: str,
    ) -> Pattern | None:
        """Create a pattern from window bars.

        Args:
            window_bars: Bars in the pattern window
            outcome_bars: Bars after the window for outcome measurement
            symbol: Trading symbol
            timeframe: Timeframe string

        Returns:
            Pattern object or None if invalid
        """
        try:
            opens, highs, lows, closes, volumes = self._extract_ohlcv(window_bars)
            first_price = opens[0]
            if first_price <= 0:
                return None

            ohlc_normalized = self._normalize_ohlc(opens, highs, lows, closes, first_price)
            price_change_pct = (closes[-1] - opens[0]) / opens[0] * 100
            volatility = self._calculate_volatility(closes)
            trend_direction = self._classify_trend(price_change_pct)
            volume_trend = self._classify_volume_trend(volumes)

            outcome_return_pct, outcome_max_drawdown_pct, outcome_label = self._calculate_outcome(
                outcome_bars,
                closes[-1],
            )

            return Pattern(
                symbol=symbol,
                timeframe=timeframe,
                start_time=window_bars[0].timestamp,
                end_time=window_bars[-1].timestamp,
                ohlc_normalized=ohlc_normalized,
                open_prices=opens,
                high_prices=highs,
                low_prices=lows,
                close_prices=closes,
                volumes=volumes,
                window_size=self.window_size,
                price_change_pct=price_change_pct,
                volatility=volatility,
                trend_direction=trend_direction,
                volume_trend=volume_trend,
                outcome_bars=len(outcome_bars),
                outcome_return_pct=outcome_return_pct,
                outcome_max_drawdown_pct=outcome_max_drawdown_pct,
                outcome_label=outcome_label,
            )

        except Exception as e:
            logger.error(f"Error creating pattern: {e}")
            return None

    def _extract_ohlcv(self, window_bars: list[HistoricalBar]):
        opens = [float(b.open) for b in window_bars]
        highs = [float(b.high) for b in window_bars]
        lows = [float(b.low) for b in window_bars]
        closes = [float(b.close) for b in window_bars]
        volumes = [float(b.volume) if b.volume else 0 for b in window_bars]
        return opens, highs, lows, closes, volumes

    def _normalize_ohlc(
        self,
        opens: list[float],
        highs: list[float],
        lows: list[float],
        closes: list[float],
        first_price: float,
    ) -> np.ndarray:
        return np.array([
            [(o - first_price) / first_price * 100 for o in opens],
            [(h - first_price) / first_price * 100 for h in highs],
            [(l - first_price) / first_price * 100 for l in lows],
            [(c - first_price) / first_price * 100 for c in closes],
        ]).T

    def _calculate_volatility(self, closes: list[float]) -> float:
        returns = np.diff(closes) / np.array(closes[:-1])
        return float(np.std(returns)) if len(returns) > 0 else 0

    def _classify_trend(self, price_change_pct: float) -> str:
        if price_change_pct > 1.0:
            return "up"
        if price_change_pct < -1.0:
            return "down"
        return "sideways"

    def _classify_volume_trend(self, volumes: list[float]) -> str:
        half = len(volumes) // 2
        vol_first_half = np.mean(volumes[:half]) if half > 0 else 0
        vol_second_half = np.mean(volumes[half:]) if half > 0 else 0
        if vol_second_half > vol_first_half * 1.2:
            return "increasing"
        if vol_second_half < vol_first_half * 0.8:
            return "decreasing"
        return "stable"

    def _calculate_outcome(
        self,
        outcome_bars: list[HistoricalBar],
        entry_price: float,
    ) -> tuple[float, float, str]:
        outcome_return_pct = 0.0
        outcome_max_drawdown_pct = 0.0
        outcome_label = "neutral"

        if outcome_bars:
            outcome_closes = [float(b.close) for b in outcome_bars]
            exit_price = outcome_closes[-1]
            outcome_return_pct = (exit_price - entry_price) / entry_price * 100
            outcome_max_drawdown_pct = self._calculate_drawdown(entry_price, outcome_closes)
            outcome_label = self._classify_outcome(outcome_return_pct)

        return outcome_return_pct, outcome_max_drawdown_pct, outcome_label

    def _calculate_drawdown(self, entry_price: float, outcome_closes: list[float]) -> float:
        peak = entry_price
        max_dd = 0.0
        for close_price in outcome_closes:
            if close_price > peak:
                peak = close_price
            dd = (peak - close_price) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def _classify_outcome(self, outcome_return_pct: float) -> str:
        if outcome_return_pct > 0.5:
            return "win"
        if outcome_return_pct < -0.5:
            return "loss"
        return "neutral"

    def extract_current_pattern(
        self,
        bars: list[HistoricalBar],
        symbol: str,
        timeframe: str,
    ) -> Pattern | None:
        """Extract the most recent pattern (for live matching).

        Args:
            bars: Recent bars (at least window_size)
            symbol: Trading symbol
            timeframe: Timeframe string

        Returns:
            Most recent pattern or None
        """
        if len(bars) < self.window_size:
            logger.warning(f"Not enough bars for current pattern: {len(bars)} < {self.window_size}")
            return None

        # Get most recent window
        sorted_bars = sorted(bars, key=lambda b: b.timestamp)
        window_bars = sorted_bars[-self.window_size:]

        return self._create_pattern(
            window_bars=window_bars,
            outcome_bars=[],  # No outcome for current pattern
            symbol=symbol,
            timeframe=timeframe,
        )
