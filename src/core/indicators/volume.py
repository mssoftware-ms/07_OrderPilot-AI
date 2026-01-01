"""Volume Indicators.

Implements OBV, CMF, AD, FI, and VWAP.
"""

import logging
from typing import Any

import pandas as pd

from .base import BaseIndicatorCalculator, PANDAS_TA_AVAILABLE, TALIB_AVAILABLE
from .types import IndicatorResult, IndicatorType

# Import optional libraries
if TALIB_AVAILABLE:
    import talib
if PANDAS_TA_AVAILABLE:
    import pandas_ta as ta

logger = logging.getLogger(__name__)


class VolumeIndicators(BaseIndicatorCalculator):
    """Calculator for volume indicators."""

    @staticmethod
    def calculate_obv(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate On-Balance Volume."""
        if use_talib and TALIB_AVAILABLE:
            values = talib.OBV(data['close'], data['volume'])
        elif PANDAS_TA_AVAILABLE:
            values = ta.obv(data['close'], data['volume'])
        else:
            # Manual calculation
            obv = pd.Series(index=data.index, dtype=float)
            obv.iloc[0] = data['volume'].iloc[0]

            for i in range(1, len(data)):
                if data['close'].iloc[i] > data['close'].iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + data['volume'].iloc[i]
                elif data['close'].iloc[i] < data['close'].iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - data['volume'].iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]

            values = obv

        return VolumeIndicators.create_result(
            IndicatorType.OBV, values, params
        )

    @staticmethod
    def calculate_cmf(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Chaikin Money Flow."""
        period = params.get('period', 20)

        if PANDAS_TA_AVAILABLE:
            values = ta.cmf(
                data['high'],
                data['low'],
                data['close'],
                data['volume'],
                length=period
            )
        else:
            # Manual calculation
            money_flow_mult = ((data['close'] - data['low']) -
                              (data['high'] - data['close'])) / (data['high'] - data['low'])
            money_flow_volume = money_flow_mult * data['volume']

            values = (money_flow_volume.rolling(window=period).sum() /
                     data['volume'].rolling(window=period).sum())

        return VolumeIndicators.create_result(
            IndicatorType.CMF, values, params
        )

    @staticmethod
    def calculate_ad(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Accumulation/Distribution."""
        if use_talib and TALIB_AVAILABLE:
            values = talib.AD(data['high'], data['low'], data['close'], data['volume'])
        elif PANDAS_TA_AVAILABLE:
            values = ta.ad(data['high'], data['low'], data['close'], data['volume'])
        else:
            # Manual calculation
            money_flow_mult = ((data['close'] - data['low']) -
                              (data['high'] - data['close'])) / (data['high'] - data['low'])
            money_flow_volume = money_flow_mult * data['volume']
            values = money_flow_volume.cumsum()

        return VolumeIndicators.create_result(
            IndicatorType.AD, values, params
        )

    @staticmethod
    def calculate_fi(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Force Index."""
        period = params.get('period', 13)

        if PANDAS_TA_AVAILABLE:
            values = ta.efi(data['close'], data['volume'], length=period)
        else:
            # Manual calculation
            force = (data['close'].diff() * data['volume'])
            values = force.ewm(span=period, adjust=False).mean()

        return VolumeIndicators.create_result(
            IndicatorType.FI, values, params
        )

    @staticmethod
    def calculate_vwap(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate VWAP."""
        if PANDAS_TA_AVAILABLE:
            values = ta.vwap(
                data['high'],
                data['low'],
                data['close'],
                data['volume']
            )
        else:
            # Manual calculation
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            cumulative_tpv = (typical_price * data['volume']).cumsum()
            cumulative_volume = data['volume'].cumsum()
            values = cumulative_tpv / cumulative_volume

        return VolumeIndicators.create_result(
            IndicatorType.VWAP, values, params
        )
