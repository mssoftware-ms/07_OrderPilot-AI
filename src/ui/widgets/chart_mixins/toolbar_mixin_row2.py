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
        print(f"[TOOLBAR] build_toolbar_row2 called, parent type: {type(self.parent).__name__}")
        self.add_live_stream_toggle(toolbar)
        toolbar.addSeparator()
        self.add_regime_badge_to_toolbar(toolbar)  # Phase 2.2: Regime Badge
        self.add_regime_filter_to_toolbar(toolbar)  # Phase 4: Regime Filter Dropdown
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
        """Add regime button to toolbar (Issue #18 - als Button implementiert)."""
        # Issue #18: Regime als klickbaren Button implementieren
        self.parent.regime_button = QPushButton("Regime: N/A")
        self.parent.regime_button.setIcon(get_icon("analytics"))  # Issue #18
        self.parent.regime_button.setIconSize(self.ICON_SIZE)
        self.parent.regime_button.setToolTip("Klicken um aktuelles Markt-Regime zu ermitteln")
        self.parent.regime_button.setProperty("class", "toolbar-button")  # Issue #18: Theme-Farben
        self.parent.regime_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #18: 32px
        self.parent.regime_button.clicked.connect(self.on_regime_button_clicked)
        toolbar.addWidget(self.parent.regime_button)
        logger.debug("Regime button added to toolbar (Issue #18)")

    def add_regime_filter_to_toolbar(self, toolbar: QToolBar) -> None:
        """Add regime filter dropdown to toolbar (Phase 4: Regime Filtering).

        Creates a checkable combobox allowing users to filter which regime lines
        are displayed on the chart.
        """
        print(f"[TOOLBAR] add_regime_filter_to_toolbar called, parent={type(self.parent).__name__}")
        # Check if the parent has the create_regime_filter_widget method (from EntryAnalyzerMixin)
        has_method = hasattr(self.parent, 'create_regime_filter_widget')
        print(f"[TOOLBAR] hasattr(parent, 'create_regime_filter_widget') = {has_method}")
        if has_method:
            try:
                print("[TOOLBAR] Calling create_regime_filter_widget...")
                filter_widget = self.parent.create_regime_filter_widget()
                print(f"[TOOLBAR] Widget created: {filter_widget}")
                toolbar.addWidget(filter_widget)
                logger.info("✓ Regime filter dropdown added to toolbar (Phase 4)")
                print("[TOOLBAR] ✓ Filter widget added to toolbar")
            except Exception as e:
                logger.error(f"Failed to create regime filter widget: {e}", exc_info=True)
                print(f"[TOOLBAR] ERROR: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.warning("Parent has no create_regime_filter_widget method - EntryAnalyzerMixin not loaded?")
            print("[TOOLBAR] WARNING: Parent has no create_regime_filter_widget method!")
            print(f"[TOOLBAR] Parent MRO: {type(self.parent).__mro__}")

    def on_regime_button_clicked(self) -> None:
        """Handle regime button click - ermittle aktuelles Regime (Issue #18)."""
        logger.debug("Regime button clicked - ermittle aktuelles Regime")
        # Issue #18: Aktuelles Regime ermitteln
        if hasattr(self.parent, '_update_regime_from_data'):
            self.parent._update_regime_from_data()
        else:
            logger.warning("_update_regime_from_data method not found")

    def update_regime_badge(self, regime: str, adx: float | None = None,
                            gate_reason: str = "", allows_entry: bool = True) -> None:
        """
        Update the regime button display (Issue #18 - angepasst für Button).

        Args:
            regime: Regime type string
            adx: ADX value
            gate_reason: Reason for gate
            allows_entry: Whether entry is allowed
        """
        # Issue #18: Regime-Text in Button schreiben
        if hasattr(self.parent, "regime_button") and self.parent.regime_button:
            # Zeige nur kurze Regime-Namen für bessere Lesbarkeit
            short_regime = regime.replace("_", " ").title() if regime else "N/A"
            self.parent.regime_button.setText(f"Regime: {short_regime}")
            # Tooltip mit Details aktualisieren
            tooltip_parts = [f"<b>{short_regime}</b>"]
            if adx is not None:
                tooltip_parts.append(f"<br>ADX: {adx:.1f}")
            if gate_reason:
                tooltip_parts.append(f"<br>⚠️ {gate_reason}")
            entry_status = "✅ Entry erlaubt" if allows_entry else "❌ Entry blockiert"
            tooltip_parts.append(f"<br>{entry_status}")
            self.parent.regime_button.setToolTip("".join(tooltip_parts))
            logger.debug(f"Regime button updated: {short_regime}")

    def update_regime_from_result(self, result) -> None:
        """
        Update regime button from RegimeResult (Issue #18 - angepasst für Button).

        Args:
            result: RegimeResult from RegimeDetectorService
        """
        # Issue #18: RegimeResult in Button anzeigen
        if result is None:
            self.update_regime_badge("UNKNOWN")
            return

        self.update_regime_badge(
            regime=result.regime.value if hasattr(result.regime, 'value') else str(result.regime),
            adx=result.adx,
            gate_reason=result.gate_reason,
            allows_entry=result.allows_market_entry,
        )

    def add_live_stream_toggle(self, toolbar: QToolBar) -> None:
        # Issue #7: Icon prüfen - nur Play-Symbol verwenden, keinen grünen Ball
        self.parent.live_stream_button = QPushButton("Live")  # Issue #15: Emoji entfernt
        self.parent.live_stream_button.setIcon(get_icon("live"))  # Issue #15 - sollte nur weißes Play-Symbol enthalten
        self.parent.live_stream_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.live_stream_button.setCheckable(True)
        self.parent.live_stream_button.setToolTip("Toggle real-time streaming (WebSocket)")
        self.parent.live_stream_button.clicked.connect(self.parent._toggle_live_stream)
        self.parent.live_stream_button.setProperty("class", "toolbar-button")
        self.parent.live_stream_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16 (32px)
        self.parent.live_stream_button.setMaximumHeight(self.BUTTON_HEIGHT)  # Issue #7: Explizite Höhenbegrenzung
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
        lines_menu.addSeparator()
        vertical_line = QAction("📏 Vertikale Linie", self.parent)
        vertical_line.triggered.connect(lambda: self.parent._add_vertical_line_interactive())
        lines_menu.addAction(vertical_line)

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
        self.parent.entry_analyzer_button.setFixedHeight(self.BUTTON_HEIGHT)
        # Style is now handled globally in themes.py (Issue #28)
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
        self.parent.strategy_concept_button.setFixedHeight(self.BUTTON_HEIGHT)
        # Style is now handled globally in themes.py (Issue #28)
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
        # Style is now handled globally in themes.py (Issue #28)
        self.parent.cel_editor_button.clicked.connect(self._on_cel_editor_clicked)
        toolbar.addWidget(self.parent.cel_editor_button)
        logger.info("Toolbar: CEL Editor button added")

    def _on_cel_editor_clicked(self) -> None:
        """Handle CEL Editor button click (Toggle-aware)."""
        if not hasattr(self.parent, 'cel_editor_button'):
            return

        checked = self.parent.cel_editor_button.isChecked()

        # Issue #27: show_cel_editor is on ChartWindow (via CelEditorMixin), not EmbeddedTradingViewChart
        # Try to find handler on parent or parent's window
        handler = self.parent
        if not hasattr(handler, "show_cel_editor") and hasattr(handler, "window"):
            handler = handler.window()

        if checked:
            if hasattr(handler, "show_cel_editor"):
                handler.show_cel_editor()
            else:
                # Debug: What is self.parent and why doesn't it have show_cel_editor?
                logger.error(
                    f"show_cel_editor not available! "
                    f"parent type={type(self.parent).__name__}, "
                    f"handler type={type(handler).__name__}"
                )
                self.parent.cel_editor_button.setChecked(False)
        else:
            # Toggle off - hide window if it exists
            if hasattr(handler, "hide_cel_editor"):
                handler.hide_cel_editor()
            else:
                logger.warning("hide_cel_editor not available on chart widget or window")

    def add_ai_chat_button(self, toolbar: QToolBar) -> None:
        self.parent.ai_chat_button = QPushButton("AI Chat")  # Issue #15: Emoji entfernt
        self.parent.ai_chat_button.setIcon(get_icon("chat"))  # Issue #15
        self.parent.ai_chat_button.setIconSize(self.ICON_SIZE)  # Issue #15
        self.parent.ai_chat_button.setCheckable(True)
        self.parent.ai_chat_button.setToolTip(
            "AI Chart-Analyse öffnen/schließen (Ctrl+Shift+C)"
        )
        self.parent.ai_chat_button.setProperty("class", "toolbar-button")
        self.parent.ai_chat_button.setFixedHeight(self.BUTTON_HEIGHT)
        # Style is now handled globally in themes.py (Issue #28)
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
        self.parent.ai_analysis_button.setFixedHeight(self.BUTTON_HEIGHT)
        # Style is now handled globally in themes.py (Issue #28)
        toolbar.addWidget(self.parent.ai_analysis_button)

    # Issue #24: Methode entfernt - Button ist jetzt in Row1 (toolbar_mixin_row1.py)
    # def add_bitunix_trading_button(self, toolbar: QToolBar) -> None:
    #     """Add Bitunix trading button to toolbar (initially hidden)."""
    #     ...

    def add_settings_button(self, toolbar: QToolBar) -> None:
        """Add settings button (gear icon) to toolbar."""
        # Issue #7: Falls Icon zu groß ist, prüfen ob kleineres Icon verfügbar ist
        self.parent.settings_button = QPushButton()
        self.parent.settings_button.setIcon(get_icon("settings"))
        self.parent.settings_button.setIconSize(self.ICON_SIZE)  # Issue #15 (20x20)
        self.parent.settings_button.setToolTip("Settings öffnen")
        self.parent.settings_button.setFixedHeight(self.BUTTON_HEIGHT)  # Issue #16 (32px)
        self.parent.settings_button.setMaximumHeight(self.BUTTON_HEIGHT)  # Issue #7: Explizite Höhenbegrenzung
        self.parent.settings_button.setFixedWidth(self.BUTTON_HEIGHT)  # Issue #25: Breite = Höhe für quadratischen Icon-Button
        self.parent.settings_button.setProperty("class", "icon-button")
        self.parent.settings_button.clicked.connect(self._open_settings_dialog)
        toolbar.addWidget(self.parent.settings_button)

    def _open_settings_dialog(self) -> None:
        """Open settings dialog from toolbar (Issue #11)."""
        from PyQt6.QtWidgets import QApplication, QMessageBox

        logger.info("Settings button clicked in toolbar")

        # Method 1: Use chart window's method (preferred)
        if hasattr(self.parent, "open_main_settings_dialog"):
            logger.info("Calling parent.open_main_settings_dialog()")
            self.parent.open_main_settings_dialog()
            return

        # Method 2: Try parent chain for show_settings_dialog
        widget = self.parent
        depth = 0
        while widget is not None and depth < 10:
            widget_type = type(widget).__name__
            logger.debug(f"Checking parent chain[{depth}]: {widget_type}")

            if hasattr(widget, "show_settings_dialog"):
                logger.info(f"Found show_settings_dialog in {widget_type}")
                widget.show_settings_dialog()
                return

            widget = widget.parent()
            depth += 1

        # Method 3: Search top-level widgets (for Chart-Only mode)
        logger.debug("Searching top-level widgets...")
        for top_widget in QApplication.topLevelWidgets():
            widget_type = type(top_widget).__name__
            has_settings = hasattr(top_widget, "show_settings_dialog")

            if has_settings:
                logger.info(f"Found settings dialog in top-level widget: {widget_type}")
                top_widget.show_settings_dialog()
                return

        # No method worked - show error
        logger.error("Settings dialog not available - no method succeeded")
        QMessageBox.warning(
            self.parent,
            "Settings nicht verfügbar",
            "Die Settings-Funktion konnte nicht gefunden werden."
        )

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
        self.parent.toggle_panel_button.setFixedHeight(self.BUTTON_HEIGHT)
        # Style is now handled globally in themes.py (Issue #28)
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
