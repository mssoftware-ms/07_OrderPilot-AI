config_integration_bridge
==========================

.. module:: src.core.tradingbot.config_integration_bridge
   :synopsis: Integration bridge between JSON config system and existing TradingBot architecture

Overview
--------

The ``config_integration_bridge`` module provides adapter classes that bridge the JSON-based configuration system with the existing TradingBot architecture. This enables gradual migration from hardcoded strategies to JSON-based configuration while maintaining backward compatibility.

**Key Features:**

* **IndicatorValueCalculator**: Maps FeatureVector to indicator_values dict for ConditionEvaluator
* **RegimeDetectorBridge**: Bridges JSON RegimeDetector with existing RegimeState
* **StrategySetAdapter**: Converts MatchedStrategySet to StrategyDefinition for execution
* **ConfigBasedStrategyCatalog**: Alternative to hardcoded StrategyCatalog using JSON config
* **Type-Safe Mapping**: 40+ indicator mappings with validation
* **Thread-Safe Config Reloading**: RLock for concurrent access
* **Auto-Reload Support**: Optional watchdog file monitoring
* **Backward Compatibility**: Works with existing FeatureEngine, RegimeEngine, StrategyExecutor

Usage Example
-------------

**Basic Integration with Existing TradingBot:**

.. code-block:: python

    from src.core.tradingbot.config_integration_bridge import (
        ConfigBasedStrategyCatalog,
        IndicatorValueCalculator,
        RegimeDetectorBridge,
        StrategySetAdapter,
    )
    from src.core.tradingbot.config.loader import ConfigLoader
    from src.core.tradingbot.feature_engine import FeatureVector
    from pathlib import Path

    # Load JSON configuration
    config_path = Path("03_JSON/Trading_Bot/trend_following_conservative.json")
    config = ConfigLoader().load_config(config_path)

    # Create catalog (alternative to hardcoded StrategyCatalog)
    catalog = ConfigBasedStrategyCatalog(
        config=config,
        config_path=config_path,
        auto_reload=True,
        debounce_seconds=1.0
    )

    # Use with existing FeatureEngine
    feature_vector = FeatureVector(
        rsi=65.5,
        adx=28.3,
        macd=0.015,
        macd_signal=0.012,
        sma_fast=50100.0,
        sma_slow=49800.0,
        # ... 40+ more indicators
    )

    # Get active strategy sets (replaces hardcoded strategy selection)
    matched_sets = catalog.get_active_strategy_sets(feature_vector)

    for matched_set in matched_sets:
        print(f"Strategy Set: {matched_set.strategy_set.name}")
        print(f"Matched Regimes: {matched_set.matched_regimes}")

        # Convert to StrategyDefinition for execution
        strategy_def = StrategySetAdapter.adapt(matched_set, feature_vector)
        print(f"Entry Conditions: {strategy_def.entry_conditions}")
        print(f"Exit Conditions: {strategy_def.exit_conditions}")

**Indicator Value Calculation:**

.. code-block:: python

    from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

    # Initialize calculator
    calculator = IndicatorValueCalculator()

    # Convert FeatureVector to indicator_values dict
    indicator_values = calculator.calculate(feature_vector)

    # Use with ConditionEvaluator
    from src.core.tradingbot.config.evaluator import ConditionEvaluator

    evaluator = ConditionEvaluator()
    condition = {
        "field": "rsi14",
        "operator": "gt",
        "value": 60.0
    }

    result = evaluator.evaluate_condition(condition, indicator_values)
    print(f"RSI > 60: {result}")  # True if rsi14 (mapped from feature_vector.rsi) > 60

**Regime Detection Bridge:**

