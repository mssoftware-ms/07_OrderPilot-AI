"""Streaming Mixin for EmbeddedTradingViewChart.

Contains live streaming and market event handling methods.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

import pandas as pd
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMessageBox

from src.common.event_bus import Event
from src.core.market_data.errors import MarketDataAccessBlocked
from src.core.market_data.types import AssetClass, DataSource
from .data_loading_mixin import get_local_timezone_offset_seconds

logger = logging.getLogger(__name__)


class StreamingMixin:
    """Mixin providing streaming functionality for EmbeddedTradingViewChart.
    
    This mixin is intended to be used with EmbeddedTradingViewChart.
    Event handling is decoupled via Qt Signals in the main class to ensure
    thread-safe UI updates.
    """

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
        """
        if price <= 0:
            return False

        if reference_price is None or reference_price <= 0:
            return True

        # Maximale erlaubte Abweichung vom Referenzpreis (5%)
        max_deviation_pct = 5.0
        deviation_pct = abs((price - reference_price) / reference_price) * 100

        if deviation_pct > max_deviation_pct:
            logger.warning(
                f"Bad tick filtered: {self.current_symbol} price={price:.2f} "
                f"deviates {deviation_pct:.1f}% from reference={reference_price:.2f}"
            )
            return False

        return True

    def _on_market_tick(self, event: Event):
        """Handle market tick event - update current candle in real-time.
        
        This method is called in the MAIN UI THREAD via Qt signals.
        """
        try:
            tick_data = self._validate_tick_event(event)
            if not tick_data:
                return

            price, volume = self._extract_tick_price_volume(tick_data)
            if not price:
                return

            reference_price = self._resolve_reference_price()
            if not self._is_valid_tick(price, reference_price):
                return

            # Throttling: Update chart max 4 times per second (250ms)
            # Critical to prevent UI freezes during high-frequency bursts
            current_time = time.time()
            if not hasattr(self, '_last_chart_update_time'):
                self._last_chart_update_time = 0
                
            if (current_time - self._last_chart_update_time) < 0.25:
                # Still update internal state even if we skip the visual update
                self._update_internal_state(event, tick_data, price, volume)
                return

            self._last_chart_update_time = current_time

            # Full update
            self._update_internal_state(event, tick_data, price, volume)
            
            candle = self._build_candle_payload(price)
            volume_bar = self._build_volume_payload(price)

            self._execute_chart_updates(candle, volume_bar)
            self._update_indicators_realtime(candle)
            self._emit_tick_price_updated(price)

        except Exception as e:
            logger.error(f"Error handling market tick: {e}")

    def _update_internal_state(self, event, tick_data, price, volume):
        """Update internal candle state without necessarily updating the chart."""
        ts = self._resolve_tick_timestamp(event, tick_data)
        _, current_minute_start = self._resolve_tick_time(ts, tick_data)

        if not hasattr(self, '_current_candle_time'):
            self._initialize_candle(current_minute_start, price)

        self._update_candle_for_tick(current_minute_start, price, tick_data)
        self._accumulate_volume(volume)
        self._current_candle_close = price
        self._last_price = price
        
        # Fast UI label update
        if hasattr(self, 'info_label'):
            self.info_label.setText(f"Last: ${price:.2f}")

    def _validate_tick_event(self, event: Event) -> dict | None:
        if not getattr(self, 'live_streaming_enabled', False):
            return None
        tick_data = getattr(event, 'data', {})
        if tick_data.get('symbol') != self.current_symbol:
            return None
        return tick_data

    def _extract_tick_price_volume(self, tick_data: dict) -> tuple[float, float]:
        price = tick_data.get('price', 0)
        volume = tick_data.get('volume', tick_data.get('size', 0))
        return float(price), float(volume)

    def _resolve_reference_price(self) -> float | None:
        reference_price = getattr(self, '_current_candle_close', None)
        if reference_price is None and hasattr(self, 'data') and self.data is not None:
            if not self.data.empty and 'close' in self.data.columns:
                reference_price = float(self.data['close'].iloc[-1])
        return reference_price

    def _log_tick(self, price: float, volume: float) -> None:
        """Deprecated: Logging moved to DEBUG or removed for performance."""
        pass

    def _resolve_tick_timestamp(self, event: Event, tick_data: dict):
        ts = tick_data.get('timestamp')
        if ts is None:
            ts = getattr(event, 'timestamp', datetime.now(timezone.utc))
        if isinstance(ts, str):
            try:
                ts = pd.to_datetime(ts).to_pydatetime()
            except Exception:
                ts = datetime.now(timezone.utc)
        elif isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts, tz=timezone.utc)
        if ts and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts or datetime.now(timezone.utc)

    def _resolve_tick_time(self, ts, tick_data: dict) -> tuple[int, int]:
        local_offset = get_local_timezone_offset_seconds()
        current_tick_time = int(ts.timestamp()) + local_offset
        current_minute_start = current_tick_time - (current_tick_time % 60)
        return current_tick_time, current_minute_start

    def _initialize_candle(self, current_minute_start: int, price: float) -> None:
        self._current_candle_time = current_minute_start
        self._current_candle_open = price
        self._current_candle_high = price
        self._current_candle_low = price
        self._current_candle_volume = 0

    def _update_candle_for_tick(self, current_minute_start: int, price: float, tick_data: dict = None) -> None:
        if not hasattr(self, '_current_candle_time'):
            self._current_candle_time = current_minute_start

        if current_minute_start > self._current_candle_time:
            prev_open = getattr(self, '_current_candle_open', price)
            prev_high = getattr(self, '_current_candle_high', price)
            prev_low = getattr(self, '_current_candle_low', price)
            prev_close = getattr(self, '_current_candle_close', price)
            prev_volume = getattr(self, '_current_candle_volume', 0)

            if hasattr(self, 'candle_closed'):
                self.candle_closed.emit(prev_open, prev_high, prev_low, prev_close, price)
                logger.info(f"🕯️ Candle closed: C={prev_close:.2f} -> new_open={price:.2f}")

            self._current_candle_time = current_minute_start
            self._current_candle_open = price
            self._current_candle_high = price
            self._current_candle_low = price
            self._current_candle_volume = 0
            return

        # OHLC update
        if tick_data and 'high' in tick_data and 'low' in tick_data:
            self._current_candle_high = max(self._current_candle_high, float(tick_data['high']))
            self._current_candle_low = min(self._current_candle_low, float(tick_data['low']))
        else:
            self._current_candle_high = max(self._current_candle_high, price)
            self._current_candle_low = min(self._current_candle_low, price)

    def _accumulate_volume(self, volume: float) -> None:
        if volume:
            if not hasattr(self, '_current_candle_volume'):
                self._current_candle_volume = 0
            self._current_candle_volume += volume

    def _build_candle_payload(self, price: float) -> dict:
        return {
            'time': getattr(self, '_current_candle_time', int(time.time())),
            'open': float(getattr(self, '_current_candle_open', price)),
            'high': float(getattr(self, '_current_candle_high', price)),
            'low': float(getattr(self, '_current_candle_low', price)),
            'close': float(price),
        }

    def _build_volume_payload(self, price: float) -> dict:
        open_price = getattr(self, '_current_candle_open', price)
        return {
            'time': getattr(self, '_current_candle_time', int(time.time())),
            'value': float(getattr(self, '_current_candle_volume', 0)),
            'color': '#26a69a' if price >= open_price else '#ef5350'
        }

    def _execute_chart_updates(self, candle: dict, volume_bar: dict) -> None:
        candle_json = json.dumps(candle)
        volume_json = json.dumps(volume_bar)
        self._execute_js(f"window.chartAPI.updateCandle({candle_json});")
        self._execute_js(f"window.chartAPI.updatePanelData('volume', {volume_json});")

    def _emit_tick_price_updated(self, price: float) -> None:
        if hasattr(self, 'tick_price_updated'):
            self.tick_price_updated.emit(price)

    def _process_pending_updates(self):
        """Process pending bar updates (batched for performance)."""
        if not self.pending_bars:
            return

        try:
            while self.pending_bars:
                bar_data = self.pending_bars.popleft()
                ts_raw = bar_data.get('timestamp', datetime.now())
                local_offset = get_local_timezone_offset_seconds()
                try:
                    unix_time = int(pd.Timestamp(ts_raw).timestamp()) + local_offset
                    unix_time = unix_time - (unix_time % 60)
                except Exception:
                    unix_time = int(time.time()) + local_offset
                    unix_time = unix_time - (unix_time % 60)

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

                self._execute_js(f"window.chartAPI.updateCandle({json.dumps(candle)});")
                self._execute_js(f"window.chartAPI.updatePanelData('volume', {json.dumps(volume)});")

        except Exception as e:
            logger.error(f"Error processing updates: {e}")

    def _toggle_live_stream(self):
        """Toggle live streaming on/off."""
        is_checked = self.live_stream_button.isChecked()
        self.live_streaming_enabled = is_checked

        if self.live_streaming_enabled:
            asyncio.ensure_future(self._start_live_stream_async())
        else:
            asyncio.ensure_future(self._stop_live_stream_async())

    async def _start_live_stream_async(self):
        """Async wrapper for starting live stream."""
        try:
            await self._start_live_stream()
            self.live_stream_button.setStyleSheet("background-color: #00FF00; color: black; font-weight: bold;")
            self.live_stream_button.setText("🟢 Live")
            self.market_status_label.setText("🔴 Streaming...")
        except MarketDataAccessBlocked as e:
            self._handle_stream_blocked(e)
        except Exception as e:
            logger.error(f"Failed to start live stream: {e}")

    async def _stop_live_stream_async(self):
        """Async wrapper for stopping live stream."""
        try:
            await self._stop_live_stream()
            self.live_stream_button.setStyleSheet("")
            self.live_stream_button.setText("🔴 Live")
            self.market_status_label.setText("Ready")
        except Exception as e:
            logger.error(f"Failed to stop live stream: {e}")

    async def _start_live_stream(self):
        """Start live streaming for current symbol."""
        if not self.history_manager or not self.current_symbol:
            return

        try:
            asset_class = getattr(self, "current_asset_class", AssetClass.STOCK)
            if "/" in self.current_symbol or self.current_symbol.endswith("USDT"):
                asset_class = AssetClass.CRYPTO

            success = await self.history_manager.start_realtime_stream([self.current_symbol])
            if success:
                self.market_status_label.setText(f"🟢 Live: {self.current_symbol}")
            else:
                self.live_stream_button.setChecked(False)
                self._toggle_live_stream()
        except MarketDataAccessBlocked:
            # Re-raise to outer handler so UI popup can be shown
            self.live_stream_button.setChecked(False)
            self.live_streaming_enabled = False
            raise
        except Exception as e:
            logger.error(f"Error starting live stream: {e}")

    def _handle_stream_blocked(self, exc: MarketDataAccessBlocked) -> None:
        """Show UI popup when Bitunix blocks access (e.g., HTTP 403)."""
        self.live_streaming_enabled = False
        self.live_stream_button.setChecked(False)
        self.live_stream_button.setStyleSheet("")
        self.live_stream_button.setText("🔴 Live")
        label_reason = exc.reason or "Bitunix blockiert"
        self.market_status_label.setText(label_reason)
        self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

        details = exc.details()
        message = (
            "Bitunix WebSocket hat den Zugriff blockiert.\n\n"
            f"Grund: {label_reason}\n"
            "Maßnahmen:\n"
            "- VPN/IP wechseln oder gültigen API-Key mit ausreichenden Rechten nutzen.\n"
            "- Falls Cloudflare-Challenge: Browser-Cookie/clearance übertragen.\n\n"
            f"Provider: {exc.provider}\n{details}"
        )
        QMessageBox.critical(self, "Bitunix blockiert", message, QMessageBox.StandardButton.Ok)

    async def _stop_live_stream(self):
        """Stop live streaming."""
        if not self.history_manager:
            return
        try:
            if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
                await self.history_manager.stream_client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting stream: {e}")
