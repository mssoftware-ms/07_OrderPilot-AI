"""Order and Execution Event Emitters.

This module provides utilities to emit order and execution events
for chart markers and UI updates.
"""

import logging
from datetime import datetime
from typing import Any

import backtrader as bt

from src.common.event_bus import (
    Event,
    EventType,
    ExecutionEvent,
    OrderEvent,
    event_bus,
)

logger = logging.getLogger(__name__)


class OrderEventEmitter:
    """Emits order events to the event bus for chart markers and UI updates."""

    def __init__(self, symbol: str, source: str = "trading_system"):
        """Initialize the order event emitter.

        Args:
            symbol: Trading symbol
            source: Event source identifier
        """
        self.symbol = symbol
        self.source = source

    def emit_order_created(
        self,
        order_id: str,
        order_type: str,
        side: str,
        quantity: float,
        price: float | None = None,
        **kwargs
    ) -> None:
        """Emit ORDER_CREATED event.

        Args:
            order_id: Unique order identifier
            order_type: Order type (market, limit, stop, etc.)
            side: Order side (buy, sell, long, short)
            quantity: Order quantity
            price: Order price (None for market orders)
            **kwargs: Additional metadata
        """
        event = OrderEvent(
            type=EventType.ORDER_CREATED,
            timestamp=datetime.now(),
            data={},
            source=self.source,
            symbol=self.symbol,
            order_id=order_id,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price,
            status="created"
        )
        event_bus.emit(event)
        logger.debug(f"Order created: {order_id} - {side} {quantity} @ {price}")

    def emit_order_submitted(self, order_id: str, **kwargs) -> None:
        """Emit ORDER_SUBMITTED event."""
        event = OrderEvent(
            type=EventType.ORDER_SUBMITTED,
            timestamp=datetime.now(),
            data={},
            source=self.source,
            symbol=self.symbol,
            order_id=order_id,
            status="submitted"
        )
        event_bus.emit(event)

    def emit_order_filled(
        self,
        order_id: str,
        filled_quantity: float,
        avg_fill_price: float,
        **kwargs
    ) -> None:
        """Emit ORDER_FILLED event.

        Args:
            order_id: Order identifier
            filled_quantity: Quantity filled
            avg_fill_price: Average fill price
            **kwargs: Additional metadata
        """
        event = OrderEvent(
            type=EventType.ORDER_FILLED,
            timestamp=datetime.now(),
            data={},
            source=self.source,
            symbol=self.symbol,
            order_id=order_id,
            filled_quantity=filled_quantity,
            avg_fill_price=avg_fill_price,
            status="filled"
        )
        event_bus.emit(event)
        logger.info(f"Order filled: {order_id} - {filled_quantity} @ {avg_fill_price}")

    def emit_order_partial_fill(
        self,
        order_id: str,
        filled_quantity: float,
        remaining_quantity: float,
        avg_fill_price: float,
        **kwargs
    ) -> None:
        """Emit ORDER_PARTIAL_FILL event."""
        event = OrderEvent(
            type=EventType.ORDER_PARTIAL_FILL,
            timestamp=datetime.now(),
            data={"remaining_quantity": remaining_quantity},
            source=self.source,
            symbol=self.symbol,
            order_id=order_id,
            filled_quantity=filled_quantity,
            avg_fill_price=avg_fill_price,
            status="partially_filled"
        )
        event_bus.emit(event)

    def emit_order_cancelled(self, order_id: str, reason: str | None = None) -> None:
        """Emit ORDER_CANCELLED event."""
        event = OrderEvent(
            type=EventType.ORDER_CANCELLED,
            timestamp=datetime.now(),
            data={"reason": reason} if reason else {},
            source=self.source,
            symbol=self.symbol,
            order_id=order_id,
            status="cancelled"
        )
        event_bus.emit(event)

    def emit_order_rejected(self, order_id: str, reason: str) -> None:
        """Emit ORDER_REJECTED event."""
        event = OrderEvent(
            type=EventType.ORDER_REJECTED,
            timestamp=datetime.now(),
            data={"reason": reason},
            source=self.source,
            symbol=self.symbol,
            order_id=order_id,
            status="rejected"
        )
        event_bus.emit(event)
        logger.warning(f"Order rejected: {order_id} - {reason}")


