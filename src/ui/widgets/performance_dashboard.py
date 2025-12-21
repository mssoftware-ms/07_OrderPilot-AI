"""Performance Dashboard Widget.

Provides comprehensive performance metrics, analytics,
and reporting for trading activities.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- dashboard_metrics.py: PerformanceMetrics, MetricCard
- dashboard_tabs_mixin.py: Tab creation methods
- performance_dashboard.py: Main dashboard class (this file)
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from PyQt6.QtCore import QDate, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import numpy as np

from src.common.event_bus import Event, EventType, event_bus
from src.database import get_db_manager
from src.database.models import AITelemetry, Order, Position

from .dashboard_metrics import MetricCard, PerformanceMetrics
from .dashboard_tabs_mixin import DashboardTabsMixin

# Re-export for backward compatibility
__all__ = [
    "PerformanceMetrics",
    "MetricCard",
    "PerformanceDashboard",
]

logger = logging.getLogger(__name__)


class PerformanceDashboard(DashboardTabsMixin, QWidget):
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
        """Get date range based on selected period."""
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
        """Calculate performance metrics."""
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
        """Handle period change."""
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
        """Create report content."""
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
        """Handle order filled event."""
        self._load_performance_data()

    def _on_position_closed(self, event: Event):
        """Handle position closed event."""
        self._load_performance_data()
