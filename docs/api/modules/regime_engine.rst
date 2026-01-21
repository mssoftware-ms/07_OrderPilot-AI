Regime Engine
=============

.. automodule:: src.core.tradingbot.regime_engine
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``RegimeEngine`` classifies market conditions into distinct regimes based on technical indicators:

* **Trend Direction**: TREND_UP, TREND_DOWN, RANGE
* **Volatility Level**: LOW, NORMAL, HIGH, EXTREME

This classification enables dynamic strategy adaptation based on current market state.

Key Features
------------

**Multi-Dimensional Classification:**
   Independently classifies trend direction and volatility level.

**Confidence Scoring:**
   Provides confidence score (0-1) for each regime classification.

**Change Detection:**
   Identifies significant regime changes for position adjustment triggers.

**Configurable Thresholds:**
   Customizable ADX, ATR, and Bollinger Band thresholds.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.regime_engine import RegimeEngine
    from src.core.tradingbot.feature_vector import FeatureVector

    # Initialize engine
    engine = RegimeEngine()

    # Classify current market state
    features = FeatureVector(
        adx=32.5,
        plus_di=28.0,
        minus_di=15.0,
        atr_pct=2.8,
        bb_width=0.045,
        rsi=58.2
    )

    regime = engine.classify(features)
    print(f"Regime: {regime.regime.name}")  # TREND_UP
    print(f"Volatility: {regime.volatility.name}")  # NORMAL
    print(f"Confidence: {regime.regime_confidence:.2%}")  # 85.00%

Classes
-------

.. autoclass:: src.core.tradingbot.regime_engine.RegimeEngine
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

classify(features)
~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_engine.RegimeEngine.classify

Classify current market regime based on feature vector.

**Parameters:**

* ``features`` (FeatureVector): Current market indicators

**Returns:**

* ``RegimeState``: Classification result with regime type, volatility, and confidence

**Algorithm:**

1. **Trend Classification** (uses ADX and ±DI):

   * TREND_UP: ADX > threshold AND +DI > -DI
   * TREND_DOWN: ADX > threshold AND -DI > +DI
   * RANGE: ADX < threshold

2. **Volatility Classification** (uses ATR% and BB Width):

   * LOW: ATR% < 1.5% OR BB Width < 0.02
   * NORMAL: 1.5% ≤ ATR% ≤ 3.0%
   * HIGH: 3.0% < ATR% ≤ 5.0%
   * EXTREME: ATR% > 5.0%

**Example:**

.. code-block:: python

    regime = engine.classify(features)
    if regime.regime == RegimeType.TREND_UP and regime.volatility == VolatilityLevel.NORMAL:
        print("Good conditions for trend following strategy")

_classify_regime(features)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_engine.RegimeEngine._classify_regime

**Internal method** - Determine trend direction.

**Logic:**

.. code-block:: python

    if adx < adx_threshold:
        return RegimeType.RANGE
    elif plus_di > minus_di:
        return RegimeType.TREND_UP
    else:
        return RegimeType.TREND_DOWN

_classify_volatility(features)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_engine.RegimeEngine._classify_volatility

**Internal method** - Determine volatility level using dual-metric approach.

**Metrics:**

1. **ATR Percentage**: Normalized volatility (ATR / Price)
2. **Bollinger Band Width**: Price range / Middle band

**Thresholds:**

.. code-block:: python

    if atr_pct < 1.5 or bb_width < 0.02:
        return VolatilityLevel.LOW
    elif atr_pct <= 3.0:
        return VolatilityLevel.NORMAL
    elif atr_pct <= 5.0:
        return VolatilityLevel.HIGH
    else:
        return VolatilityLevel.EXTREME

detect_regime_change(current_regime, new_regime)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_engine.RegimeEngine.detect_regime_change

Detect significant regime changes that require action.

**Returns:**

* ``bool``: True if regime type OR volatility changed

**Use Case:**

Trigger position adjustments when market conditions shift significantly.

**Example:**

.. code-block:: python

    old_regime = engine.classify(previous_features)
    new_regime = engine.classify(current_features)

    if engine.detect_regime_change(old_regime, new_regime):
        print(f"Regime changed: {old_regime.regime} → {new_regime.regime}")
        adjust_positions(new_regime)

Data Models
-----------

RegimeType (Enum)
~~~~~~~~~~~~~~~~~

.. code-block:: python

    class RegimeType(Enum):
        TREND_UP = "TREND_UP"      # Strong uptrend (ADX > 25, +DI > -DI)
        TREND_DOWN = "TREND_DOWN"  # Strong downtrend (ADX > 25, -DI > +DI)
        RANGE = "RANGE"            # Sideways/choppy (ADX < 25)

VolatilityLevel (Enum)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class VolatilityLevel(Enum):
        LOW = "LOW"          # ATR% < 1.5%
        NORMAL = "NORMAL"    # 1.5% ≤ ATR% ≤ 3.0%
        HIGH = "HIGH"        # 3.0% < ATR% ≤ 5.0%
        EXTREME = "EXTREME"  # ATR% > 5.0%

RegimeState (Dataclass)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class RegimeState:
        regime: RegimeType
        volatility: VolatilityLevel
        regime_confidence: float  # 0-1
        adx: float
        atr_pct: float
        timestamp: datetime

Configuration
-------------

Default thresholds can be overridden:

.. code-block:: python

    engine = RegimeEngine(
        adx_threshold=20.0,      # Lower threshold = more trend signals
        atr_low_threshold=1.0,   # Custom volatility thresholds
        atr_high_threshold=4.0,
        atr_extreme_threshold=6.0
    )

Best Practices
--------------

**1. Combine with Regime Stability Tracking:**

Avoid acting on every regime change. Use ``RegimeStabilityTracker`` to filter noise.

**2. Use Confidence Scores:**

.. code-block:: python

    if regime.regime_confidence > 0.75:
        # High confidence - safe to trade
        execute_strategy()
    else:
        # Low confidence - wait for confirmation
        wait_for_next_bar()

**3. Multi-Timeframe Analysis:**

.. code-block:: python

    regime_5m = engine.classify(features_5m)
    regime_1h = engine.classify(features_1h)

    # Only trade if both timeframes agree
    if regime_5m.regime == regime_1h.regime == RegimeType.TREND_UP:
        enter_long()

See Also
--------

* :doc:`bot_controller` - Uses regime classification for strategy switching
* :doc:`regime_stability` - Tracks regime stability over time
* :doc:`config_detector` - JSON-based regime detection
* :doc:`entry_scorer` - Uses regime for entry scoring
