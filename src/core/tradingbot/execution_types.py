"""Execution Types for Tradingbot.

Contains enums and dataclasses for order execution:
- OrderStatus: Order lifecycle states
- OrderType: Order types (market, limit, etc.)
- OrderResult: Execution result
- PositionSizeResult: Position sizing result
- RiskLimits: Risk configuration
- RiskState: Risk tracking state
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class OrderResult:
    """Result of order execution."""
    order_id: str
    status: OrderStatus
    filled_qty: float = 0.0
    filled_price: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_message: str | None = None

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED

    @property
    def is_rejected(self) -> bool:
        return self.status in (OrderStatus.REJECTED, OrderStatus.CANCELLED)


@dataclass
class PositionSizeResult:
    """Result of position size calculation."""
    quantity: float
    risk_amount: float
    position_value: float
    risk_pct_actual: float
    sizing_method: str
    constraints_applied: list[str] = field(default_factory=list)


class RiskLimits(BaseModel):
    """Risk limit configuration."""
    # Daily limits
    max_trades_per_day: int = Field(default=10, ge=1, le=100)
    max_daily_loss_pct: float = Field(default=3.0, ge=0.5, le=20.0)
    max_daily_loss_amount: float | None = Field(default=None, ge=0)

    # Position limits
    max_position_size_pct: float = Field(default=10.0, ge=1, le=100)
    max_position_value: float | None = Field(default=None, ge=0)
    max_concurrent_positions: int = Field(default=3, ge=1, le=20)

    # Loss streak
    loss_streak_cooldown: int = Field(default=3, ge=1, le=10)
    cooldown_duration_minutes: int = Field(default=60, ge=5)

    # Per-trade limits
    max_risk_per_trade_pct: float = Field(default=2.0, ge=0.1, le=100.0)
    min_risk_reward_ratio: float = Field(default=1.5, ge=1.0, le=5.0)


class RiskState(BaseModel):
    """Current risk tracking state."""
    date: datetime = Field(default_factory=datetime.utcnow)
    trades_today: int = 0
    daily_pnl: float = 0.0
    open_positions: int = 0
    consecutive_losses: int = 0
    last_loss_time: datetime | None = None
    in_cooldown: bool = False
    cooldown_until: datetime | None = None
