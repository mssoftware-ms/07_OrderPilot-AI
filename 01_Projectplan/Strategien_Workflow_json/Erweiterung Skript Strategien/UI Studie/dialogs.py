"""
CEL Editor - Dialog Widgets
Export, Import, Settings und Pattern Details Dialoge
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QTabWidget,
    QFileDialog, QListWidget, QListWidgetItem, QScrollArea,
    QGridLayout, QRadioButton, QButtonGroup, QProgressBar,
    QPlainTextEdit, QSizePolicy, QWidget, QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class BaseDialog(QDialog):
    """Basis-Dialog mit gemeinsamen Styles"""
    
    def __init__(self, title="Dialog", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #0d0f12;
            }
            QLabel {
                color: #e8eaed;
            }
            QGroupBox {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 8px;
                margin-top: 16px;
                padding: 16px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                top: 0px;
                color: #00d9ff;
                font-size: 11px;
                text-transform: uppercase;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #1a1d21;
                border: 1px solid #2d333b;
                border-radius: 6px;
                padding: 10px;
                color: #e8eaed;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #00d9ff;
            }
            QComboBox {
                background-color: #1a1d21;
                border: 1px solid #2d333b;
                border-radius: 6px;
                padding: 10px;
                color: #e8eaed;
            }
            QCheckBox {
                color: #e8eaed;
            }
            QPushButton {
                background-color: #1e2329;
                border: 1px solid #2d333b;
                border-radius: 6px;
                padding: 10px 20px;
                color: #e8eaed;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2d333b;
            }
        """)


