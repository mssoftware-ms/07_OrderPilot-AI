"""
Notification Widget - Kombiniertes Widget für WhatsApp und Telegram

Ermöglicht:
- Wechsel zwischen WhatsApp und Telegram via Radio-Buttons
- Telegram als Standardauswahl
- Einheitliche Schnittstelle für Trade-Benachrichtigungen
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QRadioButton,
    QButtonGroup,
    QFrame,
    QStackedWidget,
)

from src.ui.widgets.whatsapp_widget import WhatsAppWidget
from src.ui.widgets.telegram_widget import TelegramWidget

logger = logging.getLogger(__name__)

# Pfad zur Settings-Datei
_SETTINGS_FILE = Path(__file__).parent.parent.parent / "config" / "bot_settings.json"


class NotificationWidget(QWidget):
    """
    Kombiniertes Widget für WhatsApp und Telegram Benachrichtigungen.

    Zeigt Radio-Buttons zum Umschalten zwischen den Services und
    das entsprechende Service-Widget.
    """

    # Signal emittiert wenn sich der Service ändert
    service_changed = pyqtSignal(str)  # "whatsapp" oder "telegram"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._whatsapp_widget = None
        self._telegram_widget = None
        self._current_service = "telegram"  # Default: Telegram

        self._setup_ui()
        self._load_settings()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Erstellt das UI-Layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # --- Service-Auswahl (Radio Buttons) ---
        selector_frame = QFrame()
        selector_frame.setFrameShape(QFrame.Shape.StyledPanel)
        selector_layout = QHBoxLayout(selector_frame)
        selector_layout.setContentsMargins(10, 5, 10, 5)

        # Button Group für exklusive Auswahl
        self.service_group = QButtonGroup(self)

        # Radio Buttons
        self.telegram_radio = QRadioButton("Telegram")
        self.whatsapp_radio = QRadioButton("WhatsApp")

        self.service_group.addButton(self.telegram_radio, 0)
        self.service_group.addButton(self.whatsapp_radio, 1)

        # Issue #21: Telegram als Vorauswahl
        self.telegram_radio.setChecked(True)

        selector_layout.addWidget(self.telegram_radio)
        selector_layout.addWidget(self.whatsapp_radio)
        selector_layout.addStretch()

        layout.addWidget(selector_frame)

        # --- Stacked Widget für Service-Widgets ---
        self.stacked_widget = QStackedWidget()

        # Telegram Widget (Index 0)
        self._telegram_widget = TelegramWidget()
        self.stacked_widget.addWidget(self._telegram_widget)

        # WhatsApp Widget (Index 1)
        self._whatsapp_widget = WhatsAppWidget()
        self.stacked_widget.addWidget(self._whatsapp_widget)

        # Issue #21: Telegram als Vorauswahl
        self.stacked_widget.setCurrentIndex(0)

        layout.addWidget(self.stacked_widget)

    def _connect_signals(self) -> None:
        """Verbindet UI-Signale."""
        self.telegram_radio.toggled.connect(self._on_service_changed)
        self.whatsapp_radio.toggled.connect(self._on_service_changed)

    def _on_service_changed(self, checked: bool) -> None:
        """Callback wenn Service umgeschaltet wird."""
        if not checked:
            return

        if self.telegram_radio.isChecked():
            self.stacked_widget.setCurrentIndex(0)
            self._current_service = "telegram"
            logger.info("NotificationWidget: Telegram ausgewählt")
        else:
            self.stacked_widget.setCurrentIndex(1)
            self._current_service = "whatsapp"
            logger.info("NotificationWidget: WhatsApp ausgewählt")

        self._save_settings()
        self.service_changed.emit(self._current_service)

    def _load_settings(self) -> None:
        """Lädt die gespeicherte Service-Auswahl."""
        try:
            if _SETTINGS_FILE.exists():
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    service = settings.get("notification_service", "telegram")

                    if service == "whatsapp":
                        self.whatsapp_radio.setChecked(True)
                        self.stacked_widget.setCurrentIndex(1)
                        self._current_service = "whatsapp"
                    else:
                        self.telegram_radio.setChecked(True)
                        self.stacked_widget.setCurrentIndex(0)
                        self._current_service = "telegram"

                    logger.info(f"NotificationWidget: Service '{service}' geladen")

        except Exception as e:
            logger.warning(f"NotificationWidget: Fehler beim Laden der Settings: {e}")
            # Fallback zu Telegram (Default)
            self.telegram_radio.setChecked(True)
            self.stacked_widget.setCurrentIndex(0)
            self._current_service = "telegram"

    def _save_settings(self) -> None:
        """Speichert die aktuelle Service-Auswahl."""
        try:
            settings = {}
            if _SETTINGS_FILE.exists():
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)

            settings["notification_service"] = self._current_service

            _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            logger.info(f"NotificationWidget: Service '{self._current_service}' gespeichert")

        except Exception as e:
            logger.error(f"NotificationWidget: Fehler beim Speichern der Settings: {e}")

    # --- Public API ---

    def get_current_service(self) -> str:
        """Gibt den aktuell ausgewählten Service zurück ('telegram' oder 'whatsapp')."""
        return self._current_service

    def get_telegram_widget(self) -> TelegramWidget:
        """Gibt das Telegram-Widget zurück."""
        return self._telegram_widget

    def get_whatsapp_widget(self) -> WhatsAppWidget:
        """Gibt das WhatsApp-Widget zurück."""
        return self._whatsapp_widget

    def send_trade_notification(self, message: str) -> bool:
        """
        Sendet eine Trade-Benachrichtigung über den aktuell ausgewählten Service.

        Args:
            message: Nachrichtentext

        Returns:
            True wenn Senden erfolgreich gestartet wurde
        """
        if self._current_service == "telegram":
            return self._telegram_widget.send_trade_notification(message)
        else:
            return self._whatsapp_widget.send_trade_notification(message)

    def is_enabled(self) -> bool:
        """Gibt zurück ob Benachrichtigungen im aktuellen Service aktiviert sind."""
        if self._current_service == "telegram":
            return self._telegram_widget.is_enabled()
        else:
            return self._whatsapp_widget.is_enabled()
