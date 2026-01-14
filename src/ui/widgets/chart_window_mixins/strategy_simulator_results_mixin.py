from __future__ import annotations

import logging
import pandas as pd
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class StrategySimulatorResultsMixin:
    """Result handling and optimization"""

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

    def _finalize_all_run(self) -> None:
        """Restore UI state after ALL batch runs."""
        if not self._all_run_active:
            return
        self._all_run_active = False
        self.simulator_strategy_combo.setEnabled(True)
        if self._all_run_restore_index is not None:
            self.simulator_strategy_combo.setCurrentIndex(self._all_run_restore_index)
        self._all_run_restore_index = None

    def _on_simulator_result_selected(self) -> None:
        """Handle result selection in table."""
        selected = self.simulator_results_table.selectedItems()
        if not selected:
            self.simulator_show_markers_btn.setEnabled(False)
            if hasattr(self, "simulator_show_entry_points_checkbox"):
                if self.simulator_show_entry_points_checkbox.isChecked():
                    self._update_entry_points_from_selection()
            return

        row = selected[0].row()
        result = self._get_result_from_row(row)
        self.simulator_show_markers_btn.setEnabled(result is not None)
        if hasattr(self, "simulator_show_entry_points_checkbox"):
            if self.simulator_show_entry_points_checkbox.isChecked():
                self._update_entry_points_from_selection()

    def _get_result_from_row(self, row: int):
        """Get simulation result from table row index."""
        if 0 <= row < len(self._simulation_results):
            return self._simulation_results[row]
        return None

    def _update_entry_points_from_selection(self) -> None:
        """Update entry points display based on selected result."""
        if not hasattr(self, "chart_widget"):
            return
        # Implementation depends on chart_widget having _plot_entry_points
        if hasattr(self, "_plot_entry_points"):
            self._plot_entry_points()

