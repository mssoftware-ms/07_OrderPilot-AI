Entry Scorer
============

.. automodule:: src.core.tradingbot.entry_scorer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``EntryScorer`` evaluates trade entry quality using a multi-component scoring system:

* **Component-Based Scoring**: 7 independent scoring components
* **Weighted Aggregation**: Configurable weights per component
* **Strategy-Specific Rules**: Custom scoring logic per strategy type
* **Detailed Breakdown**: Per-component scores for analysis

Key Features
------------

**Multi-Component Analysis:**
   Evaluates entries across 7 dimensions (trend, momentum, strength, mean reversion, volume, regime match, custom rules).

**Strategy Adaptability:**
   Different scoring profiles for trend-following, mean-reversion, breakout strategies.

**Transparency:**
   Returns detailed breakdown showing which components contributed to final score.

**Configurable Weights:**
   Customize component importance per strategy.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.entry_scorer import EntryScorer
    from src.core.tradingbot.feature_vector import FeatureVector
    from src.core.tradingbot.regime_engine import RegimeState

    # Initialize scorer
    scorer = EntryScorer()

    # Evaluate entry
    features = FeatureVector(
        sma_fast=50100.0,
        sma_slow=49800.0,
        rsi=62.5,
        macd_line=120.0,
        macd_signal=100.0,
        adx=28.5,
        volume=1500000,
        volume_sma=1200000
    )

    regime = RegimeState(...)
    direction = "LONG"

    result = scorer.calculate_score(features, regime, direction)
    print(f"Entry Score: {result.total_score:.2f}/1.00")
    print(f"Components: {result.component_scores}")

    # Output:
    # Entry Score: 0.78/1.00
    # Components: {
    #   'trend_alignment': 0.85,
    #   'rsi_momentum': 0.75,
    #   'macd_momentum': 0.80,
    #   'trend_strength': 0.70,
    #   'volume': 0.82,
    #   'regime_match': 0.90
    # }

Classes
-------

.. autoclass:: src.core.tradingbot.entry_scorer.EntryScorer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

calculate_score(features, regime, direction, strategy_type)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer.calculate_score

Calculate comprehensive entry quality score.

**Parameters:**

* ``features`` (FeatureVector): Current market indicators
* ``regime`` (RegimeState): Current market regime
* ``direction`` (str): "LONG" or "SHORT"
* ``strategy_type`` (str, optional): "trend_following", "mean_reversion", "breakout"

**Returns:**

* ``EntryScore``: Result with total_score (0-1) and component_scores dict

**Scoring Components:**

1. **Trend Alignment** (0.20 weight):
   - LONG: Fast SMA > Slow SMA (bullish alignment)
   - SHORT: Fast SMA < Slow SMA (bearish alignment)

2. **RSI Momentum** (0.15 weight):
   - LONG: RSI > 50 (bullish momentum)
   - SHORT: RSI < 50 (bearish momentum)

3. **MACD Momentum** (0.15 weight):
   - LONG: MACD line > signal (bullish crossover)
   - SHORT: MACD line < signal (bearish crossover)

4. **Trend Strength** (0.15 weight):
   - ADX-based: Higher ADX = stronger trend
   - Scales 0-1 based on ADX value (25-50 range)

5. **Mean Reversion** (0.10 weight):
   - Bollinger Band position (extremes = high score)

6. **Volume Confirmation** (0.10 weight):
   - Volume above average = better entry

7. **Regime Match** (0.15 weight):
   - Entry aligns with current regime type

**Example:**

.. code-block:: python

    # Trend-following entry
    score = scorer.calculate_score(features, regime, "LONG", "trend_following")
    if score.total_score > 0.70:
        print("High quality trend-following entry")

    # Mean-reversion entry
    score = scorer.calculate_score(features, regime, "LONG", "mean_reversion")
    if score.total_score > 0.65:
        print("Good mean-reversion setup")

_score_generic(features, regime, direction)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_generic

**Internal method** - Generic weighted scoring using DEFAULT_WEIGHTS.

**Default Weights:**

.. code-block:: python

    DEFAULT_WEIGHTS = {
        'trend_alignment': 0.20,
        'rsi_momentum': 0.15,
        'macd_momentum': 0.15,
        'trend_strength': 0.15,
        'mean_reversion': 0.10,
        'volume': 0.10,
        'regime_match': 0.15
    }

_score_with_rules(features, regime, direction, strategy_type)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_with_rules

**Internal method** - Strategy-specific rule evaluation.

**Strategy Profiles:**

1. **Trend Following:**

   .. code-block:: python

       weights = {
           'trend_alignment': 0.30,  # High importance
           'trend_strength': 0.25,   # High importance
           'rsi_momentum': 0.15,
           'macd_momentum': 0.15,
           'volume': 0.10,
           'regime_match': 0.05
       }

2. **Mean Reversion:**

   .. code-block:: python

       weights = {
           'mean_reversion': 0.35,   # Highest importance
           'rsi_momentum': 0.20,     # Reversed (oversold/overbought)
           'regime_match': 0.20,     # Range regime preferred
           'volume': 0.15,
           'trend_alignment': 0.05,  # Low importance
           'trend_strength': 0.05    # Low importance
       }

3. **Breakout:**

   .. code-block:: python

       weights = {
           'volume': 0.35,           # Critical for breakouts
           'trend_strength': 0.25,
           'macd_momentum': 0.20,
           'rsi_momentum': 0.10,
           'regime_match': 0.10
       }

