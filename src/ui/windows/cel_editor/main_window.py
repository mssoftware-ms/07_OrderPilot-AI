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
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from .theme import get_qss_stylesheet, ACCENT_TEAL, TEXT_PRIMARY
from .icons import cel_icons
from ...widgets.pattern_builder.pattern_canvas import PatternBuilderCanvas
from ...widgets.pattern_builder.candle_toolbar import CandleToolbar


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

    def __init__(self, parent=None, strategy_name: str = "Untitled Strategy"):
        """Initialize CEL Editor window.

        Args:
            parent: Parent widget (usually None for standalone)
            strategy_name: Name of the strategy being edited
        """
        super().__init__(parent)

        self.strategy_name = strategy_name
        self.current_view_mode = "pattern"  # pattern, code, chart, split

        # Window setup
        self._setup_window()

        # Apply theme
        self._apply_theme()

        # Create UI components
        self._create_menu_bar()
        self._create_toolbar()
        self._create_candle_toolbar()  # Phase 2.5: Candle type selector
        self._create_dock_widgets()
        self._create_central_widget()
        self._create_status_bar()

        # Restore window state from settings
        self._restore_state()

        # Connect signals
        self._connect_signals()

    def _setup_window(self):
        """Setup basic window properties."""
        self.setWindowTitle(f"CEL Editor - {self.strategy_name}")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        # Allow dock widgets to be nested
        self.setDockNestingEnabled(True)

        # Set corner configuration (allow docks in corners)
        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

    def _apply_theme(self):
        """Apply OrderPilot-AI dark theme."""
        self.setStyleSheet(get_qss_stylesheet())

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
        """Create main toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # File actions
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)

        toolbar.addSeparator()

        # Edit actions
        toolbar.addAction(self.action_undo)
        toolbar.addAction(self.action_redo)

        toolbar.addSeparator()

        # View mode selector
        toolbar.addWidget(QLabel("  View: "))
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Pattern Builder", "Code Editor", "Chart View", "Split View"])
        self.view_mode_combo.setMinimumWidth(150)
        self.view_mode_combo.setStatusTip("Switch between view modes")
        toolbar.addWidget(self.view_mode_combo)

        toolbar.addSeparator()

        # Zoom actions
        toolbar.addAction(self.action_zoom_in)
        toolbar.addAction(self.action_zoom_out)
        toolbar.addAction(self.action_zoom_fit)

        toolbar.addSeparator()

        # AI Generate button
        self.ai_generate_btn = QPushButton(cel_icons.ai_generate, "AI Generate")
        self.ai_generate_btn.setObjectName("primary")  # Apply primary button style
        self.ai_generate_btn.setStatusTip("Generate pattern suggestions with AI")
        toolbar.addWidget(self.ai_generate_btn)

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

        # Placeholder for properties/AI widget (will be implemented in Phase 5)
        right_placeholder = QLabel("Properties & AI Assistant\n(Phase 5)")
        right_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_placeholder.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px;")
        self.right_dock.setWidget(right_placeholder)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

    def _create_central_widget(self):
        """Create central widget with Pattern Builder Canvas.

        Phase 2: Pattern Builder Canvas (QGraphicsView)
        Phase 3: CEL Code Editor (QScintilla) - will be added in split view
        """
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Pattern Builder Canvas (Phase 2)
        self.pattern_canvas = PatternBuilderCanvas(self)
        layout.addWidget(self.pattern_canvas)

        # Connect canvas signals
        self.pattern_canvas.pattern_changed.connect(self._on_pattern_changed)
        self.pattern_canvas.candle_selected.connect(self._on_candle_selected)
        self.pattern_canvas.selection_cleared.connect(self._on_selection_cleared)

        # Update undo/redo button states
        self.pattern_canvas.undo_stack.canUndoChanged.connect(self.action_undo.setEnabled)
        self.pattern_canvas.undo_stack.canRedoChanged.connect(self.action_redo.setEnabled)

    def _create_status_bar(self):
        """Create status bar with validation feedback."""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)

        # Validation status label
        self.validation_label = QLabel("✅ Ready")
        self.validation_label.setStyleSheet(f"color: {ACCENT_TEAL}; padding: 2px 8px;")
        statusbar.addPermanentWidget(self.validation_label)

        # Strategy info
        self.strategy_info_label = QLabel(f"Strategy: {self.strategy_name}")
        statusbar.addPermanentWidget(self.strategy_info_label)

        statusbar.showMessage("CEL Editor ready")

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

        # View mode combo
        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_combo_changed)

        # Zoom actions
        self.action_zoom_in.triggered.connect(self._on_zoom_in)
        self.action_zoom_out.triggered.connect(self._on_zoom_out)
        self.action_zoom_fit.triggered.connect(self._on_zoom_fit)

        # AI Generate button
        self.ai_generate_btn.clicked.connect(self._on_ai_generate)

        # Candle Toolbar signals (Phase 2.5)
        self.candle_toolbar.candle_add_requested.connect(self._on_toolbar_add_candle)
        self.candle_toolbar.candle_remove_requested.connect(self._on_toolbar_remove_candle)
        self.candle_toolbar.pattern_clear_requested.connect(self._on_clear_pattern)

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
        """Switch between view modes (Phase 1/2/3).

        Args:
            mode: 'pattern', 'code', 'chart', or 'split'
        """
        self.current_view_mode = mode

        # Update menu checkboxes
        self.action_view_pattern.setChecked(mode == "pattern")
        self.action_view_code.setChecked(mode == "code")
        self.action_view_chart.setChecked(mode == "chart")
        self.action_view_split.setChecked(mode == "split")

        # Update combo box (without triggering signal)
        mode_index = {"pattern": 0, "code": 1, "chart": 2, "split": 3}
        self.view_mode_combo.blockSignals(True)
        self.view_mode_combo.setCurrentIndex(mode_index.get(mode, 0))
        self.view_mode_combo.blockSignals(False)

        # Emit signal
        self.view_mode_changed.emit(mode)

        # Update status
        self.statusBar().showMessage(f"Switched to {mode} view", 2000)

        # TODO: Actually switch widgets in Phase 2/3

    def _on_view_mode_combo_changed(self, index: int):
        """Handle view mode combo box change."""
        modes = ["pattern", "code", "chart", "split"]
        if 0 <= index < len(modes):
            self._switch_view_mode(modes[index])

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
                self.validation_label.setText("✅ Ready")
                self.validation_label.setStyleSheet(f"color: {ACCENT_TEAL}; padding: 2px 8px;")
            elif candle_count < 2:
                self.validation_label.setText("⚠️ Need at least 2 candles")
                self.validation_label.setStyleSheet("color: #ffa726; padding: 2px 8px;")
            else:
                self.validation_label.setText(f"✅ {candle_count} candles, {relation_count} relations")
                self.validation_label.setStyleSheet(f"color: {ACCENT_TEAL}; padding: 2px 8px;")

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

        event.accept()
