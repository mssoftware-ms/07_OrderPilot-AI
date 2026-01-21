Pattern Recognizer
==================

.. automodule:: src.ai.pattern_recognizer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``PatternRecognizer`` detects chart patterns and market structure for AI-powered strategy generation:

* **Chart Patterns**: Double tops/bottoms, triangles, candlestick patterns, flags, wedges
* **Market Structure**: Support/resistance levels, market phase classification
* **Volatility Regime**: ATR-based volatility classification (LOW/NORMAL/HIGH/EXTREME)
* **Integration**: Provides context for ``StrategyGenerator`` to create regime-aware strategies

Key Features
------------

**Comprehensive Pattern Detection:**
   Detects 10+ pattern types including reversal, continuation, and candlestick patterns.

**Market Structure Analysis:**
   Identifies support/resistance levels and classifies market phase (TRENDING/RANGING/CHOPPY).

**Volatility Classification:**
   Categorizes volatility into 4 regimes using ATR percentile analysis.

**Price Action Context:**
   Combines patterns, structure, and volatility for complete market characterization.

Usage Example
-------------

.. code-block:: python

    from src.ai.pattern_recognizer import PatternRecognizer
    import pandas as pd

    # Load historical data
    df = pd.DataFrame({
        'timestamp': [...],
        'open': [...],
        'high': [...],
        'low': [...],
        'close': [...],
        'volume': [...]
    })

    # Initialize pattern recognizer
    recognizer = PatternRecognizer()

    # Detect all patterns
    patterns = recognizer.detect_chart_patterns(df)

    # Example patterns found
    for pattern in patterns:
        print(f"Pattern: {pattern.pattern_type}")
        print(f"Timeframe: {pattern.start_time} → {pattern.end_time}")
        print(f"Confidence: {pattern.confidence:.2%}")
        print(f"Direction: {pattern.direction}")
        print(f"Key levels: {pattern.key_levels}")
        print(f"Description: {pattern.description}")

    # Analyze market structure
    structure = recognizer.detect_market_structure(df)
    print(f"Market Phase: {structure.phase}")
    print(f"Support Levels: {structure.support_levels}")
    print(f"Resistance Levels: {structure.resistance_levels}")
    print(f"Trend Direction: {structure.trend_direction}")
    print(f"Trend Strength: {structure.trend_strength:.2%}")

    # Classify volatility
    volatility = recognizer.classify_volatility_regime(df)
    print(f"Volatility Regime: {volatility.regime}")
    print(f"ATR: {volatility.atr:.2f}")
    print(f"ATR%: {volatility.atr_pct:.2%}")
    print(f"Historical Percentile: {volatility.percentile:.2%}")

Classes
-------

.. autoclass:: src.ai.pattern_recognizer.PatternRecognizer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

detect_chart_patterns(df)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.pattern_recognizer.PatternRecognizer.detect_chart_patterns

Detect all chart patterns in historical data.

**Parameters:**

* ``df`` (pd.DataFrame): OHLCV data with columns: open, high, low, close, volume, timestamp

**Returns:**

* ``list[Pattern]``: List of detected patterns with metadata

**Algorithm:**

1. **Double Tops/Bottoms:**

   .. code-block:: python

       # Find local maxima (peaks) and minima (troughs)
       peaks = find_local_maxima(df['high'], distance=20)
       troughs = find_local_minima(df['low'], distance=20)

       # Check for double top pattern
       for i in range(len(peaks) - 1):
           peak1, peak2 = peaks[i], peaks[i+1]
           price_diff = abs(df.loc[peak1, 'high'] - df.loc[peak2, 'high'])

           if price_diff / df.loc[peak1, 'high'] < 0.02:  # Within 2%
               # Found double top
               neckline = df.loc[peak1:peak2, 'low'].min()
               patterns.append(Pattern(
                   pattern_type='double_top',
                   confidence=0.7 + (0.3 if price_diff < 0.01 else 0.0),
                   direction='bearish',
                   key_levels={'peak1': peak1_price, 'peak2': peak2_price, 'neckline': neckline}
               ))