Component Scoring Methods
-------------------------

_score_trend_alignment(features, direction)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_trend_alignment

**Returns:** 0-1 score for SMA alignment.

**Logic:**

.. code-block:: python

    if direction == "LONG":
        return 1.0 if features.sma_fast > features.sma_slow else 0.0
    else:  # SHORT
        return 1.0 if features.sma_fast < features.sma_slow else 0.0

_score_rsi_momentum(features, direction)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_rsi_momentum

**Returns:** 0-1 score based on RSI favorability.

**Calculation:**

.. code-block:: python

    if direction == "LONG":
        # RSI 50-70 is ideal for LONG (bullish but not overbought)
        if rsi >= 50 and rsi <= 70:
            return (rsi - 50) / 20  # 0.0 to 1.0
        elif rsi > 70:
            return 1.0 - ((rsi - 70) / 30)  # Penalize overbought
        else:
            return 0.0

_score_macd_momentum(features, direction)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_macd_momentum

**Returns:** 0-1 score for MACD signal strength.

**Calculation:**

.. code-block:: python

    histogram = features.macd_line - features.macd_signal

    if direction == "LONG":
        # Positive histogram = bullish
        return min(1.0, max(0.0, histogram / 50))  # Normalize to 0-1
    else:
        # Negative histogram = bearish
        return min(1.0, max(0.0, -histogram / 50))

_score_trend_strength(features)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_trend_strength

**Returns:** 0-1 score for ADX-based trend strength.

**Calculation:**

.. code-block:: python

    adx = features.adx
    if adx >= 50:
        return 1.0
    elif adx >= 25:
        return (adx - 25) / 25  # Scale 25-50 to 0-1
    else:
        return 0.0  # Weak trend

_score_mean_reversion(features, direction)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_mean_reversion

**Returns:** 0-1 score for Bollinger Band extremes.

**Logic:**

.. code-block:: python

    price = features.close
    bb_upper = features.bb_upper
    bb_lower = features.bb_lower
    bb_middle = features.bb_middle

    if direction == "LONG":
        # Near lower band = good for mean reversion long
        distance_from_lower = (price - bb_lower) / (bb_middle - bb_lower)
        return 1.0 - min(1.0, distance_from_lower)
    else:
        # Near upper band = good for mean reversion short
        distance_from_upper = (bb_upper - price) / (bb_upper - bb_middle)
        return 1.0 - min(1.0, distance_from_upper)

_score_volume(features)
~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_volume

**Returns:** 0-1 score for volume confirmation.

**Calculation:**

.. code-block:: python

    volume_ratio = features.volume / features.volume_sma

    if volume_ratio >= 2.0:
        return 1.0  # Very high volume
    elif volume_ratio >= 1.0:
        return (volume_ratio - 1.0)  # 1.0x to 2.0x → 0 to 1
    else:
        return 0.0  # Below average volume

_score_regime_match(regime, direction, strategy_type)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.entry_scorer.EntryScorer._score_regime_match

**Returns:** 0-1 score for regime compatibility.

**Logic:**

.. code-block:: python

    if strategy_type == "trend_following":
        if regime.regime in [RegimeType.TREND_UP, RegimeType.TREND_DOWN]:
            return 1.0 if regime.regime_confidence > 0.7 else 0.5
        else:
            return 0.0  # Range regime incompatible

    elif strategy_type == "mean_reversion":
        if regime.regime == RegimeType.RANGE:
            return 1.0
        else:
            return 0.2  # Trending regime less compatible

Data Models
-----------

EntryScore (Dataclass)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class EntryScore:
        total_score: float  # 0-1 overall score
        component_scores: dict[str, float]  # Per-component breakdown
        strategy_type: str
        direction: str
        timestamp: datetime

Best Practices
--------------

**1. Use Score Thresholds:**

.. code-block:: python

    EXCELLENT_THRESHOLD = 0.80
    GOOD_THRESHOLD = 0.70
    ACCEPTABLE_THRESHOLD = 0.60

    if score.total_score >= EXCELLENT_THRESHOLD:
        position_size = MAX_POSITION_SIZE
    elif score.total_score >= GOOD_THRESHOLD:
        position_size = NORMAL_POSITION_SIZE
    elif score.total_score >= ACCEPTABLE_THRESHOLD:
        position_size = REDUCED_POSITION_SIZE
    else:
        skip_trade()

**2. Analyze Component Breakdown:**

.. code-block:: python

    # Find weak components
    weak_components = {
        k: v for k, v in score.component_scores.items()
        if v < 0.50
    }

    if 'volume' in weak_components:
        print("Warning: Low volume confirmation")
    if 'regime_match' in weak_components:
        print("Warning: Strategy-regime mismatch")

**3. Strategy-Specific Scoring:**

.. code-block:: python

    # Always specify strategy type for accurate scoring
    trend_score = scorer.calculate_score(features, regime, "LONG", "trend_following")
    mr_score = scorer.calculate_score(features, regime, "LONG", "mean_reversion")

    # Choose best strategy for current conditions
    if trend_score.total_score > mr_score.total_score:
        execute_trend_strategy()
    else:
        execute_mean_reversion_strategy()

See Also
--------

* :doc:`bot_controller` - Uses entry scoring for trade decisions
* :doc:`regime_engine` - Provides regime context for scoring
* :doc:`backtest_engine` - Backtests scoring thresholds
* :doc:`config_executor` - Applies parameter overrides affecting scoring