.. code-block:: python

    from src.core.tradingbot.config_integration_bridge import RegimeDetectorBridge
    from src.core.tradingbot.config.detector import RegimeDetector

    # Initialize bridge with JSON regimes
    regime_detector = RegimeDetector(config.regimes)
    bridge = RegimeDetectorBridge(regime_detector)

    # Detect regime from FeatureVector (returns RegimeState)
    regime_state = bridge.detect_regime_from_features(feature_vector)

    print(f"Regime: {regime_state.regime}")  # TREND_UP, TREND_DOWN, RANGE
    print(f"Volatility: {regime_state.volatility}")  # LOW, NORMAL, HIGH, EXTREME
    print(f"ADX: {regime_state.adx}")
    print(f"Confidence: {regime_state.regime_confidence}")

**Live Config Reloading:**

.. code-block:: python

    # Enable auto-reload (watches config file for changes)
    catalog.enable_auto_reload(
        config_path=config_path,
        debounce_seconds=1.0  # Ignore rapid consecutive changes
    )

    # Manually reload config
    catalog.reload_config(new_config=None)  # Reloads from disk

    # Reload with new config object
    new_config = ConfigLoader().load_config("new_config.json")
    catalog.reload_config(new_config=new_config)

    # Disable auto-reload
    catalog.disable_auto_reload()

Classes
-------

.. autoclass:: src.core.tradingbot.config_integration_bridge.IndicatorValueCalculator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.tradingbot.config_integration_bridge.RegimeDetectorBridge
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.tradingbot.config_integration_bridge.StrategySetAdapter
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.tradingbot.config_integration_bridge.ConfigBasedStrategyCatalog
   :members:
   :undoc-members:
   :show-inheritance:

Key Methods
-----------

**IndicatorValueCalculator.calculate**

Converts FeatureVector to indicator_values dict for ConditionEvaluator.

Algorithm:

1. **Initialize Result Dict**:

   .. code-block:: python

       indicator_values = {}

2. **Map Each Indicator** using INDICATOR_MAPPING:

   .. code-block:: python

       for indicator_id, feature_attr in self.INDICATOR_MAPPING.items():
           value = getattr(feature_vector, feature_attr, None)
           if value is not None:
               indicator_values[indicator_id] = value

3. **Calculate Derived Indicators**:

   .. code-block:: python

       # RSI divergence from neutral (50)
       if "rsi" in indicator_values:
           indicator_values["rsi_divergence"] = abs(indicator_values["rsi"] - 50.0)

       # MACD histogram (MACD - Signal)
       if "macd" in indicator_values and "macd_signal" in indicator_values:
           indicator_values["macd_histogram"] = (
               indicator_values["macd"] - indicator_values["macd_signal"]
           )

       # Price-to-SMA ratios
       if "close" in indicator_values and "sma20" in indicator_values:
           indicator_values["price_to_sma_ratio"] = (
               indicator_values["close"] / indicator_values["sma20"]
           )

4. **Return Result**:

   .. code-block:: python

       return indicator_values

**Parameters:**

* ``feature_vector`` (FeatureVector): Feature vector from FeatureEngine

**Returns:**

* ``dict[str, float]``: Indicator values keyed by indicator ID

**RegimeDetectorBridge.detect_regime_from_features**

Detects regime from FeatureVector and converts to RegimeState.

Algorithm:

1. **Calculate Indicator Values**:

   .. code-block:: python

       indicator_values = self.indicator_calculator.calculate(feature_vector)

2. **Detect Active Regimes** using JSON config:

   .. code-block:: python

       active_regimes = self.regime_detector.detect_active_regimes(
           indicator_values, scope="entry"
       )

3. **Determine Primary Regime** (highest priority):

   .. code-block:: python

       if not active_regimes:
           primary_regime = "RANGE"  # Default fallback
       else:
           # Get regime with highest priority
           primary_regime = max(
               active_regimes,
               key=lambda r: r.get("priority", 0)
           )["id"]

