"""Bot Engine Persistence - Position Save/Load.

Refactored from bot_engine.py.

Contains:
- save_position: Save active position to JSON file
- load_position: Load saved position from JSON file
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .bot_types import BotState

if TYPE_CHECKING:
    from .bot_engine import TradingBotEngine

logger = logging.getLogger(__name__)

_POSITION_FILE = Path("config/trading_bot/active_position.json")


class BotEnginePersistence:
    """Helper for position persistence."""

    def __init__(self, parent: "TradingBotEngine"):
        self.parent = parent

    def save_position(self) -> bool:
        """
        Speichert aktive Position in Datei.

        Wird beim Beenden aufgerufen um Position zu erhalten.

        Returns:
            True wenn erfolgreich gespeichert
        """
        try:
            _POSITION_FILE.parent.mkdir(parents=True, exist_ok=True)

            if self.parent.position_monitor.has_position:
                position = self.parent.position_monitor.position
                data = {
                    "position": position.to_dict(),
                    "bot_state": self.parent._state.value,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                _POSITION_FILE.write_text(json.dumps(data, indent=2))
                logger.info(f"Position saved: {position.symbol} {position.side}")
                self.parent._callbacks._log(f"💾 Position gespeichert: {position.symbol}")
                return True
            else:
                # Keine Position - Datei löschen falls vorhanden
                if _POSITION_FILE.exists():
                    _POSITION_FILE.unlink()
                    logger.debug("No position to save, removed old file")
                return True

        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            return False

    def load_position(self) -> bool:
        """
        Lädt gespeicherte Position aus Datei.

        Wird beim Start aufgerufen um Position wiederherzustellen.

        Returns:
            True wenn Position geladen wurde
        """
        try:
            if not _POSITION_FILE.exists():
                logger.debug("No saved position file found")
                return False

            data = json.loads(_POSITION_FILE.read_text())
            position_data = data.get("position")

            if not position_data:
                logger.debug("Saved position file is empty")
                return False

            # Position wiederherstellen
            position = self.parent.position_monitor.restore_position(position_data)

            if position:
                self.parent._callbacks._set_state(BotState.IN_POSITION)
                self.parent._callbacks._log(
                    f"📂 Position wiederhergestellt: {position.symbol} {position.side} "
                    f"@ {position.entry_price}"
                )

                # UI Callback triggern
                if self.parent._on_position_opened:
                    self.parent._on_position_opened(position)

                # Position-Datei nach erfolgreichem Laden löschen
                # (wird beim nächsten Save neu erstellt)
                _POSITION_FILE.unlink()
                logger.info(
                    f"Position restored from file: {position.symbol} {position.side}, "
                    f"Entry: {position.entry_price}, SL: {position.stop_loss}, TP: {position.take_profit}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to load position: {e}")
            return False
