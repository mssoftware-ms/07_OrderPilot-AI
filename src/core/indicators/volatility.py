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
        """Calculate Bollinger Bands."""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2)

        if use_talib and TALIB_AVAILABLE:
            upper, middle, lower = talib.BBANDS(
                data['close'],
                timeperiod=period,
                nbdevup=std_dev,
                nbdevdn=std_dev
            )
            values = pd.DataFrame({
                'upper': upper,
                'middle': middle,
                'lower': lower,
                'bandwidth': upper - lower,
                'percent': (data['close'] - lower) / (upper - lower)
            })
        elif PANDAS_TA_AVAILABLE:
            values = ta.bbands(data['close'], length=period, std=std_dev)
            # Normalize pandas_ta output columns if needed, but for now assuming standard keys or using calculate_bb directly
            # pandas_ta returns columns like BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0 (bandwidth), BBP_20_2.0 (%b)
            # We map them to standard names for consistency
            if values is not None:
                # Find columns dynamically
                cols = values.columns
                bbl = next((c for c in cols if c.startswith('BBL')), None)
                bbm = next((c for c in cols if c.startswith('BBM')), None)
                bbu = next((c for c in cols if c.startswith('BBU')), None)
                bbb = next((c for c in cols if c.startswith('BBB')), None)
                bbp = next((c for c in cols if c.startswith('BBP')), None)
                
                new_values = pd.DataFrame(index=values.index)
                if bbu: new_values['upper'] = values[bbu]
                if bbm: new_values['middle'] = values[bbm]
                if bbl: new_values['lower'] = values[bbl]
                if bbb: new_values['bandwidth'] = values[bbb]
                if bbp: new_values['percent'] = values[bbp]
                values = new_values

        else:
            # Manual calculation
            sma = data['close'].rolling(window=period).mean()
            std = data['close'].rolling(window=period).std()

            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)

            # Avoid division by zero
            diff = upper - lower
            percent = (data['close'] - lower) / diff.replace(0, np.nan)

            values = pd.DataFrame({
                'upper': upper,
                'middle': sma,
                'lower': lower,
                'bandwidth': diff,
                'percent': percent
            })

        return VolatilityIndicators.create_result(
            IndicatorType.BB, values, params
        )

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
            # Manual calculation
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            values = true_range.rolling(window=period).mean()

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
