"""Hampel Bad Tick Detector - MAD-based Outlier Detection with Volume Confirmation.

Advanced bad tick detector using Hampel Filter (Median Absolute Deviation).
Based on "Handbuch für Algorithmische Datenintegrität und KI" methodology.

Key insight: A price spike is a BAD TICK only if it has NO high volume.
A price spike WITH high volume is a real market event (crash, news) and must be kept.

Module 3/6 of data_cleaning.py split (Lines 269-532).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .cleaning_types import CleaningStats

logger = logging.getLogger(__name__)


class HampelBadTickDetector:
    """Advanced bad tick detector using Hampel Filter with Volume Confirmation.

    Uses MAD (Median Absolute Deviation) for robust outlier detection instead of
    standard deviation, which is more resistant to outliers itself.
    """

    def __init__(
        self,
        window: int = 15,
        threshold: float = 3.5,
        vol_filter_mult: float = 10.0
    ):
        """Initialize Hampel Filter with Volume Confirmation.

        Args:
            window: Rolling window size for MAD calculation (default: 15)
            threshold: Modified Z-Score threshold for outliers (default: 3.5)
            vol_filter_mult: Volume multiplier for high-volume detection (default: 10x median)
                Higher values = more strict (only very high volume events are kept)

        Notes:
            - For high volatility (crypto): increase threshold to 4.0-6.0
            - window=15 is good for 1-minute bars (15 minutes context)
            - vol_filter_mult=10 means volume must be 10x median to be "high volume"
        """
        self.window = window
        self.threshold = threshold
        self.vol_filter_mult = vol_filter_mult
        logger.info(
            f"🛡️  Hampel Filter initialized: window={window}, threshold={threshold}, "
            f"vol_filter_mult={vol_filter_mult}x"
        )

    def detect_outliers_mad(self, df: pd.DataFrame, col: str = 'close') -> pd.Series:
        """Detect price outliers using Median Absolute Deviation (MAD).

        MAD is more robust than standard deviation because it's not affected by
        the outliers themselves. Uses rolling median instead of rolling mean.

        Args:
            df: DataFrame with price data
            col: Column to check for outliers (default: 'close')

        Returns:
            Boolean Series: True = outlier, False = normal
        """
        # Initialize all as NOT outliers
        is_outlier = pd.Series(False, index=df.index)

        if len(df) < self.window:
            # Not enough data for rolling window
            return is_outlier

        # Rolling Median (center=False for streaming/real-time compatibility)
        rolling_median = df[col].rolling(window=self.window, center=False, min_periods=self.window).median()

        # Absolute Deviation from median
        deviation = np.abs(df[col] - rolling_median)

        # Rolling MAD (Median Absolute Deviation)
        # Use min_periods=3 (minimum for meaningful median) for early detection
        min_periods_mad = 3
        mad = deviation.rolling(window=self.window, center=False, min_periods=min_periods_mad).median()

        # For constant prices (MAD=0), avoid division by zero
        price_range = df[col].max() - df[col].min()
        if price_range > 0:
            mad_floor = price_range * 1e-6  # 0.0001% of price range
        else:
            mad_floor = 1.0  # Fallback for constant prices

        mad = mad.replace(0, mad_floor)

        # Modified Z-Score (Hampel Filter)
        # 0.6745 is the constant factor for normal distribution equivalence
        with np.errstate(divide='ignore', invalid='ignore'):
            mod_z = 0.6745 * (deviation / mad)

        # Mark as outlier if modified z-score exceeds threshold
        is_outlier = (mod_z > self.threshold) | np.isinf(mod_z)
        is_outlier = is_outlier.fillna(False)

        # The first window-1 bars cannot be reliably detected (no full context)
        is_outlier.iloc[:self.window-1] = False

        return is_outlier

    def detect_bad_ticks(self, df: pd.DataFrame) -> pd.Series:
        """Detect bad ticks using Hampel Filter + Volume Confirmation.

        Bad Tick Logic:
            is_bad_tick = is_price_outlier & (~is_high_volume)

        A price spike is only a bad tick if it has NO high volume.
        A price spike WITH high volume is a real market event (crash, flash crash, news).

        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume

        Returns:
            Boolean Series: True = bad tick, False = good tick
        """
        if df.empty or len(df) < self.window:
            return pd.Series(False, index=df.index)

        # 1. Detect price outliers using MAD on Close price
        is_price_outlier = self.detect_outliers_mad(df, 'close')

        # 2. Detect high-volume events
        vol_median = df['volume'].rolling(window=self.window, center=False, min_periods=self.window).median()

        # High volume = volume exceeds median by vol_filter_mult
        is_high_volume = (df['volume'] > (vol_median * self.vol_filter_mult)).fillna(False)

        # 3. BAD TICK LOGIC: Price outlier WITHOUT high volume
        is_bad_tick = is_price_outlier & (~is_high_volume)

        # 4. Also check OHLC consistency (always invalid)
        ohlc_bad = self._check_ohlc_consistency(df)
        is_bad_tick |= ohlc_bad

        # 5. Check zero/negative prices (always invalid)
        zero_price_bad = self._check_zero_negative_prices(df)
        is_bad_tick |= zero_price_bad

        # Logging
        total_bad = is_bad_tick.sum()
        if total_bad > 0:
            outlier_count = is_price_outlier.sum()
            high_vol_count = is_high_volume.sum()
            logger.warning(
                f"🔍 Hampel Filter: {total_bad} bad ticks detected "
                f"(outliers: {outlier_count}, high-vol events: {high_vol_count}, "
                f"bad ticks: {total_bad})"
            )

        return is_bad_tick

    def _check_ohlc_consistency(self, df: pd.DataFrame) -> pd.Series:
        """Check OHLC relationship consistency."""
        bad = pd.Series(False, index=df.index)

        # High must be >= Low
        bad |= df['high'] < df['low']

        # Open must be between Low and High
        bad |= (df['open'] < df['low']) | (df['open'] > df['high'])

        # Close must be between Low and High
        bad |= (df['close'] < df['low']) | (df['close'] > df['high'])

        return bad

    def _check_zero_negative_prices(self, df: pd.DataFrame) -> pd.Series:
        """Check for zero or negative prices."""
        bad = pd.Series(False, index=df.index)

        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                bad |= df[col] <= 0

        return bad

    def clean_data(
        self,
        df: pd.DataFrame,
        method: str = "interpolate"
    ) -> tuple[pd.DataFrame, CleaningStats]:
        """Clean bad ticks from DataFrame using Hampel Filter.

        Args:
            df: DataFrame with market data
            method: Cleaning method:
                - "remove": Remove bad ticks entirely
                - "interpolate": Replace with interpolated values (recommended)
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

        df_clean = df.copy()

        # Apply cleaning method
        if method == "remove":
            df_clean = df_clean[~bad_mask].copy()
            logger.info(f"🧹 Removed {bad_count} bad ticks ({bad_count/original_count*100:.2f}%)")

        elif method == "interpolate":
            # Set bad tick OHLC values to NaN
            cols_ohlc = ['open', 'high', 'low', 'close']
            df_clean.loc[bad_mask, cols_ohlc] = np.nan

            # Time-based interpolation (recommended for time series)
            if 'timestamp' in df_clean.columns:
                df_clean = df_clean.set_index('timestamp')
                df_clean[cols_ohlc] = df_clean[cols_ohlc].interpolate(method='time')
                df_clean = df_clean.reset_index()
            else:
                # Fallback to linear interpolation
                df_clean[cols_ohlc] = df_clean[cols_ohlc].interpolate(
                    method='linear',
                    limit_direction='both'
                )

            # Set bad tick volume to median (conservative approach)
            vol_median = df['volume'].rolling(window=self.window, center=False, min_periods=self.window).median()
            df_clean.loc[bad_mask, 'volume'] = np.nan
            df_clean['volume'] = df_clean['volume'].fillna(vol_median).fillna(method='bfill')

            logger.info(f"🔧 Interpolated {bad_count} bad ticks ({bad_count/original_count*100:.2f}%)")

        elif method == "forward_fill":
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
            bad_tick_types={},
            cleaning_percentage=bad_count / original_count * 100
        )

        return df_clean, stats