class ExportDialog(BaseDialog):
    """
    Dialog zum Exportieren von Regeln als JSON RulePack
    """
    
    export_requested = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__("Export Rules", parent)
        self.setMinimumSize(600, 700)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("📤 Export RulePack")
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #e8eaed;
        """)
        layout.addWidget(header)
        
        desc = QLabel("Export your patterns and rules as a JSON RulePack "
                     "compatible with TradingBot and Entry Analyzer.")
        desc.setStyleSheet("color: #9aa0a6; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # File Settings
        file_group = QGroupBox("File Settings")
        file_layout = QVBoxLayout(file_group)
        
        # Filename
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Filename:"))
        self.filename_input = QLineEdit("my_strategy_rulepack")
        name_row.addWidget(self.filename_input)
        name_row.addWidget(QLabel(".json"))
        file_layout.addLayout(name_row)
        
        # Output Path
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Output Path:"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select output directory...")
        path_row.addWidget(self.path_input)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        path_row.addWidget(browse_btn)
        file_layout.addLayout(path_row)
        
        layout.addWidget(file_group)
        
        # Export Content
        content_group = QGroupBox("Export Content")
        content_layout = QVBoxLayout(content_group)
        
        self.entry_check = QCheckBox("Entry Rules (3 rules)")
        self.entry_check.setChecked(True)
        content_layout.addWidget(self.entry_check)
        
        self.exit_check = QCheckBox("Exit Rules (1 rule)")
        self.exit_check.setChecked(True)
        content_layout.addWidget(self.exit_check)
        
        self.risk_check = QCheckBox("Risk Rules (2 rules)")
        self.risk_check.setChecked(True)
        content_layout.addWidget(self.risk_check)
        
        self.stop_check = QCheckBox("Stop Update Rules (1 rule)")
        self.stop_check.setChecked(True)
        content_layout.addWidget(self.stop_check)
        
        self.indicators_check = QCheckBox("Include Indicator Definitions")
        self.indicators_check.setChecked(True)
        content_layout.addWidget(self.indicators_check)
        
        self.params_check = QCheckBox("Include Configuration Parameters")
        self.params_check.setChecked(True)
        content_layout.addWidget(self.params_check)
        
        layout.addWidget(content_group)
        
        # Format Options
        format_group = QGroupBox("Format Options")
        format_layout = QVBoxLayout(format_group)
        
        self.pretty_check = QCheckBox("Pretty Print (human readable)")
        self.pretty_check.setChecked(True)
        format_layout.addWidget(self.pretty_check)
        
        self.comments_check = QCheckBox("Include Comments & Documentation")
        self.comments_check.setChecked(True)
        format_layout.addWidget(self.comments_check)
        
        self.validate_check = QCheckBox("Validate Before Export")
        self.validate_check.setChecked(True)
        format_layout.addWidget(self.validate_check)
        
        layout.addWidget(format_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QPlainTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'JetBrains Mono';
                font-size: 11px;
                background-color: #0d0f12;
            }
        """)
        self.preview_text.setPlainText('''{
  "entry": [
    {
      "id": "bullish_engulfing_long",
      "expr": "(close[-2] < open[-2]) && (close[-1] > open[-1]) && ..."
    }
  ],
  "exit": [...],
  "indicators": {...}
}''')
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d9ff;
                color: #0d0f12;
                border: none;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #33e1ff;
            }
        """)
        export_btn.clicked.connect(self.accept)
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)


class ImportDialog(BaseDialog):
    """
    Dialog zum Importieren von RulePacks
    """
    
    import_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("Import Rules", parent)
        self.setMinimumSize(600, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("📥 Import RulePack")
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: #e8eaed;")
        layout.addWidget(header)
        
        # File Selection
        file_group = QGroupBox("Select File")
        file_layout = QVBoxLayout(file_group)
        
        # Drag & Drop Area
        drop_area = QFrame()
        drop_area.setMinimumHeight(150)
        drop_area.setStyleSheet("""
            QFrame {
                background-color: #1a1d21;
                border: 2px dashed #2d333b;
                border-radius: 12px;
            }
            QFrame:hover {
                border-color: #00d9ff;
            }
        """)
        
        drop_layout = QVBoxLayout(drop_area)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        drop_icon = QLabel("📁")
        drop_icon.setStyleSheet("font-size: 40px;")
        drop_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(drop_icon)
        
        drop_text = QLabel("Drag & Drop JSON file here\nor click to browse")
        drop_text.setStyleSheet("color: #9aa0a6; font-size: 13px;")
        drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(drop_text)
        
        file_layout.addWidget(drop_area)
        
        # File Path
        path_row = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("No file selected...")
        path_row.addWidget(self.file_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        path_row.addWidget(browse_btn)
        file_layout.addLayout(path_row)
        
        layout.addWidget(file_group)
        
        # Detected Content
        content_group = QGroupBox("Detected Content")
        content_layout = QVBoxLayout(content_group)
        
        self.content_list = QListWidget()
        self.content_list.setStyleSheet("""
            QListWidget {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #1e2329;
            }
        """)
        
        demo_items = [
            "✓ Entry Rules: 3 rules found",
            "✓ Exit Rules: 1 rule found",
            "✓ Risk Rules: 2 rules found",
            "✓ Indicators: EMA34, ATR14 defined",
            "✓ Parameters: 5 config values",
        ]
        for item in demo_items:
            self.content_list.addItem(QListWidgetItem(item))
            
        content_layout.addWidget(self.content_list)
        layout.addWidget(content_group)
        
        # Import Options
        options_group = QGroupBox("Import Options")
        options_layout = QVBoxLayout(options_group)
        
        self.merge_radio = QRadioButton("Merge with existing rules")
        self.replace_radio = QRadioButton("Replace all existing rules")
        self.replace_radio.setChecked(True)
        
        options_layout.addWidget(self.merge_radio)
        options_layout.addWidget(self.replace_radio)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        import_btn = QPushButton("Import")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #00c853;
                color: #0d0f12;
                border: none;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #00e676;
            }
        """)
        import_btn.clicked.connect(self.accept)
        btn_layout.addWidget(import_btn)
        
        layout.addLayout(btn_layout)
        
    def browse_file(self):
        """Öffnet File Browser"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select RulePack", "", "JSON Files (*.json)"
        )
        if filename:
            self.file_input.setText(filename)


class SettingsDialog(BaseDialog):
    """
    Editor Einstellungen Dialog
    """
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setMinimumSize(700, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border-bottom: 1px solid #1e2329;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        title = QLabel("⚙️ Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #e8eaed;")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Content with Tabs
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        
        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border-right: 1px solid #1e2329;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(4)
        
        sections = [
            ("🎨", "Appearance"),
            ("✏️", "Editor"),
            ("🤖", "AI Assistant"),
            ("📊", "Chart"),
            ("💾", "Data & Export"),
            ("⌨️", "Shortcuts"),
        ]
        
        self.section_buttons = []
        for icon, name in sections:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    text-align: left;
                    padding: 12px 16px;
                    border-radius: 6px;
                    color: #9aa0a6;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #1e2329;
                    color: #e8eaed;
                }
                QPushButton:checked {
                    background-color: #00d9ff20;
                    color: #00d9ff;
                }
            """)
            sidebar_layout.addWidget(btn)
            self.section_buttons.append(btn)
        
        self.section_buttons[0].setChecked(True)
        sidebar_layout.addStretch()
        content.addWidget(sidebar)
        
        # Settings Content
        settings_area = QScrollArea()
        settings_area.setWidgetResizable(True)
        settings_area.setStyleSheet("""
            QScrollArea {
                background-color: #0d0f12;
                border: none;
            }
        """)
        
        settings_content = QWidget()
        settings_layout = QVBoxLayout(settings_content)
        settings_layout.setContentsMargins(24, 24, 24, 24)
        settings_layout.setSpacing(20)
        
        # Appearance Section (Demo)
        appearance = QGroupBox("Theme")
        app_layout = QVBoxLayout(appearance)
        
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Color Theme:"))
        theme_combo = QComboBox()
        theme_combo.addItems(["Dark", "Dark White", "Light"])
        theme_row.addWidget(theme_combo)
        app_layout.addLayout(theme_row)
        
        accent_row = QHBoxLayout()
        accent_row.addWidget(QLabel("Accent Color:"))
        accent_combo = QComboBox()
        accent_combo.addItems(["Cyan", "Green", "Purple", "Orange"])
        accent_row.addWidget(accent_combo)
        app_layout.addLayout(accent_row)
        
        settings_layout.addWidget(appearance)
        
        # Editor Section
        editor = QGroupBox("Code Editor")
        editor_layout = QVBoxLayout(editor)
        
        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font:"))
        font_combo = QComboBox()
        font_combo.addItems(["JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas"])
        font_row.addWidget(font_combo)
        editor_layout.addLayout(font_row)
        
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Font Size:"))
        size_spin = QSpinBox()
        size_spin.setRange(8, 24)
        size_spin.setValue(13)
        size_spin.setSuffix(" px")
        size_row.addWidget(size_spin)
        editor_layout.addLayout(size_row)
        
        editor_layout.addWidget(QCheckBox("Show Line Numbers"))
        editor_layout.addWidget(QCheckBox("Enable Auto-Complete"))
        editor_layout.addWidget(QCheckBox("Highlight Current Line"))
        
        settings_layout.addWidget(editor)
        
        # AI Section
        ai_group = QGroupBox("AI Assistant")
        ai_layout = QVBoxLayout(ai_group)
        
        ai_layout.addWidget(QCheckBox("Enable AI Suggestions"))
        ai_layout.addWidget(QCheckBox("Auto-analyze Patterns"))
        ai_layout.addWidget(QCheckBox("Show Similarity Search Results"))
        
        api_row = QHBoxLayout()
        api_row.addWidget(QLabel("API Endpoint:"))
        api_input = QLineEdit()
        api_input.setPlaceholderText("https://api.anthropic.com/...")
        api_row.addWidget(api_input)
        ai_layout.addLayout(api_row)
        
        settings_layout.addWidget(ai_group)
        
        settings_layout.addStretch()
        
        settings_area.setWidget(settings_content)
        content.addWidget(settings_area)
        
        content_widget = QWidget()
        content_widget.setLayout(content)
        layout.addWidget(content_widget)
        
        # Footer Buttons
        footer = QFrame()
        footer.setFixedHeight(70)
        footer.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border-top: 1px solid #1e2329;
            }
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 0, 24, 0)
        
        restore_btn = QPushButton("Restore Defaults")
        restore_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #ff3d71;
                color: #ff3d71;
            }
            QPushButton:hover {
                background: #ff3d7120;
            }
        """)
        footer_layout.addWidget(restore_btn)
        
        footer_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d9ff;
                color: #0d0f12;
                border: none;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #33e1ff;
            }
        """)
        save_btn.clicked.connect(self.accept)
        footer_layout.addWidget(save_btn)
        
        layout.addWidget(footer)


