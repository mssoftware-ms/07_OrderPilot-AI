"""CEL Editor Theme Constants - Dark theme colors aligned with OrderPilot-AI.

Based on OrderPilot-AI standard dark theme (#1e1e1e).
Derived from UI Study but adapted for consistency.
"""

from src.ui.design_system import DARK_ORANGE_PALETTE

# Primary Colors (OrderPilot-AI standard)
BACKGROUND_PRIMARY = DARK_ORANGE_PALETTE.background_main
BACKGROUND_SECONDARY = DARK_ORANGE_PALETTE.background_surface
BACKGROUND_TERTIARY = DARK_ORANGE_PALETTE.background_input

# Accent Colors (Trading Bot style)
ACCENT_CYAN = DARK_ORANGE_PALETTE.primary  # Using Primary Orange as main accent
ACCENT_TEAL = DARK_ORANGE_PALETTE.success
ACCENT_ORANGE = DARK_ORANGE_PALETTE.warning # Warning is Red/Pink in palette, maybe use primary?
ACCENT_RED = DARK_ORANGE_PALETTE.error

# Text Colors
TEXT_PRIMARY = DARK_ORANGE_PALETTE.text_primary
TEXT_SECONDARY = DARK_ORANGE_PALETTE.text_secondary
TEXT_TERTIARY = "#5E6673"  # Custom disabled color if not in palette

# Border & Hover
BORDER = DARK_ORANGE_PALETTE.border_main
BORDER_LIGHT = DARK_ORANGE_PALETTE.border_main
HOVER = DARK_ORANGE_PALETTE.background_input
SELECTION = DARK_ORANGE_PALETTE.selection_bg

# Candle Colors (Pattern Builder)
CANDLE_BULLISH_BODY = DARK_ORANGE_PALETTE.success
CANDLE_BULLISH_BORDER = DARK_ORANGE_PALETTE.success
CANDLE_BEARISH_BODY = DARK_ORANGE_PALETTE.error
CANDLE_BEARISH_BORDER = DARK_ORANGE_PALETTE.error
CANDLE_DOJI_BODY = DARK_ORANGE_PALETTE.text_secondary
CANDLE_DOJI_BORDER = DARK_ORANGE_PALETTE.text_secondary

# Relation Line Colors (Pattern Builder)
RELATION_GREATER = DARK_ORANGE_PALETTE.success
RELATION_LESS = DARK_ORANGE_PALETTE.error
RELATION_EQUAL = DARK_ORANGE_PALETTE.primary # Orange
RELATION_NEAR = DARK_ORANGE_PALETTE.info

# Grid Colors (Pattern Builder Canvas)
GRID_MAJOR = DARK_ORANGE_PALETTE.border_main
GRID_MINOR = "#23262E"  # Slightly lighter than BG

# AI Assistant Colors
AI_SUGGESTION_BG = DARK_ORANGE_PALETTE.background_surface
AI_SUGGESTION_BORDER = DARK_ORANGE_PALETTE.primary

# Status Colors
STATUS_SUCCESS = DARK_ORANGE_PALETTE.success
STATUS_WARNING = DARK_ORANGE_PALETTE.warning
STATUS_ERROR = DARK_ORANGE_PALETTE.error
STATUS_INFO = DARK_ORANGE_PALETTE.info

# Code Editor Colors (QScintilla)
EDITOR_BACKGROUND = DARK_ORANGE_PALETTE.background_main
EDITOR_LINE_NUMBER_BG = DARK_ORANGE_PALETTE.background_surface
EDITOR_LINE_NUMBER_FG = DARK_ORANGE_PALETTE.text_secondary
EDITOR_CURRENT_LINE = DARK_ORANGE_PALETTE.background_input
EDITOR_SELECTION = DARK_ORANGE_PALETTE.selection_bg

# Syntax Highlighting
SYNTAX_KEYWORD = "#C678DD"          # Purple
SYNTAX_FUNCTION = "#61AFEF"         # Blue 
SYNTAX_NUMBER = "#D19A66"           # Orange
SYNTAX_STRING = "#98C379"           # Green
SYNTAX_COMMENT = "#5C6370"          # Grey
SYNTAX_OPERATOR = "#E06C75"         # Red
SYNTAX_VARIABLE = "#E5C07B"         # Yellow

