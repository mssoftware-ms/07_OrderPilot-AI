"""Simple test to verify chart initialization."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtWebEngineCore import QWebEnginePage
from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

class ConsolePage(QWebEnginePage):
    """Capture console messages."""

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        level_names = {
            0: "INFO",
            1: "WARN",
            2: "ERROR"
        }
        print(f"js: [{level_names.get(level, 'LOG')}] {message}")

def main():
    print("=" * 70)
    print("Chart Initialization Test")
    print("=" * 70)

    app = QApplication(sys.argv)

    print("\nCreating chart widget...")
    chart = EmbeddedTradingViewChart()

    # Enable console logging
    console_page = ConsolePage(chart.web_view)
    console_page.setHtml(chart.web_view.page().toHtml(lambda html: None))  # Copy existing content

    # Actually, easier to just override after creation
    old_page = chart.web_view.page()
    console_page = ConsolePage(chart.web_view)
    # Get HTML from template
    from src.ui.widgets.embedded_tradingview_chart import CHART_HTML_TEMPLATE
    console_page.setHtml(CHART_HTML_TEMPLATE)
    chart.web_view.setPage(console_page)

    chart.show()

    print("\nWaiting for initialization (5 seconds)...\n")

    def check_result():
        print("\n" + "=" * 70)
        print("Checking result...")
        print("=" * 70)

        def on_api_check(result):
            print(f"window.chartAPI: {result}")
            if result == 'READY':
                print("✅ SUCCESS: chartAPI is available!")
            else:
                print("❌ FAIL: chartAPI not available")
            app.quit()

        console_page.runJavaScript(
            "typeof window.chartAPI !== 'undefined' ? 'READY' : 'NOT_READY'",
            on_api_check
        )

    QTimer.singleShot(5000, check_result)

    app.exec()

if __name__ == "__main__":
    main()
