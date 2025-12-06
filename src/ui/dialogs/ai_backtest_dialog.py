"""Enhanced Backtest Dialog with AI Analysis.

Provides AI-powered backtest review and recommendations.
"""

import asyncio
import os
from datetime import datetime

import qasync
from PyQt6.QtCore import QDate, Qt, pyqtSlot
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ai.openai_service import AIConfig, BacktestReview, OpenAIService
from src.core.models.backtest_models import BacktestMetrics, BacktestResult
from src.ui.widgets.backtest_chart_widget import BacktestChartWidget


class AIBacktestDialog(QDialog):
    """Enhanced backtest dialog with AI analysis."""

    def __init__(self, parent=None, current_symbol: str = None):
        """Initialize AI Backtest Dialog.

        Args:
            parent: Parent widget
            current_symbol: Currently selected symbol from chart (optional)
        """
        super().__init__(parent)
        self.setWindowTitle("AI-Powered Backtest")
        self.setModal(True)
        self.setMinimumSize(900, 700)

        self.last_result = None
        self.last_review = None
        self.current_symbol = current_symbol

        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # Tab 1: Configuration
        config_widget = self._create_config_tab()
        tabs.addTab(config_widget, "⚙️ Configuration")

        # Tab 2: Results
        self.results_widget = self._create_results_tab()
        tabs.addTab(self.results_widget, "📊 Results")

        # Tab 3: AI Analysis
        self.ai_widget = self._create_ai_tab()
        tabs.addTab(self.ai_widget, "🤖 AI Analysis")

        # Tab 4: Chart Visualization ✨ NEW
        self.chart_widget = self._create_chart_tab()
        tabs.addTab(self.chart_widget, "📈 Chart")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        self.run_btn = QPushButton("🚀 Run Backtest")
        self.run_btn.clicked.connect(self.run_backtest)
        button_layout.addWidget(self.run_btn)

        self.ai_review_btn = QPushButton("🤖 AI Review")
        self.ai_review_btn.clicked.connect(self.run_ai_review)
        self.ai_review_btn.setEnabled(False)
        button_layout.addWidget(self.ai_review_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.tabs = tabs

    def _create_config_tab(self) -> QWidget:
        """Create configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Backtest Parameters
        params_group = QGroupBox("Backtest Parameters")
        params_layout = QFormLayout()

        # Strategy
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "SMA Crossover",
            "RSI Mean Reversion",
            "MACD Momentum",
            "Bollinger Bands",
            "Trend Following"
        ])
        params_layout.addRow("Strategy:", self.strategy_combo)

        # Symbol
        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)  # Allow custom symbol input
        self.symbol_combo.addItems(["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "SPY", "QQQ"])

        # Pre-fill with current symbol if provided
        if self.current_symbol:
            # Check if symbol is in list
            index = self.symbol_combo.findText(self.current_symbol.upper())
            if index >= 0:
                self.symbol_combo.setCurrentIndex(index)
            else:
                # Add it to the list and select it
                self.symbol_combo.addItem(self.current_symbol.upper())
                self.symbol_combo.setCurrentText(self.current_symbol.upper())

        params_layout.addRow("Symbol:", self.symbol_combo)

        # Date range
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.start_date.setCalendarPopup(True)
        params_layout.addRow("Start Date:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        params_layout.addRow("End Date:", self.end_date)

        # Initial capital
        self.capital_spin = QDoubleSpinBox()
        self.capital_spin.setRange(1000, 1000000)
        self.capital_spin.setValue(10000)
        self.capital_spin.setPrefix("€")
        params_layout.addRow("Initial Capital:", self.capital_spin)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # AI Settings
        ai_group = QGroupBox("AI Settings")
        ai_layout = QFormLayout()

        self.ai_enabled = QCheckBox("Enable AI Analysis")
        self.ai_enabled.setChecked(True)
        ai_layout.addRow("AI Analysis:", self.ai_enabled)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "Anthropic Sonnet 4.5 (Default)",
            "OpenAI GPT-5.1 Thinking",
            "OpenAI GPT-5.1 Instant",
            "OpenAI GPT-4.1 (Coding)",
            "OpenAI GPT-4.1 Nano (Fast)"
        ])
        ai_layout.addRow("AI Provider:", self.provider_combo)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        layout.addStretch()

        return widget

    def _create_results_tab(self) -> QWidget:
        """Create results tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlainText("Run a backtest to see results here...")

        font = QFont("Consolas", 10)
        self.results_text.setFont(font)

        layout.addWidget(self.results_text)

        return widget

    def _create_ai_tab(self) -> QWidget:
        """Create AI analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Scroll area for AI content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.ai_content = QWidget()
        self.ai_layout = QVBoxLayout(self.ai_content)

        # Placeholder
        placeholder = QLabel("Run backtest and click 'AI Review' to see AI analysis...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; font-size: 14px; padding: 40px;")
        self.ai_layout.addWidget(placeholder)

        scroll.setWidget(self.ai_content)
        layout.addWidget(scroll)

        return widget

    def _create_chart_tab(self) -> QWidget:
        """Create chart visualization tab with BacktestChartWidget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add BacktestChartWidget
        self.backtest_chart = BacktestChartWidget()
        layout.addWidget(self.backtest_chart)

        return widget

    @qasync.asyncSlot()
    async def run_backtest(self):
        """Run the backtest."""
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...")
        self.ai_review_btn.setEnabled(False)

        # Get parameters
        strategy = self.strategy_combo.currentText()
        symbol = self.symbol_combo.currentText()
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        capital = self.capital_spin.value()

        # Show progress
        self.results_text.setPlainText(
            f"Running backtest...\n\n"
            f"Strategy: {strategy}\n"
            f"Symbol: {symbol}\n"
            f"Period: {start} to {end}\n"
            f"Capital: €{capital:,.2f}\n\n"
            f"Please wait..."
        )

        try:
            # Run backtest (simulation)
            await asyncio.sleep(1.5)  # Simulate processing

            # Create mock result
            result = self._create_mock_result(strategy, symbol, start, end, capital)
            self.last_result = result

            # Display results
            self._display_results(result)

            # Enable AI review
            self.ai_review_btn.setEnabled(True)

            # Auto-run AI review if enabled
            if self.ai_enabled.isChecked():
                await self.run_ai_review()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backtest failed:\n{str(e)}")

        finally:
            self.run_btn.setEnabled(True)
            self.run_btn.setText("🚀 Run Backtest")

    def _create_mock_result(self, strategy, symbol, start, end, capital) -> BacktestResult:
        """Create mock backtest result."""
        import random

        # Generate realistic metrics
        total_trades = random.randint(40, 80)
        win_rate = random.uniform(0.50, 0.70)
        winning_trades = int(total_trades * win_rate)
        losing_trades = total_trades - winning_trades

        total_return_pct = random.uniform(15.0, 45.0)
        final_capital = capital * (1 + total_return_pct / 100)

        metrics = BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=random.uniform(1.3, 2.2),
            expectancy=random.uniform(30, 150),
            max_drawdown_pct=random.uniform(-20.0, -8.0),
            sharpe_ratio=random.uniform(0.8, 1.8),
            sortino_ratio=random.uniform(1.0, 2.2),
            total_return_pct=total_return_pct,
            annual_return_pct=total_return_pct,
            avg_win=random.uniform(150, 350),
            avg_loss=random.uniform(-100, -180),
            largest_win=random.uniform(500, 1000),
            largest_loss=random.uniform(-300, -600),
            avg_r_multiple=random.uniform(1.5, 2.5),
            max_consecutive_wins=random.randint(4, 8),
            max_consecutive_losses=random.randint(2, 5)
        )

        result = BacktestResult(
            symbol=symbol,
            timeframe="1D",
            mode="backtest",
            start=datetime.combine(start, datetime.min.time()),
            end=datetime.combine(end, datetime.min.time()),
            initial_capital=capital,
            final_capital=final_capital,
            metrics=metrics,
            strategy_name=strategy,
            strategy_params={"strategy_type": strategy}
        )

        return result

    def _display_results(self, result: BacktestResult):
        """Display backtest results."""
        text = f"{'='*70}\n"
        text += f"BACKTEST RESULTS: {result.strategy_name} on {result.symbol}\n"
        text += f"{'='*70}\n\n"

        text += f"Test Period: {result.start.date()} to {result.end.date()}\n"
        text += f"Duration: {result.duration_days:.0f} days\n"
        text += f"Initial Capital: €{result.initial_capital:,.2f}\n"
        text += f"Final Capital: €{result.final_capital:,.2f}\n"
        text += f"Total Return: {result.metrics.total_return_pct:+.2f}%\n"
        text += f"Total P&L: €{result.total_pnl:+,.2f}\n\n"

        text += f"{'─'*70}\n"
        text += "PERFORMANCE METRICS\n"
        text += f"{'─'*70}\n\n"

        text += f"Total Trades: {result.metrics.total_trades}\n"
        text += f"Winning Trades: {result.metrics.winning_trades} ({result.metrics.win_rate*100:.1f}%)\n"
        text += f"Losing Trades: {result.metrics.losing_trades}\n"
        text += f"Profit Factor: {result.metrics.profit_factor:.2f}\n"
        text += f"Expectancy: €{result.metrics.expectancy:.2f}\n\n"

        text += f"Average Win: €{result.metrics.avg_win:.2f}\n"
        text += f"Average Loss: €{result.metrics.avg_loss:.2f}\n"
        text += f"Largest Win: €{result.metrics.largest_win:.2f}\n"
        text += f"Largest Loss: €{result.metrics.largest_loss:.2f}\n\n"

        text += f"{'─'*70}\n"
        text += "RISK METRICS\n"
        text += f"{'─'*70}\n\n"

        text += f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}\n"
        text += f"Sortino Ratio: {result.metrics.sortino_ratio:.2f}\n"
        text += f"Max Drawdown: {result.metrics.max_drawdown_pct:.2f}%\n"
        text += f"Avg R-Multiple: {result.metrics.avg_r_multiple:.2f}\n\n"

        text += f"Max Consecutive Wins: {result.metrics.max_consecutive_wins}\n"
        text += f"Max Consecutive Losses: {result.metrics.max_consecutive_losses}\n"

        self.results_text.setPlainText(text)

        # ✨ NEW: Display results in embedded chart tab
        self.backtest_chart.load_backtest_result(result)

        # ✨ NEW: Open/update chart POPUP window
        self._open_chart_popup(result)

        # Switch to results tab
        self.tabs.setCurrentIndex(1)

    @qasync.asyncSlot()
    async def run_ai_review(self):
        """Run AI analysis on backtest results."""
        if not self.last_result:
            QMessageBox.warning(self, "No Results", "Please run a backtest first.")
            return

        # Check for API key
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            self._show_no_api_key_message()
            return

        self.ai_review_btn.setEnabled(False)
        self.ai_review_btn.setText("Analyzing...")

        try:
            # ===== CRITICAL: USE MULTI-PROVIDER AI FACTORY =====
            from src.ai import get_ai_service

            # Get AI service based on user settings (OpenAI or Anthropic)
            try:
                service = await get_ai_service()
            except ValueError as e:
                QMessageBox.warning(
                    self, "AI Not Configured",
                    f"AI service not available:\n{str(e)}\n\n"
                    f"Please configure AI settings in Settings -> AI tab."
                )
                return

            try:
                # Get AI review
                review = await service.review_backtest(self.last_result)
                self.last_review = review

                # Display AI analysis
                self._display_ai_analysis(review)

                # Switch to AI tab
                self.tabs.setCurrentIndex(2)

            finally:
                await service.close()

        except Exception as e:
            QMessageBox.critical(self, "AI Analysis Error", f"Failed to analyze:\n{str(e)}")

        finally:
            self.ai_review_btn.setEnabled(True)
            self.ai_review_btn.setText("🤖 AI Review")

    def _display_ai_analysis(self, review: BacktestReview):
        """Display AI analysis results."""
        # Clear previous content
        for i in reversed(range(self.ai_layout.count())):
            self.ai_layout.itemAt(i).widget().setParent(None)

        # Overall Assessment
        self._add_section("📊 Overall Assessment", review.overall_assessment)

        # Performance Rating
        rating_widget = QWidget()
        rating_layout = QHBoxLayout(rating_widget)
        rating_label = QLabel(f"⭐ Performance Rating:")
        rating_value = QLabel(f"{review.performance_rating:.1f}/10")
        rating_value.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #4CAF50;"
        )
        rating_layout.addWidget(rating_label)
        rating_layout.addWidget(rating_value)
        rating_layout.addStretch()
        self.ai_layout.addWidget(rating_widget)

        # Adaptability Score
        adapt_widget = QWidget()
        adapt_layout = QHBoxLayout(adapt_widget)
        adapt_label = QLabel(f"🎯 Adaptability Score:")
        adapt_value = QLabel(f"{review.adaptability_score:.1%}")
        adapt_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #2196F3;")
        adapt_layout.addWidget(adapt_label)
        adapt_layout.addWidget(adapt_value)
        adapt_layout.addStretch()
        self.ai_layout.addWidget(adapt_widget)

        # Strengths
        self._add_list_section("💪 Strengths", review.strengths, "#4CAF50")

        # Weaknesses
        self._add_list_section("⚠️ Weaknesses", review.weaknesses, "#FF9800")

        # Suggested Improvements
        improvements_group = QGroupBox("🔧 Suggested Improvements")
        improvements_layout = QVBoxLayout()

        for i, improvement in enumerate(review.suggested_improvements, 1):
            imp_widget = self._create_improvement_widget(i, improvement)
            improvements_layout.addWidget(imp_widget)

        improvements_group.setLayout(improvements_layout)
        self.ai_layout.addWidget(improvements_group)

        # Parameter Recommendations
        if review.parameter_recommendations:
            self._add_dict_section("📈 Parameter Recommendations",
                                   review.parameter_recommendations)

        # Risk Assessment
        self._add_section("⚖️ Risk Assessment", review.risk_assessment)

        # Drawdown Analysis
        self._add_section("📉 Max Drawdown Analysis", review.max_drawdown_analysis)

        # Market Conditions
        self._add_section("🌍 Market Conditions", review.market_conditions_analysis)

        self.ai_layout.addStretch()

    def _add_section(self, title: str, content: str):
        """Add a section with title and content."""
        group = QGroupBox(title)
        layout = QVBoxLayout()

        text = QLabel(content)
        text.setWordWrap(True)
        text.setStyleSheet("padding: 10px; font-size: 12px;")
        layout.addWidget(text)

        group.setLayout(layout)
        self.ai_layout.addWidget(group)

    def _add_list_section(self, title: str, items: list[str], color: str):
        """Add a section with a bullet-point list."""
        group = QGroupBox(title)
        layout = QVBoxLayout()

        for item in items:
            label = QLabel(f"• {item}")
            label.setWordWrap(True)
            label.setStyleSheet(f"padding: 5px; color: {color}; font-size: 12px;")
            layout.addWidget(label)

        group.setLayout(layout)
        self.ai_layout.addWidget(group)

    def _add_dict_section(self, title: str, data: dict):
        """Add a section displaying dictionary data."""
        group = QGroupBox(title)
        layout = QFormLayout()

        for key, value in data.items():
            layout.addRow(f"{key}:", QLabel(str(value)))

        group.setLayout(layout)
        self.ai_layout.addWidget(group)

    def _create_improvement_widget(self, index: int, improvement: dict) -> QWidget:
        """Create widget for improvement suggestion."""
        widget = QGroupBox(f"Improvement #{index}")
        layout = QVBoxLayout()

        # Improvement text
        imp_text = QLabel(improvement.get("improvement", "N/A"))
        imp_text.setWordWrap(True)
        imp_text.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(imp_text)

        # Impact
        impact_label = QLabel(f"Expected Impact: {improvement.get('expected_impact', 'N/A')}")
        impact_label.setStyleSheet("padding: 5px; color: #4CAF50;")
        layout.addWidget(impact_label)

        # Difficulty
        difficulty = improvement.get("implementation_difficulty", "medium")
        color = {"easy": "#4CAF50", "medium": "#FF9800", "hard": "#F44336"}.get(difficulty, "#888")
        diff_label = QLabel(f"Difficulty: {difficulty.upper()}")
        diff_label.setStyleSheet(f"padding: 5px; color: {color}; font-weight: bold;")
        layout.addWidget(diff_label)

        widget.setLayout(layout)
        return widget

    def _open_chart_popup(self, result):
        """Open chart popup window with backtest results.

        Args:
            result: BacktestResult to display
        """
        # Get parent app to access chart_window_manager
        parent_app = self.parent()
        if not hasattr(parent_app, 'chart_window_manager'):
            logger.warning("Parent app doesn't have chart_window_manager")
            return

        # Open or focus chart window for symbol
        chart_window = parent_app.chart_window_manager.open_or_focus_chart(result.symbol)

        # Load backtest result into chart
        chart_window.load_backtest_result(result)

        logger.info(f"Opened chart popup for {result.symbol} with backtest results")

    def _show_no_api_key_message(self):
        """Show message when no API key is configured."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("API Key Required")
        msg.setText("AI Analysis requires an API key.")
        msg.setInformativeText(
            "Please set one of these environment variables:\n\n"
            "• ANTHROPIC_API_KEY (for Claude Sonnet 4.5)\n"
            "• OPENAI_API_KEY (for GPT-5.1)\n\n"
            "Restart the application after setting the key."
        )
        msg.exec()
