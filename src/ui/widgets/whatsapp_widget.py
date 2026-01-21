"""
WhatsApp Widget - UI für WhatsApp-Benachrichtigungen

Ermöglicht:
- Manuelle Nachrichtenversendung
- Konfiguration der Telefonnummer
- Ein-/Ausschalten von Trade-Benachrichtigungen
"""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
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

logger = logging.getLogger(__name__)


class WhatsAppWidget(QWidget):
    """Widget für WhatsApp-Benachrichtigungen im Trading Bot."""

    # Signals
    notifications_toggled = pyqtSignal(bool)  # Emittiert wenn Benachrichtigungen ein/aus

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._whatsapp_service = None
        self._setup_ui()
        self._connect_signals()
        self._load_service()

    def _setup_ui(self) -> None:
        """Erstellt das UI-Layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # --- Header ---
        header = QLabel("📱 WhatsApp Benachrichtigungen")
        header.setProperty("class", "header")
        layout.addWidget(header)

        # --- Status Frame ---
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(status_frame)

        # Enable Checkbox
        self.enable_checkbox = QCheckBox("🔔 Trade-Benachrichtigungen aktivieren")
        status_layout.addWidget(self.enable_checkbox)

        # Status Label
        self.status_label = QLabel("Status: Nicht verbunden")
        status_layout.addWidget(self.status_label)

        layout.addWidget(status_frame)

        # --- Konfiguration GroupBox ---
        config_group = QGroupBox("⚙ Konfiguration")
        config_layout = QFormLayout(config_group)
        config_layout.setContentsMargins(10, 20, 10, 10)
        config_layout.setSpacing(10)

        # Telefonnummer
        self.phone_input = QLineEdit()
        self.phone_input.setText("+491607512120")
        self.phone_input.setPlaceholderText("+49...")
        config_layout.addRow("📞 Telefonnummer:", self.phone_input)

        layout.addWidget(config_group)

        # --- Manuelle Nachricht GroupBox ---
        manual_group = QGroupBox("✉ Manuelle Nachricht")
        manual_layout = QVBoxLayout(manual_group)
        manual_layout.setContentsMargins(10, 20, 10, 10)
        manual_layout.setSpacing(10)

        # Nachrichtentext
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Nachricht eingeben...")
        self.message_input.setMaximumHeight(100)
        manual_layout.addWidget(self.message_input)

        # Send Button
        self.send_btn = QPushButton("📤 Nachricht senden")
        # Use primary style from theme
        self.send_btn.setProperty("class", "primary")
        manual_layout.addWidget(self.send_btn)

        layout.addWidget(manual_group)

        # --- Log GroupBox ---
        log_group = QGroupBox("📋 Nachrichten-Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 20, 10, 10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        # Clear Log Button
        clear_btn = QPushButton("🗑 Log löschen")
        clear_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(log_group)

        # --- Info Label ---
        info_label = QLabel(
            "ℹ️ WhatsApp Web muss im Browser eingeloggt sein.\n"
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
        self.phone_input.textChanged.connect(self._on_phone_changed)

    def _load_service(self) -> None:
        """Lädt den WhatsApp-Service."""
        try:
            from src.core.notifications import get_whatsapp_service

            self._whatsapp_service = get_whatsapp_service()
            self._whatsapp_service.set_status_callback(self._on_service_status)
            self._whatsapp_service.set_error_callback(self._on_service_error)

            # UI aktualisieren
            if self._whatsapp_service.is_available:
                self.status_label.setText("Status: ✅ pywhatkit verfügbar")
                self.status_label.setStyleSheet("color: #25D366;") # Keep specific status colors
            else:
                self.status_label.setText("Status: ❌ pywhatkit nicht installiert")
                self.status_label.setStyleSheet("color: #f44336;")
                self.send_btn.setEnabled(False)
                self.enable_checkbox.setEnabled(False)

            # Telefonnummer setzen
            self.phone_input.setText(self._whatsapp_service.phone_number)
            self.enable_checkbox.setChecked(self._whatsapp_service.enabled)

            logger.info("WhatsAppWidget: Service geladen")

        except Exception as e:
            logger.error(f"WhatsAppWidget: Fehler beim Laden des Service: {e}")
            self.status_label.setText(f"Status: ❌ Fehler: {e}")
            self.send_btn.setEnabled(False)

    def _on_enable_toggled(self, enabled: bool) -> None:
        """Callback wenn Benachrichtigungen ein/aus geschaltet werden."""
        if self._whatsapp_service:
            self._whatsapp_service.enabled = enabled

        status = "aktiviert" if enabled else "deaktiviert"
        self._log(f"🔔 Benachrichtigungen {status}")
        self.notifications_toggled.emit(enabled)

    def _on_phone_changed(self, text: str) -> None:
        """Callback wenn Telefonnummer geändert wird."""
        if self._whatsapp_service and text:
            self._whatsapp_service.phone_number = text

    def _on_send_clicked(self) -> None:
        """Callback wenn Senden-Button geklickt wird."""
        message = self.message_input.toPlainText().strip()

        if not message:
            QMessageBox.warning(self, "Fehler", "Bitte eine Nachricht eingeben.")
            return

        phone = self.phone_input.text().strip()
        if not phone:
            QMessageBox.warning(self, "Fehler", "Bitte eine Telefonnummer eingeben.")
            return

        if self._whatsapp_service:
            self._log(f"📤 Sende an {phone}...")
            self.send_btn.setEnabled(False)
            self._whatsapp_service.send_message(message, phone)

            # Button nach kurzer Zeit wieder aktivieren
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.send_btn.setEnabled(True))

    def _on_service_status(self, message: str) -> None:
        """Callback für Status-Updates vom Service."""
        self._log(message)
        self.send_btn.setEnabled(True)

    def _on_service_error(self, error: str) -> None:
        """Callback für Fehler vom Service."""
        self._log(f"❌ {error}")
        self.send_btn.setEnabled(True)

    def _log(self, message: str) -> None:
        """Fügt eine Zeile zum Log hinzu."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # Issue #41: Limit log size to prevent memory growth
        # Keep only last 200 lines
        doc = self.log_text.document()
        if doc.blockCount() > 200:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, doc.blockCount() - 200)
            cursor.removeSelectedText()
            self.log_text.setTextCursor(cursor)

    # --- Public API ---

    def set_phone_number(self, phone: str) -> None:
        """Setzt die Telefonnummer."""
        self.phone_input.setText(phone)

    def set_enabled(self, enabled: bool) -> None:
        """Aktiviert/Deaktiviert Benachrichtigungen."""
        self.enable_checkbox.setChecked(enabled)

    def is_enabled(self) -> bool:
        """Gibt zurück ob Benachrichtigungen aktiviert sind."""
        return self.enable_checkbox.isChecked()

    def get_service(self):
        """Gibt den WhatsApp-Service zurück."""
        return self._whatsapp_service

    def send_trade_notification(self, message: str) -> bool:
        """
        Sendet eine Trade-Benachrichtigung über das UI-Formular.
        Nutzt das Textfeld + Button, was nachweislich funktioniert.

        Args:
            message: Nachrichtentext

        Returns:
            True wenn Senden gestartet wurde
        """
        if not self.is_enabled():
            logger.debug("WhatsAppWidget: Benachrichtigungen deaktiviert")
            return False

        if not self._whatsapp_service or not self._whatsapp_service.is_available:
            logger.error("WhatsAppWidget: Service nicht verfügbar")
            return False

        try:
            # Nachricht ins Textfeld schreiben
            self.message_input.setPlainText(message)

            # Button programmatisch klicken (simuliert Benutzer-Klick)
            self.send_btn.click()

            logger.info("WhatsAppWidget: Trade-Benachrichtigung über UI gesendet")
            return True

        except Exception as e:
            logger.error(f"WhatsAppWidget: Fehler beim Senden: {e}")
            return False
