"""
CEL Editor - Main Window
========================
Hauptfenster mit Dock-Widget-Layout für den interaktiven CEL-Editor.
Design-Studie ohne Funktionalität.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget,
    QToolBar, QStatusBar, QMenuBar, QMenu, QSplitter, QTabWidget,
    QLabel, QPushButton, QComboBox, QFrame, QStackedWidget,
    QSizePolicy, QSpacerItem, QToolButton, QButtonGroup
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QFont, QKeySequence

# Import widgets (direkte Imports - alle Module im selben Verzeichnis)
from pattern_builder import PatternBuilderCanvas, CandlePropertiesPanel
from cel_editor import CELEditorWidget, CELSnippetsPanel
from ai_assistant import AIAssistantPanel, PatternRecognitionPanel
from panels import PatternLibraryPanel, FilterPanel, StrategyTemplatesPanel

# Import dialogs
from dialogs import (
    ExportDialog, ImportDialog, SettingsDialog,
    PatternDetailsDialog, ValidationResultDialog
)

# Import themes
from dark_theme import DARK_THEME, DARK_COLORS
from dark_white_theme import DARK_WHITE_THEME, DARK_WHITE_COLORS


class MainToolBar(QToolBar):
    """Hauptwerkzeugleiste mit essentiellen Aktionen"""
    
    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setObjectName("MainToolBar")
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        self._setup_ui()
    
    def _setup_ui(self):
        # Logo/Brand
        brand_label = QLabel("  CEL EDITOR  ")
        brand_label.setObjectName("brand_label")
        brand_label.setStyleSheet("""
            QLabel#brand_label {
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 14px;
                font-weight: bold;
                color: #00d9ff;
                padding: 4px 12px;
                border-right: 1px solid #2a2d35;
                margin-right: 8px;
            }
        """)
        self.addWidget(brand_label)
        
        # Strategy Selector
        strategy_combo = QComboBox()
        strategy_combo.setMinimumWidth(200)
        strategy_combo.addItems([
            "📁 Neue Strategie",
            "── Kürzlich ──",
            "📊 Bullish Engulfing + EMA",
            "📊 SMC 3-Act Model",
            "📊 Volatility Squeeze Entry",
            "📊 Mean Reversion Setup"
        ])
        strategy_combo.setCurrentIndex(2)
        self.addWidget(strategy_combo)
        
        self.addSeparator()
        
        # File Actions
        new_btn = QToolButton()
        new_btn.setText("  Neu")
        new_btn.setIcon(QIcon())  # Placeholder
        new_btn.setToolTip("Neue Strategie erstellen (Ctrl+N)")
        self.addWidget(new_btn)
        
        open_btn = QToolButton()
        open_btn.setText("  Öffnen")
        open_btn.setToolTip("Strategie öffnen (Ctrl+O)")
        self.addWidget(open_btn)
        
        save_btn = QToolButton()
        save_btn.setText("  Speichern")
        save_btn.setToolTip("Strategie speichern (Ctrl+S)")
        save_btn.setProperty("class", "primary")
        self.addWidget(save_btn)
        
        self.addSeparator()
        
        # Edit Actions
        undo_btn = QToolButton()
        undo_btn.setText("↶")
        undo_btn.setToolTip("Rückgängig (Ctrl+Z)")
        self.addWidget(undo_btn)
        
        redo_btn = QToolButton()
        redo_btn.setText("↷")
        redo_btn.setToolTip("Wiederholen (Ctrl+Y)")
        self.addWidget(redo_btn)
        
        self.addSeparator()
        
        # Validation & Run
        validate_btn = QToolButton()
        validate_btn.setText("  Validieren")
        validate_btn.setToolTip("Alle Regeln validieren (F5)")
        self.addWidget(validate_btn)
        
        backtest_btn = QToolButton()
        backtest_btn.setText("  Backtest")
        backtest_btn.setProperty("class", "success")
        backtest_btn.setToolTip("Backtest starten (F6)")
        self.addWidget(backtest_btn)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)
        
        # Timeframe Selector
        tf_label = QLabel("Timeframe: ")
        tf_label.setStyleSheet("color: #8b8f98;")
        self.addWidget(tf_label)
        
        tf_combo = QComboBox()
        tf_combo.setMinimumWidth(80)
        tf_combo.addItems(["1m", "5m", "15m", "1H", "4H", "1D", "1W"])
        tf_combo.setCurrentIndex(3)
        self.addWidget(tf_combo)
        
        self.addSeparator()
        
        # Theme Toggle
        theme_btn = QToolButton()
        theme_btn.setText("🌙")
        theme_btn.setToolTip("Theme wechseln")
        theme_btn.setCheckable(True)
        self.addWidget(theme_btn)
        
        # Settings
        settings_btn = QToolButton()
        settings_btn.setText("⚙")
        settings_btn.setToolTip("Einstellungen")
        self.addWidget(settings_btn)


class StatusBarWidget(QStatusBar):
    """Erweiterte Statusleiste mit Trading-Infos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        # Validation Status
        self.validation_label = QLabel("✓ Alle Regeln valid")
        self.validation_label.setStyleSheet("""
            QLabel {
                color: #00c853;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                padding: 2px 8px;
                background: rgba(0, 200, 83, 0.1);
                border-radius: 3px;
            }
        """)
        self.addWidget(self.validation_label)
        
        # Rule Count
        self.rule_count = QLabel("│  4 Entry  │  2 Exit  │  3 Risk  │  1 Stop")
        self.rule_count.setStyleSheet("""
            QLabel {
                color: #6c7086;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                padding: 0 8px;
            }
        """)
        self.addWidget(self.rule_count)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)
        
        # AI Status
        self.ai_status = QLabel("🤖 AI: Bereit")
        self.ai_status.setStyleSheet("""
            QLabel {
                color: #00d9ff;
                font-size: 11px;
                padding: 0 8px;
            }
        """)
        self.addPermanentWidget(self.ai_status)
        
        # Connection Status
        self.connection_label = QLabel("● Verbunden")
        self.connection_label.setStyleSheet("""
            QLabel {
                color: #00c853;
                font-size: 11px;
                padding: 0 8px;
            }
        """)
        self.addPermanentWidget(self.connection_label)
        
        # Version
        version_label = QLabel("v2.0.0-beta")
        version_label.setStyleSheet("""
            QLabel {
                color: #4a4d55;
                font-size: 10px;
                padding: 0 8px;
            }
        """)
        self.addPermanentWidget(version_label)


