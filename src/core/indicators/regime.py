"""Regime Detection Indicators.

Composite indicators for market regime classification:
- MOMENTUM_SCORE: Price momentum based on SMA crossovers
- VOLUME_RATIO: Volume relative to moving average
- PRICE_STRENGTH: Combined price strength indicator

These are used for JSON-based regime detection in trading strategies.
"""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from .base import BaseIndicatorCalculator
from .types import IndicatorResult, IndicatorType

logger = logging.getLogger(__name__)


class RegimeIndicators(BaseIndicatorCalculator):
    """Calculators for regime detection indicators."""

    @staticmethod
    def calculate_momentum_score(
        data: pd.DataFrame,
        params: dict,
        use_talib: bool = False
    ) -> IndicatorResult:
        """Calculate momentum score from SMA crossovers and price position.

        Measures price momentum by comparing:
        - Fast SMA vs Slow SMA (trend direction)
        - Current price vs Fast SMA (current momentum)

        Params:
            - sma_fast: Fast SMA period (default: 20)
            - sma_slow: Slow SMA period (default: 50)
            - use_price_distance: Include price vs SMA in score (default: True)

        Returns:
            Momentum score as percentage:
            - Positive = upward momentum
            - Negative = downward momentum
            - Magnitude indicates strength
        """
        sma_fast_period = params.get("sma_fast", 20)
        sma_slow_period = params.get("sma_slow", 50)
        use_price_distance = params.get("use_price_distance", True)

        close = data['close']

        # Calculate SMAs
        sma_fast = close.rolling(window=sma_fast_period).mean()
        sma_slow = close.rolling(window=sma_slow_period).mean()

        # Component 1: SMA crossover distance (trend strength)
        sma_diff_pct = ((sma_fast - sma_slow) / sma_slow) * 100

        if use_price_distance:
            # Component 2: Current price vs Fast SMA (current momentum)
            price_vs_sma_pct = ((close - sma_fast) / sma_fast) * 100

            # Combined score (weighted)
            momentum_score = (sma_diff_pct * 0.6) + (price_vs_sma_pct * 0.4)
        else:
            momentum_score = sma_diff_pct

        return IndicatorResult(
            indicator_type=IndicatorType.MOMENTUM_SCORE,
            values=momentum_score,
            timestamp=datetime.utcnow(),
            params=params,
            metadata={
                "sma_fast": sma_fast.iloc[-1] if len(sma_fast) > 0 else None,
                "sma_slow": sma_slow.iloc[-1] if len(sma_slow) > 0 else None,
                "sma_diff_pct": sma_diff_pct.iloc[-1] if len(sma_diff_pct) > 0 else None
            }
        )

    @staticmethod
    def calculate_volume_ratio(
        data: pd.DataFrame,
        params: dict,
        use_talib: bool = False
    ) -> IndicatorResult:
        """Calculate volume ratio relative to moving average.

        Identifies volume spikes and extremes for confirmation of moves.

        Params:
            - period: Volume SMA period (default: 20)
            - smoothing: Apply EMA smoothing (default: False)

        Returns:
            Volume ratio (current volume / average volume):
            - 1.0 = average volume
            - >1.5 = high volume spike
            - >2.5 = extreme volume
            - <0.5 = low volume
        """
        period = params.get("period", 20)
        smoothing = params.get("smoothing", False)

        if 'volume' not in data.columns:
            # Return NaN series if no volume data
            logger.warning("No volume data available for VOLUME_RATIO calculation")
            return IndicatorResult(
                indicator_type=IndicatorType.VOLUME_RATIO,
                values=pd.Series([float('nan')] * len(data), index=data.index),
                timestamp=datetime.utcnow(),
                params=params,
                metadata={"warning": "No volume data"}
            )

        volume = data['volume']

        # Calculate volume moving average
        if smoothing:
            volume_ma = volume.ewm(span=period, adjust=False).mean()
        else:
            volume_ma = volume.rolling(window=period).mean()

        # Calculate ratio
        volume_ratio = volume / volume_ma

        # Replace inf/nan with 1.0 (neutral)
        volume_ratio = volume_ratio.replace([float('inf'), float('-inf')], 1.0)
        volume_ratio = volume_ratio.fillna(1.0)

        return IndicatorResult(
            indicator_type=IndicatorType.VOLUME_RATIO,
            values=volume_ratio,
            timestamp=datetime.utcnow(),
            params=params,
            metadata={
                "volume_ma": volume_ma.iloc[-1] if len(volume_ma) > 0 else None,
                "current_volume": volume.iloc[-1] if len(volume) > 0 else None,
                "current_ratio": volume_ratio.iloc[-1] if len(volume_ratio) > 0 else None
            }
        )

    @staticmethod
    def calculate_price_strength(
        data: pd.DataFrame,
        params: dict,
        use_talib: bool = False
    ) -> IndicatorResult:
        """Calculate combined price strength indicator.

        Combines multiple factors:
        - Momentum score (SMA-based)
        - Volume confirmation
        - RSI extremes
        - Bollinger Band position

        Params:
            - sma_fast: Fast SMA period (default: 20)
            - sma_slow: Slow SMA period (default: 50)
            - volume_period: Volume MA period (default: 20)
            - rsi_period: RSI period (default: 14)
            - bb_period: Bollinger Band period (default: 20)
            - bb_std: Bollinger Band std dev (default: 2)
            - volume_weight: Volume weight in score (default: 0.3)
            - rsi_weight: RSI weight in score (default: 0.2)
            - bb_weight: BB weight in score (default: 0.15)

        Returns:
            Composite strength score:
            - Positive = bullish strength
            - Negative = bearish strength
            - Magnitude indicates combined conviction
        """
        # Get parameters
        sma_fast = params.get("sma_fast", 20)
        sma_slow = params.get("sma_slow", 50)
        volume_period = params.get("volume_period", 20)
        rsi_period = params.get("rsi_period", 14)
        bb_period = params.get("bb_period", 20)
        bb_std = params.get("bb_std", 2.0)

        volume_weight = params.get("volume_weight", 0.3)
        rsi_weight = params.get("rsi_weight", 0.2)
        bb_weight = params.get("bb_weight", 0.15)
        momentum_weight = 1.0 - volume_weight - rsi_weight - bb_weight

        # Calculate components
        close = data['close']

        # 1. Momentum score (base score)
        momentum_result = RegimeIndicators.calculate_momentum_score(
            data,
            {"sma_fast": sma_fast, "sma_slow": sma_slow},
            use_talib
        )
        momentum_score = momentum_result.values

        # 2. Volume ratio (multiplier effect)
        volume_result = RegimeIndicators.calculate_volume_ratio(
            data,
            {"period": volume_period},
            use_talib
        )
        volume_ratio = volume_result.values
        # Convert to score: 0-1 range where 1.5+ = 1.0, 0.5- = -0.5
        volume_score = ((volume_ratio - 1.0) / 0.5).clip(-1.0, 1.0)

        # 3. RSI component (extreme confirmation)
        # Simple RSI calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Convert RSI to score: -1 to +1 where 50 = 0
        rsi_score = ((rsi - 50) / 50).clip(-1.0, 1.0)

        # 4. Bollinger Band position
        bb_ma = close.rolling(window=bb_period).mean()
        bb_std_val = close.rolling(window=bb_period).std()
        bb_upper = bb_ma + (bb_std_val * bb_std)
        bb_lower = bb_ma - (bb_std_val * bb_std)

        # Position within bands: -1 (at lower) to +1 (at upper)
        bb_range = bb_upper - bb_lower
        bb_position = ((close - bb_ma) / (bb_range / 2)).clip(-1.5, 1.5)

        # 5. Combine all components (weighted)
        price_strength = (
            momentum_score * momentum_weight +
            volume_score * volume_weight * 100 +  # Scale to match momentum
            rsi_score * rsi_weight * 100 +
            bb_position * bb_weight * 100
        )

        return IndicatorResult(
            indicator_type=IndicatorType.PRICE_STRENGTH,
            values=price_strength,
            timestamp=datetime.utcnow(),
            params=params,
            metadata={
                "momentum_score": momentum_score.iloc[-1] if len(momentum_score) > 0 else None,
                "volume_score": volume_score.iloc[-1] if len(volume_score) > 0 else None,
                "rsi_score": rsi_score.iloc[-1] if len(rsi_score) > 0 else None,
                "bb_position": bb_position.iloc[-1] if len(bb_position) > 0 else None,
                "weights": {
                    "momentum": momentum_weight,
                    "volume": volume_weight,
                    "rsi": rsi_weight,
                    "bb": bb_weight
                }
            }
        )
