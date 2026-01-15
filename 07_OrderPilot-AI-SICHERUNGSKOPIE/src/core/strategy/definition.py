"""Strategy Definition Models for Declarative Trading Strategies.

Provides Pydantic models for defining trading strategies in a declarative,
TradingView/Pine-Script-like manner. Strategies can be defined in YAML/JSON
and compiled into executable Backtrader strategies.

Example:
    >>> strategy = StrategyDefinition(
    ...     name="SMA Crossover",
    ...     indicators=[
    ...         IndicatorConfig(type="SMA", params={"period": 20}, alias="sma_fast"),
    ...         IndicatorConfig(type="SMA", params={"period": 50}, alias="sma_slow")
    ...     ],
    ...     entry_long=Condition(
    ...         left="sma_fast",
    ...         operator="crosses_above",
    ...         right="sma_slow"
    ...     ),
    ...     exit_long=Condition(
    ...         left="sma_fast",
    ...         operator="crosses_below",
    ...         right="sma_slow"
    ...     )
    ... )
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Discriminator, Field, Tag, field_validator, model_validator


class IndicatorType(str, Enum):
    """Supported technical indicator types."""

    # Moving Averages
    SMA = "SMA"  # Simple Moving Average
    EMA = "EMA"  # Exponential Moving Average
    WMA = "WMA"  # Weighted Moving Average
    DEMA = "DEMA"  # Double Exponential Moving Average
    TEMA = "TEMA"  # Triple Exponential Moving Average

    # Momentum Indicators
    RSI = "RSI"  # Relative Strength Index
    MACD = "MACD"  # Moving Average Convergence Divergence
    STOCH = "STOCH"  # Stochastic Oscillator
    CCI = "CCI"  # Commodity Channel Index
    MOM = "MOM"  # Momentum
    ROC = "ROC"  # Rate of Change

    # Volatility Indicators
    ATR = "ATR"  # Average True Range
    BBANDS = "BBANDS"  # Bollinger Bands
    KC = "KC"  # Keltner Channels
    STDDEV = "STDDEV"  # Standard Deviation

    # Volume Indicators
    OBV = "OBV"  # On-Balance Volume
    VWAP = "VWAP"  # Volume Weighted Average Price
    AD = "AD"  # Accumulation/Distribution
    CMF = "CMF"  # Chaikin Money Flow

    # Trend Indicators
    ADX = "ADX"  # Average Directional Index
    AROON = "AROON"  # Aroon Indicator
    PSAR = "PSAR"  # Parabolic SAR
    SUPERTREND = "SUPERTREND"  # SuperTrend

    # Other
    PIVOT = "PIVOT"  # Pivot Points
    VWMA = "VWMA"  # Volume Weighted Moving Average


class ComparisonOperator(str, Enum):
    """Comparison operators for conditions."""

    GT = ">"  # Greater than
    GTE = ">="  # Greater than or equal
    LT = "<"  # Less than
    LTE = "<="  # Less than or equal
    EQ = "=="  # Equal
    NEQ = "!="  # Not equal

    # Special operators
    CROSSES_ABOVE = "crosses_above"  # Value crosses above threshold
    CROSSES_BELOW = "crosses_below"  # Value crosses below threshold
    CROSSES = "crosses"  # Value crosses threshold (either direction)
    INSIDE = "inside"  # Value inside range [low, high]
    OUTSIDE = "outside"  # Value outside range [low, high]


class LogicOperator(str, Enum):
    """Logic operators for combining conditions."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class IndicatorConfig(BaseModel):
    """Configuration for a technical indicator.

    Attributes:
        type: Indicator type (SMA, RSI, MACD, etc.)
        params: Indicator-specific parameters (e.g., period, deviation)
        alias: Unique identifier for referencing in conditions
        source: Data source field (default: "close")
        plot: Whether to plot this indicator in charts

    Example:
        >>> IndicatorConfig(
        ...     type="SMA",
        ...     params={"period": 20},
        ...     alias="sma_fast",
        ...     source="close"
        ... )
    """

    type: IndicatorType
    params: dict[str, Any] = Field(default_factory=dict)
    alias: str = Field(..., min_length=1, max_length=50)
    source: str = "close"  # close, open, high, low, volume, etc.
    plot: bool = True

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, v: str) -> str:
        """Validate alias format (alphanumeric + underscore)."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                f"Alias must be alphanumeric with underscores: {v}"
            )
        return v

    class Config:
        """Pydantic config."""

        use_enum_values = True


class Condition(BaseModel):
    """Single condition for strategy logic.

    Attributes:
        type: Discriminator field (always "condition")
        left: Left operand (indicator alias or numeric value)
        operator: Comparison operator
        right: Right operand (indicator alias or numeric value)
        description: Optional human-readable description

    Example:
        >>> Condition(
        ...     left="sma_fast",
        ...     operator="crosses_above",
        ...     right="sma_slow",
        ...     description="Fast SMA crosses above slow SMA"
        ... )
    """

    type: Literal["condition"] = "condition"
    left: str | float
    operator: ComparisonOperator
    right: str | float | list[float] | None = None  # list for inside/outside operators
    right_formula: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_range_operators(self) -> Condition:
        """Validate that conditions have a usable right operand."""
        if self.right is None and self.right_formula:
            self.right = self.right_formula

        if self.right is None:
            raise ValueError("Condition requires 'right' or 'right_formula'")

        if self.operator in (ComparisonOperator.INSIDE, ComparisonOperator.OUTSIDE):
            if not isinstance(self.right, list) or len(self.right) != 2:
                raise ValueError(
                    f"Operator '{self.operator}' requires right operand "
                    f"to be list of 2 floats: [low, high]"
                )
        return self

    class Config:
        """Pydantic config."""

        use_enum_values = True


# Discriminator function for Condition | LogicGroup union
def _get_condition_type(v: Any) -> str:
    """Get discriminator value for Condition | LogicGroup union."""
    if isinstance(v, dict):
        value = v.get("type", "condition")
        if value == "composite":
            return "group"
        return value
    return getattr(v, "type", "condition")


class LogicGroup(BaseModel):
    """Group of conditions combined with logic operators.

    Supports recursive nesting for complex logic like:
    (A AND B) OR (C AND D)

    Attributes:
        type: Discriminator field (always "group")
        operator: Logic operator (AND, OR, NOT)
        conditions: List of conditions or nested logic groups
        description: Optional human-readable description

    Example:
        >>> LogicGroup(
        ...     operator="AND",
        ...     conditions=[
        ...         Condition(left="rsi", operator="<", right=30),
        ...         Condition(left="sma_fast", operator=">", right="sma_slow")
        ...     ],
        ...     description="RSI oversold AND bullish crossover"
        ... )
    """

    type: Literal["group", "composite"] = "group"
    operator: LogicOperator
    conditions: list[Annotated[
        Union[
            Annotated[Condition, Tag("condition")],
            Annotated['LogicGroup', Tag("group")]
        ],
        Discriminator(_get_condition_type)
    ]]
    description: str | None = None

    @field_validator("conditions")
    @classmethod
    def validate_conditions_not_empty(cls, v: list) -> list:
        """Validate that conditions list is not empty."""
        if not v:
            raise ValueError("LogicGroup must have at least one condition")
        return v

    @field_validator("type")
    @classmethod
    def normalize_group_type(cls, v: str) -> str:
        """Normalize legacy 'composite' type to 'group'."""
        if v == "composite":
            return "group"
        return v

    @model_validator(mode="after")
    def validate_not_operator(self) -> LogicGroup:
        """Validate that NOT operator has exactly one condition."""
        if self.operator == LogicOperator.NOT and len(self.conditions) != 1:
            raise ValueError("NOT operator must have exactly one condition")
        return self

    class Config:
        """Pydantic config."""

        use_enum_values = True


# Type alias for entry/exit logic with discriminator
EntryExitLogic = Annotated[
    Union[
        Annotated[Condition, Tag("condition")],
        Annotated[LogicGroup, Tag("group")]
    ],
    Discriminator(_get_condition_type)
]


class RiskManagement(BaseModel):
    """Risk management parameters for the strategy.

    Attributes:
        stop_loss_pct: Stop loss as percentage of entry price
        take_profit_pct: Take profit as percentage of entry price
        stop_loss_atr: Stop loss as multiple of ATR
        take_profit_atr: Take profit as multiple of ATR
        trailing_stop_pct: Trailing stop as percentage
        max_position_size_pct: Max position size as % of capital
        max_risk_per_trade_pct: Max risk per trade as % of capital

    Example:
        >>> RiskManagement(
        ...     stop_loss_pct=2.0,
        ...     take_profit_pct=5.0,
        ...     max_risk_per_trade_pct=1.0
        ... )
    """

    # Stop Loss / Take Profit (percentage-based)
    stop_loss_pct: float | None = Field(None, gt=0, le=100)
    take_profit_pct: float | None = Field(None, gt=0, le=1000)

    # Stop Loss / Take Profit (ATR-based)
    stop_loss_atr: float | None = Field(None, gt=0, le=10)
    take_profit_atr: float | None = Field(None, gt=0, le=20)

    # Trailing Stop
    trailing_stop_pct: float | None = Field(None, gt=0, le=100)
    trailing_stop_enabled: bool = False
    trailing_stop_trigger_pct: float | None = Field(None, gt=0, le=100)
    trailing_stop_distance_pct: float | None = Field(None, gt=0, le=100)

    # Position Sizing
    position_size_pct: float | None = Field(None, gt=0, le=100)
    max_position_size_pct: float = Field(100.0, gt=0, le=100)
    max_risk_per_trade_pct: float = Field(2.0, gt=0, le=100)

    @model_validator(mode="after")
    def validate_stop_loss_methods(self) -> RiskManagement:
        """Validate that only one stop loss method is used."""
        sl_methods = [
            self.stop_loss_pct is not None,
            self.stop_loss_atr is not None,
        ]
        if sum(sl_methods) > 1:
            raise ValueError(
                "Only one stop loss method can be used: "
                "stop_loss_pct OR stop_loss_atr"
            )
        return self

    @model_validator(mode="after")
    def validate_take_profit_methods(self) -> RiskManagement:
        """Validate that only one take profit method is used."""
        tp_methods = [
            self.take_profit_pct is not None,
            self.take_profit_atr is not None,
        ]
        if sum(tp_methods) > 1:
            raise ValueError(
                "Only one take profit method can be used: "
                "take_profit_pct OR take_profit_atr"
            )
        return self


class StrategyDefinition(BaseModel):
    """Complete trading strategy definition.

    Attributes:
        name: Strategy name
        version: Strategy version (semantic versioning)
        description: Strategy description
        indicators: List of indicator configurations
        entry_long: Entry condition for long positions
        exit_long: Exit condition for long positions
        entry_short: Entry condition for short positions (optional)
        exit_short: Exit condition for short positions (optional)
        risk_management: Risk management parameters
        meta: Additional metadata (tags, author, etc.)

    Example:
        >>> strategy = StrategyDefinition(
        ...     name="SMA Crossover",
        ...     version="1.0.0",
        ...     indicators=[
        ...         IndicatorConfig(type="SMA", params={"period": 20}, alias="sma_fast"),
        ...         IndicatorConfig(type="SMA", params={"period": 50}, alias="sma_slow")
        ...     ],
        ...     entry_long=Condition(
        ...         left="sma_fast", operator="crosses_above", right="sma_slow"
        ...     ),
        ...     exit_long=Condition(
        ...         left="sma_fast", operator="crosses_below", right="sma_slow"
        ...     ),
        ...     risk_management=RiskManagement(
        ...         stop_loss_pct=2.0,
        ...         take_profit_pct=5.0
        ...     )
        ... )
    """

    # Metadata
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field("1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    description: str | None = None
    category: str | None = None
    author: str | None = None
    asset_class: str | None = None
    recommended_symbols: list[str] = Field(default_factory=list)
    recommended_timeframes: list[str] = Field(default_factory=list)
    notes: str | None = None

    # Indicators
    indicators: list[IndicatorConfig] = Field(default_factory=list)

    # Entry/Exit Logic
    entry_long: EntryExitLogic
    exit_long: EntryExitLogic
    entry_short: EntryExitLogic | None = None
    exit_short: EntryExitLogic | None = None

    # Risk Management
    risk_management: RiskManagement = Field(default_factory=RiskManagement)

    # Additional Metadata
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("indicators")
    @classmethod
    def validate_unique_aliases(cls, v: list[IndicatorConfig]) -> list[IndicatorConfig]:
        """Validate that all indicator aliases are unique."""
        aliases = [ind.alias for ind in v]
        if len(aliases) != len(set(aliases)):
            duplicates = [alias for alias in aliases if aliases.count(alias) > 1]
            raise ValueError(f"Duplicate indicator aliases: {set(duplicates)}")
        return v

    @model_validator(mode="after")
    def validate_condition_references(self) -> StrategyDefinition:
        """Validate that all condition references point to valid indicators."""
        indicator_aliases = {ind.alias for ind in self.indicators}

        # Add built-in references
        valid_refs = indicator_aliases | {"close", "open", "high", "low", "volume"}

        # Extract all condition references
        def extract_refs(value: str) -> set[str]:
            return set(re.findall(r"[A-Za-z_][A-Za-z0-9_\\.]*", value))

        def get_refs_from_condition(cond: Condition | LogicGroup) -> set[str]:
            refs = set()
            if isinstance(cond, Condition):
                if isinstance(cond.left, str):
                    if any(ch in cond.left for ch in "+-*/()"):
                        refs.update(extract_refs(cond.left))
                    else:
                        refs.add(cond.left)
                if isinstance(cond.right, str):
                    if any(ch in cond.right for ch in "+-*/()"):
                        refs.update(extract_refs(cond.right))
                    else:
                        refs.add(cond.right)
                if isinstance(cond.right_formula, str):
                    if any(ch in cond.right_formula for ch in "+-*/()"):
                        refs.update(extract_refs(cond.right_formula))
                    else:
                        refs.add(cond.right_formula)
            elif isinstance(cond, LogicGroup):
                for c in cond.conditions:
                    refs.update(get_refs_from_condition(c))
            return refs

        all_refs = set()
        for condition_list in [
            self.entry_long,
            self.exit_long,
            self.entry_short,
            self.exit_short,
        ]:
            if condition_list:
                all_refs.update(get_refs_from_condition(condition_list))

        # Filter out numeric strings (they're valid literals)
        non_numeric_refs = {
            ref for ref in all_refs
            if not (isinstance(ref, str) and ref.replace(".", "", 1).replace("-", "", 1).isdigit())
        }

        # Check for invalid references
        normalized_refs = {
            ref.split(".", 1)[0] if isinstance(ref, str) else ref
            for ref in non_numeric_refs
        }
        invalid_refs = normalized_refs - valid_refs
        if invalid_refs:
            raise ValueError(
                f"Invalid indicator references in conditions: {invalid_refs}. "
                f"Valid indicators: {indicator_aliases}"
            )

        return self

    def get_indicator_by_alias(self, alias: str) -> IndicatorConfig | None:
        """Get indicator configuration by alias.

        Args:
            alias: Indicator alias

        Returns:
            IndicatorConfig or None if not found
        """
        for ind in self.indicators:
            if ind.alias == alias:
                return ind
        return None

    def to_yaml(self) -> str:
        """Export strategy definition as YAML string.

        Returns:
            YAML representation of the strategy
        """
        import yaml

        return yaml.dump(
            self.model_dump(mode="json", exclude_none=True),
            default_flow_style=False,
            sort_keys=False,
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> StrategyDefinition:
        """Load strategy definition from YAML string.

        Args:
            yaml_str: YAML string

        Returns:
            StrategyDefinition instance
        """
        import yaml

        data = yaml.safe_load(yaml_str)
        return cls(**data)

    def to_json_file(self, filepath: str) -> None:
        """Save strategy definition to JSON file.

        Args:
            filepath: Path to JSON file
        """
        with open(filepath, "w") as f:
            f.write(self.model_dump_json(indent=2, exclude_none=True))

    @classmethod
    def from_json_file(cls, filepath: str) -> StrategyDefinition:
        """Load strategy definition from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            StrategyDefinition instance
        """
        with open(filepath, "r") as f:
            return cls.model_validate_json(f.read())


# Type aliases for convenience
EntryExitLogic = Condition | LogicGroup
