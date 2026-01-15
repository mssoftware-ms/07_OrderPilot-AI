"""Trade Logger Summary - Daily Summary Statistics.

Refactored from 735 LOC monolith using composition pattern.

Module 4/4 of trade_logger.py split.

Contains:
- get_daily_summary(): Erstellt Tages-Zusammenfassung mit Statistiken
- cleanup_old_logs(): Löscht alte Logs
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TradeLoggerSummary:
    """Helper für Daily Summary und Log Cleanup."""

    def __init__(self, parent):
        """
        Args:
            parent: TradeLogger Instanz
        """
        self.parent = parent

    def get_daily_summary(self, date: datetime | None = None) -> dict:
        """
        Erstellt Zusammenfassung für einen Tag.

        Args:
            date: Datum (default: heute)

        Returns:
            Dictionary mit Tages-Statistiken
        """
        if date is None:
            date = datetime.now(timezone.utc)

        day_str = date.strftime("%Y-%m-%d")
        day_dir = self.parent.log_directory / day_str

        if not day_dir.exists():
            return {
                "date": day_str,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "breakeven": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "max_win": 0.0,
                "max_loss": 0.0,
            }

        trades = []
        for json_file in day_dir.glob("trade_*.json"):
            with open(json_file, encoding="utf-8") as f:
                trades.append(json.load(f))

        if not trades:
            return {
                "date": day_str,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "breakeven": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "max_win": 0.0,
                "max_loss": 0.0,
            }

        wins = sum(1 for t in trades if t.get("outcome") == "WIN")
        losses = sum(1 for t in trades if t.get("outcome") == "LOSS")
        breakeven = sum(1 for t in trades if t.get("outcome") == "BREAKEVEN")

        pnls = [float(t.get("net_pnl", 0) or 0) for t in trades]

        return {
            "date": day_str,
            "total_trades": len(trades),
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "win_rate": round(wins / len(trades) * 100, 1) if trades else 0.0,
            "total_pnl": round(sum(pnls), 2),
            "avg_pnl": round(sum(pnls) / len(pnls), 2) if pnls else 0.0,
            "max_win": round(max(pnls), 2) if pnls else 0.0,
            "max_loss": round(min(pnls), 2) if pnls else 0.0,
        }

    def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """
        Löscht Logs älter als retention_days.

        Args:
            retention_days: Anzahl Tage die Logs behalten werden

        Returns:
            Anzahl gelöschter Dateien
        """
        if retention_days <= 0:
            return 0

        cutoff = datetime.now(timezone.utc).date()
        deleted = 0

        for day_dir in self.parent.log_directory.iterdir():
            if not day_dir.is_dir():
                continue

            try:
                dir_date = datetime.strptime(day_dir.name, "%Y-%m-%d").date()
                age_days = (cutoff - dir_date).days

                if age_days > retention_days:
                    # Lösche alle Dateien im Verzeichnis
                    for file in day_dir.iterdir():
                        file.unlink()
                        deleted += 1
                    day_dir.rmdir()
                    logger.info(f"Deleted old log directory: {day_dir}")

            except ValueError:
                # Kein gültiges Datums-Verzeichnis, ignorieren
                continue

        return deleted
