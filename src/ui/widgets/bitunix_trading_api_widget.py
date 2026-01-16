"""Bitunix Trading API Widget - Compact Order Entry for Signals Tab.

Lightweight trading interface for the Trading Bot Signals tab.
Provides quick order entry with automatic quantity/volume calculation.

Features:
    - Symbol selection
    - Quantity (Base Asset) ↔ Volume (USDT) conversion
    - Leverage control
    - Buy/Sell buttons
    - Live/Paper mode support

Layout: Single vertical GroupBox with compact form layout.
"""

from __future__ import annotations

import logging
from typing import Optional
from decimal import Decimal

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QSlider,
    QMessageBox, QButtonGroup, QSizePolicy
)

import qasync
from src.core.broker.broker_types import OrderRequest, OrderSide
from src.database.models import OrderType as DBOrderType

logger = logging.getLogger(__name__)


class BitunixTradingAPIWidget(QGroupBox):
    """Compact trading interface for Bitunix API.

    Provides quick order entry with automatic quantity/volume calculation.
    Designed for the Trading Bot Signals tab.

    Signals:
        order_placed: Emitted when order is placed successfully
        price_needed: Emitted when price is required for calculations
    """

    order_placed = pyqtSignal(str)  # order_id
    price_needed = pyqtSignal(str)  # symbol

    def __init__(self, parent=None):
        super().__init__("Bitunix Trading API", parent)
        self.parent_widget = parent
        self._adapter = None
        self._current_symbol = None
        self._last_price = 0.0
        self._last_edited = "quantity"
        self._is_updating = False  # Prevent recursive updates
        self._setup_ui()

    def _setup_ui(self):
        """Setup compact UI layout - 3 columns: Left (Symbol/Direction/OrderType), Middle (Quantity/Volume/Leverage), Right (Buttons/Slider)."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 12, 8, 8)
        main_layout.setSpacing(6)

        # Main horizontal layout with 3 columns
        h_layout = QHBoxLayout()
        h_layout.setSpacing(12)

        # LEFT COLUMN: Symbol, Direction, Order Type, Limit Price
        left_column = self._build_left_column()
        h_layout.addWidget(left_column)

        # MIDDLE COLUMN: Stückzahl, Volumen, Leverage, Last Price
        middle_column = self._build_middle_column()
        h_layout.addWidget(middle_column)

        # RIGHT COLUMN: BUY/SELL buttons, Paper Trading, Slider, Presets
        right_column = self._build_right_column()
        h_layout.addWidget(right_column)

        main_layout.addLayout(h_layout)

        # Bottom: Adapter status (right-aligned, small)
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.adapter_status_label = QLabel("disconnected")
        self.adapter_status_label.setStyleSheet("color: #888; font-size: 9px;")
        status_layout.addWidget(self.adapter_status_label)
        main_layout.addLayout(status_layout)

        self.setLayout(main_layout)
        self.setMaximumHeight(230)
        self.setMinimumWidth(700)
        self._set_trade_mode_live(False)

    def _build_left_column(self) -> QWidget:
        """Build left column with Symbol, Direction, Order Type, Limit Price."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        # Symbol Selection
        self.symbol_combo = QComboBox()
        self.symbol_combo.setFixedWidth(180)
        self.symbol_combo.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"])
        self.symbol_combo.currentTextChanged.connect(self._on_symbol_changed)

        symbol_label = QLabel("Symbol:")
        grid.addWidget(symbol_label, 0, 0)
        grid.addWidget(self.symbol_combo, 0, 1)

        # Direction (Long/Short)
        direction_widget = QWidget()
        direction_layout = QHBoxLayout()
        direction_layout.setContentsMargins(0, 0, 0, 0)
        direction_layout.setSpacing(6)

        self.long_btn = QPushButton("Long")
        self.short_btn = QPushButton("Short")
        self.long_btn.setFixedWidth(87)
        self.short_btn.setFixedWidth(87)
        self.long_btn.setFixedHeight(32)
        self.short_btn.setFixedHeight(32)
        self.long_btn.setCheckable(True)
        self.short_btn.setCheckable(True)
        self.long_btn.setChecked(True)
        self.long_btn.clicked.connect(lambda: self._set_direction("LONG"))
        self.short_btn.clicked.connect(lambda: self._set_direction("SHORT"))

        self.long_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #26a69a;
                color: white;
                font-weight: bold;
            }
        """)
        self.short_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #3a3a3a;
                color: #888;
            }
        """)

        direction_layout.addWidget(self.long_btn)
        direction_layout.addWidget(self.short_btn)
        direction_widget.setLayout(direction_layout)

        direction_label = QLabel("Direction:")
        grid.addWidget(direction_label, 1, 0)
        grid.addWidget(direction_widget, 1, 1)

        # Order Type (Market/Limit)
        order_type_widget = QWidget()
        order_type_layout = QHBoxLayout()
        order_type_layout.setContentsMargins(0, 0, 0, 0)
        order_type_layout.setSpacing(6)

        self.order_type_group = QButtonGroup()
        self.order_type_group.setExclusive(True)
        self.market_btn = QPushButton("Market")
        self.limit_btn = QPushButton("Limit")
        self.market_btn.setFixedWidth(87)
        self.limit_btn.setFixedWidth(87)
        self.market_btn.setFixedHeight(32)
        self.limit_btn.setFixedHeight(32)
        self.market_btn.setCheckable(True)
        self.limit_btn.setCheckable(True)
        self.order_type_group.addButton(self.market_btn)
        self.order_type_group.addButton(self.limit_btn)
        self.market_btn.setChecked(True)
        self.market_btn.clicked.connect(self._on_order_type_changed)
        self.limit_btn.clicked.connect(self._on_order_type_changed)

        self.market_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
        """)
        self.limit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #3a3a3a;
                color: #888;
            }
        """)

        order_type_layout.addWidget(self.market_btn)
        order_type_layout.addWidget(self.limit_btn)
        order_type_widget.setLayout(order_type_layout)

        order_type_label = QLabel("Order Type:")
        grid.addWidget(order_type_label, 2, 0)
        grid.addWidget(order_type_widget, 2, 1)

        # Limit Price (only for Limit orders)
        self.limit_price_label = QLabel("Limit Price:")
        grid.addWidget(self.limit_price_label, 3, 0)

        self.limit_price_spin = QDoubleSpinBox()
        self.limit_price_spin.setFixedWidth(180)
        self.limit_price_spin.setRange(0.0, 1000000.0)
        self.limit_price_spin.setDecimals(2)
        self.limit_price_spin.setSingleStep(0.1)
        self.limit_price_spin.setValue(0.0)
        self.limit_price_spin.valueChanged.connect(self._on_limit_price_changed)
        self.limit_price_spin.setVisible(False)
        grid.addWidget(self.limit_price_spin, 3, 1)
        self.limit_price_label.setVisible(False)

        layout.addLayout(grid)
        widget.setLayout(layout)
        return widget

    def _build_middle_column(self) -> QWidget:
        """Build middle column with Stückzahl, Volumen, Leverage, Last Price."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        # Quantity (Base Asset)
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setFixedWidth(150)
        self.quantity_spin.setRange(0.001, 10000.0)
        self.quantity_spin.setDecimals(3)
        self.quantity_spin.setSingleStep(0.001)
        self.quantity_spin.setValue(0.01)
        self.quantity_spin.setSuffix(" BTC")
        self.quantity_spin.valueChanged.connect(self._on_quantity_changed)

        quantity_label = QLabel("Stückzahl:")
        grid.addWidget(quantity_label, 0, 0)
        grid.addWidget(self.quantity_spin, 0, 1)

        # Volume (USDT)
        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setFixedWidth(150)
        self.volume_spin.setRange(1.0, 1000000.0)
        self.volume_spin.setDecimals(2)
        self.volume_spin.setSingleStep(10.0)
        self.volume_spin.setValue(1000.0)
        self.volume_spin.setSuffix(" USDT")
        self.volume_spin.valueChanged.connect(self._on_volume_changed)

        volume_label = QLabel("Volumen:")
        grid.addWidget(volume_label, 1, 0)
        grid.addWidget(self.volume_spin, 1, 1)

        # Leverage
        self.leverage_spin = QSpinBox()
        self.leverage_spin.setFixedWidth(150)
        self.leverage_spin.setRange(1, 125)
        self.leverage_spin.setValue(10)
        self.leverage_spin.setSuffix("x")
        self.leverage_spin.valueChanged.connect(self._on_leverage_changed_spinbox)

        leverage_label = QLabel("Leverage:")
        grid.addWidget(leverage_label, 2, 0)
        grid.addWidget(self.leverage_spin, 2, 1)

        # Current Price Display
        self.price_label = QLabel("—")
        self.price_label.setStyleSheet("color: #888; font-size: 11px;")

        last_price_label = QLabel("Last Price:")
        grid.addWidget(last_price_label, 3, 0)
        grid.addWidget(self.price_label, 3, 1)

        layout.addLayout(grid)
        widget.setLayout(layout)
        return widget

    def _build_right_column(self) -> QWidget:
        """Build right column with BUY/SELL buttons, Paper Trading button, Slider, Presets."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # BUY/SELL buttons (top row)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(6)

        self.buy_btn = QPushButton("BUY")
        self.buy_btn.setFixedWidth(107)
        self.buy_btn.setFixedHeight(32)
        self.buy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #888;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        self.buy_btn.clicked.connect(self._on_buy_clicked)
        buttons_layout.addWidget(self.buy_btn)

        self.sell_btn = QPushButton("SELL")
        self.sell_btn.setFixedWidth(107)
        self.sell_btn.setFixedHeight(32)
        self.sell_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #888;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        self.sell_btn.clicked.connect(self._on_sell_clicked)
        buttons_layout.addWidget(self.sell_btn)

        layout.addLayout(buttons_layout)

        # Paper Trading button
        self.trade_mode_btn = QPushButton("Paper Trading")
        self.trade_mode_btn.setCheckable(True)
        self.trade_mode_btn.setFixedHeight(32)
        self.trade_mode_btn.setFixedWidth(220)
        self.trade_mode_btn.clicked.connect(self._on_trade_mode_changed)
        layout.addWidget(self.trade_mode_btn)

        # Leverage slider with orange indicator
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setFixedWidth(220)
        self.exposure_slider.setRange(10, 200)
        self.exposure_slider.setSingleStep(10)
        self.exposure_slider.setPageStep(10)
        self.exposure_slider.setValue(10)
        self.exposure_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #3a3a3a;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #ffa726;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #2a2a2a;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffa726;
                border: 2px solid #ff9800;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
        """)
        self.exposure_slider.valueChanged.connect(self._on_exposure_changed)
        layout.addWidget(self.exposure_slider)

        # Preset buttons (10, 20, 30, ..., 190)
        presets_widget = QWidget()
        presets_widget.setFixedWidth(220)
        presets_layout = QGridLayout()
        presets_layout.setContentsMargins(0, 0, 0, 0)
        presets_layout.setHorizontalSpacing(3)
        presets_layout.setVerticalSpacing(3)

        preset_values = list(range(10, 200, 10))
        for idx, value in enumerate(preset_values):
            btn = QPushButton(str(value))
            btn.setFixedSize(22, 16)
            btn.setStyleSheet(
                "background-color: #3a3a3a; color: #aaa; font-size: 8px; "
                "border-radius: 2px; padding: 0px;"
            )
            btn.clicked.connect(lambda _, v=value: self._on_preset_clicked(v))
            row = idx // 10
            col = idx % 10
            presets_layout.addWidget(btn, row, col)

        presets_widget.setLayout(presets_layout)
        layout.addWidget(presets_widget)

        widget.setLayout(layout)
        return widget

    def _on_leverage_changed_spinbox(self, value: int):
        """Sync slider with spinbox."""
        self.exposure_slider.blockSignals(True)
        self.exposure_slider.setValue(value)
        self.exposure_slider.blockSignals(False)

    def _on_preset_clicked(self, value: int):
        """Handle preset button click."""
        self.exposure_slider.setValue(value)
        self.leverage_spin.setValue(value)


    def _set_direction(self, direction: str):
        """Set position direction (LONG/SHORT)."""
        if direction == "LONG":
            self.long_btn.setChecked(True)
            self.short_btn.setChecked(False)
        else:
            self.long_btn.setChecked(False)
            self.short_btn.setChecked(True)
        logger.debug(f"Direction set to: {direction}")

    def _get_direction(self) -> str:
        """Get current position direction."""
        return "LONG" if self.long_btn.isChecked() else "SHORT"

    def _on_symbol_changed(self, symbol: str):
        """Handle symbol change."""
        self._current_symbol = symbol
        # Update suffix for quantity spinbox
        base_asset = symbol.replace("USDT", "")
        self.quantity_spin.setSuffix(f" {base_asset}")

        # Request price update from parent
        if self.parent_widget and hasattr(self.parent_widget, '_get_current_price_for_symbol'):
            price = self.parent_widget._get_current_price_for_symbol(symbol)
            self.set_price(price)
        else:
            self.price_needed.emit(symbol)

        logger.info(f"Symbol changed to: {symbol}")

    def _on_order_type_changed(self):
        """Handle order type change."""
        is_limit = self.limit_btn.isChecked()
        self.limit_price_spin.setVisible(is_limit)
        self.limit_price_label.setVisible(is_limit)
        if is_limit:
            self._ensure_limit_price_default()
        self._recalculate_from_price()


    def _on_limit_price_changed(self, value: float):
        """Handle limit price change."""
        if self._is_updating:
            return
        if value <= 0:
            return
        self._recalculate_from_price()

    def _on_quantity_changed(self, value: float):
        """Calculate volume from quantity."""
        if self._is_updating:
            return

        if value <= 0:
            return

        price = self._get_effective_price()
        if price <= 0:
            return

        self._is_updating = True
        self._last_edited = "quantity"
        volume = value * price
        self.volume_spin.blockSignals(True)
        self.volume_spin.setValue(volume)
        self.volume_spin.blockSignals(False)
        self._is_updating = False

    def _on_volume_changed(self, value: float):
        """Calculate quantity from volume."""
        if self._is_updating:
            return

        if value <= 0:
            return

        price = self._get_effective_price()
        if price <= 0:
            return

        self._is_updating = True
        self._last_edited = "volume"
        quantity = value / price
        self.quantity_spin.blockSignals(True)
        self.quantity_spin.setValue(quantity)
        self.quantity_spin.blockSignals(False)
        self._is_updating = False

    def _on_exposure_changed(self, value: int):
        """Update exposure label."""
        self.leverage_spin.blockSignals(True)
        self.leverage_spin.setValue(value)
        self.leverage_spin.blockSignals(False)

    def _on_trade_mode_changed(self) -> None:
        """Toggle paper/live trading mode."""
        self._set_trade_mode_live(self.trade_mode_btn.isChecked())

    def _set_trade_mode_live(self, is_live: bool) -> None:
        """Apply live trading mode to UI state."""
        if is_live:
            self.trade_mode_btn.setText("Live Trading")
            self.trade_mode_btn.setChecked(True)
            self.trade_mode_btn.setStyleSheet(
                "background-color: #ef5350; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px;"
            )
            self._connect_adapter_for_live_mode()
        else:
            self.trade_mode_btn.setText("Paper Trading")
            self.trade_mode_btn.setChecked(False)
            self.trade_mode_btn.setStyleSheet(
                "background-color: #26a69a; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px;"
            )
            self._disconnect_adapter_for_paper_mode()
        self._update_button_states()

    @qasync.asyncSlot()
    async def _on_buy_clicked(self):
        """Handle BUY button click."""
        await self._place_order(OrderSide.BUY)

    @qasync.asyncSlot()
    async def _on_sell_clicked(self):
        """Handle SELL button click."""
        await self._place_order(OrderSide.SELL)

    async def _place_order(self, side: OrderSide):
        """Place order with current settings."""
        if not self._adapter:
            QMessageBox.warning(self, "No Adapter", "No trading adapter connected!")
            return

        if not self._current_symbol:
            QMessageBox.warning(self, "No Symbol", "Please select a trading symbol!")
            return

        # Get order parameters
        direction = self._get_direction()
        quantity = self.quantity_spin.value()
        volume = self.volume_spin.value()
        leverage = self.leverage_spin.value()
        order_type_label = "Limit" if self.limit_btn.isChecked() else "Market"

        if order_type_label == "Limit":
            limit_price = self.limit_price_spin.value()
            if limit_price <= 0:
                QMessageBox.warning(
                    self,
                    "No Limit Price",
                    "Please enter a valid limit price."
                )
                return
        else:
            if self._last_price <= 0:
                QMessageBox.warning(
                    self,
                    "No Price",
                    f"No price available for {self._current_symbol}.\n\n"
                    "Please ensure chart data is loaded."
                )
                return

        # Confirm order
        action = "BUY" if side == OrderSide.BUY else "SELL"
        price_line = (
            f"Limit Price: {limit_price:.2f} USDT"
            if order_type_label == "Limit"
            else f"Est. Price: {self._last_price:.2f} USDT"
        )
        confirm_msg = (
            f"Confirm {action} Order\n\n"
            f"Symbol: {self._current_symbol}\n"
            f"Direction: {direction}\n"
            f"Quantity: {quantity:.3f}\n"
            f"Volume: {volume:.2f} USDT\n"
            f"Leverage: {leverage}x\n"
            f"{price_line}"
        )

        reply = QMessageBox.question(
            self,
            "Confirm Order",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Create order request
        try:
            if order_type_label == "Limit":
                order_type = DBOrderType.LIMIT
                order_limit_price = Decimal(str(limit_price))
            else:
                order_type = DBOrderType.MARKET
                order_limit_price = None

            order_request = OrderRequest(
                symbol=self._current_symbol,
                side=side,
                order_type=order_type,
                quantity=Decimal(str(quantity)),
                limit_price=order_limit_price
            )

            # Place order
            logger.info(f"Placing {action} order: {order_request}")
            response = await self._adapter.place_order(order_request)

            if response and response.order_id:
                QMessageBox.information(
                    self,
                    "Order Placed",
                    f"Order placed successfully!\n\n"
                    f"Order ID: {response.order_id}\n"
                    f"Status: {response.status}"
                )
                self.order_placed.emit(response.order_id)
            else:
                QMessageBox.warning(self, "Order Failed", "Order placement failed!")

        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            QMessageBox.critical(
                self,
                "Order Error",
                f"Failed to place order:\n\n{str(e)}"
            )

    # === Public API ===

    def set_adapter(self, adapter):
        """Set trading adapter.

        Args:
            adapter: BitunixAdapter or BitunixPaperAdapter instance
        """
        self._adapter = adapter
        self._update_button_states()
        logger.info(f"Adapter set: {adapter.__class__.__name__ if adapter else None}")

    def set_symbol(self, symbol: str):
        """Set trading symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
        """
        index = self.symbol_combo.findText(symbol)
        if index >= 0:
            self.symbol_combo.setCurrentIndex(index)
        else:
            self.symbol_combo.addItem(symbol)
            self.symbol_combo.setCurrentText(symbol)

    def set_price(self, price: float):
        """Update current price.

        Args:
            price: Current market price
        """
        if price > 0:
            self._last_price = price
            self.price_label.setText(f"{price:.2f} USDT")
            self.limit_price_spin.blockSignals(True)
            self.limit_price_spin.setValue(price)
            self.limit_price_spin.blockSignals(False)
            self._recalculate_from_price()

    def _ensure_limit_price_default(self) -> None:
        """Default limit price to current market price when available."""
        if not self.limit_btn.isChecked():
            return
        if self._last_price <= 0:
            return
        if self.limit_price_spin.value() > 0:
            return
        self.limit_price_spin.blockSignals(True)
        self.limit_price_spin.setValue(self._last_price)
        self.limit_price_spin.blockSignals(False)

    def _get_effective_price(self) -> float:
        """Get the price used for volume/quantity calculations."""
        if self.limit_btn.isChecked():
            limit_price = self.limit_price_spin.value()
            if limit_price > 0:
                return limit_price
        return self._last_price

    def _recalculate_from_price(self) -> None:
        """Recalculate dependent field using the active price source."""
        if self._is_updating:
            return

        price = self._get_effective_price()
        if price <= 0:
            return

        self._is_updating = True
        if self._last_edited == "volume":
            volume = self.volume_spin.value()
            if volume > 0:
                quantity = volume / price
                self.quantity_spin.blockSignals(True)
                self.quantity_spin.setValue(quantity)
                self.quantity_spin.blockSignals(False)
        else:
            quantity = self.quantity_spin.value()
            if quantity > 0:
                volume = quantity * price
                self.volume_spin.blockSignals(True)
                self.volume_spin.setValue(volume)
                self.volume_spin.blockSignals(False)
        self._is_updating = False

    def _update_button_states(self):
        """Update button enabled states."""
        enabled = (
            self._adapter is not None
            and self._current_symbol is not None
            and self.trade_mode_btn.isChecked()
        )
        self.buy_btn.setEnabled(enabled)
        self.sell_btn.setEnabled(enabled)

    def _connect_adapter_for_live_mode(self) -> None:
        """Ensure adapter is connected when live mode is enabled."""
        if not self._adapter:
            parent = self.parent_widget or self.parent()
            if parent is not None and hasattr(parent, "_bitunix_adapter"):
                self._adapter = getattr(parent, "_bitunix_adapter")
            if not self._adapter:
                QMessageBox.warning(self, "No Adapter", "No trading adapter connected!")
                self.adapter_status_label.setText("missing")
                self.adapter_status_label.setStyleSheet("color: #f44336; font-size: 10px;")
                return
        try:
            import asyncio
            self.adapter_status_label.setText("connecting...")
            self.adapter_status_label.setStyleSheet("color: #ffa726; font-size: 10px;")
            asyncio.create_task(self._adapter.connect())
        except Exception as exc:
            logger.error(f"Adapter connect failed: {exc}")
            self.adapter_status_label.setText("error")
            self.adapter_status_label.setStyleSheet("color: #f44336; font-size: 10px;")
            QMessageBox.critical(self, "Connection Error", f"Adapter connect failed:\n\n{exc}")

    def _disconnect_adapter_for_paper_mode(self) -> None:
        """Disconnect adapter when switching to paper mode."""
        if not self._adapter:
            return
        try:
            import asyncio
            self.adapter_status_label.setText("disconnecting...")
            self.adapter_status_label.setStyleSheet("color: #ffa726; font-size: 10px;")
            asyncio.create_task(self._adapter.disconnect())
            self.adapter_status_label.setText("disconnected")
            self.adapter_status_label.setStyleSheet("color: #888; font-size: 10px;")
        except Exception as exc:
            logger.error(f"Adapter disconnect failed: {exc}")
            self.adapter_status_label.setText("error")
            self.adapter_status_label.setStyleSheet("color: #f44336; font-size: 10px;")
