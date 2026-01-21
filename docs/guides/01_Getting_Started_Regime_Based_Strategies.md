# Getting Started with Regime-Based Trading Strategies

**Last Updated:** 2026-01-20
**Version:** 1.0.0
**Audience:** Trading bot users, strategy developers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Why Regime-Based Strategies?](#why-regime-based-strategies)
3. [Quick Start (5 Minutes)](#quick-start-5-minutes)
4. [Core Concepts](#core-concepts)
5. [Your First Strategy](#your-first-strategy)
6. [Next Steps](#next-steps)

---

## Introduction

**Regime-based trading** adapts your strategy to market conditions in real-time. Instead of using one strategy for all market states, the bot automatically switches between strategies based on:

- **Trend Detection** (Uptrend, Downtrend, Range)
- **Volatility Levels** (Low, Normal, High, Extreme)
- **Market Structure** (Consolidation, Breakout, Reversal)

This guide will help you:
- ✅ Understand regime-based trading concepts
- ✅ Run your first regime-based backtest
- ✅ Create custom regime definitions
- ✅ Deploy strategies in live trading

**Time Required:** 30-60 minutes to read + hands-on practice

---

## Why Regime-Based Strategies?

### Traditional vs. Regime-Based Approach

| **Traditional (Single Strategy)** | **Regime-Based (Adaptive)** |
|-----------------------------------|------------------------------|
| Same entry/exit rules all the time | Different rules per market regime |
| Fixed risk parameters | Dynamic risk adjustment |
| Works well ONLY in specific markets | Adapts to changing conditions |
| Prone to drawdowns in wrong regime | Reduces drawdowns via regime detection |
| **Example:** RSI(14) > 70 = sell | **Example:** RSI(14) in trending markets, RSI(21) in ranging markets |

### Real-World Example

**Scenario:** Bitcoin trending upward with high volatility

**Traditional Strategy:**
- Enters LONG when RSI(14) < 30 (oversold)
- **Problem:** In strong uptrends, RSI rarely reaches 30 → missed opportunities

**Regime-Based Strategy:**
- **Detects regime:** TREND_UP + HIGH_VOLATILITY
- **Switches to:** Pullback strategy with looser RSI threshold (RSI < 40)
- **Result:** More entries during healthy pullbacks in uptrend

---

## Quick Start (5 Minutes)

### Step 1: Load Sample Config

OrderPilot-AI ships with pre-built regime-based strategies:

```bash
# Navigate to JSON configs
cd 03_JSON/Trading_Bot/

# List available configs
ls *.json

# Example configs:
# - trend_following_conservative.json  (Low-risk trend following)
# - range_breakout_aggressive.json     (High-risk breakout trading)
# - regime_adaptive_balanced.json      (Balanced multi-regime)
```

### Step 2: Run Backtest

Open **Entry Analyzer** in OrderPilot-AI:

1. Click **"Entry Analyzer"** button in toolbar
2. Navigate to **"Backtest Setup"** tab
3. Select config: `03_JSON/Trading_Bot/regime_adaptive_balanced.json`
4. Set date range: Last 6 months
5. Click **"🚀 Run Backtest"**

**Expected Output:**
- Performance metrics (Sharpe, Win Rate, Profit Factor)
- Regime transition chart (vertical lines showing regime changes)
- Equity curve (cumulative returns)
- Trade list with entry/exit details

### Step 3: Analyze Results

**Key Questions to Ask:**
1. **Regime Stability**: How often did regimes change? (Check "Regime Changes" count)
2. **Performance per Regime**: Did strategy perform better in specific regimes?
3. **Drawdown**: What was max drawdown? Is it acceptable for your risk tolerance?
4. **Sharpe Ratio**: Is it above 1.0? (Good strategies typically have Sharpe > 1.5)

**Next:** Modify the config to test different regime definitions →

---

## Core Concepts

### 1. **Regimes**

A **regime** is a market state defined by conditions. Example:

```json
{
  "id": "strong_uptrend",
  "name": "Strong Uptrend",
  "scope": "entry",
  "conditions": {
    "all": [
      {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 25}},
      {"left": {"indicator": "plus_di"}, "op": "gt", "right": {"indicator": "minus_di"}}
    ]
  }
}
```

**Breakdown:**
- **id**: Unique identifier for this regime
- **name**: Human-readable name
- **scope**: When to evaluate (`entry`, `exit`, `in_trade`, `global`)
- **conditions**: Logic to determine if regime is active
  - **all**: ALL conditions must be true (AND logic)
  - **any**: ANY condition must be true (OR logic)

### 2. **Indicators**

Indicators provide market data for regime detection:

```json
{
  "id": "adx",
  "type": "ADX",
  "params": {"period": 14}
}
```

**Available Indicator Types:**
- **Trend**: ADX, SMA, EMA, MACD
- **Momentum**: RSI, Stochastic, CCI
- **Volatility**: ATR, Bollinger Bands, Standard Deviation
- **Volume**: Volume SMA, VWAP, OBV

### 3. **Strategies**

Strategies define entry/exit conditions and risk management:

```json
{
  "id": "trend_pullback",
  "name": "Trend Pullback Entry",
  "entry_conditions": {
    "all": [
      {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 40}},
      {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "sma_50"}}
    ]
  },
  "exit_conditions": {...},
  "risk": {
    "stop_loss_pct": 2.0,
    "take_profit_pct": 4.0,
    "position_size_pct": 5.0
  }
}
```

### 4. **Strategy Sets**

A **strategy set** groups multiple strategies for a specific regime:

```json
{
  "id": "uptrend_strategies",
  "name": "Uptrend Strategy Set",
  "strategies": [
    {"strategy_id": "trend_pullback"},
    {"strategy_id": "breakout_continuation"}
  ],
  "indicator_overrides": {
    "rsi": {"period": 21}  // Use RSI(21) instead of default RSI(14)
  }
}
```

### 5. **Routing Rules**

**Routing** maps regimes to strategy sets:

```json
{
  "match": {
    "all_of": ["strong_uptrend", "high_volatility"]
  },
  "strategy_set_id": "aggressive_uptrend_set"
}
```

**Logic:**
- **all_of**: ALL listed regimes must be active
- **any_of**: ANY listed regime must be active
- **none_of**: NONE of listed regimes must be active

---

## Your First Strategy

Let's create a simple regime-based strategy from scratch.

### Goal: Trade BTC with different strategies for trending vs ranging markets

#### Step 1: Define Indicators

Create `my_first_strategy.json`:

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "name": "My First Regime Strategy",
    "description": "Adaptive BTC strategy for trending and ranging markets",
    "author": "Your Name",
    "created_at": "2026-01-20"
  },
  "indicators": [
    {"id": "adx", "type": "ADX", "params": {"period": 14}},
    {"id": "rsi", "type": "RSI", "params": {"period": 14}},
    {"id": "sma_20", "type": "SMA", "params": {"period": 20}},
    {"id": "sma_50", "type": "SMA", "params": {"period": 50}},
    {"id": "atr", "type": "ATR", "params": {"period": 14}}
  ],
  ...
}
```

#### Step 2: Define Regimes

Add two regimes: **Trending** and **Ranging**

```json
"regimes": [
  {
    "id": "trending",
    "name": "Trending Market",
    "scope": "entry",
    "priority": 10,
    "conditions": {
      "all": [
        {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 25}}
      ]
    }
  },
  {
    "id": "ranging",
    "name": "Ranging Market",
    "scope": "entry",
    "priority": 5,
    "conditions": {
      "all": [
        {"left": {"indicator": "adx"}, "op": "lt", "right": {"value": 20}}
      ]
    }
  }
]
```

**Note:** Higher priority regimes are preferred when multiple regimes match.

#### Step 3: Define Strategies

**Strategy 1: Trend Following** (for trending markets)

```json
"strategies": [
  {
    "id": "trend_following",
    "name": "Trend Following",
    "entry_conditions": {
      "all": [
        {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "sma_50"}},
        {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 50}}
      ]
    },
    "exit_conditions": {
      "any": [
        {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 75}},
        {"left": {"indicator": "price"}, "op": "lt", "right": {"indicator": "sma_20"}}
      ]
    },
    "risk": {
      "stop_loss_pct": 2.5,
      "take_profit_pct": 5.0,
      "position_size_pct": 10.0
    }
  },
  ...
]
```

**Strategy 2: Mean Reversion** (for ranging markets)

```json
{
  "id": "mean_reversion",
  "name": "Mean Reversion",
  "entry_conditions": {
    "all": [
      {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 30}}
    ]
  },
  "exit_conditions": {
    "any": [
      {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 70}}
    ]
  },
  "risk": {
    "stop_loss_pct": 1.5,
    "take_profit_pct": 3.0,
    "position_size_pct": 8.0
  }
}
```

#### Step 4: Create Strategy Sets

```json
"strategy_sets": [
  {
    "id": "trending_set",
    "name": "Trending Market Strategies",
    "strategies": [{"strategy_id": "trend_following"}]
  },
  {
    "id": "ranging_set",
    "name": "Ranging Market Strategies",
    "strategies": [{"strategy_id": "mean_reversion"}]
  }
]
```

#### Step 5: Add Routing Rules

```json
"routing": [
  {
    "match": {"all_of": ["trending"]},
    "strategy_set_id": "trending_set"
  },
  {
    "match": {"all_of": ["ranging"]},
    "strategy_set_id": "ranging_set"
  }
]
```

### Complete JSON Structure

See `docs/guides/02_JSON_Configuration_Format_Guide.md` for the complete schema.

---

## Next Steps

Now that you've created your first regime-based strategy:

1. **Backtest It** → Use Entry Analyzer to test historical performance
2. **Optimize Regimes** → Tune ADX thresholds, RSI levels
3. **Add More Indicators** → Experiment with MACD, Bollinger Bands, Volume
4. **Walk-Forward Validation** → Test robustness with rolling validation (Phase 5)
5. **AI Integration** → Use AI to generate strategies from chart patterns (Phase 6)
6. **Live Trading** → Deploy to paper trading first, then live

### Recommended Reading Order

1. ✅ **You are here** - Getting Started
2. 📖 **Next** - [JSON Configuration Format Guide](02_JSON_Configuration_Format_Guide.md)
3. 📖 [Creating Custom Regimes](03_Creating_Custom_Regimes.md)
4. 📖 [Strategy Creation Guide](04_Strategy_Creation_Guide.md)
5. 📖 [Advanced Features (Walk-Forward, AI)](05_Advanced_Features_Guide.md)

### Support

- **Documentation:** `/docs/guides/`
- **Sample Configs:** `/03_JSON/Trading_Bot/`
- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)

---

**Happy Trading! 🚀**
