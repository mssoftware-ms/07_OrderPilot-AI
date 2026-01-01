"""Embedded TradingView Lightweight Charts Widget.

This module provides a fully embedded trading chart using TradingView's Lightweight Charts
library rendered directly in a Qt WebEngine view (Chromium-based).

REFACTORED: Extracted mixins to meet 600 LOC limit.
- ToolbarMixin: Toolbar creation
- IndicatorMixin: Indicator calculation and updates
- StreamingMixin: Live streaming and market events
- DataLoadingMixin: Data loading (load_data, load_symbol)
- ChartStateMixin: State management (visible range, pane layout)
"""

import logging
from collections import deque
from typing import Optional, Dict, List

import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtCore import QObject
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    logging.warning("PyQt6-WebEngine not installed. Chart widget will not work.")

from src.chart_marking import ChartMarkingMixin
from src.common.event_bus import EventType, event_bus
from src.core.indicators.engine import IndicatorEngine

from .chart_mixins import (
    ToolbarMixin,
    IndicatorMixin,
    StreamingMixin,
    DataLoadingMixin,
    ChartStateMixin,
    BotOverlayMixin,
)
from .chart_js_template import get_chart_html_template

logger = logging.getLogger(__name__)


class ChartBridge(QObject):
    """Bridge object for JavaScript to Python communication.

    Allows JavaScript in the chart to call Python methods, e.g., when
    a stop line is dragged to a new position or crosshair moves.
    """

    # Signal emitted when a stop line is moved
    stop_line_moved = pyqtSignal(str, float)  # (line_id, new_price)
    # Signal emitted when crosshair moves (for cursor position tracking)
    crosshair_moved = pyqtSignal(float, float)  # (time, price)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Store last known crosshair position
        self._last_crosshair_time = None
        self._last_crosshair_price = None

    @pyqtSlot(str, float)
    def onStopLineMoved(self, line_id: str, new_price: float):
        """Called from JavaScript when a stop line is dragged.

        Args:
            line_id: ID of the line ("initial_stop", "trailing_stop", "entry_line")
            new_price: New price level after drag
        """
        logger.info(f"[ChartBridge] Stop line moved: {line_id} -> {new_price:.2f}")
        self.stop_line_moved.emit(line_id, new_price)

    @pyqtSlot(float, float)
    def onCrosshairMove(self, time: float, price: float):
        """Called from JavaScript when crosshair moves.

        Args:
            time: Unix timestamp of crosshair position
            price: Price at crosshair position
        """
        self._last_crosshair_time = time
        self._last_crosshair_price = price
        self.crosshair_moved.emit(time, price)

    def get_crosshair_position(self) -> tuple[float | None, float | None]:
        """Get the last known crosshair position.

        Returns:
            Tuple of (time, price) or (None, None) if not available
        """
        return (self._last_crosshair_time, self._last_crosshair_price)


