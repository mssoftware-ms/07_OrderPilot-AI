"""compounding_ui_setup.py
UI widget creation and layout setup for CompoundingPanel.

This mixin handles all UI construction:
- Input tab widgets and layout
- Details tab with chart canvas
- Fee presets and trading days presets
- Matplotlib canvas setup
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
from PyQt6.QtCore import Qt, QSignalBlocker
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
    QDoubleSpinBox, QSpinBox, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# VIP fee structure for Bitunix futures
FUTURES_FEES_BY_VIP = {
    "VIP0": {"maker": 0.02, "taker": 0.06},
    "VIP1": {"maker": 0.02, "taker": 0.05},
    "VIP2": {"maker": 0.016, "taker": 0.05},
    "VIP3": {"maker": 0.014, "taker": 0.04},
    "VIP4": {"maker": 0.012, "taker": 0.0375},
    "VIP5": {"maker": 0.01, "taker": 0.035},
    "VIP6": {"maker": 0.008, "taker": 0.0315},
    "VIP7": {"maker": 0.006, "taker": 0.03},
}


# Modern color palette for financial charts
MODERN_COLORS = {
    'gross': '#FF9500',      # Orange - Gross Profit
    'fees': '#FF3B30',       # Red - Fees
    'taxes': '#AF52DE',      # Purple - Taxes
    'net': '#34C759',        # Green - Net Profit
    'invest': '#007AFF',     # Blue - Investment/Capital
    'grid': '#3A3A3C',       # Dark gray - Grid
    'background': '#1C1C1E', # Dark background
    'surface': '#2C2C2E',    # Surface color
    'text': '#FFFFFF',       # White text
    'text_secondary': '#8E8E93',  # Secondary text
}


class MplCanvas(FigureCanvas):
    """Modern matplotlib canvas with dark theme and gradient support."""

    def __init__(self, parent: QWidget):
        self.fig = Figure(facecolor='none', edgecolor='none')
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self._setup_modern_style()

    def _setup_modern_style(self) -> None:
        """Apply modern dark theme styling."""
        # Use a clean style as base
        plt.style.use('dark_background')

    def apply_qt_palette(self, widget: QWidget) -> None:
        """Apply Qt palette colors to matplotlib figure."""
        pal = widget.palette()
        window = pal.color(widget.backgroundRole())
        base = pal.color(pal.ColorRole.Base)
        text = pal.color(pal.ColorRole.Text)

        def qcol(c, alpha=1.0):
            return (c.redF(), c.greenF(), c.blueF(), alpha)

        # Modern dark styling
        bg_color = qcol(window)
        surface_color = qcol(base)
        text_color = qcol(text)

        self.fig.set_facecolor(bg_color)
        self.ax.set_facecolor(surface_color)

        # Modern axis styling
        self.ax.tick_params(axis="both", colors=text_color, labelsize=9)
        self.ax.xaxis.label.set_color(text_color)
        self.ax.yaxis.label.set_color(text_color)
        self.ax.title.set_color(text_color)

        # Subtle spines
        for spine in self.ax.spines.values():
            spine.set_color(qcol(text, 0.3))
            spine.set_linewidth(0.5)

        # Remove top and right spines for cleaner look
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)


class CompoundingUISetupMixin:
    """Mixin for UI widget creation and layout."""

    def _build_tab_inputs(self) -> None:
        """Build the input tab with all parameter controls."""
        layout = QVBoxLayout(self.tab_inputs)
        box = QGroupBox("Eingaben")
        form = QFormLayout(box)

        # Start capital
        self.sp_start_capital = QDoubleSpinBox()
        self.sp_start_capital.setRange(0, 1e9)
        self.sp_start_capital.setDecimals(2)
        self.sp_start_capital.setValue(100.0)
        self.sp_start_capital.setSuffix(" €")

        # VIP level selector
        self.cb_vip_level = QComboBox()
        self.cb_vip_level.addItems(["VIP0", "VIP1", "VIP2", "VIP3", "VIP4", "VIP5", "VIP6", "VIP7", "Custom"])
        self.cb_vip_level.setCurrentText("VIP0")

        # Order type selector
        self.cb_order_type = QComboBox()
        self.cb_order_type.addItems(["Taker/Taker", "Maker/Maker", "Maker/Taker", "Taker/Maker"])
        self.cb_order_type.setCurrentText("Taker/Taker")

        # Fee percentages
        self.sp_fee_open_pct = QDoubleSpinBox()
        self.sp_fee_open_pct.setRange(0, 100)
        self.sp_fee_open_pct.setDecimals(4)
        self.sp_fee_open_pct.setSingleStep(0.01)
        self.sp_fee_open_pct.setSuffix(" %")

        self.sp_fee_close_pct = QDoubleSpinBox()
        self.sp_fee_close_pct.setRange(0, 100)
        self.sp_fee_close_pct.setDecimals(4)
        self.sp_fee_close_pct.setSingleStep(0.01)
        self.sp_fee_close_pct.setSuffix(" %")

        # Leverage
        self.sp_leverage = QDoubleSpinBox()
        self.sp_leverage.setRange(0.01, 1000)
        self.sp_leverage.setDecimals(2)
        self.sp_leverage.setValue(20.0)
        self.sp_leverage.setSuffix(" x")

        # Daily profit percentage
        self.sp_daily_profit_pct = QDoubleSpinBox()
        self.sp_daily_profit_pct.setRange(-99.0, 1000.0)
        self.sp_daily_profit_pct.setDecimals(4)
        self.sp_daily_profit_pct.setValue(30.0)
        self.sp_daily_profit_pct.setSuffix(" %")

        # Reinvest percentage
        self.sp_reinvest_pct = QDoubleSpinBox()
        self.sp_reinvest_pct.setRange(0, 100)
        self.sp_reinvest_pct.setDecimals(2)
        self.sp_reinvest_pct.setValue(30.0)
        self.sp_reinvest_pct.setSuffix(" %")

        # Tax percentage
        self.sp_tax_pct = QDoubleSpinBox()
        self.sp_tax_pct.setRange(0, 100)
        self.sp_tax_pct.setDecimals(2)
        self.sp_tax_pct.setValue(25.0)
        self.sp_tax_pct.setSuffix(" %")

        # Days
        self.sp_days = QSpinBox()
        self.sp_days.setRange(1, 366)
        self.sp_days.setValue(30)

        # Trading days preset
        self.cb_trading_days_preset = QComboBox()
        self.cb_trading_days_preset.addItems(["30 (Kalendertage)", "22 (typ. Börsentage)", "20 (typ. Börsentage)"])
        self.cb_trading_days_preset.setCurrentIndex(0)

        # Apply losses checkbox
        self.cb_apply_losses = QCheckBox("Verluste reduzieren Kapital (optional)")
        self.cb_apply_losses.setChecked(False)

        # Target month net
        self.sp_target_month_net = QDoubleSpinBox()
        self.sp_target_month_net.setRange(-1e9, 1e9)
        self.sp_target_month_net.setDecimals(2)
        self.sp_target_month_net.setValue(0.0)
        self.sp_target_month_net.setSuffix(" €")

        # Solver status label
        self.lbl_solver_status = QLabel("")
        self.lbl_solver_status.setWordWrap(True)

        # Add all rows to form
        form.addRow("Startkapital", self.sp_start_capital)
        form.addRow("VIP Status", self.cb_vip_level)
        form.addRow("Order Type (Open/Close)", self.cb_order_type)
        form.addRow("Gebuehren Open", self.sp_fee_open_pct)
        form.addRow("Gebuehren Close", self.sp_fee_close_pct)
        form.addRow("Hebel", self.sp_leverage)
        form.addRow("Gewinn % / Tag", self.sp_daily_profit_pct)
        form.addRow("Reinvestition", self.sp_reinvest_pct)
        form.addRow("Steuern (Monatsende)", self.sp_tax_pct)
        form.addRow("Tage (manuell)", self.sp_days)
        form.addRow("Preset Trading-Tage", self.cb_trading_days_preset)
        form.addRow("", self.cb_apply_losses)
        form.addRow("Ziel netto im Monat", self.sp_target_month_net)
        form.addRow("Status", self.lbl_solver_status)

        layout.addWidget(box)

        # KPI box
        kpi_box = QGroupBox("Monats-KPIs")
        kpi_form = QFormLayout(kpi_box)

        self.kpi_end_capital = QLabel("—")
        self.kpi_sum_gross = QLabel("—")
        self.kpi_sum_fees = QLabel("—")
        self.kpi_sum_taxes = QLabel("—")
        self.kpi_sum_net = QLabel("—")
        self.kpi_sum_reinvest = QLabel("—")
        self.kpi_sum_withdrawal = QLabel("—")
        self.kpi_roi = QLabel("—")

        kpi_form.addRow("Endkapital", self.kpi_end_capital)
        kpi_form.addRow("Summe Brutto", self.kpi_sum_gross)
        kpi_form.addRow("Summe Gebühren", self.kpi_sum_fees)
        kpi_form.addRow("Summe Steuern", self.kpi_sum_taxes)
        kpi_form.addRow("Summe Netto", self.kpi_sum_net)
        kpi_form.addRow("Summe reinvestiert", self.kpi_sum_reinvest)
        kpi_form.addRow("Summe entnommen", self.kpi_sum_withdrawal)
        kpi_form.addRow("ROI", self.kpi_roi)

        layout.addWidget(kpi_box)
        layout.addStretch(1)

        # Connect signals
        self.sp_daily_profit_pct.valueChanged.connect(lambda _v: self._on_user_edited("daily"))
        self.sp_target_month_net.valueChanged.connect(lambda _v: self._on_user_edited("target"))

        for w in [
            self.sp_start_capital,
            self.sp_fee_open_pct,
            self.sp_fee_close_pct,
            self.sp_leverage,
            self.sp_reinvest_pct,
            self.sp_tax_pct,
            self.sp_days,
        ]:
            w.valueChanged.connect(lambda _v: self.recompute(origin="param_change"))

        self.sp_fee_open_pct.valueChanged.connect(self._on_fee_override)
        self.sp_fee_close_pct.valueChanged.connect(self._on_fee_override)
        self.cb_apply_losses.stateChanged.connect(lambda _s: self.recompute(origin="param_change"))
        self.cb_trading_days_preset.currentIndexChanged.connect(self._apply_trading_days_preset)
        self.cb_vip_level.currentIndexChanged.connect(self._apply_fee_preset)
        self.cb_order_type.currentIndexChanged.connect(self._apply_fee_preset)

        # Apply initial fee preset
        self._apply_fee_preset()

    def _build_tab_details(self) -> None:
        """Build the Details tab with modern chart (table hidden)."""
        layout = QVBoxLayout(self.tab_details)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Top toolbar with modern styling
        top = QHBoxLayout()
        top.setSpacing(8)

        # Plot mode selector
        plot_label = QLabel("📊 Ansicht:")
        plot_label.setStyleSheet("font-weight: bold; color: #8E8E93;")
        self.cb_plot_mode = QComboBox()
        self.cb_plot_mode.addItems([
            "Alle Metriken (gestapelt)",
            "Täglicher Netto-Gewinn",
            "Kumuliertes Netto",
            "Gewinn vs. Kosten",
            "Monatliche Übersicht (gestapelt)",
            "Jährliche Übersicht (gestapelt)",
        ])
        self.cb_plot_mode.setCurrentIndex(0)
        self.cb_plot_mode.currentIndexChanged.connect(lambda _i: self.recompute(origin="plot_mode"))
        self.cb_plot_mode.setStyleSheet("""
            QComboBox {
                background-color: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 5px 10px;
                min-width: 180px;
            }
            QComboBox:hover {
                border-color: #48484A;
            }
        """)

        # Export buttons with modern styling
        btn_style = """
            QPushButton {
                background-color: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
                border-color: #48484A;
            }
            QPushButton:pressed {
                background-color: #48484A;
            }
        """

        self.btn_copy_csv = QPushButton("📋 Kopieren")
        self.btn_copy_csv.setStyleSheet(btn_style)
        self.btn_copy_csv.clicked.connect(self._copy_table_to_clipboard)

        self.btn_export_xlsx = QPushButton("📊 XLSX exportieren")
        self.btn_export_xlsx.setStyleSheet(btn_style)
        self.btn_export_xlsx.clicked.connect(self._export_xlsx)

        # Check if openpyxl is available
        try:
            import openpyxl
            self.btn_export_xlsx.setEnabled(True)
        except ImportError:
            self.btn_export_xlsx.setEnabled(False)

        self.btn_export_docx = QPushButton("📄 DOCX Report")
        self.btn_export_docx.setStyleSheet(btn_style)
        self.btn_export_docx.clicked.connect(self._export_docx)

        # Check if python-docx is available
        try:
            import docx
            self.btn_export_docx.setEnabled(True)
        except ImportError:
            self.btn_export_docx.setEnabled(False)

        top.addWidget(plot_label)
        top.addWidget(self.cb_plot_mode)
        top.addStretch(1)
        top.addWidget(self.btn_copy_csv)
        top.addWidget(self.btn_export_xlsx)
        top.addWidget(self.btn_export_docx)
        layout.addLayout(top)

        # Hidden table (still exists for data/export)
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Tag", "Startkapital", "Brutto", "Notional", "Gebühren",
            "Vor Steuern", "Steuern", "Netto", "Reinvest", "Entnahme", "Endkapital"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setVisible(False)  # Hidden but available for export

        # Modern chart canvas - takes full space
        self.canvas = MplCanvas(self)
        self.canvas.setMinimumHeight(400)
        self.canvas.setStyleSheet("""
            background-color: #1C1C1E;
            border: 1px solid #3A3A3C;
            border-radius: 8px;
        """)

        layout.addWidget(self.canvas, stretch=1)

    def _apply_trading_days_preset(self, idx: int) -> None:
        """Apply trading days preset based on selected index."""
        preset_map = {0: 30, 1: 22, 2: 20}
        val = preset_map.get(idx, 30)
        with QSignalBlocker(self.sp_days):
            self.sp_days.setValue(val)
        self.recompute(origin="preset_days")

    def _apply_fee_preset(self) -> None:
        """Apply VIP-level fee presets."""
        vip = self.cb_vip_level.currentText()
        if vip == "Custom":
            return
        fees = FUTURES_FEES_BY_VIP.get(vip)
        if not fees:
            return

        maker = float(fees["maker"])
        taker = float(fees["taker"])
        order = self.cb_order_type.currentText()

        if order == "Maker/Maker":
            open_fee = maker
            close_fee = maker
        elif order == "Maker/Taker":
            open_fee = maker
            close_fee = taker
        elif order == "Taker/Maker":
            open_fee = taker
            close_fee = maker
        else:  # Taker/Taker
            open_fee = taker
            close_fee = taker

        with QSignalBlocker(self.sp_fee_open_pct):
            self.sp_fee_open_pct.setValue(open_fee)
        with QSignalBlocker(self.sp_fee_close_pct):
            self.sp_fee_close_pct.setValue(close_fee)
        self.recompute(origin="fee_preset")

    def _on_fee_override(self) -> None:
        """Handle manual fee override - switch to Custom."""
        if self._suppress_updates:
            return
        if self.cb_vip_level.currentText() != "Custom":
            with QSignalBlocker(self.cb_vip_level):
                self.cb_vip_level.setCurrentText("Custom")
        self.recompute(origin="fee_override")
