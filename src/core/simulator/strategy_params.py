"""Strategy Parameter Definitions.

Defines configurable parameters for the 5 base strategies:
- Breakout
- Momentum
- Mean Reversion
- Trend Following
- Scalping

Each parameter has a name, type, default value, range, and description.
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

    @classmethod
    def display_names(cls) -> dict[str, str]:
        """Get mapping of enum values to display names."""
        return {
            cls.BREAKOUT.value: "Breakout",
            cls.MOMENTUM.value: "Momentum",
            cls.MEAN_REVERSION.value: "Mean Reversion",
            cls.TREND_FOLLOWING.value: "Trend Following",
            cls.SCALPING.value: "Scalping",
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


# ============================================================================
# STRATEGY PARAMETER REGISTRY
# ============================================================================

STRATEGY_PARAMETER_REGISTRY: dict[StrategyName, StrategyParameterConfig] = {
    # -------------------------------------------------------------------------
    # BREAKOUT STRATEGY
    # -------------------------------------------------------------------------
    StrategyName.BREAKOUT: StrategyParameterConfig(
        strategy_name=StrategyName.BREAKOUT,
        display_name="Breakout",
        description="Breakout strategy using support/resistance levels and volume confirmation.",
        parameters=[
            ParameterDefinition(
                name="sr_window",
                display_name="S/R Window",
                param_type="int",
                default=20,
                min_value=10,
                max_value=50,
                step=5,
                description="Window size for support/resistance detection",
            ),
            ParameterDefinition(
                name="sr_levels",
                display_name="S/R Levels",
                param_type="int",
                default=3,
                min_value=1,
                max_value=5,
                step=1,
                description="Number of support/resistance levels to detect",
            ),
            ParameterDefinition(
                name="atr_period",
                display_name="ATR Period",
                param_type="int",
                default=14,
                min_value=5,
                max_value=30,
                step=1,
                description="Period for Average True Range calculation",
            ),
            ParameterDefinition(
                name="adx_period",
                display_name="ADX Period",
                param_type="int",
                default=14,
                min_value=5,
                max_value=30,
                step=1,
                description="Period for ADX trend strength indicator",
            ),
            ParameterDefinition(
                name="adx_threshold",
                display_name="ADX Threshold",
                param_type="int",
                default=25,
                min_value=15,
                max_value=40,
                step=5,
                description="Minimum ADX value for trend confirmation",
            ),
            ParameterDefinition(
                name="volume_ratio",
                display_name="Volume Ratio",
                param_type="float",
                default=1.5,
                min_value=1.0,
                max_value=3.0,
                step=0.1,
                description="Required volume ratio above average",
            ),
            ParameterDefinition(
                name="price_change_pct",
                display_name="Min Price Change %",
                param_type="float",
                default=0.01,
                min_value=0.005,
                max_value=0.05,
                step=0.005,
                description="Minimum price change percentage for breakout",
            ),
        ],
    ),
    # -------------------------------------------------------------------------
    # MOMENTUM STRATEGY
    # -------------------------------------------------------------------------
    StrategyName.MOMENTUM: StrategyParameterConfig(
        strategy_name=StrategyName.MOMENTUM,
        display_name="Momentum",
        description="Momentum strategy using ROC, MOM, OBV, and RSI indicators.",
        parameters=[
            ParameterDefinition(
                name="roc_period",
                display_name="ROC Period",
                param_type="int",
                default=10,
                min_value=5,
                max_value=20,
                step=1,
                description="Period for Rate of Change indicator",
            ),
            ParameterDefinition(
                name="mom_period",
                display_name="Momentum Period",
                param_type="int",
                default=10,
                min_value=5,
                max_value=20,
                step=1,
                description="Period for Momentum indicator",
            ),
            ParameterDefinition(
                name="rsi_period",
                display_name="RSI Period",
                param_type="int",
                default=14,
                min_value=7,
                max_value=21,
                step=1,
                description="Period for RSI calculation",
            ),
            ParameterDefinition(
                name="roc_threshold",
                display_name="ROC Threshold",
                param_type="float",
                default=5.0,
                min_value=2.0,
                max_value=10.0,
                step=1.0,
                description="Minimum ROC value for entry",
            ),
            ParameterDefinition(
                name="obv_change_threshold",
                display_name="OBV Change %",
                param_type="float",
                default=5.0,
                min_value=2.0,
                max_value=15.0,
                step=1.0,
                description="Minimum OBV change percentage",
            ),
            ParameterDefinition(
                name="rsi_lower",
                display_name="RSI Lower",
                param_type="int",
                default=50,
                min_value=40,
                max_value=60,
                step=5,
                description="Lower RSI threshold for entry",
            ),
            ParameterDefinition(
                name="rsi_upper",
                display_name="RSI Upper",
                param_type="int",
                default=80,
                min_value=70,
                max_value=90,
                step=5,
                description="Upper RSI threshold for entry",
            ),
            ParameterDefinition(
                name="rsi_exit_threshold",
                display_name="RSI Exit",
                param_type="int",
                default=85,
                min_value=75,
                max_value=95,
                step=5,
                description="RSI threshold for exit signal",
            ),
        ],
    ),
    # -------------------------------------------------------------------------
    # MEAN REVERSION STRATEGY
    # -------------------------------------------------------------------------
    StrategyName.MEAN_REVERSION: StrategyParameterConfig(
        strategy_name=StrategyName.MEAN_REVERSION,
        display_name="Mean Reversion",
        description="Mean reversion strategy using Bollinger Bands and RSI for oversold/overbought conditions.",
        parameters=[
            ParameterDefinition(
                name="bb_period",
                display_name="BB Period",
                param_type="int",
                default=20,
                min_value=10,
                max_value=40,
                step=5,
                description="Period for Bollinger Bands",
            ),
            ParameterDefinition(
                name="bb_std",
                display_name="BB Std Dev",
                param_type="float",
                default=2.0,
                min_value=1.5,
                max_value=3.0,
                step=0.25,
                description="Standard deviation multiplier for Bollinger Bands",
            ),
            ParameterDefinition(
                name="rsi_period",
                display_name="RSI Period",
                param_type="int",
                default=14,
                min_value=7,
                max_value=21,
                step=1,
                description="Period for RSI calculation",
            ),
            ParameterDefinition(
                name="rsi_oversold",
                display_name="RSI Oversold",
                param_type="int",
                default=30,
                min_value=20,
                max_value=40,
                step=5,
                description="RSI threshold for oversold condition",
            ),
            ParameterDefinition(
                name="rsi_overbought",
                display_name="RSI Overbought",
                param_type="int",
                default=70,
                min_value=60,
                max_value=80,
                step=5,
                description="RSI threshold for overbought condition",
            ),
            ParameterDefinition(
                name="bb_percent_entry",
                display_name="BB% Entry",
                param_type="float",
                default=0.1,
                min_value=0.0,
                max_value=0.3,
                step=0.05,
                description="Maximum BB% for entry (0=lower band, 1=upper band)",
            ),
            ParameterDefinition(
                name="bb_percent_exit",
                display_name="BB% Exit",
                param_type="float",
                default=0.9,
                min_value=0.7,
                max_value=1.0,
                step=0.05,
                description="Minimum BB% for exit",
            ),
        ],
    ),
    # -------------------------------------------------------------------------
    # TREND FOLLOWING STRATEGY
    # -------------------------------------------------------------------------
    StrategyName.TREND_FOLLOWING: StrategyParameterConfig(
        strategy_name=StrategyName.TREND_FOLLOWING,
        display_name="Trend Following",
        description="Trend following strategy using SMA crossovers, RSI, and MACD confirmation.",
        parameters=[
            ParameterDefinition(
                name="sma_fast",
                display_name="SMA Fast",
                param_type="int",
                default=50,
                min_value=20,
                max_value=100,
                step=10,
                description="Period for fast Simple Moving Average",
            ),
            ParameterDefinition(
                name="sma_slow",
                display_name="SMA Slow",
                param_type="int",
                default=200,
                min_value=100,
                max_value=300,
                step=20,
                description="Period for slow Simple Moving Average",
            ),
            ParameterDefinition(
                name="rsi_period",
                display_name="RSI Period",
                param_type="int",
                default=14,
                min_value=7,
                max_value=21,
                step=1,
                description="Period for RSI calculation",
            ),
            ParameterDefinition(
                name="rsi_upper_limit",
                display_name="RSI Upper Limit",
                param_type="int",
                default=70,
                min_value=60,
                max_value=80,
                step=5,
                description="Maximum RSI for entry (avoid overbought)",
            ),
            ParameterDefinition(
                name="rsi_lower_limit",
                display_name="RSI Lower Limit",
                param_type="int",
                default=30,
                min_value=20,
                max_value=40,
                step=5,
                description="Minimum RSI for exit signal",
            ),
            ParameterDefinition(
                name="macd_fast",
                display_name="MACD Fast",
                param_type="int",
                default=12,
                min_value=8,
                max_value=16,
                step=1,
                description="Fast period for MACD",
            ),
            ParameterDefinition(
                name="macd_slow",
                display_name="MACD Slow",
                param_type="int",
                default=26,
                min_value=20,
                max_value=32,
                step=2,
                description="Slow period for MACD",
            ),
            ParameterDefinition(
                name="macd_signal",
                display_name="MACD Signal",
                param_type="int",
                default=9,
                min_value=7,
                max_value=12,
                step=1,
                description="Signal period for MACD",
            ),
        ],
    ),
    # -------------------------------------------------------------------------
    # SCALPING STRATEGY
    # -------------------------------------------------------------------------
    StrategyName.SCALPING: StrategyParameterConfig(
        strategy_name=StrategyName.SCALPING,
        display_name="Scalping",
        description="High-frequency scalping strategy using EMA crossovers, VWAP, and Stochastic.",
        parameters=[
            ParameterDefinition(
                name="ema_fast",
                display_name="EMA Fast",
                param_type="int",
                default=5,
                min_value=3,
                max_value=10,
                step=1,
                description="Period for fast EMA",
            ),
            ParameterDefinition(
                name="ema_slow",
                display_name="EMA Slow",
                param_type="int",
                default=9,
                min_value=7,
                max_value=15,
                step=1,
                description="Period for slow EMA",
            ),
            ParameterDefinition(
                name="stoch_k",
                display_name="Stochastic K",
                param_type="int",
                default=5,
                min_value=3,
                max_value=10,
                step=1,
                description="K period for Stochastic oscillator",
            ),
            ParameterDefinition(
                name="stoch_d",
                display_name="Stochastic D",
                param_type="int",
                default=3,
                min_value=2,
                max_value=5,
                step=1,
                description="D period for Stochastic oscillator",
            ),
            ParameterDefinition(
                name="stoch_upper",
                display_name="Stoch Upper",
                param_type="int",
                default=80,
                min_value=70,
                max_value=90,
                step=5,
                description="Upper Stochastic threshold",
            ),
            ParameterDefinition(
                name="stoch_lower",
                display_name="Stoch Lower",
                param_type="int",
                default=20,
                min_value=10,
                max_value=30,
                step=5,
                description="Lower Stochastic threshold",
            ),
            ParameterDefinition(
                name="max_spread_pct",
                display_name="Max Spread %",
                param_type="float",
                default=0.5,
                min_value=0.1,
                max_value=1.0,
                step=0.1,
                description="Maximum allowed spread percentage",
            ),
            ParameterDefinition(
                name="min_hold_seconds",
                display_name="Min Hold (sec)",
                param_type="int",
                default=60,
                min_value=30,
                max_value=300,
                step=30,
                description="Minimum holding time in seconds",
            ),
        ],
    ),
}


def get_strategy_parameters(strategy: StrategyName | str) -> StrategyParameterConfig:
    """Get parameter configuration for a strategy.

    Args:
        strategy: Strategy name (enum or string)

    Returns:
        StrategyParameterConfig for the strategy

    Raises:
        KeyError: If strategy not found
    """
    if isinstance(strategy, str):
        strategy = StrategyName(strategy)
    return STRATEGY_PARAMETER_REGISTRY[strategy]


def get_default_parameters(strategy: StrategyName | str) -> dict[str, Any]:
    """Get default parameter values for a strategy.

    Args:
        strategy: Strategy name (enum or string)

    Returns:
        Dictionary of parameter names to default values
    """
    config = get_strategy_parameters(strategy)
    return config.get_defaults()