2. **Triangles (Ascending, Descending, Symmetrical):**

   .. code-block:: python

       # Find convergence of highs and lows
       highs = df['high'].rolling(20).max()
       lows = df['low'].rolling(20).min()

       # Calculate slopes
       high_slope = calculate_linear_slope(highs[-50:])
       low_slope = calculate_linear_slope(lows[-50:])

       # Classify triangle type
       if abs(high_slope) < 0.001 and low_slope > 0.01:
           # Ascending triangle: flat resistance, rising support
           pattern_type = 'ascending_triangle'
           direction = 'bullish'
       elif high_slope < -0.01 and abs(low_slope) < 0.001:
           # Descending triangle: declining resistance, flat support
           pattern_type = 'descending_triangle'
           direction = 'bearish'
       elif abs(high_slope + low_slope) < 0.005:
           # Symmetrical triangle: converging lines
           pattern_type = 'symmetrical_triangle'
           direction = 'neutral'

3. **Candlestick Patterns:**

   .. code-block:: python

       for i in range(1, len(df)):
           current = df.iloc[i]
           previous = df.iloc[i-1]

           # Hammer: long lower shadow, small body at top
           body = abs(current['close'] - current['open'])
           lower_shadow = min(current['open'], current['close']) - current['low']
           upper_shadow = current['high'] - max(current['open'], current['close'])

           if lower_shadow > 2 * body and upper_shadow < 0.1 * body:
               patterns.append(Pattern(
                   pattern_type='hammer',
                   confidence=0.6,
                   direction='bullish'
               ))

           # Doji: open ≈ close (indecision)
           if body < 0.001 * current['close']:
               patterns.append(Pattern(
                   pattern_type='doji',
                   confidence=0.5,
                   direction='neutral'
               ))

           # Bullish engulfing
           if (previous['close'] < previous['open'] and  # Previous bearish
               current['close'] > current['open'] and    # Current bullish
               current['open'] < previous['close'] and   # Opens below previous close
               current['close'] > previous['open']):     # Closes above previous open
               patterns.append(Pattern(
                   pattern_type='bullish_engulfing',
                   confidence=0.7,
                   direction='bullish'
               ))

4. **Flags and Wedges:**

   .. code-block:: python

       # Detect flag pattern (consolidation after strong move)
       recent_trend = df['close'].pct_change(20).iloc[-1]

       if abs(recent_trend) > 0.10:  # Strong move (>10%)
           # Check for consolidation
           consolidation_range = df['high'][-10:].max() - df['low'][-10:].min()
           avg_price = df['close'][-10:].mean()

           if consolidation_range / avg_price < 0.05:  # Tight range (<5%)
               patterns.append(Pattern(
                   pattern_type='bull_flag' if recent_trend > 0 else 'bear_flag',
                   confidence=0.65,
                   direction='bullish' if recent_trend > 0 else 'bearish'
               ))

**Example:**

.. code-block:: python

    # Detect patterns
    patterns = recognizer.detect_chart_patterns(df)

    # Filter by confidence
    high_confidence = [p for p in patterns if p.confidence > 0.7]

    # Filter by type
    reversal_patterns = [p for p in patterns
                         if p.pattern_type in ['double_top', 'double_bottom',
                                                 'head_and_shoulders']]

    # Filter by direction
    bullish_patterns = [p for p in patterns if p.direction == 'bullish']

detect_market_structure(df)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.pattern_recognizer.PatternRecognizer.detect_market_structure

Analyze market structure and identify support/resistance levels.

**Parameters:**

* ``df`` (pd.DataFrame): OHLCV data

**Returns:**

* ``MarketStructure``: Structural analysis with phase, levels, trend

**Algorithm:**

