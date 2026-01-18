from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QMessageBox

logger = logging.getLogger(__name__)

class BotPositionPersistenceContextMixin:
    """BotPositionPersistenceContextMixin extracted from BotPositionPersistenceMixin."""
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

        # Update signal - use "Sell" for manual close
        signal["status"] = "Sell"
        signal["is_open"] = False
        signal["exit_timestamp"] = int(datetime.now().timestamp())
        signal["exit_price"] = current_price

        # Remove all chart elements
        if hasattr(self, 'chart_widget'):
            try:
                self.chart_widget.remove_stop_line("initial_stop")
                self.chart_widget.remove_stop_line("trailing_stop")
                self.chart_widget.remove_stop_line("entry_line")
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

        # Reset bot controller for new trades
        if hasattr(self, '_bot_controller') and self._bot_controller:
            self._bot_controller._position = None
            self._bot_controller._current_signal = None
            if hasattr(self._bot_controller, '_state_machine'):
                from src.core.tradingbot.state_machine import BotTrigger
                try:
                    self._bot_controller._state_machine.trigger(BotTrigger.RESET, force=True)
                    self._add_ki_log_entry("BOT", "State Machine zurückgesetzt -> FLAT")
                except Exception as e:
                    logger.error(f"Failed to reset state machine: {e}")

        # Save and update
        self._save_signal_history()
        self._update_signals_table()
        self._add_ki_log_entry("MANUAL", f"Position manuell geschlossen @ {current_price:.4f}")
        logger.info(f"Manually closed position: {signal.get('side')} @ {signal.get('price'):.4f}")
        # Issue #6: Keep bot running after manual close
        if hasattr(self, "_ensure_bot_running_status"):
            self._ensure_bot_running_status()
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
                    self.chart_widget.remove_stop_line("entry_line")
                except:
                    pass

        self._save_signal_history()
        self._update_signals_table()
        logger.info(f"Deleted signal: {signal.get('type')} {signal.get('side')}")
