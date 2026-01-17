#!/usr/bin/env python3
"""Check for gaps in loaded chart data.

Analyzes the data that was just loaded to see if there are missing minutes.
"""

import sys
from datetime import datetime, timedelta

# Parse log data for timestamps
log_data = """
First bar: 2026-01-16 14:58:00
Last bar: 2026-01-17 17:44:00
Total bars: 1607
"""

first_str = "2026-01-16 14:58:00"
last_str = "2026-01-17 17:44:00"
total_bars = 1607

first_dt = datetime.strptime(first_str, "%Y-%m-%d %H:%M:%S")
last_dt = datetime.strptime(last_str, "%Y-%m-%d %H:%M:%S")

# Calculate expected bars (1 min intervals)
time_diff = last_dt - first_dt
expected_minutes = int(time_diff.total_seconds() / 60) + 1  # +1 to include last bar

print(f"📊 Chart Data Analysis")
print(f"=" * 60)
print(f"First bar:     {first_str}")
print(f"Last bar:      {last_str}")
print(f"Time span:     {time_diff} ({time_diff.total_seconds() / 3600:.1f} hours)")
print(f"")
print(f"Expected bars: {expected_minutes:,} (1-minute intervals)")
print(f"Actual bars:   {total_bars:,}")
print(f"Missing bars:  {expected_minutes - total_bars:,}")
print(f"Coverage:      {(total_bars / expected_minutes * 100):.2f}%")
print(f"")

if expected_minutes - total_bars > 0:
    print(f"⚠️  DATA HAS GAPS!")
    print(f"   Missing {expected_minutes - total_bars} bars out of {expected_minutes}")
    print(f"   This explains the whitespace in chart!")
    print(f"")
    print(f"Possible causes:")
    print(f"  1. Bitunix API didn't return all minutes (exchange downtime?)")
    print(f"  2. API rate limiting skipped some requests")
    print(f"  3. Data filtering removed some bars (bad ticks?)")
else:
    print(f"✅ DATA IS COMPLETE (no gaps)")
    print(f"   Chart gaps must be a rendering issue, not data issue")
