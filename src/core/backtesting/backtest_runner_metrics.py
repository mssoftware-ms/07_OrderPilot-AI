"""Backtest Runner Metrics - Metrics Calculation.

Refactored from 832 LOC monolith using composition pattern.

Module 5/5 of backtest_runner.py split.

Contains:
- Result calculation (_calculate_result)
- Performance metrics (_calculate_metrics)
- Drawdown calculation (_calculate_drawdown)
- Streaks calculation (_calculate_streaks)
- Sharpe ratio calculation (_calculate_sharpe)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.core.models.backtest_models import BacktestMetrics, BacktestResult, Bar, EquityPoint, Trade

logger = logging.getLogger(__name__)


class BacktestRunnerMetrics:
    """Helper für Metrics Calculation."""

    def __init__(self, parent):
        """
        Args:
            parent: BacktestRunner Instanz
        """
        self.parent = parent

    def _calculate_result(self) -> "BacktestResult":
        """Berechnet das finale BacktestResult."""
        from src.core.models.backtest_models import BacktestResult, Bar

        trades = self.parent.state.closed_trades
        equity_curve = self.parent.state.equity_curve

        # Metriken berechnen
        metrics = self._calculate_metrics(trades, equity_curve)

        # Bars für Result (vereinfacht - nur Timestamps)
        bars = []
        if self.parent.replay_provider.data is not None:
            for _, row in self.parent.replay_provider.data.iloc[::60].iterrows():  # Jede Stunde
                # Timestamp sicher zu int konvertieren (kann pd.Timestamp oder int sein)
                ts = row["timestamp"]
                if hasattr(ts, 'timestamp'):  # pandas Timestamp
                    ts_ms = int(ts.timestamp() * 1000)
                else:
                    ts_ms = int(ts)
                bars.append(
                    Bar(
                        time=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                        symbol=self.parent.config.symbol,
                    )
                )

        return BacktestResult(
            symbol=self.parent.config.symbol,
            timeframe=self.parent.config.base_timeframe,
            mode="backtest",
            start=self.parent.config.start_date,
            end=self.parent.config.end_date,
            initial_capital=self.parent.config.initial_capital,
            final_capital=self.parent.state.equity,
            bars=bars,
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
            strategy_name=self.parent.config.strategy_preset,
            strategy_params=self.parent.config.parameter_overrides,
        )

    def _calculate_metrics(
        self,
        trades: list["Trade"],
        equity_curve: list["EquityPoint"],
    ) -> "BacktestMetrics":
        """Berechnet Performance-Metriken."""
        from src.core.models.backtest_models import BacktestMetrics

        if not trades:
            return BacktestMetrics()

        # Calculate basic trade statistics
        basic_stats = self._calculate_basic_trade_stats(trades)

        # Calculate P&L statistics
        pnl_stats = self._calculate_pnl_stats(
            basic_stats["winners"], basic_stats["losers"], basic_stats["total_trades"]
        )

        # Calculate R-multiple statistics
        r_stats = self._calculate_r_multiple_stats(trades)

        # Calculate drawdown and streaks
        max_dd_pct, max_dd_duration = self._calculate_drawdown(equity_curve)
        max_wins, max_losses = self._calculate_streaks(trades)

        # Calculate returns and duration
        total_return = self._calculate_total_return()
        sharpe = self._calculate_sharpe(equity_curve)
        avg_duration_min = self._calculate_avg_duration(trades)

        # Build and return metrics object
        return self._build_metrics_object(
            basic_stats=basic_stats,
            pnl_stats=pnl_stats,
            r_stats=r_stats,
            max_dd_pct=max_dd_pct,
            max_dd_duration=max_dd_duration,
            total_return=total_return,
            sharpe=sharpe,
            avg_duration_min=avg_duration_min,
            max_wins=max_wins,
            max_losses=max_losses,
        )

    def _calculate_basic_trade_stats(self, trades: list["Trade"]) -> dict:
        """Calculate basic trade statistics (winners, losers, win rate).

        Args:
            trades: List of trades.

        Returns:
            Dictionary with total_trades, winners, losers, winning_trades, losing_trades, win_rate.
        """
        total_trades = len(trades)
        winners = [t for t in trades if t.realized_pnl > 0]
        losers = [t for t in trades if t.realized_pnl <= 0]

        winning_trades = len(winners)
        losing_trades = len(losers)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        return {
            "total_trades": total_trades,
            "winners": winners,
            "losers": losers,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
        }

    def _calculate_pnl_stats(
        self, winners: list["Trade"], losers: list["Trade"], total_trades: int
    ) -> dict:
        """Calculate P&L statistics (profit, loss, expectancy, profit factor).

        Args:
            winners: List of winning trades.
            losers: List of losing trades.
            total_trades: Total number of trades.

        Returns:
            Dictionary with profit_factor, expectancy, avg_win, avg_loss.
        """
        winning_trades = len(winners)
        losing_trades = len(losers)

        gross_profit = sum(t.realized_pnl for t in winners)
        gross_loss = abs(sum(t.realized_pnl for t in losers))

        profit_factor = self._calculate_profit_factor(gross_profit, gross_loss)

        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = -gross_loss / losing_trades if losing_trades > 0 else 0

        # Expectancy = (Win% * AvgWin) + (Loss% * AvgLoss)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        loss_rate = losing_trades / total_trades if total_trades > 0 else 0
        expectancy = (win_rate * avg_win) + (loss_rate * avg_loss)

        return {
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
        }

    def _calculate_profit_factor(self, gross_profit: float, gross_loss: float) -> float:
        """Calculate profit factor with proper handling of edge cases.

        Args:
            gross_profit: Total profit from winning trades.
            gross_loss: Total loss from losing trades (absolute value).

        Returns:
            Profit factor (gross_profit / gross_loss).
        """
        if gross_loss > 0:
            return gross_profit / gross_loss
        elif gross_profit > 0:
            return float("inf")
        else:
            return 0.0

    def _calculate_r_multiple_stats(self, trades: list["Trade"]) -> dict:
        """Calculate R-multiple statistics (avg, best, worst).

        Args:
            trades: List of trades.

        Returns:
            Dictionary with avg_r, best_r, worst_r.
        """
        r_multiples = [t.r_multiple for t in trades if t.r_multiple is not None]

        return {
            "avg_r": np.mean(r_multiples) if r_multiples else None,
            "best_r": max(r_multiples) if r_multiples else None,
            "worst_r": min(r_multiples) if r_multiples else None,
        }

    def _calculate_total_return(self) -> float:
        """Calculate total return percentage.

        Returns:
            Total return as percentage.
        """
        return ((self.parent.state.equity / self.parent.config.initial_capital) - 1) * 100

    def _calculate_avg_duration(self, trades: list["Trade"]) -> float | None:
        """Calculate average trade duration in minutes.

        Args:
            trades: List of trades.

        Returns:
            Average duration in minutes, or None if no duration data.
        """
        durations = [t.duration for t in trades if t.duration is not None]
        return np.mean(durations) / 60 if durations else None

    def _build_metrics_object(
        self,
        basic_stats: dict,
        pnl_stats: dict,
        r_stats: dict,
        max_dd_pct: float,
        max_dd_duration: float | None,
        total_return: float,
        sharpe: float | None,
        avg_duration_min: float | None,
        max_wins: int,
        max_losses: int,
    ) -> "BacktestMetrics":
        """Build BacktestMetrics object from calculated statistics.

        Args:
            basic_stats: Basic trade statistics dictionary.
            pnl_stats: P&L statistics dictionary.
            r_stats: R-multiple statistics dictionary.
            max_dd_pct: Maximum drawdown percentage.
            max_dd_duration: Maximum drawdown duration in days.
            total_return: Total return percentage.
            sharpe: Sharpe ratio.
            avg_duration_min: Average trade duration in minutes.
            max_wins: Maximum consecutive wins.
            max_losses: Maximum consecutive losses.

        Returns:
            BacktestMetrics object with all calculated metrics.
        """
        from src.core.models.backtest_models import BacktestMetrics

        winners = basic_stats["winners"]
        losers = basic_stats["losers"]

        return BacktestMetrics(
            total_trades=basic_stats["total_trades"],
            winning_trades=basic_stats["winning_trades"],
            losing_trades=basic_stats["losing_trades"],
            win_rate=basic_stats["win_rate"],
            profit_factor=pnl_stats["profit_factor"],
            expectancy=pnl_stats["expectancy"],
            max_drawdown_pct=max_dd_pct,
            max_drawdown_duration_days=max_dd_duration,
            sharpe_ratio=sharpe,
            avg_r_multiple=r_stats["avg_r"],
            best_r_multiple=r_stats["best_r"],
            worst_r_multiple=r_stats["worst_r"],
            avg_win=pnl_stats["avg_win"],
            avg_loss=pnl_stats["avg_loss"],
            largest_win=max(t.realized_pnl for t in winners) if winners else 0,
            largest_loss=min(t.realized_pnl for t in losers) if losers else 0,
            total_return_pct=total_return,
            avg_trade_duration_minutes=avg_duration_min,
            max_consecutive_wins=max_wins,
            max_consecutive_losses=max_losses,
        )

    def _calculate_drawdown(self, equity_curve: list["EquityPoint"]) -> tuple[float, float | None]:
        """Berechnet Max Drawdown."""
        if len(equity_curve) < 2:
            return 0.0, None

        equities = [e.equity for e in equity_curve]
        times = [e.time for e in equity_curve]

        peak = equities[0]
        max_dd = 0.0
        dd_start = times[0]
        max_dd_duration = 0.0

        for i, eq in enumerate(equities):
            if eq > peak:
                peak = eq
                dd_start = times[i]

            dd = (peak - eq) / peak * 100 if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                duration = (times[i] - dd_start).total_seconds() / 86400
                max_dd_duration = max(max_dd_duration, duration)

        return max_dd, max_dd_duration if max_dd_duration > 0 else None

    def _calculate_streaks(self, trades: list["Trade"]) -> tuple[int, int]:
        """Berechnet längste Win/Loss Streaks."""
        if not trades:
            return 0, 0

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.realized_pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    def _calculate_sharpe(
        self, equity_curve: list["EquityPoint"], risk_free_rate: float = 0.0
    ) -> float | None:
        """Berechnet Sharpe Ratio (annualisiert)."""
        if len(equity_curve) < 30:
            return None

        equities = [e.equity for e in equity_curve]
        returns = np.diff(equities) / equities[:-1]

        if len(returns) < 2:
            return None

        avg_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return None

        # Annualisieren (angenommen 1440 Punkte pro Tag bei 1m TF, aber wir samplen alle 15min)
        # Vereinfacht: 96 Punkte pro Tag
        annualized_factor = np.sqrt(96 * 365)

        sharpe = ((avg_return - risk_free_rate) / std_return) * annualized_factor

        return float(sharpe)
