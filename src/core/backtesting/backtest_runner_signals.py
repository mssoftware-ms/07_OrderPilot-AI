"""Backtest Runner Signals - Signal Generation and Execution.

Refactored from 832 LOC monolith using composition pattern.

Module 4/5 of backtest_runner.py split.

Contains:
- Signal generation (_generate_signal)
- Signal execution (_execute_signal)
- ATR calculation for slippage
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .backtest_runner_state import OpenPosition
    from .config import CandleSnapshot

logger = logging.getLogger(__name__)


class BacktestRunnerSignals:
    """Helper für Signal Generation und Execution."""

    def __init__(self, parent):
        """
        Args:
            parent: BacktestRunner Instanz
        """
        self.parent = parent

    async def _generate_signal(
        self,
        candle: "CandleSnapshot",
        history_1m: list["CandleSnapshot"],
        mtf_data: dict,
    ) -> dict | None:
        """Generiert ein Trading-Signal via Callback oder Strategy.

        Returns:
            Signal-Dict mit: action, side, sl, tp, leverage, reason
            oder None
        """
        if self.parent.signal_callback:
            return self.parent.signal_callback(candle, history_1m, mtf_data)

        # Default: Keine Signale (muss via Callback oder Strategy bereitgestellt werden)
        return None

    async def _execute_signal(self, signal: dict, candle: "CandleSnapshot") -> None:
        """Führt ein Signal aus."""
        from src.core.trading_bot.bot_config import OrderSide, OrderType
        from src.core.backtesting.execution_simulator import SimulatedOrder
        from .backtest_runner_state import OpenPosition

        if not signal:
            return

        action = signal.get("action")
        if action not in ["buy", "sell"]:
            return

        # Keine neuen Trades wenn bereits Position offen
        if self.parent.state.open_positions:
            return

        # Position Size berechnen
        risk_amount = self.parent.state.equity * (self.parent.config.risk_per_trade_pct / 100)

        sl_distance = signal.get("sl_distance", candle.close * 0.01)  # Default 1%
        if sl_distance <= 0:
            sl_distance = candle.close * 0.01

        leverage = min(signal.get("leverage", 1), self.parent.config.execution.max_leverage)
        position_size = (risk_amount * leverage) / sl_distance

        # Order erstellen
        side = OrderSide.BUY if action == "buy" else OrderSide.SELL

        order = SimulatedOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            symbol=self.parent.config.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=position_size,
            leverage=leverage,
            timestamp=candle.timestamp,
        )

        # ATR für Slippage (aus History)
        atr = self._calculate_atr(candle, 14)

        # Order ausführen
        fill = self.parent.execution_sim.execute_order(
            order=order,
            market_price=candle.close,
            atr=atr,
            available_margin=self.parent.state.cash,
        )

        from src.core.backtesting.execution_simulator import FillStatus

        if fill.status != FillStatus.FILLED:
            logger.warning(f"Order rejected: {fill.reason}")
            return

        # SL/TP berechnen
        sl_price = signal.get("stop_loss")
        if sl_price is None:
            if side == OrderSide.BUY:
                sl_price = fill.fill_price - sl_distance
            else:
                sl_price = fill.fill_price + sl_distance

        tp_price = signal.get("take_profit")

        # Position erstellen
        position = OpenPosition(
            id=fill.order_id,
            symbol=self.parent.config.symbol,
            side=side,
            entry_price=fill.fill_price,
            entry_time=candle.datetime,
            size=fill.fill_quantity,
            stop_loss=sl_price,
            take_profit=tp_price,
            leverage=leverage,
            margin_used=fill.margin_used,
            entry_fill=fill,
            entry_reason=signal.get("reason", ""),
            entry_fee=fill.fee,
        )

        self.parent.state.open_positions.append(position)
        self.parent.state.cash -= fill.margin_used
        self.parent.state.trade_count_today += 1

        logger.debug(
            f"Position opened: {side.value} {position.size:.4f} @ {fill.fill_price:.2f} "
            f"(SL: {sl_price:.2f}, TP: {tp_price})"
        )

    def _calculate_atr(self, candle: "CandleSnapshot", period: int = 14) -> float | None:
        """Berechnet ATR aus History."""
        if self.parent.replay_provider.data is None:
            return None

        end_idx = candle.bar_index
        start_idx = max(0, end_idx - period)

        if end_idx - start_idx < period:
            return None

        data = self.parent.replay_provider.data.iloc[start_idx:end_idx]

        high = data["high"].values
        low = data["low"].values
        close = data["close"].values

        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]

        tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))

        return float(np.mean(tr[-period:]))
