"""Bayesian Optimization for Strategy Parameters.

Uses optuna library for efficient parameter search with TPE sampler.
Also provides Grid Search for exhaustive parameter exploration.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import pandas as pd

from .result_types import OptimizationRun, OptimizationTrial, SimulationResult
from .simulation_engine import StrategySimulator
from .strategy_params import StrategyName, get_strategy_parameters, ParameterDefinition

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for optimization run."""

    strategy_name: StrategyName
    objective_metric: str = "total_pnl_pct"  # Optimize for P&L% (maps to Score)
    direction: str = "maximize"  # or "minimize"
    n_trials: int = 50  # For Bayesian
    n_jobs: int = 1  # Parallel jobs (1 = sequential)
    timeout_seconds: float | None = None

    # Simulation settings - 1000€ per trade
    initial_capital: float = 1000.0  # 1000€ Startkapital
    position_size_pct: float = 1.0   # 100% = voller Einsatz pro Trade
    slippage_pct: float = 0.001
    commission_pct: float = 0.001
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05


class BayesianOptimizer:
    """Bayesian optimization using optuna TPE sampler.

    Efficiently searches parameter space by learning from previous trials.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        symbol: str,
        config: OptimizationConfig,
    ):
        """Initialize optimizer.

        Args:
            data: OHLCV DataFrame
            symbol: Trading symbol
            config: Optimization configuration
        """
        self.data = data
        self.symbol = symbol
        self.config = config
        self._study = None
        self._all_results: list[SimulationResult] = []
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel running optimization."""
        self._cancelled = True
        if self._study:
            self._study.stop()

    def optimize(
        self,
        progress_callback: Callable[[int, int, float], None] | None = None,
    ) -> OptimizationRun:
        """Run Bayesian optimization (synchronous).

        Args:
            progress_callback: Optional callback(current_trial, total_trials, best_score)

        Returns:
            OptimizationRun with best parameters and all trials
        """
        try:
            import optuna
            from optuna.samplers import TPESampler

            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            raise ImportError(
                "optuna is required for Bayesian optimization. "
                "Install with: pip install optuna"
            )

        self._cancelled = False
        self._all_results = []
        start_time = time.time()

        param_config = get_strategy_parameters(self.config.strategy_name)
        simulator = StrategySimulator(self.data, self.symbol)

        # Create a single event loop for all simulations in this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Track errors for debugging
        self._trial_errors: list[str] = []

        # Create objective function
        def objective(trial: optuna.Trial) -> float:
            if self._cancelled:
                raise optuna.TrialPruned()

            try:
                params = {}
                for param_def in param_config.parameters:
                    if param_def.param_type == "int":
                        params[param_def.name] = trial.suggest_int(
                            param_def.name,
                            param_def.min_value,
                            param_def.max_value,
                            step=param_def.step or 1,
                        )
                    elif param_def.param_type == "float":
                        params[param_def.name] = trial.suggest_float(
                            param_def.name,
                            param_def.min_value,
                            param_def.max_value,
                            step=param_def.step,
                        )
                    elif param_def.param_type == "bool":
                        params[param_def.name] = trial.suggest_categorical(
                            param_def.name, [True, False]
                        )

                # Run simulation using the thread's event loop
                result = loop.run_until_complete(
                    simulator.run_simulation(
                        strategy_name=self.config.strategy_name,
                        parameters=params,
                        initial_capital=self.config.initial_capital,
                        position_size_pct=self.config.position_size_pct,
                        slippage_pct=self.config.slippage_pct,
                        commission_pct=self.config.commission_pct,
                        stop_loss_pct=self.config.stop_loss_pct,
                        take_profit_pct=self.config.take_profit_pct,
                    )
                )
                self._all_results.append(result)

                # Get objective value
                score = self._get_metric(result, self.config.objective_metric)

                # Report progress
                if progress_callback:
                    best = self._study.best_value if self._study.best_trial else score
                    progress_callback(trial.number + 1, self.config.n_trials, best)

                return score

            except Exception as e:
                error_msg = f"Trial {trial.number} failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self._trial_errors.append(error_msg)
                raise optuna.TrialPruned()

        # Create study
        direction = self.config.direction
        self._study = optuna.create_study(
            direction=direction,
            sampler=TPESampler(seed=42),
        )

        # Run optimization
        try:
            self._study.optimize(
                objective,
                n_trials=self.config.n_trials,
                timeout=self.config.timeout_seconds,
                n_jobs=self.config.n_jobs,
                show_progress_bar=False,
            )
        except KeyboardInterrupt:
            logger.info("Optimization cancelled by user")
        finally:
            loop.close()

        elapsed = time.time() - start_time

        # Build trials list
        trials = []
        result_idx = 0  # Track index into _all_results separately
        for i, trial in enumerate(self._study.trials):
            if trial.state == optuna.trial.TrialState.COMPLETE:
                result = self._all_results[result_idx] if result_idx < len(self._all_results) else None
                result_idx += 1
                metrics = {}
                if result:
                    metrics = {
                        "total_trades": result.total_trades,
                        "win_rate": result.win_rate,
                        "profit_factor": result.profit_factor,
                        "total_pnl_pct": result.total_pnl_pct,
                        "max_drawdown_pct": result.max_drawdown_pct,
                        "sharpe_ratio": result.sharpe_ratio or 0.0,
                    }
                trials.append(
                    OptimizationTrial(
                        trial_number=i + 1,
                        parameters=trial.params,
                        score=trial.value,
                        metrics=metrics,
                    )
                )

        # Get best result
        best_result = None
        best_params = {}
        best_score = 0.0

        # Check if any trials completed
        completed_trials = [t for t in self._study.trials if t.state == optuna.trial.TrialState.COMPLETE]

        if completed_trials:
            best_trial = self._study.best_trial
            if best_trial:
                best_params = best_trial.params
                best_score = best_trial.value
                # Find corresponding result
                completed_indices = [i for i, t in enumerate(self._study.trials) if t.state == optuna.trial.TrialState.COMPLETE]
                if best_trial.number in [self._study.trials[i].number for i in completed_indices]:
                    best_trial_result_idx = completed_indices.index(
                        next(i for i in completed_indices if self._study.trials[i].number == best_trial.number)
                    )
                    if best_trial_result_idx < len(self._all_results):
                        best_result = self._all_results[best_trial_result_idx]
        else:
            # No trials completed - log the errors
            error_summary = "; ".join(self._trial_errors[:5]) if self._trial_errors else "Unknown error"
            logger.error(f"Bayesian optimization failed: No trials completed. Errors: {error_summary}")

        return OptimizationRun(
            strategy_name=self.config.strategy_name.value,
            optimization_type="bayesian",
            objective_metric=self.config.objective_metric,
            best_params=best_params,
            best_score=best_score,
            all_trials=trials,
            total_trials=len(trials),
            elapsed_seconds=elapsed,
            best_result=best_result,
            errors=self._trial_errors if self._trial_errors else None,
        )

    def _get_metric(self, result: SimulationResult, metric_name: str) -> float:
        """Extract metric value from simulation result."""
        if metric_name == "sharpe_ratio":
            return result.sharpe_ratio or 0.0
        elif metric_name == "profit_factor":
            return min(result.profit_factor, 10.0)  # Cap at 10
        elif metric_name == "total_pnl_pct":
            return result.total_pnl_pct
        elif metric_name == "win_rate":
            return result.win_rate
        elif metric_name == "total_trades":
            return float(result.total_trades)
        elif metric_name == "max_drawdown_pct":
            return -result.max_drawdown_pct  # Negate for minimization
        else:
            return result.total_pnl_pct


