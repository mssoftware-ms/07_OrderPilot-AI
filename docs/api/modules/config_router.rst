Configuration Router
====================

.. automodule:: src.core.tradingbot.config.router
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``StrategyRouter`` routes active regimes to strategy sets using routing rules:

* **Regime Matching**: all_of, any_of, none_of logic for flexible routing
* **Priority-Based Selection**: Highest priority rule wins when multiple match
* **Fallback Handling**: Optional default strategy set when no rules match
* **Matched Strategy Set**: Returns complete strategy set with metadata

Key Features
------------

**Flexible Matching:**
   all_of (AND), any_of (OR), none_of (NOT) for complex regime combinations.

**Priority Ordering:**
   Higher priority routing rules take precedence.

**Complete Result:**
   Returns MatchedStrategySet with strategy set, matched regimes, and routing rule.

**Validation:**
   Ensures referenced strategy sets and regimes exist.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.config.router import StrategyRouter
    from src.core.tradingbot.config.models import RoutingRule, RegimeMatch, StrategySet

    # Define routing rules
    routing_rules = [
        RoutingRule(
            regimes=RegimeMatch(all_of=["strong_uptrend", "normal_volatility"]),
            strategy_set_id="trending_aggressive",
            priority=10
        ),
        RoutingRule(
            regimes=RegimeMatch(any_of=["range_bound", "low_volatility"]),
            strategy_set_id="ranging_conservative",
            priority=5
        )
    ]

    # Define strategy sets
    strategy_sets = [
        StrategySet(id="trending_aggressive", ...),
        StrategySet(id="ranging_conservative", ...)
    ]

    # Initialize router
    router = StrategyRouter(routing_rules, strategy_sets)

    # Route based on active regimes
    active_regimes = [
        Regime(id="strong_uptrend", ...),
        Regime(id="normal_volatility", ...)
    ]

    matched = router.route(active_regimes)
    if matched:
        print(f"Matched strategy set: {matched.strategy_set.name}")
        print(f"Matched regimes: {[r.id for r in matched.matched_regimes]}")

Classes
-------

.. autoclass:: src.core.tradingbot.config.router.StrategyRouter
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

route(active_regimes)
~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.router.StrategyRouter.route

Route active regimes to a strategy set.

**Parameters:**

* ``active_regimes`` (list[Regime]): Currently active regimes from detector

**Returns:**

* ``MatchedStrategySet | None``: Matched strategy set with metadata, or None if no match

**Algorithm:**

1. **Sort rules by priority** (highest first)

2. **For each rule, check if regime match conditions satisfied:**

   - **all_of**: All specified regimes must be active
   - **any_of**: At least one specified regime must be active
   - **none_of**: None of the specified regimes can be active

3. **Return first matching rule's strategy set**

**Example:**

.. code-block:: python

    # Active regimes: uptrend + normal volatility
    active = [uptrend_regime, normal_vol_regime]

    matched = router.route(active)

    if matched:
        print(f"Strategy set: {matched.strategy_set.id}")
        print(f"Matched regimes: {matched.matched_regimes}")
        print(f"Routing rule: {matched.routing_rule.regimes}")
    else:
        print("No matching strategy set found")

_matches_rule(rule, active_regime_ids)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.router.StrategyRouter._matches_rule

**Internal method** - Check if active regimes match a routing rule.

**Matching Logic:**

.. code-block:: python

    def _matches_rule(rule, active_regime_ids):
        # Check all_of (AND logic)
        if rule.regimes.all_of:
            if not all(rid in active_regime_ids for rid in rule.regimes.all_of):
                return False

        # Check any_of (OR logic)
        if rule.regimes.any_of:
            if not any(rid in active_regime_ids for rid in rule.regimes.any_of):
                return False

        # Check none_of (NOT logic)
        if rule.regimes.none_of:
            if any(rid in active_regime_ids for rid in rule.regimes.none_of):
                return False

        return True

**Example:**

.. code-block:: python

    rule = RoutingRule(
        regimes=RegimeMatch(
            all_of=["uptrend"],
            none_of=["extreme_volatility"]
        ),
        strategy_set_id="trend_following"
    )

    active_ids = {"uptrend", "normal_volatility"}
    matches = router._matches_rule(rule, active_ids)  # True

    active_ids = {"uptrend", "extreme_volatility"}
    matches = router._matches_rule(rule, active_ids)  # False (none_of violated)

_get_strategy_set(strategy_set_id)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.router.StrategyRouter._get_strategy_set

**Internal method** - Retrieve strategy set by ID.

**Returns:**

* ``StrategySet | None``: Strategy set if found, None otherwise

Routing Match Types
-------------------

**all_of (AND Logic)**

**All specified regimes must be active.**

.. code-block:: python

    # Requires BOTH uptrend AND normal volatility
    RegimeMatch(all_of=["strong_uptrend", "normal_volatility"])

    # Matches: ["strong_uptrend", "normal_volatility"]
    # Matches: ["strong_uptrend", "normal_volatility", "high_volume"]
    # Does NOT match: ["strong_uptrend"]  # Missing normal_volatility
    # Does NOT match: ["normal_volatility"]  # Missing strong_uptrend

**any_of (OR Logic)**

**At least one specified regime must be active.**

.. code-block:: python

    # Requires uptrend OR downtrend
    RegimeMatch(any_of=["strong_uptrend", "strong_downtrend"])

    # Matches: ["strong_uptrend"]
    # Matches: ["strong_downtrend"]
    # Matches: ["strong_uptrend", "strong_downtrend"]
    # Does NOT match: ["range_bound"]  # Neither uptrend nor downtrend

**none_of (NOT Logic)**

**None of the specified regimes can be active.**

