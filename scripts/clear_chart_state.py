#!/usr/bin/env python3
"""Utility script to manage and clear saved chart states.

This script helps clear saved chart states that have accumulated too many
annotations or drawings. It uses the same QSettings as the OrderPilot-AI
application.

Usage:
    # List all saved chart states
    python scripts/clear_chart_state.py --list

    # Clear all drawings/annotations for a specific symbol
    python scripts/clear_chart_state.py --symbol BTCUSD --clear-drawings

    # Clear entire chart state for a symbol
    python scripts/clear_chart_state.py --symbol BTCUSD --clear-all

    # Clear all chart states
    python scripts/clear_chart_state.py --clear-all-states
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication


class ChartStateManager:
    """Manager for chart state persistence in QSettings."""

    def __init__(self):
        """Initialize QSettings with OrderPilot configuration."""
        # QApplication required for QSettings to work properly
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        self.settings = QSettings("OrderPilot", "TradingApp")

    def list_all_charts(self) -> Dict[str, Dict]:
        """List all saved chart states.

        Returns:
            Dictionary mapping symbol to chart state info
        """
        charts = {}

        # Navigate to charts group
        self.settings.beginGroup("charts")
        chart_symbols = self.settings.childGroups()

        for symbol in chart_symbols:
            self.settings.beginGroup(symbol)

            # Count indicators and drawings
            indicators_json = self.settings.value("indicators", "[]")
            try:
                indicators = json.loads(indicators_json) if isinstance(indicators_json, str) else indicators_json
                indicator_count = len(indicators) if isinstance(indicators, list) else 0
            except:
                indicator_count = 0

            drawings_json = self.settings.value("drawings", "[]")
            try:
                drawings = json.loads(drawings_json) if isinstance(drawings_json, str) else drawings_json
                drawing_count = len(drawings) if isinstance(drawings, list) else 0
            except:
                drawing_count = 0

            charts[symbol] = {
                'symbol': symbol,
                'indicators': indicator_count,
                'drawings': drawing_count,
                'timeframe': self.settings.value("timeframe", "Unknown"),
                'chart_type': self.settings.value("chart_type", "Unknown")
            }

            self.settings.endGroup()

        self.settings.endGroup()

        return charts

    def clear_drawings(self, symbol: str) -> bool:
        """Clear only drawings/annotations for a symbol, keep everything else.

        Args:
            symbol: Symbol to clear drawings for

        Returns:
            True if successful, False otherwise
        """
        try:
            # Sanitize symbol (same as ChartStateManager does)
            sanitized = symbol.replace("/", "_").replace(":", "_").replace("*", "_")

            settings_key = f"charts/{sanitized}/drawings"
            self.settings.setValue(settings_key, "[]")

            print(f"✅ Cleared {settings_key}")
            return True

        except Exception as e:
            print(f"❌ Error clearing drawings for {symbol}: {e}")
            return False

    def clear_chart_state(self, symbol: str) -> bool:
        """Clear entire chart state for a symbol.

        Args:
            symbol: Symbol to clear state for

        Returns:
            True if successful, False otherwise
        """
        try:
            # Sanitize symbol
            sanitized = symbol.replace("/", "_").replace(":", "_").replace("*", "_")

            settings_key = f"charts/{sanitized}"
            self.settings.remove(settings_key)

            print(f"✅ Cleared all state for {symbol}")
            return True

        except Exception as e:
            print(f"❌ Error clearing chart state for {symbol}: {e}")
            return False

    def clear_all_states(self) -> bool:
        """Clear all chart states.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.settings.remove("charts")
            print("✅ Cleared all chart states")
            return True

        except Exception as e:
            print(f"❌ Error clearing all states: {e}")
            return False

    def get_drawings_details(self, symbol: str) -> Optional[List[Dict]]:
        """Get detailed information about drawings for a symbol.

        Args:
            symbol: Symbol to get drawings for

        Returns:
            List of drawing objects or None if not found
        """
        try:
            sanitized = symbol.replace("/", "_").replace(":", "_").replace("*", "_")
            settings_key = f"charts/{sanitized}/drawings"

            drawings_json = self.settings.value(settings_key, "[]")
            drawings = json.loads(drawings_json) if isinstance(drawings_json, str) else drawings_json

            return drawings if isinstance(drawings, list) else []

        except Exception as e:
            print(f"❌ Error getting drawings for {symbol}: {e}")
            return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage OrderPilot-AI chart states",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all saved charts
  python scripts/clear_chart_state.py --list

  # Show drawings for a specific symbol
  python scripts/clear_chart_state.py --symbol BTCUSD --show-drawings

  # Clear only drawings/annotations (keep indicators, timeframe, etc.)
  python scripts/clear_chart_state.py --symbol BTCUSD --clear-drawings

  # Clear entire chart state for a symbol
  python scripts/clear_chart_state.py --symbol BTCUSD --clear-all

  # Clear all chart states (DANGEROUS!)
  python scripts/clear_chart_state.py --clear-all-states --confirm
        """
    )

    parser.add_argument('--list', action='store_true',
                       help='List all saved chart states')
    parser.add_argument('--symbol', type=str,
                       help='Symbol to operate on (e.g., BTCUSD, BTC/USD)')
    parser.add_argument('--show-drawings', action='store_true',
                       help='Show detailed drawings for a symbol')
    parser.add_argument('--clear-drawings', action='store_true',
                       help='Clear only drawings/annotations for a symbol')
    parser.add_argument('--clear-all', action='store_true',
                       help='Clear entire chart state for a symbol')
    parser.add_argument('--clear-all-states', action='store_true',
                       help='Clear ALL chart states (requires --confirm)')
    parser.add_argument('--confirm', action='store_true',
                       help='Confirm destructive operations')

    args = parser.parse_args()

    manager = ChartStateManager()

    # List all charts
    if args.list:
        charts = manager.list_all_charts()

        if not charts:
            print("ℹ️  No saved chart states found")
            return 0

        print("\n📊 Saved Chart States:")
        print("-" * 80)
        for symbol, info in sorted(charts.items()):
            print(f"\n🔸 Symbol: {info['symbol']}")
            print(f"   Timeframe: {info['timeframe']}")
            print(f"   Chart Type: {info['chart_type']}")
            print(f"   Indicators: {info['indicators']}")
            print(f"   Drawings/Annotations: {info['drawings']} {'⚠️  HIGH!' if info['drawings'] > 50 else ''}")
        print("\n" + "-" * 80)
        return 0

    # Show drawings details
    if args.show_drawings:
        if not args.symbol:
            print("❌ --symbol required for --show-drawings")
            return 1

        drawings = manager.get_drawings_details(args.symbol)

        if drawings is None:
            print(f"❌ Could not retrieve drawings for {args.symbol}")
            return 1

        if not drawings:
            print(f"ℹ️  No drawings found for {args.symbol}")
            return 0

        print(f"\n📝 Drawings for {args.symbol}: {len(drawings)} total")
        print("-" * 80)

        # Group by type
        by_type = {}
        for drawing in drawings:
            dtype = drawing.get('type', 'unknown')
            by_type.setdefault(dtype, []).append(drawing)

        for dtype, items in sorted(by_type.items()):
            print(f"\n🔸 {dtype}: {len(items)} items")
            if len(items) <= 5:
                for item in items:
                    print(f"   - {json.dumps(item, indent=6)}")

        print("\n" + "-" * 80)
        return 0

    # Clear drawings only
    if args.clear_drawings:
        if not args.symbol:
            print("❌ --symbol required for --clear-drawings")
            return 1

        # Show current state
        charts = manager.list_all_charts()
        sanitized = args.symbol.replace("/", "_").replace(":", "_").replace("*", "_")

        if sanitized not in charts:
            print(f"❌ No saved state found for symbol: {args.symbol}")
            print(f"\nAvailable symbols: {', '.join(sorted(charts.keys()))}")
            return 1

        info = charts[sanitized]
        print(f"\n📊 Current state for {args.symbol}:")
        print(f"   Drawings: {info['drawings']}")
        print(f"   Indicators: {info['indicators']}")

        if not args.confirm:
            print("\n⚠️  Add --confirm to proceed with clearing drawings")
            return 1

        if manager.clear_drawings(args.symbol):
            print(f"\n✅ Successfully cleared {info['drawings']} drawings for {args.symbol}")
            print("   (Indicators and other settings preserved)")
            return 0
        else:
            return 1

    # Clear entire chart state
    if args.clear_all:
        if not args.symbol:
            print("❌ --symbol required for --clear-all")
            return 1

        if not args.confirm:
            print("⚠️  Add --confirm to proceed with clearing entire chart state")
            return 1

        if manager.clear_chart_state(args.symbol):
            return 0
        else:
            return 1

    # Clear all states
    if args.clear_all_states:
        if not args.confirm:
            print("⚠️  Add --confirm to proceed with clearing ALL chart states")
            return 1

        if manager.clear_all_states():
            return 0
        else:
            return 1

    # No action specified
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
