"""Backtest Runner Positions - Position Management.

Refactored from 832 LOC monolith using composition pattern.

Module 3/5 of backtest_runner.py split.

Contains:
- Position management (_manage_positions)
- Position closing (_close_position, _close_all_positions)
- Unrealized PnL calculation
- Equity curve updates
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .execution_simulator import OrderSide, OrderType
    from .backtest_runner_state import OpenPosition
    from .replay_provider import CandleSnapshot
    from src.core.models.backtest_models import EquityPoint, Trade

logger = logging.getLogger(__name__)


class BacktestRunnerPositions:
    """Helper für Position Management."""

    def __init__(self, parent):
        """
        Args:
            parent: BacktestRunner Instanz
        """
        self.parent = parent

    async def _manage_positions(
        self,
        candle: "CandleSnapshot",
        history_1m,  # pd.DataFrame mit 1m OHLCV History
        mtf_data: dict,
    ) -> None:
        """Managed offene Positionen (SL/TP Check).

        Args:
            candle: Aktuelle CandleSnapshot
            history_1m: pd.DataFrame mit 1m OHLCV History
            mtf_data: Dict mit Multi-Timeframe DataFrames
        """
        for position in list(self.parent.state.open_positions):
            # Unrealized PnL updaten
            from .execution_simulator import OrderSide

            if position.side == OrderSide.BUY:
                pnl = (candle.close - position.entry_price) * position.size * position.leverage
                pnl_pct = ((candle.close - position.entry_price) / position.entry_price) * 100
            else:
                pnl = (position.entry_price - candle.close) * position.size * position.leverage
                pnl_pct = ((position.entry_price - candle.close) / position.entry_price) * 100

            position.unrealized_pnl = pnl
            position.unrealized_pnl_pct = pnl_pct

            # SL Check
            if position.stop_loss is not None:
                if position.side == OrderSide.BUY and candle.low <= position.stop_loss:
                    await self._close_position(position, position.stop_loss, candle.datetime, "Stop Loss")
                    continue
                elif position.side == OrderSide.SELL and candle.high >= position.stop_loss:
                    await self._close_position(position, position.stop_loss, candle.datetime, "Stop Loss")
                    continue

            # TP Check
            if position.take_profit is not None:
                if position.side == OrderSide.BUY and candle.high >= position.take_profit:
                    await self._close_position(position, position.take_profit, candle.datetime, "Take Profit")
                    continue
                elif position.side == OrderSide.SELL and candle.low <= position.take_profit:
                    await self._close_position(position, position.take_profit, candle.datetime, "Take Profit")
                    continue

    async def _close_position(
        self,
        position: "OpenPosition",
        exit_price: float,
        exit_time: datetime,
        exit_reason: str,
    ) -> None:
        """Schließt eine Position und erstellt Trade-Record."""
        from .execution_simulator import OrderSide, OrderType, SimulatedOrder

        # Exit Order
        exit_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY

        order = SimulatedOrder(
            order_id=f"exit_{uuid.uuid4().hex[:8]}",
            symbol=position.symbol,
            side=exit_side,
            order_type=OrderType.MARKET,
            quantity=position.size,
            leverage=position.leverage,
            timestamp=int(exit_time.timestamp() * 1000),
        )

        fill = self.parent.execution_sim.execute_order(
            order=order,
            market_price=exit_price,
            available_margin=None,  # Exit braucht keine Margin
        )

        # PnL berechnen
        pnl_data = self.parent.execution_sim.calculate_pnl(
            entry_price=position.entry_price,
            exit_price=fill.fill_price,
            quantity=position.size,
            side=position.side,
            leverage=position.leverage,
            include_fees=True,
            entry_fee=position.entry_fee,
            exit_fee=fill.fee,
        )

        net_pnl = pnl_data["net_pnl"]

        # Trade erstellen
        from src.core.models.backtest_models import Trade

        trade = Trade(
            id=position.id,
            symbol=position.symbol,
            side=position.trade_side,
            size=position.size,
            entry_time=position.entry_time,
            entry_price=position.entry_price,
            entry_reason=position.entry_reason,
            exit_time=exit_time,
            exit_price=fill.fill_price,
            exit_reason=exit_reason,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            realized_pnl=net_pnl,
            realized_pnl_pct=pnl_data["return_pct"],
            commission=position.entry_fee + fill.fee,
            slippage=fill.slippage,
        )

        # State updaten
        self.parent.state.closed_trades.append(trade)
        self.parent.state.open_positions.remove(position)
        self.parent.state.cash += position.margin_used + net_pnl
        self.parent.state.equity = self.parent.state.cash + self._calculate_unrealized_pnl(exit_price)
        self.parent.state.daily_pnl += net_pnl

        # Loss Streak tracking
        if net_pnl < 0:
            self.parent.state.loss_streak += 1
        else:
            self.parent.state.loss_streak = 0
            self.parent.state.cooldown_until = None

        logger.debug(
            f"Position closed: {trade.side} @ {fill.fill_price:.2f} "
            f"| PnL: {net_pnl:+.2f} ({pnl_data['return_pct']:+.1f}%) | Reason: {exit_reason}"
        )

    async def _close_all_positions(self, reason: str) -> None:
        """Schließt alle offenen Positionen."""
        if not self.parent.state or not self.parent.state.open_positions:
            return

        # Letzte Candle für Exit-Preis
        if self.parent.replay_provider.data is not None and not self.parent.replay_provider.data.empty:
            last_row = self.parent.replay_provider.data.iloc[-1]
            exit_price = float(last_row["close"])
            # Timestamp sicher zu int konvertieren (kann pd.Timestamp oder int sein)
            ts = last_row["timestamp"]
            ts_ms = int(ts.timestamp() * 1000) if hasattr(ts, 'timestamp') else int(ts)
            exit_time = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        else:
            return

        for position in list(self.parent.state.open_positions):
            await self._close_position(position, exit_price, exit_time, reason)

    def _calculate_unrealized_pnl(self, current_price: float) -> float:
        """Berechnet unrealized PnL aller offenen Positionen."""
        from .execution_simulator import OrderSide

        total = 0.0
        for position in self.parent.state.open_positions:
            if position.side == OrderSide.BUY:
                pnl = (current_price - position.entry_price) * position.size * position.leverage
            else:
                pnl = (position.entry_price - current_price) * position.size * position.leverage
            total += pnl
        return total

    def _update_equity_curve(self, time: datetime, current_price: float) -> None:
        """Fügt Punkt zur Equity Curve hinzu."""
        from src.core.models.backtest_models import EquityPoint

        unrealized = self._calculate_unrealized_pnl(current_price)
        equity = self.parent.state.cash + unrealized

        # Margin in offenen Positionen hinzurechnen
        for pos in self.parent.state.open_positions:
            equity += pos.margin_used

        self.parent.state.equity = equity
        self.parent.state.equity_curve.append(EquityPoint(time=time, equity=equity))
