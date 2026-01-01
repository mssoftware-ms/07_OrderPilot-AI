from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem

class StrategySimulatorResultsMixin:
    """StrategySimulatorResultsMixin extracted from StrategySimulatorMixin."""
    def _append_simulator_log(self, message: str) -> None:
        if not hasattr(self, "simulator_log_view"):
            return
        if message:
            self.simulator_log_view.appendPlainText(message)
    def _format_entry_points(self, points: list[tuple] | None) -> str:
        if not points:
            return ""
        formatted = []
        for item in points:
            if len(item) == 3:
                price, ts, _score = item
            else:
                price, ts = item
            formatted.append(f"{price:.3f}/{ts.strftime('%H:%M:%S')}")
        return ";".join(formatted)
    def _calculate_score(self, result) -> int:
        """Calculate performance score from -1000 to +1000.

        Based on P&L% where:
        - +100% profit = +1000 score
        - -100% loss = -1000 score
        """
        if getattr(result, "entry_only", False):
            entry_score = result.entry_score or 0.0
            return int(round(entry_score))
        pnl_pct = result.total_pnl_pct
        # Clamp to -100% to +100% range, then scale to -1000 to +1000
        score = int(max(-1000, min(1000, pnl_pct * 10)))
        return score
    def _add_result_to_table(
        self,
        result,
        objective_label: str | None = None,
        entry_side: str | None = None,
    ) -> None:
        """Add simulation result to results table."""
        table = self.simulator_results_table
        was_sorting = table.isSortingEnabled()
        if was_sorting:
            table.setSortingEnabled(False)

        row = table.rowCount()
        table.insertRow(row)

        # Format parameters (ALL parameters)
        params_full = ", ".join(
            f"{k}={v}" for k, v in result.parameters.items()
        )

        # Calculate score (-1000 to +1000)
        score = self._calculate_score(result)

        if objective_label is None:
            if getattr(result, "entry_only", False):
                objective_label = self._get_objective_label("entry_score")
            elif self._current_simulation_mode == "manual":
                objective_label = "Manual"
            else:
                objective_label = self._get_objective_label(self._current_objective_metric or "score")

        if getattr(result, "entry_only", False):
            ls_value = entry_side or getattr(result, "entry_side", None) or "long"
            entry_points = getattr(result, "entry_points", None)
            entry_display = self._format_entry_points(entry_points)
            if not entry_display:
                entry_price = getattr(result, "entry_best_price", None)
                entry_time = getattr(result, "entry_best_time", None)
                if entry_price is not None and entry_time is not None:
                    entry_display = f"{entry_price:.3f}/{entry_time.strftime('%H:%M:%S')}"
            prefix_items = [f"LS={ls_value}"]
            if entry_display:
                prefix_items.append(f"EP={entry_display}")
            prefix = ", ".join(prefix_items)
            params_full = f"{prefix}, {params_full}" if params_full else prefix

        items = [
            result.strategy_name,
            str(result.total_trades),
            f"{result.win_rate * 100:.1f}",
            f"{result.profit_factor:.2f}",
            f"{result.total_pnl:.2f}",  # P&L in Euro (based on 1000€ trades)
            f"{result.total_pnl_pct:.2f}",  # P&L % of invested capital
            f"{result.max_drawdown_pct:.1f}",
            str(score),  # Score instead of Sharpe
            objective_label,
            params_full,
        ]

        for col, value in enumerate(items):
            item = QTableWidgetItem(str(value))
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, result)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)

            # Color P&L column
            if col == 4:  # P&L € column
                try:
                    pnl = float(value)
                    if pnl > 0:
                        item.setBackground(Qt.GlobalColor.green)
                    elif pnl < 0:
                        item.setBackground(Qt.GlobalColor.red)
                except ValueError:
                    pass

        if was_sorting:
            table.setSortingEnabled(True)

            # Color Score column
            if col == 7:  # Score column
                try:
                    sc = int(value)
                    if sc > 0:
                        item.setBackground(Qt.GlobalColor.green)
                    elif sc < 0:
                        item.setBackground(Qt.GlobalColor.red)
                except ValueError:
                    pass
    def _add_trial_to_table(
        self,
        trial,
        strategy_name: str,
        objective_label: str | None = None,
        entry_side: str | None = None,
    ) -> None:
        """Add optimization trial to results table (no detailed trade data)."""
        table = self.simulator_results_table
        was_sorting = table.isSortingEnabled()
        if was_sorting:
            table.setSortingEnabled(False)

        row = table.rowCount()
        table.insertRow(row)

        # Format ALL parameters
        params_full = ", ".join(
            f"{k}={v}" for k, v in trial.parameters.items()
        )

        metrics = trial.metrics
        pnl_pct = metrics.get("total_pnl_pct", 0)

        # Calculate score from P&L% (-1000 to +1000)
        entry_score = metrics.get("entry_score")
        if entry_score is not None:
            score = int(round(entry_score))
        else:
            score = int(max(-1000, min(1000, pnl_pct * 10)))

        if objective_label is None:
            objective_label = self._get_objective_label(self._current_objective_metric or "score")

        ls_value = entry_side or "long"
        entry_display = ""
        if entry_score is not None:
            entry_points = metrics.get("entry_points")
            if entry_points:
                entry_display = str(entry_points)
            else:
                entry_price = metrics.get("entry_best_price")
                entry_time = metrics.get("entry_best_time")
                if entry_price is not None and entry_time:
                    try:
                        entry_display = f"{float(entry_price):.3f}/{entry_time}"
                    except (TypeError, ValueError):
                        entry_display = f"{entry_price}/{entry_time}"
            prefix_items = [f"LS={ls_value}"]
            if entry_display:
                prefix_items.append(f"EP={entry_display}")
            prefix = ", ".join(prefix_items)
            params_full = f"{prefix}, {params_full}" if params_full else prefix

        # P&L in Euro (assuming 1000€ initial capital, pnl_pct is already percentage)
        pnl_euro = pnl_pct * 10  # 1% of 1000€ = 10€

        items = [
            strategy_name,
            str(int(metrics.get("total_trades", 0))),
            f"{metrics.get('win_rate', 0) * 100:.1f}",
            f"{metrics.get('profit_factor', 0):.2f}",
            f"{pnl_euro:.2f}",  # P&L in Euro
            f"{pnl_pct:.2f}",  # P&L %
            f"{metrics.get('max_drawdown_pct', 0):.1f}",
            str(score),  # Score instead of Sharpe
            objective_label,
            params_full,
        ]

        for col, value in enumerate(items):
            item = QTableWidgetItem(str(value))
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, None)
                item.setData(Qt.ItemDataRole.UserRole + 1, trial)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)

            # Color P&L column
            if col == 4:
                try:
                    pnl = float(value)
                    if pnl > 0:
                        item.setBackground(Qt.GlobalColor.green)
                    elif pnl < 0:
                        item.setBackground(Qt.GlobalColor.red)
                except ValueError:
                    pass

        if was_sorting:
            table.setSortingEnabled(True)

            # Color Score column
            if col == 7:
                try:
                    sc = int(value)
                    if sc > 0:
                        item.setBackground(Qt.GlobalColor.green)
                    elif sc < 0:
                        item.setBackground(Qt.GlobalColor.red)
                except ValueError:
                    pass
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
    def _on_toggle_entry_points(self, checked: bool) -> None:
        if not hasattr(self, "chart_widget"):
            return
        if checked:
            self._update_entry_points_from_selection()
        else:
            if hasattr(self.chart_widget, "clear_bot_markers"):
                self.chart_widget.clear_bot_markers()
    def _update_entry_points_from_selection(self) -> None:
        """Show entry-only points for the selected row (if available)."""
        if not hasattr(self, "chart_widget"):
            return
        selected = self.simulator_results_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        result = self._get_result_from_row(row)
        entry_points = []
        side = "long"
        default_score = 0.0
        if result and getattr(result, "entry_only", False):
            entry_points = getattr(result, "entry_points", None) or []
            side = getattr(result, "entry_side", "long")
            default_score = float(result.entry_score or 0.0)
        else:
            trial = self._get_trial_from_row(row)
            if trial and getattr(trial, "entry_points", None):
                entry_points = getattr(trial, "entry_points") or []
                side = getattr(trial, "entry_side", "long")
                try:
                    default_score = float(trial.score)
                except Exception:
                    default_score = 0.0

        if not entry_points:
            if hasattr(self.chart_widget, "clear_bot_markers"):
                self.chart_widget.clear_bot_markers()
            self.simulator_status_label.setText("No entry-only data for selected row")
            return

        if hasattr(self.chart_widget, "clear_bot_markers"):
            self.chart_widget.clear_bot_markers()

        min_score = getattr(self, "_entry_marker_min_score", 50.0)
        shown = 0
        if hasattr(self.chart_widget, "add_entry_confirmed"):
            for item in entry_points:
                if len(item) == 3:
                    price, ts, entry_score = item
                else:
                    price, ts = item
                    entry_score = default_score
                try:
                    score_val = float(entry_score)
                except Exception:
                    score_val = 0.0
                if score_val < min_score:
                    continue
                self.chart_widget.add_entry_confirmed(ts, float(price), side, score_val)
                shown += 1

        if shown == 0:
            self.simulator_status_label.setText(
                f"No entry points with score >= {min_score:.0f}"
            )

        # Zoom / refresh view if supported
        if hasattr(self.chart_widget, "zoom_to_fit_all"):
            try:
                self.chart_widget.zoom_to_fit_all()
            except Exception:
                pass
        elif hasattr(self.chart_widget, "zoom_to_fit"):
            try:
                self.chart_widget.zoom_to_fit()
            except Exception:
                pass
    def _on_show_simulation_markers(self) -> None:
        """Show entry/exit markers on chart for selected result."""
        selected = self.simulator_results_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        result = self._get_result_from_row(row)
        if result is None:
            QMessageBox.warning(
                self, "Warning",
                "Keine Detail-Daten für diese Zeile verfügbar.\n\n"
                "Optimization-Trials haben nur Metriken, keine Trade-Details.\n"
                "Nur die 'Best Result'-Zeile hat vollständige Trade-Daten."
            )
            return

        # Get chart and clear existing markers
        if hasattr(self, "chart_widget"):
            # Clear previous simulation markers
            if hasattr(self.chart_widget, "clear_bot_markers"):
                self.chart_widget.clear_bot_markers()

            # Add entry/exit points
            for trade in result.trades:
                side = trade.side

                # Entry marker
                if hasattr(self.chart_widget, "add_entry_confirmed"):
                    self.chart_widget.add_entry_confirmed(
                        int(trade.entry_time.timestamp()),
                        trade.entry_price,
                        side,
                        score=0,
                    )

                # Exit marker
                if hasattr(self.chart_widget, "add_exit_marker"):
                    self.chart_widget.add_exit_marker(
                        int(trade.exit_time.timestamp()),
                        trade.exit_price,
                        side,
                        trade.exit_reason,
                    )

            self.simulator_status_label.setText(
                f"Showing {len(result.trades)} trades on chart"
            )
    def _on_clear_simulation_markers(self) -> None:
        """Clear simulation markers from chart."""
        if hasattr(self, "chart_widget") and hasattr(
            self.chart_widget, "clear_bot_markers"
        ):
            self.chart_widget.clear_bot_markers()
            self.simulator_status_label.setText("Markers cleared")
    def _on_export_simulation_xlsx(self) -> None:
        """Export results to Excel file."""
        # Check if table has data (even if _simulation_results is empty)
        table_row_count = self.simulator_results_table.rowCount()
        if table_row_count == 0 and not self._simulation_results:
            QMessageBox.warning(self, "Warning", "No results to export")
            return

        default_name = f"strategy_simulation_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Simulation Results",
            default_name,
            "Excel Files (*.xlsx)",
        )
        if not filepath:
            return

        try:
            from src.core.simulator import export_simulation_results

            # Extract table data from UI
            ui_table_data = self._extract_table_data()

            saved_path = export_simulation_results(
                results=self._simulation_results,
                filepath=filepath,
                optimization_run=self._last_optimization_run,
                ui_table_data=ui_table_data,
            )
            QMessageBox.information(
                self,
                "Export Complete",
                f"Results exported to:\n{saved_path}",
            )
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"openpyxl is required for Excel export.\n\n{e}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
    def _extract_table_data(self) -> list[list[str]]:
        """Extract all data from the results table.

        Returns:
            List of rows, each row is a list of cell values.
        """
        table = self.simulator_results_table
        row_count = table.rowCount()
        col_count = table.columnCount()

        table_data = []
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = table.item(row, col)
                value = item.text() if item else ""
                row_data.append(value)
            table_data.append(row_data)

        return table_data
    def _on_clear_simulation_results(self) -> None:
        """Clear all simulation results."""
        self._simulation_results.clear()
        self._last_optimization_run = None
        self.simulator_results_table.setRowCount(0)
        self.simulator_export_btn.setEnabled(False)
        self.simulator_show_markers_btn.setEnabled(False)
        self.simulator_status_label.setText("Results cleared")
    def _get_result_from_row(self, row: int) -> object | None:
        """Get the SimulationResult stored on the row, if any."""
        item = self.simulator_results_table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)
    def _get_trial_from_row(self, row: int) -> object | None:
        """Get OptimizationTrial stored on the row, if any."""
        item = self.simulator_results_table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole + 1)
    def _get_strategy_display_name(self, strategy_name: str) -> str:
        """Get display name for a strategy."""
        from src.core.simulator import StrategyName

        try:
            return StrategyName.display_names().get(strategy_name, strategy_name)
        except Exception:
            return strategy_name
