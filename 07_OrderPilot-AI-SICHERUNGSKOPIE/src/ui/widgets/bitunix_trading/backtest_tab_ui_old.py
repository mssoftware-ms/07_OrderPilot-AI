"""
Backtest Tab UI - UI Setup und Layout

Erstellt das komplette UI Layout für den Backtest Tab:
- Compact Button Row (Toolbar)
- 4 Sub-Tabs (Setup, Execution, Results, Batch/WF)
- KPI Cards
- Tables und Charts

Responsibilities:
- _setup_ui(): Hauptlayout mit Stylesheet
- _create_compact_button_row(): Toolbar mit allen Buttons
- _create_setup_tab(): Datenquelle, Symbol, Zeitraum, Strategy
- _create_execution_tab(): Fees, Slippage, Leverage
- _create_results_tab(): KPI Cards, Equity Curve, Tables
- _create_batch_tab(): Config Inspector, Batch/WF Settings
- _create_kpi_card(): KPI-Card Erstellung
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QProgressBar,
    QSplitter,
    QHeaderView,
    QDateEdit,
    QTabWidget,
    QLineEdit,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestTabUI:
    """UI Setup und Layout für Backtest Tab."""

    def __init__(self, parent: QWidget):
        """
        Args:
            parent: BacktestTab Widget
        """
        self.parent = parent

    def setup_ui(self) -> None:
        """Erstellt das UI Layout."""
        # === COMPACT STYLESHEET für kleinere UI-Elemente ===
        self.parent.setStyleSheet("""
            QGroupBox {
                font-size: 10px;
                font-weight: bold;
                padding-top: 12px;
                margin-top: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
            }
            QLabel {
                font-size: 10px;
            }
            QPushButton {
                font-size: 10px;
                padding: 3px 8px;
                min-height: 20px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QLineEdit {
                font-size: 10px;
                min-height: 20px;
                max-height: 22px;
            }
            QTableWidget {
                font-size: 9px;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QHeaderView::section {
                font-size: 9px;
                padding: 2px 4px;
                min-height: 18px;
            }
            QCheckBox {
                font-size: 10px;
            }
        """)

        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # --- Kompakte Button-Leiste (alle Buttons in einer Zeile) ---
        button_row = self.create_compact_button_row()
        layout.addLayout(button_row)

        # --- Sub-Tabs ---
        self.parent.sub_tabs = QTabWidget()
        self.parent.sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #888;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a2e;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #333;
            }
        """)

        # Tab 1: Setup
        self.parent.sub_tabs.addTab(self.create_setup_tab(), "📁 Setup")

        # Tab 2: Execution Settings
        self.parent.sub_tabs.addTab(self.create_execution_tab(), "⚙️ Execution")

        # Tab 3: Results
        self.parent.sub_tabs.addTab(self.create_results_tab(), "📊 Results")

        # Tab 4: Batch/Walk-Forward
        self.parent.sub_tabs.addTab(self.create_batch_tab(), "🔄 Batch/WF")

        layout.addWidget(self.parent.sub_tabs)

        # --- Log Section ---
        log_group = QGroupBox("📜 Log")
        log_layout = QVBoxLayout(log_group)

        self.parent.log_text = QTextEdit()
        self.parent.log_text.setReadOnly(True)
        self.parent.log_text.setMaximumHeight(120)
        self.parent.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaa;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.parent.log_text)

        layout.addWidget(log_group)

    def create_compact_button_row(self) -> QVBoxLayout:
        """Erstellt kompakte Button-Zeilen (2 Reihen für bessere Sichtbarkeit)."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # === ZEILE 1: Status + Hauptaktionen ===
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        # Status Icon + Label
        self.parent.status_icon = QLabel("🧪")
        self.parent.status_icon.setStyleSheet("font-size: 16px;")
        row1.addWidget(self.parent.status_icon)

        self.parent.status_label = QLabel("IDLE")
        self.parent.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #888;")
        row1.addWidget(self.parent.status_label)

        # Progress Bar
        self.parent.progress_bar = QProgressBar()
        self.parent.progress_bar.setRange(0, 100)
        self.parent.progress_bar.setValue(0)
        self.parent.progress_bar.setFixedWidth(100)
        self.parent.progress_bar.setFixedHeight(20)
        self.parent.progress_bar.setTextVisible(True)
        self.parent.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #222;
                text-align: center;
                color: white;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        row1.addWidget(self.parent.progress_bar)

        row1.addSpacing(8)

        # === START BUTTON (grün, prominent) ===
        self.parent.start_btn = QPushButton("▶ Start Backtest")
        self.parent.start_btn.setMinimumWidth(110)
        self.parent.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.parent.start_btn.clicked.connect(self.parent._on_start_clicked)
        row1.addWidget(self.parent.start_btn)

        # Stop Button
        self.parent.stop_btn = QPushButton("⏹ Stop")
        self.parent.stop_btn.setMinimumWidth(60)
        self.parent.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 6px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.parent.stop_btn.setEnabled(False)
        self.parent.stop_btn.clicked.connect(self.parent._on_stop_clicked)
        row1.addWidget(self.parent.stop_btn)

        row1.addStretch()

        # Status Detail
        self.parent.status_detail = QLabel("Bereit")
        self.parent.status_detail.setStyleSheet("color: #666; font-size: 10px;")
        row1.addWidget(self.parent.status_detail)

        main_layout.addLayout(row1)

        # === ZEILE 2: Config + Tools ===
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        # Load Engine Configs Button (GRÖSSER)
        self.parent.load_config_btn = QPushButton("📥 Engine Configs laden")
        self.parent.load_config_btn.setMinimumWidth(140)
        self.parent.load_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.parent.load_config_btn.setToolTip("Lädt alle Engine-Konfigurationen in die Config-Tabelle")
        row2.addWidget(self.parent.load_config_btn)

        # Auto-Generate Button
        self.parent.auto_gen_btn = QPushButton("🤖 Auto-Generate")
        self.parent.auto_gen_btn.setMinimumWidth(110)
        self.parent.auto_gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.parent.auto_gen_btn.setToolTip("Generiert automatisch Test-Varianten")
        row2.addWidget(self.parent.auto_gen_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #444;")
        row2.addWidget(sep)

        # Template Buttons
        self.parent.save_template_btn = QPushButton("💾 Save")
        self.parent.save_template_btn.setMinimumWidth(60)
        self.parent.save_template_btn.setToolTip("Template speichern")
        self.parent.save_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        row2.addWidget(self.parent.save_template_btn)

        self.parent.load_template_btn = QPushButton("📂 Load")
        self.parent.load_template_btn.setMinimumWidth(60)
        self.parent.load_template_btn.setToolTip("Template laden")
        self.parent.load_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        row2.addWidget(self.parent.load_template_btn)

        self.parent.derive_variant_btn = QPushButton("📝 Variant")
        self.parent.derive_variant_btn.setMinimumWidth(65)
        self.parent.derive_variant_btn.setToolTip("Variante ableiten")
        self.parent.derive_variant_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        row2.addWidget(self.parent.derive_variant_btn)

        row2.addStretch()

        main_layout.addLayout(row2)

        return main_layout

    def create_setup_tab(self) -> QWidget:
        """Erstellt Setup Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Datenquelle ---
        data_group = QGroupBox("📁 Datenquelle")
        data_layout = QFormLayout(data_group)

        self.parent.symbol_combo = QComboBox()
        self.parent.symbol_combo.setEditable(True)
        self.parent.symbol_combo.addItems([
            "bitunix:BTCUSDT",
            "bitunix:ETHUSDT",
            "bitunix:SOLUSDT",
            "alpaca:BTC/USD",
            "alpaca:ETH/USD",
        ])
        data_layout.addRow("Symbol:", self.parent.symbol_combo)

        # Timeframe
        self.parent.timeframe_combo = QComboBox()
        self.parent.timeframe_combo.addItems([
            "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1D"
        ])
        self.parent.timeframe_combo.setCurrentText("5m")  # Default für Daytrading
        data_layout.addRow("Timeframe:", self.parent.timeframe_combo)

        # Zeitraum
        date_layout = QHBoxLayout()
        self.parent.start_date = QDateEdit()
        self.parent.start_date.setDate(datetime.now().date() - timedelta(days=90))
        self.parent.start_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Von:"))
        date_layout.addWidget(self.parent.start_date)

        self.parent.end_date = QDateEdit()
        self.parent.end_date.setDate(datetime.now().date())
        self.parent.end_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Bis:"))
        date_layout.addWidget(self.parent.end_date)

        data_layout.addRow("Zeitraum:", date_layout)

        # Quick-Select Buttons
        quick_layout = QHBoxLayout()
        for days, label in [(7, "1W"), (30, "1M"), (90, "3M"), (180, "6M"), (365, "1Y")]:
            btn = QPushButton(label)
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, d=days: self.parent._set_date_range(d))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        data_layout.addRow("", quick_layout)

        layout.addWidget(data_group)

        # --- Strategy ---
        strategy_group = QGroupBox("🎯 Strategy")
        strategy_layout = QFormLayout(strategy_group)

        self.parent.strategy_combo = QComboBox()
        self.parent.strategy_combo.addItems([
            "Default (Confluence-Based)",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Custom...",
        ])
        strategy_layout.addRow("Strategy:", self.parent.strategy_combo)

        self.parent.initial_capital = QDoubleSpinBox()
        self.parent.initial_capital.setRange(100, 10_000_000)
        self.parent.initial_capital.setValue(10_000)
        self.parent.initial_capital.setPrefix("$ ")
        self.parent.initial_capital.setSingleStep(1000)
        strategy_layout.addRow("Startkapital:", self.parent.initial_capital)

        layout.addWidget(strategy_group)

        # --- Risk Settings ---
        risk_group = QGroupBox("⚠️ Risk Management")
        risk_layout = QFormLayout(risk_group)

        self.parent.risk_per_trade = QDoubleSpinBox()
        self.parent.risk_per_trade.setRange(0.1, 10)
        self.parent.risk_per_trade.setValue(1.0)
        self.parent.risk_per_trade.setSuffix(" %")
        self.parent.risk_per_trade.setSingleStep(0.5)
        risk_layout.addRow("Risiko/Trade:", self.parent.risk_per_trade)

        self.parent.max_daily_loss = QDoubleSpinBox()
        self.parent.max_daily_loss.setRange(0.5, 20)
        self.parent.max_daily_loss.setValue(3.0)
        self.parent.max_daily_loss.setSuffix(" %")
        risk_layout.addRow("Max Daily Loss:", self.parent.max_daily_loss)

        self.parent.max_trades_day = QSpinBox()
        self.parent.max_trades_day.setRange(1, 100)
        self.parent.max_trades_day.setValue(10)
        risk_layout.addRow("Max Trades/Tag:", self.parent.max_trades_day)

        layout.addWidget(risk_group)

        layout.addStretch()
        return widget

    def create_execution_tab(self) -> QWidget:
        """Erstellt Execution Settings Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Fees ---
        fee_group = QGroupBox("💰 Gebühren")
        fee_layout = QFormLayout(fee_group)

        self.parent.fee_maker = QDoubleSpinBox()
        self.parent.fee_maker.setRange(0, 1)
        self.parent.fee_maker.setValue(0.02)
        self.parent.fee_maker.setDecimals(3)
        self.parent.fee_maker.setSuffix(" %")
        fee_layout.addRow("Maker Fee:", self.parent.fee_maker)

        self.parent.fee_taker = QDoubleSpinBox()
        self.parent.fee_taker.setRange(0, 1)
        self.parent.fee_taker.setValue(0.06)
        self.parent.fee_taker.setDecimals(3)
        self.parent.fee_taker.setSuffix(" %")
        fee_layout.addRow("Taker Fee:", self.parent.fee_taker)

        layout.addWidget(fee_group)

        # --- Slippage ---
        slip_group = QGroupBox("📉 Slippage")
        slip_layout = QFormLayout(slip_group)

        self.parent.slippage_method = QComboBox()
        self.parent.slippage_method.addItems(["Fixed BPS", "ATR-Based", "Volume-Adjusted"])
        slip_layout.addRow("Methode:", self.parent.slippage_method)

        self.parent.slippage_bps = QDoubleSpinBox()
        self.parent.slippage_bps.setRange(0, 100)
        self.parent.slippage_bps.setValue(5)
        self.parent.slippage_bps.setSuffix(" bps")
        slip_layout.addRow("Slippage:", self.parent.slippage_bps)

        layout.addWidget(slip_group)

        # --- Leverage ---
        lev_group = QGroupBox("📈 Leverage")
        lev_layout = QFormLayout(lev_group)

        self.parent.max_leverage = QSpinBox()
        self.parent.max_leverage.setRange(1, 125)
        self.parent.max_leverage.setValue(20)
        self.parent.max_leverage.setSuffix("x")
        lev_layout.addRow("Max Leverage:", self.parent.max_leverage)

        self.parent.liq_buffer = QDoubleSpinBox()
        self.parent.liq_buffer.setRange(0, 50)
        self.parent.liq_buffer.setValue(5)
        self.parent.liq_buffer.setSuffix(" %")
        lev_layout.addRow("Liquidation Buffer:", self.parent.liq_buffer)

        layout.addWidget(lev_group)

        # --- Advanced ---
        adv_group = QGroupBox("🔧 Erweitert")
        adv_layout = QFormLayout(adv_group)

        self.parent.assume_taker = QCheckBox()
        self.parent.assume_taker.setChecked(True)
        adv_layout.addRow("Market = Taker:", self.parent.assume_taker)

        self.parent.include_funding = QCheckBox()
        self.parent.include_funding.setChecked(False)
        adv_layout.addRow("Funding Rates:", self.parent.include_funding)

        layout.addWidget(adv_group)

        layout.addStretch()
        return widget

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
        # Header Label
        config_label = QLabel("🔧 Parameter aus Engine Settings (Buttons oben in der Toolbar)")
        config_label.setStyleSheet("font-weight: bold; color: #666; font-size: 10px; margin-bottom: 4px;")
        layout.addWidget(config_label)

        # Table
        self.parent.config_inspector_table = QTableWidget()
        self.parent.config_inspector_table.setColumnCount(8)
        self.parent.config_inspector_table.setHorizontalHeaderLabels([
            "Kategorie", "Parameter", "Wert", "UI-Tab", "Beschreibung", "Typ", "Min/Max", "Variationen"
        ])
        self.parent.config_inspector_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.parent.config_inspector_table.horizontalHeader().setStretchLastSection(True)
        self.parent.config_inspector_table.setMaximumHeight(180)
        self.parent.config_inspector_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only!
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

        # Parameter Space (simplified)
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

        # Issue #35: Removed addStretch() to make UI more compact
        layout.addWidget(results_group, stretch=1)  # Let results table expand

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
