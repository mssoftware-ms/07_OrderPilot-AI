"""Demo script for BacktestChartWidget.

Demonstrates the complete UI integration with Qt WebChannel and ChartBridge.

Usage:
    python tools/demo_chart_widget.py
"""

import logging
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication

from src.core.models.backtest_models import (
    BacktestMetrics,
    BacktestResult,
    Bar,
    EquityPoint,
    Trade,
    TradeSide,
)
from src.ui.widgets.backtest_chart_widget import BacktestChartWidget

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_demo_backtest_result() -> BacktestResult:
    """Create a demo BacktestResult for testing.

    Returns:
        Sample BacktestResult
    """
    logger.info("Creating demo backtest result...")

    # Generate bars (2 weeks of hourly data)
    bars = []
    base_date = datetime(2024, 1, 1, 9, 30)
    base_price = 150.0

    for i in range(336):  # 14 days * 24 hours
        # Simulate realistic price movement
        volatility = 2.0
        trend = 0.05
        noise = (i % 7 - 3) * 0.3

        open_price = base_price + noise
        high_price = open_price + abs(volatility)
        low_price = open_price - abs(volatility)
        close_price = open_price + trend + (i % 5 - 2) * 0.2

        bar = Bar(
            time=base_date + timedelta(hours=i),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=50000 + i * 100,
            symbol="TSLA"
        )
        bars.append(bar)
        base_price = close_price

    logger.info(f"Created {len(bars)} bars")

    # Generate trades
    trades = [
        # Trade 1: Winning LONG
        Trade(
            id=f"trade_1_{uuid.uuid4().hex[:8]}",
            symbol="TSLA",
            side=TradeSide.LONG,
            size=50.0,
            entry_time=datetime(2024, 1, 2, 10, 0),
            entry_price=151.0,
            entry_reason="Bullish breakout above resistance",
            exit_time=datetime(2024, 1, 5, 14, 30),
            exit_price=156.5,
            exit_reason="Target reached at 3.6% gain",
            stop_loss=148.0,
            take_profit=157.0,
            realized_pnl=275.0,
            realized_pnl_pct=3.64,
            commission=2.5,
            tags=["breakout", "trend-following"]
        ),
        # Trade 2: Losing SHORT
        Trade(
            id=f"trade_2_{uuid.uuid4().hex[:8]}",
            symbol="TSLA",
            side=TradeSide.SHORT,
            size=50.0,
            entry_time=datetime(2024, 1, 7, 11, 0),
            entry_price=158.0,
            entry_reason="Overbought RSI near resistance",
            exit_time=datetime(2024, 1, 8, 15, 0),
            exit_price=160.5,
            exit_reason="Stop loss hit",
            stop_loss=160.5,
            take_profit=153.0,
            realized_pnl=-125.0,
            realized_pnl_pct=-1.58,
            commission=2.5,
            tags=["mean-reversion"]
        ),
        # Trade 3: Winning LONG
        Trade(
            id=f"trade_3_{uuid.uuid4().hex[:8]}",
            symbol="TSLA",
            side=TradeSide.LONG,
            size=75.0,
            entry_time=datetime(2024, 1, 10, 9, 30),
            entry_price=157.5,
            entry_reason="Support bounce + bullish divergence",
            exit_time=datetime(2024, 1, 13, 15, 0),
            exit_price=163.0,
            exit_reason="Profit target at key resistance",
            stop_loss=154.0,
            take_profit=163.5,
            realized_pnl=412.5,
            realized_pnl_pct=3.49,
            commission=2.5,
            tags=["support", "divergence"]
        )
    ]

    logger.info(f"Created {len(trades)} trades")

    # Generate equity curve
    equity_curve = []
    initial_capital = 25000.0
    equity = initial_capital

    for i in range(len(bars)):
        bar_time = bars[i].time

        # Apply trade P&L at exit times
        for trade in trades:
            if trade.exit_time and abs((bar_time - trade.exit_time).total_seconds()) < 3600:
                equity += trade.realized_pnl - trade.commission

        equity_curve.append(
            EquityPoint(time=bar_time, equity=equity)
        )

    logger.info(f"Created equity curve with {len(equity_curve)} points")

    # Calculate metrics
    final_equity = equity
    total_return = ((final_equity - initial_capital) / initial_capital) * 100

    metrics = BacktestMetrics(
        total_trades=3,
        winning_trades=2,
        losing_trades=1,
        win_rate=2/3,
        profit_factor=(275.0 + 412.5) / 125.0,
        expectancy=(275.0 + 412.5 - 125.0) / 3,
        max_drawdown_pct=0.5,
        max_drawdown_duration_days=1.5,
        sharpe_ratio=2.34,
        sortino_ratio=3.12,
        avg_r_multiple=4.2,
        best_r_multiple=6.8,
        worst_r_multiple=-0.5,
        avg_win=(275.0 + 412.5) / 2,
        avg_loss=-125.0,
        largest_win=412.5,
        largest_loss=-125.0,
        total_return_pct=total_return,
        annual_return_pct=total_return * 26,  # Annualized (2 weeks)
        avg_trade_duration_minutes=4800.0,
        max_consecutive_wins=2,
        max_consecutive_losses=1
    )

    # Create result
    result = BacktestResult(
        symbol="TSLA",
        timeframe="1H",
        mode="backtest",
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 14),
        initial_capital=initial_capital,
        final_capital=final_equity,
        bars=bars,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
        indicators={
            'EMA_20': [
                (base_date + timedelta(hours=i), 150.0 + i * 0.03)
                for i in range(len(bars))
            ],
            'EMA_50': [
                (base_date + timedelta(hours=i), 150.0 + i * 0.02)
                for i in range(len(bars))
            ]
        },
        strategy_name="Breakout + Mean Reversion Combo",
        strategy_params={
            "ema_fast": 20,
            "ema_slow": 50,
            "rsi_period": 14,
            "atr_period": 14,
            "risk_per_trade": 0.02
        },
        tags=["demo", "multi-strategy"],
        notes="Demo backtest for UI testing"
    )

    logger.info("Demo BacktestResult created successfully")
    return result


