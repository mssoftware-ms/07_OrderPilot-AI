"""
CEL Editor - Pattern Library & Properties Panels
Bibliothek vordefinierter Patterns und Einstellungen
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QScrollArea, QToolButton, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QSlider, QGroupBox,
    QStackedWidget, QListWidget, QListWidgetItem,
    QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon


class PatternLibraryPanel(QWidget):
    """
    Bibliothek mit vordefinierten und benutzerdefinierten Patterns
    """
    
    pattern_selected = Signal(dict)
    pattern_loaded = Signal(str)
    
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
        
        # Main Content
        main_frame = QFrame()
        main_frame.setStyleSheet("""
            QFrame {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-top: none;
            }
        """)
        
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search patterns...")
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: #1a1d21;
                border: 1px solid #2d333b;
                border-radius: 6px;
                padding: 10px 14px;
                color: #e8eaed;
            }
            QLineEdit:focus {
                border-color: #00d9ff;
            }
        """)
        main_layout.addWidget(self.search)
        
        # Category Tabs
        self.category_tabs = QFrame()
        self.category_tabs.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 6px;
            }
        """)
        
        tab_layout = QHBoxLayout(self.category_tabs)
        tab_layout.setContentsMargins(4, 4, 4, 4)
        tab_layout.setSpacing(4)
        
        categories = ["All", "Candle", "Structure", "SMC", "Custom"]
        for i, cat in enumerate(categories):
            btn = QPushButton(cat)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    color: #9aa0a6;
                    font-weight: 500;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #1e2329;
                }
                QPushButton:checked {
                    background-color: #00d9ff20;
                    color: #00d9ff;
                }
            """)
            tab_layout.addWidget(btn)
        
        main_layout.addWidget(self.category_tabs)
        
        # Pattern Tree
        self.pattern_tree = QTreeWidget()
        self.pattern_tree.setHeaderHidden(True)
        self.pattern_tree.setStyleSheet("""
            QTreeWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QTreeWidget::item {
                padding: 8px 4px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QTreeWidget::item:hover {
                background-color: #1e2329;
            }
            QTreeWidget::item:selected {
                background-color: #00d9ff20;
                color: #00d9ff;
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
        """)
        
        # Populate Tree
        self.populate_pattern_tree()
        
        main_layout.addWidget(self.pattern_tree)
        
        layout.addWidget(main_frame)
        
    def create_header(self):
        """Header mit Titel"""
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
        
        title = QLabel("📚 Pattern Library")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #e8eaed;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Add Pattern Button
        add_btn = QToolButton()
        add_btn.setText("➕")
        add_btn.setToolTip("Create New Pattern")
        add_btn.setStyleSheet("""
            QToolButton {
                background: #00d9ff20;
                border: 1px solid #00d9ff40;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 14px;
            }
            QToolButton:hover {
                background: #00d9ff30;
            }
        """)
        layout.addWidget(add_btn)
        
        return header
        
    def populate_pattern_tree(self):
        """Füllt den Pattern-Baum"""
        patterns = {
            "📊 Candlestick Patterns": [
                ("Bullish Engulfing", "🟢", "2-bar reversal"),
                ("Bearish Engulfing", "🔴", "2-bar reversal"),
                ("Morning Star", "🟢", "3-bar reversal"),
                ("Evening Star", "🔴", "3-bar reversal"),
                ("Hammer", "🟢", "1-bar reversal"),
                ("Shooting Star", "🔴", "1-bar reversal"),
                ("Doji", "⚪", "indecision"),
                ("Pin Bar (Bull)", "🟢", "rejection"),
                ("Pin Bar (Bear)", "🔴", "rejection"),
            ],
            "📦 Price Action": [
                ("Inside Bar", "📦", "consolidation"),
                ("Outside Bar", "📦", "expansion"),
                ("Key Reversal", "🔄", "reversal"),
                ("Three Bar Reversal", "🔄", "reversal"),
            ],
            "📈 Market Structure": [
                ("Higher High", "🔺", "trend"),
                ("Lower Low", "🔻", "trend"),
                ("Break of Structure", "⚡", "breakout"),
                ("Change of Character", "🔄", "reversal"),
            ],
            "💰 Smart Money Concepts": [
                ("Order Block (Bull)", "🟢", "SMC"),
                ("Order Block (Bear)", "🔴", "SMC"),
                ("Fair Value Gap", "📊", "imbalance"),
                ("Liquidity Sweep", "💧", "manipulation"),
                ("3-Act Model", "🎭", "SMC entry"),
            ],
            "⭐ Custom Patterns": [
                ("My Pattern 1", "⭐", "custom"),
                ("Trend Entry Setup", "⭐", "custom"),
            ],
        }
        
        for category, items in patterns.items():
            category_item = QTreeWidgetItem([category])
            category_item.setFont(0, QFont('JetBrains Mono', 11, QFont.Weight.Bold))
            self.pattern_tree.addTopLevelItem(category_item)
            
            for name, icon, tag in items:
                child = QTreeWidgetItem([f"  {icon}  {name}  •  {tag}"])
                child.setData(0, Qt.ItemDataRole.UserRole, {'name': name, 'tag': tag})
                category_item.addChild(child)
            
            category_item.setExpanded(True)


