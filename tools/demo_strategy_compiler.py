"""Demo script for Strategy Compiler.

Demonstrates loading YAML strategies, compiling to Backtrader, and running backtests.

Usage:
    python tools/demo_strategy_compiler.py
"""

import logging
import sys
from pathlib import Path

import backtrader as bt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.strategy.compiler import StrategyCompiler
from src.core.strategy.definition import StrategyDefinition

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_data() -> bt.feeds.DataBase:
    """Create sample data feed for testing.

    Returns:
        Backtrader data feed
    """
    # Create synthetic data using Backtrader's PandasData
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta

    # Generate 200 days of synthetic price data
    np.random.seed(42)
    dates = pd.date_range(start=datetime(2023, 1, 1), periods=200, freq='D')

    # Generate prices with some trend and volatility
    base_price = 100.0
    prices = []
    current_price = base_price

    for i in range(200):
        # Add trend and random walk
        trend = 0.001 * i  # Slight upward trend
        noise = np.random.randn() * 2  # Random volatility
        current_price = max(current_price + trend + noise, 10.0)  # Prevent negative prices
        prices.append(current_price)

    # Create OHLCV data
    df = pd.DataFrame({
        'datetime': dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000, 10000) for _ in range(200)],
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


def run_backtest_with_strategy(
    strategy_def: StrategyDefinition,
    data: bt.feeds.DataBase,
    initial_cash: float = 100000.0
) -> dict:
    """Run backtest with compiled strategy.

    Args:
        strategy_def: Strategy definition to compile and test
        data: Backtrader data feed
        initial_cash: Initial capital

    Returns:
        Dictionary with backtest results
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"BACKTESTING: {strategy_def.name} v{strategy_def.version}")
    logger.info(f"{'='*80}")

    # Compile strategy
    compiler = StrategyCompiler()
    strategy_class = compiler.compile(strategy_def)

    # Create Cerebro engine
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class)
    cerebro.adddata(data)

    # Set initial cash
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # Run backtest
    logger.info(f"Initial Portfolio Value: ${cerebro.broker.getvalue():,.2f}")

    results = cerebro.run()
    strategy_instance = results[0]

    final_value = cerebro.broker.getvalue()
    pnl = final_value - initial_cash
    pnl_pct = (pnl / initial_cash) * 100

    logger.info(f"Final Portfolio Value: ${final_value:,.2f}")
    logger.info(f"P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")

    # Extract analyzer results
    sharpe = strategy_instance.analyzers.sharpe.get_analysis().get('sharperatio', 0.0)
    drawdown_info = strategy_instance.analyzers.drawdown.get_analysis()
    trades_info = strategy_instance.analyzers.trades.get_analysis()

    logger.info(f"\n{'PERFORMANCE METRICS':-^80}")
    sharpe_str = f"{sharpe:.3f}" if sharpe else "N/A"
    logger.info(f"Sharpe Ratio: {sharpe_str}")
    logger.info(f"Max Drawdown: {drawdown_info.max.drawdown:.2f}%")
    logger.info(f"Drawdown Duration: {drawdown_info.max.len} days")

    # Trade statistics (handle case when no trades occurred)
    try:
        total_trades = trades_info.total.closed if hasattr(trades_info, 'total') else 0
        won_trades = trades_info.won.total if hasattr(trades_info, 'won') else 0
        lost_trades = trades_info.lost.total if hasattr(trades_info, 'lost') else 0
    except (KeyError, AttributeError):
        # No trades occurred
        total_trades = 0
        won_trades = 0
        lost_trades = 0

    logger.info(f"\n{'TRADE STATISTICS':-^80}")
    logger.info(f"Total Trades: {total_trades}")
    logger.info(f"Won: {won_trades}")
    logger.info(f"Lost: {lost_trades}")
    if total_trades > 0:
        win_rate = (won_trades / total_trades) * 100
        logger.info(f"Win Rate: {win_rate:.1f}%")

    return {
        'strategy': strategy_def.name,
        'initial_value': initial_cash,
        'final_value': final_value,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'sharpe_ratio': sharpe if sharpe else 0.0,
        'max_drawdown': drawdown_info.max.drawdown,
        'total_trades': total_trades,
        'won_trades': won_trades,
        'lost_trades': lost_trades,
    }


def main():
    """Run strategy compilation demo."""
    logger.info("="*80)
    logger.info("STRATEGY COMPILER DEMO")
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

    # Create sample data
    logger.info("\nGenerating synthetic market data...")
    data = create_sample_data()

    # Load, compile, and backtest each strategy
    results = []
    for yaml_file in yaml_files:
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing: {yaml_file.name}")
            logger.info(f"{'='*80}")

            # Load strategy from YAML
            with open(yaml_file, "r") as f:
                yaml_content = f.read()

            strategy_def = StrategyDefinition.from_yaml(yaml_content)
            logger.info(f"✓ Strategy loaded: {strategy_def.name} v{strategy_def.version}")
            logger.info(f"  Indicators: {len(strategy_def.indicators)}")
            logger.info(f"  Long trading: Yes")
            logger.info(f"  Short trading: {'Yes' if strategy_def.entry_short else 'No'}")

            # Run backtest
            result = run_backtest_with_strategy(strategy_def, data)
            results.append(result)

        except Exception as e:
            logger.error(f"✗ Failed to process {yaml_file.name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")

    if results:
        logger.info(f"\nBacktest Results:")
        logger.info(f"{'Strategy':<30} {'P&L':>15} {'P&L %':>10} {'Sharpe':>10} {'Trades':>10}")
        logger.info("-" * 80)

        for r in results:
            logger.info(
                f"{r['strategy']:<30} "
                f"${r['pnl']:>13,.2f} "
                f"{r['pnl_pct']:>9.2f}% "
                f"{r['sharpe_ratio']:>9.3f} "
                f"{r['total_trades']:>10}"
            )

        logger.info("\n✓ All strategies tested successfully!")
        return 0
    else:
        logger.error("\n✗ No strategies were successfully tested")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Demo failed: {e}")
        sys.exit(1)
