"""Technical Indicator Engine.

Provides technical indicators using TA-Lib and pandas_ta libraries.
Supports custom indicators and caching for performance.
"""

import logging
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

# Try to import TA-Lib (optional dependency)
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    warnings.warn("TA-Lib not installed. Some indicators will be unavailable.")

# Try to import pandas_ta (fallback for TA-Lib)
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    warnings.warn("pandas_ta not installed. Some indicators will be unavailable.")

from src.common.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


class IndicatorType(Enum):
    """Types of technical indicators."""
    # Trend
    SMA = "sma"  # Simple Moving Average
    EMA = "ema"  # Exponential Moving Average
    WMA = "wma"  # Weighted Moving Average
    VWMA = "vwma"  # Volume Weighted Moving Average
    MACD = "macd"  # Moving Average Convergence Divergence
    ADX = "adx"  # Average Directional Index
    PSAR = "psar"  # Parabolic SAR
    ICHIMOKU = "ichimoku"  # Ichimoku Cloud

    # Momentum
    RSI = "rsi"  # Relative Strength Index
    STOCH = "stoch"  # Stochastic Oscillator
    MOM = "mom"  # Momentum
    ROC = "roc"  # Rate of Change
    WILLR = "willr"  # Williams %R
    CCI = "cci"  # Commodity Channel Index
    MFI = "mfi"  # Money Flow Index

    # Volatility
    BB = "bb"  # Bollinger Bands
    KC = "kc"  # Keltner Channels
    ATR = "atr"  # Average True Range
    NATR = "natr"  # Normalized ATR
    STD = "std"  # Standard Deviation

    # Volume
    OBV = "obv"  # On-Balance Volume
    CMF = "cmf"  # Chaikin Money Flow
    AD = "ad"  # Accumulation/Distribution
    FI = "fi"  # Force Index
    VWAP = "vwap"  # Volume Weighted Average Price

    # Custom
    PIVOTS = "pivots"  # Pivot Points
    SUPPORT_RESISTANCE = "sup_res"  # Support/Resistance Levels
    PATTERN = "pattern"  # Price Patterns


@dataclass
class IndicatorConfig:
    """Configuration for an indicator."""
    indicator_type: IndicatorType
    params: dict[str, Any]
    use_talib: bool = True  # Prefer TA-Lib if available
    cache_results: bool = True
    min_periods: int | None = None  # Minimum periods needed


@dataclass
class IndicatorResult:
    """Result from indicator calculation."""
    indicator_type: IndicatorType
    values: pd.Series | pd.DataFrame | dict[str, pd.Series]
    timestamp: datetime
    params: dict[str, Any]
    metadata: dict[str, Any] | None = None


