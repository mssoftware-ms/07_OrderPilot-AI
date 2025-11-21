"""Debug script to check if panels are created correctly."""

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
        print(f"[JS {level_names.get(level, 'LOG')}] {message}")

def main():
    print("=" * 80)
    print("PANEL DEBUG TEST")
    print("=" * 80)

    app = QApplication(sys.argv)

    # Create chart widget
    print("\n1. Creating chart widget...")
    chart = EmbeddedTradingViewChart()

    # Enable console logging
    console_page = ConsolePage(chart.web_view)
    from src.ui.widgets.embedded_tradingview_chart import CHART_HTML_TEMPLATE
    console_page.setHtml(CHART_HTML_TEMPLATE)
    chart.web_view.setPage(console_page)

    chart.show()
    print("   Widget shown\n")

    def test_sequence():
        print("2. Waiting for initialization (2 seconds)...\n")

        def check_init():
            print("3. Checking if chartAPI is ready...")

            def on_api_check(result):
                if result != "READY":
                    print(f"   ❌ chartAPI not ready: {result}")
                    app.quit()
                    return

                print("   ✅ chartAPI ready\n")
                print("4. Creating test data...")

                # Create simple test data
                dates = pd.date_range(start='2025-01-01', periods=10, freq='1min')
                data = pd.DataFrame({
                    'open': [100 + i for i in range(10)],
                    'high': [105 + i for i in range(10)],
                    'low': [95 + i for i in range(10)],
                    'close': [102 + i for i in range(10)],
                    'volume': [1000 * (i + 1) for i in range(10)]
                }, index=dates)

                print("   Created 10 bars of test data\n")
                print("5. Loading data into chart...")

                # Load data (should create Volume panel)
                chart.load_data(data)

                print("   Data loaded\n")
                print("6. Waiting 2 seconds for panels to render...\n")

                def check_panels():
                    print("7. Checking DOM for panels...")

                    check_script = """
                        (function() {
                            const container = document.getElementById('chart-container');
                            if (!container) return 'ERROR: chart-container not found';

                            const priceChart = document.getElementById('price-chart');
                            const allPanels = container.querySelectorAll('.indicator-panel');

                            let result = 'DOM Structure:\\n';
                            result += '  - chart-container: ' + (container ? 'EXISTS' : 'MISSING') + '\\n';
                            result += '  - price-chart: ' + (priceChart ? 'EXISTS' : 'MISSING') + '\\n';
                            result += '  - indicator panels: ' + allPanels.length + '\\n';

                            if (allPanels.length > 0) {
                                result += '\\nPanels found:\\n';
                                allPanels.forEach(function(panel) {
                                    result += '  - ' + panel.id + ' (height: ' + panel.clientHeight + 'px)\\n';
                                });
                            }

                            // Check if panelCharts exists
                            if (typeof window.chartAPI !== 'undefined' && window.chartAPI._panelCharts) {
                                const panelIds = Object.keys(window.chartAPI._panelCharts || {});
                                result += '\\nchartAPI panels: ' + panelIds.join(', ') + '\\n';
                            }

                            return result;
                        })();
                    """

                    def on_check(result):
                        print(result)
                        print("\n" + "=" * 80)

                        if 'indicator panels: 0' in result:
                            print("❌ NO PANELS CREATED!")
                            print("\nPossible causes:")
                            print("  - JavaScript error in createPanel()")
                            print("  - createPanel() not being called")
                            print("  - Panels created but removed immediately")
                        else:
                            print("✅ PANELS FOUND!")

                        app.quit()

                    console_page.runJavaScript(check_script, on_check)

                QTimer.singleShot(2000, check_panels)

            console_page.runJavaScript(
                "typeof window.chartAPI !== 'undefined' ? 'READY' : 'NOT_READY'",
                on_api_check
            )

        QTimer.singleShot(2000, check_init)

    QTimer.singleShot(100, test_sequence)

    app.exec()

if __name__ == "__main__":
    main()
