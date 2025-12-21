"""Backtrader Strategy Wrapper.

Contains OrderPilotStrategy - a Backtrader strategy that wraps
our OrderPilot strategy implementations.
"""

import logging
import warnings

import pandas as pd

# Try importing backtrader
try:
    import backtrader as bt
    BACKTRADER_AVAILABLE = True
except ImportError:
    BACKTRADER_AVAILABLE = False
    warnings.warn("Backtrader not installed. Backtesting will be unavailable.")
    bt = None

from src.core.indicators.engine import IndicatorEngine
from src.core.strategy.engine import Signal, SignalType

logger = logging.getLogger(__name__)


if BACKTRADER_AVAILABLE:
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

else:
    # Stub class when backtrader is not available
    class OrderPilotStrategy:
        """Stub class when backtrader is not installed."""
        def __init__(self, *args, **kwargs):
            raise ImportError("Backtrader not installed. Run: pip install backtrader")
