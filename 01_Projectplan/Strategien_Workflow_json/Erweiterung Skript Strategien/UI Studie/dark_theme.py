"""
CEL Editor - Dark Theme Definition
Professionelles Trading-UI Theme mit hohem Kontrast
"""

DARK_THEME = """
/* ==========================================
   CEL EDITOR - DARK THEME
   Professional Trading UI
   ========================================== */

/* === Global === */
QMainWindow, QWidget {
    background-color: #0d0f12;
    color: #e8eaed;
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
}

/* === Menu Bar === */
QMenuBar {
    background-color: #13161a;
    border-bottom: 1px solid #1e2329;
    padding: 4px 8px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    color: #9aa0a6;
}

QMenuBar::item:selected {
    background-color: #1e2329;
    color: #00d9ff;
}

QMenu {
    background-color: #1a1d21;
    border: 1px solid #2d333b;
    border-radius: 8px;
    padding: 8px 4px;
}

QMenu::item {
    padding: 8px 24px 8px 16px;
    border-radius: 4px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #00d9ff20;
    color: #00d9ff;
}

QMenu::separator {
    height: 1px;
    background-color: #2d333b;
    margin: 8px 12px;
}

/* === Tool Bar === */
QToolBar {
    background-color: #13161a;
    border: none;
    border-bottom: 1px solid #1e2329;
    padding: 8px;
    spacing: 8px;
}

QToolBar::separator {
    width: 1px;
    background-color: #2d333b;
    margin: 4px 8px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 8px;
    color: #9aa0a6;
}

QToolButton:hover {
    background-color: #1e2329;
    border-color: #2d333b;
    color: #e8eaed;
}

QToolButton:pressed {
    background-color: #00d9ff20;
    border-color: #00d9ff40;
}

QToolButton:checked {
    background-color: #00d9ff20;
    border-color: #00d9ff;
    color: #00d9ff;
}

/* === Dock Widgets === */
QDockWidget {
    titlebar-close-icon: url(close.png);
    titlebar-normal-icon: url(float.png);
    font-weight: 600;
    color: #9aa0a6;
}

QDockWidget::title {
    background-color: #13161a;
    padding: 10px 16px;
    border-bottom: 1px solid #1e2329;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 1px;
}

QDockWidget::close-button, QDockWidget::float-button {
    background-color: transparent;
    border: none;
    padding: 4px;
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background-color: #2d333b;
    border-radius: 4px;
}

/* === Tab Widget === */
QTabWidget::pane {
    background-color: #0d0f12;
    border: 1px solid #1e2329;
    border-radius: 8px;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #13161a;
    border: 1px solid #1e2329;
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #9aa0a6;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #0d0f12;
    color: #00d9ff;
    border-bottom: 2px solid #00d9ff;
}

QTabBar::tab:hover:!selected {
    background-color: #1a1d21;
    color: #e8eaed;
}

/* === Scroll Areas === */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    background-color: #13161a;
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: #2d333b;
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3d444d;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #13161a;
    height: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background-color: #2d333b;
    border-radius: 5px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #3d444d;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === Buttons === */
QPushButton {
    background-color: #1e2329;
    border: 1px solid #2d333b;
    border-radius: 6px;
    padding: 10px 20px;
    color: #e8eaed;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2d333b;
    border-color: #3d444d;
}

QPushButton:pressed {
    background-color: #1a1d21;
}

QPushButton:disabled {
    background-color: #13161a;
    color: #5f6368;
    border-color: #1e2329;
}

/* Primary Button */
QPushButton[class="primary"] {
    background-color: #00d9ff;
    border-color: #00d9ff;
    color: #0d0f12;
}

QPushButton[class="primary"]:hover {
    background-color: #33e1ff;
    border-color: #33e1ff;
}

/* Success Button */
QPushButton[class="success"] {
    background-color: #00c853;
    border-color: #00c853;
    color: #0d0f12;
}

/* Danger Button */
QPushButton[class="danger"] {
    background-color: #ff3d71;
    border-color: #ff3d71;
    color: #ffffff;
}

/* === Input Fields === */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1a1d21;
    border: 1px solid #2d333b;
    border-radius: 6px;
    padding: 10px 14px;
    color: #e8eaed;
    selection-background-color: #00d9ff40;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #00d9ff;
    background-color: #1e2329;
}

QLineEdit:disabled {
    background-color: #13161a;
    color: #5f6368;
}

/* === ComboBox === */
QComboBox {
    background-color: #1a1d21;
    border: 1px solid #2d333b;
    border-radius: 6px;
    padding: 10px 14px;
    color: #e8eaed;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #3d444d;
}

QComboBox:focus {
    border-color: #00d9ff;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: url(dropdown.png);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #1a1d21;
    border: 1px solid #2d333b;
    border-radius: 6px;
    selection-background-color: #00d9ff20;
    selection-color: #00d9ff;
    padding: 4px;
}

/* === CheckBox & RadioButton === */
QCheckBox, QRadioButton {
    spacing: 10px;
    color: #e8eaed;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #2d333b;
    background-color: #1a1d21;
}

QCheckBox::indicator {
    border-radius: 4px;
}

QRadioButton::indicator {
    border-radius: 10px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #00d9ff;
    border-color: #00d9ff;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #00d9ff80;
}

/* === Group Box === */
QGroupBox {
    background-color: #13161a;
    border: 1px solid #1e2329;
    border-radius: 8px;
    margin-top: 20px;
    padding: 20px 16px 16px 16px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    top: 0px;
    background-color: #13161a;
    padding: 4px 12px;
    color: #00d9ff;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* === Tree View & List View === */
QTreeView, QListView, QTableView {
    background-color: #13161a;
    border: 1px solid #1e2329;
    border-radius: 8px;
    alternate-background-color: #1a1d21;
    selection-background-color: #00d9ff20;
    selection-color: #00d9ff;
    outline: none;
}

QTreeView::item, QListView::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px 4px;
}

QTreeView::item:hover, QListView::item:hover {
    background-color: #1e2329;
}

QTreeView::item:selected, QListView::item:selected {
    background-color: #00d9ff20;
    color: #00d9ff;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: url(branch-closed.png);
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: url(branch-open.png);
}

QHeaderView::section {
    background-color: #1a1d21;
    border: none;
    border-bottom: 1px solid #2d333b;
    padding: 10px 16px;
    color: #9aa0a6;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #1e2329;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #00d9ff;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #1a1d21;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d9ff, stop:1 #00ff88);
    border-radius: 6px;
}

/* === Slider === */
QSlider::groove:horizontal {
    background-color: #1e2329;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #00d9ff;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background-color: #33e1ff;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d9ff, stop:1 #00ff88);
    border-radius: 3px;
}

/* === Status Bar === */
QStatusBar {
    background-color: #13161a;
    border-top: 1px solid #1e2329;
    color: #9aa0a6;
    padding: 4px 16px;
}

QStatusBar::item {
    border: none;
}

/* === ToolTip === */
QToolTip {
    background-color: #1e2329;
    border: 1px solid #2d333b;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e8eaed;
    font-size: 12px;
}

/* === Text Edit / Plain Text Edit === */
QTextEdit, QPlainTextEdit {
    background-color: #0d0f12;
    border: 1px solid #1e2329;
    border-radius: 8px;
    padding: 12px;
    color: #e8eaed;
    selection-background-color: #00d9ff40;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #00d9ff40;
}

/* === Label === */
QLabel {
    color: #e8eaed;
}

QLabel[class="heading"] {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
}

QLabel[class="subheading"] {
    font-size: 14px;
    font-weight: 600;
    color: #9aa0a6;
}

QLabel[class="muted"] {
    color: #5f6368;
    font-size: 12px;
}

QLabel[class="success"] {
    color: #00c853;
}

QLabel[class="warning"] {
    color: #ffab00;
}

QLabel[class="error"] {
    color: #ff3d71;
}

QLabel[class="info"] {
    color: #00d9ff;
}

/* === Frame === */
QFrame[class="card"] {
    background-color: #13161a;
    border: 1px solid #1e2329;
    border-radius: 12px;
    padding: 16px;
}

QFrame[class="card-highlight"] {
    background-color: #13161a;
    border: 1px solid #00d9ff40;
    border-radius: 12px;
    padding: 16px;
}

QFrame[class="separator"] {
    background-color: #1e2329;
    max-height: 1px;
}

/* === Dialog === */
QDialog {
    background-color: #0d0f12;
}

QDialogButtonBox {
    button-layout: 3;
}

/* === Message Box === */
QMessageBox {
    background-color: #13161a;
}

QMessageBox QLabel {
    color: #e8eaed;
    font-size: 14px;
}

/* === Custom Classes === */
/* Candle Bullish */
.candle-bullish {
    background-color: #00c853;
}

/* Candle Bearish */
.candle-bearish {
    background-color: #ff3d71;
}

/* Pattern Card */
.pattern-card {
    background-color: #1a1d21;
    border: 1px solid #2d333b;
    border-radius: 8px;
    padding: 12px;
}

.pattern-card:hover {
    border-color: #00d9ff80;
    background-color: #1e2329;
}

/* AI Suggestion */
.ai-suggestion {
    background-color: #00d9ff10;
    border-left: 3px solid #00d9ff;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
}

/* CEL Code Block */
.cel-code {
    background-color: #0d0f12;
    border: 1px solid #1e2329;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    padding: 16px;
}

/* Validation Success */
.validation-success {
    background-color: #00c85320;
    border: 1px solid #00c85380;
    border-radius: 6px;
    padding: 8px 12px;
}

/* Validation Error */
.validation-error {
    background-color: #ff3d7120;
    border: 1px solid #ff3d7180;
    border-radius: 6px;
    padding: 8px 12px;
}
"""

