"""TradingMixinBase - Base class for trading UI mixins.

Provides shared utility methods used by ChartChatMixin and BitunixTradingMixin
to eliminate code duplication.

Extracted from:
- src/chart_chat/mixin.py (lines 203-215)
- src/ui/widgets/bitunix_trading/bitunix_trading_mixin.py (lines 222-234)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TradingMixinBase:
    """Base class for trading-related UI mixins.

    Provides shared functionality:
    - _get_parent_app(): Access to parent TradingApplication
    """

    def _get_parent_app(self) -> Any | None:
        """Get the parent TradingApplication.

        Returns:
            TradingApplication instance or None
        """
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app and hasattr(app, "main_window"):
            return app.main_window

        return None
