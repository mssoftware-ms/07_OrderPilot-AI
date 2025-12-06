"""ChartBridge - Qt WebChannel Bridge for Lightweight Charts.

Provides a QObject-based bridge between Python (PyQt6) and JavaScript (Lightweight Charts)
using Qt WebChannel for bi-directional communication.
"""

import json
import logging
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.core.models.backtest_models import BacktestResult
from src.ui.chart.chart_adapter import ChartAdapter

logger = logging.getLogger(__name__)


class ChartBridge(QObject):
    """Qt WebChannel bridge for chart communication.

    Enables Python ↔ JavaScript communication for chart updates:
    - Python → JS: Emit signals with chart data (JSON)
    - JS → Python: Call slots to request data or perform actions

    Signals:
        chartDataReady: Emitted when chart data is ready (JSON string)
        error: Emitted when an error occurs (error message)
        statusChanged: Emitted when bridge status changes (status message)

    Example Usage:
        # In Python (PyQt6):
        bridge = ChartBridge()
        channel = QWebChannel()
        channel.registerObject("chartBridge", bridge)
        web_view.page().setWebChannel(channel)

        # Load backtest result
        bridge.loadBacktestResult(result.model_dump_json())

        # In JavaScript:
        new QWebChannel(qt.webChannelTransport, function(channel) {
            var chartBridge = channel.objects.chartBridge;

            chartBridge.chartDataReady.connect(function(jsonData) {
                var data = JSON.parse(jsonData);
                renderChart(data);
            });
        });
    """

    # Signals (Python → JavaScript)
    chartDataReady = pyqtSignal(str)  # JSON string with chart data
    error = pyqtSignal(str)  # Error message
    statusChanged = pyqtSignal(str)  # Status message

    def __init__(self, parent: QObject | None = None):
        """Initialize ChartBridge.

        Args:
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._adapter = ChartAdapter()
        self._current_result: BacktestResult | None = None
        logger.info("ChartBridge initialized")

    @pyqtSlot(str)
    def loadBacktestResult(self, result_json: str) -> None:
        """Load and display backtest result from JSON.

        Called from JavaScript to load backtest data.

        Args:
            result_json: BacktestResult as JSON string

        Emits:
            chartDataReady: When conversion is successful
            error: When conversion fails
        """
        try:
            logger.info("Loading backtest result from JSON...")

            # Parse JSON to BacktestResult
            result_dict = json.loads(result_json)
            result = BacktestResult(**result_dict)

            self._current_result = result
            logger.info(f"Loaded BacktestResult for {result.symbol}")

            # Convert to chart data
            self._convert_and_emit_chart_data(result)

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {e}"
            logger.error(error_msg)
            self.error.emit(error_msg)

        except Exception as e:
            error_msg = f"Error loading backtest result: {e}"
            logger.exception(error_msg)
            self.error.emit(error_msg)

    @pyqtSlot(object)
    def loadBacktestResultObject(self, result: BacktestResult) -> None:
        """Load and display backtest result from Python object.

        Called from Python code to display backtest.

        Args:
            result: BacktestResult instance

        Emits:
            chartDataReady: When conversion is successful
            error: When conversion fails
        """
        try:
            logger.info(f"Loading BacktestResult object for {result.symbol}")
            self._current_result = result
            self._convert_and_emit_chart_data(result)

        except Exception as e:
            error_msg = f"Error loading backtest result: {e}"
            logger.exception(error_msg)
            self.error.emit(error_msg)

    @pyqtSlot(str)
    def loadLiveData(self, symbol: str) -> None:
        """Load and display live market data for a symbol.

        Called from JavaScript to request live data.

        Args:
            symbol: Trading symbol (e.g., "AAPL")

        Emits:
            chartDataReady: When data is loaded
            error: When loading fails

        Note:
            This is a placeholder. In a real implementation, this would:
            1. Fetch live bars from market data provider
            2. Convert to chart format
            3. Emit chartDataReady signal
        """
        try:
            logger.info(f"Live data requested for {symbol}")
            self.statusChanged.emit(f"Loading live data for {symbol}...")

            # TODO: Implement live data loading
            # For now, emit error indicating it's not implemented
            error_msg = "Live data loading not yet implemented"
            logger.warning(error_msg)
            self.error.emit(error_msg)

        except Exception as e:
            error_msg = f"Error loading live data: {e}"
            logger.exception(error_msg)
            self.error.emit(error_msg)

    @pyqtSlot(str)
    def updateTrade(self, trade_json: str) -> None:
        """Update chart with new trade marker (for live trading).

        Called from JavaScript or Python when a trade is executed.

        Args:
            trade_json: Trade as JSON string

        Emits:
            chartDataReady: With updated markers
            error: When update fails

        Note:
            This updates only the markers, not the full chart.
        """
        try:
            logger.info("Updating trade marker...")

            # Parse trade JSON
            from src.core.models.backtest_models import Trade
            trade_dict = json.loads(trade_json)
            trade = Trade(**trade_dict)

            logger.info(f"Trade update: {trade.id} - {trade.side} @ {trade.entry_price}")

            # Build marker for this trade
            markers = self._adapter.build_markers_from_trades([trade])

            # Emit partial update (just markers)
            update_data = {
                'type': 'trade_update',
                'markers': markers
            }

            self.chartDataReady.emit(json.dumps(update_data))
            self.statusChanged.emit(f"Trade {trade.id} added to chart")

        except json.JSONDecodeError as e:
            error_msg = f"Invalid trade JSON: {e}"
            logger.error(error_msg)
            self.error.emit(error_msg)

        except Exception as e:
            error_msg = f"Error updating trade: {e}"
            logger.exception(error_msg)
            self.error.emit(error_msg)

    @pyqtSlot(result=str)
    def getCurrentSymbol(self) -> str:
        """Get currently displayed symbol.

        Returns:
            Symbol string or empty string if none loaded
        """
        if self._current_result:
            return self._current_result.symbol
        return ""

    @pyqtSlot(result=str)
    def getMetricsSummary(self) -> str:
        """Get summary of current backtest metrics as JSON.

        Returns:
            JSON string with key metrics or empty object
        """
        if not self._current_result:
            return "{}"

        try:
            metrics = self._current_result.metrics
            summary = {
                'total_trades': metrics.total_trades,
                'win_rate': metrics.win_rate,
                'profit_factor': metrics.profit_factor,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown_pct': metrics.max_drawdown_pct,
                'total_return_pct': metrics.total_return_pct
            }
            return json.dumps(summary)

        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return "{}"

    @pyqtSlot()
    def clearChart(self) -> None:
        """Clear the current chart.

        Emits:
            chartDataReady: With empty data
            statusChanged: With clear message
        """
        logger.info("Clearing chart...")
        self._current_result = None

        # Emit empty chart data
        empty_data = {
            'candlesticks': [],
            'equity_curve': [],
            'markers': [],
            'indicators': {},
            'metadata': {
                'symbol': '',
                'cleared': True
            }
        }

        self.chartDataReady.emit(json.dumps(empty_data))
        self.statusChanged.emit("Chart cleared")

    @pyqtSlot(bool)
    def toggleMarkers(self, show: bool) -> None:
        """Toggle trade markers on/off.

        Args:
            show: True to show markers, False to hide

        Emits:
            chartDataReady: With updated data
        """
        if not self._current_result:
            logger.warning("No chart data to toggle markers")
            return

        try:
            logger.info(f"Toggling markers: {show}")

            # Re-convert with or without markers
            chart_data = self._adapter.backtest_result_to_chart_data(
                self._current_result
            )

            if not show:
                chart_data['markers'] = []

            self.chartDataReady.emit(json.dumps(chart_data))
            self.statusChanged.emit(f"Markers {'shown' if show else 'hidden'}")

        except Exception as e:
            error_msg = f"Error toggling markers: {e}"
            logger.exception(error_msg)
            self.error.emit(error_msg)

    @pyqtSlot(str, bool)
    def toggleIndicator(self, indicator_name: str, show: bool) -> None:
        """Toggle specific indicator on/off.

        Args:
            indicator_name: Name of indicator (e.g., "SMA_20")
            show: True to show, False to hide

        Emits:
            chartDataReady: With updated indicators
        """
        if not self._current_result:
            logger.warning("No chart data to toggle indicator")
            return

        try:
            logger.info(f"Toggling indicator {indicator_name}: {show}")

            chart_data = self._adapter.backtest_result_to_chart_data(
                self._current_result
            )

            if not show and indicator_name in chart_data['indicators']:
                del chart_data['indicators'][indicator_name]

            self.chartDataReady.emit(json.dumps(chart_data))
            self.statusChanged.emit(
                f"Indicator {indicator_name} {'shown' if show else 'hidden'}"
            )

        except Exception as e:
            error_msg = f"Error toggling indicator: {e}"
            logger.exception(error_msg)
            self.error.emit(error_msg)

    def _convert_and_emit_chart_data(self, result: BacktestResult) -> None:
        """Convert BacktestResult to chart data and emit signal.

        Args:
            result: BacktestResult to convert

        Emits:
            chartDataReady: With converted chart data
            statusChanged: With status message
            error: If conversion fails
        """
        try:
            logger.debug("Converting BacktestResult to chart data...")

            # Convert using ChartAdapter
            chart_data = self._adapter.backtest_result_to_chart_data(result)

            # Validate
            is_valid, errors = self._adapter.validate_chart_data(chart_data)

            if not is_valid:
                error_msg = f"Chart data validation failed: {', '.join(errors)}"
                logger.error(error_msg)
                self.error.emit(error_msg)
                return

            # Convert to JSON
            json_str = json.dumps(chart_data)

            logger.info(
                f"Chart data ready: {len(chart_data['candlesticks'])} bars, "
                f"{len(chart_data['markers'])} markers"
            )

            # Emit signal
            self.chartDataReady.emit(json_str)
            self.statusChanged.emit(
                f"Loaded {result.symbol} - {result.metrics.total_trades} trades"
            )

        except Exception as e:
            error_msg = f"Error converting chart data: {e}"
            logger.exception(error_msg)
            self.error.emit(error_msg)
