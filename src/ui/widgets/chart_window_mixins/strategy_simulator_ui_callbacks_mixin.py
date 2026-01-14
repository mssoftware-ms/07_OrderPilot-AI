from __future__ import annotations

import logging
import pandas as pd
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class StrategySimulatorUICallbacksMixin:
    """UI updates, progress tracking, and callbacks"""

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
        time_range_name: str,
        data,
        symbol: str,
    ) -> None:
        objective_label = self._get_objective_label(objective_metric)
        entry_label = "entry-only" if entry_only else "full"
        side_label = "long+short" if entry_only else "long"
        trials = self.simulator_opt_trials_spin.value()
        timeframe = self._get_chart_timeframe()

        self._log_simulator_to_ki(
            "START",
            f"Running {mode} simulation: {strategy_name}, "
            f"mode: {entry_label} ({side_label}), objective: {objective_label}, "
            f"Zeitraum: {time_range_name}, Timeframe: {timeframe}, "
            f"trials: {trials}, "
            f"data rows: {len(data)}, symbol: {symbol}"
        )
        self._append_simulator_log(
            f"START | {mode} | {strategy_name} | {entry_label} ({side_label}) | "
            f"{objective_label} | {time_range_name} ({timeframe}) | "
            f"trials={trials}"
        )

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

    def _on_simulation_partial_result(self, result) -> None:
        """Handle partial results for batch runs."""

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

    def _on_show_test_parameters(self) -> None:
        """Show popup dialog with all current test parameters."""
        from .strategy_simulator_params_dialog import TestParametersDialog

        # Collect all parameters from various sources
        parameters = self._collect_all_test_parameters()

        # Create and show dialog
        dialog = TestParametersDialog(self, parameters)
        dialog.exec()

