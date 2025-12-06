"""Test Script for BacktestResult → Chart Adapter Pipeline.

Demonstrates the complete pipeline from BacktestResult to Lightweight Charts JSON:
1. Create or load BacktestResult
2. Convert to chart data using ChartAdapter
3. Validate chart data
4. Write JSON to file
5. Display summary

Usage:
    python tools/test_backtest_chart_adapter.py
"""

import json
import logging
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models.backtest_models import (
    BacktestMetrics,
    BacktestResult,
    Bar,
    EquityPoint,
    Trade,
    TradeSide,
)
from src.ui.chart.chart_adapter import ChartAdapter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_backtest_result() -> BacktestResult:
    """Create a comprehensive sample BacktestResult for testing.

    Returns:
        Sample BacktestResult with realistic data
    """
    logger.info("Creating sample BacktestResult...")

    # Generate sample bars (1 month of daily data)
    bars = []
    base_date = datetime(2024, 1, 1, 9, 30)
    base_price = 100.0

    for i in range(30):
        # Simulate price movement
        open_price = base_price + (i * 0.5)
        high_price = open_price + 2.0
        low_price = open_price - 1.5
        close_price = open_price + (1.0 if i % 3 == 0 else -0.5)

        bar = Bar(
            time=base_date + timedelta(days=i),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=10000 + i * 500,
            symbol="AAPL"
        )
        bars.append(bar)

        base_price = close_price

    logger.info(f"Created {len(bars)} bars")

    # Generate sample trades
    trades = []

    # Trade 1: Winning LONG
    trades.append(Trade(
        id=f"trade_1_{uuid.uuid4().hex[:8]}",
        symbol="AAPL",
        side=TradeSide.LONG,
        size=100.0,
        entry_time=datetime(2024, 1, 5, 10, 0),
        entry_price=102.5,
        entry_reason="Bullish crossover - SMA(20) crosses above SMA(50)",
        exit_time=datetime(2024, 1, 15, 15, 30),
        exit_price=108.0,
        exit_reason="Take profit hit at resistance level",
        stop_loss=98.0,
        take_profit=110.0,
        realized_pnl=550.0,
        realized_pnl_pct=5.37,
        commission=2.0,
        slippage=0.10,
        tags=["trend-following", "momentum"]
    ))

    # Trade 2: Losing SHORT
    trades.append(Trade(
        id=f"trade_2_{uuid.uuid4().hex[:8]}",
        symbol="AAPL",
        side=TradeSide.SHORT,
        size=100.0,
        entry_time=datetime(2024, 1, 18, 11, 0),
        entry_price=109.0,
        entry_reason="Overbought RSI(14) > 70 at resistance",
        exit_time=datetime(2024, 1, 22, 14, 0),
        exit_price=111.0,
        exit_reason="Stop loss triggered",
        stop_loss=111.5,
        take_profit=104.0,
        realized_pnl=-200.0,
        realized_pnl_pct=-1.83,
        commission=2.0,
        slippage=0.05,
        tags=["mean-reversion"]
    ))

    # Trade 3: Winning LONG
    trades.append(Trade(
        id=f"trade_3_{uuid.uuid4().hex[:8]}",
        symbol="AAPL",
        side=TradeSide.LONG,
        size=150.0,
        entry_time=datetime(2024, 1, 24, 10, 30),
        entry_price=107.0,
        entry_reason="Support bounce at previous low",
        exit_time=datetime(2024, 1, 29, 15, 0),
        exit_price=112.5,
        exit_reason="Profit target reached",
        stop_loss=104.0,
        take_profit=113.0,
        realized_pnl=825.0,
        realized_pnl_pct=5.14,
        commission=2.0,
        slippage=0.15,
        tags=["support-resistance", "breakout"]
    ))

    logger.info(f"Created {len(trades)} trades")

    # Generate equity curve
    equity_curve = []
    initial_capital = 10000.0
    equity = initial_capital

    for i in range(30):
        # Simulate equity growth
        if i == 15:  # Trade 1 exit
            equity += 550.0
        elif i == 22:  # Trade 2 exit
            equity -= 200.0
        elif i == 29:  # Trade 3 exit
            equity += 825.0

        equity_curve.append(
            EquityPoint(
                time=base_date + timedelta(days=i),
                equity=equity
            )
        )

    logger.info(f"Created equity curve with {len(equity_curve)} points")

    # Calculate metrics
    metrics = BacktestMetrics(
        total_trades=3,
        winning_trades=2,
        losing_trades=1,
        win_rate=2/3,
        profit_factor=1375.0 / 200.0,  # (550 + 825) / 200
        expectancy=391.67,  # (550 + 825 - 200) / 3
        max_drawdown_pct=2.0,
        max_drawdown_duration_days=7.0,
        sharpe_ratio=1.85,
        sortino_ratio=2.34,
        avg_r_multiple=3.25,
        best_r_multiple=5.5,
        worst_r_multiple=-0.67,
        avg_win=687.5,
        avg_loss=-200.0,
        largest_win=825.0,
        largest_loss=-200.0,
        total_return_pct=11.75,
        annual_return_pct=141.0,  # Annualized
        avg_trade_duration_minutes=7200.0,  # ~5 days
        max_consecutive_wins=2,
        max_consecutive_losses=1
    )

    # Create sample indicators
    indicators = {
        'SMA_20': [
            (base_date + timedelta(days=i), 100.0 + i * 0.3)
            for i in range(30)
        ],
        'SMA_50': [
            (base_date + timedelta(days=i), 100.0 + i * 0.2)
            for i in range(30)
        ],
        'RSI_14': [
            (base_date + timedelta(days=i), 50.0 + (i % 10) * 2.5)
            for i in range(30)
        ]
    }

    # Build BacktestResult
    result = BacktestResult(
        symbol="AAPL",
        timeframe="1D",
        mode="backtest",
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 30),
        initial_capital=initial_capital,
        final_capital=equity,
        bars=bars,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
        indicators=indicators,
        strategy_name="Trend Following + Mean Reversion Hybrid",
        strategy_params={
            "sma_fast": 20,
            "sma_slow": 50,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "risk_per_trade": 0.02
        },
        tags=["hybrid-strategy", "multi-timeframe"],
        notes="Sample backtest demonstrating chart adapter functionality"
    )

    logger.info("Sample BacktestResult created successfully")
    logger.info(f"  Symbol: {result.symbol}")
    logger.info(f"  Period: {result.start.date()} to {result.end.date()}")
    logger.info(f"  Initial Capital: ${result.initial_capital:,.2f}")
    logger.info(f"  Final Capital: ${result.final_capital:,.2f}")
    logger.info(f"  Total P&L: ${result.total_pnl:,.2f} ({result.total_pnl_pct:.2f}%)")
    logger.info(f"  Trades: {result.metrics.total_trades}")
    logger.info(f"  Win Rate: {result.metrics.win_rate:.2%}")

    return result


