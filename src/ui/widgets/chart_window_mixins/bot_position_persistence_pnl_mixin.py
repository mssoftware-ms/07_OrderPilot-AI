from __future__ import annotations

import logging

from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)

class BotPositionPersistencePnlMixin:
    """BotPositionPersistencePnlMixin extracted from BotPositionPersistenceMixin."""
    def _start_pnl_update_timer(self) -> None:
        """Start timer to update P&L for restored positions."""
        if not hasattr(self, '_pnl_update_timer') or self._pnl_update_timer is None:
            self._pnl_update_timer = QTimer()
            self._pnl_update_timer.timeout.connect(self._update_restored_positions_pnl)
        self._pnl_update_timer.start(2000)
        logger.info("P&L update timer started")
    def _update_restored_positions_pnl(self) -> None:
        """Update P&L for restored positions from chart's current price."""
        current_price = self._get_chart_current_price()

        if current_price <= 0:
            return

        # Update active positions
        table_updated = False
        for sig in self._signal_history:
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                if not self._update_signal_pnl(sig, current_price):
                    continue
                pnl_pct = sig.get("pnl_percent", 0)
                pnl_currency = sig.get("pnl_currency", 0)
                table_updated = True

                # Check trailing stop activation (from BotDisplayManagerMixin)
                if hasattr(self, '_check_tr_activation'):
                    self._check_tr_activation(sig, current_price)

                # Update Current Position display
                self._update_position_labels(current_price, pnl_pct, pnl_currency)

                # Update derivative P&L if enabled
                self._update_derivative_pnl(sig, current_price)

        if table_updated:
            self._update_signals_table()

    def _get_chart_current_price(self) -> float:
        if hasattr(self, 'chart_widget'):
            if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                try:
                    return float(self.chart_widget.data['close'].iloc[-1])
                except Exception:
                    return 0.0
        return 0.0

    def _update_signal_pnl(self, sig: dict, current_price: float) -> bool:
        entry_price = sig.get("price", 0)
        invested = sig.get("invested", 0)
        side = sig.get("side", "long")

        if entry_price <= 0:
            return False

        sig["current_price"] = current_price
        pnl_pct = self._calculate_pnl_pct(entry_price, current_price, side)
        pnl_currency = invested * (pnl_pct / 100) if invested > 0 else 0
        sig["pnl_currency"] = pnl_currency
        sig["pnl_percent"] = pnl_pct
        return True

    def _calculate_pnl_pct(self, entry_price: float, current_price: float, side: str) -> float:
        if side.lower() == "long":
            return ((current_price - entry_price) / entry_price) * 100
        return ((entry_price - current_price) / entry_price) * 100

    def _update_position_labels(self, current_price: float, pnl_pct: float, pnl_currency: float) -> None:
        if hasattr(self, 'position_current_label'):
            self.position_current_label.setText(f"{current_price:.4f}")

        if hasattr(self, 'position_pnl_label'):
            color = "#26a69a" if pnl_pct >= 0 else "#ef5350"
            sign = "+" if pnl_pct >= 0 else ""
            self.position_pnl_label.setText(
                f"{sign}{pnl_pct:.2f}% ({sign}{pnl_currency:.2f} EUR)"
            )
            self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")

    def _update_derivative_pnl(self, sig: dict, current_price: float) -> None:
        if not (
            hasattr(self, 'enable_derivathandel_cb')
            and self.enable_derivathandel_cb.isChecked()
            and hasattr(self, '_calculate_derivative_pnl_for_signal')
        ):
            return
        deriv_pnl = self._calculate_derivative_pnl_for_signal(sig, current_price)
        if not deriv_pnl or not hasattr(self, 'deriv_pnl_label'):
            return
        d_pnl_eur = deriv_pnl.get("pnl_eur", 0)
        d_pnl_pct = deriv_pnl.get("pnl_pct", 0)
        d_color = "#26a69a" if d_pnl_eur >= 0 else "#ef5350"
        d_sign = "+" if d_pnl_eur >= 0 else ""
        self.deriv_pnl_label.setText(
            f"{d_sign}{d_pnl_pct:.2f}% ({d_sign}{d_pnl_eur:.2f} €)"
        )
        self.deriv_pnl_label.setStyleSheet(f"font-weight: bold; color: {d_color};")
