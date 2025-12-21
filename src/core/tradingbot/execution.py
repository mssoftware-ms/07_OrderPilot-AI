"""Execution Layer for Tradingbot.

Handles order execution and paper trading simulation.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- execution_types.py: Enums and dataclasses
- position_sizer.py: PositionSizer class
- risk_manager.py: RiskManager class
- execution.py: PaperExecutor, ExecutionGuardrails, OrderExecutor (this file)
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Callable
from uuid import uuid4

from .config import TradingEnvironment
from .execution_types import (
    OrderResult,
    OrderStatus,
    OrderType,
    PositionSizeResult,
    RiskLimits,
    RiskState,
)
from .models import OrderIntent, Signal, TradeSide
from .position_sizer import PositionSizer
from .risk_manager import RiskManager

# Re-export types for backward compatibility
__all__ = [
    "OrderStatus",
    "OrderType",
    "OrderResult",
    "PositionSizeResult",
    "RiskLimits",
    "RiskState",
    "PositionSizer",
    "RiskManager",
    "PaperExecutor",
    "ExecutionGuardrails",
    "OrderExecutor",
]

logger = logging.getLogger(__name__)


class PaperExecutor:
    """Paper trading executor with slippage simulation.

    Simulates order execution for backtesting and paper trading.
    """

    def __init__(
        self,
        slippage_pct: float = 0.05,
        fill_probability: float = 1.0,
        partial_fill_probability: float = 0.0,
        latency_ms: int = 50,
        fee_pct: float = 0.1
    ):
        """Initialize paper executor.

        Args:
            slippage_pct: Simulated slippage percentage
            fill_probability: Probability of fill (1.0 = always)
            partial_fill_probability: Probability of partial fill
            latency_ms: Simulated latency in milliseconds
            fee_pct: Fee percentage (per side)
        """
        self.slippage_pct = slippage_pct
        self.fill_probability = fill_probability
        self.partial_fill_probability = partial_fill_probability
        self.latency_ms = latency_ms
        self.fee_pct = fee_pct

        # Tracking
        self._orders: dict[str, OrderIntent] = {}
        self._results: dict[str, OrderResult] = {}

        logger.info(
            f"PaperExecutor initialized: slippage={slippage_pct}%, "
            f"fees={fee_pct}%"
        )

    def execute(
        self,
        order: OrderIntent,
        current_price: float
    ) -> OrderResult:
        """Execute an order (paper).

        Args:
            order: Order intent
            current_price: Current market price

        Returns:
            OrderResult
        """
        order_id = str(uuid4())[:8]
        self._orders[order_id] = order

        # Simulate rejection
        if random.random() > self.fill_probability:
            result = OrderResult(
                order_id=order_id,
                status=OrderStatus.REJECTED,
                error_message="Simulated rejection"
            )
            self._results[order_id] = result
            return result

        # Calculate fill price with slippage
        slippage_direction = 1 if order.side == TradeSide.LONG else -1
        slippage = current_price * (self.slippage_pct / 100) * slippage_direction
        fill_price = current_price + slippage

        # Calculate quantity (check for partial fill)
        if random.random() < self.partial_fill_probability:
            filled_qty = order.quantity * random.uniform(0.5, 0.9)
            status = OrderStatus.PARTIAL
        else:
            filled_qty = order.quantity
            status = OrderStatus.FILLED

        # Calculate fees
        fees = filled_qty * fill_price * (self.fee_pct / 100)

        result = OrderResult(
            order_id=order_id,
            status=status,
            filled_qty=filled_qty,
            filled_price=fill_price,
            fees=fees,
            slippage=abs(slippage)
        )
        self._results[order_id] = result

        logger.info(
            f"Paper order executed: {order_id} - {order.side.value} "
            f"{filled_qty:.4f} @ {fill_price:.4f} (slip={slippage:.4f})"
        )

        return result

    def cancel(self, order_id: str) -> OrderResult:
        """Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            OrderResult with cancelled status
        """
        if order_id not in self._orders:
            return OrderResult(
                order_id=order_id,
                status=OrderStatus.REJECTED,
                error_message="Order not found"
            )

        result = OrderResult(
            order_id=order_id,
            status=OrderStatus.CANCELLED
        )
        self._results[order_id] = result
        return result

    def get_order(self, order_id: str) -> OrderResult | None:
        """Get order result by ID.

        Args:
            order_id: Order ID

        Returns:
            OrderResult or None
        """
        return self._results.get(order_id)


class ExecutionGuardrails:
    """Safety guardrails for order execution.

    Validates orders before execution and prevents
    dangerous operations.
    """

    def __init__(
        self,
        max_order_value: float = 10000.0,
        max_order_quantity: float = 1000.0,
        min_order_value: float = 10.0,
        rate_limit_per_minute: int = 10,
        require_stop_loss: bool = True,
        prevent_duplicates: bool = True
    ):
        """Initialize guardrails.

        Args:
            max_order_value: Maximum order value
            max_order_quantity: Maximum quantity
            min_order_value: Minimum order value
            rate_limit_per_minute: Orders per minute limit
            require_stop_loss: Require stop-loss for entries
            prevent_duplicates: Prevent duplicate orders
        """
        self.max_order_value = max_order_value
        self.max_order_quantity = max_order_quantity
        self.min_order_value = min_order_value
        self.rate_limit_per_minute = rate_limit_per_minute
        self.require_stop_loss = require_stop_loss
        self.prevent_duplicates = prevent_duplicates

        # Tracking
        self._recent_orders: list[tuple[datetime, str]] = []
        self._pending_signals: set[str] = set()

        logger.info(
            f"ExecutionGuardrails initialized: max_value=${max_order_value}, "
            f"rate_limit={rate_limit_per_minute}/min"
        )

    def validate(
        self,
        order: OrderIntent,
        current_price: float
    ) -> tuple[bool, list[str]]:
        """Validate an order before execution.

        Args:
            order: Order to validate
            current_price: Current market price

        Returns:
            (is_valid, list of rejection reasons)
        """
        rejections = []

        # Calculate order value
        order_value = order.quantity * current_price

        # Max order value
        if order_value > self.max_order_value:
            rejections.append(f"ORDER_VALUE_EXCEEDED: ${order_value:.2f} > ${self.max_order_value}")

        # Min order value
        if order_value < self.min_order_value:
            rejections.append(f"ORDER_VALUE_TOO_SMALL: ${order_value:.2f} < ${self.min_order_value}")

        # Max quantity
        if order.quantity > self.max_order_quantity:
            rejections.append(f"QUANTITY_EXCEEDED: {order.quantity} > {self.max_order_quantity}")

        # Stop loss required for entry
        if self.require_stop_loss and order.action == "entry":
            if not order.stop_price or order.stop_price <= 0:
                rejections.append("STOP_LOSS_REQUIRED")

        # Rate limit
        if not self._check_rate_limit():
            rejections.append(f"RATE_LIMIT_EXCEEDED: >{self.rate_limit_per_minute}/min")

        # Duplicate prevention
        if self.prevent_duplicates and order.signal_id:
            if order.signal_id in self._pending_signals:
                rejections.append(f"DUPLICATE_SIGNAL: {order.signal_id}")

        return len(rejections) == 0, rejections

    def record_order(self, order: OrderIntent) -> None:
        """Record an executed order for tracking.

        Args:
            order: Executed order
        """
        now = datetime.utcnow()
        self._recent_orders.append((now, order.symbol))

        if order.signal_id:
            self._pending_signals.add(order.signal_id)

        # Clean old records
        cutoff = now - timedelta(minutes=1)
        self._recent_orders = [
            (t, s) for t, s in self._recent_orders
            if t > cutoff
        ]

    def clear_signal(self, signal_id: str) -> None:
        """Clear a signal from pending.

        Args:
            signal_id: Signal ID to clear
        """
        self._pending_signals.discard(signal_id)

    def _check_rate_limit(self) -> bool:
        """Check if within rate limit."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        recent_count = sum(1 for t, _ in self._recent_orders if t > cutoff)
        return recent_count < self.rate_limit_per_minute


