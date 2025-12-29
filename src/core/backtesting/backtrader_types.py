"""Backtrader Types and Configuration.

Contains configuration dataclasses for backtesting.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from src.core.market_data.history_provider import Timeframe
from src.core.strategy.engine import StrategyConfig


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    start_date: datetime
    end_date: datetime
    initial_cash: Decimal = Decimal('10000')
    commission: float = 0.001  # 0.1% commission
    slippage: float = 0.0005  # 0.05% slippage
    timeframe: Timeframe = Timeframe.MINUTE_1
    symbols: list[str] = None
    strategies: list[StrategyConfig] = None
    benchmark: str | None = "SPY"
    optimize_params: dict[str, list[Any]] | None = None

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []
        if self.strategies is None:
            self.strategies = []


@dataclass
class BacktestResultLegacy:
    """Legacy results from backtesting (deprecated, use BacktestResult from models).

    Kept for backward compatibility only. New code should use
    src.core.models.backtest_models.BacktestResult instead.
    """
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_return: float
    best_trade: float
    worst_trade: float
    final_value: Decimal
    trades: list[dict[str, Any]]
    equity_curve: pd.DataFrame
    benchmark_return: float | None = None
    metadata: dict[str, Any] = None
