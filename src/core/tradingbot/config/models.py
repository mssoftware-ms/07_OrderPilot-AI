"""Pydantic Models for JSON Strategy Configuration.

Complete type-safe models for the Regime-Based JSON Strategy System.
Validates against strategy_config_schema.json (Draft 2020-12).
"""

from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, Field, field_validator, model_validator

# Strict validation toggle for Condition operator operand checks.
# Some evaluation paths expect runtime validation instead of Pydantic errors.
STRICT_CONDITION_VALIDATION: ContextVar[bool] = ContextVar(
    "STRICT_CONDITION_VALIDATION",
    default=True,
)


# ==================== Enums ====================

class ConditionOperator(str, Enum):
    """Comparison operators for condition evaluation."""
    GT = "gt"  # Greater than
    LT = "lt"  # Less than
    EQ = "eq"  # Equal
    BETWEEN = "between"  # Between min and max (inclusive)


class RegimeScope(str, Enum):
    """Scope of regime applicability."""
    ENTRY = "entry"  # Only affects entry decisions
    EXIT = "exit"  # Only affects exit decisions
    IN_TRADE = "in_trade"  # Only active during trades
    GLOBAL = "global"  # Global regime
    # None scope is treated as global (legacy)


class IndicatorType(str, Enum):
    """Supported technical indicator types."""
    # Trend Indicators
    SMA = "SMA"
    EMA = "EMA"
    WMA = "WMA"

    # Momentum Indicators
    RSI = "RSI"
    MACD = "MACD"
    STOCH = "STOCH"
    CCI = "CCI"
    MFI = "MFI"

    # Volatility Indicators
    ATR = "ATR"
    BB = "BB"  # Bollinger Bands (types.py uses "bb")

    # Trend Strength
    ADX = "ADX"

    # Volume
    VOLUME = "Volume"
    VOLUME_RATIO = "volume_ratio"  # Match types.py enum (lowercase with underscore)

    # Price-based
    PRICE = "Price"
    PRICE_CHANGE = "PriceChange"

    # Regime Detection (Composite Indicators)
    MOMENTUM_SCORE = "momentum_score"  # Match types.py enum (lowercase with underscore)
    PRICE_STRENGTH = "price_strength"  # Match types.py enum (lowercase with underscore)
    CHOP = "chop"  # Choppiness Index for range detection (match types.py enum)

    @classmethod
    def _missing_(cls, value: object) -> "IndicatorType" | None:
        """Allow case-insensitive and underscore-insensitive indicator types.

        Also handles aliases for backward compatibility:
        - BBANDS → BB (Bollinger Bands)
        """
        if not isinstance(value, str):
            return None

        # Handle aliases
        aliases = {
            "bbands": "bb",  # BBANDS is an alias for BB
        }
        value_lower = value.lower()
        if value_lower in aliases:
            value = aliases[value_lower]

        normalized = value.replace("_", "").replace(" ", "").lower()
        for member in cls:
            member_norm = member.value.replace("_", "").replace(" ", "").lower()
            if member_norm == normalized:
                return member
        return None


# ==================== Indicator Models ====================

