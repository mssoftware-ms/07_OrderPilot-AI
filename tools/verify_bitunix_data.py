"""Verify downloaded Bitunix data quality and coverage.

This script analyzes the market_bars table for Bitunix data:
- Confirms actual timeframe (1min, 5min, etc.)
- Counts total bars and calculates coverage
- Detects gaps (missing data)
- Checks OHLC consistency
- Analyzes data quality

Usage:
    python tools/verify_bitunix_data.py [--symbol SYMBOL] [--timeframe TIMEFRAME]

Example:
    python tools/verify_bitunix_data.py --symbol bitunix:BTCUSDT --timeframe 1min
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_data(symbol: str = "bitunix:BTCUSDT", expected_timeframe: str = "1min"):
    """Verify downloaded Bitunix data.

    Args:
        symbol: Symbol to analyze (default: bitunix:BTCUSDT)
        expected_timeframe: Expected timeframe (default: 1min)
    """
    from src.database import get_db_manager

    db = get_db_manager()

    # Timeframe intervals in minutes
    timeframe_minutes = {
        "1min": 1,
        "5min": 5,
        "15min": 15,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
    }

    expected_interval = timeframe_minutes.get(expected_timeframe, 1)

    print(f"\n{'=' * 80}")
    print(f"BITUNIX DATA VERIFICATION")
    print(f"{'=' * 80}\n")
    print(f"Symbol:              {symbol}")
    print(f"Expected Timeframe:  {expected_timeframe} ({expected_interval} minutes)")
    print(f"Database:            {db.db_path}")
    print(f"\n{'=' * 80}")

    # Query all bars for the symbol
    query = """
        SELECT
            timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM market_bars
        WHERE symbol = ?
        ORDER BY timestamp ASC
    """

    with db.session_scope() as session:
        result = session.execute(query, (symbol,))
        bars = list(result)

    if not bars:
        print(f"\n❌ No data found for symbol: {symbol}\n")
        return

    total_bars = len(bars)
    first_bar = bars[0]
    last_bar = bars[-1]

    first_ts = datetime.fromisoformat(first_bar[0])
    last_ts = datetime.fromisoformat(last_bar[0])

    time_span = last_ts - first_ts
    days = time_span.days + (time_span.seconds / 86400)

    print(f"\n📊 BASIC STATISTICS")
    print(f"{'=' * 80}")
    print(f"Total bars:          {total_bars:,}")
    print(f"First timestamp:     {first_ts.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Last timestamp:      {last_ts.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Time span:           {days:.2f} days ({time_span})")

    # Calculate expected bars
    total_minutes = time_span.total_seconds() / 60

    # For crypto markets (24/7 trading)
    expected_bars = int(total_minutes / expected_interval) + 1

    coverage_pct = (total_bars / expected_bars) * 100 if expected_bars > 0 else 0
    missing_bars = expected_bars - total_bars

    print(f"\n📈 COVERAGE ANALYSIS")
    print(f"{'=' * 80}")
    print(f"Expected bars:       {expected_bars:,} ({expected_timeframe} intervals)")
    print(f"Actual bars:         {total_bars:,}")
    print(f"Missing bars:        {missing_bars:,}")
    print(f"Coverage:            {coverage_pct:.2f}%")

    # Analyze time intervals between bars
    print(f"\n⏱️  INTERVAL ANALYSIS")
    print(f"{'=' * 80}")

    intervals = []
    for i in range(1, len(bars)):
        prev_ts = datetime.fromisoformat(bars[i-1][0])
        curr_ts = datetime.fromisoformat(bars[i][0])
        interval_minutes = (curr_ts - prev_ts).total_seconds() / 60
        intervals.append(interval_minutes)

    if intervals:
        min_interval = min(intervals)
        max_interval = max(intervals)
        avg_interval = sum(intervals) / len(intervals)

        # Count intervals matching expected timeframe
        correct_intervals = sum(1 for i in intervals if abs(i - expected_interval) < 0.1)
        correct_pct = (correct_intervals / len(intervals)) * 100

        print(f"Min interval:        {min_interval:.2f} minutes")
        print(f"Max interval:        {max_interval:.2f} minutes")
        print(f"Avg interval:        {avg_interval:.2f} minutes")
        print(f"Correct intervals:   {correct_intervals:,} / {len(intervals):,} ({correct_pct:.2f}%)")

        if abs(avg_interval - expected_interval) < 0.5:
            print(f"✅ Average interval matches expected {expected_timeframe}")
        else:
            print(f"⚠️  Average interval ({avg_interval:.2f}min) differs from expected {expected_timeframe} ({expected_interval}min)")

    # Detect gaps (intervals > 2x expected)
    print(f"\n🔍 GAP DETECTION")
    print(f"{'=' * 80}")

    gap_threshold = expected_interval * 2
    gaps = []

    for i in range(1, len(bars)):
        prev_ts = datetime.fromisoformat(bars[i-1][0])
        curr_ts = datetime.fromisoformat(bars[i][0])
        interval_minutes = (curr_ts - prev_ts).total_seconds() / 60

        if interval_minutes > gap_threshold:
            gaps.append({
                'start': prev_ts,
                'end': curr_ts,
                'duration_min': interval_minutes,
                'missing_bars': int(interval_minutes / expected_interval) - 1
            })

    if gaps:
        print(f"Gaps found:          {len(gaps)} (intervals > {gap_threshold:.0f} minutes)")
        print(f"\nTop 10 largest gaps:")
        print(f"{'-' * 80}")

        # Sort by duration and show top 10
        gaps.sort(key=lambda x: x['duration_min'], reverse=True)
        for i, gap in enumerate(gaps[:10], 1):
            duration_hours = gap['duration_min'] / 60
            print(f"{i:2d}. {gap['start']} → {gap['end']}")
            print(f"    Duration: {duration_hours:.2f} hours ({gap['duration_min']:.0f} min)")
            print(f"    Missing:  ~{gap['missing_bars']} bars")
    else:
        print(f"✅ No gaps detected (all intervals ≤ {gap_threshold:.0f} minutes)")

    # OHLC Consistency Check
    print(f"\n🎯 OHLC CONSISTENCY")
    print(f"{'=' * 80}")

    ohlc_errors = []

    for i, bar in enumerate(bars):
        timestamp = bar[0]
        o = float(bar[1])
        h = float(bar[2])
        l = float(bar[3])
        c = float(bar[4])

        # Check OHLC consistency
        if h < max(o, c) or l > min(o, c):
            ohlc_errors.append({
                'index': i,
                'timestamp': timestamp,
                'open': o,
                'high': h,
                'low': l,
                'close': c,
                'issue': []
            })

            if h < o:
                ohlc_errors[-1]['issue'].append(f"high ({h}) < open ({o})")
            if h < c:
                ohlc_errors[-1]['issue'].append(f"high ({h}) < close ({c})")
            if l > o:
                ohlc_errors[-1]['issue'].append(f"low ({l}) > open ({o})")
            if l > c:
                ohlc_errors[-1]['issue'].append(f"low ({l}) > close ({c})")

    if ohlc_errors:
        print(f"❌ OHLC errors found: {len(ohlc_errors)} bars")
        print(f"\nFirst 10 errors:")
        print(f"{'-' * 80}")

        for i, err in enumerate(ohlc_errors[:10], 1):
            print(f"{i:2d}. {err['timestamp']}")
            print(f"    O={err['open']:.4f} H={err['high']:.4f} L={err['low']:.4f} C={err['close']:.4f}")
            print(f"    Issue: {', '.join(err['issue'])}")
    else:
        print(f"✅ All OHLC data consistent")

    # Summary
    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")

    status = []

    # Timeframe verification
    if abs(avg_interval - expected_interval) < 0.5 if intervals else False:
        status.append(f"✅ Timeframe verified: {expected_timeframe}")
    else:
        status.append(f"⚠️  Timeframe mismatch: expected {expected_timeframe}, got ~{avg_interval:.2f}min avg")

    # Coverage
    if coverage_pct >= 99.0:
        status.append(f"✅ Excellent coverage: {coverage_pct:.2f}%")
    elif coverage_pct >= 95.0:
        status.append(f"⚠️  Good coverage: {coverage_pct:.2f}%")
    else:
        status.append(f"❌ Poor coverage: {coverage_pct:.2f}%")

    # Gaps
    if not gaps:
        status.append(f"✅ No gaps detected")
    elif len(gaps) <= 5:
        status.append(f"⚠️  Minor gaps: {len(gaps)} found")
    else:
        status.append(f"❌ Significant gaps: {len(gaps)} found")

    # OHLC
    if not ohlc_errors:
        status.append(f"✅ OHLC data valid")
    else:
        error_pct = (len(ohlc_errors) / total_bars) * 100
        status.append(f"❌ OHLC errors: {len(ohlc_errors)} bars ({error_pct:.2f}%)")

    for s in status:
        print(s)

    print(f"{'=' * 80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Verify downloaded Bitunix data quality",
        epilog="Example: python tools/verify_bitunix_data.py --symbol bitunix:BTCUSDT --timeframe 1min"
    )
    parser.add_argument(
        "--db",
        default="data/orderpilot.db",
        help="Path to database (default: data/orderpilot.db)"
    )
    parser.add_argument(
        "--symbol",
        default="bitunix:BTCUSDT",
        help="Symbol to verify (default: bitunix:BTCUSDT)"
    )
    parser.add_argument(
        "--timeframe",
        default="1min",
        choices=["1min", "5min", "15min", "1h", "4h", "1d"],
        help="Expected timeframe (default: 1min)"
    )

    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    # Initialize database connection
    from src.config.loader import config_manager
    from src.database import initialize_database

    profile = config_manager.load_profile()
    profile.database.engine = "sqlite"
    profile.database.path = str(db_path)
    initialize_database(profile.database)

    # Run verification
    verify_data(symbol=args.symbol, expected_timeframe=args.timeframe)


if __name__ == "__main__":
    main()
