#!/usr/bin/env python
"""
Real-Time Market Data and Technical Indicators Demo

This script demonstrates how to use the OrderPilot-AI real-time
market data streaming and technical indicator features powered by
Alpha Vantage.

Features demonstrated:
- Real-time market data streaming
- RSI and MACD indicator calculations
- Intraday bars
- Event handling for market updates

Requirements:
- Alpha Vantage API key (get one free at https://www.alphavantage.co/support/#api-key)
- Set the API key in your configuration or as environment variable
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.common.event_bus import Event, EventType, event_bus
from src.config.loader import config_manager
from src.core.market_data.history_provider import (
    DataRequest,
    HistoryManager,
    Timeframe
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class RealtimeDemo:
    """Demo application for real-time indicators."""

    def __init__(self):
        """Initialize demo."""
        self.history_manager = None
        self.running = False

    async def setup(self):
        """Setup the demo."""
        logger.info("Setting up demo...")

        # Initialize history manager
        self.history_manager = HistoryManager()

        # Setup event listeners
        event_bus.subscribe(EventType.MARKET_DATA_TICK, self.on_market_tick)
        event_bus.subscribe(EventType.INDICATOR_CALCULATED, self.on_indicator_update)
        event_bus.subscribe(EventType.MARKET_DATA_CONNECTED, self.on_stream_connected)
        event_bus.subscribe(EventType.MARKET_DATA_DISCONNECTED, self.on_stream_disconnected)

        logger.info("Demo setup complete")

    async def on_market_tick(self, event: Event):
        """Handle market tick events."""
        data = event.data
        logger.info(
            f"📊 Market Tick: {data['symbol']} "
            f"Price: ${data['price']:.2f} "
            f"Volume: {data['volume']:,}"
        )

    async def on_indicator_update(self, event: Event):
        """Handle indicator update events."""
        data = event.data
        symbol = data.get('symbol', 'Unknown')

        if 'rsi' in data and data['rsi']:
            rsi = data['rsi']
            logger.info(f"📈 RSI Update for {symbol}: {rsi:.2f}")

        if 'macd' in data and data['macd']:
            macd = data['macd']
            logger.info(
                f"📉 MACD Update for {symbol}: "
                f"MACD: {macd['macd']:.4f}, "
                f"Signal: {macd['signal']:.4f}, "
                f"Histogram: {macd['histogram']:.4f}"
            )

    async def on_stream_connected(self, event: Event):
        """Handle stream connection events."""
        logger.info(f"✅ Stream connected: {event.data['source']}")

    async def on_stream_disconnected(self, event: Event):
        """Handle stream disconnection events."""
        logger.info(f"❌ Stream disconnected: {event.data['source']}")

    async def demo_historical_indicators(self, symbol: str = "AAPL"):
        """Demo: Fetch historical indicators."""
        logger.info(f"\n{'='*60}")
        logger.info(f"DEMO 1: Historical Indicators for {symbol}")
        logger.info(f"{'='*60}\n")

        try:
            # Fetch historical data
            request = DataRequest(
                symbol=symbol,
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow(),
                timeframe=Timeframe.DAY_1
            )

            logger.info(f"Fetching 30 days of historical data for {symbol}...")
            bars, source = await self.history_manager.fetch_data(request)

            if bars:
                logger.info(f"✅ Fetched {len(bars)} bars from {source}")
                logger.info(f"   Latest close: ${bars[-1].close}")
                logger.info(f"   Date range: {bars[0].timestamp} to {bars[-1].timestamp}")
            else:
                logger.warning(f"No historical data available for {symbol}")

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")

    async def demo_realtime_indicators(self, symbol: str = "AAPL"):
        """Demo: Fetch real-time indicators."""
        logger.info(f"\n{'='*60}")
        logger.info(f"DEMO 2: Real-Time Indicators for {symbol}")
        logger.info(f"{'='*60}\n")

        try:
            logger.info(f"Fetching real-time RSI and MACD for {symbol}...")

            indicators = await self.history_manager.fetch_realtime_indicators(
                symbol=symbol,
                interval="1min"
            )

            if "rsi" in indicators:
                rsi = indicators["rsi"]
                logger.info(f"✅ RSI: {rsi['value']:.2f}")
                logger.info(f"   Timestamp: {rsi['timestamp']}")
                logger.info(f"   Data points: {len(rsi['series'])}")

                # Interpret RSI
                if rsi['value'] > 70:
                    logger.info("   🔴 OVERBOUGHT condition (RSI > 70)")
                elif rsi['value'] < 30:
                    logger.info("   🟢 OVERSOLD condition (RSI < 30)")
                else:
                    logger.info("   🟡 NEUTRAL condition")

            if "macd" in indicators:
                macd = indicators["macd"]
                logger.info(f"✅ MACD: {macd['macd']:.4f}")
                logger.info(f"   Signal: {macd['signal']:.4f}")
                logger.info(f"   Histogram: {macd['histogram']:.4f}")
                logger.info(f"   Timestamp: {macd['timestamp']}")

                # Interpret MACD
                if macd['histogram'] > 0:
                    logger.info("   🟢 BULLISH signal (histogram > 0)")
                else:
                    logger.info("   🔴 BEARISH signal (histogram < 0)")

            if not indicators:
                logger.warning(f"No indicator data available for {symbol}")
                logger.info("   Make sure Alpha Vantage is enabled in your config")

        except Exception as e:
            logger.error(f"Error fetching real-time indicators: {e}")

    async def demo_streaming(self, symbols: list[str] = None, duration: int = 180):
        """Demo: Real-time streaming.

        Args:
            symbols: List of symbols to stream (default: ["AAPL", "MSFT"])
            duration: Duration to stream in seconds (default: 180 = 3 minutes)
        """
        if symbols is None:
            symbols = ["AAPL", "MSFT"]

        logger.info(f"\n{'='*60}")
        logger.info(f"DEMO 3: Real-Time Streaming")
        logger.info(f"{'='*60}\n")

        try:
            logger.info(f"Starting real-time stream for: {', '.join(symbols)}")
            logger.info(f"Duration: {duration} seconds")
            logger.info(f"Note: Free tier polls every 60 seconds\n")

            # Start streaming
            success = await self.history_manager.start_realtime_stream(
                symbols=symbols,
                enable_indicators=True
            )

            if not success:
                logger.error("Failed to start stream")
                logger.info("Make sure Alpha Vantage is enabled and API key is configured")
                return

            logger.info("✅ Stream started successfully")

            # Monitor for specified duration
            start_time = datetime.utcnow()
            self.running = True

            while self.running:
                elapsed = (datetime.utcnow() - start_time).total_seconds()

                if elapsed >= duration:
                    break

                # Display metrics every 30 seconds
                if int(elapsed) % 30 == 0:
                    metrics = self.history_manager.get_stream_metrics()
                    if metrics:
                        logger.info(f"\n📊 Stream Metrics:")
                        logger.info(f"   Status: {metrics['status']}")
                        logger.info(f"   Messages received: {metrics['messages_received']}")
                        logger.info(f"   Average latency: {metrics['average_latency_ms']:.2f}ms")
                        logger.info(f"   Subscribed symbols: {', '.join(metrics['subscribed_symbols'])}\n")

                await asyncio.sleep(1)

            logger.info("\n⏱️ Demo duration elapsed")

            # Stop streaming
            await self.history_manager.stop_realtime_stream()
            logger.info("✅ Stream stopped")

        except KeyboardInterrupt:
            logger.info("\n⚠️ Stream interrupted by user")
            await self.history_manager.stop_realtime_stream()
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            await self.history_manager.stop_realtime_stream()

    async def run_all_demos(self):
        """Run all demos sequentially."""
        await self.setup()

        logger.info("\n" + "="*60)
        logger.info("  OrderPilot-AI Real-Time Indicators Demo")
        logger.info("="*60)

        # Demo 1: Historical indicators
        await self.demo_historical_indicators("AAPL")
        await asyncio.sleep(2)

        # Demo 2: Real-time indicators
        await self.demo_realtime_indicators("AAPL")
        await asyncio.sleep(2)

        # Demo 3: Streaming (3 minutes)
        await self.demo_streaming(["AAPL", "MSFT"], duration=180)

        logger.info("\n" + "="*60)
        logger.info("  Demo Complete!")
        logger.info("="*60)

    async def cleanup(self):
        """Cleanup resources."""
        if self.history_manager and self.history_manager.stream_client:
            await self.history_manager.stop_realtime_stream()


async def main():
    """Main entry point."""
    demo = RealtimeDemo()

    try:
        # Check for API key
        api_key = config_manager.get_credential("alpha_vantage_api_key")
        if not api_key:
            logger.error("❌ Alpha Vantage API key not found!")
            logger.info("\nTo use this demo:")
            logger.info("1. Get a free API key from https://www.alphavantage.co/support/#api-key")
            logger.info("2. Set it in your config or as environment variable ALPHA_VANTAGE_API_KEY")
            logger.info("3. Enable Alpha Vantage in your trading profile config")
            return 1

        # Run demos
        await demo.run_all_demos()

        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️ Demo interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        return 1
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
