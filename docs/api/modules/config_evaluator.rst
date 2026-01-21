Configuration Evaluator
=======================

.. automodule:: src.core.tradingbot.config.evaluator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``ConditionEvaluator`` evaluates conditions and condition groups from JSON configurations:

* **Operator-Based Conditions**: GT, LT, EQ, BETWEEN comparisons
* **Recursive Group Evaluation**: AND/OR logic with nested groups
* **Operand Resolution**: Resolves indicator references and constant values
* **Type-Safe Evaluation**: Handles numeric, boolean, and string comparisons

Key Features
------------

**Operator Support:**
   GT, LT, EQ, GTE, LTE, BETWEEN for flexible comparisons.

**Nested Logic:**
   Recursive evaluation of AND/OR groups with unlimited nesting depth.

**Indicator Resolution:**
   Automatically resolves indicator IDs to current values from indicator_values dict.

**Offset/Multiplier Support:**
   Applies offset (e.g., +2%) and multiplier (e.g., 1.5x) to operand values.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.config.evaluator import ConditionEvaluator
    from src.core.tradingbot.config.models import Condition, ConditionGroup, OperandValue

    # Initialize evaluator
    evaluator = ConditionEvaluator()

    # Current indicator values
    indicator_values = {
        "rsi_14": 62.5,
        "price": 50000.0,
        "sma_50": 49500.0,
        "volume": 1500000,
        "volume_sma": 1200000
    }

    # Simple condition: RSI > 50
    condition = Condition(
        left=OperandValue(indicator="rsi_14"),
        op="gt",
        right=OperandValue(value=50)
    )

    result = evaluator.evaluate_condition(condition, indicator_values)
    print(result)  # True (62.5 > 50)

    # Complex group: (RSI > 50 AND Price > SMA 50) OR (Volume > 1.5 * Volume SMA)
    group = ConditionGroup(
        any=[
            ConditionGroup(
                all=[
                    Condition(left={"indicator": "rsi_14"}, op="gt", right={"value": 50}),
                    Condition(left={"indicator": "price"}, op="gt", right={"indicator": "sma_50"})
                ]
            ),
            Condition(left={"indicator": "volume"}, op="gt", right={"indicator": "volume_sma", "multiplier": 1.5})
        ]
    )

    result = evaluator.evaluate_group(group, indicator_values)
    print(result)  # True

Classes
-------

.. autoclass:: src.core.tradingbot.config.evaluator.ConditionEvaluator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

evaluate_condition(condition, indicator_values)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.evaluator.ConditionEvaluator.evaluate_condition

Evaluate a single condition.

**Parameters:**

* ``condition`` (Condition): Condition to evaluate
* ``indicator_values`` (dict[str, float]): Current indicator values

**Returns:**

* ``bool``: Evaluation result

**Supported Operators:**

.. code-block:: python

    "gt": left > right
    "lt": left < right
    "eq": left == right
    "gte": left >= right
    "lte": left <= right
    "between": min_value <= left <= max_value

**Example:**

.. code-block:: python

    # GT: RSI > 50
    condition = Condition(left={"indicator": "rsi_14"}, op="gt", right={"value": 50})
    result = evaluator.evaluate_condition(condition, {"rsi_14": 62.5})  # True

    # BETWEEN: Price between SMA 20 and SMA 50
    condition = Condition(
        left={"indicator": "price"},
        op="between",
        right={"value": [{"indicator": "sma_20"}, {"indicator": "sma_50"}]}
    )
    result = evaluator.evaluate_condition(condition, {
        "price": 49800.0,
        "sma_20": 49500.0,
        "sma_50": 50500.0
    })  # True

evaluate_group(group, indicator_values)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.evaluator.ConditionEvaluator.evaluate_group

Evaluate a condition group with AND/OR logic.

**Parameters:**

* ``group`` (ConditionGroup): Condition group to evaluate
* ``indicator_values`` (dict[str, float]): Current indicator values

**Returns:**

* ``bool``: Evaluation result

**Logic:**

.. code-block:: python

    # AND logic (all conditions must be true)
    if group.all:
        return all(evaluate(c, indicator_values) for c in group.all)

    # OR logic (at least one condition must be true)
    if group.any:
        return any(evaluate(c, indicator_values) for c in group.any)

**Recursion:**

Groups can contain nested groups for complex logic:

.. code-block:: python

    # (A AND B) OR (C AND D)
    group = ConditionGroup(
        any=[
            ConditionGroup(all=[condition_A, condition_B]),
            ConditionGroup(all=[condition_C, condition_D])
        ]
    )

**Example:**

.. code-block:: python

    # All conditions must be true (AND)
    group = ConditionGroup(
        all=[
            Condition(left={"indicator": "rsi_14"}, op="gt", right={"value": 50}),
            Condition(left={"indicator": "adx"}, op="gt", right={"value": 25}),
            Condition(left={"indicator": "volume"}, op="gt", right={"indicator": "volume_sma"})
        ]
    )
    result = evaluator.evaluate_group(group, indicator_values)

    # At least one condition must be true (OR)
    group = ConditionGroup(
        any=[
            Condition(left={"indicator": "rsi_14"}, op="lt", right={"value": 30}),
            Condition(left={"indicator": "rsi_14"}, op="gt", right={"value": 70})
        ]
    )
    result = evaluator.evaluate_group(group, indicator_values)

_resolve_operand(operand, indicator_values)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.evaluator.ConditionEvaluator._resolve_operand

**Internal method** - Resolve operand to numeric value.

