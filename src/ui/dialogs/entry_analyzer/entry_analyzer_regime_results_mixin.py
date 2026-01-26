"""Entry Analyzer - Regime Results Tab (Mixin).

Stufe-1: Regime-Optimierung - Tab 3/3
Provides UI for viewing and managing optimization results:
- Full results table (all trials, sortable)
- Row selection
- Export to JSON
- "Apply & Continue" to Stage 2 (Indicator Optimization)
- Draw selected regime on chart
"""

from __future__ import annotations

import json
import logging
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RegimeResultsMixin:
    """Mixin for Regime Results tab in Entry Analyzer.

    Provides:
        - Full results table with all optimization trials
        - Row selection and highlighting
        - Export selected result to JSON
        - "Apply & Continue" to Stage 2
        - Draw regime periods on chart
    """

    # Type hints for parent class attributes
    _regime_results_table: QTableWidget
    _regime_results_export_btn: QPushButton
    _regime_results_draw_btn: QPushButton
    _regime_results_apply_btn: QPushButton
    _regime_results_selected_label: QLabel

    def _setup_regime_results_tab(self, tab: QWidget) -> None:
        """Setup Regime Results tab with full results table and actions.

        Args:
            tab: QWidget to populate
        """
        layout = QVBoxLayout(tab)

        # Header with help button
        header_layout = QHBoxLayout()
        header = QLabel("Regime Optimization Results")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        # Help button for RegimeScore
        help_btn = QPushButton(get_icon("help"), "")
        help_btn.setToolTip("Open RegimeScore Help")
        help_btn.setFixedSize(28, 28)
        help_btn.clicked.connect(self._on_regime_score_help_clicked)
        header_layout.addWidget(help_btn)
        layout.addLayout(header_layout)

        # Selection Info
        self._regime_results_selected_label = QLabel("No result selected. Click a row to select.")
        self._regime_results_selected_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self._regime_results_selected_label)

        # Results Table (Dynamic columns - parameters added at runtime)
        self._regime_results_table = QTableWidget()
        self._regime_results_table.setColumnCount(6)  # Initial: Rank, Score, Selected, Regimes, Avg Duration, Switches
        self._regime_results_table.setHorizontalHeaderLabels(
            ["Rank", "Score", "Selected", "Regimes", "Avg Duration", "Switches"]
        )
        self._regime_results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self._regime_results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._regime_results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._regime_results_table.setSortingEnabled(True)
        self._regime_results_table.itemSelectionChanged.connect(
            self._on_regime_results_selection_changed
        )
        layout.addWidget(self._regime_results_table, stretch=1)

        # Action Buttons
        button_layout = QHBoxLayout()

        self._regime_results_draw_btn = QPushButton(get_icon("show_chart"), "Draw on Chart")
        self._regime_results_draw_btn.setEnabled(False)
        self._regime_results_draw_btn.clicked.connect(self._on_regime_results_draw)
        button_layout.addWidget(self._regime_results_draw_btn)

        self._regime_results_export_btn = QPushButton(get_icon("download"), "Export to JSON")
        self._regime_results_export_btn.setEnabled(False)
        self._regime_results_export_btn.clicked.connect(self._on_regime_results_export)
        button_layout.addWidget(self._regime_results_export_btn)

        button_layout.addStretch()

        self._regime_results_apply_btn = QPushButton(
            get_icon("check_circle"), "Apply & Continue to Stage 2 →"
        )
        self._regime_results_apply_btn.setProperty("class", "success")
        self._regime_results_apply_btn.setEnabled(False)
        self._regime_results_apply_btn.clicked.connect(self._on_regime_results_apply)
        button_layout.addWidget(self._regime_results_apply_btn)

        layout.addLayout(button_layout)

        # Info footer
        info_label = QLabel(
            "💡 Tip: Click on any row to select it. The selected regime will be used for Stage 2 (Indicator Optimization)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-size: 9pt; padding: 5px;")
        layout.addWidget(info_label)

    def _populate_regime_results_table(self) -> None:
        """Populate results table with all optimization results.

        DYNAMIC column generation - NO hardcoded parameter names!
        Structure: Rank | Score | Selected | [Dynamic Params] | Regimes | Avg Duration | Switches
        """
        from PyQt6.QtWidgets import QApplication

        if not hasattr(self, "_regime_opt_all_results"):
            logger.warning("No optimization results available")
            return

        results = self._regime_opt_all_results

        if not results:
            logger.warning("No results to display")
            return

        # DYNAMIC COLUMN GENERATION: Get parameter names from first result
        first_result = results[0]
        params_dict = first_result.get("params", {})
        param_names = sorted(params_dict.keys())  # Sort for consistent order

        # Build column headers: Rank, Total, Selected, [Params], Regimes, Avg Duration, Switches
        # Note: Score components (Sep, Coh, Fid, Bnd, Cov) removed - legacy scoring system
        headers = ["Rank", "Total", "Selected"] + param_names + ["Regimes", "Avg Duration", "Switches"]

        # Update table structure
        self._regime_results_table.setColumnCount(len(headers))
        self._regime_results_table.setHorizontalHeaderLabels(headers)

        # Configure header resize modes
        header = self._regime_results_table.horizontalHeader()
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        logger.info(f"Dynamic results table: {len(headers)} columns ({len(param_names)} parameters)")

        # Disable visual updates for better performance
        self._regime_results_table.setUpdatesEnabled(False)
        self._regime_results_table.setSortingEnabled(False)
        self._regime_results_table.setRowCount(len(results))

        for row, result in enumerate(results):
            # Process events every 5 rows to keep spinner animation smooth
            if row > 0 and row % 5 == 0:
                QApplication.processEvents()
                # Update waiting dialog with progress
                if hasattr(self, "_waiting_dialog") and self._waiting_dialog and self._waiting_dialog.isVisible():
                    progress = int((row / len(results)) * 100)
                    self._waiting_dialog.set_status(f"Details laden: {row}/{len(results)} ({progress}%)")

            params = result.get("params", {})
            metrics = result.get("metrics", {})
            score = result.get("score", 0)

            col = 0

            # Column 0: Rank
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_results_table.setItem(row, col, rank_item)
            col += 1

            # Column 1: Total Score
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            score_item.setData(Qt.ItemDataRole.UserRole, score)  # For sorting
            # Color-code score
            if score >= 75:
                score_item.setForeground(Qt.GlobalColor.darkGreen)
            elif score >= 50:
                score_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                score_item.setForeground(Qt.GlobalColor.darkRed)
            self._regime_results_table.setItem(row, col, score_item)
            col += 1

            # Selected (checkbox-like indicator)
            selected_item = QTableWidgetItem("")
            selected_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_results_table.setItem(row, col, selected_item)
            col += 1

            # Dynamic Parameter Columns
            for param_name in param_names:
                param_value = params.get(param_name, "--")
                # Format value based on type
                if isinstance(param_value, float):
                    value_str = f"{param_value:.2f}"
                else:
                    value_str = str(param_value)

                param_item = QTableWidgetItem(value_str)
                param_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, col, param_item)
                col += 1

            # Regime Count (safe access)
            regime_count = metrics.get("regime_count", "--") if isinstance(metrics, dict) else "--"
            regimes_item = QTableWidgetItem(str(regime_count))
            regimes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_results_table.setItem(row, col, regimes_item)
            col += 1

            # Avg Duration (safe access)
            avg_duration = "--"
            if isinstance(metrics, dict):
                avg_duration = metrics.get("avg_duration", metrics.get("avg_duration_bars", "--"))
            if isinstance(avg_duration, (int, float)):
                avg_duration_str = f"{avg_duration:.1f}"
            else:
                avg_duration_str = str(avg_duration)
            duration_item = QTableWidgetItem(avg_duration_str)
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_results_table.setItem(row, col, duration_item)
            col += 1

            # Switch Count (safe access)
            switches = "--"
            if isinstance(metrics, dict):
                switches = metrics.get("switch_count", metrics.get("switches", "--"))
            switches_item = QTableWidgetItem(str(switches))
            switches_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_results_table.setItem(row, col, switches_item)

            # Highlight top 3 (DYNAMIC column count)
            if row < 3:
                colors = [
                    "#22c55e",  # Green for #1
                    "#3b82f6",  # Blue for #2
                    "#a855f7",  # Purple for #3
                ]
                for col_idx in range(len(headers)):  # Use actual column count
                    item = self._regime_results_table.item(row, col_idx)
                    if item:
                        item.setBackground(Qt.GlobalColor.lightGray)

        # Re-enable visual updates and sorting
        self._regime_results_table.setUpdatesEnabled(True)
        self._regime_results_table.setSortingEnabled(True)

        # Sort by score descending
        self._regime_results_table.sortItems(1, Qt.SortOrder.DescendingOrder)

        # Final UI update
        QApplication.processEvents()

        logger.info(f"Populated regime results table with {len(results)} results")

    @pyqtSlot()
    def _on_regime_results_selection_changed(self) -> None:
        """Handle row selection change."""
        selected_rows = self._regime_results_table.selectedIndexes()

        if selected_rows:
            row = selected_rows[0].row()
            rank = int(self._regime_results_table.item(row, 0).text())
            score = self._regime_results_table.item(row, 1).text()

            # Update selected label
            self._regime_results_selected_label.setText(f"✓ Selected: Rank #{rank}, Score: {score}")
            self._regime_results_selected_label.setStyleSheet(
                "font-weight: bold; color: #22c55e; padding: 5px;"
            )

            # Mark selected in table
            for r in range(self._regime_results_table.rowCount()):
                item = self._regime_results_table.item(r, 2)
                if item:
                    item.setText("✓" if r == row else "")

            # Enable action buttons
            self._regime_results_draw_btn.setEnabled(True)
            self._regime_results_export_btn.setEnabled(True)
            self._regime_results_apply_btn.setEnabled(True)
        else:
            self._regime_results_selected_label.setText(
                "No result selected. Click a row to select."
            )
            self._regime_results_selected_label.setStyleSheet("font-weight: bold; padding: 5px;")

            self._regime_results_draw_btn.setEnabled(False)
            self._regime_results_export_btn.setEnabled(False)
            self._regime_results_apply_btn.setEnabled(False)

    def _get_selected_regime_result(self) -> dict | None:
        """Get currently selected result.

        Returns:
            Selected result dict or None
        """
        selected_rows = self._regime_results_table.selectedIndexes()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        rank = int(self._regime_results_table.item(row, 0).text())

        # Get result by rank
        if hasattr(self, "_regime_opt_all_results") and rank <= len(self._regime_opt_all_results):
            return self._regime_opt_all_results[rank - 1]

        return None

    @pyqtSlot()
    def _on_regime_results_draw(self) -> None:
        """Draw selected regime on chart."""
        result = self._get_selected_regime_result()
        if not result:
            return

        # Get regime history from result
        regime_history = result.get("regime_history", [])

        if not regime_history:
            QMessageBox.warning(
                self, "No Regime Data", "Selected result has no regime history to draw."
            )
            return

        # Emit signal to draw regime lines on chart
        if hasattr(self, "draw_regime_lines_requested"):
            self.draw_regime_lines_requested.emit(regime_history)
            logger.info(f"Drawing {len(regime_history)} regime periods on chart")

            # Show confirmation
            QMessageBox.information(
                self, "Regime Lines Drawn", f"Drew {len(regime_history)} regime periods on chart."
            )

    @pyqtSlot()
    def _on_regime_results_export(self) -> None:
        """Export selected result to JSON."""
        result = self._get_selected_regime_result()
        if not result:
            return

        # Get save file path
        symbol = getattr(self, "_symbol", "UNKNOWN")
        timeframe = getattr(self, "_timeframe", "1m")

        # Get rank from selected row
        selected_rows = self._regime_results_table.selectedIndexes()
        row = selected_rows[0].row() if selected_rows else 0
        rank = int(self._regime_results_table.item(row, 0).text()) if self._regime_results_table.item(row, 0) else 1
        default_filename = f"optimized_regime_{symbol}_{timeframe}_#{rank}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Regime Configuration", default_filename, "JSON Files (*.json)"
        )

        if not file_path:
            return

        # Issue #28: Get entry_params and evaluation_params from config if available
        entry_params = {}
        evaluation_params = {}
        if hasattr(self, "_regime_config") and self._regime_config:
            if hasattr(self._regime_config, "entry_params") and self._regime_config.entry_params:
                entry_params = self._regime_config.entry_params
            if hasattr(self._regime_config, "evaluation_params") and self._regime_config.evaluation_params:
                evaluation_params = self._regime_config.evaluation_params

        # Prepare export data
        export_data = {
            "schema_version": "1.0.0",
            "exported_at": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "timeframe": timeframe,
            "optimization_stage": "regime_detection",
            "rank": int(
                self._regime_results_table.item(
                    self._regime_results_table.selectedIndexes()[0].row(), 0
                ).text()
            ),
            "score": result.get("score", 0),
            "params": result.get("params", {}),
            "metrics": result.get("metrics", {}),
            "config": result.get("config", {}),
        }

        # Issue #28: Include entry_params and evaluation_params if present
        if entry_params:
            export_data["entry_params"] = entry_params
        if evaluation_params:
            export_data["evaluation_params"] = evaluation_params

        # Save to file
        try:
            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Exported regime config to {file_path}")

            QMessageBox.information(
                self, "Export Successful", f"Regime configuration exported to:\n{file_path}"
            )
        except Exception as e:
            logger.error(f"Failed to export regime config: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Export Failed", f"Failed to export regime configuration:\n{str(e)}"
            )

    @pyqtSlot()
    def _on_regime_results_apply(self) -> None:
        """Apply selected result and continue to Stage 2 (Indicator Optimization)."""
        result = self._get_selected_regime_result()
        if not result:
            return

        # Store selected config for Stage 2
        self._selected_regime_config = result.get("config", {})
        self._selected_regime_params = result.get("params", {})

        logger.info(f"Applied regime config with score {result.get('score', 0):.1f}")

        # Auto-export to default location
        symbol = getattr(self, "_symbol", "UNKNOWN")
        timeframe = getattr(self, "_timeframe", "1m")
        # Path: src/ui/dialogs/entry_analyzer/this_file.py -> 5x parent = project root
        export_dir = Path(__file__).parent.parent.parent.parent.parent / "results" / "regime_optimization"
        export_dir.mkdir(parents=True, exist_ok=True)

        export_path = export_dir / f"optimized_regime_{symbol}_{timeframe}.json"

        # Issue #28: Reuse entry_params/evaluation_params from above or get fresh
        if not entry_params and hasattr(self, "_regime_config") and self._regime_config:
            if hasattr(self._regime_config, "entry_params") and self._regime_config.entry_params:
                entry_params = self._regime_config.entry_params
        if not evaluation_params and hasattr(self, "_regime_config") and self._regime_config:
            if hasattr(self._regime_config, "evaluation_params") and self._regime_config.evaluation_params:
                evaluation_params = self._regime_config.evaluation_params

        export_data = {
            "schema_version": "1.0.0",
            "exported_at": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "timeframe": timeframe,
            "optimization_stage": "regime_detection",
            "rank": int(
                self._regime_results_table.item(
                    self._regime_results_table.selectedIndexes()[0].row(), 0
                ).text()
            ),
            "score": result.get("score", 0),
            "params": result.get("params", {}),
            "metrics": result.get("metrics", {}),
            "config": result.get("config", {}),
        }

        # Issue #28: Include entry_params and evaluation_params if present
        if entry_params:
            export_data["entry_params"] = entry_params
        if evaluation_params:
            export_data["evaluation_params"] = evaluation_params

        try:
            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            logger.info(f"Auto-exported regime config to {export_path}")
        except Exception as e:
            logger.error(f"Failed to auto-export: {e}")

        # Enable and switch to Indicator Optimization tab (Stage 2)
        if hasattr(self, "_tabs"):
            # Find "Indicator Optimization" tab
            for i in range(self._tabs.count()):
                if "Indicator" in self._tabs.tabText(i):
                    self._tabs.setTabEnabled(i, True)
                    self._tabs.setCurrentIndex(i)
                    break

        # Show confirmation
        QMessageBox.information(
            self,
            "Regime Applied",
            f"Regime configuration applied (Score: {result.get('score', 0):.1f}).\n"
            f"Auto-exported to: {export_path}\n\n"
            f"You can now proceed to Indicator Optimization (Stage 2).",
        )

    @pyqtSlot()
    def _on_regime_score_help_clicked(self) -> None:
        """Open RegimeScore help file in browser."""
        help_path = Path(__file__).parent.parent.parent.parent.parent / "help" / "regime_score_help.html"
        if help_path.exists():
            webbrowser.open(help_path.as_uri())
            logger.info(f"Opened help file: {help_path}")
        else:
            QMessageBox.warning(
                self,
                "Help Not Found",
                f"Help file not found at:\n{help_path}\n\n"
                "Please ensure the help file exists.",
            )