1. **Identify Support/Resistance Levels:**

   .. code-block:: python

       # Find swing highs and lows
       swing_highs = find_local_maxima(df['high'], distance=10)
       swing_lows = find_local_minima(df['low'], distance=10)

       # Cluster nearby levels
       resistance_clusters = cluster_levels(
           [df.loc[idx, 'high'] for idx in swing_highs],
           tolerance=0.02  # 2% price tolerance
       )

       support_clusters = cluster_levels(
           [df.loc[idx, 'low'] for idx in swing_lows],
           tolerance=0.02
       )

       # Take strongest levels (most touches)
       resistance_levels = sorted(resistance_clusters,
                                   key=lambda x: x['touch_count'],
                                   reverse=True)[:5]

       support_levels = sorted(support_clusters,
                               key=lambda x: x['touch_count'],
                               reverse=True)[:5]

2. **Classify Market Phase:**

   .. code-block:: python

       # Calculate trend indicators
       sma_20 = df['close'].rolling(20).mean()
       sma_50 = df['close'].rolling(50).mean()
       current_price = df['close'].iloc[-1]

       # Calculate ADX for trend strength
       adx = calculate_adx(df, period=14)

       # Classify phase
       if adx > 25:  # Strong trend
           if sma_20.iloc[-1] > sma_50.iloc[-1]:
               phase = MarketPhase.TRENDING_UP
               trend_direction = 'bullish'
           else:
               phase = MarketPhase.TRENDING_DOWN
               trend_direction = 'bearish'
       elif adx < 20:  # Weak trend
           if df['high'][-20:].max() - df['low'][-20:].min() < 0.05 * current_price:
               phase = MarketPhase.RANGING
               trend_direction = 'sideways'
           else:
               phase = MarketPhase.CHOPPY
               trend_direction = 'mixed'
       else:
           phase = MarketPhase.TRANSITION
           trend_direction = 'uncertain'

       # Calculate trend strength
       trend_strength = min(adx / 50.0, 1.0)  # Normalize to 0-1

3. **Return Market Structure:**

   .. code-block:: python

       return MarketStructure(
           phase=phase,
           support_levels=[level['price'] for level in support_levels],
           resistance_levels=[level['price'] for level in resistance_levels],
           trend_direction=trend_direction,
           trend_strength=trend_strength,
           range_high=df['high'][-50:].max(),
           range_low=df['low'][-50:].min()
       )

**Example:**

.. code-block:: python

    structure = recognizer.detect_market_structure(df)

    # Use structure for trading decisions
    if structure.phase == MarketPhase.TRENDING_UP:
        print("Use trend-following strategies")
        print(f"Trend strength: {structure.trend_strength:.2%}")

        # Identify pullback entry zones
        for support in structure.support_levels[:3]:
            print(f"Potential entry near support: {support:.2f}")

    elif structure.phase == MarketPhase.RANGING:
        print("Use mean-reversion strategies")

        # Trade between levels
        print(f"Sell near resistance: {structure.resistance_levels[0]:.2f}")
        print(f"Buy near support: {structure.support_levels[0]:.2f}")

classify_volatility_regime(df)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.pattern_recognizer.PatternRecognizer.classify_volatility_regime

Classify volatility regime using ATR percentile analysis.

**Parameters:**

* ``df`` (pd.DataFrame): OHLCV data

**Returns:**

* ``VolatilityAnalysis``: Volatility regime with ATR metrics

**Algorithm:**

1. **Calculate ATR:**

   .. code-block:: python

       # True Range = max(high-low, |high-prev_close|, |low-prev_close|)
       df['tr'] = df.apply(lambda row: max(
           row['high'] - row['low'],
           abs(row['high'] - row['prev_close']),
           abs(row['low'] - row['prev_close'])
       ), axis=1)

       # ATR = 14-period EMA of True Range
       atr = df['tr'].ewm(span=14, adjust=False).mean().iloc[-1]

       # ATR% = ATR / Close Price
       atr_pct = (atr / df['close'].iloc[-1]) * 100

2. **Calculate Historical Percentile:**

   .. code-block:: python

       # Use last 100 periods for percentile calculation
       historical_atr_pct = (df['tr'].rolling(14).mean() / df['close']) * 100
       recent_history = historical_atr_pct[-100:]

       # Calculate percentile rank
       percentile = (recent_history < atr_pct).sum() / len(recent_history)

