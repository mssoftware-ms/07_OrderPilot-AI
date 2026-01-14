"""
Backtesting Configuration - Optimization, WalkForward, Constraints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from .enums import OptimizationMethod, TargetMetric

class OptimizationSection:
    """Optimierungs-Konfiguration."""
    method: OptimizationMethod = OptimizationMethod.RANDOM
    max_iterations: int = 300
    n_jobs: int = 1
    seed: int = 42
    target_metric: TargetMetric = TargetMetric.EXPECTANCY
    minimize: bool = False
    early_stopping_enabled: bool = False
    early_stopping_patience: int = 50
    early_stopping_min_improvement: float = 0.01
    parameter_space_override: Dict[str, List[Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "max_iterations": self.max_iterations,
            "n_jobs": self.n_jobs,
            "seed": self.seed,
            "target_metric": self.target_metric.value,
            "minimize": self.minimize,
            "early_stopping": {
                "enabled": self.early_stopping_enabled,
                "patience": self.early_stopping_patience,
                "min_improvement": self.early_stopping_min_improvement
            },
            "parameter_space_override": self.parameter_space_override
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizationSection":
        early_stop = data.get("early_stopping", {})
        return cls(
            method=OptimizationMethod(data.get("method", "random")),
            max_iterations=data.get("max_iterations", 300),
            n_jobs=data.get("n_jobs", 1),
            seed=data.get("seed", 42),
            target_metric=TargetMetric(data.get("target_metric", "expectancy")),
            minimize=data.get("minimize", False),
            early_stopping_enabled=early_stop.get("enabled", False),
            early_stopping_patience=early_stop.get("patience", 50),
            early_stopping_min_improvement=early_stop.get("min_improvement", 0.01),
            parameter_space_override=data.get("parameter_space_override", {})
        )


@dataclass
class WalkForwardSection:
    """Walk-Forward Analyse Konfiguration."""
    enabled: bool = False
    train_window_days: int = 90
    test_window_days: int = 30
    step_size_days: int = 30
    min_folds: int = 4
    reoptimize_each_fold: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "train_window_days": self.train_window_days,
            "test_window_days": self.test_window_days,
            "step_size_days": self.step_size_days,
            "min_folds": self.min_folds,
            "reoptimize_each_fold": self.reoptimize_each_fold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalkForwardSection":
        return cls(
            enabled=data.get("enabled", False),
            train_window_days=data.get("train_window_days", 90),
            test_window_days=data.get("test_window_days", 30),
            step_size_days=data.get("step_size_days", 30),
            min_folds=data.get("min_folds", 4),
            reoptimize_each_fold=data.get("reoptimize_each_fold", True)
        )


@dataclass
class ParameterGroup:
    """Parameter-Gruppe fuer gemeinsames Testen."""
    name: str
    parameters: List[str]  # JSON-Pfade
    combinations: List[List[float]]
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "combinations": self.combinations
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterGroup":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            parameters=data.get("parameters", []),
            combinations=data.get("combinations", [])
        )


@dataclass
class Conditional:
    """Bedingte Parameter-Anpassung."""
    condition: Dict[str, Any]  # if-Bedingung
    actions: Dict[str, Any]    # then-Aktionen

    def to_dict(self) -> Dict[str, Any]:
        return {
            "if": self.condition,
            "then": self.actions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conditional":
        return cls(
            condition=data.get("if", {}),
            actions=data.get("then", {})
        )


@dataclass
class ConstraintsSection:
    """Constraints fuer Backtesting-Ergebnisse."""
    min_trades: int = 50
    max_drawdown_pct: float = 30.0
    min_win_rate: float = 0.40
    min_profit_factor: float = 1.2
    min_sharpe: Optional[float] = None
    min_sortino: Optional[float] = None
    max_consecutive_losses: Optional[int] = None
    weights_must_sum_to_one: bool = True

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "min_trades": self.min_trades,
            "max_drawdown_pct": self.max_drawdown_pct,
            "min_win_rate": self.min_win_rate,
            "min_profit_factor": self.min_profit_factor,
            "weights_must_sum_to_one": self.weights_must_sum_to_one
        }
        if self.min_sharpe is not None:
            result["min_sharpe"] = self.min_sharpe
        if self.min_sortino is not None:
            result["min_sortino"] = self.min_sortino
        if self.max_consecutive_losses is not None:
            result["max_consecutive_losses"] = self.max_consecutive_losses
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstraintsSection":
        return cls(
            min_trades=data.get("min_trades", 50),
            max_drawdown_pct=data.get("max_drawdown_pct", 30.0),
            min_win_rate=data.get("min_win_rate", 0.40),
            min_profit_factor=data.get("min_profit_factor", 1.2),
            min_sharpe=data.get("min_sharpe"),
            min_sortino=data.get("min_sortino"),
            max_consecutive_losses=data.get("max_consecutive_losses"),
            weights_must_sum_to_one=data.get("weights_must_sum_to_one", True)
        )

