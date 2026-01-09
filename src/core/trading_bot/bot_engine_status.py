"""Bot Engine Status - Current Status and Properties.

Refactored from bot_engine.py.

Contains:
- get_current_status: Return full bot status as dict
- Properties: state, is_running, has_position, statistics
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .bot_types import BotState, BotStatistics

if TYPE_CHECKING:
    from .bot_engine import TradingBotEngine


class BotEngineStatus:
    """Helper for status queries."""

    def __init__(self, parent: "TradingBotEngine"):
        self.parent = parent

    # === Properties ===

    @property
    def state(self) -> BotState:
        """Aktueller Bot-Zustand."""
        return self.parent._state

    @property
    def is_running(self) -> bool:
        """Bot läuft?"""
        return self.parent._running

    @property
    def has_position(self) -> bool:
        """Position offen?"""
        return self.parent.position_monitor.has_position

    @property
    def statistics(self) -> BotStatistics:
        """Aktuelle Statistiken."""
        return self.parent._stats

    # === Status Dict ===

    def get_current_status(self) -> dict:
        """Gibt aktuellen Bot-Status zurück."""
        return {
            "state": self.parent._state.value,
            "running": self.parent._running,
            "has_position": self.has_position,
            "position": self.parent.position_monitor.get_position_status(),
            "last_signal": {
                "direction": self.parent._last_signal.direction.value,
                "confluence": self.parent._last_signal.confluence_score,
                "strength": self.parent._last_signal.strength.value,
            }
            if self.parent._last_signal
            else None,
            "last_analysis": self.parent._last_analysis_time.isoformat()
            if self.parent._last_analysis_time
            else None,
            "statistics": self.parent._stats.to_dict(),
            "last_error": self.parent._last_error,
        }
