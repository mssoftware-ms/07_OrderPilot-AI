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

Architecture:
    Uses mixin pattern to separate concerns:
    - BitunixAPIWidgetUI: UI construction
    - BitunixAPIWidgetEvents: Event handlers
    - BitunixAPIWidgetLogic: API integration

Signals:
    order_placed(str): Emitted when order is placed successfully
    price_needed(str): Emitted when price is required for calculations
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox

from src.ui.widgets.bitunix_trading.bitunix_api_widget_ui import BitunixAPIWidgetUI
from src.ui.widgets.bitunix_trading.bitunix_api_widget_events import BitunixAPIWidgetEvents
from src.ui.widgets.bitunix_trading.bitunix_api_widget_logic import BitunixAPIWidgetLogic

logger = logging.getLogger(__name__)


class BitunixTradingAPIWidget(
    BitunixAPIWidgetUI,
    BitunixAPIWidgetEvents,
    BitunixAPIWidgetLogic,
    QGroupBox
):
    """Compact trading interface for Bitunix API.

    Provides quick order entry with automatic quantity/volume calculation.
    Designed for the Trading Bot Signals tab.

    This widget combines three mixins:
    - BitunixAPIWidgetUI: UI construction methods
    - BitunixAPIWidgetEvents: Event handlers and calculations
    - BitunixAPIWidgetLogic: Order placement and adapter management

    Signals:
        order_placed: Emitted when order is placed successfully (order_id: str)
        price_needed: Emitted when price is required for calculations (symbol: str)
    """

    order_placed = pyqtSignal(str)  # order_id
    price_needed = pyqtSignal(str)  # symbol

    def __init__(self, parent=None):
        """Initialize the Bitunix Trading API Widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Bitunix Trading API", parent)

        # Store parent reference for price requests
        self.parent_widget = parent

        # Internal state
        self._adapter = None
        self._current_symbol = None
        self._last_price = 0.0
        self._last_edited = "quantity"
        self._is_updating = False  # Prevent recursive updates

        # Setup UI components (from BitunixAPIWidgetUI mixin)
        self._setup_ui()

        # Connect event handlers (from BitunixAPIWidgetEvents mixin)
        self._connect_event_handlers()

        # Set initial state
        self._set_trade_mode_live(False)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<BitunixTradingAPIWidget "
            f"symbol={self._current_symbol} "
            f"price={self._last_price:.2f} "
            f"adapter={self._adapter.__class__.__name__ if self._adapter else None}>"
        )
