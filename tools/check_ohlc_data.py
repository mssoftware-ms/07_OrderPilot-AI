#!/usr/bin/env python3
"""Check OHLC data for inconsistencies.

Analyzes the database to find bars where high/low don't make sense.
"""

import sys
import sqlite3
from datetime import datetime

db_path = "data/orderpilot.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get recent BTCUSDT data
query = """
SELECT timestamp, open, high, low, close, volume
FROM market_bars
WHERE symbol = 'BTCUSDT'
AND timestamp >= '2026-01-17 00:00:00'
ORDER BY timestamp DESC
LIMIT 20
"""

cursor.execute(query)
rows = cursor.fetchall()

print("📊 Recent BTCUSDT bars (last 20):")
print("=" * 100)
print(f"{'Timestamp':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Range':>8} {'Issue'}")
print("=" * 100)

issues_found = 0
for row in rows:
    ts, o, h, l, c, vol = row

    # Check for OHLC consistency
    max_oc = max(o, c)
    min_oc = min(o, c)

    issues = []
    if h < max_oc:
        issues.append(f"high({h}) < max(o,c)={max_oc}")
        issues_found += 1
    if l > min_oc:
        issues.append(f"low({l}) > min(o,c)={min_oc}")
        issues_found += 1
    if h == o == c == l:
        issues.append("all equal (no movement)")
        issues_found += 1

    # Calculate range
    candle_range = abs(c - o)
    wick_range = h - l

    issue_str = "; ".join(issues) if issues else "✅"

    print(f"{ts:<20} {o:>10.1f} {h:>10.1f} {l:>10.1f} {c:>10.1f} {wick_range:>8.1f} {issue_str}")

print("=" * 100)
print(f"Total issues found: {issues_found}")

# Check specific bars that might look like "no wick"
query2 = """
SELECT COUNT(*) as total,
       SUM(CASE WHEN high = open AND high = close THEN 1 ELSE 0 END) as no_upper_wick,
       SUM(CASE WHEN low = open AND low = close THEN 1 ELSE 0 END) as no_lower_wick,
       SUM(CASE WHEN high - low < 1.0 THEN 1 ELSE 0 END) as very_small_range
FROM market_bars
WHERE symbol = 'BTCUSDT'
AND timestamp >= '2026-01-17 00:00:00'
"""

cursor.execute(query2)
stats = cursor.fetchone()

print()
print("📈 Statistics for today's BTCUSDT bars:")
print("=" * 100)
print(f"Total bars:           {stats[0]}")
print(f"No upper wick:        {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
print(f"No lower wick:        {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
print(f"Very small range (<1): {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")

conn.close()
