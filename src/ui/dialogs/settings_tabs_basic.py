"""Settings Tabs - Basic Settings (General, Trading, Broker).

Refactored from 820 LOC monolith using composition pattern.

Module 1/7 of settings_tabs_mixin.py split.

Contains:
- _create_general_tab(): Theme, auto-connect, default broker, chart colors (Issue #34)
- _create_trading_tab(): Order approval, max size, risk tolerance
- _create_broker_tab(): IBKR, Trade Republic, Bitunix broker settings
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class SettingsTabsBasic:
    """Helper für Basic Settings Tabs (General, Trading, Broker)."""

    def __init__(self, parent):
        """
        Args:
            parent: SettingsDialog Instanz
        """
        self.parent = parent

    def create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.parent.theme_combo = QComboBox()
        self.parent.theme_combo.addItems(["Dark Orange", "Dark White"])
        layout.addRow("Theme:", self.parent.theme_combo)

        # Auto-connect broker
        self.parent.auto_connect_check = QCheckBox("Auto-connect to broker on startup")
        layout.addRow(self.parent.auto_connect_check)

        # Default broker
        self.parent.default_broker_combo = QComboBox()
        self.parent.default_broker_combo.addItems(["Mock Broker", "Interactive Brokers", "Trade Republic"])
        layout.addRow("Default Broker:", self.parent.default_broker_combo)

        # Separator
        layout.addRow(QLabel(""))
        layout.addRow(QLabel("<b>Logging & Debug</b>"))

        # Console Debug Level
        self.parent.console_debug_level = QComboBox()
        self.parent.console_debug_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.parent.console_debug_level.setToolTip(
            "DEBUG: Alle Nachrichten inkl. Stream-Daten\n"
            "INFO: Normale Nachrichten\n"
            "WARNING: Nur Warnungen und Fehler (ohne Stream-Infos)\n"
            "ERROR: Nur Fehlermeldungen"
        )
        layout.addRow("Console Log Level:", self.parent.console_debug_level)

        # Issue #34: Chart Colors Section
        layout.addRow(QLabel(""))
        layout.addRow(QLabel("<b>Chart Farben</b>"))

        # Bullish Candle Color
        self.parent.bullish_color_btn = QPushButton()
        self.parent.bullish_color_btn.setFixedSize(80, 30)
        self.parent.bullish_color_btn.clicked.connect(lambda: self._choose_color('bullish'))
        self.parent.bullish_color = QColor("#26a69a")  # Default green
        self._update_color_button(self.parent.bullish_color_btn, self.parent.bullish_color)
        layout.addRow("Bullische Kerzen:", self.parent.bullish_color_btn)

        # Bearish Candle Color
        self.parent.bearish_color_btn = QPushButton()
        self.parent.bearish_color_btn.setFixedSize(80, 30)
        self.parent.bearish_color_btn.clicked.connect(lambda: self._choose_color('bearish'))
        self.parent.bearish_color = QColor("#ef5350")  # Default red
        self._update_color_button(self.parent.bearish_color_btn, self.parent.bearish_color)
        layout.addRow("Bärische Kerzen:", self.parent.bearish_color_btn)

        # Background Color
        self.parent.background_color_btn = QPushButton()
        self.parent.background_color_btn.setFixedSize(80, 30)
        self.parent.background_color_btn.clicked.connect(lambda: self._choose_color('background'))
        self.parent.background_color = QColor("#1e1e1e")  # Default dark
        self._update_color_button(self.parent.background_color_btn, self.parent.background_color)
        layout.addRow("Hintergrund:", self.parent.background_color_btn)

        # Issue #35: Background Image Section
        layout.addRow(QLabel(""))
        layout.addRow(QLabel("<b>Chart Hintergrundbild</b>"))

        # Background Image Selection
        bg_image_layout = QHBoxLayout()
        self.parent.background_image_path = ""  # Will be loaded from settings
        self.parent.background_image_label = QLabel("Kein Bild ausgewählt")
        self.parent.background_image_label.setStyleSheet("color: #888; font-style: italic;")
        bg_image_layout.addWidget(self.parent.background_image_label)

        self.parent.background_image_btn = QPushButton("Bild wählen...")
        self.parent.background_image_btn.clicked.connect(self._choose_background_image)
        bg_image_layout.addWidget(self.parent.background_image_btn)

        self.parent.background_image_clear_btn = QPushButton("✕")
        self.parent.background_image_clear_btn.setFixedWidth(30)
        self.parent.background_image_clear_btn.setToolTip("Hintergrundbild entfernen")
        self.parent.background_image_clear_btn.clicked.connect(self._clear_background_image)
        bg_image_layout.addWidget(self.parent.background_image_clear_btn)

        layout.addRow("Hintergrundbild:", bg_image_layout)

        # Background Image Opacity Slider
        opacity_layout = QHBoxLayout()
        self.parent.background_image_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.background_image_opacity_slider.setRange(0, 100)
        self.parent.background_image_opacity_slider.setValue(30)  # 30% default opacity
        self.parent.background_image_opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.parent.background_image_opacity_slider.setTickInterval(10)
        self.parent.background_image_opacity_slider.valueChanged.connect(self._update_opacity_label)
        opacity_layout.addWidget(self.parent.background_image_opacity_slider)

        self.parent.background_image_opacity_label = QLabel("30%")
        self.parent.background_image_opacity_label.setFixedWidth(40)
        self.parent.background_image_opacity_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        opacity_layout.addWidget(self.parent.background_image_opacity_label)

        layout.addRow("Transparenz:", opacity_layout)

        info_label = QLabel(
            "<i>Tipp: Niedrige Transparenz (10-30%) für bessere Lesbarkeit empfohlen</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-size: 9px;")
        layout.addRow(info_label)

        # Issue #39: Candle Border Radius
        layout.addRow(QLabel(""))
        layout.addRow(QLabel("<b>Kerzen-Abrundung</b>"))

        radius_layout = QHBoxLayout()
        self.parent.candle_border_radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.candle_border_radius_slider.setRange(0, 10)  # 0-10 pixels
        self.parent.candle_border_radius_slider.setValue(0)  # 0 = no rounding (default)
        self.parent.candle_border_radius_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.parent.candle_border_radius_slider.setTickInterval(1)
        self.parent.candle_border_radius_slider.valueChanged.connect(self._update_border_radius_label)
        radius_layout.addWidget(self.parent.candle_border_radius_slider)

        self.parent.candle_border_radius_label = QLabel("0 px")
        self.parent.candle_border_radius_label.setFixedWidth(50)
        self.parent.candle_border_radius_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        radius_layout.addWidget(self.parent.candle_border_radius_label)

        layout.addRow("Ecken-Abrundung:", radius_layout)

        radius_info_label = QLabel(
            "<i>0 = Keine Abrundung (Standard), 3-5 = Leicht abgerundet, 10 = Stark abgerundet</i>"
        )
        radius_info_label.setWordWrap(True)
        radius_info_label.setStyleSheet("color: #888; font-size: 9px;")
        layout.addRow(radius_info_label)

        return tab

    def _choose_background_image(self) -> None:
        """Open file dialog to choose background image (Issue #35)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Hintergrundbild auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif);;Alle Dateien (*.*)"
        )

        if file_path:
            self.parent.background_image_path = file_path
            # Show filename in label
            import os
            filename = os.path.basename(file_path)
            self.parent.background_image_label.setText(filename)
            self.parent.background_image_label.setStyleSheet("color: #26a69a;")

    def _clear_background_image(self) -> None:
        """Clear background image selection (Issue #35)."""
        self.parent.background_image_path = ""
        self.parent.background_image_label.setText("Kein Bild ausgewählt")
        self.parent.background_image_label.setStyleSheet("color: #888; font-style: italic;")

    def _update_opacity_label(self, value: int) -> None:
        """Update opacity label when slider changes (Issue #35).

        Args:
            value: Opacity value (0-100)
        """
        self.parent.background_image_opacity_label.setText(f"{value}%")

    def _update_border_radius_label(self, value: int) -> None:
        """Update border radius label when slider changes (Issue #39).

        Args:
            value: Border radius in pixels (0-10)
        """
        self.parent.candle_border_radius_label.setText(f"{value} px")

    def _choose_color(self, color_type: str) -> None:
        """Open color picker dialog (Issue #34).

        Args:
            color_type: 'bullish', 'bearish', or 'background'
        """
        # Get current color
        if color_type == 'bullish':
            current_color = self.parent.bullish_color
            btn = self.parent.bullish_color_btn
        elif color_type == 'bearish':
            current_color = self.parent.bearish_color
            btn = self.parent.bearish_color_btn
        else:  # background
            current_color = self.parent.background_color
            btn = self.parent.background_color_btn

        # Open color dialog
        color = QColorDialog.getColor(current_color, self.parent, f"{color_type.title()} Farbe wählen")

        if color.isValid():
            # Update color
            if color_type == 'bullish':
                self.parent.bullish_color = color
            elif color_type == 'bearish':
                self.parent.bearish_color = color
            else:  # background
                self.parent.background_color = color

            # Update button appearance
            self._update_color_button(btn, color)

    def _update_color_button(self, button: QPushButton, color: QColor) -> None:
        """Update button to show selected color (Issue #34).

        Args:
            button: QPushButton to update
            color: QColor to display
        """
        button.setStyleSheet(
            f"QPushButton {{ background-color: {color.name()}; "
            f"border: 2px solid #555; }}"
        )

    def create_trading_tab(self) -> QWidget:
        """Create trading settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.parent.manual_approval = QCheckBox("Require manual approval for orders")
        self.parent.manual_approval.setChecked(True)
        layout.addRow(self.parent.manual_approval)

        self.parent.confirm_cancel = QCheckBox("Confirm before canceling orders")
        self.parent.confirm_cancel.setChecked(True)
        layout.addRow(self.parent.confirm_cancel)

        # Max order size
        self.parent.max_order_size = QDoubleSpinBox()
        self.parent.max_order_size.setRange(100, 100000)
        self.parent.max_order_size.setValue(10000)
        self.parent.max_order_size.setPrefix("€")
        layout.addRow("Max Order Size:", self.parent.max_order_size)

        # Risk tolerance
        self.parent.risk_combo = QComboBox()
        self.parent.risk_combo.addItems(["Conservative", "Moderate", "Aggressive"])
        layout.addRow("Risk Tolerance:", self.parent.risk_combo)

        return tab

    def create_broker_tab(self) -> QWidget:
        """Create broker settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # IBKR Settings
        layout.addRow(QLabel("<b>Interactive Brokers (IBKR)</b>"))

        self.parent.ibkr_host = QLineEdit()
        self.parent.ibkr_host.setPlaceholderText("localhost or IP address")
        layout.addRow("IBKR Host:", self.parent.ibkr_host)

        self.parent.ibkr_port = QComboBox()
        self.parent.ibkr_port.addItems(["7497 (Paper)", "7496 (Live)"])
        layout.addRow("IBKR Port:", self.parent.ibkr_port)

        self.parent.ibkr_client_id = QComboBox()
        self.parent.ibkr_client_id.addItems(["1", "2", "3", "4", "5"])
        layout.addRow("IBKR Client ID:", self.parent.ibkr_client_id)

        # Trade Republic Settings
        layout.addRow(QLabel("<b>Trade Republic</b>"))

        self.parent.tr_phone = QLineEdit()
        self.parent.tr_phone.setPlaceholderText("+49...")
        layout.addRow("Phone Number:", self.parent.tr_phone)

        self.parent.tr_pin = QLineEdit()
        self.parent.tr_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.tr_pin.setPlaceholderText("4-digit PIN")
        self.parent.tr_pin.setMaxLength(4)
        layout.addRow("PIN:", self.parent.tr_pin)

        # Bitunix Settings
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<b>Bitunix Futures</b>"))

        self.parent.bitunix_broker_enabled = QCheckBox("Enable Bitunix for trading")
        layout.addRow(self.parent.bitunix_broker_enabled)

        bitunix_note = QLabel("<i>Note: Configure API keys in Market Data → Bitunix tab</i>")
        bitunix_note.setWordWrap(True)
        layout.addRow(bitunix_note)

        return tab
