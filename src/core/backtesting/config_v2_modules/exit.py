"""Backtesting Configuration V2 - Exit Management

Exit-related configuration classes:
- Stop Loss configuration (ATR-based, percent-based, structure-based)
- Take Profit configuration (ATR-based, percent-based, RR ratio, level-based)
- Trailing Stop configuration (activation, distance, breakeven)
- Partial TP configuration
- Time Stop configuration
- Exit Management aggregator
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .base import (
    OptimizableFloat,
    StopLossType,
    TakeProfitType,
    TrailingType,
)


# ==================== EXIT CONFIGURATION ====================

@dataclass
class StopLossConfig:
    """Stop-Loss Konfiguration."""
    type: StopLossType = StopLossType.ATR_BASED
    atr_multiplier: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.5))
    percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.5))
    structure_buffer_atr: float = 0.2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "atr_multiplier": self.atr_multiplier.to_dict(),
            "percent": self.percent.to_dict(),
            "structure_buffer_atr": self.structure_buffer_atr
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StopLossConfig":
        return cls(
            type=StopLossType(data.get("type", "atr_based")),
            atr_multiplier=OptimizableFloat.from_dict(data.get("atr_multiplier", {"value": 1.5})),
            percent=OptimizableFloat.from_dict(data.get("percent", {"value": 0.5})),
            structure_buffer_atr=data.get("structure_buffer_atr", 0.2)
        )


@dataclass
class TakeProfitConfig:
    """Take-Profit Konfiguration."""
    type: TakeProfitType = TakeProfitType.ATR_BASED
    atr_multiplier: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=2.0))
    percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.5))
    rr_ratio: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=2.0))
    use_level: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "atr_multiplier": self.atr_multiplier.to_dict(),
            "percent": self.percent.to_dict(),
            "rr_ratio": self.rr_ratio.to_dict(),
            "use_level": self.use_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TakeProfitConfig":
        return cls(
            type=TakeProfitType(data.get("type", "atr_based")),
            atr_multiplier=OptimizableFloat.from_dict(data.get("atr_multiplier", {"value": 2.0})),
            percent=OptimizableFloat.from_dict(data.get("percent", {"value": 1.5})),
            rr_ratio=OptimizableFloat.from_dict(data.get("rr_ratio", {"value": 2.0})),
            use_level=data.get("use_level", False)
        )


@dataclass
class TrailingStopConfig:
    """Trailing Stop Konfiguration."""
    enabled: bool = True
    type: TrailingType = TrailingType.ATR_BASED
    move_to_breakeven: bool = True
    activation_atr: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.0))
    activation_percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.5))
    distance_atr: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.6))
    distance_percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.3))
    step_percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.2))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "type": self.type.value,
            "move_to_breakeven": self.move_to_breakeven,
            "activation_atr": self.activation_atr.to_dict(),
            "activation_percent": self.activation_percent.to_dict(),
            "distance_atr": self.distance_atr.to_dict(),
            "distance_percent": self.distance_percent.to_dict(),
            "step_percent": self.step_percent.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrailingStopConfig":
        return cls(
            enabled=data.get("enabled", True),
            type=TrailingType(data.get("type", "atr_based")),
            move_to_breakeven=data.get("move_to_breakeven", True),
            activation_atr=OptimizableFloat.from_dict(data.get("activation_atr", {"value": 1.0})),
            activation_percent=OptimizableFloat.from_dict(data.get("activation_percent", {"value": 0.5})),
            distance_atr=OptimizableFloat.from_dict(data.get("distance_atr", {"value": 0.6})),
            distance_percent=OptimizableFloat.from_dict(data.get("distance_percent", {"value": 0.3})),
            step_percent=OptimizableFloat.from_dict(data.get("step_percent", {"value": 0.2}))
        )


@dataclass
class PartialTPConfig:
    """Partial Take-Profit Konfiguration."""
    enabled: bool = False
    tp1_percent: float = 50.0
    tp1_rr: float = 1.0
    move_sl_to_be: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "tp1_percent": self.tp1_percent,
            "tp1_rr": self.tp1_rr,
            "move_sl_to_be": self.move_sl_to_be
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PartialTPConfig":
        return cls(
            enabled=data.get("enabled", False),
            tp1_percent=data.get("tp1_percent", 50.0),
            tp1_rr=data.get("tp1_rr", 1.0),
            move_sl_to_be=data.get("move_sl_to_be", True)
        )


@dataclass
class TimeStopConfig:
    """Time Stop Konfiguration."""
    enabled: bool = False
    max_holding_minutes: int = 480

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_holding_minutes": self.max_holding_minutes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeStopConfig":
        return cls(
            enabled=data.get("enabled", False),
            max_holding_minutes=data.get("max_holding_minutes", 480)
        )


@dataclass
class ExitManagementSection:
    """Exit Management Konfiguration."""
    stop_loss: StopLossConfig = field(default_factory=StopLossConfig)
    take_profit: TakeProfitConfig = field(default_factory=TakeProfitConfig)
    trailing_stop: TrailingStopConfig = field(default_factory=TrailingStopConfig)
    partial_tp: PartialTPConfig = field(default_factory=PartialTPConfig)
    time_stop: TimeStopConfig = field(default_factory=TimeStopConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stop_loss": self.stop_loss.to_dict(),
            "take_profit": self.take_profit.to_dict(),
            "trailing_stop": self.trailing_stop.to_dict(),
            "partial_tp": self.partial_tp.to_dict(),
            "time_stop": self.time_stop.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExitManagementSection":
        return cls(
            stop_loss=StopLossConfig.from_dict(data.get("stop_loss", {})),
            take_profit=TakeProfitConfig.from_dict(data.get("take_profit", {})),
            trailing_stop=TrailingStopConfig.from_dict(data.get("trailing_stop", {})),
            partial_tp=PartialTPConfig.from_dict(data.get("partial_tp", {})),
            time_stop=TimeStopConfig.from_dict(data.get("time_stop", {}))
        )
