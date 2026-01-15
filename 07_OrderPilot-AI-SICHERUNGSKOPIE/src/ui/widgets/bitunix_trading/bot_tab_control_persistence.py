"""Bot Tab Control Persistence - Settings and Position Persistence.

Refactored from 1,160 LOC monolith using composition pattern.

Module 5/6 of bot_tab_control.py split.

Contains:
- Settings management (_get_current_config, apply_config, _save_settings, _load_settings)
- Position persistence (cleanup, _save_position_to_file, restore_saved_position)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.trading_bot.bot_config import BotConfig

logger = logging.getLogger(__name__)

# Settings File Path
BOT_SETTINGS_FILE = Path("config/trading_bot/bot_settings.json")


class BotTabControlPersistence:
    """Helper für Settings und Position Persistence."""

    def __init__(self, parent):
        """
        Args:
            parent: BotTabControl Instanz
        """
        self.parent = parent

    def _get_current_config(self) -> "BotConfig":
        """Gibt aktuelle Bot-Konfiguration zurück (lädt aus Datei wenn vorhanden)."""
        return self._load_settings()

    def apply_config(self, config: "BotConfig") -> None:
        """Wendet neue Konfiguration an und speichert sie."""
        self._save_settings(config)
        # Neue Pipeline: Engine-Configs sofort aktualisieren
        self.parent._engine_init_helper.update_engine_configs()

    def _save_settings(self, config: "BotConfig") -> None:
        """Speichert Bot-Einstellungen in JSON-Datei."""
        try:
            # Stelle sicher dass Verzeichnis existiert
            BOT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Config zu Dictionary konvertieren
            settings = config.to_dict()

            with open(BOT_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Bot-Einstellungen gespeichert: {BOT_SETTINGS_FILE}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}")

    def _load_settings(self) -> "BotConfig":
        """Lädt Bot-Einstellungen aus JSON-Datei."""
        try:
            from src.core.trading_bot.bot_config import BotConfig

            if BOT_SETTINGS_FILE.exists():
                with open(BOT_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                logger.info(f"Bot-Einstellungen geladen: {BOT_SETTINGS_FILE}")
                return BotConfig.from_dict(settings)
        except Exception as e:
            logger.warning(f"Fehler beim Laden der Einstellungen: {e}")

        # Fallback: Default-Konfiguration
        from src.core.trading_bot.bot_config import BotConfig

        return BotConfig(symbol="BTCUSDT")

    def cleanup(self) -> None:
        """Cleanup bei Widget-Zerstörung (App schließt)."""
        self.parent.parent.update_timer.stop()
        # Neue Pipeline: Position direkt speichern
        if self.parent.parent._current_position:
            self._save_position_to_file()
            logger.info("BotTab cleanup: Position saved for next start")
        # Bot-State zurücksetzen
        self.parent.parent._bot_running = False
        logger.debug("BotTab cleanup completed")

    def _save_position_to_file(self) -> bool:
        """Speichert aktive Position in Datei (für Wiederherstellung beim Neustart)."""
        position_file = Path("config/trading_bot/active_position.json")
        try:
            position_file.parent.mkdir(parents=True, exist_ok=True)

            if self.parent.parent._current_position:
                # entry_time zu ISO-String konvertieren
                pos_data = self.parent.parent._current_position.copy()
                if "entry_time" in pos_data and hasattr(pos_data["entry_time"], "isoformat"):
                    pos_data["entry_time"] = pos_data["entry_time"].isoformat()

                data = {
                    "position": pos_data,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                position_file.write_text(json.dumps(data, indent=2))
                logger.info(f"Position saved: {pos_data.get('symbol')} {pos_data.get('side')}")
                return True
            else:
                # Keine Position - Datei löschen falls vorhanden
                if position_file.exists():
                    position_file.unlink()
                    logger.debug("No position to save, removed old file")
                return True

        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            return False

    def restore_saved_position(self) -> None:
        """Issue #20: Stellt gespeicherte Position beim Start wieder her."""
        position_file = Path("config/trading_bot/active_position.json")

        try:
            if not position_file.exists():
                logger.debug("BotTab: No saved position file found")
                return

            data = json.loads(position_file.read_text())
            position_data = data.get("position")

            if not position_data:
                logger.debug("BotTab: Saved position file is empty")
                return

            # Position wiederherstellen
            self.parent.parent._current_position = position_data

            # entry_time von ISO-String zurück konvertieren
            if "entry_time" in self.parent.parent._current_position:
                entry_time_str = self.parent.parent._current_position["entry_time"]
                if isinstance(entry_time_str, str):
                    self.parent.parent._current_position["entry_time"] = datetime.fromisoformat(entry_time_str)

            # UI-Variablen setzen
            self.parent.parent._position_entry_price = position_data.get("entry_price", 0)
            self.parent.parent._position_side = position_data.get("side", "long")
            self.parent.parent._position_quantity = position_data.get("quantity", 0)
            self.parent.parent._position_stop_loss = position_data.get("stop_loss")
            self.parent.parent._position_take_profit = position_data.get("take_profit")

            self.parent._log("📂 Gespeicherte Position wiederhergestellt")
            logger.info(
                f"BotTab: Restored saved position: {position_data.get('symbol')} "
                f"{position_data.get('side')} @ {position_data.get('entry_price')}"
            )

            # SL/TP Bar anzeigen
            if self.parent.parent._position_entry_price:
                self.parent.parent.sltp_container.setVisible(True)
                self.parent._ui_helper._update_sltp_bar(self.parent.parent._position_entry_price)

            # Position-Datei nach erfolgreichem Laden löschen (wird beim nächsten Save neu erstellt)
            position_file.unlink()
            logger.debug("BotTab: Removed position file after successful restore")

        except Exception as e:
            logger.warning(f"BotTab: Failed to restore saved position: {e}")
            self.parent._log(f"⚠️ Position konnte nicht wiederhergestellt werden: {e}")