class ViewModeSelector(QFrame):
    """Ansichtsmodus-Umschalter für die zentrale Arbeitsfläche"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ViewModeSelector")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        self.btn_group = QButtonGroup(self)
        
        modes = [
            ("🎨 Pattern Builder", True),
            ("📝 Code Editor", False),
            ("📊 Chart View", False),
            ("⚡ Split View", False)
        ]
        
        for text, checked in modes:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn.setMinimumWidth(120)
            self.btn_group.addButton(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Zoom Controls
        zoom_out = QPushButton("−")
        zoom_out.setFixedSize(28, 28)
        layout.addWidget(zoom_out)
        
        zoom_label = QLabel("100%")
        zoom_label.setStyleSheet("color: #8b8f98; min-width: 45px; text-align: center;")
        layout.addWidget(zoom_label)
        
        zoom_in = QPushButton("+")
        zoom_in.setFixedSize(28, 28)
        layout.addWidget(zoom_in)
        
        zoom_fit = QPushButton("Fit")
        zoom_fit.setFixedSize(40, 28)
        layout.addWidget(zoom_fit)
        
        self.setStyleSheet("""
            QFrame#ViewModeSelector {
                background: #14161a;
                border-bottom: 1px solid #2a2d35;
            }
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                color: #8b8f98;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.05);
                color: #e1e3e8;
            }
            QPushButton:checked {
                background: #1e2128;
                border: 1px solid #00d9ff;
                color: #00d9ff;
            }
        """)


class CentralWorkspace(QWidget):
    """Zentrale Arbeitsfläche mit Pattern Builder und Code Editor"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # View Mode Selector
        self.view_selector = ViewModeSelector()
        layout.addWidget(self.view_selector)
        
        # Main Splitter (Vertical)
        self.main_splitter = QSplitter(Qt.Vertical)
        
        # Top: Pattern Builder or Chart
        self.pattern_builder = PatternBuilderCanvas()
        self.main_splitter.addWidget(self.pattern_builder)
        
        # Bottom: CEL Editor
        self.cel_editor = CELEditorWidget()
        self.main_splitter.addWidget(self.cel_editor)
        
        # Set proportions (60% builder, 40% editor)
        self.main_splitter.setSizes([600, 400])
        self.main_splitter.setHandleWidth(4)
        
        layout.addWidget(self.main_splitter)


