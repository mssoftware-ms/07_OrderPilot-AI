from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QTableWidgetItem, QWidget

from src.ui.widgets.column_updaters import (
    ColumnUpdaterRegistry,
    CurrentPriceUpdater,
    FeesPercentUpdater,
    FeesCurrencyUpdater,
    InvestUpdater,
    LiquidationUpdater,
    PnLPercentUpdater,
    PnLCurrencyUpdater,
    QuantityUpdater,
)

logger = logging.getLogger(__name__)

class BotDisplaySignalsMixin:
    """BotDisplaySignalsMixin extracted from BotDisplayManagerMixin."""

    def _init_column_registry(self) -> None:
        """Initialize column updater registry (lazy initialization)."""
        self._column_registry = ColumnUpdaterRegistry()
        self._column_registry.register(CurrentPriceUpdater())
        self._column_registry.register(PnLPercentUpdater())
        self._column_registry.register(PnLCurrencyUpdater())
        self._column_registry.register(FeesPercentUpdater())
        self._column_registry.register(FeesCurrencyUpdater())
        self._column_registry.register(InvestUpdater())
        self._column_registry.register(QuantityUpdater())
        self._column_registry.register(LiquidationUpdater())

    def _make_non_editable(self, item: QTableWidgetItem) -> None:
        """Remove editable flag from a table item."""
        if item:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

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
        """Update P&L for all open signals in history.

        Issue #12: Use centralized _get_current_price for consistent price source.
        """
        # Use centralized price getter (prioritizes live tick, then streaming, then historical)
        current_price = 0.0
        if hasattr(self, '_get_current_price'):
            current_price = self._get_current_price()

        # Fallback if _get_current_price not available (should not happen in mixin composition)
        if current_price <= 0:
            # Check chart widget's streaming price first (Issue #12)
            if hasattr(self, 'chart_widget'):
                if hasattr(self.chart_widget, '_last_price') and self.chart_widget._last_price > 0:
                    current_price = float(self.chart_widget._last_price)

            # Then try bot controller features
            if current_price <= 0 and self._bot_controller and self._bot_controller._last_features:
                current_price = self._bot_controller._last_features.close

            # Finally fall back to DataFrame
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
            if sig.get("status") == "ENTERED" and sig.get("is_open") is not False:
                entry_price = sig.get("price", 0)
                quantity = sig.get("quantity", 0)
                invested = sig.get("invested", 0)
                side = sig.get("side", "long")

                if entry_price > 0:
                    sig["current_price"] = current_price
                    leverage = self._get_signal_leverage(sig)

                    # Calculate RAW P&L (without leverage)
                    if side.lower() == "long":
                        raw_pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    else:
                        raw_pnl_pct = ((entry_price - current_price) / entry_price) * 100

                    # Issue #10: Store RAW P&L for Current Position display (WITHOUT leverage)
                    raw_pnl_currency = invested * (raw_pnl_pct / 100) if invested > 0 else 0
                    sig["pnl_percent_raw"] = raw_pnl_pct
                    sig["pnl_currency_raw"] = raw_pnl_currency

                    # Issue #1: Apply static leverage captured on signal for Trading Table
                    pnl_pct = raw_pnl_pct
                    if leverage > 1:
                        pnl_pct = pnl_pct * leverage

                    # Issue #3: Subtract BitUnix fees from P&L (leveraged)
                    if hasattr(self, 'get_bitunix_fees'):
                        maker_fee, taker_fee = self.get_bitunix_fees()
                        # BitUnix Futures: both entry AND exit are market (taker) orders
                        total_fees_pct = taker_fee * 2
                        pnl_pct = pnl_pct - total_fees_pct
                        sig["fees_pct"] = total_fees_pct

                    # Issue #10: pnl_currency and pnl_percent include leverage for Trading Table
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

        Column layout (24 columns):
        0: Time, 1: Type, 2: Strategy, 3: Side, 4: Entry, 5: Stop, 6: SL%, 7: TR%,
        8: TRA%, 9: TR Lock, 10: Status, 11: Current, 12: P&L %, 13: P&L USDT,
        14: Trading fees % , 15: Trading fees (USDT), 16: Invest, 17: Stück,
        18: D P&L € (hidden), 19: D P&L % (hidden), 20: Hebel (visible),
        21: WKN (hidden), 22: Score (hidden), 23: TR Stop
        """
        self._signals_table_updating = True

        recent_signals = list(reversed(self._signal_history[-20:]))
        self.signals_table.setRowCount(len(recent_signals))

        for row, signal in enumerate(recent_signals):
            stop_price = signal.get("stop_price", 0.0)
            entry_price = signal.get("price", 0)
            is_open = signal.get("is_open")
            is_active = signal.get("status") == "ENTERED" and (is_open is not False)
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
        is_open = signal.get("is_open")
        is_active = signal.get("status") == "ENTERED" and (is_open is not False)

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

        # Issue #3: Entry price editable for active positions
        entry_item = QTableWidgetItem(f"{signal['price']:.4f}")
        if is_active:
            entry_item.setFlags(entry_item.flags() | Qt.ItemFlag.ItemIsEditable)
            entry_item.setToolTip("Entry-Preis (editierbar für aktive Position)")
        self.signals_table.setItem(row, 4, entry_item)

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
        # Issue #3: Stop price editable for active positions
        if stop_price > 0:
            stop_item = QTableWidgetItem(f"{stop_price:.2f}")
        else:
            stop_item = QTableWidgetItem("-")
        if is_active:
            stop_item.setFlags(stop_item.flags() | Qt.ItemFlag.ItemIsEditable)
            stop_item.setToolTip("Stop-Preis (editierbar für aktive Position)")
        self.signals_table.setItem(row, 5, stop_item)

        # Issue #20: For ENTERED positions, use ONLY stored values - no recalculation!
        initial_sl_pct = signal.get("initial_sl_pct", 0.0)
        if is_active:
            # ENTERED: Use stored value, never recalculate
            if initial_sl_pct > 0:
                sl_pct_item = QTableWidgetItem(f"{initial_sl_pct:.2f}")
                sl_pct_item.setForeground(QColor("#ef5350"))
            else:
                sl_pct_item = QTableWidgetItem("-")
            sl_pct_item.setFlags(sl_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
            sl_pct_item.setToolTip("SL%: Stop Loss Prozent vom Entry (editierbar, Enter zum Speichern)")
        else:
            # Not active: can calculate fallback
            if initial_sl_pct > 0:
                sl_pct_item = QTableWidgetItem(f"{initial_sl_pct:.2f}")
                sl_pct_item.setForeground(QColor("#ef5350"))
            elif entry_price > 0 and stop_price > 0:
                calculated_sl_pct = abs((stop_price - entry_price) / entry_price) * 100
                sl_pct_item = QTableWidgetItem(f"{calculated_sl_pct:.2f}")
                sl_pct_item.setForeground(QColor("#ef5350"))
            else:
                sl_pct_item = QTableWidgetItem("-")
        self.signals_table.setItem(row, 6, sl_pct_item)

        # Issue #20: For ENTERED positions, use ONLY stored trailing_stop_pct - no recalculation!
        stored_tr_pct = signal.get("trailing_stop_pct", 0.0)
        if is_active:
            # ENTERED: Use stored value only, ignore calculated trailing_pct parameter
            if stored_tr_pct > 0:
                tr_pct_item = QTableWidgetItem(f"{stored_tr_pct:.2f}")
                tr_pct_item.setForeground(QColor("#ff9800"))
            else:
                tr_pct_item = QTableWidgetItem("-")
            tr_pct_item.setFlags(tr_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
            tr_pct_item.setToolTip("TR%: Trailing Stop Prozent vom Entry (editierbar, Enter zum Speichern)")
        else:
            # Not active: use calculated or stored value
            display_tr_pct = stored_tr_pct if stored_tr_pct > 0 else trailing_pct
            if display_tr_pct > 0:
                tr_pct_item = QTableWidgetItem(f"{display_tr_pct:.2f}")
                tr_pct_item.setForeground(QColor("#ff9800"))
            else:
                tr_pct_item = QTableWidgetItem("-")
        self.signals_table.setItem(row, 7, tr_pct_item)

        # Issue #20: For ENTERED positions, use ONLY stored trailing_activation_pct - static value
        trailing_activation_pct = signal.get("trailing_activation_pct", 0.0)
        if is_active:
            # ENTERED: Use stored value only, make editable
            if trailing_activation_pct > 0:
                tra_item = QTableWidgetItem(f"{trailing_activation_pct:.2f}")
                if tr_is_active:
                    tra_item.setForeground(QColor("#ff9800"))
                else:
                    tra_item.setForeground(QColor("#888888"))
            else:
                tra_item = QTableWidgetItem("-")
            tra_item.setFlags(tra_item.flags() | Qt.ItemFlag.ItemIsEditable)
            tra_item.setToolTip("TRA%: Trailing Aktivierung ab X% Gewinn (editierbar, Enter zum Speichern)")
        else:
            # Not active: display only
            if trailing_activation_pct > 0:
                tra_item = QTableWidgetItem(f"{trailing_activation_pct:.2f}")
                tra_item.setForeground(QColor("#888888"))
            else:
                tra_item = QTableWidgetItem("-")
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
        """Update status and P&L columns using Column Updater Pattern.

        Delegates column updates to specialized updaters for clean separation of concerns.
        """
        # Initialize registry on first use
        if not hasattr(self, '_column_registry'):
            self._init_column_registry()

        # Get leverage for display (used even without full P&L calculations)
        leverage = self._get_signal_leverage(signal)
        current_price = signal.get("current_price", signal.get("price", 0))

        # Check if this signal should have full P&L data
        if self._should_display_pnl(signal):
            # Build context with all calculated values
            context = self._build_pnl_context(signal)

            # Use updaters for columns 11-17, 24 (delegated updates)
            for column in [11, 12, 13, 14, 15, 16, 17, 24]:
                self._column_registry.update(
                    self.signals_table,
                    row,
                    column,
                    signal,
                    context
                )

            # Use context leverage for derivative columns
            leverage = context.get("leverage", leverage)
            current_price = context.get("current_price", current_price)
        else:
            # Set empty P&L columns only (11-17, 24) but NOT derivative/tr columns
            for col in [11, 12, 13, 14, 15, 16, 17, 24]:
                self.signals_table.setItem(row, col, QTableWidgetItem("-"))

        # ALWAYS set these columns regardless of P&L status:
        # - Derivative columns (18, 19, 20, 21)
        # - Score (22)
        # - TR Stop (23)
        self._set_derivative_columns(row, signal, current_price, leverage)
        self.signals_table.setItem(row, 22, QTableWidgetItem(f"{signal.get('score', 0) * 100:.0f}"))
        self._set_tr_stop_column(row, trailing_price, tr_is_active)

    def _should_display_pnl(self, signal: dict) -> bool:
        """Check if signal should display P&L data."""
        has_quantity = signal.get("quantity", 0) > 0
        has_invested = signal.get("invested", 0) > 0
        status = signal.get("status", "")
        is_closed = status.startswith("CLOSED") or status in ("SL", "TR", "MACD", "RSI", "Sell")
        is_entered = status == "ENTERED" and signal.get("is_open") is not False
        has_derivative = signal.get("derivative") is not None
        result = has_quantity or has_invested or is_entered or is_closed or has_derivative

        # Debug logging for calculation issues
        if not result:
            logger.debug(
                f"_should_display_pnl=False: qty={signal.get('quantity', 0)}, "
                f"invested={signal.get('invested', 0)}, status={status}, "
                f"is_open={signal.get('is_open')}, deriv={has_derivative}"
            )

        return result

    def _build_pnl_context(self, signal: dict) -> dict:
        """Build context dictionary with all P&L calculations.

        Returns:
            Context dict with all values needed for column updates
        """
        current_price = signal.get("current_price", signal["price"])
        entry_price = signal.get("price", 0)
        invested = signal.get("invested", 0)
        side = signal.get("side", "long")
        leverage = self._get_signal_leverage(signal)

        # Get fees
        maker_fee, taker_fee = 0.02, 0.06
        if hasattr(self, 'get_bitunix_fees'):
            maker_fee, taker_fee = self.get_bitunix_fees()
        fees_pct_leveraged = (maker_fee + taker_fee) * leverage

        # Calculate quantity
        quantity = signal.get("quantity", 0)
        if invested > 0 and entry_price > 0:
            quantity = (invested * leverage) / entry_price

        # Calculate P&L
        pnl_pct_raw, pnl_percent, pnl_usdt = self._calculate_pnl(
            entry_price, current_price, invested, side, leverage, fees_pct_leveraged, signal
        )

        # Calculate fees
        position_size = invested * leverage
        if position_size <= 0 and quantity > 0 and current_price > 0:
            position_size = quantity * current_price * leverage

        entry_fee_euro = position_size * (taker_fee / 100) if position_size > 0 else 0
        exit_fee_euro = position_size * (taker_fee / 100) if position_size > 0 else 0
        fees_usdt = entry_fee_euro + exit_fee_euro
        if fees_usdt > 0:
            signal["fees_euro"] = fees_usdt

        # Calculate liquidation
        mm_rate, mm_rate_default = self._resolve_maintenance_margin_rate(signal)
        liquidation_price, margin_buffer = self._calculate_liquidation(
            entry_price, invested, leverage, quantity, position_size, mm_rate, side
        )

        return {
            "current_price": current_price,
            "entry_price": entry_price,
            "invested": invested,
            "side": side,
            "leverage": leverage,
            "maker_fee": maker_fee,
            "taker_fee": taker_fee,
            "fees_pct_leveraged": fees_pct_leveraged,
            "quantity": quantity,
            "pnl_pct_raw": pnl_pct_raw,
            "pnl_percent": pnl_percent,
            "pnl_usdt": pnl_usdt,
            "position_size": position_size,
            "entry_fee_euro": entry_fee_euro,
            "exit_fee_euro": exit_fee_euro,
            "fees_usdt": fees_usdt,
            "liquidation_price": liquidation_price,
            "margin_buffer": margin_buffer,
            "mm_rate": mm_rate,
            "mm_rate_default": mm_rate_default,
        }

    def _calculate_pnl(
        self,
        entry_price: float,
        current_price: float,
        invested: float,
        side: str,
        leverage: float,
        fees_pct_leveraged: float,
        signal: dict,
    ) -> tuple[float, float, float]:
        """Calculate P&L values."""
        if entry_price > 0 and current_price > 0:
            if side.lower() == "long":
                pnl_pct_raw = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct_raw = ((entry_price - current_price) / entry_price) * 100

            pnl_percent = (pnl_pct_raw * leverage) - fees_pct_leveraged
            pnl_usdt = invested * (pnl_percent / 100) if invested > 0 else 0.0
        else:
            pnl_pct_raw = 0.0
            pnl_percent = signal.get("pnl_percent", 0.0)
            pnl_usdt = signal.get("pnl_currency", 0.0)

        return pnl_pct_raw, pnl_percent, pnl_usdt

    def _calculate_liquidation(
        self,
        entry_price: float,
        invested: float,
        leverage: float,
        quantity: float,
        position_size: float,
        mm_rate: float,
        side: str,
    ) -> tuple[float | None, float | None]:
        """Calculate liquidation price and margin buffer."""
        liquidation_price = None
        margin_buffer = None

        if entry_price > 0 and invested > 0 and leverage > 0 and quantity > 0:
            maintenance_margin = position_size * mm_rate
            margin_buffer = invested - maintenance_margin
            if margin_buffer > 0:
                price_distance = margin_buffer / quantity
                if side.lower() == "short":
                    liquidation_price = entry_price + price_distance
                else:
                    liquidation_price = entry_price - price_distance

        return liquidation_price, margin_buffer

    def _set_empty_columns(self, row: int) -> None:
        """Set empty columns for signals without P&L data."""
        for col in range(11, 25):
            self.signals_table.setItem(row, col, QTableWidgetItem("-"))

    def _set_derivative_columns(self, row: int, signal: dict, current_price: float, leverage: float = 1.0) -> None:
        """Set derivative and leverage columns.

        Args:
            row: Table row index
            signal: Signal dictionary
            current_price: Current market price
            leverage: Leverage from Bot Tab override (Issue #1)

        Column indices (shifted by Trading fees % at 14, Trading fees USDT at 15):
        - 18: D P&L € (hidden)
        - 19: D P&L % (hidden)
        - 20: Hebel (VISIBLE - Issue #3)
        - 21: WKN (hidden)
        """
        deriv = signal.get("derivative")

        # Issue #1: Always set the leverage column (Heb - column 20)
        if leverage > 1.0:
            leverage_item = QTableWidgetItem(f"{leverage:.0f}x")
            leverage_item.setForeground(QColor("#2196f3"))  # Blue for manual leverage
            self.signals_table.setItem(row, 20, leverage_item)
        elif deriv and deriv.get("leverage", 0) > 0:
            self.signals_table.setItem(row, 20, QTableWidgetItem(f"{deriv['leverage']:.1f}"))
        else:
            self.signals_table.setItem(row, 20, QTableWidgetItem("-"))

        # Derivative P&L columns (shifted: 18, 19, 21)
        if deriv and current_price > 0 and hasattr(self, "_calculate_derivative_pnl_for_signal"):
            deriv_pnl = self._calculate_derivative_pnl_for_signal(signal, current_price)
            if deriv_pnl:
                d_pnl_sign = "+" if deriv_pnl["pnl_eur"] >= 0 else ""
                d_pnl_item = QTableWidgetItem(f"{d_pnl_sign}{deriv_pnl['pnl_eur']:.2f}")
                d_pnl_color = "#26a69a" if deriv_pnl["pnl_eur"] >= 0 else "#ef5350"
                d_pnl_item.setForeground(QColor(d_pnl_color))
                self.signals_table.setItem(row, 18, d_pnl_item)

                d_pct_sign = "+" if deriv_pnl["pnl_pct"] >= 0 else ""
                d_pct_item = QTableWidgetItem(f"{d_pct_sign}{deriv_pnl['pnl_pct']:.2f}%")
                d_pct_item.setForeground(QColor(d_pnl_color))
                self.signals_table.setItem(row, 19, d_pct_item)

                self.signals_table.setItem(row, 21, QTableWidgetItem(deriv["wkn"]))
                return
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 19, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 21, QTableWidgetItem("-"))
        elif deriv:
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 19, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 21, QTableWidgetItem(deriv.get("wkn", "-")))
        else:
            self.signals_table.setItem(row, 18, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 19, QTableWidgetItem("-"))
            self.signals_table.setItem(row, 21, QTableWidgetItem("-"))

    def _set_tr_stop_column(self, row: int, trailing_price: float, tr_is_active: bool) -> None:
        """Set the TR Stop column (index 23, shifted due to added columns)."""
        if trailing_price > 0:
            if tr_is_active:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f}")
                tr_price_item.setForeground(QColor("#ff9800"))
            else:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f} (inaktiv)")
                tr_price_item.setForeground(QColor("#888888"))
            self.signals_table.setItem(row, 23, tr_price_item)
        else:
            self.signals_table.setItem(row, 23, QTableWidgetItem("-"))

    def _resolve_maintenance_margin_rate(self, signal: dict) -> tuple[float, bool]:
        rate = signal.get("maintenance_margin_rate")
        if rate is None:
            rate = signal.get("mm_rate")
        if rate is None:
            rate_pct = signal.get("maintenance_margin_pct")
            if rate_pct is not None:
                return float(rate_pct) / 100, False
        if rate is None:
            return 0.005, True
        return float(rate), False
