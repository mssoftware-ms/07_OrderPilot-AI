from __future__ import annotations

import logging

from PyQt6.QtCore import QTimer

from src.ui.widgets.chart_mixins.bot_overlay_mixin import MarkerType

logger = logging.getLogger(__name__)

class BotPositionPersistenceRestoreMixin:
    """BotPositionPersistenceRestoreMixin extracted from BotPositionPersistenceMixin."""
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
            logger.info("TR line not restored - not yet active (waiting for activation threshold)")
