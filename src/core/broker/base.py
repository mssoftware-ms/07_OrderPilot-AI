"""BrokerAdapter Interface for OrderPilot-AI Trading Application.

Provides a unified interface for different broker integrations (IBKR, Trade Republic)
with support for AI hooks, rate limiting, and fee calculations.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.database.models import OrderSide, OrderStatus, OrderType, TimeInForce

logger = logging.getLogger(__name__)


# ==================== Data Models ====================

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


class OrderRequest(BaseModel):
    """Standardized order request."""
    model_config = ConfigDict(use_enum_values=True)  # Use enum values as strings

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    time_in_force: TimeInForce = TimeInForce.DAY

    # Price fields (optional based on order type)
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
    model_config = ConfigDict(use_enum_values=True)  # Use enum values as strings

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


# ==================== BrokerAdapter Interface ====================

class BrokerAdapter(ABC):
    """Abstract base class for broker integrations with template methods."""

    def __init__(
        self,
        name: str,
        fee_model: FeeModel,
        rate_limit: TokenBucketRateLimiter | None = None,
        ai_hook: Callable[[AIAnalysisRequest], AIAnalysisResult] | None = None,
        **kwargs  # Accept broker_name for backward compatibility
    ):
        """Initialize broker adapter.

        Args:
            name: Broker name
            fee_model: Fee calculation model
            rate_limit: Rate limiter instance
            ai_hook: AI analysis hook function
            **kwargs: Additional broker-specific parameters
        """
        # Support both 'name' and 'broker_name' for backward compatibility
        self.name = kwargs.get('broker_name', name)
        self.fee_model = fee_model
        self.rate_limiter = rate_limit
        self.ai_hook = ai_hook
        self._kill_switch_active = False
        self._connected = False
        self._connection_attempts = 0
        self._last_connection_error: Exception | None = None

    # ==================== Connection Management (Template Methods) ====================

    async def connect(self) -> None:
        """Establish connection to broker using template method pattern.

        This method coordinates the connection process:
        1. Validate credentials
        2. Establish broker-specific connection
        3. Verify connection is working
        4. Set up initial state (optional)

        Subclasses should implement _establish_connection() for broker-specific logic.
        """
        try:
            logger.info(f"Connecting to {self.name}...")
            self._connection_attempts += 1

            # Step 1: Validate credentials (optional hook)
            await self._validate_credentials()

            # Step 2: Broker-specific connection logic (required)
            await self._establish_connection()

            # Step 3: Verify connection is working
            await self._verify_connection()

            # Step 4: Set up initial state (optional hook)
            await self._setup_initial_state()

            # Mark as connected
            self._connected = True
            self._last_connection_error = None
            logger.info(f"Successfully connected to {self.name}")

        except Exception as e:
            self._connected = False
            self._last_connection_error = e
            logger.error(f"Failed to connect to {self.name}: {e}")
            raise BrokerConnectionError(
                code=f"{self.name.upper()}_CONNECT_FAILED",
                message=f"Failed to connect to {self.name}: {str(e)}",
                details={
                    "broker": self.name,
                    "attempts": self._connection_attempts,
                    "error": str(e)
                }
            )

    async def disconnect(self) -> None:
        """Disconnect from broker using template method pattern.

        This method coordinates the disconnection process:
        1. Cleanup broker-specific resources
        2. Reset connection state
        3. Log disconnection

        Subclasses should implement _cleanup_resources() for broker-specific cleanup.
        """
        try:
            if not self._connected:
                logger.debug(f"Already disconnected from {self.name}")
                return

            logger.info(f"Disconnecting from {self.name}...")

            # Step 1: Broker-specific cleanup
            await self._cleanup_resources()

            # Step 2: Reset connection state
            self._connected = False

            logger.info(f"Disconnected from {self.name}")

        except Exception as e:
            logger.error(f"Error during disconnect from {self.name}: {e}")
            # Force disconnected state even on error
            self._connected = False
            raise

    async def is_connected(self) -> bool:
        """Check if connected to broker.

        Default implementation checks the _connected flag.
        Subclasses can override for more sophisticated checks.

        Returns:
            True if connected
        """
        return self._connected

    # ==================== Template Method Hooks ====================

    async def _validate_credentials(self) -> None:
        """Validate credentials before connecting.

        Optional hook for subclasses to validate API keys, tokens, etc.
        Default implementation does nothing.
        """
        pass

    @abstractmethod
    async def _establish_connection(self) -> None:
        """Establish broker-specific connection.

        Required method for subclasses to implement the actual
        connection logic (e.g., create client, connect WebSocket, etc.).

        Raises:
            BrokerConnectionError: If connection fails
        """
        pass

    async def _verify_connection(self) -> None:
        """Verify the connection is working.

        Optional hook for subclasses to test the connection
        (e.g., make a test API call).
        Default implementation does nothing.
        """
        pass

    async def _setup_initial_state(self) -> None:
        """Set up initial state after connection.

        Optional hook for subclasses to request initial data,
        subscribe to streams, etc.
        Default implementation does nothing.
        """
        pass

    @abstractmethod
    async def _cleanup_resources(self) -> None:
        """Clean up broker-specific resources.

        Required method for subclasses to implement cleanup logic
        (e.g., close clients, cancel tasks, close WebSockets).
        """
        pass

    # ==================== Helper Methods ====================

    def _ensure_connected(self) -> None:
        """Ensure the adapter is connected.

        Raises:
            BrokerConnectionError: If not connected
        """
        if not self._connected:
            raise BrokerConnectionError(
                code=f"{self.name.upper()}_NOT_CONNECTED",
                message=f"Not connected to {self.name}",
                details={"last_error": str(self._last_connection_error) if self._last_connection_error else None}
            )

    async def is_available(self) -> bool:
        """Check if broker API is available.

        Default implementation tries to establish connection and check status.
        Subclasses can override for more sophisticated health checks.

        Returns:
            True if broker is available
        """
        try:
            if not self._connected:
                return False

            # Call broker-specific availability check
            return await self._check_api_status()

        except Exception as e:
            logger.debug(f"Broker {self.name} availability check failed: {e}")
            return False

    async def _check_api_status(self) -> bool:
        """Check broker API status.

        Optional hook for subclasses to implement API health check.
        Default implementation returns True if connected.

        Returns:
            True if API is healthy
        """
        return self._connected

    # ==================== Order Management ====================

    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """Place an order with the broker.

        Args:
            order: Order request details

        Returns:
            Order response with broker confirmation

        Raises:
            Various broker errors
        """
        # Check kill switch
        if self._kill_switch_active:
            raise BrokerError("KILL_SWITCH", "Trading halted by kill switch")

        # Rate limiting
        if self.rate_limiter:
            if not self.rate_limiter.try_acquire():
                raise RateLimitError("RATE_LIMIT", "Rate limit exceeded")

        # AI analysis hook
        if self.ai_hook and order.ai_analysis is None:
            analysis_request = AIAnalysisRequest(
                order=order,
                context={"broker": self.name}
            )

            try:
                ai_result = await asyncio.get_event_loop().run_in_executor(
                    None, self.ai_hook, analysis_request
                )

                if not ai_result.approved:
                    raise OrderValidationError(
                        "AI_REJECTED",
                        f"Order rejected by AI: {ai_result.reasoning}"
                    )

                # Store AI analysis in order
                order.ai_analysis = ai_result.dict()

            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                # Continue without AI if it fails (configurable)

        # Validate order
        self._validate_order(order)

        # Calculate fees
        estimated_fee = self.calculate_fee(order)

        # Place order with broker
        return await self._place_order_impl(order, estimated_fee)

    @abstractmethod
    async def _place_order_impl(
        self,
        order: OrderRequest,
        estimated_fee: Decimal
    ) -> OrderResponse:
        """Internal implementation of order placement."""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: Broker order ID

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get current order status.

        Args:
            order_id: Broker order ID

        Returns:
            Current order information
        """
        pass

    # ==================== Account Information ====================

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get all current positions."""
        pass

    @abstractmethod
    async def get_balance(self) -> Balance:
        """Get account balance."""
        pass

    # ==================== Market Data (Optional) ====================

    async def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get current quote for symbol (if supported)."""
        return None

    # ==================== Helper Methods ====================

    def _validate_order(self, order: OrderRequest) -> None:
        """Validate order parameters."""
        if order.quantity <= 0:
            raise OrderValidationError("INVALID_QUANTITY", "Quantity must be positive")

        if order.order_type == OrderType.LIMIT and not order.limit_price:
            raise OrderValidationError("MISSING_LIMIT_PRICE", "Limit price required")

        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and not order.stop_price:
            raise OrderValidationError("MISSING_STOP_PRICE", "Stop price required")

    def calculate_fee(self, order: OrderRequest) -> Decimal:
        """Calculate estimated fee for order."""
        order_value = order.quantity * (order.limit_price or Decimal('100'))  # Use default for market orders
        return self.fee_model.calculate(order_value, int(order.quantity))

    def activate_kill_switch(self) -> None:
        """Activate the kill switch to halt all trading."""
        self._kill_switch_active = True
        logger.warning(f"Kill switch activated for {self.name}")

    def deactivate_kill_switch(self) -> None:
        """Deactivate the kill switch."""
        self._kill_switch_active = False
        logger.info(f"Kill switch deactivated for {self.name}")