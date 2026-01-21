Strategy Evaluator
==================

.. automodule:: src.core.tradingbot.strategy_evaluator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``StrategyEvaluator`` provides walk-forward analysis and robustness validation:

* **Walk-Forward Analysis**: Rolling window training and out-of-sample testing
* **Robustness Validation**: Checks strategies against minimum performance criteria
* **Performance Metrics**: Calculates Sharpe ratio, max drawdown, profit factor, win rate
* **Strategy Comparison**: Ranks strategies by composite score
* **Visualization**: Creates walk-forward validation charts

Key Features
------------

**Walk-Forward Analysis:**
   Splits data into rolling windows for training and testing to avoid overfitting.

**Robustness Gates:**
   Validates strategies against minimum trades, max drawdown, Sharpe ratio thresholds.

**Out-of-Sample Validation:**
   Measures performance degradation between in-sample and out-of-sample periods.

**Composite Scoring:**
   Combines multiple metrics (Sharpe, win rate, profit factor) for strategy ranking.

**Modular Architecture:**
   Uses composition pattern with focused helper classes for each responsibility.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.strategy_evaluator import (
        StrategyEvaluator,
        WalkForwardConfig,
        RobustnessGate
    )

    # Define robustness criteria
    robustness_gate = RobustnessGate(
        min_trades=30,
        max_drawdown_pct=20.0,
        min_sharpe_ratio=1.0
    )

    # Define walk-forward configuration
    walk_forward_config = WalkForwardConfig(
        training_window_days=180,  # 6 months training
        test_window_days=60,       # 2 months testing
        step_days=30               # Roll forward 1 month at a time
    )

    # Initialize evaluator
    evaluator = StrategyEvaluator(
        robustness_gate=robustness_gate,
        walk_forward_config=walk_forward_config
    )

    # Run walk-forward analysis
    result = evaluator.run_walk_forward(
        strategy=strategy_def,
        all_trades=trades
    )

    # Validate robustness
    robustness_report = evaluator.validate_strategy_robustness(
        walk_forward_result=result,
        max_degradation_pct=30.0  # Max 30% OOS degradation
    )

    # Display results
    print(f"Total Periods: {len(result.periods)}")
    print(f"IS Sharpe: {result.in_sample_metrics.sharpe_ratio:.2f}")
    print(f"OOS Sharpe: {result.out_of_sample_metrics.sharpe_ratio:.2f}")
    print(f"Degradation: {robustness_report.oos_degradation_pct:.1f}%")
    print(f"Passes Gate: {robustness_report.passes_gate}")

Classes
-------

.. autoclass:: src.core.tradingbot.strategy_evaluator.StrategyEvaluator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Helper Classes
~~~~~~~~~~~~~~

The evaluator uses composition pattern with focused helpers:

**Metrics & Validation:**

* ``EvaluatorMetrics``: Calculates performance metrics (Sharpe, max DD, profit factor)
* ``EvaluatorValidation``: Validates against robustness gates and degradation thresholds

**Walk-Forward:**

* ``EvaluatorPeriods``: Splits data into rolling windows
* ``EvaluatorWalkForward``: Executes walk-forward analysis
* ``EvaluatorAggregation``: Aggregates results across periods

**Comparison & Visualization:**

* ``EvaluatorComparison``: Ranks strategies by composite score
* ``EvaluatorVisualization``: Creates walk-forward validation charts

Key Methods
-----------

calculate_metrics(trades, initial_capital, sample_type)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.strategy_evaluator.StrategyEvaluator.calculate_metrics

Calculate performance metrics from trade results.

**Parameters:**

* ``trades`` (list[TradeResult]): List of completed trades
* ``initial_capital`` (float): Starting capital (default: 10000.0)
* ``sample_type`` (str): "in_sample" or "out_of_sample"

**Returns:**

* ``PerformanceMetrics``: Comprehensive performance metrics

**Metrics Calculated:**

.. code-block:: python

    class PerformanceMetrics:
        total_return_pct: float       # Total return percentage
        sharpe_ratio: float            # Risk-adjusted return
        max_drawdown_pct: float        # Maximum equity decline
        win_rate: float                # Percentage of winning trades
        profit_factor: float           # Gross profit / gross loss
        total_trades: int              # Number of trades
        avg_win_pct: float             # Average winning trade %
        avg_loss_pct: float            # Average losing trade %
        sample_type: str               # "in_sample" or "out_of_sample"

