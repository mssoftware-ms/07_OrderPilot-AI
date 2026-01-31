"""Backtesting Configuration V2 - Optimization & Risk Management

Optimization and risk-related configuration classes:
- Risk & Leverage management
- Execution simulation settings
- Optimization configuration (method, iterations, target metrics)
- Walk-Forward analysis settings
- Parameter groups for joint testing
- Conditional parameter adjustments
- Constraints for backtest results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import (
    OptimizableFloat,
    OptimizableInt,
    OptimizationMethod,
    SlippageMethod,
    TargetMetric,
)


# ==================== RISK & EXECUTION ====================

@dataclass
class RiskLeverageSection:
    """Risk & Leverage Konfiguration."""
    risk_per_trade_pct: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.0))
    base_leverage: OptimizableInt = field(default_factory=lambda: OptimizableInt(value=5))
    max_leverage: int = 20
    min_liquidation_distance_pct: float = 5.0
    max_daily_loss_pct: float = 3.0
    max_trades_per_day: int = 10
    max_concurrent_positions: int = 1
    max_loss_streak: int = 3
    cooldown_after_streak_min: int = 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_per_trade_pct": self.risk_per_trade_pct.to_dict(),
            "base_leverage": self.base_leverage.to_dict(),
            "max_leverage": self.max_leverage,
            "min_liquidation_distance_pct": self.min_liquidation_distance_pct,
            "max_daily_loss_pct": self.max_daily_loss_pct,
            "max_trades_per_day": self.max_trades_per_day,
            "max_concurrent_positions": self.max_concurrent_positions,
            "max_loss_streak": self.max_loss_streak,
            "cooldown_after_streak_min": self.cooldown_after_streak_min
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskLeverageSection":
        return cls(
            risk_per_trade_pct=OptimizableFloat.from_dict(data.get("risk_per_trade_pct", {"value": 1.0})),
            base_leverage=OptimizableInt.from_dict(data.get("base_leverage", {"value": 5})),
            max_leverage=data.get("max_leverage", 20),
            min_liquidation_distance_pct=data.get("min_liquidation_distance_pct", 5.0),
            max_daily_loss_pct=data.get("max_daily_loss_pct", 3.0),
            max_trades_per_day=data.get("max_trades_per_day", 10),
            max_concurrent_positions=data.get("max_concurrent_positions", 1),
            max_loss_streak=data.get("max_loss_streak", 3),
            cooldown_after_streak_min=data.get("cooldown_after_streak_min", 60)
        )


@dataclass
class ExecutionSimulationSection:
    """Execution Simulation Konfiguration."""
    initial_capital: float = 10000.0
    symbol: str = "BTCUSDT"
    base_timeframe: str = "1m"
    mtf_timeframes: List[str] = field(default_factory=lambda: ["5m", "15m", "1h", "4h", "1D"])
    fee_maker_pct: float = 0.02
    fee_taker_pct: float = 0.06
    assume_taker: bool = True
    slippage_method: SlippageMethod = SlippageMethod.FIXED_BPS
    slippage_bps: float = 5.0
    slippage_atr_mult: float = 0.1
    funding_rate_8h: float = 0.01

    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_capital": self.initial_capital,
            "symbol": self.symbol,
            "base_timeframe": self.base_timeframe,
            "mtf_timeframes": self.mtf_timeframes,
            "fee_maker_pct": self.fee_maker_pct,
            "fee_taker_pct": self.fee_taker_pct,
            "assume_taker": self.assume_taker,
            "slippage_method": self.slippage_method.value,
            "slippage_bps": self.slippage_bps,
            "slippage_atr_mult": self.slippage_atr_mult,
            "funding_rate_8h": self.funding_rate_8h
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionSimulationSection":
        return cls(
            initial_capital=data.get("initial_capital", 10000.0),
            symbol=data.get("symbol", "BTCUSDT"),
            base_timeframe=data.get("base_timeframe", "1m"),
            mtf_timeframes=data.get("mtf_timeframes", ["5m", "15m", "1h", "4h", "1D"]),
            fee_maker_pct=data.get("fee_maker_pct", 0.02),
            fee_taker_pct=data.get("fee_taker_pct", 0.06),
            assume_taker=data.get("assume_taker", True),
            slippage_method=SlippageMethod(data.get("slippage_method", "fixed_bps")),
            slippage_bps=data.get("slippage_bps", 5.0),
            slippage_atr_mult=data.get("slippage_atr_mult", 0.1),
            funding_rate_8h=data.get("funding_rate_8h", 0.01)
        )


# ==================== OPTIMIZATION ====================

@dataclass
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


# ==================== ADVANCED FEATURES ====================

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
