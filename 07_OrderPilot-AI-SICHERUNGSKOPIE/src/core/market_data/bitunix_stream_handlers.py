"""Bitunix Stream - Channel Handlers.

Refactored from bitunix_stream.py monolith.

Module 3/5 of bitunix_stream.py split.

Contains:
- handle_ticker: Ticker updates
- handle_kline: Candlestick/kline updates
- handle_depth: Order book depth
- handle_trade: Trade feed
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from src.common.event_bus import Event, EventType, event_bus
from src.core.market_data.stream_client import MarketTick

logger = logging.getLogger(__name__)


class BitunixStreamHandlers:
    """Helper für BitunixStreamClient channel handlers."""

    def __init__(self, parent):
        """
        Args:
            parent: BitunixStreamClient Instanz
        """
        self.parent = parent
        self._kline_count = 0

    async def handle_ticker(self, data: dict) -> None:
        """Handle ticker updates.

        Example data:
        {
            "ch": "ticker",
            "data": {
                "symbol": "BTCUSDT",
                "lastPrice": "45000.0",
                "markPrice": "45010.0",
                "open": "44000.0",
                "high": "46000.0",
                "low": "43500.0",
                "baseVol": "1234.56",
                "quoteVol": "55000000.0"
            }
        }

        Args:
            data: Ticker data
        """
        ticker = data.get('data', {})
        symbol = ticker.get('symbol')

        if not symbol:
            return

        # Create MarketTick
        tick = MarketTick(
            symbol=symbol,
            last=Decimal(str(ticker.get('lastPrice', 0))),
            volume=int(float(ticker.get('baseVol', 0))),
            timestamp=datetime.utcnow(),
            source=self.parent.name
        )

        # Process tick (latency calculation, callbacks, caching)
        self.parent.process_tick(tick)

        # Emit event
        event_bus.emit(
            Event(
                type=EventType.MARKET_DATA_TICK,
                timestamp=tick.timestamp or datetime.utcnow(),
                data={
                    "symbol": symbol,
                    "tick": tick,
                    "price": float(tick.last) if tick.last is not None else 0.0,
                    "volume": tick.volume,
                    "timestamp": tick.timestamp or datetime.utcnow(),
                },
                source=self.parent.name,
            )
        )

    async def handle_kline(self, data: dict) -> None:
        """Handle kline (candlestick) updates.

        Example data:
        {
            "ch": "market_kline",
            "data": {
                "symbol": "BTCUSDT",
                "time": 1609459200000,
                "open": "29000.0",
                "high": "29500.0",
                "low": "28800.0",
                "close": "29300.0",
                "baseVol": "123.45",
                "closed": true
            }
        }

        Args:
            data: Kline data
        """
        # Bitunix WS docs format:
        # {
        #   "ch": "mark_kline_1min",
        #   "symbol": "BNBUSDT",
        #   "ts": 1732178884994,
        #   "data": {"o":"...","h":"...","l":"...","c":"...","b":"...","q":"..."}
        # }
        symbol = data.get("symbol")
        ts_ms = data.get("ts")
        kline = data.get("data") or {}

        if not symbol or not ts_ms:
            logger.warning(f"⚠ Bitunix: Kline missing symbol or timestamp: {data}")
            return

        ts = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)
        open_ = float(kline.get("o", 0))
        high = float(kline.get("h", 0))
        low = float(kline.get("l", 0))
        close = float(kline.get("c", 0))
        volume = float(kline.get("b", 0))

        # Log first kline to confirm data flow
        self._kline_count += 1
        if self._kline_count <= 3:
            logger.info(f"📊 Bitunix kline #{self._kline_count}: {symbol} @ ${close:.2f} (vol={volume:.2f})")

        # NOTE: Only emit MARKET_DATA_TICK, not MARKET_BAR
        # The streaming_mixin's _on_market_tick handler already aggregates ticks into candles.
        # Emitting MARKET_BAR would cause duplicate candles since both handlers would
        # update the chart independently with potentially different timestamps.

        # Emit tick event - the chart's tick handler will aggregate this into candles
        event_bus.emit(
            Event(
                type=EventType.MARKET_DATA_TICK,
                timestamp=ts,
                data={
                    "symbol": symbol,
                    "price": close,
                    "volume": volume,
                    "open": open_,    # Include OHLC for better tick handling
                    "high": high,
                    "low": low,
                    "timestamp": ts,
                },
                source=self.parent.name,
            )
        )

    async def handle_depth(self, data: dict) -> None:
        """Handle order book depth updates.

        Args:
            data: Depth data
        """
        # TODO: Implement depth handling if needed
        logger.debug(f"Depth update: {data.get('data', {}).get('symbol')}")

    async def handle_trade(self, data: dict) -> None:
        """Handle trade feed updates.

        Args:
            data: Trade data
        """
        # TODO: Implement trade handling if needed
        logger.debug(f"Trade update: {data.get('data', {}).get('symbol')}")
