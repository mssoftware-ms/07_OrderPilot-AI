"""
CEL Editor - Dark White Theme Definition
Softer Dark Theme with higher contrast elements
"""

DARK_WHITE_THEME = """
/* ==========================================
   CEL EDITOR - DARK WHITE THEME
   Softer Professional Trading UI
   ========================================== */

/* === Global === */
QMainWindow, QWidget {
    background-color: #1a1d23;
    color: #f0f2f5;
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
}

/* === Menu Bar === */
QMenuBar {
    background-color: #22262e;
    border-bottom: 1px solid #2d333b;
    padding: 4px 8px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    color: #b8bcc4;
}

QMenuBar::item:selected {
    background-color: #2d333b;
    color: #4fc3f7;
}

QMenu {
    background-color: #282c34;
    border: 1px solid #3d444d;
    border-radius: 8px;
    padding: 8px 4px;
}

QMenu::item {
    padding: 8px 24px 8px 16px;
    border-radius: 4px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #4fc3f725;
    color: #4fc3f7;
}

QMenu::separator {
    height: 1px;
    background-color: #3d444d;
    margin: 8px 12px;
}

/* === Tool Bar === */
QToolBar {
    background-color: #22262e;
    border: none;
    border-bottom: 1px solid #2d333b;
    padding: 8px;
    spacing: 8px;
}

QToolBar::separator {
    width: 1px;
    background-color: #3d444d;
    margin: 4px 8px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 8px;
    color: #b8bcc4;
}

QToolButton:hover {
    background-color: #2d333b;
    border-color: #3d444d;
    color: #f0f2f5;
}

QToolButton:pressed {
    background-color: #4fc3f725;
    border-color: #4fc3f740;
}

QToolButton:checked {
    background-color: #4fc3f725;
    border-color: #4fc3f7;
    color: #4fc3f7;
}

/* === Dock Widgets === */
QDockWidget {
    font-weight: 600;
    color: #b8bcc4;
}

QDockWidget::title {
    background-color: #22262e;
    padding: 10px 16px;
    border-bottom: 1px solid #2d333b;
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
    background-color: #3d444d;
    border-radius: 4px;
}

/* === Tab Widget === */
QTabWidget::pane {
    background-color: #1a1d23;
    border: 1px solid #2d333b;
    border-radius: 8px;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #22262e;
    border: 1px solid #2d333b;
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #b8bcc4;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #1a1d23;
    color: #4fc3f7;
    border-bottom: 2px solid #4fc3f7;
}

QTabBar::tab:hover:!selected {
    background-color: #282c34;
    color: #f0f2f5;
}

/* === Scroll Bars === */
QScrollBar:vertical {
    background-color: #22262e;
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: #3d444d;
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4d545d;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #22262e;
    height: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background-color: #3d444d;
    border-radius: 5px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4d545d;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === Buttons === */
QPushButton {
    background-color: #2d333b;
    border: 1px solid #3d444d;
    border-radius: 6px;
    padding: 10px 20px;
    color: #f0f2f5;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3d444d;
    border-color: #4d545d;
}

QPushButton:pressed {
    background-color: #282c34;
}

QPushButton:disabled {
    background-color: #22262e;
    color: #6b7280;
    border-color: #2d333b;
}

/* Primary Button */
QPushButton[class="primary"] {
    background-color: #4fc3f7;
    border-color: #4fc3f7;
    color: #1a1d23;
}

QPushButton[class="primary"]:hover {
    background-color: #7fd4fa;
    border-color: #7fd4fa;
}

/* Success Button */
QPushButton[class="success"] {
    background-color: #66bb6a;
    border-color: #66bb6a;
    color: #1a1d23;
}

/* Danger Button */
QPushButton[class="danger"] {
    background-color: #ef5350;
    border-color: #ef5350;
    color: #ffffff;
}

/* === Input Fields === */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #282c34;
    border: 1px solid #3d444d;
    border-radius: 6px;
    padding: 10px 14px;
    color: #f0f2f5;
    selection-background-color: #4fc3f740;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #4fc3f7;
    background-color: #2d333b;
}

QLineEdit:disabled {
    background-color: #22262e;
    color: #6b7280;
}

/* === ComboBox === */
QComboBox {
    background-color: #282c34;
    border: 1px solid #3d444d;
    border-radius: 6px;
    padding: 10px 14px;
    color: #f0f2f5;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #4d545d;
}

QComboBox:focus {
    border-color: #4fc3f7;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #282c34;
    border: 1px solid #3d444d;
    border-radius: 6px;
    selection-background-color: #4fc3f725;
    selection-color: #4fc3f7;
    padding: 4px;
}

/* === CheckBox & RadioButton === */
QCheckBox, QRadioButton {
    spacing: 10px;
    color: #f0f2f5;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #3d444d;
    background-color: #282c34;
}

QCheckBox::indicator {
    border-radius: 4px;
}

QRadioButton::indicator {
    border-radius: 10px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #4fc3f7;
    border-color: #4fc3f7;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #4fc3f780;
}

/* === Group Box === */
QGroupBox {
    background-color: #22262e;
    border: 1px solid #2d333b;
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
    background-color: #22262e;
    padding: 4px 12px;
    color: #4fc3f7;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* === Tree View & List View === */
QTreeView, QListView, QTableView {
    background-color: #22262e;
    border: 1px solid #2d333b;
    border-radius: 8px;
    alternate-background-color: #282c34;
    selection-background-color: #4fc3f725;
    selection-color: #4fc3f7;
    outline: none;
}

QTreeView::item, QListView::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px 4px;
}

QTreeView::item:hover, QListView::item:hover {
    background-color: #2d333b;
}

QTreeView::item:selected, QListView::item:selected {
    background-color: #4fc3f725;
    color: #4fc3f7;
}

QHeaderView::section {
    background-color: #282c34;
    border: none;
    border-bottom: 1px solid #3d444d;
    padding: 10px 16px;
    color: #b8bcc4;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #2d333b;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #4fc3f7;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #282c34;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4fc3f7, stop:1 #81d4fa);
    border-radius: 6px;
}

/* === Slider === */
QSlider::groove:horizontal {
    background-color: #2d333b;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #4fc3f7;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background-color: #7fd4fa;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4fc3f7, stop:1 #81d4fa);
    border-radius: 3px;
}

/* === Status Bar === */
QStatusBar {
    background-color: #22262e;
    border-top: 1px solid #2d333b;
    color: #b8bcc4;
    padding: 4px 16px;
}

QStatusBar::item {
    border: none;
}

/* === ToolTip === */
QToolTip {
    background-color: #2d333b;
    border: 1px solid #3d444d;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f0f2f5;
    font-size: 12px;
}

/* === Text Edit / Plain Text Edit === */
QTextEdit, QPlainTextEdit {
    background-color: #1a1d23;
    border: 1px solid #2d333b;
    border-radius: 8px;
    padding: 12px;
    color: #f0f2f5;
    selection-background-color: #4fc3f740;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #4fc3f740;
}

/* === Label === */
QLabel {
    color: #f0f2f5;
}

QLabel[class="heading"] {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
}

QLabel[class="subheading"] {
    font-size: 14px;
    font-weight: 600;
    color: #b8bcc4;
}

QLabel[class="muted"] {
    color: #6b7280;
    font-size: 12px;
}

QLabel[class="success"] {
    color: #66bb6a;
}

QLabel[class="warning"] {
    color: #ffa726;
}

QLabel[class="error"] {
    color: #ef5350;
}

QLabel[class="info"] {
    color: #4fc3f7;
}

/* === Frame === */
QFrame[class="card"] {
    background-color: #22262e;
    border: 1px solid #2d333b;
    border-radius: 12px;
    padding: 16px;
}

QFrame[class="card-highlight"] {
    background-color: #22262e;
    border: 1px solid #4fc3f740;
    border-radius: 12px;
    padding: 16px;
}

QFrame[class="separator"] {
    background-color: #2d333b;
    max-height: 1px;
}

/* === Dialog === */
QDialog {
    background-color: #1a1d23;
}

/* === Message Box === */
QMessageBox {
    background-color: #22262e;
}

QMessageBox QLabel {
    color: #f0f2f5;
    font-size: 14px;
}

/* === Custom Classes === */
/* Candle Bullish */
.candle-bullish {
    background-color: #66bb6a;
}

/* Candle Bearish */
.candle-bearish {
    background-color: #ef5350;
}

/* Pattern Card */
.pattern-card {
    background-color: #282c34;
    border: 1px solid #3d444d;
    border-radius: 8px;
    padding: 12px;
}

.pattern-card:hover {
    border-color: #4fc3f780;
    background-color: #2d333b;
}

/* AI Suggestion */
.ai-suggestion {
    background-color: #4fc3f715;
    border-left: 3px solid #4fc3f7;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
}

/* CEL Code Block */
.cel-code {
    background-color: #1a1d23;
    border: 1px solid #2d333b;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    padding: 16px;
}

/* Validation Success */
.validation-success {
    background-color: #66bb6a25;
    border: 1px solid #66bb6a80;
    border-radius: 6px;
    padding: 8px 12px;
}

/* Validation Error */
.validation-error {
    background-color: #ef535025;
    border: 1px solid #ef535080;
    border-radius: 6px;
    padding: 8px 12px;
}
"""

