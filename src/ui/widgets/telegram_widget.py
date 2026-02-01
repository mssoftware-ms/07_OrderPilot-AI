"""
Telegram Widget - UI für Telegram-Benachrichtigungen

Ermöglicht:
- Manuelle Nachrichtenversendung
- Konfiguration von Bot-Token und Chat-ID
- Ein-/Ausschalten von Trade-Benachrichtigungen
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import aiohttp
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QGroupBox,
    QFrame,
    QFormLayout,
    QMessageBox,
)
from qasync import asyncSlot

logger = logging.getLogger(__name__)


class TelegramWidget(QWidget):
    """Widget für Telegram-Benachrichtigungen im Trading Bot."""

    # Signals
    notifications_toggled = pyqtSignal(bool)  # Emittiert wenn Benachrichtigungen ein/aus

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._telegram_service = None
        self._setup_ui()
        self._connect_signals()
        self._load_service()

    def _setup_ui(self) -> None:
        """Erstellt das UI-Layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # --- Header ---
        header = QLabel("Telegram Benachrichtigungen")
        header.setProperty("class", "header")
        layout.addWidget(header)

        # --- Status Frame ---
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(status_frame)

        # Enable Checkbox
        self.enable_checkbox = QCheckBox("Trade-Benachrichtigungen aktivieren")
        status_layout.addWidget(self.enable_checkbox)

        # Status Label
        self.status_label = QLabel("Status: Nicht verbunden")
        status_layout.addWidget(self.status_label)

        layout.addWidget(status_frame)

        # --- Konfiguration GroupBox ---
        config_group = QGroupBox("Konfiguration")
        config_layout = QFormLayout(config_group)
        config_layout.setContentsMargins(10, 20, 10, 10)
        config_layout.setSpacing(10)

        # Bot Token wird aus Systemvariable geladen - kein UI-Feld mehr nötig
        # Info-Label für Bot-Token Status (wird in _load_service() aktualisiert)
        self.token_status_label = QLabel("⏳ Lade Bot-Token...")
        self.token_status_label.setStyleSheet("color: #888;")
        config_layout.addRow("Bot Token:", self.token_status_label)

        # Chat ID mit Auto-Abruf Button
        chat_id_layout = QHBoxLayout()
        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("123456789")
        chat_id_layout.addWidget(self.chat_id_input)

        self.get_chat_id_btn = QPushButton("Chat-ID abrufen")
        self.get_chat_id_btn.setToolTip(
            "Holt deine Chat-ID automatisch vom Bot.\n\n"
            "WICHTIG: Sende zuerst eine Nachricht an deinen Bot in Telegram\n"
            "(z.B. /start), dann klicke hier!"
        )
        self.get_chat_id_btn.clicked.connect(self._on_get_chat_id_clicked)
        chat_id_layout.addWidget(self.get_chat_id_btn)

        config_layout.addRow("Chat ID:", chat_id_layout)

        layout.addWidget(config_group)

        # --- Manuelle Nachricht GroupBox ---
        manual_group = QGroupBox("Manuelle Nachricht")
        manual_layout = QVBoxLayout(manual_group)
        manual_layout.setContentsMargins(10, 20, 10, 10)
        manual_layout.setSpacing(10)

        # Nachrichtentext
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Nachricht eingeben...")
        self.message_input.setMaximumHeight(100)
        manual_layout.addWidget(self.message_input)

        # Send Button
        self.send_btn = QPushButton("Nachricht senden")
        self.send_btn.setProperty("class", "primary")
        manual_layout.addWidget(self.send_btn)

        layout.addWidget(manual_group)

        # --- Log GroupBox ---
        log_group = QGroupBox("Nachrichten-Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 20, 10, 10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        # Clear Log Button
        clear_btn = QPushButton("Log löschen")
        clear_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(log_group)

        # --- Info Label ---
        info_label = QLabel(
            "ℹ️ Setup-Anleitung:\n"
            "   \n"
            "   1. Bot-Token Setup:\n"
            "      • Erstelle einen Bot bei @BotFather in Telegram\n"
            "      • Setze Windows Systemvariable: TELEGRAM_TOKEN=<dein_token>\n"
            "      • Starte die Anwendung neu\n"
            "   \n"
            "   2. Chat-ID automatisch abrufen:\n"
            "      • Sende eine Nachricht an deinen Bot in Telegram (z.B. /start)\n"
            "      • Klicke auf 'Chat-ID abrufen' Button\n"
            "      • Deine Chat-ID wird automatisch eingetragen\n"
            "   \n"
            "   3. Trade-Benachrichtigungen aktivieren (Checkbox oben)\n"
            "   \n"
            "   Bei aktivierten Benachrichtigungen wird bei jedem Trade\n"
            "   automatisch eine Nachricht gesendet."
        )
        info_label.setProperty("class", "info-label")
        layout.addWidget(info_label)

        layout.addStretch()

    def _connect_signals(self) -> None:
        """Verbindet UI-Signale."""
        self.enable_checkbox.toggled.connect(self._on_enable_toggled)
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.chat_id_input.textChanged.connect(self._on_chat_id_changed)

    def _load_service(self) -> None:
        """Lädt den Telegram-Service."""
        try:
            from src.core.notifications.telegram_service import get_telegram_service

            self._telegram_service = get_telegram_service()
            self._telegram_service.set_status_callback(self._on_service_status)
            self._telegram_service.set_error_callback(self._on_service_error)

            # UI aktualisieren
            if self._telegram_service.is_available:
                self.status_label.setText("Status: ✅ requests verfügbar")
                self.status_label.setStyleSheet("color: #25D366;")
            else:
                self.status_label.setText("Status: ❌ requests nicht installiert")
                self.status_label.setStyleSheet("color: #f44336;")
                self.send_btn.setEnabled(False)
                self.enable_checkbox.setEnabled(False)

            # Bot-Token Status aktualisieren
            if self._telegram_service.bot_token:
                self.token_status_label.setText("✅ Bot-Token aus TELEGRAM_TOKEN geladen")
                self.token_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.token_status_label.setText("⚠️ TELEGRAM_TOKEN Systemvariable nicht gesetzt!")
                self.token_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
                self.send_btn.setEnabled(False)
                self.get_chat_id_btn.setEnabled(False)

            # Chat-ID setzen
            self.chat_id_input.setText(self._telegram_service.chat_id)
            self.enable_checkbox.setChecked(self._telegram_service.enabled)

            logger.info("TelegramWidget: Service geladen")

        except Exception as e:
            logger.error(f"TelegramWidget: Fehler beim Laden des Service: {e}")
            self.status_label.setText(f"Status: ❌ Fehler: {e}")
            self.token_status_label.setText(f"❌ Fehler: {e}")
            self.token_status_label.setStyleSheet("color: #f44336;")
            self.send_btn.setEnabled(False)

    def _on_enable_toggled(self, enabled: bool) -> None:
        """Callback wenn Benachrichtigungen ein/aus geschaltet werden."""
        if self._telegram_service:
            self._telegram_service.enabled = enabled

        status = "aktiviert" if enabled else "deaktiviert"
        self._log(f"🔔 Benachrichtigungen {status}")
        self.notifications_toggled.emit(enabled)

    def _on_chat_id_changed(self, text: str) -> None:
        """Callback wenn Chat-ID geändert wird."""
        if self._telegram_service and text:
            self._telegram_service.chat_id = text

    def _show_message_box_threadsafe(self, box_type: str, title: str, message: str) -> None:
        """Zeigt MessageBox thread-sicher im Hauptthread an.

        Args:
            box_type: "information", "warning", oder "critical"
            title: Fenstertitel
            message: Nachrichtentext
        """
        def show_box():
            if box_type == "information":
                QMessageBox.information(self, title, message)
            elif box_type == "warning":
                QMessageBox.warning(self, title, message)
            elif box_type == "critical":
                QMessageBox.critical(self, title, message)

        # Führe im Hauptthread aus
        QTimer.singleShot(0, show_box)

    def _on_get_chat_id_clicked(self) -> None:
        """Startet den async Chat-ID Abruf."""
        # Hole Bot-Token aus dem Service (wird aus Systemvariable geladen)
        if not self._telegram_service or not self._telegram_service.bot_token:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bot-Token nicht verfügbar!\n\n"
                "Stelle sicher, dass die Windows Systemvariable\n"
                "TELEGRAM_TOKEN gesetzt ist und starte die Anwendung neu."
            )
            return

        if not self._telegram_service.is_available:
            QMessageBox.warning(
                self,
                "Fehler",
                "Telegram-Service nicht verfügbar.\nBitte installiere 'aiohttp': pip install aiohttp"
            )
            return

        # Zeige Info-Dialog
        reply = QMessageBox.question(
            self,
            "Chat-ID abrufen",
            "WICHTIG: Hast du bereits eine Nachricht an deinen Bot gesendet?\n\n"
            "Falls nicht:\n"
            "1. Öffne Telegram\n"
            "2. Suche deinen Bot\n"
            "3. Sende eine Nachricht (z.B. /start)\n"
            "4. Klicke dann auf OK\n\n"
            "Chat-ID jetzt abrufen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Starte async Abruf
        asyncio.create_task(self._fetch_chat_id_async())

    async def _fetch_chat_id_async(self) -> None:
        """Ruft die Chat-ID asynchron vom Telegram Bot ab (non-blocking)."""
        bot_token = self._telegram_service.bot_token
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

        self._log("📡 Rufe Chat-ID vom Bot ab...")
        self.get_chat_id_btn.setEnabled(False)

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    result = await response.json()

            if not result.get("ok"):
                error = result.get("description", "Unbekannter Fehler")
                self._log(f"❌ API-Fehler: {error}")
                QMessageBox.warning(
                    self,
                    "API-Fehler",
                    f"Telegram API Fehler:\n{error}\n\nPrüfe deinen Bot-Token!"
                )
                return

            updates = result.get("result", [])

            if not updates:
                self._log("❌ Keine Updates gefunden")
                QMessageBox.information(
                    self,
                    "Keine Nachrichten",
                    "Keine Nachrichten gefunden!\n\n"
                    "Bitte sende eine Nachricht an deinen Bot in Telegram\n"
                    "(z.B. /start) und versuche es erneut."
                )
                return

            # Hole die neuste Nachricht
            latest_message = updates[-1].get("message", {})
            chat = latest_message.get("chat", {})
            chat_id = chat.get("id")
            chat_name = chat.get("first_name") or chat.get("title") or "Unbekannt"

            if chat_id:
                self.chat_id_input.setText(str(chat_id))
                self._log(f"✅ Chat-ID gefunden: {chat_id} (Name: {chat_name})")
                QMessageBox.information(
                    self,
                    "Erfolg",
                    f"Chat-ID erfolgreich abgerufen!\n\n"
                    f"Chat-ID: {chat_id}\n"
                    f"Name: {chat_name}\n\n"
                    f"Die Chat-ID wurde automatisch eingetragen."
                )
            else:
                self._log("❌ Keine Chat-ID in der Antwort gefunden")
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Keine Chat-ID gefunden.\n\n"
                    "Stelle sicher, dass du dem Bot eine Nachricht geschickt hast."
                )

        except asyncio.TimeoutError:
            self._log("❌ Timeout nach 10 Sekunden")
            QMessageBox.warning(
                self,
                "Timeout",
                "Zeitüberschreitung beim Abrufen der Chat-ID.\n"
                "Bitte prüfe deine Internetverbindung."
            )
        except aiohttp.ClientError as e:
            error_msg = f"Netzwerkfehler: {e}"
            logger.error(f"TelegramWidget: {error_msg}")
            self._log(f"❌ {error_msg}")
            QMessageBox.critical(
                self,
                "Netzwerkfehler",
                f"Fehler beim Abrufen der Chat-ID:\n{e}"
            )
        except Exception as e:
            error_msg = f"Fehler beim Abrufen: {e}"
            logger.error(f"TelegramWidget: {error_msg}")
            self._log(f"❌ {error_msg}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Abrufen der Chat-ID:\n{e}"
            )
        finally:
            self.get_chat_id_btn.setEnabled(True)

    def _on_send_clicked(self) -> None:
        """Callback wenn Senden-Button geklickt wird."""
        message = self.message_input.toPlainText().strip()

        if not message:
            QMessageBox.warning(self, "Fehler", "Bitte eine Nachricht eingeben.")
            return

        # Bot-Token aus Service (Systemvariable)
        if not self._telegram_service or not self._telegram_service.bot_token:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bot-Token nicht verfügbar!\n\n"
                "Stelle sicher, dass die Windows Systemvariable\n"
                "TELEGRAM_TOKEN gesetzt ist und starte die Anwendung neu."
            )
            return

        chat_id = self.chat_id_input.text().strip()
        if not chat_id:
            QMessageBox.warning(self, "Fehler", "Bitte Chat-ID eingeben.")
            return

        if self._telegram_service:
            self._log(f"📤 Sende an Chat {chat_id}...")
            self.send_btn.setEnabled(False)
            self._telegram_service.send_message(message, chat_id)

            # Button nach kurzer Zeit wieder aktivieren
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.send_btn.setEnabled(True))

    def _on_service_status(self, message: str) -> None:
        """Callback für Status-Updates vom Service (thread-safe)."""
        # Service-Callbacks können aus Background-Thread kommen
        QTimer.singleShot(0, lambda: self._log(message))
        QTimer.singleShot(0, lambda: self.send_btn.setEnabled(True))

    def _on_service_error(self, error: str) -> None:
        """Callback für Fehler vom Service (thread-safe)."""
        # Service-Callbacks können aus Background-Thread kommen
        QTimer.singleShot(0, lambda: self._log(f"❌ {error}"))
        QTimer.singleShot(0, lambda: self.send_btn.setEnabled(True))

    def _log(self, message: str) -> None:
        """Fügt eine Zeile zum Log hinzu."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # Limit log size to prevent memory growth
        doc = self.log_text.document()
        if doc.blockCount() > 200:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, doc.blockCount() - 200)
            cursor.removeSelectedText()
            self.log_text.setTextCursor(cursor)

    # --- Public API ---

    def set_chat_id(self, chat_id: str) -> None:
        """Setzt die Chat-ID."""
        self.chat_id_input.setText(chat_id)

    def set_enabled(self, enabled: bool) -> None:
        """Aktiviert/Deaktiviert Benachrichtigungen."""
        self.enable_checkbox.setChecked(enabled)

    def is_enabled(self) -> bool:
        """Gibt zurück ob Benachrichtigungen aktiviert sind."""
        return self.enable_checkbox.isChecked()

    def get_service(self):
        """Gibt den Telegram-Service zurück."""
        return self._telegram_service

    def send_trade_notification(self, message: str) -> bool:
        """
        Sendet eine Trade-Benachrichtigung über das UI-Formular.

        Args:
            message: Nachrichtentext

        Returns:
            True wenn Senden gestartet wurde
        """
        if not self.is_enabled():
            logger.debug("TelegramWidget: Benachrichtigungen deaktiviert")
            return False

        if not self._telegram_service or not self._telegram_service.is_available:
            logger.error("TelegramWidget: Service nicht verfügbar")
            return False

        if not self._telegram_service.is_configured:
            logger.error("TelegramWidget: Bot-Token oder Chat-ID nicht konfiguriert")
            return False

        try:
            # Nachricht ins Textfeld schreiben
            self.message_input.setPlainText(message)

            # Button programmatisch klicken
            self.send_btn.click()

            logger.info("TelegramWidget: Trade-Benachrichtigung über UI gesendet")
            return True

        except Exception as e:
            logger.error(f"TelegramWidget: Fehler beim Senden: {e}")
            return False
