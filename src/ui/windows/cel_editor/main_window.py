"""CEL Editor Main Window - Interactive Pattern Builder with AI Assistance.

This is a standalone window implementing a professional visual pattern builder
for CEL (Common Expression Language) trading strategies.

Architecture:
- Dock-widget layout (Left/Center/Right) inspired by VS Code
- Central Pattern Builder Canvas (QGraphicsView)
- CEL Code Editor (QScintilla) with syntax highlighting
- AI Assistant panel (GPT-5.2) for pattern suggestions
- Pattern Library with templates

Phase 3 Refactoring:
This file has been split into 4 focused modules using mixins:
- main_window.py (this file): Main class, initialization, orchestration
- main_window_ui.py: UI setup (menus, toolbars, docks, central widget, status bar)
- main_window_events.py: Event handlers (signals, slots, user interactions)
- main_window_logic.py: Business logic (file I/O, state management, validation)

Based on UI Study but adapted to PyQt6 and OrderPilot-AI theme.

Author: CODER-009 (Claude Sonnet 4.5)
Date: 2026-01-31
Task: 3.1.1 - Split cel_editor/main_window.py (1798 LOC → 4 files)
"""

from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSignal
from pathlib import Path

from ...app_icon import set_window_icon  # Issue #29: App icon
from src.core.tradingbot.cel.models import RulePack, Rule

# Import mixins for modular architecture
from .main_window_ui import CelEditorWindowUIMixin
from .main_window_events import CelEditorWindowEventsMixin
from .main_window_logic import CelEditorWindowLogicMixin
from src.ui.debug import UIInspectorMixin  # F12 UI Inspector


class CelEditorWindow(
    UIInspectorMixin,  # F12 UI Inspector - must be before QMainWindow
    CelEditorWindowUIMixin,
    CelEditorWindowEventsMixin,
    CelEditorWindowLogicMixin,
    QMainWindow
):
    """Main window for CEL Editor - Interactive Pattern Builder.

    This class orchestrates the CEL Editor window by inheriting functionality
    from three specialized mixins:

    - CelEditorWindowUIMixin: Creates all UI components (menus, toolbars, docks)
    - CelEditorWindowEventsMixin: Handles all user interactions and events
    - CelEditorWindowLogicMixin: Implements business logic (file I/O, validation)

    Features:
    - Dock-widget layout (Left: Library, Center: Canvas/Editor, Right: Properties/AI)
    - View modes: Pattern Builder | Code Editor | Chart View | Split View
    - Toolbar with common actions (New, Open, Save, Undo, Redo)
    - Menu bar (File, Edit, View, Help)
    - Status bar with validation feedback
    - AI Assistant integration (GPT-5.2)
    - RulePack editing support
    - Generic JSON editor

    Signals:
        pattern_changed: Emitted when pattern is modified
        view_mode_changed(str): Emitted when view mode changes
        closed: Emitted when window is closed (Issue #27)
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

        # === Instance Variables ===

        # Strategy state
        self.strategy_name = strategy_name
        self.current_view_mode = "pattern"  # pattern, code, chart, split
        self.current_file: Path | None = None  # Current strategy file
        self.modified = False  # Track unsaved changes

        # Pattern → CEL translator
        # Lazy import to avoid circular import
        from ...widgets.pattern_builder.pattern_to_cel import PatternToCelTranslator
        self.translator = PatternToCelTranslator()

        # RulePack state
        self.current_rulepack: RulePack | None = None  # Loaded RulePack
        self.current_rulepack_file: Path | None = None  # RulePack file path
        self.rulepack_mode = False  # True if RulePack is loaded (vs Strategy)
        self.selected_rule: Rule | None = None  # Currently selected rule for editing
        self.selected_pack_type: str | None = None
        self._rulepack_editor_loading = False

        # === UI Initialization (delegated to mixins) ===

        # Window setup (CelEditorWindowUIMixin)
        self._setup_window()

        # Create UI components (CelEditorWindowUIMixin)
        self._create_menu_bar()
        self._create_toolbar()
        self._create_candle_toolbar()  # Phase 2.5: Candle type selector
        self._create_dock_widgets()
        self._create_central_widget()
        self._create_status_bar()

        # Apply theme (CelEditorWindowUIMixin)
        self._apply_theme()

        # Restore window state (CelEditorWindowLogicMixin)
        self._restore_state()

        # Connect signals (CelEditorWindowEventsMixin)
        self._connect_signals()

        # Ensure UI state (sidebars, toolbars) matches initial view mode (pattern)
        # This fixes Issue where tools were not shown at startup.
        # (CelEditorWindowEventsMixin)
        self._switch_view_mode(self.current_view_mode)

        # F12 UI Inspector Debug Overlay
        self.setup_ui_inspector()
