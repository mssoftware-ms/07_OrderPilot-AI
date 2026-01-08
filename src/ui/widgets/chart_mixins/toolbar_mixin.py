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
        toolbar1 = QToolBar()
        self._build_toolbar_row1(toolbar1)

        toolbar2 = QToolBar()
        self._build_toolbar_row2(toolbar2)

        return (toolbar1, toolbar2)

    def _build_toolbar_row1(self, toolbar: QToolBar) -> None:
        self._add_symbol_selector(toolbar)
        toolbar.addSeparator()
        self._add_timeframe_selector(toolbar)
        toolbar.addSeparator()
        self._add_period_selector(toolbar)
        toolbar.addSeparator()
        self._add_indicators_menu(toolbar)
        toolbar.addSeparator()
        self._add_primary_actions(toolbar)

    def _build_toolbar_row2(self, toolbar: QToolBar) -> None:
        self._add_live_stream_toggle(toolbar)
        toolbar.addSeparator()
        self._add_regime_badge_to_toolbar(toolbar)  # Phase 2.2: Regime Badge
        toolbar.addSeparator()
        self._add_chart_marking_button(toolbar)
        self._add_levels_button(toolbar)  # Phase 5.5: Levels Toggle
        self._add_ai_chat_button(toolbar)
        self._add_ai_analysis_button(toolbar)
        self._add_export_context_button(toolbar)  # Phase 5.5: Export Context
        self._add_bitunix_trading_button(toolbar)
        toolbar.addSeparator()
        self._add_bot_toggle_button(toolbar)
        toolbar.addSeparator()
        self._add_market_status(toolbar)

    def _add_symbol_selector(self, toolbar: QToolBar) -> None:
        toolbar.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(
            [
                "BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD",
                "───────",
                "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ",
            ]
        )
        self.symbol_combo.setCurrentText(self.current_symbol)
        self.symbol_combo.currentTextChanged.connect(self._on_symbol_change)
        toolbar.addWidget(self.symbol_combo)

    def _add_timeframe_selector(self, toolbar: QToolBar) -> None:
        toolbar.addWidget(QLabel("Kerzen:"))
        self.timeframe_combo = QComboBox()
        timeframes = [
            ("1 Minute", "1T"),
            ("5 Minuten", "5T"),
            ("15 Minuten", "15T"),
            ("30 Minuten", "30T"),
            ("1 Stunde", "1H"),
            ("4 Stunden", "4H"),
            ("1 Tag", "1D"),
        ]
        for display, value in timeframes:
            self.timeframe_combo.addItem(display, value)

        index = self.timeframe_combo.findData(self.current_timeframe)
        if index >= 0:
            self.timeframe_combo.setCurrentIndex(index)

        self.timeframe_combo.currentIndexChanged.connect(
            lambda idx: self._on_timeframe_change(self.timeframe_combo.itemData(idx))
        )
        toolbar.addWidget(self.timeframe_combo)

    def _add_period_selector(self, toolbar: QToolBar) -> None:
        toolbar.addWidget(QLabel("Zeitraum:"))
        self.period_combo = QComboBox()
        periods = [
            ("Intraday", "1D", 1),
            ("2 Tage", "2D", 2),
            ("5 Tage", "5D", 5),
            ("1 Woche", "1W", 7),
            ("2 Wochen", "2W", 14),
            ("1 Monat", "1M", 30),
            ("3 Monate", "3M", 90),
            ("6 Monate", "6M", 180),
            ("1 Jahr", "1Y", 365),
        ]
        for display, value, days in periods:
            self.period_combo.addItem(display, value)

        index = self.period_combo.findData(self.current_period)
        if index >= 0:
            self.period_combo.setCurrentIndex(index)

        self.period_combo.currentIndexChanged.connect(
            lambda idx: self._on_period_change(self.period_combo.itemData(idx))
        )
        toolbar.addWidget(self.period_combo)

    def _add_indicators_menu(self, toolbar: QToolBar) -> None:
        toolbar.addWidget(QLabel("Indikatoren:"))
        self.indicators_button = QPushButton("📊 Indikatoren")
        self.indicators_button.setToolTip("Mehrfach-Indikatoren hinzufügen/entfernen")

        self.indicators_menu = QMenu(self)
        # Direkt Kategorien auf oberster Ebene
        self._build_indicator_tree(self.indicators_menu)
        self._remove_actions: list[QAction] = []
        self._remove_section_separator = None

        self.indicators_button.setMenu(self.indicators_menu)
        self.indicators_button.setStyleSheet(
            """
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
        """
        )
        toolbar.addWidget(self.indicators_button)

    def _build_indicator_tree(self, root_menu: QMenu) -> None:
        """Create tree-like add menu with presets and custom entries."""
        def add_action(menu, text, ind_id, params, color):
            act = QAction(text, self)
            act.triggered.connect(lambda _=False, i=ind_id, p=params, c=color: self._on_indicator_add(i, p, c))
            menu.addAction(act)

        # 1. Overlap Studies (Trend & Struktur)
        overlap_menu = root_menu.addMenu("Trend & Struktur")
        
        # EMA
        ema_menu = overlap_menu.addMenu("EMA (Exponential Moving Average)")
        add_action(ema_menu, "EMA (9) - Scalping", "EMA", {"period": 9}, "#00CED1")
        add_action(ema_menu, "EMA (20) - Basis", "EMA", {"period": 20}, "#00FFFF")
        add_action(ema_menu, "EMA (21) - Scalping", "EMA", {"period": 21}, "#20B2AA")
        add_action(ema_menu, "EMA (50) - Trend", "EMA", {"period": 50}, "#FFB347")
        add_action(ema_menu, "EMA (200) - Langfristig", "EMA", {"period": 200}, "#FF4500")
        ema_menu.addSeparator()
        ema_custom = QAction("Custom EMA…", self)
        ema_custom.triggered.connect(lambda: self._prompt_custom_period("EMA", "#00FFFF"))
        ema_menu.addAction(ema_custom)

        # SMA
        sma_menu = overlap_menu.addMenu("SMA (Simple Moving Average)")
        add_action(sma_menu, "SMA (20)", "SMA", {"period": 20}, "#FFA500")
        add_action(sma_menu, "SMA (50)", "SMA", {"period": 50}, "#FF8C00")
        add_action(sma_menu, "SMA (200)", "SMA", {"period": 200}, "#FFD700")
        sma_menu.addSeparator()
        sma_custom = QAction("Custom SMA…", self)
        sma_custom.triggered.connect(lambda: self._prompt_custom_period("SMA", "#FFA500"))
        sma_menu.addAction(sma_custom)

        # Bollinger Bands
        bb_menu = overlap_menu.addMenu("Bollinger Bands")
        add_action(bb_menu, "BB (20, 2)", "BB", {"period": 20, "std": 2}, "#FFFF00")
        bb_menu.addSeparator()
        bb_custom = QAction("Custom BB…", self)
        bb_custom.triggered.connect(lambda: self._prompt_generic_params("BB", "#FFFF00"))
        bb_menu.addAction(bb_custom)

        # 2. Momentum & Oszillatoren
        mom_menu = root_menu.addMenu("Momentum & Oszillatoren")
        
        # RSI
        rsi_menu = mom_menu.addMenu("RSI (Relative Strength Index)")
        add_action(rsi_menu, "RSI (14)", "RSI", {"period": 14}, "#FF00FF")
        rsi_menu.addSeparator()
        rsi_custom = QAction("Custom RSI…", self)
        rsi_custom.triggered.connect(lambda: self._prompt_custom_period("RSI", "#FF00FF"))
        rsi_menu.addAction(rsi_custom)

        # MACD
        macd_menu = mom_menu.addMenu("MACD")
        add_action(macd_menu, "MACD (12, 26, 9)", "MACD", {"fast": 12, "slow": 26, "signal": 9}, "#00FF00")
        macd_menu.addSeparator()
        macd_custom = QAction("Custom MACD…", self)
        macd_custom.triggered.connect(lambda: self._prompt_generic_params("MACD", "#00FF00"))
        macd_menu.addAction(macd_custom)

        # Stochastic
        stoch_menu = mom_menu.addMenu("Stochastic")
        add_action(stoch_menu, "Stoch (14, 3, 3)", "STOCH", {"k_period": 14, "d_period": 3, "smooth": 3}, "#0000FF")
        stoch_menu.addSeparator()
        stoch_custom = QAction("Custom Stoch…", self)
        stoch_custom.triggered.connect(lambda: self._prompt_generic_params("STOCH", "#0000FF"))
        stoch_menu.addAction(stoch_custom)

        # CCI
        cci_menu = mom_menu.addMenu("CCI")
        add_action(cci_menu, "CCI (20)", "CCI", {"period": 20}, "#9933FF")
        
        # MFI
        mfi_menu = mom_menu.addMenu("MFI")
        add_action(mfi_menu, "MFI (14)", "MFI", {"period": 14}, "#33FF99")

        # 3. Volatilität & Trendstärke
        vol_menu = root_menu.addMenu("Volatilität & Trendstärke")
        
        # ATR
        atr_menu = vol_menu.addMenu("ATR (Average True Range)")
        add_action(atr_menu, "ATR (14)", "ATR", {"period": 14}, "#FF4500")
        atr_menu.addSeparator()
        atr_custom = QAction("Custom ATR…", self)
        atr_custom.triggered.connect(lambda: self._prompt_custom_period("ATR", "#FF4500"))
        atr_menu.addAction(atr_custom)

        # ADX
        adx_menu = vol_menu.addMenu("ADX (Avg Directional Index)")
        add_action(adx_menu, "ADX (14)", "ADX", {"period": 14}, "#FF6600")
        adx_menu.addSeparator()
        adx_custom = QAction("Custom ADX…", self)
        adx_custom.triggered.connect(lambda: self._prompt_custom_period("ADX", "#FF6600"))
        adx_menu.addAction(adx_custom)

        # Bollinger Derived
        bb_derived = vol_menu.addMenu("Bollinger Derived")
        add_action(bb_derived, "%B", "BB_PERCENT", {"period": 20, 'std': 2}, "#32CD32")
        add_action(bb_derived, "Bandwidth", "BB_WIDTH", {"period": 20, 'std': 2}, "#4169E1")

        # Generic custom
        custom_menu = root_menu.addMenu("Custom")

    def _prompt_custom_period(self, ind_id: str, color: str) -> None:
        from PyQt6.QtWidgets import QInputDialog
        period, ok = QInputDialog.getInt(self, "Periode wählen", f"{ind_id} Periode:", value=14, min=1, max=500)
        if ok:
            self._on_indicator_add(ind_id, {"period": period}, color)

    def _prompt_generic_params(self, ind_id: str, color: str) -> None:
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Parameter", f"{ind_id} Parameter (key=value,comma-separated):", text="period=20")
        if not ok:
            return
        params = {}
        try:
            for part in text.split(","):
                k, v = part.split("=")
                params[k.strip()] = float(v) if "." in v else int(v)
            self._on_indicator_add(ind_id, params, color)
        except Exception:
            logger.error("Parameter-Parsing fehlgeschlagen: %s", text)

    def _refresh_active_indicator_menu(self) -> None:
        """Show active indicators as remove-actions directly in main menu."""
        if not hasattr(self, "indicators_menu"):
            return
        # remove old actions
        if getattr(self, "_remove_actions", None):
            for act in self._remove_actions:
                self.indicators_menu.removeAction(act)
        if getattr(self, "_remove_section_separator", None):
            self.indicators_menu.removeAction(self._remove_section_separator)
        self._remove_actions = []
        self._remove_section_separator = None

        if not hasattr(self, "chart_widget") or not getattr(self.chart_widget, "active_indicators", None):
            return

        if self.chart_widget.active_indicators:
            self._remove_section_separator = self.indicators_menu.addSeparator()
            for instance_id, inst in self.chart_widget.active_indicators.items():
                label = f"Remove: {inst.display_name}"
                act = QAction(label, self)
                act.triggered.connect(lambda _=False, iid=instance_id: self._on_indicator_remove(iid))
                self.indicators_menu.addAction(act)
                self._remove_actions.append(act)

    # Hooks into IndicatorMixin
    def _on_indicator_add(self, ind_id: str, params: dict, color: str) -> None:
        if hasattr(self, "chart_widget") and hasattr(self.chart_widget, "_add_indicator_instance"):
            self.chart_widget._add_indicator_instance(ind_id, params, color)
            self._refresh_active_indicator_menu()

    def _on_indicator_remove(self, instance_id: str) -> None:
        if hasattr(self, "chart_widget") and hasattr(self.chart_widget, "_remove_indicator_instance"):
            self.chart_widget._remove_indicator_instance(instance_id)
            self._refresh_active_indicator_menu()

    def _add_primary_actions(self, toolbar: QToolBar) -> None:
        self.load_button = QPushButton("📊 Load Chart")
        self.load_button.clicked.connect(self._on_load_chart)
        self.load_button.setStyleSheet("font-weight: bold; padding: 5px 15px;")
        toolbar.addWidget(self.load_button)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._on_refresh)
        toolbar.addWidget(self.refresh_button)

        self.zoom_all_button = QPushButton("🔍 Alles zoomen")
        self.zoom_all_button.setToolTip(
            "Gesamten Chart einpassen und Pane-Höhen sinnvoll setzen"
        )
        self.zoom_all_button.clicked.connect(self._on_zoom_all)
        toolbar.addWidget(self.zoom_all_button)

        self.zoom_back_button = QPushButton("⤺ Zurück")
        self.zoom_back_button.setToolTip("Zur vorherigen Ansicht zurückkehren")
        self.zoom_back_button.clicked.connect(self._on_zoom_back)
        toolbar.addWidget(self.zoom_back_button)

    def _add_regime_badge_to_toolbar(self, toolbar: QToolBar) -> None:
        """Add regime badge to toolbar (Phase 2.2)."""
        try:
            from src.ui.widgets.regime_badge_widget import RegimeBadgeWidget

            toolbar.addWidget(QLabel("Regime:"))
            self._regime_badge = RegimeBadgeWidget(compact=True, show_icon=True)
            self._regime_badge.clicked.connect(self._on_regime_badge_clicked)
            toolbar.addWidget(self._regime_badge)
            logger.debug("Regime badge added to toolbar")
        except ImportError as e:
            logger.warning(f"Could not add regime badge: {e}")
            # Fallback: simple label
            self._regime_label = QLabel("N/A")
            self._regime_label.setStyleSheet("color: #888; padding: 5px;")
            toolbar.addWidget(QLabel("Regime:"))
            toolbar.addWidget(self._regime_label)

    def _on_regime_badge_clicked(self) -> None:
        """Handle regime badge click - show regime details dialog."""
        logger.debug("Regime badge clicked")
        # TODO: Open regime details dialog in Phase 5

    def update_regime_badge(self, regime: str, adx: float | None = None,
                            gate_reason: str = "", allows_entry: bool = True) -> None:
        """
        Update the regime badge display.

        Args:
            regime: Regime type string
            adx: ADX value
            gate_reason: Reason for gate
            allows_entry: Whether entry is allowed
        """
        if hasattr(self, "_regime_badge") and self._regime_badge:
            self._regime_badge.set_regime(regime, adx, gate_reason, allows_entry)
        elif hasattr(self, "_regime_label"):
            self._regime_label.setText(regime[:10])

    def update_regime_from_result(self, result) -> None:
        """
        Update regime badge from RegimeResult.

        Args:
            result: RegimeResult from RegimeDetectorService
        """
        if hasattr(self, "_regime_badge") and self._regime_badge:
            self._regime_badge.set_regime_from_result(result)

    def _add_live_stream_toggle(self, toolbar: QToolBar) -> None:
        self.live_stream_button = QPushButton("🔴 Live")
        self.live_stream_button.setCheckable(True)
        self.live_stream_button.setToolTip("Toggle real-time streaming (WebSocket)")
        self.live_stream_button.clicked.connect(self._toggle_live_stream)
        self.live_stream_button.setStyleSheet(
            """
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
        """
        )
        toolbar.addWidget(self.live_stream_button)

    def _add_chart_marking_button(self, toolbar: QToolBar) -> None:
        self.chart_marking_button = QPushButton("📏 Markierungen")
        self.chart_marking_button.setToolTip(
            "Chart-Markierungen hinzufügen (Rechtsklick auf Chart für Menü)"
        )
        self.chart_marking_button.setStyleSheet(
            """
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
        """
        )
        self.chart_marking_menu = QMenu(self)
        self._build_chart_marking_menu()
        self.chart_marking_button.setMenu(self.chart_marking_menu)
        toolbar.addWidget(self.chart_marking_button)

    def _build_chart_marking_menu(self) -> None:
        entry_menu = self.chart_marking_menu.addMenu("📍 Entry Marker")
        long_action = QAction("🟢 Long Entry", self)
        long_action.triggered.connect(lambda: self._add_test_entry_marker("long"))
        entry_menu.addAction(long_action)
        short_action = QAction("🔴 Short Entry", self)
        short_action.triggered.connect(lambda: self._add_test_entry_marker("short"))
        entry_menu.addAction(short_action)

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

    def _add_ai_chat_button(self, toolbar: QToolBar) -> None:
        self.ai_chat_button = QPushButton("🤖 AI Chat")
        self.ai_chat_button.setCheckable(True)
        self.ai_chat_button.setToolTip(
            "AI Chart-Analyse öffnen/schließen (Ctrl+Shift+C)"
        )
        self.ai_chat_button.setStyleSheet(
            """
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
        """
        )
        toolbar.addWidget(self.ai_chat_button)

    def _add_ai_analysis_button(self, toolbar: QToolBar) -> None:
        self.ai_analysis_button = QPushButton("🧠 AI Analyse")
        self.ai_analysis_button.setCheckable(True)
        self.ai_analysis_button.setToolTip(
            "Deep Market Analysis Popup öffnen"
        )
        self.ai_analysis_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2a2a2a;
                color: #9C27B0;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:checked {
                background-color: #9C27B0;
                color: #fff;
            }
        """
        )
        toolbar.addWidget(self.ai_analysis_button)

    def _add_bitunix_trading_button(self, toolbar: QToolBar) -> None:
        """Add Bitunix trading button to toolbar (initially hidden)."""
        self.bitunix_trading_button = QPushButton("💱 Bitunix")
        self.bitunix_trading_button.setCheckable(True)
        self.bitunix_trading_button.setToolTip(
            "Bitunix Futures Trading öffnen/schließen (nur Crypto)"
        )
        self.bitunix_trading_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2a2a2a;
                color: #FFC107;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:checked {
                background-color: #FFC107;
                color: #000;
            }
        """
        )
        # Always visible (user can decide to open/close the dock)
        self.bitunix_trading_button.setVisible(True)
        toolbar.addWidget(self.bitunix_trading_button)
        logger.info("Toolbar: Bitunix trading button created and added (visible)")

    def _add_bot_toggle_button(self, toolbar: QToolBar) -> None:
        self.toggle_panel_button = QPushButton("▼ Trading Bot")
        self.toggle_panel_button.setCheckable(True)
        self.toggle_panel_button.setChecked(True)
        self.toggle_panel_button.setToolTip("Trading Bot Panel ein-/ausblenden")
        self.toggle_panel_button.setStyleSheet(
            """
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
        """
        )
        toolbar.addWidget(self.toggle_panel_button)

    def _add_market_status(self, toolbar: QToolBar) -> None:
        self.market_status_label = QLabel("Ready")
        self.market_status_label.setStyleSheet(
            "color: #888; font-weight: bold; padding: 5px;"
        )
        toolbar.addWidget(self.market_status_label)

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

    # =========================================================================
    # PHASE 5.5: LEVELS BUTTON
    # =========================================================================

    def _add_levels_button(self, toolbar: QToolBar) -> None:
        """Add levels toggle button to toolbar (Phase 5.5)."""
        self.levels_button = QPushButton("📊 Levels")
        self.levels_button.setCheckable(True)
        self.levels_button.setChecked(False)
        self.levels_button.setToolTip(
            "Support/Resistance Levels im Chart anzeigen/verbergen"
        )
        self.levels_button.setStyleSheet(
            """
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
            QPushButton:checked {
                background-color: #4CAF50;
                color: #000;
            }
        """
        )

        # Add dropdown menu for level options
        levels_menu = QMenu(self)
        self._build_levels_menu(levels_menu)
        self.levels_button.setMenu(levels_menu)

        toolbar.addWidget(self.levels_button)
        logger.debug("Levels button added to toolbar")

    def _build_levels_menu(self, menu: QMenu) -> None:
        """Build the levels dropdown menu."""
        # Refresh/Detect action
        detect_action = QAction("🔍 Levels erkennen", self)
        detect_action.triggered.connect(self._on_detect_levels)
        menu.addAction(detect_action)

        menu.addSeparator()

        # Level type toggles
        self._level_type_actions = {}
        level_types = [
            ("support", "🟢 Support Levels", True),
            ("resistance", "🔴 Resistance Levels", True),
            ("pivot", "🟣 Pivot Points", False),
            ("swing", "🟠 Swing Highs/Lows", False),
            ("daily", "📈 Daily H/L", False),
        ]

        for level_type, label, default in level_types:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(default)
            action.triggered.connect(
                lambda checked, lt=level_type: self._on_level_type_toggle(lt, checked)
            )
            menu.addAction(action)
            self._level_type_actions[level_type] = action

        menu.addSeparator()

        # Key levels only
        key_only_action = QAction("⭐ Nur Key Levels", self)
        key_only_action.setCheckable(True)
        menu.addAction(key_only_action)
        self._key_only_action = key_only_action

        menu.addSeparator()

        # Clear levels
        clear_action = QAction("🗑️ Levels entfernen", self)
        clear_action.triggered.connect(self._on_clear_levels)
        menu.addAction(clear_action)

    def _on_detect_levels(self) -> None:
        """Trigger level detection."""
        logger.debug("Level detection requested via toolbar")
        # Signal wird in chart_window.py verbunden
        if hasattr(self, "levels_detect_requested"):
            self.levels_detect_requested.emit()

    def _on_level_type_toggle(self, level_type: str, checked: bool) -> None:
        """Handle level type toggle."""
        logger.debug(f"Level type {level_type} toggled: {checked}")
        if hasattr(self, "level_type_toggled"):
            self.level_type_toggled.emit(level_type, checked)

    def _on_clear_levels(self) -> None:
        """Clear all level zones from chart."""
        logger.debug("Clear levels requested")
        if hasattr(self, "clear_zones"):
            self.clear_zones()

    # =========================================================================
    # PHASE 5.5: EXPORT CONTEXT BUTTON
    # =========================================================================

    def _add_export_context_button(self, toolbar: QToolBar) -> None:
        """Add export context button to toolbar (Phase 5.5)."""
        self.export_context_button = QPushButton("📤 Context")
        self.export_context_button.setToolTip(
            "MarketContext exportieren (JSON/Clipboard)"
        )
        self.export_context_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2a2a2a;
                color: #00BCD4;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """
        )

        # Add dropdown menu for export options
        export_menu = QMenu(self)
        self._build_export_context_menu(export_menu)
        self.export_context_button.setMenu(export_menu)

        toolbar.addWidget(self.export_context_button)
        logger.debug("Export context button added to toolbar")

    def _build_export_context_menu(self, menu: QMenu) -> None:
        """Build the export context dropdown menu."""
        # View Inspector
        inspect_action = QAction("🔍 Context Inspector öffnen", self)
        inspect_action.triggered.connect(self._on_open_context_inspector)
        menu.addAction(inspect_action)

        menu.addSeparator()

        # Copy to clipboard
        copy_json_action = QAction("📋 Als JSON kopieren", self)
        copy_json_action.triggered.connect(self._on_copy_context_json)
        menu.addAction(copy_json_action)

        copy_prompt_action = QAction("📝 Als AI Prompt kopieren", self)
        copy_prompt_action.triggered.connect(self._on_copy_context_prompt)
        menu.addAction(copy_prompt_action)

        menu.addSeparator()

        # Export to file
        export_file_action = QAction("💾 Als JSON exportieren...", self)
        export_file_action.triggered.connect(self._on_export_context_file)
        menu.addAction(export_file_action)

        menu.addSeparator()

        # Refresh context
        refresh_action = QAction("🔄 Context aktualisieren", self)
        refresh_action.triggered.connect(self._on_refresh_context)
        menu.addAction(refresh_action)

    def _on_open_context_inspector(self) -> None:
        """Open the MarketContext Inspector dialog."""
        logger.debug("Context inspector requested")
        # Wird in chart_window.py implementiert
        if hasattr(self, "context_inspector_requested"):
            self.context_inspector_requested.emit()

    def _on_copy_context_json(self) -> None:
        """Copy MarketContext as JSON to clipboard."""
        logger.debug("Copy context JSON requested")
        if hasattr(self, "context_copy_json_requested"):
            self.context_copy_json_requested.emit()

    def _on_copy_context_prompt(self) -> None:
        """Copy MarketContext as AI prompt to clipboard."""
        logger.debug("Copy context prompt requested")
        if hasattr(self, "context_copy_prompt_requested"):
            self.context_copy_prompt_requested.emit()

    def _on_export_context_file(self) -> None:
        """Export MarketContext to JSON file."""
        logger.debug("Export context file requested")
        if hasattr(self, "context_export_file_requested"):
            self.context_export_file_requested.emit()

    def _on_refresh_context(self) -> None:
        """Refresh MarketContext."""
        logger.debug("Refresh context requested")
        if hasattr(self, "context_refresh_requested"):
            self.context_refresh_requested.emit()
