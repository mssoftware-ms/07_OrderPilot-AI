# JSON Config Integration Guide

How to integrate the new JSON-based configuration system with the existing TradingBot.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Integration Points](#integration-points)
5. [Migration Strategy](#migration-strategy)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The JSON Config Integration Bridge allows gradual migration from hardcoded strategies to JSON-based configuration.

**Benefits:**
- ✅ No breaking changes to existing bot code
- ✅ Gradual migration (JSON + hardcoded can coexist)
- ✅ Automatic fallback to hardcoded if JSON unavailable
- ✅ Compatible with existing FeatureVector and RegimeState

**Components:**
- `IndicatorValueCalculator` - Maps FeatureVector → indicator values
- `RegimeDetectorBridge` - Converts JSON regimes → RegimeState
- `ConfigBasedStrategyCatalog` - Alternative to hardcoded StrategyCatalog

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      TradingBot                             │
│                         (unchanged)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├──► FeatureEngine
                     │    (calculates indicators)
                     │         │
                     │         ▼
┌────────────────────┴────────────────────────────────────────┐
│            ConfigBasedStrategyCatalog                        │
│                (new JSON-based)                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FeatureVector → IndicatorValueCalculator                   │
│       │                    │                                 │
│       │                    ▼                                 │
│       │         indicator_values dict                        │
│       │                    │                                 │
│       ├────────────────────┼────────────────────┐            │
│       │                    │                    │            │
│       ▼                    ▼                    ▼            │
│  RegimeDetectorBridge  RegimeDetector    StrategyRouter     │
│       │                    │                    │            │
│       ▼                    ▼                    ▼            │
│  RegimeState        ActiveRegimes     MatchedStrategySets   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                     │
                     ▼
              Strategy Execution
```

**Flow:**
1. BotController receives new bar
2. FeatureEngine calculates FeatureVector
3. ConfigBasedStrategyCatalog processes FeatureVector
4. IndicatorValueCalculator maps FeatureVector → indicator values
5. RegimeDetector evaluates JSON regime conditions
6. StrategyRouter routes regimes → strategy sets
7. RegimeDetectorBridge converts to RegimeState (for backward compatibility)

---

## Quick Start

### 1. Create JSON Config

Create `config/trading_bot_config.json`:

```json
{
  "schema_version": "1.0.0",
  "indicators": [
    {
      "id": "rsi14",
      "type": "rsi",
      "params": {"period": 14}
    },
    {
      "id": "adx14",
      "type": "adx",
      "params": {"period": 14}
    }
  ],
  "regimes": [
    {
      "id": "trending",
      "name": "Trending Market",
      "conditions": {
        "all": [
          {
            "left": {"indicator_id": "adx14", "field": "value"},
            "op": "gt",
            "right": {"value": 25}
          }
        ]
      },
      "priority": 10,
      "scope": "entry"
    }
  ],
  "strategies": [
    {
      "id": "trend_follow",
      "name": "Trend Following",
      "entry": {
        "all": [
          {
            "left": {"indicator_id": "adx14", "field": "value"},
            "op": "gt",
            "right": {"value": 25}
          }
        ]
      },
      "exit": {
        "all": [
          {
            "left": {"indicator_id": "adx14", "field": "value"},
            "op": "lt",
            "right": {"value": 20}
          }
        ]
      },
      "risk": {
        "position_size": 0.02,
        "stop_loss": 0.02,
        "take_profit": 0.06
      }
    }
  ],
  "strategy_sets": [
    {
      "id": "set_trend",
      "name": "Trending Strategies",
      "strategies": [
        {"strategy_id": "trend_follow"}
      ]
    }
  ],
  "routing": [
    {
      "strategy_set_id": "set_trend",
      "match": {"all_of": ["trending"]}
    }
  ]
}
```

### 2. Use in BotController

```python
from src.core.tradingbot.config_integration_bridge import (
    ConfigBasedStrategyCatalog,
    load_json_config_if_available,
)

# In BotController.__init__:
def __init__(self, config: FullBotConfig, ...):
    # ... existing code ...

    # Try to load JSON config
    json_config = load_json_config_if_available("config/trading_bot_config.json")

    if json_config:
        # Use JSON-based catalog
        self._json_catalog = ConfigBasedStrategyCatalog(json_config)
        logger.info("Using JSON-based strategy catalog")
    else:
        # Fallback to hardcoded catalog
        self._json_catalog = None
        self._strategy_catalog = StrategyCatalog()
        logger.info("Using hardcoded strategy catalog")
```

### 3. Process New Bars

```python
def process_bar(self, bar: dict):
    # Calculate features (existing code)
    features = self._feature_engine.calculate_features(self._bar_buffer)

    # Get current regime
    if self._json_catalog:
        # JSON-based regime detection
        regime = self._json_catalog.get_current_regime(features)
    else:
        # Hardcoded regime detection (existing code)
        regime = self._calculate_regime_from_features(features)

    self._regime = regime

    # Get active strategy sets (if using JSON)
    if self._json_catalog:
        matched_sets = self._json_catalog.get_active_strategy_sets(features)
        strategy_ids = self._json_catalog.get_strategy_ids_from_sets(matched_sets)

        # Execute strategies...
        for strategy_id in strategy_ids:
            # TODO: Execute strategy logic
            pass
```

---

## Integration Points

### IndicatorValueCalculator

**Purpose:** Maps FeatureVector fields to indicator_id/field format.

**Supported Indicators:**
- RSI: `rsi`, `rsi14`
- ADX: `adx`, `adx14`
- MACD: `macd`, `macd_signal`, `macd_histogram`
- SMA: `sma20`, `sma50`, `sma_fast`, `sma_slow`
- EMA: `ema12`, `ema26`, `ema_fast`, `ema_slow`
- Bollinger Bands: `bb_upper`, `bb_middle`, `bb_lower`, `bb_width`
- ATR: `atr`, `atr14`
- Stochastic: `stoch_k`, `stoch_d`
- CCI: `cci`, `cci20`
- MFI: `mfi`, `mfi14`
- Volume: `volume`, `volume_sma`
- Price: `close`, `open`, `high`, `low`

**Usage:**
```python
from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

indicator_values = IndicatorValueCalculator.calculate_indicator_values(feature_vector)
# Returns: {"rsi14": {"value": 65.5}, "adx14": {"value": 30}, ...}
```

### RegimeDetectorBridge

**Purpose:** Converts JSON-based regime detection to RegimeState.

**Mapping:**
- Regime ID contains "trend" → `trending=True`
- Regime ID contains "range" → `ranging=True`
- Regime ID contains "volatile"/"breakout" → `volatile=True`
- No regime detected → `regime_name="neutral"`

**Usage:**
```python
from src.core.tradingbot.config_integration_bridge import RegimeDetectorBridge
from src.core.tradingbot.config import RegimeDetector

regime_detector = RegimeDetector(config.regimes)
bridge = RegimeDetectorBridge(regime_detector)

regime_state = bridge.detect_regime_from_features(feature_vector)
# Returns: RegimeState(trending=True, regime_name="Trending Market", ...)
```

### ConfigBasedStrategyCatalog

**Purpose:** Alternative to hardcoded StrategyCatalog.

**API:**
```python
from src.core.tradingbot.config_integration_bridge import ConfigBasedStrategyCatalog

catalog = ConfigBasedStrategyCatalog(json_config)

# Get active strategy sets
matched_sets = catalog.get_active_strategy_sets(feature_vector)

# Get current regime
regime = catalog.get_current_regime(feature_vector)

# Get strategy IDs
strategy_ids = catalog.get_strategy_ids_from_sets(matched_sets)

# List available items
catalog.list_strategies()     # → ["trend_follow", "mean_reversion", ...]
catalog.list_strategy_sets()  # → ["set_trend", "set_range", ...]
catalog.list_regimes()         # → ["trending", "range", "low_vol", ...]
```

---

## Migration Strategy

### Phase 1: Add JSON Support (Optional)

**Goal:** Add JSON config alongside hardcoded strategies (no removal).

```python
# BotController.__init__
json_config = load_json_config_if_available()

if json_config:
    self._json_catalog = ConfigBasedStrategyCatalog(json_config)
else:
    self._json_catalog = None

# Keep existing hardcoded catalog
self._strategy_catalog = StrategyCatalog()
```

**Benefits:**
- Zero risk (fallback always available)
- Test JSON config in parallel
- Compare JSON vs. hardcoded results

### Phase 2: Prefer JSON (Fallback to Hardcoded)

**Goal:** Use JSON if available, otherwise hardcoded.

```python
# BotController.__init__
json_config = load_json_config_if_available()

if json_config:
    self._json_catalog = ConfigBasedStrategyCatalog(json_config)
    self._strategy_catalog = None  # Don't create hardcoded
else:
    self._json_catalog = None
    self._strategy_catalog = StrategyCatalog()  # Fallback

# In process_bar:
if self._json_catalog:
    regime = self._json_catalog.get_current_regime(features)
    matched_sets = self._json_catalog.get_active_strategy_sets(features)
else:
    # Fallback to hardcoded
    regime = self._calculate_regime_from_features(features)
    strategies = self._strategy_selector.select_strategy(regime)
```

**Benefits:**
- Gradual rollout
- Easy rollback (delete JSON file)
- Production-safe

### Phase 3: JSON-Only (Remove Hardcoded)

**Goal:** Remove hardcoded strategies entirely.

```python
# BotController.__init__
json_config_path = config.bot.strategy_config_path  # From BotConfig
json_config = load_json_config_if_available(json_config_path)

if not json_config:
    raise ValueError("JSON config required but not found")

self._json_catalog = ConfigBasedStrategyCatalog(json_config)

# Remove: self._strategy_catalog, self._strategy_selector, etc.
```

**Benefits:**
- Single source of truth
- No duplication
- Clean codebase

---

## Examples

### Example 1: Detect Regime and Route to Strategies

```python
from src.core.tradingbot.config_integration_bridge import ConfigBasedStrategyCatalog
from src.core.tradingbot.config import ConfigLoader

# Load JSON config
loader = ConfigLoader()
config = loader.load_config("config/trading_bot_config.json")

# Create catalog
catalog = ConfigBasedStrategyCatalog(config)

# Process new bar
feature_vector = feature_engine.calculate_features(bar_buffer)

# Get current regime
regime = catalog.get_current_regime(feature_vector)
print(f"Regime: {regime.regime_name}, Trending: {regime.trending}")

# Get active strategy sets
matched_sets = catalog.get_active_strategy_sets(feature_vector)
print(f"Matched {len(matched_sets)} strategy sets:")
for matched_set in matched_sets:
    print(f"  - {matched_set.name}")

# Get strategy IDs to execute
strategy_ids = catalog.get_strategy_ids_from_sets(matched_sets)
print(f"Execute strategies: {strategy_ids}")
```

### Example 2: Custom Indicator Mapping

If you have custom indicators not in the default mapping:

```python
from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

# Add custom mapping
IndicatorValueCalculator.INDICATOR_MAPPING["my_custom_indicator"] = "my_feature_field"

# Now it will be included
indicator_values = IndicatorValueCalculator.calculate_indicator_values(feature_vector)
# → {"my_custom_indicator": {"value": ...}, ...}
```

### Example 3: Override Config Path

```python
from pathlib import Path
from src.core.tradingbot.config_integration_bridge import create_strategy_catalog

# Load from custom path
custom_path = Path("03_JSON/Trading_Bot/configs/aggressive_config.json")
catalog = create_strategy_catalog(json_config_path=custom_path)

if catalog:
    print("Using JSON config from custom path")
else:
    print("Fallback to hardcoded strategies")
```

---

## Troubleshooting

### Issue: "No JSON config found"

**Solution:** Place JSON config in one of these locations:
- `03_JSON/Trading_Bot/configs/active_config.json`
- `config/trading_bot_config.json`
- `trading_bot_config.json`

Or specify path explicitly:
```python
catalog = create_strategy_catalog(json_config_path="path/to/config.json")
```

### Issue: "ConditionEvaluationError: Missing indicator value"

**Cause:** JSON config references indicator not calculated by FeatureEngine.

**Solution:**
1. Check `IndicatorValueCalculator.INDICATOR_MAPPING`
2. Add missing indicator to FeatureEngine
3. Or update JSON config to use available indicators

### Issue: "No strategy sets matched"

**Cause:** No regimes are active (conditions not met).

**Debug:**
```python
# Check indicator values
indicator_values = IndicatorValueCalculator.calculate_indicator_values(features)
print(indicator_values)

# Check active regimes
active_regimes = catalog.regime_detector.detect_active_regimes(indicator_values)
print(f"Active regimes: {[r.id for r in active_regimes]}")
```

### Issue: "Regime detection too slow"

**Check:** Performance should be <20ms for multi-regime detection.

**Debug:**
```python
import time

start = time.perf_counter()
regime = catalog.get_current_regime(features)
duration = (time.perf_counter() - start) * 1000
print(f"Regime detection: {duration:.2f}ms")
```

If > 50ms, check:
- Too many regimes (>20)?
- Complex condition groups (deeply nested)?
- Missing indicator values (causing retries)?

---

## Best Practices

1. **Start with Phase 1** - Add JSON alongside hardcoded, test in parallel
2. **Validate JSON** - Use `tools/validate_config.py` before deployment
3. **Log Everything** - Enable debug logging to see regime/strategy decisions
4. **Monitor Performance** - Track regime detection and routing times
5. **Version Control** - Commit JSON configs to git with meaningful messages
6. **Test Extensively** - Write integration tests for your specific configs
7. **Gradual Rollout** - Test on paper trading before live

---

## Next Steps

- ✅ Phase 4.1: Bridge pattern (this guide)
- 🔄 Phase 4.2: Modify BotController to use ConfigBasedStrategyCatalog
- ⏳ Phase 4.3: Wire up indicator calculation pipeline
- ⏳ Phase 4.4: Integrate regime detection into trading loop
- ⏳ Phase 4.5: Add live config reloading
- ⏳ Phase 4.6: Strategy state persistence

See `docs/integration/RegimeBasedJSON_Integration_Plan.md` for full roadmap.