class PatternDetailsDialog(BaseDialog):
    """
    Dialog zur Anzeige von Pattern-Details
    """
    
    def __init__(self, pattern_data=None, parent=None):
        super().__init__("Pattern Details", parent)
        self.pattern_data = pattern_data or {}
        self.setMinimumSize(700, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header with Pattern Name
        header = QHBoxLayout()
        
        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 32px;")
        header.addWidget(icon)
        
        header_text = QVBoxLayout()
        name = QLabel("Bullish Engulfing")
        name.setStyleSheet("font-size: 20px; font-weight: 700; color: #e8eaed;")
        header_text.addWidget(name)
        
        tags = QLabel("2-Bar Reversal Pattern • Candlestick • Bullish")
        tags.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        header_text.addWidget(tags)
        
        header.addLayout(header_text)
        header.addStretch()
        
        # Stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #00c85320;
                border: 1px solid #00c85360;
                border-radius: 8px;
                padding: 8px 16px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(16)
        
        win_rate = QLabel("Win Rate: 68%")
        win_rate.setStyleSheet("color: #00c853; font-weight: 600;")
        stats_layout.addWidget(win_rate)
        
        avg_rr = QLabel("Avg R:R: 1.8")
        avg_rr.setStyleSheet("color: #00c853; font-weight: 600;")
        stats_layout.addWidget(avg_rr)
        
        header.addWidget(stats_frame)
        
        layout.addLayout(header)
        
        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        desc_text = QLabel(
            "A bullish engulfing pattern is a two-candle reversal pattern. "
            "The first candle is a small bearish candle, followed by a large "
            "bullish candle that completely engulfs the first candle's body. "
            "This pattern signals a potential reversal from a downtrend to an uptrend."
        )
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("color: #b8bcc4; font-size: 13px; line-height: 1.6;")
        desc_layout.addWidget(desc_text)
        
        layout.addWidget(desc_group)
        
        # Pattern Rules
        rules_group = QGroupBox("Pattern Rules")
        rules_layout = QVBoxLayout(rules_group)
        
        rules = [
            ("1.", "Candle[-2] is bearish (close < open)", "✓"),
            ("2.", "Candle[-1] is bullish (close > open)", "✓"),
            ("3.", "High[-1] > High[-2] (higher high)", "✓"),
            ("4.", "Low[-1] < Low[-2] (lower low)", "✓"),
            ("5.", "Body[-1] > Body[-2] (engulfing)", "✓"),
        ]
        
        for num, rule, status in rules:
            row = QHBoxLayout()
            
            num_label = QLabel(num)
            num_label.setStyleSheet("color: #00d9ff; font-weight: 600; width: 30px;")
            num_label.setFixedWidth(30)
            row.addWidget(num_label)
            
            rule_label = QLabel(rule)
            rule_label.setStyleSheet("color: #e8eaed; font-family: 'JetBrains Mono'; font-size: 12px;")
            row.addWidget(rule_label)
            
            row.addStretch()
            
            status_label = QLabel(status)
            status_label.setStyleSheet("color: #00c853; font-size: 14px;")
            row.addWidget(status_label)
            
            rules_layout.addLayout(row)
        
        layout.addWidget(rules_group)
        
        # CEL Expression
        cel_group = QGroupBox("CEL Expression")
        cel_layout = QVBoxLayout(cel_group)
        
        cel_code = QPlainTextEdit()
        cel_code.setReadOnly(True)
        cel_code.setMaximumHeight(120)
        cel_code.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d0f12;
                font-family: 'JetBrains Mono';
                font-size: 12px;
            }
        """)
        cel_code.setPlainText(
            "(close[-2] < open[-2])  // Candle 1 bearish\n"
            "&& (close[-1] > open[-1])  // Candle 2 bullish\n"
            "&& (high[-1] > high[-2] && low[-1] < low[-2])  // Engulfing"
        )
        cel_layout.addWidget(cel_code)
        
        layout.addWidget(cel_group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        
        use_btn = QPushButton("Use This Pattern")
        use_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d9ff;
                color: #0d0f12;
                border: none;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #33e1ff;
            }
        """)
        use_btn.clicked.connect(self.accept)
        btn_layout.addWidget(use_btn)
        
        layout.addLayout(btn_layout)


