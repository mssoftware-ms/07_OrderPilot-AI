"""Orchestrator Features - Feature calculation with indicators.

Refactored from 666 LOC monolith using composition pattern.

Module 3/6 of orchestrator.py split.

Contains:
- calculate_features(): Extract technical analysis features for each timeframe
"""

from __future__ import annotations

import logging
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.indicators.engine import IndicatorEngine

from src.core.indicators.types import IndicatorConfig, IndicatorType

logger = logging.getLogger(__name__)


class OrchestratorFeatures:
    """Helper für AnalysisWorker feature calculation."""

    def __init__(self, parent):
        """
        Args:
            parent: AnalysisWorker Instanz
        """
        self.parent = parent

    def calculate_features(self, data_map: dict) -> dict:
        """Extract technical analysis features for each timeframe.

        Args:
            data_map: Dict mapping timeframe string to DataFrame

        Returns:
            Dict mapping timeframe to feature dict
        """
        features = {}

        for tf, df in data_map.items():
            if df.empty:
                continue

            try:
                # Calculate all indicators and build feature dict
                basic_stats = self._calculate_basic_stats(df)
                indicators = self._calculate_all_indicators(df, basic_stats['last_close'])
                features[tf] = self._build_feature_dict(basic_stats, indicators)

            except Exception as e:
                # Safe fallback
                last_close = df['close'].iloc[-1]
                change_pct = ((last_close - df['open'].iloc[0]) / df['open'].iloc[0]) * 100
                features[tf] = self._build_error_fallback(len(df), last_close, change_pct, str(e))

        return features

    def _calculate_basic_stats(self, df: pd.DataFrame) -> dict:
        """Calculate basic price statistics.

        Args:
            df: DataFrame with OHLCV data.

        Returns:
            Dict with last_close and change_pct.
        """
        last_close = df['close'].iloc[-1]
        change_pct = ((last_close - df['open'].iloc[0]) / df['open'].iloc[0]) * 100
        return {
            'last_close': last_close,
            'change_pct': change_pct,
            'bars': len(df)
        }

    def _calculate_all_indicators(self, df: pd.DataFrame, last_close: float) -> dict:
        """Calculate all technical indicators.

        Args:
            df: DataFrame with OHLCV data.
            last_close: Last closing price.

        Returns:
            Dict with all indicator values.
        """
        rsi_value, rsi_state = self._calculate_rsi(df)
        ema_value, ema_distance_pct, trend_state = self._calculate_ema_trend(df, last_close)
        bb_percent = self._calculate_bollinger_bands(df, last_close)
        atr_value, atr_pct = self._calculate_atr(df, last_close)
        adx_value = self._calculate_adx(df)
        support_levels, resistance_levels = self._calculate_support_resistance(df)

        return {
            'rsi': rsi_value,
            'rsi_state': rsi_state,
            'ema20': ema_value,
            'ema20_distance_pct': ema_distance_pct,
            'trend_state': trend_state,
            'bb_percent': bb_percent,
            'atr': atr_value,
            'atr_pct': atr_pct,
            'adx': adx_value,
            'support_levels': support_levels,
            'resistance_levels': resistance_levels
        }

    def _calculate_rsi(self, df: pd.DataFrame) -> tuple[float, str]:
        """Calculate RSI with state determination.

        Returns:
            Tuple of (rsi_value, rsi_state).
        """
        rsi_config = IndicatorConfig(
            indicator_type=IndicatorType.RSI,
            params={'period': 14}
        )
        rsi_result = self.parent.indicator_engine.calculate(df, rsi_config)
        rsi_value = float(rsi_result.values.iloc[-1]) if isinstance(rsi_result.values, pd.Series) else 50.0
        rsi_state = self._determine_rsi_state(rsi_value)
        return rsi_value, rsi_state

    def _determine_rsi_state(self, rsi_value: float) -> str:
        """Determine RSI state from value.

        Args:
            rsi_value: RSI value (0-100).

        Returns:
            RSI state string.
        """
        if rsi_value > 70:
            return "Overbought"
        elif rsi_value < 30:
            return "Oversold"
        else:
            return "Neutral"

    def _calculate_ema_trend(self, df: pd.DataFrame, last_close: float) -> tuple[float, float, str]:
        """Calculate EMA with trend determination.

        Returns:
            Tuple of (ema_value, ema_distance_pct, trend_state).
        """
        ema_config = IndicatorConfig(
            indicator_type=IndicatorType.EMA,
            params={'period': 20, 'price': 'close'}
        )
        ema_result = self.parent.indicator_engine.calculate(df, ema_config)
        ema_value = float(ema_result.values.iloc[-1]) if isinstance(ema_result.values, pd.Series) else last_close
        ema_distance_pct = ((last_close - ema_value) / ema_value) * 100
        trend_state = self._determine_trend_state(ema_distance_pct)
        return ema_value, ema_distance_pct, trend_state

    def _determine_trend_state(self, ema_distance_pct: float) -> str:
        """Determine trend state from EMA distance.

        Args:
            ema_distance_pct: Distance from EMA in percent.

        Returns:
            Trend state string.
        """
        if ema_distance_pct > 1.0:
            return "Strong Uptrend"
        elif ema_distance_pct > 0:
            return "Uptrend"
        elif ema_distance_pct < -1.0:
            return "Strong Downtrend"
        elif ema_distance_pct < 0:
            return "Downtrend"
        else:
            return "Neutral"

    def _calculate_bollinger_bands(self, df: pd.DataFrame, last_close: float) -> float:
        """Calculate Bollinger Bands percentage.

        Returns:
            BB percentage (0-100).
        """
        bb_config = IndicatorConfig(
            indicator_type=IndicatorType.BB,
            params={'period': 20, 'std': 2}
        )
        bb_result = self.parent.indicator_engine.calculate(df, bb_config)

        if isinstance(bb_result.values, pd.DataFrame):
            bb_upper = float(bb_result.values['upper'].iloc[-1])
            bb_lower = float(bb_result.values['lower'].iloc[-1])
            return ((last_close - bb_lower) / (bb_upper - bb_lower)) * 100 if bb_upper != bb_lower else 50.0
        else:
            return 50.0

    def _calculate_atr(self, df: pd.DataFrame, last_close: float) -> tuple[float, float]:
        """Calculate ATR with percentage.

        Returns:
            Tuple of (atr_value, atr_pct).
        """
        atr_config = IndicatorConfig(
            indicator_type=IndicatorType.ATR,
            params={'period': 14}
        )
        atr_result = self.parent.indicator_engine.calculate(df, atr_config)
        atr_value = float(atr_result.values.iloc[-1]) if isinstance(atr_result.values, pd.Series) else 0.0
        atr_pct = (atr_value / last_close) * 100 if last_close > 0 else 0.0
        return atr_value, atr_pct

    def _calculate_adx(self, df: pd.DataFrame) -> float:
        """Calculate ADX value.

        Returns:
            ADX value (0-100).
        """
        adx_config = IndicatorConfig(
            indicator_type=IndicatorType.ADX,
            params={'period': 14}
        )
        adx_result = self.parent.indicator_engine.calculate(df, adx_config)

        if isinstance(adx_result.values, pd.DataFrame) and 'adx' in adx_result.values.columns:
            return float(adx_result.values['adx'].iloc[-1])
        elif isinstance(adx_result.values, pd.Series):
            return float(adx_result.values.iloc[-1])
        else:
            return 0.0

    def _calculate_support_resistance(self, df: pd.DataFrame) -> tuple[list, list]:
        """Calculate support and resistance levels.

        Returns:
            Tuple of (support_levels, resistance_levels).
        """
        sr_config = IndicatorConfig(
            indicator_type=IndicatorType.SUPPORT_RESISTANCE,
            params={'window': 20, 'num_levels': 3}
        )
        sr_result = self.parent.indicator_engine.calculate(df, sr_config)

        support_levels = []
        resistance_levels = []
        if isinstance(sr_result.values, dict):
            support_levels = sr_result.values.get('support', [])
            resistance_levels = sr_result.values.get('resistance', [])

        return support_levels, resistance_levels

    def _build_feature_dict(self, basic_stats: dict, indicators: dict) -> dict:
        """Build feature dictionary from stats and indicators.

        Args:
            basic_stats: Basic statistics dict.
            indicators: Indicators dict.

        Returns:
            Complete feature dict.
        """
        return {
            "bars": basic_stats['bars'],
            "last_price": basic_stats['last_close'],
            "period_change_pct": round(basic_stats['change_pct'], 2),
            "rsi": round(indicators['rsi'], 2),
            "rsi_state": indicators['rsi_state'],
            "ema20": round(indicators['ema20'], 4),
            "ema20_distance_pct": round(indicators['ema20_distance_pct'], 2),
            "trend_state": indicators['trend_state'],
            "bb_percent": round(indicators['bb_percent'], 2),
            "atr": round(indicators['atr'], 4),
            "atr_pct": round(indicators['atr_pct'], 2),
            "adx": round(indicators['adx'], 2),
            "support_levels": [round(x, 4) for x in indicators['support_levels']],
            "resistance_levels": [round(x, 4) for x in indicators['resistance_levels']]
        }

    def _build_error_fallback(self, bars: int, last_close: float, change_pct: float, error: str) -> dict:
        """Build error fallback feature dict with neutral values.

        Args:
            bars: Number of bars.
            last_close: Last closing price.
            change_pct: Period change percentage.
            error: Error message.

        Returns:
            Error fallback feature dict.
        """
        return {
            "bars": bars,
            "last_price": last_close,
            "period_change_pct": round(change_pct, 2),
            "rsi": 50.0,
            "rsi_state": "Neutral",
            "ema20": last_close,
            "ema20_distance_pct": 0.0,
            "trend_state": "Neutral",
            "bb_percent": 50.0,
            "atr": 0.0,
            "atr_pct": 0.0,
            "adx": 0.0,
            "support_levels": [],
            "resistance_levels": [],
            "error": error
        }
