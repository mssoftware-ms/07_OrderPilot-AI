"""Build Pattern Database from Historical Data.

Fetches historical data from Alpaca and builds the Qdrant pattern database.
Run this script to populate the database with historical patterns.

Usage:
    python -m src.core.pattern_db.build_database --stocks --crypto --days 365

Docker: Qdrant must be running on localhost:6333
    docker run -p 6333:6333 qdrant/qdrant
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(__file__).rsplit("src", 1)[0])

from src.core.pattern_db.fetcher import PatternDataFetcher, NASDAQ_100_TOP, CRYPTO_SYMBOLS
from src.core.pattern_db.extractor import PatternExtractor
from src.core.pattern_db.qdrant_client import TradingPatternDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def _process_symbol_batch(
    label: str,
    symbols: list[str],
    fetcher: PatternDataFetcher,
    extractor: PatternExtractor,
    db: TradingPatternDB,
    config,
) -> int:
    """Fetch bars, extract patterns, and insert into Qdrant."""
    logger.info(f"\nProcessing {len(symbols)} {label} symbols...")

    config.symbols = symbols

    def progress(symbol, tf, bars, done, total):
        logger.info(f"[{done}/{total}] {symbol} {tf.value}: {bars} bars")

    total_patterns = 0
    async for symbol, timeframe, bars in fetcher.fetch_batch(config, progress):
        if not bars:
            continue

        patterns = list(extractor.extract_patterns(bars, symbol, timeframe.value))
        if patterns:
            inserted = await db.insert_patterns_batch(patterns, batch_size=500)
            total_patterns += inserted
            logger.info(f"  -> Inserted {inserted} patterns for {symbol} {timeframe.value}")

    return total_patterns


async def build_database(
    include_stocks: bool = True,
    include_crypto: bool = True,
    days_back: int = 365,
    window_size: int = 20,
    step_size: int = 5,
    outcome_bars: int = 5,
    stock_symbols: list[str] = None,
    crypto_symbols: list[str] = None,
):
    """Build the pattern database.

    Args:
        include_stocks: Include stock patterns
        include_crypto: Include crypto patterns
        days_back: Days of historical data
        window_size: Pattern window size
        step_size: Step between patterns (higher = fewer patterns)
        outcome_bars: Bars to measure outcome
        stock_symbols: Custom stock symbols (default: NASDAQ-100 top 50)
        crypto_symbols: Custom crypto symbols (default: BTC/USD, ETH/USD)
    """
    logger.info("=" * 60)
    logger.info("Building Trading Pattern Database")
    logger.info("=" * 60)
    logger.info(f"Stocks: {include_stocks}, Crypto: {include_crypto}")
    logger.info(f"Days back: {days_back}, Window: {window_size}, Step: {step_size}")
    logger.info("=" * 60)

    # Initialize components
    fetcher = PatternDataFetcher()
    extractor = PatternExtractor(
        window_size=window_size,
        step_size=step_size,
        outcome_bars=outcome_bars,
    )
    db = TradingPatternDB()

    # Initialize Qdrant collection
    logger.info("Initializing Qdrant collection...")
    if not await db.initialize():
        logger.error("Failed to initialize Qdrant. Is Docker running?")
        logger.error("Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        return

    # Get collection info
    info = await db.get_collection_info()
    logger.info(f"Collection info: {info}")

    total_patterns = 0
    start_time = datetime.now()

    # Process stocks
    if include_stocks:
        symbols = stock_symbols or NASDAQ_100_TOP
        stock_config = fetcher.get_default_stock_config(days_back)
        total_patterns += await _process_symbol_batch(
            "stock",
            symbols,
            fetcher,
            extractor,
            db,
            stock_config,
        )

    # Process crypto
    if include_crypto:
        symbols = crypto_symbols or CRYPTO_SYMBOLS
        crypto_config = fetcher.get_default_crypto_config(days_back)
        total_patterns += await _process_symbol_batch(
            "crypto",
            symbols,
            fetcher,
            extractor,
            db,
            crypto_config,
        )

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("\n" + "=" * 60)
    logger.info("Build Complete!")
    logger.info("=" * 60)
    logger.info(f"Total patterns: {total_patterns:,}")
    logger.info(f"Elapsed time: {elapsed:.1f}s")
    logger.info(f"Patterns/sec: {total_patterns / elapsed:.1f}")

    # Final collection info
    info = await db.get_collection_info()
    logger.info(f"Collection: {info}")


def main():
    parser = argparse.ArgumentParser(
        description="Build Trading Pattern Database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build with defaults (NASDAQ-100 + BTC/ETH, 1 year)
  python -m src.core.pattern_db.build_database

  # Only crypto with 6 months
  python -m src.core.pattern_db.build_database --crypto --days 180

  # Only stocks with 2 years
  python -m src.core.pattern_db.build_database --stocks --days 730

  # Custom symbols
  python -m src.core.pattern_db.build_database --stocks --symbols AAPL MSFT NVDA
        """,
    )

    parser.add_argument(
        "--stocks",
        action="store_true",
        help="Include stock patterns (NASDAQ-100)",
    )
    parser.add_argument(
        "--crypto",
        action="store_true",
        help="Include crypto patterns (BTC/ETH)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Days of historical data (default: 365)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=20,
        help="Pattern window size in bars (default: 20)",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=5,
        help="Step between patterns (default: 5)",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Custom stock symbols (overrides NASDAQ-100)",
    )
    parser.add_argument(
        "--crypto-symbols",
        nargs="+",
        help="Custom crypto symbols (default: BTC/USD ETH/USD)",
    )

    args = parser.parse_args()

    # If neither specified, include both
    if not args.stocks and not args.crypto:
        args.stocks = True
        args.crypto = True

    asyncio.run(
        build_database(
            include_stocks=args.stocks,
            include_crypto=args.crypto,
            days_back=args.days,
            window_size=args.window,
            step_size=args.step,
            stock_symbols=args.symbols,
            crypto_symbols=args.crypto_symbols,
        )
    )


if __name__ == "__main__":
    main()
