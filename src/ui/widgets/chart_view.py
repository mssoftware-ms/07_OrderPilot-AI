"""Advanced Chart View Widget.

Provides interactive charting with technical indicators,
real-time updates, and drawing tools.
"""

import logging
from dataclasses import dataclass
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

try:
    import pyqtgraph as pg
    from pyqtgraph import PlotDataItem, PlotWidget
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    logging.warning("PyQtGraph not installed. Chart features will be limited.")

import pandas as pd

from src.common.event_bus import Event, EventType, event_bus
from src.core.indicators.engine import IndicatorConfig, IndicatorEngine, IndicatorType

logger = logging.getLogger(__name__)


@dataclass
class ChartConfig:
    """Configuration for chart display."""
    symbol: str
    timeframe: str = "1T"  # 1 minute
    show_volume: bool = True
    show_indicators: bool = True
    theme: str = "dark"
    update_interval: int = 1000  # milliseconds


class CandlestickItem(pg.GraphicsObject):
    """Custom candlestick item for PyQtGraph."""

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.generatePicture()

    def generatePicture(self):
        """Generate the picture of candlesticks."""
        self.picture = pg.QtGui.QPicture()
        painter = pg.QtGui.QPainter(self.picture)

        width = 0.6
        for i, (timestamp, o, h, l, c, v) in enumerate(self.data):
            # Determine color
            if c > o:
                painter.setPen(pg.mkPen('g', width=1))
                painter.setBrush(pg.mkBrush('g'))
            else:
                painter.setPen(pg.mkPen('r', width=1))
                painter.setBrush(pg.mkBrush('r'))

            # Draw the wick
            painter.drawLine(pg.QtCore.QPointF(i, l), pg.QtCore.QPointF(i, h))

            # Draw the body
            body_height = abs(c - o)
            body_top = max(o, c)
            painter.drawRect(pg.QtCore.QRectF(i - width/2, body_top - body_height,
                                             width, body_height))

        painter.end()

    def paint(self, painter, *args):
        """Paint the candlesticks."""
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        """Get bounding rectangle."""
        return pg.QtCore.QRectF(self.picture.boundingRect())


