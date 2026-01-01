from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    from src.core.simulator import SimulationResult, OptimizationRun

logger = logging.getLogger(__name__)

class SimulationWorker(QThread):
    """Worker thread for running simulations."""

    finished = pyqtSignal(object)  # SimulationResult or OptimizationRun
    partial_result = pyqtSignal(object)  # Intermediate result for batch runs
    progress = pyqtSignal(int, int, float)  # current, total, best_score
    strategy_started = pyqtSignal(int, int, str, str)  # index, total, strategy_name, side
    error = pyqtSignal(str)

    def __init__(
        self,
        data,
        symbol: str,
        strategy_name: str,
        parameters: dict,
        mode: str,
        opt_trials: int = 50,
        objective_metric: str = "score",
        entry_only: bool = False,
        entry_lookahead_mode: str = "session_end",
        entry_lookahead_bars: int | None = None,
    ):
        super().__init__()
        self.data = data
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.parameters = parameters
        self.mode = mode  # "manual", "grid", "bayesian"
        self.opt_trials = opt_trials
        self.objective_metric = objective_metric
        self.entry_only = entry_only
        self.entry_lookahead_mode = entry_lookahead_mode
        self.entry_lookahead_bars = entry_lookahead_bars
        self._cancelled = False
        self._optimizer = None  # type: ignore[var-annotated]

    def cancel(self):
        """Cancel running simulation."""
        self._cancelled = True
        if self._optimizer and hasattr(self._optimizer, "cancel"):
            try:
                self._optimizer.cancel()
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Optimizer cancel failed: %s", exc)

    def run(self):
        """Run simulation in separate thread."""
        try:
            from src.core.simulator import (
                StrategyName,
                StrategySimulator,
                OptimizationConfig,
                BayesianOptimizer,
                GridSearchOptimizer,
                get_default_parameters,
                load_strategy_params,
                filter_entry_only_params,
            )

            is_all = self.strategy_name == "all"
            strategies = list(StrategyName) if is_all else [StrategyName(self.strategy_name)]
            sides = ["long", "short"] if self.entry_only else ["long"]
            total_runs = len(strategies) * len(sides)

            if self.mode == "manual":
                # Single or batch simulation - needs event loop for async run_simulation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results: list[object] = []
                try:
                    simulator = StrategySimulator(self.data, self.symbol)
                    run_index = 0
                    for strategy in strategies:
                        for side in sides:
                            if self._cancelled:
                                break
                            run_index += 1
                            self.strategy_started.emit(run_index, total_runs, strategy.value, side)
                            if is_all:
                                params = load_strategy_params(strategy.value) or get_default_parameters(strategy)
                            else:
                                params = self.parameters
                            if self.entry_only:
                                params = filter_entry_only_params(strategy, params)
                            result = loop.run_until_complete(
                                simulator.run_simulation(
                                    strategy_name=strategy,
                                    parameters=params,
                                    entry_only=self.entry_only,
                                    entry_side=side,
                                    entry_lookahead_mode=self.entry_lookahead_mode,
                                    entry_lookahead_bars=self.entry_lookahead_bars,
                                )
                            )
                            results.append(result)
                            if is_all:
                                self.partial_result.emit(result)
                        if self._cancelled:
                            break
                finally:
                    loop.close()

                if is_all:
                    self.finished.emit({"batch_done": True, "count": len(results)})
                else:
                    if len(results) == 1:
                        self.finished.emit(results[0])
                    else:
                        self.finished.emit(results)

            elif self.mode in ("grid", "bayesian"):
                # Optimization - optimizers are synchronous and manage their own event loops
                results: list[object] = []
                run_index = 0

                def progress_cb(current, total, best):
                    self.progress.emit(current, total, best)

                for strategy in strategies:
                    for side in sides:
                        if self._cancelled:
                            break

                        run_index += 1
                        self.strategy_started.emit(run_index, total_runs, strategy.value, side)
                        objective_metric = "entry_score" if self.entry_only else self.objective_metric
                        config = OptimizationConfig(
                            strategy_name=strategy,
                            objective_metric=objective_metric,
                            direction="maximize",
                            n_trials=self.opt_trials,
                            entry_only=self.entry_only,
                            entry_side=side,
                            entry_lookahead_mode=self.entry_lookahead_mode,
                            entry_lookahead_bars=self.entry_lookahead_bars,
                        )

                        if self.mode == "bayesian":
                            optimizer = BayesianOptimizer(self.data, self.symbol, config)
                        else:
                            optimizer = GridSearchOptimizer(self.data, self.symbol, config)

                        # Keep reference so we can cancel from UI thread
                        self._optimizer = optimizer

                        # Optimizers are now synchronous
                        if self.mode == "grid":
                            result = optimizer.optimize(
                                progress_callback=progress_cb,
                                max_combinations=self.opt_trials,
                            )
                        else:
                            result = optimizer.optimize(progress_callback=progress_cb)
                        results.append(result)
                        if is_all:
                            self.partial_result.emit(result)
                    if self._cancelled:
                        break

                if is_all:
                    self.finished.emit({"batch_done": True, "count": len(results)})
                else:
                    if len(results) == 1:
                        self.finished.emit(results[0])
                    else:
                        self.finished.emit(results)

        except Exception as e:
            logger.error("Simulation failed: %s", e, exc_info=True)
            self.error.emit(str(e))
        finally:
            self._optimizer = None
