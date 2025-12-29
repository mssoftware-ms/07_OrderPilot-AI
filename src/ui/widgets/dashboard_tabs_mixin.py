"""Dashboard Tabs Mixin.

Contains tab creation methods for PerformanceDashboard.
"""

from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

from .dashboard_metrics import MetricCard


class DashboardTabsMixin:
    """Mixin providing tab creation methods for PerformanceDashboard."""

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
