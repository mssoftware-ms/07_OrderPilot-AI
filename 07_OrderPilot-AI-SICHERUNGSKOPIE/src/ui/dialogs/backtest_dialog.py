"""Backtest Dialog for OrderPilot-AI Trading Application."""

import asyncio

import qasync
from PyQt6.QtCore import QDate, pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class BacktestDialog(QDialog):
    """Dialog for running backtests."""

    def __init__(self, ai_service, parent=None):
        super().__init__(parent)
        self.ai_service = ai_service
        self.setWindowTitle("Run Backtest")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        """Initialize the backtest dialog UI."""
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)

        # Backtest parameters
        params_group = QGroupBox("Backtest Parameters")
        params_layout = QFormLayout()

        # Strategy
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "RSI Mean Reversion",
            "Moving Average Crossover",
            "Bollinger Bands",
            "MACD Strategy",
            "Trend Following"
        ])
        params_layout.addRow("Strategy:", self.strategy_combo)

        # Symbol
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "SPY", "QQQ"])
        params_layout.addRow("Symbol:", self.symbol_combo)

        # Date range
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-6))
        self.start_date.setCalendarPopup(True)
        params_layout.addRow("Start Date:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        params_layout.addRow("End Date:", self.end_date)

        # Initial capital
        self.capital_spin = QDoubleSpinBox()
        self.capital_spin.setRange(100, 1000000)
        self.capital_spin.setValue(10000)
        self.capital_spin.setPrefix("€")
        params_layout.addRow("Initial Capital:", self.capital_spin)

        # Commission
        self.commission_spin = QDoubleSpinBox()
        self.commission_spin.setRange(0, 10)
        self.commission_spin.setValue(0.1)
        self.commission_spin.setSingleStep(0.1)
        self.commission_spin.setSuffix("%")
        params_layout.addRow("Commission:", self.commission_spin)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Results section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlainText("Configure parameters and click 'Run Backtest' to start...")
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.run_btn = QPushButton("Run Backtest")
        self.run_btn.clicked.connect(self.run_backtest)
        button_layout.addWidget(self.run_btn)

        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_results)
        export_btn.setEnabled(False)
        self.export_btn = export_btn
        button_layout.addWidget(export_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Store backtest results
        self.last_results = None

    @qasync.asyncSlot()
    async def run_backtest(self):
        """Run the backtest."""
        # Disable button during run
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...")
        self.export_btn.setEnabled(False)

        # Get parameters
        strategy = self.strategy_combo.currentText()
        symbol = self.symbol_combo.currentText()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        initial_capital = self.capital_spin.value()
        commission = self.commission_spin.value() / 100.0

        # Show progress
        self.results_text.setPlainText(
            f"Running backtest...\n\n"
            f"Strategy: {strategy}\n"
            f"Symbol: {symbol}\n"
            f"Period: {start_date} to {end_date}\n"
            f"Initial Capital: €{initial_capital:,.2f}\n"
            f"Commission: {commission*100:.2f}%\n\n"
            f"Please wait..."
        )

        try:
            # Simulate backtest execution
            results = await self._run_backtest_simulation(
                strategy, symbol, start_date, end_date, initial_capital, commission
            )

            # Store results
            self.last_results = results

            # Display results
            results_text = f"Backtest Results: {strategy} on {symbol}\n"
            results_text += "=" * 60 + "\n\n"

            results_text += f"Test Period: {start_date} to {end_date}\n"
            results_text += f"Initial Capital: €{initial_capital:,.2f}\n"
            results_text += f"Final Value: €{results['final_value']:,.2f}\n"
            results_text += f"Total Return: {results['total_return']:.2f}%\n\n"

            results_text += "Performance Metrics:\n"
            results_text += f"  Total Trades: {results['total_trades']}\n"
            results_text += f"  Winning Trades: {results['winning_trades']} ({results['win_rate']:.1f}%)\n"
            results_text += f"  Losing Trades: {results['losing_trades']}\n"
            results_text += f"  Average Win: €{results['avg_win']:,.2f}\n"
            results_text += f"  Average Loss: €{results['avg_loss']:,.2f}\n"
            results_text += f"  Max Drawdown: {results['max_drawdown']:.2f}%\n\n"

            results_text += "Risk Metrics:\n"
            results_text += f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}\n"
            results_text += f"  Sortino Ratio: {results['sortino_ratio']:.2f}\n"
            results_text += f"  Calmar Ratio: {results['calmar_ratio']:.2f}\n\n"

            results_text += f"Commission Paid: €{results['total_commission']:,.2f}\n"

            self.results_text.setPlainText(results_text)

            # Enable export
            self.export_btn.setEnabled(True)

        except Exception as e:
            self.results_text.setPlainText(
                f"Error running backtest:\n{str(e)}\n\n"
                f"Please check your parameters and try again."
            )

        finally:
            # Re-enable button
            self.run_btn.setEnabled(True)
            self.run_btn.setText("Run Backtest")

    async def _run_backtest_simulation(self, strategy, symbol, start_date, end_date,
                                       initial_capital, commission):
        """Simulate backtest execution."""
        # Simulate processing time
        await asyncio.sleep(2.0)

        # Mock backtest results (in real implementation, would use backtrader or similar)
        import random

        total_trades = random.randint(50, 200)
        win_rate = random.uniform(45, 65)
        winning_trades = int(total_trades * win_rate / 100)
        losing_trades = total_trades - winning_trades

        total_return = random.uniform(-10, 40)
        final_value = initial_capital * (1 + total_return / 100)

        return {
            'strategy': strategy,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': random.uniform(50, 200),
            'avg_loss': random.uniform(30, 150),
            'max_drawdown': random.uniform(5, 25),
            'sharpe_ratio': random.uniform(0.5, 2.5),
            'sortino_ratio': random.uniform(0.6, 3.0),
            'calmar_ratio': random.uniform(0.4, 2.0),
            'total_commission': total_trades * initial_capital * commission * 0.01
        }

    @pyqtSlot()
    def export_results(self):
        """Export backtest results."""
        if not self.last_results:
            QMessageBox.warning(
                self, "No Results",
                "Please run a backtest first before exporting."
            )
            return

        try:
            # In real implementation, would save to CSV/Excel
            QMessageBox.information(
                self, "Export Results",
                "Backtest results would be exported to:\n"
                f"backtest_{self.last_results['symbol']}_{self.last_results['strategy']}.csv\n\n"
                "(Export functionality to be implemented)"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Export Error",
                f"Failed to export results:\n{str(e)}"
            )
