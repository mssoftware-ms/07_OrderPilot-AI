"""Bot Position Persistence - Position management and chart integration.

Contains methods for:
- Signal history persistence
- Position restoration
- P&L update timers
- Context menu (sell/delete signals)
- Chart line signals (bidirectional editing)

REFACTORED: TR% lock feature extracted to bot_tr_lock_mixin.py
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QMessageBox

from src.ui.widgets.chart_mixins.bot_overlay_mixin import MarkerType

from .bot_tr_lock_mixin import BotTRLockMixin

logger = logging.getLogger(__name__)


class BotPositionPersistenceMixin(BotTRLockMixin):
    """Mixin providing position persistence and chart integration."""

    # ==================== SIGNAL HISTORY PERSISTENCE ====================

    def _get_signal_history_key(self) -> str:
        """Get settings key for signal history based on current symbol."""
        symbol = getattr(self, 'symbol', '') or self._current_bot_symbol
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        return f"SignalHistory/{safe_symbol}"

    def _save_signal_history(self) -> None:
        """Save signal history to settings for the current symbol."""
        if not self._signal_history:
            return

        key = self._get_signal_history_key()
        if not key or key == "SignalHistory/":
            return

        try:
            history_json = json.dumps(self._signal_history)
            self._bot_settings.setValue(key, history_json)
            logger.info(f"Saved {len(self._signal_history)} signals for {key}")
        except Exception as e:
            logger.error(f"Failed to save signal history: {e}")

    def _load_signal_history(self) -> None:
        """Load signal history from settings for the current symbol."""
        key = self._get_signal_history_key()
        if not key or key == "SignalHistory/":
            return

        try:
            history_json = self._bot_settings.value(key)
            if history_json:
                if isinstance(history_json, str):
                    self._signal_history = json.loads(history_json)
                else:
                    self._signal_history = history_json

                logger.info(f"Loaded {len(self._signal_history)} signals for {key}")

                if hasattr(self, 'signals_table'):
                    self._update_signals_table()

                # Check for active positions
                active_positions = [s for s in self._signal_history
                                   if s.get("status") == "ENTERED" and s.get("is_open", False)]
                if active_positions:
                    logger.info(f"Found {len(active_positions)} active positions, scheduling restoration")
                    self._pending_position_restore = active_positions
                    if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'data_loaded'):
                        self.chart_widget.data_loaded.connect(self._on_chart_data_loaded_restore_position)
                    else:
                        QTimer.singleShot(2000, lambda: self._restore_persisted_position(active_positions))

        except Exception as e:
            logger.error(f"Failed to load signal history: {e}")

    def _on_chart_data_loaded_restore_position(self) -> None:
        """Called when chart data is loaded - restore persisted positions."""
        if hasattr(self, '_pending_position_restore') and self._pending_position_restore:
            logger.info("Chart data loaded - restoring persisted positions")
            QTimer.singleShot(500, lambda: self._restore_persisted_position(self._pending_position_restore))
            try:
                self.chart_widget.data_loaded.disconnect(self._on_chart_data_loaded_restore_position)
            except:
                pass

    def _restore_persisted_position(self, active_positions: list) -> None:
        """Restore chart elements and Current Position display for persisted positions."""
        if not active_positions:
            logger.warning("_restore_persisted_position called with no active positions")
            return

        position = active_positions[-1]
        logger.info(f"Restoring persisted position: {position}")

        try:
            side = position.get("side", "long")
            entry_price = position.get("price", 0)
            quantity = position.get("quantity", 0)
            stop_price = position.get("stop_price", 0)

            # Calculate stop from Initial SL % if not saved
            if stop_price == 0 and entry_price > 0:
                initial_sl_pct = self.initial_sl_spin.value() if hasattr(self, 'initial_sl_spin') else 2.0
                if side == "long":
                    stop_price = entry_price * (1 - initial_sl_pct / 100)
                else:
                    stop_price = entry_price * (1 + initial_sl_pct / 100)
                position["stop_price"] = stop_price
                logger.info(f"Calculated stop price from SL%: {stop_price:.2f}")

            # Update Current Position display
            if hasattr(self, 'position_side_label'):
                self.position_side_label.setText(side.upper())
                color = "#26a69a" if side == "long" else "#ef5350"
                self.position_side_label.setStyleSheet(f"font-weight: bold; color: {color};")

            if hasattr(self, 'position_entry_label'):
                self.position_entry_label.setText(f"{entry_price:.4f}")

            if hasattr(self, 'position_size_label'):
                self.position_size_label.setText(f"{quantity:.4f}" if quantity > 0 else "-")

            invested = position.get("invested", 0)
            if hasattr(self, 'position_invested_label') and invested > 0:
                self.position_invested_label.setText(f"{invested:.0f} EUR")

            if hasattr(self, 'position_stop_label'):
                self.position_stop_label.setText(f"{stop_price:.4f}" if stop_price > 0 else "-")

            # Draw chart elements
            if hasattr(self, 'chart_widget'):
                # Entry marker
                timestamp = position.get("entry_timestamp", 0)
                label = position.get("label", "E")
                if timestamp and entry_price > 0:
                    try:
                        self.chart_widget.add_bot_marker(
                            timestamp=timestamp,
                            price=entry_price,
                            marker_type=MarkerType.ENTRY_CONFIRMED,
                            side=side,
                            text=label
                        )
                        logger.info(f"Restored entry marker: {label} @ {entry_price:.2f}")
                    except Exception as e:
                        logger.error(f"Failed to restore entry marker: {e}")

                # Initial stop line
                if stop_price > 0:
                    initial_sl_pct = position.get("initial_sl_pct", 0)
                    sl_label = f"SL @ {stop_price:.2f}"
                    if initial_sl_pct > 0:
                        sl_label += f" ({initial_sl_pct:.2f}%)"

                    try:
                        self.chart_widget.add_stop_line(
                            "initial_stop",
                            stop_price,
                            line_type="initial",
                            color="#ef5350",
                            label=sl_label
                        )
                        logger.info(f"Restored initial stop line @ {stop_price:.2f}")
                    except Exception as e:
                        logger.error(f"Failed to restore initial stop line: {e}")

                # Trailing stop line - only draw if TR is active
                trailing_price = position.get("trailing_stop_price", 0)
                tr_is_active = position.get("tr_active", False)
                if trailing_price > 0 and tr_is_active:
                    trailing_pct = position.get("trailing_stop_pct", 0)
                    tr_label = f"TSL @ {trailing_price:.2f}"
                    if trailing_pct > 0:
                        tr_label += f" ({trailing_pct:.2f}%)"

                    try:
                        self.chart_widget.add_stop_line(
                            "trailing_stop",
                            trailing_price,
                            line_type="trailing",
                            color="#ff9800",
                            label=tr_label
                        )
                        logger.info(f"Restored trailing stop line @ {trailing_price:.2f}")
                    except Exception as e:
                        logger.error(f"Failed to restore trailing stop line: {e}")
                elif trailing_price > 0:
                    logger.info(f"TR line not restored - not yet active (waiting for activation threshold)")

            # Start P&L update timer
            self._start_pnl_update_timer()

            # Restore right column (Score, TR Kurs, Derivative info)
            if hasattr(self, '_update_position_right_column'):
                self._update_position_right_column(position)

            logger.info(f"Position restored: {side} @ {entry_price:.2f}")

        except Exception as e:
            logger.error(f"Failed to restore position: {e}")

    # ==================== P&L UPDATE TIMER ====================

    def _start_pnl_update_timer(self) -> None:
        """Start timer to update P&L for restored positions."""
        if not hasattr(self, '_pnl_update_timer') or self._pnl_update_timer is None:
            self._pnl_update_timer = QTimer()
            self._pnl_update_timer.timeout.connect(self._update_restored_positions_pnl)
        self._pnl_update_timer.start(2000)
        logger.info("P&L update timer started")

    def _update_restored_positions_pnl(self) -> None:
        """Update P&L for restored positions from chart's current price."""
        # Get current price from chart
        current_price = 0.0
        if hasattr(self, 'chart_widget'):
            if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                try:
                    current_price = float(self.chart_widget.data['close'].iloc[-1])
                except:
                    pass

        if current_price <= 0:
            return

        # Update active positions
        table_updated = False
        for sig in self._signal_history:
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                entry_price = sig.get("price", 0)
                invested = sig.get("invested", 0)
                side = sig.get("side", "long")

                if entry_price <= 0:
                    continue

                sig["current_price"] = current_price

                # Calculate P&L
                if side.lower() == "long":
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100

                if invested > 0:
                    pnl_currency = invested * (pnl_pct / 100)
                else:
                    pnl_currency = 0

                sig["pnl_currency"] = pnl_currency
                sig["pnl_percent"] = pnl_pct
                table_updated = True

                # Check trailing stop activation (from BotDisplayManagerMixin)
                if hasattr(self, '_check_tr_activation'):
                    self._check_tr_activation(sig, current_price)

                # Update Current Position display
                if hasattr(self, 'position_current_label'):
                    self.position_current_label.setText(f"{current_price:.4f}")

                if hasattr(self, 'position_pnl_label'):
                    color = "#26a69a" if pnl_pct >= 0 else "#ef5350"
                    sign = "+" if pnl_pct >= 0 else ""
                    self.position_pnl_label.setText(f"{sign}{pnl_pct:.2f}% ({sign}{pnl_currency:.2f} EUR)")
                    self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")

                # Update derivative P&L if enabled
                if (hasattr(self, 'enable_derivathandel_cb')
                    and self.enable_derivathandel_cb.isChecked()
                    and hasattr(self, '_calculate_derivative_pnl_for_signal')):
                    deriv_pnl = self._calculate_derivative_pnl_for_signal(sig, current_price)
                    if deriv_pnl and hasattr(self, 'deriv_pnl_label'):
                        d_pnl_eur = deriv_pnl.get("pnl_eur", 0)
                        d_pnl_pct = deriv_pnl.get("pnl_pct", 0)
                        d_color = "#26a69a" if d_pnl_eur >= 0 else "#ef5350"
                        d_sign = "+" if d_pnl_eur >= 0 else ""
                        self.deriv_pnl_label.setText(
                            f"{d_sign}{d_pnl_pct:.2f}% ({d_sign}{d_pnl_eur:.2f} €)"
                        )
                        self.deriv_pnl_label.setStyleSheet(f"font-weight: bold; color: {d_color};")

        if table_updated:
            self._update_signals_table()

    # ==================== CONTEXT MENU ====================

    def _show_signals_context_menu(self, position) -> None:
        """Show context menu for signals table."""
        row = self.signals_table.rowAt(position.y())
        if row < 0:
            return

        recent_signals = list(reversed(self._signal_history[-20:]))
        if row >= len(recent_signals):
            return

        signal = recent_signals[row]

        menu = QMenu(self)

        # Only show actions for active positions
        is_active = signal.get("status") == "ENTERED" and signal.get("is_open", False)

        if is_active:
            sell_action = QAction("Verkaufen (Manuell schliessen)", self)
            sell_action.triggered.connect(lambda: self._sell_signal(row, signal))
            menu.addAction(sell_action)
            menu.addSeparator()

        delete_action = QAction("Signal loeschen", self)
        delete_action.triggered.connect(lambda: self._delete_signal(row, signal))
        menu.addAction(delete_action)

        menu.exec(self.signals_table.mapToGlobal(position))

    def _sell_signal(self, row: int, signal: dict) -> None:
        """Manually close/sell a signal's position."""
        # Confirm
        reply = QMessageBox.question(
            self, "Position schliessen",
            f"Position {signal.get('side', 'long').upper()} @ {signal.get('price', 0):.4f} manuell schliessen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Get current price for P&L calculation
        current_price = signal.get("current_price", signal.get("price", 0))

        # Update signal - use "Sold" for manual close
        signal["status"] = "Sold"
        signal["is_open"] = False
        signal["exit_timestamp"] = int(datetime.now().timestamp())
        signal["exit_price"] = current_price

        # Remove chart elements
        if hasattr(self, 'chart_widget'):
            try:
                self.chart_widget.remove_stop_line("initial_stop")
                self.chart_widget.remove_stop_line("trailing_stop")
            except:
                pass

        # Stop P&L timer if no more active positions
        active_count = sum(1 for s in self._signal_history
                         if s.get("status") == "ENTERED" and s.get("is_open", False))
        if active_count == 0 and hasattr(self, '_pnl_update_timer'):
            self._pnl_update_timer.stop()

        # Reset position display
        if hasattr(self, 'position_side_label'):
            self.position_side_label.setText("FLAT")
            self.position_side_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
        if hasattr(self, 'position_entry_label'):
            self.position_entry_label.setText("-")
        if hasattr(self, 'position_stop_label'):
            self.position_stop_label.setText("-")

        # Reset right column (Score, TR Kurs, Derivative labels)
        if hasattr(self, '_reset_position_right_column'):
            self._reset_position_right_column()

        # Save and update
        self._save_signal_history()
        self._update_signals_table()
        self._add_ki_log_entry("MANUAL", f"Position manuell geschlossen @ {current_price:.4f}")
        logger.info(f"Manually closed position: {signal.get('side')} @ {signal.get('price'):.4f}")

    def _delete_signal(self, row: int, signal: dict) -> None:
        """Delete a signal from history."""
        reply = QMessageBox.question(
            self, "Signal loeschen",
            "Signal dauerhaft aus Historie loeschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Find and remove
        signal_index = len(self._signal_history) - 1 - row
        if 0 <= signal_index < len(self._signal_history):
            del self._signal_history[signal_index]

        # If was active, clean up chart
        if signal.get("is_open", False):
            if hasattr(self, 'chart_widget'):
                try:
                    self.chart_widget.remove_stop_line("initial_stop")
                    self.chart_widget.remove_stop_line("trailing_stop")
                except:
                    pass

        self._save_signal_history()
        self._update_signals_table()
        logger.info(f"Deleted signal: {signal.get('type')} {signal.get('side')}")

    # ==================== CHART LINE SIGNALS ====================

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
        """Handle table cell editing - update chart lines when SL% or TR% changes."""
        if self._signals_table_updating:
            return

        if column not in (6, 7):
            return

        item = self.signals_table.item(row, column)
        if not item:
            return

        try:
            new_pct = float(item.text().replace(",", ".").replace("%", "").strip())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid percentage value in row {row}, column {column}")
            return

        if new_pct <= 0:
            return

        visible_signals = [s for s in self._signal_history if s.get("status") in ("ENTERED", "EXITED")]
        signal_idx = len(visible_signals) - 1 - row

        if signal_idx < 0 or signal_idx >= len(visible_signals):
            return

        sig = visible_signals[signal_idx]

        if not (sig.get("status") == "ENTERED" and sig.get("is_open", False)):
            return

        entry_price = sig.get("price", 0)
        side = sig.get("side", "long")

        if entry_price <= 0:
            return

        if side == "long":
            new_stop_price = entry_price * (1 - new_pct / 100)
        else:
            new_stop_price = entry_price * (1 + new_pct / 100)

        logger.info(f"Table edit: col={column}, new_pct={new_pct:.2f}%, new_stop={new_stop_price:.2f}")

        if column == 6:  # SL%
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

        elif column == 7:  # TR%
            sig["trailing_stop_price"] = new_stop_price
            sig["trailing_stop_pct"] = new_pct

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

        self._sync_stop_to_bot_controller(new_stop_price)
        self._save_signal_history()

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