class LeftDockContent(QWidget):
    """Linker Dock-Bereich: Pattern Library, Templates, Filter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Pattern Library Tab
        self.pattern_library = PatternLibraryPanel()
        self.tabs.addTab(self.pattern_library, "📚 Patterns")
        
        # Strategy Templates Tab
        self.templates = StrategyTemplatesPanel()
        self.tabs.addTab(self.templates, "📋 Vorlagen")
        
        # Filter Panel Tab
        self.filters = FilterPanel()
        self.tabs.addTab(self.filters, "🔧 Filter")
        
        # Code Snippets Tab
        self.snippets = CELSnippetsPanel()
        self.tabs.addTab(self.snippets, "✂️ Snippets")
        
        layout.addWidget(self.tabs)


class RightDockContent(QWidget):
    """Rechter Dock-Bereich: Properties, AI Assistant, Pattern Recognition"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Splitter for top/bottom panels
        splitter = QSplitter(Qt.Vertical)
        
        # Top: Properties Panel
        top_tabs = QTabWidget()
        top_tabs.setDocumentMode(True)
        
        self.properties_panel = CandlePropertiesPanel()
        top_tabs.addTab(self.properties_panel, "🔧 Properties")
        
        # Rule Overview Panel
        self.rule_overview = self._create_rule_overview()
        top_tabs.addTab(self.rule_overview, "📋 Regeln")
        
        splitter.addWidget(top_tabs)
        
        # Bottom: AI Assistant
        bottom_tabs = QTabWidget()
        bottom_tabs.setDocumentMode(True)
        
        self.ai_assistant = AIAssistantPanel()
        bottom_tabs.addTab(self.ai_assistant, "🤖 AI Assistent")
        
        self.pattern_recognition = PatternRecognitionPanel()
        bottom_tabs.addTab(self.pattern_recognition, "🔍 Erkennung")
        
        splitter.addWidget(bottom_tabs)
        
        # Set proportions
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter)
    
    def _create_rule_overview(self):
        """Regel-Übersichts-Panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("Aktive Regel-Übersicht")
        header.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #e1e3e8;
            padding-bottom: 4px;
            border-bottom: 1px solid #2a2d35;
        """)
        layout.addWidget(header)
        
        # Rule Categories
        categories = [
            ("Entry-Regeln", "#00c853", [
                "✓ Bullish Engulfing + Volume",
                "✓ Inside Bar Breakout",
                "○ SMC Orderblock Entry"
            ]),
            ("Exit-Regeln", "#ffab00", [
                "✓ Take Profit @ 2R",
                "○ Evening Star Exit"
            ]),
            ("Risk-Regeln", "#ff3d71", [
                "✓ Max Daily Loss Check",
                "✓ Volatility Block",
                "✓ No Trade in Squeeze"
            ]),
            ("Stop-Regeln", "#00d9ff", [
                "✓ Trailing Stop ATR-based"
            ])
        ]
        
        for cat_name, color, rules in categories:
            cat_frame = QFrame()
            cat_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba(30, 33, 40, 0.5);
                    border: 1px solid {color}33;
                    border-left: 3px solid {color};
                    border-radius: 4px;
                    padding: 4px;
                }}
            """)
            cat_layout = QVBoxLayout(cat_frame)
            cat_layout.setContentsMargins(8, 6, 8, 6)
            cat_layout.setSpacing(2)
            
            cat_label = QLabel(f"{cat_name} ({len(rules)})")
            cat_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
            cat_layout.addWidget(cat_label)
            
            for rule in rules:
                rule_label = QLabel(f"  {rule}")
                rule_label.setStyleSheet("color: #8b8f98; font-size: 11px;")
                cat_layout.addWidget(rule_label)
            
            layout.addWidget(cat_frame)
        
        layout.addStretch()
        
        return widget


class CELEditorMainWindow(QMainWindow):
    """
    Hauptfenster des CEL-Editors
    ============================
    
    Professionelles Dock-Widget-Layout für Trading-Pattern-Definition
    und CEL-Regel-Erstellung mit KI-Unterstützung.
    """
    
    def __init__(self, use_dark_white_theme=False):
        super().__init__()
        self.use_dark_white_theme = use_dark_white_theme
        self._setup_window()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_dock_widgets()
        self._setup_status_bar()
        self._apply_theme()
    
    def _setup_window(self):
        """Fenster-Grundkonfiguration"""
        self.setWindowTitle("CEL Editor – Pattern Builder & Rule Generator")
        self.setMinimumSize(1400, 900)
        self.resize(1800, 1000)
        
        # Window State
        self.setDockNestingEnabled(True)
    
    def _setup_menu_bar(self):
        """Menüleiste erstellen"""
        menubar = self.menuBar()
        
        # Datei-Menü
        file_menu = menubar.addMenu("&Datei")
        file_menu.addAction("Neue Strategie", "Ctrl+N")
        file_menu.addAction("Öffnen...", "Ctrl+O")
        file_menu.addSeparator()
        file_menu.addAction("Speichern", "Ctrl+S")
        file_menu.addAction("Speichern unter...", "Ctrl+Shift+S")
        file_menu.addSeparator()
        file_menu.addAction("RulePack exportieren...", "Ctrl+E")
        file_menu.addAction("RulePack importieren...", "Ctrl+I")
        file_menu.addSeparator()
        file_menu.addAction("Einstellungen...", "Ctrl+,")
        file_menu.addSeparator()
        file_menu.addAction("Beenden", "Alt+F4")
        
        # Bearbeiten-Menü
        edit_menu = menubar.addMenu("&Bearbeiten")
        edit_menu.addAction("Rückgängig", "Ctrl+Z")
        edit_menu.addAction("Wiederholen", "Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction("Ausschneiden", "Ctrl+X")
        edit_menu.addAction("Kopieren", "Ctrl+C")
        edit_menu.addAction("Einfügen", "Ctrl+V")
        edit_menu.addSeparator()
        edit_menu.addAction("Alles auswählen", "Ctrl+A")
        
        # Ansicht-Menü
        view_menu = menubar.addMenu("&Ansicht")
        view_menu.addAction("Pattern Builder", "F1")
        view_menu.addAction("Code Editor", "F2")
        view_menu.addAction("Chart View", "F3")
        view_menu.addAction("Split View", "F4")
        view_menu.addSeparator()
        view_menu.addAction("Pattern Library anzeigen")
        view_menu.addAction("AI Assistant anzeigen")
        view_menu.addAction("Properties anzeigen")
        view_menu.addSeparator()
        view_menu.addAction("Zoom vergrößern", "Ctrl++")
        view_menu.addAction("Zoom verkleinern", "Ctrl+-")
        view_menu.addAction("Zoom zurücksetzen", "Ctrl+0")
        
        # Pattern-Menü
        pattern_menu = menubar.addMenu("&Pattern")
        pattern_menu.addAction("Neue Kerze hinzufügen", "K")
        pattern_menu.addAction("Relation erstellen", "R")
        pattern_menu.addSeparator()
        pattern_menu.addAction("Pattern aus Vorlage...")
        pattern_menu.addAction("Pattern in Library speichern...")
        pattern_menu.addSeparator()
        pattern_menu.addAction("Pattern duplizieren")
        pattern_menu.addAction("Pattern löschen", "Del")
        
        # Regeln-Menü
        rules_menu = menubar.addMenu("&Regeln")
        rules_menu.addAction("Als Entry-Regel", "Ctrl+1")
        rules_menu.addAction("Als Exit-Regel", "Ctrl+2")
        rules_menu.addAction("Als Risk-Regel", "Ctrl+3")
        rules_menu.addAction("Als Stop-Regel", "Ctrl+4")
        rules_menu.addSeparator()
        rules_menu.addAction("Validieren", "F5")
        rules_menu.addAction("Alle validieren", "Shift+F5")
        rules_menu.addSeparator()
        rules_menu.addAction("CEL-Code generieren")
        rules_menu.addAction("CEL-Code formatieren")
        
        # Analyse-Menü
        analysis_menu = menubar.addMenu("&Analyse")
        analysis_menu.addAction("Backtest starten", "F6")
        analysis_menu.addAction("Quick-Backtest (1 Monat)", "Shift+F6")
        analysis_menu.addSeparator()
        analysis_menu.addAction("Pattern im Chart finden...")
        analysis_menu.addAction("Historische Vorkommen...")
        analysis_menu.addSeparator()
        analysis_menu.addAction("AI-Analyse starten")
        analysis_menu.addAction("Ähnliche Patterns finden...")
        
        # Hilfe-Menü
        help_menu = menubar.addMenu("&Hilfe")
        help_menu.addAction("CEL Dokumentation", "F1")
        help_menu.addAction("Pattern-Referenz")
        help_menu.addAction("Tastenkombinationen...")
        help_menu.addSeparator()
        help_menu.addAction("Über CEL Editor...")
    
    def _setup_toolbar(self):
        """Werkzeugleiste einrichten"""
        self.main_toolbar = MainToolBar(self)
        self.addToolBar(self.main_toolbar)
    
    def _setup_central_widget(self):
        """Zentrales Widget mit Pattern Builder und Code Editor"""
        self.central_workspace = CentralWorkspace()
        self.setCentralWidget(self.central_workspace)
    
    def _setup_dock_widgets(self):
        """Dock-Widgets für Seitenpanels"""
        # Linker Dock: Pattern Library & Templates
        self.left_dock = QDockWidget("Pattern & Vorlagen", self)
        self.left_dock.setObjectName("LeftDock")
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.left_dock.setMinimumWidth(280)
        self.left_dock.setWidget(LeftDockContent())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
        
        # Rechter Dock: Properties & AI Assistant
        self.right_dock = QDockWidget("Eigenschaften & AI", self)
        self.right_dock.setObjectName("RightDock")
        self.right_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.right_dock.setMinimumWidth(320)
        self.right_dock.setWidget(RightDockContent())
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)
    
    def _setup_status_bar(self):
        """Statusleiste einrichten"""
        self.status_bar = StatusBarWidget(self)
        self.setStatusBar(self.status_bar)
    
    def _apply_theme(self):
        """Theme anwenden"""
        if self.use_dark_white_theme:
            self.setStyleSheet(DARK_WHITE_THEME)
            self.colors = DARK_WHITE_COLORS
        else:
            self.setStyleSheet(DARK_THEME)
            self.colors = DARK_COLORS
    
    def toggle_theme(self):
        """Theme wechseln"""
        self.use_dark_white_theme = not self.use_dark_white_theme
        self._apply_theme()
    
    # Dialog-Methoden (für Design-Studie als Platzhalter)
    def show_export_dialog(self):
        """Export-Dialog anzeigen"""
        dialog = ExportDialog(self)
        dialog.exec()
    
    def show_import_dialog(self):
        """Import-Dialog anzeigen"""
        dialog = ImportDialog(self)
        dialog.exec()
    
    def show_settings_dialog(self):
        """Einstellungen-Dialog anzeigen"""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def show_pattern_details_dialog(self, pattern_data=None):
        """Pattern-Details-Dialog anzeigen"""
        dialog = PatternDetailsDialog(self)
        dialog.exec()
    
    def show_validation_result_dialog(self, success=True, errors=None):
        """Validierungsergebnis-Dialog anzeigen"""
        dialog = ValidationResultDialog(success, errors, self)
        dialog.exec()


# Zusätzliche Styles für das Hauptfenster
MAIN_WINDOW_STYLES = """
/* Main Toolbar Styles */
QToolBar#MainToolBar {
    background: #14161a;
    border-bottom: 1px solid #2a2d35;
    padding: 4px 8px;
    spacing: 4px;
}

