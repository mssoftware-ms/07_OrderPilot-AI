"""Bot Signals Entry Mixin - Entry signal handling and order placement.

This module handles:
- Main signals tab creation (_create_signals_tab)
- Bitunix Trading API widget integration
- Order entry event handling
- Real-time price updates
- Compact chart synchronization
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSplitter, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class BotSignalsEntryMixin:
    """Mixin for entry signal handling and order placement.

    This mixin provides:
    - Main signals tab creation with layout
    - Bitunix Trading API widget (order entry)
    - API event handlers (order placed, price needed)
    - Price retrieval with 3-tier fallback
    - Real-time price updates in signals table
    - Compact chart synchronization
    """

    # ==========================================
    # Main Tab Creation
    # ==========================================

    def _create_signals_tab(self) -> QWidget:
        """Create signals & trade management tab.

        Layout structure:
        1. Top row (horizontal):
           - Bitunix Trading API Widget (left, stretch=1)
           - Compact Chart Widget (center, stretch=0) - Issue #9
           - Current Position Widget (right, fixed 420px width)
        2. Vertical splitter:
           - Signals table (top, 70% space)
           - Bot log (bottom, 30% space)

        Returns:
            QWidget: Complete signals tab with all components
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Top row: Bitunix Trading API + Compact Chart + Current Position
        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(8)

        # Bitunix Trading API Widget (left side, takes most space)
        trading_api_widget = self._build_bitunix_trading_api_widget()
        trading_api_container = QWidget()
        trading_api_container_layout = QVBoxLayout(trading_api_container)
        trading_api_container_layout.setContentsMargins(0, 0, 0, 0)
        trading_api_container_layout.setSpacing(0)
        trading_api_container_layout.addWidget(trading_api_widget)
        top_row_layout.addWidget(trading_api_container, stretch=1)

        # Issue #9: Compact Chart Widget BETWEEN the two GroupBoxes (horizontal)
        try:
            from src.ui.widgets.compact_chart_widget import CompactChartWidget
            self.compact_chart_widget = CompactChartWidget(parent_chart=self)
            self.compact_chart_widget.setVisible(True)  # Explicitly show widget
            self.compact_chart_widget.show()  # Force show
            top_row_layout.addWidget(self.compact_chart_widget, stretch=0)

            # Update symbol if available
            if hasattr(self, 'symbol'):
                self.compact_chart_widget.update_symbol(self.symbol)

            logger.info(f"Issue #9: Compact Chart Widget created (size: {self.compact_chart_widget.size().width()}x{self.compact_chart_widget.size().height()})")
            logger.info(f"Issue #9: Widget visible: {self.compact_chart_widget.isVisible()}, shown: {not self.compact_chart_widget.isHidden()}")
        except Exception as e:
            logger.error(f"Issue #9: Failed to create compact chart widget: {e}", exc_info=True)

        # Current Position (right side, fixed 420px width)
        position_widget = self._build_current_position_widget()
        position_widget.setMaximumWidth(420)
        position_widget.setMinimumWidth(420)
        top_row_layout.addWidget(position_widget, stretch=0)

        layout.addLayout(top_row_layout)

        # 10px spacing before Recent Signals
        layout.addSpacing(10)

        # Issue #68: Use QSplitter for Signals Table and Bot Log
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._build_signals_widget())
        splitter.addWidget(self._build_bot_log_widget())
        splitter.setStretchFactor(0, 7)  # Signals table gets more space
        splitter.setStretchFactor(1, 3)  # Log gets less

        layout.addWidget(splitter)

        return widget

    # ==========================================
    # Bitunix Trading API Widget
    # ==========================================

    def _build_bitunix_trading_api_widget(self) -> QWidget:
        """Build Bitunix Trading API Widget.

        Compact order entry interface for quick trading.
        Placed left of the HEDGE widget.

        Returns:
            QWidget: BitunixTradingAPIWidget or error placeholder

        Wire-up:
        - order_placed signal → _on_bitunix_api_order_placed
        - price_needed signal → _on_bitunix_api_price_needed
        """
        from src.ui.widgets.bitunix_trading_api_widget import BitunixTradingAPIWidget

        try:
            self.bitunix_trading_api_widget = BitunixTradingAPIWidget(parent=self)

            # Wire up signals
            self.bitunix_trading_api_widget.order_placed.connect(self._on_bitunix_api_order_placed)
            self.bitunix_trading_api_widget.price_needed.connect(self._on_bitunix_api_price_needed)

            # If adapter is already available, set it
            if hasattr(self, '_bitunix_adapter') and self._bitunix_adapter:
                self.bitunix_trading_api_widget.set_adapter(self._bitunix_adapter)

            return self.bitunix_trading_api_widget

        except Exception as e:
            logger.error(f"Failed to create Bitunix Trading API widget: {e}", exc_info=True)
            # Return placeholder on error
            error_widget = QLabel(f"Bitunix Trading API: Init failed - {e}")
            error_widget.setStyleSheet("color: #ff5555; padding: 8px;")
            return error_widget

    def _on_bitunix_api_order_placed(self, order_id: str):
        """Handle Bitunix Trading API order placed event.

        Args:
            order_id: Order ID from Bitunix API
        """
        logger.info(f"Bitunix API order placed: {order_id}")

    def _on_bitunix_api_price_needed(self, symbol: str):
        """Handle price request from Trading API widget.

        Args:
            symbol: Symbol to fetch price for
        """
        if hasattr(self, 'bitunix_trading_api_widget'):
            price = self._get_current_price_for_symbol(symbol)
            self.bitunix_trading_api_widget.set_price(price)

    # ==========================================
    # Price Retrieval (3-Tier Fallback)
    # ==========================================

    def _get_current_price_for_symbol(self, symbol: str) -> float:
        """Get current price for a symbol using 3-tier fallback.

        Tier 1: Chart tick data (_last_tick_price)
        Tier 2: Chart footer label (chart_widget.info_label)
        Tier 3: History manager (get_data)

        Args:
            symbol: Symbol to fetch price for

        Returns:
            float: Current price (0.0 if all tiers fail)
        """
        # Tier 1: Chart tick data
        if hasattr(self, 'current_symbol') and self.current_symbol == symbol:
            if hasattr(self, '_last_tick_price') and self._last_tick_price > 0:
                return self._last_tick_price

        # Tier 2: Chart footer label
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'info_label'):
            try:
                label_text = self.chart_widget.info_label.text()
                if label_text and "Last:" in label_text:
                    price_text = label_text.split("Last:")[-1].strip().lstrip("$").replace(",", "")
                    price = float(price_text)
                    if price > 0:
                        return price
            except Exception:
                pass

        # Tier 3: History manager
        if hasattr(self, '_history_manager') and self._history_manager:
            try:
                df = self._history_manager.get_data(symbol)
                if df is not None and not df.empty and 'close' in df.columns:
                    return float(df['close'].iloc[-1])
            except Exception:
                pass

        return 0.0

    # ==========================================
    # Real-Time Price Updates
    # ==========================================

    def _update_current_price_in_signals(self, price: float):
        """Update current price in Recent Signals table for ENTERED positions.

        Updates column 11 (Current) for all rows where column 10 (Status) is "ENTERED".
        Also updates compact chart widget if available.

        Args:
            price: Current market price

        Issue #2: Fixed column indices - Status is column 10, Current is column 11.
        Issue #9: Also updates compact chart widget.
        """
        if not hasattr(self, 'signals_table'):
            return

        try:
            for row in range(self.signals_table.rowCount()):
                # Issue #2: Status is column 10 (not 5)
                status_item = self.signals_table.item(row, 10)
                if status_item and status_item.text().upper() == "ENTERED":
                    # Issue #2: Current column is 11 (not 6)
                    current_item = self.signals_table.item(row, 11)
                    if current_item:
                        current_item.setText(f"{price:.2f}")

            # Issue #9: Update compact chart widget
            if hasattr(self, 'compact_chart_widget') and price > 0:
                self.compact_chart_widget.update_price(price)

        except Exception as e:
            logger.debug(f"Failed to update current price in signals table: {e}")

    # ==========================================
    # Compact Chart Synchronization
    # ==========================================

    def _update_compact_chart_from_main(self) -> None:
        """Sync compact chart with main chart data (dynamic timeframe).

        Copies data from main chart_widget to compact_chart_widget:
        - Chart data (OHLCV dataframe)
        - Current symbol

        If chart data is empty, clears the compact chart.
        """
        if not hasattr(self, 'compact_chart_widget'):
            return

        chart_widget = getattr(self, "chart_widget", None)
        if not chart_widget:
            return

        chart_data = getattr(chart_widget, "data", None)
        if chart_data is None or chart_data.empty:
            self.compact_chart_widget.clear_data()
            return

        symbol = getattr(chart_widget, "current_symbol", None) or getattr(self, "symbol", None)
        if symbol:
            self.compact_chart_widget.update_symbol(symbol)

        self.compact_chart_widget.update_chart_data(chart_data)