4. **Map to RegimeType**:

   .. code-block:: python

       regime_mapping = {
           "trend_up": RegimeType.TREND_UP,
           "trend_down": RegimeType.TREND_DOWN,
           "range": RegimeType.RANGE,
       }
       regime_type = regime_mapping.get(primary_regime.lower(), RegimeType.RANGE)

5. **Determine Volatility** from ADX/ATR:

   .. code-block:: python

       atr_pct = feature_vector.atr_pct
       if atr_pct > 3.0:
           volatility = VolatilityLevel.EXTREME
       elif atr_pct > 2.0:
           volatility = VolatilityLevel.HIGH
       elif atr_pct > 1.0:
           volatility = VolatilityLevel.NORMAL
       else:
           volatility = VolatilityLevel.LOW

6. **Calculate Confidence**:

   .. code-block:: python

       # ADX-based confidence: ADX > 25 = strong trend
       adx = feature_vector.adx
       if adx > 40:
           confidence = 0.95
       elif adx > 30:
           confidence = 0.80
       elif adx > 25:
           confidence = 0.65
       else:
           confidence = 0.50

7. **Create RegimeState**:

   .. code-block:: python

       return RegimeState(
           regime=regime_type,
           volatility=volatility,
           adx=feature_vector.adx,
           atr_pct=feature_vector.atr_pct,
           regime_confidence=confidence
       )

**Parameters:**

* ``feature_vector`` (FeatureVector): Feature vector from FeatureEngine

**Returns:**

* ``RegimeState``: Regime state compatible with existing architecture

**StrategySetAdapter.adapt**

Converts MatchedStrategySet to StrategyDefinition for execution.

Algorithm:

1. **Extract Strategy Set**:

   .. code-block:: python

       strategy_set = matched_set.strategy_set

2. **Get First Strategy** (strategy sets can have multiple):

   .. code-block:: python

       if not strategy_set.strategies:
           raise ValueError("Strategy set has no strategies")

       strategy_id = strategy_set.strategies[0]
       # Lookup full strategy definition from config

3. **Apply Parameter Overrides**:

   .. code-block:: python

       # Apply indicator overrides
       for override in strategy_set.indicator_overrides:
           indicator_id = override["indicator_id"]
           new_params = override["params"]
           # Update indicator parameters

       # Apply strategy overrides
       for override in strategy_set.strategy_overrides:
           # Update entry/exit conditions

4. **Convert Entry Conditions**:

   .. code-block:: python

       entry_conditions = []
       for condition_group in strategy.entry_conditions:
           # Convert JSON condition to StrategyDefinition format
           entry_conditions.append({
               "type": "indicator",
               "field": condition_group["field"],
               "operator": condition_group["operator"],
               "value": condition_group["value"]
           })

5. **Convert Exit Conditions**:

   .. code-block:: python

       exit_conditions = []
       for condition_group in strategy.exit_conditions:
           exit_conditions.append({
               "type": "indicator",
               "field": condition_group["field"],
               "operator": condition_group["operator"],
               "value": condition_group["value"]
           })

6. **Create StrategyDefinition**:

   .. code-block:: python

       return StrategyDefinition(
           name=strategy.name,
           entry_conditions=entry_conditions,
           exit_conditions=exit_conditions,
           risk_params={
               "position_size_pct": strategy.risk.position_size_pct,
               "max_leverage": strategy.risk.max_leverage,
               "stop_loss_pct": strategy.risk.stop_loss_pct,
               "take_profit_pct": strategy.risk.take_profit_pct,
           }
       )

**Parameters:**

* ``matched_set`` (MatchedStrategySet): Matched strategy set from router
* ``feature_vector`` (FeatureVector): Current feature vector for context

**Returns:**

* ``StrategyDefinition``: Strategy definition for execution

**ConfigBasedStrategyCatalog.get_active_strategy_sets**

Gets active strategy sets based on current market conditions.

Algorithm:

1. **Calculate Indicator Values**:

   .. code-block:: python

       indicator_values = self.indicator_calculator.calculate(feature_vector)