QToolBar#MainToolBar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #b4b8c4;
    padding: 6px 10px;
    font-size: 12px;
}

QToolBar#MainToolBar QToolButton:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: #3a3d45;
    color: #e1e3e8;
}

QToolBar#MainToolBar QToolButton:pressed {
    background: rgba(255, 255, 255, 0.12);
}

QToolBar#MainToolBar QToolButton[class="primary"] {
    background: rgba(0, 217, 255, 0.15);
    border-color: #00d9ff;
    color: #00d9ff;
}

QToolBar#MainToolBar QToolButton[class="success"] {
    background: rgba(0, 200, 83, 0.15);
    border-color: #00c853;
    color: #00c853;
}

QToolBar#MainToolBar QComboBox {
    background: #1e2128;
    border: 1px solid #3a3d45;
    border-radius: 4px;
    color: #e1e3e8;
    padding: 6px 10px;
    font-size: 12px;
}

/* Dock Widget Styles */
QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    font-size: 12px;
    font-weight: bold;
}

QDockWidget::title {
    background: #14161a;
    border-bottom: 1px solid #2a2d35;
    padding: 8px 12px;
    text-align: left;
}

QDockWidget::close-button,
QDockWidget::float-button {
    background: transparent;
    border: none;
    padding: 2px;
}

/* Splitter Styles */
QSplitter::handle {
    background: #2a2d35;
}

QSplitter::handle:horizontal {
    width: 4px;
}

QSplitter::handle:vertical {
    height: 4px;
}

QSplitter::handle:hover {
    background: #00d9ff;
}
"""
