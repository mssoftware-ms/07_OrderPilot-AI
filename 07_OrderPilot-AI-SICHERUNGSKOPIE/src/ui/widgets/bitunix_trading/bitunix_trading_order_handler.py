"""Bitunix Trading Order Handler - Order Entry & Execution Logic.

Refactored from 1,108 LOC monolith using composition pattern.

Module 2/4 of bitunix_trading_widget.py split.

Contains:
- Order entry event handlers (direction, type, investment, quantity, price, leverage)
- Price calculation logic (_get_current_price with 4-tier fallback)
- Order execution (_on_buy_clicked, _on_sell_clicked, _place_order)
- Button state management
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtWidgets import QMessageBox

from src.core.broker.broker_types import OrderRequest, OrderSide
from src.database.models import OrderType as DBOrderType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BitunixTradingOrderHandler:
    """Helper für Order Entry und Execution Logic."""

    def __init__(self, parent):
        """
        Args:
            parent: BitunixTradingWidget Instanz
        """
        self.parent = parent

    # === Event Handlers ===

    def on_direction_changed(self, index: int) -> None:
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
        return "LONG" if self.parent.position_direction_combo.currentIndex() == 0 else "SHORT"

    def on_order_type_changed(self, order_type: str) -> None:
        """Handle order type change.

        Args:
            order_type: Selected order type ("Market" or "Limit")
        """
        is_limit = order_type == "Limit"
        self.parent.price_spin.setEnabled(is_limit)

    def _update_button_states(self) -> None:
        """Update buy/sell button enabled states."""
        enabled = self.parent.adapter is not None and self.parent._current_symbol is not None
        self.parent.buy_button.setEnabled(enabled)
        self.parent.sell_button.setEnabled(enabled)

    def on_investment_changed(self, value: float) -> None:
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
                    self.parent,
                    "Keine Kurs-Daten",
                    f"Kurs für {self.parent._current_symbol or 'Symbol'} nicht verfügbar.\n\n"
                    "Bitte:\n"
                    "• Öffnen Sie einen Chart mit dem Symbol, oder\n"
                    "• Wählen Sie 'Limit' Order und geben Sie einen Preis ein",
                )
            return

        # Calculate quantity = investment / price
        quantity = value / price
        self.parent.quantity_spin.blockSignals(True)
        self.parent.quantity_spin.setValue(quantity)
        self.parent.quantity_spin.blockSignals(False)

    def on_quantity_changed(self, value: float) -> None:
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
        self.parent.investment_spin.blockSignals(True)
        self.parent.investment_spin.setValue(investment)
        self.parent.investment_spin.blockSignals(False)

    def on_price_changed(self, value: float) -> None:
        """When price changes, recalculate investment from quantity.

        Args:
            value: Price value
        """
        if value > 0:
            self.on_quantity_changed(self.parent.quantity_spin.value())

    def on_leverage_changed(self, value: int) -> None:
        """Update leverage label when slider moves.

        Args:
            value: Leverage value from slider
        """
        if hasattr(self.parent, "leverage_value"):
            self.parent.leverage_value.setText(f"{value}x")

    # === Price Calculation ===

    def _get_current_price(self) -> float:
        """Get current market price with 4-tier fallback strategy.

        Returns:
            float: Current price or 0.0 if unavailable
        """
        # Tier 1: Limit price (explicit user input)
        if self.parent.order_type_combo.currentText() == "Limit":
            limit_price = self.parent.price_spin.value()
            if limit_price > 0:
                return limit_price

        # Tier 2: Live chart price (streaming)
        try:
            parent = self.parent.parent()
            if parent and hasattr(parent, "chart_widget"):
                chart = parent.chart_widget

                # Try to get real-time streaming price
                if hasattr(chart, "_last_price"):
                    last_price = getattr(chart, "_last_price", 0)
                    if last_price > 0:
                        return last_price

                # Tier 3: Historical close price
                if hasattr(chart, "data") and chart.data is not None and not chart.data.empty:
                    try:
                        last_close = float(chart.data["close"].iloc[-1])
                        if last_close > 0:
                            return last_close
                    except (IndexError, KeyError, TypeError, ValueError):
                        pass
        except Exception as e:
            logger.warning(f"Error getting chart price: {e}")

        # Tier 4: No price available - warn user
        if self.parent._current_symbol:
            logger.warning(f"No price data available for {self.parent._current_symbol}")

        return 0.0

    def _current_leverage(self) -> int:
        """Return leverage value from slider (treat 0 as 1 for safety)."""
        val = int(self.parent.leverage_slider.value()) if hasattr(self.parent, "leverage_slider") else 1
        return max(val, 1)

    # === Order Execution ===

    @qasync.asyncSlot()
    async def on_buy_clicked(self) -> None:
        """Handle BUY button click."""
        await self._place_order(OrderSide.BUY)

    @qasync.asyncSlot()
    async def on_sell_clicked(self) -> None:
        """Handle SELL button click."""
        await self._place_order(OrderSide.SELL)

    async def _place_order(self, side: OrderSide) -> None:
        """Place an order.

        Args:
            side: Order side (BUY or SELL)
        """
        if not self.parent.adapter or not self.parent._current_symbol:
            QMessageBox.warning(self.parent, "Cannot Place Order", "No adapter or symbol selected.")
            return

        # Ensure connection is established
        if not self.parent.adapter.connected:
            try:
                await self.parent.adapter.connect()
            except Exception as e:
                logger.error(f"Failed to connect to Bitunix: {e}")
                QMessageBox.critical(
                    self.parent, "Connection Error", f"Failed to connect to Bitunix:\n\n{str(e)}"
                )
                return

        try:
            # Build order request
            order_type = (
                DBOrderType.MARKET if self.parent.order_type_combo.currentText() == "Market" else DBOrderType.LIMIT
            )
            quantity = Decimal(str(self.parent.quantity_spin.value()))
            limit_price = Decimal(str(self.parent.price_spin.value())) if order_type == DBOrderType.LIMIT else None
            stop_loss_val = Decimal(str(self.parent.stop_loss_spin.value()))
            stop_loss = stop_loss_val if stop_loss_val > 0 else None
            take_profit_val = Decimal(str(self.parent.take_profit_spin.value()))
            take_profit = take_profit_val if take_profit_val > 0 else None
            leverage_val = self._current_leverage()
            position_direction = self.get_selected_direction()  # LONG oder SHORT

            order = OrderRequest(
                symbol=self.parent._current_symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                limit_price=limit_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                notes=f"leverage={leverage_val}x,direction={position_direction}",
            )

            # Confirm order
            side_text = "BUY" if side == OrderSide.BUY else "SELL"
            direction_emoji = "🔵" if position_direction == "LONG" else "🔴"
            type_text = "Market" if order_type == DBOrderType.MARKET else f"Limit @ {limit_price}"
            stop_text = f"{stop_loss} (price)" if stop_loss else "—"
            tp_text = f"{take_profit} (price)" if take_profit else "—"
            confirm = QMessageBox.question(
                self.parent,
                "Confirm Order",
                f"Place {side_text} order?\n\n"
                f"Symbol: {self.parent._current_symbol}\n"
                f"Direction: {direction_emoji} {position_direction}\n"
                f"Type: {type_text}\n"
                f"Quantity: {quantity}\n"
                f"Leverage: {leverage_val}x\n"
                f"Stop Loss: {stop_text}\n"
                f"Take Profit: {tp_text}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if confirm != QMessageBox.StandardButton.Yes:
                return

            # Place order
            response = await self.parent.adapter.place_order(order)

            if response and response.broker_order_id:
                QMessageBox.information(
                    self.parent,
                    "Order Placed",
                    f"Order placed successfully!\n\n"
                    f"Order ID: {response.broker_order_id}\n"
                    f"Status: {response.status}",
                )
                logger.info(f"Bitunix order placed: {response.broker_order_id}")

                # Refresh positions
                await self.parent._positions_manager._load_positions()
            else:
                QMessageBox.warning(
                    self.parent, "Order Failed", "Failed to place order. Check logs for details."
                )

        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            QMessageBox.critical(self.parent, "Order Error", f"Error placing order:\n\n{str(e)}")
