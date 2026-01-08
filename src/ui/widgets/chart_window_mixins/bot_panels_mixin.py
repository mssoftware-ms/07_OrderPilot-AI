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
from .bot_derivative_mixin import BotDerivativeMixin
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
    BotDerivativeMixin,
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

        # Initialize derivative state
        self._init_derivative_state()

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
        # Connect tick_price_updated signal for real-time P&L updates
        QTimer.singleShot(500, self._connect_tick_price_signal)

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

    def _connect_tick_price_signal(self) -> None:
        """Connect the chart's tick_price_updated signal for real-time P&L updates."""
        if not hasattr(self, 'chart_widget'):
            logger.warning("Cannot connect tick_price_updated - no chart_widget")
            return

        if hasattr(self.chart_widget, 'tick_price_updated'):
            try:
                self.chart_widget.tick_price_updated.connect(self._on_tick_price_updated)
                logger.info("✅ Connected chart tick_price_updated signal for real-time P&L")
                # Also add to KI log for visibility
                if hasattr(self, '_add_ki_log_entry'):
                    self._add_ki_log_entry("TICK", "tick_price_updated Signal verbunden")
            except Exception as e:
                logger.error(f"Failed to connect tick_price_updated signal: {e}")
        else:
            logger.warning("Chart widget has no tick_price_updated signal")

    def _on_tick_price_updated(self, current_price: float) -> None:
        """Handle tick price update - update P&L displays in real-time.

        Args:
            current_price: Current price from tick
        """
        if current_price <= 0:
            return
        selection_active = self._is_signals_selection_active()
        self._log_tick_if_needed(current_price)

        # Check for active positions
        sig = self._find_active_signal()
        if sig:
            self._update_signal_pnl(sig, current_price)
            if not selection_active:
                self._update_current_position_display(sig, current_price)
            if hasattr(self, '_check_tr_activation'):
                self._check_tr_activation(sig, current_price)

        if selection_active and hasattr(self, "_update_current_position_from_selection"):
            self._update_current_position_from_selection()

        # Update signals table immediately (every tick)
        if sig:
            self._update_signals_table()
            if hasattr(self, 'signals_table') and hasattr(self.signals_table, 'viewport'):
                self.signals_table.viewport().update()

    def _is_signals_selection_active(self) -> bool:
        if hasattr(self, "_has_signals_table_selection"):
            try:
                return bool(self._has_signals_table_selection())
            except Exception:
                return False
        return False

    def _log_tick_if_needed(self, current_price: float) -> None:
        if not hasattr(self, '_tick_count'):
            self._tick_count = 0
        self._tick_count += 1
        if self._tick_count % 50 == 1:
            logger.debug(f"📊 Tick #{self._tick_count}: {current_price:.2f}")
            if hasattr(self, '_add_ki_log_entry') and self._tick_count <= 101:
                self._add_ki_log_entry("TICK", f"#{self._tick_count} Kurs: {current_price:.2f}")

    def _find_active_signal(self) -> dict | None:
        for sig in self._signal_history:
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                return sig
        return None

    def _update_signal_pnl(self, sig: dict, current_price: float) -> None:
        entry_price = sig.get("price", 0)
        invested = sig.get("invested", 0)
        side = sig.get("side", "long")

        if entry_price <= 0:
            return

        sig["current_price"] = current_price
        if side.lower() == "long":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        pnl_currency = invested * (pnl_pct / 100) if invested > 0 else 0
        sig["pnl_currency"] = pnl_currency
        sig["pnl_percent"] = pnl_pct

    def _update_current_position_display(self, sig: dict, current_price: float) -> None:
        entry_price = sig.get("price", 0)
        invested = sig.get("invested", 0)
        side = sig.get("side", "long")
        pnl_pct = sig.get("pnl_percent", 0)
        pnl_currency = sig.get("pnl_currency", 0)
        stop_price = sig.get("trailing_stop_price", sig.get("stop_price", 0))
        take_profit = sig.get("take_profit_price", sig.get("tp_price", 0))

        # Update SL/TP Progress Bar
        if hasattr(self, 'sltp_progress_bar') and entry_price > 0:
            self.sltp_progress_bar.set_prices(
                entry=entry_price,
                sl=stop_price,
                tp=take_profit,
                current=current_price,
                side=side
            )

        if hasattr(self, 'position_side_label'):
            side_upper = side.upper()
            self.position_side_label.setText(side_upper)
            color = "#26a69a" if side_upper == "LONG" else "#ef5350"
            self.position_side_label.setStyleSheet(f"font-weight: bold; color: {color};")

        if hasattr(self, 'position_entry_label') and entry_price > 0:
            self.position_entry_label.setText(f"{entry_price:.4f}")

        quantity = sig.get("quantity", 0)
        if hasattr(self, 'position_size_label'):
            self.position_size_label.setText(f"{quantity:.4f}" if quantity > 0 else "-")

        if hasattr(self, 'position_invested_label') and invested > 0:
            self.position_invested_label.setText(f"{invested:.0f}")

        stop_price = sig.get("trailing_stop_price", sig.get("stop_price", 0))
        if hasattr(self, 'position_stop_label') and stop_price > 0:
            self.position_stop_label.setText(f"{stop_price:.4f}")

        if hasattr(self, 'position_current_label'):
            self.position_current_label.setText(f"{current_price:.4f}")

        if hasattr(self, 'position_pnl_label'):
            color = "#26a69a" if pnl_pct >= 0 else "#ef5350"
            sign = "+" if pnl_pct >= 0 else ""
            self.position_pnl_label.setText(f"{sign}{pnl_pct:.2f}% ({sign}{pnl_currency:.2f} EUR)")
            self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")

        score = sig.get("score", 0)
        if hasattr(self, 'position_score_label') and score > 0:
            self.position_score_label.setText(f"{score * 100:.0f}")

        tr_price = sig.get("trailing_stop_price", 0)
        tr_active = sig.get("tr_active", False)
        if hasattr(self, 'position_tr_price_label') and tr_price > 0:
            if tr_active:
                self.position_tr_price_label.setText(f"{tr_price:.2f}")
                self.position_tr_price_label.setStyleSheet("color: #ff9800;")
            else:
                self.position_tr_price_label.setText(f"{tr_price:.2f} (inaktiv)")
                self.position_tr_price_label.setStyleSheet("color: #888888;")

        self._update_derivative_display(sig, current_price)

    def _update_derivative_display(self, sig: dict, current_price: float) -> None:
        deriv = sig.get("derivative")
        if not deriv:
            return
        if hasattr(self, 'deriv_wkn_label'):
            self.deriv_wkn_label.setText(deriv.get("wkn", "-"))
        if hasattr(self, 'deriv_leverage_label'):
            lev = deriv.get("leverage", 0)
            self.deriv_leverage_label.setText(f"{lev:.1f}x" if lev else "-")
        if hasattr(self, 'deriv_spread_label'):
            spread = deriv.get("spread_pct", 0)
            self.deriv_spread_label.setText(f"{spread:.2f}%" if spread else "-")
        if hasattr(self, 'deriv_ask_label'):
            ask = deriv.get("ask", 0)
            self.deriv_ask_label.setText(f"{ask:.2f}" if ask else "-")

        if hasattr(self, '_calculate_derivative_pnl_for_signal'):
            deriv_pnl = self._calculate_derivative_pnl_for_signal(sig, current_price)
            if deriv_pnl and hasattr(self, 'deriv_pnl_label'):
                d_pnl_eur = deriv_pnl.get("pnl_eur", 0)
                d_pnl_pct = deriv_pnl.get("pnl_pct", 0)
                d_color = "#26a69a" if d_pnl_eur >= 0 else "#ef5350"
                d_sign = "+" if d_pnl_eur >= 0 else ""
                self.deriv_pnl_label.setText(
                    f"{d_sign}{d_pnl_pct:.2f}% ({d_sign}{d_pnl_eur:.2f} €)"
                )
                self.deriv_pnl_label.setStyleSheet(f"font-weight: bold; color: {d_color};")
