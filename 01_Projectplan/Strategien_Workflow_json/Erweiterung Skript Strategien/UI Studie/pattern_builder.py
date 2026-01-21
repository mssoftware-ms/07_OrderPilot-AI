"""
CEL Editor - Pattern Builder Canvas Widget
Interaktiver visueller Pattern-Builder mit Drag & Drop Kerzen
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QToolButton, QScrollArea, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem,
    QSizePolicy, QMenu, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient,
    QPainterPath, QCursor
)


class CandleItem(QGraphicsRectItem):
    """
    Einzelne Kerze im Pattern Builder
    Unterstützt Drag & Drop und visuelle Konfiguration
    """
    
    def __init__(self, candle_type="bullish", index=0, parent=None):
        super().__init__(parent)
        
        self.candle_type = candle_type  # bullish, bearish, doji
        self.index = index
        self.is_selected = False
        
        # Dimensionen
        self.body_width = 40
        self.body_height = 80
        self.wick_width = 2
        self.upper_wick_height = 30
        self.lower_wick_height = 25
        
        # Farben basierend auf Typ
        self.colors = {
            'bullish': {'body': '#00c853', 'border': '#00e676'},
            'bearish': {'body': '#ff3d71', 'border': '#ff6b8a'},
            'doji': {'body': '#9aa0a6', 'border': '#b8bcc4'},
        }
        
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        
        # Bounding rect setzen
        total_height = self.upper_wick_height + self.body_height + self.lower_wick_height
        self.setRect(0, 0, self.body_width, total_height)
        
    def paint(self, painter, option, widget):
        """Kerze zeichnen"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        colors = self.colors.get(self.candle_type, self.colors['doji'])
        body_color = QColor(colors['body'])
        border_color = QColor(colors['border'])
        
        # Wenn selektiert, hellere Farben
        if self.isSelected():
            body_color = body_color.lighter(120)
            border_color = QColor('#00d9ff')
        
        # Wick (Docht) zeichnen
        wick_x = self.body_width / 2 - self.wick_width / 2
        wick_pen = QPen(body_color, self.wick_width)
        painter.setPen(wick_pen)
        
        # Oberer Docht
        painter.drawLine(
            int(self.body_width / 2), 0,
            int(self.body_width / 2), int(self.upper_wick_height)
        )
        
        # Unterer Docht
        painter.drawLine(
            int(self.body_width / 2), int(self.upper_wick_height + self.body_height),
            int(self.body_width / 2), int(self.upper_wick_height + self.body_height + self.lower_wick_height)
        )
        
        # Body zeichnen
        body_rect = QRectF(
            0, self.upper_wick_height,
            self.body_width, self.body_height
        )
        
        # Gradient für Body
        gradient = QLinearGradient(body_rect.topLeft(), body_rect.bottomRight())
        gradient.setColorAt(0, body_color.lighter(110))
        gradient.setColorAt(1, body_color)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(body_rect, 4, 4)
        
        # OHLC Labels
        if self.isSelected():
            font = QFont('JetBrains Mono', 8)
            painter.setFont(font)
            painter.setPen(QPen(QColor('#e8eaed')))
            
            # High Label
            painter.drawText(int(self.body_width + 5), 8, "H")
            # Open Label
            painter.drawText(int(self.body_width + 5), int(self.upper_wick_height + 12), "O")
            # Close Label
            painter.drawText(int(self.body_width + 5), int(self.upper_wick_height + self.body_height - 5), "C")
            # Low Label
            painter.drawText(int(self.body_width + 5), int(self.upper_wick_height + self.body_height + self.lower_wick_height - 5), "L")
        
        # Index Label
        font = QFont('JetBrains Mono', 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor('#ffffff')))
        index_text = f"[{-self.index}]" if self.index > 0 else "[0]"
        painter.drawText(body_rect, Qt.AlignmentFlag.AlignCenter, index_text)


