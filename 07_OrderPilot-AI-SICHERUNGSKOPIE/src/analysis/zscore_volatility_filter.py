"""Z-Score Volatility Filter - Inline Value Replacement.

Z-Score based filter that REPLACES bad tick values inline instead of just marking them.

Key features:
1. Calculates Z-Score for High and Low based on volatility
2. REPLACES extreme values (Z > 4) with 3-bar median BEFORE indicators are calculated
3. Aborts on null volume (data integrity check)

This prevents EMAs and other indicators from being affected by fat-finger errors.

Module 4/6 of data_cleaning.py split (Lines 534-762).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ZScoreVolatilityFilter:
    """Z-Score based filter that REPLACES bad tick values inline.

    Unlike Hampel Filter which only marks bad ticks, this filter:
    1. Calculates Z-Score for High and Low based on volatility
    2. REPLACES extreme values (Z > 4) with 3-bar median BEFORE indicators are calculated
    3. Aborts on null volume

    This prevents EMAs and other indicators from being "destroyed" by fat-finger errors.
    """

    def __init__(
        self,
        volatility_window: int = 20,
        z_threshold: float = 4.0,
        median_window: int = 3,
        min_volume: float = 0.0001,
    ):
        """Initialize Z-Score Volatility Filter.

        Args:
            volatility_window: Window for volatility calculation (default: 20 bars)
            z_threshold: Z-Score threshold for extreme detection (default: 4.0)
            median_window: Window for replacement median (default: 3 bars)
            min_volume: Minimum valid volume (default: 0.0001 to catch zero volume)
        """
        self.volatility_window = volatility_window
        self.z_threshold = z_threshold
        self.median_window = median_window
        self.min_volume = min_volume
        logger.info(
            f"🛡️  Z-Score Volatility Filter initialized: "
            f"vol_window={volatility_window}, z_threshold={z_threshold}, "
            f"median_window={median_window}, min_volume={min_volume}"
        )

    def clean_data_inline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean bad ticks by REPLACING extreme High/Low values inline.

        This modifies the DataFrame BEFORE any indicators are calculated.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with extreme values replaced

        Raises:
            ValueError: If null volume detected (data leak)
        """
        if df.empty or len(df) < self.volatility_window:
            return df

        df_clean = df.copy()

        # 1. NULL VOLUME CHECK - ABORT if found
        null_volume_mask = df_clean['volume'] <= self.min_volume
        if null_volume_mask.any():
            null_count = null_volume_mask.sum()
            null_indices = df_clean.index[null_volume_mask].tolist()
            logger.error(
                f"❌ NULL VOLUME DETECTED: {null_count} bars with volume <= {self.min_volume}"
            )
            logger.error(f"   Indices: {null_indices[:10]}...")  # Show first 10
            raise ValueError(
                f"Data leak: {null_count} bars have null volume (≤{self.min_volume}). "
                f"Cannot proceed with invalid data."
            )

        # 2. Calculate volatility (rolling standard deviation of Close)
        volatility = df_clean['close'].rolling(
            window=self.volatility_window,
            center=False,
            min_periods=self.volatility_window
        ).std()

        # 3. Calculate rolling mean of High and Low for Z-Score baseline
        high_mean = df_clean['high'].rolling(
            window=self.volatility_window,
            center=False,
            min_periods=self.volatility_window
        ).mean()

        low_mean = df_clean['low'].rolling(
            window=self.volatility_window,
            center=False,
            min_periods=self.volatility_window
        ).mean()

        # 4. Calculate Z-Scores for High and Low
        with np.errstate(divide='ignore', invalid='ignore'):
            z_high = np.abs((df_clean['high'] - high_mean) / volatility)
            z_low = np.abs((df_clean['low'] - low_mean) / volatility)

        # 5. Detect extreme values (Z > threshold)
        extreme_high_mask = (z_high > self.z_threshold) & ~np.isnan(z_high)
        extreme_low_mask = (z_low > self.z_threshold) & ~np.isnan(z_low)

        extreme_high_count = extreme_high_mask.sum()
        extreme_low_count = extreme_low_mask.sum()

        # 6. REPLACE extreme High values with 3-bar median
        if extreme_high_count > 0:
            high_median = df_clean['high'].rolling(
                window=self.median_window,
                center=False,
                min_periods=1
            ).median()

            df_clean.loc[extreme_high_mask, 'high'] = high_median[extreme_high_mask]

            logger.warning(
                f"🔧 Replaced {extreme_high_count} extreme HIGH values "
                f"(Z > {self.z_threshold}) with {self.median_window}-bar median"
            )

        # 7. REPLACE extreme Low values with 3-bar median
        if extreme_low_count > 0:
            low_median = df_clean['low'].rolling(
                window=self.median_window,
                center=False,
                min_periods=1
            ).median()

            df_clean.loc[extreme_low_mask, 'low'] = low_median[extreme_low_mask]

            logger.warning(
                f"🔧 Replaced {extreme_low_count} extreme LOW values "
                f"(Z > {self.z_threshold}) with {self.median_window}-bar median"
            )

        # 8. Fix OHLC consistency after replacement
        # High must be >= Low
        inconsistent_mask = df_clean['high'] < df_clean['low']
        if inconsistent_mask.any():
            # Swap them
            df_clean.loc[inconsistent_mask, ['high', 'low']] = df_clean.loc[
                inconsistent_mask, ['low', 'high']
            ].values
            logger.warning(f"⚠️  Fixed {inconsistent_mask.sum()} High/Low swaps after replacement")

        # Open must be between Low and High
        df_clean['open'] = df_clean['open'].clip(
            lower=df_clean['low'],
            upper=df_clean['high']
        )

        # Close must be between Low and High
        df_clean['close'] = df_clean['close'].clip(
            lower=df_clean['low'],
            upper=df_clean['high']
        )

        return df_clean

    def filter_single_bar(
        self,
        bar_dict: dict,
        recent_bars: pd.DataFrame
    ) -> tuple[dict, bool]:
        """Filter a single incoming bar in real-time.

        Args:
            bar_dict: Single bar dict with keys: timestamp, open, high, low, close, volume
            recent_bars: Recent historical bars for context (should have at least volatility_window bars)

        Returns:
            Tuple of (cleaned_bar_dict, is_valid)
            - cleaned_bar_dict: Bar with extreme values replaced
            - is_valid: False if null volume detected (abort), True otherwise
        """
        # 1. NULL VOLUME CHECK
        if bar_dict.get('volume', 0) <= self.min_volume:
            logger.error(
                f"❌ NULL VOLUME in incoming bar @ {bar_dict.get('timestamp')}: "
                f"volume={bar_dict.get('volume')} ≤ {self.min_volume} - ABORT"
            )
            return bar_dict, False

        # 2. Need enough history for volatility calculation
        if len(recent_bars) < self.volatility_window:
            # Not enough data yet, pass through
            return bar_dict, True

        # 3. Calculate volatility from recent bars
        volatility = recent_bars['close'].std()

        if volatility == 0 or np.isnan(volatility):
            # Constant prices or invalid, can't detect outliers
            return bar_dict, True

        # 4. Calculate mean High/Low from recent bars
        high_mean = recent_bars['high'].mean()
        low_mean = recent_bars['low'].mean()

        # 5. Calculate Z-Scores for incoming bar
        z_high = abs((bar_dict['high'] - high_mean) / volatility)
        z_low = abs((bar_dict['low'] - low_mean) / volatility)

        bar_cleaned = bar_dict.copy()

        # 6. Replace extreme High
        if z_high > self.z_threshold:
            # Use median of last N bars
            high_median = recent_bars['high'].tail(self.median_window).median()
            logger.warning(
                f"🔧 Extreme HIGH detected (Z={z_high:.1f}): "
                f"{bar_dict['high']} → {high_median} (median)"
            )
            bar_cleaned['high'] = high_median

        # 7. Replace extreme Low
        if z_low > self.z_threshold:
            low_median = recent_bars['low'].tail(self.median_window).median()
            logger.warning(
                f"🔧 Extreme LOW detected (Z={z_low:.1f}): "
                f"{bar_dict['low']} → {low_median} (median)"
            )
            bar_cleaned['low'] = low_median

        # 8. Fix OHLC consistency
        if bar_cleaned['high'] < bar_cleaned['low']:
            bar_cleaned['high'], bar_cleaned['low'] = bar_cleaned['low'], bar_cleaned['high']

        bar_cleaned['open'] = max(bar_cleaned['low'], min(bar_cleaned['high'], bar_cleaned['open']))
        bar_cleaned['close'] = max(bar_cleaned['low'], min(bar_cleaned['high'], bar_cleaned['close']))

        return bar_cleaned, True
