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

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLabel, QMenu, QPushButton, QToolBar

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolbarMixinRow2:
    """Row 2 toolbar builders (live stream, regime, chart marking, AI, bot, market status)."""

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
        self.add_ai_chat_button(toolbar)
        self.add_ai_analysis_button(toolbar)
        self.add_bitunix_trading_button(toolbar)
        toolbar.addSeparator()
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
        self.parent.live_stream_button = QPushButton("🔴 Live")
        self.parent.live_stream_button.setCheckable(True)
        self.parent.live_stream_button.setToolTip("Toggle real-time streaming (WebSocket)")
        self.parent.live_stream_button.clicked.connect(self.parent._toggle_live_stream)
        self.parent.live_stream_button.setStyleSheet(
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
        toolbar.addWidget(self.parent.live_stream_button)

    def add_chart_marking_button(self, toolbar: QToolBar) -> None:
        self.parent.chart_marking_button = QPushButton("📏 Markierungen")
        self.parent.chart_marking_button.setToolTip(
            "Chart-Markierungen hinzufügen (Rechtsklick auf Chart für Menü)"
        )
        self.parent.chart_marking_button.setStyleSheet(
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

    def add_ai_chat_button(self, toolbar: QToolBar) -> None:
        self.parent.ai_chat_button = QPushButton("🤖 AI Chat")
        self.parent.ai_chat_button.setCheckable(True)
        self.parent.ai_chat_button.setToolTip(
            "AI Chart-Analyse öffnen/schließen (Ctrl+Shift+C)"
        )
        self.parent.ai_chat_button.setStyleSheet(
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
        toolbar.addWidget(self.parent.ai_chat_button)

    def add_ai_analysis_button(self, toolbar: QToolBar) -> None:
        self.parent.ai_analysis_button = QPushButton("🧠 AI Analyse")
        self.parent.ai_analysis_button.setCheckable(True)
        self.parent.ai_analysis_button.setToolTip(
            "Deep Market Analysis Popup öffnen"
        )
        self.parent.ai_analysis_button.setStyleSheet(
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
        toolbar.addWidget(self.parent.ai_analysis_button)

    def add_bitunix_trading_button(self, toolbar: QToolBar) -> None:
        """Add Bitunix trading button to toolbar (initially hidden)."""
        self.parent.bitunix_trading_button = QPushButton("💱 Bitunix")
        self.parent.bitunix_trading_button.setCheckable(True)
        self.parent.bitunix_trading_button.setToolTip(
            "Bitunix Futures Trading öffnen/schließen (nur Crypto)"
        )
        self.parent.bitunix_trading_button.setStyleSheet(
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
        self.parent.bitunix_trading_button.setVisible(True)
        toolbar.addWidget(self.parent.bitunix_trading_button)
        logger.info("Toolbar: Bitunix trading button created and added (visible)")

    def add_bot_toggle_button(self, toolbar: QToolBar) -> None:
        self.parent.toggle_panel_button = QPushButton("▼ Trading Bot")
        self.parent.toggle_panel_button.setCheckable(True)
        self.parent.toggle_panel_button.setChecked(True)
        self.parent.toggle_panel_button.setToolTip("Trading Bot Panel ein-/ausblenden")
        self.parent.toggle_panel_button.setStyleSheet(
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
