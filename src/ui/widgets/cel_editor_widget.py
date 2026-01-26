"""
CEL Expression Editor Widget with Syntax Highlighting and Autocomplete.

Provides a code editor for Google CEL expressions with:
- Syntax highlighting
- Autocomplete for indicators, functions, variables
- Error markers
- Line numbers
- Code folding
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QToolBar
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QPlainTextEdit

try:
    from PyQt6.Qsci import QsciScintilla, QsciAPIs
    QSCI_AVAILABLE = True
except ImportError:
    QSCI_AVAILABLE = False

    class QsciAPIs:
        def __init__(self, *_):
            pass

        def add(self, *_):
            return None

        def prepare(self):
            return None

    class QsciScintilla(QPlainTextEdit):
        """Lightweight fallback to keep editor usable without QScintilla."""

        class MarginType:
            NumberMargin = 0
            SymbolMargin = 1

        class FoldStyle:
            BoxedTreeFoldStyle = 0

        class MarkerSymbol:
            Circle = 0

        class AutoCompletionSource:
            AcsAPIs = 0

        class BraceMatch:
            SloppyBraceMatch = 0

        def text(self) -> str:
            return self.toPlainText()

        # Stubs for QScintilla API used in configuration
        def setLexer(self, *_): pass
        def setMarginType(self, *_): pass
        def setMarginWidth(self, *_): pass
        def setMarginsForegroundColor(self, *_): pass
        def setMarginsBackgroundColor(self, *_): pass
        def setFolding(self, *_): pass
        def setAutoCompletionSource(self, *_): pass
        def setAutoCompletionThreshold(self, *_): pass
        def setAutoCompletionCaseSensitivity(self, *_): pass
        def setAutoCompletionReplaceWord(self, *_): pass
        def setBraceMatching(self, *_): pass
        def setMatchedBraceBackgroundColor(self, *_): pass
        def setMatchedBraceForegroundColor(self, *_): pass
        def markerDefine(self, *_): return 0
        def setMarkerBackgroundColor(self, *_): pass
        def setIndentationsUseTabs(self, *_): pass
        def setTabWidth(self, *_): pass
        def setIndentationGuides(self, *_): pass
        def setAutoIndent(self, *_): pass
        def setPaper(self, *_): pass
        def setCaretForegroundColor(self, *_): pass
        def setCaretLineVisible(self, *_): pass
        def setCaretLineBackgroundColor(self, *_): pass
        def setSelectionBackgroundColor(self, *_): pass

from .cel_lexer import CelLexer

if TYPE_CHECKING:
    pass


class CelEditorWidget(QWidget):
    """CEL Script Editor with syntax highlighting and autocomplete."""

    code_changed = pyqtSignal(str)  # Emitted when code changes
    validation_requested = pyqtSignal(str)  # Emitted when validation requested
    ai_generation_requested = pyqtSignal(str)  # Emitted when AI generation requested

    def __init__(self, parent: Optional[QWidget] = None, workflow_type: str = "entry"):
        super().__init__(parent)

        self.workflow_type = workflow_type
        self._setup_ui()
        self._load_autocomplete_data()

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header with workflow label
        header_layout = QHBoxLayout()

        workflow_labels = {
            "entry": "Entry Conditions",
            "exit": "Exit Conditions",
            "before_exit": "Before Exit Logic",
            "update_stop": "Stop Update Logic"
        }

        header_label = QLabel(f"<b>{workflow_labels.get(self.workflow_type, 'CEL Script')}</b>")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Toolbar
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # AI Generate button
        self.generate_btn = QPushButton("🤖 Generate")
        self.generate_btn.setToolTip("Generate CEL code with AI (OpenAI GPT-5.2)")
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5fa3f5;
            }
            QPushButton:pressed {
                background-color: #357abd;
            }
        """)
        toolbar.addWidget(self.generate_btn)

        # Validate button
        self.validate_btn = QPushButton("✓ Validate")
        self.validate_btn.setToolTip("Validate CEL expression syntax")
        self.validate_btn.clicked.connect(self._on_validate_clicked)
        toolbar.addWidget(self.validate_btn)

        # Format button
        self.format_btn = QPushButton("🔧 Format")
        self.format_btn.setToolTip("Format CEL code")
        self.format_btn.clicked.connect(self._on_format_clicked)
        toolbar.addWidget(self.format_btn)

        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setToolTip("Clear editor")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        toolbar.addWidget(self.clear_btn)

        header_layout.addWidget(toolbar)
        layout.addLayout(header_layout)

        # Code editor
        self.editor = QsciScintilla()
        self._configure_editor()
        layout.addWidget(self.editor)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)

        # Connect signals
        self.editor.textChanged.connect(self._on_text_changed)

    def _configure_editor(self):
        """Configure QScintilla editor."""
        # Font
        font = QFont("Consolas", 10)
        self.editor.setFont(font)
        if not QSCI_AVAILABLE:
            # Plain text fallback
            self.error_marker = 0
            self.lexer = None
            return

        self.editor.setMarginsFont(font)

        # Lexer (syntax highlighting)
        self.lexer = CelLexer(self.editor)
        self.editor.setLexer(self.lexer)

        # Line numbers
        self.editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.editor.setMarginWidth(0, "00000")
        self.editor.setMarginsForegroundColor(QColor("#858585"))
        self.editor.setMarginsBackgroundColor(QColor("#1e1e1e"))

        # Folding
        self.editor.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        self.editor.setMarginType(1, QsciScintilla.MarginType.SymbolMargin)
        self.editor.setMarginWidth(1, 15)

        # Error marker
        self.error_marker = self.editor.markerDefine(
            QsciScintilla.MarkerSymbol.Circle
        )
        self.editor.setMarkerBackgroundColor(QColor("#ff0000"), self.error_marker)

        # Autocomplete
        self.editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAPIs)
        self.editor.setAutoCompletionThreshold(2)
        self.editor.setAutoCompletionCaseSensitivity(False)
        self.editor.setAutoCompletionReplaceWord(True)

        # Brace matching
        self.editor.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.editor.setMatchedBraceBackgroundColor(QColor("#3a3a3a"))
        self.editor.setMatchedBraceForegroundColor(QColor("#ffff00"))

        # Indentation
        self.editor.setIndentationsUseTabs(False)
        self.editor.setTabWidth(2)
        self.editor.setIndentationGuides(True)
        self.editor.setAutoIndent(True)

        # Background color
        self.editor.setPaper(QColor("#1e1e1e"))
        self.editor.setCaretForegroundColor(QColor("#ffffff"))
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor("#2a2a2a"))

        # Selection colors
        self.editor.setSelectionBackgroundColor(QColor("#264f78"))

    def _load_autocomplete_data(self):
        """Load autocomplete data from CEL functions."""
        if not QSCI_AVAILABLE:
            self.api = None
            return
        self.api = QsciAPIs(self.lexer)

        # Math functions
        math_funcs = [
            'abs(value)', 'min(a, b)', 'max(a, b)', 'round(value)',
            'floor(value)', 'ceil(value)', 'pow(x, y)', 'sqrt(value)',
            'log(value)', 'log10(value)', 'sin(x)', 'cos(x)', 'tan(x)',
            'sum(...)', 'avg(...)', 'average(...)'
        ]

        # Trading functions
        trading_funcs = [
            'is_trade_open()', 'is_long()', 'is_short()',
            'is_bullish_signal()', 'is_bearish_signal()',
            'in_regime(regime)', 'stop_hit_long()', 'stop_hit_short()',
            'tp_hit()', 'price_above_ema(period)', 'price_below_ema(period)',
            'price_above_level(level)', 'price_below_level(level)',
            'isnull(value)', 'isnotnull(value)', 'nz(value, default)',
            'coalesce(...)', 'clamp(value, min, max)',
            'pct_change(old, new)', 'pct_from_level(price, level)',
            'level_at_pct(entry, pct, side)', 'retracement(from, to, pct)',
            'extension(from, to, pct)'
        ]

        # Array/Collection functions
        collection_funcs = [
            'size(array)', 'length(array)', 'has(array, element)',
            'all(array, condition)', 'any(array, condition)',
            'map(array, expr)', 'filter(array, condition)',
            'first(array)', 'last(array)', 'contains(array, element)',
            'indexOf(array, element)', 'distinct(array)', 'sort(array)',
            'reverse(array)', 'slice(array, start, end)'
        ]

        # Type functions
        type_funcs = [
            'type(value)', 'string(value)', 'int(value)',
            'double(value)', 'bool(value)'
        ]

        # String functions
        string_funcs = [
            'contains(string, substring)', 'startsWith(string, prefix)',
            'endsWith(string, suffix)', 'toLowerCase(string)',
            'toUpperCase(string)', 'substring(string, start, end)',
            'split(string, delimiter)', 'join(array, delimiter)'
        ]

        # Indicators (18 types with common periods)
        indicators = [
            # RSI
            'rsi5.value', 'rsi7.value', 'rsi14.value', 'rsi21.value',
            # EMA
            'ema8.value', 'ema21.value', 'ema34.value', 'ema50.value', 'ema89.value', 'ema200.value',
            # SMA
            'sma20.value', 'sma50.value', 'sma100.value', 'sma200.value',
            # MACD
            'macd_12_26_9.value', 'macd_12_26_9.signal', 'macd_12_26_9.histogram',
            # Stochastic
            'stoch_5_3_3.k', 'stoch_5_3_3.d', 'stoch_14_3_3.k', 'stoch_14_3_3.d',
            # ADX
            'adx14.value', 'adx14.plus_di', 'adx14.minus_di',
            # ATR
            'atr14.value',
            # Bollinger Bands
            'bb_20_2.upper', 'bb_20_2.middle', 'bb_20_2.lower', 'bb_20_2.width',
            # CCI
            'cci20.value',
            # MFI
            'mfi14.value',
            # Volume
            'volume.value', 'volume_ratio_20.value',
            # Price
            'price.value', 'price_change_14.value',
            # Momentum
            'momentum_score_14.value', 'price_strength_14.value',
            # CHOP
            'chop14.value',
            # Patterns
            'candlestick_patterns.count', 'candlestick_patterns.patterns'
        ]

        # Variables
        variables = [
            'trade.id', 'trade.strategy', 'trade.side',
            'trade.entry_price', 'trade.current_price', 'trade.leverage',
            'trade.invest_usdt', 'trade.stop_price', 'trade.sl_pct',
            'trade.tr_pct', 'trade.tra_pct', 'trade.tr_lock_pct',
            'trade.tr_stop_price', 'trade.status', 'trade.pnl_pct',
            'trade.pnl_usdt', 'trade.fees_pct', 'trade.fees_usdt',
            'trade.age_sec', 'trade.bars_in_trade', 'trade.mfe_pct',
            'trade.mae_pct', 'trade.is_open',
            'cfg.min_volume_pctl', 'cfg.min_volume_window',
            'cfg.min_atrp_pct', 'cfg.max_atrp_pct',
            'cfg.max_spread_bps', 'cfg.min_depth',
            'cfg.max_leverage', 'cfg.max_fees_pct',
            'cfg.no_trade_regimes', 'cfg.min_obi', 'cfg.min_range_pct',
            'regime', 'direction', 'open', 'high', 'low', 'close', 'volume',
            'atrp', 'atr', 'bbwidth', 'squeeze_on',
            'spread_bps', 'depth_bid', 'depth_ask', 'obi'
        ]

        # Keywords
        keywords = ['true', 'false', 'null', 'in', 'has']

        # Add all to autocomplete
        for func in (math_funcs + trading_funcs + collection_funcs +
                     type_funcs + string_funcs + indicators + variables + keywords):
            self.api.add(func)

        # Prepare autocomplete
        self.api.prepare()

    def _on_text_changed(self):
        """Handle text change."""
        code = self.editor.text()
        self.code_changed.emit(code)

        # Update status
        line_count = self.editor.lines()
        self.status_label.setText(f"Lines: {line_count}")

    def _on_generate_clicked(self):
        """Generate CEL code with AI."""
        # Emit signal to parent (Pattern Integration Widget)
        # Parent will provide pattern context and call AI helper
        self.ai_generation_requested.emit(self.workflow_type)

    def _on_validate_clicked(self):
        """Validate CEL expression."""
        code = self.editor.text().strip()

        if not code:
            QMessageBox.warning(self, "Validation", "Editor is empty")
            return

        # Emit validation request signal
        self.validation_requested.emit(code)

    def _on_format_clicked(self):
        """Format CEL code (basic formatting)."""
        code = self.editor.text().strip()

        if not code:
            return

        # Basic formatting: add spaces around operators
        formatted = code
        for op in ['==', '!=', '<=', '>=', '&&', '||']:
            formatted = formatted.replace(op, f' {op} ')
        for op in ['<', '>', '+', '-', '*', '/', '%']:
            # Don't format if part of comparison operator
            if op not in ['<', '>'] or (op + '=') not in formatted:
                formatted = formatted.replace(op, f' {op} ')

        # Remove double spaces
        while '  ' in formatted:
            formatted = formatted.replace('  ', ' ')

        # Set formatted code
        self.editor.setText(formatted)

    def _on_clear_clicked(self):
        """Clear editor."""
        if self.editor.text().strip():
            reply = QMessageBox.question(
                self, "Clear Editor",
                "Are you sure you want to clear the editor?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.editor.clear()

    def set_code(self, code: str):
        """Set code in editor."""
        self.editor.setText(code)

    def get_code(self) -> str:
        """Get code from editor."""
        return self.editor.text().strip()

    def clear_error_markers(self):
        """Clear all error markers."""
        self.editor.markerDeleteAll(self.error_marker)

    def add_error_marker(self, line: int):
        """Add error marker at line."""
        self.editor.markerAdd(line, self.error_marker)

    def set_readonly(self, readonly: bool):
        """Set editor readonly status."""
        self.editor.setReadOnly(readonly)

    def insert_text(self, text: str):
        """Insert text at current cursor position."""
        self.editor.insert(text)
