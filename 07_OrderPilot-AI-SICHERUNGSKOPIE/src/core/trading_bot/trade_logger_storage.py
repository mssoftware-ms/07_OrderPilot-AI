"""Trade Logger Storage - Persistence (JSON/Markdown).

Refactored from 735 LOC monolith using composition pattern.

Module 3/4 of trade_logger.py split.

Contains:
- save_trade_log(): Speichert Trade-Log auf Disk (JSON + Markdown)
- update_trade_log(): Aktualisiert existierenden Trade-Log
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.core.trading_bot.trade_logger_entry import TradeLogEntry

logger = logging.getLogger(__name__)


class TradeLoggerStorage:
    """Helper für Trade-Log Storage (JSON/Markdown Persistence)."""

    def __init__(self, parent):
        """
        Args:
            parent: TradeLogger Instanz
        """
        self.parent = parent

    def save_trade_log(self, trade_log: TradeLogEntry) -> Path:
        """
        Speichert Trade-Log auf Disk.

        Args:
            trade_log: Zu speichernder Log-Eintrag

        Returns:
            Path: Pfad zur gespeicherten Datei
        """
        day_dir = self.parent._get_day_directory()

        # Berechne finale Werte
        trade_log.calculate_pnl()
        trade_log.calculate_duration()

        # JSON speichern
        if self.parent.log_format in ("json", "both"):
            json_path = day_dir / f"{trade_log.trade_id}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(trade_log.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved JSON log: {json_path}")

        # Markdown speichern
        if self.parent.log_format in ("markdown", "both"):
            md_path = day_dir / f"{trade_log.trade_id}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(trade_log.to_markdown())
            logger.info(f"Saved Markdown log: {md_path}")

        return day_dir / trade_log.trade_id

    def update_trade_log(self, trade_log: TradeLogEntry) -> None:
        """
        Aktualisiert existierenden Trade-Log.

        Nützlich für Trailing-Stop Updates während Trade läuft.
        """
        self.save_trade_log(trade_log)
