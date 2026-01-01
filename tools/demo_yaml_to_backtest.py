"""End-to-End Demo: YAML Strategy → Backtest Result.

Demonstrates the complete workflow:
1. Load strategy from YAML file
2. Compile to Backtrader strategy
3. Run backtest with BacktestEngine
4. Analyze comprehensive BacktestResult

Usage:
    python tools/demo_yaml_to_backtest.py
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import backtrader as bt
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.backtesting.backtrader_integration import BacktestEngine
from src.core.market_data.history_provider import HistoryManager, Timeframe
from src.core.strategy.definition import StrategyDefinition

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_synthetic_data(
    days: int = 365,
    start_price: float = 100.0,
    volatility: float = 0.02
) -> bt.feeds.DataBase:
    """Create synthetic price data for testing.

    Args:
        days: Number of days to generate
        start_price: Starting price
        volatility: Daily volatility

    Returns:
        Backtrader data feed
    """
    np.random.seed(42)

    # Generate dates
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start=start_date, periods=days, freq='D')

    # Generate price series with trend and noise
    prices = []
    current_price = start_price

    for i in range(days):
        # Add small upward trend + random walk
        trend = 0.0003 * i  # Slight upward bias
        noise = np.random.randn() * volatility * current_price
        current_price = max(current_price + trend + noise, 10.0)
        prices.append(current_price)

    # Create OHLCV data
    df = pd.DataFrame({
        'datetime': dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': [np.random.randint(100000, 1000000) for _ in range(days)],
    })
    df.set_index('datetime', inplace=True)

    # Create Backtrader data feed
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # Use index
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1
    )

    return data


async def run_yaml_strategy_backtest(
    yaml_file: Path,
    symbol: str = "TEST",
    initial_cash: float = 100000.0
) -> None:
    """Run backtest with YAML strategy.

    Args:
        yaml_file: Path to YAML strategy file
        symbol: Trading symbol
        initial_cash: Initial capital
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"YAML STRATEGY BACKTEST")
    logger.info(f"{'='*80}")
    logger.info(f"Strategy File: {yaml_file.name}")
    logger.info(f"Symbol: {symbol}")
    logger.info(f"Initial Capital: ${initial_cash:,.2f}")

    # 1. Load strategy from YAML
    logger.info(f"\n{'Step 1: Load Strategy from YAML':-^80}")
    with open(yaml_file, "r") as f:
        yaml_content = f.read()

    strategy_def = StrategyDefinition.from_yaml(yaml_content)
    logger.info(f"✓ Loaded: {strategy_def.name} v{strategy_def.version}")
    logger.info(f"  Indicators: {len(strategy_def.indicators)}")
    for ind in strategy_def.indicators:
        logger.info(f"    • {ind.alias}: {ind.type} ({ind.params})")
    logger.info(f"  Long Trading: Yes")
    logger.info(f"  Short Trading: {'Yes' if strategy_def.entry_short else 'No'}")

    # 2. Create synthetic data
    logger.info(f"\n{'Step 2: Generate Test Data':-^80}")
    data = create_synthetic_data(days=365, start_price=100.0, volatility=0.02)
    logger.info(f"✓ Generated 365 days of synthetic price data")

    # 3. Initialize BacktestEngine (without HistoryManager since we have custom data)
    logger.info(f"\n{'Step 3: Initialize Backtest Engine':-^80}")
    # Pass None for history_manager since we're providing custom data_feed
    engine = BacktestEngine(history_manager=None)
    logger.info(f"✓ BacktestEngine initialized")

    # 4. Run Backtest
    logger.info(f"\n{'Step 4: Compile Strategy & Run Backtest':-^80}")
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)

    result = await engine.run_backtest_with_definition(
        strategy_def=strategy_def,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_cash=initial_cash,
        commission=0.001,  # 0.1%
        timeframe=Timeframe.DAY_1,
        data_feed=data
    )

    logger.info(f"✓ Backtest completed!")

    # 5. Display Results
    logger.info(f"\n{'='*80}")
    logger.info(f"BACKTEST RESULTS")
    logger.info(f"{'='*80}")

    m = result.metrics

    logger.info(f"\n{'PERFORMANCE OVERVIEW':-^80}")
    logger.info(f"Strategy: {result.strategy_name}")
    logger.info(f"Symbol: {result.symbol}")
    logger.info(f"Period: {result.start.date()} → {result.end.date()}")
    logger.info(f"Initial Capital: ${result.initial_capital:,.2f}")
    logger.info(f"Final Capital: ${result.final_capital:,.2f}")
    pnl = result.final_capital - result.initial_capital
    logger.info(f"P&L: ${pnl:,.2f} ({m.total_return_pct:+.2f}%)")

    logger.info(f"\n{'PERFORMANCE METRICS':-^80}")
    logger.info(f"Total Return: {m.total_return_pct:.2f}%")
    logger.info(f"Annual Return: {m.annual_return_pct or 0:.2f}%")
    logger.info(f"Sharpe Ratio: {m.sharpe_ratio or 0:.3f}")
    logger.info(f"Sortino Ratio: {m.sortino_ratio or 0:.3f}")
    logger.info(f"Max Drawdown: {m.max_drawdown_pct:.2f}%")
    if m.max_drawdown_duration_days:
        logger.info(f"Max DD Duration: {m.max_drawdown_duration_days:.0f} days")

    logger.info(f"\n{'TRADE STATISTICS':-^80}")
    logger.info(f"Total Trades: {m.total_trades}")
    logger.info(f"Winning Trades: {m.winning_trades}")
    logger.info(f"Losing Trades: {m.losing_trades}")
    logger.info(f"Win Rate: {m.win_rate:.1%}")
    logger.info(f"Profit Factor: {m.profit_factor:.2f}")

    if m.avg_win:
        logger.info(f"Avg Winning Trade: ${m.avg_win:.2f}")
    if m.avg_loss:
        logger.info(f"Avg Losing Trade: ${m.avg_loss:.2f}")
    if m.largest_win:
        logger.info(f"Best Trade: ${m.largest_win:.2f}")
    if m.largest_loss:
        logger.info(f"Worst Trade: ${m.largest_loss:.2f}")

    # Display sample trades
    if result.trades:
        logger.info(f"\n{'SAMPLE TRADES (First 5)':-^80}")
        for i, trade in enumerate(result.trades[:5], 1):
            logger.info(
                f"{i}. {trade.side.upper()}: "
                f"Entry={trade.entry_time.date()} @ ${trade.entry_price:.2f}, "
                f"Exit={trade.exit_time.date() if trade.exit_time else 'OPEN'} @ "
                f"${trade.exit_price:.2f if trade.exit_price else 0:.2f}, "
                f"P&L={trade.realized_pnl_pct:+.2f}%"
            )

    # Display equity curve info
    if result.equity_curve and len(result.equity_curve) > 1:
        logger.info(f"\n{'EQUITY CURVE':-^80}")
        logger.info(f"Data points: {len(result.equity_curve)}")
        peak_equity = max(point.equity for point in result.equity_curve)
        logger.info(f"Peak Equity: ${peak_equity:,.2f}")

    logger.info(f"\n{'='*80}")


async def main():
    """Run demo with all YAML strategies."""
    logger.info("="*80)
    logger.info("END-TO-END DEMO: YAML → BACKTEST RESULT")
    logger.info("="*80)

    # Find strategy files
    strategies_dir = Path(__file__).parent.parent / "examples" / "strategies"
    yaml_files = list(strategies_dir.glob("*.yaml"))

    if not yaml_files:
        logger.error(f"No YAML files found in {strategies_dir}")
        return 1

    logger.info(f"\nFound {len(yaml_files)} strategy file(s):")
    for f in yaml_files:
        logger.info(f"  • {f.name}")

    # Run backtest for each strategy
    for yaml_file in yaml_files:
        try:
            await run_yaml_strategy_backtest(
                yaml_file=yaml_file,
                symbol="SYNTH",
                initial_cash=100000.0
            )

            # Add separator between strategies
            if yaml_file != yaml_files[-1]:
                logger.info(f"\n\n")

        except Exception as e:
            logger.error(f"✗ Failed to backtest {yaml_file.name}: {e}")
            import traceback
            traceback.print_exc()

    logger.info(f"\n{'='*80}")
    logger.info("DEMO COMPLETE")
    logger.info(f"{'='*80}")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Demo failed: {e}")
        sys.exit(1)
