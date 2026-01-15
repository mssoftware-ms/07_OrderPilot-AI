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

        symbol = self.config.symbols[0]
        indicators = self._calculate_indicators(data)
        current_price = Decimal(str(data['close'].iloc[-1]))
        has_position = self.has_position(symbol)

        # Generate signals based on rules
        signal = None

        # Golden Cross - Bullish signal
        if self._is_golden_cross(indicators, data):
            signal = self._build_golden_cross_signal(symbol, current_price, indicators, has_position)

        # Death Cross - Bearish signal
        elif self._is_death_cross(indicators, data):
            signal = self._build_death_cross_signal(symbol, current_price, indicators, has_position)

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

    def _calculate_indicators(self, data: pd.DataFrame) -> dict[str, float]:
        configs = [
            IndicatorConfig(
                indicator_type=IndicatorType.SMA,
                params={'period': 50},
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.SMA,
                params={'period': 200},
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.RSI,
                params={'period': 14},
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.MACD,
                params={'fast': 12, 'slow': 26, 'signal': 9},
            ),
        ]
        results = self.indicator_engine.calculate_multiple(data, configs)
        return {
            "sma_50": float(results[IndicatorType.SMA].values.iloc[-1]),
            "sma_200": float(results[IndicatorType.SMA].values.iloc[-1]),
            "rsi": float(results[IndicatorType.RSI].values.iloc[-1]),
            "macd_hist": float(results[IndicatorType.MACD].values['histogram'].iloc[-1]),
        }

    def _is_golden_cross(self, indicators: dict[str, float], data: pd.DataFrame) -> bool:
        return (
            indicators["sma_50"] > indicators["sma_200"]
            and data['close'].iloc[-1] > indicators["sma_50"]
            and indicators["rsi"] < 70
            and indicators["macd_hist"] > 0
        )

    def _is_death_cross(self, indicators: dict[str, float], data: pd.DataFrame) -> bool:
        return (
            indicators["sma_50"] < indicators["sma_200"]
            and data['close'].iloc[-1] < indicators["sma_50"]
            and indicators["rsi"] > 30
            and indicators["macd_hist"] < 0
        )

    def _build_golden_cross_signal(
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
            confidence=0.7,
            timestamp=datetime.utcnow(),
            price=current_price,
            stop_loss=current_price * Decimal('0.95'),
            take_profit=current_price * Decimal('1.10'),
            reason="Golden cross with positive MACD",
            metadata={
                'sma_50': indicators["sma_50"],
                'sma_200': indicators["sma_200"],
                'rsi': indicators["rsi"],
                'macd_hist': indicators["macd_hist"],
            },
        )

    def _build_death_cross_signal(
        self,
        symbol: str,
        current_price: Decimal,
        indicators: dict[str, float],
        has_position: bool,
    ) -> Signal | None:
        if not has_position:
            return None
        return Signal(
            strategy_name=self.config.name,
            symbol=symbol,
            signal_type=SignalType.CLOSE_LONG,
            confidence=0.7,
            timestamp=datetime.utcnow(),
            price=current_price,
            reason="Death cross with negative MACD",
            metadata={
                'sma_50': indicators["sma_50"],
                'sma_200': indicators["sma_200"],
                'rsi': indicators["rsi"],
                'macd_hist': indicators["macd_hist"],
            },
        )
