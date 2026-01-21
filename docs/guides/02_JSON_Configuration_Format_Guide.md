# JSON Configuration Format Guide

**Last Updated:** 2026-01-20
**Version:** 1.0.0
**Schema Version:** 1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Complete JSON Schema](#complete-json-schema)
3. [Root Structure](#root-structure)
4. [Indicators Section](#indicators-section)
5. [Regimes Section](#regimes-section)
6. [Strategies Section](#strategies-section)
7. [Strategy Sets Section](#strategy-sets-section)
8. [Routing Section](#routing-section)
9. [Validation Rules](#validation-rules)
10. [Complete Example](#complete-example)

---

## Overview

OrderPilot-AI uses **JSON configuration files** to define regime-based trading strategies. This format provides:

- ✅ **Type-Safe Validation** (JSON Schema + Pydantic models)
- ✅ **Version Control** (Git-friendly text format)
- ✅ **Human-Readable** (Easy to edit and review)
- ✅ **Modular Design** (Reusable indicators, strategies, regimes)
- ✅ **Cross-Platform** (Works on Windows, Linux, macOS)

**Key Principles:**
1. **Declarative**: Define WHAT you want, not HOW to do it
2. **Composable**: Build complex strategies from simple building blocks
3. **Validated**: Errors caught at load-time, not runtime

---

## Complete JSON Schema

The full JSON Schema is located at:
```
03_JSON/schema/strategy_config_schema.json
```

**Schema Standard:** [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema)

**Validation Tools:**
- Python: `src/core/tradingbot/config/loader.py` (ConfigLoader)
- CLI: `python -m src.core.tradingbot.config.loader validate <config.json>`

---

## Root Structure

Every JSON config file must have this top-level structure:

```json
{
  "schema_version": "1.0.0",
  "metadata": { ... },
  "indicators": [ ... ],
  "regimes": [ ... ],
  "strategies": [ ... ],
  "strategy_sets": [ ... ],
  "routing": [ ... ]
}
```

### Root Fields

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| `schema_version` | String | ✅ | Must be `"1.0.0"` |
| `metadata` | Object | ❌ | Optional metadata (name, description, author) |
| `indicators` | Array | ✅ | List of indicator definitions |
| `regimes` | Array | ✅ | List of regime definitions |
| `strategies` | Array | ✅ | List of strategy definitions |
| `strategy_sets` | Array | ✅ | List of strategy set definitions |
| `routing` | Array | ✅ | List of routing rules |

---

## Indicators Section

Indicators provide market data for regime detection and strategy conditions.

### Indicator Structure

```json
{
  "id": "rsi_14",
  "type": "RSI",
  "params": {
    "period": 14,
    "source": "close"
  }
}
```

### Indicator Fields

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| `id` | String | ✅ | Unique identifier (used in conditions) |
| `type` | String (Enum) | ✅ | Indicator type (see table below) |
| `params` | Object | ✅ | Indicator-specific parameters |

### Supported Indicator Types

#### Trend Indicators

| **Type** | **Parameters** | **Description** |
|----------|---------------|-----------------|
| `SMA` | `period`, `source` | Simple Moving Average |
| `EMA` | `period`, `source` | Exponential Moving Average |
| `WMA` | `period`, `source` | Weighted Moving Average |
| `DEMA` | `period`, `source` | Double Exponential Moving Average |
| `TEMA` | `period`, `source` | Triple Exponential Moving Average |

#### Momentum Indicators

| **Type** | **Parameters** | **Description** |
|----------|---------------|-----------------|
| `RSI` | `period` (default: 14) | Relative Strength Index |
| `MACD` | `fast`, `slow`, `signal` | Moving Average Convergence Divergence |
| `Stochastic` | `k_period`, `d_period`, `smooth_k` | Stochastic Oscillator |
| `CCI` | `period` (default: 20) | Commodity Channel Index |
| `ROC` | `period` | Rate of Change |
| `MFI` | `period` (default: 14) | Money Flow Index |

#### Volatility Indicators

| **Type** | **Parameters** | **Description** |
|----------|---------------|-----------------|
| `ATR` | `period` (default: 14) | Average True Range |
| `BB` | `period`, `std_dev` (default: 2.0) | Bollinger Bands |
| `KC` | `period`, `atr_period`, `multiplier` | Keltner Channels |
| `STDDEV` | `period` | Standard Deviation |

#### Volume Indicators

| **Type** | **Parameters** | **Description** |
|----------|---------------|-----------------|
| `Volume_SMA` | `period` | Volume Simple Moving Average |
| `VWAP` | (none) | Volume Weighted Average Price |
| `OBV` | (none) | On-Balance Volume |
| `AD` | (none) | Accumulation/Distribution |

#### Trend Strength Indicators

| **Type** | **Parameters** | **Description** |
|----------|---------------|-----------------|
| `ADX` | `period` (default: 14) | Average Directional Index |
| `PLUS_DI` | `period` (default: 14) | Plus Directional Indicator |
| `MINUS_DI` | `period` (default: 14) | Minus Directional Indicator |

### Example: Multiple Indicators

```json
"indicators": [
  {"id": "rsi", "type": "RSI", "params": {"period": 14}},
  {"id": "rsi_fast", "type": "RSI", "params": {"period": 7}},
  {"id": "adx", "type": "ADX", "params": {"period": 14}},
  {"id": "plus_di", "type": "PLUS_DI", "params": {"period": 14}},
  {"id": "minus_di", "type": "MINUS_DI", "params": {"period": 14}},
  {"id": "atr", "type": "ATR", "params": {"period": 14}},
  {"id": "bb_upper", "type": "BB", "params": {"period": 20, "std_dev": 2.0}},
  {"id": "sma_50", "type": "SMA", "params": {"period": 50, "source": "close"}},
  {"id": "ema_200", "type": "EMA", "params": {"period": 200, "source": "close"}},
  {"id": "macd", "type": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}}
]
```

---

## Regimes Section

Regimes define market states using indicator-based conditions.

### Regime Structure

```json
{
  "id": "strong_uptrend",
  "name": "Strong Uptrend",
  "description": "ADX > 25 and +DI > -DI",
  "scope": "entry",
  "priority": 10,
  "conditions": {
    "all": [
      {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 25}},
      {"left": {"indicator": "plus_di"}, "op": "gt", "right": {"indicator": "minus_di"}}
    ]
  }
}
```

### Regime Fields

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| `id` | String | ✅ | Unique identifier |
| `name` | String | ✅ | Human-readable name |
| `description` | String | ❌ | Optional description |
| `scope` | String (Enum) | ✅ | When to evaluate: `entry`, `exit`, `in_trade`, `global` |
| `priority` | Integer | ❌ | Priority (higher = preferred), default: 0 |
| `conditions` | ConditionGroup | ✅ | Conditions to match regime |

### Condition Operators

| **Operator** | **Symbol** | **Description** | **Example** |
|--------------|-----------|-----------------|-------------|
| Greater Than | `gt` | Left > Right | `{"op": "gt", "left": {...}, "right": {...}}` |
| Less Than | `lt` | Left < Right | `{"op": "lt", "left": {...}, "right": {...}}` |
| Equal | `eq` | Left == Right | `{"op": "eq", "left": {...}, "right": {...}}` |
| Between | `between` | Min <= Left <= Max | `{"op": "between", "left": {...}, "right": {"min": 30, "max": 70}}` |

### Condition Operands

**Indicator Reference:**
```json
{"indicator": "rsi"}
```

**Constant Value:**
```json
{"value": 50}
```

**Between Range:**
```json
{"min": 30, "max": 70}
```

### Logic Groups

**AND Logic (all conditions must be true):**
```json
{
  "all": [
    {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 25}},
    {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 50}}
  ]
}
```

**OR Logic (any condition must be true):**
```json
{
  "any": [
    {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 30}},
    {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 70}}
  ]
}
```

**Nested Logic:**
```json
{
  "all": [
    {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 25}},
    {
      "any": [
        {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 30}},
        {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 70}}
      ]
    }
  ]
}
```

### Scope Values

| **Scope** | **Description** | **When Evaluated** |
|-----------|-----------------|-------------------|
| `entry` | Entry regime | Before opening position |
| `exit` | Exit regime | While position is open (exit checks) |
| `in_trade` | In-trade regime | While position is open (monitoring) |
| `global` | Global regime | Always evaluated (background) |

---

## Strategies Section

Strategies define entry/exit conditions and risk management.

### Strategy Structure

```json
{
  "id": "trend_pullback",
  "name": "Trend Pullback Entry",
  "description": "Enter on RSI pullback in uptrend",
  "entry_conditions": {
    "all": [
      {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 40}},
      {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "sma_50"}}
    ]
  },
  "exit_conditions": {
    "any": [
      {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 75}},
      {"left": {"indicator": "price"}, "op": "lt", "right": {"indicator": "sma_20"}}
    ]
  },
  "risk": {
    "stop_loss_pct": 2.0,
    "take_profit_pct": 4.0,
    "position_size_pct": 5.0,
    "trailing_stop_pct": null,
    "max_holding_bars": null
  }
}
```

### Strategy Fields

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| `id` | String | ✅ | Unique identifier |
| `name` | String | ✅ | Human-readable name |
| `description` | String | ❌ | Optional description |
| `entry_conditions` | ConditionGroup | ✅ | Conditions to enter trade |
| `exit_conditions` | ConditionGroup | ✅ | Conditions to exit trade |
| `risk` | RiskConfig | ✅ | Risk management parameters |

### Risk Configuration

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| `stop_loss_pct` | Float | ✅ | Stop loss as % of entry price |
| `take_profit_pct` | Float | ✅ | Take profit as % of entry price |
| `position_size_pct` | Float | ✅ | Position size as % of capital |
| `trailing_stop_pct` | Float | ❌ | Trailing stop as % (optional) |
| `max_holding_bars` | Integer | ❌ | Max bars to hold (optional) |

---

## Strategy Sets Section

Strategy sets group multiple strategies and allow parameter overrides.

### Strategy Set Structure

```json
{
  "id": "uptrend_aggressive",
  "name": "Aggressive Uptrend Strategies",
  "description": "High-risk strategies for strong uptrends",
  "strategies": [
    {"strategy_id": "trend_pullback"},
    {"strategy_id": "breakout_continuation"}
  ],
  "indicator_overrides": {
    "rsi": {"period": 21}
  },
  "strategy_overrides": {
    "trend_pullback": {
      "risk": {"position_size_pct": 8.0}
    }
  }
}
```

### Strategy Set Fields

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| `id` | String | ✅ | Unique identifier |
| `name` | String | ✅ | Human-readable name |
| `description` | String | ❌ | Optional description |
| `strategies` | Array | ✅ | List of strategy references |
| `indicator_overrides` | Object | ❌ | Override indicator params |
| `strategy_overrides` | Object | ❌ | Override strategy params |

### Parameter Overrides

**Indicator Override Example:**
```json
"indicator_overrides": {
  "rsi": {"period": 21},       // Change RSI period from 14 to 21
  "atr": {"period": 20}         // Change ATR period from 14 to 20
}
```

**Strategy Override Example:**
```json
"strategy_overrides": {
  "trend_pullback": {
    "risk": {
      "stop_loss_pct": 3.0,           // Wider stop loss
      "position_size_pct": 8.0        // Larger position
    }
  }
}
```

---

## Routing Section

Routing rules map regime combinations to strategy sets.

### Routing Rule Structure

```json
{
  "match": {
    "all_of": ["strong_uptrend", "high_volatility"],
    "any_of": null,
    "none_of": ["ranging_market"]
  },
  "strategy_set_id": "uptrend_aggressive"
}
```

### Routing Fields

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| `match` | RoutingMatch | ✅ | Regime matching criteria |
| `strategy_set_id` | String | ✅ | Strategy set to use |

### Routing Match Criteria

| **Field** | **Type** | **Description** |
|-----------|----------|-----------------|
| `all_of` | Array[String] | ALL listed regimes must be active (AND) |
| `any_of` | Array[String] | ANY listed regime must be active (OR) |
| `none_of` | Array[String] | NONE of listed regimes must be active (NOT) |

### Routing Logic Examples

**Example 1: Single Regime Match**
```json
{
  "match": {"all_of": ["trending"]},
  "strategy_set_id": "trend_following_set"
}
```

**Example 2: Multiple Regime Match (AND)**
```json
{
  "match": {"all_of": ["strong_uptrend", "high_volatility"]},
  "strategy_set_id": "aggressive_uptrend_set"
}
```

**Example 3: Any Regime Match (OR)**
```json
{
  "match": {"any_of": ["ranging", "low_volatility"]},
  "strategy_set_id": "mean_reversion_set"
}
```

**Example 4: Exclusion (NOT)**
```json
{
  "match": {
    "all_of": ["uptrend"],
    "none_of": ["extreme_volatility"]
  },
  "strategy_set_id": "conservative_uptrend_set"
}
```

**Example 5: Complex Combination**
```json
{
  "match": {
    "all_of": ["trending"],
    "any_of": ["breakout_pattern", "continuation_pattern"],
    "none_of": ["low_volume"]
  },
  "strategy_set_id": "breakout_continuation_set"
}
```

---

## Validation Rules

The JSON config is validated in two stages:

### Stage 1: JSON Schema Validation

- ✅ Correct data types (string, number, boolean, array, object)
- ✅ Required fields present
- ✅ Enum values valid (e.g., `scope` must be `entry`, `exit`, `in_trade`, or `global`)
- ✅ Schema version matches

### Stage 2: Pydantic Model Validation

- ✅ Unique IDs (no duplicate indicator/regime/strategy IDs)
- ✅ Valid references (strategy_id, indicator references exist)
- ✅ Numeric ranges (stop_loss_pct > 0, priority >= 0)
- ✅ Condition logic (all/any groups not both present)

### Common Validation Errors

#### Error: Duplicate ID
```
ValidationError: Duplicate indicator ID: 'rsi'
```
**Fix:** Ensure all IDs are unique. Use descriptive names like `rsi_14`, `rsi_21`.

#### Error: Missing Reference
```
ValidationError: Strategy 'trend_pullback' references unknown indicator 'sma_100'
```
**Fix:** Add the referenced indicator to `indicators` section.

#### Error: Invalid Scope
```
ValidationError: Invalid scope 'entry_exit'. Must be one of: entry, exit, in_trade, global
```
**Fix:** Use valid scope value from enum.

---

## Complete Example

See `03_JSON/Trading_Bot/regime_adaptive_balanced.json` for a complete, production-ready example.

**Minimal Working Example:**

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "name": "Simple Regime Strategy",
    "description": "Minimal example for testing"
  },
  "indicators": [
    {"id": "adx", "type": "ADX", "params": {"period": 14}},
    {"id": "rsi", "type": "RSI", "params": {"period": 14}}
  ],
  "regimes": [
    {
      "id": "trending",
      "name": "Trending",
      "scope": "entry",
      "conditions": {
        "all": [{"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 25}}]
      }
    }
  ],
  "strategies": [
    {
      "id": "simple_trend",
      "name": "Simple Trend",
      "entry_conditions": {
        "all": [{"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 50}}]
      },
      "exit_conditions": {
        "any": [{"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 75}}]
      },
      "risk": {
        "stop_loss_pct": 2.0,
        "take_profit_pct": 4.0,
        "position_size_pct": 5.0
      }
    }
  ],
  "strategy_sets": [
    {
      "id": "trend_set",
      "name": "Trend Set",
      "strategies": [{"strategy_id": "simple_trend"}]
    }
  ],
  "routing": [
    {
      "match": {"all_of": ["trending"]},
      "strategy_set_id": "trend_set"
    }
  ]
}
```

---

## Next Steps

- **Read:** [Creating Custom Regimes Guide](03_Creating_Custom_Regimes.md)
- **Read:** [Strategy Creation Guide](04_Strategy_Creation_Guide.md)
- **Practice:** Modify sample configs in `03_JSON/Trading_Bot/`
- **Validate:** Use ConfigLoader to validate your JSON

---

**JSON Schema Reference:** `03_JSON/schema/strategy_config_schema.json`