class EmbeddedTradingViewChart(
    ChartMarkingMixin,
    BotOverlayMixin,
    ToolbarMixin,
    IndicatorMixin,
    StreamingMixin,
    DataLoadingMixin,
    ChartStateMixin,
    QWidget
):
    """Embedded TradingView Lightweight Charts widget.

    Features:
    - Fully embedded in Qt application (no external windows)
    - Chromium-based WebEngine rendering
    - Professional TradingView appearance
    - Real-time updates
    - Technical indicators support
    """

    # Signals
    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)
    data_loaded = pyqtSignal()
    indicator_toggled = pyqtSignal(str, bool, dict)
    # Thread-safe signals for streaming updates (called from background threads)
    _tick_received = pyqtSignal(object)
    _bar_received = pyqtSignal(object)
    # Chart trading signals - emitted when user drags lines in chart
    stop_line_moved = pyqtSignal(str, float)  # (line_id, new_price)
    # Candle closed signal - emitted when a new candle starts (previous candle closed)
    candle_closed = pyqtSignal(float, float, float, float, float)  # (prev_open, prev_high, prev_low, prev_close, new_open)
    # Tick price signal - emitted on every valid tick for real-time P&L updates
    tick_price_updated = pyqtSignal(float)  # (current_price)

    def __init__(self, history_manager=None):
        """Initialize embedded chart widget.

        Args:
            history_manager: HistoryManager instance for loading data
        """
        super().__init__()

        if not WEBENGINE_AVAILABLE:
            logger.error("PyQt6-WebEngine not installed!")
            self._show_error_ui()
            return

        self.history_manager = history_manager
        self.indicator_engine = IndicatorEngine()

        # Data storage
        self.current_symbol = "AAPL"
        self.current_timeframe = "1T"
        self.current_period = "1D"
        self.current_data_provider: Optional[str] = None
        self.data: Optional[pd.DataFrame] = None
        self.volume_data: list = []
        self.active_indicators: Dict[str, bool] = {}
        self.active_indicator_params: Dict[str, dict] = {}
        self.live_streaming_enabled = False

        # State restoration queue
        self._pending_state_restoration = None
        self._indicators_loaded = False
        self._restoring_state = False  # Flag to prevent fitContent() during restoration
        self._skip_fit_content = False  # Flag to skip fitContent() on data load

        # Page load state
        self.page_loaded = False
        self.chart_initialized = False
        self.pending_data_load: Optional[pd.DataFrame] = None
        self.pending_js_commands: List[str] = []
        self.chart_ready_timer: Optional[QTimer] = None

        # Update batching for performance
        self.pending_bars = deque(maxlen=100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_pending_updates)
        self.update_timer.setInterval(1000)

        # Indicator update lock to prevent race conditions
        self._updating_indicators = False

        # Initialize bot overlay (from BotOverlayMixin)
        self._init_bot_overlay()

        # Initialize chart marking (from ChartMarkingMixin)
        self._init_chart_marking()

        # Setup UI
        self._setup_ui()

        # Connect thread-safe signals to handlers (runs in main thread)
        self._tick_received.connect(self._handle_tick_main_thread)
        self._bar_received.connect(self._handle_bar_main_thread)

        # Subscribe to events - these emit signals for thread safety
        event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar_event)
        event_bus.subscribe(EventType.MARKET_TICK, self._on_market_tick_event)
        event_bus.subscribe(EventType.MARKET_DATA_TICK, self._on_market_tick_event)

        logger.info("EmbeddedTradingViewChart initialized")

    def _on_market_tick_event(self, event):
        """Event bus callback - emit signal for thread-safe handling."""
        # This may be called from background thread, so emit signal
        self._tick_received.emit(event)

    def _on_market_bar_event(self, event):
        """Event bus callback - emit signal for thread-safe handling."""
        # This may be called from background thread, so emit signal
        self._bar_received.emit(event)

    @pyqtSlot(object)
    def _handle_tick_main_thread(self, event):
        """Handle tick in main thread (thread-safe)."""
        self._on_market_tick(event)

    @pyqtSlot(object)
    def _handle_bar_main_thread(self, event):
        """Handle bar in main thread (thread-safe)."""
        self._on_market_bar(event)

    def _show_error_ui(self):
        """Show error message if WebEngine not available."""
        layout = QVBoxLayout(self)
        error_label = QLabel(
            "⚠️ PyQt6-WebEngine not installed\n\n"
            "Run: pip install PyQt6-WebEngine"
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14pt;")
        layout.addWidget(error_label)

    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar (from ToolbarMixin) - Two rows
        toolbar1, toolbar2 = self._create_toolbar()
        layout.addWidget(toolbar1)
        layout.addWidget(toolbar2)

        # Web view for chart
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_page_loaded)
        self.web_view.setHtml(get_chart_html_template())
        layout.addWidget(self.web_view, stretch=1)

        # Setup WebChannel for JavaScript to Python communication
        self._chart_bridge = ChartBridge(self)
        self._chart_bridge.stop_line_moved.connect(self._on_bridge_stop_line_moved)
        self._web_channel = QWebChannel(self.web_view.page())
        self._web_channel.registerObject("pyBridge", self._chart_bridge)
        self.web_view.page().setWebChannel(self._web_channel)

        # Info panel
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Select a symbol to begin")
        self.info_label.setStyleSheet("color: #aaa; font-family: monospace; padding: 5px;")
        info_layout.addWidget(self.info_label)
        layout.addLayout(info_layout)

        # Setup context menu for chart markings
        self._setup_context_menu()

    def _setup_context_menu(self):
        """Setup context menu for chart marking operations."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtCore import Qt

        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.web_view.customContextMenuRequested.connect(self._show_marking_context_menu)

    def _show_marking_context_menu(self, pos):
        """Show context menu for chart markings."""
        from PyQt6.QtWidgets import QMenu, QInputDialog
        from PyQt6.QtGui import QAction
        import time

        menu = QMenu(self)

        # Check for zones at current price (for zone-specific options)
        zones_at_price = []
        if hasattr(self, "_last_price") and self._last_price is not None:
            zones_at_price = self._zones.get_zones_at_price(self._last_price)

        # If zones found at this price, show zone management options first
        if zones_at_price:
            zone_mgmt_menu = menu.addMenu(f"📍 Zones at Price ({len(zones_at_price)})")

            for zone in zones_at_price:
                zone_label = zone.label or zone.id
                zone_type_icon = {
                    "support": "🟢",
                    "resistance": "🔴",
                    "demand": "🟢",
                    "supply": "🔴",
                }.get(zone.zone_type.value, "📊")

                # Submenu for this zone
                zone_submenu = zone_mgmt_menu.addMenu(f"{zone_type_icon} {zone_label}")

                edit_action = QAction("✏️ Edit Zone...", self)
                edit_action.triggered.connect(lambda checked, z=zone: self._edit_zone(z))
                zone_submenu.addAction(edit_action)

                extend_action = QAction("➡️ Extend to Now", self)
                extend_action.triggered.connect(lambda checked, z=zone: self._extend_zone_to_now(z))
                zone_submenu.addAction(extend_action)

                zone_submenu.addSeparator()

                delete_action = QAction("🗑️ Delete Zone", self)
                delete_action.triggered.connect(lambda checked, z=zone: self._delete_zone(z))
                zone_submenu.addAction(delete_action)

            menu.addSeparator()

        # Entry Markers submenu
        entry_menu = menu.addMenu("Add Entry Marker")

        long_action = QAction("Long Entry (Arrow Up)", self)
        long_action.triggered.connect(lambda: self._add_test_entry_marker("long"))
        entry_menu.addAction(long_action)

        short_action = QAction("Short Entry (Arrow Down)", self)
        short_action.triggered.connect(lambda: self._add_test_entry_marker("short"))
        entry_menu.addAction(short_action)

        # Zones submenu
        zone_menu = menu.addMenu("Add Zone")

        support_action = QAction("🟢 Support Zone", self)
        support_action.triggered.connect(lambda: self._add_test_zone("support"))
        zone_menu.addAction(support_action)

        resistance_action = QAction("🔴 Resistance Zone", self)
        resistance_action.triggered.connect(lambda: self._add_test_zone("resistance"))
        zone_menu.addAction(resistance_action)

        zone_menu.addSeparator()

        demand_action = QAction("🟢 Demand Zone (Bullish)", self)
        demand_action.triggered.connect(lambda: self._add_test_zone("demand"))
        zone_menu.addAction(demand_action)

        supply_action = QAction("🔴 Supply Zone (Bearish)", self)
        supply_action.triggered.connect(lambda: self._add_test_zone("supply"))
        zone_menu.addAction(supply_action)

        # Structure Markers submenu
        structure_menu = menu.addMenu("Add Structure Break")

        bos_bull_action = QAction("BoS Bullish", self)
        bos_bull_action.triggered.connect(lambda: self._add_test_structure("bos", True))
        structure_menu.addAction(bos_bull_action)

        bos_bear_action = QAction("BoS Bearish", self)
        bos_bear_action.triggered.connect(lambda: self._add_test_structure("bos", False))
        structure_menu.addAction(bos_bear_action)

        choch_bull_action = QAction("CHoCH Bullish", self)
        choch_bull_action.triggered.connect(lambda: self._add_test_structure("choch", True))
        structure_menu.addAction(choch_bull_action)

        choch_bear_action = QAction("CHoCH Bearish", self)
        choch_bear_action.triggered.connect(lambda: self._add_test_structure("choch", False))
        structure_menu.addAction(choch_bear_action)

        structure_menu.addSeparator()

        msb_bull_action = QAction("⬆️ MSB Bullish", self)
        msb_bull_action.triggered.connect(lambda: self._add_test_structure("msb", True))
        structure_menu.addAction(msb_bull_action)

        msb_bear_action = QAction("⬇️ MSB Bearish", self)
        msb_bear_action.triggered.connect(lambda: self._add_test_structure("msb", False))
        structure_menu.addAction(msb_bear_action)

        # Lines submenu (Stop Loss, Take Profit, Entry)
        lines_menu = menu.addMenu("📏 Add Line")

        sl_long_action = QAction("🔴 Stop Loss (Long Position)", self)
        sl_long_action.triggered.connect(lambda: self._add_test_line("sl", True))
        lines_menu.addAction(sl_long_action)

        sl_short_action = QAction("🔴 Stop Loss (Short Position)", self)
        sl_short_action.triggered.connect(lambda: self._add_test_line("sl", False))
        lines_menu.addAction(sl_short_action)

        lines_menu.addSeparator()

        tp_long_action = QAction("🟢 Take Profit (Long Position)", self)
        tp_long_action.triggered.connect(lambda: self._add_test_line("tp", True))
        lines_menu.addAction(tp_long_action)

        tp_short_action = QAction("🟢 Take Profit (Short Position)", self)
        tp_short_action.triggered.connect(lambda: self._add_test_line("tp", False))
        lines_menu.addAction(tp_short_action)

        lines_menu.addSeparator()

        entry_long_action = QAction("🔵 Entry Line (Long)", self)
        entry_long_action.triggered.connect(lambda: self._add_test_line("entry", True))
        lines_menu.addAction(entry_long_action)

        entry_short_action = QAction("🔵 Entry Line (Short)", self)
        entry_short_action.triggered.connect(lambda: self._add_test_line("entry", False))
        lines_menu.addAction(entry_short_action)

        lines_menu.addSeparator()

        trailing_action = QAction("🟡 Trailing Stop", self)
        trailing_action.triggered.connect(lambda: self._add_test_line("trailing", True))
        lines_menu.addAction(trailing_action)

        menu.addSeparator()

        # Clear actions
        clear_markers_action = QAction("Clear All Markers", self)
        clear_markers_action.triggered.connect(self._clear_all_markers)
        menu.addAction(clear_markers_action)

        clear_zones_action = QAction("Clear All Zones", self)
        clear_zones_action.triggered.connect(self.clear_zones)
        menu.addAction(clear_zones_action)

        clear_lines_action = QAction("Clear All Lines", self)
        clear_lines_action.triggered.connect(self.clear_stop_loss_lines)
        menu.addAction(clear_lines_action)

        clear_all_action = QAction("Clear Everything", self)
        clear_all_action.triggered.connect(self._clear_all_markings)
        menu.addAction(clear_all_action)

        menu.exec(self.web_view.mapToGlobal(pos))

    def _add_test_entry_marker(self, direction: str):
        """Add a test entry marker at the cursor position.

        Uses the crosshair position if available, otherwise falls back to last candle.
        """
        # First try to get position from crosshair (cursor position)
        crosshair_time, crosshair_price = None, None
        if hasattr(self, "_chart_bridge") and self._chart_bridge is not None:
            crosshair_time, crosshair_price = self._chart_bridge.get_crosshair_position()

        if crosshair_time is not None and crosshair_price is not None:
            # Use crosshair position (cursor position)
            timestamp = int(crosshair_time)
            price = crosshair_price
            logger.info(f"Using crosshair position: time={timestamp}, price={price}")
        else:
            # Fallback: use last candle position
            if not hasattr(self, "_last_price") or self._last_price is None:
                logger.warning("No price data available for marker")
                return

            # Use timestamp from last candle in data
            if self.data is not None and len(self.data) > 0:
                last_row = self.data.iloc[-1]
                if 'time' in self.data.columns:
                    timestamp = int(last_row['time'])
                elif hasattr(last_row.name, 'timestamp'):
                    timestamp = int(last_row.name.timestamp())
                else:
                    timestamp = getattr(self, '_current_candle_time', None)
                    if timestamp is None:
                        import time
                        timestamp = int(time.time())
            else:
                import time
                timestamp = int(time.time())

            price = self._last_price
            logger.info(f"Using last candle position: time={timestamp}, price={price}")

        text = f"{direction.upper()} Entry"

        if direction == "long":
            self.add_long_entry(timestamp, price, text)
        else:
            self.add_short_entry(timestamp, price, text)

        logger.info(f"Added {direction} entry marker at {price:.2f}, timestamp={timestamp}")

    def _add_test_zone(self, zone_type: str):
        """Add a test zone around cursor position.

        Uses the crosshair position if available, otherwise falls back to last candle.

        Args:
            zone_type: 'support', 'resistance', 'demand', or 'supply'
        """
        # First try to get position from crosshair (cursor position)
        crosshair_time, crosshair_price = None, None
        if hasattr(self, "_chart_bridge") and self._chart_bridge is not None:
            crosshair_time, crosshair_price = self._chart_bridge.get_crosshair_position()

        if crosshair_time is not None and crosshair_price is not None:
            # Use crosshair position as the center of the zone
            price = crosshair_price
            end_time = int(crosshair_time)
            # Zone extends 10 candles before cursor
            if self.data is not None and len(self.data) > 1:
                candle_duration = int(self.data['time'].iloc[1] - self.data['time'].iloc[0])
                start_time = end_time - (candle_duration * 10)
            else:
                start_time = end_time - 3600  # Default 1 hour
            logger.info(f"Using crosshair position for zone: time={end_time}, price={price}")
        else:
            # Fallback: use last candle position
            if not hasattr(self, "_last_price") or self._last_price is None:
                logger.warning("No price data available for zone")
                return

            # Use timestamps from chart data
            if self.data is not None and len(self.data) > 0:
                if 'time' in self.data.columns:
                    end_time = int(self.data['time'].iloc[-1])
                    num_candles = min(20, len(self.data))
                    start_time = int(self.data['time'].iloc[-num_candles])
                else:
                    import time
                    end_time = int(time.time())
                    start_time = end_time - 3600
            else:
                import time
                end_time = int(time.time())
                start_time = end_time - 3600

            price = self._last_price
            logger.info(f"Using last candle position for zone: time={end_time}, price={price}")

        # Create zone around price (1% range)
        zone_height = price * 0.01
        top = price + zone_height / 2
        bottom = price - zone_height / 2

        if zone_type == "support":
            self.add_support_zone(start_time, end_time, top, bottom, "Support")
        elif zone_type == "resistance":
            self.add_resistance_zone(start_time, end_time, top, bottom, "Resistance")
        elif zone_type == "demand":
            self.add_demand_zone(start_time, end_time, top, bottom, "Demand")
        elif zone_type == "supply":
            self.add_supply_zone(start_time, end_time, top, bottom, "Supply")

        logger.info(f"Added {zone_type} zone: {bottom:.2f} - {top:.2f}")

    def _add_test_structure(self, break_type: str, is_bullish: bool):
        """Add a test structure break marker at cursor position.

        Uses the crosshair position if available, otherwise falls back to last candle.

        Args:
            break_type: 'bos', 'choch', or 'msb'
            is_bullish: True for bullish, False for bearish
        """
        # First try to get position from crosshair (cursor position)
        crosshair_time, crosshair_price = None, None
        if hasattr(self, "_chart_bridge") and self._chart_bridge is not None:
            crosshair_time, crosshair_price = self._chart_bridge.get_crosshair_position()

        if crosshair_time is not None and crosshair_price is not None:
            # Use crosshair position (cursor position)
            timestamp = int(crosshair_time)
            price = crosshair_price
            logger.info(f"Using crosshair position for structure: time={timestamp}, price={price}")
        else:
            # Fallback: use last candle position
            if not hasattr(self, "_last_price") or self._last_price is None:
                logger.warning("No price data available for structure marker")
                return

            if self.data is not None and len(self.data) > 0:
                if 'time' in self.data.columns:
                    timestamp = int(self.data['time'].iloc[-1])
                elif hasattr(self.data.index[-1], 'timestamp'):
                    timestamp = int(self.data.index[-1].timestamp())
                else:
                    timestamp = getattr(self, '_current_candle_time', None)
                    if timestamp is None:
                        import time
                        timestamp = int(time.time())
            else:
                import time
                timestamp = int(time.time())

            price = self._last_price
            logger.info(f"Using last candle position for structure: time={timestamp}, price={price}")

        if break_type == "bos":
            self.add_bos(timestamp, price, is_bullish)
        elif break_type == "choch":
            self.add_choch(timestamp, price, is_bullish)
        elif break_type == "msb":
            self.add_msb(timestamp, price, is_bullish)

        direction = "bullish" if is_bullish else "bearish"
        logger.info(f"Added {break_type.upper()} ({direction}) at {price:.2f}, timestamp={timestamp}")

    def _add_test_line(self, line_type: str, is_long: bool):
        """Add a test line (SL, TP, Entry, or Trailing).

        Args:
            line_type: 'sl', 'tp', 'entry', or 'trailing'
            is_long: True for long position, False for short
        """
        import time
        if not hasattr(self, "_last_price") or self._last_price is None:
            logger.warning("No price data available for line")
            return

        price = self._last_price
        line_id = f"{line_type}_{int(time.time()*1000)}"

        # Calculate entry price (simulated: current price as entry)
        entry_price = price

        # Calculate line price based on type and direction
        offset = price * 0.02  # 2% offset

        if line_type == "sl":
            # Stop loss: below entry for long, above for short
            if is_long:
                line_price = price - offset
            else:
                line_price = price + offset
            self.add_stop_loss_line(
                line_id=line_id,
                price=line_price,
                entry_price=entry_price,
                is_long=is_long,
                label=f"SL @ {line_price:.2f}",
                show_risk=True
            )
            logger.info(f"Added SL line at {line_price:.2f} for {'long' if is_long else 'short'}")

        elif line_type == "tp":
            # Take profit: above entry for long, below for short
            if is_long:
                line_price = price + offset * 2  # 2:1 R:R
            else:
                line_price = price - offset * 2
            self.add_take_profit_line(
                line_id=line_id,
                price=line_price,
                entry_price=entry_price,
                is_long=is_long,
                label=f"TP @ {line_price:.2f}"
            )
            logger.info(f"Added TP line at {line_price:.2f} for {'long' if is_long else 'short'}")

        elif line_type == "entry":
            self.add_entry_line(
                line_id=line_id,
                price=entry_price,
                is_long=is_long,
                label=f"Entry @ {entry_price:.2f}"
            )
            logger.info(f"Added Entry line at {entry_price:.2f} for {'long' if is_long else 'short'}")

        elif line_type == "trailing":
            # Trailing stop: similar to SL but labeled differently
            if is_long:
                line_price = price - offset * 0.5  # Tighter than initial SL
            else:
                line_price = price + offset * 0.5
            self.add_trailing_stop_line(
                line_id=line_id,
                price=line_price,
                entry_price=entry_price,
                is_long=is_long,
                label=f"Trail @ {line_price:.2f}"
            )
            logger.info(f"Added Trailing Stop at {line_price:.2f}")

    def _clear_all_markers(self):
        """Clear all entry and structure markers."""
        self.clear_entry_markers()
        self.clear_structure_breaks()
        logger.info("Cleared all markers")

    def _clear_all_markings(self):
        """Clear all chart markings."""
        self._clear_all_markers()
        self.clear_zones()
        self.clear_stop_loss_lines()
        logger.info("Cleared all chart markings")

    # =========================================================================
    # Zone Management (Edit/Delete)
    # =========================================================================

    def _edit_zone(self, zone):
        """Open the zone edit dialog.

        Args:
            zone: Zone object to edit
        """
        from src.ui.dialogs.zone_edit_dialog import ZoneEditDialog
        from src.chart_marking.models import ZoneType

        dialog = ZoneEditDialog(zone, self)
        result = dialog.exec()

        if result == 2:  # Delete requested
            self.remove_zone(zone.id)
            logger.info(f"Zone '{zone.label or zone.id}' deleted via edit dialog")
        elif result == 1:  # Save requested (QDialog.Accepted)
            if dialog.has_changes():
                values = dialog.get_values()

                # Update zone properties
                self._zones.update(
                    zone.id,
                    top_price=values["top_price"],
                    bottom_price=values["bottom_price"],
                )

                # Update label if changed
                if values["label"] != zone.label:
                    zone.label = values["label"]

                # Update zone type if changed
                if values["zone_type"] != zone.zone_type.value:
                    zone.zone_type = ZoneType(values["zone_type"])

                # Trigger chart update
                self._on_zones_changed()
                logger.info(f"Zone '{zone.label or zone.id}' updated")

    def _extend_zone_to_now(self, zone):
        """Extend a zone's end time to the current time.

        Args:
            zone: Zone object to extend
        """
        import time
        new_end_time = int(time.time())
        success = self.extend_zone(zone.id, new_end_time)
        if success:
            logger.info(f"Zone '{zone.label or zone.id}' extended to now")

    def _delete_zone(self, zone):
        """Delete a zone after confirmation.

        Args:
            zone: Zone object to delete
        """
        from PyQt6.QtWidgets import QMessageBox

        zone_label = zone.label or zone.id
        reply = QMessageBox.question(
            self, "Delete Zone",
            f"Are you sure you want to delete zone '{zone_label}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.remove_zone(zone.id)
            logger.info(f"Zone '{zone_label}' deleted")

    def _execute_js(self, script: str):
        """Execute JavaScript in the web view, queueing until chart is ready."""
        if self.page_loaded and self.chart_initialized:
            if 'Indicator' in script or 'Panel' in script or 'createPanel' in script:
                logger.info(f"🔧 Executing JS (indicator): {script[:100]}...")
            self.web_view.page().runJavaScript(script)
        else:
            self.pending_js_commands.append(script)
            if not self.page_loaded:
                logger.warning(f"❌ Page not loaded yet, queueing JS: {script[:50]}...")
            else:
                logger.warning(f"❌ Chart not initialized yet, queueing JS: {script[:50]}...")

    def zoom_to_fit_all(self):
        """Zoom to full data range and normalize pane heights.

        - Fits time + price scale using chartAPI.fitContent()
        - Rescales pane stretch factors so the price pane stays dominant
        """
        # Snapshot current view for undo
        self._execute_js("window.chartAPI.rememberViewState();")

        # Always attempt a fit (queued if not ready)
        def _do_fit():
            self._execute_js("window.chartAPI.fitContent();")

        if not (self.page_loaded and self.chart_initialized):
            logger.info("Zoom-to-fit queued: chart not ready yet")
            _do_fit()
            return

        def _apply_layout(layout: dict):
            try:
                layout = layout or {}
                indicator_ids = [k for k in layout.keys() if k != "price"]

                if indicator_ids:
                    # Keep price pane dominant, indicators equal + reasonable height
                    price_weight = 5
                    indicator_weight = 1
                    new_layout = {"price": price_weight}
                    for pid in indicator_ids:
                        new_layout[pid] = indicator_weight
                    self.set_pane_layout(new_layout)
                else:
                    # Ensure at least a healthy price pane height
                    self.set_pane_layout({"price": 5})
            finally:
                _do_fit()

        # Fetch current panes to know which indicator panes exist
        self.get_pane_layout(_apply_layout)

    def zoom_back_to_previous_view(self) -> bool:
        """Restore the previous zoom/layout state (one-step undo).

        Returns:
            True if a previous state existed and was applied, else False.
        """
        if not (self.page_loaded and self.chart_initialized):
            logger.info("Zoom-back skipped: chart not ready")
            return False

        def _on_result(success):
            logger.info("Zoom-back executed, success=%s", success)

        self.web_view.page().runJavaScript("window.chartAPI.restoreLastView();", _on_result)
        # Fire-and-forget; assume success if state existed
        return True

    def _flush_pending_js(self):
        """Run any JS commands that were queued before chart initialization completed."""
        if not (self.page_loaded and self.chart_initialized):
            return
        while self.pending_js_commands:
            script = self.pending_js_commands.pop(0)
            self.web_view.page().runJavaScript(script)

    def _on_page_loaded(self, success: bool):
        """Handle page load completion."""
        if success:
            self.page_loaded = True
            logger.info("Chart page loaded successfully")
            self._start_chart_ready_poll()
        else:
            logger.error("Chart page failed to load")

    def _start_chart_ready_poll(self):
        """Poll inside the WebEngine until window.chartAPI exists."""
        if self.chart_ready_timer:
            self.chart_ready_timer.stop()

        self.chart_ready_timer = QTimer(self)
        self.chart_ready_timer.setInterval(150)
        self.chart_ready_timer.timeout.connect(self._poll_chart_ready)
        self.chart_ready_timer.start()

    def _poll_chart_ready(self):
        if not self.page_loaded:
            return

        self.web_view.page().runJavaScript(
            "typeof window.chartAPI !== 'undefined' && typeof window.chartAPI.setData === 'function';",
            self._on_chart_ready_result
        )

    def _on_chart_ready_result(self, ready: bool):
        if not ready:
            return

        if self.chart_ready_timer:
            self.chart_ready_timer.stop()
            self.chart_ready_timer = None

        self.chart_initialized = True
        logger.info("chartAPI is ready")

        self._flush_pending_js()
        if self.pending_data_load is not None:
            logger.info("Loading pending data after chart initialization")
            self.load_data(self.pending_data_load)
            self.pending_data_load = None

        if hasattr(self, '_pending_indicator_update') and self._pending_indicator_update:
            logger.info("Updating pending indicators after chart initialization")
            self._pending_indicator_update = False
            self._update_indicators()

    def _on_bridge_stop_line_moved(self, line_id: str, new_price: float):
        """Handle stop line moved event from JavaScript bridge.

        Re-emits the signal so it can be caught by the chart window.
        """
        logger.info(f"Chart line moved: {line_id} -> {new_price:.4f}")
        self.stop_line_moved.emit(line_id, new_price)
