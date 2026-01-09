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
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #25D366;
            padding: 5px;
        """)
        layout.addWidget(header)

        # --- Status Frame ---
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)

        # Enable Checkbox
        self.enable_checkbox = QCheckBox("🔔 Trade-Benachrichtigungen aktivieren")
        self.enable_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #fff;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:checked {
                background-color: #25D366;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.enable_checkbox)

        # Status Label
        self.status_label = QLabel("Status: Nicht verbunden")
        self.status_label.setStyleSheet("color: #888; font-size: 11px; padding-left: 25px;")
        status_layout.addWidget(self.status_label)

        layout.addWidget(status_frame)

        # --- Konfiguration GroupBox ---
        config_group = QGroupBox("⚙ Konfiguration")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        config_layout = QFormLayout(config_group)
        config_layout.setContentsMargins(10, 20, 10, 10)
        config_layout.setSpacing(10)

        # Telefonnummer
        self.phone_input = QLineEdit()
        self.phone_input.setText("+491607512120")
        self.phone_input.setPlaceholderText("+49...")
        self.phone_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: #fff;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #25D366;
            }
        """)
        config_layout.addRow("📞 Telefonnummer:", self.phone_input)

        layout.addWidget(config_group)

        # --- Manuelle Nachricht GroupBox ---
        manual_group = QGroupBox("✉ Manuelle Nachricht")
        manual_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        manual_layout = QVBoxLayout(manual_group)
        manual_layout.setContentsMargins(10, 20, 10, 10)
        manual_layout.setSpacing(10)

        # Nachrichtentext
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Nachricht eingeben...")
        self.message_input.setMaximumHeight(100)
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d44;
                color: #fff;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #25D366;
            }
        """)
        manual_layout.addWidget(self.message_input)

        # Send Button
        self.send_btn = QPushButton("📤 Nachricht senden")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """)
        manual_layout.addWidget(self.send_btn)

        layout.addWidget(manual_group)

        # --- Log GroupBox ---
        log_group = QGroupBox("📋 Nachrichten-Log")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 20, 10, 10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #aaa;
                border: 1px solid #333;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_text)

        # Clear Log Button
        clear_btn = QPushButton("🗑 Log löschen")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #aaa;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        clear_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(log_group)

        # --- Info Label ---
        info_label = QLabel(
            "ℹ️ WhatsApp Web muss im Browser eingeloggt sein.\n"
            "   Bei aktivierten Benachrichtigungen wird bei jedem Trade\n"
            "   automatisch eine Nachricht gesendet."
        )
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
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
                self.status_label.setStyleSheet("color: #25D366; font-size: 11px; padding-left: 25px;")
            else:
                self.status_label.setText("Status: ❌ pywhatkit nicht installiert")
                self.status_label.setStyleSheet("color: #f44336; font-size: 11px; padding-left: 25px;")
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
