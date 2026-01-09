"""Execution Engine - Persistence & Status.

Refactored from engine.py monolith.

Module 7/7 of engine.py split.

Contains:
- Database storage
- Status reporting
- Metrics updates
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.core.broker import OrderResponse
from src.database import get_db_manager
from src.database.models import Order as DBOrder

logger = logging.getLogger(__name__)


class EnginePersistence:
    """Helper für ExecutionEngine persistence & status."""

    def __init__(self, parent):
        """
        Args:
            parent: ExecutionEngine Instanz
        """
        self.parent = parent

    async def store_order(self, task, response: OrderResponse) -> None:
        """Store order in database.

        Args:
            task: Execution task
            response: Order response from broker
        """
        try:
            db_manager = get_db_manager()
            with db_manager.session() as session:
                db_order = DBOrder(
                    order_id=response.internal_order_id,
                    broker_order_id=response.broker_order_id,
                    symbol=task.order_request.symbol,
                    side=task.order_request.side,
                    order_type=task.order_request.order_type,
                    quantity=task.order_request.quantity,
                    limit_price=task.order_request.limit_price,
                    stop_price=task.order_request.stop_price,
                    time_in_force=task.order_request.time_in_force,
                    status=response.status,
                    strategy_name=task.order_request.strategy_name,
                    signal_confidence=task.order_request.signal_confidence,
                    ai_analysis=task.ai_analysis.dict() if task.ai_analysis else None,
                    manual_override=not task.manual_approval,
                    created_at=task.created_at,
                    submitted_at=datetime.utcnow()
                )
                session.add(db_order)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to store order in database: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get execution engine status.

        Returns:
            Status information
        """
        return {
            "state": self.parent.state.value,
            "kill_switch_active": self.parent._kill_switch_active,
            "pending_orders": self.parent.pending_queue.qsize(),
            "active_orders": len(self.parent.active_orders),
            "completed_orders": len(self.parent.completed_orders),
            "daily_trades": self.parent.daily_trades,
            "daily_loss": float(self.parent.daily_loss),
            "current_drawdown": self.parent.current_drawdown
        }

    async def update_metrics(self, pnl: Decimal, equity: Decimal) -> None:
        """Update risk metrics.

        Args:
            pnl: Daily P&L
            equity: Current equity
        """
        # Increment daily trades
        self.parent.daily_trades += 1

        # Update daily loss
        if pnl < 0:
            self.parent.daily_loss += abs(pnl)

        # Update peak equity and drawdown
        if equity > self.parent.peak_equity:
            self.parent.peak_equity = equity
            self.parent.current_drawdown = 0.0
        else:
            self.parent.current_drawdown = float(
                (self.parent.peak_equity - equity) / self.parent.peak_equity * 100
            ) if self.parent.peak_equity > 0 else 0.0

        # Check kill switch conditions
        if self.parent.kill_switch_enabled:
            # Check max daily loss
            if self.parent.daily_loss >= self.parent.max_loss_per_day:
                self.parent._kill_switch.activate_kill_switch(
                    f"Max daily loss exceeded: ${self.parent.daily_loss} >= ${self.parent.max_loss_per_day}"
                )

            # Check max drawdown
            if self.parent.current_drawdown >= self.parent.max_drawdown_percent:
                self.parent._kill_switch.activate_kill_switch(
                    f"Max drawdown exceeded: {self.parent.current_drawdown:.2f}% >= {self.parent.max_drawdown_percent}%"
                )
