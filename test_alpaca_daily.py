"""Test Alpaca Daily bars with IEX feed."""

import sys
import io
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.config.loader import config_manager
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

api_key = config_manager.get_credential("alpaca_api_key")
api_secret = config_manager.get_credential("alpaca_api_secret")

client = StockHistoricalDataClient(api_key, api_secret)

print("Testing Daily bars with IEX feed...")
print("=" * 60)

# Test 1: Last 90 days with IEX
print("\nTest 1: Daily bars, last 90 days, IEX feed")
request = StockBarsRequest(
    symbol_or_symbols="AAPL",
    timeframe=TimeFrame.Day,
    start=datetime.now() - timedelta(days=90),
    end=datetime.now(),
    feed='iex'
)

try:
    bars = client.get_stock_bars(request)
    if hasattr(bars, 'data') and "AAPL" in bars.data:
        aapl_bars = bars.data["AAPL"]
        print(f"   [OK] Got {len(aapl_bars)} bars")
        if len(aapl_bars) > 0:
            print(f"   First: {aapl_bars[0].timestamp.strftime('%Y-%m-%d')}")
            print(f"   Last:  {aapl_bars[-1].timestamp.strftime('%Y-%m-%d')}")
    else:
        print(f"   [WARN] No bars returned")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 2: Try without feed parameter (uses account default)
print("\nTest 2: Daily bars, last 90 days, default feed (no parameter)")
request = StockBarsRequest(
    symbol_or_symbols="AAPL",
    timeframe=TimeFrame.Day,
    start=datetime.now() - timedelta(days=90),
    end=datetime.now()
    # No feed parameter
)

try:
    bars = client.get_stock_bars(request)
    if hasattr(bars, 'data') and "AAPL" in bars.data:
        aapl_bars = bars.data["AAPL"]
        print(f"   [OK] Got {len(aapl_bars)} bars")
        if len(aapl_bars) > 0:
            print(f"   First: {aapl_bars[0].timestamp.strftime('%Y-%m-%d')}")
            print(f"   Last:  {aapl_bars[-1].timestamp.strftime('%Y-%m-%d')}")
    else:
        print(f"   [WARN] No bars returned")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 3: Intraday for comparison
print("\nTest 3: 1-minute bars, last 2 days, IEX feed (for comparison)")
request = StockBarsRequest(
    symbol_or_symbols="AAPL",
    timeframe=TimeFrame.Minute,
    start=datetime.now() - timedelta(days=2),
    end=datetime.now(),
    feed='iex'
)

try:
    bars = client.get_stock_bars(request)
    if hasattr(bars, 'data') and "AAPL" in bars.data:
        aapl_bars = bars.data["AAPL"]
        print(f"   [OK] Got {len(aapl_bars)} bars")
        if len(aapl_bars) > 0:
            print(f"   First: {aapl_bars[0].timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Last:  {aapl_bars[-1].timestamp.strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"   [WARN] No bars returned")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

print("\n" + "=" * 60)
print("Conclusion:")
print("If IEX daily bars return only 1 bar, IEX feed may not support")
print("historical daily data. Use intraday timeframes or switch to SIP.")