class FilterPanel(QWidget):
    """
    Panel für Filter und Indikator-Einstellungen
    """
    
    filter_changed = Signal(dict)
    
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
        
        # Scroll Area für Filter
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-top: none;
            }
        """)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        
        # Timeframe Section
        tf_group = self.create_timeframe_group()
        content_layout.addWidget(tf_group)
        
        # Volume Filter
        vol_group = self.create_volume_group()
        content_layout.addWidget(vol_group)
        
        # Trend Filter
        trend_group = self.create_trend_group()
        content_layout.addWidget(trend_group)
        
        # Volatility Filter
        vol_group = self.create_volatility_group()
        content_layout.addWidget(vol_group)
        
        # Support/Resistance
        sr_group = self.create_sr_group()
        content_layout.addWidget(sr_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
    def create_header(self):
        """Header"""
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
        
        title = QLabel("🎛️ Filters & Indicators")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #e8eaed;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #2d333b;
                border-radius: 4px;
                padding: 4px 12px;
                color: #9aa0a6;
                font-size: 11px;
            }
            QPushButton:hover {
                border-color: #ff3d71;
                color: #ff3d71;
            }
        """)
        layout.addWidget(reset_btn)
        
        return header
        
    def create_filter_group(self, title, widgets_layout):
        """Erstellt eine Filter-Gruppe"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 8px;
                margin-top: 16px;
                padding: 16px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                top: 0px;
                color: #00d9ff;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """)
        group.setLayout(widgets_layout)
        return group
        
    def create_timeframe_group(self):
        """Timeframe Einstellungen"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Primary TF
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Primary:"))
        tf_combo = QComboBox()
        tf_combo.addItems(["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W"])
        tf_combo.setCurrentText("15m")
        row1.addWidget(tf_combo)
        layout.addLayout(row1)
        
        # HTF Context
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("HTF Context:"))
        htf_combo = QComboBox()
        htf_combo.addItems(["None", "1h", "4h", "1D"])
        htf_combo.setCurrentText("1h")
        row2.addWidget(htf_combo)
        layout.addLayout(row2)
        
        # MTF Checkbox
        mtf_check = QCheckBox("Enable Multi-Timeframe Analysis")
        mtf_check.setChecked(True)
        layout.addWidget(mtf_check)
        
        return self.create_filter_group("⏱️ Timeframe", layout)
        
    def create_volume_group(self):
        """Volume Filter"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Enable
        enable = QCheckBox("Enable Volume Filter")
        enable.setChecked(True)
        layout.addWidget(enable)
        
        # Threshold
        row = QHBoxLayout()
        row.addWidget(QLabel("Min. Volume Spike:"))
        spin = QSpinBox()
        spin.setRange(100, 500)
        spin.setValue(150)
        spin.setSuffix(" %")
        row.addWidget(spin)
        layout.addLayout(row)
        
        # Period
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Lookback Period:"))
        period = QSpinBox()
        period.setRange(5, 100)
        period.setValue(20)
        period.setSuffix(" bars")
        row2.addWidget(period)
        layout.addLayout(row2)
        
        return self.create_filter_group("📊 Volume", layout)
        
    def create_trend_group(self):
        """Trend Filter"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Enable
        enable = QCheckBox("Enable Trend Filter")
        enable.setChecked(True)
        layout.addWidget(enable)
        
        # Indicator Type
        row = QHBoxLayout()
        row.addWidget(QLabel("Indicator:"))
        combo = QComboBox()
        combo.addItems(["EMA", "SMA", "WMA", "VWMA"])
        row.addWidget(combo)
        layout.addLayout(row)
        
        # Period
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Period:"))
        period = QSpinBox()
        period.setRange(5, 200)
        period.setValue(34)
        row2.addWidget(period)
        layout.addLayout(row2)
        
        # Direction
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Direction:"))
        dir_combo = QComboBox()
        dir_combo.addItems(["With Trend", "Counter Trend", "Any"])
        row3.addWidget(dir_combo)
        layout.addLayout(row3)
        
        return self.create_filter_group("📈 Trend", layout)
        
    def create_volatility_group(self):
        """Volatility Filter"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Enable
        enable = QCheckBox("Enable Volatility Filter")
        layout.addWidget(enable)
        
        # ATR Threshold
        row = QHBoxLayout()
        row.addWidget(QLabel("Min ATR%:"))
        atr = QDoubleSpinBox()
        atr.setRange(0.1, 10.0)
        atr.setValue(0.5)
        atr.setSingleStep(0.1)
        atr.setSuffix(" %")
        row.addWidget(atr)
        layout.addLayout(row)
        
        # BB Width
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("BB Width:"))
        bb_combo = QComboBox()
        bb_combo.addItems(["Any", "Squeeze", "Normal", "Expanded"])
        row2.addWidget(bb_combo)
        layout.addLayout(row2)
        
        return self.create_filter_group("📉 Volatility", layout)
        
    def create_sr_group(self):
        """Support/Resistance"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Enable
        enable = QCheckBox("Require S/R Context")
        layout.addWidget(enable)
        
        # Distance
        row = QHBoxLayout()
        row.addWidget(QLabel("Max Distance:"))
        dist = QDoubleSpinBox()
        dist.setRange(0.1, 5.0)
        dist.setValue(0.5)
        dist.setSingleStep(0.1)
        dist.setSuffix(" %")
        row.addWidget(dist)
        layout.addLayout(row)
        
        # Type
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Level Type:"))
        type_combo = QComboBox()
        type_combo.addItems(["Any", "Support", "Resistance", "Pivot"])
        row2.addWidget(type_combo)
        layout.addLayout(row2)
        
        return self.create_filter_group("🎯 Support/Resistance", layout)


class StrategyTemplatesPanel(QWidget):
    """
    Panel für Strategie-Vorlagen
    """
    
    template_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 8px 8px 0 0;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        
        title = QLabel("📋 Strategy Templates")
        title.setStyleSheet("font-size: 14px; font-weight: 600; color: #e8eaed;")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-top: none;
            }
        """)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)
        
        # Templates
        templates = [
            {
                "name": "Trend Pullback Entry",
                "desc": "Enter on pullback to EMA in strong trends",
                "tags": ["Trend Following", "Price Action"],
                "winrate": "62%"
            },
            {
                "name": "SMC 3-Act Model",
                "desc": "Liquidity sweep → Displacement → FVG entry",
                "tags": ["SMC", "Institutional"],
                "winrate": "68%"
            },
            {
                "name": "Breakout & Retest",
                "desc": "Trade breakouts with confirmation retest",
                "tags": ["Breakout", "Structure"],
                "winrate": "55%"
            },
            {
                "name": "Mean Reversion",
                "desc": "Counter-trend entries at extremes",
                "tags": ["Counter-Trend", "Reversal"],
                "winrate": "58%"
            },
            {
                "name": "Volatility Squeeze",
                "desc": "Entry when BB squeeze releases",
                "tags": ["Volatility", "Momentum"],
                "winrate": "64%"
            },
        ]
        
        for t in templates:
            card = self.create_template_card(t)
            content_layout.addWidget(card)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
    def create_template_card(self, template):
        """Erstellt eine Template-Karte"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 8px;
                padding: 16px;
            }
            QFrame:hover {
                border-color: #00d9ff60;
            }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        
        name = QLabel(template['name'])
        name.setStyleSheet("color: #e8eaed; font-weight: 600; font-size: 14px;")
        header.addWidget(name)
        
        header.addStretch()
        
        winrate = QLabel(template['winrate'])
        winrate.setStyleSheet("""
            background-color: #00c85330;
            color: #00c853;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        """)
        header.addWidget(winrate)
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel(template['desc'])
        desc.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Tags
        tags_layout = QHBoxLayout()
        for tag in template['tags']:
            tag_label = QLabel(tag)
            tag_label.setStyleSheet("""
                background-color: #1e2329;
                color: #9aa0a6;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 10px;
            """)
            tags_layout.addWidget(tag_label)
        tags_layout.addStretch()
        
        layout.addLayout(tags_layout)
        
        # Load Button
        load_btn = QPushButton("Load Template")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d9ff20;
                color: #00d9ff;
                border: 1px solid #00d9ff40;
                border-radius: 4px;
                padding: 8px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00d9ff30;
                border-color: #00d9ff;
            }
        """)
        layout.addWidget(load_btn)
        
        return card
