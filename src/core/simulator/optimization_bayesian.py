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
    # Legacy percentage-based SL/TP
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05
    # ATR-based SL/TP (from Bot-Tab settings)
    sl_atr_multiplier: float = 0.0  # 0 = use stop_loss_pct instead
    tp_atr_multiplier: float = 0.0  # 0 = use take_profit_pct instead
    atr_period: int = 14  # ATR calculation period
    # Trailing Stop (from Bot-Tab settings)
    trailing_stop_enabled: bool = False
    trailing_stop_atr_multiplier: float = 1.5  # Trailing distance in ATR

    # Entry-only optimization settings
    entry_only: bool = False  # Only optimize entry signals, skip full simulation
    entry_side: str = "both"  # "long", "short", or "both"
    entry_lookahead_mode: str = "bars"  # "bars" or "time"
    entry_lookahead_bars: int = 5  # Bars to look ahead for entry validation


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
        optuna, TPESampler = self._load_optuna()
        self._cancelled = False
        self._all_results = []
        start_time = time.time()

        param_config = get_strategy_parameters(self.config.strategy_name)
        simulator = StrategySimulator(self.data, self.symbol)

        loop = self._create_thread_event_loop()
        self._trial_errors = []

        # Create objective function
        def objective(trial: optuna.Trial) -> float:
            if self._cancelled:
                raise optuna.TrialPruned()

            try:
                params = self._build_trial_params(trial, param_config.parameters)
                result = self._run_simulation(loop, simulator, params)
                self._all_results.append(result)

                # Get objective value
                score = self._get_metric(result, self.config.objective_metric)

                # Report progress
                self._report_progress(progress_callback, trial.number, score)

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

        trials = self._build_trials(optuna)
        best_params, best_score, best_result = self._select_best_result(optuna)

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

    def _load_optuna(self):
        """Load optuna library for Bayesian optimization."""
        try:
            import optuna
            from optuna.samplers import TPESampler

            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            raise ImportError(
                "optuna is required for Bayesian optimization. "
                "Install with: pip install optuna"
            )
        return optuna, TPESampler

    def _create_thread_event_loop(self):
        """Create a new event loop for this thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

    def _build_trial_params(self, trial, parameters) -> dict[str, Any]:
        """Build parameter dict from optuna trial suggestions."""
        params = {}
        for param_def in parameters:
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
        return params

    def _run_simulation(self, loop, simulator, params: dict[str, Any]) -> SimulationResult:
        """Run simulation with given parameters."""
        return loop.run_until_complete(
            simulator.run_simulation(
                strategy_name=self.config.strategy_name,
                parameters=params,
                initial_capital=self.config.initial_capital,
                position_size_pct=self.config.position_size_pct,
                slippage_pct=self.config.slippage_pct,
                commission_pct=self.config.commission_pct,
                stop_loss_pct=self.config.stop_loss_pct,
                take_profit_pct=self.config.take_profit_pct,
                # ATR-based SL/TP from Bot-Tab settings
                sl_atr_multiplier=self.config.sl_atr_multiplier,
                tp_atr_multiplier=self.config.tp_atr_multiplier,
                atr_period=self.config.atr_period,
                # Trailing Stop from Bot-Tab settings
                trailing_stop_enabled=self.config.trailing_stop_enabled,
                trailing_stop_atr_multiplier=self.config.trailing_stop_atr_multiplier,
            )
        )

    def _report_progress(
        self,
        progress_callback: Callable[[int, int, float], None] | None,
        trial_number: int,
        score: float,
    ) -> None:
        """Report optimization progress to callback."""
        if not progress_callback:
            return
        try:
            best = self._study.best_value if self._study.best_trial else score
        except ValueError:
            best = score
        progress_callback(trial_number + 1, self.config.n_trials, best)

    def _build_trials(self, optuna) -> list[OptimizationTrial]:
        """Build list of OptimizationTrial from study trials."""
        trials: list[OptimizationTrial] = []
        result_idx = 0
        for i, trial in enumerate(self._study.trials):
            if trial.state != optuna.trial.TrialState.COMPLETE:
                continue
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
        return trials

    def _select_best_result(self, optuna) -> tuple[dict[str, Any], float, SimulationResult | None]:
        """Select the best result from completed trials."""
        best_params: dict[str, Any] = {}
        best_score = 0.0
        best_result = None
        completed_trials = [
            t for t in self._study.trials if t.state == optuna.trial.TrialState.COMPLETE
        ]
        if completed_trials:
            best_trial = self._study.best_trial
            if best_trial:
                best_params = best_trial.params
                best_score = best_trial.value
                completed_indices = [
                    i for i, t in enumerate(self._study.trials)
                    if t.state == optuna.trial.TrialState.COMPLETE
                ]
                if best_trial.number in [
                    self._study.trials[i].number for i in completed_indices
                ]:
                    best_trial_result_idx = completed_indices.index(
                        next(
                            i for i in completed_indices
                            if self._study.trials[i].number == best_trial.number
                        )
                    )
                    if best_trial_result_idx < len(self._all_results):
                        best_result = self._all_results[best_trial_result_idx]
        else:
            error_summary = (
                "; ".join(self._trial_errors[:5]) if self._trial_errors else "Unknown error"
            )
            logger.error(
                "Bayesian optimization failed: No trials completed. "
                f"Errors: {error_summary}"
            )
        return best_params, best_score, best_result


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
        self._reset_run_state()
        start_time = time.time()

        param_config = get_strategy_parameters(self.config.strategy_name)
        simulator = StrategySimulator(self.data, self.symbol)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        param_names, all_combinations = self._build_param_combinations(
            param_config, max_combinations
        )

        total = len(all_combinations)
        trials: list[OptimizationTrial] = []
        best_score = float("-inf") if self.config.direction == "maximize" else float("inf")
        best_params: dict[str, Any] = {}
        best_result = None

        try:
            for i, values in enumerate(all_combinations):
                if self._cancelled:
                    break
                params = dict(zip(param_names, values))
                result, error_msg = self._run_single_grid_trial(loop, simulator, params, i + 1)
                if result is None:
                    self._record_trial_error(error_msg)
                else:
                    self._all_results.append(result)
                    score = self._get_metric(result, self.config.objective_metric)
                    if self._is_better(score, best_score):
                        best_score = score
                        best_params = params.copy()
                        best_result = result
                    trials.append(self._build_trial(i + 1, params, score, result))

                if progress_callback:
                    progress_callback(i + 1, total, best_score if trials else 0.0)
        finally:
            loop.close()

        elapsed = time.time() - start_time
        self._log_trial_failures(trials)

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

    def _load_optuna(self):
        try:
            import optuna
            from optuna.samplers import TPESampler

            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            raise ImportError(
                "optuna is required for Bayesian optimization. "
                "Install with: pip install optuna"
            )
        return optuna, TPESampler

    def _create_thread_event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

    def _build_trial_params(self, trial, parameters):
        params = {}
        for param_def in parameters:
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
        return params

    def _run_simulation(self, loop, simulator, params: dict[str, Any]) -> SimulationResult:
        return loop.run_until_complete(
            simulator.run_simulation(
                strategy_name=self.config.strategy_name,
                parameters=params,
                initial_capital=self.config.initial_capital,
                position_size_pct=self.config.position_size_pct,
                slippage_pct=self.config.slippage_pct,
                commission_pct=self.config.commission_pct,
                stop_loss_pct=self.config.stop_loss_pct,
                take_profit_pct=self.config.take_profit_pct,
                # ATR-based SL/TP from Bot-Tab settings
                sl_atr_multiplier=self.config.sl_atr_multiplier,
                tp_atr_multiplier=self.config.tp_atr_multiplier,
                atr_period=self.config.atr_period,
                # Trailing Stop from Bot-Tab settings
                trailing_stop_enabled=self.config.trailing_stop_enabled,
                trailing_stop_atr_multiplier=self.config.trailing_stop_atr_multiplier,
            )
        )

    def _report_progress(
        self,
        progress_callback: Callable[[int, int, float], None] | None,
        trial_number: int,
        score: float,
    ) -> None:
        if not progress_callback:
            return
        try:
            best = self._study.best_value if self._study.best_trial else score
        except ValueError:
            best = score
        progress_callback(trial_number + 1, self.config.n_trials, best)

    def _build_trials(self, optuna) -> list[OptimizationTrial]:
        trials: list[OptimizationTrial] = []
        result_idx = 0
        for i, trial in enumerate(self._study.trials):
            if trial.state != optuna.trial.TrialState.COMPLETE:
                continue
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
        return trials

    def _select_best_result(self, optuna) -> tuple[dict[str, Any], float, SimulationResult | None]:
        best_params: dict[str, Any] = {}
        best_score = 0.0
        best_result = None
        completed_trials = [
            t for t in self._study.trials if t.state == optuna.trial.TrialState.COMPLETE
        ]
        if completed_trials:
            best_trial = self._study.best_trial
            if best_trial:
                best_params = best_trial.params
                best_score = best_trial.value
                completed_indices = [
                    i for i, t in enumerate(self._study.trials)
                    if t.state == optuna.trial.TrialState.COMPLETE
                ]
                if best_trial.number in [
                    self._study.trials[i].number for i in completed_indices
                ]:
                    best_trial_result_idx = completed_indices.index(
                        next(
                            i for i in completed_indices
                            if self._study.trials[i].number == best_trial.number
                        )
                    )
                    if best_trial_result_idx < len(self._all_results):
                        best_result = self._all_results[best_trial_result_idx]
        else:
            error_summary = (
                "; ".join(self._trial_errors[:5]) if self._trial_errors else "Unknown error"
            )
            logger.error(
                "Bayesian optimization failed: No trials completed. "
                f"Errors: {error_summary}"
            )
        return best_params, best_score, best_result

    def _reset_run_state(self) -> None:
        self._cancelled = False
        self._all_results = []
        self._trial_errors = []

    def _build_param_combinations(
        self,
        param_config,
        max_combinations: int,
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        param_grid: dict[str, list[Any]] = {}
        for param_def in param_config.parameters:
            param_grid[param_def.name] = self._get_grid_values(param_def)

        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        all_combinations = list(itertools.product(*param_values))

        if len(all_combinations) > max_combinations:
            step = len(all_combinations) // max_combinations
            all_combinations = all_combinations[::step][:max_combinations]
            logger.info(
                f"Grid search limited to {len(all_combinations)} combinations "
                f"(from {len(list(itertools.product(*param_values)))} total)"
            )
        return param_names, all_combinations

    def _run_single_grid_trial(self, loop, simulator, params: dict[str, Any], trial_number: int):
        try:
            return loop.run_until_complete(
                simulator.run_simulation(
                    strategy_name=self.config.strategy_name,
                    parameters=params,
                    initial_capital=self.config.initial_capital,
                    position_size_pct=self.config.position_size_pct,
                    slippage_pct=self.config.slippage_pct,
                    commission_pct=self.config.commission_pct,
                    stop_loss_pct=self.config.stop_loss_pct,
                    take_profit_pct=self.config.take_profit_pct,
                    # ATR-based SL/TP from Bot-Tab settings
                    sl_atr_multiplier=self.config.sl_atr_multiplier,
                    tp_atr_multiplier=self.config.tp_atr_multiplier,
                    atr_period=self.config.atr_period,
                    # Trailing Stop from Bot-Tab settings
                    trailing_stop_enabled=self.config.trailing_stop_enabled,
                    trailing_stop_atr_multiplier=self.config.trailing_stop_atr_multiplier,
                )
            ), None
        except Exception as e:
            error_msg = f"Grid trial {trial_number} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg

    def _record_trial_error(self, error_msg: str) -> None:
        self._trial_errors.append(error_msg)

    def _is_better(self, score: float, best_score: float) -> bool:
        return (
            score > best_score
            if self.config.direction == "maximize"
            else score < best_score
        )

    def _build_trial(
        self,
        trial_number: int,
        params: dict[str, Any],
        score: float,
        result: SimulationResult,
    ) -> OptimizationTrial:
        metrics = {
            "total_trades": result.total_trades,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor,
            "total_pnl_pct": result.total_pnl_pct,
            "max_drawdown_pct": result.max_drawdown_pct,
            "sharpe_ratio": result.sharpe_ratio or 0.0,
        }
        return OptimizationTrial(
            trial_number=trial_number,
            parameters=params,
            score=score,
            metrics=metrics,
        )

    def _log_trial_failures(self, trials: list[OptimizationTrial]) -> None:
        if not trials and self._trial_errors:
            error_summary = "; ".join(self._trial_errors[:5])
            logger.error(
                f"Grid search failed: No trials completed. Errors: {error_summary}"
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
