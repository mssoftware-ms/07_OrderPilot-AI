"""Toolbar Row 1 Setup Mixin - Widget Creation and Layout.

This module handles widget creation and layout setup for toolbar row 1.
Part of toolbar_mixin_row1.py refactoring (827 LOC → 3 focused mixins).

Responsibilities:
- Widget creation (buttons, combos, menus)
- Layout setup and configuration
- Indicator menu tree building
- Constants and sizing
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QComboBox, QPushButton, QToolBar, QMenu

from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolbarRow1SetupMixin:
    """Row 1 toolbar setup - widget creation and layout."""

    # Issue #16: Einheitliche Button-Höhe und Icon-Größe (konsistent mit Row2)
    BUTTON_HEIGHT = 32
    ICON_SIZE = QSize(20, 20)

    def build_toolbar_row1(self, toolbar: QToolBar) -> None:
        """Build toolbar row 1.

        Phase 2 (UI Refactoring): Added Broker Mirror Controls at start.
        These are "mirror controls" that emit events to BrokerService
        rather than managing connections directly.
        """
        # Phase 2: Broker Mirror Controls (emit events, don't manage directly)
        self.add_broker_mirror_controls(toolbar)
        toolbar.addSeparator()

        # Watchlist Toggle Button
        self.add_watchlist_toggle(toolbar)
        toolbar.addSeparator()

        # Original Row 1 content
        # Symbol-Selector entfernt (Issue #20, #30) - Symbol wird über ChartWindow gesteuert
        self.add_timeframe_selector(toolbar)
        toolbar.addSeparator()
        self.add_period_selector(toolbar)
        toolbar.addSeparator()
        self.add_indicators_menu(toolbar)
        toolbar.addSeparator()
        self.add_primary_actions(toolbar)

    def add_broker_mirror_controls(self, toolbar: QToolBar) -> None:
        """Add broker mirror controls (Phase 2: Workspace Manager).

        These controls MIRROR the state from BrokerService and emit events
        rather than directly calling connect/disconnect. This ensures
        centralized broker management.
        """
        from PyQt6.QtCore import QSize
        from PyQt6.QtWidgets import QLabel
        from src.common.event_bus import Event, EventType, event_bus
        from src.core.broker import get_broker_service
        from src.ui.icons import get_icon

        # Connect/Disconnect Button (Mirror - emits events)
        self.parent.chart_connect_button = QPushButton()
        self.parent.chart_connect_button.setIcon(get_icon("connect"))
        self.parent.chart_connect_button.setIconSize(self.ICON_SIZE)
        self.parent.chart_connect_button.setCheckable(True)
        self.parent.chart_connect_button.setToolTip(
            "Broker-Verbindung (Mirror Control)\n"
            "Synchronisiert mit Workspace Manager"
        )
        self.parent.chart_connect_button.setFixedHeight(self.BUTTON_HEIGHT)
        self.parent.chart_connect_button.setFixedWidth(40)
        self.parent.chart_connect_button.clicked.connect(self._on_broker_connect_clicked)
        toolbar.addWidget(self.parent.chart_connect_button)

        # Issue #7: Trading Mode Badge (PAPER) entfernt
        # Paper Badge wurde vom Benutzer als störend empfunden und soll gelöscht werden
        # Die Trading-Modus-Information wird stattdessen im Workspace Manager angezeigt
        pass

        # Subscribe to broker events for sync
        event_bus.subscribe(EventType.MARKET_CONNECTED, self._on_broker_connected_event)
        event_bus.subscribe(EventType.MARKET_DISCONNECTED, self._on_broker_disconnected_event)

        # Initial sync with BrokerService
        broker_service = get_broker_service()
        self._update_broker_ui_state(broker_service.is_connected, broker_service.broker_type)

    def add_watchlist_toggle(self, toolbar: QToolBar) -> None:
        """Add watchlist toggle button to toolbar."""
        from src.ui.icons import get_icon

        self.parent.watchlist_toggle_btn = QPushButton("📋")
        self.parent.watchlist_toggle_btn.setToolTip("Watchlist ein/ausblenden")
        self.parent.watchlist_toggle_btn.setIconSize(self.ICON_SIZE)
        self.parent.watchlist_toggle_btn.setCheckable(True)
        self.parent.watchlist_toggle_btn.setChecked(True)  # Default: visible
        self.parent.watchlist_toggle_btn.setToolTip("Watchlist ein/ausblenden")
        self.parent.watchlist_toggle_btn.setFixedHeight(self.BUTTON_HEIGHT)
        self.parent.watchlist_toggle_btn.setFixedWidth(40)
        self.parent.watchlist_toggle_btn.setProperty("class", "toolbar-button")  # Issue #7: Theme-Klasse
        self.parent.watchlist_toggle_btn.clicked.connect(self._toggle_watchlist)
        toolbar.addWidget(self.parent.watchlist_toggle_btn)

    def add_timeframe_selector(self, toolbar: QToolBar) -> None:
        """Add timeframe selector combo box."""
        # Issue #22: Label entfernt, Tooltip stattdessen
        self.parent.timeframe_combo = QComboBox()
        self.parent.timeframe_combo.setToolTip("Kerzen-Zeitrahmen wählen")
        self.parent.timeframe_combo.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #17: Gleiche Höhe wie Buttons (32px)
        # Issue #38: Added 1 second timeframe
        # Issue #42: Added 2-hour and 8-hour timeframes
        timeframes = [
            ("1 Sekunde", "1S"),
            ("1 Minute", "1T"),
            ("5 Minuten", "5T"),
            ("10 Minuten", "10T"),
            ("15 Minuten", "15T"),
            ("30 Minuten", "30T"),
            ("1 Stunde", "1H"),
            ("2 Stunden", "2H"),
            ("4 Stunden", "4H"),
            ("8 Stunden", "8H"),
            ("1 Tag", "1D"),
        ]
        for display, value in timeframes:
            self.parent.timeframe_combo.addItem(display, value)

        index = self.parent.timeframe_combo.findData(self.parent.current_timeframe)
        if index >= 0:
            self.parent.timeframe_combo.setCurrentIndex(index)

        self.parent.timeframe_combo.currentIndexChanged.connect(
            lambda idx: self.parent._on_timeframe_change(self.parent.timeframe_combo.itemData(idx))
        )
        toolbar.addWidget(self.parent.timeframe_combo)

    def add_period_selector(self, toolbar: QToolBar) -> None:
        """Add period selector combo box."""
        # Issue #22: Label entfernt, Tooltip stattdessen
        self.parent.period_combo = QComboBox()
        self.parent.period_combo.setToolTip("Darstellungs-Zeitraum wählen")
        self.parent.period_combo.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #17: Gleiche Höhe wie Buttons (32px)
        # Issue #42: Added shorter periods (1h, 2h, 4h, 8h) for 1-second charts
        periods = [
            ("1 Stunde", "1H", 1/24),      # Issue #42: ~4% of a day
            ("2 Stunden", "2H", 2/24),     # Issue #42: ~8% of a day
            ("4 Stunden", "4H", 4/24),     # Issue #42: ~17% of a day
            ("8 Stunden", "8H", 8/24),     # Issue #42: ~33% of a day
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
            self.parent.period_combo.addItem(display, value)

        index = self.parent.period_combo.findData(self.parent.current_period)
        if index >= 0:
            self.parent.period_combo.setCurrentIndex(index)

        self.parent.period_combo.currentIndexChanged.connect(
            lambda idx: self.parent._on_period_change(self.parent.period_combo.itemData(idx))
        )
        toolbar.addWidget(self.parent.period_combo)

    def add_indicators_menu(self, toolbar: QToolBar) -> None:
        """Add indicators menu button."""
        # Issue #22: Label entfernt
        # Issue #7: Icon prüfen - sicherstellen, dass nur ein Icon verwendet wird (kein altes buntes Icon)
        self.parent.indicators_button = QPushButton("Indikatoren")  # Issue #15: Emoji entfernt
        self.parent.indicators_button.setIcon(get_icon("indicators"))  # Issue #22: Spezifisches Icon (nur weißes Icon verwenden)
        self.parent.indicators_button.setIconSize(self.ICON_SIZE)  # Issue #15: Klassen-Konstante
        self.parent.indicators_button.setToolTip("Indikatoren hinzufügen/entfernen")  # Issue #22: Kürzerer Tooltip
        self.parent.indicators_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16: Klassen-Konstante (32px)
        # Issue #7: Explizite Höhenbegrenzung für konsistente Darstellung
        self.parent.indicators_button.setMaximumHeight(self.BUTTON_HEIGHT)

        self.parent.indicators_menu = QMenu(self.parent)
        # Direkt Kategorien auf oberster Ebene
        self._build_indicator_tree(self.parent.indicators_menu)
        self.parent._remove_actions: list[QAction] = []
        self.parent._remove_section_separator = None

        self.parent.indicators_button.setMenu(self.parent.indicators_menu)
        # Style is now handled by global theme (src/ui/themes.py)
        # Class property can be used for specific styling if needed
        self.parent.indicators_button.setProperty("class", "toolbar-button")
        toolbar.addWidget(self.parent.indicators_button)

    def _build_indicator_tree(self, root_menu: QMenu) -> None:
        """Create tree-like add menu with presets and custom entries."""
        def add_action(menu, text, ind_id, params, color):
            act = QAction(text, self.parent)
            act.triggered.connect(lambda _=False, i=ind_id, p=params, c=color: self.on_indicator_add(i, p, c))
            menu.addAction(act)

        # =====================================================================
        # 1. TREND & STRUKTUR (Overlay Indicators)
        # =====================================================================
        overlap_menu = root_menu.addMenu("Trend & Struktur")  # Issue #22: Emoji entfernt

        # Moving Averages Submenu
        ma_menu = overlap_menu.addMenu("Moving Averages")

        # EMA
        ema_menu = ma_menu.addMenu("EMA (Exponential)")
        add_action(ema_menu, "EMA (9) - Scalping", "EMA", {"period": 9}, "#00CED1")
        add_action(ema_menu, "EMA (20) - Basis", "EMA", {"period": 20}, "#00FFFF")
        add_action(ema_menu, "EMA (21) - Fibonacci", "EMA", {"period": 21}, "#20B2AA")
        add_action(ema_menu, "EMA (50) - Trend", "EMA", {"period": 50}, "#FFB347")
        add_action(ema_menu, "EMA (200) - Langfristig", "EMA", {"period": 200}, "#FF4500")
        ema_menu.addSeparator()
        ema_custom = QAction("Custom EMA…", self.parent)
        ema_custom.triggered.connect(lambda: self.prompt_custom_period("EMA", "#00FFFF"))
        ema_menu.addAction(ema_custom)

        # SMA
        sma_menu = ma_menu.addMenu("SMA (Simple)")
        add_action(sma_menu, "SMA (20)", "SMA", {"period": 20}, "#FFA500")
        add_action(sma_menu, "SMA (50)", "SMA", {"period": 50}, "#FF8C00")
        add_action(sma_menu, "SMA (200)", "SMA", {"period": 200}, "#FFD700")
        sma_menu.addSeparator()
        sma_custom = QAction("Custom SMA…", self.parent)
        sma_custom.triggered.connect(lambda: self.prompt_custom_period("SMA", "#FFA500"))
        sma_menu.addAction(sma_custom)

        # WMA
        wma_menu = ma_menu.addMenu("WMA (Weighted)")
        add_action(wma_menu, "WMA (20)", "WMA", {"period": 20}, "#DA70D6")
        add_action(wma_menu, "WMA (50)", "WMA", {"period": 50}, "#BA55D3")
        wma_menu.addSeparator()
        wma_custom = QAction("Custom WMA…", self.parent)
        wma_custom.triggered.connect(lambda: self.prompt_custom_period("WMA", "#DA70D6"))
        wma_menu.addAction(wma_custom)

        # VWMA
        vwma_menu = ma_menu.addMenu("VWMA (Volume Weighted)")
        add_action(vwma_menu, "VWMA (20)", "VWMA", {"period": 20}, "#7B68EE")
        add_action(vwma_menu, "VWMA (50)", "VWMA", {"period": 50}, "#6A5ACD")
        vwma_menu.addSeparator()
        vwma_custom = QAction("Custom VWMA…", self.parent)
        vwma_custom.triggered.connect(lambda: self.prompt_custom_period("VWMA", "#7B68EE"))
        vwma_menu.addAction(vwma_custom)

        # Bands & Channels Submenu
        bands_menu = overlap_menu.addMenu("Bands & Channels")

        # Bollinger Bands
        bb_menu = bands_menu.addMenu("Bollinger Bands")
        add_action(bb_menu, "BB (20, 2) - Standard", "BB", {"period": 20, "std": 2}, "#FFFF00")
        add_action(bb_menu, "BB (20, 1) - Tight", "BB", {"period": 20, "std": 1}, "#FFD700")
        add_action(bb_menu, "BB (20, 3) - Wide", "BB", {"period": 20, "std": 3}, "#FFA500")
        bb_menu.addSeparator()
        bb_custom = QAction("Custom BB…", self.parent)
        bb_custom.triggered.connect(lambda: self.prompt_generic_params("BB", "#FFFF00"))
        bb_menu.addAction(bb_custom)

        # Keltner Channels
        kc_menu = bands_menu.addMenu("Keltner Channels")
        add_action(kc_menu, "KC (20, 1.5)", "KC", {"period": 20, "mult": 1.5}, "#87CEEB")
        add_action(kc_menu, "KC (20, 2)", "KC", {"period": 20, "mult": 2}, "#00BFFF")
        kc_menu.addSeparator()
        kc_custom = QAction("Custom KC…", self.parent)
        kc_custom.triggered.connect(lambda: self.prompt_generic_params("KC", "#87CEEB"))
        kc_menu.addAction(kc_custom)

        # Trend Following Submenu
        trend_menu = overlap_menu.addMenu("Trend Following")

        # Parabolic SAR
        psar_menu = trend_menu.addMenu("Parabolic SAR")
        add_action(psar_menu, "PSAR (0.02, 0.2) - Standard", "PSAR", {"af": 0.02, "max_af": 0.2}, "#FF69B4")
        add_action(psar_menu, "PSAR (0.01, 0.1) - Konservativ", "PSAR", {"af": 0.01, "max_af": 0.1}, "#FF1493")
        psar_menu.addSeparator()
        psar_custom = QAction("Custom PSAR…", self.parent)
        psar_custom.triggered.connect(lambda: self.prompt_generic_params("PSAR", "#FF69B4"))
        psar_menu.addAction(psar_custom)

        # Ichimoku
        ichimoku_menu = trend_menu.addMenu("Ichimoku Cloud")
        add_action(ichimoku_menu, "Ichimoku (9, 26, 52) - Standard", "ICHIMOKU", {"tenkan": 9, "kijun": 26, "senkou": 52}, "#E6E6FA")
        add_action(ichimoku_menu, "Ichimoku (7, 22, 44) - Crypto", "ICHIMOKU", {"tenkan": 7, "kijun": 22, "senkou": 44}, "#D8BFD8")

        # =====================================================================
        # 2. MOMENTUM & OSZILLATOREN
        # =====================================================================
        mom_menu = root_menu.addMenu("Momentum & Oszillatoren")  # Issue #22: Emoji entfernt

        # RSI
        rsi_menu = mom_menu.addMenu("RSI (Relative Strength)")
        add_action(rsi_menu, "RSI (14) - Standard", "RSI", {"period": 14}, "#FF00FF")
        add_action(rsi_menu, "RSI (7) - Schnell", "RSI", {"period": 7}, "#FF69B4")
        add_action(rsi_menu, "RSI (21) - Langsam", "RSI", {"period": 21}, "#DA70D6")
        rsi_menu.addSeparator()
        rsi_custom = QAction("Custom RSI…", self.parent)
        rsi_custom.triggered.connect(lambda: self.prompt_custom_period("RSI", "#FF00FF"))
        rsi_menu.addAction(rsi_custom)

        # MACD
        macd_menu = mom_menu.addMenu("MACD")
        add_action(macd_menu, "MACD (12, 26, 9) - Standard", "MACD", {"fast": 12, "slow": 26, "signal": 9}, "#00FF00")
        add_action(macd_menu, "MACD (8, 17, 9) - Schnell", "MACD", {"fast": 8, "slow": 17, "signal": 9}, "#32CD32")
        macd_menu.addSeparator()
        macd_custom = QAction("Custom MACD…", self.parent)
        macd_custom.triggered.connect(lambda: self.prompt_generic_params("MACD", "#00FF00"))
        macd_menu.addAction(macd_custom)

        # Stochastic
        stoch_menu = mom_menu.addMenu("Stochastic")
        add_action(stoch_menu, "Stoch (14, 3, 3) - Standard", "STOCH", {"k_period": 14, "d_period": 3, "smooth": 3}, "#0000FF")
        add_action(stoch_menu, "Stoch (5, 3, 3) - Schnell", "STOCH", {"k_period": 5, "d_period": 3, "smooth": 3}, "#4169E1")
        stoch_menu.addSeparator()
        stoch_custom = QAction("Custom Stoch…", self.parent)
        stoch_custom.triggered.connect(lambda: self.prompt_generic_params("STOCH", "#0000FF"))
        stoch_menu.addAction(stoch_custom)

        # CCI
        cci_menu = mom_menu.addMenu("CCI (Commodity Channel)")
        add_action(cci_menu, "CCI (20)", "CCI", {"period": 20}, "#9933FF")
        add_action(cci_menu, "CCI (14)", "CCI", {"period": 14}, "#8A2BE2")
        cci_menu.addSeparator()
        cci_custom = QAction("Custom CCI…", self.parent)
        cci_custom.triggered.connect(lambda: self.prompt_custom_period("CCI", "#9933FF"))
        cci_menu.addAction(cci_custom)

        # MFI
        mfi_menu = mom_menu.addMenu("MFI (Money Flow Index)")
        add_action(mfi_menu, "MFI (14)", "MFI", {"period": 14}, "#33FF99")
        mfi_menu.addSeparator()
        mfi_custom = QAction("Custom MFI…", self.parent)
        mfi_custom.triggered.connect(lambda: self.prompt_custom_period("MFI", "#33FF99"))
        mfi_menu.addAction(mfi_custom)

        # Momentum
        momentum_menu = mom_menu.addMenu("Momentum (MOM)")
        add_action(momentum_menu, "MOM (10)", "MOM", {"period": 10}, "#FF6347")
        add_action(momentum_menu, "MOM (14)", "MOM", {"period": 14}, "#FF4500")
        momentum_menu.addSeparator()
        mom_custom = QAction("Custom MOM…", self.parent)
        mom_custom.triggered.connect(lambda: self.prompt_custom_period("MOM", "#FF6347"))
        momentum_menu.addAction(mom_custom)

        # ROC
        roc_menu = mom_menu.addMenu("ROC (Rate of Change)")
        add_action(roc_menu, "ROC (10)", "ROC", {"period": 10}, "#20B2AA")
        add_action(roc_menu, "ROC (14)", "ROC", {"period": 14}, "#3CB371")
        roc_menu.addSeparator()
        roc_custom = QAction("Custom ROC…", self.parent)
        roc_custom.triggered.connect(lambda: self.prompt_custom_period("ROC", "#20B2AA"))
        roc_menu.addAction(roc_custom)

        # Williams %R
        willr_menu = mom_menu.addMenu("Williams %R")
        add_action(willr_menu, "Williams %R (14)", "WILLR", {"period": 14}, "#8B4513")
        willr_menu.addSeparator()
        willr_custom = QAction("Custom Williams %R…", self.parent)
        willr_custom.triggered.connect(lambda: self.prompt_custom_period("WILLR", "#8B4513"))
        willr_menu.addAction(willr_custom)

        # =====================================================================
        # 3. VOLATILITÄT & TRENDSTÄRKE
        # =====================================================================
        vol_menu = root_menu.addMenu("Volatilität & Trendstärke")  # Issue #22: Emoji entfernt

        # ATR
        atr_menu = vol_menu.addMenu("ATR (Average True Range)")
        add_action(atr_menu, "ATR (14)", "ATR", {"period": 14}, "#FF4500")
        add_action(atr_menu, "ATR (7) - Schnell", "ATR", {"period": 7}, "#FF6347")
        atr_menu.addSeparator()
        atr_custom = QAction("Custom ATR…", self.parent)
        atr_custom.triggered.connect(lambda: self.prompt_custom_period("ATR", "#FF4500"))
        atr_menu.addAction(atr_custom)

        # NATR (Normalized ATR)
        natr_menu = vol_menu.addMenu("NATR (Normalized ATR)")
        add_action(natr_menu, "NATR (14)", "NATR", {"period": 14}, "#FF8C00")
        natr_menu.addSeparator()
        natr_custom = QAction("Custom NATR…", self.parent)
        natr_custom.triggered.connect(lambda: self.prompt_custom_period("NATR", "#FF8C00"))
        natr_menu.addAction(natr_custom)

        # Standard Deviation
        std_menu = vol_menu.addMenu("StdDev (Standard Deviation)")
        add_action(std_menu, "StdDev (20)", "STD", {"period": 20}, "#9370DB")
        std_menu.addSeparator()
        std_custom = QAction("Custom StdDev…", self.parent)
        std_custom.triggered.connect(lambda: self.prompt_custom_period("STD", "#9370DB"))
        std_menu.addAction(std_custom)

        # ADX
        adx_menu = vol_menu.addMenu("ADX (Avg Directional Index)")
        add_action(adx_menu, "ADX (14)", "ADX", {"period": 14}, "#FF6600")
        adx_menu.addSeparator()
        adx_custom = QAction("Custom ADX…", self.parent)
        adx_custom.triggered.connect(lambda: self.prompt_custom_period("ADX", "#FF6600"))
        adx_menu.addAction(adx_custom)

        # Bollinger Derived
        bb_derived = vol_menu.addMenu("Bollinger Derived")
        add_action(bb_derived, "%B (BB Percent)", "BB_PERCENT", {"period": 20, 'std': 2}, "#32CD32")
        add_action(bb_derived, "Bandwidth (BB Width)", "BB_WIDTH", {"period": 20, 'std': 2}, "#4169E1")

        # =====================================================================
        # 4. VOLUMEN INDIKATOREN
        # =====================================================================
        volume_menu = root_menu.addMenu("Volumen")  # Issue #22: Emoji entfernt

        # OBV
        obv_menu = volume_menu.addMenu("OBV (On-Balance Volume)")
        add_action(obv_menu, "OBV", "OBV", {}, "#1E90FF")

        # CMF
        cmf_menu = volume_menu.addMenu("CMF (Chaikin Money Flow)")
        add_action(cmf_menu, "CMF (20)", "CMF", {"period": 20}, "#00CED1")
        add_action(cmf_menu, "CMF (10)", "CMF", {"period": 10}, "#48D1CC")
        cmf_menu.addSeparator()
        cmf_custom = QAction("Custom CMF…", self.parent)
        cmf_custom.triggered.connect(lambda: self.prompt_custom_period("CMF", "#00CED1"))
        cmf_menu.addAction(cmf_custom)

        # A/D Line
        ad_menu = volume_menu.addMenu("A/D (Accumulation/Distribution)")
        add_action(ad_menu, "A/D Line", "AD", {}, "#5F9EA0")

        # Force Index
        fi_menu = volume_menu.addMenu("Force Index")
        add_action(fi_menu, "Force Index (13)", "FI", {"period": 13}, "#6495ED")
        add_action(fi_menu, "Force Index (2) - Schnell", "FI", {"period": 2}, "#4682B4")
        fi_menu.addSeparator()
        fi_custom = QAction("Custom Force Index…", self.parent)
        fi_custom.triggered.connect(lambda: self.prompt_custom_period("FI", "#6495ED"))
        fi_menu.addAction(fi_custom)

        # VWAP (Volume Weighted Average Price)
        vwap_menu = volume_menu.addMenu("VWAP")
        add_action(vwap_menu, "VWAP", "VWAP", {}, "#9932CC")

        # =====================================================================
        # 5. RESET ACTIONS
        # =====================================================================
        root_menu.addSeparator()
        reset_action = QAction("Reset All Indicators", self.parent)  # Issue #22: Emoji entfernt
        reset_action.setToolTip("ENTFERNT alle Indikatoren und setzt den Chart zurück")
        reset_action.triggered.connect(self.on_reset_indicators)
        root_menu.addAction(reset_action)

    def add_primary_actions(self, toolbar: QToolBar) -> None:
        """Add primary action buttons (Load, Refresh, Zoom, etc.)."""
        # Issue #16: Verwende Klassen-Konstanten für einheitliche Button-Höhe
        # Issue #23: Separatoren zwischen Buttons für mehr Abstand
        # Issue #24: Bitunix und Strategy Settings aus Row2 hierher verschoben

        # Issue #16 & #17: Load Chart Button mit Theme-Styling
        self.parent.load_button = QPushButton("Load Chart")  # Issue #15: Emoji entfernt
        self.parent.load_button.setIcon(get_icon("chart_load"))  # Issue #17: Nur weißes Icon (altes Icon entfernt)
        self.parent.load_button.setIconSize(self.ICON_SIZE)  # Issue #15: Klassen-Konstante
        self.parent.load_button.clicked.connect(self.parent._on_load_chart)
        self.parent.load_button.setToolTip("Chart für aktuelles Symbol laden")
        self.parent.load_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16: Klassen-Konstante (32px)
        self.parent.load_button.setProperty("class", "toolbar-button")  # Issue #16 & #17: Theme-Klasse verwenden
        toolbar.addWidget(self.parent.load_button)
        toolbar.addSeparator()  # Issue #23: Mehr Abstand

        self.parent.refresh_button = QPushButton("Refresh")  # Issue #15: Emoji entfernt
        self.parent.refresh_button.setIcon(get_icon("refresh"))  # Issue #15
        self.parent.refresh_button.setIconSize(self.ICON_SIZE)  # Issue #15: Klassen-Konstante
        self.parent.refresh_button.clicked.connect(self.parent._on_refresh)
        self.parent.refresh_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16: Klassen-Konstante
        toolbar.addWidget(self.parent.refresh_button)
        toolbar.addSeparator()  # Issue #23: Mehr Abstand

        self.parent.zoom_all_button = QPushButton("Alles zoomen")  # Issue #15: Emoji entfernt
        self.parent.zoom_all_button.setIcon(get_icon("zoom_all"))  # Issue #15
        self.parent.zoom_all_button.setIconSize(self.ICON_SIZE)  # Issue #15: Klassen-Konstante
        self.parent.zoom_all_button.setToolTip(
            "Gesamten Chart einpassen und Pane-Höhen sinnvoll setzen"
        )
        self.parent.zoom_all_button.clicked.connect(self.on_zoom_all)
        self.parent.zoom_all_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16: Klassen-Konstante
        toolbar.addWidget(self.parent.zoom_all_button)
        toolbar.addSeparator()  # Issue #23: Mehr Abstand

        self.parent.zoom_back_button = QPushButton("Zurück")  # Issue #15: Emoji entfernt
        self.parent.zoom_back_button.setIcon(get_icon("back"))  # Issue #15
        self.parent.zoom_back_button.setIconSize(self.ICON_SIZE)  # Issue #15: Klassen-Konstante
        self.parent.zoom_back_button.setToolTip("Zur vorherigen Ansicht zurückkehren")
        self.parent.zoom_back_button.clicked.connect(self.on_zoom_back)
        self.parent.zoom_back_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16: Klassen-Konstante
        toolbar.addWidget(self.parent.zoom_back_button)
        toolbar.addSeparator()  # Issue #23: Separator nach Zurück

        # Issue #24: Bitunix Button von Row2 hierher verschoben
        self.parent.bitunix_trading_button = QPushButton("Bitunix")
        self.parent.bitunix_trading_button.setIcon(get_icon("currency_exchange"))
        self.parent.bitunix_trading_button.setIconSize(self.ICON_SIZE)
        self.parent.bitunix_trading_button.setCheckable(True)
        self.parent.bitunix_trading_button.setToolTip(
            "Bitunix Futures Trading öffnen/schließen (nur Crypto)"
        )
        self.parent.bitunix_trading_button.setProperty("class", "toolbar-button")
        self.parent.bitunix_trading_button.setFixedHeight(self.BUTTON_HEIGHT)
        self.parent.bitunix_trading_button.setVisible(True)
        self.parent.bitunix_trading_button.setFixedHeight(self.BUTTON_HEIGHT)
        self.parent.bitunix_trading_button.setVisible(True)
        # Style is now handled globally in themes.py (Issue #28)
        toolbar.addWidget(self.parent.bitunix_trading_button)
        logger.debug("Toolbar Row1: Bitunix button added (Issue #24)")

        # Issue #24: Strategy Settings Button von Row2 hierher verschoben
        self.parent.chart_strategy_settings_btn = QPushButton("Strategy Settings")
        self.parent.chart_strategy_settings_btn.setIcon(get_icon("strategy_settings"))
        self.parent.chart_strategy_settings_btn.setIconSize(self.ICON_SIZE)
        self.parent.chart_strategy_settings_btn.setCheckable(True)  # Issue #28: Checkable für active state
        self.parent.chart_strategy_settings_btn.setToolTip(
            "Strategy Settings öffnen\n"
            "- JSON Strategy Config auswählen\n"
            "- CEL RulePacks laden\n"
            "- Aktuelles Regime & Matched Strategy anzeigen"
        )
        self.parent.chart_strategy_settings_btn.setFixedHeight(self.BUTTON_HEIGHT)
        self.parent.chart_strategy_settings_btn.setProperty("class", "toolbar-button")
        self.parent.chart_strategy_settings_btn.setFixedHeight(self.BUTTON_HEIGHT)
        self.parent.chart_strategy_settings_btn.setProperty("class", "toolbar-button")
        # Style is now handled globally in themes.py (Issue #28)
        self.parent.chart_strategy_settings_btn.clicked.connect(self._on_strategy_settings_clicked)
        toolbar.addWidget(self.parent.chart_strategy_settings_btn)
        logger.debug("Toolbar Row1: Strategy Settings button added (Issue #24)")
