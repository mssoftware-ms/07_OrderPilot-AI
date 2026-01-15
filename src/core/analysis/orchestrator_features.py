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
                # Basic stats
                last_close = df['close'].iloc[-1]
                change_pct = ((last_close - df['open'].iloc[0]) / df['open'].iloc[0]) * 100

                # RSI (14)
                rsi_config = IndicatorConfig(
                    indicator_type=IndicatorType.RSI,
                    params={'period': 14}
                )
                rsi_result = self.parent.indicator_engine.calculate(df, rsi_config)
                rsi_value = float(rsi_result.values.iloc[-1]) if isinstance(rsi_result.values, pd.Series) else 50.0

                # Determine RSI state
                if rsi_value > 70:
                    rsi_state = "Overbought"
                elif rsi_value < 30:
                    rsi_state = "Oversold"
                else:
                    rsi_state = "Neutral"

                # EMA (20)
                ema_config = IndicatorConfig(
                    indicator_type=IndicatorType.EMA,
                    params={'period': 20, 'price': 'close'}
                )
                ema_result = self.parent.indicator_engine.calculate(df, ema_config)
                ema_value = float(ema_result.values.iloc[-1]) if isinstance(ema_result.values, pd.Series) else last_close
                ema_distance_pct = ((last_close - ema_value) / ema_value) * 100

                # Determine trend state from EMA
                if ema_distance_pct > 1.0:
                    trend_state = "Strong Uptrend"
                elif ema_distance_pct > 0:
                    trend_state = "Uptrend"
                elif ema_distance_pct < -1.0:
                    trend_state = "Strong Downtrend"
                elif ema_distance_pct < 0:
                    trend_state = "Downtrend"
                else:
                    trend_state = "Neutral"

                # Bollinger Bands
                bb_config = IndicatorConfig(
                    indicator_type=IndicatorType.BB,
                    params={'period': 20, 'std': 2}
                )
                bb_result = self.parent.indicator_engine.calculate(df, bb_config)

                if isinstance(bb_result.values, pd.DataFrame):
                    bb_upper = float(bb_result.values['upper'].iloc[-1])
                    bb_middle = float(bb_result.values['middle'].iloc[-1])
                    bb_lower = float(bb_result.values['lower'].iloc[-1])
                    bb_percent = ((last_close - bb_lower) / (bb_upper - bb_lower)) * 100 if bb_upper != bb_lower else 50.0
                else:
                    bb_percent = 50.0

                # ATR (14)
                atr_config = IndicatorConfig(
                    indicator_type=IndicatorType.ATR,
                    params={'period': 14}
                )
                atr_result = self.parent.indicator_engine.calculate(df, atr_config)
                atr_value = float(atr_result.values.iloc[-1]) if isinstance(atr_result.values, pd.Series) else 0.0
                atr_pct = (atr_value / last_close) * 100 if last_close > 0 else 0.0

                # ADX (14)
                adx_config = IndicatorConfig(
                    indicator_type=IndicatorType.ADX,
                    params={'period': 14}
                )
                adx_result = self.parent.indicator_engine.calculate(df, adx_config)

                if isinstance(adx_result.values, pd.DataFrame) and 'adx' in adx_result.values.columns:
                    adx_value = float(adx_result.values['adx'].iloc[-1])
                elif isinstance(adx_result.values, pd.Series):
                    adx_value = float(adx_result.values.iloc[-1])
                else:
                    adx_value = 0.0

                # Support/Resistance Levels
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

                features[tf] = {
                    "bars": len(df),
                    "last_price": last_close,
                    "period_change_pct": round(change_pct, 2),
                    "rsi": round(rsi_value, 2),
                    "rsi_state": rsi_state,
                    "ema20": round(ema_value, 4),
                    "ema20_distance_pct": round(ema_distance_pct, 2),
                    "trend_state": trend_state,
                    "bb_percent": round(bb_percent, 2),
                    "atr": round(atr_value, 4),
                    "atr_pct": round(atr_pct, 2),
                    "adx": round(adx_value, 2),
                    "support_levels": [round(x, 4) for x in support_levels],
                    "resistance_levels": [round(x, 4) for x in resistance_levels]
                }

            except Exception as e:
                # Safe fallback with basic stats only
                features[tf] = {
                    "bars": len(df),
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
                    "error": str(e)
                }

        return features
