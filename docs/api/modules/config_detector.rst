Configuration Detector
======================

.. automodule:: src.core.tradingbot.config.detector
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``RegimeDetector`` detects active regimes from JSON configurations:

* **Multi-Regime Detection**: Evaluates all regime definitions simultaneously
* **Scope Filtering**: Filters regimes by scope (ENTRY, EXIT, IN_TRADE, GLOBAL)
* **Priority Sorting**: Returns regimes sorted by priority (highest first)
* **Condition Evaluation**: Uses ConditionEvaluator for regime condition checks

Key Features
------------

**Scope-Based Detection:**
   Different regimes evaluated at different lifecycle stages (entry, exit, in-trade).

**Priority Ordering:**
   Higher priority regimes take precedence in routing decisions.

**Flexible Evaluation:**
   Supports complex nested conditions with AND/OR logic.

**Performance Optimized:**
   Evaluates only regimes matching requested scope.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.config.detector import RegimeDetector
    from src.core.tradingbot.config.models import Regime, RegimeScope

    # Define regimes
    regimes = [
        Regime(
            id="strong_uptrend",
            name="Strong Uptrend",
            conditions=ConditionGroup(all=[...]),
            scope=RegimeScope.ENTRY,
            priority=10
        ),
        Regime(
            id="high_volatility",
            name="High Volatility",
            conditions=ConditionGroup(all=[...]),
            scope=RegimeScope.GLOBAL,
            priority=5
        )
    ]

    # Initialize detector
    detector = RegimeDetector(regimes)

    # Current indicator values
    indicator_values = {
        "adx": 32.5,
        "plus_di": 28.0,
        "minus_di": 15.0,
        "atr_pct": 3.2,
        "rsi_14": 62.5
    }

    # Detect active regimes for entry
    active_regimes = detector.detect_active_regimes(
        indicator_values,
        scope="entry"
    )

    print(f"Active regimes: {[r.id for r in active_regimes]}")
    # Output: ['strong_uptrend'] (high_volatility filtered out due to scope)

Classes
-------

.. autoclass:: src.core.tradingbot.config.detector.RegimeDetector
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

detect_active_regimes(indicator_values, scope)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.detector.RegimeDetector.detect_active_regimes

Detect all active regimes matching scope and conditions.

**Parameters:**

* ``indicator_values`` (dict[str, float]): Current indicator values
* ``scope`` (str, optional): Filter by scope ("entry", "exit", "in_trade", "global", None for all)

**Returns:**

* ``list[Regime]``: Active regimes sorted by priority (descending)

**Algorithm:**

1. **Filter by Scope:**

   .. code-block:: python

       if scope:
           candidate_regimes = [r for r in self.regimes if r.scope == scope or r.scope == "global"]
       else:
           candidate_regimes = self.regimes

2. **Evaluate Conditions:**

   .. code-block:: python

       active_regimes = []
       for regime in candidate_regimes:
           if self.evaluator.evaluate(regime.conditions, indicator_values):
               active_regimes.append(regime)

3. **Sort by Priority:**

   .. code-block:: python

       active_regimes.sort(key=lambda r: r.priority, reverse=True)

**Example:**

.. code-block:: python

    # Entry scope (only ENTRY and GLOBAL regimes evaluated)
    active_regimes = detector.detect_active_regimes(
        indicator_values,
        scope="entry"
    )

    # All scopes
    active_regimes = detector.detect_active_regimes(
        indicator_values,
        scope=None
    )

    # Check specific regime
    uptrend_active = any(r.id == "strong_uptrend" for r in active_regimes)

_filter_by_scope(regimes, scope)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.detector.RegimeDetector._filter_by_scope

**Internal method** - Filter regimes by scope.

**Scope Logic:**

.. code-block:: python

    if scope is None:
        return regimes  # No filtering

    # Include regimes matching requested scope OR global scope
    return [
        r for r in regimes
        if r.scope == scope or r.scope == RegimeScope.GLOBAL
    ]

**Scope Meanings:**

* **ENTRY**: Evaluated before opening position (e.g., trend detection)
* **EXIT**: Evaluated on every bar while in position (e.g., exit signals)
* **IN_TRADE**: Evaluated only while in position (e.g., trailing stops)
* **GLOBAL**: Evaluated at all times (e.g., volatility regimes)

_sort_by_priority(regimes)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.detector.RegimeDetector._sort_by_priority

**Internal method** - Sort regimes by priority.

**Sorting:**

.. code-block:: python

    return sorted(regimes, key=lambda r: r.priority, reverse=True)

**Priority Guidelines:**

* **10**: Critical regimes (e.g., extreme volatility)
* **5-9**: Important regimes (e.g., strong trends)
* **1-4**: Normal regimes (e.g., moderate trends)
* **0**: Low priority (e.g., informational)

Regime Scopes Explained
------------------------

**ENTRY Scope**

**When Evaluated:** Before opening a position

**Use Cases:**
- Trend detection (uptrend, downtrend, range)
- Market condition classification
- Entry timing filters

**Example:**

.. code-block:: python

    regime = Regime(
        id="strong_uptrend",
        name="Strong Uptrend",
        conditions=ConditionGroup(all=[
            Condition(left={"indicator": "adx"}, op="gt", right={"value": 25}),
            Condition(left={"indicator": "plus_di"}, op="gt", right={"indicator": "minus_di"})
        ]),
        scope=RegimeScope.ENTRY,
        priority=10
    )

**EXIT Scope**

**When Evaluated:** On every bar while in position

**Use Cases:**
- Exit signal detection
- Stop loss/take profit conditions
- Trend reversal detection

**Example:**

