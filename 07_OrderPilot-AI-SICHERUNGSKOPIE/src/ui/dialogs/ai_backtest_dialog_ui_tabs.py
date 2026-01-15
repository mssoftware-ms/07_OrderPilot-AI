"""AI Backtest Dialog UI Tabs - Tab Creation Methods.

Refactored from ai_backtest_dialog.py.

Contains all 4 tab creation methods:
- _create_config_tab: Strategy, Symbol, Dates, Capital, AI settings
- _create_results_tab: QTextEdit for backtest results
- _create_ai_tab: Scroll area for AI analysis
- _create_chart_tab: BacktestChartWidget for visualization
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.backtest_chart_widget import BacktestChartWidget

if TYPE_CHECKING:
    from .ai_backtest_dialog import AIBacktestDialog


class AIBacktestDialogUITabs:
    """Helper for creating dialog tabs."""

    def __init__(self, parent: "AIBacktestDialog"):
        self.parent = parent

    def create_config_tab(self) -> QWidget:
        """Create configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Backtest Parameters
        params_group = QGroupBox("Backtest Parameters")
        params_layout = QFormLayout()

        # Strategy
        self.parent.strategy_combo = QComboBox()
        self.parent.strategy_combo.addItems([
            "SMA Crossover",
            "RSI Mean Reversion",
            "MACD Momentum",
            "Bollinger Bands",
            "Trend Following"
        ])
        params_layout.addRow("Strategy:", self.parent.strategy_combo)

        # Symbol
        self.parent.symbol_combo = QComboBox()
        self.parent.symbol_combo.setEditable(True)  # Allow custom symbol input
        self.parent.symbol_combo.addItems(["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "SPY", "QQQ"])

        # Pre-fill with current symbol if provided
        if self.parent.current_symbol:
            # Check if symbol is in list
            index = self.parent.symbol_combo.findText(self.parent.current_symbol.upper())
            if index >= 0:
                self.parent.symbol_combo.setCurrentIndex(index)
            else:
                # Add it to the list and select it
                self.parent.symbol_combo.addItem(self.parent.current_symbol.upper())
                self.parent.symbol_combo.setCurrentText(self.parent.current_symbol.upper())

        params_layout.addRow("Symbol:", self.parent.symbol_combo)

        # Date range
        self.parent.start_date = QDateEdit()
        self.parent.start_date.setDate(QDate.currentDate().addYears(-1))
        self.parent.start_date.setCalendarPopup(True)
        params_layout.addRow("Start Date:", self.parent.start_date)

        self.parent.end_date = QDateEdit()
        self.parent.end_date.setDate(QDate.currentDate())
        self.parent.end_date.setCalendarPopup(True)
        params_layout.addRow("End Date:", self.parent.end_date)

        # Initial capital
        self.parent.capital_spin = QDoubleSpinBox()
        self.parent.capital_spin.setRange(1000, 1000000)
        self.parent.capital_spin.setValue(10000)
        self.parent.capital_spin.setPrefix("€")
        params_layout.addRow("Initial Capital:", self.parent.capital_spin)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # AI Settings
        ai_group = QGroupBox("AI Settings")
        ai_layout = QFormLayout()

        self.parent.ai_enabled = QCheckBox("Enable AI Analysis")
        self.parent.ai_enabled.setChecked(True)
        ai_layout.addRow("AI Analysis:", self.parent.ai_enabled)

        self.parent.provider_combo = QComboBox()
        self.parent.provider_combo.addItems([
            "Anthropic Sonnet 4.5 (Default)",
            "OpenAI GPT-5.1 Thinking",
            "OpenAI GPT-5.1 Instant",
            "OpenAI GPT-4.1 (Coding)",
            "OpenAI GPT-4.1 Nano (Fast)"
        ])
        ai_layout.addRow("AI Provider:", self.parent.provider_combo)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        layout.addStretch()

        return widget

    def create_results_tab(self) -> QWidget:
        """Create results tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Results display
        self.parent.results_text = QTextEdit()
        self.parent.results_text.setReadOnly(True)
        self.parent.results_text.setPlainText("Run a backtest to see results here...")

        font = QFont("Consolas", 10)
        self.parent.results_text.setFont(font)

        layout.addWidget(self.parent.results_text)

        return widget

    def create_ai_tab(self) -> QWidget:
        """Create AI analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Scroll area for AI content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.parent.ai_content = QWidget()
        self.parent.ai_layout = QVBoxLayout(self.parent.ai_content)

        # Placeholder
        placeholder = QLabel("Run backtest and click 'AI Review' to see AI analysis...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; font-size: 14px; padding: 40px;")
        self.parent.ai_layout.addWidget(placeholder)

        scroll.setWidget(self.parent.ai_content)
        layout.addWidget(scroll)

        return widget

    def create_chart_tab(self) -> QWidget:
        """Create chart visualization tab with BacktestChartWidget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add BacktestChartWidget
        self.parent.backtest_chart = BacktestChartWidget()
        layout.addWidget(self.parent.backtest_chart)

        return widget
