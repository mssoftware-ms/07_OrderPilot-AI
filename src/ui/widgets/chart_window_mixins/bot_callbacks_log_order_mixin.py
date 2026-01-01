from __future__ import annotations

import logging
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)

class BotCallbacksLogOrderMixin:
    """BotCallbacksLogOrderMixin extracted from BotCallbacksMixin."""
    def _on_bot_log(self, log_type: str, message: str) -> None:
        """Handle bot log event."""
        self._add_ki_log_entry(log_type.upper(), message)
    def _on_bot_order(self, order: Any) -> None:
        """Handle bot order event."""
        order_id = getattr(order, 'order_id', getattr(order, 'id', 'unknown'))
        side = order.side.value if hasattr(order, 'side') else 'unknown'
        quantity = getattr(order, 'quantity', 0)
        fill_price = getattr(order, 'fill_price', 0)
        status = order.status.value if hasattr(order, 'status') else 'pending'
        symbol = getattr(order, 'symbol', 'unknown')

        logger.info(f"Bot order: {order_id} {side} {quantity} @ {fill_price:.4f} ({status})")

        # For Paper Trading: simulate fill immediately if order is pending
        # This creates the position in the bot controller
        if status == "pending" and self._bot_controller:
            from src.core.tradingbot.config import TradingEnvironment
            if self._bot_controller.config.bot.environment == TradingEnvironment.PAPER:
                # Get fill price from signal entry price or order
                if fill_price <= 0:
                    for sig in reversed(self._signal_history):
                        if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                            fill_price = sig.get("price", 0)
                            break

                if fill_price > 0 and quantity > 0:
                    # Simulate the fill in the bot controller
                    self._bot_controller.simulate_fill(fill_price, quantity, order_id)
                    status = "filled"
                    self._add_ki_log_entry(
                        "PAPER",
                        f"Paper-Fill simuliert: {side.upper()} {quantity:.4f} @ {fill_price:.4f}"
                    )
                    logger.info(f"Paper fill simulated: {side} {quantity} @ {fill_price:.4f}")

        self._add_ki_log_entry(
            "ORDER",
            f"{side.upper()} {quantity:.4f} {symbol} @ {fill_price:.4f} ({status})"
        )

        # Update signal history on fill
        if status == "filled":
            for sig in reversed(self._signal_history):
                if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                    if side.lower() in ("buy", "long"):
                        sig["quantity"] = quantity
                        sig["fill_price"] = fill_price
                        # Calculate invested amount
                        capital = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000
                        risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10
                        invested = capital * (risk_pct / 100)
                        sig["invested"] = invested
                        logger.info(f"Updated signal with fill: qty={quantity}, invested={invested}")
                    break

            # Add entry marker to chart
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_bot_marker'):
                try:
                    # Use fill_price or entry_price
                    entry_price = fill_price if fill_price > 0 else 0
                    for sig in reversed(self._signal_history):
                        if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                            sig_side = sig.get("side", "long")
                            label = sig.get("label", "E")
                            timestamp = sig.get("entry_timestamp", int(datetime.now().timestamp()))

                            if entry_price <= 0:
                                entry_price = sig.get("price", 0)

                            if entry_price > 0:
                                self.chart_widget.add_bot_marker(
                                    timestamp=timestamp,
                                    price=entry_price,
                                    marker_type=MarkerType.ENTRY_CONFIRMED,
                                    side=sig_side,
                                    text=label
                                )
                                self._add_ki_log_entry(
                                    "CHART",
                                    f"Entry-Marker hinzugefuegt: {label} @ {entry_price:.2f} ({sig_side})"
                                )
                            break
                except Exception as e:
                    logger.error(f"Failed to add entry marker: {e}")

            self._save_signal_history()
            self._update_signals_table()
