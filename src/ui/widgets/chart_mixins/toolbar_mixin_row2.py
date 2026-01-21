"""Toolbar Mixin Row 2 - Live Stream, Regime Badge, Chart Marking, AI Buttons.

Module 2/4 of toolbar_mixin.py split.

Contains Row 2 toolbar builders:
- Live stream toggle
- Regime badge
- Chart marking button (massive menu with 85 LOC)
- AI Chat button
- AI Analysis button
- Bitunix trading button
- Bot toggle button
- Market status label
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLabel, QMenu, QPushButton, QToolBar

from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolbarMixinRow2:
    """Row 2 toolbar builders (live stream, regime, chart marking, AI, bot, market status)."""

    # Issue #16: Einheitliche Button-Höhe für alle Toolbar-Buttons
    BUTTON_HEIGHT = 32
    ICON_SIZE = QSize(20, 20)  # Issue #15: Einheitliche Icon-Größe

    def __init__(self, parent):
        self.parent = parent

    def build_toolbar_row2(self, toolbar: QToolBar) -> None:
        """Build toolbar row 2."""
        self.add_live_stream_toggle(toolbar)
        toolbar.addSeparator()
        self.add_regime_badge_to_toolbar(toolbar)  # Phase 2.2: Regime Badge
        toolbar.addSeparator()
        self.add_chart_marking_button(toolbar)
        # Levels + Export buttons are in ToolbarMixinFeatures
        self.add_entry_analyzer_button(toolbar)  # Phase 5: Entry Analyzer
        self.add_strategy_concept_button(toolbar)  # Phase 6: Strategy Concept
        self.add_cel_editor_button(toolbar)  # Phase 7: CEL Editor
        self.add_ai_chat_button(toolbar)
        self.add_ai_analysis_button(toolbar)
        # Issue #24: Bitunix und Strategy Settings zu Row1 verschoben
        # self.add_bitunix_trading_button(toolbar)  # Jetzt in Row1
        self.add_settings_button(toolbar)
        toolbar.addSeparator()
        # self.add_strategy_settings_button(toolbar)  # Jetzt in Row1
        self.add_bot_toggle_button(toolbar)
        toolbar.addSeparator()
        self.add_market_status(toolbar)

    def add_regime_badge_to_toolbar(self, toolbar: QToolBar) -> None:
        """Add regime badge to toolbar (Phase 2.2)."""
        try:
            from src.ui.widgets.regime_badge_widget import RegimeBadgeWidget

            toolbar.addWidget(QLabel("Regime:"))
            self.parent._regime_badge = RegimeBadgeWidget(compact=True, show_icon=True)
            self.parent._regime_badge.clicked.connect(self.on_regime_badge_clicked)
            toolbar.addWidget(self.parent._regime_badge)
            logger.debug("Regime badge added to toolbar")
        except ImportError as e:
            logger.warning(f"Could not add regime badge: {e}")
            # Fallback: simple label
            self.parent._regime_label = QLabel("N/A")
            self.parent._regime_label.setStyleSheet("color: #888; padding: 5px;")
            toolbar.addWidget(QLabel("Regime:"))
            toolbar.addWidget(self.parent._regime_label)

    def on_regime_badge_clicked(self) -> None:
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
        if hasattr(self.parent, "_regime_badge") and self.parent._regime_badge:
            self.parent._regime_badge.set_regime(regime, adx, gate_reason, allows_entry)
        elif hasattr(self.parent, "_regime_label"):
            self.parent._regime_label.setText(regime[:10])

    def update_regime_from_result(self, result) -> None:
        """
        Update regime badge from RegimeResult.

        Args:
            result: RegimeResult from RegimeDetectorService
        """
        if hasattr(self.parent, "_regime_badge") and self.parent._regime_badge:
            self.parent._regime_badge.set_regime_from_result(result)

    def add_live_stream_toggle(self, toolbar: QToolBar) -> None:
        self.parent.live_stream_button = QPushButton("Live")  # Issue #15: Emoji entfernt
        self.parent.live_stream_button.setIcon(get_icon("live"))  # Issue #15
        self.parent.live_stream_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.live_stream_button.setCheckable(True)
        self.parent.live_stream_button.setToolTip("Toggle real-time streaming (WebSocket)")
        self.parent.live_stream_button.clicked.connect(self.parent._toggle_live_stream)
        self.parent.live_stream_button.setProperty("class", "toolbar-button")
        self.parent.live_stream_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16
        toolbar.addWidget(self.parent.live_stream_button)

    def add_chart_marking_button(self, toolbar: QToolBar) -> None:
        self.parent.chart_marking_button = QPushButton("Markierungen")  # Issue #15: Emoji entfernt
        self.parent.chart_marking_button.setIcon(get_icon("draw"))  # Issue #15
        self.parent.chart_marking_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.chart_marking_button.setToolTip(
            "Chart-Markierungen hinzufügen (Rechtsklick auf Chart für Menü)"
        )
        self.parent.chart_marking_button.setProperty("class", "toolbar-button")
        self.parent.chart_marking_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16
        self.parent.chart_marking_menu = QMenu(self.parent)
        self._build_chart_marking_menu()
        self.parent.chart_marking_button.setMenu(self.parent.chart_marking_menu)
        toolbar.addWidget(self.parent.chart_marking_button)

    def _build_chart_marking_menu(self) -> None:
        """Build massive chart marking menu (85 LOC)."""
        entry_menu = self.parent.chart_marking_menu.addMenu("📍 Entry Marker")
        long_action = QAction("🟢 Long Entry", self.parent)
        long_action.triggered.connect(lambda: self.parent._add_test_entry_marker("long"))
        entry_menu.addAction(long_action)
        short_action = QAction("🔴 Short Entry", self.parent)
        short_action.triggered.connect(lambda: self.parent._add_test_entry_marker("short"))
        entry_menu.addAction(short_action)

        zone_menu = self.parent.chart_marking_menu.addMenu("📊 Zonen")
        support_action = QAction("🟢 Support Zone", self.parent)
        support_action.triggered.connect(lambda: self.parent._add_test_zone("support"))
        zone_menu.addAction(support_action)
        resistance_action = QAction("🔴 Resistance Zone", self.parent)
        resistance_action.triggered.connect(lambda: self.parent._add_test_zone("resistance"))
        zone_menu.addAction(resistance_action)
        zone_menu.addSeparator()
        demand_action = QAction("🟢 Demand Zone", self.parent)
        demand_action.triggered.connect(lambda: self.parent._add_test_zone("demand"))
        zone_menu.addAction(demand_action)
        supply_action = QAction("🔴 Supply Zone", self.parent)
        supply_action.triggered.connect(lambda: self.parent._add_test_zone("supply"))
        zone_menu.addAction(supply_action)

        structure_menu = self.parent.chart_marking_menu.addMenu("📈 Structure Breaks")
        bos_bull = QAction("⬆️ BoS Bullish", self.parent)
        bos_bull.triggered.connect(lambda: self.parent._add_test_structure("bos", True))
        structure_menu.addAction(bos_bull)
        bos_bear = QAction("⬇️ BoS Bearish", self.parent)
        bos_bear.triggered.connect(lambda: self.parent._add_test_structure("bos", False))
        structure_menu.addAction(bos_bear)
        structure_menu.addSeparator()
        choch_bull = QAction("⬆️ CHoCH Bullish", self.parent)
        choch_bull.triggered.connect(lambda: self.parent._add_test_structure("choch", True))
        structure_menu.addAction(choch_bull)
        choch_bear = QAction("⬇️ CHoCH Bearish", self.parent)
        choch_bear.triggered.connect(lambda: self.parent._add_test_structure("choch", False))
        structure_menu.addAction(choch_bear)
        structure_menu.addSeparator()
        msb_bull = QAction("⬆️ MSB Bullish", self.parent)
        msb_bull.triggered.connect(lambda: self.parent._add_test_structure("msb", True))
        structure_menu.addAction(msb_bull)
        msb_bear = QAction("⬇️ MSB Bearish", self.parent)
        msb_bear.triggered.connect(lambda: self.parent._add_test_structure("msb", False))
        structure_menu.addAction(msb_bear)

        lines_menu = self.parent.chart_marking_menu.addMenu("📏 Linien")
        sl_long = QAction("🔴 Stop Loss (Long)", self.parent)
        sl_long.triggered.connect(lambda: self.parent._add_test_line("sl", True))
        lines_menu.addAction(sl_long)
        sl_short = QAction("🔴 Stop Loss (Short)", self.parent)
        sl_short.triggered.connect(lambda: self.parent._add_test_line("sl", False))
        lines_menu.addAction(sl_short)
        lines_menu.addSeparator()
        tp_long = QAction("🟢 Take Profit (Long)", self.parent)
        tp_long.triggered.connect(lambda: self.parent._add_test_line("tp", True))
        lines_menu.addAction(tp_long)
        tp_short = QAction("🟢 Take Profit (Short)", self.parent)
        tp_short.triggered.connect(lambda: self.parent._add_test_line("tp", False))
        lines_menu.addAction(tp_short)
        lines_menu.addSeparator()
        entry_line = QAction("🔵 Entry Line", self.parent)
        entry_line.triggered.connect(lambda: self.parent._add_test_line("entry", True))
        lines_menu.addAction(entry_line)
        trailing = QAction("🟡 Trailing Stop", self.parent)
        trailing.triggered.connect(lambda: self.parent._add_test_line("trailing", True))
        lines_menu.addAction(trailing)

        self.parent.chart_marking_menu.addSeparator()
        clear_markers = QAction("🗑️ Alle Marker löschen", self.parent)
        clear_markers.triggered.connect(self.parent._clear_all_markers)
        self.parent.chart_marking_menu.addAction(clear_markers)
        clear_zones = QAction("🗑️ Alle Zonen löschen", self.parent)
        clear_zones.triggered.connect(self.parent._clear_zones_with_js)
        self.parent.chart_marking_menu.addAction(clear_zones)
        clear_lines = QAction("🗑️ Alle Linien löschen", self.parent)
        clear_lines.triggered.connect(self.parent._clear_lines_with_js)
        self.parent.chart_marking_menu.addAction(clear_lines)
        clear_drawings = QAction("🗑️ Alle Zeichnungen löschen", self.parent)
        clear_drawings.triggered.connect(self.parent._clear_all_drawings)
        self.parent.chart_marking_menu.addAction(clear_drawings)
        self.parent.chart_marking_menu.addSeparator()
        clear_all = QAction("🗑️ Alles löschen", self.parent)
        clear_all.triggered.connect(self.parent._clear_all_markings)
        self.parent.chart_marking_menu.addAction(clear_all)

    def add_entry_analyzer_button(self, toolbar: QToolBar) -> None:
        """Add Entry Analyzer button to toolbar (Phase 5)."""
        self.parent.entry_analyzer_button = QPushButton("Entry Analyzer")  # Issue #15: Emoji entfernt
        self.parent.entry_analyzer_button.setIcon(get_icon("entry_analyzer"))  # Issue #15
        self.parent.entry_analyzer_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.entry_analyzer_button.setCheckable(True)  # Issue #28: Checkable für active state
        self.parent.entry_analyzer_button.setToolTip(
            "Entry Analyzer öffnen - Findet optimale Einstiegspunkte"
        )
        self.parent.entry_analyzer_button.setProperty("class", "toolbar-button")
        self.parent.entry_analyzer_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16
        # Issue #28: Active state styling (orange background/text when checked)
        self.parent.entry_analyzer_button.setStyleSheet("""
            QPushButton:checked {
                background-color: #FF6B35;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked:hover {
                background-color: #FF8C61;
            }
        """)
        self.parent.entry_analyzer_button.clicked.connect(self._on_entry_analyzer_clicked)
        toolbar.addWidget(self.parent.entry_analyzer_button)
        logger.info("Toolbar: Entry Analyzer button added")

    def _on_entry_analyzer_clicked(self) -> None:
        """Handle Entry Analyzer button click (Issue #32: Toggle-aware)."""
        # Issue #32: Button ist checkable, sync mit Panel-Visibility
        if not hasattr(self.parent, 'entry_analyzer_button'):
            return

        checked = self.parent.entry_analyzer_button.isChecked()

        if checked:
            if hasattr(self.parent, "show_entry_analyzer"):
                self.parent.show_entry_analyzer()
            else:
                logger.warning("show_entry_analyzer not available on chart widget")
                self.parent.entry_analyzer_button.setChecked(False)
        else:
            # Toggle off - hide panel if it exists
            if hasattr(self.parent, "hide_entry_analyzer"):
                self.parent.hide_entry_analyzer()
            else:
                logger.warning("hide_entry_analyzer not available on chart widget")

    def add_strategy_concept_button(self, toolbar: QToolBar) -> None:
        """Add Strategy Concept button to toolbar (Phase 6)."""
        self.parent.strategy_concept_button = QPushButton("Strategy Concept")  # Issue #15: Emoji entfernt
        self.parent.strategy_concept_button.setIcon(get_icon("strategy_concept"))  # Issue #15
        self.parent.strategy_concept_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.strategy_concept_button.setCheckable(True)  # Issue #28: Checkable für active state
        self.parent.strategy_concept_button.setToolTip(
            "Strategy Concept öffnen - Pattern-basierte Trading Strategien (Ctrl+Shift+S)"
        )
        self.parent.strategy_concept_button.setProperty("class", "toolbar-button")
        self.parent.strategy_concept_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16
        # Issue #28: Active state styling (orange background/text when checked)
        self.parent.strategy_concept_button.setStyleSheet("""
            QPushButton:checked {
                background-color: #FF6B35;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked:hover {
                background-color: #FF8C61;
            }
        """)
        self.parent.strategy_concept_button.clicked.connect(self._on_strategy_concept_clicked)
        toolbar.addWidget(self.parent.strategy_concept_button)
        logger.info("Toolbar: Strategy Concept button added")

    def _on_strategy_concept_clicked(self) -> None:
        """Handle Strategy Concept button click (Issue #32: Toggle-aware)."""
        # Issue #32: Button ist checkable, sync mit Window-Visibility
        if not hasattr(self.parent, 'strategy_concept_button'):
            return

        checked = self.parent.strategy_concept_button.isChecked()

        if checked:
            if hasattr(self.parent, "show_strategy_concept"):
                self.parent.show_strategy_concept()
            else:
                logger.warning("show_strategy_concept not available on chart widget")
                self.parent.strategy_concept_button.setChecked(False)
        else:
            # Toggle off - hide window if it exists
            if hasattr(self.parent, "hide_strategy_concept"):
                self.parent.hide_strategy_concept()
            else:
                logger.warning("hide_strategy_concept not available on chart widget")

    def add_cel_editor_button(self, toolbar: QToolBar) -> None:
        """Add CEL Editor button to toolbar (Phase 7)."""
        self.parent.cel_editor_button = QPushButton("CEL Editor")
        self.parent.cel_editor_button.setIcon(get_icon("candlestick_chart"))  # Trading/candlestick chart icon
        self.parent.cel_editor_button.setIconSize(self.ICON_SIZE)
        self.parent.cel_editor_button.setCheckable(True)  # Toggle-aware
        self.parent.cel_editor_button.setToolTip(
            "CEL Editor öffnen - Visual Pattern Builder mit AI-Assistent (Ctrl+Shift+E)"
        )
        self.parent.cel_editor_button.setProperty("class", "toolbar-button")
        self.parent.cel_editor_button.setFixedHeight(self.BUTTON_HEIGHT)
        # Active state styling (orange background/text when checked)
        self.parent.cel_editor_button.setStyleSheet("""
            QPushButton:checked {
                background-color: #FF6B35;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked:hover {
                background-color: #FF8C61;
            }
        """)
        self.parent.cel_editor_button.clicked.connect(self._on_cel_editor_clicked)
        toolbar.addWidget(self.parent.cel_editor_button)
        logger.info("Toolbar: CEL Editor button added")

    def _on_cel_editor_clicked(self) -> None:
        """Handle CEL Editor button click (Toggle-aware)."""
        if not hasattr(self.parent, 'cel_editor_button'):
            return

        checked = self.parent.cel_editor_button.isChecked()

        if checked:
            if hasattr(self.parent, "show_cel_editor"):
                self.parent.show_cel_editor()
            else:
                logger.warning("show_cel_editor not available on chart widget")
                self.parent.cel_editor_button.setChecked(False)
        else:
            # Toggle off - hide window if it exists
            if hasattr(self.parent, "hide_cel_editor"):
                self.parent.hide_cel_editor()
            else:
                logger.warning("hide_cel_editor not available on chart widget")

    def add_ai_chat_button(self, toolbar: QToolBar) -> None:
        self.parent.ai_chat_button = QPushButton("AI Chat")  # Issue #15: Emoji entfernt
        self.parent.ai_chat_button.setIcon(get_icon("chat"))  # Issue #15
        self.parent.ai_chat_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.ai_chat_button.setCheckable(True)
        self.parent.ai_chat_button.setToolTip(
            "AI Chart-Analyse öffnen/schließen (Ctrl+Shift+C)"
        )
        self.parent.ai_chat_button.setProperty("class", "toolbar-button")
        self.parent.ai_chat_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16
        # Issue #28: Active state styling (orange background/text when checked)
        self.parent.ai_chat_button.setStyleSheet("""
            QPushButton:checked {
                background-color: #FF6B35;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked:hover {
                background-color: #FF8C61;
            }
        """)
        toolbar.addWidget(self.parent.ai_chat_button)

    def add_ai_analysis_button(self, toolbar: QToolBar) -> None:
        self.parent.ai_analysis_button = QPushButton("AI Analyse")  # Issue #15: Emoji entfernt
        self.parent.ai_analysis_button.setIcon(get_icon("lightbulb"))  # Issue #15
        self.parent.ai_analysis_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.ai_analysis_button.setCheckable(True)
        self.parent.ai_analysis_button.setToolTip(
            "Deep Market Analysis Popup öffnen"
        )
        self.parent.ai_analysis_button.setProperty("class", "toolbar-button")
        self.parent.ai_analysis_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16
        # Issue #28: Active state styling (orange background/text when checked)
        self.parent.ai_analysis_button.setStyleSheet("""
            QPushButton:checked {
                background-color: #FF6B35;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked:hover {
                background-color: #FF8C61;
            }
        """)
        toolbar.addWidget(self.parent.ai_analysis_button)

    # Issue #24: Methode entfernt - Button ist jetzt in Row1 (toolbar_mixin_row1.py)
    # def add_bitunix_trading_button(self, toolbar: QToolBar) -> None:
    #     """Add Bitunix trading button to toolbar (initially hidden)."""
    #     ...

    def add_settings_button(self, toolbar: QToolBar) -> None:
        """Add settings button (gear icon) to toolbar."""
        self.parent.settings_button = QPushButton()
        self.parent.settings_button.setIcon(get_icon("settings"))
        self.parent.settings_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.settings_button.setToolTip("Settings öffnen")
        self.parent.settings_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16
        self.parent.settings_button.setFixedWidth(self.BUTTON_HEIGHT)  # Issue #25: Breite = Höhe für quadratischen Icon-Button
        self.parent.settings_button.setProperty("class", "icon-button")
        self.parent.settings_button.clicked.connect(self._open_settings_dialog)
        toolbar.addWidget(self.parent.settings_button)

    def _open_settings_dialog(self) -> None:
        if hasattr(self.parent, "open_main_settings_dialog"):
            self.parent.open_main_settings_dialog()
            return
        widget = self.parent
        while widget is not None:
            if hasattr(widget, "show_settings_dialog"):
                widget.show_settings_dialog()
                return
            widget = widget.parent()
        logger.warning("Settings dialog not available from toolbar")

    # Issue #24: Methode entfernt - Button und Event Handler sind jetzt in Row1 (toolbar_mixin_row1.py)
    # def add_strategy_settings_button(self, toolbar: QToolBar) -> None:
    #     """Add Strategy Settings button to chart toolbar (opens Strategy Settings Dialog)."""
    #     ...

    # def _on_strategy_settings_clicked(self) -> None:
    #     """Handle Strategy Settings button click - opens Strategy Settings Dialog."""
    #     ...

    def add_bot_toggle_button(self, toolbar: QToolBar) -> None:
        self.parent.toggle_panel_button = QPushButton("Trading Bot")  # Issue #15: Emoji entfernt
        self.parent.toggle_panel_button.setIcon(get_icon("bot"))  # Issue #15
        self.parent.toggle_panel_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.toggle_panel_button.setCheckable(True)
        self.parent.toggle_panel_button.setChecked(True)
        self.parent.toggle_panel_button.setToolTip("Trading Bot Panel ein-/ausblenden")
        self.parent.toggle_panel_button.setProperty("class", "toolbar-button")
        self.parent.toggle_panel_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16
        # Issue #28: Active state styling (orange background/text when checked)
        self.parent.toggle_panel_button.setStyleSheet("""
            QPushButton:checked {
                background-color: #FF6B35;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked:hover {
                background-color: #FF8C61;
            }
        """)
        toolbar.addWidget(self.parent.toggle_panel_button)

    def add_market_status(self, toolbar: QToolBar) -> None:
        self.parent.market_status_label = QLabel("Ready")
        self.parent.market_status_label.setStyleSheet(
            "color: #888; font-weight: bold; padding: 5px;"
        )
        toolbar.addWidget(self.parent.market_status_label)

    # =========================================================================
    # Issue #12: Clear Methods (called by ToolbarMixin delegation)
    # =========================================================================

    def clear_all_markers(self) -> None:
        """Clear all entry and structure markers."""
        # Use methods from ChartMarkingMixin
        if hasattr(self.parent, 'clear_entry_markers'):
            self.parent.clear_entry_markers()
        if hasattr(self.parent, 'clear_structure_breaks'):
            self.parent.clear_structure_breaks()
        # Also clear JavaScript-side markers
        if hasattr(self.parent, '_execute_js'):
            self.parent._execute_js("window.chartAPI?.clearMarkers();")
        logger.info("Cleared all markers")

    def clear_zones_with_js(self) -> None:
        """Clear all zones (Python-managed and JS-side)."""
        if hasattr(self.parent, 'clear_zones'):
            self.parent.clear_zones()
        # Also explicitly call JS clearZones for any orphaned zones
        if hasattr(self.parent, '_execute_js'):
            self.parent._execute_js("window.chartAPI?.clearZones();")
        logger.info("Cleared all zones")

    def clear_lines_with_js(self) -> None:
        """Clear all lines (Python-managed and JS-side hlines)."""
        if hasattr(self.parent, 'clear_stop_loss_lines'):
            self.parent.clear_stop_loss_lines()
        # Also explicitly call JS clearLines for drawing tool lines
        if hasattr(self.parent, '_execute_js'):
            self.parent._execute_js("window.chartAPI?.clearLines();")
        logger.info("Cleared all lines")

    def clear_all_drawings(self) -> None:
        """Clear only the JavaScript-side drawings (from drawing tools)."""
        if hasattr(self.parent, '_execute_js'):
            self.parent._execute_js("window.chartAPI?.clearAllDrawings();")
        logger.info("Cleared all JS drawings")

    def clear_all_markings(self) -> None:
        """Clear all chart markings (both Python-managed and JS drawings)."""
        self.clear_all_markers()
        self.clear_zones_with_js()
        self.clear_lines_with_js()
        self.clear_all_drawings()
        logger.info("Cleared all chart markings")
