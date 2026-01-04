import pandas as pd
import logging
from src.core.ai_analysis.types import MarketRegime
from src.core.indicators.engine import IndicatorEngine
from src.core.indicators.types import IndicatorConfig, IndicatorType

logger = logging.getLogger(__name__)

class RegimeDetector:
    """
    Determines the market regime (Trend, Range, Volatility) using deterministic logic.
    Does NOT use AI. Pure math/indicators.
    Uses IndicatorEngine to ensure consistent calculation.
    """

    def __init__(self):
        self.engine = IndicatorEngine(cache_size=20)

    def detect_regime(self, df: pd.DataFrame) -> MarketRegime:
        """
        Calculates indicators and applies the regime matrix logic.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            MarketRegime enum value
        """
        if df is None or len(df) < 50:
            return MarketRegime.NEUTRAL

        try:
            # 1. Calculate Indicators
            ema_20 = self._get_indicator(df, IndicatorType.EMA, {"period": 20})
            ema_50 = self._get_indicator(df, IndicatorType.EMA, {"period": 50})
            ema_200 = self._get_indicator(df, IndicatorType.EMA, {"period": 200})
            adx_14 = self._get_indicator(df, IndicatorType.ADX, {"period": 14})
            atr_14 = self._get_indicator(df, IndicatorType.ATR, {"period": 14})
            
            # Get latest values
            last_idx = df.index[-1]
            try:
                close = df['close'].iloc[-1]
                e20 = ema_20.iloc[-1] if hasattr(ema_20, 'iloc') else ema_20
                e50 = ema_50.iloc[-1] if hasattr(ema_50, 'iloc') else ema_50
                e200 = ema_200.iloc[-1] if hasattr(ema_200, 'iloc') else ema_200
                
                # ADX usually returns a DataFrame with ADX, DMP, DMN. We need ADX column.
                if isinstance(adx_14, pd.DataFrame):
                    # Try to find the column (usually 'ADX_14' or similar, or just first col)
                    # pandas_ta usually names it ADX_14. TA-Lib returns single series if wrapper handles it?
                    # Let's inspect column names or assume first column if one, else 'ADX_14'
                    col = next((c for c in adx_14.columns if 'ADX' in c), adx_14.columns[0])
                    adx = adx_14[col].iloc[-1]
                else:
                    adx = adx_14.iloc[-1]

                atr = atr_14.iloc[-1] if hasattr(atr_14, 'iloc') else atr_14
                
                # ATR SMA for Explosive Check (SMA 20 of ATR)
                if isinstance(atr_14, pd.Series):
                    atr_sma = atr_14.rolling(window=20).mean().iloc[-1]
                else:
                    atr_sma = atr # Fallback
            except Exception as e:
                logger.warning(f"Error accessing indicator values: {e}")
                return MarketRegime.NEUTRAL

            # 2. Logic Matrix
            
            # Explosive Check (Priority 1)
            # If ATR is 50% higher than its 20-period average -> High Volatility
            if atr > (atr_sma * 1.5):
                return MarketRegime.VOLATILITY_EXPLOSIVE

            # Trend Check (Bull)
            # Close > EMA20 > EMA50 > EMA200 AND ADX > 25
            is_bull_stacked = close > e20 > e50 > e200
            if is_bull_stacked and adx > 25:
                return MarketRegime.STRONG_TREND_BULL
            
            # Trend Check (Bear)
            # Close < EMA20 < EMA50 < EMA200 AND ADX > 25
            is_bear_stacked = close < e20 < e50 < e200
            if is_bear_stacked and adx > 25:
                return MarketRegime.STRONG_TREND_BEAR
            
            # Range Check
            # ADX < 20 (Weak trend)
            if adx < 20:
                return MarketRegime.CHOP_RANGE
                
            return MarketRegime.NEUTRAL

        except Exception as e:
            logger.error(f"Regime detection failed: {e}")
            return MarketRegime.NEUTRAL

    def _get_indicator(self, df: pd.DataFrame, type: IndicatorType, params: dict):
        """Helper to safely get indicator from engine."""
        cfg = IndicatorConfig(indicator_type=type, params=params)
        result = self.engine.calculate(df, cfg)
        return result.values