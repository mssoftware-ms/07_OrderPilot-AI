"""Bitunix Mirror Widget Mixin - Enables widgets to act as synchronized mirrors.

Provides the interface and base implementation for widgets that mirror
a master widget's state and delegate actions back to the master.

Usage:
    class MyMirrorWidget(BitunixMirrorMixin, QWidget):
        def __init__(self, master_widget, state_manager):
            super().__init__()
            self.setup_as_mirror(master_widget, state_manager)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

from PyQt6.QtCore import QObject

if TYPE_CHECKING:
    from .bitunix_state_manager import (
        BitunixTradingStateManager,
        TradingState,
        TradingMode,
        AdapterStatus,
    )

logger = logging.getLogger(__name__)


@runtime_checkable
class IBitunixMirror(Protocol):
    """Protocol for mirror-capable widgets.

    Any widget implementing this protocol can be registered as a mirror
    with the BitunixTradingStateManager.
    """

    def sync_from_state(self, state: "TradingState") -> None:
        """Synchronize widget UI with the given state snapshot."""
        ...

    def on_state_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Handle a specific state change."""
        ...

    def set_mirror_mode(self, is_mirror: bool) -> None:
        """Enable or disable mirror mode."""
        ...


class BitunixMirrorMixin:
    """Mixin that enables a widget to act as a mirror of a master widget.

    Features:
    - Automatic state synchronization with master
    - Order delegation to master/state manager
    - Visual indication of mirror mode
    - Read-only mode support

    Attributes:
        _is_mirror: Whether widget is in mirror mode
        _master_widget: Reference to master widget (if mirroring)
        _state_manager: Central state manager reference
        _mirror_readonly: Whether mirror should be read-only
    """

    _is_mirror: bool = False
    _master_widget: Optional[Any] = None
    _state_manager: Optional["BitunixTradingStateManager"] = None
    _mirror_readonly: bool = False

    def setup_as_mirror(
        self,
        master_widget: Any,
        state_manager: "BitunixTradingStateManager",
        readonly: bool = False
    ) -> None:
        """Configure widget as a mirror of the master widget.

        Args:
            master_widget: The master widget to mirror
            state_manager: Central state manager for coordination
            readonly: If True, disable order placement in mirror
        """
        self._is_mirror = True
        self._master_widget = master_widget
        self._state_manager = state_manager
        self._mirror_readonly = readonly

        # Register with state manager
        state_manager.register_widget(self, is_master=False)

        # Connect to state manager signals
        self._connect_state_signals(state_manager)

        # Apply initial state
        self.sync_from_state(state_manager.state)

        # Apply mirror styling
        self._apply_mirror_styling()

        logger.info(f"{self.__class__.__name__} configured as mirror (readonly={readonly})")

    def setup_as_master(
        self,
        state_manager: "BitunixTradingStateManager"
    ) -> None:
        """Configure widget as a master (state owner).

        Args:
            state_manager: Central state manager for coordination
        """
        self._is_mirror = False
        self._master_widget = None
        self._state_manager = state_manager
        self._mirror_readonly = False

        # Register with state manager
        state_manager.register_widget(self, is_master=True)

        logger.info(f"{self.__class__.__name__} configured as master")

    def _connect_state_signals(self, state_manager: "BitunixTradingStateManager") -> None:
        """Connect to state manager signals for synchronization."""
        # Generic state change handler
        state_manager.state_changed.connect(self._on_manager_state_changed)

        # Specific state handlers (more efficient than generic)
        state_manager.mode_changed.connect(self._on_manager_mode_changed)
        state_manager.symbol_changed.connect(self._on_manager_symbol_changed)
        state_manager.price_updated.connect(self._on_manager_price_updated)
        state_manager.adapter_status_changed.connect(self._on_manager_adapter_status_changed)
        state_manager.trading_enabled_changed.connect(self._on_manager_trading_enabled_changed)

        # Order completion handler
        state_manager.order_completed.connect(self._on_manager_order_completed)

    def _disconnect_state_signals(self) -> None:
        """Disconnect from state manager signals."""
        if self._state_manager:
            try:
                self._state_manager.state_changed.disconnect(self._on_manager_state_changed)
                self._state_manager.mode_changed.disconnect(self._on_manager_mode_changed)
                self._state_manager.symbol_changed.disconnect(self._on_manager_symbol_changed)
                self._state_manager.price_updated.disconnect(self._on_manager_price_updated)
                self._state_manager.adapter_status_changed.disconnect(
                    self._on_manager_adapter_status_changed
                )
                self._state_manager.trading_enabled_changed.disconnect(
                    self._on_manager_trading_enabled_changed
                )
                self._state_manager.order_completed.disconnect(self._on_manager_order_completed)
            except (TypeError, RuntimeError):
                pass  # Already disconnected

    # ─────────────────────────────────────────────────────────────────────
    # State Synchronization (Override in subclass for custom behavior)
    # ─────────────────────────────────────────────────────────────────────

    def sync_from_state(self, state: "TradingState") -> None:
        """Synchronize widget UI with the given state snapshot.

        Override this method in subclass to implement custom sync logic.
        """
        # Default implementation - call individual setters
        if hasattr(self, "set_symbol"):
            self.set_symbol(state.symbol)

        if hasattr(self, "set_price"):
            self.set_price(state.current_price)

        if hasattr(self, "_update_mode_display"):
            self._update_mode_display(state.mode)

        if hasattr(self, "_update_adapter_status"):
            self._update_adapter_status(state.adapter_status)

        if hasattr(self, "_update_button_states"):
            self._update_button_states()

    def on_state_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Handle a specific state change.

        Override this method in subclass for custom state change handling.
        """
        logger.debug(f"Mirror state change: {key} = {new_value}")

    def set_mirror_mode(self, is_mirror: bool) -> None:
        """Enable or disable mirror mode."""
        self._is_mirror = is_mirror
        if is_mirror:
            self._apply_mirror_styling()
        else:
            self._remove_mirror_styling()

    # ─────────────────────────────────────────────────────────────────────
    # Signal Handlers
    # ─────────────────────────────────────────────────────────────────────

    def _on_manager_state_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Handle generic state change from manager."""
        self.on_state_changed(key, old_value, new_value)

    def _on_manager_mode_changed(self, mode: "TradingMode") -> None:
        """Handle mode change from manager."""
        if hasattr(self, "_update_mode_display"):
            self._update_mode_display(mode)

        if hasattr(self, "_update_button_states"):
            self._update_button_states()

    def _on_manager_symbol_changed(self, symbol: str) -> None:
        """Handle symbol change from manager."""
        if hasattr(self, "set_symbol"):
            self.set_symbol(symbol)

    def _on_manager_price_updated(self, price: float) -> None:
        """Handle price update from manager."""
        if hasattr(self, "set_price"):
            self.set_price(price)

    def _on_manager_adapter_status_changed(self, status: "AdapterStatus") -> None:
        """Handle adapter status change from manager."""
        if hasattr(self, "_update_adapter_status"):
            self._update_adapter_status(status)

        if hasattr(self, "_update_button_states"):
            self._update_button_states()

    def _on_manager_trading_enabled_changed(self, enabled: bool) -> None:
        """Handle trading enabled change from manager."""
        if hasattr(self, "_update_button_states"):
            self._update_button_states()

    def _on_manager_order_completed(self, order_id: str, success: bool, message: str) -> None:
        """Handle order completion from manager."""
        if hasattr(self, "_on_order_completed"):
            self._on_order_completed(order_id, success, message)

    # ─────────────────────────────────────────────────────────────────────
    # Order Delegation
    # ─────────────────────────────────────────────────────────────────────

    async def delegate_order(self, order_params: dict) -> tuple[bool, str]:
        """Delegate order execution to state manager.

        This ensures orders are coordinated through the central manager,
        preventing duplicates and ensuring proper state synchronization.

        Args:
            order_params: Order parameters

        Returns:
            Tuple of (success, message)
        """
        if self._mirror_readonly:
            return False, "Mirror is read-only - orders disabled"

        if not self._state_manager:
            return False, "No state manager configured"

        return await self._state_manager.request_order(
            order_params=order_params,
            source_widget=self
        )

    # ─────────────────────────────────────────────────────────────────────
    # Mirror Styling
    # ─────────────────────────────────────────────────────────────────────

    def _apply_mirror_styling(self) -> None:
        """Apply visual styling to indicate mirror mode.

        Override in subclass for custom styling.
        """
        if hasattr(self, "setStyleSheet"):
            # Add subtle border to indicate mirror
            current_style = getattr(self, "styleSheet", lambda: "")()
            if "/* MIRROR */" not in current_style:
                mirror_style = """
                /* MIRROR */
                QGroupBox {
                    border: 1px solid #4a90d9;
                }
                """
                self.setStyleSheet(current_style + mirror_style)

    def _remove_mirror_styling(self) -> None:
        """Remove mirror mode visual styling."""
        if hasattr(self, "styleSheet") and hasattr(self, "setStyleSheet"):
            current_style = self.styleSheet()
            if "/* MIRROR */" in current_style:
                # Remove mirror style block
                start = current_style.find("/* MIRROR */")
                end = current_style.find("}", start) + 1
                new_style = current_style[:start] + current_style[end:]
                self.setStyleSheet(new_style)

    # ─────────────────────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────────────────────

    def cleanup_mirror(self) -> None:
        """Clean up mirror connections and resources."""
        self._disconnect_state_signals()

        if self._state_manager:
            self._state_manager.unregister_widget(self)

        self._is_mirror = False
        self._master_widget = None
        self._state_manager = None

        self._remove_mirror_styling()

        logger.debug(f"{self.__class__.__name__} mirror cleanup complete")