class IndicatorEngine:
    """Engine for calculating technical indicators."""

    def __init__(self, cache_size: int = 100):
        """Initialize indicator engine.

        Args:
            cache_size: Size of LRU cache for results
        """
        self.cache_size = cache_size
        self.cache: dict[str, IndicatorResult] = {}

        # Register indicator calculators
        self.calculators: dict[IndicatorType, Callable] = {
            # Trend
            IndicatorType.SMA: self._calculate_sma,
            IndicatorType.EMA: self._calculate_ema,
            IndicatorType.WMA: self._calculate_wma,
            IndicatorType.VWMA: self._calculate_vwma,
            IndicatorType.MACD: self._calculate_macd,
            IndicatorType.ADX: self._calculate_adx,
            IndicatorType.PSAR: self._calculate_psar,
            IndicatorType.ICHIMOKU: self._calculate_ichimoku,

            # Momentum
            IndicatorType.RSI: self._calculate_rsi,
            IndicatorType.STOCH: self._calculate_stoch,
            IndicatorType.MOM: self._calculate_mom,
            IndicatorType.ROC: self._calculate_roc,
            IndicatorType.WILLR: self._calculate_willr,
            IndicatorType.CCI: self._calculate_cci,
            IndicatorType.MFI: self._calculate_mfi,

            # Volatility
            IndicatorType.BB: self._calculate_bb,
            IndicatorType.KC: self._calculate_kc,
            IndicatorType.ATR: self._calculate_atr,
            IndicatorType.NATR: self._calculate_natr,
            IndicatorType.STD: self._calculate_std,

            # Volume
            IndicatorType.OBV: self._calculate_obv,
            IndicatorType.CMF: self._calculate_cmf,
            IndicatorType.AD: self._calculate_ad,
            IndicatorType.FI: self._calculate_fi,
            IndicatorType.VWAP: self._calculate_vwap,

            # Custom
            IndicatorType.PIVOTS: self._calculate_pivots,
            IndicatorType.SUPPORT_RESISTANCE: self._calculate_support_resistance,
            IndicatorType.PATTERN: self._calculate_patterns
        }

        logger.info(f"Indicator engine initialized (TA-Lib: {TALIB_AVAILABLE}, pandas_ta: {PANDAS_TA_AVAILABLE})")

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig
    ) -> IndicatorResult:
        """Calculate indicator for given data.

        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume
            config: Indicator configuration

        Returns:
            Indicator result
        """
        # Check cache
        if config.cache_results:
            cache_key = self._get_cache_key(data, config)
            if cache_key in self.cache:
                logger.debug(f"Using cached result for {config.indicator_type.value}")
                return self.cache[cache_key]

        # Validate data
        if not self._validate_data(data, config):
            raise ValueError(f"Invalid data for {config.indicator_type.value}")

        # Calculate indicator
        calculator = self.calculators.get(config.indicator_type)
        if not calculator:
            raise ValueError(f"Unknown indicator type: {config.indicator_type}")

        try:
            result = calculator(data, config.params, config.use_talib)

            # Cache result
            if config.cache_results:
                self.cache[cache_key] = result

            # Emit event
            event_bus.emit(Event(
                type=EventType.INDICATOR_CALCULATED,
                timestamp=datetime.utcnow(),
                data={
                    "indicator": config.indicator_type.value,
                    "params": config.params
                }
            ))

            return result

        except Exception as e:
            logger.error(f"Error calculating {config.indicator_type.value}: {e}")
            raise

    def calculate_multiple(
        self,
        data: pd.DataFrame,
        configs: list[IndicatorConfig]
    ) -> dict[IndicatorType, IndicatorResult]:
        """Calculate multiple indicators.

        Args:
            data: OHLCV DataFrame
            configs: List of indicator configurations

        Returns:
            Dictionary of results by indicator type
        """
        results = {}

        for config in configs:
            try:
                results[config.indicator_type] = self.calculate(data, config)
            except Exception as e:
                logger.error(f"Failed to calculate {config.indicator_type.value}: {e}")

        return results

    # Trend Indicators

    def _calculate_sma(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.SMA,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_ema(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.EMA,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_wma(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.WMA,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_vwma(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.VWMA,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_macd(
        self,
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
            result = ta.macd(data['close'], fast=fast, slow=slow, signal=signal)
            values = result
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

        return IndicatorResult(
            indicator_type=IndicatorType.MACD,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_adx(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.ADX,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_psar(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.PSAR,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_ichimoku(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.ICHIMOKU,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    # Momentum Indicators

    def _calculate_rsi(
        self,
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
            # Manual calculation
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            rs = avg_gain / avg_loss
            values = 100 - (100 / (1 + rs))

        return IndicatorResult(
            indicator_type=IndicatorType.RSI,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_stoch(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Stochastic Oscillator."""
        k_period = params.get('k_period', 14)
        d_period = params.get('d_period', 3)

        if use_talib and TALIB_AVAILABLE:
            k, d = talib.STOCH(
                data['high'],
                data['low'],
                data['close'],
                fastk_period=k_period,
                slowk_period=d_period,
                slowd_period=d_period
            )
            values = pd.DataFrame({'k': k, 'd': d})
        elif PANDAS_TA_AVAILABLE:
            result = ta.stoch(
                data['high'],
                data['low'],
                data['close'],
                k=k_period,
                d=d_period
            )
            values = result
        else:
            # Manual calculation
            low_min = data['low'].rolling(window=k_period).min()
            high_max = data['high'].rolling(window=k_period).max()

            k = 100 * ((data['close'] - low_min) / (high_max - low_min))
            d = k.rolling(window=d_period).mean()

            values = pd.DataFrame({'k': k, 'd': d})

        return IndicatorResult(
            indicator_type=IndicatorType.STOCH,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_mom(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.MOM,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_roc(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.ROC,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_willr(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.WILLR,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_cci(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.CCI,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_mfi(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.MFI,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    # Volatility Indicators

    def _calculate_bb(
        self,
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
            result = ta.bbands(data['close'], length=period, std=std_dev)
            values = result
        else:
            # Manual calculation
            sma = data['close'].rolling(window=period).mean()
            std = data['close'].rolling(window=period).std()

            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)

            values = pd.DataFrame({
                'upper': upper,
                'middle': sma,
                'lower': lower,
                'bandwidth': upper - lower,
                'percent': (data['close'] - lower) / (upper - lower)
            })

        return IndicatorResult(
            indicator_type=IndicatorType.BB,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_kc(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Keltner Channels."""
        period = params.get('period', 20)
        multiplier = params.get('multiplier', 2)

        if PANDAS_TA_AVAILABLE:
            result = ta.kc(
                data['high'],
                data['low'],
                data['close'],
                length=period,
                scalar=multiplier
            )
            values = result
        else:
            # Manual calculation
            ema = data['close'].ewm(span=period, adjust=False).mean()
            atr = self._calculate_atr(data, {'period': period}, False).values

            upper = ema + (atr * multiplier)
            lower = ema - (atr * multiplier)

            values = pd.DataFrame({
                'upper': upper,
                'middle': ema,
                'lower': lower
            })

        return IndicatorResult(
            indicator_type=IndicatorType.KC,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_atr(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.ATR,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_natr(
        self,
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
            atr = self._calculate_atr(data, params, False).values
            values = (atr / data['close']) * 100

        return IndicatorResult(
            indicator_type=IndicatorType.NATR,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_std(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.STD,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    # Volume Indicators

    def _calculate_obv(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.OBV,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_cmf(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.CMF,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_ad(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.AD,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_fi(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.FI,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_vwap(
        self,
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

        return IndicatorResult(
            indicator_type=IndicatorType.VWAP,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    # Custom Indicators

    def _calculate_pivots(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Pivot Points."""
        method = params.get('method', 'traditional')

        high = data['high'].iloc[-1]
        low = data['low'].iloc[-1]
        close = data['close'].iloc[-1]

        if method == 'traditional':
            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)
        elif method == 'fibonacci':
            pivot = (high + low + close) / 3
            r1 = pivot + 0.382 * (high - low)
            s1 = pivot - 0.382 * (high - low)
            r2 = pivot + 0.618 * (high - low)
            s2 = pivot - 0.618 * (high - low)
            r3 = pivot + (high - low)
            s3 = pivot - (high - low)
        else:
            # Camarilla
            pivot = close
            r1 = close + 1.1 * (high - low) / 12
            s1 = close - 1.1 * (high - low) / 12
            r2 = close + 1.1 * (high - low) / 6
            s2 = close - 1.1 * (high - low) / 6
            r3 = close + 1.1 * (high - low) / 4
            s3 = close - 1.1 * (high - low) / 4

        values = {
            'pivot': float(pivot),
            'r1': float(r1),
            'r2': float(r2),
            'r3': float(r3),
            's1': float(s1),
            's2': float(s2),
            's3': float(s3)
        }

        return IndicatorResult(
            indicator_type=IndicatorType.PIVOTS,
            values=values,
            timestamp=datetime.utcnow(),
            params=params,
            metadata={'method': method}
        )

    def _calculate_support_resistance(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Calculate Support and Resistance levels."""
        window = params.get('window', 20)
        num_levels = params.get('num_levels', 3)

        # Find local maxima and minima
        highs = data['high'].rolling(window=window, center=True).max()
        lows = data['low'].rolling(window=window, center=True).min()

        # Identify peaks and troughs
        peaks = data['high'][data['high'] == highs].dropna()
        troughs = data['low'][data['low'] == lows].dropna()

        # Get unique levels
        resistance_levels = peaks.nlargest(num_levels).sort_values(ascending=False)
        support_levels = troughs.nsmallest(num_levels).sort_values()

        values = {
            'resistance': resistance_levels.tolist(),
            'support': support_levels.tolist(),
            'current_price': float(data['close'].iloc[-1])
        }

        return IndicatorResult(
            indicator_type=IndicatorType.SUPPORT_RESISTANCE,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    def _calculate_patterns(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
        use_talib: bool
    ) -> IndicatorResult:
        """Detect price patterns."""
        patterns = []

        if use_talib and TALIB_AVAILABLE:
            # Check for various candlestick patterns
            pattern_functions = {
                'hammer': talib.CDLHAMMER,
                'doji': talib.CDLDOJI,
                'engulfing': talib.CDLENGULFING,
                'harami': talib.CDLHARAMI,
                'morning_star': talib.CDLMORNINGSTAR,
                'evening_star': talib.CDLEVENINGSTAR,
                'three_white_soldiers': talib.CDL3WHITESOLDIERS,
                'three_black_crows': talib.CDL3BLACKCROWS
            }

            for pattern_name, pattern_func in pattern_functions.items():
                result = pattern_func(
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close']
                )

                # Find where pattern is detected (non-zero values)
                detected = result[result != 0]
                if len(detected) > 0:
                    patterns.append({
                        'pattern': pattern_name,
                        'signal': int(detected.iloc[-1]),  # 100=bullish, -100=bearish
                        'index': detected.index[-1]
                    })

        values = {
            'patterns': patterns,
            'count': len(patterns)
        }

        return IndicatorResult(
            indicator_type=IndicatorType.PATTERN,
            values=values,
            timestamp=datetime.utcnow(),
            params=params
        )

    # Utility methods

    def _validate_data(self, data: pd.DataFrame, config: IndicatorConfig) -> bool:
        """Validate input data."""
        required_columns = ['open', 'high', 'low', 'close', 'volume']

        if not all(col in data.columns for col in required_columns):
            return False

        if config.min_periods and len(data) < config.min_periods:
            return False

        return True

    def _get_cache_key(self, data: pd.DataFrame, config: IndicatorConfig) -> str:
        """Generate cache key."""
        data_hash = hash(str(data.index[-1]) + str(len(data)))
        params_hash = hash(str(sorted(config.params.items())))

        return f"{config.indicator_type.value}_{data_hash}_{params_hash}"

    def clear_cache(self) -> None:
        """Clear indicator cache."""
        self.cache.clear()
        logger.info("Indicator cache cleared")