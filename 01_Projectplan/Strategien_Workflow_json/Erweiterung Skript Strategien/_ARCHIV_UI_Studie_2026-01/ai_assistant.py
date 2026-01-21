"""
CEL Editor - AI Assistant Panel
KI-gestützte Vorschläge und Analyse
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QScrollArea, QToolButton, QTextEdit, QLineEdit,
    QPushButton, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class AISuggestionCard(QFrame):
    """
    Einzelne AI Suggestion Karte
    """
    
    apply_clicked = Signal(str)
    dismiss_clicked = Signal()
    
    def __init__(self, suggestion_type="info", title="", description="", 
                 action_code=None, parent=None):
        super().__init__(parent)
        
        self.suggestion_type = suggestion_type
        self.action_code = action_code
        
        self.setup_ui(title, description)
        
    def setup_ui(self, title, description):
        # Farben basierend auf Typ
        colors = {
            'info': {'bg': '#00d9ff15', 'border': '#00d9ff', 'icon': '💡'},
            'warning': {'bg': '#ffab0015', 'border': '#ffab00', 'icon': '⚠️'},
            'success': {'bg': '#00c85315', 'border': '#00c853', 'icon': '✓'},
            'error': {'bg': '#ff3d7115', 'border': '#ff3d71', 'icon': '✗'},
            'pattern': {'bg': '#bd93f915', 'border': '#bd93f9', 'icon': '📊'},
        }
        
        color = colors.get(self.suggestion_type, colors['info'])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color['bg']};
                border-left: 3px solid {color['border']};
                border-radius: 0 8px 8px 0;
                padding: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header Row
        header = QHBoxLayout()
        
        icon = QLabel(color['icon'])
        icon.setStyleSheet("font-size: 18px;")
        header.addWidget(icon)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 13px;
            color: {color['border']};
        """)
        header.addWidget(title_label)
        
        header.addStretch()
        
        # Dismiss Button
        dismiss_btn = QToolButton()
        dismiss_btn.setText("✕")
        dismiss_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #5f6368;
                font-size: 14px;
            }
            QToolButton:hover {
                color: #e8eaed;
            }
        """)
        dismiss_btn.clicked.connect(self.dismiss_clicked.emit)
        header.addWidget(dismiss_btn)
        
        layout.addLayout(header)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #b8bcc4;
            font-size: 12px;
            line-height: 1.5;
        """)
        layout.addWidget(desc_label)
        
        # Action Buttons (wenn Code vorhanden)
        if self.action_code:
            action_row = QHBoxLayout()
            action_row.addStretch()
            
            apply_btn = QPushButton("Apply Suggestion")
            apply_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color['border']};
                    color: #0d0f12;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {color['border']}dd;
                }}
            """)
            apply_btn.clicked.connect(lambda: self.apply_clicked.emit(self.action_code))
            action_row.addWidget(apply_btn)
            
            layout.addLayout(action_row)


class AIAssistantPanel(QWidget):
    """
    Komplettes AI Assistant Panel
    """
    
    suggestion_applied = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header = self.create_header()
        layout.addWidget(self.header)
        
        # Main Content Area
        main_frame = QFrame()
        main_frame.setStyleSheet("""
            QFrame {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-top: none;
            }
        """)
        
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # AI Status
        self.status_frame = self.create_status_frame()
        main_layout.addWidget(self.status_frame)
        
        # Suggestions Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.suggestions_widget = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_widget)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestions_layout.setSpacing(12)
        
        # Demo Suggestions
        self.add_demo_suggestions()
        
        self.suggestions_layout.addStretch()
        self.scroll_area.setWidget(self.suggestions_widget)
        
        main_layout.addWidget(self.scroll_area)
        
        # Ask AI Input
        self.ask_frame = self.create_ask_frame()
        main_layout.addWidget(self.ask_frame)
        
        layout.addWidget(main_frame)
        
    def create_header(self):
        """Header mit Titel und Aktionen"""
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 8px 8px 0 0;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # AI Icon & Title
        ai_icon = QLabel("🤖")
        ai_icon.setStyleSheet("font-size: 20px;")
        layout.addWidget(ai_icon)
        
        title = QLabel("AI Assistant")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #e8eaed;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Refresh Button
        refresh_btn = QToolButton()
        refresh_btn.setText("🔄")
        refresh_btn.setToolTip("Refresh Suggestions")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #1e2329;
                border-radius: 6px;
            }
        """)
        layout.addWidget(refresh_btn)
        
        # Settings Button
        settings_btn = QToolButton()
        settings_btn.setText("⚙️")
        settings_btn.setToolTip("AI Settings")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #1e2329;
                border-radius: 6px;
            }
        """)
        layout.addWidget(settings_btn)
        
        return header
        
    def create_status_frame(self):
        """AI Status Anzeige"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #00d9ff10;
                border: 1px solid #00d9ff30;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #00c853; font-size: 10px;")
        layout.addWidget(status_dot)
        
        status_text = QLabel("AI Analyzing Pattern...")
        status_text.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        layout.addWidget(status_text)
        
        layout.addStretch()
        
        # Mini Progress
        progress = QProgressBar()
        progress.setFixedSize(80, 4)
        progress.setRange(0, 0)  # Indeterminate
        progress.setStyleSheet("""
            QProgressBar {
                background-color: #1e2329;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #00d9ff;
                border-radius: 2px;
            }
        """)
        layout.addWidget(progress)
        
        return frame
        
    def create_ask_frame(self):
        """Ask AI Input Frame"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        label = QLabel("Ask AI")
        label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #9aa0a6;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(label)
        
        input_row = QHBoxLayout()
        
        self.ask_input = QLineEdit()
        self.ask_input.setPlaceholderText("Ask about patterns, strategies, or get optimization tips...")
        self.ask_input.setStyleSheet("""
            QLineEdit {
                background-color: #0d0f12;
                border: 1px solid #2d333b;
                border-radius: 6px;
                padding: 10px 14px;
                color: #e8eaed;
            }
            QLineEdit:focus {
                border-color: #00d9ff;
            }
        """)
        input_row.addWidget(self.ask_input)
        
        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(60)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d9ff;
                color: #0d0f12;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #33e1ff;
            }
        """)
        input_row.addWidget(send_btn)
        
        layout.addLayout(input_row)
        
        return frame
        
    def add_demo_suggestions(self):
        """Fügt Demo Suggestions hinzu"""
        suggestions = [
            {
                'type': 'warning',
                'title': 'Volume Confirmation Missing',
                'description': 'Your Engulfing pattern has no volume filter. '
                              'Adding a volume spike requirement (>150% avg) '
                              'typically improves signal quality by 20-30%.',
                'code': '&& (volume[-1] > 1.5 * avg(volume[-20:-1]))'
            },
            {
                'type': 'info',
                'title': 'Trend Filter Suggestion',
                'description': 'Consider adding an EMA filter to trade only '
                              'in the direction of the trend. This pattern '
                              'performs better in trending markets.',
                'code': '&& (close[-1] > ema34.value)  // Trend filter'
            },
            {
                'type': 'pattern',
                'title': 'Similar Pattern Detected',
                'description': 'Current market shows a forming Inside Bar on 15m '
                              'after a strong move. Historical win rate: 68% when '
                              'combined with volume confirmation.',
                'code': None
            },
            {
                'type': 'success',
                'title': 'Risk Management OK',
                'description': 'Your stop loss placement follows best practices. '
                              'ATR-based trailing stop could improve average R:R '
                              'from 1.5 to 2.1 based on backtest data.',
                'code': None
            },
        ]
        
        for s in suggestions:
            card = AISuggestionCard(
                suggestion_type=s['type'],
                title=s['title'],
                description=s['description'],
                action_code=s.get('code')
            )
            card.apply_clicked.connect(self.suggestion_applied.emit)
            self.suggestions_layout.addWidget(card)