def test_chart_adapter_pipeline():
    """Test the complete ChartAdapter pipeline."""
    logger.info("=" * 80)
    logger.info("CHART ADAPTER PIPELINE TEST")
    logger.info("=" * 80)

    # Step 1: Create sample BacktestResult
    logger.info("\n[1/5] Creating BacktestResult...")
    backtest_result = create_sample_backtest_result()

    # Step 2: Convert to chart data
    logger.info("\n[2/5] Converting to chart data...")
    adapter = ChartAdapter()
    chart_data = adapter.backtest_result_to_chart_data(backtest_result)

    logger.info(f"  Candlesticks: {len(chart_data['candlesticks'])}")
    logger.info(f"  Equity Points: {len(chart_data['equity_curve'])}")
    logger.info(f"  Markers: {len(chart_data['markers'])}")
    logger.info(f"  Indicators: {len(chart_data['indicators'])}")

    # Step 3: Validate chart data
    logger.info("\n[3/5] Validating chart data...")
    is_valid, errors = adapter.validate_chart_data(chart_data)

    if is_valid:
        logger.info("  ✅ Chart data is valid!")
    else:
        logger.error("  ❌ Chart data validation failed:")
        for error in errors:
            logger.error(f"    - {error}")
        return False

    # Step 4: Convert to JSON
    logger.info("\n[4/5] Converting to JSON...")
    json_str = adapter.to_json(chart_data, indent=2)
    json_size_kb = len(json_str) / 1024

    logger.info(f"  JSON size: {json_size_kb:.2f} KB")

    # Step 5: Write to file
    logger.info("\n[5/5] Writing to file...")
    output_dir = Path(__file__).parent.parent / "tmp"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "backtest_chart_data.json"

    with open(output_file, 'w') as f:
        f.write(json_str)

    logger.info(f"  ✅ JSON written to: {output_file}")
    logger.info(f"  File size: {output_file.stat().st_size / 1024:.2f} KB")

    # Display summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    metadata = chart_data['metadata']
    metrics = metadata['metrics']

    logger.info(f"\nStrategy: {metadata['strategy_name']}")
    logger.info(f"Symbol: {metadata['symbol']} | Timeframe: {metadata['timeframe']}")
    logger.info(f"Period: {metadata['start']} to {metadata['end']}")
    logger.info(f"\nCapital:")
    logger.info(f"  Initial: ${metadata['initial_capital']:,.2f}")
    logger.info(f"  Final: ${metadata['final_capital']:,.2f}")
    logger.info(f"  P&L: ${metadata['total_pnl']:,.2f} ({metadata['total_pnl_pct']:.2f}%)")
    logger.info(f"\nPerformance Metrics:")
    logger.info(f"  Total Trades: {metrics['total_trades']}")
    logger.info(f"  Win Rate: {metrics['win_rate']:.2%}")
    logger.info(f"  Profit Factor: {metrics['profit_factor']:.2f}")
    logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
    logger.info(f"  Total Return: {metrics['total_return_pct']:.2f}%")

    logger.info("\n" + "=" * 80)
    logger.info("✅ PIPELINE TEST COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = test_chart_adapter_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"Pipeline test failed: {e}")
        sys.exit(1)
