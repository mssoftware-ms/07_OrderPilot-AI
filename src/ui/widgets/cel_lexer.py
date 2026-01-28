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

    def styleText(self, start: int, end: int):
        """Perform syntax highlighting."""
        editor = self.editor()
        if not editor:
            return

        # Get text to highlight
        text = editor.text()[start:end]

        # Initialize styling
        self.startStyling(start)

        i = 0
        while i < len(text):
            # Skip whitespace
            if text[i].isspace():
                self.setStyling(1, self.DEFAULT)
                i += 1
                continue

            # Comments (// style)
            if i < len(text) - 1 and text[i:i+2] == '//':
                # Find end of line
                end_comment = text.find('\n', i)
                if end_comment == -1:
                    end_comment = len(text)
                comment_len = end_comment - i
                self.setStyling(comment_len, self.COMMENT)
                i += comment_len
                continue

            # Strings (double quotes)
            if text[i] == '"':
                j = i + 1
                # Find closing quote
                while j < len(text):
                    if text[j] == '"' and text[j-1] != '\\':
                        break
                    j += 1
                string_len = j - i + 1
                self.setStyling(string_len, self.STRING)
                i += string_len
                continue

            # Strings (single quotes)
            if text[i] == "'":
                j = i + 1
                # Find closing quote
                while j < len(text):
                    if text[j] == "'" and text[j-1] != '\\':
                        break
                    j += 1
                string_len = j - i + 1
                self.setStyling(string_len, self.STRING)
                i += string_len
                continue

            # Numbers
            if text[i].isdigit() or (text[i] == '.' and i+1 < len(text) and text[i+1].isdigit()):
                j = i + 1
                has_dot = text[i] == '.'
                while j < len(text):
                    if text[j].isdigit():
                        j += 1
                    elif text[j] == '.' and not has_dot:
                        has_dot = True
                        j += 1
                    else:
                        break
                num_len = j - i
                self.setStyling(num_len, self.NUMBER)
                i += num_len
                continue

            # Operators (multi-char)
            for op in ['==', '!=', '<=', '>=', '&&', '||']:
                if i < len(text) - 1 and text[i:i+2] == op:
                    self.setStyling(2, self.OPERATOR)
                    i += 2
                    break
            else:
                # Operators (single-char)
                if text[i] in '<>=!+-*/%?:':
                    self.setStyling(1, self.OPERATOR)
                    i += 1
                    continue

                # Identifiers, keywords, functions
                if text[i].isalpha() or text[i] == '_':
                    j = i + 1
                    while j < len(text) and (text[j].isalnum() or text[j] in '_'):
                        j += 1

                    word = text[i:j]
                    word_len = j - i

                    # Check for indicator access (e.g., rsi14.value)
                    if j < len(text) - 1 and text[j] == '.':
                        # This is an indicator
                        # Find end of property access
                        k = j + 1
                        while k < len(text) and (text[k].isalnum() or text[k] == '_'):
                            k += 1
                        self.setStyling(k - i, self.INDICATOR)
                        i = k
                        continue

                    # Keywords
                    if word in self.KEYWORDS or word in self.TRADING_KEYWORDS:
                        self.setStyling(word_len, self.KEYWORD)
                    # Functions
                    elif word in self.ALL_FUNCTIONS:
                        self.setStyling(word_len, self.FUNCTION)
                    # Variables (trade., cfg.)
                    elif word in {'trade', 'cfg'}:
                        self.setStyling(word_len, self.VARIABLE)
                    # Default identifier
                    else:
                        self.setStyling(word_len, self.IDENTIFIER)

                    i += word_len
                    continue

                # Default (punctuation, etc.)
                self.setStyling(1, self.DEFAULT)
                i += 1
