"""Dashboard Widget for OrderPilot-AI Trading Application."""

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from src.common.event_bus import Event, EventType, event_bus


class DashboardWidget(QWidget):
    """Main dashboard widget displaying account overview."""

    def __init__(self):
        super().__init__()

        # Track values
        self.current_equity = 10000.00
        self.current_cash = 10000.00
        self.daily_pnl = 0.00
        self.open_positions_count = 0

        self.init_ui()
        self.setup_event_handlers()

    def init_ui(self):
        """Initialize the dashboard UI."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Trading Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Stats grid
        grid = QGridLayout()

        # Account balance
        self.balance_label = self._create_stat_widget("Total Equity", "€10,000.00")
        grid.addWidget(self.balance_label, 0, 0)

        # Cash available
        self.cash_label = self._create_stat_widget("Cash Available", "€10,000.00")
        grid.addWidget(self.cash_label, 0, 1)

        # Daily P&L
        self.pnl_label = self._create_stat_widget("Daily P&L", "€0.00")
        grid.addWidget(self.pnl_label, 1, 0)

        # Open positions
        self.positions_label = self._create_stat_widget("Open Positions", "0")
        grid.addWidget(self.positions_label, 1, 1)

        layout.addLayout(grid)
        layout.addStretch()

    def _create_stat_widget(self, title: str, value: str) -> QFrame:
        """Create a statistics display widget."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        return frame

    def setup_event_handlers(self):
        """Setup event bus handlers."""
        event_bus.subscribe(EventType.ORDER_FILLED, self.on_order_filled)
        event_bus.subscribe(EventType.MARKET_CONNECTED, self.on_market_connected)

    @pyqtSlot(object)
    def on_order_filled(self, event: Event):
        """Handle order filled event."""
        # Trigger dashboard refresh
        self.refresh_stats()

    @pyqtSlot(object)
    def on_market_connected(self, event: Event):
        """Handle market connected event."""
        # Update connection status
        pass

    def update_balance(self, balance):
        """Update balance display.

        Args:
            balance: Balance object or tuple of (equity, cash)
        """
        # Handle both Balance object and tuple/dict
        if hasattr(balance, 'total_equity'):
            # Balance object from broker
            equity = float(balance.total_equity)
            cash = float(balance.cash)
        elif isinstance(balance, (tuple, list)) and len(balance) >= 2:
            # Tuple of (equity, cash)
            equity, cash = balance[0], balance[1]
        elif isinstance(balance, dict):
            # Dict with equity/cash keys
            equity = balance.get('total_equity', balance.get('equity', 10000.0))
            cash = balance.get('cash', 10000.0)
        else:
            # Fallback
            equity = float(balance) if balance else 10000.0
            cash = equity

        self.current_equity = equity
        self.current_cash = cash

        # Update labels
        equity_widget = self.balance_label.findChild(QLabel)
        if equity_widget and hasattr(equity_widget, 'setText'):
            # Find the value label (second label in the widget)
            labels = self.balance_label.findChildren(QLabel)
            if len(labels) >= 2:
                labels[1].setText(f"€{equity:,.2f}")

        cash_widget = self.cash_label.findChild(QLabel)
        if cash_widget:
            labels = self.cash_label.findChildren(QLabel)
            if len(labels) >= 2:
                labels[1].setText(f"€{cash:,.2f}")

    def update_pnl(self, pnl: float):
        """Update P&L display."""
        self.daily_pnl = pnl

        labels = self.pnl_label.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(f"€{pnl:,.2f}")

            # Color code P&L
            if pnl > 0:
                labels[1].setStyleSheet("color: #0f0;")
            elif pnl < 0:
                labels[1].setStyleSheet("color: #f00;")
            else:
                labels[1].setStyleSheet("")

    def update_positions_count(self, count: int):
        """Update open positions count."""
        self.open_positions_count = count

        labels = self.positions_label.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(str(count))

    def refresh_stats(self):
        """Refresh dashboard statistics from database or broker."""
        # In a real implementation, this would query the database or broker
        # For now, we just update the display with current values
        self.update_balance((self.current_equity, self.current_cash))
        self.update_pnl(self.daily_pnl)
        self.update_positions_count(self.open_positions_count)