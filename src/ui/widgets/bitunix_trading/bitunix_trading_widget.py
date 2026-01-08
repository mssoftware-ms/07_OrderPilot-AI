"""Bitunix Trading Widget - Dockable trading panel for Bitunix Futures.

Provides order entry, position management, and account information for Bitunix.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
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
    QDoubleSpinBox,
    QSlider,
    QMessageBox,
    QHeaderView,
    QCheckBox,
    QFrame,
    QTabWidget,
)

from src.core.broker.broker_types import OrderRequest, OrderSide
from src.database.models import OrderType as DBOrderType
from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter

if TYPE_CHECKING:
    from src.core.broker.bitunix_adapter import BitunixAdapter
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)


class BitunixTradingWidget(QDockWidget):
    """Dockable trading widget for Bitunix Futures.

    Features:
        - Order entry panel (Market/Limit, Buy/Sell)
        - Position management table
        - Account info display (Balance, Margin, PnL)
        - Live / Paper Trading Switch
    """

    def __init__(self, adapter: BitunixAdapter | None = None, parent=None):
        """Initialize Bitunix trading widget.

        Args:
            adapter: Bitunix adapter instance (optional)
            parent: Parent widget
        """
        super().__init__("💱 Bitunix Trading", parent)
        self.setObjectName("bitunixTradingDock")

        self.live_adapter = adapter
        self.paper_adapter = BitunixPaperAdapter()
        self.adapter = self.paper_adapter # Default to Paper for safety
        self._current_symbol = None
        self.is_paper_mode = True

        self._setup_ui()
        self._setup_timers()
        self._update_mode_ui() # Set initial visual state
        self._load_positions_from_file() # Load saved positions on startup

        if self.adapter:
            self._start_updates()

    def set_history_manager(self, history_manager: HistoryManager):
        """Inject history manager into paper adapter for price feeds and bot data."""
        self._history_manager = history_manager

        # Use the new set_history_manager method if available, else direct assignment
        if hasattr(self.paper_adapter, 'set_history_manager'):
            self.paper_adapter.set_history_manager(history_manager)
        else:
            self.paper_adapter.history_manager = history_manager

        # NOTE: bot_tab und backtest_tab wurden in das ChartWindow Trading Bot Panel verschoben
        # Die History-Manager-Verknüpfung erfolgt dort über panels_mixin.py

        # Legacy: Backtest tab if it still exists locally
        if hasattr(self, 'backtest_tab') and self.backtest_tab is not None:
            self.backtest_tab.set_history_manager(history_manager)

    def _setup_ui(self) -> None:
        """Set up the widget UI with tabs for manual and bot trading."""
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(380)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # --- Mode Switch & Banner (above tabs) ---
        mode_layout = QHBoxLayout()

        self.mode_toggle = QCheckBox("Paper Trading Mode")
        self.mode_toggle.setChecked(True)
        self.mode_toggle.toggled.connect(self._toggle_mode)
        self.mode_toggle.setStyleSheet("""
            QCheckBox { font-weight: bold; font-size: 14px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
        mode_layout.addWidget(self.mode_toggle)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        self.mode_banner = QLabel("PAPER TRADING - SIMULATION")
        self.mode_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_banner.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
        """)
        main_layout.addWidget(self.mode_banner)

        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #888;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a2e;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #333;
            }
        """)

        # Tab 0: Manual Trading
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        manual_layout.setContentsMargins(4, 8, 4, 4)
        manual_layout.setSpacing(10)

        # Account info section
        manual_layout.addWidget(self._build_account_section())

        # Order entry section
        manual_layout.addWidget(self._build_order_entry_section())

        # Positions section
        manual_layout.addWidget(self._build_positions_section())

        manual_layout.addStretch()
        self.tab_widget.addTab(manual_tab, "📝 Manual Trading")

        # NOTE: Bot Trading und Backtesting Tabs wurden in das "Trading Bot" Panel
        # im ChartWindow verschoben (panels_mixin.py)
        # Die folgenden Calls wurden entfernt:
        # - self._setup_bot_tab()
        # - self._setup_backtest_tab()

        main_layout.addWidget(self.tab_widget)
        self.setWidget(container)

    def _setup_bot_tab(self) -> None:
        """Set up the bot trading tab."""
        try:
            from .bot_tab import BotTab

            self.bot_tab = BotTab(
                paper_adapter=self.paper_adapter,
                history_manager=getattr(self, '_history_manager', None),
                parent=self,
            )
            self.tab_widget.addTab(self.bot_tab, "🤖 Trading Bot")
        except ImportError as e:
            # Fallback: Placeholder wenn BotTab nicht verfügbar
            logger.warning(f"BotTab konnte nicht geladen werden: {e}")
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            label = QLabel("🤖 Auto Trading Bot\n\nKommt bald...")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(label)
            self.tab_widget.addTab(placeholder, "🤖 Auto Trading")
            self.bot_tab = None

    def _setup_backtest_tab(self) -> None:
        """Set up the backtesting tab."""
        try:
            from .backtest_tab import BacktestTab

            self.backtest_tab = BacktestTab(
                history_manager=getattr(self, '_history_manager', None),
                parent=self,
            )
            self.tab_widget.addTab(self.backtest_tab, "🧪 Backtesting")
        except ImportError as e:
            # Fallback: Placeholder wenn BacktestTab nicht verfügbar
            logger.warning(f"BacktestTab konnte nicht geladen werden: {e}")
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            label = QLabel("🧪 Backtesting\n\nKommt bald...")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(label)
            self.tab_widget.addTab(placeholder, "🧪 Backtesting")
            self.backtest_tab = None

    def _toggle_mode(self, is_paper: bool):
        """Switch between Live and Paper adapters."""
        self.is_paper_mode = is_paper

        if is_paper:
            self.adapter = self.paper_adapter
        else:
            self.adapter = self.live_adapter

        self._update_mode_ui()

        # Trigger immediate refresh
        self._load_account_info()
        self._load_positions()
        self._update_button_states()

    def _update_mode_ui(self):
        """Update banner and colors based on mode."""
        if self.is_paper_mode:
            self.mode_banner.setText("PAPER TRADING - SIMULATION")
            self.mode_banner.setStyleSheet("""
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                padding: 8px; 
                border-radius: 4px;
            """)
            self.reset_btn.setVisible(True)
        else:
            self.mode_banner.setText("⚠️ LIVE TRADING - REAL MONEY ⚠️")
            self.mode_banner.setStyleSheet("""
                background-color: #D32F2F; 
                color: white; 
                font-weight: bold; 
                padding: 8px; 
                border-radius: 4px;
            """)
            self.reset_btn.setVisible(False)

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
        
        # Reset Button (Paper only)
        self.reset_btn = QPushButton("🔄 Reset Paper Account")
        self.reset_btn.clicked.connect(self._reset_paper_account)
        self.reset_btn.setStyleSheet("background-color: #555; color: #aaa; font-size: 10px; margin-top: 5px;")
        layout.addWidget(self.reset_btn)

        return group

    def _reset_paper_account(self):
        """Reset paper trading balance."""
        if not self.is_paper_mode:
            return
            
        confirm = QMessageBox.question(
            self, "Reset Simulation", 
            "Reset paper balance to 10,000 USDT?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.paper_adapter.reset_account()
            self._load_account_info()
            self._load_positions()

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
        self.quantity_spin.valueChanged.connect(self._on_quantity_changed)
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
        self.price_spin.valueChanged.connect(self._on_price_changed)
        price_layout.addWidget(self.price_spin)
        layout.addLayout(price_layout)

        # Investment Amount (USDT) - NEW FIELD
        investment_layout = QHBoxLayout()
        investment_layout.addWidget(QLabel("Investment (USDT):"))
        self.investment_spin = QDoubleSpinBox()
        self.investment_spin.setRange(0, 1000000)
        self.investment_spin.setDecimals(2)
        self.investment_spin.setValue(100.0)  # Default $100
        self.investment_spin.setSingleStep(10.0)
        self.investment_spin.setMinimumWidth(150)
        self.investment_spin.valueChanged.connect(self._on_investment_changed)
        investment_layout.addWidget(self.investment_spin)
        layout.addLayout(investment_layout)

        # Leverage
        leverage_layout = QHBoxLayout()
        leverage_layout.addWidget(QLabel("Leverage:"))
        self.leverage_slider = QSlider(Qt.Orientation.Horizontal)
        self.leverage_slider.setMinimum(0)
        self.leverage_slider.setMaximum(100)
        self.leverage_slider.setValue(5)
        self.leverage_slider.setTickInterval(5)
        self.leverage_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.leverage_slider.valueChanged.connect(self._on_leverage_changed)
        leverage_layout.addWidget(self.leverage_slider)
        self.leverage_value = QLabel("5x")
        self.leverage_value.setMinimumWidth(40)
        leverage_layout.addWidget(self.leverage_value)
        layout.addLayout(leverage_layout)

        # Stop Loss
        stop_layout = QHBoxLayout()
        stop_layout.addWidget(QLabel("Stop Loss:"))
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setDecimals(2)
        self.stop_loss_spin.setMinimum(0)
        self.stop_loss_spin.setMaximum(1_000_000)
        self.stop_loss_spin.setValue(0)
        self.stop_loss_spin.setToolTip("0 = kein Stop Loss. Preis in USDT.")
        stop_layout.addWidget(self.stop_loss_spin)
        layout.addLayout(stop_layout)

        # Take Profit
        tp_layout = QHBoxLayout()
        tp_layout.addWidget(QLabel("Take Profit:"))
        self.take_profit_spin = QDoubleSpinBox()
        self.take_profit_spin.setDecimals(2)
        self.take_profit_spin.setMinimum(0)
        self.take_profit_spin.setMaximum(1_000_000)
        self.take_profit_spin.setValue(0)
        self.take_profit_spin.setToolTip("0 = kein Take Profit. Preis in USDT.")
        tp_layout.addWidget(self.take_profit_spin)
        layout.addLayout(tp_layout)

        # Position Direction Selector (Long/Short)
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Position Direction:"))
        self.position_direction_combo = QComboBox()
        self.position_direction_combo.addItems(["🔵 LONG", "🔴 SHORT"])
        self.position_direction_combo.setStyleSheet("""
            QComboBox {
                font-weight: bold;
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 3px;
                background-color: #2a2a2a;
                min-width: 100px;
            }
            QComboBox:focus { border: 1px solid #4CAF50; }
        """)
        self.position_direction_combo.currentIndexChanged.connect(self._on_direction_changed)
        direction_layout.addWidget(self.position_direction_combo)
        direction_layout.addStretch()
        layout.addLayout(direction_layout)

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

    def _on_direction_changed(self, index: int) -> None:
        """Handle position direction change.

        Args:
            index: 0 = LONG, 1 = SHORT

        Position Direction bestimmt die Wettrichtung:
        - LONG = Wette auf steigende Kurse
        - SHORT = Wette auf fallende Kurse

        BUY/SELL sind die Aktionen:
        - BUY = Position kaufen/eröffnen (in gewählter Richtung)
        - SELL = Position verkaufen/schließen
        """
        direction = "LONG" if index == 0 else "SHORT"
        logger.debug(f"Position direction changed to: {direction}")

    def get_selected_direction(self) -> str:
        """Returns the selected position direction.

        Returns:
            'LONG' or 'SHORT'
        """
        return "LONG" if self.position_direction_combo.currentIndex() == 0 else "SHORT"

    def _build_positions_section(self) -> QGroupBox:
        """Build positions table.

        Returns:
            Positions group box
        """
        group = QGroupBox("Open Positions")
        layout = QVBoxLayout(group)

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(7)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Direction", "Qty", "Entry", "Current", "Leverage", "PnL"
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
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.positions_table)

        # Buttons: Refresh and Delete
        buttons_layout = QHBoxLayout()

        refresh_button = QPushButton("🔄 Refresh Positions")
        refresh_button.clicked.connect(self._load_positions)
        buttons_layout.addWidget(refresh_button)

        delete_button = QPushButton("🗑️ Delete Row")
        delete_button.clicked.connect(self._delete_selected_row)
        delete_button.setStyleSheet("background-color: #d32f2f; color: white;")
        buttons_layout.addWidget(delete_button)

        layout.addLayout(buttons_layout)

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
        # Enable order buttons as soon as we have a symbol
        self._update_button_states()

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

    def _on_investment_changed(self, value: float) -> None:
        """When investment amount changes, calculate quantity.

        Args:
            value: Investment amount in USDT
        """
        if value <= 0:
            return

        price = self._get_current_price()

        if price <= 0:
            # Show warning if no price available
            if value > 0:  # Only warn if user actually entered an amount
                QMessageBox.warning(
                    self,
                    "Keine Kurs-Daten",
                    f"Kurs für {self._current_symbol or 'Symbol'} nicht verfügbar.\n\n"
                    "Bitte:\n"
                    "• Öffnen Sie einen Chart mit dem Symbol, oder\n"
                    "• Wählen Sie 'Limit' Order und geben Sie einen Preis ein"
                )
            return

        # Calculate quantity = investment / price
        quantity = value / price
        self.quantity_spin.blockSignals(True)
        self.quantity_spin.setValue(quantity)
        self.quantity_spin.blockSignals(False)

    def _on_quantity_changed(self, value: float) -> None:
        """When quantity changes, calculate investment amount.

        Args:
            value: Quantity amount
        """
        if value <= 0:
            return

        price = self._get_current_price()

        if price <= 0:
            return  # Silent for quantity changes (price will be shown when investment entered)

        # Calculate investment = quantity * price
        investment = value * price
        self.investment_spin.blockSignals(True)
        self.investment_spin.setValue(investment)
        self.investment_spin.blockSignals(False)

    def _on_price_changed(self, value: float) -> None:
        """When price changes, recalculate investment from quantity.

        Args:
            value: Price value
        """
        if value > 0:
            self._on_quantity_changed(self.quantity_spin.value())

    def _get_current_price(self) -> float:
        """Get current market price with 4-tier fallback strategy.

        Returns:
            float: Current price or 0.0 if unavailable
        """
        # Tier 1: Limit price (explicit user input)
        if self.order_type_combo.currentText() == "Limit":
            limit_price = self.price_spin.value()
            if limit_price > 0:
                return limit_price

        # Tier 2: Live chart price (streaming)
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'chart_widget'):
                chart = parent.chart_widget

                # Try to get real-time streaming price
                if hasattr(chart, '_last_price'):
                    last_price = getattr(chart, '_last_price', 0)
                    if last_price > 0:
                        return last_price

                # Tier 3: Historical close price
                if hasattr(chart, 'data') and chart.data is not None and not chart.data.empty:
                    try:
                        last_close = float(chart.data['close'].iloc[-1])
                        if last_close > 0:
                            return last_close
                    except (IndexError, KeyError, TypeError, ValueError):
                        pass
        except Exception as e:
            logger.warning(f"Error getting chart price: {e}")

        # Tier 4: No price available - warn user
        if self._current_symbol:
            logger.warning(f"No price data available for {self._current_symbol}")

        return 0.0

    def _current_leverage(self) -> int:
        """Return leverage value from slider (treat 0 as 1 for safety)."""
        val = int(self.leverage_slider.value()) if hasattr(self, "leverage_slider") else 1
        return max(val, 1)

    def _on_leverage_changed(self, value: int) -> None:
        """Update leverage label when slider moves."""
        if hasattr(self, "leverage_value"):
            self.leverage_value.setText(f"{value}x")

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
                # Symbol (Column 0)
                self.positions_table.setItem(row, 0, QTableWidgetItem(pos.symbol))

                # Direction (Column 1)
                direction_text = "🔵 LONG" if pos.is_long else "🔴 SHORT"
                direction_color = "#4CAF50" if pos.is_long else "#f44336"
                direction_item = QTableWidgetItem(direction_text)
                direction_item.setForeground(QColor(direction_color))
                self.positions_table.setItem(row, 1, direction_item)

                # Quantity (Column 2)
                self.positions_table.setItem(row, 2, QTableWidgetItem(f"{pos.quantity:.4f}"))

                # Entry Price (Column 3)
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"{pos.average_cost:.2f}"))

                # Current Price (Column 4)
                self.positions_table.setItem(row, 4, QTableWidgetItem(f"{pos.current_price:.2f}"))

                # Leverage (Column 5)
                self.positions_table.setItem(row, 5, QTableWidgetItem(f"{pos.leverage}x"))

                # PnL with color (Column 6)
                pnl_value = float(pos.unrealized_pnl)
                pnl_color = "#4CAF50" if pnl_value >= 0 else "#f44336"
                pnl_sign = "+" if pnl_value >= 0 else ""
                pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_value:.2f}")
                pnl_item.setForeground(Qt.GlobalColor.white)
                pnl_item.setBackground(Qt.GlobalColor.green if pnl_value >= 0 else Qt.GlobalColor.red)
                self.positions_table.setItem(row, 6, pnl_item)

        except Exception as e:
            logger.error(f"Failed to load positions: {e}")

    def _on_tick_price_updated(self, price: float) -> None:
        """Update current price in positions table in real-time.

        Connected to chart's tick_price_updated signal for live updates.

        Args:
            price: Current market price from streaming ticker
        """
        if not self._current_symbol:
            return

        # Update all rows where symbol matches current symbol
        for row in range(self.positions_table.rowCount()):
            symbol_item = self.positions_table.item(row, 0)
            if symbol_item and symbol_item.text() == self._current_symbol:
                # Update Current price (Column 4 - shifted by 1 due to Direction column)
                self.positions_table.setItem(
                    row, 4,
                    QTableWidgetItem(f"{price:.2f}")
                )

                # Recalculate PnL (Column 6 - shifted by 2 due to Direction and Leverage columns)
                try:
                    entry_price = float(self.positions_table.item(row, 3).text())
                    quantity = float(self.positions_table.item(row, 2).text())
                    leverage_text = self.positions_table.item(row, 5).text() if self.positions_table.item(row, 5) else "1x"
                    leverage = float(leverage_text.rstrip('x'))

                    pnl_value = (price - entry_price) * quantity * leverage
                    pnl_color = "#4CAF50" if pnl_value >= 0 else "#f44336"
                    pnl_sign = "+" if pnl_value >= 0 else ""

                    pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_value:.2f}")
                    pnl_item.setForeground(QColor(pnl_color))

                    self.positions_table.setItem(row, 6, pnl_item)
                except (ValueError, AttributeError, TypeError):
                    pass  # Silently ignore calculation errors

        # NOTE: bot_tab wurde in das ChartWindow Trading Bot Panel verschoben
        # Tick-Price-Updates erfolgen dort über das ChartWindow

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
            stop_loss_val = Decimal(str(self.stop_loss_spin.value()))
            stop_loss = stop_loss_val if stop_loss_val > 0 else None
            take_profit_val = Decimal(str(self.take_profit_spin.value()))
            take_profit = take_profit_val if take_profit_val > 0 else None
            leverage_val = self._current_leverage()
            position_direction = self.get_selected_direction()  # LONG oder SHORT

            order = OrderRequest(
                symbol=self._current_symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                limit_price=limit_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                notes=f"leverage={leverage_val}x,direction={position_direction}"
            )

            # Confirm order
            side_text = "BUY" if side == OrderSide.BUY else "SELL"
            direction_emoji = "🔵" if position_direction == "LONG" else "🔴"
            type_text = "Market" if order_type == DBOrderType.MARKET else f"Limit @ {limit_price}"
            stop_text = f"{stop_loss} (price)" if stop_loss else "—"
            tp_text = f"{take_profit} (price)" if take_profit else "—"
            confirm = QMessageBox.question(
                self,
                "Confirm Order",
                f"Place {side_text} order?\n\n"
                f"Symbol: {self._current_symbol}\n"
                f"Direction: {direction_emoji} {position_direction}\n"
                f"Type: {type_text}\n"
                f"Quantity: {quantity}\n"
                f"Leverage: {leverage_val}x\n"
                f"Stop Loss: {stop_text}\n"
                f"Take Profit: {tp_text}",
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
                    f"Status: {response.status}"
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

    def _save_positions_to_file(self) -> None:
        """Save current positions table to JSON file."""
        try:
            # Create data directory if not exists
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)

            positions_file = data_dir / "bitunix_positions.json"

            # Extract table data
            positions_data = []
            for row in range(self.positions_table.rowCount()):
                row_data = {}
                # Column 0: Symbol
                symbol_item = self.positions_table.item(row, 0)
                row_data["symbol"] = symbol_item.text() if symbol_item else ""

                # Column 1: Direction
                direction_item = self.positions_table.item(row, 1)
                row_data["direction"] = direction_item.text() if direction_item else ""

                # Column 2: Quantity
                qty_item = self.positions_table.item(row, 2)
                row_data["quantity"] = qty_item.text() if qty_item else "0"

                # Column 3: Entry Price
                entry_item = self.positions_table.item(row, 3)
                row_data["entry_price"] = entry_item.text() if entry_item else "0"

                # Column 4: Current Price
                current_item = self.positions_table.item(row, 4)
                row_data["current_price"] = current_item.text() if current_item else "0"

                # Column 5: Leverage
                leverage_item = self.positions_table.item(row, 5)
                row_data["leverage"] = leverage_item.text() if leverage_item else "1x"

                # Column 6: PnL
                pnl_item = self.positions_table.item(row, 6)
                row_data["pnl"] = pnl_item.text() if pnl_item else "0"

                positions_data.append(row_data)

            # Save to JSON
            with open(positions_file, 'w', encoding='utf-8') as f:
                json.dump(positions_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(positions_data)} positions to {positions_file}")

        except Exception as e:
            logger.error(f"Failed to save positions: {e}")

    def _load_positions_from_file(self) -> None:
        """Load positions from JSON file into table."""
        try:
            positions_file = Path("data/bitunix_positions.json")

            if not positions_file.exists():
                logger.debug("No saved positions file found")
                return

            # Load from JSON
            with open(positions_file, 'r', encoding='utf-8') as f:
                positions_data = json.load(f)

            if not positions_data:
                return

            # Populate table
            self.positions_table.setRowCount(len(positions_data))

            for row, data in enumerate(positions_data):
                # Symbol (Column 0)
                self.positions_table.setItem(row, 0, QTableWidgetItem(data.get("symbol", "")))

                # Direction (Column 1)
                direction_text = data.get("direction", "")
                direction_item = QTableWidgetItem(direction_text)
                if "LONG" in direction_text:
                    direction_item.setForeground(QColor("#4CAF50"))
                elif "SHORT" in direction_text:
                    direction_item.setForeground(QColor("#f44336"))
                self.positions_table.setItem(row, 1, direction_item)

                # Quantity (Column 2)
                self.positions_table.setItem(row, 2, QTableWidgetItem(data.get("quantity", "0")))

                # Entry Price (Column 3)
                self.positions_table.setItem(row, 3, QTableWidgetItem(data.get("entry_price", "0")))

                # Current Price (Column 4)
                self.positions_table.setItem(row, 4, QTableWidgetItem(data.get("current_price", "0")))

                # Leverage (Column 5)
                self.positions_table.setItem(row, 5, QTableWidgetItem(data.get("leverage", "1x")))

                # PnL (Column 6)
                pnl_text = data.get("pnl", "0")
                pnl_item = QTableWidgetItem(pnl_text)
                # Parse PnL value for color
                try:
                    pnl_value = float(pnl_text.replace("+", "").replace(",", ""))
                    if pnl_value >= 0:
                        pnl_item.setForeground(Qt.GlobalColor.white)
                        pnl_item.setBackground(Qt.GlobalColor.green)
                    else:
                        pnl_item.setForeground(Qt.GlobalColor.white)
                        pnl_item.setBackground(Qt.GlobalColor.red)
                except:
                    pass
                self.positions_table.setItem(row, 6, pnl_item)

            logger.info(f"Loaded {len(positions_data)} positions from {positions_file}")

        except Exception as e:
            logger.error(f"Failed to load positions: {e}")

    def _delete_selected_row(self) -> None:
        """Delete the selected row from positions table."""
        current_row = self.positions_table.currentRow()

        if current_row < 0:
            QMessageBox.warning(
                self,
                "Keine Auswahl",
                "Bitte wählen Sie eine Zeile zum Löschen aus."
            )
            return

        # Get symbol for confirmation
        symbol_item = self.positions_table.item(current_row, 0)
        symbol = symbol_item.text() if symbol_item else "Unknown"

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Position löschen",
            f"Position für {symbol} wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.positions_table.removeRow(current_row)
            self._save_positions_to_file()  # Auto-save after deletion
            logger.info(f"Deleted position row {current_row} ({symbol})")

    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self._save_positions_to_file()  # Save positions before closing
        self._stop_updates()
        super().closeEvent(event)
