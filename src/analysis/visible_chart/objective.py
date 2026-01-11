"""Objective Function for Entry Optimization.

Implements the scoring function that evaluates indicator sets
based on trade simulation results.

Phase 2.3: Objective/Score implementieren (Trefferquote primär + Constraints)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .trade_simulator import SimulationResult

logger = logging.getLogger(__name__)


@dataclass
class ObjectiveConfig:
    """Configuration for objective function.

    Attributes:
        primary_metric: Main metric to optimize ("win_rate", "profit_factor", "expectancy").
        min_trades: Minimum trades required (hard gate).
        max_signals_per_hour: Maximum signal rate (hard gate).
        max_drawdown: Maximum drawdown allowed (hard gate).
        win_rate_weight: Weight for win rate component.
        profit_factor_weight: Weight for profit factor component.
        expectancy_weight: Weight for expectancy component.
        drawdown_penalty: Penalty factor for drawdown.
        complexity_penalty: Penalty per indicator in set.
    """

    primary_metric: str = "win_rate"
    min_trades: int = 5
    max_signals_per_hour: float = 10.0
    max_drawdown: float = 5.0  # R multiples
    win_rate_weight: float = 0.5
    profit_factor_weight: float = 0.3
    expectancy_weight: float = 0.2
    drawdown_penalty: float = 0.1
    complexity_penalty: float = 0.02


@dataclass
class ObjectiveResult:
    """Result of objective function evaluation.

    Attributes:
        score: Final score (higher is better).
        is_valid: Whether all hard gates passed.
        gate_failures: List of failed gates.
        components: Breakdown of score components.
        simulation_result: Underlying simulation result.
    """

    score: float
    is_valid: bool
    gate_failures: list[str]
    components: dict[str, float]
    simulation_result: SimulationResult | None = None

    @classmethod
    def invalid(cls, reason: str) -> ObjectiveResult:
        """Create an invalid result with score = -inf."""
        return cls(
            score=float("-inf"),
            is_valid=False,
            gate_failures=[reason],
            components={},
        )


class ObjectiveFunction:
    """Evaluates indicator sets based on trade simulation results.

    Implements hard gates (instant fail) and soft scoring components.
    """

    def __init__(self, config: ObjectiveConfig | None = None) -> None:
        """Initialize the objective function.

        Args:
            config: Objective configuration.
        """
        self.config = config or ObjectiveConfig()

    def evaluate(
        self,
        sim_result: SimulationResult,
        n_indicators: int = 1,
        hours_analyzed: float = 1.0,
    ) -> ObjectiveResult:
        """Evaluate simulation result and return score.

        Args:
            sim_result: Trade simulation result.
            n_indicators: Number of indicators in the set.
            hours_analyzed: Duration of analyzed period in hours.

        Returns:
            ObjectiveResult with score and validity.
        """
        gate_failures = []

        # ====== HARD GATES ======

        # Gate 1: Minimum trades
        if sim_result.total_trades < self.config.min_trades:
            return ObjectiveResult.invalid(
                f"min_trades: {sim_result.total_trades} < {self.config.min_trades}"
            )

        # Gate 2: Maximum signal rate
        signal_rate = sim_result.total_trades / hours_analyzed if hours_analyzed > 0 else 0
        if signal_rate > self.config.max_signals_per_hour:
            return ObjectiveResult.invalid(
                f"signal_rate: {signal_rate:.1f} > {self.config.max_signals_per_hour}"
            )

        # Gate 3: Maximum drawdown
        if sim_result.max_drawdown_pct > self.config.max_drawdown:
            return ObjectiveResult.invalid(
                f"max_drawdown: {sim_result.max_drawdown_pct:.1f}R > {self.config.max_drawdown}R"
            )

        # ====== SOFT SCORING ======

        components = {}

        # Component 1: Win Rate (0-1)
        win_rate_score = min(sim_result.win_rate, 1.0)
        components["win_rate"] = win_rate_score * self.config.win_rate_weight

        # Component 2: Profit Factor (capped at 3 for scoring)
        pf_normalized = min(sim_result.profit_factor / 3.0, 1.0)
        components["profit_factor"] = pf_normalized * self.config.profit_factor_weight

        # Component 3: Expectancy (capped at 1R for scoring)
        exp_normalized = max(min(sim_result.expectancy, 1.0), -1.0)  # -1 to 1
        exp_score = (exp_normalized + 1.0) / 2.0  # 0 to 1
        components["expectancy"] = exp_score * self.config.expectancy_weight

        # ====== PENALTIES ======

        # Drawdown penalty
        dd_penalty = sim_result.max_drawdown_pct * self.config.drawdown_penalty
        components["drawdown_penalty"] = -dd_penalty

        # Complexity penalty (more indicators = higher penalty)
        complexity_penalty = n_indicators * self.config.complexity_penalty
        components["complexity_penalty"] = -complexity_penalty

        # ====== FINAL SCORE ======

        base_score = sum(components.values())

        # Bonus for high trade count (more reliable stats)
        trade_bonus = min(sim_result.total_trades / 20, 0.1)
        components["trade_bonus"] = trade_bonus

        final_score = base_score + trade_bonus

        logger.debug(
            "Objective score: %.3f (WR=%.2f, PF=%.2f, Exp=%.2f, Trades=%d)",
            final_score,
            sim_result.win_rate,
            sim_result.profit_factor,
            sim_result.expectancy,
            sim_result.total_trades,
        )

        return ObjectiveResult(
            score=final_score,
            is_valid=True,
            gate_failures=[],
            components=components,
            simulation_result=sim_result,
        )

    def compare(self, result_a: ObjectiveResult, result_b: ObjectiveResult) -> int:
        """Compare two objective results.

        Args:
            result_a: First result.
            result_b: Second result.

        Returns:
            -1 if a < b, 0 if equal, 1 if a > b.
        """
        if result_a.score < result_b.score:
            return -1
        elif result_a.score > result_b.score:
            return 1
        return 0


def create_objective_for_regime(regime: str) -> ObjectiveFunction:
    """Create objective function tuned for specific regime.

    Args:
        regime: Market regime.

    Returns:
        ObjectiveFunction with appropriate config.
    """
    if regime in ("trend_up", "trend_down"):
        # Trend: Favor lower win rate but higher R
        config = ObjectiveConfig(
            primary_metric="expectancy",
            min_trades=3,
            max_signals_per_hour=8.0,
            win_rate_weight=0.3,
            profit_factor_weight=0.4,
            expectancy_weight=0.3,
        )
    elif regime == "range":
        # Range: Favor high win rate
        config = ObjectiveConfig(
            primary_metric="win_rate",
            min_trades=5,
            max_signals_per_hour=12.0,
            win_rate_weight=0.6,
            profit_factor_weight=0.25,
            expectancy_weight=0.15,
        )
    elif regime == "squeeze":
        # Squeeze: Few but high quality signals
        config = ObjectiveConfig(
            primary_metric="profit_factor",
            min_trades=2,
            max_signals_per_hour=4.0,
            win_rate_weight=0.35,
            profit_factor_weight=0.45,
            expectancy_weight=0.2,
        )
    else:
        # Default/conservative
        config = ObjectiveConfig()

    return ObjectiveFunction(config)
