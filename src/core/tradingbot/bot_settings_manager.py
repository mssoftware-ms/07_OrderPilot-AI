"""Bot Settings Manager - Persists bot settings per symbol.

Saves and loads bot configuration settings for each trading symbol,
allowing users to have different settings for different instruments.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default settings file location
SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "config" / "bot_settings.json"


class BotSettingsManager:
    """Manages persistent bot settings per symbol."""

    def __init__(self, settings_file: Path | None = None):
        """Initialize settings manager.

        Args:
            settings_file: Path to settings file (default: config/bot_settings.json)
        """
        self._settings_file = settings_file or SETTINGS_FILE
        self._settings: dict[str, dict[str, Any]] = {}
        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from file."""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
                logger.info(f"Loaded bot settings for {len(self._settings)} symbols")
            else:
                self._settings = {}
                logger.info("No existing bot settings file, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load bot settings: {e}")
            self._settings = {}

    def _save_settings(self) -> None:
        """Save settings to file."""
        try:
            # Ensure directory exists
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
            logger.debug(f"Saved bot settings to {self._settings_file}")
        except Exception as e:
            logger.error(f"Failed to save bot settings: {e}")

    def get_settings(self, symbol: str) -> dict[str, Any]:
        """Get settings for a symbol.

        Args:
            symbol: Trading symbol (e.g., "BTC/USD", "AAPL")

        Returns:
            Settings dict or empty dict if no settings saved
        """
        # Normalize symbol
        symbol_key = symbol.upper().replace("/", "_")
        return self._settings.get(symbol_key, {})

    def save_settings(self, symbol: str, settings: dict[str, Any]) -> None:
        """Save settings for a symbol.

        Args:
            symbol: Trading symbol
            settings: Settings dict to save
        """
        # Normalize symbol
        symbol_key = symbol.upper().replace("/", "_")
        self._settings[symbol_key] = settings
        self._save_settings()
        logger.info(f"Saved bot settings for {symbol}")

    def get_all_symbols(self) -> list[str]:
        """Get list of all symbols with saved settings.

        Returns:
            List of symbol keys
        """
        return list(self._settings.keys())

    def delete_settings(self, symbol: str) -> bool:
        """Delete settings for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            True if deleted, False if not found
        """
        symbol_key = symbol.upper().replace("/", "_")
        if symbol_key in self._settings:
            del self._settings[symbol_key]
            self._save_settings()
            logger.info(f"Deleted bot settings for {symbol}")
            return True
        return False


# Singleton instance
_settings_manager: BotSettingsManager | None = None


def get_bot_settings_manager() -> BotSettingsManager:
    """Get the singleton settings manager instance.

    Returns:
        BotSettingsManager instance
    """
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = BotSettingsManager()
    return _settings_manager
