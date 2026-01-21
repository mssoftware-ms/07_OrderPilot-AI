"""
CEL Editor - Code Editor Widget
CEL Expression Editor mit Syntax Highlighting und Auto-Completion
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPlainTextEdit, QTextEdit, QToolButton, QComboBox,
    QSplitter, QListWidget, QListWidgetItem, QCompleter,
    QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QRegularExpression, QStringListModel
from PySide6.QtGui import (
    QFont, QColor, QTextCharFormat, QSyntaxHighlighter,
    QPainter, QTextCursor, QTextFormat, QPalette
)


class CELSyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax Highlighter für CEL Expressions
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#ff79c6'))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            'true', 'false', 'null', 'in', 'has', 'all', 'exists',
            'exists_one', 'map', 'filter', 'size', 'type', 'duration',
            'timestamp', 'int', 'uint', 'double', 'bool', 'string', 'bytes',
            'list', 'map', 'dyn'
        ]
        
        for keyword in keywords:
            pattern = QRegularExpression(f'\\b{keyword}\\b')
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Operators
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor('#50fa7b'))
        
        operators = ['&&', '\\|\\|', '!', '==', '!=', '<', '>', '<=', '>=', 
                    '\\+', '-', '\\*', '/', '%', '\\?', ':']
        
        for op in operators:
            pattern = QRegularExpression(op)
            self.highlighting_rules.append((pattern, operator_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor('#bd93f9'))
        
        pattern = QRegularExpression(r'\b[0-9]+\.?[0-9]*\b')
        self.highlighting_rules.append((pattern, number_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#f1fa8c'))
        
        pattern = QRegularExpression(r'"[^"]*"')
        self.highlighting_rules.append((pattern, string_format))
        
        pattern = QRegularExpression(r"'[^']*'")
        self.highlighting_rules.append((pattern, string_format))
        
        # Variables / Identifiers (Trading specific)
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor('#8be9fd'))
        
        trading_vars = [
            'close', 'open', 'high', 'low', 'volume', 'price',
            'atr', 'atrp', 'ema', 'sma', 'rsi', 'macd', 'bbwidth',
            'regime', 'squeeze_on', 'direction', 'cfg',
            'entry_price', 'position', 'stop_loss', 'take_profit'
        ]
        
        for var in trading_vars:
            pattern = QRegularExpression(f'\\b{var}\\b')
            self.highlighting_rules.append((pattern, variable_format))
        
        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor('#ffb86c'))
        
        functions = [
            'avg', 'max', 'min', 'abs', 'sum', 'std', 'var',
            'indicator', 'pattern', 'crossover', 'crossunder',
            'highest', 'lowest', 'change', 'roc', 'valuewhen'
        ]
        
        for func in functions:
            pattern = QRegularExpression(f'\\b{func}\\b')
            self.highlighting_rules.append((pattern, function_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#6272a4'))
        comment_format.setFontItalic(True)
        
        pattern = QRegularExpression(r'//[^\n]*')
        self.highlighting_rules.append((pattern, comment_format))
        
        # Array Indexing (special)
        index_format = QTextCharFormat()
        index_format.setForeground(QColor('#ff5555'))
        
        pattern = QRegularExpression(r'\[-?\d+\]')
        self.highlighting_rules.append((pattern, index_format))
        
    def highlightBlock(self, text):
        """Highlight den aktuellen Textblock"""
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class LineNumberArea(QWidget):
    """Widget für Zeilennummern"""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)
        
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CELCodeEditor(QPlainTextEdit):
    """
    Custom Code Editor mit Zeilennummern und Syntax Highlighting
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Font
        font = QFont('JetBrains Mono', 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Styling
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d0f12;
                color: #e8eaed;
                border: none;
                selection-background-color: #00d9ff40;
                padding: 8px;
            }
        """)
        
        # Line Number Area
        self.line_number_area = LineNumberArea(self)
        
        # Syntax Highlighter
        self.highlighter = CELSyntaxHighlighter(self.document())
        
        # Connections
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Tab Settings
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        
    def line_number_area_width(self):
        """Berechnet die Breite des Zeilennummernbereichs"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits + 12
        return space
        
    def update_line_number_area_width(self, _):
        """Aktualisiert die Breite des Zeilennummernbereichs"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def update_line_number_area(self, rect, dy):
        """Aktualisiert den Zeilennummernbereich beim Scrollen"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), 
                self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
            
    def resizeEvent(self, event):
        """Resize Handler"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), 
            self.line_number_area_width(), cr.height())
            
    def line_number_area_paint_event(self, event):
        """Zeichnet die Zeilennummern"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor('#13161a'))
        
        # Linie zwischen Nummern und Editor
        painter.setPen(QColor('#1e2329'))
        painter.drawLine(event.rect().topRight(), event.rect().bottomRight())
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        current_line = self.textCursor().blockNumber()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                if block_number == current_line:
                    painter.setPen(QColor('#00d9ff'))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor('#5f6368'))
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
                    
                painter.drawText(0, top, self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number)
                    
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
            
    def highlight_current_line(self):
        """Hebt die aktuelle Zeile hervor"""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor('#1e232980')
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        self.setExtraSelections(extra_selections)


