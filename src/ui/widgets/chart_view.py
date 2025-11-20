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
        self.picture = None
        self._bounds = None
        self.generatePicture()

    def setData(self, data):
        """Update candlestick data and regenerate picture."""
        self.prepareGeometryChange()  # Notify Qt that geometry will change
        self.data = data
        self.generatePicture()
        self.update()  # Trigger repaint

    def generatePicture(self):
        """Generate the picture of candlesticks."""
        if not self.data:
            self.picture = pg.QtGui.QPicture()
            self._bounds = pg.QtCore.QRectF(0, 0, 1, 1)
            return

        self.picture = pg.QtGui.QPicture()
        painter = pg.QtGui.QPainter(self.picture)

        width = 0.6
        min_price = float('inf')
        max_price = float('-inf')

        for i, (timestamp, o, h, l, c, v) in enumerate(self.data):
            # Skip invalid data
            if not all(isinstance(x, (int, float)) and not (x != x) for x in [o, h, l, c]):  # NaN check
                continue

            # Track bounds
            min_price = min(min_price, l)
            max_price = max(max_price, h)

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
            if body_height > 0:
                painter.drawRect(pg.QtCore.QRectF(i - width/2, body_top - body_height,
                                                 width, body_height))
            else:
                # Draw a line for doji candles (open == close)
                painter.drawLine(pg.QtCore.QPointF(i - width/2, o), pg.QtCore.QPointF(i + width/2, o))

        painter.end()

        # Store bounds for boundingRect()
        if len(self.data) > 0 and min_price != float('inf'):
            self._bounds = pg.QtCore.QRectF(
                -0.5, min_price,
                len(self.data) + 0.5, max_price - min_price
            )
        else:
            self._bounds = pg.QtCore.QRectF(0, 0, 1, 1)

    def paint(self, painter, *args):
        """Paint the candlesticks."""
        if self.picture:
            painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        """Get bounding rectangle."""
        if self._bounds:
            return self._bounds
        return pg.QtCore.QRectF(0, 0, 1, 1)

    def dataBounds(self, ax, frac=1.0, orthoRange=None):
        """Return the range of data along the specified axis.

        This is needed for proper AutoRange functionality.
        """
        if not self.data or len(self.data) == 0:
            return (0, 1)

        if ax == 0:  # X axis
            return (0, len(self.data))
        elif ax == 1:  # Y axis
            prices = []
            for timestamp, o, h, l, c, v in self.data:
                if all(isinstance(x, (int, float)) and not (x != x) for x in [h, l]):
                    prices.extend([h, l])

            if prices:
                return (min(prices), max(prices))
            return (0, 1)

        return (0, 1)


