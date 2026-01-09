"""Indicator Calculator - Wrapper for IndicatorEngine.

This module provides a simplified interface to the IndicatorEngine
for use by MarketContextBuilder. It calculates all required indicators
and adds them as columns to the DataFrame.

Created to resolve ImportError after market_context.py refactoring.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from src.core.indicators import IndicatorConfig, IndicatorEngine, IndicatorType

if TYPE_CHECKING:
    from .market_context_config import MarketContextBuilderConfig

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    Calculates technical indicators for MarketContextBuilder.

    Wraps the IndicatorEngine to provide a simple calculate_indicators() method.
    """

    def __init__(self, config: "MarketContextBuilderConfig"):
        """
        Initialize indicator calculator.

        Args:
            config: MarketContextBuilderConfig instance
        """
        self.config = config
        self._engine = IndicatorEngine(cache_size=100)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators required by MarketContext.

        Adds indicator columns to the DataFrame in-place.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            DataFrame with added indicator columns
        """
        if df is None or df.empty:
            logger.warning("Empty DataFrame provided to calculate_indicators")
            return df

        try:
            # EMAs
            for period in [9, 20, 50, 200]:
                config = IndicatorConfig(
                    indicator_type=IndicatorType.EMA,
                    params={"period": period, "price": "close"},
                    use_talib=True,
                    cache_results=True,
                )
                result = self._engine.calculate(df, config)
                df[f"ema_{period}"] = result.values

            # Calculate EMA distance percentages
            if "close" in df.columns and "ema_20" in df.columns:
                df["ema_20_distance_pct"] = ((df["close"] - df["ema_20"]) / df["ema_20"]) * 100
            if "close" in df.columns and "ema_50" in df.columns:
                df["ema_50_distance_pct"] = ((df["close"] - df["ema_50"]) / df["ema_50"]) * 100

            # RSI
            rsi_config = IndicatorConfig(
                indicator_type=IndicatorType.RSI,
                params={"period": 14},
                use_talib=True,
                cache_results=True,
            )
            rsi_result = self._engine.calculate(df, rsi_config)
            df["rsi_14"] = rsi_result.values

            # MACD
            macd_config = IndicatorConfig(
                indicator_type=IndicatorType.MACD,
                params={"fast_period": 12, "slow_period": 26, "signal_period": 9},
                use_talib=True,
                cache_results=True,
            )
            macd_result = self._engine.calculate(df, macd_config)
            if isinstance(macd_result.values, pd.DataFrame):
                df["macd_line"] = macd_result.values["macd"]
                df["macd_signal"] = macd_result.values["signal"]
                df["macd_histogram"] = macd_result.values["histogram"]

            # Stochastic
            stoch_config = IndicatorConfig(
                indicator_type=IndicatorType.STOCH,
                params={"k_period": 14, "d_period": 3, "smooth": 3},
                use_talib=True,
                cache_results=True,
            )
            stoch_result = self._engine.calculate(df, stoch_config)
            if isinstance(stoch_result.values, pd.DataFrame):
                df["stoch_k"] = stoch_result.values["k"]
                df["stoch_d"] = stoch_result.values["d"]

            # Bollinger Bands
            bb_config = IndicatorConfig(
                indicator_type=IndicatorType.BB,
                params={"period": 20, "std_dev": 2},
                use_talib=True,
                cache_results=True,
            )
            bb_result = self._engine.calculate(df, bb_config)
            if isinstance(bb_result.values, pd.DataFrame):
                df["bb_upper"] = bb_result.values["upper"]
                df["bb_middle"] = bb_result.values["middle"]
                df["bb_lower"] = bb_result.values["lower"]

                # Calculate BB %B (position within bands)
                bb_range = df["bb_upper"] - df["bb_lower"]
                df["bb_pct_b"] = (df["close"] - df["bb_lower"]) / bb_range
                df["bb_width"] = bb_range / df["bb_middle"]

            # ATR
            atr_config = IndicatorConfig(
                indicator_type=IndicatorType.ATR,
                params={"period": 14},
                use_talib=True,
                cache_results=True,
            )
            atr_result = self._engine.calculate(df, atr_config)
            df["atr_14"] = atr_result.values

            # Calculate ATR as percentage of price
            if "close" in df.columns and "atr_14" in df.columns:
                df["atr_percent"] = (df["atr_14"] / df["close"]) * 100

            # ADX
            adx_config = IndicatorConfig(
                indicator_type=IndicatorType.ADX,
                params={"period": 14},
                use_talib=True,
                cache_results=True,
            )
            adx_result = self._engine.calculate(df, adx_config)
            if isinstance(adx_result.values, pd.DataFrame):
                df["adx_14"] = adx_result.values["adx"]
                df["plus_di"] = adx_result.values["plus_di"]
                df["minus_di"] = adx_result.values["minus_di"]

            # Volume SMA
            volume_sma_config = IndicatorConfig(
                indicator_type=IndicatorType.SMA,
                params={"period": 20, "price": "volume"},
                use_talib=True,
                cache_results=True,
            )
            volume_sma_result = self._engine.calculate(df, volume_sma_config)
            df["volume_sma_20"] = volume_sma_result.values

            # Calculate volume ratio
            if "volume" in df.columns and "volume_sma_20" in df.columns:
                df["volume_ratio"] = df["volume"] / df["volume_sma_20"]

            logger.debug(f"Calculated {len(df.columns)} indicator columns for {len(df)} rows")

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)

        return df
