"""
WhatsApp Notification Service

Verwendet pywhatkit um WhatsApp-Nachrichten zu senden.
Wird für Trade-Benachrichtigungen verwendet.

WICHTIG: Erfordert eingeloggtes WhatsApp Web im Browser!
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

# Pfad zur Settings-Datei
_SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "config" / "bot_settings.json"


@dataclass
class TradeNotification:
    """Datenstruktur für Trade-Benachrichtigungen."""

    action: str  # "BUY", "SELL", "STOP_LOSS", "TAKE_PROFIT"
    symbol: str
    side: str  # "long", "short"
    quantity: float
    entry_price: float
    exit_price: float | None = None
    pnl: float | None = None
    pnl_percent: float | None = None
    leverage: int | None = None
    timestamp: datetime | None = None

    def format_message(self) -> str:
        """Formatiert die Benachrichtigung als WhatsApp-Nachricht."""
        ts = self.timestamp or datetime.now()
        time_str = ts.strftime("%H:%M:%S")

        if self.action == "BUY":
            emoji = "🟢" if self.side == "long" else "🔴"
            msg = (
                f"{emoji} POSITION ERÖFFNET\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 {self.symbol}\n"
                f"📈 {self.side.upper()} @ ${self.entry_price:.2f}\n"
                f"📦 Menge: {self.quantity:.4f}\n"
            )
            if self.leverage:
                msg += f"⚡ Leverage: {self.leverage}x\n"
            msg += f"🕐 {time_str}"

        elif self.action == "SELL":
            emoji = "✅" if (self.pnl or 0) >= 0 else "❌"
            pnl_sign = "+" if (self.pnl or 0) >= 0 else ""
            msg = (
                f"{emoji} POSITION GESCHLOSSEN\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 {self.symbol}\n"
                f"📈 {self.side.upper()}\n"
                f"💰 Entry: ${self.entry_price:.2f}\n"
                f"💵 Exit: ${self.exit_price:.2f}\n"
                f"📦 Menge: {self.quantity:.4f}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💎 P&L: {pnl_sign}${self.pnl:.2f} ({pnl_sign}{self.pnl_percent:.2f}%)\n"
                f"🕐 {time_str}"
            )

        elif self.action == "STOP_LOSS":
            msg = (
                f"🛑 STOP LOSS AUSGELÖST\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 {self.symbol}\n"
                f"📈 {self.side.upper()}\n"
                f"💰 Entry: ${self.entry_price:.2f}\n"
                f"💵 Exit: ${self.exit_price:.2f}\n"
                f"📦 Menge: {self.quantity:.4f}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"❌ P&L: ${self.pnl:.2f} ({self.pnl_percent:.2f}%)\n"
                f"🕐 {time_str}"
            )

        elif self.action == "TAKE_PROFIT":
            msg = (
                f"🎯 TAKE PROFIT ERREICHT\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 {self.symbol}\n"
                f"📈 {self.side.upper()}\n"
                f"💰 Entry: ${self.entry_price:.2f}\n"
                f"💵 Exit: ${self.exit_price:.2f}\n"
                f"📦 Menge: {self.quantity:.4f}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✅ P&L: +${self.pnl:.2f} (+{self.pnl_percent:.2f}%)\n"
                f"🕐 {time_str}"
            )
        else:
            msg = f"📱 Trading Alert: {self.action} {self.symbol}"

        return msg


class WhatsAppService:
    """Service zum Senden von WhatsApp-Nachrichten."""

    def __init__(self, phone_number: str = "+491607512120"):
        self._phone_number = phone_number
        self._enabled = False
        self._pywhatkit_available = False
        self._on_status_callback: Callable[[str], None] | None = None
        self._on_error_callback: Callable[[str], None] | None = None

        # Check if pywhatkit is available
        try:
            import pywhatkit
            self._pywhatkit_available = True
            logger.info("WhatsAppService: pywhatkit verfügbar")
        except ImportError:
            logger.warning("WhatsAppService: pywhatkit nicht installiert - pip install pywhatkit")

        # Lade gespeicherten Enabled-Status
        self._load_enabled_state()

    def _load_enabled_state(self) -> None:
        """Lädt den gespeicherten Enabled-Status aus der Settings-Datei."""
        try:
            if _SETTINGS_FILE.exists():
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self._enabled = settings.get("whatsapp_notifications_enabled", False)
                    logger.info(f"WhatsAppService: Enabled-Status geladen: {self._enabled}")
        except Exception as e:
            logger.warning(f"WhatsAppService: Fehler beim Laden des Enabled-Status: {e}")
            self._enabled = False

    def _save_enabled_state(self) -> None:
        """Speichert den Enabled-Status in der Settings-Datei."""
        try:
            settings = {}
            if _SETTINGS_FILE.exists():
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)

            settings["whatsapp_notifications_enabled"] = self._enabled

            with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            logger.info(f"WhatsAppService: Enabled-Status gespeichert: {self._enabled}")
        except Exception as e:
            logger.error(f"WhatsAppService: Fehler beim Speichern des Enabled-Status: {e}")

    @property
    def phone_number(self) -> str:
        return self._phone_number

    @phone_number.setter
    def phone_number(self, value: str) -> None:
        # Validierung: muss mit + beginnen
        if not value.startswith("+"):
            value = "+" + value
        self._phone_number = value
        logger.info(f"WhatsAppService: Telefonnummer geändert zu {value}")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        logger.info(f"WhatsAppService: Benachrichtigungen {'aktiviert' if value else 'deaktiviert'}")
        # Speichere Status persistent
        self._save_enabled_state()

    @property
    def is_available(self) -> bool:
        return self._pywhatkit_available

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

    def send_message(self, message: str, phone_number: str | None = None) -> bool:
        """
        Sendet eine WhatsApp-Nachricht.

        Args:
            message: Nachrichtentext
            phone_number: Optional, überschreibt Standard-Nummer

        Returns:
            True wenn erfolgreich gesendet
        """
        if not self._pywhatkit_available:
            error = "pywhatkit nicht installiert"
            logger.error(f"WhatsAppService: {error}")
            self._emit_error(error)
            return False

        target_number = phone_number or self._phone_number

        if not target_number:
            error = "Keine Telefonnummer angegeben"
            logger.error(f"WhatsAppService: {error}")
            self._emit_error(error)
            return False

        # Sende in separatem Thread um UI nicht zu blockieren
        def send_async():
            try:
                import pywhatkit as pwk

                self._emit_status(f"Sende an {target_number}...")
                logger.info(f"WhatsAppService: Sende Nachricht an {target_number}")

                # Sofort senden (öffnet Browser)
                pwk.sendwhatmsg_instantly(
                    target_number,
                    message,
                    wait_time=15,
                    tab_close=True,
                    close_time=3
                )

                # Optional: ENTER-Tastendruck erzwingen, falls Browser die Nachricht nicht automatisch sendet
                try:
                    import pyautogui  # type: ignore

                    time.sleep(2)
                    pyautogui.press("enter")
                    logger.debug("WhatsAppService: ENTER nach Senden ausgelöst (pyautogui)")
                except Exception:
                    logger.debug("WhatsAppService: pyautogui nicht verfügbar oder ENTER-Send nicht möglich")

                self._emit_status(f"✅ Nachricht gesendet an {target_number}")
                logger.info(f"WhatsAppService: Nachricht erfolgreich gesendet")
                return True

            except Exception as e:
                error = f"Fehler beim Senden: {e}"
                logger.error(f"WhatsAppService: {error}")
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
            logger.debug("WhatsAppService: Benachrichtigungen deaktiviert")
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
        # Map reason to action
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
_whatsapp_service: WhatsAppService | None = None


def get_whatsapp_service() -> WhatsAppService:
    """Gibt die Singleton-Instanz des WhatsApp-Service zurück."""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