class IndicatorDefinition(BaseModel):
    """Technical indicator definition with parameters.

    Example:
        {"id": "rsi14_1h", "type": "RSI", "params": {"period": 14}, "timeframe": "1h"}
    """
    id: str = Field(..., description="Unique indicator identifier")
    type: IndicatorType = Field(..., description="Indicator type")
    params: dict[str, Any] = Field(..., description="Indicator parameters (e.g., period, multiplier)")
    timeframe: str | None = Field(None, description="Timeframe (e.g., '1h', '4h', '1d'). None = default")

    @field_validator("params")
    @classmethod
    def validate_params(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate that params is not empty."""
        if not v:
            raise ValueError("Indicator params cannot be empty")
        return v


# ==================== Condition Models ====================

class IndicatorRef(BaseModel):
    """Reference to an indicator output field.

    Example:
        {"indicator_id": "rsi14_1h", "field": "value"}
    """
    indicator_id: str = Field(..., description="ID of referenced indicator")
    field: str = Field(..., description="Output field (e.g., 'value', 'signal', 'histogram')")


class ConditionLeft(IndicatorRef):
    """Backward-compatible left operand wrapper used by older tests/configs."""

    pass


class ConstantValue(BaseModel):
    """Constant numeric value.

    Example:
        {"value": 60}
    """
    value: float = Field(..., description="Numeric constant")


class BetweenRange(BaseModel):
    """Range for 'between' operator.

    Example:
        {"min": 45, "max": 55}
    """
    min: float = Field(..., description="Minimum value (inclusive)")
    max: float = Field(..., description="Maximum value (inclusive)")

    @field_validator("max")
    @classmethod
    def validate_range(cls, v: float, info) -> float:
        """Ensure max > min."""
        if "min" in info.data and v <= info.data["min"]:
            raise ValueError(f"max ({v}) must be greater than min ({info.data['min']})")
        return v


class ConditionRight(BaseModel):
    """Backward-compatible right operand wrapper.

    Supports either:
    - constant value (value)
    - between range (min/max)
    - indicator reference (indicator_id/field)
    """

    indicator_id: str | None = None
    field: str | None = None
    value: float | None = None
    min: float | None = None
    max: float | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "ConditionRight":
        """Ensure one operand mode is provided."""
        indicator_mode = self.indicator_id is not None and self.field is not None
        value_mode = self.value is not None
        range_mode = self.min is not None and self.max is not None

        if sum([indicator_mode, value_mode, range_mode]) != 1:
            raise ValueError(
                "ConditionRight requires exactly one of: "
                "(indicator_id & field), value, or (min & max)"
            )

        if range_mode and self.max <= self.min:
            raise ValueError("max must be greater than min for range mode")
        return self


class Condition(BaseModel):
    """Single comparison condition.

    Supports two modes:
    1. Operator-based: left, op, right (legacy)
    2. CEL expression: cel_expression (new)

    Example (gt operator):
        {
            "left": {"indicator_id": "rsi14", "field": "value"},
            "op": "gt",
            "right": {"value": 60}
        }

    Example (between operator):
        {
            "left": {"indicator_id": "rsi14", "field": "value"},
            "op": "between",
            "right": {"min": 45, "max": 55}
        }

    Example (CEL expression):
        {
            "cel_expression": "rsi14.value > 60 && adx14.value > 25"
        }
    """
    # Operator-based condition (legacy, optional if CEL is used)
    left: IndicatorRef | ConstantValue | ConditionLeft | None = Field(None, description="Left operand")
    op: ConditionOperator | None = Field(None, description="Comparison operator")
    right: IndicatorRef | ConstantValue | BetweenRange | ConditionRight | None = Field(None, description="Right operand")

    # CEL expression-based condition (new, optional if operator is used)
    cel_expression: str | None = Field(
        None,
        description="CEL expression for complex conditions (e.g., 'rsi14.value > 60 && adx14.value > 25')"
    )

    @model_validator(mode="after")
    def validate_condition_mode(self) -> "Condition":
        """Ensure either operator-based OR CEL expression is provided, not both."""
        has_operator_mode = self.left is not None and self.op is not None and self.right is not None
        has_cel_mode = self.cel_expression is not None

        if not has_operator_mode and not has_cel_mode:
            raise ValueError(
                "Condition must have either operator-based fields (left, op, right) "
                "OR cel_expression, but neither was provided"
            )

        if has_operator_mode and has_cel_mode:
            raise ValueError(
                "Condition cannot have both operator-based fields (left, op, right) "
                "AND cel_expression. Choose one mode."
            )

        return self

    @field_validator("right")
    @classmethod
    def validate_right_operand(cls, v, info) -> IndicatorRef | ConstantValue | BetweenRange | None:
        """Ensure right operand matches operator type."""
        if v is None:
            return v  # Allow None for CEL mode

        op = info.data.get("op")
        if not STRICT_CONDITION_VALIDATION.get():
            return v

        # Backward-compatible wrapper
        if isinstance(v, ConditionRight):
            indicator_mode = v.indicator_id is not None and v.field is not None
            range_mode = v.min is not None and v.max is not None
            value_mode = v.value is not None

            if op == ConditionOperator.BETWEEN:
                if not range_mode:
                    raise ValueError("'between' operator requires min/max on ConditionRight")
            else:
                if range_mode:
                    raise ValueError("Between range can only be used with 'between' operator")
                if not (value_mode or indicator_mode):
                    raise ValueError("Right operand must be value or indicator for non-between operators")
            return v

        if op == ConditionOperator.BETWEEN and not isinstance(v, BetweenRange):
            raise ValueError("'between' operator requires BetweenRange as right operand")
        if op != ConditionOperator.BETWEEN and isinstance(v, BetweenRange):
            raise ValueError("BetweenRange can only be used with 'between' operator")
        return v


class ConditionGroup(BaseModel):
    """Group of conditions with AND/OR logic. Supports recursive nesting.

    Example (all = AND):
        {
            "all": [
                {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 25}},
                {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "gt", "right": {"value": 60}}
            ]
        }

    Example (any = OR):
        {
            "any": [
                {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "lt", "right": {"value": 30}},
                {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "gt", "right": {"value": 70}}
            ]
        }

    Example (nested groups):
        {
            "any": [
                {"all": [condition1, condition2]},
                {"all": [condition3, condition4]}
            ]
        }
    """
    all: list[Union[Condition, "ConditionGroup"]] | None = Field(None, description="All conditions must be true (AND)")
    any: list[Union[Condition, "ConditionGroup"]] | None = Field(None, description="At least one condition must be true (OR)")

    # Allow dict-style access for backward compatibility with tests/legacy code
    def __getitem__(self, item: str):
        return getattr(self, item)

    def __setitem__(self, key: str, value):
        return setattr(self, key, value)

    @model_validator(mode="after")
    def validate_group(self) -> "ConditionGroup":
        """Ensure at least one of 'all' or 'any' is specified (but not both)."""
        if self.all is None and self.any is None:
            raise ValueError("ConditionGroup must have either 'all' or 'any' specified")
        if self.all is not None and self.any is not None:
            raise ValueError("ConditionGroup cannot have both 'all' and 'any' specified")
        return self


# Rebuild ConditionGroup after forward reference is defined (recursive structure)
ConditionGroup.model_rebuild()


# ==================== Regime Models ====================

class RegimeDefinition(BaseModel):
    """Market regime definition with activation conditions.

    Example:
        {
            "id": "trending",
            "name": "Trending Market",
            "conditions": {
                "all": [
                    {"left": {"indicator_id": "adx14_1h", "field": "value"}, "op": "gt", "right": {"value": 25}},
                    {"left": {"indicator_id": "adx14_4h", "field": "value"}, "op": "gt", "right": {"value": 25}}
                ]
            },
            "priority": 10,
            "scope": "entry"
        }
    """
    id: str = Field(..., description="Unique regime identifier")
    name: str = Field(..., description="Human-readable regime name")
    conditions: ConditionGroup = Field(..., description="Activation conditions")
    priority: int = Field(0, description="Priority for conflict resolution (higher = more important)")
    scope: RegimeScope | None = Field(None, description="Regime scope (entry/exit/in_trade). None = global")


# ==================== Strategy Models ====================

class RiskSettings(BaseModel):
    """Risk management parameters.

    Example:
        {
            "position_size": 0.02,
            "stop_loss": 0.02,
            "take_profit": 0.06
        }
    """
    # Core risk params (used by routing/executor tests)
    position_size: float | None = Field(None, gt=0, le=1, description="Position size as fraction of equity")
    stop_loss: float | None = Field(None, gt=0, le=1, description="Stop loss as fraction of entry")
    take_profit: float | None = Field(None, gt=0, le=10, description="Take profit as fraction of entry")

    # Legacy fields (kept for backward compatibility)
    stop_loss_pct: float | None = Field(None, gt=0, le=100, description="Stop loss percentage")
    take_profit_pct: float | None = Field(None, gt=0, le=1000, description="Take profit percentage")
    trailing_mode: str | None = Field(None, description="Trailing mode ('percent', 'atr')")
    trailing_multiplier: float | None = Field(None, gt=0, description="Trailing multiplier")
    risk_per_trade_pct: float | None = Field(None, gt=0, le=100, description="Risk per trade percentage")


class StrategyDefinition(BaseModel):
    """Trading strategy definition with entry/exit rules.

    Note: Named JSONStrategyDefinition in __init__.py to avoid conflict with existing StrategyDefinition.

    Example:
        {
            "id": "trend_follow",
            "name": "Trend Following",
            "entry": {
                "all": [
                    {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 25}},
                    {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "gt", "right": {"value": 60}}
                ]
            },
            "exit": {
                "any": [
                    {"left": {"indicator_id": "adx14", "field": "value"}, "op": "lt", "right": {"value": 20}},
                    {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "lt", "right": {"value": 40}}
                ]
            },
            "risk": {
                "stop_loss_pct": 2.0,
                "take_profit_pct": 5.0
            }
        }
    """
    id: str = Field(..., description="Unique strategy identifier")
    name: str = Field(..., description="Strategy name")
    entry: ConditionGroup | None = Field(None, description="Entry signal conditions")
    exit: ConditionGroup | None = Field(None, description="Exit signal conditions")
    risk: RiskSettings | None = Field(None, description="Risk management parameters")


# ==================== Strategy Set Models ====================

class StrategyReference(BaseModel):
    """Reference to a strategy with optional overrides.

    Example (no overrides):
        {"strategy_id": "trend_follow"}

    Example (with overrides):
        {
            "strategy_id": "trend_follow",
            "strategy_overrides": {
                "risk": {
                    "stop_loss_pct": 3.0,
                    "take_profit_pct": 6.0
                }
            }
        }
    """
    strategy_id: str = Field(..., description="ID of base strategy")
    strategy_overrides: dict[str, Any] | None = Field(None, description="Parameter overrides")


class IndicatorOverride(BaseModel):
    """Indicator parameter override for strategy set.

    Example:
        {"indicator_id": "rsi14_1h", "params": {"period": 21}}
    """
    indicator_id: str = Field(..., description="ID of indicator to override")
    params: dict[str, Any] = Field(..., description="New parameter values")


class StrategySetDefinition(BaseModel):
    """Strategy set (bundle of strategies) with overrides.

    Example:
        {
            "id": "set_trend",
            "name": "Trending Strategies",
            "strategies": [
                {
                    "strategy_id": "trend_follow",
                    "strategy_overrides": {
                        "risk": {"stop_loss_pct": 3.0}
                    }
                }
            ],
            "indicator_overrides": [
                {"indicator_id": "rsi14_1h", "params": {"period": 21}}
            ]
        }
    """
    id: str = Field(..., description="Unique strategy set identifier")
    name: str | None = Field(None, description="Strategy set name")
    strategies: list[StrategyReference] = Field(..., description="Strategies in this set")
    indicator_overrides: list[IndicatorOverride] | None = Field(None, description="Indicator param overrides")

    @field_validator("strategies")
    @classmethod
    def validate_strategies(cls, v: list[StrategyReference]) -> list[StrategyReference]:
        """Ensure at least one strategy in set."""
        if not v:
            raise ValueError("Strategy set must contain at least one strategy")
        return v


# ==================== Routing Models ====================

class RoutingMatch(BaseModel):
    """Regime matching criteria for routing.

    Example:
        {
            "all_of": ["entry_trend"],
            "none_of": ["exit_low_vol", "exit_trend_reversal"]
        }
    """
    all_of: list[str] | None = Field(None, description="All these regimes must be active (AND)")
    any_of: list[str] | None = Field(None, description="At least one regime must be active (OR)")
    none_of: list[str] | None = Field(None, description="None of these regimes can be active (NOT)")

    @model_validator(mode="after")
    def validate_match(self) -> "RoutingMatch":
        """Ensure at least one matching criterion is specified."""
        if self.all_of is None and self.any_of is None and self.none_of is None:
            raise ValueError("RoutingMatch must have at least one of: all_of, any_of, none_of")
        return self


class RoutingRule(BaseModel):
    """Routing rule mapping regimes to strategy set.

    Example:
        {
            "strategy_set_id": "set_trend_normal",
            "match": {
                "all_of": ["entry_trend"],
                "none_of": ["exit_low_vol"]
            }
        }
    """
    strategy_set_id: str = Field(..., description="Strategy set to activate")
    match: RoutingMatch = Field(..., description="Regime matching criteria")


# ==================== Root Config ====================

class ConfigMetadata(BaseModel):
    """Configuration metadata.

    Example:
        {
            "author": "Max Mustermann",
            "created_at": "2026-01-18T12:00:00Z",
            "tags": ["production", "btcusd"],
            "notes": "Production config for BTC/USD trending market"
        }
    """
    author: str | None = Field(None, description="Config author")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    tags: list[str] | None = Field(None, description="Config tags")
    notes: str | None = Field(None, description="Free-text notes")
    dataset_id: str | None = Field(None, description="Dataset identifier for backtests")


class TradingBotConfig(BaseModel):
    """Root configuration model for Regime-Based JSON Strategy System.

    Complete type-safe model matching strategy_config_schema.json.
    """
    schema_version: str = Field(..., description="Schema version (e.g., '1.0')")
    metadata: ConfigMetadata | None = Field(None, description="Configuration metadata")

    indicators: list[IndicatorDefinition] = Field(..., description="Indicator definitions")
    regimes: list[RegimeDefinition] = Field(..., description="Regime definitions")
    strategies: list[StrategyDefinition] = Field(..., description="Strategy definitions")
    strategy_sets: list[StrategySetDefinition] = Field(..., description="Strategy set definitions")
    routing: list[RoutingRule] = Field(..., description="Routing rules")

    # Issue #28: Entry and evaluation params for Analyze Visible Range
    entry_params: dict[str, Any] | None = Field(
        None, description="Entry signal parameters for visible range analysis"
    )
    evaluation_params: dict[str, Any] | None = Field(
        None, description="Evaluation parameters for scoring and validation"
    )
    optimization_results: list[dict[str, Any]] | None = Field(
        None, description="History of optimization results"
    )

    @field_validator("indicators")
    @classmethod
    def validate_indicators(cls, v: list[IndicatorDefinition]) -> list[IndicatorDefinition]:
        """Ensure indicator IDs are unique."""
        ids = [ind.id for ind in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate indicator IDs: {duplicates}")
        return v

    @field_validator("regimes")
    @classmethod
    def validate_regimes(cls, v: list[RegimeDefinition]) -> list[RegimeDefinition]:
        """Ensure regime IDs are unique."""
        ids = [regime.id for regime in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate regime IDs: {duplicates}")
        return v

    @field_validator("strategies")
    @classmethod
    def validate_strategies(cls, v: list[StrategyDefinition]) -> list[StrategyDefinition]:
        """Ensure strategy IDs are unique."""
        ids = [strat.id for strat in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate strategy IDs: {duplicates}")
        return v

    @field_validator("strategy_sets")
    @classmethod
    def validate_strategy_sets(cls, v: list[StrategySetDefinition]) -> list[StrategySetDefinition]:
        """Ensure strategy set IDs are unique."""
        ids = [ss.id for ss in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate strategy set IDs: {duplicates}")
        return v


# ==================== Aliases for backward compatibility ====================

# Tests and legacy code import these shorter names
Indicator = IndicatorDefinition
Regime = RegimeDefinition
Strategy = StrategyDefinition
StrategyRisk = RiskSettings
