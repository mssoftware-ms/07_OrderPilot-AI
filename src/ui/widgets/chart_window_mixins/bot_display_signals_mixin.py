from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QTableWidgetItem, QWidget

logger = logging.getLogger(__name__)

class BotDisplaySignalsMixin:
    """BotDisplaySignalsMixin extracted from BotDisplayManagerMixin."""
    def _get_signal_leverage(self, sig: dict) -> float:
        """Return persisted leverage for a signal, snapshotting once if missing (Issue #1)."""
        leverage = sig.get("leverage")
        if leverage is not None and leverage > 0:
            return float(leverage)

        # Snapshot current override once; afterwards value stays on the signal
        if hasattr(self, 'get_leverage_override'):
            enabled, value = self.get_leverage_override()
            if enabled and value > 0:
                leverage = float(value)
                sig["leverage"] = leverage
                return leverage

        # Fallback to derivative leverage if present
        deriv = sig.get("derivative")
        if deriv and deriv.get("leverage"):
            leverage = float(deriv["leverage"])
            sig["leverage"] = leverage
            return leverage

        sig["leverage"] = 1.0
        return 1.0
    def _update_signals_pnl(self) -> None:
        """Update P&L for all open signals in history."""
        # Use centralized price getter (prioritizes live tick)
        current_price = 0.0
        if hasattr(self, '_get_current_price'):
            current_price = self._get_current_price()
        
        # Fallback if _get_current_price not available (should not happen in mixin composition)
        if current_price <= 0:
            if self._bot_controller and self._bot_controller._last_features:
                current_price = self._bot_controller._last_features.close
            
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
                    leverage = self._get_signal_leverage(sig)

                    # Calculate P&L
                    if side.lower() == "long":
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    else:
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100

                    # Issue #1: Apply static leverage captured on signal
                    if leverage > 1:
                        pnl_pct = pnl_pct * leverage

                    # Issue #3: Subtract BitUnix fees from P&L
                    if hasattr(self, 'get_bitunix_fees'):
                        maker_fee, taker_fee = self.get_bitunix_fees()
                        # BitUnix Futures: both entry AND exit are market (taker) orders
                        total_fees_pct = taker_fee * 2
                        pnl_pct = pnl_pct - total_fees_pct
                        sig["fees_pct"] = total_fees_pct

                    if invested > 0:
                        pnl_currency = invested * (pnl_pct / 100)
                    elif quantity > 0:
                        pnl_currency = quantity * (current_price - entry_price) if side.lower() == "long" else quantity * (entry_price - current_price)
                        if leverage > 1:
                            pnl_currency = pnl_currency * leverage
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

        Column layout (23 columns):
        0: Time, 1: Type, 2: Strategy, 3: Side, 4: Entry, 5: Stop, 6: SL%, 7: TR%,
        8: TRA%, 9: TR Lock, 10: Status, 11: Current, 12: P&L %, 13: P&L USDT,
        14: Trading fees (USDT), 15: Fees €, 16: Stück, 17: D P&L € (hidden),
        18: D P&L % (hidden), 19: Hebel (visible), 20: WKN (hidden),
        21: Score (hidden), 22: TR Stop
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

        # Issue #1: Update leverage column visibility based on override state
        if hasattr(self, '_update_leverage_column_visibility'):
            self._update_leverage_column_visibility()

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

        # Strategy + parameters (Issue #7)
        strategy = signal.get("strategy", "-")
        strategy_params = []
        if "initial_sl_pct" in signal and signal.get("initial_sl_pct") is not None:
            strategy_params.append(f"SL={signal.get('initial_sl_pct',0):.2f}%")
        if "trailing_stop_pct" in signal and signal.get("trailing_stop_pct") is not None:
            strategy_params.append(f"TR={signal.get('trailing_stop_pct',0):.2f}%")
        if "trailing_activation_pct" in signal and signal.get("trailing_activation_pct") is not None:
            strategy_params.append(f"TRA={signal.get('trailing_activation_pct',0):.2f}%")
        strategy_text = strategy if not strategy_params else f"{strategy} | " + "; ".join(strategy_params)
        self.signals_table.setItem(row, 2, QTableWidgetItem(strategy_text))

        self.signals_table.setItem(row, 3, QTableWidgetItem(signal["side"]))
        self.signals_table.setItem(row, 4, QTableWidgetItem(f"{signal['price']:.4f}"))

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
            self.signals_table.setItem(row, 5, QTableWidgetItem(f"{stop_price:.2f}"))
        else:
            self.signals_table.setItem(row, 5, QTableWidgetItem("-"))

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
        self.signals_table.setItem(row, 6, sl_pct_item)

        if trailing_pct > 0:
            tr_pct_item = QTableWidgetItem(f"{trailing_pct:.2f}")
            tr_pct_item.setForeground(QColor("#ff9800"))
        else:
            tr_pct_item = QTableWidgetItem("-")
        if is_active:
            tr_pct_item.setFlags(tr_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.signals_table.setItem(row, 7, tr_pct_item)

        trailing_activation_pct = signal.get("trailing_activation_pct", 0.0)
        if trailing_activation_pct > 0:
            tra_item = QTableWidgetItem(f"{trailing_activation_pct:.2f}")
            if tr_is_active:
                tra_item.setForeground(QColor("#ff9800"))
            else:
                tra_item.setForeground(QColor("#888888"))
        else:
            tra_item = QTableWidgetItem("-")
        # Make TRA% editable for active positions
        if is_active:
            tra_item.setFlags(tra_item.flags() | Qt.ItemFlag.ItemIsEditable)
            tra_item.setToolTip("TRA%: Trailing Aktivierung ab X% Gewinn (editierbar)")
        self.signals_table.setItem(row, 8, tra_item)

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
            self.signals_table.setCellWidget(row, 9, lock_widget)
        else:
            self.signals_table.setItem(row, 9, QTableWidgetItem("-"))

        self.signals_table.setItem(row, 10, QTableWidgetItem(signal["status"]))

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
            entry_price = signal.get("price", 0)
            invested = signal.get("invested", 0)
            quantity = signal.get("quantity", 0)  # Issue #3: Added missing quantity definition
            side = signal.get("side", "long")

            # Issue #1: Use static leverage stored on the signal
            leverage = self._get_signal_leverage(signal)

            # Calculate base P&L
            if entry_price > 0 and current_price > 0:
                if side.lower() == "long":
                    pnl_percent = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_percent = ((entry_price - current_price) / entry_price) * 100

                # Issue #1: Apply leverage to P&L %
                pnl_percent = pnl_percent * leverage

                # Issue #3: Subtract BitUnix fees
                if hasattr(self, 'get_bitunix_fees'):
                    maker_fee, taker_fee = self.get_bitunix_fees()
                    # BitUnix Futures: entry and exit use taker fees
                    total_fees_pct = taker_fee * 2
                    pnl_percent = pnl_percent - total_fees_pct

                # Calculate P&L currency from adjusted percentage
                pnl_currency = invested * (pnl_percent / 100) if invested > 0 else 0
            else:
                pnl_currency = signal.get("pnl_currency", 0.0)
                pnl_percent = signal.get("pnl_percent", 0.0)

            if is_closed:
                exit_price = signal.get("exit_price", current_price)
                current_item = QTableWidgetItem(f"{exit_price:.2f}")
            else:
                current_item = QTableWidgetItem(f"{current_price:.2f}")
            self.signals_table.setItem(row, 11, current_item)

            # Issue #3: Calculate P&L USDT = (Entry - Current) * Hebel (for Long) or (Current - Entry) * Hebel (for Short)
            # P&L % = ((Entry - Current) / Entry * 100) * Hebel
            if entry_price > 0 and current_price > 0:
                if side.lower() == "long":
                    pnl_usdt = (current_price - entry_price) * leverage
                    pnl_pct_raw = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_usdt = (entry_price - current_price) * leverage
                    pnl_pct_raw = ((entry_price - current_price) / entry_price) * 100
                pnl_percent = pnl_pct_raw * leverage
            else:
                pnl_usdt = 0.0
                pnl_percent = 0.0

            # Issue #3: Column order changed - P&L % (12) first, then P&L USDT (13)
            # P&L % column (12) with color
            pnl_color = "#26a69a" if pnl_percent >= 0 else "#ef5350"
            pct_sign = "+" if pnl_percent >= 0 else ""
            pct_item = QTableWidgetItem(f"{pct_sign}{pnl_percent:.2f}%")
            pct_item.setForeground(QColor(pnl_color))
            self.signals_table.setItem(row, 12, pct_item)

            # P&L USDT column (13) with color
            pnl_usdt_color = "#26a69a" if pnl_usdt >= 0 else "#ef5350"
            pnl_sign = "+" if pnl_usdt >= 0 else ""
            pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_usdt:.2f}")
            pnl_item.setForeground(QColor(pnl_usdt_color))
            self.signals_table.setItem(row, 13, pnl_item)

            # Issue #6 & Issue #4: Calculate and display BitUnix fees
            # Fees are calculated on the leveraged position size (entry + exit taker)
            fees_usdt = 0.0
            maker_fee = 0.02  # Default 0.02% (not used for market orders)
            taker_fee = 0.06  # Default 0.06%
            position_size = invested * leverage
            if position_size <= 0 and quantity > 0 and current_price > 0:
                # Fallback: derive notional from quantity if invested is missing
                position_size = quantity * current_price * leverage
            entry_fee_euro = 0.0
            exit_fee_euro = 0.0

            if hasattr(self, 'get_bitunix_fees') and position_size > 0:
                maker_fee, taker_fee = self.get_bitunix_fees()
                # Both Entry and Exit use Taker fee (market orders for immediate execution)
                entry_fee_euro = position_size * (taker_fee / 100)
                exit_fee_euro = position_size * (taker_fee / 100)  # Exit also Taker!
                fees_usdt = entry_fee_euro + exit_fee_euro
                signal["fees_euro"] = fees_usdt

            # New column (14): Trading fees (USDT) using BitUnix fee settings
            trading_fees_item = QTableWidgetItem(f"{fees_usdt:.4f}")
            trading_fees_item.setForeground(QColor("#ff9800"))  # Orange for fees
            trading_fees_item.setToolTip(
                "Trading fees (BitUnix Futures)\n"
                f"Leverage-Notional: {position_size:.2f} USDT\n"
                f"Entry (Taker {taker_fee:.3f}%): {entry_fee_euro:.4f} USDT\n"
                f"Exit (Taker {taker_fee:.3f}%): {exit_fee_euro:.4f} USDT\n"
                f"Round-trip total: {fees_usdt:.4f} USDT"
            )
            self.signals_table.setItem(row, 14, trading_fees_item)

            # Legacy Fees € column (15) – mirror amount for compatibility
            fees_item = QTableWidgetItem(f"{fees_usdt:.2f}")
            fees_item.setForeground(QColor("#ff9800"))  # Orange for fees
            fees_item.setToolTip(trading_fees_item.toolTip())
            self.signals_table.setItem(row, 15, fees_item)

            # Stück / quantity column (16)
            qty_item = QTableWidgetItem(f"{quantity:.6f}" if quantity else "-")
            qty_item.setForeground(QColor("#cfd8dc"))
            self.signals_table.setItem(row, 16, qty_item)

            # Issue #1: Pass leverage to derivative columns (shifted by new Trading fees column)
            self._set_derivative_columns(row, signal, current_price, leverage)
            self.signals_table.setItem(row, 21, QTableWidgetItem(f"{signal['score'] * 100:.0f}"))
            self._set_tr_stop_column(row, trailing_price, tr_is_active)
        else:
            for col in range(11, 23):
                self.signals_table.setItem(row, col, QTableWidgetItem("-"))

    def _set_derivative_columns(self, row: int, signal: dict, current_price: float, leverage: float = 1.0) -> None:
        """Set derivative and leverage columns.

        Args:
            row: Table row index
            signal: Signal dictionary
            current_price: Current market price
            leverage: Leverage from Bot Tab override (Issue #1)

        Column indices (shifted by Trading fees at 14, Fees € at 15, Stück at 16):
        - 17: D P&L € (hidden)
        - 18: D P&L % (hidden)
        - 19: Hebel (VISIBLE - Issue #3)
        - 20: WKN (hidden)
        """
        deriv = signal.get("derivative")

        # Issue #1: Always set the leverage column (Heb - column 19)
        if leverage > 1.0:
            leverage_item = QTableWidgetItem(f"{leverage:.0f}x")
            leverage_item.setForeground(QColor("#2196f3"))  # Blue for manual leverage
            self.signals_table.setItem(row, 19, leverage_item)
        elif deriv and deriv.get("leverage", 0) > 0:
            self.signals_table.setItem(row, 19, QTableWidgetItem(f"{deriv['leverage']:.1f}"))
        else:
            self.signals_table.setItem(row, 19, QTableWidgetItem("-"))

        # Derivative P&L columns (shifted: 17, 18, 20)
        if deriv and current_price > 0 and hasattr(self, "_calculate_derivative_pnl_for_signal"):
            deriv_pnl = self._calculate_derivative_pnl_for_signal(signal, current_price)
            if deriv_pnl:
                d_pnl_sign = "+" if deriv_pnl["pnl_eur"] >= 0 else ""
                d_pnl_item = QTableWidgetItem(f"{d_pnl_sign}{deriv_pnl['pnl_eur']:.2f}")
                d_pnl_color = "#26a69a" if deriv_pnl["pnl_eur"] >= 0 else "#ef5350"
                d_pnl_item.setForeground(QColor(d_pnl_color))
                self.signals_table.setItem(row, 17, d_pnl_item)

                d_pct_sign = "+" if deriv_pnl["pnl_pct"] >= 0 else ""
                d_pct_item = QTableWidgetItem(f"{d_pct_sign}{deriv_pnl['pnl_pct']:.2f}%")
                d_pct_item.setForeground(QColor(d_pnl_color))
                self.signals_table.setItem(row, 18, d_pct_item)

                self.signals_table.setItem(row, 20, QTableWidgetItem(deriv["wkn"]))
                return
            self.signals_table.setItem(row, 17, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 20, QTableWidgetItem("-"))
        elif deriv:
            self.signals_table.setItem(row, 17, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 20, QTableWidgetItem(deriv.get("wkn", "-")))
        else:
            self.signals_table.setItem(row, 17, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 20, QTableWidgetItem("-"))

    def _set_tr_stop_column(self, row: int, trailing_price: float, tr_is_active: bool) -> None:
        """Set the TR Stop column (index 22, shifted due to added columns)."""
        if trailing_price > 0:
            if tr_is_active:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f}")
                tr_price_item.setForeground(QColor("#ff9800"))
            else:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f} (inaktiv)")
                tr_price_item.setForeground(QColor("#888888"))
            self.signals_table.setItem(row, 22, tr_price_item)
        else:
            self.signals_table.setItem(row, 22, QTableWidgetItem("-"))
