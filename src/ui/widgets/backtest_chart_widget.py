"""Backtest Chart Widget with Qt WebChannel Integration.

Provides a chart widget for displaying backtest results using TradingView's
Lightweight Charts JavaScript library with Qt WebChannel bridge.
"""

import logging
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.models.backtest_models import BacktestResult
from src.ui.chart.chart_bridge import ChartBridge

logger = logging.getLogger(__name__)


class BacktestChartWidget(QWidget):
    """Chart widget for displaying backtest results.

    Uses Qt WebChannel to communicate between Python and JavaScript,
    displaying interactive charts with TradingView Lightweight Charts.

    Features:
        - Display backtest candlesticks
        - Show equity curve
        - Trade markers (entry/exit with P&L)
        - Technical indicators
        - Toggle markers and indicators
        - Responsive and interactive

    Example:
        widget = BacktestChartWidget()
        widget.load_backtest_result(backtest_result)
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialize backtest chart widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Qt WebChannel and Bridge
        self.channel = QWebChannel()
        self.bridge = ChartBridge(self)

        # WebEngine View
        self.web_view = QWebEngineView()

        # UI Components
        self.symbol_label: QLabel | None = None
        self.metrics_label: QLabel | None = None
        self.toggle_markers_btn: QPushButton | None = None
        self.clear_btn: QPushButton | None = None

        # State
        self._markers_visible = True

        # Setup
        self._setup_ui()
        self._setup_webchannel()
        self._setup_connections()
        self._load_html()

        logger.info("BacktestChartWidget initialized")

    def _setup_ui(self) -> None:
        """Setup user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # WebEngine View (main chart area)
        self.web_view.setMinimumSize(800, 600)
        layout.addWidget(self.web_view)

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar with controls.

        Returns:
            QToolBar instance
        """
        toolbar = QToolBar("Chart Controls")
        toolbar.setMovable(False)

        # Symbol label
        self.symbol_label = QLabel("No data loaded")
        self.symbol_label.setStyleSheet("font-weight: bold; padding: 5px;")
        toolbar.addWidget(self.symbol_label)

        toolbar.addSeparator()

        # Metrics label
        self.metrics_label = QLabel("")
        self.metrics_label.setStyleSheet("padding: 5px;")
        toolbar.addWidget(self.metrics_label)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        toolbar.addWidget(spacer)

        # Toggle Markers button
        self.toggle_markers_btn = QPushButton("Hide Markers")
        self.toggle_markers_btn.setCheckable(True)
        self.toggle_markers_btn.clicked.connect(self._on_toggle_markers)
        toolbar.addWidget(self.toggle_markers_btn)

        # Clear button
        self.clear_btn = QPushButton("Clear Chart")
        self.clear_btn.clicked.connect(self._on_clear_chart)
        toolbar.addWidget(self.clear_btn)

        return toolbar

    def _setup_webchannel(self) -> None:
        """Setup Qt WebChannel for Python ↔ JavaScript communication."""
        # Register bridge object
        self.channel.registerObject("chartBridge", self.bridge)

        # Attach channel to web page
        self.web_view.page().setWebChannel(self.channel)

        logger.info("WebChannel registered with chartBridge object")

    def _setup_connections(self) -> None:
        """Setup signal/slot connections."""
        # Connect bridge signals
        self.bridge.chartDataReady.connect(self._on_chart_data_ready)
        self.bridge.error.connect(self._on_bridge_error)
        self.bridge.statusChanged.connect(self._on_status_changed)

    def _load_html(self) -> None:
        """Load HTML template with Lightweight Charts."""
        # For now, we'll load from a template file
        # In Phase 3.3, we'll create the full HTML/JS integration
        html_path = Path(__file__).parent.parent.parent.parent / "templates" / "chart_template.html"

        if html_path.exists():
            url = QUrl.fromLocalFile(str(html_path))
            self.web_view.load(url)
            logger.info(f"Loaded chart template from {html_path}")
        else:
            # Placeholder HTML for now
            placeholder_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Backtest Chart</title>
                <style>
                    body {
                        margin: 0;
                        padding: 20px;
                        font-family: Arial, sans-serif;
                        background: #1e1e1e;
                        color: #fff;
                    }
                    #status {
                        text-align: center;
                        padding: 100px 20px;
                    }
                    #status h1 {
                        color: #4CAF50;
                    }
                </style>
            </head>
            <body>
                <div id="status">
                    <h1>Backtest Chart Widget</h1>
                    <p>Ready to display backtest results</p>
                    <p><small>WebChannel initialized and waiting for data...</small></p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(placeholder_html)
            logger.warning(f"Chart template not found at {html_path}, using placeholder")

    def load_backtest_result(self, result: BacktestResult) -> None:
        """Load and display backtest result.

        Args:
            result: BacktestResult instance to display
        """
        logger.info(f"Loading backtest result for {result.symbol}")

        # Update symbol label
        self.symbol_label.setText(f"{result.symbol} | {result.timeframe}")

        # Update metrics label
        metrics = result.metrics
        metrics_text = (
            f"Trades: {metrics.total_trades} | "
            f"Win Rate: {metrics.win_rate:.1%} | "
            f"P&L: {result.total_pnl_pct:.2f}%"
        )
        self.metrics_label.setText(metrics_text)

        # Load into bridge
        self.bridge.loadBacktestResultObject(result)

    def clear_chart(self) -> None:
        """Clear the current chart."""
        self.bridge.clearChart()
        self.symbol_label.setText("No data loaded")
        self.metrics_label.setText("")

    def toggle_markers(self, show: bool) -> None:
        """Toggle trade markers visibility.

        Args:
            show: True to show markers, False to hide
        """
        self._markers_visible = show
        self.bridge.toggleMarkers(show)

    def _on_toggle_markers(self, checked: bool) -> None:
        """Handle toggle markers button click."""
        show = not checked
        self.toggle_markers(show)

        # Update button text
        self.toggle_markers_btn.setText("Show Markers" if checked else "Hide Markers")

    def _on_clear_chart(self) -> None:
        """Handle clear chart button click."""
        self.clear_chart()

    def _on_chart_data_ready(self, json_data: str) -> None:
        """Handle chart data ready signal from bridge.

        Args:
            json_data: Chart data as JSON string
        """
        logger.debug(f"Chart data ready: {len(json_data)} bytes")
        # JavaScript will pick up this signal automatically via WebChannel

    def _on_bridge_error(self, error_msg: str) -> None:
        """Handle error from bridge.

        Args:
            error_msg: Error message
        """
        logger.error(f"Chart bridge error: {error_msg}")
        self.metrics_label.setText(f"Error: {error_msg}")
        self.metrics_label.setStyleSheet("color: red; padding: 5px;")

    def _on_status_changed(self, status_msg: str) -> None:
        """Handle status change from bridge.

        Args:
            status_msg: Status message
        """
        logger.info(f"Chart status: {status_msg}")
        # Could display in status bar if needed

    def closeEvent(self, event) -> None:
        """Handle widget close event.

        Args:
            event: Close event
        """
        # Clean up WebChannel
        self.channel.deregisterObject(self.bridge)
        logger.info("BacktestChartWidget closed, WebChannel deregistered")
        super().closeEvent(event)