def main():
    """Run demo application."""
    logger.info("=" * 80)
    logger.info("BACKTEST CHART WIDGET DEMO")
    logger.info("=" * 80)

    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Backtest Chart Demo")

    # Create demo data
    logger.info("\nCreating demo backtest data...")
    result = create_demo_backtest_result()

    logger.info(f"\nDemo Data Summary:")
    logger.info(f"  Symbol: {result.symbol}")
    logger.info(f"  Timeframe: {result.timeframe}")
    logger.info(f"  Bars: {len(result.bars)}")
    logger.info(f"  Trades: {len(result.trades)}")
    logger.info(f"  Initial Capital: ${result.initial_capital:,.2f}")
    logger.info(f"  Final Capital: ${result.final_capital:,.2f}")
    logger.info(f"  Total P&L: ${result.total_pnl:,.2f} ({result.total_pnl_pct:.2f}%)")
    logger.info(f"  Win Rate: {result.metrics.win_rate:.1%}")

    # Create chart widget
    logger.info("\nCreating chart widget...")
    widget = BacktestChartWidget()
    widget.setWindowTitle(f"Backtest Chart - {result.symbol}")
    widget.resize(1200, 800)

    # Load backtest result
    logger.info("Loading backtest result into widget...")
    widget.load_backtest_result(result)

    # Show widget
    widget.show()

    logger.info("\n" + "=" * 80)
    logger.info("DEMO RUNNING - Close window to exit")
    logger.info("=" * 80)
    logger.info("\nFeatures to test:")
    logger.info("  - Chart displays (placeholder for now, full JS in Phase 3.3)")
    logger.info("  - Toolbar shows symbol and metrics")
    logger.info("  - 'Hide/Show Markers' button toggles trade markers")
    logger.info("  - 'Clear Chart' button clears the chart")
    logger.info("  - WebChannel bridge is active and ready for JS integration")

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Demo failed: {e}")
        sys.exit(1)
