"""Simple test to check if chart initialization works."""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

def main():
    print("=" * 60)
    print("Chart Initialization Test")
    print("=" * 60)

    app = QApplication(sys.argv)

    print("\n1. Creating chart widget...")
    chart = EmbeddedTradingViewChart()

    print("2. Showing widget...")
    chart.show()

    # Give it time to load
    print("3. Waiting for page to load (3 seconds)...")

    def check_status():
        print("\n4. Checking if chartAPI is available...")
        chart.web_view.page().runJavaScript(
            "typeof window.chartAPI !== 'undefined' ? 'API_READY' : 'API_NOT_READY'",
            lambda result: print(f"   Result: {result}")
        )

        print("5. Checking console logs...")
        chart.web_view.page().runJavaScript(
            "document.getElementById('status').textContent",
            lambda result: print(f"   Status text: {result}")
        )

        # Exit after checking
        QTimer.singleShot(1000, app.quit)

    QTimer.singleShot(3000, check_status)

    print("   Starting Qt event loop...")
    app.exec()

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
