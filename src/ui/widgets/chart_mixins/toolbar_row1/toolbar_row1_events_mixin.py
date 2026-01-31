"""Toolbar Row 1 Events Mixin - Event Handlers and UI State Updates.

This module handles event handlers and UI state synchronization for toolbar row 1.
Part of toolbar_mixin_row1.py refactoring (827 LOC → 3 focused mixins).

Responsibilities:
- Broker connection event handlers
- Watchlist toggle event handling
- Strategy settings dialog event handling
- UI state synchronization with BrokerService
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolbarRow1EventsMixin:
    """Row 1 toolbar events - event handlers and UI state updates."""

    def _on_broker_connect_clicked(self) -> None:
        """Handle connect button click - emit event to BrokerService."""
        from datetime import datetime
        from src.common.event_bus import Event, EventType, event_bus
        from src.core.broker import get_broker_service

        broker_service = get_broker_service()

        if broker_service.is_connected:
            # Request disconnect
            event_bus.emit(Event(
                type=EventType.UI_ACTION,
                timestamp=datetime.now(),
                data={"action": "broker_disconnect_requested"},
                source="ChartWindow"
            ))
            logger.info("ChartWindow: Broker disconnect requested via event")
        else:
            # Request connect (use default broker from settings)
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            broker_type = settings.value("selected_broker", "Mock Broker")

            event_bus.emit(Event(
                type=EventType.UI_ACTION,
                timestamp=datetime.now(),
                data={"action": "broker_connect_requested", "broker_type": broker_type},
                source="ChartWindow"
            ))
            logger.info(f"ChartWindow: Broker connect requested via event ({broker_type})")

    def _on_broker_connected_event(self, event) -> None:
        """Handle broker connected event - update UI."""
        broker_type = event.data.get("broker", "Unknown")
        self._update_broker_ui_state(True, broker_type)

    def _on_broker_disconnected_event(self, event) -> None:
        """Handle broker disconnected event - update UI."""
        self._update_broker_ui_state(False, "")

    def _update_broker_ui_state(self, connected: bool, broker_type: str) -> None:
        """Update broker-related UI elements."""
        from src.ui.icons import get_icon

        if not hasattr(self.parent, 'chart_connect_button'):
            return

        if connected:
            self.parent.chart_connect_button.setIcon(get_icon("disconnect"))
            self.parent.chart_connect_button.setChecked(True)
            self.parent.chart_connect_button.setToolTip(f"Verbunden: {broker_type}\nKlicken zum Trennen")
        else:
            self.parent.chart_connect_button.setIcon(get_icon("connect"))
            self.parent.chart_connect_button.setChecked(False)
            self.parent.chart_connect_button.setToolTip("Nicht verbunden\nKlicken zum Verbinden")

    def _toggle_watchlist(self) -> None:
        """Toggle watchlist dock visibility."""
        # Find ChartWindow - self.parent is EmbeddedTradingViewChart, need to go up to ChartWindow
        chart_window = None
        widget = self.parent
        while widget is not None:
            if hasattr(widget, '_watchlist_dock'):
                chart_window = widget
                break
            widget = widget.parent() if hasattr(widget, 'parent') and callable(widget.parent) else None

        if chart_window and chart_window._watchlist_dock:
            is_visible = chart_window._watchlist_dock.isVisible()
            if is_visible:
                chart_window._watchlist_dock.hide()
                self.parent.watchlist_toggle_btn.setChecked(False)
            else:
                chart_window._watchlist_dock.show()
                self.parent.watchlist_toggle_btn.setChecked(True)
            logger.info(f"Watchlist visibility toggled: {not is_visible}")
        else:
            logger.warning("Could not find watchlist dock")

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
