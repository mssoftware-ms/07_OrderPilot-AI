Backtest Engine
===============

.. automodule:: src.backtesting.engine
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``BacktestEngine`` executes JSON-based strategies against historical data:

* **Multi-Timeframe Support**: Executes on 1m base with higher timeframe indicators
* **Regime-Based Routing**: Routes active regimes to strategy sets dynamically
* **Parameter Overrides**: Applies indicator/strategy overrides from strategy sets
* **Comprehensive Metrics**: Calculates win rate, profit factor, Sharpe ratio, max drawdown
* **Regime Tracking**: Records regime changes for visualization

Key Features
------------

**Multi-Timeframe Execution:**
   Execute on 1m timeline while evaluating indicators from 5m, 15m, 1h, etc.

**Flexible Data Sources:**
   Load from database/API or use pre-loaded chart data.

**Event-Driven Simulation:**
   Processes each candle sequentially to avoid look-ahead bias.

**Dynamic Regime Detection:**
   Evaluates JSON regimes on every bar; routes to appropriate strategies.

**Trade Execution:**
   Supports stop loss, take profit, and signal-based exits with intra-bar simulation.

Usage Example
-------------

.. code-block:: python

    from src.backtesting.engine import BacktestEngine
    from src.core.tradingbot.config.loader import ConfigLoader

    # Load JSON configuration
    loader = ConfigLoader()
    config = loader.load_config("03_JSON/Trading_Bot/trend_following_conservative.json")

    # Initialize engine
    engine = BacktestEngine()

    # Run backtest
    results = engine.run(
        config=config,
        symbol="BTCUSDT",
        start_date="2024-01-01",
        end_date="2024-12-31",
        initial_capital=10000.0
    )

    # Display results
    print(f"Total Trades: {results['total_trades']}")
    print(f"Net Profit: {results['net_profit']:.2f}")
    print(f"Win Rate: {results['win_rate']:.2%}")
    print(f"Profit Factor: {results['profit_factor']:.2f}")
    print(f"Final Equity: {results['final_equity']:.2f}")

Classes
-------

.. autoclass:: src.backtesting.engine.BacktestEngine
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: src.backtesting.engine.Trade
   :members:
   :undoc-members:
   :show-inheritance:

Key Methods
-----------

run(config, symbol, start_date, end_date, initial_capital, chart_data, data_timeframe)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.backtesting.engine.BacktestEngine.run

Execute full backtest with JSON configuration.

**Parameters:**

* ``config`` (TradingBotConfig): Strategy configuration from JSON
* ``symbol`` (str): Trading symbol (e.g., "BTCUSDT")
* ``start_date`` (str | datetime, optional): Backtest start date
* ``end_date`` (str | datetime, optional): Backtest end date
* ``initial_capital`` (float): Starting capital (default: 10000.0)
* ``chart_data`` (pd.DataFrame, optional): Pre-loaded OHLCV data
* ``data_timeframe`` (str, optional): Timeframe of chart_data (e.g., "15m")

**Returns:**

* ``dict``: Backtest results with metrics and trade list

**Algorithm:**

1. **Load Data:**

   .. code-block:: python

       if chart_data is not None:
           df_1m = chart_data.copy()
       else:
           df_1m = self.data_loader.load_data(symbol, start_date, end_date)

2. **Determine Required Timeframes:**

   .. code-block:: python

       required_timeframes = set()
       for ind in config.indicators:
           tf = ind.timeframe or "1m"
           required_timeframes.add(tf)

3. **Resample & Calculate Indicators:**

   .. code-block:: python

       datasets = {}
       for tf in required_timeframes:
           if tf == "1m":
               df_tf = df_1m.copy()
           else:
               df_tf = self.data_loader.resample_data(df_1m, tf)

           self._calculate_indicators(df_tf, config.indicators, tf)
           datasets[tf] = df_tf

