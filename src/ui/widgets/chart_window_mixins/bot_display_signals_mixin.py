from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QTableWidgetItem, QWidget

logger = logging.getLogger(__name__)

class BotDisplaySignalsMixin:
    """BotDisplaySignalsMixin extracted from BotDisplayManagerMixin."""
    def _update_signals_pnl(self) -> None:
        """Update P&L for all open signals in history."""
        # Get current price - prefer bot_controller._last_features, fallback to chart data
        current_price = 0.0

        if self._bot_controller and self._bot_controller._last_features:
            current_price = self._bot_controller._last_features.close

        # Fallback: get current price from chart widget data
        if current_price <= 0 and hasattr(self, 'chart_widget'):
            if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                try:
                    current_price = float(self.chart_widget.data['close'].iloc[-1])
                except Exception:
                    pass

        if current_price <= 0:
            return

        table_updated = False

        for sig in self._signal_history:
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                entry_price = sig.get("price", 0)
                quantity = sig.get("quantity", 0)
                invested = sig.get("invested", 0)
                side = sig.get("side", "long")

                if entry_price > 0:
                    sig["current_price"] = current_price

                    # Calculate P&L
                    if side.lower() == "long":
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    else:
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100

                    if invested > 0:
                        pnl_currency = invested * (pnl_pct / 100)
                    elif quantity > 0:
                        pnl_currency = quantity * (current_price - entry_price) if side.lower() == "long" else quantity * (entry_price - current_price)
                    else:
                        pnl_currency = 0

                    sig["pnl_currency"] = pnl_currency
                    sig["pnl_percent"] = pnl_pct
                    table_updated = True

                    # Check trailing stop activation
                    self._check_tr_activation(sig, current_price)

        if table_updated:
            self._update_signals_table()
    def _check_tr_activation(self, sig: dict, current_price: float) -> None:
        """Check if trailing stop should be activated based on activation threshold.

        Trailing stop only activates when price moves TRA% into profit:
        - LONG: current_price >= entry_price * (1 + trailing_activation_pct / 100)
        - SHORT: current_price <= entry_price * (1 - trailing_activation_pct / 100)
        """
        # Already active?
        if sig.get("tr_active", False):
            return

        entry_price = sig.get("price", 0)
        trailing_activation_pct = sig.get("trailing_activation_pct", 0)
        trailing_stop_price = sig.get("trailing_stop_price", 0)
        side = sig.get("side", "long").lower()

        # No trailing stop configured
        if trailing_stop_price <= 0:
            return

        # Calculate activation threshold
        if side == "long":
            activation_price = entry_price * (1 + trailing_activation_pct / 100)
            should_activate = current_price >= activation_price
        else:
            activation_price = entry_price * (1 - trailing_activation_pct / 100)
            should_activate = current_price <= activation_price

        if should_activate:
            sig["tr_active"] = True
            self._add_ki_log_entry(
                "TR_ACTIVE",
                f"Trailing Stop aktiviert! Kurs {current_price:.2f} hat "
                f"Schwelle {activation_price:.2f} ({trailing_activation_pct:.2f}% Gewinn) erreicht"
            )
            logger.info(
                f"TR activated: price {current_price:.2f} crossed threshold {activation_price:.2f} "
                f"(entry={entry_price:.2f}, TRA%={trailing_activation_pct:.2f}%)"
            )

            # Draw trailing stop line on chart now that it's active
            if hasattr(self, 'chart_widget'):
                trailing_pct = sig.get("trailing_stop_pct", 0)
                tra_pct = abs((current_price - trailing_stop_price) / current_price) * 100 if current_price > 0 else 0
                tr_label = f"TSL @ {trailing_stop_price:.2f} ({trailing_pct:.2f}% / TRA: {tra_pct:.2f}%)"
                try:
                    self.chart_widget.add_stop_line(
                        "trailing_stop",
                        trailing_stop_price,
                        line_type="trailing",
                        color="#ff9800",
                        label=tr_label
                    )
                except Exception as e:
                    logger.error(f"Failed to draw TR line on activation: {e}")

            self._save_signal_history()
    def _update_signals_table(self) -> None:
        """Update signals table with recent entries.

        Column layout (19 columns):
        0: Time, 1: Type, 2: Side, 3: Entry, 4: Stop, 5: SL%, 6: TR%,
        7: TRA%, 8: TR Lock, 9: Status, 10: Current, 11: P&L €, 12: P&L %,
        13: D P&L € (hidden), 14: D P&L % (hidden), 15: Heb (hidden), 16: WKN (hidden),
        17: Score (hidden), 18: TR Stop (visible - orange when active, gray when inactive)
        """
        self._signals_table_updating = True

        recent_signals = list(reversed(self._signal_history[-20:]))
        self.signals_table.setRowCount(len(recent_signals))

        for row, signal in enumerate(recent_signals):
            stop_price = signal.get("stop_price", 0.0)
            entry_price = signal.get("price", 0)
            is_active = signal.get("status") == "ENTERED" and signal.get("is_open", False)
            trailing_price = signal.get("trailing_stop_price", 0.0)
            trailing_pct, tr_is_active = self._get_trailing_info(signal, entry_price, trailing_price)

            self._set_signal_basic_columns(row, signal)
            self._set_stop_columns(row, signal, stop_price, entry_price, is_active, trailing_pct, trailing_price, tr_is_active)
            self._set_status_and_pnl_columns(row, signal, trailing_price, tr_is_active)

        self._signals_table_updating = False
        if self._has_signals_table_selection():
            self._update_current_position_from_selection()

    def _set_signal_basic_columns(self, row: int, signal: dict) -> None:
        self.signals_table.setItem(row, 0, QTableWidgetItem(signal["time"]))
        signal_type = signal["type"]
        label = signal.get("label", "")
        if label and signal_type == "confirmed":
            type_item = QTableWidgetItem(label)
            type_item.setForeground(QColor("#26a69a"))
        else:
            type_item = QTableWidgetItem(signal_type)
        self.signals_table.setItem(row, 1, type_item)
        self.signals_table.setItem(row, 2, QTableWidgetItem(signal["side"]))
        self.signals_table.setItem(row, 3, QTableWidgetItem(f"{signal['price']:.4f}"))

    def _get_trailing_info(self, signal: dict, entry_price: float, trailing_price: float) -> tuple[float, bool]:
        trailing_pct = signal.get("trailing_stop_pct", 0.0)
        if trailing_pct <= 0 and trailing_price > 0 and entry_price > 0:
            side = signal.get("side", "long")
            if side == "long":
                trailing_pct = abs((entry_price - trailing_price) / entry_price) * 100
            else:
                trailing_pct = abs((trailing_price - entry_price) / entry_price) * 100
        tr_is_active = signal.get("tr_active", False)
        return trailing_pct, tr_is_active

    def _set_stop_columns(
        self,
        row: int,
        signal: dict,
        stop_price: float,
        entry_price: float,
        is_active: bool,
        trailing_pct: float,
        trailing_price: float,
        tr_is_active: bool,
    ) -> None:
        if stop_price > 0:
            self.signals_table.setItem(row, 4, QTableWidgetItem(f"{stop_price:.2f}"))
        else:
            self.signals_table.setItem(row, 4, QTableWidgetItem("-"))

        initial_sl_pct = signal.get("initial_sl_pct", 0.0)
        if initial_sl_pct > 0:
            sl_pct_item = QTableWidgetItem(f"{initial_sl_pct:.2f}")
            sl_pct_item.setForeground(QColor("#ef5350"))
        else:
            if entry_price > 0 and stop_price > 0:
                calculated_sl_pct = abs((stop_price - entry_price) / entry_price) * 100
                sl_pct_item = QTableWidgetItem(f"{calculated_sl_pct:.2f}")
                sl_pct_item.setForeground(QColor("#ef5350"))
            else:
                sl_pct_item = QTableWidgetItem("-")
        if is_active:
            sl_pct_item.setFlags(sl_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.signals_table.setItem(row, 5, sl_pct_item)

        if trailing_pct > 0:
            tr_pct_item = QTableWidgetItem(f"{trailing_pct:.2f}")
            tr_pct_item.setForeground(QColor("#ff9800"))
        else:
            tr_pct_item = QTableWidgetItem("-")
        if is_active:
            tr_pct_item.setFlags(tr_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.signals_table.setItem(row, 6, tr_pct_item)

        trailing_activation_pct = signal.get("trailing_activation_pct", 0.0)
        if trailing_activation_pct > 0:
            tra_item = QTableWidgetItem(f"{trailing_activation_pct:.2f}")
            if tr_is_active:
                tra_item.setForeground(QColor("#ff9800"))
            else:
                tra_item.setForeground(QColor("#888888"))
            self.signals_table.setItem(row, 7, tra_item)
        else:
            self.signals_table.setItem(row, 7, QTableWidgetItem("-"))

        if is_active:
            lock_checkbox = QCheckBox()
            lock_checkbox.blockSignals(True)
            lock_checkbox.setChecked(signal.get("tr_lock_active", False))

            if trailing_price <= 0:
                lock_checkbox.setEnabled(False)
                lock_checkbox.setToolTip("TR Lock nicht verfügbar - kein Trailing Stop konfiguriert")
            elif not tr_is_active:
                lock_checkbox.setEnabled(False)
                activation_pct = signal.get("trailing_activation_pct", 0)
                lock_checkbox.setToolTip(
                    f"TR Lock nicht verfügbar - Trailing Stop noch nicht aktiv.\n"
                    f"Aktivierung erst bei {activation_pct:.2f}% Gewinn vom Einstiegskurs."
                )
            else:
                lock_checkbox.setEnabled(True)
                lock_checkbox.setToolTip(
                    "TR% Lock: Sperrt den TRA% Abstand.\n"
                    "Bei neuer Kerze wird TR nachgezogen wenn Kurs steigt (LONG) bzw. faellt (SHORT)."
                )
            signal_index = len(self._signal_history) - 1 - row
            lock_checkbox.stateChanged.connect(
                lambda state, idx=signal_index: self._on_row_tr_lock_changed(idx, state)
            )
            lock_checkbox.blockSignals(False)
            lock_widget = QWidget()
            lock_layout = QHBoxLayout(lock_widget)
            lock_layout.addWidget(lock_checkbox)
            lock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lock_layout.setContentsMargins(0, 0, 0, 0)
            self.signals_table.setCellWidget(row, 8, lock_widget)
        else:
            self.signals_table.setItem(row, 8, QTableWidgetItem("-"))

        self.signals_table.setItem(row, 9, QTableWidgetItem(signal["status"]))

    def _set_status_and_pnl_columns(
        self,
        row: int,
        signal: dict,
        trailing_price: float,
        tr_is_active: bool,
    ) -> None:
        has_quantity = signal.get("quantity", 0) > 0
        has_invested = signal.get("invested", 0) > 0
        status = signal["status"]
        is_closed = status.startswith("CLOSED") or status in ("SL", "TR", "MACD", "RSI", "Sell")
        is_entered = status == "ENTERED" and signal.get("is_open", False)
        has_derivative = signal.get("derivative") is not None

        if has_quantity or has_invested or is_entered or is_closed or has_derivative:
            current_price = signal.get("current_price", signal["price"])
            pnl_currency = signal.get("pnl_currency", 0.0)
            pnl_percent = signal.get("pnl_percent", 0.0)

            if is_closed:
                exit_price = signal.get("exit_price", current_price)
                current_item = QTableWidgetItem(f"{exit_price:.2f}")
            else:
                current_item = QTableWidgetItem(f"{current_price:.2f}")
            self.signals_table.setItem(row, 10, current_item)

            pnl_sign = "+" if pnl_currency >= 0 else ""
            pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_currency:.2f}")
            pnl_color = "#26a69a" if pnl_currency >= 0 else "#ef5350"
            pnl_item.setForeground(QColor(pnl_color))
            self.signals_table.setItem(row, 11, pnl_item)

            pct_sign = "+" if pnl_percent >= 0 else ""
            pct_item = QTableWidgetItem(f"{pct_sign}{pnl_percent:.2f}%")
            pct_item.setForeground(QColor(pnl_color))
            self.signals_table.setItem(row, 12, pct_item)

            self._set_derivative_columns(row, signal, current_price)
            self.signals_table.setItem(row, 17, QTableWidgetItem(f"{signal['score'] * 100:.0f}"))
            self._set_tr_stop_column(row, trailing_price, tr_is_active)
        else:
            for col in range(10, 19):
                self.signals_table.setItem(row, col, QTableWidgetItem("-"))

    def _set_derivative_columns(self, row: int, signal: dict, current_price: float) -> None:
        deriv = signal.get("derivative")
        if deriv and current_price > 0 and hasattr(self, "_calculate_derivative_pnl_for_signal"):
            deriv_pnl = self._calculate_derivative_pnl_for_signal(signal, current_price)
            if deriv_pnl:
                d_pnl_sign = "+" if deriv_pnl["pnl_eur"] >= 0 else ""
                d_pnl_item = QTableWidgetItem(f"{d_pnl_sign}{deriv_pnl['pnl_eur']:.2f}")
                d_pnl_color = "#26a69a" if deriv_pnl["pnl_eur"] >= 0 else "#ef5350"
                d_pnl_item.setForeground(QColor(d_pnl_color))
                self.signals_table.setItem(row, 13, d_pnl_item)

                d_pct_sign = "+" if deriv_pnl["pnl_pct"] >= 0 else ""
                d_pct_item = QTableWidgetItem(f"{d_pct_sign}{deriv_pnl['pnl_pct']:.2f}%")
                d_pct_item.setForeground(QColor(d_pnl_color))
                self.signals_table.setItem(row, 14, d_pct_item)

                self.signals_table.setItem(row, 15, QTableWidgetItem(f"{deriv['leverage']:.1f}"))
                self.signals_table.setItem(row, 16, QTableWidgetItem(deriv["wkn"]))
                return
            for col in [13, 14, 15, 16]:
                self.signals_table.setItem(row, col, QTableWidgetItem("-"))
        elif deriv:
            self.signals_table.setItem(row, 13, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 14, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 15, QTableWidgetItem(f"{deriv.get('leverage', 0):.1f}"))
            self.signals_table.setItem(row, 16, QTableWidgetItem(deriv.get("wkn", "-")))
        else:
            for col in [13, 14, 15, 16]:
                self.signals_table.setItem(row, col, QTableWidgetItem("-"))

    def _set_tr_stop_column(self, row: int, trailing_price: float, tr_is_active: bool) -> None:
        if trailing_price > 0:
            if tr_is_active:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f}")
                tr_price_item.setForeground(QColor("#ff9800"))
            else:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f} (inaktiv)")
                tr_price_item.setForeground(QColor("#888888"))
            self.signals_table.setItem(row, 18, tr_price_item)
        else:
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))
