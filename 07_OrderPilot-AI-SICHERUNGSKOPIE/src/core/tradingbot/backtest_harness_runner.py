"""Backtest Harness Runner - Main Backtest Loop.

Refactored from backtest_harness.py.

Contains:
- run: Main backtest loop with bar-by-bar simulation, metrics calculation, and result saving
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from .backtest_types import BacktestResult, BacktestState

if TYPE_CHECKING:
    from .backtest_harness import BacktestHarness

logger = logging.getLogger(__name__)


class BacktestHarnessRunner:
    """Helper for running the main backtest loop."""

    def __init__(self, parent: "BacktestHarness"):
        self.parent = parent

    def run(self) -> BacktestResult:
        """Run the backtest.

        Returns:
            BacktestResult with all metrics and trades
        """
        start_time = datetime.utcnow()

        # Initialize
        self.parent._init_bot_components()
        if self.parent._data is None:
            self.parent._data_loader.load_data()

        # Reset state
        self.parent._state = BacktestState(capital=self.parent.backtest_config.initial_capital)

        # Run simulation
        total_bars = len(self.parent._data)
        logger.info(f"Starting backtest: {total_bars} bars")

        for bar_idx, (timestamp, row) in enumerate(self.parent._data.iterrows()):
            self.parent._state.bar_index = bar_idx
            self.parent._state.current_time = timestamp
            self.parent._state.current_bar = {
                "timestamp": timestamp,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row.get("volume", 0),
            }

            # Skip warmup period
            if bar_idx < self.parent.backtest_config.warmup_bars:
                continue

            # Process bar
            self.parent._bar_processor.process_bar(bar_idx)

            # Record equity
            equity = self.parent._helpers.calculate_equity()
            self.parent._state.equity_curve.append((timestamp, equity))

        # Close any open position at end
        if self.parent._state.position and self.parent._state.position.is_open:
            self.parent._execution.close_position("END_OF_BACKTEST")

        # Calculate metrics
        run_time = (datetime.utcnow() - start_time).total_seconds()
        metrics = self.parent._helpers.calculate_metrics()

        result = BacktestResult(
            config=self.parent.backtest_config,
            metrics=metrics,
            trades=self.parent._state.trades,
            equity_curve=self.parent._state.equity_curve,
            run_time_seconds=run_time,
            total_bars=total_bars,
            seed_used=self.parent._seed,
            total_trades=len(self.parent._state.trades),
            winning_trades=sum(1 for t in self.parent._state.trades if t.pnl > 0),
            losing_trades=sum(1 for t in self.parent._state.trades if t.pnl <= 0),
            total_pnl=sum(t.pnl for t in self.parent._state.trades),
            total_fees=sum(t.fees for t in self.parent._state.trades),
            max_drawdown_pct=metrics.max_drawdown_pct,
            final_capital=self.parent._helpers.calculate_equity()
        )

        logger.info(
            f"Backtest complete: {result.total_trades} trades, "
            f"PnL=${result.total_pnl:.2f}, "
            f"WinRate={metrics.win_rate:.1%}, "
            f"PF={metrics.profit_factor:.2f}"
        )

        # Save if configured
        if self.parent.backtest_config.output_dir:
            output_path = (
                self.parent.backtest_config.output_dir /
                f"backtest_{self.parent.backtest_config.symbol}_{self.parent._seed}.json"
            )
            result.save(output_path)

        return result
