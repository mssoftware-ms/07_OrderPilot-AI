from __future__ import annotations

import logging

from PyQt6.QtCore import QTimer

from src.ui.widgets.chart_mixins.bot_overlay_mixin import MarkerType

logger = logging.getLogger(__name__)

class BotPositionPersistenceRestoreMixin:
    """BotPositionPersistenceRestoreMixin extracted from BotPositionPersistenceMixin."""

    def _connect_chart_data_loaded_for_position_restore(self) -> None:
        """Connect chart data_loaded signal to restore position lines on any chart refresh.

        Issue #9: Ensures stop lines are restored at their persisted positions
        after chart refreshes (timeframe changes, symbol changes, etc.)
        """
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'data_loaded'):
            # Use a persistent connection (not one-shot) so it works on every refresh
            try:
                self.chart_widget.data_loaded.disconnect(self._on_chart_data_loaded_restore_lines)
            except (TypeError, RuntimeError):
                pass  # Not connected yet
            self.chart_widget.data_loaded.connect(self._on_chart_data_loaded_restore_lines)
            logger.info("Connected data_loaded signal for position line restoration")

    def _on_chart_data_loaded_restore_lines(self) -> None:
        """Called when chart data is loaded - restore position lines from current signal history.

        Issue #9: This ensures stop lines maintain their manually-adjusted positions
        after any chart refresh, not just on application startup.
        """
        # Small delay to ensure chart is ready
        QTimer.singleShot(300, self._restore_position_lines_from_history)

    def _restore_position_lines_from_history(self) -> None:
        """Restore stop lines from current signal_history for any open positions.

        Issue #9: Uses the persisted stop_price from signal_history, ensuring
        manually moved stop lines stay at their adjusted positions.
        """
        if not hasattr(self, '_signal_history') or not self._signal_history:
            return

        # Find active (open) positions
        active_positions = [
            s for s in self._signal_history
            if s.get("status") == "ENTERED" and s.get("is_open", False)
        ]

        if not active_positions:
            return

        position = active_positions[-1]  # Most recent open position
        logger.info(f"Restoring position lines from history: stop_price={position.get('stop_price')}")

        # Restore using the stored (potentially manually adjusted) stop_price
        self._restore_persisted_chart_elements(
            position,
            position.get("side", "long"),
            position.get("price", 0),
            position.get("stop_price", 0)  # This uses the persisted value!
        )

    def _on_chart_data_loaded_restore_position(self) -> None:
        """Called when chart data is loaded - restore persisted positions (startup only)."""
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
            stop_price = self._ensure_persisted_stop_price(position, side, entry_price)

            self._update_persisted_position_labels(position, side, entry_price, quantity, stop_price)
            self._restore_persisted_chart_elements(position, side, entry_price, stop_price)

            # Start P&L update timer
            self._start_pnl_update_timer()

            # Restore right column (Score, TR Kurs, Derivative info)
            if hasattr(self, '_update_position_right_column_from_signal'):
                self._update_position_right_column_from_signal(position)

            logger.info(f"Position restored: {side} @ {entry_price:.2f}")

        except Exception as e:
            logger.error(f"Failed to restore position: {e}")

    def _ensure_persisted_stop_price(self, position: dict, side: str, entry_price: float) -> float:
        stop_price = position.get("stop_price", 0)
        if stop_price == 0 and entry_price > 0:
            initial_sl_pct = self.initial_sl_spin.value() if hasattr(self, 'initial_sl_spin') else 2.0
            if side == "long":
                stop_price = entry_price * (1 - initial_sl_pct / 100)
            else:
                stop_price = entry_price * (1 + initial_sl_pct / 100)
            position["stop_price"] = stop_price
            logger.info(f"Calculated stop price from SL%: {stop_price:.2f}")
        return stop_price

    def _update_persisted_position_labels(
        self,
        position: dict,
        side: str,
        entry_price: float,
        quantity: float,
        stop_price: float,
    ) -> None:
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

    def _restore_persisted_chart_elements(
        self,
        position: dict,
        side: str,
        entry_price: float,
        stop_price: float,
    ) -> None:
        if not hasattr(self, 'chart_widget'):
            return
        self._restore_entry_marker(position, side, entry_price)
        self._restore_initial_stop_line(position, stop_price)
        self._restore_trailing_stop_line(position)

    def _restore_entry_marker(self, position: dict, side: str, entry_price: float) -> None:
        timestamp = position.get("entry_timestamp", 0)
        label = position.get("label", "E")
        if not (timestamp and entry_price > 0):
            return
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

    def _restore_initial_stop_line(self, position: dict, stop_price: float) -> None:
        if stop_price <= 0:
            return
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

    def _restore_trailing_stop_line(self, position: dict) -> None:
        """Restore trailing stop line from position.

        Issue #10: Draw trailing stop line whether active or not:
        - Active: Orange color (#ff9800)
        - Waiting: Gray color (#888888) with [wartend] suffix
        """
        trailing_price = position.get("trailing_stop_price", 0)
        tr_is_active = position.get("tr_active", False)
        trailing_pct = position.get("trailing_stop_pct", 0)

        if trailing_price <= 0 or trailing_pct <= 0:
            return

        if tr_is_active:
            # Active trailing stop - orange
            tr_label = f"TSL @ {trailing_price:.2f}"
            if trailing_pct > 0:
                tr_label += f" ({trailing_pct:.2f}%)"
            tr_color = "#ff9800"
        else:
            # Waiting trailing stop - gray (Issue #10)
            tr_label = f"TSL @ {trailing_price:.2f} ({trailing_pct:.2f}%) [wartend]"
            tr_color = "#888888"

        try:
            self.chart_widget.add_stop_line(
                "trailing_stop",
                trailing_price,
                line_type="trailing",
                color=tr_color,
                label=tr_label
            )
            status = "aktiv" if tr_is_active else "wartend"
            logger.info(f"Restored trailing stop line @ {trailing_price:.2f} ({status})")
        except Exception as e:
            logger.error(f"Failed to restore trailing stop line: {e}")
