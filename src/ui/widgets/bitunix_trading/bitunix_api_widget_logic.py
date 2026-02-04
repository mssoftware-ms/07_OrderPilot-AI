"""Bitunix Trading API Widget - API Logic Module.

This module contains API integration logic, order placement, and adapter management
for the BitunixTradingAPIWidget. Separated from UI and events for maintainability.

Components:
    - Order placement logic
    - Adapter connection/disconnection
    - Public API methods (set_adapter, set_symbol, set_price)
    - Price update notifications
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from PyQt6.QtWidgets import QMessageBox
import qasync

from src.core.broker.broker_types import OrderRequest, OrderSide
from src.database.models import OrderType as DBOrderType

logger = logging.getLogger(__name__)


class BitunixAPIWidgetLogic:
    """Mixin providing API logic for BitunixTradingAPIWidget."""

    # ========================================================================
    # ORDER PLACEMENT
    # ========================================================================

    async def _place_order(self, side: OrderSide):
        """Place order with current settings.

        In mirror mode, delegates to state manager for coordinated execution.
        In master/standalone mode, executes directly via adapter.

        Args:
            side: OrderSide.BUY or OrderSide.SELL
        """
        # Check if we should delegate to state manager (mirror mode)
        if getattr(self, '_is_mirror', False) and hasattr(self, '_state_manager') and self._state_manager:
            await self._place_order_via_state_manager(side)
            return

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

    # ========================================================================
    # PUBLIC API METHODS
    # ========================================================================

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

            # Update Recent Signals table & Current Position
            if hasattr(self.parent(), '_update_current_price_in_signals'):
                self.parent()._update_current_price_in_signals(price)
            if hasattr(self.parent(), '_update_current_price_in_position'):
                self.parent()._update_current_price_in_position(price)

    # ========================================================================
    # ADAPTER CONNECTION/DISCONNECTION
    # ========================================================================

    @qasync.asyncSlot()
    async def _connect_adapter_for_live_mode(self) -> None:
        """Ensure adapter is connected when live mode is enabled."""
        if not self._adapter:
            parent = self.parent_widget or self.parent()
            if parent is not None and hasattr(parent, "_bitunix_adapter"):
                self._adapter = getattr(parent, "_bitunix_adapter")
            if not self._adapter:
                QMessageBox.warning(self, "No Adapter", "No trading adapter connected!")
                self.adapter_status_label.setText("missing")
                self.adapter_status_label.setStyleSheet("color: #f44336; font-size: 10px;")
                self._set_trade_mode_live(False)  # Revert to paper mode
                return

        self.adapter_status_label.setText("connecting...")
        self.adapter_status_label.setStyleSheet("color: #ffa726; font-size: 10px;")

        # Check if adapter has connect method
        if not hasattr(self._adapter, 'connect'):
            logger.info("Adapter has no connect method, assuming already connected")
            self.adapter_status_label.setText("connected")
            self.adapter_status_label.setStyleSheet("color: #26a69a; font-size: 10px;")
            self._update_button_states()
            return

        try:
            # Properly await the async connection
            await self._connect_adapter_async()
        except Exception as exc:
            logger.error(f"Adapter connect failed: {exc}", exc_info=True)
            self.adapter_status_label.setText("error")
            self.adapter_status_label.setStyleSheet("color: #f44336; font-size: 10px;")
            QMessageBox.critical(self, "Connection Error", f"Adapter connect failed:\n\n{exc}")
            self._set_trade_mode_live(False)  # Revert to paper mode

    async def _connect_adapter_async(self):
        """Async adapter connection with status update."""
        try:
            await self._adapter.connect()
            self.adapter_status_label.setText("connected")
            self.adapter_status_label.setStyleSheet("color: #26a69a; font-size: 10px;")
            self._update_button_states()
            logger.info("Adapter connected successfully")
        except Exception as exc:
            logger.error(f"Adapter connect failed: {exc}", exc_info=True)
            self.adapter_status_label.setText("error")
            self.adapter_status_label.setStyleSheet("color: #f44336; font-size: 10px;")

            # Build helpful error message based on error code
            error_str = str(exc)
            if "MISSING_CREDENTIALS" in error_str:
                error_msg = "API credentials not configured.\n\nSet BITUNIX_API_KEY and BITUNIX_API_SECRET as environment variables."
            elif "AUTH_FAILED" in error_str:
                error_msg = "Authentication failed.\n\nPlease verify your Bitunix API key and secret are correct."
            elif "NETWORK_ERROR" in error_str:
                error_msg = "Network error.\n\nPlease check your internet connection and try again."
            else:
                error_msg = f"Connection failed:\n\n{exc}"

            QMessageBox.critical(self, "Bitunix Connection Error", error_msg)
            self._set_trade_mode_live(False)  # Revert to paper mode

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

    # ========================================================================
    # MIRROR MODE: ORDER DELEGATION
    # ========================================================================

    async def _place_order_via_state_manager(self, side: OrderSide) -> None:
        """Place order via state manager (used in mirror mode).

        This method delegates order execution to the central state manager,
        which coordinates with all registered widgets and prevents duplicates.

        Args:
            side: OrderSide.BUY or OrderSide.SELL
        """
        if not hasattr(self, '_state_manager') or not self._state_manager:
            QMessageBox.warning(self, "No State Manager", "Mirror mode requires state manager!")
            return

        # Collect order parameters from UI
        order_type_label = "LIMIT" if self.limit_btn.isChecked() else "MARKET"

        order_params = {
            "symbol": self._current_symbol,
            "side": side.name,  # "BUY" or "SELL"
            "order_type": order_type_label,
            "quantity": self.quantity_spin.value(),
            "leverage": self.leverage_spin.value(),
            "limit_price": self.limit_price_spin.value() if order_type_label == "LIMIT" else None,
        }

        # Add TP/SL if enabled
        if hasattr(self, 'tp_cb') and self.tp_cb.isChecked():
            order_params["take_profit_percent"] = self.tp_spin.value()
        if hasattr(self, 'sl_cb') and self.sl_cb.isChecked():
            order_params["stop_loss_percent"] = self.sl_spin.value()

        # Confirm order
        action = "BUY" if side == OrderSide.BUY else "SELL"
        direction = self._get_direction()
        price_line = (
            f"Limit Price: {order_params['limit_price']:.2f} USDT"
            if order_type_label == "LIMIT"
            else f"Est. Price: {self._last_price:.2f} USDT"
        )

        confirm_msg = (
            f"Confirm {action} Order (via State Manager)\n\n"
            f"Symbol: {self._current_symbol}\n"
            f"Direction: {direction}\n"
            f"Quantity: {order_params['quantity']:.3f}\n"
            f"Leverage: {order_params['leverage']}x\n"
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

        # Delegate to state manager
        try:
            success, message = await self._state_manager.request_order(
                order_params=order_params,
                source_widget=self
            )

            if success:
                QMessageBox.information(self, "Order Placed", message)
            else:
                QMessageBox.warning(self, "Order Failed", message)

        except Exception as e:
            logger.error(f"Order delegation failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Order Error", f"Failed to delegate order:\n\n{str(e)}")
