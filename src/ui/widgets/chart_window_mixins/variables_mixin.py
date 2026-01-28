"""
Variables Mixin for ChartWindow - Integration of Variable Dialogs.

This mixin provides integration of Variable Reference and Variable Manager
dialogs into the ChartWindow, including toolbar buttons and keyboard shortcuts.

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QPushButton

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class VariablesMixin:
    """
    Mixin for ChartWindow to integrate Variable Reference and Manager dialogs.

    Provides:
        - Toolbar buttons for Variable Reference and Variable Manager
        - Keyboard shortcuts (Ctrl+Shift+V, Ctrl+Shift+M)
        - Dialog lifecycle management
        - Integration with project variables path

    Usage:
        class ChartWindow(VariablesMixin, ...):
            def __init__(self, ...):
                super().__init__(...)
                self.setup_variables_integration()
    """

    # Type hints for parent ChartWindow attributes
    if TYPE_CHECKING:
        chart_widget: any
        symbol: str
        history_manager: any

    def setup_variables_integration(self: ChartWindow) -> None:
        """
        Setup Variable dialogs integration.

        Creates keyboard shortcuts for:
        - Variable Reference Dialog (Ctrl+Shift+V) - Read-only view
        - Variable Manager Dialog (Ctrl+Shift+M) - CRUD interface

        Note: Toolbar buttons are added by toolbar_mixin_row1.py
        This method should be called during ChartWindow initialization.
        """
        # Add keyboard shortcuts
        self._add_variables_shortcuts()

        # Initialize dialog references
        self._variable_reference_dialog: Optional[any] = None
        self._variable_manager_dialog: Optional[any] = None

        logger.info("Variables integration setup complete (keyboard shortcuts added)")

    # NOTE: _add_variables_toolbar_buttons() method REMOVED
    # Toolbar buttons are now added by toolbar_mixin_row1.py (add_variables_buttons method)
    # This provides better integration with existing toolbar structure and styling

    def _add_variables_shortcuts(self: ChartWindow) -> None:
        """Add keyboard shortcuts for Variable dialogs."""
        # Ctrl+Shift+V: Variable Reference (View)
        shortcut_view = QShortcut(QKeySequence("Ctrl+Shift+V"), self)
        shortcut_view.activated.connect(self._show_variable_reference)

        # Ctrl+Shift+M: Variable Manager (Manage)
        shortcut_manage = QShortcut(QKeySequence("Ctrl+Shift+M"), self)
        shortcut_manage.activated.connect(self._show_variable_manager)

        logger.debug("Variable keyboard shortcuts added")

    def _show_variable_reference(self: ChartWindow) -> None:
        """
        Show Variable Reference Dialog (read-only).

        Displays all available variables from:
        - Chart data (chart.*)
        - Bot config (bot.*)
        - Project variables (project.*)
        - Indicators (indicators.*)
        - Regime (regime.*)
        """
        try:
            from src.ui.dialogs.variables import VariableReferenceDialog

            # Lazy import to avoid circular dependencies
            if self._variable_reference_dialog is None or not self._variable_reference_dialog.isVisible():
                # Get bot config if available
                bot_config = self._get_bot_config()
                logger.debug(f"Got bot_config: {bot_config is not None}")

                # Get project variables path
                project_vars_path = self._get_project_vars_path()
                logger.debug(f"Got project_vars_path: {project_vars_path}")

                # Get current indicators and regime (if available)
                indicators = self._get_current_indicators()
                regime = self._get_current_regime()
                logger.debug(f"Got indicators: {len(indicators) if indicators else 0}, regime: {len(regime) if regime else 0}")

                # Create dialog with actual data sources
                self._variable_reference_dialog = VariableReferenceDialog(
                    chart_window=self,  # Pass self for chart data
                    bot_config=bot_config,
                    project_vars_path=project_vars_path,
                    indicators=indicators,
                    regime=regime,
                    enable_live_updates=True,  # Enable live updates for dynamic values
                    update_interval_ms=2000,  # Update every 2 seconds
                    parent=self
                )

                # Connect to copy signal (optional)
                self._variable_reference_dialog.variable_copied.connect(
                    lambda name, value: logger.info(f"Variable copied: {name} = {value}")
                )

                logger.info("Variable Reference Dialog created with data sources")

            else:
                # Dialog exists and is visible - refresh data
                logger.debug("Refreshing existing Variable Reference Dialog")
                bot_config = self._get_bot_config()
                project_vars_path = self._get_project_vars_path()
                indicators = self._get_current_indicators()
                regime = self._get_current_regime()

                self._variable_reference_dialog.set_sources(
                    chart_window=self,
                    bot_config=bot_config,
                    project_vars_path=project_vars_path,
                    indicators=indicators,
                    regime=regime
                )

            # Show dialog (non-modal)
            self._variable_reference_dialog.show()
            self._variable_reference_dialog.raise_()
            self._variable_reference_dialog.activateWindow()

            logger.info("Variable Reference Dialog opened and showing")

        except Exception as e:
            logger.error(f"Failed to show Variable Reference Dialog: {e}", exc_info=True)

    def _show_variable_manager(self: ChartWindow) -> None:
        """
        Show Variable Manager Dialog (CRUD).

        Allows creating, editing, and deleting project variables
        stored in .cel_variables.json files.
        """
        try:
            from src.ui.dialogs.variables import VariableManagerDialog

            # Get project variables path
            project_vars_path = self._get_project_vars_path()

            # Create dialog (always new instance for modal behavior)
            dialog = VariableManagerDialog(
                project_vars_path=project_vars_path,
                parent=self
            )

            # Connect to changes signal
            dialog.variables_changed.connect(self._on_variables_changed)

            # Show dialog (modal)
            result = dialog.exec()

            if result:
                logger.info("Variable Manager Dialog closed with changes")
            else:
                logger.info("Variable Manager Dialog closed without changes")

        except Exception as e:
            logger.error(f"Failed to show Variable Manager Dialog: {e}", exc_info=True)

    def _on_variables_changed(self: ChartWindow) -> None:
        """
        Handle variables changed signal from Variable Manager.

        This is called when the user modifies variables in the Manager Dialog.
        Override this method in ChartWindow to refresh CEL contexts, update
        Variable Reference Dialog, or trigger other actions.
        """
        logger.info("Project variables were modified")

        # Refresh Variable Reference Dialog if it's open
        if self._variable_reference_dialog and self._variable_reference_dialog.isVisible():
            try:
                # Reload variables in Reference Dialog
                project_vars_path = self._get_project_vars_path()
                bot_config = self._get_bot_config()
                indicators = self._get_current_indicators()
                regime = self._get_current_regime()

                self._variable_reference_dialog.set_sources(
                    chart_window=self,
                    bot_config=bot_config,
                    project_vars_path=project_vars_path,
                    indicators=indicators,
                    regime=regime
                )
                logger.debug("Variable Reference Dialog refreshed")
            except Exception as e:
                logger.error(f"Failed to refresh Variable Reference Dialog: {e}")

        # Emit event to notify other components (optional)
        if hasattr(self, 'event_bus'):
            self.event_bus.emit('variables_changed', {
                'source': 'variable_manager',
                'timestamp': __import__('time').time()
            })

    def _get_bot_config(self: ChartWindow) -> Optional[any]:
        """
        Get BotConfig instance for current chart.

        Searches multiple locations:
        1. trading_bot_panel.bot_config
        2. bottom_panel.bot_config
        3. _bitunix_panel.bot_config
        4. Dock widgets with bot_config
        5. _trading_bot_window.panel_content.bot_config

        Returns:
            BotConfig instance or None if not found
        """
        try:
            # 1. Try trading_bot_panel (main bot panel)
            if hasattr(self, 'trading_bot_panel') and self.trading_bot_panel:
                panel = self.trading_bot_panel
                if hasattr(panel, 'bot_config'):
                    logger.debug("Found BotConfig in trading_bot_panel")
                    return panel.bot_config
                if hasattr(panel, 'config'):
                    logger.debug("Found BotConfig as 'config' in trading_bot_panel")
                    return panel.config

            # 2. Try bottom_panel.bot_config
            if hasattr(self, 'bottom_panel') and self.bottom_panel:
                if hasattr(self.bottom_panel, 'bot_config'):
                    logger.debug("Found BotConfig in bottom_panel")
                    return self.bottom_panel.bot_config
                if hasattr(self.bottom_panel, 'config'):
                    logger.debug("Found BotConfig as 'config' in bottom_panel")
                    return self.bottom_panel.config

            # 3. Try BitunixTradingPanel
            if hasattr(self, '_bitunix_panel') and self._bitunix_panel:
                if hasattr(self._bitunix_panel, 'bot_config'):
                    logger.debug("Found BotConfig in _bitunix_panel")
                    return self._bitunix_panel.bot_config
                if hasattr(self._bitunix_panel, 'config'):
                    logger.debug("Found BotConfig in _bitunix_panel.config")
                    return self._bitunix_panel.config

            # 4. Try dock widgets
            from PyQt6.QtWidgets import QDockWidget
            for dock in self.findChildren(QDockWidget):
                widget = dock.widget()
                if widget:
                    if hasattr(widget, 'bot_config'):
                        logger.debug(f"Found BotConfig in dock widget: {widget.__class__.__name__}")
                        return widget.bot_config
                    if hasattr(widget, 'config'):
                        logger.debug(f"Found BotConfig as 'config' in dock widget: {widget.__class__.__name__}")
                        return widget.config

            # 5. Try trading bot window
            if hasattr(self, '_trading_bot_window') and self._trading_bot_window:
                bot_window = self._trading_bot_window
                if hasattr(bot_window, 'panel_content'):
                    panel = bot_window.panel_content
                    if hasattr(panel, 'bot_config'):
                        logger.debug("Found BotConfig in _trading_bot_window.panel_content")
                        return panel.bot_config
                    if hasattr(panel, 'config'):
                        logger.debug("Found BotConfig in _trading_bot_window.panel_content.config")
                        return panel.config

            logger.debug("BotConfig not available in any known location")
            return None

        except Exception as e:
            logger.error(f"Failed to get BotConfig: {e}", exc_info=True)
            return None

    def _get_project_vars_path(self: ChartWindow) -> Optional[str | Path]:
        """
        Get path to project variables file (.cel_variables.json).

        Returns:
            Path to .cel_variables.json or None if not available

        Override this method in ChartWindow to provide the actual project path.
        Default implementation tries to find .cel_variables.json in current directory.
        """
        try:
            # Try current working directory
            cwd_path = Path.cwd() / ".cel_variables.json"
            if cwd_path.exists():
                return str(cwd_path)

            # Try project root
            project_root = Path(__file__).parent.parent.parent.parent
            project_path = project_root / ".cel_variables.json"
            if project_path.exists():
                return str(project_path)

            # Try symbol-specific file
            symbol_path = Path.cwd() / f".cel_variables_{self.symbol}.json"
            if symbol_path.exists():
                return str(symbol_path)

            logger.debug("Project variables file not found")
            return None

        except Exception as e:
            logger.error(f"Failed to get project vars path: {e}")
            return None

    def _get_current_indicators(self: ChartWindow) -> Optional[dict]:
        """
        Get current indicator values for chart.

        Returns:
            Dictionary of indicator values or None

        Override this method in ChartWindow to provide actual indicator values.
        Default implementation attempts to extract from chart_widget.
        """
        try:
            if not hasattr(self, 'chart_widget') or self.chart_widget is None:
                logger.debug("Chart widget not available for indicators")
                return None

            indicators = {}

            # Extract indicators from chart_widget
            if hasattr(self.chart_widget, 'indicators'):
                for name, indicator in self.chart_widget.indicators.items():
                    # Get last value from indicator
                    if hasattr(indicator, 'values') and len(indicator.values) > 0:
                        indicators[name] = indicator.values[-1]
                    elif hasattr(indicator, 'data') and not indicator.data.empty:
                        indicators[name] = indicator.data.iloc[-1]
                    elif isinstance(indicator, (int, float, str)):
                        indicators[name] = indicator

            # Also check for indicator_manager if available
            if hasattr(self.chart_widget, 'indicator_manager'):
                manager = self.chart_widget.indicator_manager
                if hasattr(manager, 'get_all_values'):
                    managed_indicators = manager.get_all_values()
                    indicators.update(managed_indicators)

            logger.debug(f"Retrieved {len(indicators)} indicators: {list(indicators.keys())}")
            return indicators if indicators else None

        except Exception as e:
            logger.error(f"Failed to get current indicators: {e}", exc_info=True)
            return None

    def _get_current_regime(self: ChartWindow) -> Optional[dict]:
        """
        Get current regime state for chart.

        Returns:
            Dictionary of regime values or None

        Override this method in ChartWindow to provide actual regime state.
        Default implementation attempts to extract from regime detector.
        """
        try:
            regime_data = {}

            # Check for regime detector in chart window attributes
            if hasattr(self, '_regime_detector') and self._regime_detector:
                detector = self._regime_detector
                regime_data['current'] = getattr(detector, 'current_regime', None)
                regime_data['strength'] = getattr(detector, 'strength', None)
                regime_data['confidence'] = getattr(detector, 'confidence', None)
                regime_data['is_bullish'] = getattr(detector, 'is_bullish', None)
                regime_data['is_bearish'] = getattr(detector, 'is_bearish', None)
                logger.debug(f"Retrieved regime from _regime_detector: {regime_data.get('current')}")
                return regime_data

            # Check for regime in bottom panel
            if hasattr(self, 'bottom_panel') and self.bottom_panel:
                panel = self.bottom_panel
                if hasattr(panel, 'regime_state'):
                    regime_state = panel.regime_state
                    if isinstance(regime_state, dict):
                        return regime_state
                    elif hasattr(regime_state, '__dict__'):
                        return vars(regime_state)

            # Check for regime in trading bot panel
            if hasattr(self, 'trading_bot_panel') and self.trading_bot_panel:
                panel = self.trading_bot_panel
                if hasattr(panel, 'current_regime'):
                    current = panel.current_regime
                    regime_data['current'] = current
                    logger.debug(f"Retrieved regime from trading_bot_panel: {current}")
                    return regime_data

            logger.debug("Regime detector not available")
            return None

        except Exception as e:
            logger.error(f"Failed to get current regime: {e}", exc_info=True)
            return None

    def cleanup_variables(self: ChartWindow) -> None:
        """
        Cleanup Variable dialogs on ChartWindow close.

        This should be called in the closeEvent of ChartWindow.
        """
        # Close Variable Reference Dialog
        if self._variable_reference_dialog and self._variable_reference_dialog.isVisible():
            self._variable_reference_dialog.close()
            self._variable_reference_dialog = None

        # Variable Manager Dialog is modal, so it should already be closed

        logger.debug("Variables dialogs cleaned up")