**Resolution Logic:**

1. **Indicator Reference:**

   .. code-block:: python

       operand = OperandValue(indicator="rsi_14")
       value = indicator_values["rsi_14"]  # 62.5

2. **Constant Value:**

   .. code-block:: python

       operand = OperandValue(value=50)
       value = 50

3. **With Offset (+2%):**

   .. code-block:: python

       operand = OperandValue(indicator="sma_50", offset=1.02)
       base_value = indicator_values["sma_50"]  # 49500.0
       value = base_value * 1.02  # 50490.0

4. **With Multiplier (1.5x):**

   .. code-block:: python

       operand = OperandValue(indicator="volume_sma", multiplier=1.5)
       base_value = indicator_values["volume_sma"]  # 1200000
       value = base_value * 1.5  # 1800000

5. **Array Value (for BETWEEN):**

   .. code-block:: python

       operand = OperandValue(value=[
           {"indicator": "sma_20"},
           {"indicator": "sma_50"}
       ])
       value = [
           indicator_values["sma_20"],  # 49500.0
           indicator_values["sma_50"]   # 50500.0
       ]

_compare(left, op, right)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.evaluator.ConditionEvaluator._compare

**Internal method** - Perform operator comparison.

**Implementation:**

.. code-block:: python

    if op == "gt":
        return left > right
    elif op == "lt":
        return left < right
    elif op == "eq":
        return left == right
    elif op == "gte":
        return left >= right
    elif op == "lte":
        return left <= right
    elif op == "between":
        min_val, max_val = right
        return min_val <= left <= max_val

Common Patterns
---------------

**Pattern 1: Trend Confirmation**

.. code-block:: python

    # Uptrend: Price > SMA 50 AND ADX > 25 AND +DI > -DI
    group = ConditionGroup(
        all=[
            Condition(left={"indicator": "price"}, op="gt", right={"indicator": "sma_50"}),
            Condition(left={"indicator": "adx"}, op="gt", right={"value": 25}),
            Condition(left={"indicator": "plus_di"}, op="gt", right={"indicator": "minus_di"})
        ]
    )

**Pattern 2: Oversold/Overbought**

.. code-block:: python

    # Oversold: RSI < 30 OR Price < Lower Bollinger Band
    group = ConditionGroup(
        any=[
            Condition(left={"indicator": "rsi_14"}, op="lt", right={"value": 30}),
            Condition(left={"indicator": "price"}, op="lt", right={"indicator": "bb_lower"})
        ]
    )

**Pattern 3: Range Detection**

.. code-block:: python

    # Range: ADX < 20 AND Price between SMA 20 and SMA 50
    group = ConditionGroup(
        all=[
            Condition(left={"indicator": "adx"}, op="lt", right={"value": 20}),
            Condition(
                left={"indicator": "price"},
                op="between",
                right={"value": [{"indicator": "sma_20"}, {"indicator": "sma_50"}]}
            )
        ]
    )

**Pattern 4: Volume Confirmation**

.. code-block:: python

    # High volume: Volume > 1.5 * Average Volume
    condition = Condition(
        left={"indicator": "volume"},
        op="gt",
        right={"indicator": "volume_sma", "multiplier": 1.5}
    )

Error Handling
--------------

**Missing Indicator:**

.. code-block:: python

    try:
        result = evaluator.evaluate_condition(
            Condition(left={"indicator": "nonexistent"}, op="gt", right={"value": 50}),
            indicator_values
        )
    except KeyError as e:
        print(f"Indicator not found: {e}")

**Invalid Operator:**

.. code-block:: python

    try:
        result = evaluator.evaluate_condition(
            Condition(left={"indicator": "rsi_14"}, op="invalid", right={"value": 50}),
            indicator_values
        )
    except ValueError as e:
        print(f"Invalid operator: {e}")

**Type Mismatch:**

.. code-block:: python

    # Comparing number to string will raise TypeError
    try:
        result = evaluator.evaluate_condition(
            Condition(left={"indicator": "rsi_14"}, op="eq", right={"value": "not_a_number"}),
            indicator_values
        )
    except TypeError as e:
        print(f"Type mismatch: {e}")

Best Practices
--------------

**1. Pre-validate Indicator IDs:**

.. code-block:: python

    def validate_indicators(condition, available_indicators):
        """Ensure all referenced indicators exist."""
        required = extract_indicator_ids(condition)
        missing = required - set(available_indicators.keys())
        if missing:
            raise ValueError(f"Missing indicators: {missing}")

**2. Use Type-Safe Comparisons:**

.. code-block:: python

    # ✅ Good: Compare numbers
    Condition(left={"indicator": "rsi_14"}, op="gt", right={"value": 50})

    # ❌ Bad: Mixed types
    Condition(left={"indicator": "rsi_14"}, op="eq", right={"value": "50"})

**3. Simplify Complex Logic:**

.. code-block:: python

    # ❌ Hard to read
    group = ConditionGroup(any=[ConditionGroup(all=[...]), ConditionGroup(all=[...])])

    # ✅ Better: Break into named sub-groups
    uptrend_group = ConditionGroup(all=[...])
    high_volume_group = ConditionGroup(all=[...])
    group = ConditionGroup(any=[uptrend_group, high_volume_group])

See Also
--------

* :doc:`config_models` - Condition and ConditionGroup models
* :doc:`config_detector` - Uses evaluator for regime detection
* :doc:`config_loader` - Loads conditions from JSON
* :doc:`bot_controller` - Uses evaluated conditions for trading decisions
