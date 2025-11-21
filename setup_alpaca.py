"""Setup Alpaca API credentials for live streaming.

Quick setup script to configure Alpaca WebSocket streaming.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config.loader import config_manager


def setup_alpaca_credentials():
    """Configure Alpaca API credentials."""
    print("=" * 60)
    print("  Alpaca API Setup für Live-Streaming")
    print("=" * 60)
    print()
    print("📋 Sie brauchen:")
    print("   1. Kostenlosen Account auf https://alpaca.markets/")
    print("   2. Paper Trading API Keys (Dashboard → API Keys)")
    print()
    print("=" * 60)
    print()

    # Get existing credentials if any
    try:
        existing_key = config_manager.get_credential("alpaca_api_key")
        existing_secret = config_manager.get_credential("alpaca_api_secret")

        if existing_key and existing_secret:
            print("✅ Alpaca Keys sind bereits konfiguriert!")
            print(f"   API Key: {existing_key[:8]}...{existing_key[-4:]}")
            print()

            response = input("Möchten Sie die Keys neu eingeben? (y/N): ").strip().lower()
            if response != 'y':
                print("✓ Setup abgeschlossen - verwende bestehende Keys")
                return True
            print()
    except Exception:
        pass

    # Get API key
    print("Schritt 1: API Key eingeben")
    api_key = input("Alpaca API Key: ").strip()

    if not api_key:
        print("❌ API Key erforderlich!")
        return False

    print()

    # Get API secret
    print("Schritt 2: API Secret eingeben")
    api_secret = input("Alpaca API Secret: ").strip()

    if not api_secret:
        print("❌ API Secret erforderlich!")
        return False

    print()
    print("💾 Speichere Credentials...")

    try:
        # Store credentials
        config_manager.store_credential("alpaca_api_key", api_key)
        config_manager.store_credential("alpaca_api_secret", api_secret)

        print("✅ Credentials erfolgreich gespeichert!")
        print()
        print("=" * 60)
        print("  Nächste Schritte:")
        print("=" * 60)
        print()
        print("1. Starten Sie OrderPilot-AI:")
        print("   .venv/Scripts/python.exe start_orderpilot.py")
        print()
        print("2. Symbol auswählen (z.B. QQQ, AAPL)")
        print()
        print("3. 'Live' Button klicken")
        print()
        print("4. Im Log sollte erscheinen:")
        print("   '✓ Started Alpaca WebSocket stream'")
        print()
        print("🎉 Live-Candles wie bei Stock3 Terminal!")
        print()

        return True

    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")
        return False


def test_alpaca_connection():
    """Test Alpaca connection with stored credentials."""
    print("=" * 60)
    print("  Teste Alpaca Verbindung...")
    print("=" * 60)
    print()

    try:
        api_key = config_manager.get_credential("alpaca_api_key")
        api_secret = config_manager.get_credential("alpaca_api_secret")

        if not api_key or not api_secret:
            print("❌ Keine Credentials gefunden! Bitte erst setup_alpaca_credentials() ausführen.")
            return False

        print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
        print()

        # Try to import and test
        from src.core.broker.alpaca_adapter import AlpacaAdapter
        import asyncio

        print("📡 Verbinde zu Alpaca Paper Trading...")

        adapter = AlpacaAdapter(
            api_key=api_key,
            api_secret=api_secret,
            paper=True
        )

        async def test():
            await adapter.connect()
            balance = await adapter.get_balance()
            print(f"✅ Verbindung erfolgreich!")
            print(f"   Buying Power: ${balance.buying_power:,.2f}")
            await adapter.disconnect()
            return True

        result = asyncio.run(test())
        print()
        print("🎉 Alpaca ist bereit für Live-Streaming!")
        return result

    except Exception as e:
        print(f"❌ Verbindungsfehler: {e}")
        print()
        print("Mögliche Ursachen:")
        print("  - Falsche API Keys")
        print("  - Paper Trading Keys statt Live Keys verwendet")
        print("  - Netzwerkprobleme")
        return False


if __name__ == "__main__":
    print()

    # Setup credentials
    if setup_alpaca_credentials():
        print()

        # Ask if user wants to test
        response = input("Möchten Sie die Verbindung jetzt testen? (Y/n): ").strip().lower()

        if response != 'n':
            print()
            test_alpaca_connection()

    print()
    input("Drücken Sie Enter zum Beenden...")
