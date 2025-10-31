"""Backtrader Integration for Backtesting.

Provides comprehensive backtesting using the Backtrader framework,
integrated with our strategy engine and AI components.
"""

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

# Try importing backtrader
try:
    import backtrader as bt
    import backtrader.analyzers as btanalyzers
    import backtrader.feeds as btfeeds
    BACKTRADER_AVAILABLE = True
except ImportError:
    BACKTRADER_AVAILABLE = False
    warnings.warn("Backtrader not installed. Backtesting will be unavailable.")
    bt = None

from src.common.event_bus import Event, EventType, event_bus
from src.core.indicators.engine import IndicatorEngine
from src.core.market_data.history_provider import DataRequest, HistoryManager, Timeframe
from src.core.strategy.engine import Signal, SignalType, StrategyConfig

logger = logging.getLogger(__name__)


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
class BacktestResult:
    """Results from backtesting."""
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


class OrderPilotStrategy(bt.Strategy):
    """Backtrader strategy wrapper for OrderPilot strategies."""

    params = (
        ('strategy_config', None),
        ('indicator_engine', None),
        ('ai_enabled', False),
        ('verbose', False)
    )

    def __init__(self):
        """Initialize strategy."""
        if not self.params.strategy_config:
            raise ValueError("Strategy config required")

        # Initialize our strategy
        from ..strategy.engine import (
            BreakoutStrategy,
            MeanReversionStrategy,
            MomentumStrategy,
            ScalpingStrategy,
            StrategyType,
            TrendFollowingStrategy,
        )

        strategy_map = {
            StrategyType.TREND_FOLLOWING: TrendFollowingStrategy,
            StrategyType.MEAN_REVERSION: MeanReversionStrategy,
            StrategyType.MOMENTUM: MomentumStrategy,
            StrategyType.BREAKOUT: BreakoutStrategy,
            StrategyType.SCALPING: ScalpingStrategy
        }

        strategy_class = strategy_map.get(self.params.strategy_config.strategy_type)
        if not strategy_class:
            raise ValueError(f"Unsupported strategy type: {self.params.strategy_config.strategy_type}")

        self.orderpilot_strategy = strategy_class(
            self.params.strategy_config,
            self.params.indicator_engine or IndicatorEngine()
        )

        # Track orders and positions
        self.order = None
        self.buy_price = None
        self.buy_comm = None

        # Performance tracking
        self.trades = []
        self.signals = []

        if self.params.verbose:
            logger.info(f"Initialized {self.params.strategy_config.name} strategy")

    def notify_order(self, order):
        """Handle order notifications."""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm

                if self.params.verbose:
                    self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                            f'Cost: {order.executed.value:.2f}, '
                            f'Comm: {order.executed.comm:.2f}')

            else:  # Sell
                if self.params.verbose:
                    self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                            f'Cost: {order.executed.value:.2f}, '
                            f'Comm: {order.executed.comm:.2f}')

                # Calculate profit
                if self.buy_price:
                    profit = (order.executed.price - self.buy_price) * order.executed.size
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100

                    self.trades.append({
                        'entry_date': self.buy_bar,
                        'entry_price': self.buy_price,
                        'exit_date': self.datetime.date(),
                        'exit_price': order.executed.price,
                        'profit': profit,
                        'profit_pct': profit_pct,
                        'commission': self.buy_comm + order.executed.comm
                    })

                    self.buy_price = None
                    self.buy_comm = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if self.params.verbose:
                self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        """Handle trade notifications."""
        if not trade.isclosed:
            return

        if self.params.verbose:
            self.log(f'TRADE PROFIT, GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}')

    async def next(self):
        """Process next bar - async version."""
        # Convert Backtrader data to DataFrame for our strategy
        df = self._get_dataframe()

        if df is None or len(df) < 50:
            return

        # Evaluate our strategy
        signal = await self.orderpilot_strategy.evaluate(df)

        if signal:
            self.signals.append(signal)
            self._execute_signal(signal)

    def _get_dataframe(self) -> pd.DataFrame | None:
        """Convert Backtrader data to DataFrame."""
        try:
            # Get historical data
            data_len = min(200, len(self.data))
            if data_len < 20:
                return None

            dates = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []

            for i in range(-data_len, 0):
                dates.append(self.data.datetime.date(i))
                opens.append(self.data.open[i])
                highs.append(self.data.high[i])
                lows.append(self.data.low[i])
                closes.append(self.data.close[i])
                volumes.append(self.data.volume[i])

            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes
            }, index=dates)

            return df

        except Exception as e:
            logger.error(f"Error converting data: {e}")
            return None

    def _execute_signal(self, signal: Signal):
        """Execute trading signal."""
        # Check for pending orders
        if self.order:
            return

        # Get current position
        position = self.position

        if signal.signal_type == SignalType.BUY and position == 0:
            # Calculate position size
            size = self._calculate_size(signal)

            if size > 0:
                self.order = self.buy(size=size)
                self.buy_bar = self.datetime.date()

                if self.params.verbose:
                    self.log(f'BUY CREATE, Size: {size}, Price: {self.data.close[0]:.2f}')

        elif signal.signal_type in [SignalType.SELL, SignalType.CLOSE_LONG] and position > 0:
            self.order = self.sell(size=position)

            if self.params.verbose:
                self.log(f'SELL CREATE, Size: {position}, Price: {self.data.close[0]:.2f}')

    def _calculate_size(self, signal: Signal) -> int:
        """Calculate position size."""
        # Get available cash
        cash = self.broker.getcash()
        price = self.data.close[0]

        # Risk management - limit position to percentage of portfolio
        max_position_value = cash * 0.2  # Max 20% per position
        max_shares = int(max_position_value / price)

        # Use signal confidence for sizing
        target_shares = int(max_shares * signal.confidence)

        return max(0, min(target_shares, max_shares))

    def log(self, txt, dt=None):
        """Logging function."""
        dt = dt or self.datetime.date()
        logger.debug(f'{dt.isoformat()}: {txt}')