2. **Detect Active Regimes**:

   .. code-block:: python

       active_regimes = self.regime_detector.detect_active_regimes(
           indicator_values, scope="entry"
       )

3. **Route to Strategy Sets**:

   .. code-block:: python

       matched_sets = self.strategy_router.route(active_regimes)

4. **Apply Parameter Overrides**:

   .. code-block:: python

       for matched_set in matched_sets:
           self.strategy_executor.prepare_execution(matched_set)

5. **Return Matched Sets**:

   .. code-block:: python

       return matched_sets

**Parameters:**

* ``feature_vector`` (FeatureVector): Current feature vector

**Returns:**

* ``list[MatchedStrategySet]``: Active strategy sets with overrides applied

**ConfigBasedStrategyCatalog.reload_config**

Reloads configuration from disk or new config object.

Algorithm:

1. **Acquire Lock** (thread-safe):

   .. code-block:: python

       with self._config_lock:

2. **Load New Config**:

   .. code-block:: python

       if new_config is None:
           new_config = ConfigLoader().load_config(self.config_path)

3. **Update Components**:

   .. code-block:: python

       self.config = new_config
       self.regime_detector = RegimeDetector(new_config.regimes)
       self.strategy_router = StrategyRouter(
           new_config.routing, new_config.strategy_sets
       )
       self.strategy_executor = StrategySetExecutor(
           new_config.indicators, new_config.strategies
       )

4. **Restore Original State** (if overrides were active):

   .. code-block:: python

       self.strategy_executor.restore_state()

5. **Log Reload**:

   .. code-block:: python

       logger.info(f"Reloaded config from {self.config_path}")

**Parameters:**

* ``new_config`` (TradingBotConfig | None): New config or None to reload from disk

**Returns:**

* None

Common Patterns
---------------

**Pattern 1: Replace Hardcoded StrategyCatalog**

Migrate from hardcoded strategy selection to JSON-based configuration:

.. code-block:: python

    # OLD: Hardcoded StrategyCatalog
    from src.core.tradingbot.strategy_catalog import StrategyCatalog

    catalog = StrategyCatalog()
    strategies = catalog.get_strategies_for_regime(regime_state)

    # NEW: JSON-based ConfigBasedStrategyCatalog
    from src.core.tradingbot.config_integration_bridge import ConfigBasedStrategyCatalog
    from src.core.tradingbot.config.loader import ConfigLoader

    config = ConfigLoader().load_config("config.json")
    catalog = ConfigBasedStrategyCatalog(config, auto_reload=True)
    matched_sets = catalog.get_active_strategy_sets(feature_vector)

**Pattern 2: Gradual Migration with Fallback**

Support both hardcoded and JSON strategies during migration:

.. code-block:: python

    # Try JSON config first, fallback to hardcoded
    try:
        if config_path.exists():
            catalog = ConfigBasedStrategyCatalog(
                ConfigLoader().load_config(config_path)
            )
            matched_sets = catalog.get_active_strategy_sets(feature_vector)
        else:
            # Fallback to hardcoded
            catalog = StrategyCatalog()
            strategies = catalog.get_strategies_for_regime(regime_state)
    except Exception as e:
        logger.warning(f"JSON config failed, using hardcoded: {e}")
        catalog = StrategyCatalog()
        strategies = catalog.get_strategies_for_regime(regime_state)

**Pattern 3: Live Config Updates with Auto-Reload**

Enable live strategy updates without restarting bot:

.. code-block:: python

    # Initialize with auto-reload
    catalog = ConfigBasedStrategyCatalog(
        config=config,
        config_path=config_path,
        auto_reload=True,
        debounce_seconds=1.0
    )

    # Bot runs continuously
    while bot_running:
        feature_vector = feature_engine.process_bar(bar_data)

        # Automatically uses latest config (reloaded on file change)
        matched_sets = catalog.get_active_strategy_sets(feature_vector)

        for matched_set in matched_sets:
            # Execute strategies with latest parameters
            execute_strategy(matched_set)

    # Cleanup
    catalog.disable_auto_reload()

