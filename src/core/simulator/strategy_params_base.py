"""Strategy parameter core types.

Holds enums and dataclasses used by the strategy parameter registry.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class StrategyName(str, Enum):
    """Available strategy names."""

    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    SCALPING = "scalping"
    # New Strategies
    BOLLINGER_SQUEEZE = "bollinger_squeeze"
    TREND_PULLBACK = "trend_pullback"
    OPENING_RANGE = "opening_range"
    REGIME_HYBRID = "regime_hybrid"
    SIDEWAYS_RANGE = "sideways_range"

    @classmethod
    def display_names(cls) -> dict[str, str]:
        """Get mapping of enum values to display names."""
        return {
            cls.BREAKOUT.value: "Breakout",
            cls.MOMENTUM.value: "Momentum",
            cls.MEAN_REVERSION.value: "Mean Reversion",
            cls.TREND_FOLLOWING.value: "Trend Following",
            cls.SCALPING.value: "Scalping",
            cls.BOLLINGER_SQUEEZE.value: "Bollinger Squeeze",
            cls.TREND_PULLBACK.value: "Trend Pullback",
            cls.OPENING_RANGE.value: "Opening Range",
            cls.REGIME_HYBRID.value: "Regime Hybrid",
            cls.SIDEWAYS_RANGE.value: "Sideways Range",
        }


@dataclass
class ParameterDefinition:
    """Definition of a single configurable parameter."""

    name: str
    display_name: str
    param_type: Literal["int", "float", "bool"]
    default: Any
    min_value: Any | None = None
    max_value: Any | None = None
    step: Any | None = None
    description: str = ""

    def validate(self, value: Any) -> bool:
        """Validate a value against this parameter definition."""
        if self.param_type == "bool":
            return isinstance(value, bool)

        if self.param_type == "int":
            if not isinstance(value, int):
                return False
        elif self.param_type == "float":
            if not isinstance(value, (int, float)):
                return False

        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False

        return True

    def get_range_values(self) -> list[Any]:
        """Get list of values for grid search."""
        if self.param_type == "bool":
            return [True, False]

        if self.min_value is None or self.max_value is None:
            return [self.default]

        step = self.step or (1 if self.param_type == "int" else 0.1)
        values = []
        current = self.min_value
        while current <= self.max_value:
            if self.param_type == "int":
                values.append(int(current))
            else:
                values.append(round(current, 4))
            current += step

        return values


@dataclass
class StrategyParameterConfig:
    """Configuration for a strategy's parameters."""

    strategy_name: StrategyName
    display_name: str
    description: str
    parameters: list[ParameterDefinition] = field(default_factory=list)

    def get_defaults(self) -> dict[str, Any]:
        """Get default values for all parameters."""
        return {p.name: p.default for p in self.parameters}

    def get_parameter(self, name: str) -> ParameterDefinition | None:
        """Get a specific parameter by name."""
        for p in self.parameters:
            if p.name == name:
                return p
        return None
