Configuration Executor
======================

.. automodule:: src.core.tradingbot.config.executor
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``StrategySetExecutor`` applies parameter overrides from strategy sets:

* **Indicator Overrides**: Temporarily modify indicator parameters (e.g., RSI period)
* **Strategy Overrides**: Temporarily modify strategy risk parameters
* **State Management**: Stores original parameters for restoration
* **Execution Context**: Prepares complete execution context with overrides applied

Key Features
------------

**Temporary Modifications:**
   Overrides are temporary and can be restored to original values.

**Dual Override Support:**
   Modifies both indicators and strategy parameters independently.

**State Preservation:**
   Tracks original state for clean restoration.

**Validation:**
   Ensures overrides reference valid indicators and strategies.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.config.executor import StrategySetExecutor
    from src.core.tradingbot.config.models import StrategySet, Indicator, Strategy

    # Original configuration
    indicators = [
        Indicator(id="rsi_14", type="RSI", params={"period": 14}),
        Indicator(id="macd", type="MACD", params={"fast": 12, "slow": 26, "signal": 9})
    ]

    strategies = [
        Strategy(
            id="trend_following",
            entry_conditions=...,
            exit_conditions=...,
            risk=RiskConfig(stop_loss_pct=2.0, take_profit_pct=4.0, position_size_pct=5.0)
        )
    ]

    # Strategy set with overrides
    strategy_set = StrategySet(
        id="trending_aggressive",
        strategies=[{"strategy_id": "trend_following"}],
        indicator_overrides={
            "rsi_14": {"period": 10}  # Faster RSI for trending markets
        },
        strategy_overrides={
            "trend_following": {
                "risk": {
                    "stop_loss_pct": 3.0,      # Wider stop
                    "position_size_pct": 8.0    # Larger position
                }
            }
        }
    )

    # Create matched strategy set
    matched = MatchedStrategySet(
        strategy_set=strategy_set,
        matched_regimes=[...],
        routing_rule=[...]
    )

    # Initialize executor
    executor = StrategySetExecutor(indicators, strategies)

    # Apply overrides
    execution_context = executor.prepare_execution(matched)

    # Check applied overrides
    print(execution_context.indicator_overrides)  # {"rsi_14": {"period": 10}}
    print(execution_context.strategy_overrides)   # {"trend_following": {"risk": {...}}}

    # Restore original parameters when done
    executor.restore_state()

Classes
-------

.. autoclass:: src.core.tradingbot.config.executor.StrategySetExecutor
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

prepare_execution(matched_strategy_set)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.executor.StrategySetExecutor.prepare_execution

Prepare execution context with overrides applied.

**Parameters:**

* ``matched_strategy_set`` (MatchedStrategySet): Matched strategy set from router

**Returns:**

* ``ExecutionContext``: Context with overrides and original state

**Algorithm:**

1. **Save Original State:**

   .. code-block:: python

       original_state = {
           "indicators": {ind.id: ind.params.copy() for ind in indicators},
           "strategies": {strat.id: strat.risk.dict() for strat in strategies}
       }

2. **Apply Indicator Overrides:**

   .. code-block:: python

       for ind_id, overrides in strategy_set.indicator_overrides.items():
           indicator = find_indicator(ind_id)
           indicator.params.update(overrides)

3. **Apply Strategy Overrides:**

   .. code-block:: python

       for strat_id, overrides in strategy_set.strategy_overrides.items():
           strategy = find_strategy(strat_id)
           if "risk" in overrides:
               strategy.risk = RiskConfig(**{**strategy.risk.dict(), **overrides["risk"]})

4. **Return Execution Context:**

   .. code-block:: python

       return ExecutionContext(
           strategy_set=matched_strategy_set.strategy_set,
           applied_indicator_overrides=...,
           applied_strategy_overrides=...,
           original_state=original_state
       )

**Example:**

.. code-block:: python

    # Prepare execution with overrides
    context = executor.prepare_execution(matched)

    # Use modified indicators and strategies
    backtest_engine.run(context.indicators, context.strategies)

    # Restore when done
    executor.restore_state()

