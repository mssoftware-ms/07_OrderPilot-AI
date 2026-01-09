"""Stream Bad Tick Filter - Real-time Filtering for Streaming Data.

Real-time bad tick filter for streaming data with rolling window context.

Module 5/6 of data_cleaning.py split (Lines 764-857).
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


class StreamBadTickFilter:
    """Real-time bad tick filter for streaming data.

    Maintains a rolling window for spike detection and filters incoming bars.
    """

    def __init__(
        self,
        detector,  # BadTickDetector | HampelBadTickDetector
        window_size: int = 100,
    ):
        """Initialize stream filter.

        Args:
            detector: BadTickDetector or HampelBadTickDetector instance
            window_size: Number of recent bars to keep for context
        """
        self.detector = detector
        self.window_size = window_size
        self.recent_bars: list[dict] = []

    def filter_bar(self, bar: dict) -> tuple[bool, str | None]:
        """Filter a single incoming bar.

        Args:
            bar: Bar data dict with keys: timestamp, open, high, low, close, volume

        Returns:
            Tuple of (is_valid, rejection_reason)
            - is_valid: True if bar is clean, False if bad tick
            - rejection_reason: None if valid, else reason string
        """
        # Quick validation checks (no context needed)
        reason = self._quick_validation(bar)
        if reason:
            logger.warning(f"❌ Bad tick rejected: {reason} | Bar: {bar}")
            return False, reason

        # Add to recent bars window
        self.recent_bars.append(bar)
        if len(self.recent_bars) > self.window_size:
            self.recent_bars.pop(0)

        # Convert to DataFrame for detector
        if len(self.recent_bars) < 2:
            # Not enough context for spike detection
            return True, None

        df = pd.DataFrame(self.recent_bars)
        bad_mask = self.detector.detect_bad_ticks(df)

        # Check if the latest bar (just added) is bad
        if bad_mask.iloc[-1]:
            reason = "Price spike or anomaly detected"
            logger.warning(f"❌ Bad tick rejected: {reason} | Bar: {bar}")
            # Remove from window
            self.recent_bars.pop()
            return False, reason

        return True, None

    def _quick_validation(self, bar: dict) -> str | None:
        """Quick validation without needing historical context.

        Returns:
            None if valid, else error message
        """
        # Check required fields
        required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for field in required_fields:
            if field not in bar:
                return f"Missing field: {field}"

        # Check zero/negative prices
        for price_field in ['open', 'high', 'low', 'close']:
            if bar[price_field] <= 0:
                return f"Invalid {price_field}: {bar[price_field]}"

        # Check OHLC consistency
        if bar['high'] < bar['low']:
            return f"High ({bar['high']}) < Low ({bar['low']})"

        if not (bar['low'] <= bar['open'] <= bar['high']):
            return f"Open ({bar['open']}) outside [Low, High]"

        if not (bar['low'] <= bar['close'] <= bar['high']):
            return f"Close ({bar['close']}) outside [Low, High]"

        # Check negative volume
        if bar['volume'] < 0:
            return f"Negative volume: {bar['volume']}"

        return None
