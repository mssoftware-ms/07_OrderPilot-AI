#!/usr/bin/env python3
"""Check what timestamps exist in database."""

import sqlite3
from datetime import datetime

db_path = "data/orderpilot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get recent BTCUSDT data
query = """
SELECT timestamp, open, high, low, close
FROM market_bars
WHERE symbol = 'bitunix:BTCUSDT'
ORDER BY timestamp DESC
LIMIT 50
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"📊 Recent Database Timestamps (Last 50 bars)")
print(f"=" * 100)
print(f"{'Timestamp':<20} {'Open':>12} {'High':>12} {'Low':>12} {'Close':>12} {'Wick Check'}")
print(f"=" * 100)

for row in rows:
    ts, o, h, l, c = row

    # OHLC validation
    body_high = max(o, c)
    body_low = min(o, c)

    issues = []
    if h < body_high:
        issues.append(f"HIGH({h:.0f}) < BODY({body_high:.0f})")
    if l > body_low:
        issues.append(f"LOW({l:.0f}) > BODY({body_low:.0f})")

    issue_str = " | ".join(issues) if issues else "✅"

    print(f"{ts:<20} {o:>12.2f} {h:>12.2f} {l:>12.2f} {c:>12.2f} {issue_str}")

print(f"=" * 100)

# Count statistics
cursor.execute("""
SELECT
    COUNT(*) as total,
    MIN(timestamp) as oldest,
    MAX(timestamp) as newest
FROM market_bars
WHERE symbol = 'bitunix:BTCUSDT'
""")

stats = cursor.fetchone()
print(f"\n📈 Database Statistics:")
print(f"Total bars:  {stats[0]:,}")
print(f"Oldest bar:  {stats[1]}")
print(f"Newest bar:  {stats[2]}")

conn.close()