.. code-block:: python

    # Excludes extreme volatility
    RegimeMatch(
        all_of=["uptrend"],
        none_of=["extreme_volatility"]
    )

    # Matches: ["uptrend", "normal_volatility"]
    # Does NOT match: ["uptrend", "extreme_volatility"]  # Violates none_of

**Combined Logic**

.. code-block:: python

    # Complex rule: (Uptrend OR Downtrend) AND Normal Volatility AND NOT Extreme Conditions
    RegimeMatch(
        any_of=["strong_uptrend", "strong_downtrend"],
        all_of=["normal_volatility"],
        none_of=["extreme_volatility", "low_liquidity"]
    )

Common Routing Patterns
------------------------

**Pattern 1: Trend-Based Routing**

.. code-block:: python

    routing = [
        # Aggressive trend following in strong uptrend
        RoutingRule(
            regimes=RegimeMatch(all_of=["strong_uptrend", "normal_volatility"]),
            strategy_set_id="trending_aggressive",
            priority=10
        ),
        # Conservative trend following in moderate uptrend
        RoutingRule(
            regimes=RegimeMatch(all_of=["moderate_uptrend"]),
            strategy_set_id="trending_conservative",
            priority=5
        ),
        # Range strategies in sideways market
        RoutingRule(
            regimes=RegimeMatch(all_of=["range_bound"]),
            strategy_set_id="ranging",
            priority=3
        )
    ]

**Pattern 2: Volatility-Based Routing**

.. code-block:: python

    routing = [
        # Extreme volatility - pause or defensive strategies
        RoutingRule(
            regimes=RegimeMatch(all_of=["extreme_volatility"]),
            strategy_set_id="defensive",
            priority=10
        ),
        # High volatility - reduce position size
        RoutingRule(
            regimes=RegimeMatch(
                all_of=["high_volatility"],
                none_of=["extreme_volatility"]
            ),
            strategy_set_id="reduced_risk",
            priority=8
        ),
        # Normal volatility - standard strategies
        RoutingRule(
            regimes=RegimeMatch(all_of=["normal_volatility"]),
            strategy_set_id="standard",
            priority=5
        )
    ]

**Pattern 3: Multi-Condition Routing**

.. code-block:: python

    routing = [
        # Best conditions: trend + volume + favorable volatility
        RoutingRule(
            regimes=RegimeMatch(
                all_of=["strong_uptrend", "high_volume", "normal_volatility"],
                none_of=["extreme_volatility"]
            ),
            strategy_set_id="optimal_trending",
            priority=10
        ),
        # Good conditions: trend + favorable volatility
        RoutingRule(
            regimes=RegimeMatch(
                all_of=["moderate_uptrend", "normal_volatility"]
            ),
            strategy_set_id="standard_trending",
            priority=7
        ),
        # Fallback: any trend
        RoutingRule(
            regimes=RegimeMatch(
                any_of=["strong_uptrend", "moderate_uptrend"]
            ),
            strategy_set_id="basic_trending",
            priority=3
        )
    ]

Data Models
-----------

MatchedStrategySet
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class MatchedStrategySet:
        strategy_set: StrategySet
        matched_regimes: list[Regime]
        routing_rule: RoutingRule

**Fields:**

* ``strategy_set``: The matched strategy set to execute
* ``matched_regimes``: Regimes that caused the match
* ``routing_rule``: The routing rule that matched

Priority Handling
-----------------

**Priority determines routing order:**

.. code-block:: python

    routing = [
        RoutingRule(regimes=..., strategy_set_id="high_priority", priority=10),
        RoutingRule(regimes=..., strategy_set_id="medium_priority", priority=5),
        RoutingRule(regimes=..., strategy_set_id="low_priority", priority=1)
    ]

    # Evaluation order: high -> medium -> low
    # First matching rule wins

**Use Cases:**

1. **Critical Conditions First:**

   .. code-block:: python

       # Extreme volatility takes precedence over everything
       RoutingRule(regimes={"all_of": ["extreme_volatility"]}, priority=10)

2. **Specific Before General:**

   .. code-block:: python

       # Specific: strong uptrend + high volume (priority 8)
       RoutingRule(regimes={"all_of": ["strong_uptrend", "high_volume"]}, priority=8)

       # General: any uptrend (priority 5)
       RoutingRule(regimes={"any_of": ["uptrend"]}, priority=5)

Best Practices
--------------

**1. Use Priorities Wisely:**

.. code-block:: python

    # ✅ Good: Critical conditions have highest priority
    extreme_vol_rule = RoutingRule(..., priority=10)
    normal_rule = RoutingRule(..., priority=5)

    # ❌ Bad: All rules have same priority (ambiguous)
    rule1 = RoutingRule(..., priority=5)
    rule2 = RoutingRule(..., priority=5)

**2. Avoid Ambiguous Rules:**

.. code-block:: python

    # ❌ Bad: Overlapping rules with same priority
    rule1 = RoutingRule(regimes={"any_of": ["uptrend"]}, priority=5)
    rule2 = RoutingRule(regimes={"all_of": ["strong_uptrend"]}, priority=5)

    # ✅ Better: Distinct priorities
    rule1 = RoutingRule(regimes={"all_of": ["strong_uptrend"]}, priority=8)
    rule2 = RoutingRule(regimes={"any_of": ["uptrend"]}, priority=5)

**3. Provide Fallback:**

.. code-block:: python

    # Always include a catch-all low-priority rule
    RoutingRule(
        regimes=RegimeMatch(any_of=[]),  # Matches any state
        strategy_set_id="default",
        priority=0
    )

See Also
--------

* :doc:`config_detector` - Detects active regimes for routing
* :doc:`config_executor` - Executes matched strategy set with overrides
* :doc:`config_models` - RoutingRule and RegimeMatch models
* :doc:`bot_controller` - Uses router for strategy switching
