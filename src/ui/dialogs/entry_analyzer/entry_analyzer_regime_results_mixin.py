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

        # Header
        header = QLabel("Regime Optimization Results")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)

        description = QLabel(
            "View all optimization results sorted by score. "
            "Select a result, export it, and apply to continue to Indicator Optimization (Stage 2)."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(description)

        # Selection Info
        self._regime_results_selected_label = QLabel("No result selected. Click a row to select.")
        self._regime_results_selected_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self._regime_results_selected_label)

        # Results Table
        self._regime_results_table = QTableWidget()
        self._regime_results_table.setColumnCount(15)
        self._regime_results_table.setHorizontalHeaderLabels(
            [
                "Rank",
                "Score",
                "Selected",
                "ADX Period",
                "ADX Threshold",
                "SMA Fast",
                "SMA Slow",
                "RSI Period",
                "RSI Low",
                "RSI High",
                "BB Period",
                "BB Width",
                "Regimes",
                "Avg Duration",
                "Switches",
            ]
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
        """Populate results table with all optimization results."""
        if not hasattr(self, "_regime_opt_all_results"):
            logger.warning("No optimization results available")
            return

        results = self._regime_opt_all_results
        self._regime_results_table.setRowCount(len(results))

        for row, result in enumerate(results):
            params = result.get("params", {})
            metrics = result.get("metrics", {})
            score = result.get("score", 0)

            # Rank
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_results_table.setItem(row, 0, rank_item)

            # Score
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            score_item.setData(Qt.ItemDataRole.UserRole, score)  # For sorting
            self._regime_results_table.setItem(row, 1, score_item)

            # Selected (checkbox-like indicator)
            selected_item = QTableWidgetItem("")
            selected_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_results_table.setItem(row, 2, selected_item)

            # ADX Period
            adx_period = params.get("adx_period", params.get("adx.period", "--"))
            self._regime_results_table.setItem(row, 3, QTableWidgetItem(str(adx_period)))

            # ADX Threshold
            adx_thresh = params.get("adx_threshold", params.get("adx.threshold", "--"))
            self._regime_results_table.setItem(row, 4, QTableWidgetItem(str(adx_thresh)))

            # SMA Fast
            sma_fast = params.get("sma_fast_period", params.get("sma_fast.period", "--"))
            self._regime_results_table.setItem(row, 5, QTableWidgetItem(str(sma_fast)))

            # SMA Slow
            sma_slow = params.get("sma_slow_period", params.get("sma_slow.period", "--"))
            self._regime_results_table.setItem(row, 6, QTableWidgetItem(str(sma_slow)))

            # RSI Period
            rsi_period = params.get("rsi_period", params.get("rsi.period", "--"))
            self._regime_results_table.setItem(row, 7, QTableWidgetItem(str(rsi_period)))

            # RSI Sideways Low
            rsi_low = params.get("rsi_sideways_low", params.get("rsi.sideways_low", "--"))
            self._regime_results_table.setItem(row, 8, QTableWidgetItem(str(rsi_low)))

            # RSI Sideways High
            rsi_high = params.get("rsi_sideways_high", params.get("rsi.sideways_high", "--"))
            self._regime_results_table.setItem(row, 9, QTableWidgetItem(str(rsi_high)))

            # BB Period
            bb_period = params.get("bb_period", params.get("bb.period", "--"))
            self._regime_results_table.setItem(row, 10, QTableWidgetItem(str(bb_period)))

            # BB Width Percentile
            bb_width = params.get("bb_width_percentile", params.get("bb.width_percentile", "--"))
            self._regime_results_table.setItem(row, 11, QTableWidgetItem(str(bb_width)))

            # Regime Count
            regime_count = metrics.get("regime_count", "--")
            self._regime_results_table.setItem(row, 12, QTableWidgetItem(str(regime_count)))

            # Avg Duration
            avg_duration = metrics.get("avg_duration", metrics.get("avg_duration_bars", "--"))
            if isinstance(avg_duration, (int, float)):
                avg_duration_str = f"{avg_duration:.1f}"
            else:
                avg_duration_str = str(avg_duration)
            self._regime_results_table.setItem(row, 13, QTableWidgetItem(avg_duration_str))

            # Switch Count
            switches = metrics.get("switch_count", "--")
            self._regime_results_table.setItem(row, 14, QTableWidgetItem(str(switches)))

            # Highlight top 3
            if row < 3:
                colors = [
                    "#22c55e",  # Green for #1
                    "#3b82f6",  # Blue for #2
                    "#a855f7",  # Purple for #3
                ]
                for col in range(15):
                    item = self._regime_results_table.item(row, col)
                    if item:
                        item.setBackground(Qt.GlobalColor.lightGray)

        # Sort by score descending
        self._regime_results_table.sortItems(1, Qt.SortOrder.DescendingOrder)

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
        default_filename = f"optimized_regime_{symbol}_{timeframe}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Regime Configuration", default_filename, "JSON Files (*.json)"
        )

        if not file_path:
            return

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
        export_dir = Path(__file__).parent.parent.parent.parent / "results" / "regime_optimization"
        export_dir.mkdir(parents=True, exist_ok=True)

        export_path = export_dir / f"optimized_regime_{symbol}_{timeframe}.json"

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