# Dock Widget Colors
DOCK_TITLE_BG = DARK_ORANGE_PALETTE.background_surface
DOCK_TITLE_TEXT = DARK_ORANGE_PALETTE.primary
DOCK_BORDER = DARK_ORANGE_PALETTE.border_main

# Toolbar Colors
TOOLBAR_BG = DARK_ORANGE_PALETTE.background_surface
TOOLBAR_SEPARATOR = DARK_ORANGE_PALETTE.border_main

# Button Colors
BUTTON_PRIMARY_BG = DARK_ORANGE_PALETTE.primary
BUTTON_PRIMARY_HOVER = DARK_ORANGE_PALETTE.primary_hover
BUTTON_PRIMARY_PRESSED = DARK_ORANGE_PALETTE.primary_pressed
BUTTON_SUCCESS_BG = DARK_ORANGE_PALETTE.success
BUTTON_SUCCESS_HOVER = "#2bbbad"    # Keep custom or derive
BUTTON_WARNING_BG = DARK_ORANGE_PALETTE.warning
BUTTON_DANGER_BG = DARK_ORANGE_PALETTE.error

# Chart View Colors (for future integration)
CHART_BACKGROUND = DARK_ORANGE_PALETTE.background_main
CHART_GRID = DARK_ORANGE_PALETTE.border_main
CHART_CROSSHAIR = DARK_ORANGE_PALETTE.text_secondary

# Comprehensive Theme Dictionary
DARK_THEME = {
    # Backgrounds
    'background_primary': BACKGROUND_PRIMARY,
    'background_secondary': BACKGROUND_SECONDARY,
    'background_tertiary': BACKGROUND_TERTIARY,
    
    # Accents
    'accent': ACCENT_CYAN,
    'accent_teal': ACCENT_TEAL,
    'accent_orange': ACCENT_ORANGE,
    'accent_red': ACCENT_RED,
    
    # Text
    'text_primary': TEXT_PRIMARY,
    'text_secondary': TEXT_SECONDARY,
    'text_tertiary': TEXT_TERTIARY,
    
    # Borders
    'border': BORDER,
    'border_light': BORDER_LIGHT,
    'hover': HOVER,
    'selection': SELECTION,
    
    # Candles
    'candle_bullish_body': CANDLE_BULLISH_BODY,
    'candle_bullish_border': CANDLE_BULLISH_BORDER,
    'candle_bearish_body': CANDLE_BEARISH_BODY,
    'candle_bearish_border': CANDLE_BEARISH_BORDER,
    'candle_doji_body': CANDLE_DOJI_BODY,
    'candle_doji_border': CANDLE_DOJI_BORDER,
    
    # Relations
    'relation_greater': RELATION_GREATER,
    'relation_less': RELATION_LESS,
    'relation_equal': RELATION_EQUAL,
    'relation_near': RELATION_NEAR,
    
    # Grid
    'grid_major': GRID_MAJOR,
    'grid_minor': GRID_MINOR,
    
    # Status
    'status_success': STATUS_SUCCESS,
    'status_warning': STATUS_WARNING,
    'status_error': STATUS_ERROR,
    'status_info': STATUS_INFO,
    
    # Editor
    'editor_background': EDITOR_BACKGROUND,
    'editor_line_number_bg': EDITOR_LINE_NUMBER_BG,
    'editor_line_number_fg': EDITOR_LINE_NUMBER_FG,
    'editor_current_line': EDITOR_CURRENT_LINE,
    'editor_selection': EDITOR_SELECTION,
    
    # Syntax
    'syntax_keyword': SYNTAX_KEYWORD,
    'syntax_function': SYNTAX_FUNCTION,
    'syntax_number': SYNTAX_NUMBER,
    'syntax_string': SYNTAX_STRING,
    'syntax_comment': SYNTAX_COMMENT,
    'syntax_operator': SYNTAX_OPERATOR,
    'syntax_variable': SYNTAX_VARIABLE,
}


