"""Backtrader Result Converter.

Converts Backtrader strategy results to comprehensive BacktestResult models
for chart visualization, AI analysis, and result comparison.
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal

import pandas as pd

try:
    import backtrader as bt
    import backtrader.analyzers as btanalyzers
    BACKTRADER_AVAILABLE = True
except ImportError:
    BACKTRADER_AVAILABLE = False
    bt = None

from src.core.models.backtest_models import (
    BacktestMetrics,
    BacktestResult,
    Bar,
    EquityPoint,
    Trade,
    TradeSide,
)

logger = logging.getLogger(__name__)


def backtrader_to_backtest_result(
    strategy,
    cerebro,
    initial_value: float,
    final_value: float,
    symbol: str,
    timeframe: str,
    start_date: datetime,
    end_date: datetime,
    strategy_name: str | None = None,
    strategy_params: dict | None = None
) -> BacktestResult:
    """Convert Backtrader results to comprehensive BacktestResult.

    Args:
        strategy: Backtrader strategy instance with analyzers
        cerebro: Backtrader Cerebro instance
        initial_value: Initial portfolio value
        final_value: Final portfolio value
        symbol: Primary trading symbol
        timeframe: Data timeframe (e.g., '1min', '1D')
        start_date: Backtest start datetime
        end_date: Backtest end datetime
        strategy_name: Optional strategy identifier
        strategy_params: Optional strategy parameters

    Returns:
        Comprehensive BacktestResult instance

    Raises:
        ValueError: If required data is missing
    """
    if not BACKTRADER_AVAILABLE:
        raise ImportError("Backtrader not installed")

    logger.info(f"Converting Backtrader results for {symbol}")

    # Extract bars from data feed
    bars = _extract_bars_from_strategy(strategy, symbol)
    logger.debug(f"Extracted {len(bars)} bars")

    # Extract trades
    trades = _extract_trades_from_strategy(strategy, symbol)
    logger.debug(f"Extracted {len(trades)} trades")

    # Extract equity curve
    equity_curve = _extract_equity_curve(strategy, initial_value)
    logger.debug(f"Extracted equity curve with {len(equity_curve)} points")

    # Calculate comprehensive metrics
    metrics = _calculate_metrics(
        trades=trades,
        equity_curve=equity_curve,
        initial_capital=initial_value,
        final_capital=final_value,
        start_date=start_date,
        end_date=end_date,
        strategy_analyzers=strategy.analyzers
    )

    # Extract indicators (if available)
    indicators = _extract_indicators(strategy)

    # Build result
    result = BacktestResult(
        symbol=symbol,
        timeframe=timeframe,
        mode="backtest",
        start=start_date,
        end=end_date,
        initial_capital=initial_value,
        final_capital=final_value,
        bars=bars,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
        indicators=indicators,
        strategy_name=strategy_name or "Unknown",
        strategy_params=strategy_params or {},
        tags=["backtrader"],
        notes=f"Backtest completed with {len(trades)} trades"
    )

    logger.info(
        f"Conversion complete: {len(trades)} trades, "
        f"{metrics.win_rate:.2%} win rate, "
        f"{metrics.total_return_pct:.2f}% return"
    )

    return result


def _extract_bars_from_strategy(strategy, symbol: str) -> list[Bar]:
    """Extract OHLCV bars from Backtrader strategy data feed.

    Args:
        strategy: Backtrader strategy instance
        symbol: Trading symbol

    Returns:
        List of Bar instances
    """
    bars = []

    try:
        # Get the data feed (first one if multiple)
        data = strategy.datas[0] if hasattr(strategy, 'datas') and strategy.datas else strategy.data

        # Backtrader stores data in reverse (most recent last)
        # We need to iterate through all available bars
        data_len = len(data)

        for i in range(data_len):
            try:
                # Backtrader uses negative indexing from current position
                # For historical conversion, we access by absolute index
                timestamp = data.datetime.datetime(ago=-data_len + i + 1)

                bar = Bar(
                    time=timestamp,
                    open=float(data.open[-data_len + i + 1]),
                    high=float(data.high[-data_len + i + 1]),
                    low=float(data.low[-data_len + i + 1]),
                    close=float(data.close[-data_len + i + 1]),
                    volume=int(data.volume[-data_len + i + 1]),
                    symbol=symbol
                )
                bars.append(bar)

            except (IndexError, AttributeError) as e:
                logger.debug(f"Skipping bar {i}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error extracting bars: {e}")
        # Return empty list on error
        return []

    return bars


def _extract_trades_from_strategy(strategy, symbol: str) -> list[Trade]:
    """Extract trades from Backtrader strategy.

    Args:
        strategy: Backtrader strategy instance
        symbol: Trading symbol

    Returns:
        List of Trade instances
    """
    trades = []

    # Check if strategy has custom trades list (from OrderPilotStrategy)
    if hasattr(strategy, 'trades') and strategy.trades:
        for idx, trade_data in enumerate(strategy.trades):
            try:
                trade = Trade(
                    id=f"trade_{idx}_{uuid.uuid4().hex[:8]}",
                    symbol=symbol,
                    side=TradeSide.LONG,  # Assuming long for now (can be enhanced)
                    size=1.0,  # Default size (not stored in simple trade data)

                    # Entry
                    entry_time=datetime.combine(trade_data['entry_date'], datetime.min.time()),
                    entry_price=float(trade_data['entry_price']),
                    entry_reason="Strategy signal",

                    # Exit
                    exit_time=datetime.combine(trade_data['exit_date'], datetime.min.time()),
                    exit_price=float(trade_data['exit_price']),
                    exit_reason="Strategy exit signal",

                    # P&L
                    realized_pnl=float(trade_data.get('profit', 0)),
                    realized_pnl_pct=float(trade_data.get('profit_pct', 0)),

                    # Costs
                    commission=float(trade_data.get('commission', 0)),
                    slippage=0.0,

                    # Risk management (not available in simple trade data)
                    stop_loss=None,
                    take_profit=None
                )
                trades.append(trade)

            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing trade {idx}: {e}")
                continue

    # Alternatively, try to extract from Backtrader's trade analyzer
    elif hasattr(strategy, 'analyzers') and hasattr(strategy.analyzers, 'trades'):
        try:
            trades_analysis = strategy.analyzers.trades.get_analysis()
            # Note: Backtrader's TradeAnalyzer doesn't provide individual trade details
            # We can only get aggregate statistics
            logger.warning("TradeAnalyzer provides only aggregate stats, not individual trades")
        except Exception as e:
            logger.debug(f"Could not extract from TradeAnalyzer: {e}")

    return trades


def _extract_equity_curve(strategy, initial_value: float) -> list[EquityPoint]:
    """Extract equity curve from Backtrader strategy.

    Args:
        strategy: Backtrader strategy instance
        initial_value: Initial portfolio value

    Returns:
        List of EquityPoint instances
    """
    equity_points = []

    try:
        # Get TimeReturn analyzer results
        if hasattr(strategy, 'analyzers') and hasattr(strategy.analyzers, 'timereturn'):
            timereturn = strategy.analyzers.timereturn.get_analysis()

            # Convert to cumulative equity
            cumulative_value = initial_value

            for date, daily_return in sorted(timereturn.items()):
                cumulative_value *= (1 + daily_return)

                # Convert date to datetime
                if isinstance(date, datetime):
                    timestamp = date
                else:
                    timestamp = datetime.combine(date, datetime.min.time())

                equity_points.append(
                    EquityPoint(
                        time=timestamp,
                        equity=cumulative_value
                    )
                )

    except Exception as e:
        logger.error(f"Error extracting equity curve: {e}")
        # Fallback: create simple two-point curve
        equity_points = [
            EquityPoint(time=strategy.datas[0].datetime.datetime(0), equity=initial_value),
            EquityPoint(time=strategy.datas[0].datetime.datetime(), equity=initial_value)
        ]

    return equity_points


def _calculate_metrics(
    trades: list[Trade],
    equity_curve: list[EquityPoint],
    initial_capital: float,
    final_capital: float,
    start_date: datetime,
    end_date: datetime,
    strategy_analyzers
) -> BacktestMetrics:
    """Calculate comprehensive backtest metrics.

    Args:
        trades: List of Trade instances
        equity_curve: List of EquityPoint instances
        initial_capital: Initial portfolio value
        final_capital: Final portfolio value
        start_date: Backtest start datetime
        end_date: Backtest end datetime
        strategy_analyzers: Backtrader analyzers object

    Returns:
        BacktestMetrics instance
    """
    # Trade statistics
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.is_winner])
    losing_trades = total_trades - winning_trades

    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

    # P&L analysis
    if trades:
        wins = [t.realized_pnl for t in trades if t.is_winner]
        losses = [abs(t.realized_pnl) for t in trades if not t.is_winner]

        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        largest_win = max(wins) if wins else 0.0
        largest_loss = -max(losses) if losses else 0.0

        # Profit factor
        gross_profit = sum(wins)
        gross_loss = sum(losses)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    else:
        avg_win = 0.0
        avg_loss = 0.0
        largest_win = 0.0
        largest_loss = 0.0
        profit_factor = 0.0
        expectancy = None

    # R-multiple analysis
    r_multiples = [t.r_multiple for t in trades if t.r_multiple is not None]
    avg_r_multiple = sum(r_multiples) / len(r_multiples) if r_multiples else None
    best_r_multiple = max(r_multiples) if r_multiples else None
    worst_r_multiple = min(r_multiples) if r_multiples else None

    # Returns
    total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100

    # Annualized return
    days = (end_date - start_date).days
    years = days / 365.25 if days > 0 else 1
    annual_return_pct = (((final_capital / initial_capital) ** (1 / years)) - 1) * 100 if years > 0 else 0

    # Risk metrics from analyzers
    sharpe_ratio = None
    sortino_ratio = None
    max_drawdown_pct = 0.0
    max_drawdown_duration_days = None

    try:
        if hasattr(strategy_analyzers, 'sharpe'):
            sharpe_analysis = strategy_analyzers.sharpe.get_analysis()
            sharpe_ratio = sharpe_analysis.get('sharperatio', None)

        if hasattr(strategy_analyzers, 'drawdown'):
            drawdown_analysis = strategy_analyzers.drawdown.get_analysis()
            max_drawdown_pct = abs(drawdown_analysis.get('max', {}).get('drawdown', 0))
            max_drawdown_len = drawdown_analysis.get('max', {}).get('len', 0)
            max_drawdown_duration_days = max_drawdown_len if max_drawdown_len else None

    except Exception as e:
        logger.warning(f"Error extracting analyzer metrics: {e}")

    # Trade duration
    durations = [t.duration for t in trades if t.duration is not None]
    avg_trade_duration_minutes = (sum(durations) / len(durations) / 60) if durations else None

    # Consecutive wins/losses
    max_consecutive_wins = _calculate_max_consecutive(trades, is_winner=True)
    max_consecutive_losses = _calculate_max_consecutive(trades, is_winner=False)

    return BacktestMetrics(
        # Trade statistics
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,

        # Performance metrics
        win_rate=win_rate,
        profit_factor=profit_factor,
        expectancy=expectancy,

        # Risk metrics
        max_drawdown_pct=max_drawdown_pct,
        max_drawdown_duration_days=max_drawdown_duration_days,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,

        # R-multiple analysis
        avg_r_multiple=avg_r_multiple,
        best_r_multiple=best_r_multiple,
        worst_r_multiple=worst_r_multiple,

        # Trade quality
        avg_win=avg_win,
        avg_loss=avg_loss,
        largest_win=largest_win,
        largest_loss=largest_loss,

        # Returns
        total_return_pct=total_return_pct,
        annual_return_pct=annual_return_pct,

        # Additional metrics
        avg_trade_duration_minutes=avg_trade_duration_minutes,
        max_consecutive_wins=max_consecutive_wins,
        max_consecutive_losses=max_consecutive_losses
    )


def _calculate_max_consecutive(trades: list[Trade], is_winner: bool) -> int:
    """Calculate maximum consecutive wins or losses.

    Args:
        trades: List of Trade instances
        is_winner: True to count wins, False to count losses

    Returns:
        Maximum consecutive count
    """
    if not trades:
        return 0

    max_consecutive = 0
    current_consecutive = 0

    for trade in trades:
        if trade.is_winner == is_winner:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0

    return max_consecutive


def _extract_indicators(strategy) -> dict[str, list[tuple[datetime, float]]]:
    """Extract indicator values from Backtrader strategy.

    Args:
        strategy: Backtrader strategy instance

    Returns:
        Dictionary mapping indicator names to time-series data
    """
    indicators = {}

    # This is a placeholder - actual implementation depends on
    # how indicators are stored in the strategy
    # For now, we return empty dict

    # TODO: Implement indicator extraction if strategy exposes indicators
    # Example:
    # if hasattr(strategy, 'indicators'):
    #     for name, indicator in strategy.indicators.items():
    #         values = [(data.datetime.datetime(i), indicator[i])
    #                   for i in range(len(indicator))]
    #         indicators[name] = values

    return indicators
