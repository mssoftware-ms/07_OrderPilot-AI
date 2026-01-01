"""Toolbar Mixin for EmbeddedTradingViewChart.

Contains toolbar creation methods.
"""

import logging

from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QMenu,
    QPushButton,
    QToolBar,
)
from PyQt6.QtGui import QAction

logger = logging.getLogger(__name__)


class ToolbarMixin:
    """Mixin providing toolbar functionality for EmbeddedTradingViewChart."""

    def _create_toolbar(self) -> tuple[QToolBar, QToolBar]:
        """Create chart toolbar (two rows).

        Returns:
            Tuple of (toolbar1, toolbar2) for two-row layout
        """
        # ========== ROW 1: Symbol, Timeframe, Period, Indicators, Actions ==========
        toolbar1 = QToolBar()

        # Symbol selector
        toolbar1.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        # Add crypto symbols with separator
        self.symbol_combo.addItems([
            "BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD",  # Crypto
            "───────",  # Visual separator
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ"  # Stocks
        ])
        self.symbol_combo.setCurrentText(self.current_symbol)
        self.symbol_combo.currentTextChanged.connect(self._on_symbol_change)
        toolbar1.addWidget(self.symbol_combo)

        toolbar1.addSeparator()

        # Candle size selector (renamed from Zeitrahmen to Kerzen)
        toolbar1.addWidget(QLabel("Kerzen:"))
        self.timeframe_combo = QComboBox()
        # Add items with display labels and internal values
        timeframes = [
            ("1 Minute", "1T"),
            ("5 Minuten", "5T"),
            ("15 Minuten", "15T"),
            ("30 Minuten", "30T"),
            ("1 Stunde", "1H"),
            ("4 Stunden", "4H"),
            ("1 Tag", "1D")
        ]
        for display, value in timeframes:
            self.timeframe_combo.addItem(display, value)

        # Set current based on internal value
        index = self.timeframe_combo.findData(self.current_timeframe)
        if index >= 0:
            self.timeframe_combo.setCurrentIndex(index)

        self.timeframe_combo.currentIndexChanged.connect(
            lambda idx: self._on_timeframe_change(self.timeframe_combo.itemData(idx))
        )
        toolbar1.addWidget(self.timeframe_combo)

        toolbar1.addSeparator()

        # Time period selector (how far back to load)
        toolbar1.addWidget(QLabel("Zeitraum:"))
        self.period_combo = QComboBox()
        # Add time periods with display labels and lookback days
        periods = [
            ("Intraday", "1D", 1),      # Today only
            ("2 Tage", "2D", 2),        # Last 2 days
            ("5 Tage", "5D", 5),        # Last week
            ("1 Woche", "1W", 7),       # 1 week
            ("2 Wochen", "2W", 14),     # 2 weeks
            ("1 Monat", "1M", 30),      # 1 month
            ("3 Monate", "3M", 90),     # 3 months
            ("6 Monate", "6M", 180),    # 6 months
            ("1 Jahr", "1Y", 365),      # 1 year
        ]
        for display, value, days in periods:
            self.period_combo.addItem(display, value)

        # Set current based on internal value
        index = self.period_combo.findData(self.current_period)
        if index >= 0:
            self.period_combo.setCurrentIndex(index)

        self.period_combo.currentIndexChanged.connect(
            lambda idx: self._on_period_change(self.period_combo.itemData(idx))
        )
        toolbar1.addWidget(self.period_combo)

        toolbar1.addSeparator()

        # Indicators dropdown menu with checkboxes
        toolbar1.addWidget(QLabel("Indikatoren:"))

        self.indicators_button = QPushButton("📊 Indikatoren")
        self.indicators_button.setToolTip("Wähle Indikatoren zur Anzeige")
        self.indicators_menu = QMenu(self)

        # Available indicators (matching Strategy Tab)
        self.indicator_actions = {}
        indicators = [
            ("SMA", "SMA (Simple Moving Average)", "#FFA500"),
            ("EMA", "EMA (Exponential Moving Average)", "#00FFFF"),
            ("RSI", "RSI (Relative Strength Index)", "#FF00FF"),
            ("MACD", "MACD", "#00FF00"),
            ("BB", "Bollinger Bands", "#FFFF00"),
            ("ATR", "ATR (Average True Range)", "#FF0000"),
            ("STOCH", "Stochastic Oscillator", "#0000FF"),
            ("ADX", "ADX (Average Directional Index)", "#FF6600"),
            ("CCI", "CCI (Commodity Channel Index)", "#9933FF"),
            ("MFI", "MFI (Money Flow Index)", "#33FF99"),
        ]

        for ind_id, ind_name, color in indicators:
            action = QAction(ind_name, self)
            action.setCheckable(True)
            action.setData({"id": ind_id, "color": color})
            action.triggered.connect(lambda _checked, a=action: self._on_indicator_toggled(a))
            self.indicators_menu.addAction(action)
            self.indicator_actions[ind_id] = action

        self.indicators_button.setMenu(self.indicators_menu)
        self.indicators_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                color: #fff;
            }
            QPushButton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: right center;
            }
        """)
        toolbar1.addWidget(self.indicators_button)

        toolbar1.addSeparator()

        # Load data button
        self.load_button = QPushButton("📊 Load Chart")
        self.load_button.clicked.connect(self._on_load_chart)
        self.load_button.setStyleSheet("font-weight: bold; padding: 5px 15px;")
        toolbar1.addWidget(self.load_button)

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._on_refresh)
        toolbar1.addWidget(self.refresh_button)

        # Zoom-to-fit button
        self.zoom_all_button = QPushButton("🔍 Alles zoomen")
        self.zoom_all_button.setToolTip("Gesamten Chart einpassen und Pane-Höhen sinnvoll setzen")
        self.zoom_all_button.clicked.connect(self._on_zoom_all)
        toolbar1.addWidget(self.zoom_all_button)

        # Zoom-back button
        self.zoom_back_button = QPushButton("⤺ Zurück")
        self.zoom_back_button.setToolTip("Zur vorherigen Ansicht zurückkehren")
        self.zoom_back_button.clicked.connect(self._on_zoom_back)
        toolbar1.addWidget(self.zoom_back_button)

        # ========== ROW 2: Live, Markierungen, AI Chat, Trading Bot ==========
        toolbar2 = QToolBar()

        # Live streaming toggle
        self.live_stream_button = QPushButton("🔴 Live")
        self.live_stream_button.setCheckable(True)
        self.live_stream_button.setToolTip("Toggle real-time streaming (WebSocket)")
        self.live_stream_button.clicked.connect(self._toggle_live_stream)
        self.live_stream_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                color: #fff;
            }
        """)
        toolbar2.addWidget(self.live_stream_button)

        toolbar2.addSeparator()

        # ===== CHART MARKING BUTTON =====
        self.chart_marking_button = QPushButton("📏 Markierungen")
        self.chart_marking_button.setToolTip(
            "Chart-Markierungen hinzufügen (Rechtsklick auf Chart für Menü)"
        )
        self.chart_marking_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #4CAF50;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        self.chart_marking_menu = QMenu(self)

        # Entry Markers submenu
        entry_menu = self.chart_marking_menu.addMenu("📍 Entry Marker")
        long_action = QAction("🟢 Long Entry", self)
        long_action.triggered.connect(lambda: self._add_test_entry_marker("long"))
        entry_menu.addAction(long_action)
        short_action = QAction("🔴 Short Entry", self)
        short_action.triggered.connect(lambda: self._add_test_entry_marker("short"))
        entry_menu.addAction(short_action)

        # Zones submenu
        zone_menu = self.chart_marking_menu.addMenu("📊 Zonen")
        support_action = QAction("🟢 Support Zone", self)
        support_action.triggered.connect(lambda: self._add_test_zone("support"))
        zone_menu.addAction(support_action)
        resistance_action = QAction("🔴 Resistance Zone", self)
        resistance_action.triggered.connect(lambda: self._add_test_zone("resistance"))
        zone_menu.addAction(resistance_action)
        zone_menu.addSeparator()
        demand_action = QAction("🟢 Demand Zone", self)
        demand_action.triggered.connect(lambda: self._add_test_zone("demand"))
        zone_menu.addAction(demand_action)
        supply_action = QAction("🔴 Supply Zone", self)
        supply_action.triggered.connect(lambda: self._add_test_zone("supply"))
        zone_menu.addAction(supply_action)

        # Structure submenu
        structure_menu = self.chart_marking_menu.addMenu("📈 Structure Breaks")
        bos_bull = QAction("⬆️ BoS Bullish", self)
        bos_bull.triggered.connect(lambda: self._add_test_structure("bos", True))
        structure_menu.addAction(bos_bull)
        bos_bear = QAction("⬇️ BoS Bearish", self)
        bos_bear.triggered.connect(lambda: self._add_test_structure("bos", False))
        structure_menu.addAction(bos_bear)
        structure_menu.addSeparator()
        choch_bull = QAction("⬆️ CHoCH Bullish", self)
        choch_bull.triggered.connect(lambda: self._add_test_structure("choch", True))
        structure_menu.addAction(choch_bull)
        choch_bear = QAction("⬇️ CHoCH Bearish", self)
        choch_bear.triggered.connect(lambda: self._add_test_structure("choch", False))
        structure_menu.addAction(choch_bear)
        structure_menu.addSeparator()
        msb_bull = QAction("⬆️ MSB Bullish", self)
        msb_bull.triggered.connect(lambda: self._add_test_structure("msb", True))
        structure_menu.addAction(msb_bull)
        msb_bear = QAction("⬇️ MSB Bearish", self)
        msb_bear.triggered.connect(lambda: self._add_test_structure("msb", False))
        structure_menu.addAction(msb_bear)

        # Lines submenu
        lines_menu = self.chart_marking_menu.addMenu("📏 Linien")
        sl_long = QAction("🔴 Stop Loss (Long)", self)
        sl_long.triggered.connect(lambda: self._add_test_line("sl", True))
        lines_menu.addAction(sl_long)
        sl_short = QAction("🔴 Stop Loss (Short)", self)
        sl_short.triggered.connect(lambda: self._add_test_line("sl", False))
        lines_menu.addAction(sl_short)
        lines_menu.addSeparator()
        tp_long = QAction("🟢 Take Profit (Long)", self)
        tp_long.triggered.connect(lambda: self._add_test_line("tp", True))
        lines_menu.addAction(tp_long)
        tp_short = QAction("🟢 Take Profit (Short)", self)
        tp_short.triggered.connect(lambda: self._add_test_line("tp", False))
        lines_menu.addAction(tp_short)
        lines_menu.addSeparator()
        entry_line = QAction("🔵 Entry Line", self)
        entry_line.triggered.connect(lambda: self._add_test_line("entry", True))
        lines_menu.addAction(entry_line)
        trailing = QAction("🟡 Trailing Stop", self)
        trailing.triggered.connect(lambda: self._add_test_line("trailing", True))
        lines_menu.addAction(trailing)

        self.chart_marking_menu.addSeparator()

        # Clear actions
        clear_markers = QAction("🗑️ Alle Marker löschen", self)
        clear_markers.triggered.connect(self._clear_all_markers)
        self.chart_marking_menu.addAction(clear_markers)
        clear_zones = QAction("🗑️ Alle Zonen löschen", self)
        clear_zones.triggered.connect(self.clear_zones)
        self.chart_marking_menu.addAction(clear_zones)
        clear_lines = QAction("🗑️ Alle Linien löschen", self)
        clear_lines.triggered.connect(self.clear_stop_loss_lines)
        self.chart_marking_menu.addAction(clear_lines)
        self.chart_marking_menu.addSeparator()
        clear_all = QAction("🗑️ Alles löschen", self)
        clear_all.triggered.connect(self._clear_all_markings)
        self.chart_marking_menu.addAction(clear_all)

        self.chart_marking_button.setMenu(self.chart_marking_menu)
        toolbar2.addWidget(self.chart_marking_button)

        # ===== AI CHAT BUTTON =====
        self.ai_chat_button = QPushButton("🤖 AI Chat")
        self.ai_chat_button.setCheckable(True)
        self.ai_chat_button.setToolTip(
            "AI Chart-Analyse öffnen/schließen (Ctrl+Shift+C)"
        )
        self.ai_chat_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #2196F3;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:checked {
                background-color: #2196F3;
                color: #fff;
            }
        """)
        # Connect signal - will be handled by parent ChartWindow
        toolbar2.addWidget(self.ai_chat_button)

        toolbar2.addSeparator()

        # ===== TRADING BOT TOGGLE BUTTON (right after Live button) =====
        self.toggle_panel_button = QPushButton("▼ Trading Bot")
        self.toggle_panel_button.setCheckable(True)
        self.toggle_panel_button.setChecked(True)  # Panel initially visible
        self.toggle_panel_button.setToolTip("Trading Bot Panel ein-/ausblenden")
        self.toggle_panel_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #FFA500;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:checked {
                background-color: #FFA500;
                color: #000;
            }
        """)
        # Signal will be emitted to parent ChartWindow
        toolbar2.addWidget(self.toggle_panel_button)

        toolbar2.addSeparator()

        # Market status
        self.market_status_label = QLabel("Ready")
        self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")
        toolbar2.addWidget(self.market_status_label)

        return (toolbar1, toolbar2)

    def _on_zoom_all(self):
        """Zoom chart to show all data with sane pane heights."""
        try:
            if hasattr(self, "zoom_to_fit_all"):
                self.zoom_to_fit_all()
            else:
                logger.warning("zoom_to_fit_all not available on chart widget")
        except Exception as e:
            logger.error("Zoom-All failed: %s", e, exc_info=True)

    def _on_zoom_back(self):
        """Restore previous view (visible range + pane heights)."""
        try:
            if hasattr(self, "zoom_back_to_previous_view"):
                restored = self.zoom_back_to_previous_view()
                if not restored:
                    logger.info("No previous view state to restore")
            else:
                logger.warning("zoom_back_to_previous_view not available on chart widget")
        except Exception as e:
            logger.error("Zoom-Back failed: %s", e, exc_info=True)