# Color Palette für programmatische Verwendung
DARK_WHITE_COLORS = {
    # Backgrounds
    'bg_primary': '#1a1d23',
    'bg_secondary': '#22262e',
    'bg_tertiary': '#282c34',
    'bg_elevated': '#2d333b',
    
    # Borders
    'border_subtle': '#2d333b',
    'border_default': '#3d444d',
    'border_strong': '#4d545d',
    
    # Text
    'text_primary': '#f0f2f5',
    'text_secondary': '#b8bcc4',
    'text_muted': '#6b7280',
    
    # Accent Colors
    'accent_primary': '#4fc3f7',
    'accent_primary_hover': '#7fd4fa',
    'accent_primary_muted': '#4fc3f740',
    
    # Semantic Colors
    'success': '#66bb6a',
    'success_bg': '#66bb6a25',
    'warning': '#ffa726',
    'warning_bg': '#ffa72625',
    'error': '#ef5350',
    'error_bg': '#ef535025',
    'info': '#4fc3f7',
    'info_bg': '#4fc3f725',
    
    # Candle Colors
    'candle_bullish': '#66bb6a',
    'candle_bearish': '#ef5350',
    'candle_doji': '#b8bcc4',
    
    # Chart Colors
    'chart_grid': '#2d333b80',
    'chart_volume': '#4fc3f760',
    'chart_ema': '#ffa726',
    'chart_sma': '#81d4fa',
}
