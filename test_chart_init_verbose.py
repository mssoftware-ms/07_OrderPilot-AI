"""Test chart with console message capture."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtWebEngineCore import QWebEnginePage
from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

class ConsolePage(QWebEnginePage):
    """Custom page that logs console messages."""

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """Capture JavaScript console messages."""
        level_str = {
            QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: "INFO",
            QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: "WARN",
            QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: "ERROR",
        }.get(level, "LOG")

        print(f"js: [{level_str}] {message}")
        if lineNumber > 0:
            print(f"     (line {lineNumber})")

def main():
    print("=" * 60)
    print("Chart Initialization Test (Verbose)")
    print("=" * 60)

    app = QApplication(sys.argv)

    print("\n1. Creating chart widget...")
    chart = EmbeddedTradingViewChart()

    # Replace page with our console logging page
    old_page = chart.web_view.page()
    console_page = ConsolePage(chart.web_view)
    chart.web_view.setPage(console_page)

    # Re-load the HTML content
    print("2. Loading HTML with console capture...")
    from src.ui.widgets.embedded_tradingview_chart import HTML_TEMPLATE
    console_page.setHtml(HTML_TEMPLATE)

    print("3. Showing widget...")
    chart.show()

    print("4. Waiting 5 seconds for initialization...")

    def check_status():
        print("\n5. Final status check...")
        console_page.runJavaScript(
            "typeof window.chartAPI !== 'undefined' ? 'READY' : 'NOT_READY'",
            lambda result: print(f"   chartAPI: {result}")
        )

        # Exit
        QTimer.singleShot(500, app.quit)

    QTimer.singleShot(5000, check_status)

    app.exec()

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