restore_state()
~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.executor.StrategySetExecutor.restore_state

Restore original parameters before overrides.

**Behavior:**

.. code-block:: python

    # Restore indicator parameters
    for ind_id, original_params in self._original_indicator_params.items():
        indicator = find_indicator(ind_id)
        indicator.params = original_params.copy()

    # Restore strategy parameters
    for strat_id, original_risk in self._original_strategy_risk.items():
        strategy = find_strategy(strat_id)
        strategy.risk = RiskConfig(**original_risk)

**Example:**

.. code-block:: python

    # Execute with overrides
    context = executor.prepare_execution(matched)
    execute_trades(context)

    # Restore original state
    executor.restore_state()

    # Parameters are now back to original values

_apply_indicator_overrides(overrides)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.executor.StrategySetExecutor._apply_indicator_overrides

**Internal method** - Apply indicator parameter overrides.

**Logic:**

.. code-block:: python

    for ind_id, override_params in overrides.items():
        # Find indicator
        indicator = next(ind for ind in self.indicators if ind.id == ind_id)

        # Save original if not already saved
        if ind_id not in self._original_indicator_params:
            self._original_indicator_params[ind_id] = indicator.params.copy()

        # Apply overrides
        indicator.params.update(override_params)

**Example Overrides:**

.. code-block:: python

    overrides = {
        "rsi_14": {"period": 10},           # Change RSI period 14 → 10
        "macd": {"fast": 8, "slow": 21},    # Change MACD fast/slow
        "sma_50": {"period": 30}            # Change SMA period 50 → 30
    }

_apply_strategy_overrides(overrides)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.executor.StrategySetExecutor._apply_strategy_overrides

**Internal method** - Apply strategy parameter overrides.

**Logic:**

.. code-block:: python

    for strat_id, override_data in overrides.items():
        # Find strategy
        strategy = next(s for s in self.strategies if s.id == strat_id)

        # Save original if not already saved
        if strat_id not in self._original_strategy_risk:
            self._original_strategy_risk[strat_id] = strategy.risk.dict()

        # Apply risk overrides
        if "risk" in override_data:
            current_risk = strategy.risk.dict()
            current_risk.update(override_data["risk"])
            strategy.risk = RiskConfig(**current_risk)

**Example Overrides:**

.. code-block:: python

    overrides = {
        "trend_following": {
            "risk": {
                "stop_loss_pct": 3.0,       # Wider stop (was 2.0)
                "position_size_pct": 8.0     # Larger position (was 5.0)
            }
        },
        "mean_reversion": {
            "risk": {
                "stop_loss_pct": 1.5,       # Tighter stop
                "trailing_stop_pct": 2.0     # Add trailing stop
            }
        }
    }

Data Models
-----------

ExecutionContext
~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class ExecutionContext:
        strategy_set: StrategySet
        applied_indicator_overrides: dict[str, dict[str, Any]]
        applied_strategy_overrides: dict[str, dict[str, Any]]
        original_state: dict[str, dict[str, Any]]

**Fields:**

* ``strategy_set``: The strategy set being executed
* ``applied_indicator_overrides``: Indicator overrides that were applied
* ``applied_strategy_overrides``: Strategy overrides that were applied
* ``original_state``: Original parameters before overrides

Override Patterns
-----------------

**Pattern 1: Volatility-Based Overrides**

.. code-block:: python

    # High volatility strategy set
    StrategySet(
        id="high_volatility",
        indicator_overrides={
            "atr": {"period": 10}  # Shorter ATR for faster response
        },
        strategy_overrides={
            "trend_following": {
                "risk": {
                    "stop_loss_pct": 3.5,      # Wider stop
                    "position_size_pct": 4.0    # Smaller position
                }
            }
        }
    )

    # Low volatility strategy set
    StrategySet(
        id="low_volatility",
        indicator_overrides={
            "atr": {"period": 20}  # Longer ATR for smoother signals
        },
        strategy_overrides={
            "trend_following": {
                "risk": {
                    "stop_loss_pct": 1.5,      # Tighter stop
                    "position_size_pct": 8.0    # Larger position
                }
            }
        }
    )

