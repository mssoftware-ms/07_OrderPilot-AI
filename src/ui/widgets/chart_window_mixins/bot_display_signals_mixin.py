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
        # Get current price with fallbacks
        current_price = self._get_current_price_for_pnl()

        if current_price <= 0:
            return

        # Update P&L for all open signals
        table_updated = self._update_open_signals_pnl(current_price)

        if table_updated:
            self._update_signals_table()

    def _get_current_price_for_pnl(self) -> float:
        """Get current price for P&L calculation with multiple fallbacks.

        Returns:
            Current price, or 0.0 if not available.
        """
        # Primary: use centralized price getter (prioritizes live tick)
        if hasattr(self, '_get_current_price'):
            current_price = self._get_current_price()
            if current_price > 0:
                return current_price

        # Fallback 1: bot controller features
        if self._bot_controller and self._bot_controller._last_features:
            current_price = self._bot_controller._last_features.close
            if current_price > 0:
                return current_price

        # Fallback 2: chart widget data
        if hasattr(self, 'chart_widget'):
            if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                try:
                    return float(self.chart_widget.data['close'].iloc[-1])
                except Exception:
                    pass

        return 0.0

    def _update_open_signals_pnl(self, current_price: float) -> bool:
        """Update P&L for all open signals.

        Args:
            current_price: Current market price.

        Returns:
            True if any signal was updated, False otherwise.
        """
        table_updated = False

        for sig in self._signal_history:
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                entry_price = sig.get("price", 0)

                if entry_price > 0:
                    # Update signal with current price and P&L
                    self._update_single_signal_pnl(sig, entry_price, current_price)
                    table_updated = True

                    # Check trailing stop activation
                    self._check_tr_activation(sig, current_price)

        return table_updated

    def _update_single_signal_pnl(
        self, sig: dict, entry_price: float, current_price: float
    ) -> None:
        """Update P&L values for a single signal.

        Args:
            sig: Signal dictionary to update.
            entry_price: Entry price.
            current_price: Current market price.
        """
        sig["current_price"] = current_price

        quantity = sig.get("quantity", 0)
        invested = sig.get("invested", 0)
        side = sig.get("side", "long")

        # Calculate P&L with leverage and fees
        pnl_pct, leverage = self._calculate_pnl_with_adjustments(
            entry_price, current_price, side
        )

        # Calculate P&L in currency
        pnl_currency = self._calculate_pnl_currency(
            entry_price, current_price, invested, quantity, side, leverage, pnl_pct
        )

        # Store results in signal
        sig["pnl_currency"] = pnl_currency
        sig["pnl_percent"] = pnl_pct
        if leverage > 1:
            sig["leverage"] = leverage

    def _calculate_pnl_with_adjustments(
        self, entry_price: float, current_price: float, side: str
    ) -> tuple[float, float]:
        """Calculate P&L percentage with leverage and fees adjustments.

        Args:
            entry_price: Entry price.
            current_price: Current price.
            side: Trade side (long/short).

        Returns:
            Tuple of (adjusted_pnl_pct, leverage).
        """
        # Calculate base P&L
        if side.lower() == "long":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        # Issue #1: Apply manual leverage override if enabled
        leverage = 1.0
        if hasattr(self, 'get_leverage_override'):
            override_enabled, override_value = self.get_leverage_override()
            if override_enabled and override_value > 1:
                leverage = float(override_value)
                pnl_pct = pnl_pct * leverage

        # Issue #3: Subtract BitUnix fees from P&L
        if hasattr(self, 'get_bitunix_fees'):
            maker_fee, taker_fee = self.get_bitunix_fees()
            # BitUnix Futures: both entry AND exit are market (taker) orders
            total_fees_pct = taker_fee * 2
            pnl_pct = pnl_pct - total_fees_pct

        return pnl_pct, leverage

    def _calculate_pnl_currency(
        self, entry_price: float, current_price: float,
        invested: float, quantity: float, side: str,
        leverage: float, pnl_pct: float
    ) -> float:
        """Calculate P&L in currency.

        Args:
            entry_price: Entry price.
            current_price: Current price.
            invested: Invested amount.
            quantity: Position quantity.
            side: Trade side (long/short).
            leverage: Leverage factor.
            pnl_pct: P&L percentage (already adjusted).

        Returns:
            P&L in currency.
        """
        if invested > 0:
            return invested * (pnl_pct / 100)
        elif quantity > 0:
            if side.lower() == "long":
                pnl_currency = quantity * (current_price - entry_price)
            else:
                pnl_currency = quantity * (entry_price - current_price)

            if leverage > 1:
                pnl_currency = pnl_currency * leverage

            return pnl_currency
        else:
            return 0.0
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

        Column layout (21 columns):
        0: Time, 1: Type (dreistellige ID), 2: Strategy, 3: Side, 4: Entry, 5: Stop, 6: SL%, 7: TR%,
        8: TRA%, 9: TR Lock, 10: Status, 11: Current, 12: P&L %, 13: P&L USDT,
        14: Fees USDT (Issue #6: BitUnix fees in USDT),
        15: D P&L USDT (hidden), 16: D P&L % (hidden), 17: Heb (hidden), 18: WKN (hidden),
        19: Score (hidden), 20: TR Stop (visible - orange when active, gray when inactive)
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
        # Column 0: Time
        self.signals_table.setItem(row, 0, QTableWidgetItem(signal["time"]))

        # Column 1: Type (dreistellige fortlaufende ID)
        signal_id = signal.get("signal_id", 0)
        type_item = QTableWidgetItem(f"{signal_id:03d}")  # Dreistelliges Format: 001, 002, ...
        type_item.setForeground(QColor("#26a69a"))
        self.signals_table.setItem(row, 1, type_item)

        # Column 2: Strategy (neu!)
        strategy_details = signal.get("strategy_details", signal.get("strategy", ""))
        strategy_item = QTableWidgetItem(strategy_details if strategy_details else "-")
        self.signals_table.setItem(row, 2, strategy_item)

        # Column 3: Side (vorher 2)
        self.signals_table.setItem(row, 3, QTableWidgetItem(signal["side"]))

        # Column 4: Entry (vorher 3)
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
        # Column 5: Stop (vorher 4)
        if stop_price > 0:
            self.signals_table.setItem(row, 5, QTableWidgetItem(f"{stop_price:.2f}"))
        else:
            self.signals_table.setItem(row, 5, QTableWidgetItem("-"))

        # Column 6: SL% (vorher 5)
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

        # Column 7: TR% (vorher 6)
        if trailing_pct > 0:
            tr_pct_item = QTableWidgetItem(f"{trailing_pct:.2f}")
            tr_pct_item.setForeground(QColor("#ff9800"))
        else:
            tr_pct_item = QTableWidgetItem("-")
        if is_active:
            tr_pct_item.setFlags(tr_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.signals_table.setItem(row, 7, tr_pct_item)

        # Column 8: TRA% (vorher 7)
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
            # Column 9: TR Lock (vorher 8)
            self.signals_table.setCellWidget(row, 9, lock_widget)
        else:
            self.signals_table.setItem(row, 9, QTableWidgetItem("-"))

        # Column 10: Status (vorher 9)
        self.signals_table.setItem(row, 10, QTableWidgetItem(signal["status"]))

    def _set_status_and_pnl_columns(
        self,
        row: int,
        signal: dict,
        trailing_price: float,
        tr_is_active: bool,
    ) -> None:
        # Check if signal has data to display
        if not self._should_display_signal_pnl(signal):
            # Fill remaining columns with "-" (Issue #5: Now up to column 22)
            for col in range(11, 22):
                self.signals_table.setItem(row, col, QTableWidgetItem("-"))
            return

        # Get signal data and calculate P&L
        signal_data = self._get_signal_display_data(signal)

        # Set display columns
        self._set_current_price_column(row, signal, signal_data)
        self._set_pnl_columns(row, signal_data)
        self._set_fees_column(row, signal_data)
        self._set_quantity_column(row, signal, signal_data)  # Issue #5: Gekaufte Stückzahl
        self._set_derivative_columns(row, signal, signal_data["current_price"], signal_data["leverage"])
        self.signals_table.setItem(row, 20, QTableWidgetItem(f"{signal['score'] * 100:.0f}"))  # Score moved to col 20
        self._set_tr_stop_column(row, trailing_price, tr_is_active)

    def _should_display_signal_pnl(self, signal: dict) -> bool:
        """Check if signal has data worth displaying.

        Args:
            signal: Signal dictionary.

        Returns:
            True if signal should display P&L data.
        """
        has_quantity = signal.get("quantity", 0) > 0
        has_invested = signal.get("invested", 0) > 0
        status = signal["status"]
        is_closed = status.startswith("CLOSED") or status in ("SL", "TR", "MACD", "RSI", "Sell")
        is_entered = status == "ENTERED" and signal.get("is_open", False)
        has_derivative = signal.get("derivative") is not None

        return has_quantity or has_invested or is_entered or is_closed or has_derivative

    def _get_signal_display_data(self, signal: dict) -> dict:
        """Get calculated data for signal display.

        Args:
            signal: Signal dictionary.

        Returns:
            Dictionary with current_price, entry_price, invested, side, leverage,
            pnl_percent, pnl_currency, fees_euro, position_size, taker_fee.
        """
        current_price = signal.get("current_price", signal["price"])
        entry_price = signal.get("price", 0)
        invested = signal.get("invested", 0)
        side = signal.get("side", "long")

        # Get static leverage (frozen at entry)
        leverage = self._get_signal_leverage(signal)

        # Calculate P&L
        pnl_percent, pnl_currency = self._calculate_display_pnl(
            entry_price, current_price, invested, side, leverage, signal
        )

        # Calculate fees
        fees_data = self._calculate_signal_fees(invested, leverage)

        return {
            "current_price": current_price,
            "entry_price": entry_price,
            "invested": invested,
            "side": side,
            "leverage": leverage,
            "pnl_percent": pnl_percent,
            "pnl_currency": pnl_currency,
            "fees_euro": fees_data["fees_euro"],
            "position_size": fees_data["position_size"],
            "taker_fee": fees_data["taker_fee"],
            "entry_fee_euro": fees_data["entry_fee_euro"],
            "exit_fee_euro": fees_data["exit_fee_euro"],
        }

    def _get_signal_leverage(self, signal: dict) -> float:
        """Get leverage for signal (prefer static, fallback to current).

        Args:
            signal: Signal dictionary.

        Returns:
            Leverage value.
        """
        # Issue #1: Use STATIC leverage from entry
        leverage = signal.get("leverage_at_entry", 1.0)

        # If no static leverage was saved (old signals), fall back to current UI value
        if leverage is None or leverage <= 0:
            leverage = 1.0
            if hasattr(self, 'get_leverage_override'):
                override_enabled, override_value = self.get_leverage_override()
                if override_enabled and override_value > 1:
                    leverage = float(override_value)

        return leverage

    def _calculate_display_pnl(
        self, entry_price: float, current_price: float,
        invested: float, side: str, leverage: float, signal: dict
    ) -> tuple[float, float]:
        """Calculate P&L for display with leverage and fees.

        Args:
            entry_price: Entry price.
            current_price: Current price.
            invested: Invested amount.
            side: Trade side.
            leverage: Leverage factor.
            signal: Signal dictionary (for fallback values).

        Returns:
            Tuple of (pnl_percent, pnl_currency).
        """
        if entry_price > 0 and current_price > 0:
            # Calculate base P&L
            if side.lower() == "long":
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_percent = ((entry_price - current_price) / entry_price) * 100

            # Issue #1: Apply leverage to P&L %
            pnl_percent = pnl_percent * leverage

            # Issue #3: Subtract BitUnix fees
            if hasattr(self, 'get_bitunix_fees'):
                maker_fee, taker_fee = self.get_bitunix_fees()
                total_fees_pct = taker_fee * 2
                pnl_percent = pnl_percent - total_fees_pct

            # Calculate P&L currency from adjusted percentage
            pnl_currency = invested * (pnl_percent / 100) if invested > 0 else 0
        else:
            # Fallback to stored values
            pnl_currency = signal.get("pnl_currency", 0.0)
            pnl_percent = signal.get("pnl_percent", 0.0)

        return pnl_percent, pnl_currency

    def _calculate_signal_fees(self, invested: float, leverage: float) -> dict:
        """Calculate BitUnix fees for signal display.

        Args:
            invested: Invested amount.
            leverage: Leverage factor.

        Returns:
            Dictionary with fees_euro, position_size, taker_fee, entry_fee_euro, exit_fee_euro.
        """
        # Issue #6: Calculate BitUnix fees on leveraged position
        position_size = invested * leverage
        fees_euro = 0.0
        taker_fee = 0.06  # Default 0.06%
        entry_fee_euro = 0.0
        exit_fee_euro = 0.0

        if hasattr(self, 'get_bitunix_fees') and invested > 0:
            maker_fee, taker_fee = self.get_bitunix_fees()
            # Both Entry and Exit use Taker fee (market orders)
            entry_fee_euro = position_size * (taker_fee / 100)
            exit_fee_euro = position_size * (taker_fee / 100)
            fees_euro = entry_fee_euro + exit_fee_euro

        return {
            "fees_euro": fees_euro,
            "position_size": position_size,
            "taker_fee": taker_fee,
            "entry_fee_euro": entry_fee_euro,
            "exit_fee_euro": exit_fee_euro,
        }

    def _set_current_price_column(self, row: int, signal: dict, signal_data: dict) -> None:
        """Set current price column (Column 11).

        Args:
            row: Table row.
            signal: Signal dictionary.
            signal_data: Calculated signal data.
        """
        status = signal["status"]
        is_closed = status.startswith("CLOSED") or status in ("SL", "TR", "MACD", "RSI", "Sell")

        if is_closed:
            exit_price = signal.get("exit_price", signal_data["current_price"])
            current_item = QTableWidgetItem(f"{exit_price:.2f}")
        else:
            current_item = QTableWidgetItem(f"{signal_data['current_price']:.2f}")

        self.signals_table.setItem(row, 11, current_item)

    def _set_pnl_columns(self, row: int, signal_data: dict) -> None:
        """Set P&L percentage and currency columns (Columns 12, 13).

        Args:
            row: Table row.
            signal_data: Calculated signal data.
        """
        pnl_percent = signal_data["pnl_percent"]
        pnl_currency = signal_data["pnl_currency"]
        pnl_color = "#26a69a" if pnl_currency >= 0 else "#ef5350"

        # Column 12: P&L %
        pct_sign = "+" if pnl_percent >= 0 else ""
        pct_item = QTableWidgetItem(f"{pct_sign}{pnl_percent:.2f}%")
        pct_item.setForeground(QColor(pnl_color))
        self.signals_table.setItem(row, 12, pct_item)

        # Column 13: P&L USDT
        pnl_sign = "+" if pnl_currency >= 0 else ""
        pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_currency:.2f}")
        pnl_item.setForeground(QColor(pnl_color))
        self.signals_table.setItem(row, 13, pnl_item)

    def _set_fees_column(self, row: int, signal_data: dict) -> None:
        """Set fees column with tooltip (Column 14).

        Args:
            row: Table row.
            signal_data: Calculated signal data.
        """
        fees_euro = signal_data["fees_euro"]
        position_size = signal_data["position_size"]
        taker_fee = signal_data["taker_fee"]
        entry_fee_euro = signal_data["entry_fee_euro"]
        exit_fee_euro = signal_data["exit_fee_euro"]

        fees_item = QTableWidgetItem(f"{fees_euro:.2f}")
        fees_item.setForeground(QColor("#ff9800"))  # Orange for fees
        fees_item.setToolTip(
            f"BitUnix Futures Gebühren (beide Taker)\n"
            f"Positionsgröße mit Hebel: {position_size:.2f} USDT\n"
            f"Entry (Taker {taker_fee:.3f}%): {entry_fee_euro:.2f} USDT\n"
            f"Exit (Taker {taker_fee:.3f}%): {exit_fee_euro:.2f} USDT\n"
            f"Gesamt: {fees_euro:.2f} USDT"
        )
        self.signals_table.setItem(row, 14, fees_item)

    def _set_quantity_column(self, row: int, signal: dict, signal_data: dict) -> None:
        """Set quantity column (gekaufte Stückzahl) - Column 15 (Issue #5).

        Args:
            row: Table row.
            signal: Signal dictionary.
            signal_data: Calculated signal data.
        """
        quantity = signal.get("quantity", 0)
        invested = signal_data.get("invested", 0)
        entry_price = signal_data.get("entry_price", 0)

        # Calculate quantity if not stored
        if quantity <= 0 and invested > 0 and entry_price > 0:
            quantity = invested / entry_price

        if quantity > 0:
            # Format quantity based on asset type (crypto vs stocks)
            if quantity < 1:
                # Crypto (fractional amounts)
                quantity_text = f"{quantity:.6f}".rstrip('0').rstrip('.')
            else:
                # Stocks or larger amounts
                quantity_text = f"{quantity:.2f}"

            quantity_item = QTableWidgetItem(quantity_text)
            quantity_item.setForeground(QColor("#2196f3"))  # Blue
            quantity_item.setToolTip(
                f"Gekaufte Stückzahl: {quantity:.8f}\n"
                f"Eingesetztes Kapital: {invested:.2f} USDT\n"
                f"Entry-Preis: {entry_price:.4f} USDT"
            )
            self.signals_table.setItem(row, 15, quantity_item)
        else:
            self.signals_table.setItem(row, 15, QTableWidgetItem("-"))

    def _set_derivative_columns(self, row: int, signal: dict, current_price: float, leverage: float = 1.0) -> None:
        """Set derivative and leverage columns.

        Args:
            row: Table row index
            signal: Signal dictionary
            current_price: Current market price
            leverage: Leverage from Bot Tab override (Issue #1)

        Column indices (Issue #5: With "Stück" column added):
        - 16: D P&L USDT (hidden)
        - 17: D P&L % (hidden)
        - 18: Heb (hidden)
        - 19: WKN (hidden)
        """
        deriv = signal.get("derivative")

        # Column 18: Heb (Issue #5: moved from 17)
        # Use static leverage from signal (frozen at entry), not current UI value
        signal_leverage = signal.get("leverage_at_entry")

        if signal_leverage and signal_leverage > 1.0:
            leverage_item = QTableWidgetItem(f"{signal_leverage:.0f}x")
            leverage_item.setForeground(QColor("#2196f3"))  # Blue for static leverage
            leverage_item.setToolTip(f"Hebel beim Entry: {signal_leverage:.0f}x (statisch)")
            self.signals_table.setItem(row, 18, leverage_item)
        elif leverage > 1.0:
            # Fallback for old signals without saved leverage
            leverage_item = QTableWidgetItem(f"{leverage:.0f}x")
            leverage_item.setForeground(QColor("#ff9800"))  # Orange for fallback
            leverage_item.setToolTip(f"Hebel (aus Bot-Tab): {leverage:.0f}x")
            self.signals_table.setItem(row, 18, leverage_item)
        elif deriv and deriv.get("leverage", 0) > 0:
            self.signals_table.setItem(row, 18, QTableWidgetItem(f"{deriv['leverage']:.1f}"))
        else:
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))

        # Derivative P&L columns (Issue #5: columns 16, 17, 19)
        if deriv and current_price > 0 and hasattr(self, "_calculate_derivative_pnl_for_signal"):
            deriv_pnl = self._calculate_derivative_pnl_for_signal(signal, current_price)
            if deriv_pnl:
                # Column 16: D P&L USDT
                d_pnl_sign = "+" if deriv_pnl["pnl_eur"] >= 0 else ""
                d_pnl_item = QTableWidgetItem(f"{d_pnl_sign}{deriv_pnl['pnl_eur']:.2f}")
                d_pnl_color = "#26a69a" if deriv_pnl["pnl_eur"] >= 0 else "#ef5350"
                d_pnl_item.setForeground(QColor(d_pnl_color))
                self.signals_table.setItem(row, 16, d_pnl_item)

                # Column 17: D P&L %
                d_pct_sign = "+" if deriv_pnl["pnl_pct"] >= 0 else ""
                d_pct_item = QTableWidgetItem(f"{d_pct_sign}{deriv_pnl['pnl_pct']:.2f}%")
                d_pct_item.setForeground(QColor(d_pnl_color))
                self.signals_table.setItem(row, 17, d_pct_item)

                # Column 19: WKN
                self.signals_table.setItem(row, 19, QTableWidgetItem(deriv["wkn"]))
                return
            self.signals_table.setItem(row, 16, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 17, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 19, QTableWidgetItem("-"))
        elif deriv:
            self.signals_table.setItem(row, 15, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 16, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 18, QTableWidgetItem(deriv.get("wkn", "-")))
        else:
            self.signals_table.setItem(row, 15, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 16, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))

    def _set_tr_stop_column(self, row: int, trailing_price: float, tr_is_active: bool) -> None:
        """Set the TR Stop column (Column 21, Issue #5: moved from 20)."""
        if trailing_price > 0:
            if tr_is_active:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f}")
                tr_price_item.setForeground(QColor("#ff9800"))
            else:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f} (inaktiv)")
                tr_price_item.setForeground(QColor("#888888"))
            # Column 21: TR Stop (Issue #5: moved from 20)
            self.signals_table.setItem(row, 21, tr_price_item)
        else:
            self.signals_table.setItem(row, 21, QTableWidgetItem("-"))