3. **Classify Regime:**

   .. code-block:: python

       # Classification thresholds
       if percentile < 0.25:
           regime = VolatilityRegime.LOW
           description = "Low volatility - tight ranges, mean reversion favorable"
       elif percentile < 0.60:
           regime = VolatilityRegime.NORMAL
           description = "Normal volatility - balanced conditions"
       elif percentile < 0.85:
           regime = VolatilityRegime.HIGH
           description = "High volatility - wider stops, trend following favorable"
       else:
           regime = VolatilityRegime.EXTREME
           description = "Extreme volatility - exercise caution, reduce position sizes"

       return VolatilityAnalysis(
           regime=regime,
           atr=atr,
           atr_pct=atr_pct,
           percentile=percentile,
           description=description
       )

**Example:**

.. code-block:: python

    volatility = recognizer.classify_volatility_regime(df)

    # Adjust strategy parameters based on volatility
    if volatility.regime == VolatilityRegime.LOW:
        # Tighter stops, smaller targets
        stop_loss_pct = 1.5
        take_profit_pct = 3.0
        position_size_pct = 10.0

    elif volatility.regime == VolatilityRegime.HIGH:
        # Wider stops, larger targets
        stop_loss_pct = 3.5
        take_profit_pct = 7.0
        position_size_pct = 5.0

    elif volatility.regime == VolatilityRegime.EXTREME:
        # Defensive parameters
        stop_loss_pct = 5.0
        take_profit_pct = 10.0
        position_size_pct = 2.0

        print("⚠ EXTREME VOLATILITY - Consider reducing exposure")

Common Patterns
---------------

**Pattern 1: Complete Market Analysis**

.. code-block:: python

    from src.ai.pattern_recognizer import PatternRecognizer

    recognizer = PatternRecognizer()

    # 1. Detect patterns
    patterns = recognizer.detect_chart_patterns(df)
    bullish_patterns = [p for p in patterns if p.direction == 'bullish']
    bearish_patterns = [p for p in patterns if p.direction == 'bearish']

    # 2. Analyze structure
    structure = recognizer.detect_market_structure(df)

    # 3. Classify volatility
    volatility = recognizer.classify_volatility_regime(df)

    # 4. Synthesize analysis
    print(f"Market Phase: {structure.phase}")
    print(f"Trend: {structure.trend_direction} (strength: {structure.trend_strength:.2%})")
    print(f"Volatility: {volatility.regime} (ATR%: {volatility.atr_pct:.2%})")
    print(f"Bullish Patterns: {len(bullish_patterns)}")
    print(f"Bearish Patterns: {len(bearish_patterns)}")

    # 5. Make trading decision
    if structure.phase == MarketPhase.TRENDING_UP and len(bullish_patterns) > 0:
        print("✓ LONG BIAS - Trend + Bullish Patterns")
    elif structure.phase == MarketPhase.TRENDING_DOWN and len(bearish_patterns) > 0:
        print("✓ SHORT BIAS - Downtrend + Bearish Patterns")
    else:
        print("⚠ MIXED SIGNALS - Stay neutral")

**Pattern 2: Feed to Strategy Generator**

.. code-block:: python

    from src.ai.pattern_recognizer import PatternRecognizer
    from src.ai.strategy_generator import StrategyGenerator

    # 1. Analyze market
    recognizer = PatternRecognizer()
    patterns = recognizer.detect_chart_patterns(df)
    structure = recognizer.detect_market_structure(df)
    volatility = recognizer.classify_volatility_regime(df)

    # 2. Generate strategy from analysis
    generator = StrategyGenerator()
    result = await generator.generate_from_patterns(
        patterns=patterns,
        market_structure=structure,
        volatility_analysis=volatility,
        constraints=GenerationConstraints(
            risk_tolerance='medium',
            style='balanced'
        )
    )

    # 3. Use generated config
    if result.success:
        config = result.config
        print(f"Generated strategy: {config.metadata.get('strategy_name')}")
        print(f"Indicators: {len(config.indicators)}")
        print(f"Regimes: {len(config.regimes)}")
        print(f"Strategies: {len(config.strategies)}")

