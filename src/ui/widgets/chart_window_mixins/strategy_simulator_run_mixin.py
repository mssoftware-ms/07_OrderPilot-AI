from __future__ import annotations

import logging

from PyQt6.QtWidgets import QMessageBox
from .strategy_simulator_worker import SimulationWorker

logger = logging.getLogger(__name__)

class StrategySimulatorRunMixin:
    """StrategySimulatorRunMixin extracted from StrategySimulatorMixin."""
    def _on_run_simulation(self) -> None:
        """Run simulation with current settings."""
        # Get chart data
        if not hasattr(self, "chart_widget"):
            QMessageBox.warning(self, "Error", "No chart widget available")
            return

        data = self._get_chart_dataframe()
        if data is None or (hasattr(data, "empty") and data.empty):
            QMessageBox.warning(
                self, "Error", "No chart data available. Load a chart first."
            )
            return

        # Get symbol from chart_widget or ChartWindow
        symbol = self._get_simulation_symbol()

        # Get current parameters
        (
            params,
            strategy_name,
            entry_only,
            entry_lookahead_mode,
            entry_lookahead_bars,
            objective_metric,
        ) = self._collect_simulation_params()
        self._prepare_simulation_run(entry_only)

        # Determine mode
        mode = self._resolve_simulation_mode()
        self._current_simulation_mode = mode
        if entry_only and mode == "manual" and self.simulator_opt_trials_spin.value() > 1:
            self._append_simulator_log(
                "Entry-Only: Manual ignores trials. Switch to Grid/Bayesian to use trials."
            )

        # Disable UI
        self._set_simulation_ui_state()

        self._log_simulation_start(
            mode,
            strategy_name,
            entry_only,
            objective_metric,
            entry_lookahead_mode,
            data,
            symbol,
        )

        # Create worker
        self._current_worker = self._create_simulation_worker(
            data=data,
            symbol=symbol,
            strategy_name=strategy_name,
            parameters=params,
            mode=mode,
            opt_trials=self.simulator_opt_trials_spin.value(),
            objective_metric=objective_metric,
            entry_only=entry_only,
            entry_lookahead_mode=entry_lookahead_mode,
            entry_lookahead_bars=entry_lookahead_bars,
        )
        self._wire_simulation_worker(self._current_worker)
        self._current_worker.start()

    def _get_chart_dataframe(self):
        if hasattr(self.chart_widget, "data") and self.chart_widget.data is not None:
            return self.chart_widget.data
        if hasattr(self.chart_widget, "get_dataframe"):
            return self.chart_widget.get_dataframe()
        if hasattr(self.chart_widget, "_df"):
            return self.chart_widget._df
        return None

    def _get_simulation_symbol(self) -> str:
        symbol = getattr(self, "symbol", "UNKNOWN")
        if hasattr(self.chart_widget, "current_symbol") and self.chart_widget.current_symbol:
            return self.chart_widget.current_symbol
        if hasattr(self.chart_widget, "symbol"):
            return self.chart_widget.symbol
        return symbol

    def _collect_simulation_params(self):
        params = self._get_simulator_parameters()
        strategy_name = self._get_simulator_strategy_name()
        entry_only = self._is_entry_only_selected()
        entry_lookahead_mode = self._get_entry_lookahead_mode()
        entry_lookahead_bars = self._get_entry_lookahead_bars()
        objective_metric = "entry_score" if entry_only else self._get_selected_objective_metric()
        self._current_objective_metric = objective_metric
        self._current_entry_only = entry_only
        return (
            params,
            strategy_name,
            entry_only,
            entry_lookahead_mode,
            entry_lookahead_bars,
            objective_metric,
        )

    def _prepare_simulation_run(self, entry_only: bool) -> None:
        if hasattr(self, "simulator_log_view"):
            self.simulator_log_view.clear()
        if self._is_all_strategy_selected():
            self._all_run_active = True
            self._all_run_restore_index = self.simulator_strategy_combo.currentIndex()
            self.simulator_params_group.setEnabled(False)
            self.simulator_strategy_combo.setEnabled(False)

    def _resolve_simulation_mode(self) -> str:
        mode_id = self.simulator_opt_mode_group.checkedId()
        mode_map = {0: "manual", 1: "grid", 2: "bayesian"}
        return mode_map.get(mode_id, "manual")

    def _set_simulation_ui_state(self) -> None:
        self.simulator_run_btn.setEnabled(False)
        self.simulator_stop_btn.setEnabled(True)
        self.simulator_progress.setVisible(True)
        self.simulator_progress.setValue(0)
        self.simulator_status_label.setText("Running simulation...")

    def _log_simulation_start(
        self,
        mode: str,
        strategy_name: str,
        entry_only: bool,
        objective_metric: str,
        entry_lookahead_mode: str,
        data,
        symbol: str,
    ) -> None:
        objective_label = self._get_objective_label(objective_metric)
        entry_label = "entry-only" if entry_only else "full"
        side_label = "long+short" if entry_only else "long"
        trials = self.simulator_opt_trials_spin.value()

        self._log_simulator_to_ki(
            "START",
            f"Running {mode} simulation: {strategy_name}, "
            f"mode: {entry_label} ({side_label}), objective: {objective_label}, "
            f"lookahead: {entry_lookahead_mode}, "
            f"trials: {trials}, "
            f"data rows: {len(data)}, symbol: {symbol}"
        )
        self._append_simulator_log(
            f"START | {mode} | {strategy_name} | {entry_label} ({side_label}) | "
            f"{objective_label} | lookahead={entry_lookahead_mode} | "
            f"trials={trials}"
        )

    def _create_simulation_worker(self, **kwargs) -> SimulationWorker:
        return SimulationWorker(**kwargs)

    def _wire_simulation_worker(self, worker: SimulationWorker) -> None:
        worker.finished.connect(self._on_simulation_finished)
        worker.partial_result.connect(self._on_simulation_partial_result)
        worker.progress.connect(self._on_simulation_progress)
        worker.strategy_started.connect(self._on_simulation_strategy_started)
        worker.error.connect(self._on_simulation_error)
    def _on_stop_simulation(self) -> None:
        """Stop running simulation."""
        if self._current_worker:
            # Signal cancellation; keep reference so thread can exit cleanly
            self._current_worker.cancel()
            self.simulator_status_label.setText("Stopping...")
    def _on_simulation_progress(self, current: int, total: int, best: float) -> None:
        """Update progress bar."""
        pct = int((current / total) * 100) if total > 0 else 0
        self.simulator_progress.setValue(pct)
        strategy_prefix = ""
        if self._current_sim_strategy_name:
            index = self._current_sim_strategy_index or 1
            total_strategies = self._current_sim_strategy_total or 1
            display_name = self._get_strategy_display_name(self._current_sim_strategy_name)
            if self._current_entry_only and self._current_sim_strategy_side:
                side_label = self._current_sim_strategy_side.upper()
                strategy_prefix = f"{index}/{total_strategies} {display_name} {side_label} | "
            else:
                strategy_prefix = f"{index}/{total_strategies} {display_name} | "
        objective_label = self._get_objective_label(self._current_objective_metric or "score")
        self.simulator_status_label.setText(
            f"{strategy_prefix}Trial {current}/{total} | Best {objective_label}: {best:.4f}"
        )
        log_prefix = strategy_prefix.replace(" | ", " ").strip()
        self._append_simulator_log(
            f"{log_prefix}Trial {current}/{total} | Best {objective_label}: {best:.4f}".strip()
        )
    def _on_simulation_finished(self, result) -> None:
        """Handle simulation completion."""
        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)
        self._finalize_all_run()

        if isinstance(result, dict) and result.get("batch_done"):
            count = result.get("count", 0)
            label = "runs" if self._current_entry_only else "strategies"
            status_msg = f"Completed batch run: {count} {label}"
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)
            self._append_simulator_log(status_msg)
            self._append_simulator_log(status_msg)
        elif isinstance(result, list):
            for item in result:
                self._handle_simulation_result(item)

            label = "runs" if self._current_entry_only else "strategies"
            status_msg = f"Completed batch run: {len(result)} {label}"
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)
        else:
            self._handle_simulation_result(result)

        self.simulator_export_btn.setEnabled(bool(self._simulation_results))
        # Ensure thread is fully stopped before dropping reference
        self._cleanup_simulation_worker(wait_ms=200)
    def _handle_simulation_result(self, result) -> None:
        """Handle a single simulation or optimization result."""
        from src.core.simulator import SimulationResult, OptimizationRun

        if isinstance(result, SimulationResult):
            self._handle_simulation_run_result(result)

        elif isinstance(result, OptimizationRun):
            self._handle_optimization_result(result)

    def _handle_simulation_run_result(self, result) -> None:
        self._simulation_results.append(result)
        objective_label = self._resolve_result_objective_label(result)
        self._add_result_to_table(result, objective_label=objective_label)
        status_msg = self._build_simulation_status(result)
        self.simulator_status_label.setText(status_msg)
        self._log_simulator_to_ki("OK", status_msg)

    def _resolve_result_objective_label(self, result) -> str:
        if result.entry_only:
            return self._get_objective_label("entry_score")
        if self._current_simulation_mode == "manual":
            return "Manual"
        return self._get_objective_label(self._current_objective_metric or "score")

    def _build_simulation_status(self, result) -> str:
        if result.entry_only:
            entry_score = result.entry_score or 0.0
            return f"Entry-Only: {result.entry_count} entries, Score: {entry_score:.1f}"
        return f"Completed: {result.total_trades} trades, P&L: {result.total_pnl:.2f}"

    def _handle_optimization_result(self, result) -> None:
        self._last_optimization_run = result
        self._log_optimization_errors(result)

        if result.total_trials == 0:
            self._handle_no_trials(result)
            return

        seen_params = self._add_best_result(result)
        self._add_top_trials(result, seen_params)
        status_msg = self._build_optimization_status(result)
        self.simulator_status_label.setText(status_msg)
        self._log_simulator_to_ki("OK", status_msg)
        self._append_simulator_log(status_msg)

    def _log_optimization_errors(self, result) -> None:
        if not result.errors:
            return
        for error in result.errors[:5]:
            self._log_simulator_to_ki("ERROR", error)
        if len(result.errors) > 5:
            self._log_simulator_to_ki(
                "ERROR", f"... and {len(result.errors) - 5} more errors"
            )

    def _handle_no_trials(self, result) -> None:
        error_msg = "No optimization trials completed successfully."
        if result.errors:
            error_msg += f" First error: {result.errors[0]}"
        self.simulator_status_label.setText(f"Error: {error_msg}")
        self._log_simulator_to_ki("ERROR", error_msg)
        QMessageBox.warning(
            self,
            "Optimization Warning",
            "No trials completed.\n\nCheck KI Logs for error details.",
        )

    def _add_best_result(self, result) -> set[tuple]:
        seen_params: set[tuple] = set()
        if not result.best_result:
            return seen_params
        self._simulation_results.append(result.best_result)
        objective_label = self._get_objective_label(result.objective_metric)
        self._add_result_to_table(
            result.best_result,
            objective_label=objective_label,
            entry_side=result.entry_side,
        )
        best_side = (
            result.best_result.entry_side
            if getattr(result.best_result, "entry_only", False)
            else None
        )
        seen_params.add(
            self._make_param_fingerprint(
                result.strategy_name,
                result.best_result.parameters,
                best_side,
            )
        )
        return seen_params

    def _add_top_trials(self, result, seen_params: set[tuple]) -> None:
        objective_label = self._get_objective_label(result.objective_metric)
        for trial in result.get_top_n_trials(10):
            trial_side = trial.entry_side if result.entry_only else None
            fingerprint = self._make_param_fingerprint(
                result.strategy_name, trial.parameters, trial_side
            )
            if fingerprint in seen_params:
                continue
            seen_params.add(fingerprint)
            self._add_trial_to_table(
                trial,
                result.strategy_name,
                objective_label=objective_label,
                entry_side=result.entry_side,
            )

    def _build_optimization_status(self, result) -> str:
        status_msg = (
            f"Optimization complete: {result.total_trials} trials, "
            f"Best score: {result.best_score:.4f}"
        )
        if result.entry_only:
            status_msg += f" ({result.entry_side.upper()})"
        if result.errors:
            status_msg += f" ({len(result.errors)} failed)"
        return status_msg
    def _on_simulation_error(self, error_msg: str) -> None:
        """Handle simulation error."""
        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)
        self.simulator_status_label.setText(f"Error: {error_msg}")
        self._append_simulator_log(f"ERROR: {error_msg}")
        self._finalize_all_run()

        # Log to KI Logs
        self._log_simulator_to_ki("ERROR", f"Simulation failed: {error_msg}")

        QMessageBox.critical(self, "Simulation Error", error_msg)
        self._cleanup_simulation_worker(wait_ms=200)
    def _on_simulation_partial_result(self, result) -> None:
        """Handle partial results for batch runs."""
        self._handle_simulation_result(result)
    def _on_simulation_strategy_started(
        self,
        index: int,
        total: int,
        strategy_name: str,
        side: str,
    ) -> None:
        """Update UI when a strategy run starts."""
        self._current_sim_strategy_name = strategy_name
        self._current_sim_strategy_index = index
        self._current_sim_strategy_total = total
        self._current_sim_strategy_side = side
        if self._all_run_active:
            combo_index = self._get_strategy_index_by_name(strategy_name)
            if combo_index is not None:
                self.simulator_strategy_combo.setCurrentIndex(combo_index)
            try:
                from src.core.simulator import StrategyName, get_default_parameters, load_strategy_params

                strategy_enum = StrategyName(strategy_name)
                saved_params = load_strategy_params(strategy_name)
                seed_params = saved_params or get_default_parameters(strategy_enum)
                self._apply_params_to_widgets(seed_params)
                seed_source = "saved" if saved_params else "default"
                self._append_simulator_log(
                    f"Seed params: {seed_source} ({strategy_name})"
                )
            except Exception:
                pass
        display_name = self._get_strategy_display_name(strategy_name)
        mode = self._current_simulation_mode or "manual"
        side_label = ""
        if self._current_entry_only and side:
            side_label = f" {side.upper()}"
        status_msg = f"Running {index}/{total}: {display_name}{side_label} ({mode})"
        self.simulator_status_label.setText(status_msg)
        self._log_simulator_to_ki("INFO", status_msg)
        self._append_simulator_log(status_msg)
    def _cleanup_simulation_worker(self, wait_ms: int = 0, cancel: bool = False) -> None:
        """Safely stop and dispose the simulation worker thread.

        Args:
            wait_ms: How long to wait for the thread to finish. 0 = no wait.
            cancel: Whether to request cancellation first.
        """
        worker = self._current_worker
        if not worker:
            return

        if cancel:
            worker.cancel()

        finished = not worker.isRunning()
        if wait_ms and not finished:
            finished = worker.wait(wait_ms)

        if finished:
            worker.deleteLater()
            self._current_worker = None
        else:
            logger.warning("Simulation worker still running after %d ms", wait_ms)
    def _finalize_all_run(self) -> None:
        """Restore UI state after ALL batch runs."""
        if not self._all_run_active:
            return
        self._all_run_active = False
        self.simulator_strategy_combo.setEnabled(True)
        if self._all_run_restore_index is not None:
            self.simulator_strategy_combo.setCurrentIndex(self._all_run_restore_index)
        self._all_run_restore_index = None
        self.simulator_params_group.setEnabled(not self._is_all_strategy_selected())
    def _log_simulator_to_ki(self, entry_type: str, message: str) -> None:
        """Log simulator messages to KI Logs tab.

        Uses _add_ki_log_entry from BotDisplayManagerMixin if available.
        """
        prefixed_msg = f"[Simulator] {message}"
        if hasattr(self, '_add_ki_log_entry'):
            self._add_ki_log_entry(entry_type, prefixed_msg)
        else:
            # Fallback to standard logging
            logger.info(f"[{entry_type}] {prefixed_msg}")
