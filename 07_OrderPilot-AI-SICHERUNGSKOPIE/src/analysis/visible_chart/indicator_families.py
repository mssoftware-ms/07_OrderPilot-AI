"""Indicator Families for Entry Optimizer.

Defines the candidate space of indicators and their parameter ranges
for optimization. Each family represents a category of technical indicators.

Phase 2.1: Kandidatenraum definieren
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IndicatorFamily(str, Enum):
    """Available indicator families."""

    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    MEAN_REVERSION = "mean_reversion"
    SQUEEZE = "squeeze"


@dataclass
class ParameterRange:
    """Defines a parameter's valid range for optimization.

    Attributes:
        name: Parameter name.
        min_val: Minimum value.
        max_val: Maximum value.
        step: Step size for discrete search.
        default: Default value.
        param_type: 'int' or 'float'.
    """

    name: str
    min_val: float
    max_val: float
    step: float = 1.0
    default: float = 0.0
    param_type: str = "float"

    def sample_values(self, n_samples: int = 5) -> list[float]:
        """Generate sample values within range.

        Args:
            n_samples: Number of samples to generate.

        Returns:
            List of sample values.
        """
        if n_samples <= 1:
            return [self.default]

        step = (self.max_val - self.min_val) / (n_samples - 1)
        values = [self.min_val + i * step for i in range(n_samples)]

        if self.param_type == "int":
            values = [int(round(v)) for v in values]

        return values

    def random_value(self) -> float:
        """Generate random value within range."""
        import random

        if self.param_type == "int":
            return random.randint(int(self.min_val), int(self.max_val))
        return random.uniform(self.min_val, self.max_val)


@dataclass
class IndicatorConfig:
    """Configuration for a single indicator.

    Attributes:
        name: Indicator name.
        family: Which family it belongs to.
        parameters: Dict of parameter name -> ParameterRange.
        role: Entry trigger, filter, or confirmation.
        weight_range: Min/max weight for scoring.
    """

    name: str
    family: IndicatorFamily
    parameters: dict[str, ParameterRange] = field(default_factory=dict)
    role: str = "filter"  # trigger, filter, confirmation
    weight_range: tuple[float, float] = (0.1, 1.0)

    def get_default_params(self) -> dict[str, float]:
        """Get default parameter values."""
        return {name: p.default for name, p in self.parameters.items()}

    def randomize_params(self) -> dict[str, float]:
        """Generate random parameter values."""
        return {name: p.random_value() for name, p in self.parameters.items()}


# ============================================================================
# CANDIDATE SPACE: Indicator Families with Parameter Ranges
# ============================================================================

TREND_INDICATORS: list[IndicatorConfig] = [
    IndicatorConfig(
        name="SMA_Cross",
        family=IndicatorFamily.TREND,
        parameters={
            "fast_period": ParameterRange("fast_period", 5, 20, 1, 10, "int"),
            "slow_period": ParameterRange("slow_period", 15, 50, 5, 20, "int"),
        },
        role="trigger",
    ),
    IndicatorConfig(
        name="EMA_Trend",
        family=IndicatorFamily.TREND,
        parameters={
            "period": ParameterRange("period", 10, 50, 5, 20, "int"),
            "threshold": ParameterRange("threshold", 0.001, 0.01, 0.001, 0.005),
        },
        role="filter",
    ),
    IndicatorConfig(
        name="ADX_Trend",
        family=IndicatorFamily.TREND,
        parameters={
            "period": ParameterRange("period", 10, 30, 2, 14, "int"),
            "threshold": ParameterRange("threshold", 20, 40, 5, 25),
        },
        role="filter",
    ),
]

MOMENTUM_INDICATORS: list[IndicatorConfig] = [
    IndicatorConfig(
        name="RSI",
        family=IndicatorFamily.MOMENTUM,
        parameters={
            "period": ParameterRange("period", 7, 21, 2, 14, "int"),
            "oversold": ParameterRange("oversold", 20, 35, 5, 30),
            "overbought": ParameterRange("overbought", 65, 80, 5, 70),
        },
        role="trigger",
    ),
    IndicatorConfig(
        name="MACD",
        family=IndicatorFamily.MOMENTUM,
        parameters={
            "fast": ParameterRange("fast", 8, 15, 1, 12, "int"),
            "slow": ParameterRange("slow", 20, 30, 2, 26, "int"),
            "signal": ParameterRange("signal", 7, 12, 1, 9, "int"),
        },
        role="confirmation",
    ),
    IndicatorConfig(
        name="Stochastic",
        family=IndicatorFamily.MOMENTUM,
        parameters={
            "k_period": ParameterRange("k_period", 10, 20, 2, 14, "int"),
            "d_period": ParameterRange("d_period", 3, 5, 1, 3, "int"),
            "oversold": ParameterRange("oversold", 15, 25, 5, 20),
            "overbought": ParameterRange("overbought", 75, 85, 5, 80),
        },
        role="trigger",
    ),
]

VOLATILITY_INDICATORS: list[IndicatorConfig] = [
    IndicatorConfig(
        name="ATR",
        family=IndicatorFamily.VOLATILITY,
        parameters={
            "period": ParameterRange("period", 10, 20, 2, 14, "int"),
            "multiplier": ParameterRange("multiplier", 1.5, 3.0, 0.5, 2.0),
        },
        role="filter",
    ),
    IndicatorConfig(
        name="BB_Width",
        family=IndicatorFamily.VOLATILITY,
        parameters={
            "period": ParameterRange("period", 15, 25, 5, 20, "int"),
            "std_dev": ParameterRange("std_dev", 1.5, 2.5, 0.5, 2.0),
        },
        role="filter",
    ),
]

MEAN_REVERSION_INDICATORS: list[IndicatorConfig] = [
    IndicatorConfig(
        name="BB_Bands",
        family=IndicatorFamily.MEAN_REVERSION,
        parameters={
            "period": ParameterRange("period", 15, 25, 5, 20, "int"),
            "std_dev": ParameterRange("std_dev", 1.5, 2.5, 0.5, 2.0),
            "entry_pct": ParameterRange("entry_pct", 0.8, 1.0, 0.05, 0.95),
        },
        role="trigger",
    ),
    IndicatorConfig(
        name="Keltner",
        family=IndicatorFamily.MEAN_REVERSION,
        parameters={
            "period": ParameterRange("period", 15, 25, 5, 20, "int"),
            "atr_mult": ParameterRange("atr_mult", 1.0, 2.0, 0.25, 1.5),
        },
        role="trigger",
    ),
]

SQUEEZE_INDICATORS: list[IndicatorConfig] = [
    IndicatorConfig(
        name="BB_KC_Squeeze",
        family=IndicatorFamily.SQUEEZE,
        parameters={
            "bb_period": ParameterRange("bb_period", 15, 25, 5, 20, "int"),
            "bb_std": ParameterRange("bb_std", 1.5, 2.5, 0.5, 2.0),
            "kc_period": ParameterRange("kc_period", 15, 25, 5, 20, "int"),
            "kc_mult": ParameterRange("kc_mult", 1.0, 2.0, 0.25, 1.5),
        },
        role="trigger",
    ),
]

VOLUME_INDICATORS: list[IndicatorConfig] = [
    IndicatorConfig(
        name="Volume_MA",
        family=IndicatorFamily.VOLUME,
        parameters={
            "period": ParameterRange("period", 10, 30, 5, 20, "int"),
            "threshold": ParameterRange("threshold", 1.2, 2.0, 0.2, 1.5),
        },
        role="confirmation",
    ),
]


# ============================================================================
# REGIME-BASED CANDIDATE SETS
# ============================================================================

def get_candidates_for_regime(regime: str) -> list[IndicatorConfig]:
    """Get suitable indicator candidates for a given regime.

    Args:
        regime: Market regime (trend_up, trend_down, range, etc.)

    Returns:
        List of suitable indicator configs.
    """
    if regime in ("trend_up", "trend_down"):
        return TREND_INDICATORS + MOMENTUM_INDICATORS + VOLATILITY_INDICATORS
    elif regime == "range":
        return MEAN_REVERSION_INDICATORS + MOMENTUM_INDICATORS + VOLATILITY_INDICATORS
    elif regime == "squeeze":
        return SQUEEZE_INDICATORS + VOLATILITY_INDICATORS + VOLUME_INDICATORS
    elif regime == "high_vol":
        return VOLATILITY_INDICATORS + MOMENTUM_INDICATORS
    else:
        # Conservative: only momentum + volatility
        return MOMENTUM_INDICATORS + VOLATILITY_INDICATORS


def get_all_indicators() -> dict[IndicatorFamily, list[IndicatorConfig]]:
    """Get all available indicators grouped by family."""
    return {
        IndicatorFamily.TREND: TREND_INDICATORS,
        IndicatorFamily.MOMENTUM: MOMENTUM_INDICATORS,
        IndicatorFamily.VOLATILITY: VOLATILITY_INDICATORS,
        IndicatorFamily.MEAN_REVERSION: MEAN_REVERSION_INDICATORS,
        IndicatorFamily.SQUEEZE: SQUEEZE_INDICATORS,
        IndicatorFamily.VOLUME: VOLUME_INDICATORS,
    }


@dataclass
class OptimizableSet:
    """A complete set of indicators for optimization.

    Phase 2.2: Set-Definition

    Attributes:
        indicators: Selected indicators with their params.
        scoring_weights: Weight for each indicator in final score.
        postprocess_config: Cooldown, rate limit, etc.
        stop_config: SL/TP parameters.
    """

    indicators: list[tuple[IndicatorConfig, dict[str, float]]] = field(
        default_factory=list
    )
    scoring_weights: dict[str, float] = field(default_factory=dict)
    postprocess_config: dict[str, Any] = field(default_factory=lambda: {
        "cooldown_minutes": 5,
        "max_signals_per_hour": 6,
        "min_confidence": 0.5,
    })
    stop_config: dict[str, Any] = field(default_factory=lambda: {
        "atr_multiplier": 2.0,
        "max_risk_pct": 1.0,
    })

    def to_indicator_set(self, name: str, regime: str, score: float):
        """Convert to IndicatorSet for display.

        Args:
            name: Set name.
            regime: Regime this set is optimized for.
            score: Optimization score.

        Returns:
            IndicatorSet for UI display.
        """
        from .types import IndicatorSet, RegimeType

        params = {}
        families = []

        for config, param_values in self.indicators:
            params[config.name] = param_values
            if config.family.value not in families:
                families.append(config.family.value)

        params["postprocess"] = self.postprocess_config
        params["stop"] = self.stop_config

        return IndicatorSet(
            name=name,
            regime=RegimeType(regime),
            score=score,
            parameters=params,
            families=families,
            description=f"Optimized for {regime} regime",
        )