class BitunixMasterMixin:
    """Mixin for master widgets that own and propagate state changes.

    Master widgets can modify state directly and changes propagate to mirrors.
    """

    _state_manager: Optional["BitunixTradingStateManager"] = None

    def setup_state_manager(
        self,
        state_manager: "BitunixTradingStateManager"
    ) -> None:
        """Configure widget with state manager as master.

        Args:
            state_manager: Central state manager
        """
        self._state_manager = state_manager
        state_manager.register_widget(self, is_master=True)

        logger.info(f"{self.__class__.__name__} configured as master with state manager")

    def propagate_symbol_change(self, symbol: str) -> None:
        """Propagate symbol change to all mirrors via state manager."""
        if self._state_manager:
            self._state_manager.set_symbol(symbol)

    def propagate_price_update(self, price: float) -> None:
        """Propagate price update to all mirrors via state manager."""
        if self._state_manager:
            self._state_manager.set_price(price)

    def propagate_mode_change(self, mode: "TradingMode") -> None:
        """Propagate mode change to all mirrors via state manager."""
        if self._state_manager:
            self._state_manager.set_mode(mode)

    def propagate_adapter_status(self, status: "AdapterStatus") -> None:
        """Propagate adapter status change to all mirrors via state manager."""
        if self._state_manager:
            self._state_manager.set_adapter_status(status)
