"""Momentum Strategy using Rate of Change and Volume.

Part of the OrderPilot-AI Strategy Engine.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from src.core.indicators.engine import IndicatorConfig, IndicatorType

from ..engine import BaseStrategy, Signal, SignalType


class MomentumStrategy(BaseStrategy):
    """Momentum strategy using rate of change and volume."""

    async def evaluate(self, data: pd.DataFrame) -> Signal | None:
        """Evaluate momentum strategy."""
        if len(data) < 50:
            return None

        symbol = self.config.symbols[0]

        # Calculate indicators
        configs = [
            IndicatorConfig(
                indicator_type=IndicatorType.ROC,
                params={'period': 10}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.MOM,
                params={'period': 10}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.OBV,
                params={}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.RSI,
                params={'period': 14}
            )
        ]

        results = self.indicator_engine.calculate_multiple(data, configs)

        # Get indicator values
        roc = results[IndicatorType.ROC].values.iloc[-1]
        momentum = results[IndicatorType.MOM].values.iloc[-1]
        obv = results[IndicatorType.OBV].values
        obv_change = (obv.iloc[-1] - obv.iloc[-5]) / obv.iloc[-5] * 100
        rsi = results[IndicatorType.RSI].values.iloc[-1]

        current_price = Decimal(str(data['close'].iloc[-1]))
        has_position = self.has_position(symbol)

        signal = None

        # Strong momentum up
        if (roc > 5 and
            momentum > 0 and
            obv_change > 5 and
            rsi > 50 and rsi < 80):

            if not has_position:
                signal = Signal(
                    strategy_name=self.config.name,
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    confidence=0.6,
                    timestamp=datetime.utcnow(),
                    price=current_price,
                    stop_loss=current_price * Decimal('0.96'),
                    take_profit=current_price * Decimal('1.08'),
                    reason="Strong positive momentum with volume",
                    metadata={
                        'roc': float(roc),
                        'momentum': float(momentum),
                        'obv_change': float(obv_change),
                        'rsi': float(rsi)
                    }
                )

        # Momentum exhaustion
        elif has_position and (roc < -3 or rsi > 85 or obv_change < -5):
            signal = Signal(
                strategy_name=self.config.name,
                symbol=symbol,
                signal_type=SignalType.CLOSE_LONG,
                confidence=0.6,
                timestamp=datetime.utcnow(),
                price=current_price,
                reason="Momentum exhaustion",
                metadata={
                    'roc': float(roc),
                    'obv_change': float(obv_change),
                    'rsi': float(rsi)
                }
            )

        if signal:
            self.state.last_signal = signal
            self.state.last_update = datetime.utcnow()
            self.signal_history.append(signal)

        return signal
