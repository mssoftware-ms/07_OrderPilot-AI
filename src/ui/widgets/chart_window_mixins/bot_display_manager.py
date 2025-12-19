"""Bot Display Manager - Display update methods.

Contains methods for updating UI displays:
- _update_bot_status, _update_bot_display
- _update_signals_pnl, _update_signals_table
- _add_ki_log_entry, _log_bot_diagnostics
- update_strategy_scores, update_walk_forward_results
- log_ki_request
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QTableWidgetItem,
    QWidget,
)

logger = logging.getLogger(__name__)


class BotDisplayManagerMixin:
    """Mixin providing bot display update methods."""

    def _update_bot_status(self, status: str, color: str) -> None:
        """Update bot status indicator."""
        if hasattr(self, 'bot_status_label'):
            self.bot_status_label.setText(f"Status: {status}")
            self.bot_status_label.setStyleSheet(
                f"font-weight: bold; color: {color}; font-size: 14px;"
            )

    def _update_bot_display(self) -> None:
        """Update bot display with current state."""
        if not self._bot_controller:
            # Even without bot_controller, update P&L from chart data for restored positions
            self._update_signals_pnl()
            return

        # Update position display
        position = self._bot_controller.position
        if position:
            side = position.side.value.upper() if hasattr(position.side, 'value') else str(position.side)
            self.position_side_label.setText(side)

            if side == "LONG":
                self.position_side_label.setStyleSheet("font-weight: bold; color: #26a69a;")
            elif side == "SHORT":
                self.position_side_label.setStyleSheet("font-weight: bold; color: #ef5350;")

            self.position_entry_label.setText(f"{position.entry_price:.4f}")
            self.position_size_label.setText(f"{position.quantity:.4f}")

            # Invested amount from signal history
            invested = 0
            for sig in reversed(self._signal_history):
                if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                    invested = sig.get("invested", 0)
                    break
            if invested > 0:
                self.position_invested_label.setText(f"{invested:.0f}")
            else:
                capital = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000
                risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10
                invested = capital * (risk_pct / 100)
                self.position_invested_label.setText(f"~{invested:.0f}")

            # Stop price
            trailing = getattr(position, 'trailing', None)
            if trailing:
                stop = trailing.current_stop_price
                self.position_stop_label.setText(f"{stop:.4f}")

            # Current price and P&L - get from _last_features or chart data
            current = 0.0
            if self._bot_controller._last_features:
                current = self._bot_controller._last_features.close

            # Fallback: get current price from chart widget data
            if current <= 0 and hasattr(self, 'chart_widget'):
                if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                    try:
                        current = float(self.chart_widget.data['close'].iloc[-1])
                    except Exception:
                        pass

            if current > 0:
                self.position_current_label.setText(f"{current:.4f}")

                # Calculate P&L
                if side == "LONG":
                    pnl_pct = ((current - position.entry_price) / position.entry_price) * 100
                else:
                    pnl_pct = ((position.entry_price - current) / position.entry_price) * 100

                pnl_currency = invested * (pnl_pct / 100)

                color = "#26a69a" if pnl_pct >= 0 else "#ef5350"
                sign = "+" if pnl_pct >= 0 else ""
                self.position_pnl_label.setText(f"{sign}{pnl_pct:.2f}% ({sign}{pnl_currency:.2f})")
                self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")

            # Bars held
            bars = position.bars_held
            self.position_bars_held_label.setText(str(bars))

            # Update right column (Score, TR Kurs, Derivative)
            self._update_position_right_column()

        else:
            # No position in bot_controller - check signal_history for open positions
            open_signal = None
            for sig in reversed(self._signal_history):
                if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                    open_signal = sig
                    break

            if open_signal:
                # Show position from signal history
                side = open_signal.get("side", "unknown").upper()
                self.position_side_label.setText(side)
                if side == "LONG":
                    self.position_side_label.setStyleSheet("font-weight: bold; color: #26a69a;")
                elif side == "SHORT":
                    self.position_side_label.setStyleSheet("font-weight: bold; color: #ef5350;")

                entry_price = open_signal.get("price", 0)
                self.position_entry_label.setText(f"{entry_price:.4f}" if entry_price > 0 else "-")

                quantity = open_signal.get("quantity", 0)
                self.position_size_label.setText(f"{quantity:.4f}" if quantity > 0 else "-")

                invested = open_signal.get("invested", 0)
                self.position_invested_label.setText(f"{invested:.0f}" if invested > 0 else "-")

                stop_price = open_signal.get("trailing_stop_price", open_signal.get("stop_price", 0))
                self.position_stop_label.setText(f"{stop_price:.4f}" if stop_price > 0 else "-")

                # Get current price from chart
                current = 0.0
                if hasattr(self, 'chart_widget'):
                    if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                        try:
                            current = float(self.chart_widget.data['close'].iloc[-1])
                        except Exception:
                            pass

                if current > 0:
                    self.position_current_label.setText(f"{current:.4f}")
                    open_signal["current_price"] = current

                    # Calculate P&L
                    if entry_price > 0:
                        if side == "LONG":
                            pnl_pct = ((current - entry_price) / entry_price) * 100
                        else:
                            pnl_pct = ((entry_price - current) / entry_price) * 100

                        pnl_currency = invested * (pnl_pct / 100) if invested > 0 else 0
                        open_signal["pnl_percent"] = pnl_pct
                        open_signal["pnl_currency"] = pnl_currency

                        color = "#26a69a" if pnl_pct >= 0 else "#ef5350"
                        sign = "+" if pnl_pct >= 0 else ""
                        self.position_pnl_label.setText(f"{sign}{pnl_pct:.2f}% ({sign}{pnl_currency:.2f})")
                        self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")
                    else:
                        self.position_pnl_label.setText("-")
                else:
                    self.position_current_label.setText("-")
                    self.position_pnl_label.setText("-")

                self.position_bars_held_label.setText("-")  # Not tracked without bot position

                # Update right column for signal from history
                self._update_position_right_column()
            else:
                # Truly flat - no position anywhere
                self.position_side_label.setText("FLAT")
                self.position_side_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
                self.position_entry_label.setText("-")
                self.position_size_label.setText("-")
                self.position_invested_label.setText("-")
                self.position_stop_label.setText("-")
                self.position_current_label.setText("-")
                self.position_pnl_label.setText("-")
                self.position_bars_held_label.setText("-")

                # Reset right column
                self._reset_position_right_column()

        # Update signals P&L
        self._update_signals_pnl()

    def _update_position_right_column(self) -> None:
        """Update the right column of Current Position groupbox (Score, TR, Derivative)."""
        # Find the active signal
        open_signal = None
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                open_signal = sig
                break

        if not open_signal:
            self._reset_position_right_column()
            return

        # Update Score
        score = open_signal.get("score", 0)
        if hasattr(self, "position_score_label"):
            self.position_score_label.setText(f"{score * 100:.0f}")

        # Update TR Kurs
        tr_price = open_signal.get("trailing_stop_price", 0)
        tr_active = open_signal.get("tr_active", False)
        if hasattr(self, "position_tr_price_label"):
            if tr_price > 0:
                if tr_active:
                    self.position_tr_price_label.setText(f"{tr_price:.2f}")
                    self.position_tr_price_label.setStyleSheet("color: #ff9800;")
                else:
                    self.position_tr_price_label.setText(f"{tr_price:.2f} (inaktiv)")
                    self.position_tr_price_label.setStyleSheet("color: #888888;")
            else:
                self.position_tr_price_label.setText("-")
                self.position_tr_price_label.setStyleSheet("")

        # Update Derivative section
        deriv = open_signal.get("derivative")
        if deriv:
            if hasattr(self, "deriv_wkn_label"):
                self.deriv_wkn_label.setText(deriv.get("wkn", "-"))
            if hasattr(self, "deriv_leverage_label"):
                lev = deriv.get("leverage", 0)
                self.deriv_leverage_label.setText(f"{lev:.1f}x" if lev else "-")
            if hasattr(self, "deriv_spread_label"):
                spread = deriv.get("spread_pct", 0)
                self.deriv_spread_label.setText(f"{spread:.2f}%" if spread else "-")
            if hasattr(self, "deriv_ask_label"):
                ask = deriv.get("ask", 0)
                self.deriv_ask_label.setText(f"{ask:.2f}" if ask else "-")

            # Calculate derivative P&L
            current_price = open_signal.get("current_price", 0)
            if current_price > 0 and hasattr(self, "_calculate_derivative_pnl_for_signal"):
                deriv_pnl = self._calculate_derivative_pnl_for_signal(open_signal, current_price)
                if deriv_pnl and hasattr(self, "deriv_pnl_label"):
                    sign = "+" if deriv_pnl["pnl_pct"] >= 0 else ""
                    color = "#26a69a" if deriv_pnl["pnl_pct"] >= 0 else "#ef5350"
                    self.deriv_pnl_label.setText(
                        f"{sign}{deriv_pnl['pnl_pct']:.2f}% ({sign}{deriv_pnl['pnl_eur']:.2f})"
                    )
                    self.deriv_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")
                elif hasattr(self, "deriv_pnl_label"):
                    self.deriv_pnl_label.setText("-")
                    self.deriv_pnl_label.setStyleSheet("")
            elif hasattr(self, "deriv_pnl_label"):
                self.deriv_pnl_label.setText("-")
                self.deriv_pnl_label.setStyleSheet("")
        else:
            self._reset_derivative_labels()

    def _reset_position_right_column(self) -> None:
        """Reset all labels in the right column of Current Position groupbox."""
        if hasattr(self, "position_score_label"):
            self.position_score_label.setText("-")
        if hasattr(self, "position_tr_price_label"):
            self.position_tr_price_label.setText("-")
            self.position_tr_price_label.setStyleSheet("")
        self._reset_derivative_labels()

    def _reset_derivative_labels(self) -> None:
        """Reset derivative labels to default state."""
        deriv_labels = ["deriv_wkn_label", "deriv_leverage_label", "deriv_spread_label",
                        "deriv_ask_label", "deriv_pnl_label"]
        for label_name in deriv_labels:
            label = getattr(self, label_name, None)
            if label:
                label.setText("-")
                label.setStyleSheet("")

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
        13: D P&L €, 14: D P&L %, 15: Heb, 16: WKN, 17: Score (hidden), 18: TR Kurs (hidden)
        """
        self._signals_table_updating = True

        recent_signals = list(reversed(self._signal_history[-20:]))
        self.signals_table.setRowCount(len(recent_signals))

        for row, signal in enumerate(recent_signals):
            # Column 0: Time
            self.signals_table.setItem(row, 0, QTableWidgetItem(signal["time"]))

            # Column 1: Type
            signal_type = signal["type"]
            label = signal.get("label", "")
            if label and signal_type == "confirmed":
                type_item = QTableWidgetItem(label)
                type_item.setForeground(QColor("#26a69a"))
            else:
                type_item = QTableWidgetItem(signal_type)
            self.signals_table.setItem(row, 1, type_item)

            # Column 2: Side
            self.signals_table.setItem(row, 2, QTableWidgetItem(signal["side"]))

            # Column 3: Entry
            self.signals_table.setItem(row, 3, QTableWidgetItem(f"{signal['price']:.4f}"))

            # Column 4: Stop
            stop_price = signal.get("stop_price", 0.0)
            entry_price = signal.get("price", 0)
            if stop_price > 0:
                self.signals_table.setItem(row, 4, QTableWidgetItem(f"{stop_price:.2f}"))
            else:
                self.signals_table.setItem(row, 4, QTableWidgetItem("-"))

            # Column 5: SL%
            initial_sl_pct = signal.get("initial_sl_pct", 0.0)
            is_active = signal.get("status") == "ENTERED" and signal.get("is_open", False)
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

            # Column 6: TR%
            trailing_pct = signal.get("trailing_stop_pct", 0.0)
            trailing_price = signal.get("trailing_stop_price", 0.0)

            if trailing_pct <= 0 and trailing_price > 0 and entry_price > 0:
                side = signal.get("side", "long")
                if side == "long":
                    trailing_pct = abs((entry_price - trailing_price) / entry_price) * 100
                else:
                    trailing_pct = abs((trailing_price - entry_price) / entry_price) * 100

            if trailing_pct > 0:
                tr_pct_item = QTableWidgetItem(f"{trailing_pct:.2f}")
                tr_pct_item.setForeground(QColor("#ff9800"))
            else:
                tr_pct_item = QTableWidgetItem("-")
            if is_active:
                tr_pct_item.setFlags(tr_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.signals_table.setItem(row, 6, tr_pct_item)

            # Column 7: TRA% - distance from current price to TR line
            tr_is_active = signal.get("tr_active", False)
            current_price_for_tra = signal.get("current_price", signal["price"])
            if trailing_price > 0 and current_price_for_tra > 0:
                tra_pct = abs((current_price_for_tra - trailing_price) / current_price_for_tra) * 100
                tra_item = QTableWidgetItem(f"{tra_pct:.2f}")
                if tr_is_active:
                    tra_item.setForeground(QColor("#ff9800"))
                else:
                    tra_item.setForeground(QColor("#888888"))
                self.signals_table.setItem(row, 7, tra_item)
            else:
                self.signals_table.setItem(row, 7, QTableWidgetItem("-"))

            # Column 8: TR Lock - checkbox for active positions
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

            # Column 9: Status
            self.signals_table.setItem(row, 9, QTableWidgetItem(signal["status"]))

            # P&L columns
            has_quantity = signal.get("quantity", 0) > 0
            has_invested = signal.get("invested", 0) > 0
            status = signal["status"]
            is_closed = status.startswith("CLOSED") or status in ("SL", "TR Stop", "MACD", "RSI", "Time", "Sold")
            is_entered = status == "ENTERED" and signal.get("is_open", False)

            if has_quantity or has_invested or is_entered or is_closed:
                current_price = signal.get("current_price", signal["price"])
                pnl_currency = signal.get("pnl_currency", 0.0)
                pnl_percent = signal.get("pnl_percent", 0.0)

                # Column 10: Current
                if is_closed:
                    exit_price = signal.get("exit_price", current_price)
                    current_item = QTableWidgetItem(f"{exit_price:.2f}")
                else:
                    current_item = QTableWidgetItem(f"{current_price:.2f}")
                self.signals_table.setItem(row, 10, current_item)

                # Column 11: P&L €
                pnl_sign = "+" if pnl_currency >= 0 else ""
                pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_currency:.2f}")
                pnl_color = "#26a69a" if pnl_currency >= 0 else "#ef5350"
                pnl_item.setForeground(QColor(pnl_color))
                self.signals_table.setItem(row, 11, pnl_item)

                # Column 12: P&L %
                pct_sign = "+" if pnl_percent >= 0 else ""
                pct_item = QTableWidgetItem(f"{pct_sign}{pnl_percent:.2f}%")
                pct_item.setForeground(QColor(pnl_color))
                self.signals_table.setItem(row, 12, pct_item)

                # Columns 13-16: Derivative P&L (only if derivative exists)
                deriv = signal.get("derivative")
                if deriv and current_price > 0 and hasattr(self, "_calculate_derivative_pnl_for_signal"):
                    deriv_pnl = self._calculate_derivative_pnl_for_signal(signal, current_price)
                    if deriv_pnl:
                        # Column 13: D P&L €
                        d_pnl_sign = "+" if deriv_pnl["pnl_eur"] >= 0 else ""
                        d_pnl_item = QTableWidgetItem(f"{d_pnl_sign}{deriv_pnl['pnl_eur']:.2f}")
                        d_pnl_color = "#26a69a" if deriv_pnl["pnl_eur"] >= 0 else "#ef5350"
                        d_pnl_item.setForeground(QColor(d_pnl_color))
                        self.signals_table.setItem(row, 13, d_pnl_item)

                        # Column 14: D P&L %
                        d_pct_sign = "+" if deriv_pnl["pnl_pct"] >= 0 else ""
                        d_pct_item = QTableWidgetItem(f"{d_pct_sign}{deriv_pnl['pnl_pct']:.2f}%")
                        d_pct_item.setForeground(QColor(d_pnl_color))
                        self.signals_table.setItem(row, 14, d_pct_item)

                        # Column 15: Hebel
                        self.signals_table.setItem(row, 15, QTableWidgetItem(f"{deriv['leverage']:.1f}"))

                        # Column 16: WKN
                        self.signals_table.setItem(row, 16, QTableWidgetItem(deriv["wkn"]))
                    else:
                        for col in [13, 14, 15, 16]:
                            self.signals_table.setItem(row, col, QTableWidgetItem("-"))
                elif deriv:
                    # Derivative exists but no P&L calculation possible
                    self.signals_table.setItem(row, 13, QTableWidgetItem("-"))
                    self.signals_table.setItem(row, 14, QTableWidgetItem("-"))
                    self.signals_table.setItem(row, 15, QTableWidgetItem(f"{deriv.get('leverage', 0):.1f}"))
                    self.signals_table.setItem(row, 16, QTableWidgetItem(deriv.get("wkn", "-")))
                else:
                    for col in [13, 14, 15, 16]:
                        self.signals_table.setItem(row, col, QTableWidgetItem("-"))

                # Column 17: Score (hidden)
                self.signals_table.setItem(row, 17, QTableWidgetItem(f"{signal['score'] * 100:.0f}"))

                # Column 18: TR Kurs (hidden)
                if trailing_price > 0:
                    if tr_is_active:
                        tr_price_item = QTableWidgetItem(f"{trailing_price:.2f}")
                    else:
                        tr_price_item = QTableWidgetItem(f"{trailing_price:.2f} (inaktiv)")
                    self.signals_table.setItem(row, 18, tr_price_item)
                else:
                    self.signals_table.setItem(row, 18, QTableWidgetItem("-"))
            else:
                for col in range(10, 19):
                    self.signals_table.setItem(row, col, QTableWidgetItem("-"))

        self._signals_table_updating = False

    def _add_ki_log_entry(self, entry_type: str, message: str) -> None:
        """Add entry to KI log (uses local time)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{entry_type}] {message}"
        self.ki_log_text.appendPlainText(entry)
        self._ki_log_entries.append({
            "time": timestamp,
            "type": entry_type,
            "message": message
        })

    def _log_bot_diagnostics(self) -> None:
        """Log periodic bot diagnostics for debugging."""
        if not self._bot_controller:
            return

        bc = self._bot_controller
        state = bc.state.value if hasattr(bc.state, 'value') else str(bc.state)
        can_trade = bc.can_trade
        reasons = []

        if hasattr(bc, '_state_machine'):
            if bc._state_machine.is_paused():
                reasons.append("PAUSED")
            if bc._state_machine.is_error():
                reasons.append("ERROR")

        if not bc.config.bot.disable_restrictions:
            if bc._trades_today >= bc.config.risk.max_trades_per_day:
                reasons.append(f"MAX_TRADES({bc._trades_today}/{bc.config.risk.max_trades_per_day})")

            account_value = 10000.0
            daily_pnl_pct = (bc._daily_pnl / account_value) * 100
            if daily_pnl_pct <= -bc.config.risk.max_daily_loss_pct:
                reasons.append(f"MAX_LOSS({daily_pnl_pct:.2f}%)")

            if bc._consecutive_losses >= bc.config.risk.loss_streak_cooldown:
                reasons.append(f"LOSS_STREAK({bc._consecutive_losses}/{bc.config.risk.loss_streak_cooldown})")
        else:
            reasons.append("UNRESTRICTED")

        pos_status = "None"
        if bc.position:
            pos_status = f"{bc.position.side.value.upper()} @ {bc.position.entry_price:.2f}"

        status_str = "OK" if can_trade else "X"
        reason_str = ", ".join(reasons) if reasons else "OK"

        self._add_ki_log_entry(
            "DIAG",
            f"State={state} | CanTrade={status_str} [{reason_str}] | Pos={pos_status} | Trades={bc._trades_today}"
        )

    def update_strategy_scores(self, scores: list[dict]) -> None:
        """Update strategy scores table.

        Args:
            scores: List of strategy score dicts
        """
        self.strategy_scores_table.setRowCount(len(scores))
        for row, score_data in enumerate(scores):
            self.strategy_scores_table.setItem(
                row, 0, QTableWidgetItem(score_data.get("name", "-"))
            )
            self.strategy_scores_table.setItem(
                row, 1, QTableWidgetItem(f"{score_data.get('score', 0):.2f}")
            )
            self.strategy_scores_table.setItem(
                row, 2, QTableWidgetItem(f"{score_data.get('profit_factor', 0):.2f}")
            )
            self.strategy_scores_table.setItem(
                row, 3, QTableWidgetItem(f"{score_data.get('win_rate', 0):.1%}")
            )
            self.strategy_scores_table.setItem(
                row, 4, QTableWidgetItem(f"{score_data.get('max_drawdown', 0):.1%}")
            )

    def update_walk_forward_results(self, results: dict) -> None:
        """Update walk-forward results display.

        Args:
            results: Walk-forward results dict
        """
        text = []
        if results:
            text.append(f"Training Window: {results.get('training_days', 'N/A')} days")
            text.append(f"Test Window: {results.get('test_days', 'N/A')} days")
            text.append(f"IS Profit Factor: {results.get('is_pf', 0):.2f}")
            text.append(f"OOS Profit Factor: {results.get('oos_pf', 0):.2f}")
            text.append(f"OOS Degradation: {results.get('degradation', 0):.1%}")
            text.append(f"Passed Gate: {'Yes' if results.get('passed', False) else 'No'}")
        self.wf_results_text.setText("\n".join(text))

    def log_ki_request(self, request: dict, response: dict | None = None) -> None:
        """Log a KI request/response pair.

        Args:
            request: Request data sent to KI
            response: Response received (if any)
        """
        self._add_ki_log_entry("REQUEST", f"Sent: {len(str(request))} chars")
        if response:
            if response.get("error"):
                self._add_ki_log_entry("ERROR", response["error"])
            else:
                action = response.get("action", "unknown")
                confidence = response.get("confidence", 0)
                self._add_ki_log_entry(
                    "RESPONSE",
                    f"Action: {action}, Confidence: {confidence:.2f}"
                )

        calls = int(self.ki_calls_today_label.text()) + 1
        self.ki_calls_today_label.setText(str(calls))
        self.ki_last_call_label.setText(datetime.now().strftime("%H:%M:%S"))
