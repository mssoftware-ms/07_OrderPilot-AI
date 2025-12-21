"""Backtest Harness for Tradingbot.

Main backtesting class that provides:
- Deterministic backtesting
- Multi-timeframe data support
- Event-by-event simulation
- Comprehensive metrics collection

REFACTORED: Split into multiple files to meet 600 LOC limit.
- backtest_types.py: Data types (BacktestMode, BacktestConfig, etc.)
- backtest_simulator.py: BacktestSimulator + ReleaseGate
- backtest_harness.py: BacktestHarness main class (this file)
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator

import pandas as pd

from .backtest_simulator import BacktestSimulator
from .backtest_types import (
    BacktestMode,
    BacktestConfig,
    BacktestTrade,
    BacktestState,
    BacktestResult,
)
from .config import FullBotConfig, MarketType, TrailingMode, KIMode
from .execution import OrderResult, OrderStatus, PositionSizeResult
from .models import (
    BotDecision,
    FeatureVector,
    PositionState,
    RegimeState,
    Signal,
    TradeSide,
)
from .backtest_metrics_helpers import calculate_backtest_metrics
from .strategy_evaluator import PerformanceMetrics

if TYPE_CHECKING:
    from .bot_controller import BotController

logger = logging.getLogger(__name__)

class BacktestHarness:
    """Main backtest harness for tradingbot.

    Runs event-by-event backtests with full bot simulation.
    """

    def __init__(
        self,
        bot_config: FullBotConfig,
        backtest_config: BacktestConfig,
        data_provider: Callable[[str, datetime, datetime, str], pd.DataFrame] | None = None
    ):
        """Initialize backtest harness.

        Args:
            bot_config: Bot configuration
            backtest_config: Backtest configuration
            data_provider: Function to fetch historical data
        """
        self.bot_config = bot_config
        self.backtest_config = backtest_config
        self._data_provider = data_provider

        # Initialize components
        self._seed = backtest_config.get_seed()
        self._simulator = BacktestSimulator(
            slippage_pct=backtest_config.slippage_pct,
            commission_pct=backtest_config.commission_pct,
            seed=self._seed
        )

        self._state = BacktestState(capital=backtest_config.initial_capital)
        self._data: pd.DataFrame | None = None

        # Bot components (lazy initialized)
        self._feature_engine = None
        self._regime_engine = None
        self._entry_scorer = None
        self._exit_checker = None
        self._trailing_manager = None
        self._no_trade_filter = None
        self._strategy_selector = None

        logger.info(
            f"BacktestHarness initialized: {backtest_config.symbol} "
            f"from {backtest_config.start_date} to {backtest_config.end_date}, "
            f"seed={self._seed}"
        )

    def _init_bot_components(self) -> None:
        """Initialize bot components."""
        from .feature_engine import FeatureEngine
        from .regime_engine import RegimeEngine
        from .entry_exit_engine import EntryScorer, ExitSignalChecker, TrailingStopManager
        from .no_trade_filter import NoTradeFilter
        from .strategy_selector import StrategySelector

        self._feature_engine = FeatureEngine()
        self._regime_engine = RegimeEngine()
        self._entry_scorer = EntryScorer()
        self._exit_checker = ExitSignalChecker()
        self._trailing_manager = TrailingStopManager(
            activation_pct=self.bot_config.risk.trailing_activation_pct
        )
        self._no_trade_filter = NoTradeFilter(self.bot_config.risk)
        self._strategy_selector = StrategySelector()

    def load_data(self) -> pd.DataFrame:
        """Load historical data for backtest.

        Returns:
            DataFrame with OHLCV data
        """
        if self._data_provider:
            self._data = self._data_provider(
                self.backtest_config.symbol,
                self.backtest_config.start_date,
                self.backtest_config.end_date,
                self.backtest_config.timeframe
            )
        else:
            # Try to load from default provider
            try:
                from src.core.market_data.history_provider import HistoryManager
                from src.core.market_data.types import DataRequest, Timeframe, AssetClass

                manager = HistoryManager()
                request = DataRequest(
                    symbol=self.backtest_config.symbol,
                    start_date=self.backtest_config.start_date,
                    end_date=self.backtest_config.end_date,
                    timeframe=Timeframe.MINUTE_1,
                    asset_class=AssetClass.STOCK
                )
                self._data = manager.fetch_data(request)
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
                raise ValueError(f"No data provider and default load failed: {e}")

        if self._data is None or self._data.empty:
            raise ValueError("No data loaded for backtest")

        logger.info(f"Loaded {len(self._data)} bars for backtest")
        return self._data

    def run(self) -> BacktestResult:
        """Run the backtest.

        Returns:
            BacktestResult with all metrics and trades
        """
        start_time = datetime.utcnow()

        # Initialize
        self._init_bot_components()
        if self._data is None:
            self.load_data()

        # Reset state
        self._state = BacktestState(capital=self.backtest_config.initial_capital)

        # Run simulation
        total_bars = len(self._data)
        logger.info(f"Starting backtest: {total_bars} bars")

        for bar_idx, (timestamp, row) in enumerate(self._data.iterrows()):
            self._state.bar_index = bar_idx
            self._state.current_time = timestamp
            self._state.current_bar = {
                "timestamp": timestamp,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row.get("volume", 0),
            }

            # Skip warmup period
            if bar_idx < self.backtest_config.warmup_bars:
                continue

            # Process bar
            self._process_bar(bar_idx)

            # Record equity
            equity = self._calculate_equity()
            self._state.equity_curve.append((timestamp, equity))

        # Close any open position at end
        if self._state.position and self._state.position.is_open:
            self._close_position("END_OF_BACKTEST")

        # Calculate metrics
        run_time = (datetime.utcnow() - start_time).total_seconds()
        metrics = self._calculate_metrics()

        result = BacktestResult(
            config=self.backtest_config,
            metrics=metrics,
            trades=self._state.trades,
            equity_curve=self._state.equity_curve,
            run_time_seconds=run_time,
            total_bars=total_bars,
            seed_used=self._seed,
            total_trades=len(self._state.trades),
            winning_trades=sum(1 for t in self._state.trades if t.pnl > 0),
            losing_trades=sum(1 for t in self._state.trades if t.pnl <= 0),
            total_pnl=sum(t.pnl for t in self._state.trades),
            total_fees=sum(t.fees for t in self._state.trades),
            max_drawdown_pct=metrics.max_drawdown_pct,
            final_capital=self._calculate_equity()
        )

        logger.info(
            f"Backtest complete: {result.total_trades} trades, "
            f"PnL=${result.total_pnl:.2f}, "
            f"WinRate={metrics.win_rate:.1%}, "
            f"PF={metrics.profit_factor:.2f}"
        )

        # Save if configured
        if self.backtest_config.output_dir:
            output_path = (
                self.backtest_config.output_dir /
                f"backtest_{self.backtest_config.symbol}_{self._seed}.json"
            )
            result.save(output_path)

        return result

    def _process_bar(self, bar_idx: int) -> None:
        """Process a single bar.

        Args:
            bar_idx: Bar index in data
        """
        # Calculate features
        data_slice = self._data.iloc[:bar_idx + 1]
        features = self._feature_engine.calculate_features(
            data_slice,
            self.backtest_config.symbol,
            self._state.current_time
        )

        if features is None:
            return

        self._state.features = features

        # Classify regime
        regime = self._regime_engine.classify(features)
        self._state.regime = regime

        # Check no-trade filter
        filter_result = self._no_trade_filter.check(
            features, regime, self._state.current_time
        )

        # State-dependent processing
        if self._state.position and self._state.position.is_open:
            self._process_manage_state(features, regime)
        elif self._state.pending_signal:
            self._process_signal_state(features, regime, filter_result.can_trade)
        else:
            if filter_result.can_trade:
                self._process_flat_state(features, regime)

    def _process_flat_state(
        self,
        features: FeatureVector,
        regime: RegimeState
    ) -> None:
        """Process bar in FLAT state (look for entries)."""
        # Get current strategy
        strategy = self._strategy_selector.get_current_strategy(regime)
        if not strategy:
            return

        # Score entry for both sides
        for side in [TradeSide.LONG, TradeSide.SHORT]:
            score_result = self._entry_scorer.calculate_score(
                features, side, regime, strategy
            )

            if score_result.meets_threshold:
                # Create signal
                signal = Signal(
                    symbol=self.backtest_config.symbol,
                    side=side,
                    entry_price=features.close,
                    stop_loss_price=self._calculate_initial_stop(
                        features, side, regime
                    ),
                    score=score_result.score,
                    timestamp=self._state.current_time
                )
                self._state.pending_signal = signal
                self._state.signals_generated += 1
                break

    def _process_signal_state(
        self,
        features: FeatureVector,
        regime: RegimeState,
        can_trade: bool
    ) -> None:
        """Process bar in SIGNAL state (confirm or expire)."""
        signal = self._state.pending_signal
        if not signal:
            return

        # Simple confirmation: next bar also favorable
        strategy = self._strategy_selector.get_current_strategy(regime)
        if strategy and can_trade:
            score_result = self._entry_scorer.calculate_score(
                features, signal.side, regime, strategy
            )

            if score_result.meets_threshold:
                # Confirmed - execute entry
                self._execute_entry(signal, features)
                self._state.signals_confirmed += 1

        # Clear signal either way
        self._state.pending_signal = None

    def _process_manage_state(
        self,
        features: FeatureVector,
        regime: RegimeState
    ) -> None:
        """Process bar in MANAGE state (trailing stop, exit signals)."""
        position = self._state.position
        if not position:
            return

        bar = self._state.current_bar

        # Update position tracking
        position.bars_held += 1
        current_price = features.close

        # Check stop hit
        if position.side == TradeSide.LONG:
            if bar["low"] <= position.trailing.current_stop_price:
                self._close_position("STOP_HIT", position.trailing.current_stop_price)
                return
            # Update MFE/MAE
            position.max_favorable_excursion = max(
                position.max_favorable_excursion,
                (bar["high"] - position.entry_price) / position.entry_price
            )
            position.max_adverse_excursion = max(
                position.max_adverse_excursion,
                (position.entry_price - bar["low"]) / position.entry_price
            )
        else:  # SHORT
            if bar["high"] >= position.trailing.current_stop_price:
                self._close_position("STOP_HIT", position.trailing.current_stop_price)
                return
            position.max_favorable_excursion = max(
                position.max_favorable_excursion,
                (position.entry_price - bar["low"]) / position.entry_price
            )
            position.max_adverse_excursion = max(
                position.max_adverse_excursion,
                (bar["high"] - position.entry_price) / position.entry_price
            )

        # Check exit signals
        strategy = self._strategy_selector.get_current_strategy(regime)
        exit_result = self._exit_checker.check_exit(
            features, position, regime, self._state.regime, strategy
        )

        if exit_result.should_exit:
            self._close_position(exit_result.reason.value, current_price)
            return

        # Update trailing stop
        trailing_result = self._trailing_manager.calculate_trailing_stop(
            features, position, regime, bar
        )

        if trailing_result.should_update:
            position.trailing.update_stop(
                trailing_result.new_stop,
                self._state.bar_count,
                self._state.current_time,
                is_long=position.side == TradeSide.LONG
            )

    def _execute_entry(self, signal: Signal, features: FeatureVector) -> None:
        """Execute entry order.

        Args:
            signal: Entry signal
            features: Current features
        """
        bar = self._state.current_bar

        # Calculate position size
        risk_pct = self.bot_config.risk.risk_per_trade_pct
        stop_distance = abs(features.close - signal.stop_loss_price)
        risk_amount = self._state.capital * (risk_pct / 100)
        quantity = risk_amount / stop_distance if stop_distance > 0 else 0

        if quantity <= 0:
            return

        # Simulate fill
        fill_price, slippage, commission = self._simulator.simulate_fill(
            signal.side,
            quantity,
            features.close,
            bar["high"],
            bar["low"]
        )

        # Deduct commission
        self._state.capital -= commission

        # Create position
        from .models import TrailingState

        trailing = TrailingState(
            mode=self.bot_config.bot.trailing_mode,
            current_stop_price=signal.stop_loss_price,
            initial_stop_price=signal.stop_loss_price,
            highest_price=fill_price,
            lowest_price=fill_price,
            trailing_distance=abs(fill_price - signal.stop_loss_price)
        )

        self._state.position = PositionState(
            symbol=signal.symbol,
            side=signal.side,
            entry_price=fill_price,
            entry_time=self._state.current_time,
            quantity=quantity,
            current_price=fill_price,
            trailing=trailing
        )

        self._state.orders_executed += 1
        logger.debug(
            f"Entry: {signal.side.value} {quantity:.4f} @ {fill_price:.4f}, "
            f"stop={signal.stop_loss_price:.4f}"
        )

    def _close_position(
        self,
        reason: str,
        exit_price: float | None = None
    ) -> None:
        """Close current position.

        Args:
            reason: Exit reason
            exit_price: Exit price (uses current close if None)
        """
        position = self._state.position
        if not position:
            return

        bar = self._state.current_bar
        if exit_price is None:
            exit_price = bar["close"]

        # Simulate exit fill
        exit_side = TradeSide.SHORT if position.side == TradeSide.LONG else TradeSide.LONG
        fill_price, slippage, commission = self._simulator.simulate_fill(
            exit_side,
            position.quantity,
            exit_price,
            bar["high"],
            bar["low"]
        )

        # Calculate P&L
        if position.side == TradeSide.LONG:
            pnl = (fill_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - fill_price) * position.quantity

        pnl -= commission  # Deduct exit commission
        pnl_pct = pnl / (position.entry_price * position.quantity) * 100

        # Update capital
        self._state.capital += pnl

        # Record trade
        trade = BacktestTrade(
            trade_id=self._simulator.generate_order_id(),
            symbol=position.symbol,
            side=position.side,
            entry_time=position.entry_time,
            entry_price=position.entry_price,
            entry_size=position.quantity,
            exit_time=self._state.current_time,
            exit_price=fill_price,
            exit_reason=reason,
            pnl=pnl,
            pnl_pct=pnl_pct,
            bars_held=position.bars_held,
            max_favorable_excursion=position.max_favorable_excursion,
            max_adverse_excursion=position.max_adverse_excursion,
            fees=commission * 2,  # Entry + exit
            slippage=slippage
        )
        self._state.trades.append(trade)
        self._state.position = None

        logger.debug(
            f"Exit: {reason}, PnL=${pnl:.2f} ({pnl_pct:.1f}%), "
            f"bars={trade.bars_held}"
        )

    def _calculate_initial_stop(
        self,
        features: FeatureVector,
        side: TradeSide,
        regime: RegimeState
    ) -> float:
        """Calculate initial stop-loss price.

        Args:
            features: Current features
            side: Trade side
            regime: Current regime

        Returns:
            Stop-loss price
        """
        stop_pct = self.bot_config.risk.initial_stop_loss_pct / 100

        if side == TradeSide.LONG:
            return features.close * (1 - stop_pct)
        else:
            return features.close * (1 + stop_pct)

    def _calculate_equity(self) -> float:
        """Calculate current equity.

        Returns:
            Current equity value
        """
        equity = self._state.capital

        if self._state.position and self._state.position.is_open:
            position = self._state.position
            current_price = self._state.current_bar["close"]

            if position.side == TradeSide.LONG:
                unrealized = (current_price - position.entry_price) * position.quantity
            else:
                unrealized = (position.entry_price - current_price) * position.quantity

            equity += unrealized

        return equity

    def _calculate_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from trades."""
        return calculate_backtest_metrics(self._state.trades)


