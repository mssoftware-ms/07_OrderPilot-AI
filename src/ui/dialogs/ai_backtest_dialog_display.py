"""AI Backtest Dialog Display - Results Display and Chart Opening.

Refactored from ai_backtest_dialog.py.

Contains:
- display_results: Format and display backtest results in text + chart
- _open_chart_popup: Open standalone chart window with results
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.models.backtest_models import BacktestResult

if TYPE_CHECKING:
    from .ai_backtest_dialog import AIBacktestDialog

logger = logging.getLogger(__name__)


class AIBacktestDialogDisplay:
    """Helper for results display."""

    def __init__(self, parent: "AIBacktestDialog"):
        self.parent = parent

    def display_results(self, result: BacktestResult):
        """Display backtest results."""
        m = result.metrics
        text = (f"{'='*70}\nBACKTEST RESULTS: {result.strategy_name} on {result.symbol}\n{'='*70}\n\n"
                f"Test Period: {result.start.date()} to {result.end.date()}\nDuration: {result.duration_days:.0f} days\n"
                f"Initial Capital: €{result.initial_capital:,.2f}\nFinal Capital: €{result.final_capital:,.2f}\n"
                f"Total Return: {m.total_return_pct:+.2f}%\nTotal P&L: €{result.total_pnl:+,.2f}\n\n"
                f"{'─'*70}\nPERFORMANCE METRICS\n{'─'*70}\n\n"
                f"Total Trades: {m.total_trades}\nWinning Trades: {m.winning_trades} ({m.win_rate*100:.1f}%)\n"
                f"Losing Trades: {m.losing_trades}\nProfit Factor: {m.profit_factor:.2f}\nExpectancy: €{m.expectancy:.2f}\n\n"
                f"Average Win: €{m.avg_win:.2f}\nAverage Loss: €{m.avg_loss:.2f}\n"
                f"Largest Win: €{m.largest_win:.2f}\nLargest Loss: €{m.largest_loss:.2f}\n\n"
                f"{'─'*70}\nRISK METRICS\n{'─'*70}\n\n"
                f"Sharpe Ratio: {m.sharpe_ratio:.2f}\nSortino Ratio: {m.sortino_ratio:.2f}\n"
                f"Max Drawdown: {m.max_drawdown_pct:.2f}%\nAvg R-Multiple: {m.avg_r_multiple:.2f}\n\n"
                f"Max Consecutive Wins: {m.max_consecutive_wins}\nMax Consecutive Losses: {m.max_consecutive_losses}\n")
        self.parent.results_text.setPlainText(text)

        # Display results in embedded chart tab
        self.parent.backtest_chart.load_backtest_result(result)

        # Open/update chart POPUP window
        self._open_chart_popup(result)

        # Switch to results tab
        self.parent.tabs.setCurrentIndex(1)

    def _open_chart_popup(self, result):
        """Open chart popup window with backtest results.

        Args:
            result: BacktestResult to display
        """
        # Get parent app to access chart_window_manager
        parent_app = self.parent.parent()
        if not hasattr(parent_app, 'backtest_chart_manager'):
            logger.warning("Parent app doesn't have backtest_chart_manager")
            return

        # Open or focus chart window for symbol
        chart_window = parent_app.backtest_chart_manager.open_or_focus_chart(result.symbol)

        # Load backtest result into chart
        chart_window.load_backtest_result(result)

        logger.info(f"Opened chart popup for {result.symbol} with backtest results")