**Pattern 4: Custom Indicator Mapping**

Add custom indicators not in default INDICATOR_MAPPING:

.. code-block:: python

    from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

    # Extend with custom mappings
    calculator = IndicatorValueCalculator()
    calculator.INDICATOR_MAPPING.update({
        "custom_momentum": "custom_momentum_indicator",
        "custom_volume": "custom_volume_indicator",
    })

    # Use extended calculator
    indicator_values = calculator.calculate(feature_vector)

    # Now custom indicators are available in conditions
    condition = {
        "field": "custom_momentum",
        "operator": "gt",
        "value": 0.5
    }

**Pattern 5: Regime Detection with Custom Confidence**

Override default confidence calculation:

.. code-block:: python

    from src.core.tradingbot.config_integration_bridge import RegimeDetectorBridge

    class CustomRegimeDetectorBridge(RegimeDetectorBridge):
        def detect_regime_from_features(self, feature_vector):
            # Use parent detection
            regime_state = super().detect_regime_from_features(feature_vector)

            # Custom confidence logic
            if regime_state.regime == RegimeType.TREND_UP:
                # Strong bullish confirmation
                if feature_vector.macd > 0 and feature_vector.rsi > 60:
                    regime_state.regime_confidence = 0.95

            return regime_state

    # Use custom bridge
    bridge = CustomRegimeDetectorBridge(regime_detector)

Data Models
-----------

**INDICATOR_MAPPING (40+ Mappings)**

Maps indicator IDs (used in JSON config) to FeatureVector attributes:

.. code-block:: python

    INDICATOR_MAPPING = {
        # Technical Indicators
        "rsi14": "rsi",
        "rsi7": "rsi_fast",
        "rsi28": "rsi_slow",
        "adx14": "adx",
        "adx28": "adx_slow",
        "macd": "macd",
        "macd_signal": "macd_signal",
        "macd_histogram": "macd_histogram",

        # Moving Averages
        "sma20": "sma_fast",
        "sma50": "sma_slow",
        "ema12": "ema_fast",
        "ema26": "ema_slow",
        "ema50": "ema_medium",
        "ema200": "ema_long",

        # Bollinger Bands
        "bb_upper": "bb_upper",
        "bb_middle": "bb_middle",
        "bb_lower": "bb_lower",
        "bb_width": "bb_width",
        "bb_position": "bb_position",

        # ATR
        "atr14": "atr",
        "atr_pct": "atr_pct",
        "atr28": "atr_slow",

        # Volume
        "volume": "volume",
        "volume_sma20": "volume_sma",
        "volume_ratio": "volume_ratio",

        # Price
        "close": "close",
        "high": "high",
        "low": "low",
        "open": "open",

        # Stochastic
        "stoch_k": "stoch_k",
        "stoch_d": "stoch_d",

        # Ichimoku
        "ichimoku_conversion": "ichimoku_conversion",
        "ichimoku_base": "ichimoku_base",
        "ichimoku_span_a": "ichimoku_span_a",
        "ichimoku_span_b": "ichimoku_span_b",

        # Higher Timeframe Indicators
        "htf_rsi": "htf_rsi",
        "htf_adx": "htf_adx",
        "htf_macd": "htf_macd",
        "htf_sma": "htf_sma",
    }

**RegimeState (Existing Model)**

Output from RegimeDetectorBridge:

.. code-block:: python

    @dataclass
    class RegimeState:
        regime: RegimeType  # TREND_UP, TREND_DOWN, RANGE
        volatility: VolatilityLevel  # LOW, NORMAL, HIGH, EXTREME
        adx: float  # ADX value (0-100)
        atr_pct: float  # ATR as percentage of price
        regime_confidence: float  # Confidence score (0.0-1.0)

