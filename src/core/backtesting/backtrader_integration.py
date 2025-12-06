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
    BACKTRADER_AVAILABLE = True
except ImportError:
    BACKTRADER_AVAILABLE = False
    warnings.warn("Backtrader not installed. Backtesting will be unavailable.")
    bt = None

from src.common.event_bus import Event, EventType, event_bus
from src.core.indicators.engine import IndicatorEngine
from src.core.market_data.history_provider import DataRequest, HistoryManager, Timeframe
from src.core.models.backtest_models import BacktestResult
from src.core.strategy.compiler import StrategyCompiler
from src.core.strategy.definition import StrategyDefinition
from src.core.strategy.engine import Signal, SignalType, StrategyConfig

from .result_converter import backtrader_to_backtest_result

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
            history_manager: Historical data manager (optional, only needed if fetching from data sources)
        """
        if not BACKTRADER_AVAILABLE:
            raise ImportError("Backtrader not installed. Run: pip install backtrader")

        self.history_manager = history_manager  # Can be None if using custom data feeds
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

        # Process results with new comprehensive model
        return self._process_results(
            strategy=results[0],
            initial_value=initial_value,
            final_value=final_value,
            config=config,
            cerebro=cerebro
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
        config: BacktestConfig,
        cerebro=None
    ) -> BacktestResult:
        """Process backtest results using comprehensive BacktestResult model.

        Args:
            strategy: Backtrader strategy instance
            initial_value: Initial portfolio value
            final_value: Final portfolio value
            config: Backtest configuration
            cerebro: Optional Backtrader Cerebro instance

        Returns:
            Comprehensive BacktestResult
        """
        # Determine symbol and timeframe
        symbol = config.symbols[0] if config.symbols else "UNKNOWN"
        timeframe_str = config.timeframe.value if config.timeframe else "1min"

        # Get strategy name and params
        strategy_name = None
        strategy_params = {}
        if config.strategies:
            strategy_config = config.strategies[0]
            strategy_name = strategy_config.name
            strategy_params = strategy_config.parameters

        # Use converter to create comprehensive result
        try:
            result = backtrader_to_backtest_result(
                strategy=strategy,
                cerebro=cerebro,
                initial_value=initial_value,
                final_value=final_value,
                symbol=symbol,
                timeframe=timeframe_str,
                start_date=config.start_date,
                end_date=config.end_date,
                strategy_name=strategy_name,
                strategy_params=strategy_params
            )
        except Exception as e:
            logger.error(f"Error converting backtest results: {e}")
            # Fallback to basic result if conversion fails
            from src.core.models.backtest_models import BacktestMetrics, EquityPoint

            result = BacktestResult(
                symbol=symbol,
                timeframe=timeframe_str,
                mode="backtest",
                start=config.start_date,
                end=config.end_date,
                initial_capital=initial_value,
                final_capital=final_value,
                bars=[],
                trades=[],
                equity_curve=[
                    EquityPoint(time=config.start_date, equity=initial_value),
                    EquityPoint(time=config.end_date, equity=final_value)
                ],
                metrics=BacktestMetrics(),
                strategy_name=strategy_name or "Unknown",
                strategy_params=strategy_params,
                notes=f"Error during conversion: {e}"
            )

        # Emit event
        event_bus.emit(Event(
            type=EventType.BACKTEST_COMPLETE,
            timestamp=datetime.utcnow(),
            data={
                'symbol': result.symbol,
                'total_return_pct': result.metrics.total_return_pct,
                'sharpe_ratio': result.metrics.sharpe_ratio,
                'max_drawdown_pct': result.metrics.max_drawdown_pct,
                'total_trades': result.metrics.total_trades,
                'win_rate': result.metrics.win_rate
            }
        ))

        logger.info(
            f"Backtest complete for {symbol}: "
            f"Return={result.metrics.total_return_pct:.2f}%, "
            f"Sharpe={result.metrics.sharpe_ratio or 0:.2f}, "
            f"MaxDD={result.metrics.max_drawdown_pct:.2f}%, "
            f"Trades={result.metrics.total_trades}, "
            f"WinRate={result.metrics.win_rate:.2%}"
        )

        return result

    async def run_backtest_with_definition(
        self,
        strategy_def: StrategyDefinition,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_cash: float = 10000.0,
        commission: float = 0.001,
        timeframe: Timeframe = Timeframe.DAY_1,
        data_feed: bt.feeds.DataBase | None = None
    ) -> BacktestResult:
        """Run backtest with StrategyDefinition (YAML/JSON strategy).

        This method compiles a declarative strategy definition into a Backtrader
        strategy and runs a backtest with it.

        Args:
            strategy_def: Strategy definition (loaded from YAML/JSON)
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_cash: Starting capital
            commission: Commission rate (default 0.1%)
            timeframe: Data timeframe
            data_feed: Optional custom data feed (if None, fetches from history manager)

        Returns:
            Comprehensive backtest results

        Example:
            >>> from src.core.strategy.definition import StrategyDefinition
            >>> strategy_def = StrategyDefinition.from_yaml(yaml_content)
            >>> result = await engine.run_backtest_with_definition(
            ...     strategy_def=strategy_def,
            ...     symbol="AAPL",
            ...     start_date=datetime(2023, 1, 1),
            ...     end_date=datetime(2023, 12, 31)
            ... )
        """
        logger.info(
            f"Running backtest with strategy: {strategy_def.name} v{strategy_def.version}"
        )

        # Compile strategy
        compiler = StrategyCompiler()
        strategy_class = compiler.compile(strategy_def)

        # Create Cerebro engine
        cerebro = bt.Cerebro()

        # Set initial cash
        cerebro.broker.setcash(initial_cash)

        # Set commission
        cerebro.broker.setcommission(commission=commission)

        # Add data feed
        if data_feed is not None:
            cerebro.adddata(data_feed, name=symbol)
        else:
            # Fetch data from history manager
            if not self.history_manager:
                raise ValueError("HistoryManager required when data_feed is not provided")
            data = await self._get_data_feed(symbol, start_date, end_date, timeframe)
            if not data:
                raise ValueError(f"No data available for {symbol}")
            cerebro.adddata(data, name=symbol)

        # Add compiled strategy
        cerebro.addstrategy(strategy_class)

        # Add analyzers
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(btanalyzers.Returns, _name='returns')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(btanalyzers.TimeReturn, _name='timereturn')

        # Run backtest
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        initial_value = cerebro.broker.getvalue()

        results = cerebro.run()
        strategy_instance = results[0]

        final_value = cerebro.broker.getvalue()

        # Process results
        timeframe_str = timeframe.value if timeframe else "1d"

        try:
            result = backtrader_to_backtest_result(
                strategy=strategy_instance,
                cerebro=cerebro,
                initial_value=initial_value,
                final_value=final_value,
                symbol=symbol,
                timeframe=timeframe_str,
                start_date=start_date,
                end_date=end_date,
                strategy_name=f"{strategy_def.name} v{strategy_def.version}",
                strategy_params={
                    "indicators": [
                        {"type": ind.type, "alias": ind.alias, "params": ind.params}
                        for ind in strategy_def.indicators
                    ],
                    "risk_management": strategy_def.risk_management.model_dump(exclude_none=True)
                }
            )
        except Exception as e:
            logger.error(f"Error converting backtest results: {e}")
            # Fallback to basic result
            from src.core.models.backtest_models import BacktestMetrics, EquityPoint

            result = BacktestResult(
                symbol=symbol,
                timeframe=timeframe_str,
                mode="backtest",
                start=start_date,
                end=end_date,
                initial_capital=initial_value,
                final_capital=final_value,
                bars=[],
                trades=[],
                equity_curve=[
                    EquityPoint(time=start_date, equity=initial_value),
                    EquityPoint(time=end_date, equity=final_value)
                ],
                metrics=BacktestMetrics(),
                strategy_name=f"{strategy_def.name} v{strategy_def.version}",
                strategy_params={},
                notes=f"Error during conversion: {e}"
            )

        # Emit event
        event_bus.emit(Event(
            type=EventType.BACKTEST_COMPLETE,
            timestamp=datetime.utcnow(),
            data={
                'symbol': result.symbol,
                'strategy': strategy_def.name,
                'total_return_pct': result.metrics.total_return_pct,
                'sharpe_ratio': result.metrics.sharpe_ratio,
                'max_drawdown_pct': result.metrics.max_drawdown_pct,
                'total_trades': result.metrics.total_trades,
                'win_rate': result.metrics.win_rate
            }
        ))

        logger.info(
            f"Backtest complete for {symbol} with {strategy_def.name}: "
            f"Return={result.metrics.total_return_pct:.2f}%, "
            f"Sharpe={result.metrics.sharpe_ratio or 0:.2f}, "
            f"MaxDD={result.metrics.max_drawdown_pct:.2f}%, "
            f"Trades={result.metrics.total_trades}, "
            f"WinRate={result.metrics.win_rate:.2%}"
        )

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
            result: Backtest results (new comprehensive model)
            show: Whether to show plot
        """
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(3, 1, figsize=(12, 10))

            # Convert equity curve to pandas for plotting
            if result.equity_curve:
                equity_df = pd.DataFrame([
                    {'date': point.time, 'equity': point.equity}
                    for point in result.equity_curve
                ])
                equity_df.set_index('date', inplace=True)
                equity_df['cumulative'] = equity_df['equity'] / result.initial_capital

                # Equity curve
                ax1 = axes[0]
                ax1.plot(equity_df.index, equity_df['cumulative'], label='Strategy')
                ax1.set_title('Equity Curve')
                ax1.set_xlabel('Date')
                ax1.set_ylabel('Cumulative Return')
                ax1.legend()
                ax1.grid(True, alpha=0.3)

                # Drawdown
                ax2 = axes[1]
                cumulative = equity_df['cumulative']
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                ax2.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
                ax2.set_title('Drawdown')
                ax2.set_xlabel('Date')
                ax2.set_ylabel('Drawdown %')
                ax2.grid(True, alpha=0.3)

                # Returns distribution
                ax3 = axes[2]
                returns = equity_df['cumulative'].pct_change().dropna()
                ax3.hist(returns, bins=50, alpha=0.7, color='blue')
                ax3.set_title('Returns Distribution')
                ax3.set_xlabel('Daily Return')
                ax3.set_ylabel('Frequency')
                ax3.grid(True, alpha=0.3)
            else:
                # No equity curve available
                for ax in axes:
                    ax.text(0.5, 0.5, 'No equity data available',
                           ha='center', va='center', transform=ax.transAxes)

            # Add statistics text
            m = result.metrics
            stats_text = (
                f"Total Return: {m.total_return_pct:.2f}%\n"
                f"Annual Return: {m.annual_return_pct or 0:.2f}%\n"
                f"Sharpe Ratio: {m.sharpe_ratio or 0:.2f}\n"
                f"Max Drawdown: {m.max_drawdown_pct:.2f}%\n"
                f"Win Rate: {m.win_rate:.2%}\n"
                f"Total Trades: {m.total_trades}"
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