.. code-block:: python

    regime = Regime(
        id="trend_reversal",
        name="Trend Reversal Detected",
        conditions=ConditionGroup(any=[
            Condition(left={"indicator": "rsi_14"}, op="gt", right={"value": 75}),
            Condition(left={"indicator": "macd_histogram"}, op="lt", right={"value": 0})
        ]),
        scope=RegimeScope.EXIT,
        priority=8
    )

**IN_TRADE Scope**

**When Evaluated:** Only while position is open

**Use Cases:**
- Trailing stop adjustments
- Position size scaling
- In-trade risk management

**Example:**

.. code-block:: python

    regime = Regime(
        id="trailing_stop_tightening",
        name="Tighten Trailing Stop",
        conditions=ConditionGroup(all=[
            Condition(left={"indicator": "profit_pct"}, op="gt", right={"value": 5.0}),
            Condition(left={"indicator": "volatility"}, op="lt", right={"value": 2.0})
        ]),
        scope=RegimeScope.IN_TRADE,
        priority=5
    )

**GLOBAL Scope**

**When Evaluated:** At all times (all scopes)

**Use Cases:**
- Market-wide conditions (volatility, liquidity)
- Risk-off events
- Cross-regime conditions

**Example:**

.. code-block:: python

    regime = Regime(
        id="extreme_volatility",
        name="Extreme Volatility",
        conditions=ConditionGroup(any=[
            Condition(left={"indicator": "atr_pct"}, op="gt", right={"value": 5.0}),
            Condition(left={"indicator": "vix"}, op="gt", right={"value": 30})
        ]),
        scope=RegimeScope.GLOBAL,
        priority=10
    )

Common Detection Patterns
--------------------------

**Pattern 1: Multi-Regime Detection**

.. code-block:: python

    # Detect all active entry regimes
    active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")

    # Check for specific combinations
    has_uptrend = any(r.id == "strong_uptrend" for r in active_regimes)
    has_low_volatility = any(r.id == "low_volatility" for r in active_regimes)

    if has_uptrend and has_low_volatility:
        print("Good conditions for trend following")

**Pattern 2: Priority-Based Selection**

.. code-block:: python

    # Get highest priority active regime
    active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")

    if active_regimes:
        primary_regime = active_regimes[0]  # Highest priority
        print(f"Primary regime: {primary_regime.name} (priority {primary_regime.priority})")

**Pattern 3: Scope-Specific Detection**

.. code-block:: python

    # Different regimes for different lifecycle stages
    entry_regimes = detector.detect_active_regimes(indicator_values, scope="entry")
    exit_regimes = detector.detect_active_regimes(indicator_values, scope="exit")

    print(f"Entry regimes: {[r.id for r in entry_regimes]}")
    print(f"Exit regimes: {[r.id for r in exit_regimes]}")

**Pattern 4: Global + Specific**

.. code-block:: python

    # Global regimes apply everywhere
    active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")

    # Will include both ENTRY and GLOBAL regimes
    for regime in active_regimes:
        print(f"{regime.id} (scope: {regime.scope})")

Integration Example
-------------------

**Complete Detection Flow:**

.. code-block:: python

    from src.core.tradingbot.config.detector import RegimeDetector
    from src.core.tradingbot.config.loader import ConfigLoader
    from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

    # 1. Load configuration
    loader = ConfigLoader()
    config = loader.load_config("strategy.json")

    # 2. Initialize detector
    detector = RegimeDetector(config.regimes)

    # 3. Calculate indicator values from features
    calculator = IndicatorValueCalculator()
    features = get_current_features()  # FeatureVector from feature engine
    indicator_values = calculator.calculate(features)

    # 4. Detect active regimes
    active_regimes = detector.detect_active_regimes(
        indicator_values,
        scope="entry"
    )

    # 5. Use for routing
    if active_regimes:
        print(f"Detected {len(active_regimes)} active regimes")
        for regime in active_regimes:
            print(f"  - {regime.name} (priority {regime.priority})")
    else:
        print("No active regimes detected")

Best Practices
--------------

**1. Use Priority Wisely:**

.. code-block:: python

    # Higher priority for critical conditions
    extreme_volatility = Regime(..., priority=10)
    normal_volatility = Regime(..., priority=5)

    # Ensures extreme conditions take precedence

**2. Scope Appropriately:**

.. code-block:: python

    # ✅ Good: Trend detection at entry
    uptrend = Regime(..., scope=RegimeScope.ENTRY)

    # ✅ Good: Exit signals while in trade
    profit_target = Regime(..., scope=RegimeScope.EXIT)

    # ❌ Bad: Exit signals at entry (won't be evaluated)
    profit_target = Regime(..., scope=RegimeScope.ENTRY)

**3. Avoid Overlapping Regimes:**

.. code-block:: python

    # ❌ Bad: Both can be true simultaneously
    regime1 = Regime(id="uptrend", conditions=ConditionGroup(all=[
        Condition(left={"indicator": "adx"}, op="gt", right={"value": 20})
    ]))
    regime2 = Regime(id="strong_uptrend", conditions=ConditionGroup(all=[
        Condition(left={"indicator": "adx"}, op="gt", right={"value": 25})
    ]))

    # ✅ Better: Use mutually exclusive conditions or different priorities
    regime1 = Regime(id="moderate_uptrend", priority=5, conditions=...)
    regime2 = Regime(id="strong_uptrend", priority=10, conditions=...)

See Also
--------

* :doc:`config_evaluator` - Evaluates regime conditions
* :doc:`config_router` - Routes based on detected regimes
* :doc:`config_models` - Regime model definitions
* :doc:`regime_engine` - Hardcoded regime classification (alternative approach)