**Algorithm:**

1. **Calculate Returns:**

   .. code-block:: python

       returns = []
       equity = initial_capital

       for trade in trades:
           pnl = trade.exit_price - trade.entry_price
           returns.append(pnl / equity)
           equity += pnl

       total_return_pct = (equity - initial_capital) / initial_capital

2. **Calculate Sharpe Ratio:**

   .. code-block:: python

       mean_return = np.mean(returns)
       std_return = np.std(returns)

       # Annualized Sharpe (assumes daily returns)
       sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0.0

3. **Calculate Max Drawdown:**

   .. code-block:: python

       equity_curve = np.cumsum(returns) + 1.0
       running_max = np.maximum.accumulate(equity_curve)
       drawdown = (equity_curve - running_max) / running_max

       max_drawdown_pct = abs(drawdown.min()) * 100.0

4. **Calculate Win Rate & Profit Factor:**

   .. code-block:: python

       wins = [t for t in trades if t.pnl > 0]
       losses = [t for t in trades if t.pnl <= 0]

       win_rate = len(wins) / len(trades)

       gross_profit = sum(t.pnl for t in wins)
       gross_loss = abs(sum(t.pnl for t in losses))

       profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

**Example:**

.. code-block:: python

    metrics = evaluator.calculate_metrics(
        trades=trades,
        initial_capital=10000.0,
        sample_type="in_sample"
    )

    print(f"Total Return: {metrics.total_return_pct:.2%}")
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {metrics.max_drawdown_pct:.1f}%")

run_walk_forward(strategy, all_trades, config)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.strategy_evaluator.StrategyEvaluator.run_walk_forward

Run walk-forward analysis on strategy.

**Parameters:**

* ``strategy`` (StrategyDefinition): Strategy to evaluate
* ``all_trades`` (list[TradeResult]): All trades chronologically ordered
* ``config`` (WalkForwardConfig, optional): Walk-forward configuration

**Returns:**

* ``WalkForwardResult``: Results with in-sample and out-of-sample metrics

**Algorithm:**

1. **Split into Periods:**

   .. code-block:: python

       periods = []
       current_date = start_date

       while current_date + training_window + test_window <= end_date:
           # Training period
           train_start = current_date
           train_end = current_date + training_window

           # Testing period
           test_start = train_end
           test_end = test_start + test_window

           periods.append({
               'train': (train_start, train_end),
               'test': (test_start, test_end)
           })

           # Roll forward
           current_date += step_days

2. **Evaluate Each Period:**

   .. code-block:: python

       for period in periods:
           # Get trades for training period
           train_trades = get_trades_in_period(all_trades, period['train'])

           # Calculate in-sample metrics
           is_metrics = evaluator.calculate_metrics(
               train_trades,
               initial_capital=10000.0,
               sample_type="in_sample"
           )

           # Get trades for testing period
           test_trades = get_trades_in_period(all_trades, period['test'])

           # Calculate out-of-sample metrics
           oos_metrics = evaluator.calculate_metrics(
               test_trades,
               initial_capital=10000.0,
               sample_type="out_of_sample"
           )

3. **Aggregate Results:**

   .. code-block:: python

       # Average in-sample metrics
       avg_is_sharpe = np.mean([p.is_metrics.sharpe_ratio for p in periods])
       avg_is_max_dd = np.mean([p.is_metrics.max_drawdown_pct for p in periods])

       # Average out-of-sample metrics
       avg_oos_sharpe = np.mean([p.oos_metrics.sharpe_ratio for p in periods])
       avg_oos_max_dd = np.mean([p.oos_metrics.max_drawdown_pct for p in periods])

       return WalkForwardResult(
           strategy_id=strategy.id,
           periods=periods,
           in_sample_metrics=PerformanceMetrics(sharpe_ratio=avg_is_sharpe, ...),
           out_of_sample_metrics=PerformanceMetrics(sharpe_ratio=avg_oos_sharpe, ...)
       )

**Example:**