class ChartView(QWidget):
    """Advanced interactive chart widget."""

    # Signals
    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)
    indicator_added = pyqtSignal(str)
    drawing_completed = pyqtSignal(dict)

    def __init__(self, config: ChartConfig | None = None):
        """Initialize chart view.

        Args:
            config: Chart configuration
        """
        super().__init__()

        if not PYQTGRAPH_AVAILABLE:
            logger.error("PyQtGraph not available. Chart functionality limited.")

        self.config = config or ChartConfig(symbol="AAPL")
        self.indicator_engine = IndicatorEngine()

        # Data storage
        self.data: pd.DataFrame | None = None
        self.indicators: dict[str, Any] = {}
        self.drawings: list[Any] = []

        # Setup UI
        self._setup_ui()

        # Setup timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_chart)
        self.update_timer.start(self.config.update_interval)

        # Connect to event bus
        event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar)
        event_bus.subscribe(EventType.MARKET_TICK, self._on_market_tick)

    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        if PYQTGRAPH_AVAILABLE:
            # Create main chart
            self.chart_widget = pg.PlotWidget()
            self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
            self.chart_widget.setLabel('left', 'Price', units='$')
            self.chart_widget.setLabel('bottom', 'Time')

            # Apply theme
            if self.config.theme == "dark":
                self.chart_widget.setBackground('k')
            else:
                self.chart_widget.setBackground('w')

            # Add crosshair
            self.crosshair_v = pg.InfiniteLine(angle=90, movable=False)
            self.crosshair_h = pg.InfiniteLine(angle=0, movable=False)
            self.chart_widget.addItem(self.crosshair_v, ignoreBounds=True)
            self.chart_widget.addItem(self.crosshair_h, ignoreBounds=True)

            # Mouse tracking
            self.chart_widget.scene().sigMouseMoved.connect(self._on_mouse_move)

            layout.addWidget(self.chart_widget, stretch=3)

            # Create volume chart
            if self.config.show_volume:
                self.volume_widget = pg.PlotWidget()
                self.volume_widget.showGrid(x=True, y=True, alpha=0.3)
                self.volume_widget.setLabel('left', 'Volume')
                self.volume_widget.setXLink(self.chart_widget)  # Link X-axis

                if self.config.theme == "dark":
                    self.volume_widget.setBackground('k')
                else:
                    self.volume_widget.setBackground('w')

                layout.addWidget(self.volume_widget, stretch=1)
        else:
            # Fallback to simple label
            self.chart_widget = QLabel("PyQtGraph not installed")
            self.chart_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.chart_widget)

    def _create_toolbar(self) -> QToolBar:
        """Create chart toolbar."""
        toolbar = QToolBar()

        # Symbol selector
        toolbar.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"])
        self.symbol_combo.setCurrentText(self.config.symbol)
        self.symbol_combo.currentTextChanged.connect(self._on_symbol_change)
        toolbar.addWidget(self.symbol_combo)

        toolbar.addSeparator()

        # Timeframe selector
        toolbar.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1T", "5T", "15T", "30T", "1H", "4H", "1D"])
        self.timeframe_combo.setCurrentText(self.config.timeframe)
        self.timeframe_combo.currentTextChanged.connect(self._on_timeframe_change)
        toolbar.addWidget(self.timeframe_combo)

        toolbar.addSeparator()

        # Indicator buttons
        toolbar.addWidget(QLabel("Indicators:"))

        self.ma_button = QPushButton("MA")
        self.ma_button.setCheckable(True)
        self.ma_button.clicked.connect(lambda: self._toggle_indicator("MA"))
        toolbar.addWidget(self.ma_button)

        self.bb_button = QPushButton("BB")
        self.bb_button.setCheckable(True)
        self.bb_button.clicked.connect(lambda: self._toggle_indicator("BB"))
        toolbar.addWidget(self.bb_button)

        self.rsi_button = QPushButton("RSI")
        self.rsi_button.setCheckable(True)
        self.rsi_button.clicked.connect(lambda: self._toggle_indicator("RSI"))
        toolbar.addWidget(self.rsi_button)

        self.macd_button = QPushButton("MACD")
        self.macd_button.setCheckable(True)
        self.macd_button.clicked.connect(lambda: self._toggle_indicator("MACD"))
        toolbar.addWidget(self.macd_button)

        toolbar.addSeparator()

        # Drawing tools
        toolbar.addWidget(QLabel("Tools:"))

        self.line_button = QPushButton("Line")
        self.line_button.setCheckable(True)
        self.line_button.clicked.connect(lambda: self._set_drawing_mode("line"))
        toolbar.addWidget(self.line_button)

        self.hline_button = QPushButton("H-Line")
        self.hline_button.setCheckable(True)
        self.hline_button.clicked.connect(lambda: self._set_drawing_mode("hline"))
        toolbar.addWidget(self.hline_button)

        self.rect_button = QPushButton("Rectangle")
        self.rect_button.setCheckable(True)
        self.rect_button.clicked.connect(lambda: self._set_drawing_mode("rect"))
        toolbar.addWidget(self.rect_button)

        toolbar.addSeparator()

        # Zoom controls
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self._zoom_in)
        toolbar.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self._zoom_out)
        toolbar.addWidget(self.zoom_out_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self._reset_view)
        toolbar.addWidget(self.reset_button)

        return toolbar

    def load_data(self, data: pd.DataFrame):
        """Load market data.

        Args:
            data: OHLCV DataFrame
        """
        self.data = data
        self._update_chart()

    def _update_chart(self):
        """Update the chart display."""
        if not PYQTGRAPH_AVAILABLE or self.data is None:
            return

        try:
            # Clear existing items
            self.chart_widget.clear()

            # Prepare candlestick data
            candle_data = []
            for i, (index, row) in enumerate(self.data.iterrows()):
                candle_data.append((
                    i,
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row.get('volume', 0)
                ))

            # Draw candlesticks
            if candle_data:
                candles = CandlestickItem(candle_data)
                self.chart_widget.addItem(candles)

            # Draw indicators
            self._draw_indicators()

            # Draw volume bars
            if self.config.show_volume and hasattr(self, 'volume_widget'):
                self._draw_volume()

            # Restore drawings
            self._restore_drawings()

            # Update axis
            self.chart_widget.setXRange(0, len(self.data), padding=0.1)

        except Exception as e:
            logger.error(f"Error updating chart: {e}")

    def _draw_indicators(self):
        """Draw technical indicators."""
        if not self.config.show_indicators or self.data is None:
            return

        x_axis = list(range(len(self.data)))

        # Moving Averages
        if self.ma_button.isChecked():
            # Calculate SMA
            config = IndicatorConfig(
                indicator_type=IndicatorType.SMA,
                params={'period': 20}
            )
            result = self.indicator_engine.calculate(self.data, config)

            # Plot SMA
            sma_plot = self.chart_widget.plot(
                x_axis,
                result.values.values,
                pen=pg.mkPen('y', width=2),
                name='SMA(20)'
            )
            self.indicators['sma'] = sma_plot

        # Bollinger Bands
        if self.bb_button.isChecked():
            config = IndicatorConfig(
                indicator_type=IndicatorType.BB,
                params={'period': 20, 'std_dev': 2}
            )
            result = self.indicator_engine.calculate(self.data, config)

            # Plot bands
            bb = result.values
            upper = self.chart_widget.plot(
                x_axis,
                bb['upper'].values,
                pen=pg.mkPen('c', width=1, style=Qt.PenStyle.DashLine),
                name='BB Upper'
            )
            middle = self.chart_widget.plot(
                x_axis,
                bb['middle'].values,
                pen=pg.mkPen('c', width=1),
                name='BB Middle'
            )
            lower = self.chart_widget.plot(
                x_axis,
                bb['lower'].values,
                pen=pg.mkPen('c', width=1, style=Qt.PenStyle.DashLine),
                name='BB Lower'
            )

            # Fill between bands
            fill = pg.FillBetweenItem(upper, lower, brush=pg.mkBrush(100, 100, 255, 30))
            self.chart_widget.addItem(fill)

            self.indicators['bb'] = {'upper': upper, 'middle': middle, 'lower': lower, 'fill': fill}

    def _draw_volume(self):
        """Draw volume bars."""
        if self.data is None or 'volume' not in self.data.columns:
            return

        x_axis = list(range(len(self.data)))
        volumes = self.data['volume'].values

        # Create volume bars
        self.volume_widget.clear()

        # Color based on price change
        for i in range(len(self.data)):
            if i == 0:
                color = 'g'
            else:
                color = 'g' if self.data['close'].iloc[i] > self.data['close'].iloc[i-1] else 'r'

            bar = pg.BarGraphItem(
                x=[i],
                height=[volumes[i]],
                width=0.8,
                brush=color
            )
            self.volume_widget.addItem(bar)

    def _toggle_indicator(self, indicator: str):
        """Toggle indicator display.

        Args:
            indicator: Indicator name
        """
        self._update_chart()
        self.indicator_added.emit(indicator)

    def _set_drawing_mode(self, mode: str):
        """Set drawing mode.

        Args:
            mode: Drawing mode (line, hline, rect)
        """
        # Reset other buttons
        for button in [self.line_button, self.hline_button, self.rect_button]:
            if button != self.sender():
                button.setChecked(False)

        self.drawing_mode = mode if self.sender().isChecked() else None
        logger.debug(f"Drawing mode: {self.drawing_mode}")

    def _on_mouse_move(self, pos):
        """Handle mouse movement for crosshair.

        Args:
            pos: Mouse position
        """
        if not PYQTGRAPH_AVAILABLE:
            return

        if self.chart_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.chart_widget.plotItem.vb.mapSceneToView(pos)
            self.crosshair_v.setPos(mouse_point.x())
            self.crosshair_h.setPos(mouse_point.y())

            # Update info label
            if self.data is not None and 0 <= int(mouse_point.x()) < len(self.data):
                idx = int(mouse_point.x())
                row = self.data.iloc[idx]
                info = f"O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f}"
                self.chart_widget.setTitle(info)

    def _zoom_in(self):
        """Zoom in on chart."""
        if PYQTGRAPH_AVAILABLE:
            self.chart_widget.plotItem.vb.scaleBy((0.8, 1))

    def _zoom_out(self):
        """Zoom out on chart."""
        if PYQTGRAPH_AVAILABLE:
            self.chart_widget.plotItem.vb.scaleBy((1.2, 1))

    def _reset_view(self):
        """Reset chart view."""
        if PYQTGRAPH_AVAILABLE and self.data is not None:
            self.chart_widget.setXRange(0, len(self.data), padding=0.1)
            self.chart_widget.autoRange(axis='y')

    def _restore_drawings(self):
        """Restore saved drawings."""
        # Implement drawing restoration
        pass

    def _on_symbol_change(self, symbol: str):
        """Handle symbol change.

        Args:
            symbol: New symbol
        """
        self.config.symbol = symbol
        self.symbol_changed.emit(symbol)
        logger.info(f"Symbol changed to: {symbol}")

    def _on_timeframe_change(self, timeframe: str):
        """Handle timeframe change.

        Args:
            timeframe: New timeframe
        """
        self.config.timeframe = timeframe
        self.timeframe_changed.emit(timeframe)
        logger.info(f"Timeframe changed to: {timeframe}")

    def _on_market_bar(self, event: Event):
        """Handle market bar event.

        Args:
            event: Market bar event
        """
        if event.data.get('symbol') == self.config.symbol:
            # Update data with new bar
            # This would append the new bar to self.data
            self._update_chart()

    def _on_market_tick(self, event: Event):
        """Handle market tick event.

        Args:
            event: Market tick event
        """
        # Update current bar with tick data
        pass

    def save_screenshot(self, filepath: str):
        """Save chart screenshot.

        Args:
            filepath: Path to save screenshot
        """
        if PYQTGRAPH_AVAILABLE:
            exporter = pg.exporters.ImageExporter(self.chart_widget.plotItem)
            exporter.export(filepath)
            logger.info(f"Chart saved to: {filepath}")