class ValidationResultDialog(BaseDialog):
    """
    Dialog zur Anzeige von Validierungsergebnissen
    """
    
    def __init__(self, is_valid=True, errors=None, parent=None):
        super().__init__("Validation Result", parent)
        self.is_valid = is_valid
        self.errors = errors or []
        self.setMinimumSize(500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Status Icon & Message
        status_frame = QFrame()
        if self.is_valid:
            status_frame.setStyleSheet("""
                QFrame {
                    background-color: #00c85320;
                    border: 1px solid #00c85360;
                    border-radius: 12px;
                    padding: 24px;
                }
            """)
            icon = "✓"
            title = "Validation Successful"
            color = "#00c853"
        else:
            status_frame.setStyleSheet("""
                QFrame {
                    background-color: #ff3d7120;
                    border: 1px solid #ff3d7160;
                    border-radius: 12px;
                    padding: 24px;
                }
            """)
            icon = "✗"
            title = "Validation Failed"
            color = "#ff3d71"
            
        status_layout = QVBoxLayout(status_frame)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 48px; color: {color};")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {color};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(title_label)
        
        layout.addWidget(status_frame)
        
        # Details
        if self.is_valid:
            details = QLabel("All CEL expressions are syntactically correct and "
                           "all required indicators are defined.")
            details.setWordWrap(True)
            details.setStyleSheet("color: #9aa0a6; font-size: 13px;")
            layout.addWidget(details)
        else:
            errors_group = QGroupBox("Errors Found")
            errors_layout = QVBoxLayout(errors_group)
            
            for err in self.errors:
                err_label = QLabel(f"• {err}")
                err_label.setStyleSheet("color: #ff3d71; font-size: 12px;")
                errors_layout.addWidget(err_label)
            
            layout.addWidget(errors_group)
        
        layout.addStretch()
        
        # Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(100)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