class PatternRecognitionPanel(QFrame):
    """
    Panel für erkannte Patterns im aktuellen Chart
    """
    
    pattern_selected = Signal(dict)
    
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
        header_row = QHBoxLayout()
        
        title = QLabel("Detected Patterns")
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #00d9ff;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        header_row.addWidget(title)
        
        header_row.addStretch()
        
        scan_btn = QPushButton("Scan")
        scan_btn.setFixedWidth(60)
        scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e2329;
                color: #e8eaed;
                border: 1px solid #2d333b;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2d333b;
                border-color: #00d9ff;
            }
        """)
        header_row.addWidget(scan_btn)
        
        layout.addLayout(header_row)
        
        # Patterns List
        patterns = [
            {"name": "Bullish Engulfing", "tf": "15m", "score": 85, "state": "confirmed"},
            {"name": "Inside Bar", "tf": "1h", "score": 72, "state": "forming"},
            {"name": "Pin Bar", "tf": "4h", "score": 91, "state": "confirmed"},
        ]
        
        for p in patterns:
            card = self.create_pattern_card(p)
            layout.addWidget(card)
            
        layout.addStretch()
        
    def create_pattern_card(self, pattern_data):
        """Erstellt eine Pattern-Karte"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1a1d21;
                border: 1px solid #2d333b;
                border-radius: 6px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #00d9ff80;
                background-color: #1e2329;
            }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # Top Row
        top_row = QHBoxLayout()
        
        name = QLabel(pattern_data['name'])
        name.setStyleSheet("color: #e8eaed; font-weight: 600; font-size: 12px;")
        top_row.addWidget(name)
        
        top_row.addStretch()
        
        # Score Badge
        score_color = '#00c853' if pattern_data['score'] >= 80 else '#ffab00'
        score = QLabel(f"{pattern_data['score']}%")
        score.setStyleSheet(f"""
            background-color: {score_color}30;
            color: {score_color};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        """)
        top_row.addWidget(score)
        
        layout.addLayout(top_row)
        
        # Bottom Row
        bottom_row = QHBoxLayout()
        
        tf = QLabel(f"📊 {pattern_data['tf']}")
        tf.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        bottom_row.addWidget(tf)
        
        state_color = '#00c853' if pattern_data['state'] == 'confirmed' else '#ffab00'
        state = QLabel(f"● {pattern_data['state'].capitalize()}")
        state.setStyleSheet(f"color: {state_color}; font-size: 11px;")
        bottom_row.addWidget(state)
        
        bottom_row.addStretch()
        
        use_btn = QLabel("Use →")
        use_btn.setStyleSheet("color: #00d9ff; font-size: 11px; font-weight: 500;")
        bottom_row.addWidget(use_btn)
        
        layout.addLayout(bottom_row)
        
        return card
