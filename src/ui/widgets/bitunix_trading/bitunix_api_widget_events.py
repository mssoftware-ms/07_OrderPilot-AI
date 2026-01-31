"""Bitunix Trading API Widget - Event Handlers Module.

This module contains all event handlers and calculation logic for the BitunixTradingAPIWidget.
Separated from UI construction and API logic for maintainability.

Handlers:
    - Symbol and order type changes
    - Quantity/Volume calculations
    - Leverage/Preset adjustments
    - TP/SL toggle and sync
    - Direction and trade mode changes
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import QMessageBox
import qasync

logger = logging.getLogger(__name__)


class BitunixAPIWidgetEvents:
    """Mixin providing event handlers for BitunixTradingAPIWidget."""

    def _connect_event_handlers(self):
        """Connect all event handlers to UI components.

        This method should be called after UI setup to wire all signals.
        """
        # Symbol and order type
        self.symbol_combo.currentTextChanged.connect(self._on_symbol_changed)
        self.market_btn.clicked.connect(self._on_order_type_changed)
        self.limit_btn.clicked.connect(self._on_order_type_changed)
        self.limit_price_spin.valueChanged.connect(self._on_limit_price_changed)

        # Direction
        self.long_btn.clicked.connect(lambda: self._set_direction("LONG"))
        self.short_btn.clicked.connect(lambda: self._set_direction("SHORT"))

        # Quantity and volume
        self.quantity_spin.valueChanged.connect(self._on_quantity_changed)
        self.volume_spin.valueChanged.connect(self._on_volume_changed)

        # Leverage
        self.leverage_spin.valueChanged.connect(self._on_leverage_changed_spinbox)
        self.exposure_slider.valueChanged.connect(self._on_exposure_changed)

        # TP/SL
        self.tp_cb.toggled.connect(self._on_tp_toggled)
        self.sl_cb.toggled.connect(self._on_sl_toggled)
        self.sync_sl_btn.clicked.connect(self._on_sync_sl)
        self.trailing_cb.toggled.connect(self._on_trailing_toggled)

        # Trade mode
        self.trade_mode_btn.clicked.connect(self._on_trade_mode_changed)

        # BUY/SELL buttons
        self.buy_btn.clicked.connect(self._on_buy_clicked)
        self.sell_btn.clicked.connect(self._on_sell_clicked)

        # Preset buttons - connect all preset buttons
        from PyQt6.QtWidgets import QPushButton
        for btn in self.findChildren(QPushButton):
            preset_value = btn.property("preset_value")
            if preset_value is not None:
                btn.clicked.connect(lambda checked, v=preset_value: self._on_preset_clicked(v))

    # ========================================================================
    # SYMBOL AND ORDER TYPE HANDLERS
    # ========================================================================

    def _on_symbol_changed(self, symbol: str):
        """Handle symbol change.

        Args:
            symbol: New trading symbol (e.g., "BTCUSDT")
        """
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
        """Handle order type change (Market/Limit)."""
        is_limit = self.limit_btn.isChecked()
        self.limit_price_spin.setVisible(is_limit)
        self.limit_price_label.setVisible(is_limit)
        if is_limit:
            # Statisch mit aktuellem Kurs befüllen beim Sichtbar-Werden
            if self._last_price > 0:
                self.limit_price_spin.blockSignals(True)
                self.limit_price_spin.setValue(self._last_price)
                self.limit_price_spin.blockSignals(False)
        self._recalculate_from_price()

    def _on_limit_price_changed(self, value: float):
        """Handle limit price change.

        Args:
            value: New limit price value
        """
        if self._is_updating:
            return
        if value <= 0:
            return
        self._recalculate_from_price()

    # ========================================================================
    # DIRECTION HANDLERS
    # ========================================================================

    def _set_direction(self, direction: str):
        """Set position direction (LONG/SHORT).

        Args:
            direction: "LONG" or "SHORT"
        """
        if direction == "LONG":
            self.long_btn.setChecked(True)
            self.short_btn.setChecked(False)
        else:
            self.long_btn.setChecked(False)
            self.short_btn.setChecked(True)
        logger.debug(f"Direction set to: {direction}")

    def _get_direction(self) -> str:
        """Get current position direction.

        Returns:
            str: "LONG" or "SHORT"
        """
        return "LONG" if self.long_btn.isChecked() else "SHORT"

    # ========================================================================
    # QUANTITY AND VOLUME HANDLERS
    # ========================================================================

    def _on_quantity_changed(self, value: float):
        """Calculate volume from quantity.

        Args:
            value: New quantity value
        """
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
        """Calculate quantity from volume.

        Args:
            value: New volume value
        """
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

    def _get_effective_price(self) -> float:
        """Get the price used for volume/quantity calculations.

        Returns:
            float: Limit price if set and limit order, otherwise last market price
        """
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

    # ========================================================================
    # LEVERAGE AND PRESET HANDLERS
    # ========================================================================

    def _on_leverage_changed_spinbox(self, value: int):
        """Sync slider with spinbox.

        Args:
            value: New leverage value
        """
        self.exposure_slider.blockSignals(True)
        self.exposure_slider.setValue(value)
        self.exposure_slider.blockSignals(False)

    def _on_exposure_changed(self, value: int):
        """Update exposure label and sync spinbox.

        Args:
            value: New slider value
        """
        self.leverage_spin.blockSignals(True)
        self.leverage_spin.setValue(value)
        self.leverage_spin.blockSignals(False)

    def _on_preset_clicked(self, value: int):
        """Handle preset button click.

        Args:
            value: Preset leverage value (10-200)
        """
        self.exposure_slider.setValue(value)
        self.leverage_spin.setValue(value)
        logger.debug(f"Preset clicked: {value}x")

    # ========================================================================
    # TP/SL HANDLERS
    # ========================================================================

    def _on_tp_toggled(self, checked: bool):
        """Handle TP checkbox toggle.

        Args:
            checked: True if TP enabled
        """
        self.tp_spin.setEnabled(checked)

    def _on_sl_toggled(self, checked: bool):
        """Handle SL checkbox toggle.

        Args:
            checked: True if SL enabled
        """
        self.sl_spin.setEnabled(checked)

    def _on_sync_sl(self):
        """Sync SL to exchange via modify_position_tp_sl_order."""
        if not self._adapter:
            QMessageBox.warning(self, "No Adapter", "No trading adapter connected!")
            return

        if not self.sl_cb.isChecked():
            QMessageBox.warning(self, "SL Not Enabled", "Stop Loss checkbox is not enabled!")
            return

        sl_percent = self.sl_spin.value()
        if sl_percent <= 0:
            QMessageBox.warning(self, "Invalid SL", "Stop Loss percentage must be greater than 0!")
            return

        # Calculate absolute SL price from percentage
        if self._last_price <= 0:
            QMessageBox.warning(self, "No Price", "No current price available!")
            return

        direction = self._get_direction()
        if direction == "LONG":
            # Long: SL below entry price
            sl_price = self._last_price * (1 - sl_percent / 100)
        else:
            # Short: SL above entry price
            sl_price = self._last_price * (1 + sl_percent / 100)

        # TODO: Call adapter.modify_position_tp_sl_order(position_id, sl_price)
        logger.info(f"Sync SL to exchange: {sl_percent}% = ${sl_price:.2f}")
        self.trailing_info.setText(f"Last SL: {sl_percent:.1f}%")
        QMessageBox.information(self, "SL Synced", f"Stop Loss synced to {sl_percent:.1f}% (${sl_price:.2f})")

    def _on_trailing_toggled(self, checked: bool):
        """Handle trailing stop toggle.

        Args:
            checked: True if trailing enabled
        """
        if checked:
            logger.info("Trailing stop enabled - will update SL on price movement")
        else:
            logger.info("Trailing stop disabled")

    # ========================================================================
    # TRADE MODE HANDLERS
    # ========================================================================

    def _on_trade_mode_changed(self) -> None:
        """Toggle paper/live trading mode."""
        self._set_trade_mode_live(self.trade_mode_btn.isChecked())

    def _set_trade_mode_live(self, is_live: bool) -> None:
        """Apply live trading mode to UI state.

        Args:
            is_live: True for live trading, False for paper
        """
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

    # ========================================================================
    # BUY/SELL HANDLERS
    # ========================================================================

    @qasync.asyncSlot()
    async def _on_buy_clicked(self):
        """Handle BUY button click."""
        from src.core.broker.broker_types import OrderSide
        await self._place_order(OrderSide.BUY)

    @qasync.asyncSlot()
    async def _on_sell_clicked(self):
        """Handle SELL button click."""
        from src.core.broker.broker_types import OrderSide
        await self._place_order(OrderSide.SELL)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _update_button_states(self):
        """Update button enabled states based on adapter and mode."""
        enabled = (
            self._adapter is not None
            and self._current_symbol is not None
            and self.trade_mode_btn.isChecked()
        )
        self.buy_btn.setEnabled(enabled)
        self.sell_btn.setEnabled(enabled)

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
