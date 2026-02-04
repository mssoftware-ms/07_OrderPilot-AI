"""Bitunix Trading UI Components.

Dockable trading widget for Bitunix Futures trading.
Includes manual trading, automatic bot trading, and backtesting tabs.

API Widget Components (Split for maintainability):
    - BitunixAPIWidgetUI: UI construction methods
    - BitunixAPIWidgetEvents: Event handlers
    - BitunixAPIWidgetLogic: API integration logic

State Management (Master/Mirror Pattern):
    - BitunixTradingStateManager: Central state manager
    - OrderExecutionGuard: Prevents duplicate orders
    - TradingState: Immutable state snapshot
"""

from .bitunix_trading_widget import BitunixTradingWidget
from .bitunix_trading_mixin import BitunixTradingMixin
from .bot_tab_main import BotTab
from .backtest_tab import BacktestTab

# API Widget Components (NEW - split from bitunix_trading_api_widget.py)
from .bitunix_api_widget_ui import BitunixAPIWidgetUI
from .bitunix_api_widget_compact_ui import BitunixAPIWidgetCompactUI
from .bitunix_api_widget_events import BitunixAPIWidgetEvents
from .bitunix_api_widget_logic import BitunixAPIWidgetLogic

# State Management (Master/Mirror Pattern)
from .bitunix_state_manager import (
    BitunixTradingStateManager,
    OrderExecutionGuard,
    TradingState,
    TradingMode,
    AdapterStatus,
)
from .bitunix_mirror_mixin import (
    BitunixMirrorMixin,
    BitunixMasterMixin,
    IBitunixMirror,
)
from .signals_table_mirror import (
    SignalsTableMirror,
    SignalsTableMirrorWidget,
)

__all__ = [
    # Widgets
    "BitunixTradingWidget",
    "BitunixTradingMixin",
    "BotTab",
    "BacktestTab",
    # API Widget Components
    "BitunixAPIWidgetUI",
    "BitunixAPIWidgetCompactUI",
    "BitunixAPIWidgetEvents",
    "BitunixAPIWidgetLogic",
    # State Management
    "BitunixTradingStateManager",
    "OrderExecutionGuard",
    "TradingState",
    "TradingMode",
    "AdapterStatus",
    # Mirror Pattern
    "BitunixMirrorMixin",
    "BitunixMasterMixin",
    "IBitunixMirror",
    # Signals Table Mirror
    "SignalsTableMirror",
    "SignalsTableMirrorWidget",
]
