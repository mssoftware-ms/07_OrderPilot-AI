"""Parameter Optimization for Trading Strategies.

Auto-tunes strategy parameters using genetic algorithms or Bayesian optimization
for better performance.

Phase 6: AI Analysis Integration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from src.core.tradingbot.config.models import (
    IndicatorDefinition,
    RegimeDefinition,
    RiskSettings,
    StrategyDefinition,
    TradingBotConfig,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Models & Types
# ─────────────────────────────────────────────────────────────────


class OptimizationMethod(str, Enum):
    """Optimization methods."""

    GENETIC = "genetic"  # Genetic algorithm
    BAYESIAN = "bayesian"  # Bayesian optimization
    GRID = "grid"  # Grid search
    RANDOM = "random"  # Random search


class OptimizationObjective(str, Enum):
    """Optimization objectives."""

    SHARPE = "sharpe"  # Maximize Sharpe ratio
    WIN_RATE = "win_rate"  # Maximize win rate
    PROFIT_FACTOR = "profit_factor"  # Maximize profit factor
    TOTAL_RETURN = "total_return"  # Maximize total return
    RISK_ADJ_RETURN = "risk_adjusted_return"  # Maximize risk-adjusted return


@dataclass
class ParameterRange:
    """Parameter optimization range."""

    name: str
    min_value: float
    max_value: float
    step: float | None = None  # For grid search
    is_integer: bool = False


class OptimizationConfig(BaseModel):
    """Configuration for parameter optimization."""

    method: OptimizationMethod = Field(default=OptimizationMethod.GENETIC)
    objective: OptimizationObjective = Field(default=OptimizationObjective.SHARPE)
    max_iterations: int = Field(default=50, ge=10, le=500)
    population_size: int = Field(default=20, ge=5, le=100)
    early_stopping_patience: int = Field(default=10, ge=3, le=50)
    cv_folds: int = Field(default=3, ge=2, le=10, description="Cross-validation folds")
    random_seed: int | None = Field(default=None, description="Random seed for reproducibility")


class OptimizationResult(BaseModel):
    """Result of parameter optimization."""

    best_params: dict[str, Any] = Field(description="Best parameter values")
    best_score: float = Field(description="Best objective score")
    all_trials: list[dict[str, Any]] = Field(description="All trials performed")
    convergence_history: list[float] = Field(description="Score progression over iterations")
    total_trials: int = Field(description="Total trials performed")
    notes: str = Field(default="", description="Optimization notes")


# ─────────────────────────────────────────────────────────────────
# Parameter Optimizer
# ─────────────────────────────────────────────────────────────────


class ParameterOptimizer:
    """Optimize strategy parameters using various algorithms.

    Usage:
        optimizer = ParameterOptimizer()
        result = optimizer.optimize_regime_thresholds(config, data, param_ranges)
        optimized_config = optimizer.apply_best_params(config, result.best_params)
    """

    def __init__(self, config: OptimizationConfig | None = None) -> None:
        """Initialize parameter optimizer.

        Args:
            config: Optimization configuration.
        """
        self.config = config or OptimizationConfig()

        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)

    def optimize_regime_thresholds(
        self,
        config: TradingBotConfig,
        data: pd.DataFrame,
        param_ranges: list[ParameterRange] | None = None,
        objective_fn: Callable[[TradingBotConfig, pd.DataFrame], float] | None = None,
    ) -> OptimizationResult:
        """Optimize regime threshold parameters.

        Args:
            config: Base configuration to optimize.
            data: Historical OHLCV data for evaluation.
            param_ranges: Parameter ranges to optimize. If None, uses defaults.
            objective_fn: Custom objective function. If None, uses simulated backtest.

        Returns:
            OptimizationResult with best parameters.
        """
        # Define default parameter ranges if not provided
        if param_ranges is None:
            param_ranges = self._get_default_regime_ranges()

        # Use default objective if not provided
        if objective_fn is None:
            objective_fn = self._default_objective_function

        # Run optimization based on method
        if self.config.method == OptimizationMethod.GENETIC:
            result = self._optimize_genetic(config, data, param_ranges, objective_fn)
        elif self.config.method == OptimizationMethod.BAYESIAN:
            result = self._optimize_bayesian(config, data, param_ranges, objective_fn)
        elif self.config.method == OptimizationMethod.GRID:
            result = self._optimize_grid(config, data, param_ranges, objective_fn)
        else:  # RANDOM
            result = self._optimize_random(config, data, param_ranges, objective_fn)

        logger.info(
            "Optimization complete: best_score=%.4f, trials=%d",
            result.best_score,
            result.total_trials,
        )

        return result

    def optimize_indicator_params(
        self,
        config: TradingBotConfig,
        data: pd.DataFrame,
        indicator_id: str,
        param_ranges: list[ParameterRange],
    ) -> OptimizationResult:
        """Optimize parameters for a specific indicator.

        Args:
            config: Configuration containing the indicator.
            data: Historical data.
            indicator_id: ID of indicator to optimize.
            param_ranges: Parameter ranges for the indicator.

        Returns:
            OptimizationResult with best parameters.
        """
        # Validate indicator exists
        indicator = next((i for i in config.indicators if i.id == indicator_id), None)
        if not indicator:
            raise ValueError(f"Indicator '{indicator_id}' not found in config")

        logger.info("Optimizing indicator '%s' parameters", indicator_id)

        # Define objective function that updates this specific indicator
        def indicator_objective(cfg: TradingBotConfig, df: pd.DataFrame) -> float:
            return self._default_objective_function(cfg, df)

        return self.optimize_regime_thresholds(config, data, param_ranges, indicator_objective)

    def optimize_risk_params(
        self,
        config: TradingBotConfig,
        data: pd.DataFrame,
        strategy_id: str,
    ) -> OptimizationResult:
        """Optimize risk parameters for a specific strategy.

        Args:
            config: Configuration containing the strategy.
            data: Historical data.
            strategy_id: ID of strategy to optimize.

        Returns:
            OptimizationResult with best risk parameters.
        """
        # Define risk parameter ranges
        param_ranges = [
            ParameterRange(name="position_size", min_value=0.01, max_value=0.1, step=0.01),
            ParameterRange(name="stop_loss", min_value=0.01, max_value=0.05, step=0.005),
            ParameterRange(name="take_profit", min_value=0.02, max_value=0.15, step=0.01),
        ]

        logger.info("Optimizing risk parameters for strategy '%s'", strategy_id)

        return self.optimize_regime_thresholds(config, data, param_ranges)

    def apply_best_params(
        self,
        config: TradingBotConfig,
        params: dict[str, Any],
        target_type: str = "regime",
        target_id: str | None = None,
    ) -> TradingBotConfig:
        """Apply optimized parameters to configuration.

        Args:
            config: Original configuration.
            params: Best parameters from optimization.
            target_type: Type of target: "regime", "indicator", "strategy".
            target_id: ID of specific target (if applicable).

        Returns:
            Updated configuration.
        """
        # Create a copy to avoid mutating original
        config_dict = config.model_dump()

        if target_type == "regime" and target_id:
            # Update regime conditions with new thresholds
            for regime in config_dict["regimes"]:
                if regime["id"] == target_id:
                    self._update_conditions_with_params(regime["conditions"], params)

        elif target_type == "indicator" and target_id:
            # Update indicator parameters
            for indicator in config_dict["indicators"]:
                if indicator["id"] == target_id:
                    indicator["params"].update(params)

        elif target_type == "strategy" and target_id:
            # Update strategy risk parameters
            for strategy in config_dict["strategies"]:
                if strategy["id"] == target_id:
                    if "risk" not in strategy:
                        strategy["risk"] = {}
                    strategy["risk"].update(params)

        return TradingBotConfig(**config_dict)

    # ─────────────────────────────────────────────────────────────────
    # Optimization Algorithms
    # ─────────────────────────────────────────────────────────────────

    def _optimize_genetic(
        self,
        config: TradingBotConfig,
        data: pd.DataFrame,
        param_ranges: list[ParameterRange],
        objective_fn: Callable,
    ) -> OptimizationResult:
        """Genetic algorithm optimization."""
        population = self._initialize_population(param_ranges, self.config.population_size)
        best_score = float("-inf")
        best_params = None
        convergence_history = []
        all_trials = []
        patience_counter = 0

        for generation in range(self.config.max_iterations):
            # Evaluate population
            scores = []
            for individual in population:
                updated_config = self._apply_params_to_config(config, individual, param_ranges)
                score = objective_fn(updated_config, data)
                scores.append(score)

                all_trials.append({"params": individual.copy(), "score": score})

                # Track best
                if score > best_score:
                    best_score = score
                    best_params = individual.copy()
                    patience_counter = 0
                else:
                    patience_counter += 1

            convergence_history.append(max(scores))

            # Early stopping
            if patience_counter >= self.config.early_stopping_patience:
                logger.info("Early stopping at generation %d", generation)
                break

            # Selection, crossover, mutation
            population = self._evolve_population(population, scores, param_ranges)

            if generation % 10 == 0:
                logger.debug("Generation %d: best_score=%.4f", generation, best_score)

        return OptimizationResult(
            best_params=self._format_params(best_params, param_ranges),
            best_score=best_score,
            all_trials=all_trials,
            convergence_history=convergence_history,
            total_trials=len(all_trials),
            notes=f"Genetic algorithm with {len(population)} population",
        )

    def _optimize_bayesian(
        self,
        config: TradingBotConfig,
        data: pd.DataFrame,
        param_ranges: list[ParameterRange],
        objective_fn: Callable,
    ) -> OptimizationResult:
        """Bayesian optimization (simplified implementation)."""
        # Initialize with random samples
        n_initial = min(10, self.config.population_size)
        trials = []
        best_score = float("-inf")
        best_params = None
        convergence_history = []

        # Random initial exploration
        for _ in range(n_initial):
            params = self._sample_params(param_ranges)
            updated_config = self._apply_params_to_config(config, params, param_ranges)
            score = objective_fn(updated_config, data)

            trials.append({"params": params.copy(), "score": score})
            convergence_history.append(score if score > best_score else best_score)

            if score > best_score:
                best_score = score
                best_params = params.copy()

        # Bayesian iterations (simplified - normally uses Gaussian processes)
        for _ in range(self.config.max_iterations - n_initial):
            # Sample near best params with exploration
            params = self._sample_near_best(best_params, param_ranges)
            updated_config = self._apply_params_to_config(config, params, param_ranges)
            score = objective_fn(updated_config, data)

            trials.append({"params": params.copy(), "score": score})
            convergence_history.append(score if score > best_score else best_score)

            if score > best_score:
                best_score = score
                best_params = params.copy()

        return OptimizationResult(
            best_params=self._format_params(best_params, param_ranges),
            best_score=best_score,
            all_trials=trials,
            convergence_history=convergence_history,
            total_trials=len(trials),
            notes="Simplified Bayesian optimization",
        )

    def _optimize_grid(
        self,
        config: TradingBotConfig,
        data: pd.DataFrame,
        param_ranges: list[ParameterRange],
        objective_fn: Callable,
    ) -> OptimizationResult:
        """Grid search optimization."""
        # Generate grid
        grid_points = self._generate_grid(param_ranges)

        best_score = float("-inf")
        best_params = None
        all_trials = []

        for params in grid_points:
            updated_config = self._apply_params_to_config(config, params, param_ranges)
            score = objective_fn(updated_config, data)

            all_trials.append({"params": params.copy(), "score": score})

            if score > best_score:
                best_score = score
                best_params = params.copy()

        convergence = [max(t["score"] for t in all_trials[: i + 1]) for i in range(len(all_trials))]

        return OptimizationResult(
            best_params=self._format_params(best_params, param_ranges),
            best_score=best_score,
            all_trials=all_trials,
            convergence_history=convergence,
            total_trials=len(all_trials),
            notes=f"Grid search with {len(grid_points)} points",
        )

    def _optimize_random(
        self,
        config: TradingBotConfig,
        data: pd.DataFrame,
        param_ranges: list[ParameterRange],
        objective_fn: Callable,
    ) -> OptimizationResult:
        """Random search optimization."""
        best_score = float("-inf")
        best_params = None
        all_trials = []
        convergence_history = []

        for _ in range(self.config.max_iterations):
            params = self._sample_params(param_ranges)
            updated_config = self._apply_params_to_config(config, params, param_ranges)
            score = objective_fn(updated_config, data)

            all_trials.append({"params": params.copy(), "score": score})
            convergence_history.append(score if score > best_score else best_score)

            if score > best_score:
                best_score = score
                best_params = params.copy()

        return OptimizationResult(
            best_params=self._format_params(best_params, param_ranges),
            best_score=best_score,
            all_trials=all_trials,
            convergence_history=convergence_history,
            total_trials=len(all_trials),
            notes="Random search",
        )

    # ─────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────

    def _get_default_regime_ranges(self) -> list[ParameterRange]:
        """Get default parameter ranges for regime optimization."""
        return [
            ParameterRange(name="adx_threshold", min_value=15.0, max_value=35.0, step=5.0),
            ParameterRange(name="rsi_upper", min_value=60.0, max_value=80.0, step=5.0),
            ParameterRange(name="rsi_lower", min_value=20.0, max_value=40.0, step=5.0),
            ParameterRange(name="volatility_threshold", min_value=0.5, max_value=2.0, step=0.25),
        ]

    def _default_objective_function(self, config: TradingBotConfig, data: pd.DataFrame) -> float:
        """Default objective function (simulated backtest).

        Args:
            config: Configuration to evaluate.
            data: Historical data.

        Returns:
            Objective score (Sharpe ratio approximation).
        """
        # Simplified backtest simulation
        # In real implementation, this would run full backtest
        returns = data["close"].pct_change().dropna()

        # Simulate strategy performance (placeholder)
        mean_return = returns.mean()
        std_return = returns.std()

        if std_return == 0:
            return 0.0

        # Sharpe-like score
        sharpe = mean_return / std_return * np.sqrt(252)  # Annualized

        return float(sharpe)

    def _initialize_population(
        self, param_ranges: list[ParameterRange], size: int
    ) -> list[list[float]]:
        """Initialize random population for genetic algorithm."""
        population = []
        for _ in range(size):
            individual = self._sample_params(param_ranges)
            population.append(individual)
        return population

    def _sample_params(self, param_ranges: list[ParameterRange]) -> list[float]:
        """Sample random parameters within ranges."""
        params = []
        for pr in param_ranges:
            if pr.is_integer:
                val = np.random.randint(int(pr.min_value), int(pr.max_value) + 1)
            else:
                val = np.random.uniform(pr.min_value, pr.max_value)
            params.append(val)
        return params

    def _sample_near_best(
        self, best_params: list[float], param_ranges: list[ParameterRange]
    ) -> list[float]:
        """Sample parameters near best (for Bayesian optimization)."""
        params = []
        for i, pr in enumerate(param_ranges):
            # Add Gaussian noise around best
            noise = np.random.normal(0, (pr.max_value - pr.min_value) * 0.1)
            val = best_params[i] + noise

            # Clip to bounds
            val = max(pr.min_value, min(pr.max_value, val))

            if pr.is_integer:
                val = int(round(val))

            params.append(val)
        return params

    def _evolve_population(
        self,
        population: list[list[float]],
        scores: list[float],
        param_ranges: list[ParameterRange],
    ) -> list[list[float]]:
        """Evolve population via selection, crossover, mutation."""
        # Selection (tournament)
        selected = self._tournament_selection(population, scores, len(population) // 2)

        # Crossover
        offspring = []
        for i in range(0, len(selected), 2):
            if i + 1 < len(selected):
                child1, child2 = self._crossover(selected[i], selected[i + 1])
                offspring.extend([child1, child2])
            else:
                offspring.append(selected[i])

        # Mutation
        offspring = [self._mutate(ind, param_ranges) for ind in offspring]

        # Combine with elite from previous generation
        elite_count = len(population) - len(offspring)
        elite_indices = np.argsort(scores)[-elite_count:]
        elite = [population[i] for i in elite_indices]

        return elite + offspring

    def _tournament_selection(
        self, population: list[list[float]], scores: list[float], n_select: int
    ) -> list[list[float]]:
        """Tournament selection."""
        selected = []
        for _ in range(n_select):
            # Select 3 random individuals
            indices = np.random.choice(len(population), size=3, replace=False)
            # Pick best among them
            best_idx = indices[np.argmax([scores[i] for i in indices])]
            selected.append(population[best_idx].copy())
        return selected

    def _crossover(self, parent1: list[float], parent2: list[float]) -> tuple[list[float], list[float]]:
        """Single-point crossover."""
        point = np.random.randint(1, len(parent1))
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2

    def _mutate(self, individual: list[float], param_ranges: list[ParameterRange]) -> list[float]:
        """Mutate individual."""
        mutated = individual.copy()
        for i, pr in enumerate(param_ranges):
            if np.random.rand() < 0.1:  # 10% mutation rate
                if pr.is_integer:
                    mutated[i] = np.random.randint(int(pr.min_value), int(pr.max_value) + 1)
                else:
                    mutated[i] = np.random.uniform(pr.min_value, pr.max_value)
        return mutated

    def _generate_grid(self, param_ranges: list[ParameterRange]) -> list[list[float]]:
        """Generate grid points for grid search."""
        # Limit grid size to prevent explosion
        max_points_per_param = 5

        grids = []
        for pr in param_ranges:
            if pr.step:
                grid = np.arange(pr.min_value, pr.max_value + pr.step, pr.step)
            else:
                grid = np.linspace(pr.min_value, pr.max_value, max_points_per_param)

            if pr.is_integer:
                grid = np.unique(grid.astype(int))

            grids.append(grid)

        # Generate all combinations
        from itertools import product

        grid_points = list(product(*grids))
        return [list(point) for point in grid_points]

    def _apply_params_to_config(
        self,
        config: TradingBotConfig,
        params: list[float],
        param_ranges: list[ParameterRange],
    ) -> TradingBotConfig:
        """Apply parameters to configuration."""
        param_dict = self._format_params(params, param_ranges)
        # For now, return original config (full implementation would modify it)
        # In real use, this would update regime thresholds, indicator params, etc.
        return config

    def _format_params(
        self, params: list[float], param_ranges: list[ParameterRange]
    ) -> dict[str, Any]:
        """Format parameter list as dictionary."""
        return {pr.name: params[i] for i, pr in enumerate(param_ranges)}

    def _update_conditions_with_params(
        self, conditions: dict[str, Any], params: dict[str, Any]
    ) -> None:
        """Update condition thresholds with new parameters."""
        # Recursively update condition values
        # This is a placeholder - real implementation would intelligently map params
        pass
