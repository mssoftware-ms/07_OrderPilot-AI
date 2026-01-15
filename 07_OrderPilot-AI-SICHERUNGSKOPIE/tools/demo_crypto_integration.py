"""Demo: Cryptocurrency Integration with Alpaca.

Demonstrates:
1. Fetching historical crypto data (BTC/USD, ETH/USD)
2. Real-time crypto streaming
3. Using HistoryManager with crypto asset class
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta

from src.core.market_data import (
    AlpacaCryptoProvider,
    AlpacaCryptoStreamClient,
    AssetClass,
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


async def demo_crypto_historical_data():
    """Demo: Fetch historical cryptocurrency data."""
    logger.info("=== Demo 1: Historical Crypto Data ===")

    # Get credentials
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")

    if not api_key or not api_secret:
        logger.error("Alpaca credentials not found in environment!")
        return

    # Create crypto provider
    provider = AlpacaCryptoProvider(api_key, api_secret)

    # Fetch BTC/USD data (last 24 hours, hourly bars)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)

    logger.info("Fetching BTC/USD hourly bars for last 24 hours...")
    btc_bars = await provider.fetch_bars(
        symbol="BTC/USD",
        start_date=start_date,
        end_date=end_date,
        timeframe=Timeframe.HOUR_1
    )

    if btc_bars:
        logger.info(f"✅ Fetched {len(btc_bars)} BTC/USD bars")
        # Show first and last bar
        first_bar = btc_bars[0]
        last_bar = btc_bars[-1]
        logger.info(
            f"   First: {first_bar.timestamp} - "
            f"OHLC: {first_bar.open}/{first_bar.high}/{first_bar.low}/{first_bar.close}"
        )
        logger.info(
            f"   Last:  {last_bar.timestamp} - "
            f"OHLC: {last_bar.open}/{last_bar.high}/{last_bar.low}/{last_bar.close}"
        )
        logger.info(f"   Current BTC Price: ${last_bar.close}")
    else:
        logger.warning("❌ No BTC/USD data received")

    # Fetch ETH/USD data (last 6 hours, 15-minute bars)
    start_date = end_date - timedelta(hours=6)

    logger.info("\nFetching ETH/USD 15-minute bars for last 6 hours...")
    eth_bars = await provider.fetch_bars(
        symbol="ETH/USD",
        start_date=start_date,
        end_date=end_date,
        timeframe=Timeframe.MINUTE_15
    )

    if eth_bars:
        logger.info(f"✅ Fetched {len(eth_bars)} ETH/USD bars")
        last_bar = eth_bars[-1]
        logger.info(f"   Current ETH Price: ${last_bar.close}")
    else:
        logger.warning("❌ No ETH/USD data received")


async def demo_crypto_streaming():
    """Demo: Real-time cryptocurrency streaming."""
    logger.info("\n=== Demo 2: Real-Time Crypto Streaming ===")

    # Get credentials
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")

    if not api_key or not api_secret:
        logger.error("Alpaca credentials not found in environment!")
        return

    # Create crypto stream client
    stream_client = AlpacaCryptoStreamClient(api_key, api_secret)

    # Connect
    logger.info("Connecting to Alpaca crypto WebSocket...")
    connected = await stream_client.connect()

    if not connected:
        logger.error("❌ Failed to connect to crypto stream")
        return

    logger.info("✅ Connected to crypto stream")

    # Subscribe to crypto symbols
    crypto_symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]
    logger.info(f"Subscribing to: {', '.join(crypto_symbols)}")
    await stream_client.subscribe(crypto_symbols)

    # Listen for 30 seconds
    logger.info("Listening for crypto market data (30 seconds)...")
    logger.info("(Press Ctrl+C to stop early)")

    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    # Get metrics
    metrics = stream_client.get_metrics()
    logger.info(f"\nStream Metrics:")
    logger.info(f"   Messages received: {metrics['messages_received']}")
    logger.info(f"   Messages dropped: {metrics['messages_dropped']}")
    logger.info(f"   Avg latency: {metrics['average_latency_ms']:.2f}ms")

    # Get latest ticks
    logger.info("\nLatest Prices:")
    for symbol in crypto_symbols:
        tick = stream_client.get_latest_tick(symbol)
        if tick:
            logger.info(f"   {symbol}: ${tick.last} (volume: {tick.volume})")

    # Disconnect
    logger.info("\nDisconnecting...")
    await stream_client.disconnect()
    logger.info("✅ Disconnected")


async def demo_history_manager_crypto():
    """Demo: Using HistoryManager with crypto asset class."""
    logger.info("\n=== Demo 3: HistoryManager with Crypto ===")

    # Create history manager (auto-registers providers from config)
    manager = HistoryManager()

    # Fetch crypto data using DataRequest with AssetClass.CRYPTO
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=12)

    logger.info("Fetching BTC/USD via HistoryManager (asset_class=CRYPTO)...")
    request = DataRequest(
        symbol="BTC/USD",
        start_date=start_date,
        end_date=end_date,
        timeframe=Timeframe.HOUR_1,
        asset_class=AssetClass.CRYPTO  # Important: specify CRYPTO asset class
    )

    bars, source = await manager.fetch_data(request)

    if bars:
        logger.info(f"✅ Fetched {len(bars)} bars from source: {source}")
        last_bar = bars[-1]
        logger.info(f"   Latest BTC Price: ${last_bar.close}")
    else:
        logger.warning("❌ No data received")

    # Demonstrate asset class filtering
    logger.info("\n--- Testing Asset Class Filtering ---")

    # Try fetching stock data (should skip crypto providers)
    stock_request = DataRequest(
        symbol="AAPL",
        start_date=start_date,
        end_date=end_date,
        timeframe=Timeframe.HOUR_1,
        asset_class=AssetClass.STOCK  # Stock asset class
    )

    logger.info("Fetching AAPL (stock) - should NOT use crypto providers...")
    bars, source = await manager.fetch_data(stock_request)
    if bars:
        logger.info(f"✅ Fetched from source: {source} (should NOT be alpaca_crypto)")
    else:
        logger.info("No AAPL data available")


async def demo_multiple_crypto_pairs():
    """Demo: Fetch data for multiple cryptocurrency pairs."""
    logger.info("\n=== Demo 4: Multiple Crypto Trading Pairs ===")

    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")

    if not api_key or not api_secret:
        logger.error("Alpaca credentials not found!")
        return

    provider = AlpacaCryptoProvider(api_key, api_secret)

    # Popular crypto trading pairs
    crypto_pairs = [
        "BTC/USD",   # Bitcoin
        "ETH/USD",   # Ethereum
        "SOL/USD",   # Solana
        "AVAX/USD",  # Avalanche
        "MATIC/USD"  # Polygon
    ]

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=3)

    logger.info(f"Fetching data for {len(crypto_pairs)} crypto pairs (last 3 hours)...")

    results = {}
    for symbol in crypto_pairs:
        bars = await provider.fetch_bars(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=Timeframe.MINUTE_30
        )

        if bars:
            last_price = bars[-1].close
            results[symbol] = {
                "bars": len(bars),
                "price": float(last_price)
            }
            logger.info(f"   ✅ {symbol}: ${last_price:.2f} ({len(bars)} bars)")
        else:
            logger.warning(f"   ❌ {symbol}: No data")

    logger.info(f"\n📊 Summary: Successfully fetched {len(results)}/{len(crypto_pairs)} pairs")


async def main():
    """Run all demos."""
    logger.info("=" * 60)
    logger.info("OrderPilot-AI - Cryptocurrency Integration Demo")
    logger.info("=" * 60)

    try:
        # Demo 1: Historical data
        await demo_crypto_historical_data()

        # Demo 2: Real-time streaming (commented out by default - uncomment to test)
        # await demo_crypto_streaming()

        # Demo 3: HistoryManager integration
        await demo_history_manager_crypto()

        # Demo 4: Multiple crypto pairs
        await demo_multiple_crypto_pairs()

    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)

    logger.info("\n" + "=" * 60)
    logger.info("Demo completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
