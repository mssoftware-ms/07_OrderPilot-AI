"""
Market Sessions Overlay Widget.

Displays current market status, active sessions, and price information
overlayed on the chart.
"""
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtGui import QColor, QPalette, QBrush

from src.ui.design_system import THEMES, ColorPalette
from src.core.market_data.market_hours import get_active_sessions, get_next_event, MarketSession

class MarketSessionsOverlay(QWidget):
    """Semi-transparent overlay for market session info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True) # Let clicks pass through to chart? 
        # Actually user might want to select text, but usually overlays are pass-through. 
        # If "MessageBox" implies interaction, I'd disable this. 
        # But for now, chart interaction is priority.
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Data state
        self.current_price = 0.0
        self.prev_close = 0.0
        self.symbol = "--"
        
        self.init_ui()
        
        # Timer for minute-updates (sessions)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_sessions)
        self.timer.start(60000) # Every minute
        
        self.update_sessions()

    def init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Container Frame
        self.container = QFrame()
        self.container.setObjectName("sessionOverlay")
        # Semi-transparent background via stylesheet
        self.container.setStyleSheet("""
            QFrame#sessionOverlay {
                background-color: rgba(20, 25, 30, 180);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
            }
            QLabel {
                color: #EAECEF;
                background: transparent;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(4)
        container_layout.setContentsMargins(12, 8, 12, 8)

        # 1. Active Sessions Row
        self.sessions_layout = QHBoxLayout()
        self.sessions_layout.setSpacing(6)
        container_layout.addLayout(self.sessions_layout)

        # 2. Symbol & Price Row
        price_layout = QHBoxLayout()
        price_layout.setSpacing(10)
        
        self.symbol_label = QLabel("--")
        self.symbol_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #848E9C;")
        price_layout.addWidget(self.symbol_label)
        
        self.price_label = QLabel("0.00")
        self.price_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        price_layout.addWidget(self.price_label)
        
        self.change_label = QLabel("0.00%")
        self.change_label.setStyleSheet("font-size: 14px;")
        price_layout.addWidget(self.change_label)
        
        price_layout.addStretch()
        container_layout.addLayout(price_layout)
        
        # 3. Next Event Label
        self.next_event_label = QLabel("Market Info...")
        self.next_event_label.setStyleSheet("font-size: 11px; color: #848E9C; font-style: italic;")
        container_layout.addWidget(self.next_event_label)

        main_layout.addWidget(self.container)

    def update_price(self, price: float):
        """Update current price display."""
        if price <= 0: return
        
        self.current_price = price
        self.price_label.setText(f"{price:,.2f}")
        
        # Calculate change if we have prev_close
        if self.prev_close > 0:
            change = price - self.prev_close
            pct_change = (change / self.prev_close) * 100
            
            prefix = "+" if change >= 0 else ""
            self.change_label.setText(f"{prefix}{pct_change:.2f}%")
            
            color = "#0ECB81" if change >= 0 else "#F6465D"
            self.change_label.setStyleSheet(f"font-size: 14px; color: {color};")
            
    def set_symbol_info(self, symbol: str, prev_close: float = 0.0):
        """Update symbol and previous close data."""
        self.symbol = symbol
        self.prev_close = prev_close
        self.symbol_label.setText(symbol)
        
        # Reset price labels if symbol changes
        if prev_close > 0:
             self.price_label.setText(f"{prev_close:,.2f}")
             self.change_label.setText("0.00%")
             self.change_label.setStyleSheet("font-size: 14px; color: #848E9C;")

    def update_sessions(self):
        """Update active session badges and next event text."""
        # Update Next Event
        event_text = get_next_event()
        self.next_event_label.setText(event_text)
        
        # Update Session Badges
        # Clear existing
        while self.sessions_layout.count():
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        active_sessions = get_active_sessions()
        
        if not active_sessions:
            lbl = QLabel("MARKET CLOSED")
            lbl.setStyleSheet("""
                background-color: #2A2D33; 
                color: #848E9C; 
                padding: 2px 6px; 
                border-radius: 3px; 
                font-size: 10px; 
                font-weight: bold;
            """)
            self.sessions_layout.addWidget(lbl)
        else:
            for s in active_sessions:
                lbl = QLabel(s.name.upper())
                lbl.setStyleSheet(f"""
                    background-color: {s.color}; 
                    color: white; 
                    padding: 2px 6px; 
                    border-radius: 3px; 
                    font-size: 10px; 
                    font-weight: bold;
                """)
                self.sessions_layout.addWidget(lbl)
                
        self.sessions_layout.addStretch()

