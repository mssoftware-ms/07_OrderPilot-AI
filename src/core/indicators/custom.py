"""Custom Indicators.

Implements PIVOTS, SUPPORT_RESISTANCE, and PATTERN detection.
"""

import logging
from typing import Any

import pandas as pd

from .base import BaseIndicatorCalculator, TALIB_AVAILABLE
from .types import IndicatorResult, IndicatorType

# Import optional libraries
if TALIB_AVAILABLE:
    import talib

logger = logging.getLogger(__name__)


class CustomIndicators(BaseIndicatorCalculator):
    """Calculator for custom indicators."""

    @staticmethod
    def calculate_pivots(
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

        return CustomIndicators.create_result(
            IndicatorType.PIVOTS,
            values,
            params,
            metadata={'method': method}
        )

    @staticmethod
    def calculate_support_resistance(
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

        return CustomIndicators.create_result(
            IndicatorType.SUPPORT_RESISTANCE, values, params
        )

    @staticmethod
    def calculate_patterns(
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

        return CustomIndicators.create_result(
            IndicatorType.PATTERN, values, params
        )