**Pattern 2: Timeframe-Based Overrides**

.. code-block:: python

    # Fast-moving markets
    StrategySet(
        id="fast_markets",
        indicator_overrides={
            "rsi_14": {"period": 7},      # Faster RSI
            "macd": {"fast": 8, "slow": 17, "signal": 9}  # Faster MACD
        }
    )

    # Slow-moving markets
    StrategySet(
        id="slow_markets",
        indicator_overrides={
            "rsi_14": {"period": 21},     # Slower RSI
            "macd": {"fast": 16, "slow": 34, "signal": 9}  # Slower MACD
        }
    )

**Pattern 3: Risk-Adjusted Overrides**

.. code-block:: python

    # Conservative (low confidence)
    StrategySet(
        id="conservative",
        strategy_overrides={
            "all_strategies": {
                "risk": {
                    "position_size_pct": 3.0,   # Smaller positions
                    "stop_loss_pct": 1.5        # Tighter stops
                }
            }
        }
    )

    # Aggressive (high confidence)
    StrategySet(
        id="aggressive",
        strategy_overrides={
            "all_strategies": {
                "risk": {
                    "position_size_pct": 10.0,  # Larger positions
                    "stop_loss_pct": 4.0,       # Wider stops
                    "trailing_stop_pct": 5.0    # Add trailing stop
                }
            }
        }
    )

State Management
----------------

**Lifecycle:**

1. **Initial State:**

   .. code-block:: python

       # Original parameters
       rsi.params = {"period": 14}
       strategy.risk.stop_loss_pct = 2.0

2. **Apply Overrides:**

   .. code-block:: python

       context = executor.prepare_execution(matched)
       # rsi.params = {"period": 10}  # Overridden
       # strategy.risk.stop_loss_pct = 3.0  # Overridden

3. **Execute Trades:**

   .. code-block:: python

       # Trade with overridden parameters
       execute_with_context(context)

4. **Restore State:**

   .. code-block:: python

       executor.restore_state()
       # rsi.params = {"period": 14}  # Restored
       # strategy.risk.stop_loss_pct = 2.0  # Restored

**Best Practices:**

.. code-block:: python

    # ✅ Good: Always restore state
    try:
        context = executor.prepare_execution(matched)
        execute_trades(context)
    finally:
        executor.restore_state()  # Ensure restoration even on error

    # ❌ Bad: Forget to restore
    context = executor.prepare_execution(matched)
    execute_trades(context)
    # Parameters stay overridden!

Integration Example
-------------------

**Complete Execution Flow:**

.. code-block:: python

    from src.core.tradingbot.config.executor import StrategySetExecutor
    from src.core.tradingbot.config.router import StrategyRouter
    from src.core.tradingbot.config.detector import RegimeDetector

    # 1. Detect active regimes
    detector = RegimeDetector(config.regimes)
    active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")

    # 2. Route to strategy set
    router = StrategyRouter(config.routing, config.strategy_sets)
    matched = router.route(active_regimes)

    if matched:
        # 3. Prepare execution with overrides
        executor = StrategySetExecutor(config.indicators, config.strategies)
        context = executor.prepare_execution(matched)

        try:
            # 4. Execute trades with overridden parameters
            print(f"Using strategy set: {context.strategy_set.name}")
            print(f"Indicator overrides: {context.applied_indicator_overrides}")
            print(f"Strategy overrides: {context.applied_strategy_overrides}")

            execute_trades_with_context(context)

        finally:
            # 5. Always restore original state
            executor.restore_state()
            print("Restored original parameters")

See Also
--------

* :doc:`config_router` - Routes regimes to strategy sets
* :doc:`config_models` - StrategySet model with overrides
* :doc:`bot_controller` - Uses executor for strategy switching
* :doc:`backtest_engine` - Applies overrides during backtesting