**StrategyDefinition (Existing Model)**

Output from StrategySetAdapter:

.. code-block:: python

    @dataclass
    class StrategyDefinition:
        name: str  # Strategy name
        entry_conditions: list[dict]  # Entry condition groups
        exit_conditions: list[dict]  # Exit condition groups
        risk_params: dict  # Risk management parameters

Best Practices
--------------

**✅ DO:**

* **Use ConfigBasedStrategyCatalog for new bots**: Replace hardcoded StrategyCatalog with JSON-based catalog
* **Enable auto-reload in development**: Set ``auto_reload=True`` for live config updates during testing
* **Thread-safe access**: Use catalog's built-in RLock for concurrent access
* **Validate configs before deployment**: Use ConfigLoader with schema validation
* **Extend INDICATOR_MAPPING for custom indicators**: Add custom mappings for project-specific indicators
* **Test regime detection accuracy**: Compare RegimeDetectorBridge output with RegimeEngine output

.. code-block:: python

    # ✅ GOOD: Thread-safe with auto-reload
    catalog = ConfigBasedStrategyCatalog(
        config=config,
        config_path=config_path,
        auto_reload=True,
        debounce_seconds=1.0
    )

    # Concurrent access is safe
    matched_sets = catalog.get_active_strategy_sets(feature_vector)

**❌ DON'T:**

* **Don't bypass ConfigLoader validation**: Always use ConfigLoader to load configs, not raw JSON
* **Don't modify INDICATOR_MAPPING at runtime**: Extend before initialization, not during execution
* **Don't disable auto-reload in production without monitoring**: Use health checks to detect config issues
* **Don't mix hardcoded and JSON strategies without fallback**: Always have a fallback strategy
* **Don't ignore reload errors**: Log and alert on config reload failures
* **Don't use auto-reload with very low debounce**: Set debounce_seconds >= 1.0 to avoid rapid reloads

.. code-block:: python

    # ❌ BAD: Bypassing validation
    import json
    with open("config.json") as f:
        config = json.load(f)  # NO! Missing validation

    # ✅ GOOD: Validated loading
    config = ConfigLoader().load_config("config.json")

    # ❌ BAD: Very low debounce causes rapid reloads
    catalog.enable_auto_reload(debounce_seconds=0.1)

    # ✅ GOOD: Reasonable debounce prevents reload storms
    catalog.enable_auto_reload(debounce_seconds=1.0)

**Performance Considerations:**

* **Reload overhead**: Config reloading takes ~50-100ms (JSON parse + validation + object creation)
* **Thread contention**: RLock acquisition is fast (<1ms) but can cause brief delays under high concurrency
* **Indicator calculation**: ~5-10ms for 40+ indicators (cached in FeatureVector)
* **Regime detection**: ~2-5ms for complex condition evaluation
* **Memory**: Each config instance uses ~1-2 MB (Pydantic models + routing tables)

**Migration Strategy:**

1. **Phase 1**: Add ConfigBasedStrategyCatalog alongside StrategyCatalog (both active)
2. **Phase 2**: A/B test JSON strategies vs hardcoded (compare performance)
3. **Phase 3**: Migrate high-performing strategies to JSON
4. **Phase 4**: Remove StrategyCatalog, use only JSON configs
5. **Phase 5**: Enable auto-reload in production with monitoring

See Also
--------

* :doc:`config_loader` - Loads and validates JSON configs
* :doc:`config_detector` - Detects active regimes from indicator values
* :doc:`config_router` - Routes regimes to strategy sets
* :doc:`config_executor` - Applies parameter overrides for execution
* :doc:`config_reloader` - Thread-safe config reloading with file watching
* :doc:`regime_engine` - Classic regime detection (non-JSON)
* :doc:`entry_scorer` - Scores entry quality using indicators