class CELEditorWidget(QWidget):
    """
    Komplettes CEL Editor Widget mit Toolbar und Output
    """
    
    code_changed = Signal(str)
    validation_result = Signal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header Toolbar
        self.header = self.create_header()
        layout.addWidget(self.header)
        
        # Tab Widget für verschiedene Regel-Typen
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-top: none;
            }
            QTabBar::tab {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
                color: #9aa0a6;
                font-size: 11px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #0d0f12;
                color: #00d9ff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #1a1d21;
            }
        """)
        
        # Entry Rules Tab
        self.entry_editor = CELCodeEditor()
        self.entry_editor.setPlaceholderText(
            "// Entry Rule - Define your entry conditions here\n"
            "// Example: Bullish Engulfing Pattern\n"
            "(close[-2] < open[-2])  // Candle 1 bearish\n"
            "&& (close[-1] > open[-1])  // Candle 2 bullish\n"
            "&& (high[-1] > high[-2] && low[-1] < low[-2])"
        )
        self.tabs.addTab(self.entry_editor, "📈 Entry Rules")
        
        # Exit Rules Tab
        self.exit_editor = CELCodeEditor()
        self.exit_editor.setPlaceholderText(
            "// Exit Rule - Define your exit conditions here\n"
            "// Example: Exit on Evening Star pattern or target hit"
        )
        self.tabs.addTab(self.exit_editor, "📉 Exit Rules")
        
        # Risk Rules Tab
        self.risk_editor = CELCodeEditor()
        self.risk_editor.setPlaceholderText(
            "// Risk Rule - Define risk management conditions\n"
            "// Example: No trade when volatility too low"
        )
        self.tabs.addTab(self.risk_editor, "⚠️ Risk Rules")
        
        # Stop Update Tab
        self.stop_editor = CELCodeEditor()
        self.stop_editor.setPlaceholderText(
            "// Stop Update Rule - Define trailing stop logic\n"
            "// Example: Move stop to breakeven after +1%"
        )
        self.tabs.addTab(self.stop_editor, "🛑 Stop Update")
        
        layout.addWidget(self.tabs)
        
        # Validation & Output Panel
        self.output_panel = self.create_output_panel()
        layout.addWidget(self.output_panel)
        
    def create_header(self):
        """Header mit Toolbar"""
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Titel
        title = QLabel("CEL Expression Editor")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #e8eaed;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Rule Type Selector
        rule_label = QLabel("Rule Type:")
        rule_label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        layout.addWidget(rule_label)
        
        self.rule_type_combo = QComboBox()
        self.rule_type_combo.addItems([
            "Entry (Long)", "Entry (Short)", "Exit", "No Trade", 
            "Update Stop", "Risk Block", "Risk Exit"
        ])
        self.rule_type_combo.setFixedWidth(140)
        layout.addWidget(self.rule_type_combo)
        
        layout.addSpacing(16)
        
        # Toolbar Buttons
        buttons = [
            ("▶️", "Validate", "validate"),
            ("📋", "Copy", "copy"),
            ("📥", "Paste", "paste"),
            ("🔄", "Format", "format"),
            ("💡", "AI Assist", "ai_assist"),
            ("📚", "Snippets", "snippets"),
        ]
        
        for icon, tooltip, action in buttons:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(tooltip)
            btn.setFixedSize(36, 36)
            btn.setStyleSheet("""
                QToolButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    font-size: 16px;
                }
                QToolButton:hover {
                    background-color: #1e2329;
                    border-color: #2d333b;
                }
            """)
            if action == "validate":
                btn.setStyleSheet("""
                    QToolButton {
                        background-color: #00c85330;
                        border: 1px solid #00c85380;
                        border-radius: 6px;
                        font-size: 16px;
                    }
                    QToolButton:hover {
                        background-color: #00c85350;
                        border-color: #00c853;
                    }
                """)
            layout.addWidget(btn)
        
        return header
        
    def create_output_panel(self):
        """Output Panel für Validation & Logs"""
        panel = QFrame()
        panel.setFixedHeight(120)
        panel.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-top: none;
                border-radius: 0 0 8px 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header Row
        header_row = QHBoxLayout()
        
        output_label = QLabel("Validation Output")
        output_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #9aa0a6;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        header_row.addWidget(output_label)
        
        header_row.addStretch()
        
        # Status Badge
        self.status_badge = QLabel("✓ Valid")
        self.status_badge.setStyleSheet("""
            background-color: #00c85330;
            color: #00c853;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_row.addWidget(self.status_badge)
        
        layout.addLayout(header_row)
        
        # Output Text
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-radius: 6px;
                color: #9aa0a6;
                font-family: 'JetBrains Mono';
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.output_text.setPlaceholderText(
            "Click 'Validate' to check your CEL expression..."
        )
        layout.addWidget(self.output_text)
        
        return panel
        
    def set_validation_success(self, message="Expression is valid"):
        """Setzt den Validation Status auf Erfolg"""
        self.status_badge.setText("✓ Valid")
        self.status_badge.setStyleSheet("""
            background-color: #00c85330;
            color: #00c853;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        """)
        self.output_text.setPlainText(f"✓ {message}")
        
    def set_validation_error(self, message="Expression has errors"):
        """Setzt den Validation Status auf Fehler"""
        self.status_badge.setText("✗ Error")
        self.status_badge.setStyleSheet("""
            background-color: #ff3d7130;
            color: #ff3d71;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        """)
        self.output_text.setPlainText(f"✗ {message}")


