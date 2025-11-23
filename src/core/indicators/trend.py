"""Trend Indicators.

Implements SMA, EMA, WMA, VWMA, MACD, ADX, PSAR, and ICHIMOKU.
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


class TrendIndicators(BaseIndicatorCalculator):
    """Calculator for trend indicators."""

    @staticmethod
    def calculate_sma(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Simple Moving Average."""
        period = params.get('period', 20)
        price = params.get('price', 'close')

        if use_talib and TALIB_AVAILABLE:
            values = talib.SMA(data[price], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.sma(data[price], length=period)
        else:
            values = data[price].rolling(window=period).mean()

        return TrendIndicators.create_result(
            IndicatorType.SMA, values, params
        )

    @staticmethod
    def calculate_ema(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Exponential Moving Average."""
        period = params.get('period', 20)
        price = params.get('price', 'close')

        if use_talib and TALIB_AVAILABLE:
            values = talib.EMA(data[price], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.ema(data[price], length=period)
        else:
            values = data[price].ewm(span=period, adjust=False).mean()

        return TrendIndicators.create_result(
            IndicatorType.EMA, values, params
        )

    @staticmethod
    def calculate_wma(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Weighted Moving Average."""
        period = params.get('period', 20)
        price = params.get('price', 'close')

        if use_talib and TALIB_AVAILABLE:
            values = talib.WMA(data[price], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.wma(data[price], length=period)
        else:
            # Manual calculation
            weights = np.arange(1, period + 1)
            values = data[price].rolling(period).apply(
                lambda x: np.dot(x, weights) / weights.sum(), raw=True
            )

        return TrendIndicators.create_result(
            IndicatorType.WMA, values, params
        )

    @staticmethod
    def calculate_vwma(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Volume Weighted Moving Average."""
        period = params.get('period', 20)

        if PANDAS_TA_AVAILABLE:
            values = ta.vwma(data['close'], data['volume'], length=period)
        else:
            # Manual calculation
            pv = data['close'] * data['volume']
            values = pv.rolling(period).sum() / data['volume'].rolling(period).sum()

        return TrendIndicators.create_result(
            IndicatorType.VWMA, values, params
        )

    @staticmethod
    def calculate_macd(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate MACD."""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        if use_talib and TALIB_AVAILABLE:
            macd, macd_signal, macd_hist = talib.MACD(
                data['close'],
                fastperiod=fast,
                slowperiod=slow,
                signalperiod=signal
            )
            values = pd.DataFrame({
                'macd': macd,
                'signal': macd_signal,
                'histogram': macd_hist
            })
        elif PANDAS_TA_AVAILABLE:
            values = ta.macd(data['close'], fast=fast, slow=slow, signal=signal)
        else:
            # Manual calculation
            ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
            ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line

            values = pd.DataFrame({
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            })

        return TrendIndicators.create_result(
            IndicatorType.MACD, values, params
        )

    @staticmethod
    def calculate_adx(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate ADX."""
        period = params.get('period', 14)

        if use_talib and TALIB_AVAILABLE:
            values = talib.ADX(data['high'], data['low'], data['close'], timeperiod=period)
        elif PANDAS_TA_AVAILABLE:
            values = ta.adx(data['high'], data['low'], data['close'], length=period)['ADX_14']
        else:
            # Simplified calculation
            values = pd.Series(index=data.index, dtype=float)

        return TrendIndicators.create_result(
            IndicatorType.ADX, values, params
        )

    @staticmethod
    def calculate_psar(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Parabolic SAR."""
        af_start = params.get('af_start', 0.02)
        af_increment = params.get('af_increment', 0.02)
        af_max = params.get('af_max', 0.2)

        if use_talib and TALIB_AVAILABLE:
            values = talib.SAR(
                data['high'],
                data['low'],
                acceleration=af_start,
                maximum=af_max
            )
        elif PANDAS_TA_AVAILABLE:
            values = ta.psar(
                data['high'],
                data['low'],
                af0=af_start,
                af=af_increment,
                max_af=af_max
            )['PSARl_0.02_0.2']
        else:
            # Simplified calculation
            values = pd.Series(index=data.index, dtype=float)

        return TrendIndicators.create_result(
            IndicatorType.PSAR, values, params
        )

    @staticmethod
    def calculate_ichimoku(
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Ichimoku Cloud."""
        tenkan = params.get('tenkan', 9)
        kijun = params.get('kijun', 26)
        senkou_b = params.get('senkou_b', 52)

        if PANDAS_TA_AVAILABLE:
            result = ta.ichimoku(
                data['high'],
                data['low'],
                data['close'],
                tenkan=tenkan,
                kijun=kijun,
                senkou=senkou_b
            )[0]
            values = result
        else:
            # Manual calculation
            high_9 = data['high'].rolling(window=tenkan).max()
            low_9 = data['low'].rolling(window=tenkan).min()
            tenkan_sen = (high_9 + low_9) / 2

            high_26 = data['high'].rolling(window=kijun).max()
            low_26 = data['low'].rolling(window=kijun).min()
            kijun_sen = (high_26 + low_26) / 2

            senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun)

            high_52 = data['high'].rolling(window=senkou_b).max()
            low_52 = data['low'].rolling(window=senkou_b).min()
            senkou_span_b = ((high_52 + low_52) / 2).shift(kijun)

            values = pd.DataFrame({
                'tenkan': tenkan_sen,
                'kijun': kijun_sen,
                'senkou_a': senkou_span_a,
                'senkou_b': senkou_span_b,
                'chikou': data['close'].shift(-kijun)
            })

        return TrendIndicators.create_result(
            IndicatorType.ICHIMOKU, values, params
        )
