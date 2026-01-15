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
        """Calculates indicators and applies regime matrix logic (refactored).

        Args:
            df: OHLCV DataFrame

        Returns:
            MarketRegime enum value
        """
        # Guard: Check if data is sufficient
        if df is None or len(df) < 50:
            return MarketRegime.NEUTRAL

        try:
            # Calculate all indicators
            indicators = self._calculate_indicators(df)

            # Extract latest values with type handling
            values = self._extract_latest_values(df, indicators)
            if values is None:
                return MarketRegime.NEUTRAL

            # Apply regime classification logic
            return self._determine_regime(values)

        except Exception as e:
            logger.error(f"Regime detection failed: {e}")
            return MarketRegime.NEUTRAL

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate all indicators needed for regime detection.

        Args:
            df: OHLCV DataFrame

        Returns:
            Dictionary with indicator results
        """
        return {
            'ema_20': self._get_indicator(df, IndicatorType.EMA, {"period": 20}),
            'ema_50': self._get_indicator(df, IndicatorType.EMA, {"period": 50}),
            'ema_200': self._get_indicator(df, IndicatorType.EMA, {"period": 200}),
            'adx_14': self._get_indicator(df, IndicatorType.ADX, {"period": 14}),
            'atr_14': self._get_indicator(df, IndicatorType.ATR, {"period": 14})
        }

    def _extract_latest_values(self, df: pd.DataFrame, indicators: dict) -> dict | None:
        """Extract latest values from indicators with type handling.

        Args:
            df: OHLCV DataFrame
            indicators: Dictionary of indicator results

        Returns:
            Dictionary with extracted values or None if error
        """
        try:
            close = df['close'].iloc[-1]

            # Extract EMAs (safe scalar extraction)
            e20 = self._safe_extract_value(indicators['ema_20'])
            e50 = self._safe_extract_value(indicators['ema_50'])
            e200 = self._safe_extract_value(indicators['ema_200'])

            # Extract ADX (special handling for DataFrame)
            adx = self._extract_adx_value(indicators['adx_14'])

            # Extract ATR and calculate SMA
            atr = self._safe_extract_value(indicators['atr_14'])
            atr_sma = self._calculate_atr_sma(indicators['atr_14'], atr)

            return {
                'close': close,
                'e20': e20,
                'e50': e50,
                'e200': e200,
                'adx': adx,
                'atr': atr,
                'atr_sma': atr_sma
            }

        except Exception as e:
            logger.warning(f"Error accessing indicator values: {e}")
            return None

    def _safe_extract_value(self, indicator_data):
        """Safely extract scalar value from indicator result.

        Args:
            indicator_data: Series or scalar value

        Returns:
            Last value as scalar
        """
        return indicator_data.iloc[-1] if hasattr(indicator_data, 'iloc') else indicator_data

    def _extract_adx_value(self, adx_14) -> float:
        """Extract ADX value from DataFrame with column discovery.

        Args:
            adx_14: ADX result (DataFrame or Series)

        Returns:
            ADX value as float
        """
        if isinstance(adx_14, pd.DataFrame):
            # Find ADX column (usually 'ADX_14' or similar)
            col = next((c for c in adx_14.columns if 'ADX' in c), adx_14.columns[0])
            return adx_14[col].iloc[-1]
        else:
            return adx_14.iloc[-1]

    def _calculate_atr_sma(self, atr_14, atr_fallback: float) -> float:
        """Calculate 20-period SMA of ATR for explosive check.

        Args:
            atr_14: ATR Series or scalar
            atr_fallback: Fallback value if calculation fails

        Returns:
            ATR SMA value
        """
        if isinstance(atr_14, pd.Series):
            return atr_14.rolling(window=20).mean().iloc[-1]
        return atr_fallback

    def _determine_regime(self, values: dict) -> MarketRegime:
        """Apply regime classification logic matrix.

        Args:
            values: Dictionary with extracted indicator values

        Returns:
            MarketRegime classification
        """
        close = values['close']
        e20 = values['e20']
        e50 = values['e50']
        e200 = values['e200']
        adx = values['adx']
        atr = values['atr']
        atr_sma = values['atr_sma']

        # Explosive Check (Priority 1)
        # If ATR is 50% higher than its 20-period average -> High Volatility
        if atr > (atr_sma * 1.5):
            return MarketRegime.VOLATILITY_EXPLOSIVE

        # Trend Check (Bull)
        # Close > EMA20 > EMA50 > EMA200 AND ADX > 25
        if close > e20 > e50 > e200 and adx > 25:
            return MarketRegime.STRONG_TREND_BULL

        # Trend Check (Bear)
        # Close < EMA20 < EMA50 < EMA200 AND ADX > 25
        if close < e20 < e50 < e200 and adx > 25:
            return MarketRegime.STRONG_TREND_BEAR

        # Range Check
        # ADX < 20 (Weak trend)
        if adx < 20:
            return MarketRegime.CHOP_RANGE

        return MarketRegime.NEUTRAL

    def _get_indicator(self, df: pd.DataFrame, type: IndicatorType, params: dict):
        """Helper to safely get indicator from engine."""
        cfg = IndicatorConfig(indicator_type=type, params=params)
        result = self.engine.calculate(df, cfg)
        return result.values