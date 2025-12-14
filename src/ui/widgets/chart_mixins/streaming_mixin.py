"""Streaming Mixin for EmbeddedTradingViewChart.

Contains live streaming and market event handling methods.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import pandas as pd
from PyQt6.QtCore import pyqtSlot

from src.common.event_bus import Event

logger = logging.getLogger(__name__)


class StreamingMixin:
    """Mixin providing streaming functionality for EmbeddedTradingViewChart."""

    @pyqtSlot(object)
    def _on_market_bar(self, event: Event):
        """Handle market bar event."""
        try:
            bar_data = event.data
            if bar_data.get('symbol') != self.current_symbol:
                return

            # Add to pending updates (batched processing)
            self.pending_bars.append(bar_data)

        except Exception as e:
            logger.error(f"Error handling market bar: {e}")

    @pyqtSlot(object)
    def _on_market_tick(self, event: Event):
        """Handle market tick event - update current candle in real-time."""
        try:
            tick_data = event.data
            if tick_data.get('symbol') != self.current_symbol:
                return

            # Update price in info label
            price = tick_data.get('price', 0)
            volume = tick_data.get('volume', tick_data.get('size', 0))

            if not price:
                logger.warning(f"Received tick for {self.current_symbol} but no price data")
                return

            self.info_label.setText(f"Last: ${price:.2f}")
            logger.info(f"📊 Live tick: {self.current_symbol} @ ${price:.2f}")

            # --- Time Handling Fix ---
            # Use timestamp from event, NOT system time
            ts = tick_data.get('timestamp')
            if ts is None:
                ts = event.timestamp

            if ts is None:
                ts = datetime.now(timezone.utc)

            # Ensure ts is datetime and UTC
            if isinstance(ts, str):
                try:
                    ts = pd.to_datetime(ts).to_pydatetime()
                except Exception:
                    ts = datetime.now(timezone.utc)
            elif isinstance(ts, (int, float)):
                ts = datetime.fromtimestamp(ts, tz=timezone.utc)

            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            current_tick_time = int(ts.timestamp())
            current_minute_start = current_tick_time - (current_tick_time % 60)

            # DEBUG LOGGING
            logger.info(f"LIVE TICK DEBUG: Raw TS: {tick_data.get('timestamp')} | Resolved TS: {ts} | TickUnix: {current_tick_time} | MinStart: {current_minute_start}")

            # Update current candle in real-time (Stock3 style)
            if not hasattr(self, '_current_candle_time'):
                # Initialize with current minute boundary from DATA
                self._current_candle_time = current_minute_start
                self._current_candle_open = price
                self._current_candle_high = price
                self._current_candle_low = price
                self._current_candle_volume = 0

            # Check if we need a new candle (new minute)
            if current_minute_start > self._current_candle_time:
                # New candle - reset
                self._current_candle_time = current_minute_start
                self._current_candle_open = price
                self._current_candle_high = price
                self._current_candle_low = price
                self._current_candle_volume = 0
            else:
                # Same candle - update high/low
                self._current_candle_high = max(self._current_candle_high, price)
                self._current_candle_low = min(self._current_candle_low, price)

            # Accumulate volume
            if volume:
                self._current_candle_volume += volume

            # Create candle update
            candle = {
                'time': self._current_candle_time,
                'open': float(self._current_candle_open),
                'high': float(self._current_candle_high),
                'low': float(self._current_candle_low),
                'close': float(price),
            }

            volume_bar = {
                'time': self._current_candle_time,
                'value': float(self._current_candle_volume),
                'color': '#26a69a' if price >= self._current_candle_open else '#ef5350'
            }

            # Update chart immediately (like Stock3!)
            candle_json = json.dumps(candle)
            volume_json = json.dumps(volume_bar)

            self._execute_js(f"window.chartAPI.updateCandle({candle_json});")
            self._execute_js(f"window.chartAPI.updatePanelData('volume', {volume_json});")

            # Update indicators in real-time
            self._update_indicators_realtime(candle)

        except Exception as e:
            logger.error(f"Error handling market tick: {e}", exc_info=True)

    def _process_pending_updates(self):
        """Process pending bar updates (batched for performance)."""
        if not self.pending_bars:
            return

        try:
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
                    unix_time = int(pd.Timestamp(ts_value).timestamp())
                except Exception:
                    unix_time = int(datetime.now().timestamp())

                candle = {
                    'time': unix_time,
                    'open': float(bar_data.get('open', 0)),
                    'high': float(bar_data.get('high', 0)),
                    'low': float(bar_data.get('low', 0)),
                    'close': float(bar_data.get('close', 0)),
                }

                volume = {
                    'time': unix_time,
                    'value': float(bar_data.get('volume', 0)),
                    'color': '#26a69a' if candle['close'] >= candle['open'] else '#ef5350'
                }

                # Update chart
                candle_json = json.dumps(candle)
                volume_json = json.dumps(volume)

                self._execute_js(f"window.chartAPI.updateCandle({candle_json});")
                self._execute_js(f"window.chartAPI.updatePanelData('volume', {volume_json});")

        except Exception as e:
            logger.error(f"Error processing updates: {e}", exc_info=True)

    def _toggle_live_stream(self):
        """Toggle live streaming on/off."""
        # Get current button state
        is_checked = self.live_stream_button.isChecked()

        logger.info(f"🔄 Live stream toggle clicked: button_checked={is_checked}, current_enabled={self.live_streaming_enabled}")

        # Update enabled flag
        self.live_streaming_enabled = is_checked

        if self.live_streaming_enabled:
            # Start live stream
            logger.info(f"Starting live stream for {self.current_symbol}...")

            # Get or create event loop compatible with Qt
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Try qasync loop if available
                try:
                    from qasync import QEventLoop
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        loop = QEventLoop(app)
                        asyncio.set_event_loop(loop)
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except ImportError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

            asyncio.create_task(self._start_live_stream())

            # Update button style
            self.live_stream_button.setStyleSheet("""
                QPushButton {
                    background-color: #00FF00;
                    color: black;
                    border: 2px solid #00AA00;
                    border-radius: 3px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #00CC00;
                }
            """)
            self.live_stream_button.setText("🟢 Live")
            self.market_status_label.setText("🔴 Streaming...")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

        else:
            # Stop live stream
            logger.info("Stopping live stream...")

            # Get or create event loop compatible with Qt
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Try qasync loop if available
                try:
                    from qasync import QEventLoop
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        loop = QEventLoop(app)
                        asyncio.set_event_loop(loop)
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except ImportError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

            asyncio.create_task(self._stop_live_stream())

            # Reset button style
            self.live_stream_button.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #aaa;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    color: #fff;
                }
            """)
            self.live_stream_button.setText("🔴 Live")
            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")

    async def _start_live_stream(self):
        """Start live streaming for current symbol."""
        if not self.history_manager:
            logger.warning("No history manager available")
            self.market_status_label.setText("⚠ No data source")
            return

        if not self.current_symbol:
            logger.warning("No symbol selected")
            self.market_status_label.setText("⚠ No symbol")
            return

        try:
            # Detect if crypto symbol (contains "/" like BTC/USD)
            is_crypto = "/" in self.current_symbol

            # Start appropriate real-time stream via HistoryManager
            if is_crypto:
                success = await self.history_manager.start_crypto_realtime_stream([self.current_symbol])
                logger.info(f"✓ Live crypto stream started for {self.current_symbol}")
            else:
                success = await self.history_manager.start_realtime_stream([self.current_symbol])
                logger.info(f"✓ Live stock stream started for {self.current_symbol}")

            if success:
                asset_type = "Crypto" if is_crypto else "Stock"
                self.market_status_label.setText(f"🟢 Live ({asset_type}): {self.current_symbol}")
                self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")
            else:
                logger.error("Failed to start live stream")
                self.market_status_label.setText("⚠ Stream failed")
                self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
                # Uncheck button
                self.live_stream_button.setChecked(False)
                self._toggle_live_stream()

        except Exception as e:
            logger.error(f"Error starting live stream: {e}")
            self.market_status_label.setText(f"⚠ Error: {str(e)[:20]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
            # Uncheck button
            self.live_stream_button.setChecked(False)
            self._toggle_live_stream()

    async def _stop_live_stream(self):
        """Stop live streaming for this symbol."""
        if not self.history_manager or not self.current_symbol:
            return

        try:
            # Unsubscribe only this symbol (don't stop entire stream)
            is_crypto = "/" in self.current_symbol

            if is_crypto:
                # Unsubscribe from crypto stream
                if hasattr(self.history_manager, 'crypto_stream_client') and self.history_manager.crypto_stream_client:
                    await self.history_manager.crypto_stream_client.unsubscribe([self.current_symbol])
                    logger.info(f"✓ Unsubscribed {self.current_symbol} from crypto stream")
            else:
                # Unsubscribe from stock stream
                if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
                    await self.history_manager.stream_client.unsubscribe([self.current_symbol])
                    logger.info(f"✓ Unsubscribed {self.current_symbol} from stock stream")

            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")

        except Exception as e:
            logger.error(f"Error unsubscribing {self.current_symbol} from stream: {e}")
