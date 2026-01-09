"""Backtest Tab UI - Results & Batch Tabs Module.

Creates Results and Batch/Walk-Forward analysis tabs:
- Results Tab: KPI cards, equity curve, metrics table, trades table, breakdown
- Batch Tab: Config inspector, batch settings, walk-forward settings, results table

Module 3/4 of backtest_tab_ui.py split.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTextEdit,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QSplitter,
    QHeaderView,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestTabUIResults:
    """Results and Batch tabs builder for backtest tab.

    Creates tabs for displaying backtest results and configuring
    batch/walk-forward optimization.
    """

    def __init__(self, parent: QWidget):
        """
        Args:
            parent: BacktestTab Widget
        """
        self.parent = parent

    def create_results_tab(self) -> QWidget:
        """Erstellt Results Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- KPI Cards ---
        kpi_layout = QHBoxLayout()

        self.parent.kpi_pnl = self.create_kpi_card("💰 P&L", "—", "#4CAF50")
        kpi_layout.addWidget(self.parent.kpi_pnl)

        self.parent.kpi_winrate = self.create_kpi_card("🎯 Win Rate", "—", "#2196F3")
        kpi_layout.addWidget(self.parent.kpi_winrate)

        self.parent.kpi_pf = self.create_kpi_card("📊 Profit Factor", "—", "#FF9800")
        kpi_layout.addWidget(self.parent.kpi_pf)

        self.parent.kpi_dd = self.create_kpi_card("📉 Max DD", "—", "#f44336")
        kpi_layout.addWidget(self.parent.kpi_dd)

        layout.addLayout(kpi_layout)

        # --- Equity Curve Chart ---
        equity_group = QGroupBox("📈 Equity Curve")
        equity_layout = QVBoxLayout(equity_group)

        try:
            from src.ui.widgets.equity_curve_widget import EquityCurveWidget
            self.parent.equity_chart = EquityCurveWidget()
            self.parent.equity_chart.setMinimumHeight(200)
            self.parent.equity_chart.setMaximumHeight(300)
            equity_layout.addWidget(self.parent.equity_chart)
        except ImportError as e:
            logger.warning(f"EquityCurveWidget not available: {e}")
            self.parent.equity_chart = None
            placeholder = QLabel("Equity Chart nicht verfügbar")
            placeholder.setStyleSheet("color: #666;")
            equity_layout.addWidget(placeholder)

        layout.addWidget(equity_group)

        # --- Splitter für Metrics und Trades ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Metrics Table ---
        metrics_widget = QWidget()
        metrics_layout_inner = QVBoxLayout(metrics_widget)
        metrics_layout_inner.setContentsMargins(0, 0, 0, 0)

        metrics_label = QLabel("📊 Detaillierte Metriken")
        metrics_label.setStyleSheet("font-weight: bold; color: #aaa;")
        metrics_layout_inner.addWidget(metrics_label)

        self.parent.metrics_table = QTableWidget()
        self.parent.metrics_table.setColumnCount(2)
        self.parent.metrics_table.setHorizontalHeaderLabels(["Metrik", "Wert"])
        self.parent.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.parent.metrics_table.setMaximumHeight(180)
        metrics_layout_inner.addWidget(self.parent.metrics_table)

        splitter.addWidget(metrics_widget)

        # --- Trades Table ---
        trades_widget = QWidget()
        trades_layout_inner = QVBoxLayout(trades_widget)
        trades_layout_inner.setContentsMargins(0, 0, 0, 0)

        trades_header = QHBoxLayout()
        trades_label = QLabel("📋 Trades")
        trades_label.setStyleSheet("font-weight: bold; color: #aaa;")
        trades_header.addWidget(trades_label)

        trades_header.addStretch()

        self.parent.export_csv_btn = QPushButton("📄 Trades CSV")
        self.parent.export_csv_btn.setMaximumWidth(80)
        trades_header.addWidget(self.parent.export_csv_btn)

        self.parent.export_equity_btn = QPushButton("📈 Equity CSV")
        self.parent.export_equity_btn.setMaximumWidth(80)
        trades_header.addWidget(self.parent.export_equity_btn)

        self.parent.export_json_btn = QPushButton("📋 JSON")
        self.parent.export_json_btn.setMaximumWidth(60)
        trades_header.addWidget(self.parent.export_json_btn)

        trades_layout_inner.addLayout(trades_header)

        self.parent.trades_table = QTableWidget()
        self.parent.trades_table.setColumnCount(8)
        self.parent.trades_table.setHorizontalHeaderLabels([
            "ID", "Symbol", "Side", "Entry", "Exit", "Size", "P&L", "R-Mult"
        ])
        self.parent.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        trades_layout_inner.addWidget(self.parent.trades_table)

        splitter.addWidget(trades_widget)

        # --- Regime/Setup Breakdown Table ---
        breakdown_widget = QWidget()
        breakdown_layout = QVBoxLayout(breakdown_widget)
        breakdown_layout.setContentsMargins(0, 0, 0, 0)

        breakdown_label = QLabel("🎯 Regime/Setup Breakdown")
        breakdown_label.setStyleSheet("font-weight: bold; color: #aaa;")
        breakdown_layout.addWidget(breakdown_label)

        self.parent.breakdown_table = QTableWidget()
        self.parent.breakdown_table.setColumnCount(7)
        self.parent.breakdown_table.setHorizontalHeaderLabels([
            "Regime/Setup", "Trades", "Win Rate", "Avg P&L", "Profit Factor", "Expectancy", "Anteil"
        ])
        self.parent.breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.parent.breakdown_table.setMaximumHeight(150)
        breakdown_layout.addWidget(self.parent.breakdown_table)

        splitter.addWidget(breakdown_widget)

        layout.addWidget(splitter)

        return widget

    def create_batch_tab(self) -> QWidget:
        """Erstellt Batch/Walk-Forward Tab mit Config Inspector."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)

        # --- Config Inspector Table (Read-Only Basistabelle) ---
        config_label = QLabel("🔧 Parameter aus Engine Settings (Buttons oben in der Toolbar)")
        config_label.setStyleSheet("font-weight: bold; color: #666; font-size: 10px; margin-bottom: 4px;")
        layout.addWidget(config_label)

        self.parent.config_inspector_table = QTableWidget()
        self.parent.config_inspector_table.setColumnCount(8)
        self.parent.config_inspector_table.setHorizontalHeaderLabels([
            "Kategorie", "Parameter", "Wert", "UI-Tab", "Beschreibung", "Typ", "Min/Max", "Variationen"
        ])
        self.parent.config_inspector_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.parent.config_inspector_table.horizontalHeader().setStretchLastSection(True)
        self.parent.config_inspector_table.setMaximumHeight(180)
        self.parent.config_inspector_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.parent.config_inspector_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.parent.config_inspector_table.setStyleSheet("""
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
        layout.addWidget(self.parent.config_inspector_table)

        # --- Indicator Sets Quick-Select ---
        ind_set_layout = QHBoxLayout()
        ind_set_label = QLabel("📊 Indikator-Set:")
        ind_set_label.setStyleSheet("color: #888;")
        ind_set_layout.addWidget(ind_set_label)

        self.parent.indicator_set_combo = QComboBox()
        self.parent.indicator_set_combo.addItems([
            "-- Manuell --",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Conservative",
            "Aggressive",
            "Balanced (Default)",
        ])
        self.parent.indicator_set_combo.setCurrentIndex(0)
        ind_set_layout.addWidget(self.parent.indicator_set_combo)

        ind_set_layout.addStretch()
        layout.addLayout(ind_set_layout)

        # --- Batch & Walk-Forward nebeneinander ---
        batch_wf_row = QHBoxLayout()
        batch_wf_row.setSpacing(8)

        # --- Batch Settings (links) ---
        batch_group = QGroupBox("🔄 Batch Testing")
        batch_layout = QFormLayout(batch_group)
        batch_layout.setContentsMargins(6, 6, 6, 6)
        batch_layout.setSpacing(4)

        self.parent.batch_method = QComboBox()
        self.parent.batch_method.addItems(["Grid Search", "Random Search", "Bayesian (Optuna)"])
        batch_layout.addRow("Methode:", self.parent.batch_method)

        self.parent.batch_iterations = QSpinBox()
        self.parent.batch_iterations.setRange(1, 1000)
        self.parent.batch_iterations.setValue(50)
        batch_layout.addRow("Max Iterationen:", self.parent.batch_iterations)

        self.parent.batch_target = QComboBox()
        self.parent.batch_target.addItems(["Expectancy", "Profit Factor", "Sharpe Ratio", "Min Drawdown"])
        batch_layout.addRow("Zielmetrik:", self.parent.batch_target)

        self.parent.param_space_text = QTextEdit()
        self.parent.param_space_text.setMaximumHeight(60)
        self.parent.param_space_text.setPlaceholderText(
            '{"risk_per_trade": [0.5, 1.0, 1.5, 2.0]}'
        )
        batch_layout.addRow("Params:", self.parent.param_space_text)

        batch_wf_row.addWidget(batch_group)

        # --- Walk-Forward (rechts) ---
        wf_group = QGroupBox("🚶 Walk-Forward Analyse")
        wf_layout = QFormLayout(wf_group)
        wf_layout.setContentsMargins(6, 6, 6, 6)
        wf_layout.setSpacing(4)

        self.parent.wf_train_days = QSpinBox()
        self.parent.wf_train_days.setRange(7, 365)
        self.parent.wf_train_days.setValue(90)
        self.parent.wf_train_days.setSuffix(" Tage")
        wf_layout.addRow("Training:", self.parent.wf_train_days)

        self.parent.wf_test_days = QSpinBox()
        self.parent.wf_test_days.setRange(7, 180)
        self.parent.wf_test_days.setValue(30)
        self.parent.wf_test_days.setSuffix(" Tage")
        wf_layout.addRow("Test:", self.parent.wf_test_days)

        self.parent.wf_step_days = QSpinBox()
        self.parent.wf_step_days.setRange(7, 90)
        self.parent.wf_step_days.setValue(30)
        self.parent.wf_step_days.setSuffix(" Tage")
        wf_layout.addRow("Step:", self.parent.wf_step_days)

        self.parent.wf_reoptimize = QCheckBox()
        self.parent.wf_reoptimize.setChecked(True)
        wf_layout.addRow("Re-Optimize:", self.parent.wf_reoptimize)

        batch_wf_row.addWidget(wf_group)

        layout.addLayout(batch_wf_row)

        # --- Batch/WF Buttons ---
        btn_layout = QHBoxLayout()

        self.parent.run_batch_btn = QPushButton("🔄 Run Batch Test")
        self.parent.run_batch_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.parent.run_batch_btn.clicked.connect(self.parent._on_batch_clicked)
        btn_layout.addWidget(self.parent.run_batch_btn)

        self.parent.run_wf_btn = QPushButton("🚶 Run Walk-Forward")
        self.parent.run_wf_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.parent.run_wf_btn.clicked.connect(self.parent._on_wf_clicked)
        btn_layout.addWidget(self.parent.run_wf_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Results Summary ---
        results_group = QGroupBox("📊 Batch/WF Ergebnisse")
        results_layout = QVBoxLayout(results_group)

        self.parent.batch_results_table = QTableWidget()
        self.parent.batch_results_table.setColumnCount(5)
        self.parent.batch_results_table.setHorizontalHeaderLabels([
            "Run", "Parameters", "P&L", "Expectancy", "Max DD"
        ])
        self.parent.batch_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.parent.batch_results_table)

        layout.addWidget(results_group, stretch=1)

        return widget

    def create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
        """Erstellt eine KPI-Karte."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a2e;
                border-radius: 8px;
                border-left: 4px solid {color};
                padding: 8px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("kpi_value")
        value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        layout.addWidget(value_label)

        return card
