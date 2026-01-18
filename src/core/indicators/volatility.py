"""Volatility Indicators.

Implements BB, KC, ATR, NATR, and STD.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

from .base import BaseIndicatorCalculator, PANDAS_TA_AVAILABLE, TALIB_AVAILABLE
from .types import IndicatorResult, IndicatorType

# Import optional libraries
if TALIB_AVAILABLE:
    import talib
if PANDAS_TA_AVAILABLE:
    import pandas_ta as ta

logger = logging.getLogger(__name__)


class VolatilityIndicators(BaseIndicatorCalculator):
    """Calculator for volatility indicators."""

    @staticmethod
    def calculate_bb(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Bollinger Bands (refactored).

        Args:
            data: Price data with 'close' column
            params: Parameters (period, std_dev)
            use_talib: Whether to prefer TALib if available

        Returns:
            IndicatorResult with BB values
        """
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2)

        # Dispatch to appropriate calculation method
        if use_talib and TALIB_AVAILABLE:
            values = VolatilityIndicators._calculate_bb_talib(data, period, std_dev)
        elif PANDAS_TA_AVAILABLE:
            values = VolatilityIndicators._calculate_bb_pandas_ta(data, period, std_dev)
        else:
            values = VolatilityIndicators._calculate_bb_manual(data, period, std_dev)

        return VolatilityIndicators.create_result(
            IndicatorType.BB, values, params
        )

    @staticmethod
    def _calculate_bb_talib(
        data: pd.DataFrame,
        period: int,
        std_dev: float
    ) -> pd.DataFrame:
        """Calculate BB using TALib.

        Args:
            data: Price data
            period: Rolling window period
            std_dev: Standard deviation multiplier

        Returns:
            DataFrame with BB columns
        """
        upper, middle, lower = talib.BBANDS(
            data['close'],
            timeperiod=period,
            nbdevup=std_dev,
            nbdevdn=std_dev
        )
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': upper - lower,
            'percent': (data['close'] - lower) / (upper - lower)
        })

    @staticmethod
    def _calculate_bb_pandas_ta(
        data: pd.DataFrame,
        period: int,
        std_dev: float
    ) -> pd.DataFrame:
        """Calculate BB using pandas_ta.

        Args:
            data: Price data
            period: Rolling window period
            std_dev: Standard deviation multiplier

        Returns:
            DataFrame with BB columns
        """
        values = ta.bbands(data['close'], length=period, std=std_dev)
        # Normalize pandas_ta output columns
        # pandas_ta returns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0
        if values is not None:
            return VolatilityIndicators._normalize_pandas_ta_columns(values)
        return pd.DataFrame()

    @staticmethod
    def _normalize_pandas_ta_columns(values: pd.DataFrame) -> pd.DataFrame:
        """Normalize pandas_ta BB column names to standard format.

        Args:
            values: DataFrame from pandas_ta.bbands()

        Returns:
            DataFrame with standardized column names
        """
        cols = values.columns
        # Find columns dynamically
        bbl = next((c for c in cols if c.startswith('BBL')), None)
        bbm = next((c for c in cols if c.startswith('BBM')), None)
        bbu = next((c for c in cols if c.startswith('BBU')), None)
        bbb = next((c for c in cols if c.startswith('BBB')), None)
        bbp = next((c for c in cols if c.startswith('BBP')), None)

        new_values = pd.DataFrame(index=values.index)
        if bbu:
            new_values['upper'] = values[bbu]
        if bbm:
            new_values['middle'] = values[bbm]
        if bbl:
            new_values['lower'] = values[bbl]
        if bbb:
            new_values['bandwidth'] = values[bbb]
        if bbp:
            new_values['percent'] = values[bbp]

        return new_values

    @staticmethod
    def _calculate_bb_manual(
        data: pd.DataFrame,
        period: int,
        std_dev: float
    ) -> pd.DataFrame:
        """Calculate BB manually (fallback).

        Args:
            data: Price data
            period: Rolling window period
            std_dev: Standard deviation multiplier

        Returns:
            DataFrame with BB columns
        """
        sma = data['close'].rolling(window=period).mean()
        std = data['close'].rolling(window=period).std()

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        # Avoid division by zero
        diff = upper - lower
        percent = (data['close'] - lower) / diff.replace(0, np.nan)

        return pd.DataFrame({
            'upper': upper,
            'middle': sma,
            'lower': lower,
            'bandwidth': diff,
            'percent': percent
        })

    @staticmethod
    def calculate_bb_width(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Bollinger Bandwidth."""
        result = VolatilityIndicators.calculate_bb(data, params, use_talib)
        values = result.values['bandwidth']
        return VolatilityIndicators.create_result(
            IndicatorType.BB_WIDTH, values, params
        )

    @staticmethod
    def calculate_bb_percent(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Bollinger %B."""
        result = VolatilityIndicators.calculate_bb(data, params, use_talib)
        values = result.values['percent']
        return VolatilityIndicators.create_result(
            IndicatorType.BB_PERCENT, values, params
        )

    @staticmethod
    def calculate_kc(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Keltner Channels."""
        period = params.get('period', 20)
        multiplier = params.get('multiplier', 2)

        if PANDAS_TA_AVAILABLE:
            values = ta.kc(
                data['high'],
                data['low'],
                data['close'],
                length=period,
                scalar=multiplier
            )
        else:
            # Manual calculation
            ema = data['close'].ewm(span=period, adjust=False).mean()
            atr = VolatilityIndicators.calculate_atr(data, {'period': period}, False).values

            upper = ema + (atr * multiplier)
            lower = ema - (atr * multiplier)

            values = pd.DataFrame({
                'upper': upper,
                'middle': ema,
                'lower': lower
            })

        return VolatilityIndicators.create_result(
            IndicatorType.KC, values, params
        )

    @staticmethod
    def calculate_atr(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Average True Range."""
        period = params.get('period', 14)

        if use_talib and TALIB_AVAILABLE:
            values = talib.ATR(data['high'], data['low'], data['close'], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.atr(data['high'], data['low'], data['close'], length=period)
        else:
            # Manual calculation using Wilder's Smoothing Method
            # Reference: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-atr
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            # Use Wilder's smoothing (EMA with alpha = 1/period)
            alpha = 1.0 / period
            values = true_range.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

        return VolatilityIndicators.create_result(
            IndicatorType.ATR, values, params
        )

    @staticmethod
    def calculate_natr(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Normalized ATR."""
        period = params.get('period', 14)

        if use_talib and TALIB_AVAILABLE:
            values = talib.NATR(data['high'], data['low'], data['close'], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.natr(data['high'], data['low'], data['close'], length=period)
        else:
            # Manual calculation
            atr = VolatilityIndicators.calculate_atr(data, params, False).values
            values = (atr / data['close']) * 100

        return VolatilityIndicators.create_result(
            IndicatorType.NATR, values, params
        )

    @staticmethod
    def calculate_std(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Standard Deviation."""
        period = params.get('period', 20)

        if use_talib and TALIB_AVAILABLE:
            values = talib.STDDEV(data['close'], timeperiod=period)
        else:
            values = data['close'].rolling(window=period).std()

        return VolatilityIndicators.create_result(
            IndicatorType.STD, values, params
        )

    @staticmethod
    def calculate_chop(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Choppiness Index (CHOP).

        The Choppiness Index is a volatility indicator that determines
        whether the market is choppy (trading sideways) or trending.

        Formula: CHOP = 100 * log10(sum(ATR, n) / (max(high, n) - min(low, n))) / log10(n)

        Range: 0 to 100
        - Values > 61.8: Market is choppy (sideways/ranging)
        - Values < 38.2: Market is trending
        - Values between 38.2 and 61.8: Transitional

        Args:
            data: Price data with 'high', 'low', 'close' columns
            params: Parameters (period, default 14)
            use_talib: Ignored for CHOP (no TALib implementation)

        Returns:
            IndicatorResult with CHOP values (0-100)
        """
        period = params.get('period', 14)

        # Calculate ATR first (using existing method)
        atr_result = VolatilityIndicators.calculate_atr(
            data,
            {'period': period},
            use_talib
        )
        atr = atr_result.values

        # Sum of ATR over period
        atr_sum = atr.rolling(window=period).sum()

        # Highest high and lowest low over period
        high_max = data['high'].rolling(window=period).max()
        low_min = data['low'].rolling(window=period).min()

        # High-Low range
        hl_range = high_max - low_min

        # Avoid division by zero
        hl_range = hl_range.replace(0, np.nan)

        # CHOP formula
        # log10(sum(ATR) / (high_max - low_min)) / log10(period)
        log_numerator = np.log10(atr_sum / hl_range)
        log_denominator = np.log10(period)

        values = 100 * log_numerator / log_denominator

        # Clip to 0-100 range (handle edge cases)
        values = values.clip(0, 100)

        return VolatilityIndicators.create_result(
            IndicatorType.CHOP, values, params
        )
