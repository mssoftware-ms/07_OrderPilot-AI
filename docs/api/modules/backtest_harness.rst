Backtest Harness
================

.. automodule:: src.core.tradingbot.backtest_harness
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``BacktestHarness`` provides full bot simulation with event-by-event backtesting:

* **Deterministic Execution**: Reproducible results with seed control
* **Event-Driven Simulation**: Processes bars sequentially to avoid look-ahead bias
* **Full Bot Integration**: Uses FeatureEngine, RegimeEngine, EntryScorer, ExitChecker
* **Composition Pattern**: Helper modules for data loading, execution, bar processing
* **Comprehensive Metrics**: Tracks trades, equity curve, drawdown, Sharpe ratio

Key Features
------------

**Deterministic Backtesting:**
   Seed-controlled randomness ensures reproducible results across runs.

**Multi-Component Integration:**
   Integrates FeatureEngine (indicators), RegimeEngine (regimes), EntryScorer (quality), ExitChecker (exits), TrailingStopManager (dynamic stops).

**Modular Architecture:**
   Uses composition pattern with focused helper classes for each responsibility.

**Multi-Timeframe Support:**
   Fetches and resamples data for multiple timeframes automatically.

**Realistic Simulation:**
   Includes slippage, commissions, and intra-bar execution logic.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.backtest_harness import BacktestHarness
    from src.core.tradingbot.config import FullBotConfig
    from src.core.tradingbot.backtest_types import BacktestConfig

    # Load bot configuration
    bot_config = FullBotConfig(
        strategy="trend_following",
        risk=RiskConfig(
            stop_loss_pct=2.0,
            take_profit_pct=4.0,
            position_size_pct=5.0
        ),
        entry_score_threshold=0.6,
        trailing_activation_pct=2.0
    )

    # Create backtest configuration
    backtest_config = BacktestConfig(
        symbol="BTCUSDT",
        start_date="2024-01-01",
        end_date="2024-12-31",
        initial_capital=10000.0,
        slippage_pct=0.05,
        commission_pct=0.1,
        seed=42  # Deterministic results
    )

    # Initialize harness
    harness = BacktestHarness(
        bot_config=bot_config,
        backtest_config=backtest_config
    )

    # Run backtest
    result = harness.run()

    # Display results
    print(f"Total Trades: {result.total_trades}")
    print(f"Win Rate: {result.win_rate:.2%}")
    print(f"Net Profit: {result.net_profit:.2f}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.2%}")

Classes
-------

.. autoclass:: src.core.tradingbot.backtest_harness.BacktestHarness
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Helper Classes
~~~~~~~~~~~~~~

The harness uses composition pattern with focused helpers:

**Data Management:**

* ``BacktestHarnessDataLoader``: Fetches and resamples historical data
* ``BacktestHarnessHelpers``: Utility functions (timeframe conversion, calculations)

**Execution:**

* ``BacktestHarnessRunner``: Main backtest loop
* ``BacktestHarnessBarProcessor``: Processes each bar (features, regimes, signals)
* ``BacktestHarnessExecution``: Order execution and position management

**Simulation:**

* ``BacktestSimulator``: Applies slippage, commissions, and execution logic

Key Methods
-----------

__init__(bot_config, backtest_config, data_provider)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.backtest_harness.BacktestHarness.__init__

Initialize backtest harness.

**Parameters:**

* ``bot_config`` (FullBotConfig): Bot configuration with strategy and risk settings
* ``backtest_config`` (BacktestConfig): Backtest parameters (symbol, dates, capital)
* ``data_provider`` (Callable, optional): Custom data provider function

**Initialization:**

