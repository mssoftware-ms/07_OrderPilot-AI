"""Simple test to check if Alpaca provider is available and can fetch data."""

import asyncio
import sys
import io
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("Alpaca Provider Test")
print("=" * 60)

async def test_alpaca():
    from src.config.loader import config_manager
    from src.core.market_data.history_provider import AlpacaProvider, Timeframe

    # Get credentials
    api_key = config_manager.get_credential("alpaca_api_key")
    api_secret = config_manager.get_credential("alpaca_api_secret")

    print(f"\n1. Credentials check:")
    print(f"   API Key: {'[OK] ' + api_key[:10] + '...' if api_key else '[FAIL] Not found'}")
    print(f"   API Secret: {'[OK] ' + api_secret[:10] + '...' if api_secret else '[FAIL] Not found'}")

    if not api_key or not api_secret:
        print("\n[FAIL] Missing credentials!")
        return

    # Create provider
    print(f"\n2. Creating Alpaca provider...")
    provider = AlpacaProvider(api_key, api_secret)

    # Check if available
    print(f"\n3. Checking if provider is available...")
    is_available = await provider.is_available()
    print(f"   Available: {'[OK] Yes' if is_available else '[FAIL] No'}")

    if not is_available:
        print("\n[FAIL] Alpaca provider not available!")
        print("   Possible reasons:")
        print("   - API keys are invalid")
        print("   - alpaca-py library not installed")
        print("   - Network connection issues")
        return

    # Try to fetch some data
    print(f"\n4. Fetching test data (AAPL, last 30 days)...")
    try:
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        bars = await provider.fetch_bars(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            timeframe=Timeframe.DAY_1
        )

        if bars:
            print(f"   [OK] Fetched {len(bars)} bars")
            print(f"   First bar: {bars[0].timestamp.strftime('%Y-%m-%d')} - Close: ${bars[0].close}")
            print(f"   Last bar:  {bars[-1].timestamp.strftime('%Y-%m-%d')} - Close: ${bars[-1].close}")
        else:
            print(f"   [WARN] No bars returned (market might be closed)")

    except Exception as e:
        print(f"   [FAIL] Error fetching data: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_alpaca())
