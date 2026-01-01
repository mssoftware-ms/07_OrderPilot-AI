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
        info = self._extract_order_info(order)
        order_id = info["order_id"]
        side = info["side"]
        quantity = info["quantity"]
        fill_price = info["fill_price"]
        status = info["status"]
        symbol = info["symbol"]

        logger.info(f"Bot order: {order_id} {side} {quantity} @ {fill_price:.4f} ({status})")

        # For Paper Trading: simulate fill immediately if order is pending
        # This creates the position in the bot controller
        status, fill_price = self._maybe_simulate_paper_fill(
            status, fill_price, quantity, order_id, side
        )

        self._add_ki_log_entry(
            "ORDER",
            f"{side.upper()} {quantity:.4f} {symbol} @ {fill_price:.4f} ({status})"
        )

        # Update signal history on fill
        if status == "filled":
            signal = self._find_open_entered_signal()
            if signal and side.lower() in ("buy", "long"):
                self._update_signal_on_fill(signal, quantity, fill_price)

            # Add entry marker to chart
            self._maybe_add_entry_marker(signal, fill_price)

            self._save_signal_history()
            self._update_signals_table()

    def _extract_order_info(self, order: Any) -> dict[str, Any]:
        return {
            "order_id": getattr(order, "order_id", getattr(order, "id", "unknown")),
            "side": order.side.value if hasattr(order, "side") else "unknown",
            "quantity": getattr(order, "quantity", 0),
            "fill_price": getattr(order, "fill_price", 0),
            "status": order.status.value if hasattr(order, "status") else "pending",
            "symbol": getattr(order, "symbol", "unknown"),
        }

    def _maybe_simulate_paper_fill(
        self,
        status: str,
        fill_price: float,
        quantity: float,
        order_id: str,
        side: str,
    ) -> tuple[str, float]:
        if status != "pending" or not self._bot_controller:
            return status, fill_price
        from src.core.tradingbot.config import TradingEnvironment

        if self._bot_controller.config.bot.environment != TradingEnvironment.PAPER:
            return status, fill_price

        if fill_price <= 0:
            fill_price = self._get_recent_signal_price()

        if fill_price > 0 and quantity > 0:
            self._bot_controller.simulate_fill(fill_price, quantity, order_id)
            status = "filled"
            self._add_ki_log_entry(
                "PAPER",
                f"Paper-Fill simuliert: {side.upper()} {quantity:.4f} @ {fill_price:.4f}",
            )
            logger.info(f"Paper fill simulated: {side} {quantity} @ {fill_price:.4f}")

        return status, fill_price

    def _get_recent_signal_price(self) -> float:
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                return sig.get("price", 0)
        return 0

    def _find_open_entered_signal(self) -> dict[str, Any] | None:
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                return sig
        return None

    def _update_signal_on_fill(
        self, signal: dict[str, Any], quantity: float, fill_price: float
    ) -> None:
        signal["quantity"] = quantity
        signal["fill_price"] = fill_price
        invested = self._calculate_invested_amount()
        signal["invested"] = invested
        logger.info(f"Updated signal with fill: qty={quantity}, invested={invested}")

    def _calculate_invested_amount(self) -> float:
        capital = self.bot_capital_spin.value() if hasattr(self, "bot_capital_spin") else 10000
        risk_pct = (
            self.risk_per_trade_spin.value() if hasattr(self, "risk_per_trade_spin") else 10
        )
        return capital * (risk_pct / 100)

    def _maybe_add_entry_marker(
        self, signal: dict[str, Any] | None, fill_price: float
    ) -> None:
        if not signal:
            return
        if not (hasattr(self, "chart_widget") and hasattr(self.chart_widget, "add_bot_marker")):
            return
        try:
            entry_price = fill_price if fill_price > 0 else signal.get("price", 0)
            if entry_price <= 0:
                return
            sig_side = signal.get("side", "long")
            label = signal.get("label", "E")
            timestamp = signal.get("entry_timestamp", int(datetime.now().timestamp()))
            self.chart_widget.add_bot_marker(
                timestamp=timestamp,
                price=entry_price,
                marker_type=MarkerType.ENTRY_CONFIRMED,
                side=sig_side,
                text=label,
            )
            self._add_ki_log_entry(
                "CHART",
                f"Entry-Marker hinzugefuegt: {label} @ {entry_price:.2f} ({sig_side})",
            )
        except Exception as e:
            logger.error(f"Failed to add entry marker: {e}")