def get_qss_stylesheet() -> str:
    """Generate complete QSS stylesheet for CEL Editor.

    Returns:
        Complete QSS stylesheet string for all widgets.
    """
    return f"""
    /* Main Window */
    QMainWindow {{
        background-color: {BACKGROUND_PRIMARY};
        color: {TEXT_PRIMARY};
    }}

    /* Dock Widgets */
    QDockWidget {{
        background: {BACKGROUND_SECONDARY};
        border: 1px solid {BORDER};
        titlebar-close-icon: url(close.png);
        titlebar-normal-icon: url(undock.png);
    }}

    QDockWidget::title {{
        background: {DOCK_TITLE_BG};
        color: {DOCK_TITLE_TEXT};
        padding: 8px;
        font-weight: bold;
        border-bottom: 2px solid {ACCENT_TEAL};
    }}

    /* Toolbar (Compact design) */
    QToolBar {{
        background: {TOOLBAR_BG};
        border: none;
        spacing: 3px;
        padding: 2px 5px;
    }}

    QToolBar::separator {{
        background: {TOOLBAR_SEPARATOR};
        width: 1px;
        margin: 3px;
    }}

    /* Toolbar Buttons (Compact) */
    QToolButton {{
        background-color: {BACKGROUND_SECONDARY};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 3px;
        padding: 3px;
        min-height: 24px;
        max-height: 28px;
        min-width: 24px;
    }}

    QToolButton:hover {{
        background-color: {HOVER};
        border-color: {BORDER_LIGHT};
    }}

    QToolButton:pressed {{
        background-color: {BACKGROUND_PRIMARY};
    }}

    /* Buttons (Compact design) */
    QPushButton {{
        background-color: {BACKGROUND_SECONDARY};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 3px;
        padding: 3px 8px;
        font-weight: normal;
        min-height: 24px;
        max-height: 28px;
    }}

    QPushButton:hover {{
        background-color: {HOVER};
        border-color: {BORDER_LIGHT};
    }}

    QPushButton:pressed {{
        background-color: {BACKGROUND_PRIMARY};
    }}

    QPushButton:disabled {{
        color: {TEXT_TERTIARY};
        background-color: {BACKGROUND_PRIMARY};
    }}

    /* Primary Button (AI Generate) */
    QPushButton#primary {{
        background-color: {BUTTON_PRIMARY_BG};
        color: white;
        font-weight: bold;
    }}

    QPushButton#primary:hover {{
        background-color: {BUTTON_PRIMARY_HOVER};
    }}

    QPushButton#primary:pressed {{
        background-color: {BUTTON_PRIMARY_PRESSED};
    }}

    /* Success Button (Apply) */
    QPushButton#success {{
        background-color: {BUTTON_SUCCESS_BG};
        color: white;
        font-weight: bold;
    }}

    QPushButton#success:hover {{
        background-color: {BUTTON_SUCCESS_HOVER};
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        background: {BACKGROUND_SECONDARY};
    }}

    QTabBar::tab {{
        background: {BACKGROUND_PRIMARY};
        color: {TEXT_SECONDARY};
        padding: 6px 15px;
        margin: 2px;
        border: 1px solid {BORDER};
        border-bottom: none;
        border-radius: 5px 5px 0 0;
        min-height: 20px;
        max-height: 32px;
    }}

    QTabBar::tab:selected {{
        background: {BACKGROUND_SECONDARY};
        color: {DOCK_TITLE_TEXT};
        border-bottom: 2px solid {ACCENT_TEAL};
        font-weight: bold;
    }}

    QTabBar::tab:hover {{
        background: {HOVER};
        color: {ACCENT_TEAL};
    }}

    /* Labels */
    QLabel {{
        color: {TEXT_PRIMARY};
        background: transparent;
    }}

    /* Status Bar */
    QStatusBar {{
        background: {BACKGROUND_SECONDARY};
        color: {TEXT_PRIMARY};
        border-top: 1px solid {BORDER};
    }}

    QStatusBar::item {{
        border: none;
    }}

    /* Scroll Bars */
    QScrollBar:vertical {{
        background: {BACKGROUND_SECONDARY};
        width: 12px;
        border: none;
    }}

    QScrollBar::handle:vertical {{
        background: {BORDER_LIGHT};
        min-height: 20px;
        border-radius: 6px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {HOVER};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {BACKGROUND_TERTIARY};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        padding: 5px;
    }}
    """
