"""Bot TR% Lock Mixin - Trailing Stop Lock Feature.

Contains methods for:
- TR% lock activation/deactivation
- Automatic trailing stop adjustment on candle close
- Lock state management
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BotTRLockMixin:
    """Mixin providing TR% lock feature for trailing stop management."""

    def _on_row_tr_lock_changed(self, signal_index: int, state: int) -> None:
        """Handle TR% lock checkbox change for a specific signal row."""
        is_locked = state == Qt.CheckState.Checked.value

        if signal_index < 0 or signal_index >= len(self._signal_history):
            return

        signal = self._signal_history[signal_index]

        if is_locked:
            current_price = signal.get("current_price", signal.get("price", 0))
            trailing_price = signal.get("trailing_stop_price", 0)

            if current_price <= 0 or trailing_price <= 0:
                return

            tra_pct = abs((current_price - trailing_price) / current_price) * 100

            signal["tr_lock_active"] = True
            signal["tr_lock_tra_pct"] = tra_pct
            signal["tr_lock_last_close"] = current_price

            logger.info(f"TR% Lock aktiviert fuer Signal #{signal_index}: TRA%={tra_pct:.2f}%")
            self._add_ki_log_entry("TR_LOCK", f"TR% Lock aktiviert: TRA%={tra_pct:.2f}% bei Kurs {current_price:.2f}")
        else:
            signal["tr_lock_active"] = False
            signal.pop("tr_lock_tra_pct", None)
            signal.pop("tr_lock_last_close", None)

            logger.info(f"TR% Lock deaktiviert fuer Signal #{signal_index}")
            self._add_ki_log_entry("TR_LOCK", "TR% Lock deaktiviert")

        self._save_signal_history()

    def _get_signals_with_active_lock(self) -> list[dict]:
        """Get all signals that have TR% lock active."""
        locked_signals = []
        for signal in self._signal_history:
            if signal.get("tr_lock_active", False):
                if signal.get("status") == "ENTERED" and signal.get("is_open") is not False:
                    locked_signals.append(signal)
        return locked_signals

    def _on_candle_closed(self, previous_close: float, new_open: float) -> None:
        """Handle candle close event for TR% lock feature."""
        locked_signals = self._get_signals_with_active_lock()
        if not locked_signals:
            return

        current_price = previous_close
        any_updated = False

        for signal in locked_signals:
            locked_tra_pct = signal.get("tr_lock_tra_pct", 0)
            if locked_tra_pct <= 0:
                continue

            locked_side = signal.get("side", "LONG").upper()
            last_close = signal.get("tr_lock_last_close", current_price)

            # Check direction condition
            if locked_side == "LONG":
                if current_price <= last_close:
                    signal["tr_lock_last_close"] = current_price
                    continue
            else:
                if current_price >= last_close:
                    signal["tr_lock_last_close"] = current_price
                    continue

            # Calculate new trailing stop
            if locked_side == "LONG":
                new_trailing_price = current_price * (1 - locked_tra_pct / 100)
            else:
                new_trailing_price = current_price * (1 + locked_tra_pct / 100)

            old_trailing = signal.get("trailing_stop_price", 0)

            # Only move in favorable direction
            if locked_side == "LONG":
                if new_trailing_price <= old_trailing:
                    signal["tr_lock_last_close"] = current_price
                    continue
            else:
                if new_trailing_price >= old_trailing:
                    signal["tr_lock_last_close"] = current_price
                    continue

            # Update signal
            signal["trailing_stop_price"] = new_trailing_price
            entry_price = signal.get("price", current_price)
            new_tr_pct = abs((entry_price - new_trailing_price) / entry_price) * 100
            if signal.get("trailing_stop_pct", 0) <= 0:
                signal["trailing_stop_pct"] = new_tr_pct
            signal["current_price"] = current_price
            signal["tr_lock_last_close"] = current_price

            # Update chart line
            if hasattr(self, 'chart_widget'):
                new_tra_pct = abs((current_price - new_trailing_price) / current_price) * 100
                label_text = f"TSL @ {new_trailing_price:.2f} ({new_tr_pct:.2f}% / TRA: {new_tra_pct:.2f}%)"
                try:
                    self.chart_widget.update_stop_line(
                        line_id="trailing_stop",
                        new_price=new_trailing_price,
                        label=label_text
                    )
                except:
                    self.chart_widget.add_stop_line(
                        line_id="trailing_stop",
                        price=new_trailing_price,
                        line_type="trailing",
                        color="#ff9800",
                        label=label_text
                    )

            self._add_ki_log_entry(
                "TR_LOCK",
                f"Trailing nachgezogen: {old_trailing:.2f} -> {new_trailing_price:.2f} (TRA%={locked_tra_pct:.2f}%)"
            )
            logger.info(f"TR% Lock: Trailing stop moved {old_trailing:.2f} -> {new_trailing_price:.2f}")
            any_updated = True

        if any_updated:
            self._save_signal_history()
            self._update_signals_table()