class BacktestEngine:
    """Engine for running backtests with Backtrader."""

    def __init__(self, history_manager: HistoryManager | None = None):
        """Initialize backtest engine.

        Args:
            history_manager: Historical data manager
        """
        if not BACKTRADER_AVAILABLE:
            raise ImportError("Backtrader not installed. Run: pip install backtrader")

        self.history_manager = history_manager or HistoryManager()
        self.indicator_engine = IndicatorEngine()

        logger.info("Backtest engine initialized")

    async def run_backtest(
        self,
        config: BacktestConfig
    ) -> BacktestResult:
        """Run a backtest.

        Args:
            config: Backtest configuration

        Returns:
            Backtest results
        """
        # Create Cerebro engine
        cerebro = bt.Cerebro()

        # Set initial cash
        cerebro.broker.setcash(float(config.initial_cash))

        # Set commission
        cerebro.broker.setcommission(commission=config.commission)

        # Add data feeds
        for symbol in config.symbols:
            data = await self._get_data_feed(
                symbol,
                config.start_date,
                config.end_date,
                config.timeframe
            )

            if data:
                cerebro.adddata(data, name=symbol)

        # Add strategies
        for strategy_config in config.strategies:
            cerebro.addstrategy(
                OrderPilotStrategy,
                strategy_config=strategy_config,
                indicator_engine=self.indicator_engine,
                ai_enabled=False,  # Disable AI for backtesting
                verbose=False
            )

        # Add analyzers
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(btanalyzers.Returns, _name='returns')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(btanalyzers.TimeReturn, _name='timereturn')

        # Run backtest
        logger.info(f"Starting backtest from {config.start_date} to {config.end_date}")
        initial_value = cerebro.broker.getvalue()

        results = cerebro.run()

        final_value = cerebro.broker.getvalue()

        # Process results
        return self._process_results(
            results[0],
            initial_value,
            final_value,
            config
        )

    async def _get_data_feed(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> bt.feeds.PandasData | None:
        """Get data feed for symbol.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe

        Returns:
            Backtrader data feed or None
        """
        # Fetch historical data
        request = DataRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )

        bars, source = await self.history_manager.fetch_data(request)

        if not bars:
            logger.error(f"No data available for {symbol}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame([{
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': bar.volume
        } for bar in bars])

        df.index = pd.DatetimeIndex([bar.timestamp for bar in bars])

        # Create Backtrader data feed
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )

        logger.info(f"Loaded {len(df)} bars for {symbol} from {source}")

        return data

    def _process_results(
        self,
        strategy,
        initial_value: float,
        final_value: float,
        config: BacktestConfig
    ) -> BacktestResult:
        """Process backtest results.

        Args:
            strategy: Backtrader strategy instance
            initial_value: Initial portfolio value
            final_value: Final portfolio value
            config: Backtest configuration

        Returns:
            Processed results
        """
        # Get analyzers
        sharpe = strategy.analyzers.sharpe.get_analysis()
        returns = strategy.analyzers.returns.get_analysis()
        drawdown = strategy.analyzers.drawdown.get_analysis()
        trades_analysis = strategy.analyzers.trades.get_analysis()
        timereturn = strategy.analyzers.timereturn.get_analysis()

        # Calculate metrics
        total_return = (final_value - initial_value) / initial_value

        # Annualized return
        days = (config.end_date - config.start_date).days
        years = days / 365.25
        annual_return = (final_value / initial_value) ** (1/years) - 1 if years > 0 else 0

        # Trade statistics
        total_trades = trades_analysis.get('total', {}).get('total', 0)
        won_trades = trades_analysis.get('won', {}).get('total', 0)
        lost_trades = trades_analysis.get('lost', {}).get('total', 0)

        win_rate = won_trades / total_trades if total_trades > 0 else 0

        # Profit factor
        gross_profit = trades_analysis.get('won', {}).get('pnl', {}).get('total', 0)
        gross_loss = abs(trades_analysis.get('lost', {}).get('pnl', {}).get('total', 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Average trade
        avg_trade_return = returns.get('ravg', 0)

        # Best/worst trades
        best_trade = trades_analysis.get('won', {}).get('pnl', {}).get('max', 0)
        worst_trade = trades_analysis.get('lost', {}).get('pnl', {}).get('max', 0)

        # Build equity curve
        equity_curve = pd.DataFrame(list(timereturn.items()), columns=['date', 'return'])
        equity_curve['cumulative'] = (1 + equity_curve['return']).cumprod()
        equity_curve.set_index('date', inplace=True)

        # Get trades from strategy
        trades = strategy.trades if hasattr(strategy, 'trades') else []

        result = BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe.get('sharperatio', 0),
            max_drawdown=drawdown.get('max', {}).get('drawdown', 0),
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=won_trades,
            losing_trades=lost_trades,
            avg_trade_return=avg_trade_return,
            best_trade=best_trade,
            worst_trade=worst_trade,
            final_value=Decimal(str(final_value)),
            trades=trades,
            equity_curve=equity_curve,
            metadata={
                'initial_value': initial_value,
                'days': days,
                'source': 'backtrader'
            }
        )

        # Emit event
        event_bus.emit(Event(
            type=EventType.BACKTEST_COMPLETE,
            timestamp=datetime.utcnow(),
            data={
                'total_return': total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'total_trades': total_trades
            }
        ))

        logger.info(f"Backtest complete: Return={total_return:.2%}, "
                   f"Sharpe={result.sharpe_ratio:.2f}, "
                   f"MaxDD={result.max_drawdown:.2%}, "
                   f"Trades={total_trades}")

        return result

    async def optimize_strategy(
        self,
        config: BacktestConfig
    ) -> list[tuple[dict[str, Any], BacktestResult]]:
        """Optimize strategy parameters.

        Args:
            config: Backtest configuration with optimize_params

        Returns:
            List of (params, results) tuples sorted by Sharpe ratio
        """
        if not config.optimize_params:
            raise ValueError("optimize_params required for optimization")

        results = []

        # Generate parameter combinations
        param_combinations = self._generate_param_combinations(config.optimize_params)

        logger.info(f"Running {len(param_combinations)} parameter combinations")

        for params in param_combinations:
            # Update strategy config with params
            strategy_config = config.strategies[0]
            for key, value in params.items():
                if key in strategy_config.parameters:
                    strategy_config.parameters[key] = value

            # Run backtest
            try:
                result = await self.run_backtest(config)
                results.append((params, result))

                logger.info(f"Params {params}: Sharpe={result.sharpe_ratio:.2f}")

            except Exception as e:
                logger.error(f"Error with params {params}: {e}")

        # Sort by Sharpe ratio
        results.sort(key=lambda x: x[1].sharpe_ratio, reverse=True)

        # Log best parameters
        if results:
            best_params, best_result = results[0]
            logger.info(f"Best parameters: {best_params}")
            logger.info(f"Best Sharpe: {best_result.sharpe_ratio:.2f}")

        return results

    def _generate_param_combinations(
        self,
        optimize_params: dict[str, list[Any]]
    ) -> list[dict[str, Any]]:
        """Generate parameter combinations for optimization.

        Args:
            optimize_params: Parameter ranges

        Returns:
            List of parameter combinations
        """
        import itertools

        keys = list(optimize_params.keys())
        values = list(optimize_params.values())

        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))

        return combinations

    def plot_results(self, result: BacktestResult, show: bool = True):
        """Plot backtest results.

        Args:
            result: Backtest results
            show: Whether to show plot
        """
        try:
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(3, 1, figsize=(12, 10))

            # Equity curve
            ax1 = axes[0]
            ax1.plot(result.equity_curve.index,
                    result.equity_curve['cumulative'],
                    label='Strategy')
            ax1.set_title('Equity Curve')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Cumulative Return')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Drawdown
            ax2 = axes[1]
            cumulative = result.equity_curve['cumulative']
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            ax2.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
            ax2.set_title('Drawdown')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Drawdown %')
            ax2.grid(True, alpha=0.3)

            # Returns distribution
            ax3 = axes[2]
            returns = result.equity_curve['return'].dropna()
            ax3.hist(returns, bins=50, alpha=0.7, color='blue')
            ax3.set_title('Returns Distribution')
            ax3.set_xlabel('Daily Return')
            ax3.set_ylabel('Frequency')
            ax3.grid(True, alpha=0.3)

            # Add statistics text
            stats_text = (
                f"Total Return: {result.total_return:.2%}\n"
                f"Annual Return: {result.annual_return:.2%}\n"
                f"Sharpe Ratio: {result.sharpe_ratio:.2f}\n"
                f"Max Drawdown: {result.max_drawdown:.2%}\n"
                f"Win Rate: {result.win_rate:.2%}\n"
                f"Total Trades: {result.total_trades}"
            )

            fig.text(0.15, 0.02, stats_text, fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3))

            plt.tight_layout()

            if show:
                plt.show()

            return fig

        except ImportError:
            logger.warning("Matplotlib not installed. Cannot plot results.")
            return None