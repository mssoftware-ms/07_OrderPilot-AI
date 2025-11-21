"""Direct test of Alpaca API without wrapper."""

import sys
import io
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("Direct Alpaca API Test")
print("=" * 60)

from src.config.loader import config_manager

api_key = config_manager.get_credential("alpaca_api_key")
api_secret = config_manager.get_credential("alpaca_api_secret")

print(f"\nAPI Key: {api_key[:10]}...")
print(f"API Secret: {api_secret[:10]}...")

print("\nTesting direct Alpaca API...")

try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    client = StockHistoricalDataClient(api_key, api_secret)
    print("[OK] Client created")

    # Test 1: Get latest trade
    print("\nTest 1: Latest quote for AAPL...")
    try:
        from alpaca.data.requests import StockLatestQuoteRequest
        latest_quote_request = StockLatestQuoteRequest(symbol_or_symbols="AAPL", feed='iex')
        latest_quote = client.get_stock_latest_quote(latest_quote_request)
        print(f"[OK] Latest quote: {latest_quote}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")

    # Test 2: Get intraday bars (last few hours)
    print("\nTest 2: Intraday bars (1-minute, last 2 days)...")
    try:
        request = StockBarsRequest(
            symbol_or_symbols="AAPL",
            timeframe=TimeFrame.Minute,
            start=datetime.now() - timedelta(days=2),
            end=datetime.now(),
            feed='iex'
        )

        bars = client.get_stock_bars(request)
        print(f"[OK] Got response: {type(bars)}")
        print(f"    Dir: {[attr for attr in dir(bars) if not attr.startswith('_')][:10]}")

        # Try to access data
        print(f"    Trying bars.data...")
        if hasattr(bars, 'data'):
            print(f"        bars.data = {bars.data}")

        print(f"    Trying bars.dict()...")
        if hasattr(bars, 'dict'):
            data_dict = bars.dict()
            print(f"        Dict keys: {list(data_dict.keys())}")
            if "AAPL" in data_dict:
                aapl_bars = data_dict["AAPL"]
                print(f"    [OK] AAPL bars: {len(aapl_bars)} bars")

        # Try direct access
        print(f"    Trying direct iteration...")
        try:
            for symbol, symbol_bars in bars:
                print(f"        Symbol: {symbol}, Bars: {len(list(symbol_bars))}")
        except:
            print(f"        Cannot iterate")

        # Try df conversion
        print(f"    Trying bars.df...")
        if hasattr(bars, 'df'):
            try:
                df = bars.df
                print(f"        DataFrame shape: {df.shape}")
                print(f"        DataFrame head:\n{df.head()}")
            except:
                print(f"        Cannot convert to df")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"[FAIL] Import error: {e}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
