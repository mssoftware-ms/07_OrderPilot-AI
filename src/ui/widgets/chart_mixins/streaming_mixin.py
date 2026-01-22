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
from .data_loading_mixin import get_local_timezone_offset_seconds

logger = logging.getLogger(__name__)


class StreamingMixin:
    """Mixin providing streaming functionality for EmbeddedTradingViewChart."""

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

    def _is_valid_tick(self, price: float, reference_price: float | None) -> bool:
        """
        Prüfe ob Tick-Preis plausibel ist (Bad Tick Filter).

        Filtert extreme Ausreißer die durch fehlerhafte Daten entstehen.

        Args:
            price: Neuer Tick-Preis
            reference_price: Referenzpreis (letzter bekannter gültiger Preis)

        Returns:
            True wenn Tick plausibel, False wenn Bad Tick
        """
        if price <= 0:
            return False

        if reference_price is None or reference_price <= 0:
            return True  # Kein Referenzpreis - akzeptiere

        # Maximale erlaubte Abweichung vom Referenzpreis (5%)
        # Bei sehr volatilen Assets könnte man das erhöhen
        max_deviation_pct = 5.0

        deviation_pct = abs((price - reference_price) / reference_price) * 100

        if deviation_pct > max_deviation_pct:
            logger.warning(
                f"Bad tick filtered: {self.current_symbol} price={price:.2f} "
                f"deviates {deviation_pct:.1f}% from reference={reference_price:.2f}"
            )
            return False

        return True

    @pyqtSlot(object)
    def _on_market_tick(self, event: Event):
        """Handle market tick event - update current candle in real-time."""
        try:
            tick_data = self._validate_tick_event(event)
            if not tick_data:
                return

            price, volume = self._extract_tick_price_volume(tick_data)
            if not price:
                logger.warning(f"Received tick for {self.current_symbol} but no price data")
                return

            # Bitunix ticks are already filtered by Z-Score filter in provider
            # Only apply 5% deviation filter to Alpaca ticks (which can have bad ticks)
            try:
                source = str(getattr(event, 'source', ''))
                is_bitunix = source.lower() == 'bitunix stream'
            except (AttributeError, TypeError):
                is_bitunix = False

            if not is_bitunix:
                reference_price = self._resolve_reference_price()
                if not self._is_valid_tick(price, reference_price):
                    return

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

            # Issue #26: Update price labels on tick
            if hasattr(self, 'update_last_price_label'):
                try:
                    self.update_last_price_label(price)
                except Exception as e:
                    logger.warning(f"Failed to update last price label: {e}")
            if hasattr(self, 'update_price_label'):
                try:
                    self.update_price_label(price)
                except Exception as e:
                    logger.warning(f"Failed to update price label: {e}")

        except Exception as e:
            logger.error(f"Error handling market tick: {e}", exc_info=True)

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

    def _resolve_reference_price(self) -> float | None:
        reference_price = getattr(self, '_current_candle_close', None)
        if reference_price is None and hasattr(self, 'data') and self.data is not None:
            if len(self.data) > 0 and 'close' in self.data.columns:
                reference_price = float(self.data['close'].iloc[-1])
        return reference_price

    def _log_tick(self, price: float, volume: float) -> None:
        self.info_label.setText(f"Last: ${price:.2f}")
        print(f"📊 TICK: {self.current_symbol} @ ${price:.2f} vol={volume}")
        # logger.info removed - print statement is sufficient

        # Forward live price into Signals tab (Bitunix Trading API + tables)
        parent = self.parent()
        if parent and hasattr(parent, 'bitunix_trading_api_widget'):
            try:
                parent.bitunix_trading_api_widget.set_price(price)
            except Exception:
                logger.debug("Failed to push price into BitunixTradingAPIWidget", exc_info=True)

        if parent and hasattr(parent, '_update_current_price_in_signals'):
            try:
                parent._update_current_price_in_signals(price)
            except Exception:
                logger.debug("Failed to push price into signals table", exc_info=True)

        if parent and hasattr(parent, '_update_current_price_in_position'):
            try:
                parent._update_current_price_in_position(price)
            except Exception:
                logger.debug("Failed to push price into current position widget", exc_info=True)

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
        # Verbose debug logging removed - not needed for normal operation
        # logger.debug(f"LIVE TICK DEBUG: Raw TS: {tick_data.get('timestamp')} | Resolved TS: {ts} | "
        #              f"TickUnix: {current_tick_time} | CandleStart: {current_candle_start} | Resolution: {resolution_seconds}s")
        return current_tick_time, current_candle_start

    def _initialize_candle(self, current_minute_start: int, price: float) -> None:
        self._current_candle_time = current_minute_start
        self._current_candle_open = price
        self._current_candle_high = price
        self._current_candle_low = price
        self._current_candle_volume = 0

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
                    f"🕯️ Candle closed: O={prev_open:.2f} H={prev_high:.2f} "
                    f"L={prev_low:.2f} C={prev_close:.2f} V={prev_volume:.0f} -> new_open={price:.2f}"
                )

                # Update Entry Analyzer if available
                if hasattr(self, 'on_new_candle_received'):
                    # Calculate timestamp for the closed candle
                    # current_minute_start is the NEW candle start.
                    # Closed candle start should be previous period.
                    # But actually we just need a dict with the closed values.
                    # The timestamp is tricky here without resolution.
                    # Assuming standard sequential bars.
                    # Use _current_candle_time which was the START of the closed candle
                    # BEFORE it was updated to current_minute_start below.
                    
                    # Wait, _current_candle_time is updated AFTER this block?
                    # No, self._current_candle_time holds the start of the candle being closed.
                    closed_candle_time = self._current_candle_time
                    
                    closed_candle = {
                        'timestamp': closed_candle_time,
                        'open': prev_open,
                        'high': prev_high,
                        'low': prev_low,
                        'close': prev_close,
                        'volume': prev_volume
                    }
                    self.on_new_candle_received(closed_candle)

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
        # Issue #40, #47: Use custom colors from settings (same as initial load)
        from .data_loading_series import _get_volume_colors
        vol_colors = _get_volume_colors()
        is_bullish = price >= self._current_candle_open
        return {
            'time': self._current_candle_time,
            'value': float(self._current_candle_volume),
            'color': vol_colors['bullish'] if is_bullish else vol_colors['bearish']
        }

    def _execute_chart_updates(self, candle: dict, volume_bar: dict) -> None:
        candle_json = json.dumps(candle)
        volume_json = json.dumps(volume_bar)
        self._execute_js(f"window.chartAPI.updateCandle({candle_json});")
        self._execute_js(f"window.chartAPI.updatePanelData('volume', {volume_json});")

    def _emit_tick_price_updated(self, price: float) -> None:
        if hasattr(self, 'tick_price_updated'):
            self.tick_price_updated.emit(price)
            if not hasattr(self, '_tick_emit_count'):
                self._tick_emit_count = 0
            self._tick_emit_count += 1
            if self._tick_emit_count % 100 == 1:
                logger.info(f"📡 tick_price_updated emitted #{self._tick_emit_count}: {price:.2f}")

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

                # Issue #40, #47: Use custom colors from settings
                from .data_loading_series import _get_volume_colors
                vol_colors = _get_volume_colors()
                is_bullish = candle['close'] >= candle['open']
                volume = {
                    'time': aligned_time,
                    'value': float(bar_data.get('volume', 0)),
                    'color': vol_colors['bullish'] if is_bullish else vol_colors['bearish']
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
            # Start live stream - schedule async without blocking
            logger.info(f"Starting live stream for {self.current_symbol}...")
            asyncio.ensure_future(self._start_live_stream_async())
        else:
            # Stop live stream - schedule async without blocking
            logger.info("Stopping live stream...")
            asyncio.ensure_future(self._stop_live_stream_async())

    async def _start_live_stream_async(self):
        """Async wrapper for starting live stream."""
        try:
            await self._start_live_stream()

            # Issue #17: Use theme system via checked state instead of hardcoded colors
            self.live_stream_button.setChecked(True)
            self.live_stream_button.setText("Live")
            self.market_status_label.setText("🔴 Streaming...")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

        except Exception as e:
            logger.error(f"Failed to start live stream: {e}")

    async def _stop_live_stream_async(self):
        """Async wrapper for stopping live stream."""
        try:
            await self._stop_live_stream()

            # Issue #17: Use theme system via checked state instead of hardcoded colors
            self.live_stream_button.setChecked(False)
            self.live_stream_button.setText("Live")
            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")
        except Exception as e:
            logger.error(f"Failed to stop live stream: {e}")

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
            # Detect symbol type
            is_bitunix = "USDT" in self.current_symbol or "USDC" in self.current_symbol
            is_alpaca_crypto = "/" in self.current_symbol
            is_stock = not is_bitunix and not is_alpaca_crypto

            logger.warning(
                f"🔍 START STREAM: symbol={self.current_symbol}, "
                f"bitunix={is_bitunix}, alpaca_crypto={is_alpaca_crypto}, stock={is_stock}"
            )

            # Start appropriate real-time stream via HistoryManager
            if is_bitunix:
                logger.warning(f"📡 Starting BITUNIX stream for {self.current_symbol}")
                success = await self.history_manager.start_bitunix_stream([self.current_symbol])
                logger.info(f"✓ Live Bitunix stream started for {self.current_symbol}")
            elif is_alpaca_crypto:
                logger.warning(f"📡 Starting ALPACA CRYPTO stream for {self.current_symbol}")
                success = await self.history_manager.start_crypto_realtime_stream([self.current_symbol])
                logger.info(f"✓ Live Alpaca crypto stream started for {self.current_symbol}")
            else:
                logger.warning(f"📡 Starting STOCK stream for {self.current_symbol}")
                success = await self.history_manager.start_realtime_stream([self.current_symbol])
                logger.info(f"✓ Live stock stream started for {self.current_symbol}")

            if success:
                if is_bitunix:
                    asset_type = "Bitunix"
                elif is_alpaca_crypto:
                    asset_type = "Crypto"
                else:
                    asset_type = "Stock"
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
        """Stop live streaming - disconnect WebSocket to free connection slot."""
        if not self.history_manager:
            return

        try:
            is_bitunix = "USDT" in self.current_symbol or "USDC" in self.current_symbol if self.current_symbol else False
            is_alpaca_crypto = "/" in self.current_symbol if self.current_symbol else False

            if is_bitunix:
                # Disconnect Bitunix stream
                if hasattr(self.history_manager, 'bitunix_stream_client') and self.history_manager.bitunix_stream_client:
                    await self.history_manager.bitunix_stream_client.disconnect()
                    logger.info(f"✓ Disconnected Bitunix stream")
            elif is_alpaca_crypto:
                # Disconnect Alpaca crypto stream
                if hasattr(self.history_manager, 'crypto_stream_client') and self.history_manager.crypto_stream_client:
                    await self.history_manager.crypto_stream_client.disconnect()
                    logger.info(f"✓ Disconnected crypto stream")
            else:
                # Disconnect stock stream completely to free connection
                if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
                    await self.history_manager.stream_client.disconnect()
                    logger.info(f"✓ Disconnected stock stream")

            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")

        except Exception as e:
            logger.error(f"Error disconnecting stream: {e}")
