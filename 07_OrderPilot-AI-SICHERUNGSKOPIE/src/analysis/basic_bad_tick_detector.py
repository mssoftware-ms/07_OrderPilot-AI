"""Basic Bad Tick Detector - Threshold-based Detection.

Detects bad ticks using:
- OHLC consistency checks
- Price spike detection (moving average deviation)
- Volume anomaly detection
- Duplicate timestamp detection
- Zero/negative price detection

Module 2/6 of data_cleaning.py split (Lines 34-267).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .cleaning_types import CleaningStats

logger = logging.getLogger(__name__)


class BadTickDetector:
    """Detects and removes bad ticks from market data using threshold-based methods."""

    def __init__(
        self,
        max_price_deviation_pct: float = 10.0,
        min_volume: int = 0,
        max_volume_multiplier: float = 100.0,
        ma_window: int = 20,
        check_ohlc_consistency: bool = True,
        check_price_spikes: bool = True,
        check_volume_anomalies: bool = True,
        check_duplicates: bool = True,
    ):
        """Initialize bad tick detector.

        Args:
            max_price_deviation_pct: Max allowed deviation from moving average (%)
            min_volume: Minimum valid volume (0 = allow zero volume)
            max_volume_multiplier: Max volume as multiplier of average volume
            ma_window: Moving average window for spike detection
            check_ohlc_consistency: Check OHLC relationship consistency
            check_price_spikes: Check for unrealistic price spikes
            check_volume_anomalies: Check for volume anomalies
            check_duplicates: Check for duplicate timestamps
        """
        self.max_price_deviation_pct = max_price_deviation_pct
        self.min_volume = min_volume
        self.max_volume_multiplier = max_volume_multiplier
        self.ma_window = ma_window
        self.check_ohlc_consistency = check_ohlc_consistency
        self.check_price_spikes = check_price_spikes
        self.check_volume_anomalies = check_volume_anomalies
        self.check_duplicates = check_duplicates

    def detect_bad_ticks(self, df: pd.DataFrame) -> pd.Series:
        """Detect bad ticks in DataFrame.

        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume

        Returns:
            Boolean Series: True = bad tick, False = good tick
        """
        if df.empty:
            return pd.Series(dtype=bool)

        bad_mask = pd.Series(False, index=df.index)
        bad_tick_counts = {}

        # 1. OHLC Consistency Checks
        if self.check_ohlc_consistency:
            ohlc_bad = self._check_ohlc_consistency(df)
            bad_mask |= ohlc_bad
            bad_tick_counts['ohlc_inconsistency'] = ohlc_bad.sum()

        # 2. Price Spike Detection
        if self.check_price_spikes:
            spike_bad = self._check_price_spikes(df)
            bad_mask |= spike_bad
            bad_tick_counts['price_spike'] = spike_bad.sum()

        # 3. Volume Anomaly Detection
        if self.check_volume_anomalies:
            volume_bad = self._check_volume_anomalies(df)
            bad_mask |= volume_bad
            bad_tick_counts['volume_anomaly'] = volume_bad.sum()

        # 4. Duplicate Timestamp Detection
        if self.check_duplicates:
            duplicate_bad = self._check_duplicates(df)
            bad_mask |= duplicate_bad
            bad_tick_counts['duplicate_timestamp'] = duplicate_bad.sum()

        # 5. Zero/Negative Price Check
        zero_price_bad = self._check_zero_negative_prices(df)
        bad_mask |= zero_price_bad
        bad_tick_counts['zero_negative_price'] = zero_price_bad.sum()

        # Log summary
        total_bad = bad_mask.sum()
        if total_bad > 0:
            logger.warning(f"Detected {total_bad} bad ticks ({total_bad/len(df)*100:.2f}%)")
            for tick_type, count in bad_tick_counts.items():
                if count > 0:
                    logger.warning(f"  - {tick_type}: {count}")

        return bad_mask

    def clean_data(self, df: pd.DataFrame, method: str = "remove") -> tuple[pd.DataFrame, CleaningStats]:
        """Clean bad ticks from DataFrame.

        Args:
            df: DataFrame with market data
            method: Cleaning method:
                - "remove": Remove bad ticks entirely
                - "interpolate": Replace bad ticks with interpolated values
                - "forward_fill": Use previous valid value

        Returns:
            Tuple of (cleaned DataFrame, cleaning statistics)
        """
        if df.empty:
            return df, CleaningStats(0, 0, {}, 0.0)

        original_count = len(df)
        bad_mask = self.detect_bad_ticks(df)
        bad_count = bad_mask.sum()

        if bad_count == 0:
            logger.info("✅ No bad ticks detected - data is clean")
            return df, CleaningStats(original_count, 0, {}, 0.0)

        # Apply cleaning method
        if method == "remove":
            df_clean = df[~bad_mask].copy()
            logger.info(f"🧹 Removed {bad_count} bad ticks ({bad_count/original_count*100:.2f}%)")

        elif method == "interpolate":
            df_clean = df.copy()
            # Interpolate only numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df_clean.columns:
                    df_clean.loc[bad_mask, col] = np.nan
                    df_clean[col] = df_clean[col].interpolate(method='linear', limit_direction='both')
            logger.info(f"🔧 Interpolated {bad_count} bad ticks")

        elif method == "forward_fill":
            df_clean = df.copy()
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df_clean.columns:
                    df_clean.loc[bad_mask, col] = np.nan
                    df_clean[col] = df_clean[col].fillna(method='ffill')
            logger.info(f"⏭️ Forward-filled {bad_count} bad ticks")

        else:
            raise ValueError(f"Unknown cleaning method: {method}")

        stats = CleaningStats(
            total_bars=original_count,
            bad_ticks_removed=bad_count,
            bad_tick_types={},  # TODO: Track by type
            cleaning_percentage=bad_count / original_count * 100
        )

        return df_clean, stats

    def _check_ohlc_consistency(self, df: pd.DataFrame) -> pd.Series:
        """Check OHLC relationship consistency.

        Valid OHLC must satisfy:
        - Low <= Open <= High
        - Low <= Close <= High
        - High >= Low
        """
        bad = pd.Series(False, index=df.index)

        # High must be >= Low
        bad |= df['high'] < df['low']

        # Open must be between Low and High
        bad |= (df['open'] < df['low']) | (df['open'] > df['high'])

        # Close must be between Low and High
        bad |= (df['close'] < df['low']) | (df['close'] > df['high'])

        return bad

    def _check_price_spikes(self, df: pd.DataFrame) -> pd.Series:
        """Detect unrealistic price spikes.

        Price spike = Close price deviates more than X% from moving average.
        """
        bad = pd.Series(False, index=df.index)

        if len(df) < self.ma_window:
            return bad

        # Calculate moving average
        ma = df['close'].rolling(window=self.ma_window, min_periods=1).mean()

        # Calculate deviation percentage
        deviation_pct = ((df['close'] - ma) / ma * 100).abs()

        # Mark spikes exceeding threshold
        bad = deviation_pct > self.max_price_deviation_pct

        return bad

    def _check_volume_anomalies(self, df: pd.DataFrame) -> pd.Series:
        """Detect volume anomalies.

        Volume anomalies:
        - Volume below minimum threshold
        - Volume exceeds average by large multiplier
        """
        bad = pd.Series(False, index=df.index)

        # Check minimum volume
        if self.min_volume > 0:
            bad |= df['volume'] < self.min_volume

        # Check maximum volume (vs average)
        if len(df) >= self.ma_window:
            avg_volume = df['volume'].rolling(window=self.ma_window, min_periods=1).mean()
            bad |= df['volume'] > (avg_volume * self.max_volume_multiplier)

        return bad

    def _check_duplicates(self, df: pd.DataFrame) -> pd.Series:
        """Detect duplicate timestamps.

        Keeps first occurrence, marks duplicates as bad.
        """
        if 'timestamp' not in df.columns:
            return pd.Series(False, index=df.index)

        # Mark duplicates (keep='first' keeps first occurrence)
        duplicates = df.duplicated(subset=['timestamp'], keep='first')

        return duplicates

    def _check_zero_negative_prices(self, df: pd.DataFrame) -> pd.Series:
        """Check for zero or negative prices (always invalid)."""
        bad = pd.Series(False, index=df.index)

        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                bad |= df[col] <= 0

        return bad