class RelationLine(QGraphicsLineItem):
    """
    Visuelle Verbindungslinie zwischen Kerzen
    Zeigt Relationen wie >, <, ≈
    """
    
    def __init__(self, start_point, end_point, relation_type="greater", parent=None):
        super().__init__(parent)
        
        self.relation_type = relation_type
        self.setLine(start_point.x(), start_point.y(), end_point.x(), end_point.y())
        
        # Stil basierend auf Relation
        colors = {
            'greater': '#00c853',
            'less': '#ff3d71',
            'equal': '#ffab00',
            'near': '#00d9ff',
        }
        
        color = QColor(colors.get(relation_type, '#9aa0a6'))
        pen = QPen(color, 2, Qt.PenStyle.DashLine)
        self.setPen(pen)


class PatternBuilderCanvas(QWidget):
    """
    Hauptwidget für den visuellen Pattern Builder
    Enthält die Candle-Drag-Zone und Relation-Editor
    """
    
    pattern_changed = Signal(dict)  # Emitted wenn Pattern sich ändert
    candle_selected = Signal(int)   # Emitted wenn Kerze ausgewählt wird
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header mit Tools
        self.header = self.create_header()
        layout.addWidget(self.header)
        
        # Hauptbereich mit Canvas
        self.main_area = QFrame()
        self.main_area.setObjectName("patternBuilderMain")
        self.main_area.setStyleSheet("""
            #patternBuilderMain {
                background-color: #0d0f12;
                border: 1px solid #1e2329;
                border-radius: 8px;
            }
        """)
        
        main_layout = QVBoxLayout(self.main_area)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Graphics Scene & View
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor('#0d0f12')))
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setStyleSheet("""
            QGraphicsView {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Grid zeichnen
        self.draw_grid()
        
        main_layout.addWidget(self.view)
        
        # Candle Toolbar (unten)
        self.candle_toolbar = self.create_candle_toolbar()
        main_layout.addWidget(self.candle_toolbar)
        
        layout.addWidget(self.main_area)
        
    def create_header(self):
        """Header mit Titel und Aktionen"""
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border-bottom: 1px solid #1e2329;
                border-radius: 8px 8px 0 0;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Titel
        title = QLabel("Pattern Builder")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #e8eaed;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Toolbar Buttons
        buttons_data = [
            ("🗑️", "Clear All", "clear"),
            ("↩️", "Undo", "undo"),
            ("↪️", "Redo", "redo"),
            ("📋", "Copy Pattern", "copy"),
            ("📥", "Paste Pattern", "paste"),
            ("🔍+", "Zoom In", "zoom_in"),
            ("🔍-", "Zoom Out", "zoom_out"),
            ("⚙️", "Settings", "settings"),
        ]
        
        for icon, tooltip, action in buttons_data:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(tooltip)
            btn.setFixedSize(36, 36)
            btn.setObjectName(f"btn_{action}")
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
            layout.addWidget(btn)
        
        return header
        
    def create_candle_toolbar(self):
        """Toolbar zum Hinzufügen von Kerzen"""
        toolbar = QFrame()
        toolbar.setFixedHeight(80)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #13161a;
                border: 1px solid #1e2329;
                border-radius: 8px;
                margin-top: 12px;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Label
        label = QLabel("Drag to Canvas:")
        label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        layout.addWidget(label)
        
        # Kerzen-Typen
        candle_types = [
            ("🟢", "Bullish Candle", "bullish", "#00c853"),
            ("🔴", "Bearish Candle", "bearish", "#ff3d71"),
            ("⚪", "Doji", "doji", "#9aa0a6"),
            ("📍", "Pin Bar (Bull)", "pinbar_bull", "#00c853"),
            ("📍", "Pin Bar (Bear)", "pinbar_bear", "#ff3d71"),
            ("📦", "Inside Bar", "inside_bar", "#ffab00"),
            ("📈", "Engulfing (Bull)", "engulfing_bull", "#00c853"),
            ("📉", "Engulfing (Bear)", "engulfing_bear", "#ff3d71"),
        ]
        
        for icon, tooltip, candle_type, color in candle_types:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(tooltip)
            btn.setFixedSize(50, 50)
            btn.setProperty("candle_type", candle_type)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: #1a1d21;
                    border: 2px solid {color}40;
                    border-radius: 8px;
                    font-size: 20px;
                }}
                QToolButton:hover {{
                    background-color: {color}20;
                    border-color: {color};
                }}
                QToolButton:pressed {{
                    background-color: {color}30;
                }}
            """)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Quick Actions
        quick_label = QLabel("Quick:")
        quick_label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        layout.addWidget(quick_label)
        
        quick_patterns = [
            ("2-Bar", "Add 2-Bar Pattern"),
            ("3-Bar", "Add 3-Bar Pattern"),
            ("Template", "From Template"),
        ]
        
        for text, tooltip in quick_patterns:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(60, 36)
            btn.setStyleSheet("""
                QToolButton {
                    background-color: #1e2329;
                    border: 1px solid #2d333b;
                    border-radius: 6px;
                    color: #e8eaed;
                    font-size: 11px;
                    font-weight: 500;
                }
                QToolButton:hover {
                    background-color: #2d333b;
                    border-color: #00d9ff;
                    color: #00d9ff;
                }
            """)
            layout.addWidget(btn)
        
        return toolbar
        
    def draw_grid(self):
        """Zeichnet ein Grid auf die Scene"""
        grid_color = QColor('#1e232940')
        pen = QPen(grid_color, 1, Qt.PenStyle.DotLine)
        
        grid_size = 50
        width = 1200
        height = 400
        
        # Vertikale Linien
        for x in range(0, width, grid_size):
            line = self.scene.addLine(x, 0, x, height, pen)
            
        # Horizontale Linien
        for y in range(0, height, grid_size):
            line = self.scene.addLine(0, y, width, y, pen)
            
        # Zentrale Zeitachse
        timeline_pen = QPen(QColor('#2d333b'), 2)
        self.scene.addLine(0, height/2, width, height/2, timeline_pen)
        
        # Demo-Kerzen hinzufügen
        self.add_demo_candles()
        
    def add_demo_candles(self):
        """Fügt Demo-Kerzen für die Vorschau hinzu"""
        # Bearish Candle (Bar[-2])
        candle1 = CandleItem(candle_type="bearish", index=2)
        candle1.setPos(200, 100)
        self.scene.addItem(candle1)
        
        # Bullish Candle (Bar[-1])
        candle2 = CandleItem(candle_type="bullish", index=1)
        candle2.setPos(300, 80)
        self.scene.addItem(candle2)
        
        # Relation Line zwischen den Kerzen
        relation = RelationLine(
            QPointF(240, 130),
            QPointF(300, 110),
            relation_type="greater"
        )
        self.scene.addItem(relation)


