"""Bot UI Control Mixin - Main Orchestrator (Refactored).

Main mixin for bot control tab that delegates to specialized helper classes:
- BotUIControlWidgets: UI widget creation
- BotUIControlHandlers: Event handling
- BotSettingsManager: Settings persistence

Refactored from 898 LOC monolith using composition pattern.

Module 4/4 of bot_ui_control_mixin.py split (Main Orchestrator).
"""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .bot_ui_control_widgets import BotUIControlWidgets
from .bot_ui_control_handlers import BotUIControlHandlers
from .bot_settings_manager import BotSettingsManager

logger = logging.getLogger(__name__)


class BotUIControlMixin:
    """Bot UI Control Mixin - Main orchestrator using helper classes.

    This mixin creates the bot control tab and delegates all responsibilities
    to specialized helper classes via composition pattern:

    - BotUIControlWidgets: Creates all UI elements
    - BotUIControlHandlers: Handles all UI events
    - BotSettingsManager: Manages settings persistence

    This approach reduces complexity from 898 LOC to ~250 LOC and maintains
    clear separation of concerns.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mixin (called by parent class).

        Note: This is a mixin, so __init__ is typically called as part of
        multiple inheritance. Helper classes are initialized lazily in
        _ensure_helpers() to avoid initialization order issues.
        """
        super().__init__(*args, **kwargs)
        # Helpers are initialized lazily
        self._widgets_helper: BotUIControlWidgets | None = None
        self._handlers_helper: BotUIControlHandlers | None = None
        self._settings_helper: BotSettingsManager | None = None

    def _ensure_helpers(self) -> None:
        """Lazy initialization of helper classes (composition pattern).

        Called on first use to ensure parent class is fully initialized.
        """
        if self._widgets_helper is None:
            self._widgets_helper = BotUIControlWidgets(parent=self)
            self._handlers_helper = BotUIControlHandlers(parent=self)
            self._settings_helper = BotSettingsManager(parent=self)
            logger.debug("BotUIControlMixin helpers initialized")

    def _create_bot_control_tab(self) -> QWidget:
        """Create bot control tab with start/stop and settings.

        Main entry point that orchestrates all UI creation.
        """
        self._ensure_helpers()

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Control Group (Start/Stop/Pause)
        layout.addWidget(self._build_control_group())

        # Settings Row (Bot Settings + Trailing Settings)
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)
        settings_row.addWidget(self._build_settings_group())
        settings_row.addWidget(self._build_trailing_group())
        layout.addLayout(settings_row)

        # Pattern Validation Group
        layout.addWidget(self._build_pattern_group())

        # Trigger initial UI updates
        self._on_trailing_mode_changed()
        self._on_regime_adaptive_changed()

        # Bottom Row (Display Options + Help)
        layout.addLayout(self._build_bottom_row())

        layout.addStretch()
        return widget

    # =========================================================================
    # UI BUILDER METHODS (Delegated to BotUIControlWidgets)
    # =========================================================================

    def _build_control_group(self):
        """Create control group (delegated to widgets helper)."""
        return self._widgets_helper.build_control_group()

    def _build_settings_group(self):
        """Create settings group (delegated to widgets helper)."""
        return self._widgets_helper.build_settings_group()

    def _build_trailing_group(self):
        """Create trailing group (delegated to widgets helper)."""
        return self._widgets_helper.build_trailing_group()

    def _build_pattern_group(self):
        """Create pattern group (delegated to widgets helper)."""
        return self._widgets_helper.build_pattern_group()

    def _build_bottom_row(self):
        """Create bottom row with display options and help (delegated)."""
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        bottom_row.addWidget(self._widgets_helper.build_display_group())
        bottom_row.addWidget(self._widgets_helper.build_help_button())
        bottom_row.addStretch()
        return bottom_row

    # =========================================================================
    # EVENT HANDLERS (Delegated to BotUIControlHandlers)
    # =========================================================================

    def _on_open_help_clicked(self) -> None:
        """Open help documentation (delegated to handlers helper)."""
        self._handlers_helper.on_open_help_clicked()

    def _on_leverage_override_changed(self, state: int) -> None:
        """Handle leverage override checkbox (delegated to handlers helper)."""
        self._handlers_helper.on_leverage_override_changed(state)

    def _on_leverage_slider_changed(self, value: int) -> None:
        """Handle leverage slider value change (delegated to handlers helper)."""
        self._handlers_helper.on_leverage_slider_changed(value)

    def _on_trade_direction_changed(self, direction: str) -> None:
        """Handle trade direction change (delegated to handlers helper)."""
        self._handlers_helper.on_trade_direction_changed(direction)

    def _update_bot_display(self) -> None:
        """Update bot status display (QTimer callback). Delegates to widgets helper."""
        if self._widgets_helper:
            self._widgets_helper.update_bot_display()

    def _on_bot_start_clicked(self) -> None:
        """Handle bot start button click. Delegates to handlers helper."""
        if self._handlers_helper:
            self._handlers_helper.on_bot_start_clicked()

    def _on_bot_stop_clicked(self) -> None:
        """Handle bot stop button click. Delegates to handlers helper."""
        if self._handlers_helper:
            self._handlers_helper.on_bot_stop_clicked()

    def _on_bot_settings_clicked(self) -> None:
        """Handle bot settings button click. Delegates to settings helper."""
        if self._settings_helper:
            self._settings_helper.on_bot_settings_clicked()

    # =========================================================================
    # SETTINGS MANAGEMENT (Delegated to BotSettingsManager)
    # =========================================================================

    def _get_bot_settings(self) -> dict:
        """Get current bot settings (delegated to settings helper)."""
        return self._settings_helper.get_bot_settings()

    def _apply_bot_settings(self, settings: dict) -> None:
        """Apply bot settings to UI (delegated to settings helper)."""
        self._settings_helper.apply_bot_settings(settings)

    def _on_save_defaults_clicked(self) -> None:
        """Save settings as defaults (delegated to settings helper)."""
        self._settings_helper.on_save_defaults_clicked()

    def _on_load_defaults_clicked(self) -> None:
        """Load default settings (delegated to settings helper)."""
        self._settings_helper.on_load_defaults_clicked()

    def _on_reset_defaults_clicked(self) -> None:
        """Reset to factory defaults (delegated to settings helper)."""
        self._settings_helper.on_reset_defaults_clicked()

    # =========================================================================
    # PUBLIC API (Retained for backward compatibility)
    # =========================================================================

    def _set_leverage(self, value: int) -> None:
        """Set leverage slider value.

        Args:
            value: Leverage value (1-100)
        """
        if hasattr(self, 'leverage_slider'):
            self.leverage_slider.setValue(value)

    def get_leverage_override(self) -> tuple[bool, int]:
        """Get current leverage override status.

        Returns:
            Tuple of (override_enabled, leverage_value)
        """
        if hasattr(self, 'leverage_override_cb') and hasattr(self, 'leverage_slider'):
            return (
                self.leverage_override_cb.isChecked(),
                self.leverage_slider.value()
            )
        return (False, 1)

    def get_trade_direction(self) -> str:
        """Get current trade direction.

        Returns:
            'AUTO', 'BOTH', 'LONG_ONLY' or 'SHORT_ONLY'
        """
        if hasattr(self, 'trade_direction_combo'):
            return self.trade_direction_combo.currentText()
        return "BOTH"

    def set_trade_direction_from_backtest(self, direction: str) -> None:
        """Set trade direction based on backtesting result.

        Args:
            direction: 'BOTH', 'LONG_ONLY' or 'SHORT_ONLY'
        """
        if hasattr(self, 'trade_direction_combo'):
            idx = self.trade_direction_combo.findText(direction)
            if idx >= 0:
                self.trade_direction_combo.setCurrentIndex(idx)
                logger.info(f"Trade Direction durch Backtesting gesetzt: {direction}")

    # =========================================================================
    # PLACEHOLDER METHODS (Must be implemented by parent class)
    # =========================================================================
    # These methods are referenced by helper classes but must be implemented
    # by the parent class (typically ChartWindow or similar):
    #
    # - _on_bot_start_clicked()
    # - _on_bot_stop_clicked()
    # - _on_bot_pause_clicked()
    # - _on_ki_mode_changed()
    # - _on_trailing_mode_changed()
    # - _on_derivathandel_changed()
    # - _on_regime_adaptive_changed()
    # - _on_display_option_changed()
    # - _on_debug_hud_changed()
    # =========================================================================
