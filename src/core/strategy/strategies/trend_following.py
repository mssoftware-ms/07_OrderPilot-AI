"""Trend Following Strategy using Moving Averages.

Part of the OrderPilot-AI Strategy Engine.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from src.common.event_bus import Event, EventType, event_bus
from src.core.indicators.engine import IndicatorConfig, IndicatorType

from ..engine import BaseStrategy, Signal, SignalType


class TrendFollowingStrategy(BaseStrategy):
    """Trend following strategy using moving averages."""

    async def evaluate(self, data: pd.DataFrame) -> Signal | None:
        """Evaluate trend following strategy."""
        if len(data) < 200:  # Need enough data for indicators
            return None

        symbol = self.config.symbols[0]  # Single symbol for now

        # Calculate indicators
        configs = [
            IndicatorConfig(
                indicator_type=IndicatorType.SMA,
                params={'period': 50}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.SMA,
                params={'period': 200}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.RSI,
                params={'period': 14}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.MACD,
                params={'fast': 12, 'slow': 26, 'signal': 9}
            )
        ]

        results = self.indicator_engine.calculate_multiple(data, configs)

        # Get indicator values
        sma_50 = results[IndicatorType.SMA].values.iloc[-1]
        sma_200 = results[IndicatorType.SMA].values.iloc[-1]
        rsi = results[IndicatorType.RSI].values.iloc[-1]
        macd_hist = results[IndicatorType.MACD].values['histogram'].iloc[-1]

        current_price = Decimal(str(data['close'].iloc[-1]))
        has_position = self.has_position(symbol)

        # Generate signals based on rules
        signal = None

        # Golden Cross - Bullish signal
        if (sma_50 > sma_200 and
            data['close'].iloc[-1] > sma_50 and
            rsi < 70 and
            macd_hist > 0):

            if not has_position:
                signal = Signal(
                    strategy_name=self.config.name,
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                    price=current_price,
                    stop_loss=current_price * Decimal('0.95'),
                    take_profit=current_price * Decimal('1.10'),
                    reason="Golden cross with positive MACD",
                    metadata={
                        'sma_50': float(sma_50),
                        'sma_200': float(sma_200),
                        'rsi': float(rsi),
                        'macd_hist': float(macd_hist)
                    }
                )

        # Death Cross - Bearish signal
        elif (sma_50 < sma_200 and
              data['close'].iloc[-1] < sma_50 and
              rsi > 30 and
              macd_hist < 0):

            if has_position:
                signal = Signal(
                    strategy_name=self.config.name,
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG,
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                    price=current_price,
                    reason="Death cross with negative MACD",
                    metadata={
                        'sma_50': float(sma_50),
                        'sma_200': float(sma_200),
                        'rsi': float(rsi),
                        'macd_hist': float(macd_hist)
                    }
                )

        # Store signal
        if signal:
            self.state.last_signal = signal
            self.state.last_update = datetime.utcnow()
            self.signal_history.append(signal)

            # Emit event
            event_bus.emit(Event(
                type=EventType.STRATEGY_SIGNAL,
                timestamp=datetime.utcnow(),
                data={
                    'strategy': self.config.name,
                    'signal': signal.signal_type.value,
                    'symbol': signal.symbol,
                    'confidence': signal.confidence
                }
            ))

        return signal
