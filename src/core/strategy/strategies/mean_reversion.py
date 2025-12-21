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

        # Calculate indicators
        configs = [
            IndicatorConfig(
                indicator_type=IndicatorType.BB,
                params={'period': 20, 'std_dev': 2}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.RSI,
                params={'period': 14}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.STD,
                params={'period': 20}
            )
        ]

        results = self.indicator_engine.calculate_multiple(data, configs)

        # Get indicator values
        bb = results[IndicatorType.BB].values
        upper_band = bb['upper'].iloc[-1]
        lower_band = bb['lower'].iloc[-1]
        middle_band = bb['middle'].iloc[-1]
        bb_percent = bb['percent'].iloc[-1]

        rsi = results[IndicatorType.RSI].values.iloc[-1]
        volatility = results[IndicatorType.STD].values.iloc[-1]

        current_price = Decimal(str(data['close'].iloc[-1]))
        has_position = self.has_position(symbol)

        signal = None

        # Oversold condition - Buy signal
        if (current_price <= Decimal(str(lower_band)) and
            rsi < 30 and
            bb_percent < 0.1):

            if not has_position:
                signal = Signal(
                    strategy_name=self.config.name,
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    confidence=0.65,
                    timestamp=datetime.utcnow(),
                    price=current_price,
                    stop_loss=current_price * Decimal('0.97'),
                    take_profit=Decimal(str(middle_band)),
                    reason="Price at lower BB with oversold RSI",
                    metadata={
                        'bb_upper': float(upper_band),
                        'bb_lower': float(lower_band),
                        'bb_percent': float(bb_percent),
                        'rsi': float(rsi),
                        'volatility': float(volatility)
                    }
                )

        # Overbought condition - Sell signal
        elif (current_price >= Decimal(str(upper_band)) and
              rsi > 70 and
              bb_percent > 0.9):

            if has_position and self.get_position(symbol) > 0:
                signal = Signal(
                    strategy_name=self.config.name,
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG,
                    confidence=0.65,
                    timestamp=datetime.utcnow(),
                    price=current_price,
                    reason="Price at upper BB with overbought RSI",
                    metadata={
                        'bb_upper': float(upper_band),
                        'bb_lower': float(lower_band),
                        'bb_percent': float(bb_percent),
                        'rsi': float(rsi)
                    }
                )

        # Mean reversion - Close position
        elif has_position and abs(float(current_price) - middle_band) < volatility * 0.5:
            signal = Signal(
                strategy_name=self.config.name,
                symbol=symbol,
                signal_type=SignalType.CLOSE_LONG,
                confidence=0.5,
                timestamp=datetime.utcnow(),
                price=current_price,
                reason="Price reverted to mean",
                metadata={'bb_middle': float(middle_band)}
            )

        if signal:
            self.state.last_signal = signal
            self.state.last_update = datetime.utcnow()
            self.signal_history.append(signal)

        return signal
