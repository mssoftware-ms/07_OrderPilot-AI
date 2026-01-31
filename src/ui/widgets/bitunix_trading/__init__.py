"""Bitunix Trading UI Components.

Dockable trading widget for Bitunix Futures trading.
Includes manual trading, automatic bot trading, and backtesting tabs.

API Widget Components (Split for maintainability):
    - BitunixAPIWidgetUI: UI construction methods
    - BitunixAPIWidgetEvents: Event handlers
    - BitunixAPIWidgetLogic: API integration logic
"""

from .bitunix_trading_widget import BitunixTradingWidget
from .bitunix_trading_mixin import BitunixTradingMixin
from .bot_tab_main import BotTab
from .backtest_tab import BacktestTab

# API Widget Components (NEW - split from bitunix_trading_api_widget.py)
from .bitunix_api_widget_ui import BitunixAPIWidgetUI
from .bitunix_api_widget_events import BitunixAPIWidgetEvents
from .bitunix_api_widget_logic import BitunixAPIWidgetLogic

__all__ = [
    "BitunixTradingWidget",
    "BitunixTradingMixin",
    "BotTab",
    "BacktestTab",
    "BitunixAPIWidgetUI",
    "BitunixAPIWidgetEvents",
    "BitunixAPIWidgetLogic",
]
