"""
Bot Types - State Machine and Statistics

Core types for Trading Bot Engine:
- BotState enum (state machine states)
- BotStatistics dataclass (daily trade statistics)

Module 1/4 of bot_engine.py split (Lines 58-111)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class BotState(str, Enum):
    """Bot-Zustände."""

    IDLE = "IDLE"  # Bot gestoppt
    STARTING = "STARTING"  # Bot startet
    ANALYZING = "ANALYZING"  # Markt wird analysiert, keine Position
    WAITING_SIGNAL = "WAITING_SIGNAL"  # Warte auf Signal
    VALIDATING = "VALIDATING"  # Signal wird validiert (AI)
    OPENING_POSITION = "OPENING_POSITION"  # Order wird platziert
    IN_POSITION = "IN_POSITION"  # Position offen, überwache
    CLOSING_POSITION = "CLOSING_POSITION"  # Position wird geschlossen
    STOPPING = "STOPPING"  # Bot stoppt
    ERROR = "ERROR"  # Fehler-Zustand


@dataclass
class BotStatistics:
    """Tagesstatistiken des Bots."""

    date: str
    trades_total: int = 0
    trades_won: int = 0
    trades_lost: int = 0
    trades_breakeven: int = 0
    total_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    max_drawdown: Decimal = field(default_factory=lambda: Decimal("0"))
    peak_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    signals_generated: int = 0
    signals_rejected_confluence: int = 0
    signals_rejected_ai: int = 0

    @property
    def win_rate(self) -> float:
        """Gewinnrate in %."""
        if self.trades_total == 0:
            return 0.0
        return round(self.trades_won / self.trades_total * 100, 1)

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "date": self.date,
            "trades_total": self.trades_total,
            "trades_won": self.trades_won,
            "trades_lost": self.trades_lost,
            "trades_breakeven": self.trades_breakeven,
            "win_rate": self.win_rate,
            "total_pnl": str(self.total_pnl),
            "max_drawdown": str(self.max_drawdown),
            "signals_generated": self.signals_generated,
            "signals_rejected_confluence": self.signals_rejected_confluence,
            "signals_rejected_ai": self.signals_rejected_ai,
        }
