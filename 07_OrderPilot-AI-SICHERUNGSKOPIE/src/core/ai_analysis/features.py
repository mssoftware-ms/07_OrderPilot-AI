import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from src.core.ai_analysis.types import TechnicalFeatures, MarketStructure, RSIState
from src.core.indicators.engine import IndicatorEngine
from src.core.indicators.types import IndicatorConfig, IndicatorType

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """
    Transforms raw OHLCV data into semantic features for the AI.
    Calculates distances, identifies structure (pivots), and formats data.
    """

    def __init__(self):
        self.engine = IndicatorEngine(cache_size=50)

    def extract_technicals(self, df: pd.DataFrame) -> TechnicalFeatures:
        """
        Extracts single-point technical metrics from the latest candle.
        """
        try:
            # 1. Calculate Indicators
            rsi_res = self._get_indicator(df, IndicatorType.RSI, {"period": 14})
            ema20_res = self._get_indicator(df, IndicatorType.EMA, {"period": 20})
            ema200_res = self._get_indicator(df, IndicatorType.EMA, {"period": 200})
            bb_res = self._get_indicator(df, IndicatorType.BB, {"period": 20, "std": 2})
            atr_res = self._get_indicator(df, IndicatorType.ATR, {"period": 14})
            adx_res = self._get_indicator(df, IndicatorType.ADX, {"period": 14})

            # 2. Extract Values
            close = df['close'].iloc[-1]
            
            rsi = self._get_scalar(rsi_res)
            ema20 = self._get_scalar(ema20_res)
            ema200 = self._get_scalar(ema200_res)
            atr = self._get_scalar(atr_res)
            
            # ADX handling (DataFrame or Series)
            if isinstance(adx_res, pd.DataFrame):
                col = next((c for c in adx_res.columns if 'ADX' in c), adx_res.columns[0])
                adx = adx_res[col].iloc[-1]
            else:
                adx = self._get_scalar(adx_res)

            # BB Handling (usually Lower, Mid, Upper)
            # We need %B and Width
            # %B = (Price - Lower) / (Upper - Lower)
            # Width = (Upper - Lower) / Mid
            bb_pct_b = 0.5
            bb_width = 0.0
            
            if isinstance(bb_res, pd.DataFrame):
                # Assume cols: BBL, BBM, BBU
                lower = bb_res.iloc[-1, 0] # BBL
                mid = bb_res.iloc[-1, 1]   # BBM
                upper = bb_res.iloc[-1, 2] # BBU
                
                if upper != lower:
                    bb_pct_b = (close - lower) / (upper - lower)
                if mid != 0:
                    bb_width = (upper - lower) / mid

            # 3. Derive Features
            # RSI State
            if rsi > 70:
                rsi_state = RSIState.OVERBOUGHT
            elif rsi < 30:
                rsi_state = RSIState.OVERSOLD
            else:
                rsi_state = RSIState.NEUTRAL

            # EMA Distances
            ema20_dist = ((close - ema20) / ema20) * 100 if ema20 != 0 else 0.0
            ema200_dist = ((close - ema200) / ema200) * 100 if ema200 != 0 else 0.0

            return TechnicalFeatures(
                rsi_value=round(float(rsi), 2),
                rsi_state=rsi_state,
                ema_20_dist_pct=round(float(ema20_dist), 2),
                ema_200_dist_pct=round(float(ema200_dist), 2),
                bb_pct_b=round(float(bb_pct_b), 2),
                bb_width=round(float(bb_width), 4),
                atr_14=round(float(atr), 4),
                adx_14=round(float(adx), 2),
                volume_z_score=None # TODO
            )

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return safe default
            return TechnicalFeatures(
                rsi_value=50, rsi_state=RSIState.NEUTRAL,
                ema_20_dist_pct=0, ema_200_dist_pct=0,
                bb_pct_b=0.5, bb_width=0, atr_14=0, adx_14=0
            )

    def extract_structure(self, df: pd.DataFrame, lookback: int = 50) -> MarketStructure:
        """
        Identifies key pivot points (Highs/Lows) in the lookback period.
        Simple logic: Local extrema over window of 5.
        """
        try:
            subset = df.tail(lookback).copy()
            
            # Simple Pivot High/Low (window 5)
            # High > High[t-1] and High > High[t+1] ... simplified:
            # We iterate or use rolling max.
            
            # Use rolling window to find local peaks
            # Peak if value == rolling_max(center=True)
            w = 5
            subset['is_high'] = subset['high'] == subset['high'].rolling(window=w, center=True).max()
            subset['is_low'] = subset['low'] == subset['low'].rolling(window=w, center=True).min()
            
            pivots_high = subset[subset['is_high']]['high'].tolist()
            pivots_low = subset[subset['is_low']]['low'].tolist()
            
            # Filter distinct levels (remove noise/duplicates close to each other)
            # For now, just return last 3
            return MarketStructure(
                recent_highs=pivots_high[-3:],
                recent_lows=pivots_low[-3:],
                current_price=df['close'].iloc[-1]
            )
            
        except Exception as e:
            logger.error(f"Structure extraction failed: {e}")
            return MarketStructure(recent_highs=[], recent_lows=[], current_price=0.0)

    def summarize_candles(self, df: pd.DataFrame, count: int = 5) -> List[Dict[str, Any]]:
        """
        Returns a simplified list of the last N candles for the prompt.
        """
        try:
            subset = df.tail(count)
            summary = []
            for idx, row in subset.iterrows():
                summary.append({
                    "time": str(idx),
                    "open": row['open'],
                    "high": row['high'],
                    "low": row['low'],
                    "close": row['close'],
                    "vol": row['volume']
                })
            return summary
        except Exception:
            return []

    def _get_indicator(self, df: pd.DataFrame, type: IndicatorType, params: dict):
        cfg = IndicatorConfig(indicator_type=type, params=params)
        return self.engine.calculate(df, cfg).values

    def _get_scalar(self, val):
        if isinstance(val, (pd.Series, pd.DataFrame)):
            return val.iloc[-1]
        return val