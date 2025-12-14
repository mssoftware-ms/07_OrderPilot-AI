"""Scalping Strategy for High-Frequency Trading.

Part of the OrderPilot-AI Strategy Engine.
"""

import json
from datetime import datetime
from decimal import Decimal

import pandas as pd

from src.core.indicators.engine import IndicatorConfig, IndicatorType

from ..engine import BaseStrategy, Signal, SignalType


class ScalpingStrategy(BaseStrategy):
    """High-frequency scalping strategy."""

    async def evaluate(self, data: pd.DataFrame) -> Signal | None:
        """Evaluate scalping strategy."""
        if len(data) < 20:
            return None

        symbol = self.config.symbols[0]

        # Calculate fast indicators
        configs = [
            IndicatorConfig(
                indicator_type=IndicatorType.EMA,
                params={'period': 5}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.EMA,
                params={'period': 9}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.VWAP,
                params={}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.STOCH,
                params={'k_period': 5, 'd_period': 3}
            )
        ]

        results = self.indicator_engine.calculate_multiple(data, configs)

        # Get indicator values
        ema_5 = results[IndicatorType.EMA].values.iloc[-1]
        ema_9 = results[IndicatorType.EMA].values.iloc[-1]
        vwap = results[IndicatorType.VWAP].values.iloc[-1]
        stoch = results[IndicatorType.STOCH].values
        stoch_k = stoch['k'].iloc[-1]

        current_price = Decimal(str(data['close'].iloc[-1]))
        spread = (data['high'].iloc[-1] - data['low'].iloc[-1]) / data['close'].iloc[-1]

        has_position = self.has_position(symbol)
        signal = None

        # Quick buy signal
        if (ema_5 > ema_9 and
            current_price > Decimal(str(vwap)) and
            stoch_k < 80 and
            spread < 0.005 and  # Tight spread for scalping
            not has_position):

            signal = Signal(
                strategy_name=self.config.name,
                symbol=symbol,
                signal_type=SignalType.BUY,
                confidence=0.5,
                timestamp=datetime.utcnow(),
                price=current_price,
                stop_loss=current_price * Decimal('0.995'),  # Tight stop
                take_profit=current_price * Decimal('1.005'),  # Quick profit
                reason="Scalp buy signal",
                metadata={
                    'ema_5': float(ema_5),
                    'vwap': float(vwap),
                    'stoch_k': float(stoch_k),
                    'spread': float(spread)
                }
            )

        # Quick exit
        elif has_position:
            position_time = (datetime.utcnow() -
                           self.state.last_signal.timestamp).total_seconds()

            if (position_time > 60 or  # Exit after 1 minute
                ema_5 < ema_9 or
                current_price < Decimal(str(vwap))):

                signal = Signal(
                    strategy_name=self.config.name,
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG,
                    confidence=0.5,
                    timestamp=datetime.utcnow(),
                    price=current_price,
                    reason="Scalp exit",
                    metadata={'position_time': position_time}
                )

        if signal:
            self.state.last_signal = signal
            self.state.last_update = datetime.utcnow()
            self.signal_history.append(signal)

        return signal
