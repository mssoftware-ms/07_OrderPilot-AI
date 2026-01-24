"""Entry Analyzer - Indicator Results V2 Mixin (Stage 2).

Handles Indicator Results Display and Export for Stage 2:
- Regime selection dropdown
- 4 sub-tables (one per signal type)
- Result filtering and selection
- Export to indicator_sets_*.json
- Integration with IndicatorResultsManager

Date: 2026-01-24
Stage: 2 (Indicator Optimization)
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
    QComboBox,
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
    """Stage 2: Indicator Results Display and Export.

    Provides:
    - Regime selector (loads results from optimization)
    - 4 sub-tables (entry_long, entry_short, exit_long, exit_short)
    - Result selection with checkboxes
    - Top-N filtering (e.g., top 3 by score)
    - Export to indicator_sets_*.json
    - Preview of selected indicator sets

    Attributes (defined in parent):
        _ind_v2_results_regime_combo: QComboBox - Regime selector
        _ind_v2_results_tabs: QTabWidget - 4 sub-tabs for signal types
        _ind_v2_results_tables: dict[str, QTableWidget] - Tables per signal type
        _ind_v2_export_btn: QPushButton - Export button
        _ind_v2_top_n_spin: QSpinBox - Top-N filter
        _ind_v2_optimization_results: dict - Results from optimization
    """

    # Type hints for parent attributes
    _ind_v2_results_regime_combo: QComboBox
    _ind_v2_results_tabs: QTabWidget
    _ind_v2_results_tables: dict[str, QTableWidget]
    _ind_v2_export_btn: QPushButton
    _ind_v2_top_n_spin: QSpinBox
    _ind_v2_optimization_results: dict
    _symbol: str
    _timeframe: str

    def _setup_indicator_results_v2_tab(self, tab: QWidget) -> None:
        """Setup Indicator Results V2 tab (Stage 2).

        Creates:
        - Regime selector
        - 4 sub-tables (entry_long, entry_short, exit_long, exit_short)
        - Top-N filter
        - Export button
        """
        layout = QVBoxLayout(tab)

        # ===== Header Controls =====
        header_layout = QHBoxLayout()

        # Regime selector
        header_layout.addWidget(QLabel("Regime:"))
        self._ind_v2_results_regime_combo = QComboBox()
        self._ind_v2_results_regime_combo.addItems(["BULL", "BEAR", "SIDEWAYS"])
        self._ind_v2_results_regime_combo.currentTextChanged.connect(
            self._on_indicator_v2_results_regime_changed
        )
        header_layout.addWidget(self._ind_v2_results_regime_combo)

        header_layout.addSpacing(20)

        # Top-N filter
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

        # ===== 4 Sub-Tables =====
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

        # ===== Export Controls =====
        export_layout = QHBoxLayout()

        self._ind_v2_export_btn = QPushButton(" Export Indicator Sets")
        self._ind_v2_export_btn.setIcon(get_icon("save"))
        self._ind_v2_export_btn.setProperty("class", "success")
        self._ind_v2_export_btn.clicked.connect(self._on_export_indicator_v2_sets)
        export_layout.addWidget(self._ind_v2_export_btn)

        # Preview button
        preview_btn = QPushButton(" Preview JSON")
        preview_btn.setIcon(get_icon("visibility"))
        preview_btn.clicked.connect(self._on_preview_indicator_v2_sets)
        export_layout.addWidget(preview_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

    def _create_indicator_v2_results_table(self) -> QTableWidget:
        """Create a results table for one signal type.

        Returns:
            QTableWidget with columns: Select, Rank, Indicator, Score, Win Rate,
            Profit Factor, Sharpe, Trades, Parameters
        """
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

        # Table configuration
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

        table.setColumnWidth(0, 60)  # Select checkbox
        table.setColumnWidth(1, 60)  # Rank

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)

        return table

    def _on_indicator_v2_results_regime_changed(self, regime: str) -> None:
        """Handle regime selection change in results view.

        Args:
            regime: Selected regime name
        """
        logger.info(f"Stage 2 Results: Regime changed to {regime}")
        self._load_indicator_v2_results_for_regime(regime)

    def _on_indicator_v2_results_filter_changed(self) -> None:
        """Handle top-N filter change.

        Reloads and filters current results.
        """
        regime = self._ind_v2_results_regime_combo.currentText()
        self._load_indicator_v2_results_for_regime(regime)

    def _load_indicator_v2_results_for_regime(self, regime: str) -> None:
        """Load and display optimization results for a regime.

        Args:
            regime: Regime name (BULL, BEAR, SIDEWAYS)
        """
        # Check if we have results in memory
        if not hasattr(self, "_ind_v2_optimization_results"):
            self._ind_v2_optimization_results = {}

        # Get top-N filter
        top_n = self._ind_v2_top_n_spin.value()

        # Populate each signal type table
        for signal_type, table in self._ind_v2_results_tables.items():
            table.setRowCount(0)

            # Get results for this signal type
            results = self._ind_v2_optimization_results.get(signal_type, [])
            if not results:
                continue

            # Sort by score (descending)
            sorted_results = sorted(results, key=lambda r: r.get("score", 0.0), reverse=True)

            # Apply top-N filter
            filtered_results = sorted_results[:top_n]

            # Populate table
            for rank, result in enumerate(filtered_results, start=1):
                row = table.rowCount()
                table.insertRow(row)

                # Select checkbox
                checkbox = QCheckBox()
                checkbox.setChecked(rank == 1)  # Auto-select top result
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                table.setCellWidget(row, 0, checkbox_widget)

                # Rank
                rank_item = QTableWidgetItem(str(rank))
                rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 1, rank_item)

                # Indicator
                table.setItem(row, 2, QTableWidgetItem(result.get("indicator", "N/A")))

                # Score (color-coded)
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

                # Win Rate
                win_rate = result.get("win_rate", 0.0)
                table.setItem(row, 4, QTableWidgetItem(f"{win_rate:.1%}"))

                # Profit Factor
                profit_factor = result.get("profit_factor", 0.0)
                table.setItem(row, 5, QTableWidgetItem(f"{profit_factor:.2f}"))

                # Sharpe Ratio
                sharpe = result.get("sharpe_ratio", 0.0)
                table.setItem(row, 6, QTableWidgetItem(f"{sharpe:.2f}"))

                # Trades
                trades = result.get("trades", 0)
                table.setItem(row, 7, QTableWidgetItem(str(trades)))

                # Parameters
                params = result.get("params", {})
                params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                table.setItem(row, 8, QTableWidgetItem(params_str))

    def _get_selected_indicator_v2_sets(self) -> dict:
        """Extract selected indicator sets from all 4 tables.

        Returns:
            Dictionary with signal_sets structure for JSON export
        """
        signal_sets = {}

        for signal_type, table in self._ind_v2_results_tables.items():
            selected_row = None

            # Find selected row (checkbox checked)
            for row in range(table.rowCount()):
                checkbox_widget = table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        selected_row = row
                        break

            if selected_row is not None:
                # Extract result data
                rank = int(table.item(selected_row, 1).text())
                indicator = table.item(selected_row, 2).text()
                score = float(table.item(selected_row, 3).text())
                win_rate_str = table.item(selected_row, 4).text().rstrip("%")
                win_rate = float(win_rate_str) / 100.0
                profit_factor = float(table.item(selected_row, 5).text())
                sharpe = float(table.item(selected_row, 6).text())
                trades = int(table.item(selected_row, 7).text())
                params_str = table.item(selected_row, 8).text()

                # Parse parameters
                params = {}
                if params_str:
                    for param_pair in params_str.split(", "):
                        if "=" in param_pair:
                            key, value = param_pair.split("=", 1)
                            try:
                                params[key] = float(value)
                            except ValueError:
                                params[key] = value

                signal_sets[signal_type] = {
                    "enabled": True,
                    "selected_rank": rank,
                    "score": score,
                    "indicator": indicator,
                    "indicator_id": f"{indicator.lower()}_{int(params.get('period', 14))}",
                    "params": params,
                    "conditions": {"all": []},  # Placeholder
                    "metrics": {
                        "signals": trades * 2,  # Estimate
                        "trades": trades,
                        "win_rate": win_rate,
                        "profit_factor": profit_factor,
                        "avg_win": 0.0,  # Not available yet
                        "avg_loss": 0.0,  # Not available yet
                        "max_drawdown": 0.0,  # Not available yet
                        "sharpe_ratio": sharpe,
                        "expectancy": 0.0,  # Not available yet
                    },
                    "research_notes": f"Auto-selected from Stage 2 optimization (Rank {rank})",
                }
            else:
                # No selection - disabled signal type
                signal_sets[signal_type] = {
                    "enabled": False,
                    "selected_rank": None,
                    "score": 0.0,
                    "indicator": None,
                    "indicator_id": None,
                    "params": None,
                    "conditions": {"all": []},
                    "metrics": None,
                    "research_notes": "Not selected",
                }

        return signal_sets

    def _on_preview_indicator_v2_sets(self) -> None:
        """Preview selected indicator sets as JSON.

        Shows formatted JSON in a message box.
        """
        regime = self._ind_v2_results_regime_combo.currentText()
        signal_sets = self._get_selected_indicator_v2_sets()

        # Build full JSON structure
        export_data = {
            "version": "2.0",
            "meta": {
                "stage": "indicator_sets",
                "regime": regime,
                "regime_color": {"BULL": "#26a69a", "BEAR": "#ef5350", "SIDEWAYS": "#9e9e9e"}[
                    regime
                ],
                "created_at": datetime.now().isoformat() + "Z",
                "name": f"{regime}_{self._symbol}_{self._timeframe}_Indicators",
                "regime_config_ref": f"optimized_regime_{self._symbol}_{self._timeframe}.json",
                "source": {"symbol": self._symbol, "timeframe": self._timeframe},
                "aggregate_metrics": {
                    "total_signals_enabled": sum(1 for s in signal_sets.values() if s["enabled"]),
                    "combined_win_rate": 0.0,  # Calculate later
                    "combined_profit_factor": 0.0,  # Calculate later
                },
            },
            "signal_sets": signal_sets,
        }

        # Format JSON
        json_preview = json.dumps(export_data, indent=2)

        # Show in message box (truncated)
        preview_text = json_preview[:2000]
        if len(json_preview) > 2000:
            preview_text += "\n\n... (truncated)"

        QMessageBox.information(self, "JSON Preview", f"<pre>{preview_text}</pre>")

    def _on_export_indicator_v2_sets(self) -> None:
        """Export selected indicator sets to indicator_sets_*.json.

        Saves to: 03_JSON/Entry_Analyzer/Regime/STUFE_2_Indicators/{REGIME}/
        """
        regime = self._ind_v2_results_regime_combo.currentText()
        signal_sets = self._get_selected_indicator_v2_sets()

        # Check if any signal type is enabled
        if not any(s["enabled"] for s in signal_sets.values()):
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select at least one indicator set to export.",
            )
            return

        # Build export data
        export_data = {
            "version": "2.0",
            "meta": {
                "stage": "indicator_sets",
                "regime": regime,
                "regime_color": {"BULL": "#26a69a", "BEAR": "#ef5350", "SIDEWAYS": "#9e9e9e"}[
                    regime
                ],
                "created_at": datetime.now().isoformat() + "Z",
                "name": f"{regime}_{self._symbol}_{self._timeframe}_Indicators",
                "regime_config_ref": f"optimized_regime_{self._symbol}_{self._timeframe}.json",
                "optimization_results_ref": f"indicator_optimization_results_{regime}_{self._symbol}_{self._timeframe}.json",
                "source": {"symbol": self._symbol, "timeframe": self._timeframe},
            },
            "signal_sets": signal_sets,
        }

        # Default save path
        project_root = Path(__file__).parents[4]
        default_dir = (
            project_root / "03_JSON" / "Entry_Analyzer" / "Regime" / "STUFE_2_Indicators" / regime
        )
        default_dir.mkdir(parents=True, exist_ok=True)

        default_filename = f"indicator_sets_{regime}_{self._symbol}_{self._timeframe}.json"
        default_path = default_dir / default_filename

        # File dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Indicator Sets",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )

        if not file_path:
            return

        # Save file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Indicator sets exported to:\n{file_path}",
            )
            logger.info(f"Exported indicator sets to {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export indicator sets:\n\n{str(e)}",
            )
            logger.error(f"Failed to export indicator sets: {e}", exc_info=True)
