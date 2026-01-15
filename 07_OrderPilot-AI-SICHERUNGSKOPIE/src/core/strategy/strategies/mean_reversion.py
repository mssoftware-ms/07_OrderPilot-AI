"""Mean Reversion Strategy using Bollinger Bands.

Part of the OrderPilot-AI Strategy Engine.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from src.core.indicators.engine import IndicatorConfig, IndicatorType

from ..engine import BaseStrategy, Signal, SignalType


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy using Bollinger Bands."""

    async def evaluate(self, data: pd.DataFrame) -> Signal | None:
        """Evaluate mean reversion strategy."""
        if len(data) < 50:
            return None

        symbol = self.config.symbols[0]
        indicators = self._calculate_indicators(data)
        current_price = Decimal(str(data['close'].iloc[-1]))
        has_position = self.has_position(symbol)

        signal = None

        # Oversold condition - Buy signal
        if self._is_oversold(current_price, indicators):
            signal = self._build_oversold_signal(
                symbol,
                current_price,
                indicators,
                has_position,
            )

        # Overbought condition - Sell signal
        elif self._is_overbought(current_price, indicators):
            signal = self._build_overbought_signal(
                symbol,
                current_price,
                indicators,
                has_position,
            )

        # Mean reversion - Close position
        elif has_position and self._is_reverted_to_mean(current_price, indicators):
            signal = self._build_mean_reversion_signal(symbol, current_price, indicators)

        if signal:
            self.state.last_signal = signal
            self.state.last_update = datetime.utcnow()
            self.signal_history.append(signal)

        return signal

    def _calculate_indicators(self, data: pd.DataFrame) -> dict[str, float]:
        configs = [
            IndicatorConfig(
                indicator_type=IndicatorType.BB,
                params={'period': 20, 'std_dev': 2},
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.RSI,
                params={'period': 14},
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.STD,
                params={'period': 20},
            ),
        ]
        results = self.indicator_engine.calculate_multiple(data, configs)
        bb = results[IndicatorType.BB].values
        return {
            "upper_band": float(bb['upper'].iloc[-1]),
            "lower_band": float(bb['lower'].iloc[-1]),
            "middle_band": float(bb['middle'].iloc[-1]),
            "bb_percent": float(bb['percent'].iloc[-1]),
            "rsi": float(results[IndicatorType.RSI].values.iloc[-1]),
            "volatility": float(results[IndicatorType.STD].values.iloc[-1]),
        }

    def _is_oversold(self, current_price: Decimal, indicators: dict[str, float]) -> bool:
        return (
            current_price <= Decimal(str(indicators["lower_band"]))
            and indicators["rsi"] < 30
            and indicators["bb_percent"] < 0.1
        )

    def _is_overbought(self, current_price: Decimal, indicators: dict[str, float]) -> bool:
        return (
            current_price >= Decimal(str(indicators["upper_band"]))
            and indicators["rsi"] > 70
            and indicators["bb_percent"] > 0.9
        )

    def _is_reverted_to_mean(self, current_price: Decimal, indicators: dict[str, float]) -> bool:
        return abs(float(current_price) - indicators["middle_band"]) < indicators["volatility"] * 0.5

    def _build_oversold_signal(
        self,
        symbol: str,
        current_price: Decimal,
        indicators: dict[str, float],
        has_position: bool,
    ) -> Signal | None:
        if has_position:
            return None
        return Signal(
            strategy_name=self.config.name,
            symbol=symbol,
            signal_type=SignalType.BUY,
            confidence=0.65,
            timestamp=datetime.utcnow(),
            price=current_price,
            stop_loss=current_price * Decimal('0.97'),
            take_profit=Decimal(str(indicators["middle_band"])),
            reason="Price at lower BB with oversold RSI",
            metadata={
                'bb_upper': indicators["upper_band"],
                'bb_lower': indicators["lower_band"],
                'bb_percent': indicators["bb_percent"],
                'rsi': indicators["rsi"],
                'volatility': indicators["volatility"],
            },
        )

    def _build_overbought_signal(
        self,
        symbol: str,
        current_price: Decimal,
        indicators: dict[str, float],
        has_position: bool,
    ) -> Signal | None:
        if not (has_position and self.get_position(symbol) > 0):
            return None
        return Signal(
            strategy_name=self.config.name,
            symbol=symbol,
            signal_type=SignalType.CLOSE_LONG,
            confidence=0.65,
            timestamp=datetime.utcnow(),
            price=current_price,
            reason="Price at upper BB with overbought RSI",
            metadata={
                'bb_upper': indicators["upper_band"],
                'bb_lower': indicators["lower_band"],
                'bb_percent': indicators["bb_percent"],
                'rsi': indicators["rsi"],
            },
        )

    def _build_mean_reversion_signal(
        self,
        symbol: str,
        current_price: Decimal,
        indicators: dict[str, float],
    ) -> Signal:
        return Signal(
            strategy_name=self.config.name,
            symbol=symbol,
            signal_type=SignalType.CLOSE_LONG,
            confidence=0.5,
            timestamp=datetime.utcnow(),
            price=current_price,
            reason="Price reverted to mean",
            metadata={'bb_middle': indicators["middle_band"]},
        )
