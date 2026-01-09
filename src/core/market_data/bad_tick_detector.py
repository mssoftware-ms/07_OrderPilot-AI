"""Bad Tick Detector - Detection and Cleaning Logic.

Handles bad tick detection using multiple methods:
- Hampel Filter (Modified Z-score with MAD)
- Z-Score Outlier Detection
- Basic OHLC Consistency Checks

Module 2/4 of historical_data_manager.py split (Lines 415-682).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .historical_data_config import FilterConfig, FilterStats

logger = logging.getLogger(__name__)


class BadTickDetector:
    """Detects and cleans bad ticks using configurable methods.

    Supports three detection methods:
    - Hampel: Modified Z-score using Median Absolute Deviation (MAD)
    - Z-score: Standard deviation-based outlier detection
    - Basic: OHLC consistency and volume spike checks
    """

    def __init__(self, config: FilterConfig):
        """
        Initialize detector with configuration.

        Args:
            config: FilterConfig instance
        """
        self.config = config

    async def filter_bad_ticks(
        self, bars: list, symbol: str
    ) -> tuple[list, FilterStats]:
        """
        Apply bad tick filtering to bars.

        Args:
            bars: List of Bar objects
            symbol: Trading symbol for logging

        Returns:
            Tuple of (cleaned_bars, stats)
        """
        if not self.config.enabled or not bars:
            return bars, FilterStats(total_bars=len(bars))

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "timestamp": b.timestamp,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars
        ])

        original_len = len(df)
        stats = FilterStats(total_bars=original_len)

        # Detect bad ticks
        bad_mask = self._detect_bad_ticks(df)
        bad_count = bad_mask.sum()
        stats.bad_ticks_found = int(bad_count)

        if bad_count == 0:
            if self.config.log_stats:
                logger.info(f"✅ {symbol}: No bad ticks found ({original_len} bars)")
            return bars, stats

        # Clean bad ticks
        if self.config.cleaning_mode == "interpolate":
            df = self._interpolate_bad_ticks(df, bad_mask)
            stats.bad_ticks_interpolated = int(bad_count)
        elif self.config.cleaning_mode == "forward_fill":
            df = self._forward_fill_bad_ticks(df, bad_mask)
            stats.bad_ticks_interpolated = int(bad_count)
        elif self.config.cleaning_mode == "remove":
            df = df[~bad_mask].copy()
            stats.bad_ticks_removed = int(bad_count)
        else:
            logger.warning(f"Unknown cleaning_mode: {self.config.cleaning_mode}")
            return bars, stats

        stats.filtering_percentage = (bad_count / original_len * 100) if original_len > 0 else 0.0

        if self.config.log_stats:
            logger.info(
                f"🧹 {symbol}: Filtered {bad_count}/{original_len} bars ({stats.filtering_percentage:.2f}%) "
                f"using {self.config.method} method, mode={self.config.cleaning_mode}"
            )

        # Convert back to Bar objects
        from alpaca.data.models.bars import Bar
        from datetime import datetime

        cleaned_bars = []
        for _, row in df.iterrows():
            ts = row["timestamp"]
            if not isinstance(ts, datetime):
                ts = pd.to_datetime(ts)
            cleaned_bars.append(
                Bar(
                    symbol=bars[0].symbol if bars else symbol,
                    timestamp=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                    trade_count=getattr(bars[0], "trade_count", 0) if bars else 0,
                    vwap=getattr(bars[0], "vwap", None) if bars else None,
                )
            )

        return cleaned_bars, stats

    def _detect_bad_ticks(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect bad ticks using configured method.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Boolean mask (True = bad tick)
        """
        if self.config.method == "hampel":
            return self._detect_hampel_outliers(df)
        elif self.config.method == "zscore":
            return self._detect_zscore_outliers(df)
        elif self.config.method == "basic":
            return self._detect_basic_outliers(df)
        else:
            logger.warning(f"Unknown detection method: {self.config.method}, using basic")
            return self._detect_basic_outliers(df)

    def _detect_hampel_outliers(self, df: pd.DataFrame) -> pd.Series:
        """
        Hampel Filter: Modified Z-score using Median Absolute Deviation (MAD).

        More robust than standard Z-score for financial data with fat tails.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Boolean mask (True = outlier)
        """
        bad_mask = pd.Series(False, index=df.index)

        for col in ["close", "high", "low", "open"]:
            if col not in df.columns:
                continue

            values = df[col].values
            n = len(values)
            window = self.config.hampel_window

            # Rolling median and MAD
            for i in range(window, n - window):
                window_values = values[i - window : i + window + 1]
                median = np.median(window_values)
                mad = np.median(np.abs(window_values - median))

                if mad == 0:
                    continue

                # Modified Z-score
                modified_z_score = 0.6745 * (values[i] - median) / mad

                if abs(modified_z_score) > self.config.hampel_threshold:
                    bad_mask.iloc[i] = True

        return bad_mask

    def _detect_zscore_outliers(self, df: pd.DataFrame) -> pd.Series:
        """
        Z-Score outlier detection (standard deviations from mean).

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Boolean mask (True = outlier)
        """
        bad_mask = pd.Series(False, index=df.index)

        for col in ["close", "high", "low", "open"]:
            if col not in df.columns:
                continue

            values = df[col]
            mean = values.mean()
            std = values.std()

            if std == 0:
                continue

            z_scores = np.abs((values - mean) / std)
            bad_mask |= z_scores > self.config.zscore_threshold

        return bad_mask

    def _detect_basic_outliers(self, df: pd.DataFrame) -> pd.Series:
        """
        Basic OHLC consistency checks and volume spikes.

        Detects:
        - OHLC relationship violations (high < low, close outside high/low)
        - Extreme volume spikes
        - Zero or negative prices

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Boolean mask (True = bad tick)
        """
        bad_mask = pd.Series(False, index=df.index)

        # OHLC consistency
        if all(col in df.columns for col in ["open", "high", "low", "close"]):
            bad_mask |= df["high"] < df["low"]
            bad_mask |= df["close"] > df["high"]
            bad_mask |= df["close"] < df["low"]
            bad_mask |= df["open"] > df["high"]
            bad_mask |= df["open"] < df["low"]

        # Zero or negative prices
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                bad_mask |= df[col] <= 0

        # Volume spikes
        if "volume" in df.columns:
            vol_median = df["volume"].rolling(window=20, min_periods=1).median()
            bad_mask |= df["volume"] > (vol_median * self.config.volume_multiplier)
            bad_mask |= df["volume"] < 0

        return bad_mask

    def _interpolate_bad_ticks(self, df: pd.DataFrame, bad_mask: pd.Series) -> pd.DataFrame:
        """
        Interpolate bad ticks using linear interpolation.

        Args:
            df: DataFrame with OHLCV data
            bad_mask: Boolean mask of bad ticks

        Returns:
            DataFrame with interpolated values
        """
        df = df.copy()

        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                continue

            # Set bad values to NaN
            df.loc[bad_mask, col] = np.nan

            # Interpolate
            df[col] = df[col].interpolate(method="linear", limit_direction="both")

            # Forward fill if interpolation fails
            df[col] = df[col].fillna(method="ffill")

            # Backward fill if still NaN
            df[col] = df[col].fillna(method="bfill")

        return df

    def _forward_fill_bad_ticks(self, df: pd.DataFrame, bad_mask: pd.Series) -> pd.DataFrame:
        """
        Forward fill bad ticks with previous valid values.

        Args:
            df: DataFrame with OHLCV data
            bad_mask: Boolean mask of bad ticks

        Returns:
            DataFrame with forward-filled values
        """
        df = df.copy()

        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                continue

            # Set bad values to NaN
            df.loc[bad_mask, col] = np.nan

            # Forward fill
            df[col] = df[col].fillna(method="ffill")

            # Backward fill if still NaN
            df[col] = df[col].fillna(method="bfill")

        return df