class ChartView(QWidget):
    """Advanced interactive chart widget."""

    # Signals
    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)
    indicator_added = pyqtSignal(str)
    drawing_completed = pyqtSignal(dict)

    def __init__(self, config: ChartConfig | None = None, history_manager=None):
        """Initialize chart view.

        Args:
            config: Chart configuration
            history_manager: HistoryManager instance for loading data
        """
        super().__init__()

        if not PYQTGRAPH_AVAILABLE:
            logger.error("PyQtGraph not available. Chart functionality limited.")

        self.config = config or ChartConfig(symbol="AAPL")
        self.indicator_engine = IndicatorEngine()
        self.history_manager = history_manager

        # Data storage
        self.data: pd.DataFrame | None = None
        self.full_data: pd.DataFrame | None = None  # Full dataset when displaying subset
        self.indicators: dict[str, Any] = {}
        self.drawings: list[Any] = []
        self.current_symbol: str | None = None
        self.current_data_provider: str | None = None
        self.drawing_mode: str | None = None  # Current drawing mode (line, hline, rect)
        self.market_is_open: bool = False  # Track if market is currently open
        self.pending_updates: bool = False  # Track if updates are pending

        # Setup UI
        self._setup_ui()

        # Setup timers - but don't start automatically
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_pending_updates)
        # Note: Timer is started only when market is open and we're subscribed to real-time data

        # Connect to event bus
        event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar)
        event_bus.subscribe(EventType.MARKET_TICK, self._on_market_tick)

    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create and add toolbar
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        if PYQTGRAPH_AVAILABLE:
            # Create main chart with performance optimizations
            self.chart_widget = pg.PlotWidget()
            self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
            self.chart_widget.setLabel('left', 'Price', units='$')
            self.chart_widget.setLabel('bottom', 'Time')

            # Performance optimizations
            # Disable auto-ranging after initial display for better performance
            self.chart_widget.setClipToView(True)  # Only render visible data
            self.chart_widget.setDownsampling(auto=True)  # Enable downsampling

            # Apply theme
            if self.config.theme == "dark":
                self.chart_widget.setBackground('k')
            else:
                self.chart_widget.setBackground('w')

            # Add crosshair
            self.crosshair_v = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('y', width=1))
            self.crosshair_h = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('y', width=1))
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
        toolbar.setVisible(True)  # Show toolbar with all tools

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

        # Market status label
        toolbar.addSeparator()
        self.market_status_label = QLabel("Market: Live")
        self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")
        toolbar.addWidget(self.market_status_label)

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

    def load_data(self, data: pd.DataFrame, max_bars: int = 2000):
        """Load market data.

        Args:
            data: OHLCV DataFrame
            max_bars: Maximum number of bars to display (default: 2000)
        """
        if len(data) > max_bars:
            logger.info(f"Dataset has {len(data)} bars. Showing last {max_bars} bars for performance.")
            self.data = data.tail(max_bars).copy()
            self.full_data = data  # Keep full data for reference
        else:
            self.data = data
            self.full_data = None
        self._update_chart()

    def _update_chart(self):
        """Update the chart display."""
        if not PYQTGRAPH_AVAILABLE or self.data is None:
            return

        if len(self.data) == 0:
            logger.warning("No data to display in chart")
            return

        try:
            # Clear existing items
            self.chart_widget.clear()

            # Validate data and prepare candlestick data
            candle_data = []
            nan_count = 0
            for i, (index, row) in enumerate(self.data.iterrows()):
                # Check for NaN values
                o, h, l, c = row['open'], row['high'], row['low'], row['close']
                v = row.get('volume', 0)

                # Skip rows with NaN values
                if any(pd.isna(x) or x != x for x in [o, h, l, c]):
                    nan_count += 1
                    continue

                candle_data.append((
                    i,
                    float(o),
                    float(h),
                    float(l),
                    float(c),
                    float(v) if not pd.isna(v) else 0
                ))

            if nan_count > 0:
                logger.warning(f"Skipped {nan_count} rows with NaN values")

            # Draw candlesticks
            if candle_data:
                logger.debug(f"Drawing {len(candle_data)} candlesticks")
                candles = CandlestickItem(candle_data)
                self.chart_widget.addItem(candles)

                # Re-add crosshair on top
                self.chart_widget.addItem(self.crosshair_v, ignoreBounds=True)
                self.chart_widget.addItem(self.crosshair_h, ignoreBounds=True)
            else:
                logger.error("No valid candle data to display")
                return

            # Draw indicators
            self._draw_indicators()

            # Draw volume bars
            if self.config.show_volume and hasattr(self, 'volume_widget'):
                self._draw_volume()

            # Restore drawings
            self._restore_drawings()

            # Update axis range
            self.chart_widget.setXRange(0, len(self.data), padding=0.1)
            self.chart_widget.enableAutoRange(axis='y')

            logger.debug(f"Chart updated successfully with {len(candle_data)} bars")

        except Exception as e:
            logger.error(f"Error updating chart: {e}", exc_info=True)

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

        # Load the new symbol with current data provider
        import asyncio
        asyncio.create_task(self.load_symbol(symbol, self.current_data_provider))

    def _on_timeframe_change(self, timeframe: str):
        """Handle timeframe change.

        Args:
            timeframe: New timeframe
        """
        self.config.timeframe = timeframe
        self.timeframe_changed.emit(timeframe)
        logger.info(f"Timeframe changed to: {timeframe}")

        # Reload data with new timeframe
        if self.current_symbol:
            import asyncio
            asyncio.create_task(self.load_symbol(self.current_symbol, self.current_data_provider))

    def _process_pending_updates(self):
        """Process pending chart updates (called by timer during market hours)."""
        if not self.pending_updates:
            return

        # Only process if we have data and chart is visible
        if self.data is None or not PYQTGRAPH_AVAILABLE:
            self.pending_updates = False
            return

        # For now, just clear the flag - actual incremental updates would be implemented here
        # This prevents constant full redraws
        self.pending_updates = False
        logger.debug("Processed pending chart updates")

    def _on_market_bar(self, event: Event):
        """Handle market bar event.

        Args:
            event: Market bar event
        """
        if event.data.get('symbol') == self.config.symbol:
            # Mark that we have pending updates instead of immediately redrawing
            self.pending_updates = True
            logger.debug(f"New bar received for {self.config.symbol}, update pending")

    def _on_market_tick(self, event: Event):
        """Handle market tick event.

        Args:
            event: Market tick event
        """
        if event.data.get('symbol') == self.config.symbol:
            # Mark pending updates for tick data
            self.pending_updates = True

    async def load_symbol(self, symbol: str, data_provider: str | None = None):
        """Load symbol data and display chart.

        Args:
            symbol: Trading symbol to load
            data_provider: Optional data provider source (e.g., 'alpaca', 'yahoo')
        """
        try:
            if not self.history_manager:
                logger.warning("No history manager available. Cannot load symbol data.")
                if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'setTitle'):
                    self.chart_widget.setTitle(f"{symbol} - No data source available")
                return

            # Update UI
            self.symbol_combo.setCurrentText(symbol)
            self.current_symbol = symbol
            self.current_data_provider = data_provider

            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'setTitle'):
                self.chart_widget.setTitle(f"Loading {symbol}...")

            logger.info(f"Loading {symbol} from provider: {data_provider or 'auto'}")

            # Import required classes
            from datetime import datetime, timedelta
            from src.core.market_data.history_provider import DataRequest, DataSource, Timeframe

            # Map timeframe string to enum
            timeframe_map = {
                "1T": Timeframe.MINUTE_1,
                "5T": Timeframe.MINUTE_5,
                "15T": Timeframe.MINUTE_15,
                "30T": Timeframe.MINUTE_30,
                "1H": Timeframe.HOUR_1,
                "4H": Timeframe.HOUR_4,
                "1D": Timeframe.DAY_1,
            }
            timeframe = timeframe_map.get(self.config.timeframe, Timeframe.MINUTE_1)

            # Map provider string to DataSource enum
            provider_source = None
            if data_provider:
                provider_map = {
                    "database": DataSource.DATABASE,
                    "ibkr": DataSource.IBKR,
                    "alpaca": DataSource.ALPACA,
                    "alpha_vantage": DataSource.ALPHA_VANTAGE,
                    "finnhub": DataSource.FINNHUB,
                    "yahoo": DataSource.YAHOO,
                }
                provider_source = provider_map.get(data_provider)

            # Create data request - always fetch last 90 days to ensure we have data even on weekends
            request = DataRequest(
                symbol=symbol,
                start_date=datetime.now() - timedelta(days=90),  # Last 90 days to ensure data on weekends
                end_date=datetime.now(),
                timeframe=timeframe,
                source=provider_source
            )

            # Fetch data with progress indicator
            logger.info(f"Fetching data for {symbol} from {request.start_date} to {request.end_date}, timeframe={timeframe}, provider={data_provider or 'auto'}")
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'setTitle'):
                self.chart_widget.setTitle(f"Loading {symbol}... Please wait")
            bars, source_used = await self.history_manager.fetch_data(request)

            if not bars:
                logger.warning(f"No data available for {symbol} from source {source_used}")
                if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'setTitle'):
                    self.chart_widget.setTitle(f"{symbol} - No data available")
                return

            # Check if we have recent data or only historical data (market closed)
            latest_bar_date = bars[-1].timestamp
            today = datetime.now().date()
            days_old = (datetime.now() - latest_bar_date).days

            market_status = ""
            if days_old >= 1:
                market_status = f" ⚠ Market Closed - Last data: {latest_bar_date.strftime('%Y-%m-%d %H:%M')}"
                logger.info(f"Market appears closed. Showing last available data from {latest_bar_date}")

                # Update market status label
                if hasattr(self, 'market_status_label'):
                    self.market_status_label.setText(f"⚠ MARKET CLOSED - Last: {latest_bar_date.strftime('%Y-%m-%d')}")
                    self.market_status_label.setStyleSheet("color: #FFA500; font-weight: bold; padding: 5px; background-color: #332200;")
            else:
                # Market is open/live data
                if hasattr(self, 'market_status_label'):
                    self.market_status_label.setText("✓ Market: Live")
                    self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")

            logger.info(f"Loaded {len(bars)} bars for {symbol} from {source_used}{market_status}")

            # Convert to DataFrame with progress indicator
            if len(bars) > 5000:
                if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'setTitle'):
                    self.chart_widget.setTitle(f"Processing {len(bars)} bars...")

            data_dict = {
                'timestamp': [bar.timestamp for bar in bars],
                'open': [float(bar.open) for bar in bars],
                'high': [float(bar.high) for bar in bars],
                'low': [float(bar.low) for bar in bars],
                'close': [float(bar.close) for bar in bars],
                'volume': [bar.volume for bar in bars]
            }

            df = pd.DataFrame(data_dict)
            df.set_index('timestamp', inplace=True)

            # Load data into chart (with performance limit)
            total_bars = len(bars)
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'setTitle'):
                self.chart_widget.setTitle(f"Rendering chart...")
            self.load_data(df, max_bars=2000)

            # Update title with source info and market status
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'setTitle'):
                displayed_bars = len(self.data) if self.data is not None else 0
                if total_bars > displayed_bars:
                    title = f"{symbol} ({source_used.upper()}) - Showing {displayed_bars}/{total_bars} bars"
                else:
                    title = f"{symbol} ({source_used.upper()}) - {total_bars} bars"
                if market_status:
                    title += market_status
                self.chart_widget.setTitle(title)

            # Check market hours and control real-time updates
            self._control_updates_based_on_market()

            logger.info(f"Chart loaded successfully. Market open: {self.market_is_open}, Timer active: {self.update_timer.isActive()}")

        except Exception as e:
            logger.error(f"Error loading symbol {symbol}: {e}", exc_info=True)
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'setTitle'):
                self.chart_widget.setTitle(f"{symbol} - Error: {str(e)}")

    async def refresh_data(self):
        """Refresh current symbol data."""
        if self.current_symbol:
            await self.load_symbol(self.current_symbol, self.current_data_provider)

    def _check_market_hours(self) -> bool:
        """Check if market is currently open.

        Returns:
            True if market is open, False otherwise
        """
        try:
            from datetime import datetime, time
            import pytz

            # Get current time in US/Eastern (NYSE timezone)
            eastern = pytz.timezone('US/Eastern')
            now = datetime.now(eastern)

            # Market hours: Monday-Friday, 9:30 AM - 4:00 PM ET
            market_open = time(9, 30)
            market_close = time(16, 0)

            # Check if it's a weekday (0 = Monday, 4 = Friday)
            is_weekday = now.weekday() < 5

            # Check if current time is within market hours
            current_time = now.time()
            is_trading_hours = market_open <= current_time <= market_close

            is_open = is_weekday and is_trading_hours

            # Update market status
            if is_open != self.market_is_open:
                self.market_is_open = is_open
                if is_open:
                    logger.info("Market detected as OPEN - starting real-time updates")
                    self.update_timer.start(self.config.update_interval)
                else:
                    logger.info("Market detected as CLOSED - stopping real-time updates")
                    self.update_timer.stop()

            return is_open

        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            # Default to closed if we can't determine
            return False

    def _control_updates_based_on_market(self):
        """Control chart updates based on market open/closed status."""
        is_open = self._check_market_hours()

        if is_open:
            # Market is open - enable real-time updates if we have a symbol
            if self.current_symbol and not self.update_timer.isActive():
                logger.info("Starting chart updates - market is open")
                self.update_timer.start(self.config.update_interval)
        else:
            # Market is closed - stop updates
            if self.update_timer.isActive():
                logger.info("Stopping chart updates - market is closed")
                self.update_timer.stop()

    def save_screenshot(self, filepath: str):
        """Save chart screenshot.

        Args:
            filepath: Path to save screenshot
        """
        if PYQTGRAPH_AVAILABLE:
            exporter = pg.exporters.ImageExporter(self.chart_widget.plotItem)
            exporter.export(filepath)
            logger.info(f"Chart saved to: {filepath}")