"""CEL Editor Main Window - Interactive Pattern Builder with AI Assistance.

This is a standalone window implementing a professional visual pattern builder
for CEL (Common Expression Language) trading strategies.

Architecture:
- Dock-widget layout (Left/Center/Right) inspired by VS Code
- Central Pattern Builder Canvas (QGraphicsView)
- CEL Code Editor (QScintilla) with syntax highlighting
- AI Assistant panel (GPT-5.2) for pattern suggestions
- Pattern Library with templates

Based on UI Study but adapted to PyQt6 and OrderPilot-AI theme.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget,
    QToolBar, QStatusBar, QLabel, QComboBox, QPushButton, QMenuBar,
    QMenu, QMessageBox, QTabWidget, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from .theme import (
    get_qss_stylesheet, STATUS_SUCCESS, ACCENT_CYAN, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_TERTIARY, BORDER, BACKGROUND_PRIMARY
)
from ...themes import ThemeManager
from .icons import cel_icons
from ...app_icon import set_window_icon  # Issue #29: App icon
from ...widgets.pattern_builder.pattern_canvas import PatternBuilderCanvas
from ...widgets.pattern_builder.candle_toolbar import CandleToolbar
from ...widgets.pattern_builder.properties_panel import PropertiesPanel
from ...widgets.cel_strategy_editor_widget import CelStrategyEditorWidget


class CelEditorWindow(QMainWindow):
    """Main window for CEL Editor - Interactive Pattern Builder.

    Features:
    - Dock-widget layout (Left: Library, Center: Canvas/Editor, Right: Properties/AI)
    - View modes: Pattern Builder | Code Editor | Chart View | Split View
    - Toolbar with common actions (New, Open, Save, Undo, Redo)
    - Menu bar (File, Edit, View, Help)
    - Status bar with validation feedback
    - AI Assistant integration (GPT-5.2)
    """

    # Signals
    pattern_changed = pyqtSignal()  # Emitted when pattern is modified
    view_mode_changed = pyqtSignal(str)  # Emitted when view mode changes
    closed = pyqtSignal()  # Emitted when window is closed (Issue #27)

    def __init__(self, parent=None, strategy_name: str = "Untitled Strategy"):
        """Initialize CEL Editor window.

        Args:
            parent: Parent widget (usually None for standalone)
            strategy_name: Name of the strategy being edited
        """
        super().__init__(parent)

        # Issue #29: Set application icon (candlestick chart, white)
        set_window_icon(self)

        self.strategy_name = strategy_name
        self.current_view_mode = "pattern"  # pattern, code, chart, split

        # Window setup
        self._setup_window()

        # Create UI components
        self._create_menu_bar()
        self._create_toolbar()
        self._create_candle_toolbar()  # Phase 2.5: Candle type selector
        self._create_dock_widgets()
        self._create_central_widget()
        self._create_status_bar()

        # Apply theme
        self._apply_theme()

        # Restore window state from settings
        self._restore_state()

        # Connect signals
        self._connect_signals()

    def _setup_window(self):
        """Setup window properties to match ChartWindow."""
        self.setWindowTitle(f"CEL Editor - {self.strategy_name}")
        
        # Match ChartWindow flags
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self.setMinimumSize(1200, 800)
        self.resize(1600, 950)

        # Allow dock widgets to be nested
        self.setDockNestingEnabled(True)

        # Set corner configuration (allow docks in corners)
        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

    def _apply_theme(self):
        """Apply OrderPilot-AI global dark theme (Dark Orange)."""
        # Use global ThemeManager to match ChartWindow and Main App
        theme_manager = ThemeManager()
        self.setStyleSheet(theme_manager.get_theme("Dark Orange"))
        
        # Additional specialized styles for the CEL Editor
        self.central_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #32363E; top: -1px; }
            QTabBar::tab { height: 32px; min-width: 120px; font-weight: bold; }
        """)

    def _create_menu_bar(self):
        """Create menu bar with File, Edit, View, Help menus."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        self.action_new = QAction(cel_icons.new_file, "&New Strategy", self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.setStatusTip("Create a new strategy")
        file_menu.addAction(self.action_new)

        self.action_open = QAction(cel_icons.open_file, "&Open...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.setStatusTip("Open existing strategy")
        file_menu.addAction(self.action_open)

        self.action_save = QAction(cel_icons.save, "&Save", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.setStatusTip("Save current strategy")
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("Save &As...", self)
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_save_as.setStatusTip("Save strategy with new name")
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_export_json = QAction("Export as &JSON...", self)
        self.action_export_json.setStatusTip("Export strategy as JSON RulePack")
        file_menu.addAction(self.action_export_json)

        file_menu.addSeparator()

        self.action_close = QAction("&Close", self)
        self.action_close.setShortcut(QKeySequence.StandardKey.Close)
        self.action_close.setStatusTip("Close CEL Editor")
        file_menu.addAction(self.action_close)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        self.action_undo = QAction(cel_icons.undo, "&Undo", self)
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_undo.setEnabled(False)
        edit_menu.addAction(self.action_undo)

        self.action_redo = QAction(cel_icons.redo, "&Redo", self)
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.action_redo.setEnabled(False)
        edit_menu.addAction(self.action_redo)

        edit_menu.addSeparator()

        self.action_clear = QAction(cel_icons.clear_all, "&Clear All", self)
        self.action_clear.setStatusTip("Clear all candles from pattern")
        edit_menu.addAction(self.action_clear)

        # View Menu
        view_menu = menubar.addMenu("&View")

        self.action_view_pattern = QAction(cel_icons.view_pattern, "&Pattern Builder", self)
        self.action_view_pattern.setCheckable(True)
        self.action_view_pattern.setChecked(True)
        self.action_view_pattern.setStatusTip("Show pattern builder canvas")
        view_menu.addAction(self.action_view_pattern)

        self.action_view_code = QAction(cel_icons.view_code, "&Code Editor", self)
        self.action_view_code.setCheckable(True)
        self.action_view_code.setStatusTip("Show CEL code editor")
        view_menu.addAction(self.action_view_code)

        self.action_view_chart = QAction(cel_icons.view_chart, "Chart &View", self)
        self.action_view_chart.setCheckable(True)
        self.action_view_chart.setStatusTip("Show chart with pattern overlay")
        view_menu.addAction(self.action_view_chart)

        self.action_view_split = QAction(cel_icons.view_split, "&Split View", self)
        self.action_view_split.setCheckable(True)
        self.action_view_split.setStatusTip("Show pattern builder and code editor side-by-side")
        view_menu.addAction(self.action_view_split)

        view_menu.addSeparator()

        self.action_zoom_in = QAction(cel_icons.zoom_in, "Zoom &In", self)
        self.action_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        view_menu.addAction(self.action_zoom_in)

        self.action_zoom_out = QAction(cel_icons.zoom_out, "Zoom &Out", self)
        self.action_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        view_menu.addAction(self.action_zoom_out)

        self.action_zoom_fit = QAction(cel_icons.zoom_fit, "Zoom to &Fit", self)
        view_menu.addAction(self.action_zoom_fit)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        self.action_help = QAction(cel_icons.help, "CEL Editor &Help", self)
        self.action_help.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_menu.addAction(self.action_help)

        self.action_about = QAction("&About CEL Editor", self)
        help_menu.addAction(self.action_about)

    def _create_toolbar(self):
        """Create main toolbar with common actions matching ChartWindow style."""
        # 1. Action Row
        self.action_toolbar = QToolBar("Actions")
        self.action_toolbar.setObjectName("ActionToolbar")
        self.action_toolbar.setMovable(False)
        self.action_toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.action_toolbar)

        # Brand Label (matching ChartWindow style)
        brand_label = QLabel("  CEL EDITOR  ")
        brand_label.setStyleSheet("""
            color: #F29F05; 
            font-weight: bold; 
            font-family: 'Consolas', monospace; 
            font-size: 15px; 
            padding: 0 15px;
            border-right: 1px solid #32363E;
        """)
        self.action_toolbar.addWidget(brand_label)

        # Strategy Selector
        self.strategy_selector = QComboBox()
        self.strategy_selector.addItems([
            f"📁 {self.strategy_name}",
            "📊 New Strategy...",
            "📊 Recent: RSI Scalper",
            "📊 Recent: EMA Cross"
        ])
        self.strategy_selector.setMinimumWidth(200)
        self.action_toolbar.addWidget(self.strategy_selector)

        self.action_toolbar.addSeparator()

        # Tools
        btn_new = self._make_premium_button(self.action_new)
        self.action_toolbar.addWidget(btn_new)

        btn_open = self._make_premium_button(self.action_open)
        self.action_toolbar.addWidget(btn_open)

        btn_save = self._make_premium_button(self.action_save, is_primary=True)
        self.action_toolbar.addWidget(btn_save)

        self.action_toolbar.addSeparator()

        # Undo/Redo (without text for compactness)
        self.action_toolbar.addAction(self.action_undo)
        self.action_toolbar.addAction(self.action_redo)

        # Spacer to push AI button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.action_toolbar.addWidget(spacer)

        # AI Generate (Right Side)
        self.ai_btn = QPushButton(cel_icons.ai_generate, "  AI Generate  ")
        self.ai_btn.setProperty("class", "primary")
        self.ai_btn.setFixedHeight(32)
        self.ai_btn.clicked.connect(self._on_ai_generate)
        self.action_toolbar.addWidget(self.ai_btn)

    def _make_premium_button(self, action, is_primary=False):
        """Create a QPushButton for toolbar that matches ChartWindow style."""
        btn = QPushButton(action.icon(), f" {action.text().replace('&', '')}")
        btn.setProperty("class", "primary" if is_primary else "toolbar-button")
        btn.setFixedHeight(32)
        btn.setToolTip(action.statusTip())
        btn.clicked.connect(action.trigger)
        return btn

    def _create_candle_toolbar(self):
        """Create candle toolbar for adding candles to canvas.

        Phase 2.5: Vertical toolbar on the left side with:
        - 8 candle type buttons (Bullish, Bearish, Doji, etc.)
        - Add/Remove/Clear action buttons
        - Active candle type tracking
        """
        self.candle_toolbar = CandleToolbar(self)
        self.candle_toolbar.setObjectName("CandleToolbar")

        # Add to left side of window (vertical orientation)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.candle_toolbar)

    def _create_dock_widgets(self):
        """Create dock widgets for Library, Properties, and AI Assistant.

        Layout:
        - Left Dock (280px): Pattern Library & Templates
        - Right Dock (320px): Properties Panel & AI Assistant
        """
        # LEFT DOCK: Pattern Library & Templates
        self.left_dock = QDockWidget("Pattern Library & Templates", self)
        self.left_dock.setObjectName("LeftDock")
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.left_dock.setMinimumWidth(280)

        # Placeholder for library widget (will be implemented in Phase 6)
        left_placeholder = QLabel("Pattern Library\n(Phase 6)")
        left_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_placeholder.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px;")
        self.left_dock.setWidget(left_placeholder)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # RIGHT DOCK: Properties & AI Assistant
        self.right_dock = QDockWidget("Properties & AI Assistant", self)
        self.right_dock.setObjectName("RightDock")
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.right_dock.setMinimumWidth(320)

        # Properties Panel (Phase 2.6) + AI Assistant (Phase 5)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Properties Panel
        self.properties_panel = PropertiesPanel(self)
        right_layout.addWidget(self.properties_panel)

        # AI Assistant Placeholder (Phase 5)
        ai_placeholder = QLabel("AI Assistant\n(Phase 5)")
        ai_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_placeholder.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")
        right_layout.addWidget(ai_placeholder)

        self.right_dock.setWidget(right_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

    def _create_central_widget(self):
        """Create central widget with Tabs for different view modes.

        Tabs:
        0: Pattern Builder (Visual)
        1: Code Editor (Script)
        2: Chart View (Reference)
        3: Split View (Visual + Script side-by-side)
        """
        self.central_tabs = QTabWidget()
        self.central_tabs.setDocumentMode(True)  # Clean tab style
        self.setCentralWidget(self.central_tabs)

        # 1. Pattern Builder View
        self.pattern_container = QWidget()
        pattern_layout = QVBoxLayout(self.pattern_container)
        pattern_layout.setContentsMargins(0, 0, 0, 0)
        
        self.pattern_canvas = PatternBuilderCanvas(self)
        pattern_layout.addWidget(self.pattern_canvas)
        
        self.central_tabs.addTab(self.pattern_container, cel_icons.view_pattern, "Pattern Builder")

        # 2. Code Editor View
        self.code_editor = CelStrategyEditorWidget(self)
        self.central_tabs.addTab(self.code_editor, cel_icons.view_code, "Code Editor")

        # 3. Chart View (Placeholder for now)
        self.chart_view_placeholder = QLabel("Chart View Integration\n(Coming soon - Phase 6 integration)")
        self.chart_view_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_view_placeholder.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 18px; background: {BACKGROUND_PRIMARY};")
        self.central_tabs.addTab(self.chart_view_placeholder, cel_icons.view_chart, "Chart View")

        # 4. Split View
        self.split_view = QSplitter(Qt.Orientation.Horizontal)
        self.split_view.setStyleSheet("QSplitter::handle { background: #32363E; width: 4px; }")
        
        self.split_pattern = PatternBuilderCanvas(self)
        self.split_code = CelStrategyEditorWidget(self)
        
        self.split_view.addWidget(self.split_pattern)
        self.split_view.addWidget(self.split_code)
        self.split_view.setSizes([600, 600])
        
        self.central_tabs.addTab(self.split_view, cel_icons.view_split, "Split View")

        # Connect canvas signals
        self.pattern_canvas.pattern_changed.connect(self._on_pattern_changed)
        self.pattern_canvas.candle_selected.connect(self._on_candle_selected)
        self.pattern_canvas.selection_cleared.connect(self._on_selection_cleared)

        # Update undo/redo button states
        self.pattern_canvas.undo_stack.canUndoChanged.connect(self.action_undo.setEnabled)
        self.pattern_canvas.undo_stack.canRedoChanged.connect(self.action_redo.setEnabled)

        # Connect canvas signals
        self.pattern_canvas.pattern_changed.connect(self._on_pattern_changed)
        self.pattern_canvas.candle_selected.connect(self._on_candle_selected)
        self.pattern_canvas.selection_cleared.connect(self._on_selection_cleared)

        # Update undo/redo button states
        self.pattern_canvas.undo_stack.canUndoChanged.connect(self.action_undo.setEnabled)
        self.pattern_canvas.undo_stack.canRedoChanged.connect(self.action_redo.setEnabled)

    def _create_status_bar(self):
        """Create status bar with validation feedback matching ChartWindow."""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)

        # Validation status label
        self.validation_label = QLabel("✓ CEL Ready")
        self.validation_label.setStyleSheet(f"""
            color: #0ECB81; 
            background: rgba(14, 203, 129, 0.1); 
            border-radius: 3px; 
            padding: 2px 10px; 
            font-family: 'Consolas', monospace;
            font-weight: bold;
        """)
        statusbar.addWidget(self.validation_label)

        # Rule counts
        self.rule_counts_label = QLabel("  0 Entry  |  0 Exit  |  0 Risk  |  0 Stop  ")
        self.rule_counts_label.setStyleSheet("color: #848E9C; padding: 0 10px;")
        statusbar.addWidget(self.rule_counts_label)

        # AI Status
        self.ai_status_label = QLabel("🤖 AI: Ready")
        self.ai_status_label.setStyleSheet("color: #F29F05; padding: 0 10px; font-weight: bold;")
        statusbar.addPermanentWidget(self.ai_status_label)

        # Version
        version_label = QLabel("v1.2.0-beta")
        version_label.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 10px; padding: 0 5px;")
        statusbar.addPermanentWidget(version_label)

        statusbar.showMessage("Ready")

    def _connect_signals(self):
        """Connect signals to slots."""
        # File actions
        self.action_new.triggered.connect(self._on_new_strategy)
        self.action_open.triggered.connect(self._on_open_strategy)
        self.action_save.triggered.connect(self._on_save_strategy)
        self.action_save_as.triggered.connect(self._on_save_as_strategy)
        self.action_export_json.triggered.connect(self._on_export_json)
        self.action_close.triggered.connect(self.close)

        # Edit actions
        self.action_undo.triggered.connect(self._on_undo)
        self.action_redo.triggered.connect(self._on_redo)
        self.action_clear.triggered.connect(self._on_clear_pattern)

        # View actions
        self.action_view_pattern.triggered.connect(lambda: self._switch_view_mode("pattern"))
        self.action_view_code.triggered.connect(lambda: self._switch_view_mode("code"))
        self.action_view_chart.triggered.connect(lambda: self._switch_view_mode("chart"))
        self.action_view_split.triggered.connect(lambda: self._switch_view_mode("split"))

        # View mode Tabs
        self.central_tabs.currentChanged.connect(self._on_tab_changed)

        # Zoom actions
        self.action_zoom_in.triggered.connect(self._on_zoom_in)
        self.action_zoom_out.triggered.connect(self._on_zoom_out)
        self.action_zoom_fit.triggered.connect(self._on_zoom_fit)

        # Strategy Selector
        self.strategy_selector.currentIndexChanged.connect(self._on_strategy_selected)

        # Connect Code Editor changes to update status bar
        self.code_editor.strategy_changed.connect(self._on_code_strategy_changed)

        # Candle Toolbar signals (Phase 2.5)
        self.candle_toolbar.candle_add_requested.connect(self._on_toolbar_add_candle)
        self.candle_toolbar.candle_remove_requested.connect(self._on_toolbar_remove_candle)
        self.candle_toolbar.pattern_clear_requested.connect(self._on_clear_pattern)

        # Properties Panel signals (Phase 2.6)
        # Panel → Canvas: Update candle when user applies changes
        self.properties_panel.values_changed.connect(self.pattern_canvas.update_candle_properties)

        # Canvas → Panel: Update panel when selection changes
        self.pattern_canvas.candle_selected.connect(self._on_candle_selected_for_properties)
        self.pattern_canvas.selection_cleared.connect(self._on_selection_cleared_for_properties)

        # Help actions
        self.action_help.triggered.connect(self._on_show_help)
        self.action_about.triggered.connect(self._on_show_about)

    def _restore_state(self):
        """Restore window state from QSettings."""
        settings = QSettings("OrderPilot-AI", "CELEditor")

        # Restore geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore dock state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def _save_state(self):
        """Save window state to QSettings."""
        settings = QSettings("OrderPilot-AI", "CELEditor")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    # Placeholder methods (will be implemented in later phases)

    def _on_strategy_selected(self, index: int):
        """Handle strategy selection change."""
        selection = self.strategy_selector.itemText(index)
        if "New Strategy" in selection:
            self._on_new_strategy()
        elif "Recent" not in selection:
            self.statusBar().showMessage(f"Loading {selection}...", 3000)
            # In a real app, this would load the JSON file
            self.strategy_name = selection.replace("📁 ", "").replace("📊 ", "")
            self.setWindowTitle(f"CEL Editor - {self.strategy_name}")

    def _on_code_strategy_changed(self, strategy_data: dict):
        """Update status bar when code strategy changes."""
        workflow = strategy_data.get("workflow", {})
        
        counts = {
            "entry": workflow.get("entry", {}).get("expression", "").count("&&") + 1 if workflow.get("entry", {}).get("expression", "") else 0,
            "exit": workflow.get("exit", {}).get("expression", "").count("&&") + 1 if workflow.get("exit", {}).get("expression", "") else 0,
            "risk": 0, # Placeholder
            "stop": workflow.get("update_stop", {}).get("expression", "").count("&&") + 1 if workflow.get("update_stop", {}).get("expression", "") else 0
        }
        
        self.rule_counts_label.setText(
            f"  {counts['entry']} Entry  |  {counts['exit']} Exit  |  {counts['risk']} Risk  |  {counts['stop']} Stop  "
        )

    def _on_new_strategy(self):
        """Create new strategy (Phase 1)."""
        # TODO: Implement in Phase 1.7
        self.statusBar().showMessage("New strategy (not yet implemented)", 3000)

    def _on_open_strategy(self):
        """Open existing strategy (Phase 7)."""
        # TODO: Implement in Phase 7 (JSON Integration)
        self.statusBar().showMessage("Open strategy (not yet implemented)", 3000)

    def _on_save_strategy(self):
        """Save current strategy (Phase 7)."""
        # TODO: Implement in Phase 7 (JSON Integration)
        self.statusBar().showMessage("Save strategy (not yet implemented)", 3000)

    def _on_save_as_strategy(self):
        """Save strategy with new name (Phase 7)."""
        # TODO: Implement in Phase 7 (JSON Integration)
        self.statusBar().showMessage("Save as (not yet implemented)", 3000)

    def _on_export_json(self):
        """Export strategy as JSON RulePack (Phase 7)."""
        # TODO: Implement in Phase 7 (JSON Integration)
        self.statusBar().showMessage("Export JSON (not yet implemented)", 3000)

    def _on_undo(self):
        """Undo last action."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.undo()
            undo_text = self.pattern_canvas.undo_stack.undoText()
            self.statusBar().showMessage(f"Undo: {undo_text}" if undo_text else "Undo", 2000)

    def _on_redo(self):
        """Redo last undone action."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.redo()
            redo_text = self.pattern_canvas.undo_stack.redoText()
            self.statusBar().showMessage(f"Redo: {redo_text}" if redo_text else "Redo", 2000)

    def _on_clear_pattern(self):
        """Clear all candles from pattern."""
        if hasattr(self, 'pattern_canvas'):
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Clear Pattern",
                "Are you sure you want to clear all candles?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.pattern_canvas.clear_pattern()
                self.statusBar().showMessage("Pattern cleared", 2000)

    def _switch_view_mode(self, mode: str):
        """Switch between view modes via TabWidget."""
        self.current_view_mode = mode

        # Update menu checkboxes
        self.action_view_pattern.setChecked(mode == "pattern")
        self.action_view_code.setChecked(mode == "code")
        self.action_view_chart.setChecked(mode == "chart")
        self.action_view_split.setChecked(mode == "split")

        # Sync tab widget
        mode_index = {"pattern": 0, "code": 1, "chart": 2, "split": 3}
        self.central_tabs.blockSignals(True)
        self.central_tabs.setCurrentIndex(mode_index.get(mode, 0))
        self.central_tabs.blockSignals(False)

        # Emit signal
        self.view_mode_changed.emit(mode)

        # Update status
        self.statusBar().showMessage(f"Switched to {mode} view", 2000)

        # Show/hide sidebars based on mode
        is_pattern = mode in ["pattern", "split"]
        self.left_dock.setVisible(is_pattern)
        self.right_dock.setVisible(is_pattern)
        self.candle_toolbar.setVisible(is_pattern)

    def _on_tab_changed(self, index: int):
        """Handle view mode tab change."""
        modes = ["pattern", "code", "chart", "split"]
        if 0 <= index < len(modes):
            self._switch_view_mode(modes[index])

    def _on_view_mode_combo_changed(self, index: int):
        """Legacy handler for combo box (kept for compatibility during refactoring)."""
        pass

    def _on_zoom_in(self):
        """Zoom in on canvas."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.zoom_in()
            self.statusBar().showMessage("Zoomed in", 1000)

    def _on_zoom_out(self):
        """Zoom out on canvas."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.zoom_out()
            self.statusBar().showMessage("Zoomed out", 1000)

    def _on_zoom_fit(self):
        """Zoom to fit all candles."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.zoom_fit()
            self.statusBar().showMessage("Zoomed to fit", 1000)

    def _on_toolbar_add_candle(self, candle_type: str):
        """Handle add candle request from toolbar.

        Args:
            candle_type: Type of candle to add (bullish, bearish, doji, etc.)
        """
        if hasattr(self, 'pattern_canvas'):
            # Add candle at auto-positioned coordinates (canvas handles positioning)
            candle = self.pattern_canvas.add_candle(candle_type)

            # Update status bar
            self.statusBar().showMessage(
                f"Added {candle_type.replace('_', ' ').title()} candle",
                2000
            )

    def _on_toolbar_remove_candle(self):
        """Handle remove candle request from toolbar."""
        if hasattr(self, 'pattern_canvas'):
            # Remove selected candles
            self.pattern_canvas.remove_selected_candles()

            # Update status bar
            self.statusBar().showMessage("Removed selected candle(s)", 2000)

    def _on_ai_generate(self):
        """Generate pattern suggestions with AI (Phase 5)."""
        # TODO: Implement in Phase 5 (AI Assistant)
        self.statusBar().showMessage("AI Generate (not yet implemented - Phase 5)", 3000)

    def _on_pattern_changed(self):
        """Handle pattern changes from canvas."""
        # Update validation status
        if hasattr(self, 'pattern_canvas'):
            stats = self.pattern_canvas.get_statistics()
            candle_count = stats['total_candles']
            relation_count = stats['total_relations']

            if candle_count == 0:
                self.validation_label.setText("✓ Ready")
                self.validation_label.setStyleSheet(f"color: {STATUS_SUCCESS}; font-family: 'Consolas', monospace;")
            elif candle_count < 2:
                self.validation_label.setText("⚠️ Need at least 2 candles")
                self.validation_label.setStyleSheet("color: #ffa726; font-family: 'Consolas', monospace;")
            else:
                self.validation_label.setText(f"✓ {candle_count} candles, {relation_count} relations")
                self.validation_label.setStyleSheet(f"color: {STATUS_SUCCESS}; font-family: 'Consolas', monospace;")

        # Emit main window signal
        self.pattern_changed.emit()

    def _on_candle_selected(self, candle_data: dict):
        """Handle candle selection from canvas.

        Args:
            candle_data: Dict with candle properties (type, index, ohlc, position)
        """
        # TODO: Update properties panel in Phase 2.6
        candle_type = candle_data.get('type', 'unknown')
        index = candle_data.get('index', 0)
        self.statusBar().showMessage(
            f"Selected: {candle_type.replace('_', ' ').title()} [index {index}]",
            2000
        )

    def _on_selection_cleared(self):
        """Handle selection cleared from canvas."""
        # TODO: Clear properties panel in Phase 2.6
        self.statusBar().showMessage("Selection cleared", 1000)

    def _on_candle_selected_for_properties(self, candle_data: dict):
        """Update properties panel when candle is selected.

        Args:
            candle_data: Dict with candle properties (from canvas signal)
        """
        # Get selected candles from canvas
        selected_candles = self.pattern_canvas.get_selected_candles()

        # Update properties panel
        self.properties_panel.on_canvas_selection_changed(selected_candles)

    def _on_selection_cleared_for_properties(self):
        """Clear properties panel when selection is cleared."""
        # Clear properties panel
        self.properties_panel.on_canvas_selection_changed([])

    def _on_show_help(self):
        """Show CEL Editor help."""
        QMessageBox.information(
            self,
            "CEL Editor Help",
            "CEL Editor - Interactive Pattern Builder\n\n"
            "Features:\n"
            "• Visual Pattern Builder with drag & drop\n"
            "• CEL Code Editor with syntax highlighting\n"
            "• AI-powered pattern suggestions\n"
            "• Pattern library and templates\n"
            "• JSON RulePack export/import\n\n"
            "Phase 1: Basic window structure (current)\n"
            "Phase 2: Pattern Builder Canvas\n"
            "Phase 3: CEL Code Editor\n"
            "Phase 4: Pattern → CEL Translation\n"
            "Phase 5: AI Assistant\n"
            "Phase 6: Pattern Library\n"
            "Phase 7: JSON Integration"
        )

    def _on_show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About CEL Editor",
            "CEL Editor - Interactive Pattern Builder\n\n"
            "Version: 1.0.0 (Phase 1)\n"
            "Part of OrderPilot-AI Trading Platform\n\n"
            "A professional visual pattern builder for creating\n"
            "CEL (Common Expression Language) trading strategies.\n\n"
            "© 2026 OrderPilot-AI"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        # Save window state
        self._save_state()

        # TODO: Check for unsaved changes in later phases

        # Issue #27: Emit closed signal for button state sync
        self.closed.emit()

        event.accept()