4. **Simulation Loop:**

   .. code-block:: python

       for i in range(len(combined_df)):
           row = combined_df.iloc[i]

           # Detect active regimes
           active_regimes = self._evaluate_regimes(config.regimes, row, config.indicators)

           # Route to strategy set
           strategy_set_id = self._route_regimes(config.routing, regime_ids)

           # Evaluate entry/exit
           if active_trade is None:
               # Check entry conditions
               if self._evaluate_conditions(strategy.entry, row, config.indicators):
                   # Enter trade
           else:
               # Check exit conditions (SL/TP/Signal)
               if sl_hit or tp_hit or signal_exit:
                   # Close trade

5. **Return Results:**

   .. code-block:: python

       return self._calculate_stats(trades, initial_capital, equity, regime_history)

**Example:**

.. code-block:: python

    # Backtest from database
    results = engine.run(
        config=config,
        symbol="BTCUSDT",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    # Backtest from chart data
    results = engine.run(
        config=config,
        symbol="BTCUSDT",
        chart_data=df_15m,  # Pre-loaded 15m chart
        data_timeframe="15m"
    )

_calculate_indicators(df, indicators, tf_suffix)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.backtesting.engine.BacktestEngine._calculate_indicators

**Internal method** - Calculate indicators using pandas_ta.

**Supported Indicators:**

.. code-block:: python

    # RSI
    if ind.type == "RSI":
        rsi = ta.rsi(df['close'], length=ind.params['period'])
        df[f"{ind.id}_value"] = rsi

    # SMA
    if ind.type == "SMA":
        sma = ta.sma(df['close'], length=ind.params['period'])
        df[f"{ind.id}_value"] = sma

    # ADX
    if ind.type == "ADX":
        adx_df = ta.adx(df['high'], df['low'], df['close'], length=ind.params['period'])
        df[f"{ind.id}_value"] = adx_df.iloc[:, 0]  # Main ADX column

**Column Naming:**

.. code-block:: python

    # 1m indicators: "{indicator_id}_{field}"
    df["rsi14_value"] = ...

    # HTF indicators: "{timeframe}_{indicator_id}_{field}"
    df["15m_rsi14_value"] = ...

_evaluate_regimes(regimes, row, indicators)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.backtesting.engine.BacktestEngine._evaluate_regimes

**Internal method** - Detect active regimes from conditions.

**Logic:**

.. code-block:: python

    active = []
    for regime in regimes:
        if self._evaluate_conditions(regime.conditions, row, indicators):
            active.append(regime)
    return active

**Fallback to RegimeEngine:**

.. code-block:: python

    # If no JSON regimes active, use hardcoded RegimeEngine
    if not active_regimes:
        feature_vector = FeatureVector(...)
        regime_state = regime_engine.classify(feature_vector)

        # Create synthetic regime IDs
        regime_ids = [
            f"regime_{regime_state.regime.name.lower()}",
            f"volatility_{regime_state.volatility.name.lower()}"
        ]

_route_regimes(routing, active_regime_ids)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.backtesting.engine.BacktestEngine._route_regimes

**Internal method** - Route regime IDs to strategy set.

**Matching Logic:**

.. code-block:: python

    for rule in routing:
        match = True

        # all_of: ALL must be present
        if rule.match.all_of:
            for req in rule.match.all_of:
                if req not in active_regime_ids:
                    match = False

        # any_of: AT LEAST ONE must be present
        if rule.match.any_of:
            if not any(r in active_regime_ids for r in rule.match.any_of):
                match = False

        # none_of: NONE can be present
        if rule.match.none_of:
            if any(r in active_regime_ids for r in rule.match.none_of):
                match = False

        if match:
            return rule.strategy_set_id

    return None  # No matching strategy set

_evaluate_conditions(group, row, indicators)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.backtesting.engine.BacktestEngine._evaluate_conditions

**Internal method** - Evaluate condition group (AND/OR logic).

**Logic:**

.. code-block:: python

    # AND: All conditions must be true
    if group.all:
        for cond in group.all:
            if not self._check_condition(cond, row, indicators):
                return False

    # OR: At least one must be true
    if group.any:
        if not any(self._check_condition(c, row, indicators) for c in group.any):
            return False

    return True

_calculate_stats(trades, initial_capital, final_equity, regime_history)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.backtesting.engine.BacktestEngine._calculate_stats

**Internal method** - Calculate performance metrics.

**Metrics Calculated:**

.. code-block:: python

    return {
        "total_trades": len(trades),
        "net_profit": final_equity - initial_capital,
        "net_profit_pct": (final_equity - initial_capital) / initial_capital,
        "win_rate": len(wins) / len(trades),
        "final_equity": final_equity,
        "max_drawdown": ...,  # TODO
        "profit_factor": sum(wins_pnl) / abs(sum(losses_pnl)),
        "trades": trade_list,
        "regime_history": regime_history,
        "data_source": {
            "timeframe": "15m",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "total_candles": 10000,
            "source": "Chart Data"
        }
    }

Common Patterns
---------------

**Pattern 1: Database Backtest**

.. code-block:: python

    # Load from database/API
    results = engine.run(
        config=config,
        symbol="BTCUSDT",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

**Pattern 2: Chart Data Backtest**

.. code-block:: python

    # Use pre-loaded chart data (faster)
    df_15m = load_chart_data()  # Your chart data loading logic

    results = engine.run(
        config=config,
        symbol="BTCUSDT",
        chart_data=df_15m,
        data_timeframe="15m"
    )

**Pattern 3: Multi-Timeframe Strategy**

.. code-block:: python

    # Strategy uses 5m, 15m, 1h indicators
    config = {
        "indicators": [
            {"id": "rsi5m", "type": "RSI", "timeframe": "5m", "params": {"period": 14}},
            {"id": "sma15m", "type": "SMA", "timeframe": "15m", "params": {"period": 50}},
            {"id": "adx1h", "type": "ADX", "timeframe": "1h", "params": {"period": 14}}
        ]
    }

    # Engine automatically resamples 1m → 5m, 15m, 1h
    results = engine.run(config=config, symbol="BTCUSDT", ...)

**Pattern 4: Regime Visualization**

.. code-block:: python

    results = engine.run(...)

    # Extract regime changes
    regime_history = results['regime_history']
    for change in regime_history:
        print(f"{change['timestamp']}: {change['regime_ids']}")

    # Plot regime boundaries on chart
    for change in regime_history:
        chart.add_vertical_line(
            timestamp=change['timestamp'],
            label=", ".join([r['name'] for r in change['regimes']])
        )

**Pattern 5: Trade Analysis**

.. code-block:: python

    results = engine.run(...)

    # Analyze trades
    for trade in results['trades']:
        print(f"{trade['entry_time']} → {trade['exit_time']}")
        print(f"Entry: {trade['entry_price']}, Exit: {trade['exit_price']}")
        print(f"PnL: {trade['pnl']:.2f} ({trade['pnl_pct']:.2%})")
        print(f"Reason: {trade['reason']}")

Data Models
-----------

Trade
~~~~~

.. code-block:: python

    @dataclass
    class Trade:
        entry_time: pd.Timestamp
        entry_price: float
        side: str  # 'long' or 'short'
        size: float
        exit_time: pd.Timestamp = None
        exit_price: float = None
        pnl: float = 0.0
        pnl_pct: float = 0.0
        exit_reason: str = ""  # "SL", "TP", "Signal"

**Fields:**

* ``entry_time``: Entry timestamp
* ``entry_price``: Entry price
* ``side``: "long" or "short"
* ``size``: Position size (units)
* ``exit_time``: Exit timestamp (None if still open)
* ``exit_price``: Exit price
* ``pnl``: Profit/loss in currency
* ``pnl_pct``: Profit/loss percentage
* ``exit_reason``: "SL" (stop loss), "TP" (take profit), "Signal" (exit signal)

Backtest Results
~~~~~~~~~~~~~~~~

.. code-block:: python

    {
        "total_trades": 45,
        "net_profit": 1250.50,
        "net_profit_pct": 0.12505,  # 12.5%
        "win_rate": 0.6222,  # 62.22%
        "final_equity": 11250.50,
        "max_drawdown": 8.5,  # 8.5%
        "profit_factor": 2.15,
        "trades": [
            {
                "entry_time": "2024-01-15 09:00",
                "exit_time": "2024-01-15 14:30",
                "side": "long",
                "entry_price": 45000.0,
                "exit_price": 45500.0,
                "pnl": 125.0,
                "pnl_pct": 0.0111,
                "reason": "TP"
            },
            ...
        ],
        "regime_history": [
            {
                "timestamp": "2024-01-15 09:00",
                "regime_ids": ["strong_uptrend", "normal_volatility"],
                "regimes": [
                    {"id": "strong_uptrend", "name": "Strong Uptrend"},
                    {"id": "normal_volatility", "name": "Normal Volatility"}
                ]
            },
            ...
        ],
        "data_source": {
            "timeframe": "15m",
            "start_date": "2024-01-01 00:00",
            "end_date": "2024-12-31 23:59",
            "total_candles": 35040,
            "source": "Chart Data"
        }
    }

Timeframe Compatibility
------------------------

**Rule:** Cannot downsample (create smaller timeframes from larger ones).

**Valid:**

.. code-block:: python

    # Chart: 1m → Strategy needs 5m, 15m indicators ✅
    df_1m = load_1m_data()
    results = engine.run(config=config, chart_data=df_1m, data_timeframe="1m")

    # Chart: 5m → Strategy needs 15m, 1h indicators ✅
    df_5m = load_5m_data()
    results = engine.run(config=config, chart_data=df_5m, data_timeframe="5m")

**Invalid:**

.. code-block:: python

    # Chart: 15m → Strategy needs 5m indicators ❌
    df_15m = load_15m_data()
    results = engine.run(config=config, chart_data=df_15m, data_timeframe="15m")

    # Error: ⚠️ TIMEFRAME INCOMPATIBILITY
    # Chart data has 15m timeframe, but strategy requires 5m indicators.
    # Downsampling (15m → 5m) is not possible.

**Solutions:**

1. Load chart with required base timeframe (1m or 5m)
2. Use strategy that requires only chart timeframe or higher
3. Let system load data from database/API (1m base)

Best Practices
--------------

**1. Prefer Chart Data for Speed:**

.. code-block:: python

    # ✅ Fast: Pre-loaded chart data
    results = engine.run(config=config, chart_data=df_15m, data_timeframe="15m")

    # ❌ Slow: Database loading (only if chart not available)
    results = engine.run(config=config, symbol="BTCUSDT", start_date=..., end_date=...)

**2. Validate Timeframe Compatibility:**

.. code-block:: python

    # Check indicator timeframes before loading data
    required_timeframes = set()
    for ind in config.indicators:
        required_timeframes.add(ind.timeframe or "1m")

    # Ensure chart timeframe is smaller than or equal to smallest required
    chart_tf_minutes = 15  # 15m chart
    min_required = min(timeframe_to_minutes(tf) for tf in required_timeframes)

    if chart_tf_minutes > min_required:
        # Load smaller timeframe data

**3. Use Regime History for Debugging:**

.. code-block:: python

    # Analyze regime changes
    regime_history = results['regime_history']

    # Find regime oscillations
    for i, change in enumerate(regime_history[:-1]):
        next_change = regime_history[i + 1]
        time_diff = (next_change['timestamp'] - change['timestamp']).total_seconds() / 60

        if time_diff < 30:  # Regime changed within 30 minutes
            print(f"⚠ Rapid regime change at {change['timestamp']}")

**4. Analyze Trade Distribution:**

.. code-block:: python

    # Group trades by regime
    trades_by_regime = {}
    for trade in results['trades']:
        # Find regime active during entry
        regime = find_regime_at_time(regime_history, trade['entry_time'])

        if regime not in trades_by_regime:
            trades_by_regime[regime] = []

        trades_by_regime[regime].append(trade)

    # Analyze performance per regime
    for regime, trades in trades_by_regime.items():
        win_rate = sum(1 for t in trades if t['pnl'] > 0) / len(trades)
        print(f"{regime}: {len(trades)} trades, {win_rate:.2%} win rate")

See Also
--------

* :doc:`backtest_harness` - Full bot simulation with event-by-event backtesting
* :doc:`strategy_evaluator` - Walk-forward analysis and robustness validation
* :doc:`config_models` - TradingBotConfig model for JSON configurations
* :doc:`config_loader` - Loading and validating JSON configurations
* :doc:`config_detector` - Regime detection from JSON conditions
* :doc:`config_router` - Routing regimes to strategy sets
