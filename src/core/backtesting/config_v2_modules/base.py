"""Backtesting Configuration V2 - Base Types

Foundational types for the backtesting configuration system:
- Enums (Strategy types, stop/exit types, optimization methods, etc.)
- Optimizable parameter types (OptimizableFloat, OptimizableInt)

These types are used throughout the config system for type safety
and parameter optimization support.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==================== ENUMS ====================

class StrategyType(str, Enum):
    """Strategie-Typen."""
    TRENDFOLLOWING = "trendfollowing"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    HYBRID = "hybrid"


class WeightPresetName(str, Enum):
    """Vordefinierte Weight-Presets."""
    W0 = "W0"  # Default/Balanced
    W1 = "W1"  # Trend/ADX-heavy
    W2 = "W2"  # Momentum/Volatility-heavy
    CUSTOM = "custom"


class DirectionBias(str, Enum):
    """Handelsrichtungs-Bias."""
    BOTH = "BOTH"
    LONG_ONLY = "LONG_ONLY"
    SHORT_ONLY = "SHORT_ONLY"


class ScenarioType(str, Enum):
    """Szenario-Typ."""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"


class AssetClass(str, Enum):
    """Asset-Klassen."""
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FOREX = "forex"
    FUTURES = "futures"


class StopLossType(str, Enum):
    """Stop-Loss Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"
    STRUCTURE_BASED = "structure_based"


class TakeProfitType(str, Enum):
    """Take-Profit Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"
    RR_RATIO = "rr_ratio"
    LEVEL_BASED = "level_based"


class TrailingType(str, Enum):
    """Trailing Stop Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"


class SlippageMethod(str, Enum):
    """Slippage-Berechnungsmethoden."""
    FIXED_BPS = "fixed_bps"
    ATR_BASED = "atr_based"
    VOLUME_ADJUSTED = "volume_adjusted"


class OptimizationMethod(str, Enum):
    """Optimierungsmethoden."""
    GRID = "grid"
    RANDOM = "random"
    BAYESIAN = "bayesian"


class TargetMetric(str, Enum):
    """Ziel-Metriken fuer Optimierung."""
    EXPECTANCY = "expectancy"
    PROFIT_FACTOR = "profit_factor"
    SHARPE = "sharpe"
    SORTINO = "sortino"
    CALMAR = "calmar"
    MAX_DD = "max_dd"


# ==================== OPTIMIZABLE TYPES ====================

@dataclass
class OptimizableFloat:
    """Float-Parameter der optimiert werden kann."""
    value: float
    optimize: bool = False
    range: Optional[List[float]] = None  # Diskrete Werte
    min: Optional[float] = None          # Kontinuierlicher Bereich
    max: Optional[float] = None
    step: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"value": self.value, "optimize": self.optimize}
        if self.range:
            result["range"] = self.range
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        if self.step is not None:
            result["step"] = self.step
        return result

    @classmethod
    def from_dict(cls, data: Any) -> "OptimizableFloat":
        """Create OptimizableFloat from dict or number."""
        if isinstance(data, (int, float)):
            return cls(value=float(data))
        return cls(
            value=data.get("value", 0.0),
            optimize=data.get("optimize", False),
            range=data.get("range"),
            min=data.get("min"),
            max=data.get("max"),
            step=data.get("step")
        )

    def get_search_space(self) -> List[float]:
        """Gibt den Suchraum fuer Optimierung zurueck."""
        if not self.optimize:
            return [self.value]
        if self.range:
            return self.range
        if self.min is not None and self.max is not None:
            step = self.step or (self.max - self.min) / 10
            values = []
            v = self.min
            while v <= self.max:
                values.append(round(v, 6))
                v += step
            return values
        return [self.value]


@dataclass
class OptimizableInt:
    """Integer-Parameter der optimiert werden kann."""
    value: int
    optimize: bool = False
    range: Optional[List[int]] = None
    min: Optional[int] = None
    max: Optional[int] = None
    step: int = 1

    def to_dict(self) -> Dict[str, Any]:
        result = {"value": self.value, "optimize": self.optimize}
        if self.range:
            result["range"] = self.range
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        if self.step != 1:
            result["step"] = self.step
        return result

    @classmethod
    def from_dict(cls, data: Any) -> "OptimizableInt":
        """Create OptimizableInt from dict or number."""
        if isinstance(data, int):
            return cls(value=data)
        return cls(
            value=data.get("value", 0),
            optimize=data.get("optimize", False),
            range=data.get("range"),
            min=data.get("min"),
            max=data.get("max"),
            step=data.get("step", 1)
        )

    def get_search_space(self) -> List[int]:
        """Gibt den Suchraum fuer Optimierung zurueck."""
        if not self.optimize:
            return [self.value]
        if self.range:
            return self.range
        if self.min is not None and self.max is not None:
            return list(range(self.min, self.max + 1, self.step))
        return [self.value]
