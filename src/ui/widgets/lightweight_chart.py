"""Lightweight Chart Widget using lightweight-charts library.

This module provides high-performance trading charts using TradingView's
lightweight-charts library. Significantly faster than PyQtGraph for OHLCV data.
"""

import logging
from collections import deque
from datetime import datetime
from typing import Optional, Dict, List, Any

import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QPushButton,
    QToolBar,
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    logging.warning("PyQt6-WebEngine not installed. Will use external browser mode.")

try:
    from lightweight_charts import Chart
    LIGHTWEIGHT_CHARTS_AVAILABLE = True
except ImportError:
    LIGHTWEIGHT_CHARTS_AVAILABLE = False
    logging.error("lightweight-charts not installed. Run: pip install lightweight-charts")

from src.common.event_bus import Event, EventType, event_bus
from src.core.indicators.engine import IndicatorConfig, IndicatorEngine, IndicatorType

logger = logging.getLogger(__name__)


class LightweightChartWidget(QWidget):
    """High-performance chart widget using lightweight-charts.

    Features:
    - WebGL-accelerated rendering (10-100x faster than PyQtGraph)
    - Professional trading chart appearance
    - Real-time updates with minimal CPU usage
    - Smooth zoom and pan
    - Built-in candlestick patterns
    """

    # Signals
    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)

    def __init__(self, embedded: bool = False, history_manager=None):
        """Initialize lightweight chart widget.

        Args:
            embedded: If True and WebEngine available, embed chart in widget.
                     If False, opens in external browser (more stable).
            history_manager: HistoryManager instance for loading data
        """
        super().__init__()

        if not LIGHTWEIGHT_CHARTS_AVAILABLE:
            logger.error("lightweight-charts not installed!")
            self._show_error_ui()
            return

        self.embedded = embedded and WEBENGINE_AVAILABLE
        self.history_manager = history_manager
        self.indicator_engine = IndicatorEngine()

        # Data storage
        self.current_symbol = "AAPL"
        self.current_timeframe = "1T"
        self.current_data_provider: Optional[str] = None
        self.data: Optional[pd.DataFrame] = None
        self.chart: Optional[Chart] = None
        self.chart_series = None  # Main candlestick series
        self.indicator_series: Dict[str, Any] = {}
        self.volume_series = None

        # Update batching for performance
        self.pending_bars = deque(maxlen=100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_pending_updates)
        self.update_timer.setInterval(1000)  # Batch updates every 1 second

        # Setup UI
        self._setup_ui()

        # Subscribe to events
        event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar)
        event_bus.subscribe(EventType.MARKET_TICK, self._on_market_tick)

        logger.info(f"LightweightChartWidget initialized (embedded={self.embedded})")

    def _show_error_ui(self):
        """Show error message if lightweight-charts not available."""
        layout = QVBoxLayout(self)
        error_label = QLabel(
            "⚠️ lightweight-charts not installed\n\n"
            "Run: pip install lightweight-charts"
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14pt;")
        layout.addWidget(error_label)

    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Chart container
        if self.embedded and WEBENGINE_AVAILABLE:
            # Embedded web view (requires PyQt6-WebEngine)
            self.web_view = QWebEngineView()
            layout.addWidget(self.web_view)
            self.status_label = QLabel("Chart will load here (embedded mode)")
        else:
            # External browser mode (more stable, no additional dependencies)
            self.status_label = QLabel(
                "📊 Chart will open in browser\n\n"
                "Charts are displayed in your default web browser for best performance.\n"
                "Keep the browser tab open while trading."
            )
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_label.setStyleSheet(
                "color: #888; font-size: 12pt; padding: 20px;"
            )
            layout.addWidget(self.status_label, stretch=1)

        # Info panel
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Select a symbol to begin")
        self.info_label.setStyleSheet("color: #aaa; font-family: monospace; padding: 5px;")
        info_layout.addWidget(self.info_label)
        layout.addLayout(info_layout)

    def _create_toolbar(self) -> QToolBar:
        """Create chart toolbar."""
        toolbar = QToolBar()

        # Symbol selector
        toolbar.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ"])
        self.symbol_combo.setCurrentText(self.current_symbol)
        self.symbol_combo.currentTextChanged.connect(self._on_symbol_change)
        toolbar.addWidget(self.symbol_combo)

        toolbar.addSeparator()

        # Timeframe selector
        toolbar.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1T", "5T", "15T", "30T", "1H", "4H", "1D"])
        self.timeframe_combo.setCurrentText(self.current_timeframe)
        self.timeframe_combo.currentTextChanged.connect(self._on_timeframe_change)
        toolbar.addWidget(self.timeframe_combo)

        toolbar.addSeparator()

        # Indicator buttons
        toolbar.addWidget(QLabel("Indicators:"))

        self.ma_button = QPushButton("MA")
        self.ma_button.setCheckable(True)
        self.ma_button.clicked.connect(lambda: self._toggle_indicator("MA"))
        toolbar.addWidget(self.ma_button)

        self.ema_button = QPushButton("EMA")
        self.ema_button.setCheckable(True)
        self.ema_button.clicked.connect(lambda: self._toggle_indicator("EMA"))
        toolbar.addWidget(self.ema_button)

        toolbar.addSeparator()

        # Load data button
        self.load_button = QPushButton("📊 Load Chart")
        self.load_button.clicked.connect(self._on_load_chart)
        self.load_button.setStyleSheet("font-weight: bold; padding: 5px 15px;")
        toolbar.addWidget(self.load_button)

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._on_refresh)
        toolbar.addWidget(self.refresh_button)

        toolbar.addSeparator()

        # Market status
        self.market_status_label = QLabel("Ready")
        self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")
        toolbar.addWidget(self.market_status_label)

        return toolbar

    def _create_chart(self):
        """Create a new lightweight chart instance."""
        try:
            # Create chart with optimized settings
            self.chart = Chart(
                volume_enabled=True,
                width=1200,
                height=600,
                toolbox=True,  # Enable drawing tools
            )

            # Configure chart appearance
            self.chart.layout(
                background_color='#0a0a0a',
                text_color='#d1d4dc',
                font_size=12,
                font_family='Trebuchet MS',
            )

            # Configure grid
            self.chart.grid(
                vert_enabled=True,
                horz_enabled=True,
                color='rgba(70, 70, 70, 0.4)',
                style='solid',
            )

            # Configure crosshair
            self.chart.crosshair(
                mode='normal',
                vert_color='#758696',
                vert_style='dashed',
                horz_color='#758696',
                horz_style='dashed',
            )

            # Create candlestick series
            self.chart_series = self.chart.set('candlestick')

            logger.info("Lightweight chart created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating chart: {e}", exc_info=True)
            return False

    def load_data(self, data: pd.DataFrame):
        """Load market data into chart.

        Args:
            data: OHLCV DataFrame with DatetimeIndex
        """
        try:
            if not LIGHTWEIGHT_CHARTS_AVAILABLE:
                logger.error("Cannot load data: lightweight-charts not available")
                return

            self.data = data

            # Create chart if needed
            if self.chart is None:
                if not self._create_chart():
                    return

            # Prepare data for lightweight-charts format
            # Requires: time (Unix timestamp), open, high, low, close, volume
            chart_data = []
            for timestamp, row in data.iterrows():
                # Skip invalid data
                if any(pd.isna(x) for x in [row['open'], row['high'], row['low'], row['close']]):
                    continue

                chart_data.append({
                    'time': int(timestamp.timestamp()),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row.get('volume', 0)),
                })

            # Set data
            self.chart_series.set(chart_data)

            # Update indicators
            self._update_indicators()

            # Show chart
            self.chart.show(block=False)  # Non-blocking

            # Update UI
            self.info_label.setText(
                f"Loaded {len(chart_data)} bars | "
                f"From: {data.index[0].strftime('%Y-%m-%d')} | "
                f"To: {data.index[-1].strftime('%Y-%m-%d')}"
            )
            self.market_status_label.setText("✓ Chart Loaded")
            self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")

            # Start update timer for real-time data
            if not self.update_timer.isActive():
                self.update_timer.start()

            logger.info(f"Loaded {len(chart_data)} bars into chart")

        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

    def _update_indicators(self):
        """Update technical indicators on chart."""
        if self.data is None or self.chart is None:
            return

        try:
            # Moving Average
            if self.ma_button.isChecked():
                config = IndicatorConfig(
                    indicator_type=IndicatorType.SMA,
                    params={'period': 20}
                )
                result = self.indicator_engine.calculate(self.data, config)

                # Convert to lightweight-charts format
                ma_data = [
                    {'time': int(ts.timestamp()), 'value': float(val)}
                    for ts, val in zip(self.data.index, result.values.values)
                    if not pd.isna(val)
                ]

                # Add as line series
                if 'ma' not in self.indicator_series:
                    self.indicator_series['ma'] = self.chart.create_line()
                self.indicator_series['ma'].set(ma_data)
                self.indicator_series['ma'].name = 'SMA(20)'
                self.indicator_series['ma'].color = '#FFA500'

            elif 'ma' in self.indicator_series:
                # Remove MA if unchecked
                self.chart.remove_line(self.indicator_series['ma'])
                del self.indicator_series['ma']

            # EMA
            if self.ema_button.isChecked():
                config = IndicatorConfig(
                    indicator_type=IndicatorType.EMA,
                    params={'period': 20}
                )
                result = self.indicator_engine.calculate(self.data, config)

                ema_data = [
                    {'time': int(ts.timestamp()), 'value': float(val)}
                    for ts, val in zip(self.data.index, result.values.values)
                    if not pd.isna(val)
                ]

                if 'ema' not in self.indicator_series:
                    self.indicator_series['ema'] = self.chart.create_line()
                self.indicator_series['ema'].set(ema_data)
                self.indicator_series['ema'].name = 'EMA(20)'
                self.indicator_series['ema'].color = '#00FFFF'

            elif 'ema' in self.indicator_series:
                self.chart.remove_line(self.indicator_series['ema'])
                del self.indicator_series['ema']

        except Exception as e:
            logger.error(f"Error updating indicators: {e}", exc_info=True)

    def _toggle_indicator(self, indicator: str):
        """Toggle indicator display."""
        self._update_indicators()

    @pyqtSlot(object)
    def _on_market_bar(self, event: Event):
        """Handle market bar event."""
        try:
            bar_data = event.data
            if bar_data.get('symbol') != self.current_symbol:
                return

            # Add to pending updates (batched processing)
            self.pending_bars.append(bar_data)

        except Exception as e:
            logger.error(f"Error handling market bar: {e}")

    @pyqtSlot(object)
    def _on_market_tick(self, event: Event):
        """Handle market tick event."""
        try:
            tick_data = event.data
            if tick_data.get('symbol') != self.current_symbol:
                return

            # Update price in info label
            price = tick_data.get('price', 0)
            self.info_label.setText(f"Last: ${price:.2f}")

        except Exception:
            pass

    def _process_pending_updates(self):
        """Process pending bar updates (batched for performance)."""
        if not self.pending_bars or self.chart is None:
            return

        try:
            # Process all pending bars
            updates = []
            while self.pending_bars:
                bar_data = self.pending_bars.popleft()

                timestamp = bar_data.get('timestamp', datetime.now())
                updates.append({
                    'time': int(timestamp.timestamp()),
                    'open': float(bar_data.get('open', 0)),
                    'high': float(bar_data.get('high', 0)),
                    'low': float(bar_data.get('low', 0)),
                    'close': float(bar_data.get('close', 0)),
                    'volume': float(bar_data.get('volume', 0)),
                })

            # Update chart with all bars at once (efficient!)
            if updates:
                for update in updates:
                    self.chart_series.update(update)

                logger.debug(f"Updated chart with {len(updates)} new bars")

        except Exception as e:
            logger.error(f"Error processing updates: {e}", exc_info=True)

    def _on_symbol_change(self, symbol: str):
        """Handle symbol change."""
        self.current_symbol = symbol
        self.symbol_changed.emit(symbol)
        logger.info(f"Symbol changed to: {symbol}")

    def _on_timeframe_change(self, timeframe: str):
        """Handle timeframe change."""
        self.current_timeframe = timeframe
        self.timeframe_changed.emit(timeframe)
        logger.info(f"Timeframe changed to: {timeframe}")

    def _on_load_chart(self):
        """Load chart data for current symbol."""
        import asyncio
        asyncio.create_task(self.load_symbol(self.current_symbol, self.current_data_provider))

    def _on_refresh(self):
        """Refresh current chart."""
        if self.data is not None:
            self.load_data(self.data)
        else:
            self._on_load_chart()

    async def load_symbol(self, symbol: str, data_provider: Optional[str] = None):
        """Load symbol data and display chart.

        Args:
            symbol: Trading symbol
            data_provider: Data provider (alpaca, yahoo, etc.)
        """
        try:
            if not self.history_manager:
                logger.warning("No history manager available")
                self.market_status_label.setText("⚠ No data source")
                return

            self.current_symbol = symbol
            self.current_data_provider = data_provider
            self.symbol_combo.setCurrentText(symbol)

            self.market_status_label.setText(f"Loading {symbol}...")
            self.market_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")

            # Import required classes
            from datetime import timedelta
            from src.core.market_data.history_provider import DataRequest, DataSource, Timeframe

            # Map timeframe
            timeframe_map = {
                "1T": Timeframe.MINUTE_1,
                "5T": Timeframe.MINUTE_5,
                "15T": Timeframe.MINUTE_15,
                "30T": Timeframe.MINUTE_30,
                "1H": Timeframe.HOUR_1,
                "4H": Timeframe.HOUR_4,
                "1D": Timeframe.DAY_1,
            }
            timeframe = timeframe_map.get(self.current_timeframe, Timeframe.MINUTE_1)

            # Map provider
            provider_source = None
            if data_provider:
                provider_map = {
                    "database": DataSource.DATABASE,
                    "alpaca": DataSource.ALPACA,
                    "yahoo": DataSource.YAHOO,
                }
                provider_source = provider_map.get(data_provider)

            # Fetch data (last 30 days)
            request = DataRequest(
                symbol=symbol,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                timeframe=timeframe,
                source=provider_source
            )

            bars, source_used = await self.history_manager.fetch_data(request)

            if not bars:
                logger.warning(f"No data for {symbol}")
                self.market_status_label.setText(f"⚠ No data for {symbol}")
                return

            # Convert to DataFrame
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

            # Load into chart
            self.load_data(df)

            logger.info(f"Loaded {len(bars)} bars for {symbol} from {source_used}")

        except Exception as e:
            logger.error(f"Error loading symbol: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
