#!/usr/bin/env python3
"""Check OHLC data in database for specific timeframe."""

import sqlite3
from datetime import datetime

db_path = "data/orderpilot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get data for visible chart timeframe (17:40-18:30 UTC today)
query = """
SELECT timestamp, open, high, low, close, volume
FROM market_bars
WHERE symbol = 'bitunix:BTCUSDT'
AND timestamp >= '2026-01-17 17:40:00'
AND timestamp <= '2026-01-17 18:30:00'
ORDER BY timestamp
LIMIT 30
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"📊 Database OHLC Check (Chart Timeframe)")
print(f"=" * 120)
print(f"{'Timestamp':<20} {'Open':>12} {'High':>12} {'Low':>12} {'Close':>12} {'Body%':>8} {'Upper Wick%':>12} {'Lower Wick%':>12}")
print(f"=" * 120)

for row in rows:
    ts, o, h, l, c, vol = row

    # Calculate candle metrics
    body_high = max(o, c)
    body_low = min(o, c)
    body_size = abs(c - o)

    # Calculate wick percentages relative to price
    mid_price = (body_high + body_low) / 2 if body_high > 0 else c

    upper_wick = h - body_high if h > body_high else 0
    lower_wick = body_low - l if l < body_low else 0

    upper_wick_pct = (upper_wick / mid_price * 100) if mid_price > 0 else 0
    lower_wick_pct = (lower_wick / mid_price * 100) if mid_price > 0 else 0
    body_pct = (body_size / mid_price * 100) if mid_price > 0 else 0

    # Check for issues
    issues = []
    if h < body_high:
        issues.append("❌ HIGH < BODY_HIGH")
    if l > body_low:
        issues.append("❌ LOW > BODY_LOW")
    if h == o == c == l:
        issues.append("⚠️ FLAT (no movement)")

    issue_str = " | ".join(issues) if issues else ""

    print(f"{ts:<20} {o:>12.2f} {h:>12.2f} {l:>12.2f} {c:>12.2f} {body_pct:>7.2f}% {upper_wick_pct:>11.2f}% {lower_wick_pct:>11.2f}%  {issue_str}")

print(f"=" * 120)

# Summary statistics
cursor.execute("""
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN high < MAX(open, close) THEN 1 ELSE 0 END) as high_too_low,
    SUM(CASE WHEN low > MIN(open, close) THEN 1 ELSE 0 END) as low_too_high,
    SUM(CASE WHEN high = open AND high = close THEN 1 ELSE 0 END) as no_upper_wick,
    SUM(CASE WHEN low = open AND low = close THEN 1 ELSE 0 END) as no_lower_wick,
    AVG((high - MAX(open, close)) / ((MAX(open, close) + MIN(open, close)) / 2) * 100) as avg_upper_wick_pct,
    AVG((MIN(open, close) - low) / ((MAX(open, close) + MIN(open, close)) / 2) * 100) as avg_lower_wick_pct
FROM market_bars
WHERE symbol = 'bitunix:BTCUSDT'
AND timestamp >= '2026-01-17 17:40:00'
AND timestamp <= '2026-01-17 18:30:00'
""")

stats = cursor.fetchone()

print(f"\n📈 OHLC Statistics:")
print(f"=" * 120)
print(f"Total bars:                {stats[0]}")
print(f"HIGH < BODY_HIGH (errors): {stats[1]}")
print(f"LOW > BODY_LOW (errors):   {stats[2]}")
print(f"No upper wick:             {stats[3]}")
print(f"No lower wick:             {stats[4]}")
print(f"Avg upper wick:            {stats[5]:.2f}%")
print(f"Avg lower wick:            {stats[6]:.2f}%")

conn.close()
