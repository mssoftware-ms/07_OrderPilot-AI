"""Bitunix Trading Widget - Dockable trading panel for Bitunix Futures.

Provides order entry, position management, and account information for Bitunix.
"""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QHeaderView,
)

from src.core.broker.broker_types import OrderRequest, OrderSide
from src.database.models import OrderType as DBOrderType

if TYPE_CHECKING:
    from src.core.broker.bitunix_adapter import BitunixAdapter

logger = logging.getLogger(__name__)


class BitunixTradingWidget(QDockWidget):
    """Dockable trading widget for Bitunix Futures.

    Features:
        - Order entry panel (Market/Limit, Buy/Sell)
        - Position management table
        - Account info display (Balance, Margin, PnL)
    """

    def __init__(self, adapter: BitunixAdapter | None = None, parent=None):
        """Initialize Bitunix trading widget.

        Args:
            adapter: Bitunix adapter instance (optional)
            parent: Parent widget
        """
        super().__init__("💱 Bitunix Trading", parent)

        self.adapter = adapter
        self._current_symbol = None

        self._setup_ui()
        self._setup_timers()

        if self.adapter:
            self._start_updates()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(350)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Account info section
        layout.addWidget(self._build_account_section())

        # Order entry section
        layout.addWidget(self._build_order_entry_section())

        # Positions section
        layout.addWidget(self._build_positions_section())

        layout.addStretch()
        self.setWidget(container)

    def _build_account_section(self) -> QGroupBox:
        """Build account information display.

        Returns:
            Account info group box
        """
        group = QGroupBox("Account Info")
        layout = QVBoxLayout(group)

        # Balance row
        balance_layout = QHBoxLayout()
        balance_layout.addWidget(QLabel("Balance:"))
        self.balance_label = QLabel("-- USDT")
        self.balance_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        balance_layout.addWidget(self.balance_label)
        balance_layout.addStretch()
        layout.addLayout(balance_layout)

        # Margin row
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Available Margin:"))
        self.margin_label = QLabel("-- USDT")
        self.margin_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        margin_layout.addWidget(self.margin_label)
        margin_layout.addStretch()
        layout.addLayout(margin_layout)

        # PnL row
        pnl_layout = QHBoxLayout()
        pnl_layout.addWidget(QLabel("Daily PnL:"))
        self.pnl_label = QLabel("-- USDT")
        pnl_layout.addWidget(self.pnl_label)
        pnl_layout.addStretch()
        layout.addLayout(pnl_layout)

        return group

    def _build_order_entry_section(self) -> QGroupBox:
        """Build order entry panel.

        Returns:
            Order entry group box
        """
        group = QGroupBox("Place Order")
        layout = QVBoxLayout(group)

        # Symbol display
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Symbol:"))
        self.symbol_label = QLabel("--")
        self.symbol_label.setStyleSheet("font-weight: bold; color: #FFC107;")
        symbol_layout.addWidget(self.symbol_label)
        symbol_layout.addStretch()
        layout.addLayout(symbol_layout)

        # Order type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["Market", "Limit"])
        self.order_type_combo.currentTextChanged.connect(self._on_order_type_changed)
        type_layout.addWidget(self.order_type_combo)
        layout.addLayout(type_layout)

        # Quantity
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:"))
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setDecimals(4)
        self.quantity_spin.setMinimum(0.0001)
        self.quantity_spin.setMaximum(1000000)
        self.quantity_spin.setValue(0.01)
        qty_layout.addWidget(self.quantity_spin)
        layout.addLayout(qty_layout)

        # Price (for limit orders)
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Price:"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setDecimals(2)
        self.price_spin.setMinimum(0)
        self.price_spin.setMaximum(1000000)
        self.price_spin.setEnabled(False)  # Disabled by default (Market order)
        price_layout.addWidget(self.price_spin)
        layout.addLayout(price_layout)

        # Leverage
        leverage_layout = QHBoxLayout()
        leverage_layout.addWidget(QLabel("Leverage:"))
        self.leverage_spin = QSpinBox()
        self.leverage_spin.setMinimum(1)
        self.leverage_spin.setMaximum(100)
        self.leverage_spin.setValue(1)
        leverage_layout.addWidget(self.leverage_spin)
        layout.addLayout(leverage_layout)

        # Buy/Sell buttons
        button_layout = QHBoxLayout()
        self.buy_button = QPushButton("🟢 BUY")
        self.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.buy_button.clicked.connect(self._on_buy_clicked)
        button_layout.addWidget(self.buy_button)

        self.sell_button = QPushButton("🔴 SELL")
        self.sell_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.sell_button.clicked.connect(self._on_sell_clicked)
        button_layout.addWidget(self.sell_button)
        layout.addLayout(button_layout)

        # Initially disable buttons (no adapter)
        self._update_button_states()

        return group

    def _build_positions_section(self) -> QGroupBox:
        """Build positions table.

        Returns:
            Positions group box
        """
        group = QGroupBox("Open Positions")
        layout = QVBoxLayout(group)

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(5)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Qty", "Entry", "Current", "PnL"
        ])
        self.positions_table.horizontalHeader().setStretchLastSection(True)
        self.positions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.positions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Auto-resize columns
        header = self.positions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.positions_table)

        # Refresh button
        refresh_button = QPushButton("🔄 Refresh Positions")
        refresh_button.clicked.connect(self._load_positions)
        layout.addWidget(refresh_button)

        return group

    def _setup_timers(self) -> None:
        """Set up periodic update timers."""
        # Update account info every 10 seconds
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self._load_account_info)
        self.account_timer.setInterval(10000)

        # Update positions every 5 seconds
        self.positions_timer = QTimer()
        self.positions_timer.timeout.connect(self._load_positions)
        self.positions_timer.setInterval(5000)

    def _start_updates(self) -> None:
        """Start periodic updates."""
        if self.adapter:
            self.account_timer.start()
            self.positions_timer.start()
            # Trigger initial load
            self._load_account_info()
            self._load_positions()

    def _stop_updates(self) -> None:
        """Stop periodic updates."""
        self.account_timer.stop()
        self.positions_timer.stop()

    def set_adapter(self, adapter: BitunixAdapter) -> None:
        """Set the Bitunix adapter.

        Args:
            adapter: Bitunix adapter instance
        """
        self.adapter = adapter
        self._update_button_states()
        self._start_updates()

    def set_symbol(self, symbol: str) -> None:
        """Set the current trading symbol.

        Args:
            symbol: Trading symbol (e.g. "BTCUSDT")
        """
        self._current_symbol = symbol
        self.symbol_label.setText(symbol)
        logger.info(f"Bitunix trading symbol set to: {symbol}")

    def _on_order_type_changed(self, order_type: str) -> None:
        """Handle order type change.

        Args:
            order_type: Selected order type ("Market" or "Limit")
        """
        is_limit = order_type == "Limit"
        self.price_spin.setEnabled(is_limit)

    def _update_button_states(self) -> None:
        """Update buy/sell button enabled states."""
        enabled = self.adapter is not None and self._current_symbol is not None
        self.buy_button.setEnabled(enabled)
        self.sell_button.setEnabled(enabled)

    @qasync.asyncSlot()
    async def _on_buy_clicked(self) -> None:
        """Handle BUY button click."""
        await self._place_order(OrderSide.BUY)

    @qasync.asyncSlot()
    async def _on_sell_clicked(self) -> None:
        """Handle SELL button click."""
        await self._place_order(OrderSide.SELL)

    @qasync.asyncSlot()
    async def _load_account_info(self) -> None:
        """Load and display account information."""
        if not self.adapter:
            return

        # Ensure connection is established
        if not self.adapter.connected:
            try:
                await self.adapter.connect()
            except Exception as e:
                # Stop timers on persistent auth failure to avoid UI stalls
                if "AUTH_FAILED" in str(e):
                    logger.error(f"Bitunix auth failed, stopping Bitunix timers: {e}")
                    self._stop_updates()
                else:
                    logger.error(f"Failed to connect to Bitunix: {e}")
                return

        try:
            balance = await self.adapter.get_balance()
            if balance:
                self.balance_label.setText(f"{balance.cash:.2f} USDT")
                self.margin_label.setText(f"{balance.margin_available:.2f} USDT")

                # Update PnL with color
                pnl_value = float(balance.daily_pnl)
                pnl_color = "#4CAF50" if pnl_value >= 0 else "#f44336"
                pnl_sign = "+" if pnl_value >= 0 else ""
                self.pnl_label.setText(f"{pnl_sign}{pnl_value:.2f} USDT")
                self.pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")

        except Exception as e:
            logger.error(f"Failed to load account info: {e}")

    @qasync.asyncSlot()
    async def _load_positions(self) -> None:
        """Load and display open positions."""
        if not self.adapter:
            return

        # Ensure connection is established
        if not self.adapter.connected:
            try:
                await self.adapter.connect()
            except Exception as e:
                if "AUTH_FAILED" in str(e):
                    logger.error(f"Bitunix auth failed, stopping Bitunix timers: {e}")
                    self._stop_updates()
                else:
                    logger.error(f"Failed to connect to Bitunix: {e}")
                return

        try:
            positions = await self.adapter.get_positions()
            self.positions_table.setRowCount(len(positions))

            for row, pos in enumerate(positions):
                self.positions_table.setItem(row, 0, QTableWidgetItem(pos.symbol))
                self.positions_table.setItem(row, 1, QTableWidgetItem(f"{pos.quantity:.4f}"))
                self.positions_table.setItem(row, 2, QTableWidgetItem(f"{pos.average_cost:.2f}"))
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"{pos.current_price:.2f}"))

                # PnL with color
                pnl_value = float(pos.unrealized_pnl)
                pnl_color = "#4CAF50" if pnl_value >= 0 else "#f44336"
                pnl_sign = "+" if pnl_value >= 0 else ""
                pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_value:.2f}")
                pnl_item.setForeground(Qt.GlobalColor.white)
                pnl_item.setBackground(Qt.GlobalColor.green if pnl_value >= 0 else Qt.GlobalColor.red)
                self.positions_table.setItem(row, 4, pnl_item)

        except Exception as e:
            logger.error(f"Failed to load positions: {e}")

    async def _place_order(self, side: OrderSide) -> None:
        """Place an order.

        Args:
            side: Order side (BUY or SELL)
        """
        if not self.adapter or not self._current_symbol:
            QMessageBox.warning(
                self,
                "Cannot Place Order",
                "No adapter or symbol selected."
            )
            return

        # Ensure connection is established
        if not self.adapter.connected:
            try:
                await self.adapter.connect()
            except Exception as e:
                logger.error(f"Failed to connect to Bitunix: {e}")
                QMessageBox.critical(
                    self,
                    "Connection Error",
                    f"Failed to connect to Bitunix:\n\n{str(e)}"
                )
                return

        try:
            # Build order request
            order_type = DBOrderType.MARKET if self.order_type_combo.currentText() == "Market" else DBOrderType.LIMIT
            quantity = Decimal(str(self.quantity_spin.value()))
            limit_price = Decimal(str(self.price_spin.value())) if order_type == DBOrderType.LIMIT else None

            order = OrderRequest(
                symbol=self._current_symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                limit_price=limit_price
            )

            # Confirm order
            side_text = "BUY" if side == OrderSide.BUY else "SELL"
            type_text = "Market" if order_type == DBOrderType.MARKET else f"Limit @ {limit_price}"
            confirm = QMessageBox.question(
                self,
                "Confirm Order",
                f"Place {side_text} order?\n\n"
                f"Symbol: {self._current_symbol}\n"
                f"Type: {type_text}\n"
                f"Quantity: {quantity}\n"
                f"Leverage: {self.leverage_spin.value()}x",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirm != QMessageBox.StandardButton.Yes:
                return

            # Place order
            response = await self.adapter.place_order(order)

            if response and response.broker_order_id:
                QMessageBox.information(
                    self,
                    "Order Placed",
                    f"Order placed successfully!\n\n"
                    f"Order ID: {response.broker_order_id}\n"
                    f"Status: {response.status.value}"
                )
                logger.info(f"Bitunix order placed: {response.broker_order_id}")

                # Refresh positions
                await self._load_positions()
            else:
                QMessageBox.warning(
                    self,
                    "Order Failed",
                    "Failed to place order. Check logs for details."
                )

        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            QMessageBox.critical(
                self,
                "Order Error",
                f"Error placing order:\n\n{str(e)}"
            )

    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self._stop_updates()
        super().closeEvent(event)
