"""Bitunix-only Streaming Mixin for EmbeddedTradingViewChart.

CRITICAL: This is ONLY for Bitunix.
NO Alpaca code allowed here!
NO Bad Tick Filter needed (Bitunix ticks are already filtered by Z-Score in provider)
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import pandas as pd
from PyQt6.QtCore import pyqtSlot

from src.common.event_bus import Event
from .data_loading_mixin import get_local_timezone_offset_seconds

logger = logging.getLogger(__name__)


class BitunixStreamingMixin:
    """Mixin providing Bitunix-ONLY streaming functionality."""

    @pyqtSlot(object)
    def _on_market_bar(self, event: Event):
        """Handle market bar event."""
        try:
            # WICHTIG: Ignoriere Events wenn Streaming deaktiviert ist
            if not getattr(self, 'live_streaming_enabled', False):
                return

            bar_data = event.data
            if bar_data.get('symbol') != self.current_symbol:
                return

            # Add to pending updates (batched processing)
            self.pending_bars.append(bar_data)

        except Exception as e:
            logger.error(f"Error handling market bar: {e}")

    @pyqtSlot(object)
    def _on_market_tick(self, event: Event):
        """Handle market tick event - update current candle in real-time (BITUNIX ONLY).

        NO BAD TICK FILTER - Bitunix ticks are already filtered by Z-Score in provider.
        """
        try:
            tick_data = self._validate_tick_event(event)
            if not tick_data:
                return

            price, volume = self._extract_tick_price_volume(tick_data)
            if not price:
                logger.warning(f"Received tick for {self.current_symbol} but no price data")
                return

            # BITUNIX: NO Bad Tick Filter needed - already filtered in provider
            self._log_tick(price, volume)

            ts = self._resolve_tick_timestamp(event, tick_data)
            current_tick_time, current_minute_start = self._resolve_tick_time(ts, tick_data)

            if not hasattr(self, '_current_candle_time'):
                self._initialize_candle(current_minute_start, price)

            self._update_candle_for_tick(current_minute_start, price)
            self._accumulate_volume(volume)
            self._current_candle_close = price
            self._last_price = price

            candle = self._build_candle_payload(price)
            volume_bar = self._build_volume_payload(price)

            self._execute_chart_updates(candle, volume_bar)
            self._update_indicators_realtime(candle)
            self._emit_tick_price_updated(price)

        except Exception as e:
            logger.error(f"Error handling Bitunix market tick: {e}", exc_info=True)

    def _validate_tick_event(self, event: Event) -> dict | None:
        if not getattr(self, 'live_streaming_enabled', False):
            return None
        tick_data = event.data
        if tick_data.get('symbol') != self.current_symbol:
            return None
        return tick_data

    def _extract_tick_price_volume(self, tick_data: dict) -> tuple[float, float]:
        price = tick_data.get('price', 0)
        volume = tick_data.get('volume', tick_data.get('size', 0))
        return price, volume

    def _log_tick(self, price: float, volume: float) -> None:
        self.info_label.setText(f"Last: ${price:.2f}")
        print(f"📊 BITUNIX TICK: {self.current_symbol} @ ${price:.2f} vol={volume}")
        logger.info(f"📊 Bitunix live tick: {self.current_symbol} @ ${price:.2f}")

        # Update Bitunix Trading API Widget with live price
        # Widget is in parent ChartWindow, not in chart itself
        parent = self.parent()
        if parent and hasattr(parent, 'bitunix_trading_api_widget'):
            if parent.bitunix_trading_api_widget:
                parent.bitunix_trading_api_widget.set_price(price)
                logger.debug(f"Updated trading API widget with price: {price:.2f}")

        # Update Recent Signals table and Current Position widget
        if parent and hasattr(parent, '_update_current_price_in_signals'):
            parent._update_current_price_in_signals(price)
            logger.debug(f"Updated signals table with price: {price:.2f}")

        if parent and hasattr(parent, '_update_current_price_in_position'):
            parent._update_current_price_in_position(price)
            logger.debug(f"Updated position widget with price: {price:.2f}")

    def _resolve_tick_timestamp(self, event: Event, tick_data: dict):
        ts = tick_data.get('timestamp')
        if ts is None:
            ts = event.timestamp
        if ts is None:
            ts = datetime.now(timezone.utc)
        if isinstance(ts, str):
            try:
                ts = pd.to_datetime(ts).to_pydatetime()
            except Exception:
                ts = datetime.now(timezone.utc)
        elif isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts, tz=timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts

    def _get_resolution_seconds(self) -> int:
        """Get current chart timeframe resolution in seconds.

        Maps timeframe string (e.g., "5T") to seconds (e.g., 300).
        """
        timeframe_to_seconds = {
            "1S": 1,       # 1 second
            "1T": 60,      # 1 minute
            "5T": 300,     # 5 minutes
            "10T": 600,    # 10 minutes
            "15T": 900,    # 15 minutes
            "30T": 1800,   # 30 minutes
            "1H": 3600,    # 1 hour
            "2H": 7200,    # 2 hours
            "4H": 14400,   # 4 hours
            "8H": 28800,   # 8 hours
            "1D": 86400,   # 1 day
        }
        current_tf = getattr(self, 'current_timeframe', '1T')
        return timeframe_to_seconds.get(current_tf, 60)

    def _resolve_tick_time(self, ts, tick_data: dict) -> tuple[int, int]:
        local_offset = get_local_timezone_offset_seconds()
        current_tick_time = int(ts.timestamp()) + local_offset
        # Use chart's actual resolution instead of hardcoded 60 seconds
        resolution_seconds = self._get_resolution_seconds()
        current_candle_start = current_tick_time - (current_tick_time % resolution_seconds)
        logger.debug(
            f"BITUNIX TICK DEBUG: Raw TS: {tick_data.get('timestamp')} | Resolved TS: {ts} | "
            f"TickUnix: {current_tick_time} | CandleStart: {current_candle_start} | Resolution: {resolution_seconds}s"
        )
        return current_tick_time, current_candle_start

    def _initialize_candle(self, current_minute_start: int, price: float) -> None:
        """Initialize candle state for streaming.

        Issue #4 Fix: When starting streaming mid-candle, use the historical data's
        OHLC values for the current candle time if available, instead of just using
        the first tick price (which creates a "flat" candle).
        """
        self._current_candle_time = current_minute_start

        # Issue #4: Check if we have historical data for this candle time
        # If so, use that candle's OHLC as the base instead of just the tick price
        historical_candle = self._get_historical_candle_at_time(current_minute_start)
        if historical_candle:
            # Use historical OHLC as base, but update close with current price
            self._current_candle_open = historical_candle['open']
            self._current_candle_high = max(historical_candle['high'], price)
            self._current_candle_low = min(historical_candle['low'], price)
            self._current_candle_volume = historical_candle.get('volume', 0)
            logger.info(
                f"Issue #4: Initialized candle from historical data at {current_minute_start}: "
                f"O={self._current_candle_open:.2f} H={self._current_candle_high:.2f} "
                f"L={self._current_candle_low:.2f} (tick price={price:.2f})"
            )
        else:
            # No historical data - use tick price as base (first candle scenario)
            self._current_candle_open = price
            self._current_candle_high = price
            self._current_candle_low = price
            self._current_candle_volume = 0

    def _get_historical_candle_at_time(self, candle_time: int) -> dict | None:
        """Get historical candle data for a specific time if available.

        Issue #4: Used to merge streaming data with historical data.

        Args:
            candle_time: Unix timestamp of candle start

        Returns:
            Dict with 'open', 'high', 'low', 'close', 'volume' or None if not found
        """
        try:
            if not hasattr(self, 'data') or self.data is None or len(self.data) == 0:
                return None

            # Convert DataFrame timestamps to check if we have this candle
            if 'time' in self.data.columns:
                # Data has 'time' column with unix timestamps
                matching_rows = self.data[self.data['time'] == candle_time]
                if not matching_rows.empty:
                    row = matching_rows.iloc[-1]
                    return {
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row.get('volume', 0))
                    }
            else:
                # Data has timestamp index
                from datetime import datetime, timezone
                candle_dt = datetime.fromtimestamp(candle_time, tz=timezone.utc)
                if candle_dt in self.data.index:
                    row = self.data.loc[candle_dt]
                    return {
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row.get('volume', 0))
                    }
        except Exception as e:
            logger.debug(f"Could not get historical candle at {candle_time}: {e}")
        return None

    def _update_candle_for_tick(self, current_minute_start: int, price: float) -> None:
        if current_minute_start > self._current_candle_time:
            prev_open = getattr(self, '_current_candle_open', price)
            prev_high = getattr(self, '_current_candle_high', price)
            prev_low = getattr(self, '_current_candle_low', price)
            prev_close = getattr(self, '_current_candle_close', price)
            prev_volume = getattr(self, '_current_candle_volume', 0)

            self._prev_candle_volume = prev_volume

            if hasattr(self, 'candle_closed'):
                self.candle_closed.emit(prev_open, prev_high, prev_low, prev_close, price)
                logger.info(
                    f"🕯️ Bitunix candle closed: O={prev_open:.2f} H={prev_high:.2f} "
                    f"L={prev_low:.2f} C={prev_close:.2f} V={prev_volume:.0f} -> new_open={price:.2f}"
                )

            self._current_candle_time = current_minute_start
            self._current_candle_open = price
            self._current_candle_high = price
            self._current_candle_low = price
            self._current_candle_volume = 0
            return

        self._current_candle_high = max(self._current_candle_high, price)
        self._current_candle_low = min(self._current_candle_low, price)

    def _accumulate_volume(self, volume: float) -> None:
        if volume:
            self._current_candle_volume += volume

    def _build_candle_payload(self, price: float) -> dict:
        return {
            'time': self._current_candle_time,
            'open': float(self._current_candle_open),
            'high': float(self._current_candle_high),
            'low': float(self._current_candle_low),
            'close': float(price),
        }

    def _build_volume_payload(self, price: float) -> dict:
        return {
            'time': self._current_candle_time,
            'value': float(self._current_candle_volume),
            'color': '#26a69a' if price >= self._current_candle_open else '#ef5350'
        }

    def _execute_chart_updates(self, candle: dict, volume_bar: dict) -> None:
        candle_json = json.dumps(candle)
        volume_json = json.dumps(volume_bar)
        # Issue #4: updateCandle now auto-scales the Y axis
        self._execute_js(f"window.chartAPI.updateCandle({candle_json});")
        self._execute_js(f"window.chartAPI.updatePanelData('volume', {volume_json});")

    def _emit_tick_price_updated(self, price: float) -> None:
        if hasattr(self, 'tick_price_updated'):
            self.tick_price_updated.emit(price)
            if not hasattr(self, '_tick_emit_count'):
                self._tick_emit_count = 0
            self._tick_emit_count += 1
            if self._tick_emit_count % 100 == 1:
                logger.info(f"📡 Bitunix tick_price_updated emitted #{self._tick_emit_count}: {price:.2f}")

    def _process_pending_updates(self):
        """Process pending bar updates (batched for performance)."""
        if not self.pending_bars:
            return

        try:
            # Get resolution for time alignment
            resolution_seconds = self._get_resolution_seconds()
            local_offset = get_local_timezone_offset_seconds()

            # Process all pending bars
            while self.pending_bars:
                bar_data = self.pending_bars.popleft()

                ts_raw = bar_data.get('timestamp', datetime.now())
                # Robust parsing: handle str/np datetime/pandas Timestamp
                try:
                    if isinstance(ts_raw, str):
                        ts_parsed = pd.to_datetime(ts_raw)
                        ts_value = ts_parsed.to_pydatetime() if hasattr(ts_parsed, "to_pydatetime") else datetime.now()
                    elif hasattr(ts_raw, "to_pydatetime"):
                        ts_value = ts_raw.to_pydatetime()
                    else:
                        ts_value = ts_raw
                    unix_time = int(pd.Timestamp(ts_value).timestamp()) + local_offset
                except Exception:
                    unix_time = int(datetime.now().timestamp()) + local_offset

                # CRITICAL FIX: Align time to candle boundaries (clock time)
                # e.g., for 5-minute candles: 15:07 -> 15:05, 15:03 -> 15:00
                aligned_time = unix_time - (unix_time % resolution_seconds)

                candle = {
                    'time': aligned_time,
                    'open': float(bar_data.get('open', 0)),
                    'high': float(bar_data.get('high', 0)),
                    'low': float(bar_data.get('low', 0)),
                    'close': float(bar_data.get('close', 0)),
                }

                volume = {
                    'time': aligned_time,
                    'value': float(bar_data.get('volume', 0)),
                    'color': '#26a69a' if candle['close'] >= candle['open'] else '#ef5350'
                }

                # Update chart
                candle_json = json.dumps(candle)
                volume_json = json.dumps(volume)

                self._execute_js(f"window.chartAPI.updateCandle({candle_json});")
                self._execute_js(f"window.chartAPI.updatePanelData('volume', {volume_json});")

        except Exception as e:
            logger.error(f"Error processing Bitunix updates: {e}", exc_info=True)

    def _toggle_live_stream(self):
        """Toggle live streaming on/off."""
        is_checked = self.live_stream_button.isChecked()
        logger.info(f"🔄 Bitunix live stream toggle: button_checked={is_checked}, current_enabled={self.live_streaming_enabled}")

        self.live_streaming_enabled = is_checked

        if self.live_streaming_enabled:
            logger.info(f"Starting Bitunix live stream for {self.current_symbol}...")
            asyncio.ensure_future(self._start_live_stream_async())
        else:
            logger.info("Stopping Bitunix live stream...")
            asyncio.ensure_future(self._stop_live_stream_async())

    async def _start_live_stream_async(self):
        """Async wrapper for starting live stream."""
        try:
            await self._start_live_stream()

            # Issue #4: Enable auto-scaling during streaming to prevent flat candles
            self._execute_js("window.chartAPI.setStreamingAutoScale(true);")

            # Issue #17: Use theme system via checked state instead of hardcoded colors
            self.live_stream_button.setChecked(True)
            self.live_stream_button.setText("Live")
            self.market_status_label.setText("🔴 Streaming (Bitunix)...")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

        except Exception as e:
            logger.error(f"Failed to start Bitunix live stream: {e}")

    async def _stop_live_stream_async(self):
        """Async wrapper for stopping live stream."""
        try:
            await self._stop_live_stream()

            # Issue #4: Disable auto-scaling when streaming stops
            self._execute_js("window.chartAPI.setStreamingAutoScale(false);")

            # Issue #17: Use theme system via checked state instead of hardcoded colors
            self.live_stream_button.setChecked(False)
            self.live_stream_button.setText("Live")
            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")
        except Exception as e:
            logger.error(f"Failed to stop Bitunix live stream: {e}")

    async def _start_live_stream(self):
        """Start Bitunix live streaming for current symbol."""
        if not self.history_manager:
            logger.warning("No history manager available")
            self.market_status_label.setText("⚠ No data source")
            return

        if not self.current_symbol:
            logger.warning("No symbol selected")
            self.market_status_label.setText("⚠ No symbol")
            return

        try:
            logger.warning(f"🔍 START BITUNIX STREAM: symbol={self.current_symbol}")

            # BITUNIX ONLY
            logger.warning(f"📡 Starting BITUNIX stream for {self.current_symbol}")
            success = await self.history_manager.start_bitunix_stream([self.current_symbol])
            logger.info(f"✓ Bitunix stream started for {self.current_symbol}")

            if success:
                self.market_status_label.setText(f"🟢 Live (Bitunix): {self.current_symbol}")
                self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")
            else:
                logger.error("Failed to start Bitunix live stream")
                self.market_status_label.setText("⚠ Stream failed")
                self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
                self.live_stream_button.setChecked(False)
                self._toggle_live_stream()

        except Exception as e:
            logger.error(f"Error starting Bitunix live stream: {e}")
            self.market_status_label.setText(f"⚠ Error: {str(e)[:20]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
            self.live_stream_button.setChecked(False)
            self._toggle_live_stream()

    async def _stop_live_stream(self):
        """Stop Bitunix live streaming - disconnect WebSocket."""
        if not self.history_manager:
            return

        try:
            # BITUNIX ONLY: Disconnect Bitunix stream
            if hasattr(self.history_manager, 'bitunix_stream_client') and self.history_manager.bitunix_stream_client:
                await self.history_manager.bitunix_stream_client.disconnect()
                logger.info(f"✓ Disconnected Bitunix stream")

            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")

        except Exception as e:
            logger.error(f"Error disconnecting Bitunix stream: {e}")
