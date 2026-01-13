"""Event Bus Mixin for ChartWindow.

Contains event bus integration for live trade markers.
"""

import json
import logging

from src.common.event_bus import event_bus, EventType, ExecutionEvent, OrderEvent
from src.ui.widgets.chart_mixins.data_loading_mixin import get_local_timezone_offset_seconds

logger = logging.getLogger(__name__)


def _ts_to_chart_time(timestamp) -> int:
    """Convert timestamp to chart time (UTC).

    Issue #52 fix: Handles both timezone-aware and naive datetimes.
    Naive datetimes are interpreted as LOCAL time, then converted to UTC.
    This fixes the 53-minute offset bug where entry points were marked too early.
    """
    from datetime import timezone
    import time

    if timestamp.tzinfo is None:
        # Issue #52: Interpret naive datetime as LOCAL time, not UTC
        # Get local timezone offset
        if time.daylight and time.localtime().tm_isdst > 0:
            local_offset_seconds = -time.altzone
        else:
            local_offset_seconds = -time.timezone

        # Create timezone-aware datetime with local offset
        from datetime import timedelta
        local_tz = timezone(timedelta(seconds=local_offset_seconds))
        timestamp = timestamp.replace(tzinfo=local_tz)

    return int(timestamp.timestamp())


class EventBusMixin:
    """Mixin providing event bus integration for ChartWindow."""

    def _setup_event_subscriptions(self):
        """Subscribe to event bus for live trade marker updates."""
        try:
            event_bus.subscribe(EventType.TRADE_ENTRY, self._on_trade_entry)
            event_bus.subscribe(EventType.TRADE_EXIT, self._on_trade_exit)
            event_bus.subscribe(EventType.STOP_LOSS_HIT, self._on_stop_loss_hit)
            event_bus.subscribe(EventType.TAKE_PROFIT_HIT, self._on_take_profit_hit)
            event_bus.subscribe(EventType.ORDER_FILLED, self._on_order_filled)
            event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar)

            # Connect to chart widget's symbol change signal
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'signals'):
                self.chart_widget.signals.symbolChanged.connect(self._on_chart_symbol_changed)
                logger.debug("Connected to chart symbolChanged signal")

            logger.info(f"Event bus subscriptions established for {self.symbol} chart")

        except Exception as e:
            logger.error(f"Failed to set up event subscriptions: {e}", exc_info=True)

    def _on_chart_symbol_changed(self, new_symbol: str) -> None:
        """Handle symbol change in chart - update bot panel settings.

        Args:
            new_symbol: The new symbol that was selected
        """
        logger.info(f"Chart symbol changed to: {new_symbol}")

        # Update window title
        self.setWindowTitle(f"Chart - {new_symbol}")
        self.symbol = new_symbol

        # Update bot panel if available
        if hasattr(self, 'update_bot_symbol'):
            self.update_bot_symbol(new_symbol)

    def _on_trade_entry(self, event: ExecutionEvent):
        """Handle TRADE_ENTRY event - add entry marker to chart."""
        try:
            if event.symbol != self.symbol:
                return

            logger.info(f"TRADE_ENTRY event: {event.side} {event.quantity} @ {event.price}")

            marker = {
                "time": _ts_to_chart_time(event.timestamp),
                "position": "belowBar" if event.side == "LONG" else "aboveBar",
                "color": "#26a69a" if event.side == "LONG" else "#ef5350",
                "shape": "arrowUp" if event.side == "LONG" else "arrowDown",
                "text": f"{event.side} @ €{event.price:.2f}"
            }

            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling TRADE_ENTRY event: {e}", exc_info=True)

    def _on_trade_exit(self, event: ExecutionEvent):
        """Handle TRADE_EXIT event - add exit marker to chart."""
        try:
            if event.symbol != self.symbol:
                return

            logger.info(f"TRADE_EXIT event: {event.side} exit @ {event.price}, P/L: {event.pnl_pct:.2f}%")

            is_win = event.pnl is not None and event.pnl > 0

            marker = {
                "time": _ts_to_chart_time(event.timestamp),
                "position": "aboveBar" if event.side == "LONG" else "belowBar",
                "color": "#26a69a" if is_win else "#ef5350",
                "shape": "circle",
                "text": f"EXIT @ €{event.price:.2f} ({event.pnl_pct:+.2f}%)" if event.pnl_pct else f"EXIT @ €{event.price:.2f}"
            }

            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling TRADE_EXIT event: {e}", exc_info=True)

    def _on_stop_loss_hit(self, event: ExecutionEvent):
        """Handle STOP_LOSS_HIT event - add SL marker to chart."""
        try:
            if event.symbol != self.symbol:
                return

            logger.warning(f"STOP_LOSS_HIT event: {event.side} @ {event.price}")

            marker = {
                "time": _ts_to_chart_time(event.timestamp),
                "position": "aboveBar",
                "color": "#ef5350",
                "shape": "circle",
                "text": f"STOP LOSS @ €{event.price:.2f} ({event.pnl_pct:+.2f}%)" if event.pnl_pct else f"STOP LOSS @ €{event.price:.2f}"
            }

            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling STOP_LOSS_HIT event: {e}", exc_info=True)

    def _on_take_profit_hit(self, event: ExecutionEvent):
        """Handle TAKE_PROFIT_HIT event - add TP marker to chart."""
        try:
            if event.symbol != self.symbol:
                return

            logger.info(f"TAKE_PROFIT_HIT event: {event.side} @ {event.price}")

            marker = {
                "time": _ts_to_chart_time(event.timestamp),
                "position": "aboveBar",
                "color": "#26a69a",
                "shape": "circle",
                "text": f"TAKE PROFIT @ €{event.price:.2f} (+{event.pnl_pct:.2f}%)" if event.pnl_pct else f"TAKE PROFIT @ €{event.price:.2f}"
            }

            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling TAKE_PROFIT_HIT event: {e}", exc_info=True)

    def _on_order_filled(self, event: OrderEvent):
        """Handle ORDER_FILLED event - add fill marker to chart."""
        try:
            if event.symbol != self.symbol:
                return

            logger.info(f"ORDER_FILLED event: {event.side} {event.filled_quantity} @ {event.avg_fill_price}")

            is_buy = event.side and event.side.upper() in ["BUY", "LONG"]

            marker = {
                "time": _ts_to_chart_time(event.timestamp),
                "position": "belowBar" if is_buy else "aboveBar",
                "color": "#26a69a" if is_buy else "#ef5350",
                "shape": "arrowUp" if is_buy else "arrowDown",
                "text": f"{'BUY' if is_buy else 'SELL'} {event.filled_quantity} @ €{event.avg_fill_price:.2f}"
            }

            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling ORDER_FILLED event: {e}", exc_info=True)

    def _on_market_bar(self, event):
        """Handle MARKET_BAR event - update chart with real-time data."""
        try:
            if event.data.get("symbol") != self.symbol:
                return

            logger.debug(f"MARKET_BAR event: {event.data.get('symbol')}")

            # Bar data for chart (JSON-serializable)
            bar_data = {
                "time": _ts_to_chart_time(event.timestamp),
                "open": event.data.get("open"),
                "high": event.data.get("high"),
                "low": event.data.get("low"),
                "close": event.data.get("close"),
                "volume": event.data.get("volume", 0)
            }

            self._update_chart_bar(bar_data)

            # NOTE: Do NOT feed bars to bot here!
            # The bot should only receive completed candles via candle_closed signal
            # (handled in bot_callbacks.py -> _on_chart_candle_closed)
            # Feeding on every MARKET_BAR would trigger SL checks on intrabar ticks

        except Exception as e:
            logger.error(f"Error handling MARKET_BAR event: {e}", exc_info=True)

    def _feed_bar_to_bot(self, bar_data: dict):
        """Feed bar data to the trading bot if active.

        Args:
            bar_data: Bar data dictionary with OHLCV
        """
        # Check if bot controller exists and is running
        if not hasattr(self, '_bot_controller') or self._bot_controller is None:
            return

        if not self._bot_controller._running:
            return

        try:
            # Use qasync-compatible async scheduling
            import asyncio
            # ensure_future works with qasync event loop
            asyncio.ensure_future(self._bot_controller.on_bar(bar_data))
        except Exception as e:
            logger.error(f"Error feeding bar to bot: {e}")

    def _update_chart_bar(self, bar_data: dict):
        """Update the chart with a new real-time bar."""
        try:
            if not hasattr(self.chart_widget, '_execute_js'):
                logger.warning("Chart widget doesn't support JavaScript execution")
                return

            bar_json = json.dumps(bar_data)
            js_command = f"window.chartAPI.updateBar({bar_json});"
            self.chart_widget._execute_js(js_command)

            logger.debug(f"Chart updated with real-time bar: {bar_data['time']}")

        except Exception as e:
            logger.error(f"Error updating chart with bar: {e}", exc_info=True)

    def _add_single_marker(self, marker: dict):
        """Add a single marker to the chart in real-time."""
        try:
            if not hasattr(self.chart_widget, '_execute_js'):
                logger.warning("Chart widget doesn't support JavaScript execution")
                return

            marker_json = json.dumps([marker])
            js_command = f"window.chartAPI.addTradeMarkers({marker_json});"
            self.chart_widget._execute_js(js_command)

            logger.debug(f"Marker added to chart: {marker['text']}")

        except Exception as e:
            logger.error(f"Error adding marker to chart: {e}", exc_info=True)

    def _unsubscribe_events(self):
        """Unsubscribe from all event bus events."""
        try:
            event_bus.unsubscribe(EventType.TRADE_ENTRY, self._on_trade_entry)
            event_bus.unsubscribe(EventType.TRADE_EXIT, self._on_trade_exit)
            event_bus.unsubscribe(EventType.STOP_LOSS_HIT, self._on_stop_loss_hit)
            event_bus.unsubscribe(EventType.TAKE_PROFIT_HIT, self._on_take_profit_hit)
            event_bus.unsubscribe(EventType.ORDER_FILLED, self._on_order_filled)
            event_bus.unsubscribe(EventType.MARKET_BAR, self._on_market_bar)

            logger.info(f"Event bus unsubscribed for {self.symbol} chart")

        except Exception as e:
            logger.error(f"Error unsubscribing from events: {e}", exc_info=True)
