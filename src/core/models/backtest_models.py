"""Backtest Data Models for OrderPilot-AI.

Central models for backtesting, trades, equity tracking, and result metrics.
These models provide a standardized interface for backtest results that can be
used for chart visualization, KI analysis, and result comparison.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field


class TradeSide(str, Enum):
    """Trade direction."""
    LONG = "long"
    SHORT = "short"


class Bar(BaseModel):
    """OHLCV bar data.

    Represents a single candlestick/bar with price and volume information.
    """
    time: datetime = Field(..., description="Bar timestamp")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: float | int = Field(..., description="Trading volume")
    symbol: str | None = Field(None, description="Trading symbol")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }


class Trade(BaseModel):
    """Represents a completed or active trade.

    Captures all relevant information about a trade including entry/exit,
    P&L, risk management levels, and reasoning.
    """
    id: str = Field(..., description="Unique trade identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: TradeSide = Field(..., description="Trade direction (long/short)")
    size: float = Field(..., gt=0, description="Position size")

    # Entry information
    entry_time: datetime = Field(..., description="Trade entry timestamp")
    entry_price: float = Field(..., gt=0, description="Entry price")
    entry_reason: str = Field(..., description="Why trade was entered")

    # Exit information (None if still open)
    exit_time: datetime | None = Field(None, description="Trade exit timestamp")
    exit_price: float | None = Field(None, description="Exit price")
    exit_reason: str = Field("", description="Why trade was exited")

    # Risk management
    stop_loss: float | None = Field(None, description="Stop loss price level")
    take_profit: float | None = Field(None, description="Take profit price level")

    # P&L metrics
    realized_pnl: float = Field(0.0, description="Realized profit/loss in currency")
    realized_pnl_pct: float = Field(0.0, description="Realized P&L as percentage")

    # Additional metadata
    tags: list[str] = Field(default_factory=list, description="Trade categorization tags")
    commission: float = Field(0.0, description="Commission paid")
    slippage: float = Field(0.0, description="Slippage impact")

    @computed_field
    @property
    def duration(self) -> float | None:
        """Trade duration in seconds."""
        if self.exit_time:
            return (self.exit_time - self.entry_time).total_seconds()
        return None

    @computed_field
    @property
    def r_multiple(self) -> float | None:
        """Risk-reward multiple (R-multiple).

        Returns how many times the initial risk was gained/lost.
        """
        if not self.stop_loss or not self.exit_price:
            return None

        risk = abs(self.entry_price - self.stop_loss) * self.size
        if risk == 0:
            return None

        return self.realized_pnl / risk

    @computed_field
    @property
    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.realized_pnl > 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v),
        }


class EquityPoint(BaseModel):
    """Point on the equity curve.

    Represents account equity at a specific point in time.
    """
    time: datetime = Field(..., description="Timestamp")
    equity: float = Field(..., description="Account equity value")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class BacktestMetrics(BaseModel):
    """Comprehensive backtest performance metrics.

    Provides statistical analysis of backtest results including
    profitability, risk, and trading efficiency metrics.
    """
    # Trade statistics
    total_trades: int = Field(0, ge=0, description="Total number of trades")
    winning_trades: int = Field(0, ge=0, description="Number of winning trades")
    losing_trades: int = Field(0, ge=0, description="Number of losing trades")

    # Performance metrics
    win_rate: float = Field(0.0, ge=0, le=1, description="Percentage of winning trades")
    profit_factor: float = Field(0.0, ge=0, description="Gross profit / gross loss")
    expectancy: float | None = Field(None, description="Average expected return per trade")

    # Risk metrics
    max_drawdown_pct: float = Field(0.0, description="Maximum drawdown percentage")
    max_drawdown_duration_days: float | None = Field(None, description="Longest drawdown period")
    sharpe_ratio: float | None = Field(None, description="Sharpe ratio (risk-adjusted return)")
    sortino_ratio: float | None = Field(None, description="Sortino ratio (downside risk)")

    # R-multiple analysis
    avg_r_multiple: float | None = Field(None, description="Average risk-reward multiple")
    best_r_multiple: float | None = Field(None, description="Best R-multiple achieved")
    worst_r_multiple: float | None = Field(None, description="Worst R-multiple")

    # Trade quality
    avg_win: float = Field(0.0, description="Average winning trade P&L")
    avg_loss: float = Field(0.0, description="Average losing trade P&L")
    largest_win: float = Field(0.0, description="Largest winning trade")
    largest_loss: float = Field(0.0, description="Largest losing trade")

    # Returns
    total_return_pct: float = Field(0.0, description="Total return percentage")
    annual_return_pct: float | None = Field(None, description="Annualized return")

    # Additional metrics
    avg_trade_duration_minutes: float | None = Field(None, description="Average trade duration")
    max_consecutive_wins: int = Field(0, ge=0, description="Longest winning streak")
    max_consecutive_losses: int = Field(0, ge=0, description="Longest losing streak")

    @computed_field
    @property
    def recovery_factor(self) -> float | None:
        """Recovery factor: Net profit / Max drawdown."""
        if self.max_drawdown_pct == 0:
            return None
        return self.total_return_pct / abs(self.max_drawdown_pct)


class BacktestResult(BaseModel):
    """Complete backtest result with all data and metrics.

    Consolidates all information from a backtest run including market data,
    trades, equity curve, indicators, and performance metrics.
    """
    # Run metadata
    symbol: str = Field(..., description="Primary trading symbol")
    timeframe: str = Field(..., description="Data timeframe (e.g., '1min', '1D')")
    mode: Literal["backtest", "paper", "live"] = Field("backtest", description="Execution mode")

    # Time period
    start: datetime = Field(..., description="Backtest start time")
    end: datetime = Field(..., description="Backtest end time")

    # Capital tracking
    initial_capital: float = Field(..., gt=0, description="Starting capital")
    final_capital: float = Field(..., description="Ending capital")

    # Core data
    bars: list[Bar] = Field(default_factory=list, description="OHLCV bars used in backtest")
    trades: list[Trade] = Field(default_factory=list, description="All trades executed")
    equity_curve: list[EquityPoint] = Field(default_factory=list, description="Equity over time")

    # Performance analysis
    metrics: BacktestMetrics = Field(..., description="Performance metrics")

    # Technical indicators (optional)
    indicators: dict[str, list[tuple[datetime, float]]] = Field(
        default_factory=dict,
        description="Indicator values over time {name: [(time, value), ...]}"
    )

    # Strategy metadata
    strategy_name: str | None = Field(None, description="Strategy identifier")
    strategy_params: dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")

    # Additional context
    tags: list[str] = Field(default_factory=list, description="Result categorization tags")
    notes: str = Field("", description="Additional notes or comments")

    @computed_field
    @property
    def duration_days(self) -> float:
        """Backtest duration in days."""
        return (self.end - self.start).total_seconds() / 86400

    @computed_field
    @property
    def total_pnl(self) -> float:
        """Total profit/loss."""
        return self.final_capital - self.initial_capital

    @computed_field
    @property
    def total_pnl_pct(self) -> float:
        """Total return percentage."""
        return ((self.final_capital / self.initial_capital) - 1) * 100

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }


# Adapter functions for backward compatibility with existing code

def from_historical_bar(bar: "HistoricalBar", symbol: str | None = None) -> Bar:
    """Convert HistoricalBar (from market_data.types) to Bar.

    Args:
        bar: HistoricalBar instance from history provider
        symbol: Optional symbol override

    Returns:
        Bar instance
    """
    from src.core.market_data.types import HistoricalBar

    return Bar(
        time=bar.timestamp,
        open=float(bar.open),
        high=float(bar.high),
        low=float(bar.low),
        close=float(bar.close),
        volume=bar.volume,
        symbol=symbol
    )


def to_historical_bars(bars: list[Bar], symbol: str) -> list["HistoricalBar"]:
    """Convert Bar list to HistoricalBar list.

    Args:
        bars: List of Bar instances
        symbol: Symbol for the bars

    Returns:
        List of HistoricalBar instances
    """
    from decimal import Decimal as Dec
    from src.core.market_data.types import HistoricalBar

    return [
        HistoricalBar(
            timestamp=bar.time,
            open=Dec(str(bar.open)),
            high=Dec(str(bar.high)),
            low=Dec(str(bar.low)),
            close=Dec(str(bar.close)),
            volume=int(bar.volume),
            source=bar.symbol or symbol
        )
        for bar in bars
    ]