.. code-block:: python

    def __init__(self, bot_config, backtest_config, data_provider=None):
        self.bot_config = bot_config
        self.backtest_config = backtest_config
        self._data_provider = data_provider

        # Seed for deterministic results
        self._seed = backtest_config.get_seed()

        # Initialize simulator
        self._simulator = BacktestSimulator(
            slippage_pct=backtest_config.slippage_pct,
            commission_pct=backtest_config.commission_pct,
            seed=self._seed
        )

        # Initialize state
        self._state = BacktestState(capital=backtest_config.initial_capital)

        # Lazy-initialize bot components
        self._feature_engine = None
        self._regime_engine = None
        self._entry_scorer = None
        self._exit_checker = None
        self._trailing_manager = None

        # Create helpers (composition pattern)
        self._data_loader = BacktestHarnessDataLoader(self)
        self._runner = BacktestHarnessRunner(self)
        self._bar_processor = BacktestHarnessBarProcessor(self)
        self._execution = BacktestHarnessExecution(self)
        self._helpers = BacktestHarnessHelpers(self)

**Example:**

.. code-block:: python

    harness = BacktestHarness(
        bot_config=bot_config,
        backtest_config=BacktestConfig(
            symbol="BTCUSDT",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=10000.0,
            seed=42  # Reproducible results
        )
    )

run()
~~~~~

.. automethod:: src.core.tradingbot.backtest_harness.BacktestHarness.run

Execute full backtest simulation.

**Returns:**

* ``BacktestResult``: Comprehensive backtest results with trades and metrics

**Algorithm:**

1. **Load Data:**

   .. code-block:: python

       data = self.load_data()  # Delegates to BacktestHarnessDataLoader

2. **Initialize Bot Components:**

   .. code-block:: python

       self._init_bot_components()  # Create FeatureEngine, RegimeEngine, etc.

3. **Event-Driven Loop:**

   .. code-block:: python

       for timestamp, bar in data.iterrows():
           # Process bar (features, regimes, signals)
           self._bar_processor.process_bar(timestamp, bar)

           # Execute trades (entry/exit)
           self._execution.execute_signals(timestamp, bar)

4. **Calculate Metrics:**

   .. code-block:: python

       result = BacktestResult(
           trades=self._state.trades,
           equity_curve=self._state.equity_curve,
           metrics=self._calculate_metrics()
       )

**Example:**

.. code-block:: python

    # Run backtest
    result = harness.run()

    # Access results
    print(f"Total Trades: {result.total_trades}")
    print(f"Win Rate: {result.win_rate:.2%}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")

    # Access trades
    for trade in result.trades:
        print(f"{trade.entry_time} → {trade.exit_time}: {trade.pnl:.2f}")

load_data()
~~~~~~~~~~~

.. automethod:: src.core.tradingbot.backtest_harness.BacktestHarness.load_data

Load historical data for backtest (delegates to ``BacktestHarnessDataLoader``).

**Returns:**

* ``pd.DataFrame``: OHLCV data for backtest period

**Data Loading:**

.. code-block:: python

    def load_data(self) -> pd.DataFrame:
        # Delegates to BacktestHarnessDataLoader
        return self._data_loader.load_data()

**BacktestHarnessDataLoader Logic:**

.. code-block:: python

    # Determine required timeframes from bot config
    required_timeframes = self._get_required_timeframes()

    # Fetch base data (1m)
    if self._data_provider:
        data_1m = self._data_provider(symbol, start_date, end_date, "1m")
    else:
        data_1m = fetch_from_database(symbol, start_date, end_date)

    # Resample for higher timeframes
    datasets = {}
    for tf in required_timeframes:
        if tf == "1m":
            datasets[tf] = data_1m
        else:
            datasets[tf] = resample_data(data_1m, tf)

    # Merge all timeframes
    combined_df = merge_timeframes(datasets)

    return combined_df

_init_bot_components()
~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.backtest_harness.BacktestHarness._init_bot_components

**Internal method** - Initialize bot components.

**Components Initialized:**

.. code-block:: python

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

Backtest Workflow
-----------------

**Complete Event Loop:**

