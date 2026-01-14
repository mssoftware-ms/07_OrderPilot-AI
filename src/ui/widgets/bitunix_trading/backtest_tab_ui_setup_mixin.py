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
    QHeaderView, QFrame, QDateEdit,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)


class BacktestTabUISetupMixin:
    """UI creation for Setup and Execution tabs"""

    def _setup_ui(self) -> None:
        """Erstellt das UI Layout."""
        # === COMPACT STYLESHEET für kleinere UI-Elemente ===
        self.setStyleSheet("""
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # --- Kompakte Button-Leiste (alle Buttons in einer Zeile) ---
        button_row = self._create_compact_button_row()
        layout.addLayout(button_row)

        # --- Sub-Tabs ---
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
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
        self.sub_tabs.addTab(self._create_setup_tab(), "📁 Setup")

        # Tab 2: Execution Settings
        self.sub_tabs.addTab(self._create_execution_tab(), "⚙️ Execution")

        # Tab 3: Results
        self.sub_tabs.addTab(self._create_results_tab(), "📊 Results")

        # Tab 4: Batch/Walk-Forward
        self.sub_tabs.addTab(self._create_batch_tab(), "🔄 Batch/WF")

        layout.addWidget(self.sub_tabs)

        # --- Log Section ---
        log_group = QGroupBox("📜 Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(240)  # Issue #40: Doubled height for better log visibility
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaa;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)
    def _create_compact_button_row(self) -> QVBoxLayout:
        """Erstellt kompakte Button-Zeilen (2 Reihen für bessere Sichtbarkeit)."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # === ZEILE 1: Status + Hauptaktionen ===
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        # Status Icon + Label
        self.status_icon = QLabel("🧪")
        self.status_icon.setStyleSheet("font-size: 16px;")
        row1.addWidget(self.status_icon)

        self.status_label = QLabel("IDLE")
        self.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #888;")
        row1.addWidget(self.status_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
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
        row1.addWidget(self.progress_bar)

        row1.addSpacing(8)

        # === START BUTTON (grün, prominent) ===
        self.start_btn = QPushButton("▶ Start Backtest")
        self.start_btn.setMinimumWidth(110)
        self.start_btn.setStyleSheet("""
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
        self.start_btn.clicked.connect(self._on_start_btn_clicked)
        row1.addWidget(self.start_btn)

        # Stop Button
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setMinimumWidth(60)
        self.stop_btn.setStyleSheet("""
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
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        row1.addWidget(self.stop_btn)

        row1.addStretch()

        # Status Detail
        self.status_detail = QLabel("Bereit")
        self.status_detail.setStyleSheet("color: #666; font-size: 10px;")
        row1.addWidget(self.status_detail)

        main_layout.addLayout(row1)

        # === ZEILE 2: Config + Tools ===
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        # Load Engine Configs Button (GRÖSSER)
        self.load_config_btn = QPushButton("📥 Engine Configs laden")
        self.load_config_btn.setMinimumWidth(140)
        self.load_config_btn.setStyleSheet("""
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
        self.load_config_btn.setToolTip("Lädt alle Engine-Konfigurationen in die Config-Tabelle")
        self.load_config_btn.clicked.connect(self._on_load_configs_clicked)
        row2.addWidget(self.load_config_btn)

        # Auto-Generate Button
        self.auto_gen_btn = QPushButton("🤖 Auto-Generate")
        self.auto_gen_btn.setMinimumWidth(110)
        self.auto_gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.auto_gen_btn.setToolTip("Generiert automatisch Test-Varianten")
        self.auto_gen_btn.clicked.connect(self._on_auto_generate_clicked)
        row2.addWidget(self.auto_gen_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #444;")
        row2.addWidget(sep)

        # Template Buttons
        self.save_template_btn = QPushButton("💾 Save")
        self.save_template_btn.setMinimumWidth(60)
        self.save_template_btn.setToolTip("Template speichern")
        self.save_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.save_template_btn.clicked.connect(self._on_save_template_clicked)
        row2.addWidget(self.save_template_btn)

        self.load_template_btn = QPushButton("📂 Load")
        self.load_template_btn.setMinimumWidth(60)
        self.load_template_btn.setToolTip("Template laden")
        self.load_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.load_template_btn.clicked.connect(self._on_load_template_clicked)
        row2.addWidget(self.load_template_btn)

        self.derive_variant_btn = QPushButton("📝 Variant")
        self.derive_variant_btn.setMinimumWidth(65)
        self.derive_variant_btn.setToolTip("Variante ableiten")
        self.derive_variant_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.derive_variant_btn.clicked.connect(self._on_derive_variant_clicked)
        row2.addWidget(self.derive_variant_btn)

        row2.addStretch()

        main_layout.addLayout(row2)

        return main_layout
    def _create_setup_tab(self) -> QWidget:
        """Erstellt Setup Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Datenquelle ---
        data_group = QGroupBox("📁 Datenquelle")
        data_layout = QFormLayout(data_group)

        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)
        self.symbol_combo.addItems([
            "bitunix:BTCUSDT",
            "bitunix:ETHUSDT",
            "bitunix:SOLUSDT",
            "alpaca:BTC/USD",
            "alpaca:ETH/USD",
        ])
        data_layout.addRow("Symbol:", self.symbol_combo)

        # Timeframe
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems([
            "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1D"
        ])
        self.timeframe_combo.setCurrentText("5m")  # Default für Daytrading
        data_layout.addRow("Timeframe:", self.timeframe_combo)

        # Zeitraum
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setDate(datetime.now().date() - timedelta(days=90))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Von:"))
        date_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(datetime.now().date())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Bis:"))
        date_layout.addWidget(self.end_date)

        data_layout.addRow("Zeitraum:", date_layout)

        # Quick-Select Buttons
        quick_layout = QHBoxLayout()
        for days, label in [(1, "1T"), (2, "2T"), (7, "1W"), (30, "1M"), (90, "3M"), (180, "6M"), (365, "1Y")]:
            btn = QPushButton(label)
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, d=days: self._set_date_range(d))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        data_layout.addRow("", quick_layout)

        layout.addWidget(data_group)

        # --- Strategy ---
        strategy_group = QGroupBox("🎯 Strategy")
        strategy_layout = QFormLayout(strategy_group)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "Default (Confluence-Based)",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Custom...",
        ])
        strategy_layout.addRow("Strategy:", self.strategy_combo)

        self.initial_capital = QDoubleSpinBox()
        self.initial_capital.setRange(100, 10_000_000)
        self.initial_capital.setValue(10_000)
        self.initial_capital.setPrefix("$ ")
        self.initial_capital.setSingleStep(1000)
        strategy_layout.addRow("Startkapital:", self.initial_capital)

        layout.addWidget(strategy_group)

        # --- Risk Settings ---
        risk_group = QGroupBox("⚠️ Risk Management")
        risk_layout = QFormLayout(risk_group)

        self.risk_per_trade = QDoubleSpinBox()
        self.risk_per_trade.setRange(0.1, 10)
        self.risk_per_trade.setValue(1.0)
        self.risk_per_trade.setSuffix(" %")
        self.risk_per_trade.setSingleStep(0.5)
        risk_layout.addRow("Risiko/Trade:", self.risk_per_trade)

        self.max_daily_loss = QDoubleSpinBox()
        self.max_daily_loss.setRange(0.5, 20)
        self.max_daily_loss.setValue(3.0)
        self.max_daily_loss.setSuffix(" %")
        risk_layout.addRow("Max Daily Loss:", self.max_daily_loss)

        self.max_trades_day = QSpinBox()
        self.max_trades_day.setRange(1, 100)
        self.max_trades_day.setValue(10)
        risk_layout.addRow("Max Trades/Tag:", self.max_trades_day)

        layout.addWidget(risk_group)

        layout.addStretch()
        return widget
    def _create_execution_tab(self) -> QWidget:
        """Erstellt Execution Settings Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Fees ---
        fee_group = QGroupBox("💰 Gebühren")
        fee_layout = QFormLayout(fee_group)

        self.fee_maker = QDoubleSpinBox()
        self.fee_maker.setRange(0, 1)
        self.fee_maker.setValue(0.02)
        self.fee_maker.setDecimals(3)
        self.fee_maker.setSuffix(" %")
        fee_layout.addRow("Maker Fee:", self.fee_maker)

        self.fee_taker = QDoubleSpinBox()
        self.fee_taker.setRange(0, 1)
        self.fee_taker.setValue(0.06)
        self.fee_taker.setDecimals(3)
        self.fee_taker.setSuffix(" %")
        fee_layout.addRow("Taker Fee:", self.fee_taker)

        layout.addWidget(fee_group)

        # --- Slippage ---
        slip_group = QGroupBox("📉 Slippage")
        slip_layout = QFormLayout(slip_group)

        self.slippage_method = QComboBox()
        self.slippage_method.addItems(["Fixed BPS", "ATR-Based", "Volume-Adjusted"])
        slip_layout.addRow("Methode:", self.slippage_method)

        self.slippage_bps = QDoubleSpinBox()
        self.slippage_bps.setRange(0, 100)
        self.slippage_bps.setValue(5)
        self.slippage_bps.setSuffix(" bps")
        slip_layout.addRow("Slippage:", self.slippage_bps)

        layout.addWidget(slip_group)

        # --- Leverage ---
        lev_group = QGroupBox("📈 Leverage")
        lev_layout = QFormLayout(lev_group)

        self.max_leverage = QSpinBox()
        self.max_leverage.setRange(1, 125)
        self.max_leverage.setValue(20)
        self.max_leverage.setSuffix("x")
        lev_layout.addRow("Max Leverage:", self.max_leverage)

        self.liq_buffer = QDoubleSpinBox()
        self.liq_buffer.setRange(0, 50)
        self.liq_buffer.setValue(5)
        self.liq_buffer.setSuffix(" %")
        lev_layout.addRow("Liquidation Buffer:", self.liq_buffer)

        layout.addWidget(lev_group)

        # --- Advanced ---
        adv_group = QGroupBox("🔧 Erweitert")
        adv_layout = QFormLayout(adv_group)

        self.assume_taker = QCheckBox()
        self.assume_taker.setChecked(True)
        adv_layout.addRow("Market = Taker:", self.assume_taker)

        self.include_funding = QCheckBox()
        self.include_funding.setChecked(False)
        adv_layout.addRow("Funding Rates:", self.include_funding)

        layout.addWidget(adv_group)

        layout.addStretch()
        return widget
    def _create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
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
