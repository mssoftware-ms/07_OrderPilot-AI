"""Broker Types and Data Models for OrderPilot-AI.

Contains all Pydantic models, exceptions, and utility classes for broker integration.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.database.models import OrderSide, OrderStatus, OrderType, TimeInForce


# ==================== Exceptions ====================

class BrokerError(Exception):
    """Base exception for broker-related errors."""
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")


class BrokerConnectionError(BrokerError):
    """Raised when broker connection fails."""
    pass


class OrderValidationError(BrokerError):
    """Raised when order validation fails."""
    pass


class InsufficientFundsError(BrokerError):
    """Raised when account has insufficient funds."""
    pass


class RateLimitError(BrokerError):
    """Raised when rate limit is exceeded."""
    pass


# ==================== Order Models ====================

class OrderRequest(BaseModel):
    """Standardized order request."""
    model_config = ConfigDict(use_enum_values=True)

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    time_in_force: TimeInForce = TimeInForce.DAY

    # Price fields
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None

    # Risk management
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None

    # Strategy metadata
    strategy_name: str | None = None
    signal_confidence: float | None = None

    # AI analysis placeholder
    ai_analysis: dict[str, Any] | None = None

    # Internal tracking
    internal_order_id: str | None = None
    notes: str | None = None

    @field_validator('limit_price')
    @classmethod
    def validate_limit_price(cls, v: Decimal | None, info) -> Decimal | None:
        """Ensure limit price is set for limit orders."""
        values = info.data
        if values.get('order_type') in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError("Limit price required for limit orders")
        return v

    @field_validator('stop_price')
    @classmethod
    def validate_stop_price(cls, v: Decimal | None, info) -> Decimal | None:
        """Ensure stop price is set for stop orders."""
        values = info.data
        if values.get('order_type') in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
            raise ValueError("Stop price required for stop orders")
        return v


class OrderResponse(BaseModel):
    """Standardized order response."""
    model_config = ConfigDict(use_enum_values=True)

    broker_order_id: str
    internal_order_id: str
    status: OrderStatus
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal

    # Execution details
    filled_quantity: Decimal = Decimal('0')
    average_fill_price: Decimal | None = None

    # Timestamps
    created_at: datetime
    submitted_at: datetime | None = None
    updated_at: datetime

    # Fee information
    estimated_fee: Decimal = Decimal('0')
    actual_fee: Decimal | None = None

    # Additional info
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Position(BaseModel):
    """Current position information."""
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal | None = None
    market_value: Decimal | None = None

    # P&L
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal = Decimal('0')

    # Percentages
    pnl_percentage: float | None = None

    # Additional info
    exchange: str | None = None
    currency: str = "EUR"

    @property
    def is_long(self) -> bool:
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        return self.quantity < 0


class Balance(BaseModel):
    """Account balance information."""
    currency: str = "EUR"
    cash: Decimal
    market_value: Decimal
    total_equity: Decimal

    # Buying power
    buying_power: Decimal
    margin_used: Decimal | None = None
    margin_available: Decimal | None = None

    # Daily tracking
    daily_pnl: Decimal | None = None
    daily_pnl_percentage: float | None = None

    # Risk metrics
    maintenance_margin: Decimal | None = None
    initial_margin: Decimal | None = None

    # Timestamp
    as_of: datetime = Field(default_factory=datetime.utcnow)


class FeeModel(BaseModel):
    """Fee calculation model."""
    broker: str
    fee_type: str  # flat, percentage, tiered

    # Flat fee
    flat_fee: Decimal | None = None

    # Percentage fee
    percentage: float | None = None
    min_fee: Decimal | None = None
    max_fee: Decimal | None = None

    # Additional fees
    exchange_fee: Decimal = Decimal('0')
    regulatory_fee: Decimal = Decimal('0')

    def calculate(self, order_value: Decimal, quantity: int | None = None) -> Decimal:
        """Calculate total fee for an order."""
        base_fee = Decimal('0')

        if self.fee_type == "flat" and self.flat_fee:
            base_fee = self.flat_fee
        elif self.fee_type == "percentage" and self.percentage:
            base_fee = order_value * Decimal(str(self.percentage / 100))
            if self.min_fee:
                base_fee = max(base_fee, self.min_fee)
            if self.max_fee:
                base_fee = min(base_fee, self.max_fee)

        total_fee = base_fee + self.exchange_fee + self.regulatory_fee
        return total_fee


# ==================== AI Hook Types ====================

class AIAnalysisRequest(BaseModel):
    """Request for AI analysis before order placement."""
    order: OrderRequest
    context: dict[str, Any] = Field(default_factory=dict)

    # Market context
    current_price: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    spread: Decimal | None = None

    # Position context
    current_position: Position | None = None

    # Account context
    account_balance: Balance | None = None

    # Strategy context
    strategy_signals: dict[str, Any] | None = None

    # Risk metrics
    position_risk: dict[str, Any] | None = None
    portfolio_risk: dict[str, Any] | None = None


class AIAnalysisResult(BaseModel):
    """Result from AI analysis."""
    approved: bool
    confidence: float  # 0.0 to 1.0

    # Reasoning
    reasoning: str
    risks_identified: list[str] = Field(default_factory=list)
    opportunities_identified: list[str] = Field(default_factory=list)

    # Suggested modifications
    suggested_price_adjustment: Decimal | None = None
    suggested_quantity_adjustment: Decimal | None = None
    suggested_stop_loss: Decimal | None = None
    suggested_take_profit: Decimal | None = None

    # Fee warning
    estimated_fees: Decimal | None = None
    fee_impact_warning: str | None = None

    # Structured data for UI display
    display_data: dict[str, Any] = Field(default_factory=dict)

    # Metadata
    model_used: str | None = None
    analysis_time_ms: int | None = None
    prompt_version: str | None = None


# ==================== Rate Limiter ====================

class TokenBucketRateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rate: float, burst: int):
        """Initialize rate limiter.

        Args:
            rate: Tokens per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, blocking if necessary."""
        async with self._lock:
            while tokens > self.tokens:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_update = now

                if tokens > self.tokens:
                    sleep_time = (tokens - self.tokens) / self.rate
                    await asyncio.sleep(sleep_time)

            self.tokens -= tokens

    def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now

        if tokens <= self.tokens:
            self.tokens -= tokens
            return True
        return False
