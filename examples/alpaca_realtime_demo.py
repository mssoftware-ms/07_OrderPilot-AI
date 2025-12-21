#!/usr/bin/env python
"""
Alpaca Real-Time Trading Demo for OrderPilot-AI

Demonstrates:
- Real-time WebSocket market data streaming
- Trading order placement and management
- Position monitoring
- RSI/MACD indicators with Alpaca
- Complete trading workflow

Requirements:
- Alpaca API keys (paper trading recommended for testing)
- Get keys at: https://alpaca.markets/ (Paper Trading section)
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.common.event_bus import Event, EventType, event_bus
from src.config.loader import config_manager
from src.core.broker.alpaca_adapter import AlpacaAdapter
from src.core.broker.base import OrderRequest
from src.core.market_data.alpaca_stream import AlpacaStreamClient
from src.core.market_data.history_provider import HistoryManager
from src.database.models import OrderSide, OrderType, TimeInForce
from decimal import Decimal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class AlpacaDemo:
    """Alpaca integration demo application."""

    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        """Initialize demo.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper: Use paper trading (default: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper

        self.stream_client: AlpacaStreamClient | None = None
        self.broker_adapter: AlpacaAdapter | None = None
        self.history_manager: HistoryManager | None = None

        # Stats
        self.bars_received = 0
        self.trades_received = 0

    async def setup(self):
        """Setup demo components."""
        logger.info("Setting up Alpaca demo...")

        # Create stream client
        self.stream_client = AlpacaStreamClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            paper=self.paper,
            feed="iex"  # Free IEX feed
        )

        # Create broker adapter
        self.broker_adapter = AlpacaAdapter(
            api_key=self.api_key,
            api_secret=self.api_secret,
            paper=self.paper
        )

        # Create history manager
        self.history_manager = HistoryManager()

        # Setup event listeners
        event_bus.subscribe(EventType.MARKET_BAR, self.on_market_bar)
        event_bus.subscribe(EventType.MARKET_DATA_TICK, self.on_market_tick)
        event_bus.subscribe(EventType.MARKET_DATA_CONNECTED, self.on_connected)
        event_bus.subscribe(EventType.MARKET_DATA_DISCONNECTED, self.on_disconnected)

        logger.info("Demo setup complete")

    async def on_market_bar(self, event: Event):
        """Handle market bar events."""
        self.bars_received += 1
        data = event.data

        logger.info(
            f"📊 BAR: {data['symbol']} "
            f"O:{data['open']:.2f} H:{data['high']:.2f} "
            f"L:{data['low']:.2f} C:{data['close']:.2f} "
            f"V:{data['volume']:,}"
        )

    async def on_market_tick(self, event: Event):
        """Handle market tick events."""
        self.trades_received += 1
        data = event.data

        logger.debug(f"💱 TICK: {data['symbol']} @ ${data['price']:.2f}")

    async def on_connected(self, event: Event):
        """Handle connection events."""
        logger.info(f"✅ Connected to {event.data['source']}")

    async def on_disconnected(self, event: Event):
        """Handle disconnection events."""
        logger.info(f"❌ Disconnected from {event.data['source']}")

    async def demo_broker_info(self):
        """Demo: Show broker account information."""
        logger.info("\n" + "="*60)
        logger.info("DEMO 1: Broker Account Information")
        logger.info("="*60 + "\n")

        await self.broker_adapter.connect()

        # Get balance
        balance = await self.broker_adapter.get_balance()
        logger.info(f"💰 Account Balance:")
        logger.info(f"   Cash: ${balance.cash}")
        logger.info(f"   Buying Power: ${balance.buying_power}")
        logger.info(f"   Total Equity: ${balance.total_equity}")
        logger.info(f"   Daily P&L: ${balance.daily_pnl} ({balance.daily_pnl_percentage:.2f}%)")

        # Get positions
        positions = await self.broker_adapter.get_positions()
        if positions:
            logger.info(f"\n📈 Open Positions: {len(positions)}")
            for pos in positions:
                logger.info(
                    f"   {pos.symbol}: {pos.quantity} shares @ ${pos.average_cost:.2f}"
                )
                logger.info(
                    f"      Current: ${pos.current_price:.2f} | "
                    f"P&L: ${pos.unrealized_pnl:.2f} ({pos.pnl_percentage:.2f}%)"
                )
        else:
            logger.info("\n📈 No open positions")

    async def demo_realtime_streaming(self, symbols: list[str], duration: int = 120):
        """Demo: Real-time WebSocket streaming.

        Args:
            symbols: List of symbols to stream
            duration: Duration in seconds (default: 120 = 2 minutes)
        """
        logger.info("\n" + "="*60)
        logger.info("DEMO 2: Real-Time WebSocket Streaming")
        logger.info("="*60 + "\n")

        logger.info(f"Streaming {len(symbols)} symbols: {', '.join(symbols)}")
        logger.info(f"Duration: {duration} seconds")
        logger.info(f"Feed: IEX (free tier)\n")

        # Connect and subscribe
        await self.stream_client.connect()
        await self.stream_client.subscribe(symbols)

        # Monitor for specified duration
        start_time = datetime.utcnow()
        self.bars_received = 0
        self.trades_received = 0

        while (datetime.utcnow() - start_time).total_seconds() < duration:
            await asyncio.sleep(10)

            # Show stats every 10 seconds
            metrics = self.stream_client.get_metrics()
            logger.info(
                f"📊 Stats: Bars: {self.bars_received} | "
                f"Messages: {metrics['messages_received']} | "
                f"Latency: {metrics['average_latency_ms']:.2f}ms"
            )

        logger.info(f"\n✅ Streaming complete: {self.bars_received} bars received")

    async def demo_place_order(self, symbol: str = "AAPL", quantity: int = 1):
        """Demo: Place a market order.

        Args:
            symbol: Symbol to trade (default: AAPL)
            quantity: Number of shares (default: 1)
        """
        logger.info("\n" + "="*60)
        logger.info(f"DEMO 3: Place Market Order ({symbol})")
        logger.info("="*60 + "\n")

        if not self.paper:
            logger.warning("⚠️ LIVE TRADING MODE - Order will execute with real money!")
            logger.info("Set paper=True to use paper trading")
            return

        logger.info(f"Placing paper trading order for {quantity} shares of {symbol}")

        # Get current quote
        quote = await self.broker_adapter.get_quote(symbol)
        if quote:
            logger.info(f"Current bid/ask: ${quote['bid']:.2f} / ${quote['ask']:.2f}")

        # Create order
        order = OrderRequest(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal(str(quantity)),
            time_in_force=TimeInForce.DAY
        )

        try:
            response = await self.broker_adapter.place_order(order)

            logger.info(f"✅ Order placed successfully!")
            logger.info(f"   Order ID: {response.broker_order_id}")
            logger.info(f"   Status: {response.status.value}")
            logger.info(f"   Symbol: {response.symbol}")
            logger.info(f"   Side: {response.side.value}")
            logger.info(f"   Quantity: {response.quantity}")

            # Wait a bit and check status
            await asyncio.sleep(2)

            updated_status = await self.broker_adapter.get_order_status(
                response.broker_order_id
            )

            logger.info(f"\n📊 Order Status Update:")
            logger.info(f"   Status: {updated_status.status.value}")
            logger.info(f"   Filled: {updated_status.filled_quantity}/{updated_status.quantity}")

            if updated_status.average_fill_price:
                logger.info(f"   Avg Fill Price: ${updated_status.average_fill_price:.2f}")

        except Exception as e:
            logger.error(f"❌ Order failed: {e}")

    async def demo_historical_data(self, symbol: str = "AAPL", days: int = 7):
        """Demo: Fetch historical data from Alpaca.

        Args:
            symbol: Symbol to fetch (default: AAPL)
            days: Number of days of history (default: 7)
        """
        logger.info("\n" + "="*60)
        logger.info(f"DEMO 4: Historical Data ({symbol})")
        logger.info("="*60 + "\n")

        from src.core.market_data.history_provider import (
            DataRequest,
            Timeframe,
            DataSource
        )
        from datetime import timedelta

        request = DataRequest(
            symbol=symbol,
            start_date=datetime.utcnow() - timedelta(days=days),
            end_date=datetime.utcnow(),
            timeframe=Timeframe.MINUTE_5,
            source=DataSource.ALPACA
        )

        logger.info(f"Fetching {days} days of 5-minute bars for {symbol}...")

        bars, source = await self.history_manager.fetch_data(request)

        if bars:
            logger.info(f"✅ Fetched {len(bars)} bars from {source}")
            logger.info(f"\nLatest 5 bars:")
            for bar in bars[-5:]:
                logger.info(
                    f"   {bar.timestamp.strftime('%Y-%m-%d %H:%M')}: "
                    f"${bar.close:.2f} (vol: {bar.volume:,})"
                )
        else:
            logger.warning(f"No data available for {symbol}")

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("\nCleaning up...")

        if self.stream_client:
            await self.stream_client.disconnect()

        if self.broker_adapter:
            await self.broker_adapter.disconnect()

        logger.info("Cleanup complete")


