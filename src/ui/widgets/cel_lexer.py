"""
CEL Expression Language Lexer for QScintilla.

Custom lexer for Google CEL (Common Expression Language) syntax highlighting.
Provides a lightweight fallback when QScintilla is not available, so tests can
import the lexer even in headless CI environments.
"""

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QPlainTextEdit

try:
    from PyQt6.Qsci import QsciLexerCustom, QsciScintilla
    QSCI_AVAILABLE = True
except ImportError:
    QSCI_AVAILABLE = False

    class QsciLexerCustom:
        def __init__(self, *args, **kwargs):
            super().__init__()

        def startStyling(self, *_):
            return None

        def setStyling(self, *_):
            return None

        def editor(self):
            return None

    class QsciScintilla(QPlainTextEdit):
        """Minimal stub with QPlainTextEdit backing."""

        def text(self) -> str:
            return self.toPlainText()


try:
    from src.core.tradingbot.cel.cel_validator import CelValidator as CoreCelValidator
    CORE_FUNCTIONS = set(CoreCelValidator.BUILTIN_FUNCTIONS)
except Exception:
    CoreCelValidator = None
    CORE_FUNCTIONS = set()

from src.ui.widgets.syntax_handlers import (
    HandlerRegistry,
    WhitespaceHandler,
    CommentHandler,
    StringHandler,
    NumberHandler,
    OperatorHandler,
    IdentifierHandler,
    DefaultHandler,
)


class CelLexer(QsciLexerCustom):
    """Custom lexer for CEL expression language."""

    # Token types
    DEFAULT = 0
    KEYWORD = 1
    OPERATOR = 2
    NUMBER = 3
    STRING = 4
    COMMENT = 5
    IDENTIFIER = 6
    INDICATOR = 7
    FUNCTION = 8
    VARIABLE = 9

    # CEL Keywords
    KEYWORDS = {
        'true', 'false', 'null',
        'in', 'has', 'all', 'any',
        'map', 'filter', 'first', 'last',
        'size', 'type', 'string', 'int', 'double', 'bool'
    }

    # Trading-specific keywords
    TRADING_KEYWORDS = {
        'trade', 'cfg', 'regime', 'direction',
        'open', 'high', 'low', 'close', 'volume',
        'atrp', 'atr', 'bbwidth', 'squeeze_on',
        'spread_bps', 'depth_bid', 'depth_ask', 'obi'
    }

    # CEL Operators
    OPERATORS = {
        '==', '!=', '<', '>', '<=', '>=',
        '&&', '||', '!',
        '+', '-', '*', '/', '%',
        '?', ':'
    }

    # Known functions (synced to core CEL validator if available)
    ALL_FUNCTIONS = CORE_FUNCTIONS or {
        'abs', 'min', 'max', 'clamp', 'round', 'floor', 'ceil', 'sqrt', 'pow', 'exp',
        'type', 'string', 'int', 'double', 'bool', 'timestamp',
        'contains', 'startsWith', 'endsWith', 'toLowerCase', 'toUpperCase',
        'substring', 'split', 'join',
        'size', 'length', 'has', 'all', 'any', 'map', 'filter',
        'first', 'last', 'indexOf', 'slice', 'distinct', 'sort', 'reverse',
        'sum', 'avg', 'average',
        'isnull', 'nz', 'coalesce',
        'pctl', 'crossover',
        'pct_change', 'pct_from_level', 'level_at_pct', 'retracement', 'extension',
        'is_trade_open', 'is_long', 'is_short', 'is_bullish_signal', 'is_bearish_signal', 'in_regime',
        'stop_hit_long', 'stop_hit_short', 'tp_hit',
        'price_above_ema', 'price_below_ema', 'price_above_level', 'price_below_level',
        'highest', 'lowest', 'sma',
        'now', 'timestamp', 'bar_age', 'bars_since', 'is_new_day', 'is_new_hour', 'is_new_week', 'is_new_month',
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set default font
        self.default_font = QFont("Consolas", 10)

        # Initialize handler registry (lazy initialization)
        self._handler_registry = None

    def description(self, style: int) -> str:
        """Return description for each style."""
        descriptions = {
            self.DEFAULT: "Default",
            self.KEYWORD: "Keyword",
            self.OPERATOR: "Operator",
            self.NUMBER: "Number",
            self.STRING: "String",
            self.COMMENT: "Comment",
            self.IDENTIFIER: "Identifier",
            self.INDICATOR: "Indicator",
            self.FUNCTION: "Function",
            self.VARIABLE: "Variable"
        }
        return descriptions.get(style, "")

    def defaultColor(self, style: int) -> QColor:
        """Return default color for each style."""
        colors = {
            self.DEFAULT: QColor("#d4d4d4"),
            self.KEYWORD: QColor("#569cd6"),       # Blue
            self.OPERATOR: QColor("#d4d4d4"),
            self.NUMBER: QColor("#b5cea8"),        # Green
            self.STRING: QColor("#ce9178"),        # Orange
            self.COMMENT: QColor("#6a9955"),       # Green
            self.IDENTIFIER: QColor("#d4d4d4"),
            self.INDICATOR: QColor("#4ec9b0"),     # Cyan
            self.FUNCTION: QColor("#dcdcaa"),      # Yellow
            self.VARIABLE: QColor("#9cdcfe")       # Light Blue
        }
        return colors.get(style, QColor("#d4d4d4"))

    def defaultFont(self, style: int) -> QFont:
        """Return default font for each style."""
        font = QFont(self.default_font)

        if style == self.KEYWORD:
            font.setBold(True)
        elif style == self.FUNCTION:
            font.setBold(True)
        elif style == self.INDICATOR:
            font.setItalic(True)

        return font

    def _init_handler_registry(self):
        """
        Initialize the handler registry with all token handlers.

        Handlers are registered with their priorities for ordered matching.
        """
        registry = HandlerRegistry()

        # Register handlers in any order (registry will sort by priority)
        registry.register(WhitespaceHandler(self.DEFAULT))
        registry.register(CommentHandler(self.COMMENT))
        registry.register(StringHandler(self.STRING))
        registry.register(NumberHandler(self.NUMBER))
        registry.register(OperatorHandler(
            self.OPERATOR,
            {'==', '!=', '<=', '>=', '&&', '||'},
            '<>=!+-*/%?:'
        ))
        registry.register(IdentifierHandler(
            self.KEYWORDS,
            self.TRADING_KEYWORDS,
            self.ALL_FUNCTIONS,
            {'trade', 'cfg'},
            self.KEYWORD,
            self.FUNCTION,
            self.VARIABLE,
            self.INDICATOR,
            self.IDENTIFIER
        ))
        registry.register(DefaultHandler(self.DEFAULT))

        self._handler_registry = registry

    def styleText(self, start: int, end: int):
        """
        Perform syntax highlighting using Token Handler Pattern.

        Args:
            start: Start position in text
            end: End position in text
        """
        editor = self.editor()
        if not editor:
            return

        # Lazy initialize handler registry
        if self._handler_registry is None:
            self._init_handler_registry()

        # Get text to highlight
        text = editor.text()[start:end]

        # Initialize styling
        self.startStyling(start)

        # Process text using handlers
        position = 0
        while position < len(text):
            match = self._handler_registry.try_match(text, position)

            if match.matched:
                self.setStyling(match.length, match.style)
                position += match.length
            else:
                # Should never happen with DefaultHandler, but safety fallback
                self.setStyling(1, self.DEFAULT)
                position += 1
