"""Execution Engine - Event Emission.

Refactored from engine.py monolith.

Module 5/7 of engine.py split.

Contains:
- Order submitted event emission
- Order filled event emission
- Trade entry/exit event emission
- Helper methods for side/type strings
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.common.event_bus import Event, EventType, event_bus
from src.core.broker import OrderResponse

logger = logging.getLogger(__name__)


class EngineEvents:
    """Helper für ExecutionEngine event emission."""

    def __init__(self, parent):
        """
        Args:
            parent: ExecutionEngine Instanz
        """
        self.parent = parent

    def emit_order_submitted(self, task, response: OrderResponse) -> None:
        event_bus.emit(
            Event(
                type=EventType.ORDER_SUBMITTED,
                timestamp=datetime.now(timezone.utc),
                data={
                    "task_id": task.task_id,
                    "broker_order_id": response.broker_order_id,
                    "status": response.status.value,
                },
                source="execution_engine",
            )
        )

    def emit_filled_events(self, task, response: OrderResponse) -> None:
        if not response.filled_qty or response.filled_qty <= 0:
            return

        from src.common.event_bus import OrderEvent

        side_str = self.order_side_str(task)
        order_type_str = self.order_type_str(task)
        avg_price = response.filled_avg_price or response.limit_price or 0.0

        event_bus.emit(
            OrderEvent(
                type=EventType.ORDER_FILLED,
                timestamp=datetime.now(timezone.utc),
                symbol=task.order_request.symbol,
                order_id=response.broker_order_id,
                order_type=order_type_str,
                side=side_str,
                quantity=task.order_request.quantity,
                filled_quantity=response.filled_qty,
                avg_fill_price=avg_price,
                status="filled",
                data={
                    "symbol": task.order_request.symbol,
                    "order_id": response.broker_order_id,
                    "side": side_str,
                    "filled_quantity": response.filled_qty,
                    "avg_fill_price": avg_price,
                    "order_type": order_type_str,
                },
                source="execution_engine",
            )
        )

        logger.info(
            f"✅ ORDER_FILLED event emitted for {task.order_request.symbol} @ {response.filled_avg_price}"
        )

        self.emit_trade_entry_exit(task, response, side_str, avg_price)

    def emit_trade_entry_exit(
        self,
        task,
        response: OrderResponse,
        side_str: str,
        avg_price: float,
    ) -> None:
        from src.common.event_bus import ExecutionEvent

        is_buy = side_str.upper() in ["BUY", "LONG"]
        trade_id = f"trade_{task.order_request.symbol}_{response.broker_order_id}"

        if is_buy:
            event_bus.emit(
                ExecutionEvent(
                    type=EventType.TRADE_ENTRY,
                    timestamp=datetime.now(timezone.utc),
                    symbol=task.order_request.symbol,
                    trade_id=trade_id,
                    action="entry",
                    side="LONG",
                    quantity=response.filled_qty,
                    price=avg_price,
                    data={
                        "symbol": task.order_request.symbol,
                        "side": "LONG",
                        "quantity": response.filled_qty,
                        "price": avg_price,
                    },
                    source="execution_engine",
                )
            )
            logger.info(f"✅ TRADE_ENTRY event emitted for {task.order_request.symbol}")
            return

        event_bus.emit(
            ExecutionEvent(
                type=EventType.TRADE_EXIT,
                timestamp=datetime.now(timezone.utc),
                symbol=task.order_request.symbol,
                trade_id=trade_id,
                action="exit",
                side="SHORT",  # Exiting long = short action
                quantity=response.filled_qty,
                price=avg_price,
                pnl=None,  # Would need position tracking for real P&L
                pnl_pct=None,
                reason="manual_exit",
                data={
                    "symbol": task.order_request.symbol,
                    "side": "SHORT",
                    "quantity": response.filled_qty,
                    "price": avg_price,
                },
                source="execution_engine",
            )
        )

    def order_side_str(self, task) -> str:
        return (
            task.order_request.side.value
            if hasattr(task.order_request.side, "value")
            else str(task.order_request.side)
        )

    def order_type_str(self, task) -> str:
        return (
            task.order_request.order_type.value
            if hasattr(task.order_request.order_type, "value")
            else str(task.order_request.order_type)
        )