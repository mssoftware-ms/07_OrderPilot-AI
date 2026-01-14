"""Bitunix HEDGE Execution Widget.

UI for quick, safe order execution via Bitunix Futures API (HEDGE mode).
Single-Trade, Adaptive Limit + Trailing-SL-Sync.

Layout: 3-Column Grid + Status Footer
- Column A: Connection & Risk
- Column B: Entry (Standard / Adaptive)
- Column C: TP/SL & Trailing
- Footer: Status/IDs + Actions

Based on: UI_Spezifikation_TradingBot_Signals_BitunixExecution.md
"""

from __future__ import annotations

import logging
from typing import Optional
from decimal import Decimal

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox,
    QRadioButton, QButtonGroup, QSlider, QFrame, QMessageBox
)
from PyQt6.QtCore import QSettings

logger = logging.getLogger(__name__)


class BitunixHedgeExecutionWidget(QGroupBox):
    """Bitunix HEDGE Execution Widget.

    Provides:
    - Connection & Risk Settings (Column A)
    - Entry Controls: Standard/Adaptive Limit (Column B)
    - TP/SL & Trailing Stop (Column C)
    - Status Footer with State, IDs, Kill Switch

    Signals:
        order_placed: Emitted when order is placed (order_id)
        position_opened: Emitted when position opens (position_id)
        trade_closed: Emitted when trade is closed
    """

    order_placed = pyqtSignal(str)
    position_opened = pyqtSignal(str)
    trade_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Bitunix Execution (HEDGE)", parent)
        self._settings = QSettings("OrderPilot", "BitunixHedge")
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup the 4-column layout with GroupBoxes + Help button."""
        # Main vertical layout for title row + columns
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.setSpacing(8)

        # Issue #68: Live Mode UI moved to Current Position Widget
        # We still initialize them here to keep logic working, but don't add to layout.
        # The parent/mixin will take these widgets and place them in Current Position.
        
        self.live_mode_cb = QCheckBox("Live Trading aktivieren")
        self.live_mode_cb.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.live_mode_cb.setChecked(False)  # Default: Paper mode
        self.live_mode_cb.toggled.connect(self._on_trading_mode_changed)
        
        self.mode_indicator = QLabel("📄 PAPERTRADING")
        self.mode_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_indicator.setStyleSheet(
            "background-color: #26a69a; color: white; "
            "font-weight: bold; font-size: 11px; "  # Issue #68: Reduced from 14px
            "padding: 4px 8px; border-radius: 4px; "  # Issue #68: Reduced padding
            "min-width: 120px;"  # Issue #68: Reduced from 150px
        )

        # Help button (Keep it here or move? Keeping it here for now as it relates to this widget)
        # Actually, help might be better in the groupbox title bar or top right.
        # For now, I'll add it to top right of outer layout if possible, or just append to columns
        
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(20, 20)
        self.help_btn.setStyleSheet(
            "QPushButton { background-color: #4a4a4a; color: white; "
            "font-weight: bold; border-radius: 10px; }"
            "QPushButton:hover { background-color: #666; }"
        )
        self.help_btn.setToolTip("Hilfe zu Bitunix Execution (HEDGE)")
        self.help_btn.clicked.connect(self._on_help)
        header_layout.addWidget(self.help_btn)
        
        outer_layout.addLayout(header_layout)

        # Columns layout (4 GroupBoxes)
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(8)

        # GroupBox A: Connection & Risk
        columns_layout.addWidget(self._create_connection_risk_groupbox())

        # GroupBox B: Entry
        columns_layout.addWidget(self._create_entry_groupbox())

        # GroupBox C: TP/SL & Trailing
        columns_layout.addWidget(self._create_tpsl_groupbox())

        # GroupBox D: Status
        columns_layout.addWidget(self._create_status_groupbox())

        outer_layout.addLayout(columns_layout)

        self.setLayout(outer_layout)

        # Issue #66: Collect all trading widgets for Paper/Live mode control
        self._collect_tradeable_widgets()

        # Set initial mode (Paper mode by default)
        self._update_mode_display(is_live=False)

    def _create_connection_risk_groupbox(self) -> QGroupBox:
        """Create GroupBox A: Connection & Risk."""
        group = QGroupBox("Connection && Risk")
        layout = QFormLayout()
        layout.setVerticalSpacing(4) # Tighter spacing
        layout.setContentsMargins(8, 8, 8, 8)

        # Connection Status
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: #ff5555; font-weight: bold;")
        layout.addRow("Status:", self.connection_status)

        # Symbol ComboBox
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"])
        self.symbol_combo.currentTextChanged.connect(self._on_symbol_changed)
        layout.addRow("Symbol:", self.symbol_combo)

        # Leverage
        leverage_widget = QWidget()
        leverage_layout = QHBoxLayout()
        leverage_layout.setContentsMargins(0, 0, 0, 0)
        leverage_layout.setSpacing(4)

        self.leverage_spin = QSpinBox()
        self.leverage_spin.setRange(1, 125)
        self.leverage_spin.setValue(10)
        self.leverage_spin.setSuffix("x")
        leverage_layout.addWidget(self.leverage_spin)

        self.leverage_btn = QPushButton("Apply")
        self.leverage_btn.setMaximumWidth(50)
        self.leverage_btn.setStyleSheet("padding: 2px;")
        self.leverage_btn.clicked.connect(self._on_apply_leverage)
        leverage_layout.addWidget(self.leverage_btn)

        leverage_widget.setLayout(leverage_layout)
        layout.addRow("Leverage:", leverage_widget)

        # Order Quantity
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.001, 1000.0)
        self.qty_spin.setDecimals(3)
        self.qty_spin.setSingleStep(0.001)
        self.qty_spin.setValue(0.01)
        layout.addRow("Qty (Base):", self.qty_spin)

        # Notional Preview
        self.notional_label = QLabel("≈ $0.00")
        self.notional_label.setStyleSheet("color: #888;")
        layout.addRow("Notional:", self.notional_label)

        # Limits Info
        self.limits_label = QLabel("Min: 0.001, Prec: 0.001/0.1")
        self.limits_label.setStyleSheet("color: #666; font-size: 9px;")
        layout.addRow("Limits:", self.limits_label)

        # Risk Guards - Issue #68: Side-by-side
        risk_widget = QWidget()
        risk_layout = QHBoxLayout()
        risk_layout.setContentsMargins(0, 0, 0, 0)
        risk_layout.setSpacing(4)

        self.require_sl_cb = QCheckBox("Req SL")
        self.require_sl_cb.setChecked(True)
        risk_layout.addWidget(self.require_sl_cb)

        self.confirm_market_cb = QCheckBox("Conf Mkt")
        self.confirm_market_cb.setChecked(True)
        risk_layout.addWidget(self.confirm_market_cb)
        
        risk_widget.setLayout(risk_layout)
        layout.addRow("", risk_widget)

        group.setLayout(layout)
        group.setMaximumWidth(260)
        return group

    def _create_entry_groupbox(self) -> QGroupBox:
        """Create GroupBox B: Entry (Standard / Adaptive)."""
        group = QGroupBox("Entry")
        layout = QFormLayout()
        layout.setVerticalSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        # Direction (Long/Short)
        direction_widget = QWidget()
        direction_layout = QHBoxLayout()
        direction_layout.setContentsMargins(0, 0, 0, 0)
        direction_layout.setSpacing(8)

        self.direction_group = QButtonGroup()
        self.long_radio = QRadioButton("Long")
        self.short_radio = QRadioButton("Short")
        self.long_radio.setStyleSheet("color: #26a69a; font-weight: bold;")
        self.short_radio.setStyleSheet("color: #ef5350; font-weight: bold;")
        self.direction_group.addButton(self.long_radio, 1)
        self.direction_group.addButton(self.short_radio, 2)
        self.long_radio.setChecked(True)

        direction_layout.addWidget(self.long_radio)
        direction_layout.addWidget(self.short_radio)
        direction_layout.addStretch()
        direction_widget.setLayout(direction_layout)
        layout.addRow("Direction:", direction_widget)

        # Entry Mode
        self.entry_mode_combo = QComboBox()
        self.entry_mode_combo.addItems(["Standard", "Adaptive Limit"])
        self.entry_mode_combo.currentTextChanged.connect(self._on_entry_mode_changed)
        layout.addRow("Mode:", self.entry_mode_combo)

        # Order Type (Standard only)
        self.order_type_widget = QWidget()
        order_type_layout = QHBoxLayout()
        order_type_layout.setContentsMargins(0, 0, 0, 0)
        order_type_layout.setSpacing(8)

        self.order_type_group = QButtonGroup()
        self.limit_radio = QRadioButton("LIMIT")
        self.market_radio = QRadioButton("MARKET")
        self.order_type_group.addButton(self.limit_radio, 1)
        self.order_type_group.addButton(self.market_radio, 2)
        self.limit_radio.setChecked(True)
        self.limit_radio.toggled.connect(self._on_order_type_changed)

        order_type_layout.addWidget(self.limit_radio)
        order_type_layout.addWidget(self.market_radio)
        order_type_layout.addStretch()
        self.order_type_widget.setLayout(order_type_layout)
        layout.addRow("Type:", self.order_type_widget)

        # Price (Standard LIMIT only)
        price_widget = QWidget()
        price_layout = QHBoxLayout()
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(4)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.0, 1000000.0)
        self.price_spin.setDecimals(1)
        self.price_spin.setSingleStep(0.1)
        self.price_spin.setValue(0.0)
        price_layout.addWidget(self.price_spin)

        self.use_last_btn = QPushButton("Last")
        self.use_last_btn.setMaximumWidth(40)
        self.use_last_btn.setStyleSheet("padding: 2px;")
        self.use_last_btn.clicked.connect(self._on_use_last_price)
        price_layout.addWidget(self.use_last_btn)

        price_widget.setLayout(price_layout)
        layout.addRow("Price:", price_widget)

        # Adaptive Offset (Adaptive only)
        self.offset_widget = QWidget()
        offset_layout = QHBoxLayout()
        offset_layout.setContentsMargins(0, 0, 0, 0)
        offset_layout.setSpacing(4)

        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(0.01, 1.0)
        self.offset_spin.setDecimals(2)
        self.offset_spin.setSingleStep(0.01)
        self.offset_spin.setValue(0.05)
        self.offset_spin.setSuffix("%")
        offset_layout.addWidget(self.offset_spin)

        self.offset_widget.setLayout(offset_layout)
        self.offset_widget.setVisible(False)  # Hidden by default
        layout.addRow("Offset:", self.offset_widget)

        # Adaptive Target Price
        self.adaptive_target_label = QLabel("Target: —")
        self.adaptive_target_label.setStyleSheet("color: #888;")
        self.adaptive_target_label.setVisible(False)
        layout.addRow("", self.adaptive_target_label)

        # Actions - Issue #68: Side-by-side, smaller
        actions_widget = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 8, 0, 0)
        actions_layout.setSpacing(4)

        # Smaller font style
        btn_style = "color: white; font-weight: bold; padding: 4px; font-size: 11px; border-radius: 4px;"

        self.arm_btn = QPushButton("ARM")
        self.arm_btn.setStyleSheet(f"background-color: #ff9800; {btn_style}")
        self.arm_btn.setMinimumHeight(28)
        self.arm_btn.clicked.connect(self._on_arm)
        actions_layout.addWidget(self.arm_btn)

        self.send_btn = QPushButton("SEND")
        self.send_btn.setStyleSheet(f"background-color: #4CAF50; {btn_style}")
        self.send_btn.setMinimumHeight(28)
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self._on_send)
        actions_layout.addWidget(self.send_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(f"background-color: #666; {btn_style}")
        self.cancel_btn.setMinimumHeight(28)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        actions_layout.addWidget(self.cancel_btn)

        actions_widget.setLayout(actions_layout)
        layout.addRow("", actions_widget)

        group.setLayout(layout)
        group.setMaximumWidth(286)
        return group

    def _create_tpsl_groupbox(self) -> QGroupBox:
        """Create GroupBox C: TP/SL & Trailing."""
        group = QGroupBox("TP/SL && Trailing")
        layout = QFormLayout()
        layout.setVerticalSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        # Take Profit
        tp_widget = QWidget()
        tp_layout = QHBoxLayout()
        tp_layout.setContentsMargins(0, 0, 0, 0)
        tp_layout.setSpacing(4)

        self.tp_cb = QCheckBox()
        self.tp_cb.setChecked(False)
        self.tp_cb.toggled.connect(self._on_tp_toggled)
        tp_layout.addWidget(self.tp_cb)

        self.tp_spin = QDoubleSpinBox()
        self.tp_spin.setRange(0.0, 1000000.0)
        self.tp_spin.setDecimals(1)
        self.tp_spin.setEnabled(False)
        tp_layout.addWidget(self.tp_spin)

        tp_widget.setLayout(tp_layout)
        layout.addRow("TP:", tp_widget)

        # Stop Loss
        sl_widget = QWidget()
        sl_layout = QHBoxLayout()
        sl_layout.setContentsMargins(0, 0, 0, 0)
        sl_layout.setSpacing(4)

        self.sl_cb = QCheckBox()
        self.sl_cb.setChecked(True)
        self.sl_cb.toggled.connect(self._on_sl_toggled)
        sl_layout.addWidget(self.sl_cb)

        self.sl_spin = QDoubleSpinBox()
        self.sl_spin.setRange(0.0, 1000000.0)
        self.sl_spin.setDecimals(1)
        sl_layout.addWidget(self.sl_spin)

        sl_widget.setLayout(sl_layout)
        layout.addRow("SL:", sl_widget)

        # Sync SL Button
        self.sync_sl_btn = QPushButton("Sync SL to Exchange")
        self.sync_sl_btn.setStyleSheet("font-size: 10px; padding: 2px;")
        self.sync_sl_btn.clicked.connect(self._on_sync_sl)
        layout.addRow("", self.sync_sl_btn)

        # Trailing Stop
        self.trailing_cb = QCheckBox("Use Trailing Stop")
        self.trailing_cb.setChecked(False)
        layout.addRow("", self.trailing_cb)

        self.trailing_info = QLabel("Last SL pushed: —")
        self.trailing_info.setStyleSheet("color: #666; font-size: 9px;")
        layout.addRow("", self.trailing_info)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333;")
        layout.addRow(sep)

        # Exit Controls - Issue #68: Side-by-side
        exit_widget = QWidget()
        exit_layout = QHBoxLayout()
        exit_layout.setContentsMargins(0, 0, 0, 0)
        exit_layout.setSpacing(4)

        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("background-color: #ef5350; color: white; font-weight: bold; padding: 4px; font-size: 11px; border-radius: 4px;")
        self.close_btn.clicked.connect(self._on_close_position)
        exit_layout.addWidget(self.close_btn)

        self.flash_close_btn = QPushButton("FLASH")
        self.flash_close_btn.setStyleSheet("background-color: #ff0000; color: white; font-weight: bold; padding: 4px; font-size: 10px; border-radius: 4px;")
        self.flash_close_btn.clicked.connect(self._on_flash_close)
        exit_layout.addWidget(self.flash_close_btn)
        
        exit_widget.setLayout(exit_layout)
        layout.addRow("", exit_widget)

        group.setLayout(layout)
        group.setMaximumWidth(234)
        return group

    def _create_status_groupbox(self) -> QGroupBox:
        """Create GroupBox D: Current Position.

        Contains Live Mode controls, State, Order ID, Position ID, Adaptive, Kill Switch.
        Issue #68: Renamed from "Status" to "Current Position"
        """
        status_group = QGroupBox("Current Position")
        layout = QFormLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setVerticalSpacing(4)

        # Issue #68: Live Mode controls moved from top to here, side-by-side
        live_mode_widget = QWidget()
        live_mode_layout = QHBoxLayout()
        live_mode_layout.setContentsMargins(0, 0, 0, 0)
        live_mode_layout.setSpacing(6)

        live_mode_layout.addWidget(self.live_mode_cb)
        live_mode_layout.addWidget(self.mode_indicator)

        live_mode_widget.setLayout(live_mode_layout)
        layout.addRow("", live_mode_widget)

        # State
        self.state_label = QLabel("IDLE")
        self.state_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        layout.addRow("State:", self.state_label)

        # Order ID
        self.order_id_label = QLabel("—")
        self.order_id_label.setWordWrap(True)
        layout.addRow("Order ID:", self.order_id_label)

        # Position ID
        self.position_id_label = QLabel("—")
        self.position_id_label.setWordWrap(True)
        layout.addRow("Position ID:", self.position_id_label)

        # Adaptive Price
        self.adaptive_price_label = QLabel("—")
        layout.addRow("Adaptive:", self.adaptive_price_label)

        # Spacer
        layout.addRow(QLabel(""))

        # Kill Switch
        self.kill_btn = QPushButton("KILL SWITCH")
        self.kill_btn.setStyleSheet(
            "background-color: #ff0000; color: white; font-weight: bold; "
            "padding: 8px 12px; border-radius: 4px;"
        )
        self.kill_btn.clicked.connect(self._on_kill_switch)
        layout.addRow(self.kill_btn)

        status_group.setLayout(layout)
        status_group.setMinimumWidth(160)
        status_group.setMaximumWidth(200)

        return status_group

    # --- Issue #66: Paper/Live Mode Management ---

    def _collect_tradeable_widgets(self) -> None:
        """Collect all interactive widgets that should be disabled in Paper mode.

        Issue #66: When in Paper Trading mode, all buttons and controls should be
        disabled to prevent accidental live trading.
        """
        self._tradeable_widgets = [
            # GroupBox A: Connection & Risk
            self.symbol_combo,
            self.leverage_spin,
            self.leverage_btn,
            self.qty_spin,
            self.require_sl_cb,
            self.confirm_market_cb,

            # GroupBox B: Entry
            self.long_radio,
            self.short_radio,
            self.entry_mode_combo,
            self.limit_radio,
            self.market_radio,
            self.price_spin,
            self.use_last_btn,
            self.offset_spin,
            self.arm_btn,
            self.send_btn,
            self.cancel_btn,

            # GroupBox C: TP/SL & Trailing
            self.tp_cb,
            self.tp_spin,
            self.sl_cb,
            self.sl_spin,
            self.sync_sl_btn,
            self.trailing_cb,
            self.close_btn,
            self.flash_close_btn,

            # GroupBox D: Status
            self.kill_btn,
        ]

    def _on_trading_mode_changed(self, is_live: bool) -> None:
        """Handle Paper/Live mode toggle.

        Args:
            is_live: True if Live mode is enabled, False for Paper mode

        Issue #66: When switching modes, update the visual indicator and
        enable/disable all trading controls accordingly.
        """
        logger.info(f"Trading mode changed: {'LIVE' if is_live else 'PAPER'}")
        self._update_mode_display(is_live)
        self._save_settings()

        # Show warning dialog when switching to Live mode
        if is_live:
            reply = QMessageBox.warning(
                self,
                "Live Trading aktiviert",
                "⚠️ ACHTUNG: Live Trading ist jetzt aktiviert!\n\n"
                "Alle Trades werden REAL ausgeführt und verwenden ECHTES Geld.\n\n"
                "Sind Sie sicher, dass Sie Live Trading aktivieren möchten?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                # User cancelled, revert to Paper mode
                self.live_mode_cb.setChecked(False)
                return

    def _update_mode_display(self, is_live: bool) -> None:
        """Update the mode indicator banner and enable/disable trading widgets.

        Args:
            is_live: True if Live mode, False for Paper mode

        Issue #66: Visual indicator and button states must clearly show current mode.
        """
        if is_live:
            # Live mode: Red banner, all controls enabled
            self.mode_indicator.setText("🔴 LIVE TRADING")
            self.mode_indicator.setStyleSheet(
                "background-color: #ef5350; color: white; "
                "font-weight: bold; font-size: 11px; "  # Issue #68: Reduced from 14px
                "padding: 4px 8px; border-radius: 4px; "  # Issue #68: Reduced padding
                "min-width: 120px;"  # Issue #68: Reduced from 150px
            )
            enabled = True
        else:
            # Paper mode: Green banner, all controls disabled
            self.mode_indicator.setText("📄 PAPERTRADING")
            self.mode_indicator.setStyleSheet(
                "background-color: #26a69a; color: white; "
                "font-weight: bold; font-size: 11px; "  # Issue #68: Reduced from 14px
                "padding: 4px 8px; border-radius: 4px; "  # Issue #68: Reduced padding
                "min-width: 120px;"  # Issue #68: Reduced from 150px
            )
            enabled = False

        # Enable/disable all trading widgets
        for widget in self._tradeable_widgets:
            widget.setEnabled(enabled)

    # --- Event Handlers ---

    def _on_symbol_changed(self, symbol: str):
        """Handle symbol change."""
        logger.info(f"Symbol changed to: {symbol}")
        self._save_settings()

    def _on_apply_leverage(self):
        """Apply leverage setting."""
        leverage = self.leverage_spin.value()
        logger.info(f"Applying leverage: {leverage}x")
        self._save_settings()

    def _on_entry_mode_changed(self, mode: str):
        """Handle entry mode change."""
        is_adaptive = mode == "Adaptive Limit"
        self.order_type_widget.setVisible(not is_adaptive)
        self.price_spin.setEnabled(not is_adaptive and self.limit_radio.isChecked())
        self.use_last_btn.setEnabled(not is_adaptive and self.limit_radio.isChecked())
        self.offset_widget.setVisible(is_adaptive)
        self.adaptive_target_label.setVisible(is_adaptive)

    def _on_order_type_changed(self, is_limit: bool):
        """Handle order type change."""
        self.price_spin.setEnabled(is_limit)
        self.use_last_btn.setEnabled(is_limit)

    def _on_use_last_price(self):
        """Set price to last traded price."""
        # TODO: Get last price from market data
        logger.info("Use last price clicked")

    def _on_tp_toggled(self, checked: bool):
        """Handle TP checkbox toggle."""
        self.tp_spin.setEnabled(checked)

    def _on_sl_toggled(self, checked: bool):
        """Handle SL checkbox toggle."""
        self.sl_spin.setEnabled(checked)

    def _on_sync_sl(self):
        """Sync SL to exchange."""
        logger.info("Sync SL to exchange")

    def _on_arm(self):
        """Arm the order."""
        self.arm_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px 12px;")
        self.arm_btn.setText("ARMED")
        self.send_btn.setEnabled(True)
        logger.info("Order armed")

    def _on_send(self):
        """Send the order."""
        # Validate
        if self.require_sl_cb.isChecked() and not self.sl_cb.isChecked():
            QMessageBox.warning(self, "Validation Error", "SL is required but not set!")
            return

        direction = "LONG" if self.long_radio.isChecked() else "SHORT"
        qty = self.qty_spin.value()

        logger.info(f"Sending {direction} order: qty={qty}")

        # Reset arm state
        self.arm_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 6px 12px;")
        self.arm_btn.setText("ARM")
        self.send_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        # Update state
        self.state_label.setText("ENTRY_PENDING")
        self.state_label.setStyleSheet("font-weight: bold; color: #ff9800;")

    def _on_cancel(self):
        """Cancel pending order."""
        logger.info("Cancelling pending order")
        self.cancel_btn.setEnabled(False)
        self.state_label.setText("IDLE")
        self.state_label.setStyleSheet("font-weight: bold; color: #4CAF50;")

    def _on_close_position(self):
        """Close position."""
        if self.confirm_market_cb.isChecked():
            reply = QMessageBox.question(
                self, "Confirm Close",
                "Are you sure you want to close the position?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        logger.info("Closing position")

    def _on_flash_close(self):
        """Flash close (emergency)."""
        reply = QMessageBox.warning(
            self, "FLASH CLOSE",
            "This will immediately close ALL positions!\n\nAre you absolutely sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.warning("FLASH CLOSE executed!")

    def _on_help(self):
        """Open help page for Bitunix Execution (HEDGE).

        Issue #57: Fixed path to help file - was going up too many directories
        and using lowercase 'help' instead of 'Help'.
        """
        import os
        import webbrowser

        # Path to help file (Issue #57: Fixed - 4 levels up, 'Help' capitalized)
        help_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "Help", "BitunixExcecution_HEDGE.html"
        )

        if os.path.exists(help_path):
            webbrowser.open(f"file://{help_path}")
        else:
            QMessageBox.information(
                self, "Hilfe",
                "Hilfeseite nicht gefunden.\n\n"
                f"Erwartet unter:\n{help_path}"
            )

    def _on_kill_switch(self):
        """Kill switch - stop everything."""
        reply = QMessageBox.critical(
            self, "KILL SWITCH",
            "This will:\n- Cancel ALL pending orders\n- Stop adaptive limit\n- Disable trading\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.critical("KILL SWITCH activated!")
            self.state_label.setText("KILLED")
            self.state_label.setStyleSheet("font-weight: bold; color: #ff0000;")

    def _load_settings(self):
        """Load settings from QSettings."""
        self.symbol_combo.setCurrentText(self._settings.value("last_symbol", "BTCUSDT"))
        self.leverage_spin.setValue(int(self._settings.value("last_leverage", 10)))
        self.qty_spin.setValue(float(self._settings.value("last_qty", 0.01)))
        self.offset_spin.setValue(float(self._settings.value("last_offset", 0.05)))

        # Issue #66: Load Paper/Live mode setting (default: Paper mode = False)
        is_live = self._settings.value("live_trading_enabled", False, type=bool)
        self.live_mode_cb.setChecked(is_live)
        self._update_mode_display(is_live)

    def _save_settings(self):
        """Save settings to QSettings."""
        self._settings.setValue("last_symbol", self.symbol_combo.currentText())
        self._settings.setValue("last_leverage", self.leverage_spin.value())
        self._settings.setValue("last_qty", self.qty_spin.value())
        self._settings.setValue("last_offset", self.offset_spin.value())

        # Issue #66: Save Paper/Live mode setting
        self._settings.setValue("live_trading_enabled", self.live_mode_cb.isChecked())

    # --- Public API for external status labels ---

    def set_status_labels(self, state_label, order_id_label, position_id_label, adaptive_label, kill_btn):
        """Set external status labels from the Status Panel.

        This allows the widget to update status information in a separate Status Panel.
        """
        # Copy current values first
        if hasattr(self, 'state_label'):
            state_label.setText(self.state_label.text())
            state_label.setStyleSheet(self.state_label.styleSheet())

        # Replace internal references with external labels
        self.state_label = state_label
        self.order_id_label = order_id_label
        self.position_id_label = position_id_label
        self.adaptive_price_label = adaptive_label

        # Connect kill button
        if kill_btn:
            kill_btn.clicked.connect(self._on_kill_switch)