Bot Controller
==============

.. automodule:: src.core.tradingbot.bot_controller
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``BotController`` is the main orchestrator for regime-based trading operations. It coordinates:

* Market data processing
* Regime detection and classification
* Strategy routing and switching
* Position management
* Risk management
* Event emission

Key Features
------------

**Regime-Based Strategy Switching:**
   Automatically switches between strategies based on detected market regimes.

**Parameter Overrides:**
   Applies temporary parameter modifications when switching strategies.

**Position Adjustment:**
   Adjusts stop losses and position sizes based on regime changes.

**Event Bus Integration:**
   Emits events for regime changes, strategy switches, and position updates.

**Activity Logging:**
   Comprehensive logging of all trading decisions and regime changes.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.bot_controller import BotController
    from src.core.tradingbot.config.loader import ConfigLoader

    # Load JSON configuration
    config_loader = ConfigLoader()
    config = config_loader.load_config("config.json")

    # Initialize bot controller
    bot = BotController()
    bot.set_json_config(config)

    # Start trading
    bot.start()

Classes
-------

.. autoclass:: src.core.tradingbot.bot_controller.BotController
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

set_json_config(config_path)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.bot_controller.BotController.set_json_config

Load and validate a JSON configuration file.

**Parameters:**

* ``config_path`` (str | Path): Path to JSON configuration file

**Raises:**

* ``ValueError``: If config is invalid
* ``FileNotFoundError``: If config file not found

**Example:**

.. code-block:: python

    bot.set_json_config("03_JSON/Trading_Bot/my_strategy.json")

_switch_strategy(matched_strategy_set)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.bot_controller.BotController._switch_strategy

Switch to a new strategy set when regime changes.

**Internal method** - Called automatically when regime change detected.

**Features:**

* Applies parameter overrides from strategy set
* Adjusts open positions for new regime
* Logs strategy switch event
* Emits regime_changed event

_adjust_positions_for_new_regime()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.bot_controller.BotController._adjust_positions_for_new_regime

Adjust position risk parameters based on new regime.

**Adjustments:**

* **High/Extreme Volatility:** Tighten stops by 30%
* **Low Volatility:** Loosen stops by 20%
* **Trend Reversal:** Log warning (LONG in downtrend, SHORT in uptrend)

**Example Output:**

.. code-block:: text

    HIGH volatility detected: tightened stop from $95,000 to $96,500 (30% tighter)

_has_regime_changed(new_regime)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.bot_controller.BotController._has_regime_changed

Check if regime has changed significantly.

**Returns:**

* ``bool``: True if regime type or volatility changed

**Logic:**

.. code-block:: python

    return (
        new_regime.regime != current_regime.regime or
        new_regime.volatility != current_regime.volatility
    )

Events Emitted
--------------

regime_changed
~~~~~~~~~~~~~~

Emitted when market regime changes.

**Payload:**

.. code-block:: python

    {
        "old_regime": RegimeState,
        "new_regime": RegimeState,
        "new_strategy": str
    }

**Example Listener:**

.. code-block:: python

    def on_regime_changed(event):
        print(f"Regime changed: {event['old_regime'].regime} → {event['new_regime'].regime}")
        print(f"New strategy: {event['new_strategy']}")

    bot.event_bus.on("regime_changed", on_regime_changed)

Activity Log Events
-------------------

The bot controller logs these activity types:

* ``REGIME_CHANGE``: Regime transition detected
* ``STRATEGY_SWITCH``: Strategy set changed
* ``OVERRIDE``: Parameter overrides applied
* ``POSITION_ADJUST``: Position risk adjusted
* ``WARNING``: Risk warnings (trend reversal, oscillation)
* ``ERROR``: Error conditions

See Also
--------

* :doc:`regime_engine` - Regime classification
* :doc:`config_router` - Strategy routing
* :doc:`config_executor` - Parameter overrides
* :doc:`regime_stability` - Stability tracking