class CandlePropertiesPanel(QFrame):
    """
    Panel zur Konfiguration der ausgewählten Kerze
    """
    
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
        layout.setSpacing(16)
        
        # Header
        header = QLabel("Candle Properties")
        header.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #00d9ff;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(header)
        
        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #1e2329;")
        layout.addWidget(sep)
        
        # Index Input
        index_row = self.create_property_row("Bar Index:", "[-1]")
        layout.addLayout(index_row)
        
        # Direction
        direction_row = self.create_property_row("Direction:", "Bullish ▲")
        layout.addLayout(direction_row)
        
        # Body Size
        body_row = self.create_property_row("Body Size:", "Normal")
        layout.addLayout(body_row)
        
        # Upper Wick
        upper_wick_row = self.create_property_row("Upper Wick:", "Medium")
        layout.addLayout(upper_wick_row)
        
        # Lower Wick
        lower_wick_row = self.create_property_row("Lower Wick:", "Short")
        layout.addLayout(lower_wick_row)
        
        layout.addStretch()
        
    def create_property_row(self, label_text, value_text):
        """Erstellt eine Property-Zeile"""
        row = QHBoxLayout()
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        label.setFixedWidth(90)
        row.addWidget(label)
        
        value = QLabel(value_text)
        value.setStyleSheet("""
            color: #e8eaed;
            font-size: 12px;
            background-color: #1a1d21;
            border: 1px solid #2d333b;
            border-radius: 4px;
            padding: 6px 10px;
        """)
        row.addWidget(value)
        
        return row
