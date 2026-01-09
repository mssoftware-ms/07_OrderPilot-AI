"""Bot Engine Callbacks - State Changes and Logging.

Refactored from bot_engine.py.

Contains:
- _set_state: Set new state and trigger callback
- _log: Log message and trigger callback
- 7 callback setters (state, signal, position opened/closed, error, log)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable

from .bot_types import BotState
from .position_monitor import MonitoredPosition
from .signal_generator import TradeSignal
from .trade_logger import TradeLogEntry

if TYPE_CHECKING:
    from .bot_engine import TradingBotEngine

logger = logging.getLogger(__name__)


class BotEngineCallbacks:
    """Helper for callback management."""

    def __init__(self, parent: "TradingBotEngine"):
        self.parent = parent

    def _set_state(self, new_state: BotState) -> None:
        """Setzt neuen Zustand und triggert Callback."""
        old_state = self.parent._state
        self.parent._state = new_state
        self._log(f"State: {old_state.value} → {new_state.value}")

        if self.parent._on_state_changed:
            self.parent._on_state_changed(new_state)

    def _log(self, message: str) -> None:
        """Loggt Nachricht und triggert Callback."""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        logger.info(f"Bot: {message}")

        if self.parent._on_log:
            self.parent._on_log(full_message)

    # === Callback Setters ===

    def set_state_callback(self, callback: Callable[[BotState], None]) -> None:
        """Setzt Callback für State-Änderungen."""
        self.parent._on_state_changed = callback

    def set_signal_callback(self, callback: Callable[[TradeSignal], None]) -> None:
        """Setzt Callback für neue Signale."""
        self.parent._on_signal_generated = callback

    def set_position_opened_callback(
        self, callback: Callable[[MonitoredPosition], None]
    ) -> None:
        """Setzt Callback für Position-Öffnung."""
        self.parent._on_position_opened = callback

    def set_position_closed_callback(
        self, callback: Callable[[TradeLogEntry], None]
    ) -> None:
        """Setzt Callback für Position-Schließung."""
        self.parent._on_position_closed = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Setzt Callback für Fehler."""
        self.parent._on_error = callback

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """Setzt Callback für Log-Nachrichten."""
        self.parent._on_log = callback
