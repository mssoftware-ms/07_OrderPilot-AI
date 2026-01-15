from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

class BotPositionPersistenceChartMixin:
    """BotPositionPersistenceChartMixin extracted from BotPositionPersistenceMixin."""
    def _connect_chart_line_signals(self) -> None:
        """Connect chart line drag signals for bidirectional editing."""
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'stop_line_moved'):
            self.chart_widget.stop_line_moved.connect(self._on_chart_stop_line_moved)
            logger.info("Connected chart stop_line_moved signal")
    def _on_chart_stop_line_moved(self, line_id: str, new_price: float) -> None:
        """Handle stop line being dragged in the chart."""
        logger.info(f"Chart line moved: {line_id} -> {new_price:.4f}")

        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                entry_price = sig.get("price", 0)
                side = sig.get("side", "long")

                if line_id == "initial_stop":
                    sig["stop_price"] = new_price
                    new_sl_pct = 0.0
                    if entry_price > 0:
                        new_sl_pct = abs((new_price - entry_price) / entry_price) * 100
                        sig["initial_sl_pct"] = new_sl_pct
                    self._add_ki_log_entry("CHART", f"Stop Loss verschoben -> {new_price:.2f} ({new_sl_pct:.2f}%)")

                    # Update Current Position display
                    if hasattr(self, 'position_stop_label'):
                        self.position_stop_label.setText(f"{new_price:.4f}")

                    if hasattr(self, "chart_widget") and self.chart_widget:
                        label = f"SL @ {new_price:.2f} ({new_sl_pct:.2f}%)"
                        self.chart_widget.add_stop_line(
                            line_id="initial_stop",
                            price=new_price,
                            line_type="initial",
                            label=label
                        )

                elif line_id == "trailing_stop":
                    sig["trailing_stop_price"] = new_price
                    new_tr_pct = 0.0
                    if entry_price > 0:
                        if side == "long":
                            new_tr_pct = abs((entry_price - new_price) / entry_price) * 100
                        else:
                            new_tr_pct = abs((new_price - entry_price) / entry_price) * 100
                        sig["trailing_stop_pct"] = new_tr_pct

                    current_price = sig.get("current_price", entry_price)
                    tra_pct = abs((current_price - new_price) / current_price) * 100 if current_price > 0 else 0.0
                    self._add_ki_log_entry("CHART", f"Trailing Stop verschoben -> {new_price:.2f} ({new_tr_pct:.2f}% / TRA: {tra_pct:.2f}%)")

                    # Update Current Position display (trailing stop becomes active stop)
                    if hasattr(self, 'position_stop_label'):
                        self.position_stop_label.setText(f"{new_price:.4f}")

                    if hasattr(self, "chart_widget") and self.chart_widget:
                        label = f"TSL @ {new_price:.2f} ({new_tr_pct:.2f}% / TRA: {tra_pct:.2f}%)"
                        self.chart_widget.add_stop_line(
                            line_id="trailing_stop",
                            price=new_price,
                            line_type="trailing",
                            label=label
                        )

                elif line_id == "entry_line":
                    old_entry = entry_price
                    sig["price"] = new_price
                    stop_price = sig.get("stop_price", 0)
                    if new_price > 0 and stop_price > 0:
                        sig["initial_sl_pct"] = abs((stop_price - new_price) / new_price) * 100
                    self._add_ki_log_entry("CHART", f"Entry verschoben -> {new_price:.2f} (war {old_entry:.2f})")

                # Sync to bot controller
                if line_id in ("initial_stop", "trailing_stop"):
                    self._sync_stop_to_bot_controller(new_price)

                self._save_signal_history()
                self._update_signals_table()
                break
    def _on_signals_table_cell_changed(self, row: int, column: int) -> None:
        """Handle table cell editing - update SL%, TR%, or TRA% values.

        Column mapping:
        - 5: SL% (Stop Loss Percent from entry)
        - 6: TR% (Trailing Stop Percent from entry)
        - 7: TRA% (Trailing Activation Percent - when trailing activates)
        """
        # Guard clauses - allow columns 5, 6, and 7
        if self._signals_table_updating or column not in (5, 6, 7):
            return

        # Parse and validate input
        new_pct = self._parse_percentage_input(row, column)
        if new_pct is None or new_pct < 0:
            return

        # Get signal
        sig = self._get_editable_signal(row)
        if not sig:
            return

        logger.info(f"Table edit: col={column}, new_pct={new_pct:.2f}%")

        # Handle TRA% (column 7) separately - it's not a stop price calculation
        if column == 7:  # TRA% (Trailing Activation)
            self._update_trailing_activation(sig, new_pct)
            self._save_signal_history()
            self._refresh_signals_table()
            return

        # For SL% and TR%, calculate new stop price
        new_stop_price = self._calculate_stop_price(sig, new_pct)
        if new_stop_price is None:
            return

        logger.info(f"Table edit: col={column}, new_pct={new_pct:.2f}%, new_stop={new_stop_price:.2f}")

        # Update based on column type
        if column == 5:  # SL%
            self._update_stop_loss(sig, new_stop_price, new_pct)
        elif column == 6:  # TR%
            self._update_trailing_stop(sig, new_stop_price, new_pct)

        # Sync and save
        self._sync_stop_to_bot_controller(new_stop_price)
        self._save_signal_history()
        self._refresh_signals_table()

    def _parse_percentage_input(self, row: int, column: int) -> float | None:
        """Parse percentage input from table cell."""
        item = self.signals_table.item(row, column)
        if not item:
            return None

        try:
            return float(item.text().replace(",", ".").replace("%", "").strip())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid percentage value in row {row}, column {column}")
            return None

    def _get_editable_signal(self, row: int) -> dict | None:
        """Get signal that can be edited from table row."""
        visible_signals = [s for s in self._signal_history if s.get("status") in ("ENTERED", "EXITED")]
        signal_idx = len(visible_signals) - 1 - row

        if signal_idx < 0 or signal_idx >= len(visible_signals):
            return None

        sig = visible_signals[signal_idx]

        # Only allow editing open positions
        if not (sig.get("status") == "ENTERED" and sig.get("is_open", False)):
            return None

        return sig

    def _calculate_stop_price(self, sig: dict, new_pct: float) -> float | None:
        """Calculate new stop price based on entry price and percentage."""
        entry_price = sig.get("price", 0)
        if entry_price <= 0:
            return None

        side = sig.get("side", "long")
        if side == "long":
            return entry_price * (1 - new_pct / 100)
        else:
            return entry_price * (1 + new_pct / 100)

    def _update_stop_loss(self, sig: dict, new_stop_price: float, new_pct: float) -> None:
        """Update stop loss on signal and chart."""
        sig["stop_price"] = new_stop_price
        sig["initial_sl_pct"] = new_pct

        if hasattr(self, "chart_widget") and self.chart_widget:
            label = f"SL @ {new_stop_price:.2f} ({new_pct:.2f}%)"
            self.chart_widget.add_stop_line(
                line_id="initial_stop",
                price=new_stop_price,
                line_type="initial",
                label=label
            )
        self._add_ki_log_entry("TABLE", f"Stop Loss geaendert -> {new_stop_price:.2f} ({new_pct:.2f}%)")

    def _update_trailing_stop(self, sig: dict, new_stop_price: float, new_pct: float) -> None:
        """Update trailing stop on signal and chart."""
        sig["trailing_stop_price"] = new_stop_price
        sig["trailing_stop_pct"] = new_pct

        entry_price = sig.get("price", 0)
        current_price = sig.get("current_price", entry_price)
        tra_pct = abs((current_price - new_stop_price) / current_price) * 100 if current_price > 0 else 0.0

        if hasattr(self, "chart_widget") and self.chart_widget:
            label = f"TSL @ {new_stop_price:.2f} ({new_pct:.2f}% / TRA: {tra_pct:.2f}%)"
            self.chart_widget.add_stop_line(
                line_id="trailing_stop",
                price=new_stop_price,
                line_type="trailing",
                label=label
            )
        self._add_ki_log_entry("TABLE", f"Trailing Stop geaendert -> {new_stop_price:.2f} ({new_pct:.2f}%)")

    def _update_trailing_activation(self, sig: dict, new_tra_pct: float) -> None:
        """Update trailing activation percentage on signal.

        TRA% defines when the trailing stop becomes active:
        - LONG: Trailing activates when price >= entry * (1 + TRA%/100)
        - SHORT: Trailing activates when price <= entry * (1 - TRA%/100)

        Args:
            sig: Signal dictionary to update
            new_tra_pct: New trailing activation percentage
        """
        old_tra_pct = sig.get("trailing_activation_pct", 0.0)
        sig["trailing_activation_pct"] = new_tra_pct

        # Calculate activation price for logging
        entry_price = sig.get("price", 0)
        side = sig.get("side", "long")

        if entry_price > 0:
            if side == "long":
                activation_price = entry_price * (1 + new_tra_pct / 100)
            else:
                activation_price = entry_price * (1 - new_tra_pct / 100)

            self._add_ki_log_entry(
                "TABLE",
                f"TRA% geaendert: {old_tra_pct:.2f}% -> {new_tra_pct:.2f}% "
                f"(Aktivierung bei {activation_price:.2f})"
            )
        else:
            self._add_ki_log_entry(
                "TABLE",
                f"TRA% geaendert: {old_tra_pct:.2f}% -> {new_tra_pct:.2f}%"
            )

        # Sync to bot controller if available
        self._sync_trailing_activation_to_bot(new_tra_pct)

    def _sync_trailing_activation_to_bot(self, new_tra_pct: float) -> None:
        """Sync trailing activation percentage to bot controller."""
        if not hasattr(self, '_bot_controller') or not self._bot_controller:
            return

        position = getattr(self._bot_controller, '_position', None)
        if not position:
            return

        trailing = getattr(position, 'trailing', None)
        if trailing and hasattr(trailing, 'activation_pct'):
            old_pct = trailing.activation_pct
            trailing.activation_pct = new_tra_pct
            logger.info(f"[BOT SYNC] TRA% synced: {old_pct:.2f}% -> {new_tra_pct:.2f}%")

    def _refresh_signals_table(self) -> None:
        """Refresh signals table with update lock."""
        self._signals_table_updating = True
        try:
            self._update_signals_table()
        finally:
            self._signals_table_updating = False
    def _sync_stop_to_bot_controller(self, new_stop_price: float) -> None:
        """Sync stop price to bot controller's internal position."""
        if not hasattr(self, '_bot_controller') or not self._bot_controller:
            return

        position = getattr(self._bot_controller, '_position', None)
        if not position:
            return

        trailing = getattr(position, 'trailing', None)
        if not trailing:
            return

        old_stop = trailing.current_stop_price
        trailing.current_stop_price = new_stop_price

        if new_stop_price < trailing.initial_stop_price:
            trailing.initial_stop_price = new_stop_price

        logger.info(f"[BOT SYNC] Stop synced: {old_stop:.4f} -> {new_stop_price:.4f}")
        self._add_ki_log_entry("SYNC", f"Bot-Stop synchronisiert: {old_stop:.2f} -> {new_stop_price:.2f}")
