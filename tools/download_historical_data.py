"""Download Historical Market Data Script.

Downloads and caches historical market data from Alpaca and Bitunix providers.
Stores data in local database with provider-prefixed symbols for unique storage.

Usage:
    python tools/download_historical_data.py --provider alpaca --symbols BTC/USD --days 365
    python tools/download_historical_data.py --provider bitunix --symbols BTCUSDT,ETHUSDT --days 365
    python tools/download_historical_data.py --both --days 365  # Download both BTC from both providers
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.loader import config_manager
from src.core.market_data.historical_data_manager import HistoricalDataManager
from src.core.market_data.types import DataSource, Timeframe
from src.core.market_data.providers.bitunix_provider import BitunixProvider
from src.database import initialize_database

logger = logging.getLogger(__name__)


async def download_alpaca_crypto(
    symbols: list[str],
    days_back: int = 365,
    timeframe: Timeframe = Timeframe.MINUTE_1,
) -> dict:
    """Download historical data from Alpaca Crypto API.

    Args:
        symbols: List of crypto symbols (e.g., ["BTC/USD", "ETH/USD"])
        days_back: Number of days of history to download
        timeframe: Timeframe for bars

    Returns:
        Dictionary with download results
    """
    try:
        from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider

        # Get Alpaca credentials (optional for crypto market data)
        api_key = config_manager.get_credential("alpaca_api_key")
        api_secret = config_manager.get_credential("alpaca_api_secret")

        if not api_key or not api_secret:
            logger.info("ℹ️  Alpaca API keys not found - using public crypto market data API")
            logger.info("   (Keys are only needed for trading operations)")
            provider = AlpacaCryptoProvider()  # No keys needed for market data
        else:
            logger.info("✅ Alpaca API keys found - using authenticated client")
            provider = AlpacaCryptoProvider(api_key, api_secret)

        # Create manager
        manager = HistoricalDataManager()

        # Download data
        logger.info(f"Starting Alpaca download for {symbols}")
        results = await manager.bulk_download(
            provider=provider,
            symbols=symbols,
            days_back=days_back,
            timeframe=timeframe,
            source=DataSource.ALPACA_CRYPTO,
            batch_size=100,
        )

        # Show coverage
        for symbol in symbols:
            coverage = await manager.get_data_coverage(symbol, DataSource.ALPACA_CRYPTO)
            logger.info(f"\n{'='*60}")
            logger.info(f"Symbol: {coverage['symbol']}")
            logger.info(f"First Date: {coverage['first_date']}")
            logger.info(f"Last Date: {coverage['last_date']}")
            logger.info(f"Total Bars: {coverage['total_bars']:,}")
            logger.info(f"Coverage: {coverage['coverage_days']} days")
            logger.info(f"{'='*60}\n")

        return results

    except ImportError as e:
        logger.error(f"Failed to import Alpaca provider: {e}")
        logger.error("Make sure alpaca-py package is installed: pip install alpaca-py")
        return {}
    except Exception as e:
        logger.error(f"Failed to download from Alpaca: {e}", exc_info=True)
        return {}


async def download_bitunix(
    symbols: list[str],
    days_back: int = 365,
    timeframe: Timeframe = Timeframe.MINUTE_1,
) -> dict:
    """Download historical data from Bitunix Futures API.

    Args:
        symbols: List of crypto symbols (e.g., ["BTCUSDT", "ETHUSDT"])
        days_back: Number of days of history to download
        timeframe: Timeframe for bars

    Returns:
        Dictionary with download results
    """
    try:
        # Get Bitunix credentials
        api_key = config_manager.get_credential("bitunix_api_key")
        api_secret = config_manager.get_credential("bitunix_api_secret")

        if not api_key or not api_secret:
            logger.error("Bitunix API keys not found in environment variables!")
            logger.error("Please set BITUNIX_API_KEY and BITUNIX_API_SECRET")
            return {}

        # Create provider
        provider = BitunixProvider(
            api_key=api_key,
            api_secret=api_secret,
            use_testnet=False,  # Use mainnet for historical data
            max_bars=525600,  # 1 year of 1min bars
            max_batches=2628,  # 525600 / 200 bars per batch
        )

        # Create manager
        manager = HistoricalDataManager()

        # Download data
        logger.info(f"Starting Bitunix download for {symbols}")
        results = await manager.bulk_download(
            provider=provider,
            symbols=symbols,
            days_back=days_back,
            timeframe=timeframe,
            source=DataSource.BITUNIX,
            batch_size=100,
        )

        # Show coverage
        for symbol in symbols:
            coverage = await manager.get_data_coverage(symbol, DataSource.BITUNIX)
            logger.info(f"\n{'='*60}")
            logger.info(f"Symbol: {coverage['symbol']}")
            logger.info(f"First Date: {coverage['first_date']}")
            logger.info(f"Last Date: {coverage['last_date']}")
            logger.info(f"Total Bars: {coverage['total_bars']:,}")
            logger.info(f"Coverage: {coverage['coverage_days']} days")
            logger.info(f"{'='*60}\n")

        return results

    except Exception as e:
        logger.error(f"Failed to download from Bitunix: {e}", exc_info=True)
        return {}


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download historical market data from Alpaca and/or Bitunix"
    )
    parser.add_argument(
        "--provider",
        choices=["alpaca", "bitunix", "both"],
        default="both",
        help="Data provider (default: both)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated list of symbols (e.g., 'BTC/USD,ETH/USD' or 'BTCUSDT,ETHUSDT')"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days of history to download (default: 365)"
    )
    parser.add_argument(
        "--timeframe",
        choices=["1min", "5min", "15min", "1h", "4h", "1d"],
        default="1min",
        help="Bar timeframe (default: 1min)"
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Download BTC from both Alpaca (BTC/USD) and Bitunix (BTCUSDT)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: Download only 7 days of data"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output (DEBUG level)"
    )
    parser.add_argument(
        "--sqlite",
        action="store_true",
        help="Use SQLite database (useful when PostgreSQL is not available)"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test mode: only 7 days
    if args.test:
        args.days = 7
        logger.info("🧪 TEST MODE: Downloading only 7 days of data")

    # Map timeframe
    timeframe_map = {
        "1min": Timeframe.MINUTE_1,
        "5min": Timeframe.MINUTE_5,
        "15min": Timeframe.MINUTE_15,
        "1h": Timeframe.HOUR_1,
        "4h": Timeframe.HOUR_4,
        "1d": Timeframe.DAY_1,
    }
    timeframe = timeframe_map[args.timeframe]

    # Initialize database
    logger.info("Initializing database...")
    profile = config_manager.load_profile()

    # Override to SQLite if requested (useful when PostgreSQL not available)
    if args.sqlite:
        logger.info("📦 Using SQLite database (--sqlite flag)")
        profile.database.engine = "sqlite"
        profile.database.path = "./data/orderpilot_historical.db"

    initialize_database(profile.database)

    # Determine what to download
    if args.both or (not args.symbols and args.provider == "both"):
        # Default: Download BTC from both providers
        logger.info("📥 Downloading BTC from both Alpaca and Bitunix")

        alpaca_results = await download_alpaca_crypto(
            symbols=["BTC/USD"],
            days_back=args.days,
            timeframe=timeframe
        )

        bitunix_results = await download_bitunix(
            symbols=["BTCUSDT"],
            days_back=args.days,
            timeframe=timeframe
        )

        logger.info(f"\n{'='*60}")
        logger.info("📊 DOWNLOAD SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Alpaca (BTC/USD): {alpaca_results.get('BTC/USD', 0):,} bars")
        logger.info(f"Bitunix (BTCUSDT): {bitunix_results.get('BTCUSDT', 0):,} bars")
        logger.info(f"{'='*60}\n")

    elif args.provider == "alpaca" or (args.provider == "both" and args.symbols):
        if not args.symbols:
            logger.error("--symbols required for Alpaca provider")
            sys.exit(1)

        symbols = [s.strip() for s in args.symbols.split(",")]
        results = await download_alpaca_crypto(
            symbols=symbols,
            days_back=args.days,
            timeframe=timeframe
        )

        logger.info(f"\n{'='*60}")
        logger.info("📊 DOWNLOAD SUMMARY (Alpaca)")
        logger.info(f"{'='*60}")
        for symbol, count in results.items():
            logger.info(f"{symbol}: {count:,} bars")
        logger.info(f"{'='*60}\n")

    elif args.provider == "bitunix":
        if not args.symbols:
            logger.error("--symbols required for Bitunix provider")
            sys.exit(1)

        symbols = [s.strip() for s in args.symbols.split(",")]
        results = await download_bitunix(
            symbols=symbols,
            days_back=args.days,
            timeframe=timeframe
        )

        logger.info(f"\n{'='*60}")
        logger.info("📊 DOWNLOAD SUMMARY (Bitunix)")
        logger.info(f"{'='*60}")
        for symbol, count in results.items():
            logger.info(f"{symbol}: {count:,} bars")
        logger.info(f"{'='*60}\n")

    logger.info("✅ Download complete!")


if __name__ == "__main__":
    asyncio.run(main())
