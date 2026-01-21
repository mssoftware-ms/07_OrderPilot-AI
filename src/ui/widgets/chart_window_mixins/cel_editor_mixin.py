"""CEL Editor Mixin for ChartWindow (Phase 7).

Provides integration with CEL Editor window (Visual Pattern Builder with AI-Assistent).
Follows the same pattern as EntryAnalyzerMixin and StrategyConceptMixin.

Created: 2026-01-21
Part of: Phase 7.1.3 - UI Controls Integration
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CelEditorMixin:
    """Mixin for CEL Editor window integration.

    Provides methods to show/hide the CEL Editor window and manage its state.
    Button state is synchronized via the toolbar button's checked property.
    """

    # Class attributes
    _cel_editor_window: Optional[object] = None

    def _init_cel_editor(self) -> None:
        """Initialize CEL Editor window integration.

        Must be called from ChartWindow __init__.
        """
        self._cel_editor_window = None
        self._setup_cel_editor_signals()

    def _setup_cel_editor_signals(self) -> None:
        """Setup signal connections for CEL Editor.

        Should be called after __init__ to connect chart signals.
        """
        # Connect to chart data changes if needed
        if hasattr(self, "symbol_changed"):
            self.symbol_changed.connect(self._on_cel_editor_symbol_changed)
        if hasattr(self, "timeframe_changed"):
            self.timeframe_changed.connect(self._on_cel_editor_timeframe_changed)

    def show_cel_editor(self) -> None:
        """Show the CEL Editor window."""
        from src.ui.windows.cel_editor import CelEditorWindow

        if self._cel_editor_window is None:
            # Create new CEL Editor window
            strategy_name = f"{getattr(self, 'symbol', 'BTC')} Strategy"
            self._cel_editor_window = CelEditorWindow(
                strategy_name=strategy_name,
                parent=self
            )

            # Connect window close event to reset button state
            self._cel_editor_window.finished.connect(
                self._on_cel_editor_closed
            )

            # Optional: Connect strategy export signal if available
            if hasattr(self._cel_editor_window, 'strategy_exported'):
                self._cel_editor_window.strategy_exported.connect(
                    self._on_cel_strategy_exported
                )

        # Update window context with current chart data
        self._update_cel_editor_context()

        self._cel_editor_window.show()
        self._cel_editor_window.raise_()
        self._cel_editor_window.activateWindow()

        # Set button checked state if button exists
        if hasattr(self, 'cel_editor_button'):
            self.cel_editor_button.setChecked(True)

        logger.info("CEL Editor window opened")

    def hide_cel_editor(self) -> None:
        """Hide the CEL Editor window."""
        if self._cel_editor_window is not None:
            self._cel_editor_window.hide()

            # Uncheck button
            if hasattr(self, 'cel_editor_button'):
                self.cel_editor_button.setChecked(False)

            logger.info("CEL Editor window hidden")

    def _update_cel_editor_context(self) -> None:
        """Update CEL Editor window with current chart context."""
        if self._cel_editor_window is None:
            return

        # Update strategy name based on current symbol
        symbol = getattr(self, 'symbol', None) or getattr(self, '_symbol', 'BTC')
        timeframe = getattr(self, 'timeframe', None) or getattr(self, '_timeframe', '1m')

        # Update window title if method available
        if hasattr(self._cel_editor_window, 'set_symbol_context'):
            self._cel_editor_window.set_symbol_context(symbol, timeframe)

        logger.debug(f"Updated CEL Editor context: {symbol} @ {timeframe}")

    def _on_cel_editor_closed(self) -> None:
        """Handle CEL Editor window close event.

        Resets the toolbar button checked state when window is closed.
        """
        if hasattr(self, 'cel_editor_button'):
            self.cel_editor_button.setChecked(False)

        logger.info("CEL Editor window closed by user")

    def _on_cel_strategy_exported(self, strategy_path: str) -> None:
        """Handle strategy export from CEL Editor.

        Args:
            strategy_path: Path to exported strategy JSON file
        """
        logger.info(f"Strategy exported from CEL Editor: {strategy_path}")

        # Optional: Show notification to user
        if hasattr(self, 'show_notification'):
            self.show_notification(
                f"Strategy exported to: {strategy_path}",
                level="success"
            )

    def _on_cel_editor_symbol_changed(self, symbol: str) -> None:
        """Handle symbol change event.

        Updates CEL Editor context when chart symbol changes.

        Args:
            symbol: New symbol name
        """
        if self._cel_editor_window is not None and self._cel_editor_window.isVisible():
            self._update_cel_editor_context()
            logger.debug(f"CEL Editor context updated for new symbol: {symbol}")

    def _on_cel_editor_timeframe_changed(self, timeframe: str) -> None:
        """Handle timeframe change event.

        Updates CEL Editor context when chart timeframe changes.

        Args:
            timeframe: New timeframe
        """
        if self._cel_editor_window is not None and self._cel_editor_window.isVisible():
            self._update_cel_editor_context()
            logger.debug(f"CEL Editor context updated for new timeframe: {timeframe}")
