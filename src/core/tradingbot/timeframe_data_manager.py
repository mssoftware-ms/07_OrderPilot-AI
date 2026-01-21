"""Timeframe Data Manager for Multi-Timeframe Analysis.

Manages OHLCV data across multiple timeframes with automatic alignment,
resampling, and caching for optimal performance.

Key Features:
- Multi-timeframe data management (1m, 5m, 15m, 1h, 4h, 1d, etc.)
- Automatic data alignment and synchronization
- Bar resampling from lower to higher timeframes
- Efficient caching to minimize recomputation
- Thread-safe operations for concurrent access

Example:
    >>> manager = TimeframeDataManager(base_timeframe="1T")
    >>> manager.add_timeframe("5T")  # 5 minutes
    >>> manager.add_timeframe("1H")  # 1 hour
    >>>
    >>> # Feed 1-minute bars
    >>> manager.add_bar("1T", bar_data)
    >>>
    >>> # Get aligned data across all timeframes
    >>> aligned_data = manager.get_aligned_data()
    >>> # {'1T': [...], '5T': [...], '1H': [...]}
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# Timeframe conversion mapping (to pandas offset aliases)
TIMEFRAME_ALIASES = {
    "1m": "1T",
    "5m": "5T",
    "15m": "15T",
    "30m": "30T",
    "1h": "1H",
    "4h": "4H",
    "1d": "1D",
    "1w": "1W",
    # Standard aliases
    "1T": "1T",
    "5T": "5T",
    "15T": "15T",
    "30T": "30T",
    "1H": "1H",
    "4H": "4H",
    "1D": "1D",
    "1W": "1W",
}


@dataclass
class TimeframeBar:
    """Single OHLCV bar for a specific timeframe."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str

    # Tracking
    bar_count: int = 1  # Number of base bars aggregated
    complete: bool = False  # Is this bar complete (closed)?

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass
class TimeframeData:
    """Data container for a single timeframe."""
    timeframe: str
    bars: deque[TimeframeBar] = field(default_factory=lambda: deque(maxlen=1000))
    max_bars: int = 1000

    # Current incomplete bar (being built from base bars)
    current_bar: TimeframeBar | None = None

    # Cache for resampled data
    cache_valid: bool = False
    cached_df: pd.DataFrame | None = None

    def add_bar(self, bar: TimeframeBar) -> None:
        """Add completed bar to history."""
        self.bars.append(bar)
        self.cache_valid = False  # Invalidate cache

    def get_last_n_bars(self, n: int) -> list[TimeframeBar]:
        """Get last N bars."""
        return list(self.bars)[-n:] if n <= len(self.bars) else list(self.bars)

    def get_dataframe(self, use_cache: bool = True) -> pd.DataFrame:
        """Convert bars to DataFrame.

        Args:
            use_cache: Use cached DataFrame if valid

        Returns:
            DataFrame with OHLCV columns indexed by timestamp
        """
        if use_cache and self.cache_valid and self.cached_df is not None:
            return self.cached_df

        if not self.bars:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        data = [bar.to_dict() for bar in self.bars]
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)

        # Cache result
        self.cached_df = df
        self.cache_valid = True

        return df