class CELSnippetsPanel(QFrame):
    """
    Panel mit vordefinierten CEL Code Snippets
    """
    
    snippet_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Code Snippets")
        header.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #00d9ff;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(header)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search snippets...")
        layout.addWidget(self.search_input)
        
        # Categories
        self.snippet_list = QListWidget()
        self.snippet_list.setStyleSheet("""
            QListWidget {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #1e2329;
            }
            QListWidget::item:hover {
                background-color: #1e2329;
            }
            QListWidget::item:selected {
                background-color: #00d9ff20;
                color: #00d9ff;
            }
        """)
        
        snippets = [
            ("📈 Bullish Engulfing", "Pattern"),
            ("📉 Bearish Engulfing", "Pattern"),
            ("📍 Pin Bar Entry", "Pattern"),
            ("📦 Inside Bar Breakout", "Pattern"),
            ("🔺 Higher High", "Structure"),
            ("🔻 Lower Low", "Structure"),
            ("📊 Volume Spike", "Filter"),
            ("📈 Trend Up (EMA)", "Filter"),
            ("📉 Trend Down (EMA)", "Filter"),
            ("⚡ Volatility Check", "Filter"),
            ("🛑 Trailing Stop BE", "Stop"),
            ("🛑 Trailing Stop ATR", "Stop"),
        ]
        
        for name, category in snippets:
            item = QListWidgetItem(f"{name}  •  {category}")
            self.snippet_list.addItem(item)
        
        layout.addWidget(self.snippet_list)


# Import fix
from PySide6.QtWidgets import QLineEdit
