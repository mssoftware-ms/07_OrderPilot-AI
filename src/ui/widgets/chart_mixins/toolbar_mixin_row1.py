"""Toolbar Mixin Row 1 - Timeframe, Period, Indicators, Primary Actions.

Module 1/4 of toolbar_mixin.py split.

Contains Row 1 toolbar builders:
- Timeframe selector
- Period selector
- Indicators menu (massive tree with 50+ indicators)
- Primary actions (Load, Refresh, Zoom)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QComboBox, QLabel, QMenu, QPushButton, QToolBar

from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolbarMixinRow1:
    """Row 1 toolbar builders (timeframe, period, indicators, primary actions)."""

    # Issue #16: Einheitliche Button-Höhe und Icon-Größe (konsistent mit Row2)
    BUTTON_HEIGHT = 32
    ICON_SIZE = QSize(20, 20)

    def __init__(self, parent):
        self.parent = parent

    def build_toolbar_row1(self, toolbar: QToolBar) -> None:
        """Build toolbar row 1."""
        # Symbol-Selector entfernt (Issue #20, #30) - Symbol wird über ChartWindow gesteuert
        self.add_timeframe_selector(toolbar)
        toolbar.addSeparator()
        self.add_period_selector(toolbar)
        toolbar.addSeparator()
        self.add_indicators_menu(toolbar)
        toolbar.addSeparator()
        self.add_primary_actions(toolbar)

    def add_timeframe_selector(self, toolbar: QToolBar) -> None:
        # Issue #22: Label entfernt, Tooltip stattdessen
        self.parent.timeframe_combo = QComboBox()
        self.parent.timeframe_combo.setToolTip("Kerzen-Zeitrahmen wählen")
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
        # Issue #22: Label entfernt, Tooltip stattdessen
        self.parent.period_combo = QComboBox()
        self.parent.period_combo.setToolTip("Darstellungs-Zeitraum wählen")
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
        # Issue #22: Label entfernt
        self.parent.indicators_button = QPushButton("Indikatoren")  # Issue #15: Emoji entfernt
        self.parent.indicators_button.setIcon(get_icon("indicators"))  # Issue #22: Spezifisches Icon
        self.parent.indicators_button.setIconSize(self.ICON_SIZE)  # Issue #15: Klassen-Konstante
        self.parent.indicators_button.setToolTip("Indikatoren hinzufügen/entfernen")  # Issue #22: Kürzerer Tooltip
        self.parent.indicators_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16: Klassen-Konstante

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

    def prompt_custom_period(self, ind_id: str, color: str) -> None:
        from PyQt6.QtWidgets import QInputDialog
        period, ok = QInputDialog.getInt(self.parent, "Periode wählen", f"{ind_id} Periode:", value=14, min=1, max=500)
        if ok:
            self.on_indicator_add(ind_id, {"period": period}, color)

    def prompt_generic_params(self, ind_id: str, color: str) -> None:
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self.parent, "Parameter", f"{ind_id} Parameter (key=value,comma-separated):", text="period=20")
        if not ok:
            return
        params = {}
        try:
            for part in text.split(","):
                k, v = part.split("=")
                params[k.strip()] = float(v) if "." in v else int(v)
            self.on_indicator_add(ind_id, params, color)
        except Exception:
            logger.error("Parameter-Parsing fehlgeschlagen: %s", text)

    def refresh_active_indicator_menu(self) -> None:
        """Show active indicators as remove-actions directly in main menu."""
        if not hasattr(self.parent, "indicators_menu"):
            return
        # remove old actions
        if getattr(self.parent, "_remove_actions", None):
            for act in self.parent._remove_actions:
                self.parent.indicators_menu.removeAction(act)
        if getattr(self.parent, "_remove_section_separator", None):
            self.parent.indicators_menu.removeAction(self.parent._remove_section_separator)
        self.parent._remove_actions = []
        self.parent._remove_section_separator = None

        if not hasattr(self.parent, "chart_widget") or not getattr(self.parent.chart_widget, "active_indicators", None):
            return

        if self.parent.chart_widget.active_indicators:
            self.parent._remove_section_separator = self.parent.indicators_menu.addSeparator()
            for instance_id, inst in self.parent.chart_widget.active_indicators.items():
                label = f"Remove: {inst.display_name}"
                act = QAction(label, self.parent)
                act.triggered.connect(lambda _=False, iid=instance_id: self.on_indicator_remove(iid))
                self.parent.indicators_menu.addAction(act)
                self.parent._remove_actions.append(act)

    # Hooks into IndicatorMixin
    def on_indicator_add(self, ind_id: str, params: dict, color: str) -> None:
        if hasattr(self.parent, "chart_widget") and hasattr(self.parent.chart_widget, "_add_indicator_instance"):
            self.parent.chart_widget._add_indicator_instance(ind_id, params, color)
            self.refresh_active_indicator_menu()

    def on_indicator_remove(self, instance_id: str) -> None:
        if hasattr(self.parent, "chart_widget") and hasattr(self.parent.chart_widget, "_remove_indicator_instance"):
            self.parent.chart_widget._remove_indicator_instance(instance_id)
            self.refresh_active_indicator_menu()

    def on_reset_indicators(self) -> None:
        """Completely clear all indicators from the chart."""
        if hasattr(self.parent, "chart_widget"):
            chart = self.parent.chart_widget
            if hasattr(chart, "_cleanup_all_chart_indicators"):
                chart._cleanup_all_chart_indicators()
            
            # Explicitly clear active_indicators and counter
            if hasattr(chart, "active_indicators"):
                chart.active_indicators.clear()
            if hasattr(chart, "_indicator_counter"):
                chart._indicator_counter = 0
                
            self.refresh_active_indicator_menu()
            if hasattr(chart, "_update_indicators_button_badge"):
                chart._update_indicators_button_badge()
            
            logger.info("Nuclear reset: All indicators cleared from chart")

    def add_primary_actions(self, toolbar: QToolBar) -> None:
        # Issue #16: Verwende Klassen-Konstanten für einheitliche Button-Höhe
        # Issue #23: Separatoren zwischen Buttons für mehr Abstand
        # Issue #24: Bitunix und Strategy Settings aus Row2 hierher verschoben

        self.parent.load_button = QPushButton("Load Chart")  # Issue #15: Emoji entfernt
        self.parent.load_button.setIcon(get_icon("chart_load"))  # Issue #15
        self.parent.load_button.setIconSize(self.ICON_SIZE)  # Issue #15: Klassen-Konstante
        self.parent.load_button.clicked.connect(self.parent._on_load_chart)
        self.parent.load_button.setProperty("class", "primary")
        self.parent.load_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16: Klassen-Konstante
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

    def on_zoom_all(self):
        """Zoom chart to show all data with sane pane heights."""
        try:
            if hasattr(self.parent, "zoom_to_fit_all"):
                self.parent.zoom_to_fit_all()
            else:
                logger.warning("zoom_to_fit_all not available on chart widget")
        except Exception as e:
            logger.error("Zoom-All failed: %s", e, exc_info=True)

    def on_zoom_back(self):
        """Restore previous view (visible range + pane heights)."""
        try:
            if hasattr(self.parent, "zoom_back_to_previous_view"):
                restored = self.parent.zoom_back_to_previous_view()
                if not restored:
                    logger.info("No previous view state to restore")
            else:
                logger.warning("zoom_back_to_previous_view not available on chart widget")
        except Exception as e:
            logger.error("Zoom-Back failed: %s", e, exc_info=True)

    def on_load_chart(self) -> None:
        """Handle load chart button - reload current symbol."""
        try:
            if hasattr(self.parent, 'current_symbol') and self.parent.current_symbol:
                symbol = self.parent.current_symbol
                provider = getattr(self.parent, 'current_data_provider', None)
                logger.info(f"Reloading chart for {symbol}")
                # Use qasync to run async method
                import qasync
                import asyncio
                if hasattr(self.parent, 'load_symbol'):
                    asyncio.ensure_future(self.parent.load_symbol(symbol, provider))
            else:
                logger.warning("No current symbol to load")
        except Exception as e:
            logger.error(f"Load chart failed: {e}", exc_info=True)

    def on_refresh(self) -> None:
        """Handle refresh button - same as load chart."""
        self.on_load_chart()

    def _on_strategy_settings_clicked(self) -> None:
        """Handle Strategy Settings button click - opens Strategy Settings Dialog."""
        try:
            from src.ui.dialogs.strategy_settings_dialog import StrategySettingsDialog

            # Find chart window - self.parent is EmbeddedTradingViewChart
            # We need to go up to find ChartWindow
            widget = self.parent
            chart_window = None

            # Try to find ChartWindow in parent hierarchy
            for _ in range(5):  # Max 5 levels up
                if widget is None:
                    break
                # Check if this widget has bot_controller (likely ChartWindow)
                if hasattr(widget, 'bot_controller'):
                    chart_window = widget
                    break
                # Check class name as fallback
                if widget.__class__.__name__ == 'ChartWindow':
                    chart_window = widget
                    break
                widget = widget.parent()

            if chart_window is None:
                logger.warning("Could not find ChartWindow - using parent widget as fallback")
                chart_window = self.parent

            # Open Strategy Settings Dialog
            dialog = StrategySettingsDialog(chart_window)
            result = dialog.exec()

            # Issue #32: Reset button after dialog closes
            if hasattr(self.parent, 'chart_strategy_settings_btn'):
                self.parent.chart_strategy_settings_btn.setChecked(False)

            if result:  # Dialog was accepted (OK/Apply clicked)
                # Check if dialog has methods to get config
                if hasattr(dialog, 'get_selected_config_path'):
                    config_path = dialog.get_selected_config_path()
                    if config_path:
                        logger.info(f"Strategy config selected: {config_path}")

                        # Try to load config in bot controller if available
                        if hasattr(chart_window, 'bot_controller') and chart_window.bot_controller:
                            try:
                                if hasattr(chart_window.bot_controller, 'load_rulepack'):
                                    chart_window.bot_controller.load_rulepack(config_path)
                                    logger.info(f"RulePack loaded: {config_path}")
                                elif hasattr(chart_window.bot_controller, 'set_json_config'):
                                    chart_window.bot_controller.set_json_config(config_path)
                                    logger.info(f"JSON config loaded: {config_path}")
                            except Exception as e:
                                logger.error(f"Failed to load config: {e}")
                                from PyQt6.QtWidgets import QMessageBox
                                QMessageBox.warning(
                                    chart_window,
                                    "Config Load Error",
                                    f"Fehler beim Laden der Config:\n{e}"
                                )
                else:
                    logger.info("Strategy Settings Dialog closed without selection")
            else:
                logger.debug("Strategy Settings Dialog cancelled")

        except ImportError as e:
            logger.warning(f"StrategySettingsDialog not available: {e}")
            # Fallback: show simple message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self.parent,
                "Strategy Settings",
                "Strategy Settings Dialog ist noch nicht implementiert.\n"
                "Bitte verwenden Sie den '⚙️ Settings Bot' Button im Trading Tab."
            )
        except Exception as e:
            logger.error(f"Error opening Strategy Settings Dialog: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Fehler beim Öffnen des Strategy Settings Dialogs:\n{e}"
            )