class ExecutionEventEmitter:
    """Emits execution events (trade entry/exit) for chart markers."""

    def __init__(self, symbol: str, source: str = "trading_system"):
        """Initialize the execution event emitter.

        Args:
            symbol: Trading symbol
            source: Event source identifier
        """
        self.symbol = symbol
        self.source = source

    def emit_trade_entry(
        self,
        trade_id: str,
        side: str,
        quantity: float,
        price: float,
        **kwargs
    ) -> None:
        """Emit TRADE_ENTRY event for chart marker.

        Args:
            trade_id: Unique trade identifier
            side: Trade side (long, short)
            quantity: Entry quantity
            price: Entry price
            **kwargs: Additional metadata
        """
        event = ExecutionEvent(
            type=EventType.TRADE_ENTRY,
            timestamp=datetime.now(),
            data={},
            source=self.source,
            symbol=self.symbol,
            trade_id=trade_id,
            action="entry",
            side=side,
            quantity=quantity,
            price=price
        )
        event_bus.emit(event)
        logger.info(f"Trade entry: {trade_id} - {side} {quantity} @ {price}")

    def emit_trade_exit(
        self,
        trade_id: str,
        side: str,
        quantity: float,
        price: float,
        pnl: float,
        pnl_pct: float,
        reason: str = "signal",
        **kwargs
    ) -> None:
        """Emit TRADE_EXIT event for chart marker.

        Args:
            trade_id: Trade identifier
            side: Trade side (long, short)
            quantity: Exit quantity
            price: Exit price
            pnl: Profit/loss in currency
            pnl_pct: Profit/loss percentage
            reason: Exit reason (signal, stop_loss, take_profit, manual)
            **kwargs: Additional metadata
        """
        event = ExecutionEvent(
            type=EventType.TRADE_EXIT,
            timestamp=datetime.now(),
            data={},
            source=self.source,
            symbol=self.symbol,
            trade_id=trade_id,
            action="exit",
            side=side,
            quantity=quantity,
            price=price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            reason=reason
        )
        event_bus.emit(event)
        logger.info(f"Trade exit: {trade_id} - {reason} - P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")

    def emit_stop_loss_hit(
        self,
        trade_id: str,
        side: str,
        quantity: float,
        price: float,
        pnl: float,
        pnl_pct: float,
        **kwargs
    ) -> None:
        """Emit STOP_LOSS_HIT event."""
        event = ExecutionEvent(
            type=EventType.STOP_LOSS_HIT,
            timestamp=datetime.now(),
            data={},
            source=self.source,
            symbol=self.symbol,
            trade_id=trade_id,
            action="exit",
            side=side,
            quantity=quantity,
            price=price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            reason="stop_loss"
        )
        event_bus.emit(event)
        logger.warning(f"Stop loss hit: {trade_id} - Loss: ${pnl:.2f} ({pnl_pct:.2f}%)")

    def emit_take_profit_hit(
        self,
        trade_id: str,
        side: str,
        quantity: float,
        price: float,
        pnl: float,
        pnl_pct: float,
        **kwargs
    ) -> None:
        """Emit TAKE_PROFIT_HIT event."""
        event = ExecutionEvent(
            type=EventType.TAKE_PROFIT_HIT,
            timestamp=datetime.now(),
            data={},
            source=self.source,
            symbol=self.symbol,
            trade_id=trade_id,
            action="exit",
            side=side,
            quantity=quantity,
            price=price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            reason="take_profit"
        )
        event_bus.emit(event)
        logger.info(f"Take profit hit: {trade_id} - Profit: ${pnl:.2f} ({pnl_pct:+.2f}%)")

    def emit_position_opened(
        self,
        position_id: str,
        side: str,
        quantity: float,
        price: float,
        **kwargs
    ) -> None:
        """Emit POSITION_OPENED event."""
        event = Event(
            type=EventType.POSITION_OPENED,
            timestamp=datetime.now(),
            data={
                "symbol": self.symbol,
                "position_id": position_id,
                "side": side,
                "quantity": quantity,
                "price": price
            },
            source=self.source
        )
        event_bus.emit(event)

    def emit_position_closed(
        self,
        position_id: str,
        pnl: float,
        pnl_pct: float,
        **kwargs
    ) -> None:
        """Emit POSITION_CLOSED event."""
        event = Event(
            type=EventType.POSITION_CLOSED,
            timestamp=datetime.now(),
            data={
                "symbol": self.symbol,
                "position_id": position_id,
                "pnl": pnl,
                "pnl_pct": pnl_pct
            },
            source=self.source
        )
        event_bus.emit(event)