**Pattern 3: Historical Pattern Statistics**

.. code-block:: python

    # Analyze pattern performance over time
    all_patterns = []

    # Rolling window analysis
    for i in range(100, len(df), 20):
        window_df = df.iloc[i-100:i]
        patterns = recognizer.detect_chart_patterns(window_df)
        all_patterns.extend(patterns)

    # Statistics by pattern type
    from collections import Counter
    pattern_counts = Counter(p.pattern_type for p in all_patterns)

    print("Pattern Frequency:")
    for pattern_type, count in pattern_counts.most_common():
        avg_confidence = sum(p.confidence for p in all_patterns
                            if p.pattern_type == pattern_type) / count
        print(f"{pattern_type}: {count} occurrences (avg confidence: {avg_confidence:.2%})")

**Pattern 4: Support/Resistance Trading Zones**

.. code-block:: python

    structure = recognizer.detect_market_structure(df)
    current_price = df['close'].iloc[-1]

    # Find nearest support and resistance
    supports_below = [s for s in structure.support_levels if s < current_price]
    resistances_above = [r for r in structure.resistance_levels if r > current_price]

    nearest_support = max(supports_below) if supports_below else None
    nearest_resistance = min(resistances_above) if resistances_above else None

    # Calculate risk/reward
    if nearest_support and nearest_resistance:
        risk = current_price - nearest_support
        reward = nearest_resistance - current_price
        risk_reward_ratio = reward / risk

        print(f"Current Price: {current_price:.2f}")
        print(f"Nearest Support: {nearest_support:.2f} (risk: {risk:.2f})")
        print(f"Nearest Resistance: {nearest_resistance:.2f} (reward: {reward:.2f})")
        print(f"Risk/Reward Ratio: {risk_reward_ratio:.2f}")

        if risk_reward_ratio >= 2.0:
            print("✓ FAVORABLE RISK/REWARD - Consider long entry")

Data Models
-----------

Pattern
~~~~~~~

.. code-block:: python

    @dataclass
    class Pattern:
        pattern_type: str  # 'double_top', 'ascending_triangle', 'hammer', etc.
        start_time: pd.Timestamp
        end_time: pd.Timestamp
        confidence: float  # 0.0 to 1.0
        direction: str  # 'bullish', 'bearish', 'neutral'
        key_levels: dict[str, float]  # Pattern-specific price levels
        description: str
        timeframe: str = '1h'
        volume_confirmation: bool = False

**Fields:**

* ``pattern_type``: Type of detected pattern
* ``start_time``: Pattern formation start
* ``end_time``: Pattern formation end (or current time for developing patterns)
* ``confidence``: Detection confidence (0-1, higher = more reliable)
* ``direction``: Expected price direction (bullish/bearish/neutral)
* ``key_levels``: Important price levels (e.g., neckline, peaks, support/resistance)
* ``description``: Human-readable pattern description
* ``timeframe``: Chart timeframe where pattern was detected
* ``volume_confirmation``: Whether pattern has volume confirmation

MarketStructure
~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class MarketStructure:
        phase: MarketPhase  # TRENDING_UP, TRENDING_DOWN, RANGING, CHOPPY, TRANSITION
        support_levels: list[float]  # Key support prices (sorted by strength)
        resistance_levels: list[float]  # Key resistance prices (sorted by strength)
        trend_direction: str  # 'bullish', 'bearish', 'sideways', 'mixed', 'uncertain'
        trend_strength: float  # 0.0 to 1.0
        range_high: float  # Recent range high
        range_low: float  # Recent range low

**Fields:**

* ``phase``: Current market phase classification
* ``support_levels``: Support prices (most significant first)
* ``resistance_levels``: Resistance prices (most significant first)
* ``trend_direction``: Overall trend direction
* ``trend_strength``: Trend strength (0=no trend, 1=very strong trend)
* ``range_high``: Upper boundary of recent price action
* ``range_low``: Lower boundary of recent price action

VolatilityAnalysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class VolatilityAnalysis:
        regime: VolatilityRegime  # LOW, NORMAL, HIGH, EXTREME
        atr: float  # Absolute ATR value
        atr_pct: float  # ATR as percentage of price
        percentile: float  # Historical percentile (0.0 to 1.0)
        description: str  # Human-readable description

**Fields:**

* ``regime``: Volatility regime classification
* ``atr``: Average True Range (absolute value)
* ``atr_pct``: ATR as percentage of current price
* ``percentile``: ATR percentile vs. recent history (0-1)
* ``description``: Interpretation and trading implications

Enumerations
~~~~~~~~~~~~

.. code-block:: python

    class MarketPhase(Enum):
        TRENDING_UP = "trending_up"
        TRENDING_DOWN = "trending_down"
        RANGING = "ranging"
        CHOPPY = "choppy"
        TRANSITION = "transition"

    class VolatilityRegime(Enum):
        LOW = "low"
        NORMAL = "normal"
        HIGH = "high"
        EXTREME = "extreme"

Best Practices
--------------

**1. Combine Multiple Signals:**

.. code-block:: python

    # ✅ Good: Use patterns + structure + volatility
    patterns = recognizer.detect_chart_patterns(df)
    structure = recognizer.detect_market_structure(df)
    volatility = recognizer.classify_volatility_regime(df)

    # Make decision based on all three
    if (structure.phase == MarketPhase.TRENDING_UP and
        any(p.direction == 'bullish' for p in patterns) and
        volatility.regime in [VolatilityRegime.NORMAL, VolatilityRegime.HIGH]):
        execute_long_strategy()

    # ❌ Bad: Rely on single signal
    patterns = recognizer.detect_chart_patterns(df)
    if patterns[0].direction == 'bullish':
        execute_long_strategy()  # Ignores market context!

**2. Filter by Confidence:**

.. code-block:: python

    # ✅ Good: Use high-confidence patterns only
    patterns = recognizer.detect_chart_patterns(df)
    high_confidence = [p for p in patterns if p.confidence >= 0.7]

    # ❌ Bad: Use all patterns regardless of confidence
    patterns = recognizer.detect_chart_patterns(df)
    for pattern in patterns:
        trade_on_pattern(pattern)  # May trade low-quality patterns

**3. Respect Volatility Regime:**

.. code-block:: python

    # ✅ Good: Adjust parameters based on volatility
    volatility = recognizer.classify_volatility_regime(df)

    if volatility.regime == VolatilityRegime.EXTREME:
        # Reduce exposure, widen stops
        position_size = 0.02  # 2% of capital
        stop_loss_pct = 5.0
    elif volatility.regime == VolatilityRegime.LOW:
        # Normal exposure, tighter stops
        position_size = 0.10  # 10% of capital
        stop_loss_pct = 1.5

    # ❌ Bad: Same parameters regardless of volatility
    position_size = 0.10  # Fixed size
    stop_loss_pct = 2.0   # Fixed stop

**4. Use Structure for Entry Zones:**

.. code-block:: python

    # ✅ Good: Enter near support/resistance
    structure = recognizer.detect_market_structure(df)
    current_price = df['close'].iloc[-1]

    # Wait for pullback to support
    nearest_support = max(s for s in structure.support_levels if s < current_price)
    if abs(current_price - nearest_support) / current_price < 0.01:  # Within 1%
        print("✓ Near support - good entry zone")

    # ❌ Bad: Enter anywhere regardless of levels
    if any(p.direction == 'bullish' for p in patterns):
        enter_long_immediately()  # May enter at resistance!

See Also
--------

* :doc:`strategy_generator` - Uses pattern analysis to generate JSON configs
* :doc:`parameter_optimizer` - Optimizes strategy parameters based on detected regimes
* :doc:`regime_engine` - Classifies market regimes (complementary to pattern detection)
* :doc:`config_models` - JSON configuration models for strategies
