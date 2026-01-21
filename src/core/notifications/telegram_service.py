"""
Telegram Notification Service

Verwendet requests um Telegram-Nachrichten zu senden.
Wird für Trade-Benachrichtigungen verwendet.

WICHTIG: Erfordert Bot-Token von @BotFather und Chat-ID!
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

# Pfad zur Settings-Datei
_SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "config" / "bot_settings.json"


# Reuse TradeNotification from whatsapp_service
from src.core.notifications.whatsapp_service import TradeNotification


class TelegramService:
    """Service zum Senden von Telegram-Nachrichten."""

    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._enabled = False
        self._requests_available = False
        self._on_status_callback: Callable[[str], None] | None = None
        self._on_error_callback: Callable[[str], None] | None = None

        # Check if requests is available
        try:
            import requests
            self._requests_available = True
            logger.info("TelegramService: requests verfügbar")
        except ImportError:
            logger.warning("TelegramService: requests nicht installiert - pip install requests")

        # Lade Bot-Token aus Systemvariablen (Windows)
        if not self._bot_token:
            env_token = os.environ.get("TELEGRAM_TOKEN", "")
            if env_token:
                self._bot_token = env_token
                logger.info("TelegramService: Bot-Token aus TELEGRAM_TOKEN Systemvariable geladen")

        # Lade gespeicherten Status
        self._load_settings()

    def _load_settings(self) -> None:
        """Lädt die gespeicherten Settings aus der Settings-Datei."""
        try:
            if _SETTINGS_FILE.exists():
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self._enabled = settings.get("telegram_notifications_enabled", False)

                    # Bot-Token nur aus Settings laden, wenn nicht bereits aus Systemvariable geladen
                    if not self._bot_token:
                        self._bot_token = settings.get("telegram_bot_token", "")

                    self._chat_id = settings.get("telegram_chat_id", "")
                    logger.info(f"TelegramService: Settings geladen - Enabled: {self._enabled}")
        except Exception as e:
            logger.warning(f"TelegramService: Fehler beim Laden der Settings: {e}")
            self._enabled = False

    def _save_settings(self) -> None:
        """Speichert die Settings in der Settings-Datei."""
        try:
            settings = {}
            if _SETTINGS_FILE.exists():
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)

            settings["telegram_notifications_enabled"] = self._enabled
            settings["telegram_bot_token"] = self._bot_token
            settings["telegram_chat_id"] = self._chat_id

            with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            logger.info(f"TelegramService: Settings gespeichert")
        except Exception as e:
            logger.error(f"TelegramService: Fehler beim Speichern der Settings: {e}")

    @property
    def bot_token(self) -> str:
        return self._bot_token

    @bot_token.setter
    def bot_token(self, value: str) -> None:
        self._bot_token = value.strip()
        logger.info(f"TelegramService: Bot-Token geändert")
        self._save_settings()

    @property
    def chat_id(self) -> str:
        return self._chat_id

    @chat_id.setter
    def chat_id(self, value: str) -> None:
        self._chat_id = value.strip()
        logger.info(f"TelegramService: Chat-ID geändert zu {value}")
        self._save_settings()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        logger.info(f"TelegramService: Benachrichtigungen {'aktiviert' if value else 'deaktiviert'}")
        self._save_settings()

    @property
    def is_available(self) -> bool:
        return self._requests_available

    @property
    def is_configured(self) -> bool:
        """Prüft ob Bot-Token und Chat-ID konfiguriert sind."""
        return bool(self._bot_token and self._chat_id)

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Setzt Callback für Status-Updates."""
        self._on_status_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Setzt Callback für Fehler."""
        self._on_error_callback = callback

    def _emit_status(self, message: str) -> None:
        """Emittiert Status-Update."""
        if self._on_status_callback:
            self._on_status_callback(message)

    def _emit_error(self, message: str) -> None:
        """Emittiert Fehler."""
        if self._on_error_callback:
            self._on_error_callback(message)

    def send_message(self, message: str, chat_id: str | None = None) -> bool:
        """
        Sendet eine Telegram-Nachricht.

        Args:
            message: Nachrichtentext
            chat_id: Optional, überschreibt Standard-Chat-ID

        Returns:
            True wenn erfolgreich gesendet
        """
        if not self._requests_available:
            error = "requests nicht installiert"
            logger.error(f"TelegramService: {error}")
            self._emit_error(error)
            return False

        if not self._bot_token:
            error = "Kein Bot-Token konfiguriert"
            logger.error(f"TelegramService: {error}")
            self._emit_error(error)
            return False

        target_chat_id = chat_id or self._chat_id

        if not target_chat_id:
            error = "Keine Chat-ID angegeben"
            logger.error(f"TelegramService: {error}")
            self._emit_error(error)
            return False

        # Sende in separatem Thread um UI nicht zu blockieren
        def send_async():
            try:
                import requests

                url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
                params = {
                    "chat_id": target_chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }

                self._emit_status(f"Sende an Chat {target_chat_id}...")
                logger.info(f"TelegramService: Sende Nachricht an Chat {target_chat_id}")

                response = requests.get(url, params=params, timeout=10)
                result = response.json()

                if result.get("ok"):
                    self._emit_status(f"✅ Nachricht gesendet an Chat {target_chat_id}")
                    logger.info(f"TelegramService: Nachricht erfolgreich gesendet")
                    return True
                else:
                    error = result.get("description", "Unbekannter Fehler")
                    logger.error(f"TelegramService: API-Fehler: {error}")
                    self._emit_error(f"Telegram-Fehler: {error}")
                    return False

            except Exception as e:
                error = f"Fehler beim Senden: {e}"
                logger.error(f"TelegramService: {error}")
                self._emit_error(error)
                return False

        thread = threading.Thread(target=send_async, daemon=True)
        thread.start()
        return True

    def send_trade_notification(self, notification: TradeNotification) -> bool:
        """
        Sendet eine Trade-Benachrichtigung.

        Args:
            notification: TradeNotification mit Trade-Details

        Returns:
            True wenn Senden gestartet wurde
        """
        if not self._enabled:
            logger.debug("TelegramService: Benachrichtigungen deaktiviert")
            return False

        if not self.is_configured:
            logger.error("TelegramService: Bot-Token oder Chat-ID nicht konfiguriert")
            return False

        message = notification.format_message()
        return self.send_message(message)

    def notify_position_opened(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        leverage: int | None = None
    ) -> bool:
        """Sendet Benachrichtigung bei Position-Eröffnung."""
        notification = TradeNotification(
            action="BUY",
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            leverage=leverage,
            timestamp=datetime.now()
        )
        return self.send_trade_notification(notification)

    def notify_position_closed(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        exit_price: float,
        pnl: float,
        pnl_percent: float,
        reason: str = "SELL"
    ) -> bool:
        """Sendet Benachrichtigung bei Position-Schließung."""
        action_map = {
            "SELL": "SELL",
            "STOP_LOSS": "STOP_LOSS",
            "SL": "STOP_LOSS",
            "TAKE_PROFIT": "TAKE_PROFIT",
            "TP": "TAKE_PROFIT",
        }
        action = action_map.get(reason.upper(), "SELL")

        notification = TradeNotification(
            action=action,
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=pnl,
            pnl_percent=pnl_percent,
            timestamp=datetime.now()
        )
        return self.send_trade_notification(notification)


# Singleton Instance
_telegram_service: TelegramService | None = None


def get_telegram_service() -> TelegramService:
    """Gibt die Singleton-Instanz des Telegram-Service zurück."""
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramService()
    return _telegram_service
