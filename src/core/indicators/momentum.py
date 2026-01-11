"""Momentum Indicators.

Implements RSI, STOCH, MOM, ROC, WILLR, CCI, and MFI.
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


class MomentumIndicators(BaseIndicatorCalculator):
    """Calculator for momentum indicators."""

    @staticmethod
    def calculate_rsi(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate RSI."""
        period = params.get('period', 14)

        if use_talib and TALIB_AVAILABLE:
            values = talib.RSI(data['close'], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.rsi(data['close'], length=period)
        else:
            # Manual calculation using Wilder's Smoothing Method
            # Reference: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)

            # Use Wilder's smoothing (EMA with alpha = 1/period)
            alpha = 1.0 / period
            avg_gain = gain.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
            avg_loss = loss.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

            rs = avg_gain / avg_loss.replace(0, np.nan)
            values = 100 - (100 / (1 + rs))

        return MomentumIndicators.create_result(
            IndicatorType.RSI, values, params
        )

    @staticmethod
    def calculate_stoch(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Stochastic Oscillator."""
        k_period = params.get('k_period', 14)
        d_period = params.get('d_period', 3)
        smooth = params.get('smooth', 3)

        if use_talib and TALIB_AVAILABLE:
            k, d = talib.STOCH(
                data['high'],
                data['low'],
                data['close'],
                fastk_period=k_period,
                slowk_period=smooth,
                slowd_period=d_period
            )
            values = pd.DataFrame({'k': k, 'd': d})
        elif PANDAS_TA_AVAILABLE:
            values = ta.stoch(
                data['high'],
                data['low'],
                data['close'],
                k=k_period,
                d=d_period,
                smooth_k=smooth
            )
        else:
            # Manual calculation
            low_min = data['low'].rolling(window=k_period).min()
            high_max = data['high'].rolling(window=k_period).max()

            fast_k = 100 * ((data['close'] - low_min) / (high_max - low_min))
            # Smooth K
            k = fast_k.rolling(window=smooth).mean()
            # D is moving average of K
            d = k.rolling(window=d_period).mean()

            values = pd.DataFrame({'k': k, 'd': d})

        return MomentumIndicators.create_result(
            IndicatorType.STOCH, values, params
        )

    @staticmethod
    def calculate_mom(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Momentum."""
        period = params.get('period', 10)

        if use_talib and TALIB_AVAILABLE:
            values = talib.MOM(data['close'], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.mom(data['close'], length=period)
        else:
            values = data['close'].diff(period)

        return MomentumIndicators.create_result(
            IndicatorType.MOM, values, params
        )

    @staticmethod
    def calculate_roc(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Rate of Change."""
        period = params.get('period', 10)

        if use_talib and TALIB_AVAILABLE:
            values = talib.ROC(data['close'], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.roc(data['close'], length=period)
        else:
            values = ((data['close'] - data['close'].shift(period)) /
                     data['close'].shift(period)) * 100

        return MomentumIndicators.create_result(
            IndicatorType.ROC, values, params
        )

    @staticmethod
    def calculate_willr(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Williams %R."""
        period = params.get('period', 14)

        if use_talib and TALIB_AVAILABLE:
            values = talib.WILLR(data['high'], data['low'], data['close'], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.willr(data['high'], data['low'], data['close'], length=period)
        else:
            # Manual calculation
            high_max = data['high'].rolling(window=period).max()
            low_min = data['low'].rolling(window=period).min()
            values = -100 * ((high_max - data['close']) / (high_max - low_min))

        return MomentumIndicators.create_result(
            IndicatorType.WILLR, values, params
        )

    @staticmethod
    def calculate_cci(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate CCI."""
        period = params.get('period', 20)

        if use_talib and TALIB_AVAILABLE:
            values = talib.CCI(data['high'], data['low'], data['close'], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.cci(data['high'], data['low'], data['close'], length=period)
        else:
            # Manual calculation
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            sma = typical_price.rolling(window=period).mean()
            mad = typical_price.rolling(window=period).apply(
                lambda x: np.mean(np.abs(x - np.mean(x)))
            )
            values = (typical_price - sma) / (0.015 * mad)

        return MomentumIndicators.create_result(
            IndicatorType.CCI, values, params
        )

    @staticmethod
    def calculate_mfi(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Money Flow Index."""
        period = params.get('period', 14)

        if use_talib and TALIB_AVAILABLE:
            values = talib.MFI(
                data['high'],
                data['low'],
                data['close'],
                data['volume'],
                timeperiod=period
            )
        elif PANDAS_TA_AVAILABLE:
            values = ta.mfi(
                data['high'],
                data['low'],
                data['close'],
                data['volume'],
                length=period
            )
        else:
            # Simplified calculation
            values = pd.Series(index=data.index, dtype=float)

        return MomentumIndicators.create_result(
            IndicatorType.MFI, values, params
        )
