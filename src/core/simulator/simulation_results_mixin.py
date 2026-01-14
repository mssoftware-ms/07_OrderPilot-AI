from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np

class SimulationResultsMixin:
    """Result calculation and performance metrics"""

    def _calculate_result(
        self,
        strategy_name: str,
        parameters: dict[str, Any],
        trades: list[TradeRecord],
        initial_capital: float,
    ) -> SimulationResult:
        """Calculate simulation result from trades."""
        if not trades:
            return self._empty_result(strategy_name, parameters, initial_capital)

        metrics = self._calculate_trade_metrics(trades, initial_capital)

        return SimulationResult(
            strategy_name=strategy_name,
            parameters=parameters,
            symbol=self.symbol,
            trades=trades,
            total_pnl=metrics["total_pnl"],
            total_pnl_pct=(metrics["total_pnl"] / initial_capital) * 100,
            win_rate=metrics["win_rate"],
            profit_factor=metrics["profit_factor"],
            max_drawdown_pct=metrics["max_drawdown_pct"],
            sharpe_ratio=metrics["sharpe_ratio"],
            sortino_ratio=metrics["sortino_ratio"],
            total_trades=len(trades),
            winning_trades=metrics["total_wins"],
            losing_trades=metrics["total_losses"],
            avg_win=metrics["avg_win"],
            avg_loss=metrics["avg_loss"],
            largest_win=metrics["largest_win"],
            largest_loss=metrics["largest_loss"],
            avg_trade_duration_seconds=metrics["avg_duration"],
            max_consecutive_wins=metrics["max_cons_wins"],
            max_consecutive_losses=metrics["max_cons_losses"],
            initial_capital=initial_capital,
            final_capital=metrics["final_capital"],
            data_start=self.data.index[0],
            data_end=self.data.index[-1],
            bars_processed=len(self.data),
        )

    def _empty_result(
        self,
        strategy_name: str,
        parameters: dict[str, Any],
        initial_capital: float,
    ) -> SimulationResult:
        return SimulationResult(
            strategy_name=strategy_name,
            parameters=parameters,
            symbol=self.symbol,
            trades=[],
            total_pnl=0.0,
            total_pnl_pct=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=None,
            sortino_ratio=None,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            avg_win=0.0,
            avg_loss=0.0,
            largest_win=0.0,
            largest_loss=0.0,
            avg_trade_duration_seconds=0.0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
            initial_capital=initial_capital,
            final_capital=initial_capital,
            data_start=self.data.index[0],
            data_end=self.data.index[-1],
            bars_processed=len(self.data),
        )

    def _calculate_trade_metrics(
        self,
        trades: list[TradeRecord],
        initial_capital: float,
    ) -> dict[str, Any]:
        total_pnl = sum(t.pnl for t in trades)
        winning_trades = [t for t in trades if t.is_winner]
        losing_trades = [t for t in trades if not t.is_winner]

        total_wins = len(winning_trades)
        total_losses = len(losing_trades)
        win_rate = total_wins / len(trades) if trades else 0.0

        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        profit_factor = profit_factor if profit_factor != float("inf") else 99.99

        avg_win = gross_profit / total_wins if total_wins > 0 else 0.0
        avg_loss = gross_loss / total_losses if total_losses > 0 else 0.0

        largest_win = max((t.pnl for t in winning_trades), default=0.0)
        largest_loss = min((t.pnl for t in losing_trades), default=0.0)

        max_dd = self._max_drawdown_pct(trades, initial_capital)
        final_capital = initial_capital + total_pnl

        max_cons_wins, max_cons_losses = self._max_consecutive_runs(trades)
        avg_duration = self._avg_trade_duration(trades)
        sharpe, sortino = self._risk_ratios(trades)

        return {
            "total_pnl": total_pnl,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_dd,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "avg_duration": avg_duration,
            "max_cons_wins": max_cons_wins,
            "max_cons_losses": max_cons_losses,
            "final_capital": final_capital,
        }

    def _max_drawdown_pct(self, trades: list[TradeRecord], initial_capital: float) -> float:
        equity = initial_capital
        peak = equity
        max_dd = 0.0
        for trade in trades:
            equity += trade.pnl
            peak = max(peak, equity)
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)
        return max_dd * 100

    def _max_consecutive_runs(self, trades: list[TradeRecord]) -> tuple[int, int]:
        max_cons_wins = max_cons_losses = 0
        current_wins = current_losses = 0
        for trade in trades:
            if trade.is_winner:
                current_wins += 1
                current_losses = 0
                max_cons_wins = max(max_cons_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_cons_losses = max(max_cons_losses, current_losses)
        return max_cons_wins, max_cons_losses

    def _avg_trade_duration(self, trades: list[TradeRecord]) -> float:
        durations = [t.duration_seconds for t in trades]
        return np.mean(durations) if durations else 0.0

    def _risk_ratios(self, trades: list[TradeRecord]) -> tuple[float | None, float | None]:
        returns = [t.pnl_pct for t in trades]
        if len(returns) <= 1:
            return None, None
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        neg_returns = [r for r in returns if r < 0]
        downside_std = np.std(neg_returns) if neg_returns else 0.0
        sharpe = (mean_return * 252) / (std_return * np.sqrt(252)) if std_return > 0 else None
        sortino = (mean_return * 252) / (downside_std * np.sqrt(252)) if downside_std > 0 else None
        return sharpe, sortino


