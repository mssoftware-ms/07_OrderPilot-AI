"""Dashboard Metrics and Widget Components.

Contains PerformanceMetrics dataclass and MetricCard widget.
"""

from dataclasses import dataclass
from datetime import timedelta

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


@dataclass
class PerformanceMetrics:
    """Performance metrics data."""
    total_return: float = 0.0
    daily_return: float = 0.0
    monthly_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_trade_duration: timedelta = timedelta()
    best_trade: float = 0.0
    worst_trade: float = 0.0


class MetricCard(QWidget):
    """Widget for displaying a single metric."""

    def __init__(self, title: str, value: str = "0", suffix: str = "",
                 color: str | None = None):
        """Initialize metric card.

        Args:
            title: Metric title
            value: Metric value
            suffix: Value suffix (%, $, etc.)
            color: Text color
        """
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(2)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(title_label)

        # Value
        self.value_label = QLabel(f"{value}{suffix}")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.value_label.setFont(font)

        if color:
            self.value_label.setStyleSheet(f"color: {color};")

        layout.addWidget(self.value_label)

        self.setMaximumHeight(80)

    def update_value(self, value: str, suffix: str = ""):
        """Update the metric value.

        Args:
            value: New value
            suffix: Value suffix
        """
        self.value_label.setText(f"{value}{suffix}")
