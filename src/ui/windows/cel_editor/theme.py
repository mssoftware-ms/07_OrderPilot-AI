"""CEL Editor Theme Constants - Dark theme colors aligned with OrderPilot-AI.

Based on OrderPilot-AI standard dark theme (#1e1e1e).
Derived from UI Study but adapted for consistency.
"""

# Primary Colors (OrderPilot-AI standard)
BACKGROUND_PRIMARY = '#1e1e1e'      # Main background
BACKGROUND_SECONDARY = '#2d2d2d'    # Secondary surfaces
BACKGROUND_TERTIARY = '#252525'     # Elevated surfaces

# Accent Colors (Trading Bot style)
ACCENT_CYAN = '#00d9ff'             # Primary accent (info)
ACCENT_TEAL = '#26a69a'             # Success / Bullish
ACCENT_ORANGE = '#ffa726'           # Warning / Neutral
ACCENT_RED = '#ef5350'              # Error / Bearish

# Text Colors
TEXT_PRIMARY = '#e0e0e0'            # Main text
TEXT_SECONDARY = '#b0b0b0'          # Secondary text
TEXT_TERTIARY = '#808080'           # Disabled text

# Border & Hover
BORDER = '#404040'                  # Borders and separators
BORDER_LIGHT = '#4a4a4a'            # Lighter borders
HOVER = '#353535'                   # Hover background
SELECTION = '#2a4f6a'               # Selection background

# Candle Colors (Pattern Builder)
CANDLE_BULLISH_BODY = '#00c853'     # Bullish candle fill
CANDLE_BULLISH_BORDER = '#00e676'   # Bullish candle border
CANDLE_BEARISH_BODY = '#ff3d71'     # Bearish candle fill
CANDLE_BEARISH_BORDER = '#ff6b8a'   # Bearish candle border
CANDLE_DOJI_BODY = '#9aa0a6'        # Doji candle fill
CANDLE_DOJI_BORDER = '#b8bcc4'      # Doji candle border

# Relation Line Colors (Pattern Builder)
RELATION_GREATER = '#00c853'        # Green (>)
RELATION_LESS = '#ff3d71'           # Red (<)
RELATION_EQUAL = '#ffab00'          # Orange (≈)
RELATION_NEAR = '#00d9ff'           # Cyan (near)

# Grid Colors (Pattern Builder Canvas)
GRID_MAJOR = '#2a2a2a'              # Major grid lines (50px)
GRID_MINOR = '#242424'              # Minor grid lines (10px)

# AI Assistant Colors
AI_SUGGESTION_BG = '#2a3f5f'        # Suggestion card background
AI_SUGGESTION_BORDER = '#4a90e2'    # Suggestion card border

# Status Colors
STATUS_SUCCESS = '#26a69a'          # Validation success
STATUS_WARNING = '#ffa726'          # Validation warning
STATUS_ERROR = '#ef5350'            # Validation error
STATUS_INFO = '#00d9ff'             # Info messages

# Code Editor Colors (QScintilla)
EDITOR_BACKGROUND = '#1e1e1e'       # Code editor background
EDITOR_LINE_NUMBER_BG = '#2d2d2d'   # Line number area
EDITOR_LINE_NUMBER_FG = '#808080'   # Line number text
EDITOR_CURRENT_LINE = '#2a2a2a'     # Current line highlight
EDITOR_SELECTION = '#2a4f6a'        # Text selection

# Syntax Highlighting
SYNTAX_KEYWORD = '#569cd6'          # Keywords (and, or, if)
SYNTAX_FUNCTION = '#dcdcaa'         # Functions (rsi, ema)
SYNTAX_NUMBER = '#b5cea8'           # Numbers
SYNTAX_STRING = '#ce9178'           # Strings
SYNTAX_COMMENT = '#6a9955'          # Comments
SYNTAX_OPERATOR = '#d4d4d4'         # Operators (+, -, *, /)
SYNTAX_VARIABLE = '#9cdcfe'         # Variables (trade.pnl_pct)

# Dock Widget Colors
DOCK_TITLE_BG = '#2d2d2d'           # Dock title background
DOCK_TITLE_TEXT = '#ffa726'         # Dock title text (orange)
DOCK_BORDER = '#404040'             # Dock borders

# Toolbar Colors
TOOLBAR_BG = '#2d2d2d'              # Toolbar background
TOOLBAR_SEPARATOR = '#404040'       # Toolbar separator

# Button Colors
BUTTON_PRIMARY_BG = '#4a90e2'       # Primary button (AI Generate)
BUTTON_PRIMARY_HOVER = '#5fa3f5'    # Primary button hover
BUTTON_PRIMARY_PRESSED = '#357abd'  # Primary button pressed
BUTTON_SUCCESS_BG = '#26a69a'       # Success button (Apply)
BUTTON_SUCCESS_HOVER = '#2bbbad'    # Success button hover
BUTTON_WARNING_BG = '#ffa726'       # Warning button
BUTTON_DANGER_BG = '#ef5350'        # Danger button (Delete)

# Chart View Colors (for future integration)
CHART_BACKGROUND = '#1e1e1e'        # Chart background
CHART_GRID = '#2a2a2a'              # Chart grid lines
CHART_CROSSHAIR = '#808080'         # Crosshair color

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

    /* Toolbar */
    QToolBar {{
        background: {TOOLBAR_BG};
        border: none;
        spacing: 5px;
        padding: 5px;
    }}

    QToolBar::separator {{
        background: {TOOLBAR_SEPARATOR};
        width: 1px;
        margin: 5px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {BACKGROUND_SECONDARY};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 3px;
        padding: 5px 10px;
        font-weight: normal;
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
        padding: 10px 20px;
        margin: 2px;
        border: 1px solid {BORDER};
        border-bottom: none;
        border-radius: 5px 5px 0 0;
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
