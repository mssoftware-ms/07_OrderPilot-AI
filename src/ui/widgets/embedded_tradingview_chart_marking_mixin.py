from __future__ import annotations

import logging

from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

class EmbeddedTradingViewChartMarkingMixin:
    """EmbeddedTradingViewChartMarkingMixin extracted from EmbeddedTradingViewChart."""
    def _add_test_entry_marker(self, direction: str):
        """Add a test entry marker at the cursor position.

        Uses the crosshair position if available, otherwise falls back to last candle.
        """
        # First try to get position from crosshair (cursor position)
        crosshair_time, crosshair_price = None, None
        if hasattr(self, "_chart_bridge") and self._chart_bridge is not None:
            crosshair_time, crosshair_price = self._chart_bridge.get_crosshair_position()

        if crosshair_time is not None and crosshair_price is not None:
            # Use crosshair position (cursor position)
            timestamp = int(crosshair_time)
            price = crosshair_price
            logger.info(f"Using crosshair position: time={timestamp}, price={price}")
        else:
            # Fallback: use last candle position
            if not hasattr(self, "_last_price") or self._last_price is None:
                logger.warning("No price data available for marker")
                return

            # Use timestamp from last candle in data
            if self.data is not None and len(self.data) > 0:
                last_row = self.data.iloc[-1]
                if 'time' in self.data.columns:
                    timestamp = int(last_row['time'])
                elif hasattr(last_row.name, 'timestamp'):
                    timestamp = int(last_row.name.timestamp())
                else:
                    timestamp = getattr(self, '_current_candle_time', None)
                    if timestamp is None:
                        import time
                        timestamp = int(time.time())
            else:
                import time
                timestamp = int(time.time())

            price = self._last_price
            logger.info(f"Using last candle position: time={timestamp}, price={price}")

        text = f"{direction.upper()} Entry"

        if direction == "long":
            self.add_long_entry(timestamp, price, text)
        else:
            self.add_short_entry(timestamp, price, text)

        logger.info(f"Added {direction} entry marker at {price:.2f}, timestamp={timestamp}")
    def _add_test_zone(self, zone_type: str):
        """Add a test zone around cursor position.

        Uses the crosshair position if available, otherwise falls back to last candle.

        Args:
            zone_type: 'support', 'resistance', 'demand', or 'supply'
        """
        # First try to get position from crosshair (cursor position)
        crosshair_time, crosshair_price = None, None
        if hasattr(self, "_chart_bridge") and self._chart_bridge is not None:
            crosshair_time, crosshair_price = self._chart_bridge.get_crosshair_position()

        if crosshair_time is not None and crosshair_price is not None:
            # Use crosshair position as the center of the zone
            price = crosshair_price
            end_time = int(crosshair_time)
            # Zone extends 10 candles before cursor
            if self.data is not None and len(self.data) > 1:
                candle_duration = int(self.data['time'].iloc[1] - self.data['time'].iloc[0])
                start_time = end_time - (candle_duration * 10)
            else:
                start_time = end_time - 3600  # Default 1 hour
            logger.info(f"Using crosshair position for zone: time={end_time}, price={price}")
        else:
            # Fallback: use last candle position
            if not hasattr(self, "_last_price") or self._last_price is None:
                logger.warning("No price data available for zone")
                return

            # Use timestamps from chart data
            if self.data is not None and len(self.data) > 0:
                if 'time' in self.data.columns:
                    end_time = int(self.data['time'].iloc[-1])
                    num_candles = min(20, len(self.data))
                    start_time = int(self.data['time'].iloc[-num_candles])
                else:
                    import time
                    end_time = int(time.time())
                    start_time = end_time - 3600
            else:
                import time
                end_time = int(time.time())
                start_time = end_time - 3600

            price = self._last_price
            logger.info(f"Using last candle position for zone: time={end_time}, price={price}")

        # Create zone around price (1% range)
        zone_height = price * 0.01
        top = price + zone_height / 2
        bottom = price - zone_height / 2

        if zone_type == "support":
            self.add_support_zone(start_time, end_time, top, bottom, "Support")
        elif zone_type == "resistance":
            self.add_resistance_zone(start_time, end_time, top, bottom, "Resistance")
        elif zone_type == "demand":
            self.add_demand_zone(start_time, end_time, top, bottom, "Demand")
        elif zone_type == "supply":
            self.add_supply_zone(start_time, end_time, top, bottom, "Supply")

        logger.info(f"Added {zone_type} zone: {bottom:.2f} - {top:.2f}")
    def _add_test_structure(self, break_type: str, is_bullish: bool):
        """Add a test structure break marker at cursor position.

        Uses the crosshair position if available, otherwise falls back to last candle.

        Args:
            break_type: 'bos', 'choch', or 'msb'
            is_bullish: True for bullish, False for bearish
        """
        # First try to get position from crosshair (cursor position)
        crosshair_time, crosshair_price = None, None
        if hasattr(self, "_chart_bridge") and self._chart_bridge is not None:
            crosshair_time, crosshair_price = self._chart_bridge.get_crosshair_position()

        if crosshair_time is not None and crosshair_price is not None:
            # Use crosshair position (cursor position)
            timestamp = int(crosshair_time)
            price = crosshair_price
            logger.info(f"Using crosshair position for structure: time={timestamp}, price={price}")
        else:
            # Fallback: use last candle position
            if not hasattr(self, "_last_price") or self._last_price is None:
                logger.warning("No price data available for structure marker")
                return

            if self.data is not None and len(self.data) > 0:
                if 'time' in self.data.columns:
                    timestamp = int(self.data['time'].iloc[-1])
                elif hasattr(self.data.index[-1], 'timestamp'):
                    timestamp = int(self.data.index[-1].timestamp())
                else:
                    timestamp = getattr(self, '_current_candle_time', None)
                    if timestamp is None:
                        import time
                        timestamp = int(time.time())
            else:
                import time
                timestamp = int(time.time())

            price = self._last_price
            logger.info(f"Using last candle position for structure: time={timestamp}, price={price}")

        if break_type == "bos":
            self.add_bos(timestamp, price, is_bullish)
        elif break_type == "choch":
            self.add_choch(timestamp, price, is_bullish)
        elif break_type == "msb":
            self.add_msb(timestamp, price, is_bullish)

        direction = "bullish" if is_bullish else "bearish"
        logger.info(f"Added {break_type.upper()} ({direction}) at {price:.2f}, timestamp={timestamp}")
    def _add_test_line(self, line_type: str, is_long: bool):
        """Add a test line (SL, TP, Entry, or Trailing).

        Args:
            line_type: 'sl', 'tp', 'entry', or 'trailing'
            is_long: True for long position, False for short
        """
        import time
        if not hasattr(self, "_last_price") or self._last_price is None:
            logger.warning("No price data available for line")
            return

        price = self._last_price
        line_id = f"{line_type}_{int(time.time()*1000)}"

        # Calculate entry price (simulated: current price as entry)
        entry_price = price

        # Calculate line price based on type and direction
        offset = price * 0.02  # 2% offset

        if line_type == "sl":
            # Stop loss: below entry for long, above for short
            if is_long:
                line_price = price - offset
            else:
                line_price = price + offset
            self.add_stop_loss_line(
                line_id=line_id,
                price=line_price,
                entry_price=entry_price,
                is_long=is_long,
                label=f"SL @ {line_price:.2f}",
                show_risk=True
            )
            logger.info(f"Added SL line at {line_price:.2f} for {'long' if is_long else 'short'}")

        elif line_type == "tp":
            # Take profit: above entry for long, below for short
            if is_long:
                line_price = price + offset * 2  # 2:1 R:R
            else:
                line_price = price - offset * 2
            self.add_take_profit_line(
                line_id=line_id,
                price=line_price,
                entry_price=entry_price,
                is_long=is_long,
                label=f"TP @ {line_price:.2f}"
            )
            logger.info(f"Added TP line at {line_price:.2f} for {'long' if is_long else 'short'}")

        elif line_type == "entry":
            self.add_entry_line(
                line_id=line_id,
                price=entry_price,
                is_long=is_long,
                label=f"Entry @ {entry_price:.2f}"
            )
            logger.info(f"Added Entry line at {entry_price:.2f} for {'long' if is_long else 'short'}")

        elif line_type == "trailing":
            # Trailing stop: similar to SL but labeled differently
            if is_long:
                line_price = price - offset * 0.5  # Tighter than initial SL
            else:
                line_price = price + offset * 0.5
            self.add_trailing_stop_line(
                line_id=line_id,
                price=line_price,
                entry_price=entry_price,
                is_long=is_long,
                label=f"Trail @ {line_price:.2f}"
            )
            logger.info(f"Added Trailing Stop at {line_price:.2f}")
    def _clear_all_markers(self):
        """Clear all entry and structure markers."""
        self.clear_entry_markers()
        self.clear_structure_breaks()
        logger.info("Cleared all markers")
    def _clear_all_markings(self):
        """Clear all chart markings."""
        self._clear_all_markers()
        self.clear_zones()
        self.clear_stop_loss_lines()
        logger.info("Cleared all chart markings")
    def _edit_zone(self, zone):
        """Open the zone edit dialog.

        Args:
            zone: Zone object to edit
        """
        from PyQt6.QtWidgets import QMessageBox
        from src.ui.dialogs.zone_edit_dialog import ZoneEditDialog
        from src.chart_marking.models import ZoneType

        # GUARD: Check if locked
        if zone.is_locked:
            QMessageBox.warning(
                self, "Zone Locked",
                f"Zone '{zone.label or zone.id}' is locked.\n"
                "Unlock it first to edit."
            )
            return

        dialog = ZoneEditDialog(zone, self)
        result = dialog.exec()

        if result == 2:  # Delete requested
            self.remove_zone(zone.id)
            logger.info(f"Zone '{zone.label or zone.id}' deleted via edit dialog")
        elif result == 1:  # Save requested (QDialog.Accepted)
            if dialog.has_changes():
                values = dialog.get_values()

                # Update zone properties
                self._zones.update(
                    zone.id,
                    top_price=values["top_price"],
                    bottom_price=values["bottom_price"],
                )

                # Update label if changed
                if values["label"] != zone.label:
                    zone.label = values["label"]

                # Update zone type if changed
                if values["zone_type"] != zone.zone_type.value:
                    zone.zone_type = ZoneType(values["zone_type"])

                # Trigger chart update
                self._on_zones_changed()
                logger.info(f"Zone '{zone.label or zone.id}' updated")
    def _extend_zone_to_now(self, zone):
        """Extend a zone's end time to the current time.

        Args:
            zone: Zone object to extend
        """
        from PyQt6.QtWidgets import QMessageBox
        import time

        # GUARD: Check if locked
        if zone.is_locked:
            QMessageBox.warning(
                self, "Zone Locked",
                "Cannot extend locked zone."
            )
            return

        new_end_time = int(time.time())
        success = self.extend_zone(zone.id, new_end_time)
        if success:
            logger.info(f"Zone '{zone.label or zone.id}' extended to now")
    def _delete_zone(self, zone):
        """Delete a zone after confirmation.

        Args:
            zone: Zone object to delete
        """
        from PyQt6.QtWidgets import QMessageBox

        zone_label = zone.label or zone.id
        reply = QMessageBox.question(
            self, "Delete Zone",
            f"Are you sure you want to delete zone '{zone_label}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.remove_zone(zone.id)
            logger.info(f"Zone '{zone_label}' deleted")

    def _toggle_zone_lock(self, zone):
        """Toggle zone lock status.

        Args:
            zone: Zone object to toggle lock state
        """
        new_state = self._zones.toggle_locked(zone.id)
        if new_state is not None:
            status = "locked" if new_state else "unlocked"
            logger.info(f"Zone '{zone.label or zone.id}' {status}")

            # Optional: Show brief tooltip notification
            from PyQt6.QtWidgets import QToolTip
            from PyQt6.QtGui import QCursor
            QToolTip.showText(QCursor.pos(), f"Zone {status}", self, msecShowTime=1500)
