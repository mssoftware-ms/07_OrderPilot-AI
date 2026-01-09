"""Trade Logger - Detailliertes Logging-System für jeden Trade (Refactored).

Refactored from 735 LOC monolith using composition pattern.

Main Orchestrator (Module 5/5).

Delegates to 4 specialized helper modules:
- TradeLoggerState: Enums and simple dataclasses
- TradeLoggerEntry: TradeLogEntry dataclass with business logic
- TradeLoggerStorage: JSON/Markdown persistence
- TradeLoggerSummary: Daily summary statistics

Provides:
- TradeLogger: Main orchestration class with delegation
- Re-exports all state types for backward compatibility
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from src.core.trading_bot.trade_logger_entry import TradeLogEntry
from src.core.trading_bot.trade_logger_state import (
    ExitReason,
    IndicatorSnapshot,
    MarketContext,
    SignalDetails,
    TradeOutcome,
    TrailingStopHistory,
)
from src.core.trading_bot.trade_logger_storage import TradeLoggerStorage
from src.core.trading_bot.trade_logger_summary import TradeLoggerSummary

logger = logging.getLogger(__name__)


class TradeLogger:
    """
    Manager für Trade-Logging.

    Erstellt und verwaltet Trade-Logs für jeden einzelnen Trade.
    """

    def __init__(
        self,
        log_directory: Path | str = "logs/trades",
        log_format: str = "both",
    ):
        self.log_directory = Path(log_directory)
        self.log_format = log_format
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Täglicher Unterordner
        self._current_day_dir: Path | None = None
        self._trade_counter = 0

        # Instantiate helper modules (composition pattern)
        self._storage = TradeLoggerStorage(parent=self)
        self._summary = TradeLoggerSummary(parent=self)

        logger.info(f"TradeLogger initialized. Directory: {self.log_directory}")

    def _get_day_directory(self) -> Path:
        """Gibt Verzeichnis für aktuellen Tag zurück."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        day_dir = self.log_directory / today

        if self._current_day_dir != day_dir:
            day_dir.mkdir(parents=True, exist_ok=True)
            self._current_day_dir = day_dir
            self._trade_counter = self._count_existing_trades(day_dir)

        return day_dir

    def _count_existing_trades(self, directory: Path) -> int:
        """Zählt existierende Trades im Verzeichnis."""
        json_files = list(directory.glob("trade_*.json"))
        return len(json_files)

    def create_trade_log(self, symbol: str, bot_config: dict | None = None) -> TradeLogEntry:
        """
        Erstellt einen neuen Trade-Log-Eintrag.

        Returns:
            TradeLogEntry: Neuer Log-Eintrag (noch ohne Entry-Daten)
        """
        self._trade_counter += 1
        now = datetime.now(timezone.utc)

        trade_id = f"trade_{now.strftime('%Y%m%d_%H%M%S')}_{self._trade_counter:03d}"

        entry = TradeLogEntry(
            trade_id=trade_id,
            symbol=symbol,
            created_at=now,
            bot_config_snapshot=bot_config or {},
        )

        logger.info(f"Created new trade log: {trade_id}")
        return entry

    def save_trade_log(self, trade_log: TradeLogEntry) -> Path:
        """
        Speichert Trade-Log auf Disk.

        Delegates to TradeLoggerStorage.save_trade_log().

        Args:
            trade_log: Zu speichernder Log-Eintrag

        Returns:
            Path: Pfad zur gespeicherten Datei
        """
        return self._storage.save_trade_log(trade_log)

    def update_trade_log(self, trade_log: TradeLogEntry) -> None:
        """
        Aktualisiert existierenden Trade-Log.

        Delegates to TradeLoggerStorage.update_trade_log().

        Nützlich für Trailing-Stop Updates während Trade läuft.
        """
        self._storage.update_trade_log(trade_log)

    def get_daily_summary(self, date: datetime | None = None) -> dict:
        """
        Erstellt Zusammenfassung für einen Tag.

        Delegates to TradeLoggerSummary.get_daily_summary().

        Args:
            date: Datum (default: heute)

        Returns:
            Dictionary mit Tages-Statistiken
        """
        return self._summary.get_daily_summary(date)

    def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """
        Löscht Logs älter als retention_days.

        Delegates to TradeLoggerSummary.cleanup_old_logs().

        Args:
            retention_days: Anzahl Tage die Logs behalten werden

        Returns:
            Anzahl gelöschter Dateien
        """
        return self._summary.cleanup_old_logs(retention_days)


# Re-export für backward compatibility
__all__ = [
    "TradeLogger",
    "TradeLogEntry",
    "TradeOutcome",
    "ExitReason",
    "IndicatorSnapshot",
    "MarketContext",
    "SignalDetails",
    "TrailingStopHistory",
]
