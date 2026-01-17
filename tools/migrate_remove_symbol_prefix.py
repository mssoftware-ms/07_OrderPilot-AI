#!/usr/bin/env python3
"""Migration: Remove source prefix from symbol column.

BEFORE: symbol="bitunix:BTCUSDT", source="bitunix"
AFTER:  symbol="BTCUSDT", source="bitunix"

This allows querying by symbol without knowing the source prefix,
while still maintaining data source tracking via the 'source' column.
"""

import sqlite3
from datetime import datetime

def migrate_remove_symbol_prefix():
    """Remove source prefix from symbol column in market_bars table."""

    db_path = "data/orderpilot.db"

    print("=" * 80)
    print("Migration: Remove Symbol Prefix")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Started:  {datetime.now()}")
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Analyze current data
    print("Step 1: Analyzing current data...")
    cursor.execute("""
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT symbol) as unique_symbols,
            COUNT(DISTINCT source) as unique_sources
        FROM market_bars
    """)

    total, symbols, sources = cursor.fetchone()
    print(f"  Total rows:      {total:,}")
    print(f"  Unique symbols:  {symbols:,}")
    print(f"  Unique sources:  {sources}")
    print()

    # Step 2: Find symbols with prefix
    print("Step 2: Finding symbols with prefix...")
    cursor.execute("""
        SELECT DISTINCT symbol, source
        FROM market_bars
        WHERE symbol LIKE '%:%'
        ORDER BY symbol
    """)

    prefixed_symbols = cursor.fetchall()
    print(f"  Found {len(prefixed_symbols)} symbols with prefix:")
    for symbol, source in prefixed_symbols[:10]:  # Show first 10
        print(f"    {symbol} (source: {source})")
    if len(prefixed_symbols) > 10:
        print(f"    ... and {len(prefixed_symbols) - 10} more")
    print()

    if not prefixed_symbols:
        print("✅ No migration needed - symbols already clean!")
        conn.close()
        return

    # Step 3: Create backup
    print("Step 3: Creating backup table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_bars_backup AS
        SELECT * FROM market_bars
    """)

    backup_count = cursor.execute("SELECT COUNT(*) FROM market_bars_backup").fetchone()[0]
    print(f"  ✅ Backup created: {backup_count:,} rows")
    print()

    # Step 4: Update symbols (remove prefix)
    print("Step 4: Removing prefixes from symbols...")

    # SQLite doesn't have SPLIT_PART, so we need to update row by row
    # But we can be smart: UPDATE with SUBSTR

    # For each prefixed symbol, extract the part after ":"
    updated_count = 0
    for old_symbol, source in prefixed_symbols:
        # Extract symbol part after ":"
        if ":" in old_symbol:
            new_symbol = old_symbol.split(":", 1)[1]

            # Update all rows with this symbol
            cursor.execute("""
                UPDATE market_bars
                SET symbol = ?
                WHERE symbol = ? AND source = ?
            """, (new_symbol, old_symbol, source))

            rows_updated = cursor.rowcount
            updated_count += rows_updated

            if rows_updated > 0:
                print(f"  ✅ {old_symbol} → {new_symbol} ({rows_updated:,} rows)")

    print()
    print(f"  Total rows updated: {updated_count:,}")
    print()

    # Step 5: Verify migration
    print("Step 5: Verifying migration...")
    cursor.execute("""
        SELECT COUNT(*) FROM market_bars WHERE symbol LIKE '%:%'
    """)
    remaining_prefixed = cursor.fetchone()[0]

    if remaining_prefixed > 0:
        print(f"  ⚠️ Warning: {remaining_prefixed} rows still have prefix!")
        cursor.execute("""
            SELECT DISTINCT symbol FROM market_bars WHERE symbol LIKE '%:%' LIMIT 5
        """)
        print("  Examples:")
        for (symbol,) in cursor.fetchall():
            print(f"    {symbol}")
    else:
        print("  ✅ All prefixes removed successfully!")

    # Show new state
    cursor.execute("""
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT symbol) as unique_symbols,
            COUNT(DISTINCT source) as unique_sources
        FROM market_bars
    """)

    total, symbols, sources = cursor.fetchone()
    print()
    print("  New state:")
    print(f"    Total rows:      {total:,}")
    print(f"    Unique symbols:  {symbols:,}")
    print(f"    Unique sources:  {sources}")
    print()

    # Step 6: Commit changes
    print("Step 6: Committing changes...")
    conn.commit()
    print("  ✅ Changes committed!")
    print()

    # Step 7: Final summary
    print("=" * 80)
    print("Migration Summary")
    print("=" * 80)
    print(f"  Rows updated:        {updated_count:,}")
    print(f"  Symbols migrated:    {len(prefixed_symbols)}")
    print(f"  Remaining prefixed:  {remaining_prefixed}")
    print(f"  Backup table:        market_bars_backup ({backup_count:,} rows)")
    print()
    print("✅ Migration completed successfully!")
    print(f"Finished: {datetime.now()}")
    print("=" * 80)

    conn.close()


def rollback_migration():
    """Rollback migration - restore from backup."""

    db_path = "data/orderpilot.db"

    print("=" * 80)
    print("Migration Rollback: Restore Symbol Prefixes")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if backup exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='market_bars_backup'
    """)

    if not cursor.fetchone():
        print("❌ Error: No backup table found!")
        print("   Cannot rollback migration.")
        conn.close()
        return

    print("Step 1: Dropping current market_bars table...")
    cursor.execute("DROP TABLE market_bars")
    print("  ✅ Dropped")

    print("Step 2: Restoring from backup...")
    cursor.execute("ALTER TABLE market_bars_backup RENAME TO market_bars")
    print("  ✅ Restored")

    print("Step 3: Committing changes...")
    conn.commit()
    print("  ✅ Committed")

    print()
    print("✅ Rollback completed successfully!")
    print("=" * 80)

    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        print("⚠️  ROLLBACK MODE")
        print()
        confirm = input("Are you sure you want to rollback the migration? (y/yes): ")
        if confirm.lower() in ("y", "yes"):
            rollback_migration()
        else:
            print("Rollback cancelled.")
    else:
        print("This migration will remove source prefixes from symbol column.")
        print("A backup will be created automatically.")
        print()
        confirm = input("Proceed with migration? (y/yes): ")
        if confirm.lower() in ("y", "yes"):
            migrate_remove_symbol_prefix()
        else:
            print("Migration cancelled.")
