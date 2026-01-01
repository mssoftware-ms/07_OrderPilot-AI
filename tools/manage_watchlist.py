#!/usr/bin/env python
"""
Watchlist Management Tool for OrderPilot-AI

Einfaches Tool zum Hinzufügen, Entfernen und Verwalten von Symbolen
in deiner Watchlist.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config.loader import config_manager


def print_header():
    """Print tool header."""
    print("\n" + "="*60)
    print("  OrderPilot-AI Watchlist Manager")
    print("="*60 + "\n")


def load_watchlist() -> list[str]:
    """Load current watchlist.

    Returns:
        List of symbols
    """
    try:
        return config_manager.load_watchlist()
    except Exception:
        pass

    return []


def save_watchlist(symbols: list[str]):
    """Save watchlist.

    Args:
        symbols: List of symbols
    """
    try:
        config_manager.settings.watchlist = symbols
        config_manager.save_watchlist()
        print(f"✅ Watchlist gespeichert ({len(symbols)} Symbole)")

    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")


def show_watchlist(symbols: list[str]):
    """Show current watchlist.

    Args:
        symbols: List of symbols
    """
    if not symbols:
        print("📋 Watchlist ist leer")
        return

    print(f"📋 Aktuelle Watchlist ({len(symbols)} Symbole):")
    for i, symbol in enumerate(symbols, 1):
        print(f"   {i}. {symbol}")
    print()


def add_symbol(symbols: list[str], symbol: str) -> list[str]:
    """Add symbol to watchlist.

    Args:
        symbols: Current symbols
        symbol: Symbol to add

    Returns:
        Updated symbols list
    """
    symbol = symbol.upper().strip()

    if not symbol:
        print("❌ Kein Symbol angegeben")
        return symbols

    if symbol in symbols:
        print(f"⚠️ {symbol} ist bereits in der Watchlist")
        return symbols

    symbols.append(symbol)
    print(f"✅ {symbol} hinzugefügt")
    return symbols


def remove_symbol(symbols: list[str], symbol: str) -> list[str]:
    """Remove symbol from watchlist.

    Args:
        symbols: Current symbols
        symbol: Symbol to remove

    Returns:
        Updated symbols list
    """
    symbol = symbol.upper().strip()

    if symbol in symbols:
        symbols.remove(symbol)
        print(f"✅ {symbol} entfernt")
    else:
        print(f"⚠️ {symbol} nicht in Watchlist gefunden")

    return symbols


def add_preset(symbols: list[str], preset: str) -> list[str]:
    """Add preset symbols.

    Args:
        symbols: Current symbols
        preset: Preset name

    Returns:
        Updated symbols list
    """
    presets = {
        'indices': {
            'name': 'Major Indices',
            'symbols': ['QQQ', 'DIA', 'SPY', 'IWM', 'VTI']
        },
        'tech': {
            'name': 'Tech Stocks',
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
        },
        'finance': {
            'name': 'Financial Stocks',
            'symbols': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C']
        },
        'energy': {
            'name': 'Energy Stocks',
            'symbols': ['XOM', 'CVX', 'COP', 'SLB', 'EOG']
        },
        'crypto_related': {
            'name': 'Crypto-Related Stocks',
            'symbols': ['COIN', 'MARA', 'RIOT', 'MSTR']
        },
        'german': {
            'name': 'German Stocks (DAX)',
            'symbols': ['SAP', 'SIE.DE', 'DTE.DE', 'VOW3.DE', 'BAS.DE']
        }
    }

    if preset not in presets:
        print(f"❌ Unbekanntes Preset: {preset}")
        print(f"Verfügbare Presets: {', '.join(presets.keys())}")
        return symbols

    preset_data = presets[preset]
    print(f"Füge {preset_data['name']} hinzu...")

    for symbol in preset_data['symbols']:
        if symbol not in symbols:
            symbols.append(symbol)
            print(f"  ✅ {symbol}")
        else:
            print(f"  ⏭️ {symbol} (bereits vorhanden)")

    return symbols


def main():
    """Main entry point."""
    print_header()

    # Load current watchlist
    symbols = load_watchlist()
    show_watchlist(symbols)

    print("Befehle:")
    print("  add <SYMBOL>       - Symbol hinzufügen (z.B. 'add AAPL')")
    print("  remove <SYMBOL>    - Symbol entfernen")
    print("  preset <NAME>      - Preset laden (indices, tech, finance, energy, crypto_related, german)")
    print("  list               - Watchlist anzeigen")
    print("  clear              - Alle Symbole entfernen")
    print("  save               - Watchlist speichern")
    print("  quit               - Beenden")
    print()

    modified = False

    while True:
        try:
            command = input(">>> ").strip().lower()

            if not command:
                continue

            parts = command.split(maxsplit=1)
            cmd = parts[0]

            if cmd == 'quit' or cmd == 'exit' or cmd == 'q':
                if modified:
                    save_watchlist(symbols)
                print("\n👋 Auf Wiedersehen!\n")
                break

            elif cmd == 'add':
                if len(parts) < 2:
                    print("❌ Verwendung: add <SYMBOL>")
                    continue
                symbols = add_symbol(symbols, parts[1])
                modified = True

            elif cmd == 'remove' or cmd == 'rm' or cmd == 'del':
                if len(parts) < 2:
                    print("❌ Verwendung: remove <SYMBOL>")
                    continue
                symbols = remove_symbol(symbols, parts[1])
                modified = True

            elif cmd == 'preset':
                if len(parts) < 2:
                    print("❌ Verwendung: preset <NAME>")
                    print("Verfügbare: indices, tech, finance, energy, crypto_related, german")
                    continue
                symbols = add_preset(symbols, parts[1])
                modified = True

            elif cmd == 'list' or cmd == 'ls' or cmd == 'show':
                show_watchlist(symbols)

            elif cmd == 'clear':
                confirm = input("Wirklich alle Symbole entfernen? (y/N) ").lower()
                if confirm == 'y' or confirm == 'yes':
                    symbols = []
                    print("✅ Watchlist geleert")
                    modified = True

            elif cmd == 'save':
                save_watchlist(symbols)
                modified = False

            elif cmd == 'help' or cmd == 'h':
                print("\nBefehle:")
                print("  add <SYMBOL>       - Symbol hinzufügen")
                print("  remove <SYMBOL>    - Symbol entfernen")
                print("  preset <NAME>      - Preset laden")
                print("  list               - Watchlist anzeigen")
                print("  clear              - Alle entfernen")
                print("  save               - Speichern")
                print("  quit               - Beenden")

            else:
                print(f"❌ Unbekannter Befehl: {cmd}")
                print("Hilfe: 'help' eingeben")

        except KeyboardInterrupt:
            print("\n")
            if modified:
                save = input("Änderungen speichern? (Y/n) ").lower()
                if save != 'n' and save != 'no':
                    save_watchlist(symbols)
            print("\n👋 Auf Wiedersehen!\n")
            break
        except Exception as e:
            print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    main()
