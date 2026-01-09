"""Chart Window Handlers - Event handlers for buttons and widgets.

Refactored from 706 LOC monolith using composition pattern.

Module 4/6 of chart_window.py split.

Contains:
- on_ai_chat_button_clicked(): Handle AI chat button
- on_bitunix_trading_button_clicked(): Handle Bitunix trading button
- on_ai_analysis_button_clicked(): Handle AI analysis popup button
- on_analysis_window_closed(): Handle analysis window close
- on_dock_visibility_changed(): Handle dock visibility change
- on_bitunix_visibility_changed(): Handle Bitunix widget visibility
- sync_bitunix_trading_button_state(): Sync button with widget state
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ChartWindowHandlers:
    """Helper für ChartWindow Event Handlers (Button clicks, visibility changes)."""

    def __init__(self, parent):
        """
        Args:
            parent: ChartWindow Instanz
        """
        self.parent = parent

    def on_ai_chat_button_clicked(self, checked: bool):
        """Handle AI Chat toolbar button click.

        Args:
            checked: Button checked state
        """
        if checked:
            self.parent.show_chat_widget()
            self.parent._setup.ensure_chat_docked_right()
        else:
            self.parent.hide_chat_widget()

        self.parent._setup.sync_ai_chat_button_state()

    def on_bitunix_trading_button_clicked(self, checked: bool = None):
        """Handle Bitunix Trading toolbar button click.

        Args:
            checked: Button checked state (may be None if signal connected without args)
        """
        logger.info(f"🔘 Bitunix button clicked! checked={checked}")

        # Get actual checked state from button if not provided
        if checked is None and hasattr(self.parent.chart_widget, 'bitunix_trading_button'):
            checked = self.parent.chart_widget.bitunix_trading_button.isChecked()
            logger.info(f"   Got checked state from button: {checked}")

        bitunix_widget = getattr(self.parent, '_bitunix_widget', None)
        logger.info(f"   _bitunix_widget exists: {bitunix_widget is not None}")

        if bitunix_widget:
            logger.info(f"   Current visibility: {bitunix_widget.isVisible()}")

        if checked:
            self.parent.show_bitunix_widget()
            logger.info("   Called show_bitunix_widget()")
        else:
            self.parent.hide_bitunix_widget()
            logger.info("   Called hide_bitunix_widget()")

        self.sync_bitunix_trading_button_state()

    def on_ai_analysis_button_clicked(self, checked: bool) -> None:
        """Open or focus the AI Analysis Popup."""
        from src.ui.ai_analysis_window import AIAnalysisWindow

        if checked:
            if not self.parent._ai_analysis_window:
                self.parent._ai_analysis_window = AIAnalysisWindow(self.parent, symbol=self.parent.symbol)
                self.parent._ai_analysis_window.finished.connect(self.on_analysis_window_closed)

            self.parent._ai_analysis_window.show()
            self.parent._ai_analysis_window.raise_()
            self.parent._ai_analysis_window.activateWindow()
        else:
            if self.parent._ai_analysis_window:
                self.parent._ai_analysis_window.hide()

    def on_analysis_window_closed(self, result: int) -> None:
        """Handle analysis window close event to uncheck the button."""
        self.parent._ai_analysis_window = None
        if hasattr(self.parent.chart_widget, 'ai_analysis_button'):
            self.parent.chart_widget.ai_analysis_button.setChecked(False)

    def on_dock_visibility_changed(self, visible: bool) -> None:
        """Handle dock visibility change."""
        self.parent._update_toggle_button_text()

    def on_bitunix_visibility_changed(self, visible: bool) -> None:
        """Handle Bitunix widget visibility change."""
        self.sync_bitunix_trading_button_state()
        self.parent._setup.schedule_chart_resize()

    def sync_bitunix_trading_button_state(self) -> None:
        """Ensure the toolbar toggle reflects the Bitunix widget visibility."""
        if hasattr(self.parent.chart_widget, 'bitunix_trading_button') and getattr(self.parent, "_bitunix_widget", None):
            self.parent.chart_widget.bitunix_trading_button.setChecked(self.parent._bitunix_widget.isVisible())
