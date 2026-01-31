"""CEL Editor Window - UI Setup Mixin.

This module contains all UI setup methods for the CEL Editor main window.
Extracted from monolithic main_window.py (1798 LOC) as part of Phase 3 refactoring.

Responsibilities:
- Window configuration and theming
- Menu bar creation (File, Edit, View, Help)
- Toolbar creation (action toolbar, candle toolbar)
- Dock widget creation (left, right, functions)
- Central widget creation (tabs with different views)
- Status bar creation

Author: CODER-009 (Claude Sonnet 4.5)
Date: 2026-01-31
Task: 3.1.1 - Split cel_editor/main_window.py
"""

from PyQt6.QtWidgets import (
    QToolBar, QLabel, QComboBox, QPushButton, QDockWidget, QTabWidget,
    QWidget, QVBoxLayout, QSplitter, QStatusBar
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon

# UI constants and theme
from .theme import TEXT_PRIMARY, TEXT_TERTIARY, BACKGROUND_PRIMARY
from ...themes import ThemeManager
from .icons import cel_icons
from src.ui.widgets.cel_strategy_editor_widget import CelStrategyEditorWidget
from src.ui.widgets.regime_editor_widget import RegimeEditorWidget
from src.ui.widgets.cel_rulepack_panel import CelRulePackPanel
from src.ui.widgets.cel_ai_assistant_panel import CelAIAssistantPanel
from src.ui.widgets.cel_function_palette import CelFunctionPalette


class CelEditorWindowUIMixin:
    """Mixin for CEL Editor window UI setup methods.

    This mixin provides all methods for creating the user interface components:
    - Window setup and theme application
    - Menu bar with File, Edit, View, Help menus
    - Toolbars (action toolbar, candle toolbar)
    - Dock widgets (pattern library, properties, AI assistant, functions)
    - Central widget with tabs (pattern builder, code editor, chart, split, JSON)
    - Status bar with validation feedback

    Usage:
        class CelEditorWindow(CelEditorWindowUIMixin, QMainWindow):
            def __init__(self):
                super().__init__()
                self._setup_window()
                self._apply_theme()
                # ... other UI setup
    """

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
        """Apply OrderPilot-AI global dark theme (Dark Orange) + compact overrides."""
        # Use global ThemeManager to match ChartWindow and Main App
        theme_manager = ThemeManager()
        base_stylesheet = theme_manager.get_theme("Dark Orange")

        # Add compact design overrides for CEL Editor
        compact_overrides = """
        /* Compact Toolbar */
        QToolBar {
            spacing: 3px;
            padding: 2px 5px;
        }

        /* Compact Buttons */
        QPushButton {
            padding: 3px 8px;
            min-height: 24px;
            max-height: 28px;
        }

        /* Compact Toolbar Buttons */
        QToolButton {
            padding: 3px;
            min-height: 24px;
            max-height: 28px;
            min-width: 24px;
        }

        /* Compact Tabs */
        QTabBar::tab {
            padding: 6px 15px;
            min-height: 20px;
            max-height: 32px;
        }
        """

        self.setStyleSheet(base_stylesheet + compact_overrides)

        # Additional specialized styles for the CEL Editor
        self.central_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #32363E; top: -1px; }
            QTabBar::tab { height: 28px; min-width: 100px; font-weight: bold; }
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

        # RulePack Actions
        self.action_open_rulepack = QAction(cel_icons.open_file, "Open &RulePack...", self)
        self.action_open_rulepack.setShortcut("Ctrl+Shift+O")
        self.action_open_rulepack.setStatusTip("Open CEL RulePack JSON file")
        file_menu.addAction(self.action_open_rulepack)

        self.action_save_rulepack = QAction(cel_icons.save, "Save Rule&Pack", self)
        self.action_save_rulepack.setShortcut("Ctrl+Shift+S")
        self.action_save_rulepack.setStatusTip("Save current RulePack")
        self.action_save_rulepack.setEnabled(False)  # Enabled when RulePack loaded
        file_menu.addAction(self.action_save_rulepack)

        self.action_save_rulepack_as = QAction("Save RulePack &As...", self)
        self.action_save_rulepack_as.setStatusTip("Save RulePack with new name")
        self.action_save_rulepack_as.setEnabled(False)
        file_menu.addAction(self.action_save_rulepack_as)

        file_menu.addSeparator()

        # Generic JSON Editor Actions
        self.action_open_regime = QAction(cel_icons.open_file, "Edit &JSON File...", self)
        self.action_open_regime.setShortcut("Ctrl+Shift+J")
        self.action_open_regime.setStatusTip("Open any JSON file in the JSON Editor")
        file_menu.addAction(self.action_open_regime)

        self.action_save_regime = QAction(cel_icons.save, "Save &JSON", self)
        self.action_save_regime.setStatusTip("Save current JSON file")
        self.action_save_regime.setEnabled(False)
        file_menu.addAction(self.action_save_regime)

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

        edit_menu.addSeparator()

        # Variable System action
        self.action_variables = QAction(cel_icons.variables, "&Variables Reference", self)
        self.action_variables.setShortcut("Ctrl+Shift+V")
        self.action_variables.setStatusTip("Open Variables Reference Dialog")
        edit_menu.addAction(self.action_variables)

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
        # 1. Action Row (Compact design like ChartWindow)
        self.action_toolbar = QToolBar("Actions")
        self.action_toolbar.setObjectName("ActionToolbar")
        self.action_toolbar.setMovable(False)
        self.action_toolbar.setIconSize(QSize(18, 18))  # Reduced from 20x20 for compactness
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.action_toolbar)

        # Brand Label (Compact design like ChartWindow)
        brand_label = QLabel(" CEL EDITOR ")
        brand_label.setStyleSheet("""
            color: #F29F05;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            padding: 0 10px;
            border-right: 1px solid #32363E;
        """)
        self.action_toolbar.addWidget(brand_label)

        # Strategy Selector
        from PyQt6.QtWidgets import QSizePolicy
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

        self.action_toolbar.addSeparator()

        # Variables button (Variable System Integration)
        btn_variables = self._make_premium_button(self.action_variables)
        self.action_toolbar.addWidget(btn_variables)

        # Spacer to push AI button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.action_toolbar.addWidget(spacer)

        # Pattern → CEL (Right Side)
        self.ai_btn = QPushButton(cel_icons.ai_generate, "  Pattern → CEL  ")
        self.ai_btn.setProperty("class", "primary")
        self.ai_btn.setToolTip("Generate CEL code from visual pattern")
        self.ai_btn.setFixedHeight(28)  # Reduced from 32 for compactness
        self.ai_btn.clicked.connect(self._on_ai_generate)
        self.action_toolbar.addWidget(self.ai_btn)

    def _make_premium_button(self, action, is_primary=False):
        """Create a QPushButton for toolbar that matches ChartWindow style.

        Args:
            action: QAction to create button from
            is_primary: Whether button should have primary styling

        Returns:
            QPushButton configured with action properties
        """
        btn = QPushButton(action.icon(), f" {action.text().replace('&', '')}")
        btn.setProperty("class", "primary" if is_primary else "toolbar-button")
        btn.setFixedHeight(28)  # Reduced from 32 for compactness
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
        # Lazy import to avoid circular import
        from ...widgets.pattern_builder.candle_toolbar import CandleToolbar
        self.candle_toolbar = CandleToolbar(self)
        self.candle_toolbar.setObjectName("CandleToolbar")

        # Add to left side of window (vertical orientation)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.candle_toolbar)

    def _create_dock_widgets(self):
        """Create dock widgets for Library, Properties, and AI Assistant.

        Layout:
        - Left Dock (280px): Pattern Library & Templates
        - Right Dock (320px): Properties Panel & AI Assistant
        - Functions Dock (300px): Command Reference & Function Palette
        """
        # LEFT DOCK: Pattern Library & RulePack Editor
        self.left_dock = QDockWidget("Pattern Library & Templates", self)
        self.left_dock.setObjectName("LeftDock")
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.left_dock.setMinimumWidth(280)

        # Tabs: Pattern Library (Strategy) + RulePack Editor
        self.left_tabs = QTabWidget()
        self.left_tabs.setDocumentMode(True)

        # Pattern Library widget with templates
        # Lazy import to avoid circular import
        from ...widgets.pattern_builder.pattern_library import PatternLibrary
        self.pattern_library = PatternLibrary(self)
        self.pattern_library.pattern_selected.connect(self._on_library_pattern_selected)

        # RulePack editor panel (Phase 2.5.2)
        self.rulepack_panel = CelRulePackPanel(self)
        self.rulepack_panel.rule_selected.connect(self._on_rulepack_rule_selected)
        self.rulepack_panel.rule_updated.connect(self._on_rulepack_rule_updated)
        self.rulepack_panel.rule_order_changed.connect(self._on_rulepack_rule_order_changed)

        self.left_tabs.addTab(self.pattern_library, "Library")
        self.left_tabs.addTab(self.rulepack_panel, "RulePack")
        self.left_tabs.setCurrentWidget(self.pattern_library)
        self.left_tabs.setTabEnabled(1, False)

        self.left_dock.setWidget(self.left_tabs)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # RIGHT DOCK: Properties & AI Assistant
        self.right_dock = QDockWidget("Properties & AI Assistant", self)
        self.right_dock.setObjectName("RightDock")
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.right_dock.setMinimumWidth(320)

        # Properties Panel (Phase 2.6) + AI Assistant (Phase 3.3)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_tabs = QTabWidget()
        right_tabs.setDocumentMode(True)

        # Properties Panel
        # Lazy import to avoid circular import
        from ...widgets.pattern_builder.properties_panel import PropertiesPanel
        self.properties_panel = PropertiesPanel(self)
        right_tabs.addTab(self.properties_panel, "Properties")

        # AI Assistant Panel
        self.ai_panel = CelAIAssistantPanel(self)
        self.ai_panel.code_ready.connect(self._on_ai_code_ready)
        self.ai_panel.status_changed.connect(self._on_ai_status_changed)
        right_tabs.addTab(self.ai_panel, "AI Assistant")

        right_layout.addWidget(right_tabs)

        self.right_dock.setWidget(right_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

        # FUNCTIONS DOCK: Command Reference + Function Palette
        # This is the ONLY instance of these tabs (duplicate removed from cel_strategy_editor_widget.py)
        self.functions_dock = QDockWidget("CEL Functions", self)
        self.functions_dock.setObjectName("FunctionsDock")
        self.functions_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.functions_dock.setMinimumWidth(300)

        functions_tabs = QTabWidget()
        functions_tabs.setDocumentMode(True)
        from src.ui.widgets.cel_strategy_editor_widget import CelCommandReference
        self.functions_command_reference = CelCommandReference(self)
        self.functions_palette = CelFunctionPalette(self)
        self.functions_command_reference.command_selected.connect(self._on_functions_insert)
        self.functions_palette.function_selected.connect(self._on_functions_insert)

        # Three tabs as required: Command Reference, Function Palette, AI Assistant (in strategy editor)
        functions_tabs.addTab(self.functions_command_reference, "📚 Commands")
        functions_tabs.addTab(self.functions_palette, "🔧 Functions")

        self.functions_dock.setWidget(functions_tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.functions_dock)

    def _create_central_widget(self):
        """Create central widget with Tabs for different view modes.

        Tabs:
        0: Pattern Builder (Visual)
        1: Code Editor (Script)
        2: Chart View (Reference)
        3: Split View (Visual + Script side-by-side)
        4: JSON Editor (Generic JSON editing)
        """
        # Lazy import to avoid circular import
        from ...widgets.pattern_builder.pattern_canvas import PatternBuilderCanvas

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

        # 5. JSON Editor View (Generic JSON editing)
        self.regime_editor = RegimeEditorWidget(self)
        self.central_tabs.addTab(self.regime_editor, cel_icons.regime, "JSON Editor")

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
