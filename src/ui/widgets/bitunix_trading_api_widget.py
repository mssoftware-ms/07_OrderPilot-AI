"""Bitunix Trading API Widget - Main Orchestrator.

Compact trading interface for Bitunix API, designed for the Trading Bot Signals tab.
This is the main widget that composes UI, event handling, and API logic mixins.

Features:
    - Symbol selection
    - Quantity (Base Asset) ↔ Volume (USDT) conversion
    - Leverage control
    - Buy/Sell buttons
    - Live/Paper mode support
    - TP/SL controls
    - Trailing stop loss
    - Mirror mode for synchronized dock widgets
    - Compact vertical layout for dock panels

Architecture:
    Uses mixin pattern to separate concerns:
    - BitunixAPIWidgetUI: UI construction (horizontal layout)
    - BitunixAPIWidgetCompactUI: UI construction (vertical layout for dock)
    - BitunixAPIWidgetEvents: Event handlers
    - BitunixAPIWidgetLogic: API integration
    - BitunixMirrorMixin: State synchronization for mirror widgets

Signals:
    order_placed(str): Emitted when order is placed successfully
    price_needed(str): Emitted when price is required for calculations
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox

from src.ui.widgets.bitunix_trading.bitunix_api_widget_ui import BitunixAPIWidgetUI
from src.ui.widgets.bitunix_trading.bitunix_api_widget_compact_ui import BitunixAPIWidgetCompactUI
from src.ui.widgets.bitunix_trading.bitunix_api_widget_events import BitunixAPIWidgetEvents
from src.ui.widgets.bitunix_trading.bitunix_api_widget_logic import BitunixAPIWidgetLogic
from src.ui.widgets.bitunix_trading.bitunix_mirror_mixin import BitunixMirrorMixin

if TYPE_CHECKING:
    from src.ui.widgets.bitunix_trading.bitunix_state_manager import (
        BitunixTradingStateManager,
        TradingState,
        TradingMode,
        AdapterStatus,
    )

logger = logging.getLogger(__name__)


class BitunixTradingAPIWidget(
    QGroupBox,
    BitunixAPIWidgetUI,
    BitunixAPIWidgetCompactUI,
    BitunixAPIWidgetEvents,
    BitunixAPIWidgetLogic,
    BitunixMirrorMixin,
):
    """Compact trading interface for Bitunix API.

    Provides quick order entry with automatic quantity/volume calculation.
    Designed for the Trading Bot Signals tab and dock panels.

    This widget combines multiple mixins:
    - BitunixAPIWidgetUI: UI construction methods (horizontal layout)
    - BitunixAPIWidgetCompactUI: UI construction (vertical layout for dock)
    - BitunixAPIWidgetEvents: Event handlers and calculations
    - BitunixAPIWidgetLogic: Order placement and adapter management
    - BitunixMirrorMixin: State synchronization for mirror mode

    Modes:
        - Master mode (default): Owns state, executes orders directly
        - Mirror mode: Synchronizes with master, delegates orders

    Layouts:
        - Horizontal (default): 1005px wide, for TradingBotWindow
        - Compact vertical: 360px wide, for dock panels

    Signals:
        order_placed: Emitted when order is placed successfully (order_id: str)
        price_needed: Emitted when price is required for calculations (symbol: str)
    """

    order_placed = pyqtSignal(str)  # order_id
    price_needed = pyqtSignal(str)  # symbol

    def __init__(
        self,
        parent=None,
        *,
        is_mirror: bool = False,
        state_manager: Optional["BitunixTradingStateManager"] = None,
        compact_layout: bool = False,
        title: str = "Bitunix Trading API"
    ):
        """Initialize the Bitunix Trading API Widget.

        Args:
            parent: Optional parent widget
            is_mirror: If True, widget acts as mirror (syncs with master)
            state_manager: Central state manager for coordination
            compact_layout: If True, use vertical compact layout for dock
            title: Widget title
        """
        super().__init__(title, parent)

        # Store parent reference for price requests
        self.parent_widget = parent

        # Internal state
        self._adapter = None
        self._current_symbol = None
        self._last_price = 0.0
        self._last_edited = "quantity"
        self._is_updating = False  # Prevent recursive updates

        # Mirror mode state (from BitunixMirrorMixin)
        self._is_mirror = is_mirror
        self._compact_layout = compact_layout
        self._state_manager_ref = state_manager

        # Setup UI components based on layout mode
        if compact_layout:
            self._setup_compact_ui()
        else:
            self._setup_ui()

        # Connect event handlers (from BitunixAPIWidgetEvents mixin)
        self._connect_event_handlers()

        # Setup mirror mode if requested
        if is_mirror and state_manager:
            self.setup_as_mirror(
                master_widget=None,  # Will be set later if needed
                state_manager=state_manager,
                readonly=False  # Full functionality in mirror
            )
            logger.info(f"BitunixTradingAPIWidget initialized as MIRROR (compact={compact_layout})")
        elif state_manager:
            self.setup_as_master(state_manager)
            logger.info(f"BitunixTradingAPIWidget initialized as MASTER (compact={compact_layout})")
        else:
            logger.info(f"BitunixTradingAPIWidget initialized (standalone, compact={compact_layout})")

        # Set initial state
        self._set_trade_mode_live(False)

    @property
    def is_mirror(self) -> bool:
        """Check if widget is in mirror mode."""
        return self._is_mirror

    @property
    def is_compact(self) -> bool:
        """Check if widget uses compact layout."""
        return self._compact_layout

    def __repr__(self) -> str:
        """String representation for debugging."""
        mode = "MIRROR" if self._is_mirror else "MASTER"
        layout = "compact" if self._compact_layout else "horizontal"
        return (
            f"<BitunixTradingAPIWidget "
            f"mode={mode} layout={layout} "
            f"symbol={self._current_symbol} "
            f"price={self._last_price:.2f} "
            f"adapter={self._adapter.__class__.__name__ if self._adapter else None}>"
        )
