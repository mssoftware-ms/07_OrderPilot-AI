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
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QToolBar
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QPlainTextEdit

logger = logging.getLogger(__name__)

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

# Import CEL Validator
try:
    from ...core.tradingbot.cel.cel_validator import CelValidator, ValidationSeverity
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False
    CelValidator = None
    ValidationSeverity = None

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

        # Initialize CEL Validator
        self.validator = CelValidator() if VALIDATOR_AVAILABLE else None

        # Validation timer for debouncing (500ms)
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._perform_validation)

        # Variables autocomplete handler (Phase 3.3)
        self.variables_autocomplete = None
        self._init_variables_autocomplete()

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

        # Variables button (Phase 3.3: Variables Autocomplete)
        self.variables_btn = QPushButton("📋 Variables")
        self.variables_btn.setToolTip("Show available variables (Ctrl+Space)\nManage variables (Ctrl+Shift+M)")
        self.variables_btn.clicked.connect(self._on_variables_clicked)
        toolbar.addWidget(self.variables_btn)

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
            'abs(value)', 'min(a, b)', 'max(a, b)', 'round(value, decimals)',
            'floor(value)', 'ceil(value)', 'pow(x, y)', 'sqrt(value)', 'exp(value)',
            'sum(...)', 'avg(...)', 'average(...)'
        ]

        # Trading functions
        trading_funcs = [
            'is_trade_open(trade)', 'is_long(trade)', 'is_short(trade)',
            'is_bullish_signal(strategy)', 'is_bearish_signal(strategy)',
            "in_regime(regime, 'R1')", 'stop_hit_long(trade, price)', 'stop_hit_short(trade, price)',
            'tp_hit(trade, price)', 'price_above_ema(price, ema)', 'price_below_ema(price, ema)',
            'price_above_level(price, level)', 'price_below_level(price, level)',
            'isnull(value)', 'nz(value, default)', 'coalesce(...)', 'clamp(value, min, max)',
            'pct_change(old, new)', 'pct_from_level(price, level)',
            "level_at_pct(entry, pct, 'long')", 'retracement(from, to, pct)',
            'extension(from, to, pct)', 'pctl(series, percentile)', 'crossover(series1, series2)',
            'highest(series, period)', 'lowest(series, period)', 'sma(series, period)',
            'pin_bar_bullish()', 'pin_bar_bearish()', 'inside_bar()', 'inverted_hammer()',
            'bull_flag()', 'bear_flag()', 'cup_and_handle()', 'double_bottom()', 'double_top()',
            'ascending_triangle()', 'descending_triangle()', 'breakout_above()', 'breakdown_below()',
            'false_breakout()', 'break_of_structure()', 'liquidity_swept()', 'fvg_exists()',
            'order_block_retest()', 'harmonic_pattern_detected()'
        ]

        # Array/Collection functions
        collection_funcs = [
            'size(array)', 'length(array)', 'has(array, element)',
            'all(array, condition)', 'any(array, condition)',
            'map(array, expr)', 'filter(array, condition)',
            'first(array)', 'last(array)',
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

        # Phase 3.3: Load project variables if autocomplete handler is available
        if self.variables_autocomplete:
            try:
                chart_window = self._get_chart_window()
                bot_config = self._get_bot_config(chart_window)
                project_vars_path = self._get_project_vars_path(chart_window)
                indicators_dict = self._get_current_indicators(chart_window)
                regime_dict = self._get_current_regime(chart_window)

                # Set API for variables autocomplete
                self.variables_autocomplete.api = self.api

                # Load and add variables
                self.variables_autocomplete.load_all_variables(
                    chart_window=chart_window,
                    bot_config=bot_config,
                    project_vars_path=project_vars_path,
                    indicators=indicators_dict,
                    regime=regime_dict,
                )
                self.variables_autocomplete.add_to_autocomplete()

                logger.debug("Project variables added to autocomplete")
            except Exception as e:
                logger.warning(f"Failed to load project variables for autocomplete: {e}")

        # Prepare autocomplete
        self.api.prepare()

    def _on_text_changed(self):
        """Handle text change."""
        code = self.editor.text()
        self.code_changed.emit(code)

        # Update status
        line_count = self.editor.lines()
        self.status_label.setText(f"Lines: {line_count}")

        # Trigger debounced validation (500ms delay)
        if self.validator and QSCI_AVAILABLE:
            self.validation_timer.start(500)

    def _on_generate_clicked(self):
        """Generate CEL code with AI."""
        # Emit signal to parent (Pattern Integration Widget)
        # Parent will provide pattern context and call AI helper
        self.ai_generation_requested.emit(self.workflow_type)

    def _on_validate_clicked(self):
        """Validate CEL expression - explicit validation via button."""
        code = self.editor.text().strip()

        if not code:
            QMessageBox.warning(self, "Validation", "Editor is empty")
            return

        if not self.validator:
            QMessageBox.warning(
                self, "Validation",
                "Validator not available. Install required packages."
            )
            return

        # Perform immediate validation
        errors = self.validator.validate(code)

        if not errors:
            QMessageBox.information(
                self, "Validation",
                "✅ Expression is valid!"
            )
            self.status_label.setText("✅ Valid")
            self.status_label.setStyleSheet("color: green; font-size: 10px; font-weight: bold;")
        else:
            error_count = len([e for e in errors if e.severity == ValidationSeverity.ERROR])
            warning_count = len([e for e in errors if e.severity == ValidationSeverity.WARNING])

            error_msg = f"Found {error_count} error(s)"
            if warning_count > 0:
                error_msg += f" and {warning_count} warning(s)"
            error_msg += ":\n\n"

            for error in errors[:10]:  # Show first 10 errors
                severity_icon = "❌" if error.severity == ValidationSeverity.ERROR else "⚠️"
                error_msg += f"{severity_icon} Line {error.line}, Col {error.column}: {error.message}\n"

            if len(errors) > 10:
                error_msg += f"\n... and {len(errors) - 10} more errors"

            QMessageBox.warning(self, "Validation Errors", error_msg)
            self.status_label.setText(f"❌ {error_count} error(s)")
            self.status_label.setStyleSheet("color: red; font-size: 10px; font-weight: bold;")

        # Display errors visually in editor
        self._display_validation_errors(errors)

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

    def _init_variables_autocomplete(self):
        """Initialize variables autocomplete handler (Phase 3.3)."""
        try:
            from .cel_editor_variables_autocomplete import CelEditorVariablesAutocomplete

            self.variables_autocomplete = CelEditorVariablesAutocomplete()
            logger.info("Variables autocomplete initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize variables autocomplete: {e}")
            self.variables_autocomplete = None

    def _on_variables_clicked(self):
        """Show Variable Reference Dialog (Phase 3.3)."""
        try:
            from src.ui.dialogs.variables import VariableReferenceDialog

            # Try to get parent ChartWindow
            chart_window = self._get_chart_window()

            # Get data sources
            bot_config = self._get_bot_config(chart_window)
            project_vars_path = self._get_project_vars_path(chart_window)
            indicators = self._get_current_indicators(chart_window)
            regime = self._get_current_regime(chart_window)

            # Create and show dialog
            dialog = VariableReferenceDialog(
                chart_window=chart_window,
                bot_config=bot_config,
                project_vars_path=project_vars_path,
                indicators=indicators,
                regime=regime,
                enable_live_updates=False,
                parent=self
            )

            dialog.show()
            logger.info("Variable Reference Dialog opened from CEL Editor")

        except Exception as e:
            logger.error(f"Failed to show Variable Reference Dialog: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Variable Reference",
                f"Failed to open Variable Reference:\n{str(e)}"
            )

    def refresh_variables_autocomplete(
        self,
        chart_window: Optional[any] = None,
        bot_config: Optional[any] = None,
        project_vars_path: Optional[str] = None,
        indicators: Optional[dict] = None,
        regime: Optional[dict] = None,
    ):
        """
        Refresh variables autocomplete with updated data (Phase 3.3).

        Call this method when variables change to update autocomplete suggestions.

        Args:
            chart_window: ChartWindow instance
            bot_config: BotConfig instance
            project_vars_path: Path to .cel_variables.json
            indicators: Dictionary of indicator values
            regime: Dictionary of regime values
        """
        if self.variables_autocomplete is None:
            logger.warning("Variables autocomplete not initialized")
            return

        if self.api is None:
            logger.warning("QsciAPIs not available")
            return

        try:
            # Refresh autocomplete
            count = self.variables_autocomplete.refresh_autocomplete(
                chart_window=chart_window,
                bot_config=bot_config,
                project_vars_path=project_vars_path,
                indicators=indicators,
                regime=regime,
            )

            logger.info(f"Autocomplete refreshed with {count} variables")

        except Exception as e:
            logger.error(f"Failed to refresh variables autocomplete: {e}")

    def _get_chart_window(self):
        """Get parent ChartWindow if available."""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == "ChartWindow":
                return parent
            parent = parent.parent()
        return None

    def _get_bot_config(self, chart_window):
        """Get BotConfig from ChartWindow."""
        if chart_window and hasattr(chart_window, "_get_bot_config"):
            return chart_window._get_bot_config()
        return None

    def _get_project_vars_path(self, chart_window):
        """Get project vars path from ChartWindow."""
        if chart_window and hasattr(chart_window, "_get_project_vars_path"):
            return chart_window._get_project_vars_path()
        return None

    def _get_current_indicators(self, chart_window):
        """Get current indicators from ChartWindow."""
        if chart_window and hasattr(chart_window, "_get_current_indicators"):
            return chart_window._get_current_indicators()
        return None

    def _get_current_regime(self, chart_window):
        """Get current regime from ChartWindow."""
        if chart_window and hasattr(chart_window, "_get_current_regime"):
            return chart_window._get_current_regime()
        return None

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

    def _perform_validation(self):
        """Perform live validation (triggered by timer)."""
        if not self.validator or not QSCI_AVAILABLE:
            return

        code = self.editor.text().strip()

        if not code:
            # Clear errors if editor is empty
            self.clear_error_markers()
            if hasattr(self.editor, 'clearAnnotations'):
                self.editor.clearAnnotations()
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")
            return

        # Validate expression
        errors = self.validator.validate(code)

        # Display errors visually
        self._display_validation_errors(errors)

        # Update status label
        if not errors:
            self.status_label.setText("✅ Valid")
            self.status_label.setStyleSheet("color: green; font-size: 10px;")
        else:
            error_count = len([e for e in errors if e.severity == ValidationSeverity.ERROR])
            warning_count = len([e for e in errors if e.severity == ValidationSeverity.WARNING])

            if error_count > 0:
                self.status_label.setText(f"❌ {error_count} error(s)")
                self.status_label.setStyleSheet("color: red; font-size: 10px; font-weight: bold;")
            else:
                self.status_label.setText(f"⚠️ {warning_count} warning(s)")
                self.status_label.setStyleSheet("color: orange; font-size: 10px; font-weight: bold;")

    def _display_validation_errors(self, errors: list):
        """Display validation errors visually in editor.

        Args:
            errors: List of ValidationError objects
        """
        if not QSCI_AVAILABLE:
            return

        # Clear previous error markers
        self.clear_error_markers()

        # Clear previous annotations
        if hasattr(self.editor, 'clearAnnotations'):
            self.editor.clearAnnotations()

        # Add error markers and annotations
        for error in errors:
            # QScintilla uses 0-indexed lines
            line_num = error.line - 1

            # Add marker to margin
            if error.severity == ValidationSeverity.ERROR:
                self.add_error_marker(line_num)

            # Add annotation (tooltip-like message)
            if hasattr(self.editor, 'annotate'):
                severity_icon = {
                    ValidationSeverity.ERROR: "❌",
                    ValidationSeverity.WARNING: "⚠️",
                    ValidationSeverity.INFO: "ℹ️"
                }.get(error.severity, "•")

                annotation_msg = f"{severity_icon} {error.message}"
                self.editor.annotate(line_num, annotation_msg, 2)  # Style 2 = error style

        # Set annotation display style (if supported)
        if hasattr(self.editor, 'setAnnotationDisplay'):
            from PyQt6.Qsci import QsciScintilla
            self.editor.setAnnotationDisplay(QsciScintilla.AnnotationDisplay.AnnotationBoxed)
