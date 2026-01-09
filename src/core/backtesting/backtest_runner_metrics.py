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

        # Basis-Statistiken
        total_trades = len(trades)
        winners = [t for t in trades if t.realized_pnl > 0]
        losers = [t for t in trades if t.realized_pnl <= 0]

        winning_trades = len(winners)
        losing_trades = len(losers)

        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # P&L Statistiken
        gross_profit = sum(t.realized_pnl for t in winners)
        gross_loss = abs(sum(t.realized_pnl for t in losers))

        profit_factor = (
            gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0
        )

        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = -gross_loss / losing_trades if losing_trades > 0 else 0

        # Expectancy = (Win% * AvgWin) - (Loss% * AvgLoss)
        loss_rate = losing_trades / total_trades if total_trades > 0 else 0
        expectancy = (win_rate * avg_win) + (loss_rate * avg_loss)  # avg_loss ist negativ

        # R-Multiples
        r_multiples = [t.r_multiple for t in trades if t.r_multiple is not None]
        avg_r = np.mean(r_multiples) if r_multiples else None
        best_r = max(r_multiples) if r_multiples else None
        worst_r = min(r_multiples) if r_multiples else None

        # Drawdown
        max_dd_pct, max_dd_duration = self._calculate_drawdown(equity_curve)

        # Streaks
        max_wins, max_losses = self._calculate_streaks(trades)

        # Returns
        total_return = ((self.parent.state.equity / self.parent.config.initial_capital) - 1) * 100

        # Sharpe (vereinfacht)
        sharpe = self._calculate_sharpe(equity_curve)

        # Trade Duration
        durations = [t.duration for t in trades if t.duration is not None]
        avg_duration_min = np.mean(durations) / 60 if durations else None

        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            expectancy=expectancy,
            max_drawdown_pct=max_dd_pct,
            max_drawdown_duration_days=max_dd_duration,
            sharpe_ratio=sharpe,
            avg_r_multiple=avg_r,
            best_r_multiple=best_r,
            worst_r_multiple=worst_r,
            avg_win=avg_win,
            avg_loss=avg_loss,
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
