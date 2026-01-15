"""Levels & Context Mixin for ChartWindow.

Handles:
- Level detection and rendering
- Market context building and inspection
- Context export (JSON, AI prompt, file)
- Level interaction (Set TP/SL/Entry from level click)

Module 1/2 of chart_window.py Phase 5.5-5.7 extraction (Lines 710-1072)
"""

import json
import logging
from typing import Optional

from PyQt6.QtWidgets import QMessageBox, QApplication, QFileDialog

logger = logging.getLogger(__name__)


class LevelsContextMixin:
    """Mixin for Levels & Context functionality in ChartWindow."""

    def _setup_levels_and_context(self) -> None:
        """Setup levels and context toolbar button connections (Phase 5.5)."""
        # Initialize context cache
        self._market_context = None
        self._context_inspector = None

        # Connect levels button
        if hasattr(self.chart_widget, 'levels_button'):
            self.chart_widget.levels_button.clicked.connect(self._on_levels_button_clicked)

        # Connect level signals
        if hasattr(self.chart_widget, 'levels_detect_requested'):
            self.chart_widget.levels_detect_requested.connect(self._on_detect_levels)
        if hasattr(self.chart_widget, 'level_type_toggled'):
            self.chart_widget.level_type_toggled.connect(self._on_level_type_toggled)
        # Phase 5.7: Connect level target suggestion signal
        if hasattr(self.chart_widget, 'level_target_suggested'):
            self.chart_widget.level_target_suggested.connect(self._on_level_target_suggested)

        # Connect context signals
        if hasattr(self.chart_widget, 'context_inspector_requested'):
            self.chart_widget.context_inspector_requested.connect(self._on_open_context_inspector)
        if hasattr(self.chart_widget, 'context_copy_json_requested'):
            self.chart_widget.context_copy_json_requested.connect(self._on_copy_context_json)
        if hasattr(self.chart_widget, 'context_copy_prompt_requested'):
            self.chart_widget.context_copy_prompt_requested.connect(self._on_copy_context_prompt)
        if hasattr(self.chart_widget, 'context_export_file_requested'):
            self.chart_widget.context_export_file_requested.connect(self._on_export_context_file)
        if hasattr(self.chart_widget, 'context_refresh_requested'):
            self.chart_widget.context_refresh_requested.connect(self._on_refresh_context)

        logger.debug("Levels and context toolbar buttons connected")

    # =========================================================================
    # LEVEL DETECTION & RENDERING
    # =========================================================================

    def _on_levels_button_clicked(self, checked: bool) -> None:
        """Handle levels button toggle."""
        if checked:
            # Auto-detect levels on first activation
            self._on_detect_levels()
        else:
            # Hide levels
            if hasattr(self.chart_widget, 'clear_zones'):
                self.chart_widget.clear_zones()

        logger.debug(f"Levels button toggled: {checked}")

    def _on_detect_levels(self) -> None:
        """Detect and render levels on chart."""
        try:
            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None:
                logger.warning("No chart data available for level detection")
                return

            # Use LevelZonesMixin if available
            if hasattr(self.chart_widget, 'detect_and_render_levels'):
                df = self.chart_widget.data
                symbol = getattr(self.chart_widget, 'current_symbol', 'UNKNOWN')
                timeframe = getattr(self.chart_widget, 'current_timeframe', '5m')
                current_price = df['close'].iloc[-1] if len(df) > 0 else None

                self.chart_widget.detect_and_render_levels(
                    df=df,
                    symbol=symbol,
                    timeframe=timeframe,
                    current_price=current_price,
                )
                logger.info(f"Levels detected and rendered for {symbol}")

                # Update button state
                if hasattr(self.chart_widget, 'levels_button'):
                    self.chart_widget.levels_button.setChecked(True)
            else:
                logger.warning("detect_and_render_levels not available on chart widget")

        except Exception as e:
            logger.error(f"Level detection failed: {e}", exc_info=True)

    def _on_level_type_toggled(self, level_type: str, checked: bool) -> None:
        """Handle level type toggle from dropdown menu."""
        logger.debug(f"Level type {level_type} toggled: {checked}")
        # Re-render levels with updated filters
        self._on_detect_levels()

    # =========================================================================
    # CONTEXT BUILDING & INSPECTION
    # =========================================================================

    def _get_or_build_context(self):
        """Get current MarketContext or build a new one."""
        try:
            from src.core.trading_bot.market_context_builder import MarketContextBuilder

            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None:
                logger.warning("No chart data for context")
                return None

            builder = MarketContextBuilder()
            symbol = getattr(self.chart_widget, 'current_symbol', 'UNKNOWN')
            timeframe = getattr(self.chart_widget, 'current_timeframe', '5m')

            context = builder.build(
                symbol=symbol,
                timeframe=timeframe,
                df=self.chart_widget.data,
            )
            self._market_context = context
            return context

        except ImportError as e:
            logger.warning(f"MarketContextBuilder not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Context building failed: {e}", exc_info=True)
            return None

    def _on_open_context_inspector(self) -> None:
        """Open MarketContext Inspector dialog."""
        try:
            from src.ui.dialogs.market_context_inspector import MarketContextInspector

            context = self._get_or_build_context()

            if self._context_inspector is None or not self._context_inspector.isVisible():
                self._context_inspector = MarketContextInspector(
                    context=context,
                    refresh_callback=self._get_or_build_context,
                    parent=self,
                )
                self._context_inspector.show()
            else:
                # Update existing inspector
                if context and hasattr(self._context_inspector, '_update_display'):
                    self._context_inspector._update_display(context)
                self._context_inspector.raise_()
                self._context_inspector.activateWindow()

            logger.info("Context inspector opened")

        except ImportError as e:
            logger.warning(f"MarketContextInspector not available: {e}")
        except Exception as e:
            logger.error(f"Failed to open context inspector: {e}", exc_info=True)

    # =========================================================================
    # CONTEXT EXPORT
    # =========================================================================

    def _on_copy_context_json(self) -> None:
        """Copy MarketContext as JSON to clipboard."""
        try:
            context = self._get_or_build_context()
            if context is None:
                logger.warning("No context available to copy")
                return

            # Convert to dict and then JSON
            if hasattr(context, 'to_dict'):
                context_dict = context.to_dict()
            else:
                context_dict = {"error": "Context does not support to_dict()"}

            json_str = json.dumps(context_dict, indent=2, default=str)
            QApplication.clipboard().setText(json_str)
            logger.info("Context JSON copied to clipboard")

        except Exception as e:
            logger.error(f"Failed to copy context JSON: {e}", exc_info=True)

    def _on_copy_context_prompt(self) -> None:
        """Copy MarketContext as AI prompt to clipboard."""
        try:
            context = self._get_or_build_context()
            if context is None:
                logger.warning("No context available to copy")
                return

            # Use AI prompt format
            if hasattr(context, 'to_ai_prompt_context'):
                prompt = context.to_ai_prompt_context()
            else:
                prompt = f"MarketContext for {getattr(context, 'symbol', 'UNKNOWN')}"

            QApplication.clipboard().setText(prompt)
            logger.info("Context AI prompt copied to clipboard")

        except Exception as e:
            logger.error(f"Failed to copy context prompt: {e}", exc_info=True)

    def _on_export_context_file(self) -> None:
        """Export MarketContext to JSON file."""
        try:
            from datetime import datetime

            context = self._get_or_build_context()
            if context is None:
                logger.warning("No context available to export")
                return

            # Generate default filename
            symbol = getattr(context, 'symbol', 'UNKNOWN').replace('/', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"market_context_{symbol}_{timestamp}.json"

            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "MarketContext exportieren",
                default_name,
                "JSON Files (*.json)"
            )

            if filepath:
                if hasattr(context, 'to_dict'):
                    context_dict = context.to_dict()
                else:
                    context_dict = {"error": "Context does not support to_dict()"}

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(context_dict, f, indent=2, default=str)

                logger.info(f"Context exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export context: {e}", exc_info=True)

    def _on_refresh_context(self) -> None:
        """Refresh MarketContext and update inspector if open."""
        try:
            context = self._get_or_build_context()

            # Update inspector if open
            if self._context_inspector and self._context_inspector.isVisible():
                if hasattr(self._context_inspector, '_update_display'):
                    self._context_inspector._update_display(context)

            # Issue #36: Update AI Chat Tab with new context
            if hasattr(self, 'update_ai_chat_context'):
                self.update_ai_chat_context(context)

            logger.info("Context refreshed")

        except Exception as e:
            logger.error(f"Failed to refresh context: {e}", exc_info=True)

    # =========================================================================
    # LEVEL INTERACTION (Phase 5.7)
    # =========================================================================

    def _on_level_target_suggested(self, target_type: str, price: float) -> None:
        """Handle level target suggestion from chart (Set TP/SL/Entry from level click).

        Args:
            target_type: "TP", "SL", or "Entry"
            price: Target price from level
        """
        try:
            logger.info(f"Level target suggested: {target_type} @ {price:.2f}")

            # Try to set in bot control panel if available
            bot_panel = self._find_bot_control_panel()
            if bot_panel:
                self._apply_target_to_bot_panel(bot_panel, target_type, price)
            else:
                # Fallback: show info dialog and copy to clipboard
                self._show_target_suggestion_dialog(target_type, price)

        except Exception as e:
            logger.error(f"Failed to apply level target: {e}", exc_info=True)

    def _find_bot_control_panel(self):
        """Find bot control panel in the current window hierarchy."""
        # Look for bot control panel in all windows
        for widget in QApplication.allWidgets():
            widget_name = type(widget).__name__
            if 'BotControlPanel' in widget_name or 'BotTab' in widget_name:
                return widget

        # Check if we have a direct reference
        if hasattr(self, '_bot_control_panel'):
            return self._bot_control_panel

        return None

    def _apply_target_to_bot_panel(self, bot_panel, target_type: str, price: float) -> None:
        """Apply target price to bot control panel fields.

        Args:
            bot_panel: Bot control panel widget
            target_type: "TP", "SL", or "Entry"
            price: Target price
        """
        try:
            # Map target type to field names
            field_map = {
                "TP": ["take_profit_input", "tp_input", "take_profit_price"],
                "SL": ["stop_loss_input", "sl_input", "stop_loss_price"],
                "Entry": ["entry_price_input", "entry_input", "entry_price"],
            }

            field_names = field_map.get(target_type, [])
            applied = False

            for field_name in field_names:
                if hasattr(bot_panel, field_name):
                    field = getattr(bot_panel, field_name)
                    if hasattr(field, 'setValue'):
                        field.setValue(price)
                        applied = True
                        break
                    elif hasattr(field, 'setText'):
                        field.setText(f"{price:.2f}")
                        applied = True
                        break

            if applied:
                logger.info(f"Applied {target_type} = {price:.2f} to bot panel")
                # Show brief notification
                self._show_brief_notification(f"{target_type} auf {price:.2f} gesetzt")
            else:
                # Fallback to dialog
                self._show_target_suggestion_dialog(target_type, price)

        except Exception as e:
            logger.error(f"Failed to apply target to bot panel: {e}")
            self._show_target_suggestion_dialog(target_type, price)

    def _show_target_suggestion_dialog(self, target_type: str, price: float) -> None:
        """Show dialog suggesting to set the target price.

        Args:
            target_type: "TP", "SL", or "Entry"
            price: Target price
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(f"{target_type} Vorschlag")
        msg.setText(f"Level als {target_type} vorgeschlagen:")
        msg.setInformativeText(
            f"Preis: {price:.2f}\n\n"
            "Der Preis wurde in die Zwischenablage kopiert.\n"
            "Fügen Sie ihn manuell in das Bot-Panel ein."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(f"{price:.2f}")

        msg.exec()
        logger.info(f"{target_type} suggestion shown, price copied to clipboard")

    def _show_brief_notification(self, message: str) -> None:
        """Show brief status notification.

        Args:
            message: Message to display
        """
        # Try to use status label if available
        if hasattr(self.chart_widget, 'info_label'):
            self.chart_widget.info_label.setText(message)
        elif hasattr(self, 'statusBar'):
            self.statusBar().showMessage(message, 3000)
