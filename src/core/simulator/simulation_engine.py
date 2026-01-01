"""Strategy Simulation Engine.

Runs backtests with configurable parameters against provided chart data.
This is a simplified simulator focused on the 5 base strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import numpy as np
import pandas as pd

from .strategy_params import StrategyName
from .simulation_signals import StrategySignalGenerator
from .result_types import SimulationResult, TradeRecord


@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""

    strategy_name: StrategyName
    parameters: dict[str, Any]
    initial_capital: float = 1000.0  # 1000€ Startkapital
    position_size_pct: float = 1.0   # 100% = voller Einsatz pro Trade (1000€)
    slippage_pct: float = 0.001  # 0.1% slippage
    commission_pct: float = 0.001  # 0.1% commission
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.05  # 5% take profit


class StrategySimulator:
    """Simulator for running strategies with configurable parameters.

    This class provides a simplified backtesting engine that:
    - Uses existing chart data (no data fetching)
    - Supports configurable strategy parameters
    - Calculates comprehensive performance metrics
    """

    def __init__(self, data: pd.DataFrame, symbol: str):
        """Initialize simulator with chart data.

        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume
                  Index should be DatetimeIndex or have a 'timestamp' column
            symbol: Trading symbol
        """
        self.data = self._prepare_data(data)
        self.symbol = symbol
        self._signal_generator = StrategySignalGenerator(self.data)
        self._trades: list[TradeRecord] = []
        self._equity_curve: list[tuple[datetime, float]] = []

    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data."""
        df = data.copy()

        # Ensure we have required columns
        required = ["open", "high", "low", "close", "volume"]
        # Try lowercase first
        if not all(c in df.columns for c in required):
            # Try uppercase
            for col in required:
                if col.upper() in df.columns:
                    df[col] = df[col.upper()]

        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if "timestamp" in df.columns:
                df.set_index("timestamp", inplace=True)
            elif "date" in df.columns:
                df.set_index("date", inplace=True)
            else:
                df.index = pd.to_datetime(df.index)

        return df.sort_index()

    async def run_simulation(
        self,
        strategy_name: StrategyName | str,
        parameters: dict[str, Any],
        initial_capital: float = 1000.0,  # 1000€ Startkapital
        position_size_pct: float = 1.0,   # 100% = voller Einsatz pro Trade
        slippage_pct: float = 0.001,
        commission_pct: float = 0.001,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.05,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> SimulationResult:
        """Run a single simulation with given parameters.

        Args:
            strategy_name: Strategy to simulate
            parameters: Strategy parameters
            initial_capital: Starting capital
            position_size_pct: Position size as percentage of capital
            slippage_pct: Slippage percentage
            commission_pct: Commission percentage
            stop_loss_pct: Default stop loss percentage
            take_profit_pct: Default take profit percentage
            progress_callback: Optional callback(current_bar, total_bars)

        Returns:
            SimulationResult with trades and metrics
        """
        if isinstance(strategy_name, str):
            strategy_name = StrategyName(strategy_name)

        config = SimulationConfig(
            strategy_name=strategy_name,
            parameters=parameters,
            initial_capital=initial_capital,
            position_size_pct=position_size_pct,
            slippage_pct=slippage_pct,
            commission_pct=commission_pct,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
        )

        # Calculate indicators and signals
        signals = self._generate_signals(strategy_name, parameters)

        # Simulate trades
        trades = self._simulate_trades(signals, config)

        # Calculate metrics
        result = self._calculate_result(
            strategy_name=strategy_name.value,
            parameters=parameters,
            trades=trades,
            initial_capital=initial_capital,
        )

        return result

    def _generate_signals(
        self,
        strategy_name: StrategyName,
        parameters: dict[str, Any],
    ) -> pd.DataFrame:
        """Generate trading signals based on strategy logic."""
        return self._signal_generator.generate(strategy_name, parameters)

    def _breakout_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._breakout_signals(df, params)

    def _momentum_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._momentum_signals(df, params)

    def _mean_reversion_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._mean_reversion_signals(df, params)

    def _trend_following_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._trend_following_signals(df, params)

    def _scalping_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._scalping_signals(df, params)

    def _bollinger_squeeze_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._bollinger_squeeze_signals(df, params)

    def _trend_pullback_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._trend_pullback_signals(df, params)

    def _opening_range_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._opening_range_signals(df, params)

    def _regime_hybrid_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._regime_hybrid_signals(df, params)

    def _simulate_trades(
        self,
        signals_df: pd.DataFrame,
        config: SimulationConfig,
    ) -> list[TradeRecord]:
        """Simulate trades based on signals."""
        trades: list[TradeRecord] = []
        position: dict | None = None
        capital = config.initial_capital

        for i, (timestamp, row) in enumerate(signals_df.iterrows()):
            signal = row["signal"]
            price = row["close"]

            # Check for exit conditions if in position
            if position is not None:
                exit_info = self._check_exit_conditions(row, signal, position, config)
                if exit_info:
                    trade, capital = self._close_position(
                        position,
                        timestamp,
                        exit_info,
                        config,
                        capital,
                    )
                    trades.append(trade)
                    position = None

            # Check for entry signal
            if position is None and signal == 1:
                position, capital = self._open_position(timestamp, price, config, capital)

        # Close any open position at end
        if position is not None:
            trade = self._close_position_end(signals_df, position, config)
            trades.append(trade)

        return trades

    def _check_exit_conditions(
        self,
        row: pd.Series,
        signal: int,
        position: dict,
        config: SimulationConfig,
    ) -> dict | None:
        if row["low"] <= position["stop_loss"]:
            return {"price": position["stop_loss"], "reason": "STOP_LOSS"}
        if row["high"] >= position["take_profit"]:
            return {"price": position["take_profit"], "reason": "TAKE_PROFIT"}
        if signal == -1:
            return {"price": row["close"] * (1 - config.slippage_pct), "reason": "SIGNAL"}
        return None

    def _close_position(
        self,
        position: dict,
        timestamp,
        exit_info: dict,
        config: SimulationConfig,
        capital: float,
    ) -> tuple[TradeRecord, float]:
        exit_price = exit_info["price"]
        pnl = (exit_price - position["entry_price"]) * position["size"]
        commission = exit_price * position["size"] * config.commission_pct
        pnl -= commission
        trade = TradeRecord(
            entry_time=position["entry_time"],
            entry_price=position["entry_price"],
            exit_time=timestamp,
            exit_price=exit_price,
            side="long",
            size=position["size"],
            pnl=pnl,
            pnl_pct=pnl / (position["entry_price"] * position["size"]),
            exit_reason=exit_info["reason"],
            stop_loss=position["stop_loss"],
            take_profit=position["take_profit"],
            commission=commission + position["commission"],
        )
        return trade, capital + pnl

    def _open_position(
        self,
        timestamp,
        price: float,
        config: SimulationConfig,
        capital: float,
    ) -> tuple[dict, float]:
        entry_price = price * (1 + config.slippage_pct)
        position_value = capital * config.position_size_pct
        size = position_value / entry_price
        commission = position_value * config.commission_pct
        position = {
            "entry_time": timestamp,
            "entry_price": entry_price,
            "size": size,
            "stop_loss": entry_price * (1 - config.stop_loss_pct),
            "take_profit": entry_price * (1 + config.take_profit_pct),
            "commission": commission,
        }
        return position, capital - commission

    def _close_position_end(
        self,
        signals_df: pd.DataFrame,
        position: dict,
        config: SimulationConfig,
    ) -> TradeRecord:
        last_row = signals_df.iloc[-1]
        exit_price = last_row["close"]
        pnl = (exit_price - position["entry_price"]) * position["size"]
        commission = exit_price * position["size"] * config.commission_pct
        pnl -= commission
        return TradeRecord(
            entry_time=position["entry_time"],
            entry_price=position["entry_price"],
            exit_time=signals_df.index[-1],
            exit_price=exit_price,
            side="long",
            size=position["size"],
            pnl=pnl,
            pnl_pct=pnl / (position["entry_price"] * position["size"]),
            exit_reason="END_OF_DATA",
            stop_loss=position["stop_loss"],
            take_profit=position["take_profit"],
            commission=commission + position["commission"],
        )

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

    # Helper methods for indicator calculations
    def _true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range."""
        return self._signal_generator._true_range(df)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        return self._signal_generator._calculate_rsi(prices, period)

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        return self._signal_generator._calculate_obv(df)

    def get_entry_exit_points(
        self, result: SimulationResult
    ) -> list[dict[str, Any]]:
        """Extract entry/exit points for chart visualization.

        Returns list of dicts with timestamp, price, type, and metadata.
        """
        points = []

        for trade in result.trades:
            # Entry point
            points.append(
                {
                    "timestamp": trade.entry_time,
                    "price": trade.entry_price,
                    "type": "entry",
                    "side": trade.side,
                    "stop_loss": trade.stop_loss,
                    "take_profit": trade.take_profit,
                }
            )
            # Exit point
            points.append(
                {
                    "timestamp": trade.exit_time,
                    "price": trade.exit_price,
                    "type": "exit",
                    "side": trade.side,
                    "reason": trade.exit_reason,
                    "pnl": trade.pnl,
                }
            )

        return points