class OrderExecutor:
    """Unified order executor supporting paper and live modes.

    Combines position sizing, risk management, guardrails,
    and execution in a single interface.
    """

    def __init__(
        self,
        environment: TradingEnvironment = TradingEnvironment.PAPER,
        account_value: float = 10000.0,
        risk_limits: RiskLimits | None = None,
        guardrails: ExecutionGuardrails | None = None,
        on_fill: Callable[[OrderResult], None] | None = None
    ):
        """Initialize order executor.

        Args:
            environment: Trading environment (paper/live)
            account_value: Account value
            risk_limits: Risk limits
            guardrails: Execution guardrails
            on_fill: Callback for fills
        """
        self.environment = environment
        self.account_value = account_value

        self.position_sizer = PositionSizer(account_value, risk_limits)
        self.risk_manager = RiskManager(risk_limits, account_value)
        self.guardrails = guardrails or ExecutionGuardrails()
        self.paper_executor = PaperExecutor()

        self._on_fill = on_fill

        logger.info(
            f"OrderExecutor initialized: env={environment.value}, "
            f"account=${account_value:.2f}"
        )

    def execute_entry(
        self,
        signal: Signal,
        current_price: float,
        atr: float | None = None
    ) -> OrderResult:
        """Execute an entry order.

        Args:
            signal: Entry signal
            current_price: Current price
            atr: ATR for sizing

        Returns:
            OrderResult
        """
        # Check risk limits
        can_trade, blocks = self.risk_manager.can_trade()
        if not can_trade:
            return OrderResult(
                order_id="blocked",
                status=OrderStatus.REJECTED,
                error_message=f"Risk blocked: {', '.join(blocks)}"
            )

        # Calculate position size
        if atr:
            size_result = self.position_sizer.calculate_size_atr(
                signal, current_price, atr
            )
        else:
            size_result = self.position_sizer.calculate_size(
                signal, current_price
            )

        if size_result.quantity <= 0:
            return OrderResult(
                order_id="zero_size",
                status=OrderStatus.REJECTED,
                error_message="Position size calculation resulted in zero"
            )

        # Create order intent
        order = OrderIntent(
            symbol=signal.symbol,
            side=signal.side,
            action="entry",
            quantity=size_result.quantity,
            order_type="market",
            stop_price=signal.stop_loss_price,
            signal_id=signal.id,
            reason=f"Entry signal {signal.id}",
            risk_amount=size_result.risk_amount,
            position_value=size_result.position_value
        )

        # Validate with guardrails
        is_valid, rejections = self.guardrails.validate(order, current_price)
        if not is_valid:
            return OrderResult(
                order_id="guardrail",
                status=OrderStatus.REJECTED,
                error_message=f"Guardrail rejected: {', '.join(rejections)}"
            )

        # Execute
        if self.environment == TradingEnvironment.PAPER:
            result = self.paper_executor.execute(order, current_price)
        else:
            # Live execution would go here
            logger.warning("Live execution not implemented - using paper")
            result = self.paper_executor.execute(order, current_price)

        # Record if filled
        if result.is_filled:
            self.guardrails.record_order(order)
            self.risk_manager.record_trade_start()

            if self._on_fill:
                self._on_fill(result)

        return result

    def execute_exit(
        self,
        symbol: str,
        side: TradeSide,
        quantity: float,
        current_price: float,
        reason: str
    ) -> OrderResult:
        """Execute an exit order.

        Args:
            symbol: Symbol
            side: Original position side
            quantity: Quantity to exit
            current_price: Current price
            reason: Exit reason

        Returns:
            OrderResult
        """
        # Exit side is opposite
        exit_side = TradeSide.SHORT if side == TradeSide.LONG else TradeSide.LONG

        order = OrderIntent(
            symbol=symbol,
            side=exit_side,
            action="exit",
            quantity=quantity,
            order_type="market",
            reason=reason
        )

        # Execute
        if self.environment == TradingEnvironment.PAPER:
            result = self.paper_executor.execute(order, current_price)
        else:
            logger.warning("Live execution not implemented - using paper")
            result = self.paper_executor.execute(order, current_price)

        # Calculate P&L if filled
        if result.is_filled and self._on_fill:
            self._on_fill(result)

        return result

    def record_trade_pnl(self, pnl: float) -> None:
        """Record trade P&L for risk tracking.

        Args:
            pnl: Trade P&L
        """
        self.risk_manager.record_trade_end(pnl)

    def update_account_value(self, value: float) -> None:
        """Update account value.

        Args:
            value: New account value
        """
        self.account_value = value
        self.position_sizer.update_account_value(value)
        self.risk_manager.update_account_value(value)

    def get_risk_stats(self) -> dict[str, Any]:
        """Get current risk statistics.

        Returns:
            Risk stats dict
        """
        return self.risk_manager.get_stats()

    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed.

        Returns:
            True if trading allowed
        """
        can_trade, _ = self.risk_manager.can_trade()
        return can_trade