.. code-block:: python

    # Run walk-forward analysis
    result = evaluator.run_walk_forward(
        strategy=strategy_def,
        all_trades=trades,
        config=WalkForwardConfig(
            training_window_days=180,
            test_window_days=60,
            step_days=30
        )
    )

    # Display results
    print(f"Periods: {len(result.periods)}")
    print(f"IS Sharpe: {result.in_sample_metrics.sharpe_ratio:.2f}")
    print(f"OOS Sharpe: {result.out_of_sample_metrics.sharpe_ratio:.2f}")

validate_strategy_robustness(walk_forward_result, min_trades, max_drawdown_threshold, min_sharpe, max_degradation_pct)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.strategy_evaluator.StrategyEvaluator.validate_strategy_robustness

Validate strategy robustness using walk-forward results.

**Parameters:**

* ``walk_forward_result`` (WalkForwardResult): Walk-forward analysis result
* ``min_trades`` (int): Minimum total trades required (default: 30)
* ``max_drawdown_threshold`` (float): Maximum allowed drawdown % (default: 20.0)
* ``min_sharpe`` (float): Minimum Sharpe ratio required (default: 1.0)
* ``max_degradation_pct`` (float): Maximum allowed OOS degradation % (default: 30.0)

**Returns:**

* ``RobustnessReport``: Validation results with pass/fail status

**Validation Checks:**

.. code-block:: python

    # 1. Minimum Trades
    total_trades = sum(p.oos_metrics.total_trades for p in periods)
    passes_min_trades = total_trades >= min_trades

    # 2. Max Drawdown
    oos_max_dd = result.out_of_sample_metrics.max_drawdown_pct
    passes_max_dd = oos_max_dd <= max_drawdown_threshold

    # 3. Min Sharpe
    oos_sharpe = result.out_of_sample_metrics.sharpe_ratio
    passes_min_sharpe = oos_sharpe >= min_sharpe

    # 4. OOS Degradation
    is_sharpe = result.in_sample_metrics.sharpe_ratio
    oos_degradation_pct = ((is_sharpe - oos_sharpe) / is_sharpe) * 100.0
    passes_degradation = oos_degradation_pct <= max_degradation_pct

    # Overall gate
    passes_gate = all([
        passes_min_trades,
        passes_max_dd,
        passes_min_sharpe,
        passes_degradation
    ])

**Example:**

.. code-block:: python

    report = evaluator.validate_strategy_robustness(
        walk_forward_result=result,
        min_trades=30,
        max_drawdown_threshold=20.0,
        min_sharpe=1.0,
        max_degradation_pct=30.0
    )

    print(f"Passes Gate: {report.passes_gate}")
    print(f"Total Trades: {report.total_trades} (min: 30)")
    print(f"Max DD: {report.max_drawdown_pct:.1f}% (threshold: 20%)")
    print(f"OOS Sharpe: {report.oos_sharpe:.2f} (min: 1.0)")
    print(f"Degradation: {report.oos_degradation_pct:.1f}% (max: 30%)")

    if not report.passes_gate:
        print(f"Failed Checks: {', '.join(report.failed_checks)}")

compare_strategies(results)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.strategy_evaluator.StrategyEvaluator.compare_strategies

Rank strategies by composite score.

**Parameters:**

* ``results`` (list[WalkForwardResult]): Walk-forward results for multiple strategies

**Returns:**

* ``list[tuple[str, float]]``: Ranked list of (strategy_id, composite_score)

**Composite Score Formula:**

.. code-block:: python

    # Weights
    SHARPE_WEIGHT = 0.40
    WIN_RATE_WEIGHT = 0.20
    PROFIT_FACTOR_WEIGHT = 0.20
    MAX_DD_WEIGHT = 0.20

    # Normalize metrics to 0-1 range
    normalized_sharpe = min(oos_sharpe / 3.0, 1.0)
    normalized_win_rate = oos_win_rate
    normalized_pf = min(oos_profit_factor / 2.0, 1.0)
    normalized_max_dd = max(1.0 - (oos_max_dd / 50.0), 0.0)

    # Composite score
    composite_score = (
        SHARPE_WEIGHT * normalized_sharpe +
        WIN_RATE_WEIGHT * normalized_win_rate +
        PROFIT_FACTOR_WEIGHT * normalized_pf +
        MAX_DD_WEIGHT * normalized_max_dd
    )

