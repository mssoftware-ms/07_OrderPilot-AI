from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QTabWidget, QLineEdit,
    QHeaderView,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)


class BacktestTabUIBatchMixin:
    """UI creation and updates for Batch tab"""

    def _create_batch_tab(self) -> QWidget:
        """Erstellt Batch/Walk-Forward Tab mit Config Inspector."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)

        # --- Config Inspector Table (Read-Only Basistabelle) ---
        # Header Label
        config_label = QLabel("🔧 Parameter aus Engine Settings (Buttons oben in der Toolbar)")
        config_label.setStyleSheet("font-weight: bold; color: #666; font-size: 10px; margin-bottom: 4px;")
        layout.addWidget(config_label)

        # Table ---
        self.config_inspector_table = QTableWidget()
        self.config_inspector_table.setColumnCount(8)
        self.config_inspector_table.setHorizontalHeaderLabels([
            "Kategorie", "Parameter", "Wert", "UI-Tab", "Beschreibung", "Typ", "Min/Max", "Variationen"
        ])
        self.config_inspector_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.config_inspector_table.horizontalHeader().setStretchLastSection(True)
        self.config_inspector_table.setMaximumHeight(180)
        self.config_inspector_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only!
        self.config_inspector_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.config_inspector_table.setStyleSheet("""
            QTableWidget {
                font-size: 10px;
                background-color: #1a1a2e;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QTableWidget::item:selected {
                background-color: #2a3a5e;
            }
            QHeaderView::section {
                background-color: #2a2a4a;
                color: #aaa;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #333;
            }
        """)
        layout.addWidget(self.config_inspector_table)

        # --- Indicator Sets Quick-Select ---
        ind_set_layout = QHBoxLayout()
        ind_set_label = QLabel("📊 Indikator-Set:")
        ind_set_label.setStyleSheet("color: #888;")
        ind_set_layout.addWidget(ind_set_label)

        self.indicator_set_combo = QComboBox()
        self.indicator_set_combo.addItems([
            "-- Manuell --",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Conservative",
            "Aggressive",
            "Balanced (Default)",
        ])
        self.indicator_set_combo.setCurrentIndex(0)
        self.indicator_set_combo.currentIndexChanged.connect(self._on_indicator_set_changed)
        ind_set_layout.addWidget(self.indicator_set_combo)

        ind_set_layout.addStretch()
        layout.addLayout(ind_set_layout)

        # --- Batch & Walk-Forward nebeneinander ---
        batch_wf_row = QHBoxLayout()
        batch_wf_row.setSpacing(8)

        # --- Batch Settings (links) ---
        batch_group = QGroupBox("🔄 Batch Testing")
        batch_group.setMaximumHeight(150)  # Issue #36: Höhe begrenzen für Log-Sichtbarkeit
        batch_layout = QFormLayout(batch_group)
        batch_layout.setContentsMargins(6, 6, 6, 6)
        batch_layout.setSpacing(4)

        self.batch_method = QComboBox()
        self.batch_method.addItems(["Grid Search", "Random Search", "Bayesian (Optuna)"])
        batch_layout.addRow("Methode:", self.batch_method)

        self.batch_iterations = QSpinBox()
        self.batch_iterations.setRange(1, 1000)
        self.batch_iterations.setValue(50)
        batch_layout.addRow("Max Iterationen:", self.batch_iterations)

        self.batch_target = QComboBox()
        self.batch_target.addItems(["Expectancy", "Profit Factor", "Sharpe Ratio", "Min Drawdown"])
        batch_layout.addRow("Zielmetrik:", self.batch_target)

        # Parameter Space (simplified)
        self.param_space_text = QTextEdit()
        self.param_space_text.setMaximumHeight(40)  # Issue #36: Reduziert für mehr Platz
        self.param_space_text.setPlaceholderText(
            '{"risk_per_trade": [0.5, 1.0, 1.5, 2.0]}'
        )
        batch_layout.addRow("Params:", self.param_space_text)

        batch_wf_row.addWidget(batch_group)

        # --- Walk-Forward (rechts) ---
        wf_group = QGroupBox("🚶 Walk-Forward Analyse")
        wf_group.setMaximumHeight(150)  # Issue #36: Höhe begrenzen für Log-Sichtbarkeit
        wf_layout = QFormLayout(wf_group)
        wf_layout.setContentsMargins(6, 6, 6, 6)
        wf_layout.setSpacing(4)

        self.wf_train_days = QSpinBox()
        self.wf_train_days.setRange(7, 365)
        self.wf_train_days.setValue(90)
        self.wf_train_days.setSuffix(" Tage")
        wf_layout.addRow("Training:", self.wf_train_days)

        self.wf_test_days = QSpinBox()
        self.wf_test_days.setRange(7, 180)
        self.wf_test_days.setValue(30)
        self.wf_test_days.setSuffix(" Tage")
        wf_layout.addRow("Test:", self.wf_test_days)

        self.wf_step_days = QSpinBox()
        self.wf_step_days.setRange(7, 90)
        self.wf_step_days.setValue(30)
        self.wf_step_days.setSuffix(" Tage")
        wf_layout.addRow("Step:", self.wf_step_days)

        self.wf_reoptimize = QCheckBox()
        self.wf_reoptimize.setChecked(True)
        wf_layout.addRow("Re-Optimize:", self.wf_reoptimize)

        batch_wf_row.addWidget(wf_group)

        layout.addLayout(batch_wf_row)

        # --- Batch/WF Buttons ---
        btn_layout = QHBoxLayout()

        self.run_batch_btn = QPushButton("🔄 Run Batch Test")
        self.run_batch_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.run_batch_btn.clicked.connect(self._on_batch_btn_clicked)
        btn_layout.addWidget(self.run_batch_btn)

        self.run_wf_btn = QPushButton("🚶 Run Walk-Forward")
        self.run_wf_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.run_wf_btn.clicked.connect(self._on_wf_btn_clicked)
        btn_layout.addWidget(self.run_wf_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Results Summary ---
        results_group = QGroupBox("📊 Batch/WF Ergebnisse")
        results_group.setMaximumHeight(200)  # Issue #40: Limit height to make room for larger log
        results_layout = QVBoxLayout(results_group)

        self.batch_results_table = QTableWidget()
        self.batch_results_table.setColumnCount(5)
        self.batch_results_table.setHorizontalHeaderLabels([
            "Run", "Parameters", "P&L", "Expectancy", "Max DD"
        ])
        self.batch_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.batch_results_table)

        # Issue #35: Removed addStretch() to make UI more compact
        layout.addWidget(results_group, stretch=1)  # Let results table expand

        return widget
    def _update_batch_results_table(self, results: list) -> None:
        """Aktualisiert die Batch-Ergebnisse Tabelle.

        Args:
            results: Liste von BatchRunResult Objekten
        """
        self.batch_results_table.setRowCount(len(results))

        for row, run in enumerate(results):
            # Rank/Run
            self.batch_results_table.setItem(row, 0, QTableWidgetItem(f"#{row + 1}"))

            # Parameters (kurze Darstellung)
            params_str = ", ".join(f"{k}={v}" for k, v in list(run.parameters.items())[:2])
            if len(run.parameters) > 2:
                params_str += "..."
            self.batch_results_table.setItem(row, 1, QTableWidgetItem(params_str))

            if run.metrics:
                # P&L
                pnl = run.metrics.total_return_pct
                pnl_item = QTableWidgetItem(f"{pnl:.1f}%")
                pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
                self.batch_results_table.setItem(row, 2, pnl_item)

                # Expectancy
                exp = run.metrics.expectancy if run.metrics.expectancy else 0
                self.batch_results_table.setItem(row, 3, QTableWidgetItem(f"${exp:.2f}"))

                # Max DD
                dd = run.metrics.max_drawdown_pct
                dd_item = QTableWidgetItem(f"{dd:.1f}%")
                dd_item.setForeground(QColor("#f44336" if dd > 10 else "#FF9800" if dd > 5 else "#4CAF50"))
                self.batch_results_table.setItem(row, 4, dd_item)
            else:
                # Error case
                error_item = QTableWidgetItem(run.error or "Fehler")
                error_item.setForeground(QColor("#f44336"))
                self.batch_results_table.setItem(row, 2, error_item)
    def _update_wf_results_table(self, fold_results: list) -> None:
        """Aktualisiert die Walk-Forward Ergebnisse Tabelle.

        Args:
            fold_results: Liste von FoldResult Objekten
        """
        self.batch_results_table.setRowCount(len(fold_results))

        for row, fold in enumerate(fold_results):
            # Fold Number
            self.batch_results_table.setItem(row, 0, QTableWidgetItem(f"Fold {fold.fold_number}"))

            # Parameters (optimierte)
            if fold.optimized_parameters:
                params_str = ", ".join(f"{k}={v}" for k, v in list(fold.optimized_parameters.items())[:2])
            else:
                params_str = "Standard"
            self.batch_results_table.setItem(row, 1, QTableWidgetItem(params_str))

            # OOS P&L
            if fold.oos_metrics:
                pnl = fold.oos_metrics.total_return_pct
                pnl_item = QTableWidgetItem(f"{pnl:.1f}%")
                pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
                self.batch_results_table.setItem(row, 2, pnl_item)

                # OOS Expectancy
                exp = fold.oos_metrics.expectancy if fold.oos_metrics.expectancy else 0
                self.batch_results_table.setItem(row, 3, QTableWidgetItem(f"${exp:.2f}"))

                # OOS Max DD
                dd = fold.oos_metrics.max_drawdown_pct
                dd_item = QTableWidgetItem(f"{dd:.1f}%")
                dd_item.setForeground(QColor("#f44336" if dd > 10 else "#FF9800" if dd > 5 else "#4CAF50"))
                self.batch_results_table.setItem(row, 4, dd_item)
            else:
                error_item = QTableWidgetItem("Keine OOS-Daten")
                error_item.setForeground(QColor("#888"))
                self.batch_results_table.setItem(row, 2, error_item)
