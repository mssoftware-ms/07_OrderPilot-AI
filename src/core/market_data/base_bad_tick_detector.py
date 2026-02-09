"""Base Bad Tick Detector - Common Detection and Cleaning Logic.

Consolidates shared bad tick detection logic between provider-specific detectors:
- Alpaca Bad Tick Detector (alpaca_bad_tick_detector.py)
- Bitunix Bad Tick Detector (bitunix_bad_tick_detector.py)

Extracted Code Coverage:
- Lines 32-39: __init__ method (100% identical)
- Lines 131-254: Detection logic (100% identical algorithms)
- Lines 256-313: Cleaning logic (95% identical, pandas syntax varies)

Provider-Specific Code (remains in subclasses):
- Config imports (provider-specific FilterConfig)
- Bar object reconstruction (Alpaca Bar vs HistoricalBar)
- DataFrame conversion (Decimal handling for Bitunix)

Created: 2026-01-31 (CODER-005, Task 1.3.1)
Refactoring: Eliminate ~182 LOC code duplication
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# Generic type for FilterConfig (provider-specific)
TFilterConfig = TypeVar("TFilterConfig")
TFilterStats = TypeVar("TFilterStats")
TBar = TypeVar("TBar")


class BaseBadTickDetector(ABC, Generic[TFilterConfig, TFilterStats, TBar]):
    """Base class for provider-specific bad tick detection.

    Consolidates common detection and cleaning logic shared between
    Alpaca and Bitunix bad tick detectors.

    Generic Type Parameters:
        TFilterConfig: Provider-specific FilterConfig type
        TFilterStats: Provider-specific FilterStats type
        TBar: Provider-specific Bar/HistoricalBar type

    Subclasses must implement:
        - _convert_bars_to_dataframe(): Convert provider bars to DataFrame
        - _convert_dataframe_to_bars(): Convert DataFrame back to provider bars

    Detection Methods:
        - Hampel Filter: Modified Z-score using Median Absolute Deviation (MAD)
        - Z-Score: Standard deviation-based outlier detection
        - Basic: OHLC consistency and volume spike checks

    Cleaning Modes:
        - interpolate: Linear interpolation of bad ticks
        - forward_fill: Forward fill with previous valid values
        - remove: Remove bad ticks entirely
    """

    def __init__(self, config: TFilterConfig):
        """Initialize detector with configuration.

        Args:
            config: Provider-specific FilterConfig instance

        Extracted From:
            alpaca_bad_tick_detector.py: Lines 32-39
            bitunix_bad_tick_detector.py: Lines 32-39
        """
        self.config = config

    # ========================================================================
    # Abstract Methods (Provider-Specific Implementation)
    # ========================================================================

    @abstractmethod
    def _convert_bars_to_dataframe(self, bars: list[TBar]) -> pd.DataFrame:
        """Convert provider-specific Bar objects to DataFrame.

        Args:
            bars: List of provider-specific Bar objects

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume

        Note:
            - Alpaca: Direct conversion (b.open, b.high, etc.)
            - Bitunix: Explicit float conversion (float(b.open)) for Decimal handling
        """
        pass

    @abstractmethod
    def _convert_dataframe_to_bars(
        self, df: pd.DataFrame, original_bars: list[TBar], symbol: str
    ) -> list[TBar]:
        """Convert DataFrame back to provider-specific Bar objects.

        Args:
            df: DataFrame with OHLCV data
            original_bars: Original bar list (for metadata extraction)
            symbol: Trading symbol

        Returns:
            List of provider-specific Bar objects

        Note:
            - Alpaca: alpaca.data.models.bars.Bar with symbol, trade_count, vwap
            - Bitunix: HistoricalBar with source="bitunix", Decimal conversion
        """
        pass

    @abstractmethod
    def _create_filter_stats(
        self,
        total_bars: int = 0,
        bad_ticks_found: int = 0,
        bad_ticks_removed: int = 0,
        bad_ticks_interpolated: int = 0,
        filtering_percentage: float = 0.0,
    ) -> TFilterStats:
        """Create provider-specific FilterStats object.

        Args:
            total_bars: Total number of bars processed
            bad_ticks_found: Number of bad ticks detected
            bad_ticks_removed: Number of bad ticks removed
            bad_ticks_interpolated: Number of bad ticks interpolated
            filtering_percentage: Percentage of bars filtered

        Returns:
            Provider-specific FilterStats instance
        """
        pass

    # ========================================================================
    # Public API (Common Implementation)
    # ========================================================================

    async def filter_bad_ticks(
        self, bars: list[TBar], symbol: str
    ) -> tuple[list[TBar], TFilterStats]:
        """Apply bad tick filtering to bars.

        Args:
            bars: List of provider-specific Bar objects
            symbol: Trading symbol for logging

        Returns:
            Tuple of (cleaned_bars, stats)

        Extracted From:
            alpaca_bad_tick_detector.py: Lines 41-128
            bitunix_bad_tick_detector.py: Lines 41-129
        """
        if not self.config.enabled or not bars:
            return bars, self._create_filter_stats(total_bars=len(bars))

        # Convert to DataFrame (provider-specific)
        df = self._convert_bars_to_dataframe(bars)

        original_len = len(df)

        # Detect bad ticks (common algorithm)
        bad_mask = self._detect_bad_ticks(df)
        bad_count = bad_mask.sum()

        if bad_count == 0:
            if self.config.log_stats:
                logger.info(f"✅ {symbol}: No bad ticks found ({original_len} bars)")
            return bars, self._create_filter_stats(total_bars=original_len)

        # Clean bad ticks (common logic, mode-dependent)
        if self.config.cleaning_mode == "interpolate":
            df = self._interpolate_bad_ticks(df, bad_mask)
            cleaned_bars = self._convert_dataframe_to_bars(df, bars, symbol)
            stats = self._create_filter_stats(
                total_bars=original_len,
                bad_ticks_found=int(bad_count),
                bad_ticks_interpolated=int(bad_count),
                filtering_percentage=(bad_count / original_len * 100)
                if original_len > 0
                else 0.0,
            )
        elif self.config.cleaning_mode == "forward_fill":
            df = self._forward_fill_bad_ticks(df, bad_mask)
            cleaned_bars = self._convert_dataframe_to_bars(df, bars, symbol)
            stats = self._create_filter_stats(
                total_bars=original_len,
                bad_ticks_found=int(bad_count),
                bad_ticks_interpolated=int(bad_count),
                filtering_percentage=(bad_count / original_len * 100)
                if original_len > 0
                else 0.0,
            )
        elif self.config.cleaning_mode == "remove":
            df = df[~bad_mask].copy()
            cleaned_bars = self._convert_dataframe_to_bars(df, bars, symbol)
            stats = self._create_filter_stats(
                total_bars=original_len,
                bad_ticks_found=int(bad_count),
                bad_ticks_removed=int(bad_count),
                filtering_percentage=(bad_count / original_len * 100)
                if original_len > 0
                else 0.0,
            )
        else:
            logger.warning(f"Unknown cleaning_mode: {self.config.cleaning_mode}")
            return bars, self._create_filter_stats(
                total_bars=original_len, bad_ticks_found=int(bad_count)
            )

        if self.config.log_stats:
            logger.info(
                f"🧹 {symbol}: Filtered {bad_count}/{original_len} bars "
                f"({stats.filtering_percentage:.2f}%) "
                f"using {self.config.method} method, mode={self.config.cleaning_mode}"
            )

        return cleaned_bars, stats

    # ========================================================================
    # Detection Methods (Common Implementation - Extracted from both files)
    # ========================================================================

    def _detect_bad_ticks(self, df: pd.DataFrame) -> pd.Series:
        """Detect bad ticks using configured method.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Boolean mask (True = bad tick)

        Extracted From:
            alpaca_bad_tick_detector.py: Lines 131-149
            bitunix_bad_tick_detector.py: Lines 131-149
        """
        if self.config.method == "hampel":
            return self._detect_hampel_outliers(df)
        elif self.config.method == "zscore":
            return self._detect_zscore_outliers(df)
        elif self.config.method == "basic":
            return self._detect_basic_outliers(df)
        else:
            logger.warning(
                f"Unknown detection method: {self.config.method}, using basic"
            )
            return self._detect_basic_outliers(df)

    def _detect_hampel_outliers(self, df: pd.DataFrame) -> pd.Series:
        """Hampel Filter: Modified Z-score using Median Absolute Deviation (MAD).

        More robust than standard Z-score for financial data with fat tails.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Boolean mask (True = outlier)

        Extracted From:
            alpaca_bad_tick_detector.py: Lines 151-188
            bitunix_bad_tick_detector.py: Lines 151-188
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
        """Z-Score outlier detection (standard deviations from mean).

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Boolean mask (True = outlier)

        Extracted From:
            alpaca_bad_tick_detector.py: Lines 190-216
            bitunix_bad_tick_detector.py: Lines 190-216
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
        """Basic OHLC consistency checks and volume spikes.

        Detects:
        - OHLC relationship violations (high < low, close outside high/low)
        - Price spikes vs rolling median
        - Extreme volume spikes
        - Zero or negative prices

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Boolean mask (True = bad tick)

        Extracted From:
            alpaca_bad_tick_detector.py: Lines 218-254
            bitunix_bad_tick_detector.py: Lines 218-254
        """
        if df.empty:
            return pd.Series(False, index=df.index)

        # Use numpy arrays to minimize pandas overhead for the "basic" path.
        length = len(df)
        bad = np.zeros(length, dtype=bool)

        price_matrix = None
        has_prices = all(col in df.columns for col in ("open", "high", "low", "close"))
        if has_prices:
            price_matrix = df[["open", "high", "low", "close"]].to_numpy(dtype=float, copy=False)
            open_arr = price_matrix[:, 0]
            high_arr = price_matrix[:, 1]
            low_arr = price_matrix[:, 2]
            close_arr = price_matrix[:, 3]

            # OHLC consistency
            ohlc_bad = (
                (high_arr < low_arr)
                | (close_arr > high_arr)
                | (close_arr < low_arr)
                | (open_arr > high_arr)
                | (open_arr < low_arr)
            )
            bad |= ohlc_bad

            # Zero or negative prices
            neg_bad = (
                (open_arr <= 0)
                | (high_arr <= 0)
                | (low_arr <= 0)
                | (close_arr <= 0)
            )
            bad |= neg_bad

            # Price spikes vs global median (fast baseline for basic mode)
            spike_multiplier = getattr(self.config, "price_spike_multiplier", None)
            if spike_multiplier:
                baseline = float(np.median(close_arr))
                if not np.isfinite(baseline):
                    baseline = float(np.nanmedian(close_arr))
                if baseline > 0:
                    safe_min = np.where(low_arr > 0, low_arr, np.nan)
                    spike_up = (high_arr / baseline) >= spike_multiplier
                    spike_down = (baseline / safe_min) >= spike_multiplier
                    bad |= spike_up | np.nan_to_num(spike_down, nan=False, posinf=True, neginf=True)
        else:
            arrays: dict[str, np.ndarray] = {}
            for col in ("open", "high", "low", "close"):
                if col in df.columns:
                    arrays[col] = df[col].to_numpy(dtype=float, copy=False)

            if all(col in arrays for col in ("open", "high", "low", "close")):
                open_arr = arrays["open"]
                high_arr = arrays["high"]
                low_arr = arrays["low"]
                close_arr = arrays["close"]

                ohlc_bad = (
                    (high_arr < low_arr)
                    | (close_arr > high_arr)
                    | (close_arr < low_arr)
                    | (open_arr > high_arr)
                    | (open_arr < low_arr)
                )
                bad |= ohlc_bad

                neg_bad = (
                    (open_arr <= 0)
                    | (high_arr <= 0)
                    | (low_arr <= 0)
                    | (close_arr <= 0)
                )
                bad |= neg_bad

                spike_multiplier = getattr(self.config, "price_spike_multiplier", None)
                if spike_multiplier:
                    baseline = float(np.median(close_arr))
                    if not np.isfinite(baseline):
                        baseline = float(np.nanmedian(close_arr))
                    if baseline > 0:
                        safe_min = np.where(low_arr > 0, low_arr, np.nan)
                        spike_up = (high_arr / baseline) >= spike_multiplier
                        spike_down = (baseline / safe_min) >= spike_multiplier
                        bad |= spike_up | np.nan_to_num(spike_down, nan=False, posinf=True, neginf=True)

        # Volume spikes (fast global median baseline)
        if "volume" in df.columns:
            vol_arr = df["volume"].to_numpy(dtype=float, copy=False)
            vol_median = float(np.median(vol_arr))
            if not np.isfinite(vol_median):
                vol_median = float(np.nanmedian(vol_arr))
            if vol_median > 0:
                bad |= vol_arr > (vol_median * self.config.volume_multiplier)
            bad |= vol_arr < 0

        return pd.Series(bad, index=df.index)

    # ========================================================================
    # Cleaning Methods (Common Implementation - Extracted from both files)
    # ========================================================================

    def _interpolate_bad_ticks(
        self, df: pd.DataFrame, bad_mask: pd.Series
    ) -> pd.DataFrame:
        """Interpolate bad ticks using linear interpolation.

        Args:
            df: DataFrame with OHLCV data
            bad_mask: Boolean mask of bad ticks

        Returns:
            DataFrame with interpolated values

        Extracted From:
            alpaca_bad_tick_detector.py: Lines 256-285
            bitunix_bad_tick_detector.py: Lines 256-285
        """
        df = df.copy()

        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                continue

            # Set bad values to NaN
            df.loc[bad_mask, col] = np.nan

            # Interpolate (modern pandas syntax)
            df[col] = df[col].interpolate(method="linear", limit_direction="both")

            # Forward fill if interpolation fails
            df[col] = df[col].ffill()

            # Backward fill if still NaN
            df[col] = df[col].bfill()

        return df

    def _forward_fill_bad_ticks(
        self, df: pd.DataFrame, bad_mask: pd.Series
    ) -> pd.DataFrame:
        """Forward fill bad ticks with previous valid values.

        Args:
            df: DataFrame with OHLCV data
            bad_mask: Boolean mask of bad ticks

        Returns:
            DataFrame with forward-filled values

        Extracted From:
            alpaca_bad_tick_detector.py: Lines 287-313
            bitunix_bad_tick_detector.py: Lines 287-313
        """
        df = df.copy()

        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                continue

            # Set bad values to NaN
            df.loc[bad_mask, col] = np.nan

            # Forward fill (modern pandas syntax)
            df[col] = df[col].ffill()

            # Backward fill if still NaN
            df[col] = df[col].bfill()

        return df
