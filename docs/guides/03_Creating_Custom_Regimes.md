# Creating Custom Regimes Guide

**Last Updated:** 2026-01-20
**Version:** 1.0.0

---

## Table of Contents

1. [Introduction](#introduction)
2. [Regime Design Patterns](#regime-design-patterns)
3. [Step-by-Step Regime Creation](#step-by-step-regime-creation)
4. [Advanced Regime Techniques](#advanced-regime-techniques)
5. [Testing & Validation](#testing--validation)
6. [Best Practices](#best-practices)

---

## Introduction

**Custom regimes** allow you to detect specific market conditions that match your trading style. This guide covers:

- ✅ Common regime patterns (trend, range, volatility, volume)
- ✅ Multi-indicator regime definitions
- ✅ Nested logic for complex conditions
- ✅ Regime priority and scope management

**Prerequisites:**
- Read [Getting Started Guide](01_Getting_Started_Regime_Based_Strategies.md)
- Understand [JSON Configuration Format](02_JSON_Configuration_Format_Guide.md)

---

## Regime Design Patterns

### Pattern 1: Trend Detection

**Goal:** Detect strong uptrends and downtrends using ADX and directional indicators.

**Indicators Needed:**
- ADX (trend strength)
- +DI (positive directional indicator)
- -DI (negative directional indicator)

**Uptrend Regime:**
```json
{
  "id": "uptrend",
  "name": "Uptrend",
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

**Downtrend Regime:**
```json
{
  "id": "downtrend",
  "name": "Downtrend",
  "scope": "entry",
  "priority": 10,
  "conditions": {
    "all": [
      {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 25}},
      {"left": {"indicator": "minus_di"}, "op": "gt", "right": {"indicator": "plus_di"}}
    ]
  }
}
```

### Pattern 2: Ranging Market Detection

**Goal:** Detect sideways/choppy markets with low trend strength.

**Indicators Needed:**
- ADX (trend strength)
- Price vs moving averages (SMA 20, SMA 50)

**Ranging Regime:**
```json
{
  "id": "ranging",
  "name": "Ranging Market",
  "scope": "entry",
  "priority": 5,
  "conditions": {
    "all": [
      {"left": {"indicator": "adx"}, "op": "lt", "right": {"value": 20}},
      {
        "any": [
          {"left": {"indicator": "price"}, "op": "between", "right": {"min_indicator": "sma_20", "max_indicator": "sma_50"}},
          {"left": {"indicator": "rsi"}, "op": "between", "right": {"min": 40, "max": 60}}
        ]
      }
    ]
  }
}
```

### Pattern 3: Volatility Regimes

**Goal:** Classify volatility levels for risk management.

**Indicators Needed:**
- ATR (volatility)
- Historical ATR average

**Low Volatility:**
```json
{
  "id": "low_volatility",
  "name": "Low Volatility",
  "scope": "global",
  "conditions": {
    "all": [
      {"left": {"indicator": "atr_pct"}, "op": "lt", "right": {"value": 1.5}}
    ]
  }
}
```

**High Volatility:**
```json
{
  "id": "high_volatility",
  "name": "High Volatility",
  "scope": "global",
  "conditions": {
    "all": [
      {"left": {"indicator": "atr_pct"}, "op": "gt", "right": {"value": 3.0}}
    ]
  }
}
```

**Extreme Volatility:**
```json
{
  "id": "extreme_volatility",
  "name": "Extreme Volatility",
  "scope": "global",
  "priority": 15,
  "conditions": {
    "all": [
      {"left": {"indicator": "atr_pct"}, "op": "gt", "right": {"value": 5.0}}
    ]
  }
}
```

### Pattern 4: Volume Confirmation

**Goal:** Require volume confirmation for regime changes.

**Indicators Needed:**
- Volume
- Volume SMA

**High Volume Regime:**
```json
{
  "id": "high_volume_breakout",
  "name": "High Volume Breakout",
  "scope": "entry",
  "priority": 12,
  "conditions": {
    "all": [
      {"left": {"indicator": "volume"}, "op": "gt", "right": {"indicator": "volume_sma", "multiplier": 1.5}},
      {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "bb_upper"}}
    ]
  }
}
```

---

## Step-by-Step Regime Creation

### Example: Create "Bullish Reversal" Regime

**Goal:** Detect oversold conditions in an uptrend (buy the dip).

#### Step 1: Define Required Indicators

```json
"indicators": [
  {"id": "rsi", "type": "RSI", "params": {"period": 14}},
  {"id": "sma_50", "type": "SMA", "params": {"period": 50, "source": "close"}},
  {"id": "adx", "type": "ADX", "params": {"period": 14}}
]
```

#### Step 2: Write Regime Logic

**Conditions:**
1. Price above 50-day SMA (uptrend context)
2. RSI < 35 (oversold)
3. ADX > 20 (some trend strength)

```json
{
  "id": "bullish_reversal",
  "name": "Bullish Reversal (Oversold in Uptrend)",
  "scope": "entry",
  "priority": 12,
  "conditions": {
    "all": [
      {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "sma_50"}},
      {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 35}},
      {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 20}}
    ]
  }
}
```

#### Step 3: Test with Backtest

Run backtest to verify regime detects expected conditions:

1. Load config in Entry Analyzer
2. Run backtest on historical data
3. Review regime change markers on chart
4. Verify regime triggered at expected points (oversold dips in uptrends)

#### Step 4: Refine Thresholds

Adjust based on results:
- If too many false positives → tighten RSI threshold (e.g., RSI < 30)
- If too few detections → loosen thresholds (e.g., RSI < 40)

---

## Advanced Regime Techniques

### Technique 1: Multi-Timeframe Regimes

Combine indicators from multiple timeframes (requires multi-TF data):

```json
{
  "id": "aligned_trend",
  "name": "Aligned Trend (Multiple Timeframes)",
  "scope": "entry",
  "conditions": {
    "all": [
      {"left": {"indicator": "ema_20_1h"}, "op": "gt", "right": {"indicator": "ema_50_1h"}},
      {"left": {"indicator": "ema_20_4h"}, "op": "gt", "right": {"indicator": "ema_50_4h"}},
      {"left": {"indicator": "ema_20_1d"}, "op": "gt", "right": {"indicator": "ema_50_1d"}}
    ]
  }
}
```

### Technique 2: Nested Logic (Complex Conditions)

**Goal:** Detect breakout OR pullback in uptrend.

```json
{
  "id": "uptrend_entry_opportunity",
  "name": "Uptrend Entry (Breakout OR Pullback)",
  "scope": "entry",
  "conditions": {
    "all": [
      {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 25}},
      {
        "any": [
          {
            "all": [
              {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "bb_upper"}},
              {"left": {"indicator": "volume"}, "op": "gt", "right": {"indicator": "volume_sma", "multiplier": 1.5}}
            ]
          },
          {
            "all": [
              {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 40}},
              {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "sma_50"}}
            ]
          }
        ]
      }
    ]
  }
}
```

**Logic Breakdown:**
1. ADX > 25 (trending) **AND**
2. **Either:**
   - Price breaks above BB upper + volume spike (breakout)
   - **OR**
   - RSI < 40 and price above SMA 50 (pullback)

### Technique 3: Time-Based Regimes

**Goal:** Different regimes for market sessions (Asia, Europe, US).

```json
{
  "id": "us_market_hours",
  "name": "US Market Hours",
  "scope": "global",
  "conditions": {
    "all": [
      {"left": {"time_hour"}, "op": "between", "right": {"min": 9, "max": 16}},
      {"left": {"time_zone"}, "op": "eq", "right": {"value": "US/Eastern"}}
    ]
  }
}
```

**Note:** Time-based conditions require custom implementation.

---

## Testing & Validation

### Validation Checklist

Before deploying a custom regime:

- [ ] **Backtest:** Run 6-12 months of historical data
- [ ] **Regime Frequency:** Check how often regime triggers (aim for 5-20% of time)
- [ ] **Stability:** Verify regime doesn't oscillate rapidly (use Performance Monitor Widget)
- [ ] **Performance:** Strategies in this regime have positive Sharpe ratio
- [ ] **Edge Cases:** Test with extreme market conditions (crashes, rallies)

### Common Issues

**Issue 1: Regime Never Triggers**
- **Symptom:** 0 regime changes in backtest
- **Fix:** Loosen conditions (lower ADX threshold, widen RSI range)

**Issue 2: Regime Triggers Too Often**
- **Symptom:** 100+ regime changes per day
- **Fix:** Tighten conditions, add confirmation indicators

**Issue 3: Conflicting Regimes**
- **Symptom:** Multiple regimes active simultaneously
- **Fix:** Use `none_of` in routing to exclude conflicting regimes, or adjust priorities

---

## Best Practices

### 1. **Use Descriptive IDs and Names**

❌ **Bad:**
```json
{"id": "r1", "name": "Regime 1"}
```

✅ **Good:**
```json
{"id": "strong_uptrend_high_vol", "name": "Strong Uptrend with High Volatility"}
```

### 2. **Set Appropriate Priorities**

**Priority Guidelines:**
- **15-20:** Critical regimes (extreme volatility, news events)
- **10-14:** Strong trend/range regimes
- **5-9:** Moderate regimes
- **0-4:** Weak/fallback regimes

### 3. **Use Scope Correctly**

| **Scope** | **Use Case** |
|-----------|--------------|
| `entry` | Regime must be active BEFORE opening position |
| `exit` | Check during position (exit signals) |
| `in_trade` | Monitor during position (but don't force exit) |
| `global` | Background monitoring (volatility, time) |

### 4. **Combine Indicators for Confirmation**

**Single Indicator (Weak):**
```json
{"all": [{"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 30}}]}
```

**Multiple Indicators (Strong):**
```json
{
  "all": [
    {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 30}},
    {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "sma_200"}},
    {"left": {"indicator": "volume"}, "op": "gt", "right": {"indicator": "volume_sma"}}
  ]
}
```

### 5. **Document Your Regimes**

Always add `description` field:

```json
{
  "id": "bullish_reversal",
  "name": "Bullish Reversal",
  "description": "Oversold conditions (RSI < 35) in established uptrend (price > SMA 50, ADX > 20). Designed for mean reversion entries.",
  ...
}
```

---

## Next Steps

- **Read:** [Strategy Creation Guide](04_Strategy_Creation_Guide.md)
- **Read:** [Advanced Features Guide](05_Advanced_Features_Guide.md)
- **Practice:** Create 3-5 custom regimes for your trading style
- **Backtest:** Validate regimes with historical data

---

**Examples:** See `03_JSON/Trading_Bot/` for production regime definitions.
