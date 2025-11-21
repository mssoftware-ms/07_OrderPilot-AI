"""Quick setup script for Alpaca API keys.

Run this to store your Alpaca API keys in Windows Credential Manager.
"""

from src.config.loader import config_manager

# Replace with your actual keys from Alpaca dashboard
ALPACA_API_KEY = "YOUR_ALPACA_API_KEY"  # PK... (Public Key)
ALPACA_API_SECRET = "YOUR_ALPACA_API_SECRET"  # Secret Key

def setup_keys():
    """Store Alpaca API keys in credential manager."""

    if ALPACA_API_KEY == "YOUR_ALPACA_API_KEY":
        print("❌ Please edit this file and replace the placeholder keys!")
        print("   Get your keys from: https://app.alpaca.markets/paper/dashboard/overview")
        return

    try:
        # Store keys
        config_manager.store_credential("alpaca_api_key", ALPACA_API_KEY)
        config_manager.store_credential("alpaca_api_secret", ALPACA_API_SECRET)

        print("✅ Alpaca API keys saved successfully!")
        print("   Service: OrderPilot-AI")
        print("   Keys: alpaca_api_key, alpaca_api_secret")

        # Verify
        stored_key = config_manager.get_credential("alpaca_api_key")
        if stored_key:
            print(f"✅ Verification: Key starts with {stored_key[:10]}...")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_keys()