.. code-block:: python

    # 1. Load data
    data = harness.load_data()

    # 2. Initialize bot
    harness._init_bot_components()

    # 3. Loop through bars
    for timestamp, bar in data.iterrows():
        # a) Calculate features
        features = harness._feature_engine.process_bar(bar)

        # b) Classify regime
        regime = harness._regime_engine.classify(features)

        # c) Check entry signals
        if not in_position:
            entry_score = harness._entry_scorer.calculate_score(features, regime)

            if entry_score >= threshold:
                # Enter position
                position = harness._execution.enter_trade(timestamp, bar, entry_score)

        # d) Check exit signals
        else:
            exit_signal = harness._exit_checker.check_exit(features, regime, position)

            if exit_signal:
                # Exit position
                harness._execution.exit_trade(timestamp, bar, exit_signal.reason)

            # Update trailing stop
            harness._trailing_manager.update(position, bar['close'])

    # 4. Calculate final metrics
    result = harness._calculate_metrics()

Common Patterns
---------------

**Pattern 1: Basic Backtest**

.. code-block:: python

    # Minimal setup
    harness = BacktestHarness(
        bot_config=FullBotConfig(strategy="trend_following"),
        backtest_config=BacktestConfig(
            symbol="BTCUSDT",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
    )

    result = harness.run()

**Pattern 2: Custom Data Provider**

.. code-block:: python

    def my_data_provider(symbol, start_date, end_date, timeframe):
        # Load from custom source
        df = load_from_csv(f"data/{symbol}_{timeframe}.csv")
        return df[(df.index >= start_date) & (df.index <= end_date)]

    harness = BacktestHarness(
        bot_config=bot_config,
        backtest_config=backtest_config,
        data_provider=my_data_provider
    )

**Pattern 3: Parameter Sweep**

.. code-block:: python

    # Test different risk parameters
    risk_params = [
        (1.0, 2.0),  # SL 1%, TP 2%
        (2.0, 4.0),  # SL 2%, TP 4%
        (3.0, 6.0),  # SL 3%, TP 6%
    ]

    results = []
    for sl, tp in risk_params:
        bot_config.risk.stop_loss_pct = sl
        bot_config.risk.take_profit_pct = tp

        harness = BacktestHarness(bot_config, backtest_config)
        result = harness.run()

        results.append({
            'sl': sl,
            'tp': tp,
            'sharpe': result.sharpe_ratio,
            'max_dd': result.max_drawdown
        })

    # Find best parameters
    best = max(results, key=lambda r: r['sharpe'])
    print(f"Best: SL={best['sl']}%, TP={best['tp']}% → Sharpe={best['sharpe']:.2f}")

**Pattern 4: Walk-Forward Validation**

.. code-block:: python

    # Split into training and testing periods
    training_config = BacktestConfig(
        symbol="BTCUSDT",
        start_date="2024-01-01",
        end_date="2024-06-30",  # 6 months training
        initial_capital=10000.0
    )

    testing_config = BacktestConfig(
        symbol="BTCUSDT",
        start_date="2024-07-01",
        end_date="2024-12-31",  # 6 months testing
        initial_capital=10000.0
    )

    # Train on first period
    train_harness = BacktestHarness(bot_config, training_config)
    train_result = train_harness.run()

    # Test on second period
    test_harness = BacktestHarness(bot_config, testing_config)
    test_result = test_harness.run()

    # Compare performance
    print(f"Training Sharpe: {train_result.sharpe_ratio:.2f}")
    print(f"Testing Sharpe: {test_result.sharpe_ratio:.2f}")

    degradation = (train_result.sharpe_ratio - test_result.sharpe_ratio) / train_result.sharpe_ratio
    print(f"Degradation: {degradation:.2%}")

Data Models
-----------

BacktestConfig
~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class BacktestConfig:
        symbol: str
        start_date: str | datetime
        end_date: str | datetime
        initial_capital: float = 10000.0
        slippage_pct: float = 0.05
        commission_pct: float = 0.1
        seed: int | None = None

        def get_seed(self) -> int:
            return self.seed if self.seed is not None else 42

**Fields:**

* ``symbol``: Trading symbol (e.g., "BTCUSDT")
* ``start_date``: Backtest start date
* ``end_date``: Backtest end date
* ``initial_capital``: Starting capital
* ``slippage_pct``: Slippage percentage (0.05 = 0.05%)
* ``commission_pct``: Commission percentage (0.1 = 0.1%)
* ``seed``: Random seed for deterministic results

BacktestState
~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class BacktestState:
        capital: float
        position: Position | None = None
        trades: list[BacktestTrade] = field(default_factory=list)
        equity_curve: list[float] = field(default_factory=list)
        current_bar: int = 0

**Fields:**

* ``capital``: Current available capital
* ``position``: Active position (None if not in trade)
* ``trades``: List of closed trades
* ``equity_curve``: Equity at each bar
* ``current_bar``: Current bar index

BacktestResult
~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class BacktestResult:
        total_trades: int
        win_rate: float
        net_profit: float
        net_profit_pct: float
        sharpe_ratio: float
        max_drawdown: float
        profit_factor: float
        avg_win: float
        avg_loss: float
        largest_win: float
        largest_loss: float
        trades: list[BacktestTrade]
        equity_curve: list[float]

**Fields:**

* ``total_trades``: Number of trades executed
* ``win_rate``: Percentage of winning trades
* ``net_profit``: Total profit in currency
* ``net_profit_pct``: Total profit percentage
* ``sharpe_ratio``: Risk-adjusted returns
* ``max_drawdown``: Maximum equity decline
* ``profit_factor``: Gross profit / gross loss
* ``avg_win``: Average winning trade
* ``avg_loss``: Average losing trade
* ``largest_win``: Largest winning trade
* ``largest_loss``: Largest losing trade
* ``trades``: List of all trades
* ``equity_curve``: Equity values over time

Deterministic Backtesting
--------------------------

**Seed Control for Reproducibility:**

.. code-block:: python

    # Same seed → identical results
    config1 = BacktestConfig(symbol="BTCUSDT", seed=42, ...)
    harness1 = BacktestHarness(bot_config, config1)
    result1 = harness1.run()

    config2 = BacktestConfig(symbol="BTCUSDT", seed=42, ...)
    harness2 = BacktestHarness(bot_config, config2)
    result2 = harness2.run()

    # result1 == result2 (exactly)
    assert result1.net_profit == result2.net_profit
    assert result1.total_trades == result2.total_trades

**Where Randomness Occurs:**

1. **Slippage**: Random slippage within specified percentage
2. **Execution Delay**: Random sub-bar execution timing
3. **Fill Simulation**: Probabilistic partial fills (if implemented)

**All randomness is controlled by seed.**

Best Practices
--------------

**1. Always Use Seeds for Production Backtests:**

.. code-block:: python

    # ✅ Good: Deterministic
    backtest_config = BacktestConfig(seed=42, ...)

    # ❌ Bad: Non-reproducible
    backtest_config = BacktestConfig(seed=None, ...)

**2. Use Realistic Slippage and Commissions:**

.. code-block:: python

    # ✅ Realistic: 0.05% slippage, 0.1% commission
    BacktestConfig(slippage_pct=0.05, commission_pct=0.1, ...)

    # ❌ Optimistic: No slippage/commission
    BacktestConfig(slippage_pct=0.0, commission_pct=0.0, ...)

**3. Validate Results with Walk-Forward:**

.. code-block:: python

    # Train on 70% of data
    train_result = BacktestHarness(bot_config, train_config).run()

    # Test on remaining 30%
    test_result = BacktestHarness(bot_config, test_config).run()

    # Expect some degradation, but not too much
    assert test_result.sharpe_ratio > train_result.sharpe_ratio * 0.7

**4. Monitor Equity Curve:**

.. code-block:: python

    result = harness.run()

    # Plot equity curve
    plt.plot(result.equity_curve)
    plt.title("Equity Curve")
    plt.xlabel("Bar")
    plt.ylabel("Equity")
    plt.show()

    # Check for smooth growth (not jagged)

See Also
--------

* :doc:`backtest_engine` - Generic JSON-based backtesting
* :doc:`strategy_evaluator` - Walk-forward analysis and robustness validation
* :doc:`bot_controller` - Main bot controller using backtest results
* :doc:`regime_engine` - Regime classification used in backtesting
* :doc:`entry_scorer` - Entry quality scoring used in backtesting
