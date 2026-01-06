"""Clean Bad Ticks from Database - Permanent Deletion.

This script finds and DELETES bad ticks directly from the database.
"""

import sqlite3
import logging
from datetime import datetime

import pandas as pd

from src.analysis.data_cleaning import BadTickDetector

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

db_path = "./data/orderpilot_historical.db"


def clean_bad_ticks_from_database(symbol: str = "alpaca_crypto:BTC/USD", dry_run: bool = False):
    """Clean bad ticks from database.

    Args:
        symbol: Symbol to clean
        dry_run: If True, only show what would be deleted without actually deleting
    """
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Load all data for symbol
    query = """
        SELECT id, timestamp, open, high, low, close, volume
        FROM market_bars
        WHERE symbol = ?
        ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn, params=(symbol,))

    if df.empty:
        logger.warning(f"No data found for {symbol}")
        conn.close()
        return

    logger.info(f"Loaded {len(df)} bars for {symbol}")

    # Initialize detector with AGGRESSIVE settings
    detector = BadTickDetector(
        max_price_deviation_pct=5.0,  # 5% threshold (more aggressive)
        min_volume=0,
        check_ohlc_consistency=True,
        check_price_spikes=True,
        check_volume_anomalies=False,
        check_duplicates=True,
    )

    # Detect bad ticks
    bad_mask = detector.detect_bad_ticks(df[['timestamp', 'open', 'high', 'low', 'close', 'volume']])
    bad_count = bad_mask.sum()

    if bad_count == 0:
        logger.info("✅ No bad ticks found!")
        conn.close()
        return

    # Show bad ticks
    bad_df = df[bad_mask]
    logger.warning(f"\n⚠️  Found {bad_count} bad ticks ({bad_count/len(df)*100:.2f}%):\n")

    for idx, row in bad_df.head(20).iterrows():
        logger.warning(
            f"  ID {row['id']}: {row['timestamp']} | "
            f"O:{row['open']} H:{row['high']} L:{row['low']} C:{row['close']}"
        )

    if len(bad_df) > 20:
        logger.warning(f"  ... and {len(bad_df) - 20} more")

    # DELETE bad ticks from database
    if dry_run:
        logger.info("\n🔍 DRY RUN - Would delete these bad ticks (use --delete to actually delete)")
    else:
        logger.warning(f"\n🗑️  DELETING {bad_count} bad ticks from database...")

        # Get IDs to delete
        bad_ids = bad_df['id'].tolist()

        # Delete in batches
        batch_size = 100
        deleted_count = 0

        for i in range(0, len(bad_ids), batch_size):
            batch = bad_ids[i:i+batch_size]
            placeholders = ','.join('?' * len(batch))
            delete_query = f"DELETE FROM market_bars WHERE id IN ({placeholders})"
            cursor.execute(delete_query, batch)
            deleted_count += len(batch)
            logger.info(f"  Deleted batch {i//batch_size + 1}: {deleted_count}/{len(bad_ids)}")

        conn.commit()
        logger.info(f"\n✅ Successfully deleted {deleted_count} bad ticks!")

        # Verify
        verify_query = "SELECT COUNT(*) FROM market_bars WHERE symbol = ?"
        remaining = cursor.execute(verify_query, (symbol,)).fetchone()[0]
        logger.info(f"✅ Remaining bars: {remaining} (was: {len(df)})")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean bad ticks from database")
    parser.add_argument("--symbol", default="alpaca_crypto:BTC/USD", help="Symbol to clean")
    parser.add_argument("--delete", action="store_true", help="Actually delete (default is dry-run)")

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("DATABASE BAD TICK CLEANER")
    logger.info("="*80)

    if not args.delete:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        logger.info("   Use --delete flag to actually delete bad ticks")

    logger.info(f"Symbol: {args.symbol}")
    logger.info("="*80 + "\n")

    clean_bad_ticks_from_database(args.symbol, dry_run=not args.delete)

    logger.info("\n" + "="*80)
    logger.info("DONE")
    logger.info("="*80 + "\n")
