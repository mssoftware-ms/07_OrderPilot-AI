"""Chart Widget for OrderPilot-AI Trading Application."""

from collections import deque
from datetime import datetime
from decimal import Decimal

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.common.event_bus import Event, EventType, event_bus
from .candlestick_item import CandlestickItem


class ChartWidget(QWidget):
    """Widget for displaying trading charts with real-time updates."""

    def __init__(self):
        super().__init__()

        # Data storage
        self.bars_data = deque(maxlen=500)  # Store last 500 bars
        self.current_symbol = "AAPL"
        self.current_timeframe = "1min"

        # Initialize UI
        self.init_ui()

        # Setup event handlers
        self.setup_event_handlers()

    def init_ui(self):
        """Initialize the chart UI."""
        layout = QVBoxLayout(self)

        # Control panel (hidden - use main toolbar instead)
        control_layout = QHBoxLayout()

        # Symbol selector
        control_layout.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "SPY", "QQQ"])
        self.symbol_combo.setCurrentText(self.current_symbol)
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        control_layout.addWidget(self.symbol_combo)

        # Timeframe selector
        control_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1min", "5min", "15min", "1h", "1D"])
        self.timeframe_combo.setCurrentText(self.current_timeframe)
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        control_layout.addWidget(self.timeframe_combo)

        # Clear button
        self.clear_btn = QPushButton("Clear Chart")
        self.clear_btn.clicked.connect(self.clear_chart)
        control_layout.addWidget(self.clear_btn)

        control_layout.addStretch()

        # Status label
        self.status_label = QLabel("No data")
        self.status_label.setStyleSheet("color: #888;")
        control_layout.addWidget(self.status_label)

        # Create control widget but don't add to layout (controlled from main toolbar)
        self.control_widget = QWidget()
        self.control_widget.setLayout(control_layout)
        # NOTE: control_widget not added to layout to avoid duplicate toolbars

        # Chart view
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Price', color='white', size='12pt')
        self.plot_widget.setLabel('bottom', 'Time', color='white', size='12pt')
        self.plot_widget.setTitle(f'{self.current_symbol} - {self.current_timeframe}',
                                  color='white', size='14pt')

        # Create candlestick item
        self.candlestick_item = CandlestickItem()
        self.plot_widget.addItem(self.candlestick_item)

        # Volume subplot
        self.volume_plot = self.plot_widget.getPlotItem().vb.scene().addItem(pg.PlotDataItem())

        layout.addWidget(self.plot_widget)

        # Info panel
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Open: - | High: - | Low: - | Close: - | Volume: -")
        self.info_label.setStyleSheet("color: #aaa; font-family: monospace;")
        info_layout.addWidget(self.info_label)
        layout.addLayout(info_layout)

    def setup_event_handlers(self):
        """Setup event bus handlers."""
        event_bus.subscribe(EventType.MARKET_BAR, self.on_market_bar)
        event_bus.subscribe(EventType.MARKET_TICK, self.on_market_tick)

    @pyqtSlot(object)
    def on_market_bar(self, event: Event):
        """Handle market bar event."""
        try:
            bar_data = event.data

            # Check if this bar is for current symbol
            if bar_data.get('symbol') != self.current_symbol:
                return

            # Extract OHLCV data
            timestamp = bar_data.get('timestamp', datetime.now())
            if isinstance(timestamp, datetime):
                t = timestamp.timestamp()
            else:
                t = timestamp

            open_price = float(bar_data.get('open', 0))
            high = float(bar_data.get('high', 0))
            low = float(bar_data.get('low', 0))
            close = float(bar_data.get('close', 0))
            volume = float(bar_data.get('volume', 0))

            # Add to data storage
            self.bars_data.append((t, open_price, high, low, close, volume))

            # Update chart
            self.update_chart()

            # Update status
            self.status_label.setText(f"Bars: {len(self.bars_data)} | Last: {timestamp.strftime('%H:%M:%S')}")
            self.status_label.setStyleSheet("color: #0f0;")

            # Update info panel
            self.info_label.setText(
                f"O: {open_price:.2f} | H: {high:.2f} | L: {low:.2f} | "
                f"C: {close:.2f} | V: {volume:,.0f}"
            )

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)[:50]}")
            self.status_label.setStyleSheet("color: #f00;")

    @pyqtSlot(object)
    def on_market_tick(self, event: Event):
        """Handle market tick event (for real-time price updates)."""
        try:
            tick_data = event.data

            if tick_data.get('symbol') != self.current_symbol:
                return

            # Update current price indicator
            price = float(tick_data.get('price', 0))
            self.status_label.setText(f"Last tick: ${price:.2f}")

        except Exception as e:
            logger.debug(f"Error updating chart status: {e}")

    def update_chart(self):
        """Update the candlestick chart with current data."""
        if not self.bars_data:
            return

        # Prepare candlestick data
        candle_data = [
            (t, o, h, l, c)
            for t, o, h, l, c, v in self.bars_data
        ]

        # Update candlestick item
        self.candlestick_item.set_data(candle_data)

        # Auto-range to fit data
        if len(self.bars_data) > 0:
            self.plot_widget.autoRange()

    @pyqtSlot(str)
    def on_symbol_changed(self, symbol: str):
        """Handle symbol change."""
        self.current_symbol = symbol
        self.bars_data.clear()
        self.plot_widget.setTitle(f'{self.current_symbol} - {self.current_timeframe}',
                                  color='white', size='14pt')
        self.update_chart()
        self.status_label.setText(f"Switched to {symbol}")

    @pyqtSlot(str)
    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change."""
        self.current_timeframe = timeframe
        self.bars_data.clear()
        self.plot_widget.setTitle(f'{self.current_symbol} - {self.current_timeframe}',
                                  color='white', size='14pt')
        self.update_chart()
        self.status_label.setText(f"Switched to {timeframe}")

    @pyqtSlot()
    def clear_chart(self):
        """Clear all chart data."""
        self.bars_data.clear()
        self.update_chart()
        self.status_label.setText("Chart cleared")
        self.status_label.setStyleSheet("color: #888;")
        self.info_label.setText("Open: - | High: - | Low: - | Close: - | Volume: -")

    def add_test_data(self):
        """Add test data for development (can be removed in production)."""
        import random
        from datetime import timedelta

        base_time = datetime.now()
        base_price = 150.0

        for i in range(100):
            t = (base_time + timedelta(minutes=i)).timestamp()
            open_price = base_price + random.uniform(-2, 2)
            close = open_price + random.uniform(-1, 1)
            high = max(open_price, close) + random.uniform(0, 0.5)
            low = min(open_price, close) - random.uniform(0, 0.5)
            volume = random.uniform(1000, 10000)

            self.bars_data.append((t, open_price, high, low, close, volume))

        self.update_chart()
        self.status_label.setText(f"Test data loaded: {len(self.bars_data)} bars")
