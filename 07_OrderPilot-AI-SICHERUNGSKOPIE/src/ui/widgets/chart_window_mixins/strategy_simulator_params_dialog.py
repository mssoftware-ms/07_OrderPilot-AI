"""Test Parameters Dialog for Strategy Simulator.

Shows all current simulation parameters in a readable popup.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QFormLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TestParametersDialog(QDialog):
    """Dialog showing all current test/simulation parameters."""

    def __init__(self, parent=None, parameters: dict | None = None):
        """Initialize the dialog.

        Args:
            parent: Parent widget
            parameters: Dictionary containing all parameter categories
        """
        super().__init__(parent)
        self.parameters = parameters or {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("📋 Test Parameters")
        self.setMinimumSize(500, 600)
        self.setMaximumSize(800, 900)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        header = QLabel("Aktuelle Simulationsparameter")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)

        # Add parameter groups
        self._add_simulation_settings(scroll_layout)
        self._add_capital_settings(scroll_layout)
        self._add_strategy_params(scroll_layout)
        self._add_sl_tp_settings(scroll_layout)
        self._add_trailing_settings(scroll_layout)
        self._add_fees_settings(scroll_layout)
        self._add_data_range(scroll_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Schließen")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _create_group(self, title: str, icon: str = "") -> tuple[QGroupBox, QFormLayout]:
        """Create a styled group box with form layout."""
        group = QGroupBox(f"{icon} {title}" if icon else title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        form = QFormLayout(group)
        form.setSpacing(5)
        return group, form

    def _add_value_label(self, form: QFormLayout, label: str, value: Any, highlight: bool = False) -> None:
        """Add a label-value pair to the form."""
        value_label = QLabel(str(value))
        if highlight:
            value_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        form.addRow(f"{label}:", value_label)

    def _add_simulation_settings(self, layout: QVBoxLayout) -> None:
        """Add simulation settings group."""
        group, form = self._create_group("Simulation", "⚙️")

        sim = self.parameters.get("simulation", {})
        self._add_value_label(form, "Strategy", sim.get("strategy", "N/A"), highlight=True)
        self._add_value_label(form, "Mode", sim.get("mode", "manual"))
        self._add_value_label(form, "Trials", sim.get("trials", 50))
        self._add_value_label(form, "Objective", sim.get("objective", "score"))

        # Entry Only settings
        entry_only = sim.get("entry_only", False)
        self._add_value_label(form, "Entry Only", "✅ Ja" if entry_only else "❌ Nein")

        # Time range settings
        time_range = sim.get("time_range", "Chart-Ansicht")
        timeframe = sim.get("timeframe", "N/A")
        bars_for_range = sim.get("bars_for_range")

        self._add_value_label(form, "Zeitraum", time_range, highlight=True)
        self._add_value_label(form, "Kerzen-Timeframe", timeframe)
        if bars_for_range:
            self._add_value_label(form, "Kerzen für Zeitraum", f"~{bars_for_range}")

        layout.addWidget(group)

    def _add_strategy_params(self, layout: QVBoxLayout) -> None:
        """Add strategy parameters group."""
        group, form = self._create_group("Strategy Parameter", "📊")

        params = self.parameters.get("strategy_params", {})
        if not params:
            self._add_value_label(form, "Status", "Keine Parameter verfügbar")
        else:
            for key, value in params.items():
                # Format value based on type
                if isinstance(value, float):
                    formatted = f"{value:.4f}" if abs(value) < 1 else f"{value:.2f}"
                elif isinstance(value, bool):
                    formatted = "✅" if value else "❌"
                else:
                    formatted = str(value)
                self._add_value_label(form, key, formatted)

        layout.addWidget(group)

    def _add_capital_settings(self, layout: QVBoxLayout) -> None:
        """Add Capital and Position Sizing settings group."""
        group, form = self._create_group("Kapital & Position", "💰")

        capital = self.parameters.get("capital", {})
        initial = capital.get("initial_capital", 1000.0)
        risk_pct = capital.get("risk_per_trade_pct", 100.0)
        leverage = capital.get("leverage", 1.0)
        direction = capital.get("trade_direction", "BOTH")

        self._add_value_label(form, "Startkapital", f"€ {initial:,.0f}", highlight=True)
        self._add_value_label(form, "Risk/Trade", f"{risk_pct:.1f}%")
        self._add_value_label(form, "Leverage", f"{leverage:.0f}x" if leverage > 1 else "Ohne")

        # Trade direction with description
        direction_labels = {
            "AUTO": "Auto (Backtesting)",
            "BOTH": "Long + Short",
            "LONG_ONLY": "Nur Long",
            "SHORT_ONLY": "Nur Short",
        }
        direction_label = direction_labels.get(direction, direction)
        self._add_value_label(form, "Trade-Richtung", direction_label, highlight=True)

        layout.addWidget(group)

    def _add_sl_tp_settings(self, layout: QVBoxLayout) -> None:
        """Add Stop Loss / Take Profit settings group."""
        group, form = self._create_group("Stop Loss / Take Profit", "🎯")

        sl_tp = self.parameters.get("sl_tp", {})
        sl_atr = sl_tp.get("sl_atr_multiplier", 0.0)
        tp_atr = sl_tp.get("tp_atr_multiplier", 0.0)
        atr_period = sl_tp.get("atr_period", 14)
        initial_sl = sl_tp.get("initial_sl_pct", 2.0)

        # Initial Stop Loss
        self._add_value_label(form, "Initial SL", f"{initial_sl:.2f}%", highlight=True)

        if sl_atr > 0:
            self._add_value_label(form, "SL Mode", "ATR-basiert")
            self._add_value_label(form, "SL ATR Multiplier", f"{sl_atr:.1f}x ATR")
        else:
            self._add_value_label(form, "SL Mode", "Prozent-basiert")

        if tp_atr > 0:
            self._add_value_label(form, "TP Mode", "ATR-basiert")
            self._add_value_label(form, "TP ATR Multiplier", f"{tp_atr:.1f}x ATR")
        else:
            self._add_value_label(form, "TP Mode", "Prozent-basiert")

        self._add_value_label(form, "ATR Periode", atr_period)

        layout.addWidget(group)

    def _add_trailing_settings(self, layout: QVBoxLayout) -> None:
        """Add trailing stop settings group."""
        group, form = self._create_group("Trailing Stop", "📈")

        trailing = self.parameters.get("trailing", {})
        enabled = trailing.get("enabled", False)

        self._add_value_label(
            form, "Status",
            "✅ Aktiviert" if enabled else "❌ Deaktiviert",
            highlight=enabled
        )

        if enabled:
            mode = trailing.get("mode", "ATR")
            pct_distance = trailing.get("pct_distance", 1.0)
            atr_mult = trailing.get("atr_multiplier", 1.5)
            activation = trailing.get("activation_pct", 5.0)
            regime_adaptive = trailing.get("regime_adaptive", True)
            atr_trending = trailing.get("atr_trending", 1.2)
            atr_ranging = trailing.get("atr_ranging", 2.0)

            # Format mode description
            mode_descriptions = {
                "PCT": "Prozent-basiert",
                "ATR": "Volatilitäts-basiert (ATR)",
                "SWING": "Swing/Struktur-basiert (BB)"
            }
            mode_desc = mode_descriptions.get(mode, mode)

            self._add_value_label(form, "Mode", mode_desc, highlight=True)
            self._add_value_label(form, "Aktivierung ab", f"{activation:.1f}% Gewinn")

            # Show distance with appropriate unit based on mode
            if mode == "PCT":
                self._add_value_label(form, "Distance", f"{pct_distance:.1f}%")
            elif mode == "ATR":
                self._add_value_label(form, "ATR Multiplier", f"{atr_mult:.2f}x")
                if regime_adaptive:
                    self._add_value_label(form, "Regime-Adaptiv", "✅ Aktiv", highlight=True)
                    self._add_value_label(form, "ATR Trending", f"{atr_trending:.2f}x (ADX>25)")
                    self._add_value_label(form, "ATR Ranging", f"{atr_ranging:.2f}x (ADX<20)")
            elif mode == "SWING":
                self._add_value_label(form, "Basis", "Bollinger Bands (20/2)")

        layout.addWidget(group)

    def _add_fees_settings(self, layout: QVBoxLayout) -> None:
        """Add trading fees settings group."""
        group, form = self._create_group("Trading Gebühren", "💸")

        fees = self.parameters.get("fees", {})
        maker = fees.get("maker_fee_pct", 0.02)
        taker = fees.get("taker_fee_pct", 0.06)

        self._add_value_label(form, "Maker Fee", f"{maker:.3f}%")
        self._add_value_label(form, "Taker Fee", f"{taker:.3f}%")

        # Show estimated round-trip fee
        roundtrip = taker * 2  # Entry (taker) + Exit (taker for SL)
        self._add_value_label(form, "Round-Trip (Taker)", f"~{roundtrip:.3f}%", highlight=True)

        layout.addWidget(group)

    def _add_data_range(self, layout: QVBoxLayout) -> None:
        """Add data range information group."""
        group, form = self._create_group("Datenbereich", "📅")

        data = self.parameters.get("data_range", {})
        self._add_value_label(form, "Symbol", data.get("symbol", "N/A"), highlight=True)
        self._add_value_label(form, "Timeframe", data.get("timeframe", "N/A"), highlight=True)

        # Show total bars available
        total_bars = data.get("total_bars", 0)
        self._add_value_label(form, "Bars verfügbar", total_bars)

        # Show selected bars (based on time range selection)
        selected_bars = data.get("selected_bars", data.get("visible_bars", "N/A"))
        self._add_value_label(form, "Bars für Simulation", selected_bars, highlight=True)

        # Date range for selected data
        if data.get("start_date"):
            self._add_value_label(form, "Start", data.get("start_date"))
        if data.get("end_date"):
            self._add_value_label(form, "Ende", data.get("end_date"))

        layout.addWidget(group)


def create_test_parameters_dialog(parent, parameters: dict) -> TestParametersDialog:
    """Factory function to create and show the test parameters dialog.

    Args:
        parent: Parent widget
        parameters: Dictionary with parameter categories

    Returns:
        TestParametersDialog instance
    """
    dialog = TestParametersDialog(parent, parameters)
    return dialog