**Example:**

.. code-block:: python

    # Run walk-forward for multiple strategies
    results = []
    for strategy in strategies:
        result = evaluator.run_walk_forward(strategy, all_trades)
        results.append(result)

    # Rank strategies
    ranked = evaluator.compare_strategies(results)

    # Display rankings
    for i, (strategy_id, score) in enumerate(ranked, 1):
        print(f"{i}. {strategy_id}: {score:.3f}")

Data Models
-----------

WalkForwardConfig
~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class WalkForwardConfig:
        training_window_days: int = 180  # 6 months
        test_window_days: int = 60       # 2 months
        step_days: int = 30              # Roll forward 1 month

**Fields:**

* ``training_window_days``: In-sample training period length
* ``test_window_days``: Out-of-sample testing period length
* ``step_days``: Days to roll forward between periods

**Example Configuration:**

.. code-block:: python

    # 6 months training, 2 months testing, roll forward 1 month
    config = WalkForwardConfig(
        training_window_days=180,
        test_window_days=60,
        step_days=30
    )

    # Timeline:
    # Period 1: Train[Jan-Jun] Test[Jul-Aug]
    # Period 2: Train[Feb-Jul] Test[Aug-Sep]
    # Period 3: Train[Mar-Aug] Test[Sep-Oct]
    # ...

RobustnessGate
~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class RobustnessGate:
        min_trades: int = 30
        max_drawdown_pct: float = 20.0
        min_sharpe_ratio: float = 1.0

**Fields:**

* ``min_trades``: Minimum total trades required
* ``max_drawdown_pct``: Maximum allowed drawdown percentage
* ``min_sharpe_ratio``: Minimum Sharpe ratio required

RobustnessReport
~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class RobustnessReport:
        passes_gate: bool
        total_trades: int
        max_drawdown_pct: float
        oos_sharpe: float
        oos_degradation_pct: float
        failed_checks: list[str]

**Fields:**

* ``passes_gate``: Overall pass/fail status
* ``total_trades``: Total out-of-sample trades
* ``max_drawdown_pct``: Maximum out-of-sample drawdown
* ``oos_sharpe``: Out-of-sample Sharpe ratio
* ``oos_degradation_pct``: Degradation from in-sample to out-of-sample
* ``failed_checks``: List of failed validation checks

WalkForwardResult
~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class WalkForwardResult:
        strategy_id: str
        periods: list[WalkForwardPeriod]
        in_sample_metrics: PerformanceMetrics
        out_of_sample_metrics: PerformanceMetrics

**Fields:**

* ``strategy_id``: Strategy identifier
* ``periods``: List of walk-forward periods with individual results
* ``in_sample_metrics``: Aggregated in-sample metrics
* ``out_of_sample_metrics``: Aggregated out-of-sample metrics

Common Patterns
---------------

**Pattern 1: Basic Walk-Forward Validation**

.. code-block:: python

    # Run walk-forward analysis
    result = evaluator.run_walk_forward(strategy, all_trades)

    # Validate robustness
    report = evaluator.validate_strategy_robustness(result)

    # Check if strategy passes
    if report.passes_gate:
        print("✅ Strategy is robust")
    else:
        print(f"❌ Strategy failed: {', '.join(report.failed_checks)}")

**Pattern 2: Parameter Sweep with Validation**

.. code-block:: python

    # Test different parameter combinations
    param_configs = [
        {"sl": 1.0, "tp": 2.0},
        {"sl": 2.0, "tp": 4.0},
        {"sl": 3.0, "tp": 6.0}
    ]

    robust_strategies = []

    for params in param_configs:
        # Update strategy parameters
        strategy.risk.stop_loss_pct = params["sl"]
        strategy.risk.take_profit_pct = params["tp"]

        # Run backtest
        trades = run_backtest(strategy, ...)

        # Run walk-forward
        result = evaluator.run_walk_forward(strategy, trades)

        # Validate
        report = evaluator.validate_strategy_robustness(result)

        if report.passes_gate:
            robust_strategies.append({
                'params': params,
                'sharpe': report.oos_sharpe,
                'degradation': report.oos_degradation_pct
            })

    # Find best robust strategy
    if robust_strategies:
        best = max(robust_strategies, key=lambda s: s['sharpe'])
        print(f"Best: SL={best['params']['sl']}%, TP={best['params']['tp']}%")

