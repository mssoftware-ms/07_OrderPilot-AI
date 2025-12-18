"""Backtest Harness for Tradingbot.

Provides reproducible backtesting with:
- Deterministic random seeds
- Slippage/fees simulation
- Multi-timeframe data support
- Event-by-event simulation
- Comprehensive metrics collection
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator

import pandas as pd
from pydantic import BaseModel, Field

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
from .strategy_evaluator import PerformanceMetrics, TradeResult

if TYPE_CHECKING:
    from .bot_controller import BotController

logger = logging.getLogger(__name__)


class BacktestMode(str, Enum):
    """Backtest execution modes."""
    FAST = "fast"  # Skip some calculations for speed
    FULL = "full"  # Full simulation with all features
    DEBUG = "debug"  # Extra logging and validation


@dataclass
class BacktestConfig:
    """Configuration for backtest run."""
    # Data range
    start_date: datetime
    end_date: datetime
    symbol: str
    timeframe: str = "1T"  # 1 minute default

    # Simulation parameters
    initial_capital: float = 10000.0
    slippage_pct: float = 0.05
    commission_pct: float = 0.1  # Per side
    seed: int | None = None  # Random seed for reproducibility

    # Execution
    mode: BacktestMode = BacktestMode.FULL
    warmup_bars: int = 50  # Bars needed for indicators

    # Output
    save_trades: bool = True
    save_equity_curve: bool = True
    save_decisions: bool = False  # Can be large
    output_dir: Path | None = None

    def get_seed(self) -> int:
        """Get deterministic seed based on config."""
        if self.seed is not None:
            return self.seed
        # Generate seed from config hash
        config_str = f"{self.symbol}{self.start_date}{self.end_date}{self.timeframe}"
        return int(hashlib.sha256(config_str.encode()).hexdigest()[:8], 16)


@dataclass
class BacktestTrade:
    """Record of a completed trade."""
    trade_id: str
    symbol: str
    side: TradeSide
    entry_time: datetime
    entry_price: float
    entry_size: float
    exit_time: datetime
    exit_price: float
    exit_reason: str
    pnl: float
    pnl_pct: float
    bars_held: int
    max_favorable_excursion: float
    max_adverse_excursion: float
    fees: float
    slippage: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "entry_time": self.entry_time.isoformat(),
            "entry_price": self.entry_price,
            "entry_size": self.entry_size,
            "exit_time": self.exit_time.isoformat(),
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "bars_held": self.bars_held,
            "mfe": self.max_favorable_excursion,
            "mae": self.max_adverse_excursion,
            "fees": self.fees,
            "slippage": self.slippage,
        }


@dataclass
class BacktestState:
    """State tracking during backtest."""
    bar_index: int = 0
    current_time: datetime | None = None
    capital: float = 10000.0
    position: PositionState | None = None
    pending_signal: Signal | None = None

    # Tracking
    equity_curve: list[tuple[datetime, float]] = field(default_factory=list)
    trades: list[BacktestTrade] = field(default_factory=list)
    decisions: list[BotDecision] = field(default_factory=list)
    signals_generated: int = 0
    signals_confirmed: int = 0
    orders_executed: int = 0

    # Current bar data
    current_bar: dict | None = None
    features: FeatureVector | None = None
    regime: RegimeState | None = None


@dataclass
class BacktestResult:
    """Result of a backtest run."""
    config: BacktestConfig
    metrics: PerformanceMetrics
    trades: list[BacktestTrade]
    equity_curve: list[tuple[datetime, float]]
    run_time_seconds: float
    total_bars: int
    seed_used: int

    # Summary stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_fees: float = 0.0
    max_drawdown_pct: float = 0.0
    final_capital: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "config": {
                "symbol": self.config.symbol,
                "start_date": self.config.start_date.isoformat(),
                "end_date": self.config.end_date.isoformat(),
                "timeframe": self.config.timeframe,
                "initial_capital": self.config.initial_capital,
                "slippage_pct": self.config.slippage_pct,
                "commission_pct": self.config.commission_pct,
                "seed": self.seed_used,
            },
            "metrics": {
                "profit_factor": self.metrics.profit_factor,
                "max_drawdown_pct": self.metrics.max_drawdown_pct,
                "win_rate": self.metrics.win_rate,
                "expectancy": self.metrics.expectancy,
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "sortino_ratio": self.metrics.sortino_ratio,
                "calmar_ratio": self.metrics.calmar_ratio,
            },
            "summary": {
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "total_pnl": self.total_pnl,
                "total_fees": self.total_fees,
                "max_drawdown_pct": self.max_drawdown_pct,
                "final_capital": self.final_capital,
                "run_time_seconds": self.run_time_seconds,
                "total_bars": self.total_bars,
            },
            "trades": [t.to_dict() for t in self.trades],
        }

    def save(self, path: Path) -> None:
        """Save result to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Backtest result saved to {path}")


