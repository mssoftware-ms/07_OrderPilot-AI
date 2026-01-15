"""Bitunix Trading Widget - Main Orchestrator for Bitunix Futures Trading.

Refactored from 1,108 LOC monolith using composition pattern.

Module 4/4 (Main Orchestrator)

Provides order entry, position management, and account information for Bitunix.
Delegates to specialized helper modules:
- BitunixTradingUI: UI construction (account, order entry, positions sections)
- BitunixTradingModeManager: Live/Paper mode switching
- BitunixTradingOrderHandler: Order entry logic and execution
- BitunixTradingPositionsManager: Position loading and persistence

Public API:
- set_adapter(adapter): Set Bitunix adapter
- set_symbol(symbol): Set trading symbol
- set_history_manager(manager): Inject history manager
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QTabWidget,
)

from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter
from src.ui.widgets.bitunix_trading.bitunix_trading_ui import BitunixTradingUI
from src.ui.widgets.bitunix_trading.bitunix_trading_mode_manager import BitunixTradingModeManager
from src.ui.widgets.bitunix_trading.bitunix_trading_order_handler import BitunixTradingOrderHandler
from src.ui.widgets.bitunix_trading.bitunix_trading_positions_manager import BitunixTradingPositionsManager

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

    Architecture (Composition Pattern):
    - BitunixTradingUI: UI construction
    - BitunixTradingModeManager: Mode switching
    - BitunixTradingOrderHandler: Order logic
    - BitunixTradingPositionsManager: Position management
    - BitunixTradingWidget (this): Thin Orchestrator
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
        self.adapter = self.paper_adapter  # Default to Paper for safety
        self._current_symbol = None
        self.is_paper_mode = True

        # Instantiate helper modules (composition pattern)
        self.ui_manager = BitunixTradingUI(self)
        self._mode_manager = BitunixTradingModeManager(self)
        self._order_handler = BitunixTradingOrderHandler(self)
        self._positions_manager = BitunixTradingPositionsManager(self)

        self._setup_ui()
        self._setup_timers()
        self._mode_manager.update_mode_ui()  # Set initial visual state
        self._positions_manager.load_positions_from_file()  # Load saved positions on startup

        if self.adapter:
            self._start_updates()

    def set_history_manager(self, history_manager: HistoryManager):
        """Inject history manager into paper adapter for price feeds and bot data."""
        self._history_manager = history_manager

        # Use the new set_history_manager method if available, else direct assignment
        if hasattr(self.paper_adapter, "set_history_manager"):
            self.paper_adapter.set_history_manager(history_manager)
        else:
            self.paper_adapter.history_manager = history_manager

        # NOTE: bot_tab und backtest_tab wurden in das ChartWindow Trading Bot Panel verschoben
        # Die History-Manager-Verknüpfung erfolgt dort über panels_mixin.py

    def _setup_ui(self) -> None:
        """Set up the widget UI with tabs for manual trading."""
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
        self.mode_toggle.toggled.connect(self._mode_manager.toggle_mode)
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

        # Account info section (delegated to UI manager)
        manual_layout.addWidget(self.ui_manager.build_account_section())

        # Order entry section (delegated to UI manager)
        manual_layout.addWidget(self.ui_manager.build_order_entry_section())

        # Positions section (delegated to UI manager)
        manual_layout.addWidget(self.ui_manager.build_positions_section())

        manual_layout.addStretch()
        self.tab_widget.addTab(manual_tab, "📝 Manual Trading")

        # NOTE: Bot Trading und Backtesting Tabs wurden in das "Trading Bot" Panel
        # im ChartWindow verschoben (panels_mixin.py)

        main_layout.addWidget(self.tab_widget)
        self.setWidget(container)

    def _setup_timers(self) -> None:
        """Set up periodic update timers."""
        # Update account info every 10 seconds
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self._load_account_info)
        self.account_timer.setInterval(10000)

        # Update positions every 5 seconds
        self.positions_timer = QTimer()
        self.positions_timer.timeout.connect(self._load_positions)  # Use asyncSlot wrapper
        self.positions_timer.setInterval(5000)

    def _start_updates(self) -> None:
        """Start periodic updates."""
        if self.adapter:
            self.account_timer.start()
            self.positions_timer.start()
            # Trigger initial load (both are asyncSlot decorated)
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
        self._order_handler._update_button_states()
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
        self._order_handler._update_button_states()

    def _reset_paper_account(self) -> None:
        """Reset paper trading account.

        Delegates to BitunixTradingModeManager.reset_paper_account().
        """
        if hasattr(self, '_mode_manager') and self._mode_manager is not None:
            self._mode_manager.reset_paper_account()

    def _on_order_type_changed(self, order_type: str) -> None:
        """Handle order type change event.

        Delegates to BitunixTradingOrderHandler.on_order_type_changed().

        Args:
            order_type: Selected order type ("Market" or "Limit")
        """
        if hasattr(self, '_order_handler') and self._order_handler is not None:
            self._order_handler.on_order_type_changed(order_type)

    def _on_quantity_changed(self, value: float) -> None:
        """Handle quantity change event. Delegates to order handler."""
        if hasattr(self, '_order_handler') and self._order_handler is not None:
            self._order_handler.on_quantity_changed(value)

    def _on_price_changed(self, value: float) -> None:
        """Handle price change event. Delegates to order handler."""
        if hasattr(self, '_order_handler') and self._order_handler is not None:
            self._order_handler.on_price_changed(value)

    def _on_investment_changed(self, value: float) -> None:
        """Handle investment change event. Delegates to order handler."""
        if hasattr(self, '_order_handler') and self._order_handler is not None:
            self._order_handler.on_investment_changed(value)

    def _on_leverage_changed(self, value: int) -> None:
        """Handle leverage change event. Delegates to order handler."""
        if hasattr(self, '_order_handler') and self._order_handler is not None:
            self._order_handler.on_leverage_changed(value)

    @qasync.asyncSlot()
    async def _on_buy_clicked(self) -> None:
        """Handle buy button click. Delegates to order handler."""
        if hasattr(self, '_order_handler') and self._order_handler is not None:
            await self._order_handler.on_buy_clicked()

    @qasync.asyncSlot()
    async def _on_sell_clicked(self) -> None:
        """Handle sell button click. Delegates to order handler."""
        if hasattr(self, '_order_handler') and self._order_handler is not None:
            await self._order_handler.on_sell_clicked()

    @qasync.asyncSlot()
    async def _load_positions(self) -> None:
        """Load positions. Delegates to positions manager."""
        if hasattr(self, '_positions_manager') and self._positions_manager is not None:
            await self._positions_manager._load_positions()

    def _delete_selected_row(self) -> None:
        """Delete selected position row. Delegates to positions manager."""
        if hasattr(self, '_positions_manager') and self._positions_manager is not None:
            self._positions_manager.delete_selected_row()

    def _on_tick_price_updated(self, price: float) -> None:
        """Handle real-time tick price update from chart. Delegates to positions manager."""
        if hasattr(self, '_positions_manager') and self._positions_manager is not None:
            self._positions_manager.on_tick_price_updated(price)

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

    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self._positions_manager.save_positions_to_file()  # Save positions before closing
        self._stop_updates()
        super().closeEvent(event)


# Re-export für backward compatibility
__all__ = ["BitunixTradingWidget"]