class GridSearchOptimizer:
    """Grid search optimizer for exhaustive parameter exploration.

    Tests all combinations of parameter values from their ranges.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        symbol: str,
        config: OptimizationConfig,
    ):
        """Initialize optimizer.

        Args:
            data: OHLCV DataFrame
            symbol: Trading symbol
            config: Optimization configuration
        """
        self.data = data
        self.symbol = symbol
        self.config = config
        self._cancelled = False
        self._all_results: list[SimulationResult] = []

    def cancel(self) -> None:
        """Cancel running optimization."""
        self._cancelled = True

    def optimize(
        self,
        progress_callback: Callable[[int, int, float], None] | None = None,
        max_combinations: int = 1000,
    ) -> OptimizationRun:
        """Run grid search optimization (synchronous).

        Args:
            progress_callback: Optional callback(current, total, best_score)
            max_combinations: Maximum number of parameter combinations to try

        Returns:
            OptimizationRun with best parameters and all trials
        """
        self._cancelled = False
        self._all_results = []
        self._trial_errors: list[str] = []
        start_time = time.time()

        param_config = get_strategy_parameters(self.config.strategy_name)
        simulator = StrategySimulator(self.data, self.symbol)

        # Create event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Generate parameter grid
        param_grid = {}
        for param_def in param_config.parameters:
            values = self._get_grid_values(param_def)
            param_grid[param_def.name] = values

        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        all_combinations = list(itertools.product(*param_values))

        # Limit combinations
        if len(all_combinations) > max_combinations:
            # Sample evenly
            step = len(all_combinations) // max_combinations
            all_combinations = all_combinations[::step][:max_combinations]
            logger.info(
                f"Grid search limited to {len(all_combinations)} combinations "
                f"(from {len(list(itertools.product(*param_values)))} total)"
            )

        total = len(all_combinations)
        trials = []
        best_score = float("-inf") if self.config.direction == "maximize" else float("inf")
        best_params = {}
        best_result = None

        try:
            for i, values in enumerate(all_combinations):
                if self._cancelled:
                    break

                params = dict(zip(param_names, values))

                try:
                    # Run simulation using thread's event loop
                    result = loop.run_until_complete(
                        simulator.run_simulation(
                            strategy_name=self.config.strategy_name,
                            parameters=params,
                            initial_capital=self.config.initial_capital,
                            position_size_pct=self.config.position_size_pct,
                            slippage_pct=self.config.slippage_pct,
                            commission_pct=self.config.commission_pct,
                            stop_loss_pct=self.config.stop_loss_pct,
                            take_profit_pct=self.config.take_profit_pct,
                        )
                    )
                    self._all_results.append(result)

                    score = self._get_metric(result, self.config.objective_metric)

                    # Check if best
                    is_better = (
                        score > best_score
                        if self.config.direction == "maximize"
                        else score < best_score
                    )
                    if is_better:
                        best_score = score
                        best_params = params.copy()
                        best_result = result

                    # Create trial
                    metrics = {
                        "total_trades": result.total_trades,
                        "win_rate": result.win_rate,
                        "profit_factor": result.profit_factor,
                        "total_pnl_pct": result.total_pnl_pct,
                        "max_drawdown_pct": result.max_drawdown_pct,
                        "sharpe_ratio": result.sharpe_ratio or 0.0,
                    }
                    trials.append(
                        OptimizationTrial(
                            trial_number=i + 1,
                            parameters=params,
                            score=score,
                            metrics=metrics,
                        )
                    )

                except Exception as e:
                    error_msg = f"Grid trial {i + 1} failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    self._trial_errors.append(error_msg)

                # Progress callback
                if progress_callback:
                    progress_callback(i + 1, total, best_score if trials else 0.0)
        finally:
            loop.close()

        elapsed = time.time() - start_time

        # Log if all trials failed
        if not trials and self._trial_errors:
            error_summary = "; ".join(self._trial_errors[:5])
            logger.error(f"Grid search failed: No trials completed. Errors: {error_summary}")

        return OptimizationRun(
            strategy_name=self.config.strategy_name.value,
            optimization_type="grid",
            objective_metric=self.config.objective_metric,
            best_params=best_params,
            best_score=best_score if trials else 0.0,
            all_trials=trials,
            total_trials=len(trials),
            elapsed_seconds=elapsed,
            best_result=best_result,
            errors=self._trial_errors if self._trial_errors else None,
        )

    def _get_grid_values(self, param_def: ParameterDefinition) -> list[Any]:
        """Get grid values for a parameter.

        Uses coarser step sizes for grid search to reduce combinations.
        """
        if param_def.param_type == "bool":
            return [True, False]

        if param_def.min_value is None or param_def.max_value is None:
            return [param_def.default]

        # Use coarser steps for grid search (2x normal step)
        step = param_def.step or (1 if param_def.param_type == "int" else 0.1)
        grid_step = step * 2  # Coarser for efficiency

        values = []
        current = param_def.min_value
        while current <= param_def.max_value:
            if param_def.param_type == "int":
                values.append(int(current))
            else:
                values.append(round(current, 4))
            current += grid_step

        # Always include default if not present
        if param_def.default not in values:
            values.append(param_def.default)
            values.sort()

        return values

    def _get_metric(self, result: SimulationResult, metric_name: str) -> float:
        """Extract metric value from simulation result."""
        if metric_name == "sharpe_ratio":
            return result.sharpe_ratio or 0.0
        elif metric_name == "profit_factor":
            return min(result.profit_factor, 10.0)
        elif metric_name == "total_pnl_pct":
            return result.total_pnl_pct
        elif metric_name == "win_rate":
            return result.win_rate
        elif metric_name == "total_trades":
            return float(result.total_trades)
        elif metric_name == "max_drawdown_pct":
            return -result.max_drawdown_pct
        else:
            return result.total_pnl_pct

    def estimate_combinations(self) -> int:
        """Estimate total number of parameter combinations."""
        param_config = get_strategy_parameters(self.config.strategy_name)
        total = 1
        for param_def in param_config.parameters:
            values = self._get_grid_values(param_def)
            total *= len(values)
        return total
