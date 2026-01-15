"""Breakout Strategy using Support/Resistance and Volume.

Part of the OrderPilot-AI Strategy Engine.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from src.core.indicators.engine import IndicatorConfig, IndicatorType

from ..engine import BaseStrategy, Signal, SignalType


class BreakoutStrategy(BaseStrategy):
    """Breakout strategy using support/resistance and volume."""

    async def evaluate(self, data: pd.DataFrame) -> Signal | None:
        """Evaluate breakout strategy."""
        if len(data) < 100:
            return None

        symbol = self.config.symbols[0]

        # Calculate indicators
        configs = [
            IndicatorConfig(
                indicator_type=IndicatorType.SUPPORT_RESISTANCE,
                params={'window': 20, 'num_levels': 3}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.ATR,
                params={'period': 14}
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.ADX,
                params={'period': 14}
            )
        ]

        results = self.indicator_engine.calculate_multiple(data, configs)

        # Get indicator values
        sr = results[IndicatorType.SUPPORT_RESISTANCE].values
        resistance_levels = sr['resistance']
        support_levels = sr['support']
        atr = results[IndicatorType.ATR].values.iloc[-1]
        adx = results[IndicatorType.ADX].values.iloc[-1]

        current_price = float(data['close'].iloc[-1])
        prev_close = float(data['close'].iloc[-2])
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].iloc[-20:].mean()

        has_position = self.has_position(symbol)
        signal = None

        # Resistance breakout
        if resistance_levels and current_price > resistance_levels[0]:
            price_change = (current_price - prev_close) / prev_close
            volume_ratio = current_volume / avg_volume

            if (price_change > 0.01 and
                volume_ratio > 1.5 and
                adx > 25 and
                not has_position):

                signal = Signal(
                    strategy_name=self.config.name,
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    confidence=0.65,
                    timestamp=datetime.utcnow(),
                    price=Decimal(str(current_price)),
                    stop_loss=Decimal(str(resistance_levels[0] - atr)),
                    take_profit=Decimal(str(current_price + 2 * atr)),
                    reason="Resistance breakout with volume",
                    metadata={
                        'resistance': resistance_levels[0],
                        'volume_ratio': float(volume_ratio),
                        'adx': float(adx),
                        'atr': float(atr)
                    }
                )

        # Support breakdown (for closing longs)
        elif support_levels and current_price < support_levels[0]:
            if has_position:
                signal = Signal(
                    strategy_name=self.config.name,
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG,
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                    price=Decimal(str(current_price)),
                    reason="Support breakdown",
                    metadata={'support': support_levels[0]}
                )

        if signal:
            self.state.last_signal = signal
            self.state.last_update = datetime.utcnow()
            self.signal_history.append(signal)

        return signal
