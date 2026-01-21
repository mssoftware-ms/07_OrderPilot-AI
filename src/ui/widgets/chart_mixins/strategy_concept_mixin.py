"""Strategy Concept Mixin for ChartWindow.

Provides Strategy Concept window lifecycle management.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.ui.dialogs.strategy_concept_window import StrategyConceptWindow

logger = logging.getLogger(__name__)


class StrategyConceptMixin:
    """Mixin for Strategy Concept window management."""

    # Class attributes
    _strategy_concept_window: Optional[StrategyConceptWindow] = None

    def _init_strategy_concept(self) -> None:
        """Initialize Strategy Concept window integration.

        Must be called from chart widget __init__.
        """
        self._strategy_concept_window = None
        self._setup_strategy_concept_connections()

    def _setup_strategy_concept_connections(self):
        """Setup signal connections for Strategy Concept."""
        # Connect to symbol/timeframe changes if available
        if hasattr(self, "symbol_changed"):
            self.symbol_changed.connect(self._on_strategy_concept_symbol_changed)
        if hasattr(self, "timeframe_changed"):
            self.timeframe_changed.connect(self._on_strategy_concept_timeframe_changed)

    def show_strategy_concept(self) -> None:
        """Show the Strategy Concept window."""
        from src.ui.dialogs.strategy_concept_window import StrategyConceptWindow

        if self._strategy_concept_window is None:
            # Find parent ChartWindow (self is chart_widget, parent is ChartWindow)
            chart_window = self.parent() if hasattr(self, 'parent') else self
            self._strategy_concept_window = StrategyConceptWindow(parent=chart_window)
            self._strategy_concept_window.strategy_applied.connect(
                self._on_strategy_applied
            )
            self._strategy_concept_window.closed.connect(
                self._on_strategy_concept_closed
            )

        # Update window context with current chart data
        self._update_strategy_concept_context()

        self._strategy_concept_window.show()
        self._strategy_concept_window.raise_()
        self._strategy_concept_window.activateWindow()
        logger.info("Strategy Concept window opened")

    def _update_strategy_concept_context(self) -> None:
        """Update Strategy Concept window with current chart context."""
        if self._strategy_concept_window is None:
            return

        # Update chart data reference if pattern recognition needs it
        if hasattr(self._strategy_concept_window, "pattern_recognition"):
            pattern_widget = self._strategy_concept_window.pattern_recognition
            if hasattr(pattern_widget, "set_chart_data"):
                # Pass current chart data for pattern analysis
                chart_data = getattr(self, "data", None)
                if chart_data is not None:
                    pattern_widget.set_chart_data(chart_data)
                    logger.debug("Updated pattern recognition with chart data")

    def _on_strategy_applied(self, pattern_type: str, strategy: dict) -> None:
        """Handle strategy application from Strategy Concept window.

        Args:
            pattern_type: Pattern type identifier (e.g., "cup_and_handle")
            strategy: Strategy configuration dict
        """
        pattern_name = strategy.get('pattern_name', 'Unknown')
        logger.info(f"Strategy applied: {pattern_type} - {pattern_name}")

        # Get pattern metadata if available
        pattern_data = strategy.get('pattern_data', {})
        entry_price = pattern_data.get('entry_price')
        stop_loss = pattern_data.get('stop_loss')
        take_profit = pattern_data.get('take_profit')

        # 1. Draw pattern on chart
        if pattern_data:
            self._draw_pattern_on_chart(pattern_type, pattern_data, pattern_name)

        # 2. Draw entry/stop/target levels
        if entry_price and stop_loss and take_profit:
            self._draw_strategy_levels(entry_price, stop_loss, take_profit, pattern_name)

        # 3. Notify user
        self._show_strategy_applied_notification(pattern_name, entry_price)

        logger.info(f"Pattern visualization complete for {pattern_name}")

    def _on_strategy_concept_closed(self) -> None:
        """Handle Strategy Concept window close event (Issue #32)."""
        logger.info("Strategy Concept window closed")

        # Issue #32: Reset button state when window closes
        if hasattr(self, 'strategy_concept_button'):
            self.strategy_concept_button.setChecked(False)

        # Don't destroy window - keep it for reuse

    def _on_strategy_concept_symbol_changed(self, symbol: str) -> None:
        """Handle symbol change - update Strategy Concept context.

        Args:
            symbol: New symbol
        """
        if self._strategy_concept_window is not None and self._strategy_concept_window.isVisible():
            self._update_strategy_concept_context()
            logger.debug(f"Strategy Concept context updated for symbol: {symbol}")

    def _on_strategy_concept_timeframe_changed(self, timeframe: str) -> None:
        """Handle timeframe change - update Strategy Concept context.

        Args:
            timeframe: New timeframe
        """
        if self._strategy_concept_window is not None and self._strategy_concept_window.isVisible():
            self._update_strategy_concept_context()
            logger.debug(f"Strategy Concept context updated for timeframe: {timeframe}")

    def close_strategy_concept(self) -> None:
        """Close Strategy Concept window."""
        if self._strategy_concept_window is not None:
            self._strategy_concept_window.close()
            logger.info("Strategy Concept window closed programmatically")

    # ========== Pattern Visualization Methods ==========

    def _draw_pattern_on_chart(self, pattern_type: str, pattern_data: dict, pattern_name: str) -> None:
        """Draw pattern visualization on chart.

        Args:
            pattern_type: Pattern type (cup_and_handle, triple_bottom, ascending_triangle)
            pattern_data: Pattern metadata with pivots and levels
            pattern_name: Human-readable pattern name
        """
        pivots = pattern_data.get('pivots', [])
        if not pivots:
            logger.warning(f"No pivots found for pattern {pattern_name}")
            return

        try:
            if pattern_type == "cup_and_handle":
                self._draw_cup_and_handle(pivots, pattern_data, pattern_name)
            elif pattern_type == "triple_bottom":
                self._draw_triple_bottom(pivots, pattern_data, pattern_name)
            elif pattern_type == "ascending_triangle":
                self._draw_ascending_triangle(pivots, pattern_data, pattern_name)
            else:
                logger.warning(f"Unknown pattern type for visualization: {pattern_type}")

        except Exception as e:
            logger.error(f"Error drawing pattern {pattern_name}: {e}")

    def _draw_cup_and_handle(self, pivots: list, pattern_data: dict, pattern_name: str) -> None:
        """Draw Cup and Handle pattern visualization.

        Pattern structure: P0(high) → P1(low) → P2(high) → P3(high) → P4(low)
        - Cup: P0 → P1 → P2 (U-shaped curve)
        - Handle: P2 → P3 → P4 (downward correction)
        """
        if not hasattr(self, 'add_horizontal_line') or not hasattr(self, 'add_zone'):
            logger.warning("Chart marking methods not available")
            return

        # Extract key levels from pattern data
        cup_depth = pattern_data.get('cup_depth')
        handle_depth = pattern_data.get('handle_depth')
        left_rim = pattern_data.get('left_rim')
        right_rim = pattern_data.get('right_rim')

        if left_rim:
            # Draw resistance line at cup rim
            self.add_horizontal_line(
                price=left_rim,
                label=f"{pattern_name} - Resistance",
                color="#9C27B0"
            )

        if len(pivots) >= 2:
            # Draw support zone at cup bottom
            cup_bottom = pivots[1].get('price')
            if cup_bottom and cup_depth:
                zone_height = cup_depth * 0.1  # 10% of cup depth
                self.add_support_zone(
                    start_time=int(pivots[0].get('timestamp', 0)),
                    end_time=int(pivots[2].get('timestamp', 0) if len(pivots) > 2 else pivots[1].get('timestamp', 0)),
                    top_price=cup_bottom + zone_height,
                    bottom_price=cup_bottom - zone_height,
                    label=f"{pattern_name} - Cup Support"
                )

        logger.info(f"Drew Cup and Handle pattern: {pattern_name}")

    def _draw_triple_bottom(self, pivots: list, pattern_data: dict, pattern_name: str) -> None:
        """Draw Triple Bottom pattern visualization.

        Pattern structure: 3 similar bottoms with 2 intermediate peaks
        - Neckline: Resistance at peak levels
        - Support: At triple bottom level
        """
        if not hasattr(self, 'add_horizontal_line') or not hasattr(self, 'add_zone'):
            logger.warning("Chart marking methods not available")
            return

        # Extract key levels
        avg_bottom = pattern_data.get('avg_bottom_price')
        neckline = pattern_data.get('neckline_price')
        pattern_height = pattern_data.get('pattern_height')

        if neckline:
            # Draw neckline resistance
            self.add_horizontal_line(
                price=neckline,
                label=f"{pattern_name} - Neckline",
                color="#FF9800"
            )

        if avg_bottom and pattern_height:
            # Draw support zone at triple bottom
            zone_height = pattern_height * 0.05  # 5% of pattern height
            self.add_support_zone(
                start_time=int(pivots[0].get('timestamp', 0)),
                end_time=int(pivots[-1].get('timestamp', 0)),
                top_price=avg_bottom + zone_height,
                bottom_price=avg_bottom - zone_height,
                label=f"{pattern_name} - Support"
            )

        logger.info(f"Drew Triple Bottom pattern: {pattern_name}")

    def _draw_ascending_triangle(self, pivots: list, pattern_data: dict, pattern_name: str) -> None:
        """Draw Ascending Triangle pattern visualization.

        Pattern structure: Horizontal resistance + ascending support
        - Resistance: Flat line at top
        - Support: Rising trendline at bottom
        """
        if not hasattr(self, 'add_horizontal_line') or not hasattr(self, 'add_zone'):
            logger.warning("Chart marking methods not available")
            return

        # Extract key levels
        resistance_level = pattern_data.get('resistance_level')
        initial_support = pattern_data.get('initial_support')
        triangle_height = pattern_data.get('triangle_height')

        if resistance_level:
            # Draw horizontal resistance line
            self.add_horizontal_line(
                price=resistance_level,
                label=f"{pattern_name} - Resistance",
                color="#2196F3"
            )

        if initial_support and triangle_height:
            # Draw support zone (ascending)
            zone_height = triangle_height * 0.08  # 8% of triangle height
            self.add_support_zone(
                start_time=int(pivots[0].get('timestamp', 0)),
                end_time=int(pivots[-1].get('timestamp', 0)),
                top_price=initial_support + zone_height,
                bottom_price=initial_support - zone_height,
                label=f"{pattern_name} - Support"
            )

        logger.info(f"Drew Ascending Triangle pattern: {pattern_name}")

    def _draw_strategy_levels(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        pattern_name: str
    ) -> None:
        """Draw entry, stop loss, and take profit levels on chart.

        Args:
            entry_price: Entry price level
            stop_loss: Stop loss price level
            take_profit: Take profit price level
            pattern_name: Pattern name for labels
        """
        if not hasattr(self, 'add_horizontal_line'):
            logger.warning("add_horizontal_line method not available")
            return

        try:
            # Draw entry line (green)
            self.add_horizontal_line(
                price=entry_price,
                label=f"Entry - {pattern_name}",
                color="#26a69a"
            )

            # Draw stop loss line (red)
            self.add_horizontal_line(
                price=stop_loss,
                label=f"Stop Loss - {pattern_name}",
                color="#ef5350"
            )

            # Draw take profit line (blue)
            self.add_horizontal_line(
                price=take_profit,
                label=f"Take Profit - {pattern_name}",
                color="#42a5f5"
            )

            # Calculate risk-reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0

            logger.info(
                f"Drew strategy levels for {pattern_name}: "
                f"Entry={entry_price:.2f}, SL={stop_loss:.2f}, TP={take_profit:.2f}, "
                f"R:R={rr_ratio:.2f}"
            )

        except Exception as e:
            logger.error(f"Error drawing strategy levels: {e}")

    def _show_strategy_applied_notification(
        self,
        pattern_name: str,
        entry_price: Optional[float]
    ) -> None:
        """Show notification that strategy was applied.

        Args:
            pattern_name: Pattern name
            entry_price: Entry price (optional)
        """
        try:
            from PyQt6.QtWidgets import QMessageBox

            message = f"Strategy Applied: {pattern_name}"
            if entry_price:
                message += f"\n\nEntry Price: {entry_price:.2f}"
            message += "\n\nPattern levels have been drawn on the chart."

            QMessageBox.information(
                self._strategy_concept_window if self._strategy_concept_window else None,
                "Strategy Applied",
                message
            )

        except Exception as e:
            logger.error(f"Error showing notification: {e}")

    # ========== Bot Integration Methods ==========

    def apply_strategy_to_bot(
        self,
        pattern_type: str,
        strategy_data: dict,
        bot_controller=None
    ) -> bool:
        """Apply pattern strategy to BotController for automated trading.

        Args:
            pattern_type: Pattern type identifier (e.g., "cup_and_handle")
            strategy_data: Strategy data from Pattern Integration widget
            bot_controller: BotController instance (or retrieve from parent)

        Returns:
            True if strategy applied successfully, False otherwise
        """
        try:
            from src.core.tradingbot.pattern_strategy_converter import PatternStrategyConverter

            # Get bot controller
            if bot_controller is None:
                bot_controller = self._get_bot_controller()

            if bot_controller is None:
                logger.warning("No BotController available - cannot apply strategy")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self._strategy_concept_window,
                    "Bot Not Available",
                    "Trading bot is not initialized. Please start the bot first."
                )
                return False

            # Convert pattern strategy to bot configuration
            converter = PatternStrategyConverter()

            # Validate strategy data
            is_valid, error_msg = converter.validate_strategy_data(strategy_data)
            if not is_valid:
                logger.error(f"Invalid strategy data: {error_msg}")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self._strategy_concept_window,
                    "Invalid Strategy",
                    f"Cannot apply strategy: {error_msg}"
                )
                return False

            # Convert to StrategyProfile
            strategy_profile = converter.convert_to_strategy_profile(
                pattern_type, strategy_data
            )

            # Extract fixed levels
            entry_price, stop_loss, take_profit = converter.extract_fixed_levels(strategy_data)

            # Apply to bot controller
            self._apply_strategy_profile_to_bot(
                bot_controller,
                strategy_profile,
                entry_price,
                stop_loss,
                take_profit
            )

            logger.info(
                f"Strategy applied to bot: {strategy_profile.name}, "
                f"Entry={entry_price}, SL={stop_loss}, TP={take_profit}"
            )

            # Show confirmation
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self._strategy_concept_window,
                "Strategy Applied to Bot",
                f"Strategy '{strategy_profile.name}' has been applied to the trading bot.\n\n"
                f"Entry: {entry_price:.2f}\n"
                f"Stop Loss: {stop_loss:.2f}\n"
                f"Take Profit: {take_profit:.2f}\n\n"
                f"The bot will use this strategy for automated trading."
            )

            return True

        except Exception as e:
            logger.error(f"Error applying strategy to bot: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self._strategy_concept_window,
                "Error",
                f"Failed to apply strategy to bot: {e}"
            )
            return False

    def _get_bot_controller(self):
        """Get BotController instance from parent hierarchy.

        Returns:
            BotController instance or None if not found
        """
        # Try to get from chart window parent
        widget = self
        while widget is not None:
            if hasattr(widget, 'bot_controller') and widget.bot_controller is not None:
                logger.info(f"Found BotController in {widget.__class__.__name__}")
                return widget.bot_controller

            # Try parent attribute
            widget = getattr(widget, 'parent', lambda: None)()

        logger.warning("BotController not found in parent hierarchy")
        return None

    def _apply_strategy_profile_to_bot(
        self,
        bot_controller,
        strategy_profile,
        entry_price: float | None,
        stop_loss: float | None,
        take_profit: float | None
    ) -> None:
        """Apply strategy profile and fixed levels to bot controller.

        Args:
            bot_controller: BotController instance
            strategy_profile: StrategyProfile to apply
            entry_price: Fixed entry price level
            stop_loss: Fixed stop loss level
            take_profit: Fixed take profit level
        """
        # Set strategy profile
        bot_controller._active_strategy = strategy_profile
        bot_controller._manual_strategy_mode = True  # Disable auto-selection

        logger.info(
            f"Applied strategy profile to bot: {strategy_profile.name}, "
            f"entry_threshold={strategy_profile.entry_threshold}, "
            f"trailing_mode={strategy_profile.trailing_mode}, "
            f"trailing_multiplier={strategy_profile.trailing_multiplier}"
        )

        # Store fixed levels for reference
        # NOTE: BotController doesn't have built-in fixed levels storage,
        # so we add it as a custom attribute
        bot_controller._pattern_strategy_levels = {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'source': 'pattern_strategy',
        }

        logger.info(
            f"Stored pattern strategy levels in bot: "
            f"Entry={entry_price}, SL={stop_loss}, TP={take_profit}"
        )

    def show_bot_integration_dialog(self) -> None:
        """Show dialog to apply current strategy to bot.

        Allows user to review strategy and confirm application to bot.
        """
        try:
            from PyQt6.QtWidgets import (
                QDialog, QVBoxLayout, QLabel, QPushButton,
                QHBoxLayout, QGroupBox, QFormLayout
            )

            # Check if strategy is available
            if self._strategy_concept_window is None:
                logger.warning("Strategy Concept window not available")
                return

            # Get current strategy from Pattern Integration tab
            pattern_integration = getattr(self._strategy_concept_window, 'pattern_integration', None)
            if pattern_integration is None:
                logger.warning("Pattern Integration widget not available")
                return

            # Get selected strategy
            selected_pattern_type = getattr(pattern_integration, '_selected_pattern_type', None)
            selected_strategy = getattr(pattern_integration, '_selected_strategy', None)

            if not selected_pattern_type or not selected_strategy:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self._strategy_concept_window,
                    "No Strategy Selected",
                    "Please select a pattern and strategy first in the Pattern Integration tab."
                )
                return

            # Create dialog
            dialog = QDialog(self._strategy_concept_window)
            dialog.setWindowTitle("Apply Strategy to Bot")
            dialog.setMinimumWidth(400)

            layout = QVBoxLayout(dialog)

            # Header
            header = QLabel("<b>Apply Pattern Strategy to Trading Bot</b>")
            layout.addWidget(header)

            # Strategy details group
            details_group = QGroupBox("Strategy Details")
            details_layout = QFormLayout(details_group)

            pattern_name = selected_strategy.get('pattern_name', 'Unknown')
            pattern_data = selected_strategy.get('pattern_data', {})

            details_layout.addRow("Pattern:", QLabel(pattern_name))
            details_layout.addRow("Type:", QLabel(selected_pattern_type))

            entry = pattern_data.get('entry_price', 0)
            stop = pattern_data.get('stop_loss', 0)
            target = pattern_data.get('take_profit', 0)

            details_layout.addRow("Entry:", QLabel(f"{entry:.2f}"))
            details_layout.addRow("Stop Loss:", QLabel(f"{stop:.2f}"))
            details_layout.addRow("Take Profit:", QLabel(f"{target:.2f}"))

            # Calculate R:R
            risk = abs(entry - stop) if entry and stop else 0
            reward = abs(target - entry) if target and entry else 0
            rr = reward / risk if risk > 0 else 0
            details_layout.addRow("Risk:Reward:", QLabel(f"1:{rr:.2f}"))

            layout.addWidget(details_group)

            # Buttons
            button_layout = QHBoxLayout()

            apply_btn = QPushButton("✓ Apply to Bot")
            apply_btn.clicked.connect(
                lambda: self._on_apply_to_bot_clicked(
                    dialog,
                    selected_pattern_type,
                    selected_strategy
                )
            )

            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)

            button_layout.addStretch()
            button_layout.addWidget(apply_btn)
            button_layout.addWidget(cancel_btn)

            layout.addLayout(button_layout)

            dialog.exec()

        except Exception as e:
            logger.error(f"Error showing bot integration dialog: {e}")

    def _on_apply_to_bot_clicked(
        self,
        dialog,
        pattern_type: str,
        strategy_data: dict
    ) -> None:
        """Handle Apply to Bot button click."""
        # Apply strategy
        success = self.apply_strategy_to_bot(pattern_type, strategy_data)

        if success:
            # Close dialog
            dialog.accept()
        else:
            # Keep dialog open on error
            pass
