"""Panels Mixin for ChartWindow.

Contains the main panel/tab creation for the dock widget.
Only Bot-related tabs are created here.
"""

import logging

from PyQt6.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class PanelsMixin:
    """Mixin providing panel/tab creation for ChartWindow."""

    def _create_bottom_panel(self) -> QWidget:
        """Create bottom panel with Bot tabs only."""
        panel_container = QWidget()
        panel_layout = QVBoxLayout(panel_container)
        panel_layout.setContentsMargins(5, 5, 5, 5)

        self.panel_tabs = QTabWidget()

        # Bot Tabs (from BotPanelsMixin)
        if hasattr(self, '_create_bot_control_tab'):
            # Tab 1: Bot Control
            self.bot_control_tab = self._create_bot_control_tab()
            self.panel_tabs.addTab(self.bot_control_tab, "Bot")

            # Tab 2: Daily Strategy Selection
            self.bot_strategy_tab = self._create_strategy_selection_tab()
            self.panel_tabs.addTab(self.bot_strategy_tab, "Daily Strategy")

            # Tab 3: Signals & Trade Management
            self.bot_signals_tab = self._create_signals_tab()
            self.panel_tabs.addTab(self.bot_signals_tab, "Signals")

            # Tab 4: KI Logs
            self.bot_ki_tab = self._create_ki_logs_tab()
            self.panel_tabs.addTab(self.bot_ki_tab, "KI Logs")

            # Tab 5: Engine Settings
            if hasattr(self, '_create_engine_settings_tab'):
                self.bot_engine_settings_tab = self._create_engine_settings_tab()
                self.panel_tabs.addTab(self.bot_engine_settings_tab, "Engine Settings")

            # Initialize bot panel state
            if hasattr(self, '_init_bot_panels'):
                self._init_bot_panels()

        # Tab 5: KO-Finder (from KOFinderMixin)
        if hasattr(self, '_create_ko_finder_tab'):
            self.ko_finder_tab = self._create_ko_finder_tab()
            self.panel_tabs.addTab(self.ko_finder_tab, "KO-Finder")

        # Tab 6: Strategy Simulator (from StrategySimulatorMixin)
        if hasattr(self, '_create_strategy_simulator_tab'):
            self.strategy_simulator_tab = self._create_strategy_simulator_tab()
            self.panel_tabs.addTab(self.strategy_simulator_tab, "Strategy Simulator")

        panel_layout.addWidget(self.panel_tabs)
        return panel_container

    def _toggle_bottom_panel(self):
        """Toggle visibility of bottom panel dock widget."""
        if not hasattr(self.chart_widget, 'toggle_panel_button'):
            return

        button = self.chart_widget.toggle_panel_button
        should_show = button.isChecked()

        self.dock_widget.setVisible(should_show)
        self._update_toggle_button_text()

    def _on_dock_visibility_changed(self, visible: bool):
        """Handle dock visibility changes."""
        if hasattr(self.chart_widget, 'toggle_panel_button'):
            self.chart_widget.toggle_panel_button.setChecked(visible)
            self._update_toggle_button_text()

    def _update_toggle_button_text(self):
        """Update the toggle button text based on state."""
        if hasattr(self.chart_widget, 'toggle_panel_button'):
            button = self.chart_widget.toggle_panel_button
            if button.isChecked():
                button.setText("▼ Trading Bot")
            else:
                button.setText("▶ Trading Bot")
