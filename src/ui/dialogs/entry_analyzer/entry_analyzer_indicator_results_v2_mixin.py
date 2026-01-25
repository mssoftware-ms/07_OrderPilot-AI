"""Entry Analyzer - Indicator Results V2 Mixin (Indicators only).

Zeigt und exportiert Ergebnisse der Indicator-Optimierung (Entry/Exit Long/Short).
Keine Regime-Selektion mehr; Filter nur über Top-N.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IndicatorResultsV2Mixin:
    """Stage 2: Indicator Results Display and Export (no Regime)."""

    _ind_v2_results_tabs: QTabWidget
    _ind_v2_results_tables: dict[str, QTableWidget]
    _ind_v2_export_btn: QPushButton
    _ind_v2_top_n_spin: QSpinBox
    _ind_v2_optimization_results: dict
    _symbol: str
    _timeframe: str

    def _setup_indicator_results_v2_tab(self, tab: QWidget) -> None:
        """Setup Results tab (Indicators only)."""
        layout = QVBoxLayout(tab)

        # Header: Top-N filter
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Show Top:"))
        self._ind_v2_top_n_spin = QSpinBox()
        self._ind_v2_top_n_spin.setMinimum(1)
        self._ind_v2_top_n_spin.setMaximum(20)
        self._ind_v2_top_n_spin.setValue(5)
        self._ind_v2_top_n_spin.setSuffix(" results")
        self._ind_v2_top_n_spin.valueChanged.connect(self._on_indicator_v2_results_filter_changed)
        header_layout.addWidget(self._ind_v2_top_n_spin)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 4 Sub-Tables
        self._ind_v2_results_tabs = QTabWidget()
        self._ind_v2_results_tables = {}

        signal_types = {
            "entry_long": "Entry Long",
            "entry_short": "Entry Short",
            "exit_long": "Exit Long",
            "exit_short": "Exit Short",
        }

        for signal_type, label in signal_types.items():
            table = self._create_indicator_v2_results_table()
            self._ind_v2_results_tables[signal_type] = table
            self._ind_v2_results_tabs.addTab(table, label)

        layout.addWidget(self._ind_v2_results_tabs)

        # Export Controls
        export_layout = QHBoxLayout()

        self._ind_v2_export_btn = QPushButton(" Export Indicator Sets")
        self._ind_v2_export_btn.setIcon(get_icon("save"))
        self._ind_v2_export_btn.setProperty("class", "success")
        self._ind_v2_export_btn.clicked.connect(self._on_export_indicator_v2_sets)
        export_layout.addWidget(self._ind_v2_export_btn)

        preview_btn = QPushButton(" Preview JSON")
        preview_btn.setIcon(get_icon("visibility"))
        preview_btn.clicked.connect(self._on_preview_indicator_v2_sets)
        export_layout.addWidget(preview_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

    # ------------------------------------------------------------------ Tables
    def _create_indicator_v2_results_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels(
            [
                "Select",
                "Rank",
                "Indicator",
                "Score",
                "Win Rate",
                "Profit Factor",
                "Sharpe",
                "Trades",
                "Parameters",
            ]
        )

        header = table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 60)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        return table

    # ------------------------------------------------------------------ Loading / Filtering
    def _on_indicator_v2_results_filter_changed(self) -> None:
        self._load_indicator_v2_results()

    def _load_indicator_v2_results(self) -> None:
        if not hasattr(self, "_ind_v2_optimization_results"):
            self._ind_v2_optimization_results = {}

        top_n = self._ind_v2_top_n_spin.value()

        for signal_type, table in self._ind_v2_results_tables.items():
            table.setRowCount(0)
            results = self._ind_v2_optimization_results.get(signal_type, [])
            if not results:
                continue
            sorted_results = sorted(results, key=lambda r: r.get("score", 0.0), reverse=True)
            for rank, result in enumerate(sorted_results[:top_n], start=1):
                row = table.rowCount()
                table.insertRow(row)

                checkbox = QCheckBox()
                checkbox.setChecked(rank == 1)
                widget = QWidget()
                lay = QHBoxLayout(widget)
                lay.addWidget(checkbox)
                lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lay.setContentsMargins(0, 0, 0, 0)
                table.setCellWidget(row, 0, widget)

                rank_item = QTableWidgetItem(str(rank))
                rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 1, rank_item)

                table.setItem(row, 2, QTableWidgetItem(result.get("indicator", "N/A")))

                score = result.get("score", 0.0)
                score_item = QTableWidgetItem(f"{score:.1f}")
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if score >= 70:
                    score_item.setBackground(Qt.GlobalColor.green)
                elif score >= 50:
                    score_item.setBackground(Qt.GlobalColor.yellow)
                else:
                    score_item.setBackground(Qt.GlobalColor.red)
                table.setItem(row, 3, score_item)

                win_rate = result.get("win_rate", 0.0)
                table.setItem(row, 4, QTableWidgetItem(f"{win_rate:.1%}"))

                profit_factor = result.get("profit_factor", 0.0)
                table.setItem(row, 5, QTableWidgetItem(f"{profit_factor:.2f}"))

                sharpe = result.get("sharpe_ratio", 0.0)
                table.setItem(row, 6, QTableWidgetItem(f"{sharpe:.2f}"))

                trades = result.get("trades", 0)
                table.setItem(row, 7, QTableWidgetItem(str(trades)))

                params = result.get("params", {})
                params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                table.setItem(row, 8, QTableWidgetItem(params_str))

    # ------------------------------------------------------------------ Selection Helpers
    def _get_selected_indicator_v2_sets(self) -> dict:
        signal_sets = {}
        for signal_type, table in self._ind_v2_results_tables.items():
            selected_row = None
            for row in range(table.rowCount()):
                widget = table.cellWidget(row, 0)
                if widget:
                    cb = widget.findChild(QCheckBox)
                    if cb and cb.isChecked():
                        selected_row = row
                        break

            if selected_row is None:
                signal_sets[signal_type] = {
                    "enabled": False,
                    "selected_rank": None,
                    "score": 0.0,
                    "indicator": None,
                    "params": None,
                    "metrics": None,
                    "research_notes": "Not selected",
                }
                continue

            rank = int(table.item(selected_row, 1).text())
            indicator = table.item(selected_row, 2).text()
            score = float(table.item(selected_row, 3).text())
            win_rate = float(table.item(selected_row, 4).text().rstrip("%")) / 100.0
            profit_factor = float(table.item(selected_row, 5).text())
            sharpe = float(table.item(selected_row, 6).text())
            trades = int(table.item(selected_row, 7).text())
            params_str = table.item(selected_row, 8).text()
            params = {}
            if params_str:
                for pair in params_str.split(", "):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        try:
                            params[k] = float(v)
                        except ValueError:
                            params[k] = v

            signal_sets[signal_type] = {
                "enabled": True,
                "selected_rank": rank,
                "score": score,
                "indicator": indicator,
                "params": params,
                "conditions": {"all": []},
                "metrics": {
                    "trades": trades,
                    "win_rate": win_rate,
                    "profit_factor": profit_factor,
                    "sharpe_ratio": sharpe,
                },
                "research_notes": f"Auto-selected (Rank {rank})",
            }
        return signal_sets

    # ------------------------------------------------------------------ Preview / Export
    def _on_preview_indicator_v2_sets(self) -> None:
        signal_sets = self._get_selected_indicator_v2_sets()
        export_data = self._build_indicator_export(signal_sets)
        json_preview = json.dumps(export_data, indent=2)
        preview_text = json_preview[:2000]
        if len(json_preview) > 2000:
            preview_text += "\n\n... (truncated)"
        QMessageBox.information(self, "JSON Preview", f"<pre>{preview_text}</pre>")

    def _on_export_indicator_v2_sets(self) -> None:
        signal_sets = self._get_selected_indicator_v2_sets()
        if not any(s["enabled"] for s in signal_sets.values()):
            QMessageBox.warning(self, "No Selection", "Select at least one result to export.")
            return

        export_data = self._build_indicator_export(signal_sets)

        project_root = Path(__file__).parents[4]
        default_dir = project_root / "03_JSON" / "Trading_Indicatorsets" / "exports"
        default_dir.mkdir(parents=True, exist_ok=True)
        default_filename = f"indicator_sets_{self._symbol}_{self._timeframe}.json"
        default_path = default_dir / default_filename

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Indicator Sets",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Export Successful", f"Saved to:\n{file_path}")
            logger.info("Exported indicator sets to %s", file_path)
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not save file:\n{e}")
            logger.error("Export failed: %s", e, exc_info=True)

    def _build_indicator_export(self, signal_sets: dict) -> dict:
        return {
            "version": "2.0",
            "meta": {
                "stage": "indicator_sets",
                "created_at": datetime.now().isoformat() + "Z",
                "name": f"{self._symbol}_{self._timeframe}_Indicators",
                "source": {"symbol": self._symbol, "timeframe": self._timeframe},
            },
            "signal_sets": signal_sets,
        }
