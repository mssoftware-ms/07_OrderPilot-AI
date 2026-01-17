"""Fix OHLC inconsistencies in database caused by Bitunix rounding errors.

This script validates and corrects OHLC data in the market_bars table:
- Ensures high >= max(open, close)
- Ensures low <= min(open, close)
- Creates backup before making changes

Usage:
    python tools/fix_ohlc_database.py [--dry-run] [--symbol SYMBOL]

Note: This CLI tool is provided for convenience. The same functionality
is available in the GUI: Settings -> Market Data -> Bitunix -> "Validate & Fix OHLC Data"
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.ohlc_validator import OHLCValidator


def validate_and_fix_ohlc(symbol: str | None = None, dry_run: bool = True):
    """Validate and fix OHLC data using the OHLCValidator class.

    Args:
        symbol: Optional symbol filter (default: all symbols)
        dry_run: If True, only report issues without fixing
    """
    validator = OHLCValidator()

    # Progress callback for CLI
    def progress_callback(current: int, total: int, message: str):
        if current % 10 == 0 or current == total:
            pct = int((current / total) * 100) if total > 0 else 0
            print(f"[{pct:3d}%] {message}")

    print(f"\n{'=' * 80}")
    print(f"OHLC Validation {'(DRY RUN)' if dry_run else '(APPLY FIXES)'}")
    print(f"{'=' * 80}\n")

    results = validator.validate_and_fix(
        symbol=symbol,
        dry_run=dry_run,
        progress_callback=progress_callback
    )

    print(f"\n{'=' * 80}")
    print("Results:")
    print(f"{'=' * 80}")
    print(f"Invalid bars found: {results['invalid_bars']}")
    print(f"Bars fixed:         {results['fixed_bars']}")
    print(f"Symbols affected:   {', '.join(results['symbols_affected']) if results['symbols_affected'] else 'None'}")
    print(f"{'=' * 80}\n")

    if dry_run and results['invalid_bars'] > 0:
        print("⚠️  DRY RUN - No changes made. Run with --apply to fix.\n")
    elif results['fixed_bars'] > 0:
        print(f"✅ Fixed {results['fixed_bars']} bars!\n")


def create_backup(db_path: str) -> str:
    """Create a backup of the database.

    Args:
        db_path: Path to database

    Returns:
        Path to backup file
    """
    import sqlite3
    from datetime import datetime

    db_file = Path(db_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_file.parent / f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"

    conn = sqlite3.connect(db_path)
    backup_conn = sqlite3.connect(str(backup_path))
    conn.backup(backup_conn)
    backup_conn.close()
    conn.close()

    print(f"✅ Backup created: {backup_path}")
    return str(backup_path)


def main():
    parser = argparse.ArgumentParser(
        description="Fix OHLC inconsistencies in database",
        epilog="Note: This functionality is also available in the GUI: "
               "Settings -> Market Data -> Bitunix -> 'Validate & Fix OHLC Data'"
    )
    parser.add_argument(
        "--db",
        default="data/orderpilot.db",
        help="Path to database (default: data/orderpilot.db)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report issues without fixing"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply fixes (creates backup first)"
    )
    parser.add_argument(
        "--symbol",
        help="Filter by symbol (default: all symbols)"
    )

    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    # Initialize database connection (required for OHLCValidator)
    from src.config.loader import config_manager
    from src.database import initialize_database

    profile = config_manager.load_profile()
    profile.database.engine = "sqlite"
    profile.database.path = str(db_path)
    initialize_database(profile.database)

    if args.apply and not args.dry_run:
        # Create backup before applying fixes
        create_backup(str(db_path))
        validate_and_fix_ohlc(symbol=args.symbol, dry_run=False)
    else:
        # Dry run (default)
        validate_and_fix_ohlc(symbol=args.symbol, dry_run=True)


if __name__ == "__main__":
    main()
