"""Data Cleaning and Bad Tick Detection for Market Data.

Identifies and filters out erroneous data (bad ticks) from historical and streaming data.
Bad ticks can severely impact backtesting results and AI model training.

Common bad tick patterns:
- Price spikes: Sudden unrealistic price jumps (>5-10% from moving average)
- Volume anomalies: Zero volume or unrealistically high volume
- OHLC inconsistencies: High < Low, Close outside [Low, High]
- Duplicate timestamps: Same timestamp appearing multiple times
- Zero/negative prices: Invalid price values
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CleaningStats:
    """Statistics from data cleaning operation."""
    total_bars: int
    bad_ticks_removed: int
    bad_tick_types: dict[str, int]
    cleaning_percentage: float


class BadTickDetector:
    """Detects and removes bad ticks from market data."""

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


class HampelBadTickDetector:
    """Advanced bad tick detector using Hampel Filter with Volume Confirmation.

    Based on "Handbuch für Algorithmische Datenintegrität und KI" methodology.

    Key insight: A price spike is a BAD TICK only if it has NO high volume.
    A price spike WITH high volume is a real market event (crash, news) and must be kept.

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

        # Rolling Median (center=True for historical analysis, False for real-time)
        # For streaming, we use center=False (look backward only)
        # Use min_periods=window for reliable median
        rolling_median = df[col].rolling(window=self.window, center=False, min_periods=self.window).median()

        # Absolute Deviation from median
        deviation = np.abs(df[col] - rolling_median)

        # Rolling MAD (Median Absolute Deviation)
        # PROBLEM: Using min_periods=window requires 2*window bars total!
        # SOLUTION: Use min_periods=3 (minimum for meaningful median) for early detection
        # This means MAD will be valid as soon as we have 3 non-NaN deviation values
        # (which happens at index window+2, e.g., index 17 for window=15)
        min_periods_mad = 3  # Minimum for median calculation
        mad = deviation.rolling(window=self.window, center=False, min_periods=min_periods_mad).median()

        # For constant prices (MAD=0), we can't determine outliers
        # Replace 0 with a small value to avoid inf, but large enough to not trigger false positives
        # If all deviations are 0 (constant prices), any deviation will be an outlier
        # Use 1e-6 times the price range to set a reasonable threshold
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
        # Handle NaN (not enough data), inf (extreme outlier), and normal values
        is_outlier = pd.Series(False, index=df.index)
        is_outlier = (mod_z > self.threshold) | np.isinf(mod_z)
        is_outlier = is_outlier.fillna(False)

        # The first window-1 bars cannot be reliably detected (no full context)
        # Force them to False to avoid false positives from early bars
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
        # Calculate rolling median volume (use min_periods=window for reliable stats)
        vol_median = df['volume'].rolling(window=self.window, center=False, min_periods=self.window).median()

        # High volume = volume exceeds median by vol_filter_mult
        # This identifies crashes, news events, or other legitimate extreme moves
        # Use .fillna(False) to handle first window bars (assume normal volume)
        is_high_volume = (df['volume'] > (vol_median * self.vol_filter_mult)).fillna(False)

        # 3. BAD TICK LOGIC: Price outlier WITHOUT high volume
        # If price is extreme BUT volume is normal → Bad Tick (technical error)
        # If price is extreme AND volume is high → Real Market Event (keep it!)
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


class StreamBadTickFilter:
    """Real-time bad tick filter for streaming data.

    Maintains a rolling window for spike detection and filters incoming bars.
    """

    def __init__(
        self,
        detector: BadTickDetector | HampelBadTickDetector,
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


def clean_historical_data(
    symbol: str,
    source: str = "alpaca_crypto",
    db_path: str = "./data/orderpilot_historical.db",
    method: str = "remove",
    save_cleaned: bool = True,
) -> CleaningStats:
    """Clean historical data from database.

    Args:
        symbol: Symbol to clean (e.g., "alpaca_crypto:BTC/USD")
        source: Data source filter
        db_path: Path to SQLite database
        method: Cleaning method ("remove", "interpolate", "forward_fill")
        save_cleaned: Save cleaned data back to database

    Returns:
        Cleaning statistics
    """
    import sqlite3

    logger.info(f"🧹 Starting data cleaning for {symbol}...")

    # Load data from database
    conn = sqlite3.connect(db_path)
    query = f"""
        SELECT timestamp, open, high, low, close, volume
        FROM market_bars
        WHERE symbol = '{symbol}'
        ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn, parse_dates=['timestamp'])

    if df.empty:
        logger.warning(f"No data found for {symbol}")
        conn.close()
        return CleaningStats(0, 0, {}, 0.0)

    logger.info(f"Loaded {len(df)} bars for cleaning")

    # Clean data
    detector = BadTickDetector()
    df_clean, stats = detector.clean_data(df, method=method)

    if save_cleaned and stats.bad_ticks_removed > 0:
        # TODO: Implement database update
        # For now, we keep original data and mark bad ticks
        logger.info("💾 Would save cleaned data (not implemented yet)")

    conn.close()

    logger.info(f"✅ Cleaning complete: {stats.bad_ticks_removed}/{stats.total_bars} "
                f"bad ticks ({stats.cleaning_percentage:.2f}%)")

    return stats


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Clean Alpaca historical data
    stats = clean_historical_data(
        symbol="alpaca_crypto:BTC/USD",
        method="remove",
        save_cleaned=False
    )

    print(f"\n{'='*60}")
    print("CLEANING SUMMARY")
    print(f"{'='*60}")
    print(f"Total Bars: {stats.total_bars:,}")
    print(f"Bad Ticks Removed: {stats.bad_ticks_removed:,}")
    print(f"Cleaning Percentage: {stats.cleaning_percentage:.2f}%")
    print(f"{'='*60}")