class BacktestSimulator:
    """Simulates order execution during backtest.

    Provides deterministic slippage and fill simulation.
    """

    def __init__(
        self,
        slippage_pct: float = 0.05,
        commission_pct: float = 0.1,
        seed: int = 42
    ):
        """Initialize simulator.

        Args:
            slippage_pct: Slippage percentage
            commission_pct: Commission per side
            seed: Random seed
        """
        self.slippage_pct = slippage_pct
        self.commission_pct = commission_pct
        self._rng = random.Random(seed)
        self._order_counter = 0

    def simulate_fill(
        self,
        side: TradeSide,
        quantity: float,
        price: float,
        bar_high: float,
        bar_low: float
    ) -> tuple[float, float, float]:
        """Simulate order fill with slippage.

        Args:
            side: Order side
            quantity: Order quantity
            price: Expected price
            bar_high: Bar high price
            bar_low: Bar low price

        Returns:
            (fill_price, slippage_amount, commission)
        """
        # Calculate slippage (adverse direction)
        slippage_factor = self._rng.uniform(0, self.slippage_pct / 100)

        if side == TradeSide.LONG:
            # Buy: slippage increases price
            slippage = price * slippage_factor
            fill_price = min(price + slippage, bar_high)
        else:
            # Sell: slippage decreases price
            slippage = price * slippage_factor
            fill_price = max(price - slippage, bar_low)

        slippage_amount = abs(fill_price - price) * quantity
        commission = fill_price * quantity * (self.commission_pct / 100)

        return fill_price, slippage_amount, commission

    def generate_order_id(self) -> str:
        """Generate unique order ID."""
        self._order_counter += 1
        return f"bt_order_{self._order_counter:06d}"


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
        """Calculate performance metrics from trades.

        Returns:
            PerformanceMetrics
        """
        trades = self._state.trades

        if not trades:
            return PerformanceMetrics(
                profit_factor=0,
                max_drawdown_pct=0,
                win_rate=0,
                expectancy=0,
                total_trades=0
            )

        # Convert to TradeResult format
        trade_results = [
            TradeResult(
                entry_time=t.entry_time,
                exit_time=t.exit_time,
                side=t.side,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                pnl=t.pnl,
                pnl_pct=t.pnl_pct,
                bars_held=t.bars_held
            )
            for t in trades
        ]

        # Use strategy evaluator for consistent metrics
        from .strategy_evaluator import StrategyEvaluator

        evaluator = StrategyEvaluator()
        return evaluator.calculate_metrics(trade_results)


class ReleaseGate:
    """Release gate checker for Paper → Live transition.

    Validates that backtest/paper results meet minimum criteria.
    """

    def __init__(
        self,
        min_trades: int = 20,
        min_win_rate: float = 0.4,
        min_profit_factor: float = 1.2,
        max_drawdown_pct: float = 15.0,
        min_sharpe: float = 0.5,
        min_paper_days: int = 7,
        max_consecutive_losses: int = 5
    ):
        """Initialize release gate.

        Args:
            min_trades: Minimum number of trades
            min_win_rate: Minimum win rate
            min_profit_factor: Minimum profit factor
            max_drawdown_pct: Maximum drawdown percentage
            min_sharpe: Minimum Sharpe ratio
            min_paper_days: Minimum days of paper trading
            max_consecutive_losses: Maximum consecutive losses
        """
        self.min_trades = min_trades
        self.min_win_rate = min_win_rate
        self.min_profit_factor = min_profit_factor
        self.max_drawdown_pct = max_drawdown_pct
        self.min_sharpe = min_sharpe
        self.min_paper_days = min_paper_days
        self.max_consecutive_losses = max_consecutive_losses

    def check(self, result: BacktestResult) -> tuple[bool, list[str]]:
        """Check if result passes release gate.

        Args:
            result: Backtest or paper trading result

        Returns:
            (passed, list of failure reasons)
        """
        failures = []

        if result.total_trades < self.min_trades:
            failures.append(
                f"MIN_TRADES: {result.total_trades} < {self.min_trades}"
            )

        if result.metrics.win_rate < self.min_win_rate:
            failures.append(
                f"MIN_WIN_RATE: {result.metrics.win_rate:.1%} < {self.min_win_rate:.1%}"
            )

        if result.metrics.profit_factor < self.min_profit_factor:
            failures.append(
                f"MIN_PROFIT_FACTOR: {result.metrics.profit_factor:.2f} < {self.min_profit_factor:.2f}"
            )

        if result.metrics.max_drawdown_pct > self.max_drawdown_pct:
            failures.append(
                f"MAX_DRAWDOWN: {result.metrics.max_drawdown_pct:.1f}% > {self.max_drawdown_pct:.1f}%"
            )

        if result.metrics.sharpe_ratio < self.min_sharpe:
            failures.append(
                f"MIN_SHARPE: {result.metrics.sharpe_ratio:.2f} < {self.min_sharpe:.2f}"
            )

        # Check consecutive losses
        max_consec = self._calculate_max_consecutive_losses(result.trades)
        if max_consec > self.max_consecutive_losses:
            failures.append(
                f"MAX_CONSECUTIVE_LOSSES: {max_consec} > {self.max_consecutive_losses}"
            )

        passed = len(failures) == 0

        if passed:
            logger.info("Release gate PASSED")
        else:
            logger.warning(f"Release gate FAILED: {failures}")

        return passed, failures

    def _calculate_max_consecutive_losses(
        self,
        trades: list[BacktestTrade]
    ) -> int:
        """Calculate maximum consecutive losses.

        Args:
            trades: List of trades

        Returns:
            Maximum consecutive loss count
        """
        max_consec = 0
        current_consec = 0

        for trade in trades:
            if trade.pnl <= 0:
                current_consec += 1
                max_consec = max(max_consec, current_consec)
            else:
                current_consec = 0

        return max_consec