**Pattern 3: Multi-Strategy Comparison**

.. code-block:: python

    # Run walk-forward for multiple strategies
    strategies = [
        trend_following_strategy,
        mean_reversion_strategy,
        breakout_strategy
    ]

    results = []
    for strategy in strategies:
        trades = run_backtest(strategy, ...)
        result = evaluator.run_walk_forward(strategy, trades)
        results.append(result)

    # Rank strategies
    ranked = evaluator.compare_strategies(results)

    # Display rankings
    print("Strategy Rankings:")
    for i, (strategy_id, score) in enumerate(ranked, 1):
        print(f"{i}. {strategy_id}: {score:.3f}")

    # Use top strategy
    best_strategy_id = ranked[0][0]

**Pattern 4: Adaptive Walk-Forward Windows**

.. code-block:: python

    # Test different walk-forward configurations
    configs = [
        WalkForwardConfig(training_window_days=90, test_window_days=30),   # 3m/1m
        WalkForwardConfig(training_window_days=180, test_window_days=60),  # 6m/2m
        WalkForwardConfig(training_window_days=365, test_window_days=90),  # 12m/3m
    ]

    best_config = None
    best_oos_sharpe = -float('inf')

    for config in configs:
        result = evaluator.run_walk_forward(strategy, all_trades, config)

        if result.out_of_sample_metrics.sharpe_ratio > best_oos_sharpe:
            best_oos_sharpe = result.out_of_sample_metrics.sharpe_ratio
            best_config = config

    print(f"Best Config: {best_config.training_window_days}d train, {best_config.test_window_days}d test")

Best Practices
--------------

**1. Always Use Walk-Forward for Production Strategies:**

.. code-block:: python

    # ✅ Good: Walk-forward validation
    result = evaluator.run_walk_forward(strategy, trades)
    report = evaluator.validate_strategy_robustness(result)

    if report.passes_gate:
        deploy_to_production(strategy)

    # ❌ Bad: No out-of-sample validation
    metrics = evaluator.calculate_metrics(trades)  # Only in-sample!
    deploy_to_production(strategy)  # Dangerous!

**2. Set Conservative Robustness Gates:**

.. code-block:: python

    # ✅ Conservative: Strict requirements
    robustness_gate = RobustnessGate(
        min_trades=50,           # Require many trades
        max_drawdown_pct=15.0,   # Low max drawdown
        min_sharpe_ratio=1.5     # High Sharpe required
    )

    # ❌ Lax: Easy to pass but risky
    robustness_gate = RobustnessGate(
        min_trades=10,
        max_drawdown_pct=50.0,
        min_sharpe_ratio=0.5
    )

**3. Monitor OOS Degradation:**

.. code-block:: python

    # Acceptable degradation: < 30%
    if report.oos_degradation_pct > 30.0:
        print(f"⚠ High degradation: {report.oos_degradation_pct:.1f}%")
        print("Strategy may be overfitted to training data")

**4. Use Multiple Walk-Forward Windows:**

.. code-block:: python

    # Test robustness across different time horizons
    windows = [
        (90, 30),   # Short-term (3m/1m)
        (180, 60),  # Medium-term (6m/2m)
        (365, 90),  # Long-term (12m/3m)
    ]

    all_pass = True
    for train_days, test_days in windows:
        config = WalkForwardConfig(train_days, test_days)
        result = evaluator.run_walk_forward(strategy, trades, config)
        report = evaluator.validate_strategy_robustness(result)

        if not report.passes_gate:
            all_pass = False
            print(f"Failed {train_days}d/{test_days}d window")

    if all_pass:
        print("✅ Strategy is robust across all time horizons")

See Also
--------

* :doc:`backtest_engine` - Generic JSON-based backtesting
* :doc:`backtest_harness` - Full bot simulation
* :doc:`regime_engine` - Regime classification for strategy selection
* :doc:`entry_scorer` - Entry quality scoring
