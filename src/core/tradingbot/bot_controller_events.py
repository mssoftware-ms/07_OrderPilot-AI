"""Bot Controller Event Handling.

Handles event logging and lifecycle operations for the trading bot controller.
Extracted from bot_controller.py as part of refactoring to maintain <500 LOC per file.

This module contains:
- Activity logging (_log_activity)
- Lifecycle methods (start, stop, pause, resume, reset)
- Warmup functionality (warmup_from_history)
- KI mode setting (set_ki_mode)
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from .config import KIMode

logger = logging.getLogger(__name__)


class BotControllerEvents:
    """Event handling and lifecycle management for bot controller.

    Handles activity logging, lifecycle control, and warmup functionality.
    Base class for BotController - inherited to provide event management.

    Methods:
        _log_activity: Log activity to logger and UI callback
        start: Start the bot
        stop: Stop the bot
        pause: Pause the bot
        resume: Resume the bot
        reset: Reset bot to initial state
        warmup_from_history: Pre-fill bar buffer with historical data
        set_ki_mode: Set KI mode dynamically
    """

    # ==================== Activity Logging ====================

    def _log_activity(self, log_type: str, message: str) -> None:
        """Log activity to both logger and UI callback.

        Args:
            log_type: Type of log entry (INFO, BAR, FEATURE, SIGNAL, etc.)
            message: Log message
        """
        logger.info(f"[{log_type}] {message}")
        if self._on_log:
            try:
                self._on_log(log_type, message)
            except Exception as e:
                logger.error(f"Log callback error: {e}")

    # ==================== Lifecycle ====================

    def start(self) -> None:
        """Start the bot.

        Note: Synchronous for easy UI integration. Async operations
        happen in on_bar() which should be awaited.
        """
        if self._running:
            logger.warning(f"Bot already running: {self.symbol}")
            return

        self._running = True
        self._run_id = str(uuid4())[:8]
        restrictions_status = "AUS (Paper)" if self.config.bot.disable_restrictions else "AN"
        self._log_activity(
            "START",
            f"Bot gestartet: {self.symbol} | Timeframe: {self.timeframe} | "
            f"KI-Mode: {self.config.bot.ki_mode.value} | Restriktionen: {restrictions_status} | "
            f"Run-ID: {self._run_id}"
        )

    def stop(self) -> None:
        """Stop the bot.

        Note: Synchronous for easy UI integration.
        """
        if not self._running:
            return

        self._running = False
        self._log_activity(
            "STOP",
            f"Bot gestoppt: {self.symbol} | Bars verarbeitet: {self._bar_count} | "
            f"Trades heute: {self._trades_today}"
        )

    def pause(self, reason: str = "manual") -> None:
        """Pause the bot."""
        self._state_machine.pause(reason)
        logger.info(f"Bot paused: {reason}")

    def resume(self) -> None:
        """Resume the bot."""
        self._state_machine.resume()
        logger.info("Bot resumed")

    def reset(self) -> None:
        """Reset bot to initial state."""
        self._state_machine.reset(clear_history=False)
        self._position = None
        self._current_signal = None
        self._trades_today = 0
        self._daily_pnl = 0.0
        self._consecutive_losses = 0
        logger.info(f"Bot reset: symbol={self.symbol}")

    def warmup_from_history(self, bars: list[dict]) -> int:
        """Pre-fill bar buffer with historical data for instant warmup.

        This allows the bot to skip the warmup period by using existing
        chart data instead of waiting for 60+ new bars.

        Args:
            bars: List of bar dicts with keys: timestamp, open, high, low, close, volume

        Returns:
            Number of bars loaded into buffer
        """
        if not bars:
            logger.warning("No bars provided for warmup")
            return 0

        # Clear existing buffer
        self._bar_buffer.clear()

        # Take last N bars (up to max buffer size)
        recent_bars = bars[-self._max_buffer_size:]

        for bar in recent_bars:
            self._bar_buffer.append({
                'timestamp': bar.get('timestamp', datetime.utcnow()),
                'open': bar.get('open', 0),
                'high': bar.get('high', 0),
                'low': bar.get('low', 0),
                'close': bar.get('close', 0),
                'volume': bar.get('volume', 0),
            })

        loaded_count = len(self._bar_buffer)
        min_bars = self._feature_engine.MIN_BARS

        if loaded_count >= min_bars:
            self._log_activity(
                "WARMUP",
                f"Warmup abgeschlossen: {loaded_count} Bars aus Chart-Historie geladen (min: {min_bars})"
            )
        else:
            self._log_activity(
                "WARMUP",
                f"Teilweise Warmup: {loaded_count}/{min_bars} Bars geladen"
            )

        logger.info(f"Warmup: loaded {loaded_count} bars from chart history")
        return loaded_count

    def set_ki_mode(self, mode: str) -> None:
        """Set KI mode dynamically.

        Args:
            mode: "NO_KI", "LOW_KI", or "FULL_KI" (case-insensitive)
        """
        try:
            # Convert uppercase UI values to lowercase enum values
            mode_lower = mode.lower()
            self.config.bot.ki_mode = KIMode(mode_lower)
            logger.info(f"KI mode changed to: {mode}")
        except ValueError:
            logger.warning(f"Invalid KI mode: {mode}")
