#!/usr/bin/env python3
"""Fix Alpaca credentials in Windows Credential Manager.

This script helps migrate or fix credentials that might be stored
under different names in Windows Credential Manager.
"""

import sys
import logging
from pathlib import Path
from getpass import getpass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.loader import config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_alternative_names():
    """Check if credentials exist under alternative names."""
    import keyring

    print("\n🔍 Checking for credentials under alternative names...")
    print("=" * 70)

    alternative_names = [
        ("ALPACA_API_KEY", "alpaca_api_key"),
        ("ALPACA_API_SECRET", "alpaca_api_secret"),
        ("APCA_API_KEY_ID", "alpaca_api_key"),
        ("APCA_API_SECRET_KEY", "alpaca_api_secret"),
    ]

    found = []
    for old_name, new_name in alternative_names:
        value = keyring.get_password("OrderPilot-AI", old_name)
        if value:
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
            print(f"✓ Found '{old_name}': {masked}")
            found.append((old_name, new_name, value))

    return found


def migrate_credentials(found_creds):
    """Migrate credentials to correct names."""
    if not found_creds:
        print("\n⚠ No credentials found to migrate")
        return False

    print("\n📦 Migrating credentials to correct names...")
    print("=" * 70)

    for old_name, new_name, value in found_creds:
        try:
            # Set with new name
            config_manager.set_credential(new_name, value)
            print(f"✅ Migrated: {old_name} → {new_name}")
        except Exception as e:
            print(f"❌ Failed to migrate {old_name}: {e}")
            return False

    print("\n✅ Migration complete!")
    return True


def manual_entry():
    """Manually enter credentials."""
    print("\n📝 Manual Credential Entry")
    print("=" * 70)
    print("Please enter your Alpaca API credentials.")
    print("Get them from: https://app.alpaca.markets/paper/dashboard/overview")
    print()

    # Get API Key
    api_key = input("Alpaca API Key: ").strip()
    if not api_key:
        print("❌ API Key cannot be empty")
        return False

    # Get API Secret
    api_secret = getpass("Alpaca API Secret (hidden): ").strip()
    if not api_secret:
        print("❌ API Secret cannot be empty")
        return False

    # Confirm
    print(f"\nAPI Key: {api_key[:4]}...{api_key[-4:]}")
    print(f"API Secret: {api_secret[:4]}...{api_secret[-4:]}")
    confirm = input("\nSave these credentials? (yes/no): ").strip().lower()

    if confirm not in ["yes", "y"]:
        print("❌ Cancelled")
        return False

    # Save credentials
    try:
        config_manager.set_credential("alpaca_api_key", api_key)
        config_manager.set_credential("alpaca_api_secret", api_secret)
        print("\n✅ Credentials saved to Windows Credential Manager!")
        return True
    except Exception as e:
        print(f"\n❌ Failed to save credentials: {e}")
        return False


def main():
    """Main function."""
    print("\n🔧 OrderPilot-AI Credential Fix Tool\n")

    # Check if credentials already exist correctly
    api_key = config_manager.get_credential("alpaca_api_key")
    api_secret = config_manager.get_credential("alpaca_api_secret")

    if api_key and api_secret:
        print("✅ Credentials already correctly configured!")
        masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
        masked_secret = api_secret[:4] + "*" * (len(api_secret) - 8) + api_secret[-4:]
        print(f"   API Key: {masked_key}")
        print(f"   API Secret: {masked_secret}")
        print("\nNo action needed. You can start the application.")
        return 0

    # Check for alternative names
    found_creds = check_alternative_names()

    if found_creds:
        print("\n💡 Found credentials under different names!")
        choice = input("\nMigrate to correct names? (yes/no): ").strip().lower()
        if choice in ["yes", "y"]:
            if migrate_credentials(found_creds):
                print("\n✅ Done! You can now start the application.")
                return 0
            else:
                print("\n❌ Migration failed")
                return 1

    # Manual entry
    print("\n❌ Credentials not found in Windows Credential Manager")
    choice = input("\nEnter credentials manually? (yes/no): ").strip().lower()

    if choice in ["yes", "y"]:
        if manual_entry():
            print("\n✅ Done! You can now start the application.")
            return 0
        else:
            return 1
    else:
        print("\n⚠ No credentials configured. Application will not work.")
        print("\nOptions:")
        print("1. Run this script again: python fix_credentials.py")
        print("2. Manually add to Windows Credential Manager:")
        print("   - Service: 'OrderPilot-AI'")
        print("   - Username: 'alpaca_api_key'")
        print("   - Password: <your API key>")
        print("   (Repeat for 'alpaca_api_secret')")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
