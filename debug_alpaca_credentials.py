"""Debug script to test Alpaca credential storage and loading."""

import sys
import logging

# Set UTF-8 encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("=" * 60)
print("Alpaca Credentials Debug Tool")
print("=" * 60)

# Test 1: Check if keyring is working
print("\n1. Testing keyring library...")
try:
    import keyring
    print(f"[OK] keyring imported")

    # Get current backend
    backend = keyring.get_keyring()
    print(f"   Backend: {backend}")

    # Test write/read
    test_service = "OrderPilot-AI-Test"
    test_key = "test_key"
    test_value = "test_123"

    keyring.set_password(test_service, test_key, test_value)
    retrieved = keyring.get_password(test_service, test_key)

    if retrieved == test_value:
        print(f"[OK] Keyring read/write works!")
        keyring.delete_password(test_service, test_key)
    else:
        print(f"[FAIL] Keyring test failed! Stored: {test_value}, Got: {retrieved}")

except Exception as e:
    print(f"[FAIL] Keyring error: {e}")
    sys.exit(1)

# Test 2: Check config_manager
print("\n2. Testing config_manager...")
try:
    from src.config.loader import config_manager
    print("[OK] config_manager imported")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Test 3: Try to get existing Alpaca credentials
print("\n3. Checking existing Alpaca credentials...")
try:
    api_key = config_manager.get_credential("alpaca_api_key")
    api_secret = config_manager.get_credential("alpaca_api_secret")

    if api_key:
        print(f"[OK] Found alpaca_api_key: {api_key[:10]}...")
    else:
        print("[WARN] No alpaca_api_key found")

    if api_secret:
        print(f"[OK] Found alpaca_api_secret: {api_secret[:10]}...")
    else:
        print("[WARN] No alpaca_api_secret found")

except Exception as e:
    print(f"[FAIL] Error getting credentials: {e}")

# Test 4: Check all credentials in keyring
print("\n4. Searching Windows Credential Manager for 'OrderPilot-AI'...")
try:
    # Try to get all common credentials
    common_keys = [
        "alpaca_api_key",
        "alpaca_api_secret",
        "openai_api_key",
        "alpha_vantage_key",
        "finnhub_key",
    ]

    found_any = False
    for key in common_keys:
        value = keyring.get_password("OrderPilot-AI", key)
        if value:
            print(f"   [OK] {key}: {value[:10]}...")
            found_any = True

    if not found_any:
        print("   [WARN] No credentials found in 'OrderPilot-AI' service")

except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 5: Skipped (no user input needed)
print("\n5. Manual credential storage test...")
print("   [SKIP] Skipping interactive test")

# Test 6: Check if Alpaca provider is being used
print("\n6. Checking data provider configuration...")
try:
    from src.core.market_data.history_provider import HistoryManager
    from datetime import datetime, timedelta

    # Check if HistoryManager can see Alpaca credentials
    config = config_manager.load_profile()
    print(f"   Current profile: {config.profile_name}")
    print(f"   Alpaca enabled: {getattr(config.market_data, 'alpaca_enabled', False)}")

    # Try to create history manager
    history_mgr = HistoryManager(config_manager)

    # Check providers
    print("\n   Checking available providers:")
    import asyncio

    async def check_providers():
        for name in ["alpaca", "yahoo", "database"]:
            provider = history_mgr._get_provider(name)
            if provider:
                available = await provider.is_available()
                print(f"      {name}: {'[OK] Available' if available else '[FAIL] Not available'}")

    asyncio.run(check_providers())

except Exception as e:
    print(f"   [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug completed!")
print("=" * 60)

print("\nRecommendations:")
print("1. If credentials are not found, re-enter them via the UI")
print("2. Check Windows Credential Manager manually:")
print("   - Press Win+R, type: control /name Microsoft.CredentialManager")
print("   - Look for 'OrderPilot-AI' entries")
print("3. If keyring backend is 'null' or 'fail', install: pip install keyring")
