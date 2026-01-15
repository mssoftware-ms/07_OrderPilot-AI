"""Technical Indicator Engine - Refactored.

Coordinates indicator calculations using modular calculator classes.
Provides caching and event emission for performance.
"""

import logging
from collections.abc import Callable
from datetime import datetime

import pandas as pd

from src.common.event_bus import Event, EventType, event_bus

from .base import BaseIndicatorCalculator, PANDAS_TA_AVAILABLE, TALIB_AVAILABLE
from .custom import CustomIndicators
from .momentum import MomentumIndicators
from .trend import TrendIndicators
from .types import IndicatorConfig, IndicatorResult, IndicatorType
from .volatility import VolatilityIndicators
from .volume import VolumeIndicators

logger = logging.getLogger(__name__)


class IndicatorEngine:
    """Engine for calculating technical indicators."""

    def __init__(self, cache_size: int = 100):
        """Initialize indicator engine.

        Args:
            cache_size: Size of LRU cache for results
        """
        self.cache_size = cache_size
        self.cache: dict[str, IndicatorResult] = {}

        # Register indicator calculators by type
        self.calculators: dict[IndicatorType, Callable] = {
            # Trend
            IndicatorType.SMA: TrendIndicators.calculate_sma,
            IndicatorType.EMA: TrendIndicators.calculate_ema,
            IndicatorType.WMA: TrendIndicators.calculate_wma,
            IndicatorType.VWMA: TrendIndicators.calculate_vwma,
            IndicatorType.MACD: TrendIndicators.calculate_macd,
            IndicatorType.ADX: TrendIndicators.calculate_adx,
            IndicatorType.PSAR: TrendIndicators.calculate_psar,
            IndicatorType.ICHIMOKU: TrendIndicators.calculate_ichimoku,

            # Momentum
            IndicatorType.RSI: MomentumIndicators.calculate_rsi,
            IndicatorType.STOCH: MomentumIndicators.calculate_stoch,
            IndicatorType.MOM: MomentumIndicators.calculate_mom,
            IndicatorType.ROC: MomentumIndicators.calculate_roc,
            IndicatorType.WILLR: MomentumIndicators.calculate_willr,
            IndicatorType.CCI: MomentumIndicators.calculate_cci,
            IndicatorType.MFI: MomentumIndicators.calculate_mfi,

            # Volatility
            IndicatorType.BB: VolatilityIndicators.calculate_bb,
            IndicatorType.BB_WIDTH: VolatilityIndicators.calculate_bb_width,
            IndicatorType.BB_PERCENT: VolatilityIndicators.calculate_bb_percent,
            IndicatorType.KC: VolatilityIndicators.calculate_kc,
            IndicatorType.ATR: VolatilityIndicators.calculate_atr,
            IndicatorType.NATR: VolatilityIndicators.calculate_natr,
            IndicatorType.STD: VolatilityIndicators.calculate_std,

            # Volume
            IndicatorType.OBV: VolumeIndicators.calculate_obv,
            IndicatorType.CMF: VolumeIndicators.calculate_cmf,
            IndicatorType.AD: VolumeIndicators.calculate_ad,
            IndicatorType.FI: VolumeIndicators.calculate_fi,
            IndicatorType.VWAP: VolumeIndicators.calculate_vwap,

            # Custom
            IndicatorType.PIVOTS: CustomIndicators.calculate_pivots,
            IndicatorType.SUPPORT_RESISTANCE: CustomIndicators.calculate_support_resistance,
            IndicatorType.PATTERN: CustomIndicators.calculate_patterns
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
        if not BaseIndicatorCalculator.validate_data(data, config):
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

    def _get_cache_key(self, data: pd.DataFrame, config: IndicatorConfig) -> str:
        """Generate cache key."""
        data_hash = hash(str(data.index[-1]) + str(len(data)))
        params_hash = hash(str(sorted(config.params.items())))

        return f"{config.indicator_type.value}_{data_hash}_{params_hash}"

    def clear_cache(self) -> None:
        """Clear indicator cache."""
        self.cache.clear()
        logger.info("Indicator cache cleared")
