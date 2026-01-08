"""Clean Bad Ticks from Database - Using Hampel Filter with Volume Confirmation.

This script scans and cleans bad ticks from the historical market data database.
Uses Hampel Filter (MAD-based) with volume confirmation to distinguish between:
- Bad ticks (price spikes WITHOUT high volume) → Interpolate/Remove
- Real market events (price spikes WITH high volume) → Keep

Usage:
    # Scan all symbols (dry run)
    python tools/clean_database_bad_ticks.py --scan

    # Preview what would be cleaned for a specific symbol
    python tools/clean_database_bad_ticks.py --symbol alpaca_crypto:BTC/USD

    # Actually clean (interpolate bad ticks)
    python tools/clean_database_bad_ticks.py --symbol alpaca_crypto:BTC/USD --clean

    # Delete bad ticks instead of interpolating
    python tools/clean_database_bad_ticks.py --symbol alpaca_crypto:BTC/USD --clean --mode remove

    # Adjust filter sensitivity for crypto (higher threshold)
    python tools/clean_database_bad_ticks.py --symbol alpaca_crypto:BTC/USD --threshold 4.5
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.market_data.historical_data_manager import (
    FilterConfig,
    FilterStats,
    HistoricalDataManager,
)
from src.core.market_data.types import DataSource

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def scan_all_symbols(config: FilterConfig) -> dict[str, FilterStats]:
    """Scan all symbols in database for bad ticks."""
    manager = HistoricalDataManager(filter_config=config)
    return await manager.scan_all_symbols_for_bad_ticks()


async def clean_symbol(
    symbol: str,
    source: DataSource,
    config: FilterConfig,
    dry_run: bool = True
) -> FilterStats:
    """Clean bad ticks for a specific symbol."""
    manager = HistoricalDataManager(filter_config=config)
    return await manager.clean_existing_data(
        symbol=symbol,
        source=source,
        filter_config=config,
        dry_run=dry_run
    )


def parse_symbol(db_symbol: str) -> tuple[str, DataSource]:
    """Parse database symbol format (e.g., 'alpaca_crypto:BTC/USD').

    Returns:
        Tuple of (clean_symbol, DataSource)
    """
    if ':' in db_symbol:
        source_str, symbol = db_symbol.split(':', 1)
    else:
        # Assume alpaca_crypto if no prefix
        source_str = "alpaca_crypto"
        symbol = db_symbol

    # Map source string to DataSource enum
    source_map = {
        'alpaca_crypto': DataSource.ALPACA_CRYPTO,
        'alpaca_stock': DataSource.ALPACA_STOCK,
        'bitunix': DataSource.BITUNIX,
    }
    source = source_map.get(source_str.lower(), DataSource.ALPACA_CRYPTO)

    return symbol, source


def main():
    parser = argparse.ArgumentParser(
        description="Clean bad ticks from database using Hampel Filter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan all symbols for bad ticks (dry run)
  python tools/clean_database_bad_ticks.py --scan

  # Preview cleaning for BTC/USD
  python tools/clean_database_bad_ticks.py --symbol alpaca_crypto:BTC/USD

  # Actually clean (interpolate bad ticks)
  python tools/clean_database_bad_ticks.py --symbol alpaca_crypto:BTC/USD --clean

  # Delete bad ticks instead of interpolating
  python tools/clean_database_bad_ticks.py --symbol alpaca_crypto:BTC/USD --clean --mode remove

  # Use higher threshold for volatile crypto (less sensitive)
  python tools/clean_database_bad_ticks.py --symbol alpaca_crypto:BTC/USD --threshold 4.5 --clean

Filter Methods:
  hampel    - Hampel Filter with MAD (Median Absolute Deviation) - RECOMMENDED
  zscore    - Standard Z-Score based detection
  basic     - Simple percentage deviation from moving average

Cleaning Modes:
  interpolate  - Replace bad tick values with interpolated values (RECOMMENDED)
  remove       - Delete bad tick rows entirely
  forward_fill - Replace with previous valid value
        """
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan all symbols for bad ticks (dry run)"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Symbol to clean (e.g., 'alpaca_crypto:BTC/USD' or just 'BTC/USD')"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Actually clean (without this flag, only preview)"
    )

    # Filter configuration
    parser.add_argument(
        "--method",
        type=str,
        choices=["hampel", "zscore", "basic"],
        default="hampel",
        help="Detection method (default: hampel)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["interpolate", "remove", "forward_fill"],
        default="interpolate",
        help="Cleaning mode (default: interpolate)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.5,
        help="Outlier threshold (default: 3.5, use 4.0-6.0 for crypto)"
    )
    parser.add_argument(
        "--window",
        type=int,
        default=15,
        help="Rolling window size (default: 15)"
    )
    parser.add_argument(
        "--volume-mult",
        type=float,
        default=10.0,
        help="Volume multiplier for high-volume detection (default: 10.0)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Build filter config
    config = FilterConfig(
        enabled=True,
        method=args.method,
        cleaning_mode=args.mode,
        hampel_window=args.window,
        hampel_threshold=args.threshold,
        volume_multiplier=args.volume_mult,
        log_stats=True,
    )

    print("\n" + "=" * 70)
    print("🛡️  BAD TICK CLEANER - Hampel Filter with Volume Confirmation")
    print("=" * 70)
    print(f"Method: {config.method}")
    print(f"Threshold: {config.hampel_threshold}")
    print(f"Window: {config.hampel_window}")
    print(f"Volume Multiplier: {config.volume_multiplier}x")
    print(f"Cleaning Mode: {config.cleaning_mode}")
    print("=" * 70 + "\n")

    if args.scan:
        # Scan all symbols
        print("📊 Scanning all symbols for bad ticks...\n")
        results = asyncio.run(scan_all_symbols(config))

        if results:
            print("\n" + "-" * 70)
            print("SCAN RESULTS:")
            print("-" * 70)

            total_bars = 0
            total_bad = 0
            symbols_with_bad = []

            for symbol, stats in sorted(results.items()):
                total_bars += stats.total_bars
                total_bad += stats.bad_ticks_found
                if stats.bad_ticks_found > 0:
                    symbols_with_bad.append((symbol, stats))
                    print(f"  ⚠️  {symbol}: {stats.bad_ticks_found:,} bad ticks "
                          f"({stats.filtering_percentage:.2f}%) in {stats.total_bars:,} bars")

            print("-" * 70)
            print(f"TOTAL: {total_bad:,} bad ticks in {total_bars:,} bars "
                  f"({total_bad/total_bars*100:.2f}%)" if total_bars > 0 else "No data found")

            if symbols_with_bad:
                print("\nTo clean a specific symbol, run:")
                print(f"  python tools/clean_database_bad_ticks.py --symbol {symbols_with_bad[0][0]} --clean")
        else:
            print("No data found in database")

    elif args.symbol:
        # Clean specific symbol
        symbol, source = parse_symbol(args.symbol)
        dry_run = not args.clean

        if dry_run:
            print(f"🔍 DRY RUN - Preview cleaning for {args.symbol}")
            print("   (Use --clean flag to actually clean)\n")
        else:
            print(f"🧹 CLEANING {args.symbol} (mode: {config.cleaning_mode})\n")

        stats = asyncio.run(clean_symbol(symbol, source, config, dry_run))

        print("\n" + "-" * 70)
        print("RESULTS:")
        print("-" * 70)
        print(f"Total Bars: {stats.total_bars:,}")
        print(f"Bad Ticks Found: {stats.bad_ticks_found:,}")
        print(f"Percentage: {stats.filtering_percentage:.2f}%")

        if not dry_run:
            if config.cleaning_mode == "remove":
                print(f"Removed: {stats.bad_ticks_removed:,}")
            else:
                print(f"Interpolated: {stats.bad_ticks_interpolated:,}")
        else:
            print("\n💡 Run with --clean to actually clean the data")

    else:
        parser.print_help()
        print("\n⚠️  Please specify --scan or --symbol")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
