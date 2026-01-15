"""Backtrader Integration for Backtesting.

Provides comprehensive backtesting using the Backtrader framework,
integrated with our strategy engine and AI components.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- backtrader_types.py: BacktestConfig, BacktestResultLegacy
- backtrader_strategy.py: OrderPilotStrategy
- backtrader_integration.py: BacktestEngine (this file)
"""

import logging
import warnings
from datetime import datetime
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

from .backtrader_strategy import OrderPilotStrategy
from .backtrader_types import BacktestConfig, BacktestResultLegacy
from .result_converter import backtrader_to_backtest_result

# Re-export for backward compatibility
__all__ = [
    "BacktestConfig",
    "BacktestResultLegacy",
    "OrderPilotStrategy",
    "BacktestEngine",
    "BACKTRADER_AVAILABLE",
]

logger = logging.getLogger(__name__)


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
        """Get data feed for symbol."""
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
        """Process backtest results using comprehensive BacktestResult model."""
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
        """Run backtest with StrategyDefinition (YAML/JSON strategy)."""
        logger.info(
            f"Running backtest with strategy: {strategy_def.name} v{strategy_def.version}"
        )

        strategy_class = self._compile_strategy(strategy_def)
        cerebro = self._build_cerebro(initial_cash, commission)
        await self._add_backtest_data(cerebro, symbol, start_date, end_date, timeframe, data_feed)
        cerebro.addstrategy(strategy_class)
        self._add_backtest_analyzers(cerebro)

        logger.info(f"Starting backtest from {start_date} to {end_date}")
        initial_value = cerebro.broker.getvalue()
        strategy_instance = cerebro.run()[0]
        final_value = cerebro.broker.getvalue()

        timeframe_str = timeframe.value if timeframe else "1d"
        result = self._convert_backtest_result(
            strategy_def,
            strategy_instance,
            cerebro,
            initial_value,
            final_value,
            symbol,
            timeframe_str,
            start_date,
            end_date,
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

    def _compile_strategy(self, strategy_def: StrategyDefinition):
        compiler = StrategyCompiler()
        return compiler.compile(strategy_def)

    def _build_cerebro(self, initial_cash: float, commission: float):
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=commission)
        return cerebro

    async def _add_backtest_data(
        self,
        cerebro: bt.Cerebro,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe,
        data_feed: bt.feeds.DataBase | None,
    ) -> None:
        if data_feed is not None:
            cerebro.adddata(data_feed, name=symbol)
            return
        if not self.history_manager:
            raise ValueError("HistoryManager required when data_feed is not provided")
        data = await self._get_data_feed(symbol, start_date, end_date, timeframe)
        if not data:
            raise ValueError(f"No data available for {symbol}")
        cerebro.adddata(data, name=symbol)

    def _add_backtest_analyzers(self, cerebro: bt.Cerebro) -> None:
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(btanalyzers.Returns, _name='returns')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(btanalyzers.TimeReturn, _name='timereturn')

    def _convert_backtest_result(
        self,
        strategy_def: StrategyDefinition,
        strategy_instance,
        cerebro: bt.Cerebro,
        initial_value: float,
        final_value: float,
        symbol: str,
        timeframe_str: str,
        start_date: datetime,
        end_date: datetime,
    ) -> BacktestResult:
        try:
            return backtrader_to_backtest_result(
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
                    "risk_management": strategy_def.risk_management.model_dump(exclude_none=True),
                },
            )
        except Exception as e:
            logger.error(f"Error converting backtest results: {e}")
            from src.core.models.backtest_models import BacktestMetrics, EquityPoint

            return BacktestResult(
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
                    EquityPoint(time=end_date, equity=final_value),
                ],
                metrics=BacktestMetrics(),
                strategy_name=f"{strategy_def.name} v{strategy_def.version}",
                strategy_params={},
                notes=f"Error during conversion: {e}",
            )

    async def optimize_strategy(
        self,
        config: BacktestConfig
    ) -> list[tuple[dict[str, Any], BacktestResult]]:
        """Optimize strategy parameters."""
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
        """Generate parameter combinations for optimization."""
        import itertools

        keys = list(optimize_params.keys())
        values = list(optimize_params.values())

        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))

        return combinations

    def plot_results(self, result: BacktestResult, show: bool = True):
        """Plot backtest results."""
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
