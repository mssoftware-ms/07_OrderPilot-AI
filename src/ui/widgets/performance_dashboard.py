"""Performance Dashboard Widget.

Provides comprehensive performance metrics, analytics,
and reporting for trading activities.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from PyQt6.QtCore import QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

import numpy as np

from src.common.event_bus import Event, EventType, event_bus
from src.database import get_db_manager
from src.database.models import AITelemetry, Order, Position

logger = logging.getLogger(__name__)


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


class PerformanceDashboard(QWidget):
    """Performance dashboard widget."""

    # Signals
    period_changed = pyqtSignal(str)
    report_generated = pyqtSignal(str)

    def __init__(self):
        """Initialize performance dashboard."""
        super().__init__()

        self.db_manager = None  # Will be loaded lazily when database is ready
        self.metrics = PerformanceMetrics()

        self._setup_ui()
        self._setup_timers()

        # Initial load will be deferred until database is ready
        # self._load_performance_data()

        # Subscribe to events
        event_bus.subscribe(EventType.ORDER_FILLED, self._on_order_filled)

    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)

        # Header with period selector
        header_layout = QHBoxLayout()

        header_layout.addWidget(QLabel("Performance Period:"))

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Today", "Week", "Month", "Year", "All Time", "Custom"])
        self.period_combo.currentTextChanged.connect(self._on_period_changed)
        header_layout.addWidget(self.period_combo)

        # Custom date range
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setVisible(False)
        header_layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setVisible(False)
        header_layout.addWidget(self.end_date_edit)

        self.apply_date_button = QPushButton("Apply")
        self.apply_date_button.setVisible(False)
        self.apply_date_button.clicked.connect(self._apply_custom_dates)
        header_layout.addWidget(self.apply_date_button)

        header_layout.addStretch()

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._load_performance_data)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Create tabs
        self.tabs = QTabWidget()

        # Overview tab
        self.overview_tab = self._create_overview_tab()
        self.tabs.addTab(self.overview_tab, "Overview")

        # Returns tab
        self.returns_tab = self._create_returns_tab()
        self.tabs.addTab(self.returns_tab, "Returns")

        # Trades tab
        self.trades_tab = self._create_trades_tab()
        self.tabs.addTab(self.trades_tab, "Trades")

        # Positions tab
        self.positions_tab = self._create_positions_tab()
        self.tabs.addTab(self.positions_tab, "Positions")

        # AI Analytics tab
        self.ai_tab = self._create_ai_tab()
        self.tabs.addTab(self.ai_tab, "AI Analytics")

        # Reports tab
        self.reports_tab = self._create_reports_tab()
        self.tabs.addTab(self.reports_tab, "Reports")

        layout.addWidget(self.tabs)

    def _create_overview_tab(self) -> QWidget:
        """Create overview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Key metrics grid
        metrics_layout = QGridLayout()

        # Create metric cards
        self.total_return_card = MetricCard("Total Return", "0.00", "%")
        metrics_layout.addWidget(self.total_return_card, 0, 0)

        self.daily_return_card = MetricCard("Daily Return", "0.00", "%")
        metrics_layout.addWidget(self.daily_return_card, 0, 1)

        self.sharpe_ratio_card = MetricCard("Sharpe Ratio", "0.00")
        metrics_layout.addWidget(self.sharpe_ratio_card, 0, 2)

        self.max_drawdown_card = MetricCard("Max Drawdown", "0.00", "%")
        metrics_layout.addWidget(self.max_drawdown_card, 0, 3)

        self.win_rate_card = MetricCard("Win Rate", "0.00", "%")
        metrics_layout.addWidget(self.win_rate_card, 1, 0)

        self.profit_factor_card = MetricCard("Profit Factor", "0.00")
        metrics_layout.addWidget(self.profit_factor_card, 1, 1)

        self.total_trades_card = MetricCard("Total Trades", "0")
        metrics_layout.addWidget(self.total_trades_card, 1, 2)

        self.avg_trade_card = MetricCard("Avg Trade", "0.00", "$")
        metrics_layout.addWidget(self.avg_trade_card, 1, 3)

        layout.addLayout(metrics_layout)

        # Equity curve
        if PYQTGRAPH_AVAILABLE:
            equity_group = QGroupBox("Equity Curve")
            equity_layout = QVBoxLayout()

            self.equity_plot = pg.PlotWidget()
            self.equity_plot.showGrid(x=True, y=True, alpha=0.3)
            self.equity_plot.setLabel('left', 'Equity', units='$')
            self.equity_plot.setLabel('bottom', 'Date')
            equity_layout.addWidget(self.equity_plot)

            equity_group.setLayout(equity_layout)
            layout.addWidget(equity_group)
        else:
            layout.addWidget(QLabel("PyQtGraph not installed - Charts unavailable"))

        # Performance summary
        summary_group = QGroupBox("Performance Summary")
        summary_layout = QVBoxLayout()

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        summary_layout.addWidget(self.summary_text)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        return widget

    def _create_returns_tab(self) -> QWidget:
        """Create returns analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Returns table
        returns_group = QGroupBox("Returns Analysis")
        returns_layout = QVBoxLayout()

        self.returns_table = QTableWidget()
        self.returns_table.setColumnCount(5)
        self.returns_table.setHorizontalHeaderLabels([
            "Period", "Return %", "Cumulative %", "Volatility", "Sharpe"
        ])
        self.returns_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Add sample data
        periods = [
            ("Today", 0.5, 0.5, 0.02, 0.8),
            ("This Week", 2.1, 2.6, 0.03, 1.2),
            ("This Month", 5.3, 8.1, 0.04, 1.5),
            ("This Year", 15.2, 24.5, 0.06, 1.8),
            ("All Time", 45.6, 45.6, 0.05, 2.1)
        ]

        self.returns_table.setRowCount(len(periods))
        for i, (period, ret, cum, vol, sharpe) in enumerate(periods):
            self.returns_table.setItem(i, 0, QTableWidgetItem(period))
            self.returns_table.setItem(i, 1, QTableWidgetItem(f"{ret:.2f}%"))
            self.returns_table.setItem(i, 2, QTableWidgetItem(f"{cum:.2f}%"))
            self.returns_table.setItem(i, 3, QTableWidgetItem(f"{vol:.4f}"))
            self.returns_table.setItem(i, 4, QTableWidgetItem(f"{sharpe:.2f}"))

        returns_layout.addWidget(self.returns_table)
        returns_group.setLayout(returns_layout)
        layout.addWidget(returns_group)

        # Returns distribution
        if PYQTGRAPH_AVAILABLE:
            dist_group = QGroupBox("Returns Distribution")
            dist_layout = QVBoxLayout()

            self.returns_hist = pg.PlotWidget()
            self.returns_hist.showGrid(x=True, y=True, alpha=0.3)
            self.returns_hist.setLabel('left', 'Frequency')
            self.returns_hist.setLabel('bottom', 'Daily Return %')
            dist_layout.addWidget(self.returns_hist)

            dist_group.setLayout(dist_layout)
            layout.addWidget(dist_group)

        return widget

    def _create_trades_tab(self) -> QWidget:
        """Create trades analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Trade statistics
        stats_group = QGroupBox("Trade Statistics")
        stats_layout = QGridLayout()

        self.trades_stats_labels = {}
        stats = [
            ("Total Trades", "0"),
            ("Winning Trades", "0"),
            ("Losing Trades", "0"),
            ("Win Rate", "0%"),
            ("Avg Win", "$0"),
            ("Avg Loss", "$0"),
            ("Best Trade", "$0"),
            ("Worst Trade", "$0"),
            ("Avg Duration", "0h"),
            ("Profit Factor", "0.0")
        ]

        for i, (label, value) in enumerate(stats):
            row = i // 2
            col = (i % 2) * 2

            stats_layout.addWidget(QLabel(f"{label}:"), row, col)
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: bold;")
            self.trades_stats_labels[label] = value_label
            stats_layout.addWidget(value_label, row, col + 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Recent trades table
        trades_group = QGroupBox("Recent Trades")
        trades_layout = QVBoxLayout()

        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(8)
        self.trades_table.setHorizontalHeaderLabels([
            "Date", "Symbol", "Side", "Qty", "Entry", "Exit", "P&L", "Return %"
        ])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        trades_layout.addWidget(self.trades_table)
        trades_group.setLayout(trades_layout)
        layout.addWidget(trades_group)

        return widget

    def _create_positions_tab(self) -> QWidget:
        """Create positions tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Current positions
        current_group = QGroupBox("Current Positions")
        current_layout = QVBoxLayout()

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(9)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Qty", "Side", "Avg Cost", "Current", "Market Value",
            "Unrealized P&L", "% Change", "Strategy"
        ])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        current_layout.addWidget(self.positions_table)
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)

        # Position allocation
        if PYQTGRAPH_AVAILABLE:
            allocation_group = QGroupBox("Position Allocation")
            allocation_layout = QVBoxLayout()

            self.allocation_pie = pg.PlotWidget()
            self.allocation_pie.setTitle('Portfolio Allocation')
            allocation_layout.addWidget(self.allocation_pie)

            allocation_group.setLayout(allocation_layout)
            layout.addWidget(allocation_group)

        return widget

    def _create_ai_tab(self) -> QWidget:
        """Create AI analytics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # AI performance metrics
        ai_metrics_group = QGroupBox("AI Performance Metrics")
        ai_metrics_layout = QGridLayout()

        self.ai_metrics_labels = {}
        ai_stats = [
            ("AI Signals Generated", "0"),
            ("AI Approval Rate", "0%"),
            ("AI Win Rate", "0%"),
            ("Avg Confidence", "0%"),
            ("Total API Calls", "0"),
            ("Total Cost", "$0"),
            ("Avg Response Time", "0ms"),
            ("Cache Hit Rate", "0%")
        ]

        for i, (label, value) in enumerate(ai_stats):
            row = i // 2
            col = (i % 2) * 2

            ai_metrics_layout.addWidget(QLabel(f"{label}:"), row, col)
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: bold;")
            self.ai_metrics_labels[label] = value_label
            ai_metrics_layout.addWidget(value_label, row, col + 1)

        ai_metrics_group.setLayout(ai_metrics_layout)
        layout.addWidget(ai_metrics_group)

        # AI analysis history
        ai_history_group = QGroupBox("Recent AI Analysis")
        ai_history_layout = QVBoxLayout()

        self.ai_history_table = QTableWidget()
        self.ai_history_table.setColumnCount(7)
        self.ai_history_table.setHorizontalHeaderLabels([
            "Timestamp", "Symbol", "Signal", "Confidence", "Approved",
            "Response Time", "Cost"
        ])
        self.ai_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        ai_history_layout.addWidget(self.ai_history_table)
        ai_history_group.setLayout(ai_history_layout)
        layout.addWidget(ai_history_group)

        # AI confidence chart
        if PYQTGRAPH_AVAILABLE:
            confidence_group = QGroupBox("AI Confidence Over Time")
            confidence_layout = QVBoxLayout()

            self.confidence_plot = pg.PlotWidget()
            self.confidence_plot.showGrid(x=True, y=True, alpha=0.3)
            self.confidence_plot.setLabel('left', 'Confidence %')
            self.confidence_plot.setLabel('bottom', 'Time')
            confidence_layout.addWidget(self.confidence_plot)

            confidence_group.setLayout(confidence_layout)
            layout.addWidget(confidence_group)

        return widget

    def _create_reports_tab(self) -> QWidget:
        """Create reports tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Report generation
        gen_group = QGroupBox("Generate Report")
        gen_layout = QVBoxLayout()

        # Report type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Report Type:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Daily Summary", "Weekly Performance", "Monthly Statement",
            "Tax Report", "Strategy Analysis", "Risk Report"
        ])
        type_layout.addWidget(self.report_type_combo)
        gen_layout.addLayout(type_layout)

        # Report format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.report_format_combo = QComboBox()
        self.report_format_combo.addItems(["PDF", "HTML", "CSV", "Excel"])
        format_layout.addWidget(self.report_format_combo)
        gen_layout.addLayout(format_layout)

        # Generate button
        self.generate_report_button = QPushButton("Generate Report")
        self.generate_report_button.clicked.connect(self._generate_report)
        gen_layout.addWidget(self.generate_report_button)

        # Progress bar
        self.report_progress = QProgressBar()
        self.report_progress.setVisible(False)
        gen_layout.addWidget(self.report_progress)

        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)

        # Report preview
        preview_group = QGroupBox("Report Preview")
        preview_layout = QVBoxLayout()

        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        preview_layout.addWidget(self.report_preview)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        return widget

    def _setup_timers(self):
        """Setup update timers."""
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._update_metrics)
        self.refresh_timer.start(5000)  # Update every 5 seconds

    def _load_performance_data(self):
        """Load performance data from database."""
        try:
            # Lazy load db_manager if not already initialized
            if self.db_manager is None:
                try:
                    self.db_manager = get_db_manager()
                except RuntimeError:
                    # Database not initialized yet, skip loading
                    logger.debug("Database not initialized yet, skipping performance data load")
                    return

            with self.db_manager.session() as session:
                # Get date range based on selected period
                start_date, end_date = self._get_date_range()

                # Load orders
                orders = session.query(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).all()

                # Load positions
                positions = session.query(Position).all()

                # Load AI telemetry
                ai_data = session.query(AITelemetry).filter(
                    AITelemetry.timestamp >= start_date,
                    AITelemetry.timestamp <= end_date
                ).all()

                # Calculate metrics
                self._calculate_metrics(orders, positions, ai_data)

                # Update UI
                self._update_ui()

        except Exception as e:
            logger.error(f"Error loading performance data: {e}")

    def _get_date_range(self) -> tuple:
        """Get date range based on selected period.

        Returns:
            Tuple of (start_date, end_date)
        """
        period = self.period_combo.currentText()
        end_date = datetime.now()

        if period == "Today":
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "Week":
            start_date = end_date - timedelta(days=7)
        elif period == "Month":
            start_date = end_date - timedelta(days=30)
        elif period == "Year":
            start_date = end_date - timedelta(days=365)
        elif period == "Custom":
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
        else:  # All Time
            start_date = datetime(2000, 1, 1)

        return start_date, end_date

    def _calculate_metrics(self, orders: list[Order], positions: list[Position],
                          ai_data: list[AITelemetry]):
        """Calculate performance metrics.

        Args:
            orders: List of orders
            positions: List of positions
            ai_data: List of AI telemetry records
        """
        # Reset metrics
        self.metrics = PerformanceMetrics()

        if not orders:
            return

        # Calculate trade metrics
        completed_trades = [o for o in orders if o.status == "FILLED"]
        self.metrics.total_trades = len(completed_trades)

        # Calculate P&L
        total_pnl = Decimal('0')
        winning_trades = []
        losing_trades = []

        for order in completed_trades:
            if order.realized_pnl:
                pnl = order.realized_pnl
                total_pnl += pnl

                if pnl > 0:
                    winning_trades.append(float(pnl))
                else:
                    losing_trades.append(float(pnl))

        self.metrics.winning_trades = len(winning_trades)
        self.metrics.losing_trades = len(losing_trades)

        if self.metrics.total_trades > 0:
            self.metrics.win_rate = self.metrics.winning_trades / self.metrics.total_trades

        if winning_trades:
            self.metrics.avg_win = np.mean(winning_trades)
            self.metrics.best_trade = max(winning_trades)

        if losing_trades:
            self.metrics.avg_loss = np.mean(losing_trades)
            self.metrics.worst_trade = min(losing_trades)

        # Calculate profit factor
        if losing_trades:
            gross_profit = sum(winning_trades)
            gross_loss = abs(sum(losing_trades))
            if gross_loss > 0:
                self.metrics.profit_factor = gross_profit / gross_loss

        # Calculate returns (simplified)
        initial_capital = Decimal('10000')  # Assumed
        final_value = initial_capital + total_pnl
        self.metrics.total_return = float((final_value - initial_capital) / initial_capital)
        self.metrics.daily_return = self.metrics.total_return / max(1, (datetime.now() -
                                                                      orders[0].created_at).days)

        # AI metrics
        if ai_data:
            total_calls = len(ai_data)
            total_cost = sum(a.cost for a in ai_data if a.cost)
            avg_response_time = np.mean([a.response_time_ms for a in ai_data
                                        if a.response_time_ms])

            self.ai_metrics_labels["Total API Calls"].setText(str(total_calls))
            self.ai_metrics_labels["Total Cost"].setText(f"${total_cost:.2f}")
            self.ai_metrics_labels["Avg Response Time"].setText(f"{avg_response_time:.0f}ms")

    def _update_ui(self):
        """Update UI with current metrics."""
        # Update metric cards
        self.total_return_card.update_value(f"{self.metrics.total_return:.2f}", "%")
        self.daily_return_card.update_value(f"{self.metrics.daily_return:.2f}", "%")
        self.sharpe_ratio_card.update_value(f"{self.metrics.sharpe_ratio:.2f}")
        self.max_drawdown_card.update_value(f"{self.metrics.max_drawdown:.2f}", "%")
        self.win_rate_card.update_value(f"{self.metrics.win_rate * 100:.1f}", "%")
        self.profit_factor_card.update_value(f"{self.metrics.profit_factor:.2f}")
        self.total_trades_card.update_value(str(self.metrics.total_trades))
        self.avg_trade_card.update_value(f"{self.metrics.avg_win:.2f}", "$")

        # Update trade statistics
        self.trades_stats_labels["Total Trades"].setText(str(self.metrics.total_trades))
        self.trades_stats_labels["Winning Trades"].setText(str(self.metrics.winning_trades))
        self.trades_stats_labels["Losing Trades"].setText(str(self.metrics.losing_trades))
        self.trades_stats_labels["Win Rate"].setText(f"{self.metrics.win_rate * 100:.1f}%")
        self.trades_stats_labels["Avg Win"].setText(f"${self.metrics.avg_win:.2f}")
        self.trades_stats_labels["Avg Loss"].setText(f"${abs(self.metrics.avg_loss):.2f}")
        self.trades_stats_labels["Best Trade"].setText(f"${self.metrics.best_trade:.2f}")
        self.trades_stats_labels["Worst Trade"].setText(f"${self.metrics.worst_trade:.2f}")
        self.trades_stats_labels["Profit Factor"].setText(f"{self.metrics.profit_factor:.2f}")

        # Update summary
        summary = f"""
Performance Summary
==================
Total Return: {self.metrics.total_return:.2%}
Win Rate: {self.metrics.win_rate:.1%}
Profit Factor: {self.metrics.profit_factor:.2f}
Total Trades: {self.metrics.total_trades}
Best Trade: ${self.metrics.best_trade:.2f}
Worst Trade: ${self.metrics.worst_trade:.2f}
        """
        self.summary_text.setText(summary.strip())

    def _update_metrics(self):
        """Update metrics (called by timer)."""
        # Quick update without full reload
        pass

    def _on_period_changed(self, period: str):
        """Handle period change.

        Args:
            period: Selected period
        """
        # Show/hide custom date controls
        is_custom = period == "Custom"
        self.start_date_edit.setVisible(is_custom)
        self.end_date_edit.setVisible(is_custom)
        self.apply_date_button.setVisible(is_custom)

        if not is_custom:
            self._load_performance_data()

        self.period_changed.emit(period)

    def _apply_custom_dates(self):
        """Apply custom date range."""
        self._load_performance_data()

    def _generate_report(self):
        """Generate performance report."""
        report_type = self.report_type_combo.currentText()
        report_format = self.report_format_combo.currentText()

        # Show progress
        self.report_progress.setVisible(True)
        self.generate_report_button.setEnabled(False)

        # Generate report content
        report = self._create_report_content(report_type)

        # Update preview
        self.report_preview.setText(report)

        # Hide progress
        self.report_progress.setVisible(False)
        self.generate_report_button.setEnabled(True)

        # Emit signal
        self.report_generated.emit(report_type)

        logger.info(f"Generated {report_type} report in {report_format} format")

    def _create_report_content(self, report_type: str) -> str:
        """Create report content.

        Args:
            report_type: Type of report

        Returns:
            Report content as text
        """
        content = f"{report_type}\n" + "=" * 50 + "\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        content += "Performance Metrics:\n"
        content += f"  Total Return: {self.metrics.total_return:.2%}\n"
        content += f"  Win Rate: {self.metrics.win_rate:.1%}\n"
        content += f"  Profit Factor: {self.metrics.profit_factor:.2f}\n"
        content += f"  Total Trades: {self.metrics.total_trades}\n"
        content += f"  Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}\n"
        content += f"  Max Drawdown: {self.metrics.max_drawdown:.2%}\n"

        return content

    def _on_order_filled(self, event: Event):
        """Handle order filled event.

        Args:
            event: Order filled event
        """
        self._load_performance_data()

    def _on_position_closed(self, event: Event):
        """Handle position closed event.

        Args:
            event: Position closed event
        """
        self._load_performance_data()