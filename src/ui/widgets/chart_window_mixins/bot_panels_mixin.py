"""Bot Panels Mixin for ChartWindow.

Provides additional tabs for tradingbot control and monitoring:
- Bot Control (Start/Stop, Settings)
- Daily Strategy Selection
- Signals & Trade Management
- KI Logs

This is the main coordinator that inherits from specialized sub-mixins:
- BotUIPanelsMixin: Tab creation (bot_ui_panels.py)
- BotEventHandlersMixin: Event handlers + settings (bot_event_handlers.py)
- BotCallbacksMixin: Bot controller callbacks (bot_callbacks.py)
- BotDisplayManagerMixin: Display updates (bot_display_manager.py)
- BotPositionPersistenceMixin: Position management (bot_position_persistence.py)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSettings, QTimer, pyqtSignal

# Import sub-mixins
from .bot_callbacks import BotCallbacksMixin
from .bot_display_manager import BotDisplayManagerMixin
from .bot_event_handlers import BotEventHandlersMixin
from .bot_position_persistence import BotPositionPersistenceMixin
from .bot_ui_panels import BotUIPanelsMixin

if TYPE_CHECKING:
    from src.core.tradingbot import BotController, FullBotConfig

logger = logging.getLogger(__name__)


class BotPanelsMixin(
    BotUIPanelsMixin,
    BotEventHandlersMixin,
    BotCallbacksMixin,
    BotDisplayManagerMixin,
    BotPositionPersistenceMixin,
):
    """Mixin providing bot control and monitoring panels.

    This class combines all bot-related functionality through multiple inheritance
    from specialized sub-mixins. Each sub-mixin handles a specific concern:

    - BotUIPanelsMixin: Creates the UI tabs and widgets
    - BotEventHandlersMixin: Handles UI events and settings persistence
    - BotCallbacksMixin: Manages bot controller lifecycle and callbacks
    - BotDisplayManagerMixin: Updates displays (status, tables, P&L)
    - BotPositionPersistenceMixin: Manages position persistence and chart integration

    Usage:
        class ChartWindow(QMainWindow, BotPanelsMixin, ...):
            def __init__(self):
                super().__init__()
                self._init_bot_panels()
                # Add tabs using:
                # - self._create_bot_control_tab()
                # - self._create_strategy_selection_tab()
                # - self._create_signals_tab()
                # - self._create_ki_logs_tab()
    """

    # Signals for bot events
    bot_started = pyqtSignal()
    bot_stopped = pyqtSignal()
    bot_config_changed = pyqtSignal(object)

    def _init_bot_panels(self) -> None:
        """Initialize bot panel state.

        Must be called during ChartWindow initialization to set up:
        - Bot controller reference
        - Update timer
        - Signal/trade history
        - Settings manager
        """
        self._bot_controller: BotController | None = None
        self._bot_update_timer: QTimer | None = None
        self._pnl_update_timer: QTimer | None = None
        self._ki_log_entries: list[dict] = []
        self._signal_history: list[dict] = []
        self._trade_history: list[dict] = []
        self._current_bot_symbol: str = ""
        self._bot_settings = QSettings("OrderPilot", "TradingApp")
        self._pending_position_restore: list[dict] | None = None

        # Initialize settings manager
        from src.core.tradingbot.bot_settings_manager import get_bot_settings_manager
        self._bot_settings_manager = get_bot_settings_manager()

        # Update symbol display and load settings (delayed to ensure UI is ready)
        QTimer.singleShot(100, self.update_bot_symbol)
        # Load signal history after UI is ready
        QTimer.singleShot(200, self._load_signal_history)
        # Connect chart line drag signal (delayed to ensure chart_widget exists)
        QTimer.singleShot(300, self._connect_chart_line_signals)
        # Connect candle_closed signal for bot bar feeding
        QTimer.singleShot(400, self._connect_candle_closed_signal)

        logger.info("Bot panels initialized")

    def _connect_candle_closed_signal(self) -> None:
        """Connect the chart's candle_closed signal to feed bars to the bot.

        This is critical for the trading bot to receive candle data when
        using tick-based streaming (Live button).
        """
        if not hasattr(self, 'chart_widget'):
            logger.warning("Cannot connect candle_closed - no chart_widget")
            return

        if hasattr(self.chart_widget, 'candle_closed'):
            try:
                self.chart_widget.candle_closed.connect(self._on_chart_candle_closed)
                logger.info("Connected chart candle_closed signal to bot")
            except Exception as e:
                logger.error(f"Failed to connect candle_closed signal: {e}")
        else:
            logger.warning("Chart widget has no candle_closed signal")
