"""Strategy Evaluator - Walk-Forward Visualization.

Creates charts for walk-forward validation results:
- Rolling Sharpe ratio
- In-sample vs out-of-sample equity curves
- Drawdown comparison
- Performance metrics table
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from .evaluator_types import RobustnessReport, WalkForwardResult

logger = logging.getLogger(__name__)


class EvaluatorVisualization:
    """Helper for StrategyEvaluator visualization."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyEvaluator instance
        """
        self.parent = parent

    def create_walk_forward_charts(
        self,
        walk_forward_result: WalkForwardResult,
        robustness_report: RobustnessReport | None = None
    ) -> Figure:
        """Create comprehensive walk-forward validation charts.

        Args:
            walk_forward_result: Walk-forward analysis result
            robustness_report: Optional robustness validation report

        Returns:
            Matplotlib Figure with 4 subplots
        """
        fig = plt.figure(figsize=(14, 10))
        fig.suptitle(
            f"Walk-Forward Validation: {walk_forward_result.strategy_name}",
            fontsize=14,
            fontweight="bold"
        )

        # 2x2 grid
        ax1 = plt.subplot(2, 2, 1)  # Rolling Sharpe
        ax2 = plt.subplot(2, 2, 2)  # Equity Curves
        ax3 = plt.subplot(2, 2, 3)  # Drawdown Comparison
        ax4 = plt.subplot(2, 2, 4)  # Metrics Table

        # Chart 1: Rolling Sharpe Ratio
        self._plot_rolling_sharpe(ax1, walk_forward_result)

        # Chart 2: Equity Curves (IS vs OOS)
        self._plot_equity_curves(ax2, walk_forward_result)

        # Chart 3: Drawdown Comparison
        self._plot_drawdown_comparison(ax3, walk_forward_result)

        # Chart 4: Metrics Table
        self._plot_metrics_table(ax4, walk_forward_result, robustness_report)

        plt.tight_layout(rect=[0, 0, 1, 0.97])
        return fig

    def _plot_rolling_sharpe(self, ax, result: WalkForwardResult) -> None:
        """Plot rolling Sharpe ratio over time."""
        if not result.rolling_sharpe:
            ax.text(0.5, 0.5, "No Sharpe data", ha="center", va="center")
            ax.set_title("Rolling Sharpe Ratio")
            return

        periods = range(1, len(result.rolling_sharpe) + 1)
        sharpe_values = result.rolling_sharpe

        ax.plot(periods, sharpe_values, marker="o", linewidth=2, markersize=6)
        ax.axhline(y=1.0, color="g", linestyle="--", alpha=0.5, label="Target (1.0)")
        ax.axhline(y=0, color="k", linestyle="-", alpha=0.3)

        ax.set_title("Rolling Sharpe Ratio (Out-of-Sample)")
        ax.set_xlabel("Period")
        ax.set_ylabel("Sharpe Ratio")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Color positive/negative
        for i, val in enumerate(sharpe_values):
            color = "green" if val >= 1.0 else "orange" if val >= 0 else "red"
            ax.plot(i + 1, val, marker="o", color=color, markersize=6)

    def _plot_equity_curves(self, ax, result: WalkForwardResult) -> None:
        """Plot in-sample vs out-of-sample equity curves."""
        if not result.period_results:
            ax.text(0.5, 0.5, "No period data", ha="center", va="center")
            ax.set_title("Equity Curves")
            return

        # Build cumulative equity
        is_equity = [100.0]  # Start at 100%
        oos_equity = [100.0]

        for is_metrics, oos_metrics in result.period_results:
            # Add net profit % to current equity
            is_equity.append(is_equity[-1] * (1 + is_metrics.net_profit / 10000.0))
            oos_equity.append(oos_equity[-1] * (1 + oos_metrics.net_profit / 10000.0))

        periods = range(len(is_equity))

        ax.plot(periods, is_equity, label="In-Sample", linewidth=2, color="blue")
        ax.plot(periods, oos_equity, label="Out-of-Sample", linewidth=2, color="orange")
        ax.axhline(y=100, color="k", linestyle="--", alpha=0.3)

        ax.set_title("Equity Curves (Cumulative)")
        ax.set_xlabel("Period")
        ax.set_ylabel("Equity (%)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Fill area between curves to show degradation
        ax.fill_between(periods, is_equity, oos_equity, alpha=0.2, color="gray")

    def _plot_drawdown_comparison(self, ax, result: WalkForwardResult) -> None:
        """Plot rolling drawdown comparison."""
        if not result.rolling_drawdown:
            ax.text(0.5, 0.5, "No drawdown data", ha="center", va="center")
            ax.set_title("Drawdown Comparison")
            return

        periods = range(1, len(result.rolling_drawdown) + 1)
        drawdowns = [-d for d in result.rolling_drawdown]  # Negative for chart

        ax.fill_between(periods, drawdowns, 0, alpha=0.3, color="red")
        ax.plot(periods, drawdowns, linewidth=2, color="darkred")

        # Threshold lines
        ax.axhline(y=-20, color="orange", linestyle="--", alpha=0.5, label="Warning (-20%)")
        ax.axhline(y=-30, color="red", linestyle="--", alpha=0.5, label="Critical (-30%)")

        ax.set_title("Rolling Maximum Drawdown")
        ax.set_xlabel("Period")
        ax.set_ylabel("Drawdown (%)")
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_metrics_table(
        self,
        ax,
        result: WalkForwardResult,
        robustness_report: RobustnessReport | None
    ) -> None:
        """Plot performance metrics table."""
        ax.axis("off")

        # Prepare table data
        is_m = result.in_sample_metrics
        oos_m = result.out_of_sample_metrics

        data = [
            ["Metric", "In-Sample", "Out-of-Sample"],
            ["Trades", f"{is_m.total_trades}", f"{oos_m.total_trades}"],
            ["Win Rate", f"{is_m.win_rate:.1%}", f"{oos_m.win_rate:.1%}"],
            ["Profit Factor", f"{is_m.profit_factor:.2f}", f"{oos_m.profit_factor:.2f}"],
            ["Sharpe Ratio",
             f"{is_m.sharpe_ratio:.2f}" if is_m.sharpe_ratio else "N/A",
             f"{oos_m.sharpe_ratio:.2f}" if oos_m.sharpe_ratio else "N/A"],
            ["Max DD %", f"{abs(is_m.max_drawdown_pct):.1f}%", f"{abs(oos_m.max_drawdown_pct):.1f}%"],
        ]

        # Color cells based on robustness
        cell_colors = [["lightgray"] * 3]  # Header
        for _ in range(len(data) - 1):
            cell_colors.append(["white", "lightblue", "lightyellow"])

        if robustness_report:
            # Update colors based on pass/fail
            if not robustness_report.min_trades_met:
                cell_colors[1] = ["white", "lightcoral", "lightcoral"]

            if not robustness_report.max_drawdown_met:
                cell_colors[5] = ["white", "lightcoral", "lightcoral"]

            if not robustness_report.min_sharpe_met:
                cell_colors[4] = ["white", "lightcoral", "lightcoral"]

        table = ax.table(
            cellText=data,
            cellColours=cell_colors,
            cellLoc="center",
            loc="center",
            bbox=[0, 0, 1, 1]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)

        ax.set_title("Performance Metrics", fontweight="bold", pad=10)

    def save_chart_to_bytes(self, fig: Figure) -> bytes:
        """Save matplotlib figure to bytes (PNG format).

        Args:
            fig: Matplotlib Figure

        Returns:
            PNG image as bytes
        """
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        return buffer.read()

    def save_chart_to_file(self, fig: Figure, path: str) -> None:
        """Save matplotlib figure to file.

        Args:
            fig: Matplotlib Figure
            path: File path (e.g., "walk_forward.png")
        """
        fig.savefig(path, dpi=150, bbox_inches="tight")
        logger.info(f"Walk-forward chart saved to {path}")