async def main():
    """Main entry point."""
    # Check for API keys
    api_key = config_manager.get_credential("alpaca_api_key")
    api_secret = config_manager.get_credential("alpaca_api_secret")

    if not api_key or not api_secret:
        logger.error("❌ Alpaca API credentials not found!")
        logger.info("\nTo use this demo:")
        logger.info("1. Sign up at https://alpaca.markets/")
        logger.info("2. Go to Paper Trading → API Keys")
        logger.info("3. Generate API keys")
        logger.info("4. Set credentials:")
        logger.info("   from src.config.loader import config_manager")
        logger.info('   config_manager.store_credential("alpaca_api_key", "YOUR_KEY")')
        logger.info('   config_manager.store_credential("alpaca_api_secret", "YOUR_SECRET")')
        return 1

    # Create demo
    demo = AlpacaDemo(
        api_key=api_key,
        api_secret=api_secret,
        paper=True  # Use paper trading
    )

    try:
        await demo.setup()

        logger.info("\n" + "="*60)
        logger.info("  Alpaca Real-Time Trading Demo")
        logger.info("  Paper Trading Mode (Safe to Test!)")
        logger.info("="*60)

        # Run demos
        await demo.demo_broker_info()
        await asyncio.sleep(2)

        await demo.demo_historical_data("AAPL", days=7)
        await asyncio.sleep(2)

        await demo.demo_realtime_streaming(
            symbols=["AAPL", "MSFT", "QQQ", "DIA"],
            duration=120  # 2 minutes
        )
        await asyncio.sleep(2)

        await demo.demo_place_order("AAPL", quantity=1)

        logger.info("\n" + "="*60)
        logger.info("  Demo Complete!")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("- Check the ALPACA_INTEGRATION.md documentation")
        logger.info("- Build your own trading strategy")
        logger.info("- Test thoroughly in paper trading")
        logger.info("- Go live when ready (set paper=False)")

        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️ Demo interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}", exc_info=True)
        return 1
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
