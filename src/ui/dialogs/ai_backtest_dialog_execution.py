"""AI Backtest Dialog Execution - Backtest Runner and Mock Generator.

Refactored from ai_backtest_dialog.py.

Contains:
- run_backtest: Async method to execute backtest with progress updates
- _create_mock_result: Generate realistic mock backtest result for demo
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtWidgets import QMessageBox

from src.core.models.backtest_models import BacktestMetrics, BacktestResult

if TYPE_CHECKING:
    from .ai_backtest_dialog import AIBacktestDialog

logger = logging.getLogger(__name__)


class AIBacktestDialogExecution:
    """Helper for backtest execution."""

    def __init__(self, parent: "AIBacktestDialog"):
        self.parent = parent

    @qasync.asyncSlot()
    async def run_backtest(self):
        """Run the backtest."""
        self.parent.run_btn.setEnabled(False)
        self.parent.run_btn.setText("Running...")
        self.parent.ai_review_btn.setEnabled(False)

        # Get parameters
        strategy = self.parent.strategy_combo.currentText()
        symbol = self.parent.symbol_combo.currentText()
        start = self.parent.start_date.date().toPyDate()
        end = self.parent.end_date.date().toPyDate()
        capital = self.parent.capital_spin.value()

        # Show progress
        self.parent.results_text.setPlainText(
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
            self.parent.last_result = result

            # Display results
            self.parent._display.display_results(result)

            # Enable AI review
            self.parent.ai_review_btn.setEnabled(True)

            # Auto-run AI review if enabled
            if self.parent.ai_enabled.isChecked():
                await self.parent._ai_review.run_ai_review()

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Backtest failed:\n{str(e)}")

        finally:
            self.parent.run_btn.setEnabled(True)
            self.parent.run_btn.setText("🚀 Run Backtest")

    def _create_mock_result(self, strategy, symbol, start, end, capital) -> BacktestResult:
        """Create mock backtest result."""
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
