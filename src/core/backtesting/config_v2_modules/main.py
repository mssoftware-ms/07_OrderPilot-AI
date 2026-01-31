"""Backtesting Configuration V2 - Main Aggregator

Main configuration class that aggregates all config sections:
- Entry configuration (score, triggers)
- Exit configuration (SL, TP, trailing, etc.)
- Risk & leverage management
- Execution simulation
- Optimization settings
- Walk-forward analysis
- Parameter groups and conditionals
- Constraints
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .entry import (
    EntryScoreSection,
    EntryTriggersSection,
    MetaSection,
    StrategyProfileSection,
)
from .exit import ExitManagementSection
from .optimization import (
    Conditional,
    ConstraintsSection,
    ExecutionSimulationSection,
    OptimizationSection,
    ParameterGroup,
    RiskLeverageSection,
    WalkForwardSection,
)

logger = logging.getLogger(__name__)


# ==================== MAIN CONFIG CLASS ====================

@dataclass
class BacktestConfigV2:
    """
    Einheitliche Backtesting-Konfiguration V2.

    Konsolidiert alle Parameter aus:
    - Entry Score (Weights, Gates, Thresholds)
    - Entry Triggers (Breakout, Pullback, SFP)
    - Exit Management (SL, TP, Trailing, Partial TP, Time Stop)
    - Risk/Leverage
    - Execution Simulation
    - Optimization
    - Walk-Forward
    - Parameter-Gruppen
    - Conditionals
    - Constraints
    """
    version: str = "2.0.0"
    extends: Optional[str] = None
    meta: MetaSection = field(default_factory=lambda: MetaSection(name="Unnamed Config"))
    strategy_profile: StrategyProfileSection = field(default_factory=StrategyProfileSection)
    entry_score: EntryScoreSection = field(default_factory=EntryScoreSection)
    entry_triggers: EntryTriggersSection = field(default_factory=EntryTriggersSection)
    exit_management: ExitManagementSection = field(default_factory=ExitManagementSection)
    risk_leverage: RiskLeverageSection = field(default_factory=RiskLeverageSection)
    execution_simulation: ExecutionSimulationSection = field(default_factory=ExecutionSimulationSection)
    optimization: OptimizationSection = field(default_factory=OptimizationSection)
    walk_forward: WalkForwardSection = field(default_factory=WalkForwardSection)
    parameter_groups: List[ParameterGroup] = field(default_factory=list)
    conditionals: List[Conditional] = field(default_factory=list)
    constraints: ConstraintsSection = field(default_factory=ConstraintsSection)
    overrides: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary (JSON-serialisierbar)."""
        result = {
            "$schema": "./schemas/backtest_config_v2.schema.json",
            "version": self.version,
            "meta": self.meta.to_dict(),
            "strategy_profile": self.strategy_profile.to_dict(),
            "entry_score": self.entry_score.to_dict(),
            "entry_triggers": self.entry_triggers.to_dict(),
            "exit_management": self.exit_management.to_dict(),
            "risk_leverage": self.risk_leverage.to_dict(),
            "execution_simulation": self.execution_simulation.to_dict(),
            "optimization": self.optimization.to_dict(),
            "walk_forward": self.walk_forward.to_dict(),
            "constraints": self.constraints.to_dict()
        }

        if self.extends:
            result["extends"] = self.extends
        if self.parameter_groups:
            result["parameter_groups"] = [pg.to_dict() for pg in self.parameter_groups]
        if self.conditionals:
            result["conditionals"] = [c.to_dict() for c in self.conditionals]
        if self.overrides:
            result["overrides"] = self.overrides

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BacktestConfigV2":
        """Erstellt aus Dictionary."""
        param_groups = [ParameterGroup.from_dict(pg) for pg in data.get("parameter_groups", [])]
        conditionals = [Conditional.from_dict(c) for c in data.get("conditionals", [])]

        return cls(
            version=data.get("version", "2.0.0"),
            extends=data.get("extends"),
            meta=MetaSection.from_dict(data.get("meta", {})),
            strategy_profile=StrategyProfileSection.from_dict(data.get("strategy_profile", {})),
            entry_score=EntryScoreSection.from_dict(data.get("entry_score", {})),
            entry_triggers=EntryTriggersSection.from_dict(data.get("entry_triggers", {})),
            exit_management=ExitManagementSection.from_dict(data.get("exit_management", {})),
            risk_leverage=RiskLeverageSection.from_dict(data.get("risk_leverage", {})),
            execution_simulation=ExecutionSimulationSection.from_dict(data.get("execution_simulation", {})),
            optimization=OptimizationSection.from_dict(data.get("optimization", {})),
            walk_forward=WalkForwardSection.from_dict(data.get("walk_forward", {})),
            parameter_groups=param_groups,
            conditionals=conditionals,
            constraints=ConstraintsSection.from_dict(data.get("constraints", {})),
            overrides=data.get("overrides", {})
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialisiert zu JSON-String."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "BacktestConfigV2":
        """Erstellt aus JSON-String."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: Path) -> bool:
        """Speichert Konfiguration als JSON-Datei."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Config saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    @classmethod
    def load(cls, path: Path) -> "BacktestConfigV2":
        """Laedt Konfiguration aus JSON-Datei."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def get_optimizable_parameters(self) -> Dict[str, List[Any]]:
        """
        Sammelt alle Parameter mit optimize=True und gibt deren Suchraum zurueck.

        Returns:
            Dict mit Parameter-Pfaden und deren moeglichen Werten
        """
        params = {}

        # Entry Score
        if self.entry_score.min_score_for_entry.optimize:
            params["entry_score.min_score_for_entry"] = \
                self.entry_score.min_score_for_entry.get_search_space()

        # Entry Triggers - Breakout
        if self.entry_triggers.breakout.enabled:
            if self.entry_triggers.breakout.volume_multiplier.optimize:
                params["entry_triggers.breakout.volume_multiplier"] = \
                    self.entry_triggers.breakout.volume_multiplier.get_search_space()
            if self.entry_triggers.breakout.close_threshold.optimize:
                params["entry_triggers.breakout.close_threshold"] = \
                    self.entry_triggers.breakout.close_threshold.get_search_space()

        # Entry Triggers - Pullback
        if self.entry_triggers.pullback.enabled:
            if self.entry_triggers.pullback.max_distance_atr.optimize:
                params["entry_triggers.pullback.max_distance_atr"] = \
                    self.entry_triggers.pullback.max_distance_atr.get_search_space()

        # Exit Management - Stop Loss
        if self.exit_management.stop_loss.atr_multiplier.optimize:
            params["exit_management.stop_loss.atr_multiplier"] = \
                self.exit_management.stop_loss.atr_multiplier.get_search_space()

        # Exit Management - Take Profit
        if self.exit_management.take_profit.atr_multiplier.optimize:
            params["exit_management.take_profit.atr_multiplier"] = \
                self.exit_management.take_profit.atr_multiplier.get_search_space()

        # Exit Management - Trailing Stop
        if self.exit_management.trailing_stop.enabled:
            if self.exit_management.trailing_stop.activation_atr.optimize:
                params["exit_management.trailing_stop.activation_atr"] = \
                    self.exit_management.trailing_stop.activation_atr.get_search_space()
            if self.exit_management.trailing_stop.distance_atr.optimize:
                params["exit_management.trailing_stop.distance_atr"] = \
                    self.exit_management.trailing_stop.distance_atr.get_search_space()

        # Risk/Leverage
        if self.risk_leverage.risk_per_trade_pct.optimize:
            params["risk_leverage.risk_per_trade_pct"] = \
                self.risk_leverage.risk_per_trade_pct.get_search_space()
        if self.risk_leverage.base_leverage.optimize:
            params["risk_leverage.base_leverage"] = \
                self.risk_leverage.base_leverage.get_search_space()

        return params

    def __str__(self) -> str:
        return f"BacktestConfigV2(name={self.meta.name}, strategy={self.strategy_profile.type.value})"

    def __repr__(self) -> str:
        return self.__str__()
