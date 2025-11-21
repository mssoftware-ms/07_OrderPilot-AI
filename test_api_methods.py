"""Test that chartAPI methods exist."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

def main():
    print("=" * 70)
    print("Chart API Methods Test")
    print("=" * 70)

    app = QApplication(sys.argv)

    print("\n1. Creating chart widget...")
    chart = EmbeddedTradingViewChart()
    chart.show()

    print("2. Waiting for initialization (3 seconds)...\n")

    def check_api():
        print("3. Checking API methods...")

        script = """
            if (window.chartAPI) {
                const methods = Object.keys(window.chartAPI);
                'API_READY: ' + methods.join(', ');
            } else {
                'API_NOT_READY';
            }
        """

        def on_result(result):
            print(f"\n   Result: {result}\n")

            if result and result.startswith('API_READY'):
                methods = result.replace('API_READY: ', '')
                print(f"✅ SUCCESS!")
                print(f"   Available methods: {methods}")
            else:
                print(f"❌ FAIL: API not ready")

            app.quit()

        chart.web_view.page().runJavaScript(script, on_result)

    QTimer.singleShot(3000, check_api)

    app.exec()

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