# Color Palette für programmatische Verwendung
DARK_COLORS = {
    # Backgrounds
    'bg_primary': '#0d0f12',
    'bg_secondary': '#13161a',
    'bg_tertiary': '#1a1d21',
    'bg_elevated': '#1e2329',
    
    # Borders
    'border_subtle': '#1e2329',
    'border_default': '#2d333b',
    'border_strong': '#3d444d',
    
    # Text
    'text_primary': '#e8eaed',
    'text_secondary': '#9aa0a6',
    'text_muted': '#5f6368',
    
    # Accent Colors
    'accent_primary': '#00d9ff',
    'accent_primary_hover': '#33e1ff',
    'accent_primary_muted': '#00d9ff40',
    
    # Semantic Colors
    'success': '#00c853',
    'success_bg': '#00c85320',
    'warning': '#ffab00',
    'warning_bg': '#ffab0020',
    'error': '#ff3d71',
    'error_bg': '#ff3d7120',
    'info': '#00d9ff',
    'info_bg': '#00d9ff20',
    
    # Candle Colors
    'candle_bullish': '#00c853',
    'candle_bearish': '#ff3d71',
    'candle_doji': '#9aa0a6',
    
    # Chart Colors
    'chart_grid': '#1e232980',
    'chart_volume': '#00d9ff60',
    'chart_ema': '#ffab00',
    'chart_sma': '#00ff88',
}