class TimeframeDataManager:
    """Manager for multi-timeframe OHLCV data.

    Handles data storage, resampling, alignment, and caching
    across multiple timeframes efficiently.
    """

    def __init__(
        self,
        base_timeframe: str = "1T",
        max_bars_per_tf: int = 1000,
        auto_resample: bool = True
    ):
        """Initialize TimeframeDataManager.

        Args:
            base_timeframe: Base timeframe (smallest resolution)
            max_bars_per_tf: Maximum bars to store per timeframe
            auto_resample: Automatically resample higher timeframes
        """
        self.base_timeframe = self._normalize_timeframe(base_timeframe)
        self.max_bars_per_tf = max_bars_per_tf
        self.auto_resample = auto_resample

        # Data storage per timeframe
        self._data: dict[str, TimeframeData] = {}

        # Timeframe hierarchy (ordered from smallest to largest)
        self._timeframes: list[str] = []

        # Thread safety
        self._lock = Lock()

        # Statistics
        self._stats = {
            "bars_added": 0,
            "resamples_performed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Add base timeframe
        self.add_timeframe(self.base_timeframe)

        logger.info(f"TimeframeDataManager initialized with base TF: {self.base_timeframe}")

    def _normalize_timeframe(self, tf: str) -> str:
        """Normalize timeframe to pandas alias."""
        return TIMEFRAME_ALIASES.get(tf, tf)

    def _get_timeframe_seconds(self, tf: str) -> int:
        """Get timeframe duration in seconds."""
        # Parse pandas offset string
        freq = pd.Timedelta(tf)
        return int(freq.total_seconds())

    def add_timeframe(self, timeframe: str) -> None:
        """Add a new timeframe to manage.

        Args:
            timeframe: Timeframe string (e.g., "5T", "1H", "1D")
        """
        tf = self._normalize_timeframe(timeframe)

        with self._lock:
            if tf not in self._data:
                self._data[tf] = TimeframeData(
                    timeframe=tf,
                    max_bars=self.max_bars_per_tf
                )

                # Insert in sorted order (smallest to largest)
                self._timeframes.append(tf)
                self._timeframes.sort(key=self._get_timeframe_seconds)

                logger.info(f"Added timeframe: {tf}")

    def add_bar(self, timeframe: str, bar_data: dict[str, Any]) -> None:
        """Add a bar to the specified timeframe.

        Args:
            timeframe: Target timeframe
            bar_data: Bar dictionary with OHLCV + timestamp
        """
        tf = self._normalize_timeframe(timeframe)

        if tf not in self._data:
            logger.warning(f"Timeframe {tf} not registered. Adding it now.")
            self.add_timeframe(tf)

        with self._lock:
            # Create TimeframeBar
            bar = TimeframeBar(
                timestamp=bar_data["timestamp"],
                open=bar_data["open"],
                high=bar_data["high"],
                low=bar_data["low"],
                close=bar_data["close"],
                volume=bar_data.get("volume", 0.0),
                timeframe=tf,
                complete=True,  # Assume bars are complete when added
            )

            # Add to storage
            self._data[tf].add_bar(bar)
            self._stats["bars_added"] += 1

            # Auto-resample higher timeframes if enabled
            if self.auto_resample and tf == self.base_timeframe:
                self._resample_higher_timeframes(bar)

    def _resample_higher_timeframes(self, base_bar: TimeframeBar) -> None:
        """Resample higher timeframes from base timeframe.

        Args:
            base_bar: Latest base timeframe bar
        """
        base_idx = self._timeframes.index(self.base_timeframe)

        for higher_tf in self._timeframes[base_idx + 1:]:
            self._resample_bar(higher_tf, base_bar)

    def _resample_bar(self, target_tf: str, base_bar: TimeframeBar) -> None:
        """Resample a single bar from base to target timeframe.

        Args:
            target_tf: Target timeframe to resample to
            base_bar: Base timeframe bar
        """
        tf_data = self._data[target_tf]

        # Calculate target bar timestamp (align to period boundary)
        target_timestamp = self._align_timestamp(base_bar.timestamp, target_tf)

        # Check if we have an incomplete bar for this period
        if tf_data.current_bar is None or tf_data.current_bar.timestamp != target_timestamp:
            # Start new bar
            if tf_data.current_bar is not None and tf_data.current_bar.bar_count > 0:
                # Complete previous bar
                tf_data.current_bar.complete = True
                tf_data.add_bar(tf_data.current_bar)

            # Create new incomplete bar
            tf_data.current_bar = TimeframeBar(
                timestamp=target_timestamp,
                open=base_bar.open,
                high=base_bar.high,
                low=base_bar.low,
                close=base_bar.close,
                volume=base_bar.volume,
                timeframe=target_tf,
                bar_count=1,
                complete=False,
            )
        else:
            # Update existing incomplete bar
            tf_data.current_bar.high = max(tf_data.current_bar.high, base_bar.high)
            tf_data.current_bar.low = min(tf_data.current_bar.low, base_bar.low)
            tf_data.current_bar.close = base_bar.close
            tf_data.current_bar.volume += base_bar.volume
            tf_data.current_bar.bar_count += 1

        self._stats["resamples_performed"] += 1

    def _align_timestamp(self, timestamp: datetime, timeframe: str) -> datetime:
        """Align timestamp to timeframe period boundary.

        Args:
            timestamp: Original timestamp
            timeframe: Target timeframe

        Returns:
            Aligned timestamp at period start
        """
        # Use pandas for alignment
        ts = pd.Timestamp(timestamp)
        freq = pd.Timedelta(timeframe)

        # Floor to period boundary
        aligned = ts.floor(freq)

        return aligned.to_pydatetime()

    def get_bars(
        self,
        timeframe: str,
        n: int | None = None,
        as_dataframe: bool = False
    ) -> list[TimeframeBar] | pd.DataFrame:
        """Get bars for a specific timeframe.

        Args:
            timeframe: Target timeframe
            n: Number of bars (None = all)
            as_dataframe: Return as DataFrame instead of list

        Returns:
            List of TimeframeBar or DataFrame
        """
        tf = self._normalize_timeframe(timeframe)

        if tf not in self._data:
            logger.warning(f"Timeframe {tf} not found")
            return pd.DataFrame() if as_dataframe else []

        with self._lock:
            if as_dataframe:
                df = self._data[tf].get_dataframe(use_cache=True)
                if n is not None:
                    return df.tail(n)
                return df
            else:
                if n is None:
                    return list(self._data[tf].bars)
                return self._data[tf].get_last_n_bars(n)

    def get_aligned_data(
        self,
        timeframes: list[str] | None = None,
        n: int | None = None
    ) -> dict[str, pd.DataFrame]:
        """Get aligned data across multiple timeframes.

        Aligns timestamps so each timeframe has data for the same
        time periods (useful for multi-TF indicator calculation).

        Args:
            timeframes: List of timeframes (None = all)
            n: Number of aligned periods (None = all)

        Returns:
            Dict mapping timeframe to aligned DataFrame
        """
        tfs = timeframes or self._timeframes
        tfs = [self._normalize_timeframe(tf) for tf in tfs]

        with self._lock:
            # Get DataFrames for each timeframe
            dfs = {}
            for tf in tfs:
                if tf in self._data:
                    dfs[tf] = self._data[tf].get_dataframe(use_cache=True)

            if not dfs:
                return {}

            # Find common timestamp range
            # Use the largest timeframe's timestamps as reference
            largest_tf = tfs[-1]
            ref_timestamps = dfs[largest_tf].index

            # Limit to n most recent
            if n is not None:
                ref_timestamps = ref_timestamps[-n:]

            # Align all timeframes to reference timestamps
            aligned = {}
            for tf, df in dfs.items():
                if tf == largest_tf:
                    aligned[tf] = df.loc[ref_timestamps]
                else:
                    # For smaller timeframes, get bars within each ref period
                    # Use forward-fill to get latest bar <= ref timestamp
                    aligned[tf] = df.reindex(
                        df.index.union(ref_timestamps),
                        method='ffill'
                    ).loc[ref_timestamps]

            return aligned

    def clear_timeframe(self, timeframe: str) -> None:
        """Clear all data for a specific timeframe.

        Args:
            timeframe: Timeframe to clear
        """
        tf = self._normalize_timeframe(timeframe)

        with self._lock:
            if tf in self._data:
                self._data[tf].bars.clear()
                self._data[tf].current_bar = None
                self._data[tf].cache_valid = False
                logger.info(f"Cleared data for timeframe: {tf}")

    def get_stats(self) -> dict[str, int]:
        """Get manager statistics.

        Returns:
            Dict with stats (bars_added, resamples, cache hits/misses)
        """
        with self._lock:
            return {
                **self._stats,
                "total_timeframes": len(self._timeframes),
                "total_bars": sum(len(tf_data.bars) for tf_data in self._data.values()),
            }

    def get_timeframes(self) -> list[str]:
        """Get list of registered timeframes (sorted smallest to largest)."""
        return self._timeframes.copy()

    def warmup_from_history(
        self,
        timeframe: str,
        historical_bars: list[dict[str, Any]]
    ) -> None:
        """Warmup timeframe with historical data.

        Args:
            timeframe: Timeframe for historical bars
            historical_bars: List of bar dictionaries
        """
        tf = self._normalize_timeframe(timeframe)

        logger.info(f"Warming up {tf} with {len(historical_bars)} bars")

        for bar_data in historical_bars:
            self.add_bar(tf, bar_data)

        logger.info(f"Warmup complete for {tf}")


# ==================== Multi-Timeframe Feature Engine Integration ====================


class MultiTimeframeFeatureEngine:
    """Feature engine that calculates indicators across multiple timeframes.

    Integrates TimeframeDataManager with FeatureEngine for multi-TF analysis.
    """

    def __init__(
        self,
        timeframes: list[str],
        base_timeframe: str = "1T",
        indicator_periods: dict[str, dict[str, int]] | None = None
    ):
        """Initialize multi-timeframe feature engine.

        Args:
            timeframes: List of timeframes to analyze
            base_timeframe: Base (smallest) timeframe
            indicator_periods: Custom periods per timeframe
                             {'1T': {'sma': 20}, '1H': {'sma': 50}}
        """
        from .feature_engine import FeatureEngine

        self.timeframes = [TIMEFRAME_ALIASES.get(tf, tf) for tf in timeframes]
        self.base_timeframe = TIMEFRAME_ALIASES.get(base_timeframe, base_timeframe)

        # Data manager
        self.data_manager = TimeframeDataManager(
            base_timeframe=self.base_timeframe,
            auto_resample=True
        )

        # Register all timeframes
        for tf in self.timeframes:
            self.data_manager.add_timeframe(tf)

        # Feature engines per timeframe
        self.feature_engines: dict[str, FeatureEngine] = {}
        for tf in self.timeframes:
            periods = indicator_periods.get(tf) if indicator_periods else None
            self.feature_engines[tf] = FeatureEngine(periods=periods)

        logger.info(f"MultiTimeframeFeatureEngine initialized with TFs: {self.timeframes}")

    def process_bar(self, bar_data: dict[str, Any]) -> dict[str, Any]:
        """Process a base timeframe bar and calculate features across all TFs.

        Args:
            bar_data: Base timeframe bar

        Returns:
            Dict with features per timeframe:
            {'1T': FeatureVector, '5T': FeatureVector, '1H': FeatureVector}
        """
        # Add bar to data manager (will auto-resample)
        self.data_manager.add_bar(self.base_timeframe, bar_data)

        # Get aligned data across all timeframes
        aligned_data = self.data_manager.get_aligned_data(n=200)  # Get enough for indicators

        # Calculate features for each timeframe
        features = {}
        for tf in self.timeframes:
            if tf not in aligned_data or aligned_data[tf].empty:
                continue

            # Get feature engine for this timeframe
            engine = self.feature_engines[tf]

            # Calculate features from DataFrame
            df = aligned_data[tf]
            if len(df) >= engine.MIN_BARS:
                # Process last bar
                last_bar = {
                    "timestamp": df.index[-1],
                    "open": df["open"].iloc[-1],
                    "high": df["high"].iloc[-1],
                    "low": df["low"].iloc[-1],
                    "close": df["close"].iloc[-1],
                    "volume": df["volume"].iloc[-1],
                }

                # Calculate features (requires warmup with full DataFrame)
                # For now, return basic features - full integration needs FeatureEngine refactor
                features[tf] = last_bar

        return features
