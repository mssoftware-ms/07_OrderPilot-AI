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
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
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

        return tab

    def create_theme_tab(self) -> QWidget:
        """Create theme and UI customization settings tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        
        # Scroll Area might be needed if many settings, but for now we use columns or groupboxes
        from PyQt6.QtWidgets import QScrollArea, QFrame
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # 1. Base Theme Selection
        theme_group = QGroupBox("Base Theme")
        theme_layout = QFormLayout(theme_group)
        self.parent.theme_combo = QComboBox()
        self.parent.theme_combo.addItems(["Dark Orange", "Dark White"])
        theme_layout.addRow("Global Theme:", self.parent.theme_combo)
        layout.addWidget(theme_group)

        # 2. UI Colors
        ui_colors_group = QGroupBox("UI Colors")
        ui_colors_layout = QFormLayout(ui_colors_group)
        
        # App Background
        self.parent.ui_bg_color_btn = QPushButton()
        self.parent.ui_bg_color_btn.setFixedSize(80, 25)
        self.parent.ui_bg_color_btn.clicked.connect(lambda: self._choose_color('ui_bg'))
        self.parent.ui_bg_color = QColor("#0F1115")
        ui_colors_layout.addRow("Main Background:", self.parent.ui_bg_color_btn)

        # Button Color
        self.parent.ui_btn_color_btn = QPushButton()
        self.parent.ui_btn_color_btn.setFixedSize(80, 25)
        self.parent.ui_btn_color_btn.clicked.connect(lambda: self._choose_color('ui_btn'))
        self.parent.ui_btn_color = QColor("#2A2D33")
        ui_colors_layout.addRow("Button Background:", self.parent.ui_btn_color_btn)

        # Dropdown Color
        self.parent.ui_dropdown_color_btn = QPushButton()
        self.parent.ui_dropdown_color_btn.setFixedSize(80, 25)
        self.parent.ui_dropdown_color_btn.clicked.connect(lambda: self._choose_color('ui_dropdown'))
        self.parent.ui_dropdown_color = QColor("#23262E")
        ui_colors_layout.addRow("Dropdown Fields:", self.parent.ui_dropdown_color_btn)

        # Edit/Input Color
        self.parent.ui_edit_color = QColor("#23262E")
        self.parent.ui_edit_color_btn = QPushButton()
        self.parent.ui_edit_color_btn.setFixedSize(80, 25)
        self.parent.ui_edit_color_btn.clicked.connect(lambda: self._choose_color('ui_edit'))
        ui_colors_layout.addRow("Edit/Input Bg:", self.parent.ui_edit_color_btn)

        # Edit/Input Text Color
        self.parent.ui_edit_text_color = QColor("#EAECEF")
        self.parent.ui_edit_text_color_btn = QPushButton()
        self.parent.ui_edit_text_color_btn.setFixedSize(80, 25)
        self.parent.ui_edit_text_color_btn.clicked.connect(lambda: self._choose_color('ui_edit_text'))
        ui_colors_layout.addRow("Edit/Input Text:", self.parent.ui_edit_text_color_btn)
        
        layout.addWidget(ui_colors_group)

        # 3. Button Styling
        btn_styling_group = QGroupBox("Button Styling")
        btn_styling_layout = QFormLayout(btn_styling_group)
        
        self.parent.ui_btn_font_combo = QFontComboBox()
        btn_styling_layout.addRow("Font Family:", self.parent.ui_btn_font_combo)
        
        self.parent.ui_btn_font_size = QSpinBox()
        self.parent.ui_btn_font_size.setRange(8, 24)
        self.parent.ui_btn_font_size.setValue(12)
        btn_styling_layout.addRow("Font Size:", self.parent.ui_btn_font_size)
        
        size_layout = QHBoxLayout()
        self.parent.ui_btn_width = QSpinBox()
        self.parent.ui_btn_width.setRange(20, 300)
        self.parent.ui_btn_width.setValue(80)
        self.parent.ui_btn_width.setSuffix(" px")
        
        self.parent.ui_btn_height = QSpinBox()
        self.parent.ui_btn_height.setRange(15, 100)
        self.parent.ui_btn_height.setValue(32)
        self.parent.ui_btn_height.setSuffix(" px")
        
        size_layout.addWidget(QLabel("W:"))
        size_layout.addWidget(self.parent.ui_btn_width)
        size_layout.addWidget(QLabel(" H:"))
        size_layout.addWidget(self.parent.ui_btn_height)
        btn_styling_layout.addRow("Button Min Size:", size_layout)
        
        layout.addWidget(btn_styling_group)

        # 4. Interaction colors (Toggle Buttons)
        toggle_group = QGroupBox("Toggle/Checkbox Button Colors")
        toggle_layout = QFormLayout(toggle_group)
        
        self.parent.ui_active_btn_color_btn = QPushButton()
        self.parent.ui_active_btn_color_btn.setFixedSize(80, 25)
        self.parent.ui_active_btn_color_btn.clicked.connect(lambda: self._choose_color('ui_active'))
        self.parent.ui_active_btn_color = QColor("#F29F05")
        toggle_layout.addRow("Active State:", self.parent.ui_active_btn_color_btn)

        self.parent.ui_inactive_btn_color_btn = QPushButton()
        self.parent.ui_inactive_btn_color_btn.setFixedSize(80, 25)
        self.parent.ui_inactive_btn_color_btn.clicked.connect(lambda: self._choose_color('ui_inactive'))
        self.parent.ui_inactive_btn_color = QColor("#2A2D33")
        toggle_layout.addRow("Inactive State:", self.parent.ui_inactive_btn_color_btn)

        # Hover State Colors (Issue #26)
        self.parent.ui_btn_hover_border_color_btn = QPushButton()
        self.parent.ui_btn_hover_border_color_btn.setFixedSize(80, 25)
        self.parent.ui_btn_hover_border_color_btn.clicked.connect(lambda: self._choose_color('ui_btn_hover_border'))
        self.parent.ui_btn_hover_border_color = QColor("#F29F05")
        toggle_layout.addRow("Hover Border Color:", self.parent.ui_btn_hover_border_color_btn)

        self.parent.ui_btn_hover_text_color_btn = QPushButton()
        self.parent.ui_btn_hover_text_color_btn.setFixedSize(80, 25)
        self.parent.ui_btn_hover_text_color_btn.clicked.connect(lambda: self._choose_color('ui_btn_hover_text'))
        self.parent.ui_btn_hover_text_color = QColor("#F29F05")
        toggle_layout.addRow("Hover Text Color:", self.parent.ui_btn_hover_text_color_btn)
        
        layout.addWidget(toggle_group)

        # 5. Chart Appearance (Moved from General)
        chart_group = QGroupBox("Chart Appearance")
        chart_layout = QFormLayout(chart_group)
        
        # Candle colors row
        candle_layout = QHBoxLayout()
        self.parent.bullish_color_btn = QPushButton()
        self.parent.bullish_color_btn.setFixedSize(60, 25)
        self.parent.bullish_color_btn.clicked.connect(lambda: self._choose_color('bullish'))
        self.parent.bullish_color = QColor("#26a69a")
        self._update_color_button(self.parent.bullish_color_btn, self.parent.bullish_color)
        
        self.parent.bearish_color_btn = QPushButton()
        self.parent.bearish_color_btn.setFixedSize(60, 25)
        self.parent.bearish_color_btn.clicked.connect(lambda: self._choose_color('bearish'))
        self.parent.bearish_color = QColor("#ef5350")
        self._update_color_button(self.parent.bearish_color_btn, self.parent.bearish_color)
        
        candle_layout.addWidget(QLabel("Bullish:"))
        candle_layout.addWidget(self.parent.bullish_color_btn)
        candle_layout.addSpacing(10)
        candle_layout.addWidget(QLabel("Bearish:"))
        candle_layout.addWidget(self.parent.bearish_color_btn)
        chart_layout.addRow("Candle Colors:", candle_layout)

        # Chart Background
        self.parent.background_color_btn = QPushButton()
        self.parent.background_color_btn.setFixedSize(80, 25)
        self.parent.background_color_btn.clicked.connect(lambda: self._choose_color('background'))
        self.parent.background_color = QColor("#1e1e1e")
        self._update_color_button(self.parent.background_color_btn, self.parent.background_color)
        chart_layout.addRow("Chart Background:", self.parent.background_color_btn)

        # Background Image Selection
        bg_image_layout = QHBoxLayout()
        self.parent.background_image_path = ""
        self.parent.background_image_label = QLabel("Kein Bild ausgewählt")
        self.parent.background_image_label.setStyleSheet("color: #888; font-style: italic;")
        bg_image_layout.addWidget(self.parent.background_image_label)

        self.parent.background_image_btn = QPushButton("Bild wählen...")
        self.parent.background_image_btn.clicked.connect(self._choose_background_image)
        bg_image_layout.addWidget(self.parent.background_image_btn)

        self.parent.background_image_clear_btn = QPushButton("✕")
        self.parent.background_image_clear_btn.setFixedWidth(30)
        self.parent.background_image_clear_btn.clicked.connect(self._clear_background_image)
        bg_image_layout.addWidget(self.parent.background_image_clear_btn)
        chart_layout.addRow("Hintergrundbild:", bg_image_layout)

        # Background Image Opacity Slider
        opacity_layout = QHBoxLayout()
        self.parent.background_image_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.background_image_opacity_slider.setRange(0, 100)
        self.parent.background_image_opacity_slider.setValue(30)
        self.parent.background_image_opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.parent.background_image_opacity_slider.setTickInterval(10)
        self.parent.background_image_opacity_slider.valueChanged.connect(self._update_opacity_label)
        opacity_layout.addWidget(self.parent.background_image_opacity_slider)

        self.parent.background_image_opacity_label = QLabel("30%")
        self.parent.background_image_opacity_label.setFixedWidth(40)
        self.parent.background_image_opacity_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        opacity_layout.addWidget(self.parent.background_image_opacity_label)
        chart_layout.addRow("Transparenz Bild:", opacity_layout)

        # Candle Border Radius
        radius_layout = QHBoxLayout()
        self.parent.candle_border_radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.candle_border_radius_slider.setRange(0, 10)
        self.parent.candle_border_radius_slider.setValue(0)
        self.parent.candle_border_radius_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.parent.candle_border_radius_slider.setTickInterval(1)
        self.parent.candle_border_radius_slider.valueChanged.connect(self._update_border_radius_label)
        radius_layout.addWidget(self.parent.candle_border_radius_slider)

        self.parent.candle_border_radius_label = QLabel("0 px")
        self.parent.candle_border_radius_label.setFixedWidth(40)
        self.parent.candle_border_radius_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        radius_layout.addWidget(self.parent.candle_border_radius_label)
        chart_layout.addRow("Kerzen Abrundung:", radius_layout)

        layout.addWidget(chart_group)

        # 6. Icon Collection
        icon_group = QGroupBox("Icon Collection")
        icon_layout = QFormLayout(icon_group)

        # Icon Directory Selection
        icon_dir_layout = QHBoxLayout()
        self.parent.icon_dir_path = ""
        self.parent.icon_dir_label = QLabel("Standard (Assets)")
        self.parent.icon_dir_label.setStyleSheet("color: #888; font-style: italic;")
        icon_dir_layout.addWidget(self.parent.icon_dir_label)

        self.parent.icon_dir_btn = QPushButton("Ordner wählen...")
        self.parent.icon_dir_btn.clicked.connect(self._choose_icon_dir)
        icon_dir_layout.addWidget(self.parent.icon_dir_btn)

        self.parent.icon_dir_clear_btn = QPushButton("✕")
        self.parent.icon_dir_clear_btn.setFixedWidth(30)
        self.parent.icon_dir_clear_btn.clicked.connect(self._clear_icon_dir)
        icon_dir_layout.addWidget(self.parent.icon_dir_clear_btn)
        icon_layout.addRow("Icon Verzeichnis:", icon_dir_layout)

        # Force white icons
        self.parent.icon_force_white_check = QCheckBox("Icons zu weiß invertieren")
        self.parent.icon_force_white_check.setToolTip("Invertiert schwarze Icons zu weiß mit transparentem Hintergrund")
        self.parent.icon_force_white_check.setChecked(True)
        icon_layout.addRow(self.parent.icon_force_white_check)

        layout.addWidget(icon_group)

        layout.addStretch()

        return tab

    def _choose_icon_dir(self) -> None:
        """Open directory dialog to choose icon collection path."""
        dir_path = QFileDialog.getExistingDirectory(
            self.parent,
            "Icon Verzeichnis auswählen",
            ""
        )

        if dir_path:
            # Nutze vollen absoluten Pfad
            self.parent.icon_dir_path = os.path.abspath(dir_path)
            self.parent.icon_dir_label.setText(self.parent.icon_dir_path)
            self.parent.icon_dir_label.setStyleSheet("color: #F29F05; font-size: 10px;")
            self.parent.icon_dir_label.setToolTip(self.parent.icon_dir_path)

    def _clear_icon_dir(self) -> None:
        """Clear icon directory selection."""
        self.parent.icon_dir_path = ""
        self.parent.icon_dir_label.setText("Standard (Assets)")
        self.parent.icon_dir_label.setStyleSheet("color: #888; font-style: italic;")

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
        elif color_type == 'ui_bg':
            current_color = self.parent.ui_bg_color
            btn = self.parent.ui_bg_color_btn
        elif color_type == 'ui_btn':
            current_color = self.parent.ui_btn_color
            btn = self.parent.ui_btn_color_btn
        elif color_type == 'ui_dropdown':
            current_color = self.parent.ui_dropdown_color
            btn = self.parent.ui_dropdown_color_btn
        elif color_type == 'ui_edit':
            current_color = self.parent.ui_edit_color
            btn = self.parent.ui_edit_color_btn
        elif color_type == 'ui_edit_text':
            current_color = self.parent.ui_edit_text_color
            btn = self.parent.ui_edit_text_color_btn
        elif color_type == 'ui_active':
            current_color = self.parent.ui_active_btn_color
            btn = self.parent.ui_active_btn_color_btn
        elif color_type == 'ui_inactive':
            current_color = self.parent.ui_inactive_btn_color
            btn = self.parent.ui_inactive_btn_color_btn
        elif color_type == 'ui_btn_hover_border':
            current_color = self.parent.ui_btn_hover_border_color
            btn = self.parent.ui_btn_hover_border_color_btn
        elif color_type == 'ui_btn_hover_text':
            current_color = self.parent.ui_btn_hover_text_color
            btn = self.parent.ui_btn_hover_text_color_btn
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
            elif color_type == 'ui_bg':
                self.parent.ui_bg_color = color
            elif color_type == 'ui_btn':
                self.parent.ui_btn_color = color
            elif color_type == 'ui_dropdown':
                self.parent.ui_dropdown_color = color
            elif color_type == 'ui_edit':
                self.parent.ui_edit_color = color
            elif color_type == 'ui_edit_text':
                self.parent.ui_edit_text_color = color
            elif color_type == 'ui_active':
                self.parent.ui_active_btn_color = color
            elif color_type == 'ui_inactive':
                self.parent.ui_inactive_btn_color = color
            elif color_type == 'ui_btn_hover_border':
                self.parent.ui_btn_hover_border_color = color
            elif color_type == 'ui_btn_hover_text':
                self.parent.ui_btn_hover_text_color = color
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
        if button is None:
            return
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
