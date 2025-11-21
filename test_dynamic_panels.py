"""Test dynamic panel creation."""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtWebEngineCore import QWebEnginePage
from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart
import pandas as pd
import numpy as np

class ConsolePage(QWebEnginePage):
    """Capture console messages."""

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        level_names = {0: "INFO", 1: "WARN", 2: "ERROR"}
        print(f"js: [{level_names.get(level, 'LOG')}] {message}")

def main():
    print("=" * 70)
    print("Dynamic Panel Test")
    print("=" * 70)

    app = QApplication(sys.argv)

    print("\n1. Creating chart widget...")
    chart = EmbeddedTradingViewChart()

    # Enable console logging
    console_page = ConsolePage(chart.web_view)
    from src.ui.widgets.embedded_tradingview_chart import CHART_HTML_TEMPLATE
    console_page.setHtml(CHART_HTML_TEMPLATE)
    chart.web_view.setPage(console_page)

    chart.show()

    print("2. Waiting for initialization...\n")

    def test_panels():
        print("\n" + "=" * 70)
        print("3. Testing dynamic panel creation...")
        print("=" * 70)

        # Test 1: Create Volume panel
        print("\n   Creating Volume panel...")
        volume_data = [
            {"time": "2025-01-01", "value": 1000000, "color": "#26a69a"},
            {"time": "2025-01-02", "value": 1500000, "color": "#ef5350"},
            {"time": "2025-01-03", "value": 1200000, "color": "#26a69a"},
        ]

        create_script = f"""
            window.chartAPI.createPanel('volume', 'Volume', 'histogram', '#26a69a', null, null);
            window.chartAPI.setPanelData('volume', {json.dumps(volume_data)});
            console.log('Volume panel created and data set');
        """
        console_page.runJavaScript(create_script)

        # Test 2: Create RSI panel
        def test_rsi():
            print("   Creating RSI panel...")
            rsi_data = [
                {"time": "2025-01-01", "value": 45},
                {"time": "2025-01-02", "value": 55},
                {"time": "2025-01-03", "value": 62},
            ]

            rsi_script = f"""
                window.chartAPI.createPanel('rsi', 'RSI(14)', 'line', '#FF00FF', 0, 100);
                window.chartAPI.setPanelData('rsi', {json.dumps(rsi_data)});
                console.log('RSI panel created and data set');
            """
            console_page.runJavaScript(rsi_script)

            # Check results
            def check_results():
                print("\n" + "=" * 70)
                print("4. Checking results...")
                print("=" * 70)

                def on_check(result):
                    print(f"   Panel count: {result}")
                    if result == "2":
                        print("\n✅ SUCCESS: Both panels created!")
                    else:
                        print(f"\n❌ FAIL: Expected 2 panels, got {result}")

                    app.quit()

                console_page.runJavaScript(
                    "Object.keys(window.chartAPI ? (window.chartAPI._panelCharts || {}) : {}).length.toString()",
                    on_check
                )

            QTimer.singleShot(500, check_results)

        QTimer.singleShot(500, test_rsi)

    QTimer.singleShot(2000, test_panels)

    app.exec()

if __name__ == "__main__":
    main()