class BacktraderEventAdapter:
    """Adapter to emit events from Backtrader strategy execution."""

    def __init__(self, symbol: str, source: str = "backtest"):
        """Initialize the Backtrader event adapter.

        Args:
            symbol: Trading symbol
            source: Event source (default: "backtest")
        """
        self.symbol = symbol
        self.order_emitter = OrderEventEmitter(symbol, source)
        self.execution_emitter = ExecutionEventEmitter(symbol, source)
        self._trades = {}  # Track open trades

    def on_order_created(self, order: bt.Order) -> None:
        """Handle order created by Backtrader."""
        self.order_emitter.emit_order_created(
            order_id=str(id(order)),
            order_type=self._get_order_type(order),
            side=self._get_order_side(order),
            quantity=order.size,
            price=order.price if hasattr(order, 'price') else None
        )

    def on_order_submitted(self, order: bt.Order) -> None:
        """Handle order submitted."""
        self.order_emitter.emit_order_submitted(order_id=str(id(order)))

    def on_order_filled(self, order: bt.Order, execution: bt.Trade | None = None) -> None:
        """Handle order filled and emit appropriate events."""
        order_id = str(id(order))

        # Emit order filled event
        self.order_emitter.emit_order_filled(
            order_id=order_id,
            filled_quantity=order.executed.size,
            avg_fill_price=order.executed.price
        )

        # If this opens/closes a position, emit execution event
        if execution:
            trade_id = str(id(execution))

            if execution.justopened:
                # Trade entry
                self._trades[trade_id] = {
                    'side': 'long' if order.isbuy() else 'short',
                    'entry_price': execution.price,
                    'quantity': abs(order.executed.size)
                }
                self.execution_emitter.emit_trade_entry(
                    trade_id=trade_id,
                    side='long' if order.isbuy() else 'short',
                    quantity=abs(order.executed.size),
                    price=execution.price
                )

            elif execution.isclosed:
                # Trade exit
                trade_info = self._trades.get(trade_id, {})
                pnl = execution.pnl
                pnl_pct = execution.pnlcomm / execution.value * 100 if execution.value else 0

                self.execution_emitter.emit_trade_exit(
                    trade_id=trade_id,
                    side=trade_info.get('side', 'unknown'),
                    quantity=trade_info.get('quantity', abs(order.executed.size)),
                    price=execution.price,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    reason="signal"
                )

                # Clean up
                if trade_id in self._trades:
                    del self._trades[trade_id]

    def on_order_cancelled(self, order: bt.Order) -> None:
        """Handle order cancelled."""
        self.order_emitter.emit_order_cancelled(order_id=str(id(order)))

    def on_order_rejected(self, order: bt.Order) -> None:
        """Handle order rejected."""
        self.order_emitter.emit_order_rejected(
            order_id=str(id(order)),
            reason="Rejected by broker/system"
        )

    @staticmethod
    def _get_order_type(order: bt.Order) -> str:
        """Get order type string from Backtrader order."""
        if order.exectype == bt.Order.Market:
            return "market"
        elif order.exectype == bt.Order.Limit:
            return "limit"
        elif order.exectype == bt.Order.Stop:
            return "stop"
        elif order.exectype == bt.Order.StopLimit:
            return "stop_limit"
        return "unknown"

    @staticmethod
    def _get_order_side(order: bt.Order) -> str:
        """Get order side from Backtrader order."""
        return "buy" if order.isbuy() else "sell"
