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
        # Auto-strategy mode
        auto_strategy: bool = False,
        # ATR-based SL/TP from Bot-Tab settings
        sl_atr_multiplier: float = 0.0,
        tp_atr_multiplier: float = 0.0,
        atr_period: int = 14,
        # Trailing Stop from Bot-Tab settings
        trailing_stop_enabled: bool = False,
        trailing_stop_atr_multiplier: float = 1.5,
        trailing_stop_mode: str = "ATR",  # PCT, ATR, SWING
        trailing_pct_distance: float = 1.0,  # Distance in % for PCT mode
        trailing_activation_pct: float = 5.0,  # Activation threshold
        # Regime-adaptive trailing
        regime_adaptive: bool = True,
        atr_trending_mult: float = 1.2,
        atr_ranging_mult: float = 2.0,
        # Trading fees
        maker_fee_pct: float = 0.0002,
        taker_fee_pct: float = 0.0006,
        # Trade direction filter
        trade_direction: str = "BOTH",
        # Capital and position sizing
        initial_capital: float = 1000.0,
        position_size_pct: float = 1.0,
        # Leverage
        leverage: float = 1.0,
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
        # Auto-strategy mode
        self.auto_strategy = auto_strategy
        # ATR-based SL/TP from Bot-Tab settings
        self.sl_atr_multiplier = sl_atr_multiplier
        self.tp_atr_multiplier = tp_atr_multiplier
        self.atr_period = atr_period
        # Trailing Stop from Bot-Tab settings
        self.trailing_stop_enabled = trailing_stop_enabled
        self.trailing_stop_atr_multiplier = trailing_stop_atr_multiplier
        self.trailing_stop_mode = trailing_stop_mode  # PCT, ATR, SWING
        self.trailing_pct_distance = trailing_pct_distance
        self.trailing_activation_pct = trailing_activation_pct
        # Regime-adaptive trailing
        self.regime_adaptive = regime_adaptive
        self.atr_trending_mult = atr_trending_mult
        self.atr_ranging_mult = atr_ranging_mult
        # Trading fees
        self.maker_fee_pct = maker_fee_pct
        self.taker_fee_pct = taker_fee_pct
        # Trade direction filter
        self.trade_direction = trade_direction
        # Capital and position sizing
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        # Leverage
        self.leverage = leverage
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
            strategies = self._resolve_strategies(StrategyName, is_all)
            sides = self._resolve_sides()
            total_runs = len(strategies) * len(sides)

            if self.mode == "manual":
                results = self._run_manual(
                    StrategySimulator,
                    get_default_parameters,
                    load_strategy_params,
                    filter_entry_only_params,
                    strategies,
                    sides,
                    total_runs,
                    is_all,
                )
                self._emit_finished(results, is_all)

            elif self.mode in ("grid", "bayesian"):
                results = self._run_optimization(
                    BayesianOptimizer,
                    GridSearchOptimizer,
                    OptimizationConfig,
                    strategies,
                    sides,
                    total_runs,
                    is_all,
                )
                self._emit_finished(results, is_all)

        except Exception as e:
            logger.error("Simulation failed: %s", e, exc_info=True)
            self.error.emit(str(e))
        finally:
            self._optimizer = None

    def _resolve_strategies(self, StrategyName, is_all: bool):
        if is_all:
            return list(StrategyName)
        # Map catalog strategy name to StrategyName enum
        strategy_enum = self._catalog_to_strategy_enum(StrategyName, self.strategy_name)
        return [strategy_enum]

    def _catalog_to_strategy_enum(self, StrategyName, catalog_name: str):
        """Map catalog strategy name to StrategyName enum."""
        # Mapping from catalog strategy names to simulator family enums
        catalog_to_enum = {
            "breakout_volatility": StrategyName.BREAKOUT,
            "breakout_momentum": StrategyName.BREAKOUT,
            "momentum_macd": StrategyName.MOMENTUM,
            "mean_reversion_bb": StrategyName.MEAN_REVERSION,
            "mean_reversion_rsi": StrategyName.MEAN_REVERSION,
            "trend_following_conservative": StrategyName.TREND_FOLLOWING,
            "trend_following_aggressive": StrategyName.TREND_FOLLOWING,
            "scalping_range": StrategyName.SCALPING,
            "sideways_range_bounce": StrategyName.SIDEWAYS_RANGE,
        }
        # Try catalog mapping first, then try direct enum conversion for legacy names
        if catalog_name in catalog_to_enum:
            return catalog_to_enum[catalog_name]
        try:
            return StrategyName(catalog_name)
        except ValueError:
            logger.warning(f"Unknown strategy name: {catalog_name}, defaulting to TREND_FOLLOWING")
            return StrategyName.TREND_FOLLOWING

    def _resolve_sides(self) -> list[str]:
        return ["long", "short"] if self.entry_only else ["long"]

    def _emit_finished(self, results: list[object], is_all: bool) -> None:
        if is_all:
            self.finished.emit({"batch_done": True, "count": len(results)})
            return
        if len(results) == 1:
            self.finished.emit(results[0])
        else:
            self.finished.emit(results)

    def _run_manual(
        self,
        StrategySimulator,
        get_default_parameters,
        load_strategy_params,
        filter_entry_only_params,
        strategies,
        sides,
        total_runs: int,
        is_all: bool,
    ) -> list[object]:
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
                    params = self._resolve_parameters(
                        strategy,
                        is_all,
                        get_default_parameters,
                        load_strategy_params,
                    )
                    if self.entry_only:
                        params = filter_entry_only_params(strategy, params)
                    result = loop.run_until_complete(
                        simulator.run_simulation(
                            strategy_name=strategy,
                            parameters=params,
                            entry_only=self.entry_only,
                            entry_side=side,
                            # Capital and position sizing
                            initial_capital=self.initial_capital,
                            position_size_pct=self.position_size_pct,
                            # ATR-based SL/TP from Bot-Tab settings
                            sl_atr_multiplier=self.sl_atr_multiplier,
                            tp_atr_multiplier=self.tp_atr_multiplier,
                            atr_period=self.atr_period,
                            # Trailing Stop from Bot-Tab settings
                            trailing_stop_enabled=self.trailing_stop_enabled,
                            trailing_stop_atr_multiplier=self.trailing_stop_atr_multiplier,
                            trailing_stop_mode=self.trailing_stop_mode,
                            trailing_pct_distance=self.trailing_pct_distance,
                            trailing_activation_pct=self.trailing_activation_pct,
                            # Regime-adaptive trailing
                            regime_adaptive=self.regime_adaptive,
                            atr_trending_mult=self.atr_trending_mult,
                            atr_ranging_mult=self.atr_ranging_mult,
                            # Trading fees
                            maker_fee_pct=self.maker_fee_pct,
                            taker_fee_pct=self.taker_fee_pct,
                            # Trade direction filter
                            trade_direction=self.trade_direction,
                            # Leverage
                            leverage=self.leverage,
                        )
                    )
                    results.append(result)
                    if is_all:
                        self.partial_result.emit(result)
                if self._cancelled:
                    break
        finally:
            loop.close()
        return results

    def _resolve_parameters(
        self,
        strategy,
        is_all: bool,
        get_default_parameters,
        load_strategy_params,
    ) -> dict:
        if is_all:
            return load_strategy_params(strategy.value) or get_default_parameters(strategy)
        return self.parameters

    def _run_optimization(
        self,
        BayesianOptimizer,
        GridSearchOptimizer,
        OptimizationConfig,
        strategies,
        sides,
        total_runs: int,
        is_all: bool,
    ) -> list[object]:
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
                )

                optimizer = (
                    BayesianOptimizer(self.data, self.symbol, config)
                    if self.mode == "bayesian"
                    else GridSearchOptimizer(self.data, self.symbol, config)
                )

                self._optimizer = optimizer

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
        return results
