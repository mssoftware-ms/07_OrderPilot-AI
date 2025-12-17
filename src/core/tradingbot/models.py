"""Tradingbot Domain Models and DTOs.

Core data models for the trading bot including feature vectors,
regime states, signals, positions, and LLM responses.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator

from .config import TrailingMode


# ==================== Enums ====================

class TradeSide(str, Enum):
    """Trade direction."""
    LONG = "long"
    SHORT = "short"
    NONE = "none"


class BotAction(str, Enum):
    """Bot decision actions."""
    NO_TRADE = "no_trade"   # Do nothing, conditions not met
    ENTER = "enter"         # Enter a new position
    HOLD = "hold"           # Keep current position
    EXIT = "exit"           # Exit position now
    ADJUST_STOP = "adjust_stop"  # Adjust stop-loss (trailing)


class RegimeType(str, Enum):
    """Market regime types."""
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    UNKNOWN = "unknown"


class VolatilityLevel(str, Enum):
    """Volatility classification."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class SignalType(str, Enum):
    """Signal confirmation level."""
    CANDIDATE = "candidate"   # Potential signal, not confirmed
    CONFIRMED = "confirmed"   # Signal confirmed, ready for entry


# ==================== Feature Models ====================

class FeatureVector(BaseModel):
    """Feature vector for bot decision making.

    Contains all indicator values and derived features
    used for entry/exit scoring and LLM input.
    """
    timestamp: datetime = Field(..., description="Feature calculation timestamp")
    symbol: str = Field(..., description="Trading symbol")

    # Price data
    open: float = Field(..., description="Current bar open")
    high: float = Field(..., description="Current bar high")
    low: float = Field(..., description="Current bar low")
    close: float = Field(..., description="Current bar close")
    volume: float = Field(..., description="Current bar volume")

    # Trend indicators
    sma_20: float | None = Field(None, description="20-period SMA")
    sma_50: float | None = Field(None, description="50-period SMA")
    ema_12: float | None = Field(None, description="12-period EMA")
    ema_26: float | None = Field(None, description="26-period EMA")
    ma_slope_20: float | None = Field(None, description="MA slope (normalized)")

    # Momentum indicators
    rsi_14: float | None = Field(None, ge=0, le=100, description="14-period RSI")
    macd: float | None = Field(None, description="MACD line")
    macd_signal: float | None = Field(None, description="MACD signal line")
    macd_hist: float | None = Field(None, description="MACD histogram")
    stoch_k: float | None = Field(None, ge=0, le=100, description="Stochastic %K")
    stoch_d: float | None = Field(None, ge=0, le=100, description="Stochastic %D")
    cci: float | None = Field(None, description="CCI value")
    mfi: float | None = Field(None, ge=0, le=100, description="Money Flow Index")

    # Volatility indicators
    atr_14: float | None = Field(None, ge=0, description="14-period ATR")
    bb_upper: float | None = Field(None, description="Bollinger upper band")
    bb_middle: float | None = Field(None, description="Bollinger middle band")
    bb_lower: float | None = Field(None, description="Bollinger lower band")
    bb_width: float | None = Field(None, ge=0, description="Bollinger band width")
    bb_pct: float | None = Field(None, description="Price position in BB (%)")

    # Trend strength
    adx: float | None = Field(None, ge=0, le=100, description="ADX value")
    plus_di: float | None = Field(None, ge=0, description="+DI value")
    minus_di: float | None = Field(None, ge=0, description="-DI value")

    # Derived features
    price_vs_sma20: float | None = Field(None, description="Price relative to SMA20 (%)")
    volume_ratio: float | None = Field(None, ge=0, description="Volume vs avg volume ratio")

    def to_dict_normalized(self) -> dict[str, float]:
        """Export as normalized dict for LLM input.

        Returns dict with only numeric features, suitable for structured prompt.
        """
        data = {}
        for key, value in self.model_dump().items():
            if key in ('timestamp', 'symbol'):
                continue
            if value is not None and isinstance(value, (int, float)):
                data[key] = round(float(value), 4)
        return data

    def compute_hash(self) -> str:
        """Compute hash of feature vector for audit trail."""
        data = json.dumps(self.to_dict_normalized(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class RegimeState(BaseModel):
    """Current market regime classification.

    Combines trend direction and volatility level for
    strategy selection and parameter adjustment.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    regime: RegimeType = Field(default=RegimeType.UNKNOWN)
    volatility: VolatilityLevel = Field(default=VolatilityLevel.NORMAL)

    # Confidence scores
    regime_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in regime classification"
    )
    volatility_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in volatility classification"
    )

    # Underlying metrics
    adx_value: float | None = Field(None, description="ADX value used")
    atr_pct: float | None = Field(None, description="ATR as % of price")
    bb_width_pct: float | None = Field(None, description="BB width as % of price")

    @computed_field
    @property
    def is_trending(self) -> bool:
        """Check if market is trending."""
        return self.regime in (RegimeType.TREND_UP, RegimeType.TREND_DOWN)

    @computed_field
    @property
    def regime_label(self) -> str:
        """Human-readable regime label."""
        return f"{self.regime.value}/{self.volatility.value}"


# ==================== Signal Models ====================

class Signal(BaseModel):
    """Trading signal with entry details.

    Represents a potential or confirmed entry signal with
    scoring, direction, and risk parameters.
    """
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: str = Field(...)

    # Signal details
    signal_type: SignalType = Field(default=SignalType.CANDIDATE)
    side: TradeSide = Field(...)
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Entry score (0-1)"
    )

    # Price levels
    entry_price: float = Field(..., gt=0, description="Suggested entry price")
    stop_loss_price: float = Field(..., gt=0, description="Initial stop-loss price")
    stop_loss_pct: float = Field(..., gt=0, description="Stop-loss as %")

    # Context
    regime: RegimeType = Field(default=RegimeType.UNKNOWN)
    strategy_name: str | None = Field(None, description="Strategy that generated signal")
    reason_codes: list[str] = Field(default_factory=list, description="Signal reason codes")

    @computed_field
    @property
    def risk_reward_potential(self) -> float | None:
        """Estimated risk-reward based on ATR."""
        # Simplified: assume 2:1 potential R:R
        return 2.0

    def to_marker_data(self) -> dict[str, Any]:
        """Convert to chart marker data format."""
        return {
            "time": int(self.timestamp.timestamp()),
            "position": "belowBar" if self.side == TradeSide.LONG else "aboveBar",
            "color": "#4CAF50" if self.side == TradeSide.LONG else "#F44336",
            "shape": "arrowUp" if self.side == TradeSide.LONG else "arrowDown",
            "text": f"{self.side.value.upper()} {self.score:.0%}",
            "size": 2 if self.signal_type == SignalType.CONFIRMED else 1
        }


class OrderIntent(BaseModel):
    """Intent to place an order.

    Represents the bot's decision to enter/exit, before
    actual order execution. Used for validation and logging.
    """
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: str = Field(...)

    # Order details
    side: TradeSide = Field(...)
    action: Literal["entry", "exit", "stop_update"] = Field(...)
    quantity: float = Field(..., gt=0)
    order_type: Literal["market", "limit", "stop", "stop_limit"] = Field(default="market")

    # Prices
    limit_price: float | None = Field(None, gt=0)
    stop_price: float | None = Field(None, gt=0)

    # Context
    signal_id: str | None = Field(None, description="Source signal ID")
    reason: str = Field(..., description="Why this order")

    # Validation state
    validated: bool = Field(default=False)
    validation_errors: list[str] = Field(default_factory=list)


# ==================== Position Models ====================

class TrailingState(BaseModel):
    """Trailing stop state tracking.

    Tracks the current trailing stop level and mode,
    with history of adjustments.
    """
    mode: TrailingMode = Field(...)
    current_stop_price: float = Field(..., gt=0)
    initial_stop_price: float = Field(..., gt=0)
    highest_price: float = Field(..., gt=0, description="Highest price since entry (long)")
    lowest_price: float = Field(..., gt=0, description="Lowest price since entry (short)")

    # Trailing parameters
    trailing_distance: float = Field(..., gt=0, description="Current trailing distance")
    last_update_bar: int = Field(default=0, description="Bar index of last update")
    update_count: int = Field(default=0, description="Number of trailing updates")

    # History (last N updates)
    stop_history: list[tuple[datetime, float]] = Field(
        default_factory=list,
        description="History of stop price changes"
    )

    def update_stop(
        self,
        new_stop: float,
        current_bar: int,
        timestamp: datetime,
        is_long: bool = True
    ) -> bool:
        """Update stop price if valid (never loosens).

        Args:
            new_stop: New stop price
            current_bar: Current bar index
            timestamp: Current timestamp
            is_long: True for LONG positions (stop can only go up),
                     False for SHORT positions (stop can only go down)

        Returns:
            True if stop was updated, False if rejected
        """
        # Never loosen stop invariant
        # Long: stop can only go up
        # Short: stop can only go down
        if is_long:
            is_valid = new_stop > self.current_stop_price
        else:
            is_valid = new_stop < self.current_stop_price

        if is_valid:
            self.stop_history.append((timestamp, new_stop))
            if len(self.stop_history) > 50:  # Keep last 50
                self.stop_history = self.stop_history[-50:]
            self.current_stop_price = new_stop
            self.last_update_bar = current_bar
            self.update_count += 1
            return True
        return False


class PositionState(BaseModel):
    """Current position state.

    Complete state of an open position including entry,
    trailing stop, P&L, and metadata.
    """
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    symbol: str = Field(...)
    side: TradeSide = Field(...)

    # Entry details
    entry_time: datetime = Field(...)
    entry_price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)

    # Current state
    current_price: float = Field(..., gt=0)
    trailing: TrailingState = Field(...)

    # P&L tracking
    unrealized_pnl: float = Field(default=0.0)
    unrealized_pnl_pct: float = Field(default=0.0)
    max_favorable_excursion: float = Field(default=0.0, description="Best unrealized P&L")
    max_adverse_excursion: float = Field(default=0.0, description="Worst unrealized P&L")

    # Metadata
    signal_id: str | None = Field(None)
    strategy_name: str | None = Field(None)
    bars_held: int = Field(default=0)

    def update_price(self, price: float) -> None:
        """Update current price and recalculate P&L."""
        self.current_price = price

        if self.side == TradeSide.LONG:
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
            self.unrealized_pnl_pct = ((price / self.entry_price) - 1) * 100
            self.trailing.highest_price = max(self.trailing.highest_price, price)
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.quantity
            self.unrealized_pnl_pct = ((self.entry_price / price) - 1) * 100
            self.trailing.lowest_price = min(self.trailing.lowest_price, price)

        # Track excursions
        if self.unrealized_pnl > self.max_favorable_excursion:
            self.max_favorable_excursion = self.unrealized_pnl
        if self.unrealized_pnl < self.max_adverse_excursion:
            self.max_adverse_excursion = self.unrealized_pnl

    def is_stopped_out(self) -> bool:
        """Check if position hit stop-loss."""
        if self.side == TradeSide.LONG:
            return self.current_price <= self.trailing.current_stop_price
        else:
            return self.current_price >= self.trailing.current_stop_price


# ==================== Decision Models ====================

class BotDecision(BaseModel):
    """Bot decision record.

    Complete record of a bot decision for audit trail,
    including inputs, action, and reasoning.
    """
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: str = Field(...)

    # Decision
    action: BotAction = Field(...)
    side: TradeSide = Field(default=TradeSide.NONE)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Context (hashed for audit)
    features_hash: str = Field(..., description="Hash of input features")
    regime: RegimeType = Field(...)
    strategy_name: str | None = Field(None)

    # Stop management (if applicable)
    stop_price_before: float | None = Field(None)
    stop_price_after: float | None = Field(None)

    # Reasoning
    reason_codes: list[str] = Field(default_factory=list)
    notes: str = Field(default="")

    # Source
    source: Literal["rule_based", "llm", "manual"] = Field(default="rule_based")
    llm_response_id: str | None = Field(None, description="LLM response ID if applicable")


# ==================== LLM Response Models ====================

class LLMBotResponse(BaseModel):
    """Structured LLM response for bot decisions.

    JSON schema for OpenAI Structured Outputs.
    """
    action: BotAction = Field(..., description="Recommended action")
    side: TradeSide = Field(default=TradeSide.NONE, description="Trade side if entering")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")

    # Reasoning
    reason_codes: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Codes explaining decision"
    )

    # Entry details (if action is ENTER)
    entry: dict[str, Any] | None = Field(
        None,
        description="Entry details: {ok: bool, price_hint: float}"
    )

    # Stop management (if action is ADJUST_STOP)
    stop: dict[str, Any] | None = Field(
        None,
        description="Stop details: {mode: str, new_stop_price: float}"
    )

    # Additional parameters
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters"
    )

    # Validation flag
    constraints_ok: bool = Field(
        default=True,
        description="Whether all constraints are met"
    )

    @field_validator('reason_codes')
    @classmethod
    def validate_reason_codes(cls, v: list[str]) -> list[str]:
        """Ensure reason codes are uppercase."""
        return [code.upper() for code in v]


# ==================== Strategy Profile ====================

class StrategyProfile(BaseModel):
    """Strategy profile for daily selection.

    Defines a trading strategy with its parameters,
    applicable regimes, and performance history.
    """
    name: str = Field(..., description="Strategy identifier")
    description: str = Field(default="", description="Strategy description")

    # Applicable conditions
    regimes: list[RegimeType] = Field(
        default_factory=list,
        description="Applicable market regimes"
    )
    volatility_levels: list[VolatilityLevel] = Field(
        default_factory=list,
        description="Applicable volatility levels"
    )

    # Parameters
    entry_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum entry score"
    )
    trailing_mode: TrailingMode = Field(
        default=TrailingMode.ATR,
        description="Preferred trailing mode"
    )
    trailing_multiplier: float = Field(
        default=1.0,
        ge=0.5,
        le=3.0,
        description="Trailing distance multiplier"
    )

    # Historical performance
    win_rate: float | None = Field(None, ge=0, le=1)
    profit_factor: float | None = Field(None, ge=0)
    expectancy: float | None = Field(None)
    sample_size: int = Field(default=0)

    # Robustness
    is_robust: bool = Field(default=False, description="Passed robustness tests")
    last_validated: datetime | None = Field(None)

    def is_applicable(self, regime: RegimeState) -> bool:
        """Check if strategy is applicable for current regime."""
        regime_ok = not self.regimes or regime.regime in self.regimes
        vol_ok = not self.volatility_levels or regime.volatility in self.volatility_levels
        return regime_ok and vol_ok
