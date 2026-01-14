"""
Backtesting Configuration - Optimizable parameter types + WeightPreset
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

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
    def from_dict(cls, data: Union[Dict[str, Any], float]) -> "OptimizableFloat":
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
    def from_dict(cls, data: Union[Dict[str, Any], int]) -> "OptimizableInt":
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


# =============================================================================
# WEIGHT PRESETS
# =============================================================================


@dataclass
class WeightPreset:
    """Vordefinierte Weight-Kombination."""
    trend: float = 0.25
    rsi: float = 0.15
    macd: float = 0.20
    adx: float = 0.15
    vol: float = 0.10
    volume: float = 0.15

    def to_dict(self) -> Dict[str, float]:
        return {
            "trend": self.trend,
            "rsi": self.rsi,
            "macd": self.macd,
            "adx": self.adx,
            "vol": self.vol,
            "volume": self.volume
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "WeightPreset":
        return cls(
            trend=data.get("trend", 0.25),
            rsi=data.get("rsi", 0.15),
            macd=data.get("macd", 0.20),
            adx=data.get("adx", 0.15),
            vol=data.get("vol", 0.10),
            volume=data.get("volume", 0.15)
        )

    def validate(self) -> bool:
        """Prueft ob Weights zu 1.0 summieren."""
        total = self.trend + self.rsi + self.macd + self.adx + self.vol + self.volume
        return 0.99 <= total <= 1.01

