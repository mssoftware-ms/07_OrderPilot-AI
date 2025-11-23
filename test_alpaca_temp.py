"""Quick test for Alpaca data fetch."""
import sys
from datetime import datetime, timedelta
from src.config.loader import config_manager
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

# Load credentials
api_key = config_manager.get_credential("alpaca_api_key")
api_secret = config_manager.get_credential("alpaca_api_secret")

print(f"API Key: {api_key[:8]}... (length: {len(api_key)})")
print(f"API Secret: {api_secret[:8]}... (length: {len(api_secret)})")

# Create client (explicitly set raw_data=False for easier debugging)
try:
    client = StockHistoricalDataClient(
        api_key=api_key,
        secret_key=api_secret,
        raw_data=False  # Return objects instead of raw JSON
    )
    print("Client created successfully")

    # Test if we can get account info or any basic endpoint
    print(f"API endpoint being used: {client._get_url('stocks')}")
except Exception as e:
    print(f"ERROR creating client: {e}")
    sys.exit(1)

# Request data for multiple dates to find working trading day
dates_to_try = [
    (datetime(2025, 11, 21, 9, 30), datetime(2025, 11, 21, 16, 0), "Thu 21 Nov"),
    (datetime(2025, 11, 20, 9, 30), datetime(2025, 11, 20, 16, 0), "Wed 20 Nov"),
    (datetime(2025, 11, 19, 9, 30), datetime(2025, 11, 19, 16, 0), "Tue 19 Nov"),
]

found_data = False
for start, end, date_label in dates_to_try:
    print(f"\n{'='*60}")
    print(f"Testing {date_label}: {start} to {end}")

    # Try both feeds
    for feed in ["sip", "iex"]:
        try:
            request = StockBarsRequest(
                symbol_or_symbols="QQQ",
                timeframe=TimeFrame(1, TimeFrameUnit.Minute),
                start=start,
                end=end,
                feed=feed
            )

            print(f"  Trying {feed.upper()} feed...")
            bars_dict = client.get_stock_bars(request)

            if "QQQ" in bars_dict:
                bars = list(bars_dict["QQQ"])
                if bars:
                    print(f"  SUCCESS! Got {len(bars)} bars")
                    print(f"    First bar: {bars[0].timestamp} | C:{bars[0].close}")
                    print(f"    Last bar:  {bars[-1].timestamp} | C:{bars[-1].close}")
                    found_data = True
                    break
                else:
                    print(f"    No bars in response")
            else:
                print(f"    No data in response")
        except Exception as e:
            print(f"    ERROR: {e}")

    if found_data:
        break

if not found_data:
    print("\n" + "="*60)
    print("ERROR: Could not fetch data for any date!")

print("\nDone!")
