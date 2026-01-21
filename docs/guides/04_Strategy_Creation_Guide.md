# Strategy Creation Guide

**Last Updated:** 2026-01-20
**Version:** 1.0.0

---

## Table of Contents

1. [Strategy Fundamentals](#strategy-fundamentals)
2. [Entry Conditions](#entry-conditions)
3. [Exit Conditions](#exit-conditions)
4. [Risk Management](#risk-management)
5. [Strategy Sets & Parameter Overrides](#strategy-sets--parameter-overrides)
6. [Complete Examples](#complete-examples)

---

## Strategy Fundamentals

A **strategy** defines:
- **Entry conditions:** When to open a position
- **Exit conditions:** When to close a position
- **Risk management:** Stop loss, take profit, position sizing

### Basic Strategy Structure

```json
{
  "id": "my_strategy",
  "name": "My Trading Strategy",
  "description": "Clear description of what this strategy does",
  "entry_conditions": { ... },
  "exit_conditions": { ... },
  "risk": { ... }
}
```

---

## Entry Conditions

Entry conditions determine when to open a trade.

### Pattern 1: Trend Following

**Buy when:**
- Price above 50-day SMA (uptrend)
- RSI > 50 (momentum)

```json
"entry_conditions": {
  "all": [
    {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "sma_50"}},
    {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 50}}
  ]
}
```

### Pattern 2: Mean Reversion

**Buy when:**
- RSI < 30 (oversold)
- Price near lower Bollinger Band

```json
"entry_conditions": {
  "all": [
    {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 30}},
    {"left": {"indicator": "price"}, "op": "lt", "right": {"indicator": "bb_lower", "offset": 1.02}}
  ]
}
```

### Pattern 3: Breakout

**Buy when:**
- Price breaks above resistance (e.g., 20-day high)
- High volume (>1.5x average)

```json
"entry_conditions": {
  "all": [
    {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "high_20"}},
    {"left": {"indicator": "volume"}, "op": "gt", "right": {"indicator": "volume_sma", "multiplier": 1.5}}
  ]
}
```

### Pattern 4: MACD Crossover

**Buy when:**
- MACD line crosses above signal line
- Price above 200-day EMA (long-term uptrend)

```json
"entry_conditions": {
  "all": [
    {"left": {"indicator": "macd_line"}, "op": "gt", "right": {"indicator": "macd_signal"}},
    {"left": {"indicator": "macd_histogram"}, "op": "gt", "right": {"value": 0}},
    {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "ema_200"}}
  ]
}
```

---

## Exit Conditions

Exit conditions determine when to close a position.

### Exit Pattern 1: Profit Target

**Sell when:**
- RSI reaches overbought (>75)
- OR MACD histogram turns negative

```json
"exit_conditions": {
  "any": [
    {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 75}},
    {"left": {"indicator": "macd_histogram"}, "op": "lt", "right": {"value": 0}}
  ]
}
```

### Exit Pattern 2: Trend Reversal

**Sell when:**
- Price crosses below 20-day SMA
- OR RSI divergence (price new high, RSI lower high)

```json
"exit_conditions": {
  "any": [
    {"left": {"indicator": "price"}, "op": "lt", "right": {"indicator": "sma_20"}},
    {
      "all": [
        {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "price_prev_high"}},
        {"left": {"indicator": "rsi"}, "op": "lt", "right": {"indicator": "rsi_prev_high"}}
      ]
    }
  ]
}
```

### Exit Pattern 3: Time-Based

**Sell when:**
- Held for more than 20 bars (managed via `max_holding_bars` in risk config)

```json
"risk": {
  "max_holding_bars": 20
}
```

### Exit Pattern 4: Trailing Stop

**Sell when:**
- Price drops 3% from highest point since entry

```json
"risk": {
  "trailing_stop_pct": 3.0
}
```

---

## Risk Management

The `risk` section controls position sizing and loss limits.

### Complete Risk Configuration

```json
"risk": {
  "stop_loss_pct": 2.0,        // Exit if price drops 2% below entry
  "take_profit_pct": 4.0,      // Exit if price rises 4% above entry
  "position_size_pct": 5.0,    // Risk 5% of capital per trade
  "trailing_stop_pct": 3.0,    // Trailing stop at 3% from peak (optional)
  "max_holding_bars": null     // No time limit (optional)
}
```

### Risk-Reward Ratios

**Conservative (1:2 ratio):**
```json
{"stop_loss_pct": 1.0, "take_profit_pct": 2.0}
```

**Balanced (1:2.5 ratio):**
```json
{"stop_loss_pct": 2.0, "take_profit_pct": 5.0}
```

**Aggressive (1:3 ratio):**
```json
{"stop_loss_pct": 3.0, "take_profit_pct": 9.0}
```

### Position Sizing Guidelines

| **Risk Tolerance** | **Position Size %** |
|-------------------|---------------------|
| Very Conservative | 1-2% |
| Conservative | 3-5% |
| Moderate | 5-8% |
| Aggressive | 8-12% |
| Very Aggressive | 12-20% |

**Warning:** Never risk more than 20% of capital per trade.

---

## Strategy Sets & Parameter Overrides

Strategy sets allow you to:
1. Group multiple strategies
2. Override indicator parameters per regime
3. Override risk parameters per regime

### Example: Aggressive vs Conservative Sets

**Conservative Set (Ranging Market):**
```json
{
  "id": "ranging_conservative",
  "name": "Conservative Range Trading",
  "strategies": [{"strategy_id": "mean_reversion"}],
  "indicator_overrides": {
    "rsi": {"period": 21}  // Slower RSI for fewer signals
  },
  "strategy_overrides": {
    "mean_reversion": {
      "risk": {
        "stop_loss_pct": 1.5,       // Tighter stop
        "position_size_pct": 3.0    // Smaller position
      }
    }
  }
}
```

**Aggressive Set (Trending Market):**
```json
{
  "id": "trending_aggressive",
  "name": "Aggressive Trend Following",
  "strategies": [{"strategy_id": "trend_following"}],
  "indicator_overrides": {
    "rsi": {"period": 14}  // Faster RSI for more signals
  },
  "strategy_overrides": {
    "trend_following": {
      "risk": {
        "stop_loss_pct": 3.0,       // Wider stop
        "position_size_pct": 8.0    // Larger position
      }
    }
  }
}
```

### When to Use Overrides

**Use indicator overrides when:**
- Different regimes need different timeframes (e.g., RSI(14) for trending, RSI(21) for ranging)
- Volatility changes require ATR adjustments

**Use strategy overrides when:**
- Risk tolerance varies by regime (more aggressive in strong trends)
- Position sizing depends on market conditions

---

## Complete Examples

### Example 1: Pullback Strategy

**Goal:** Buy dips in uptrends

```json
{
  "id": "pullback_strategy",
  "name": "Pullback in Uptrend",
  "description": "Buy oversold conditions in established uptrend",
  "entry_conditions": {
    "all": [
      {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "ema_50"}},
      {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 40}},
      {"left": {"indicator": "adx"}, "op": "gt", "right": {"value": 20}}
    ]
  },
  "exit_conditions": {
    "any": [
      {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 70}},
      {"left": {"indicator": "price"}, "op": "lt", "right": {"indicator": "ema_20"}}
    ]
  },
  "risk": {
    "stop_loss_pct": 2.5,
    "take_profit_pct": 5.0,
    "position_size_pct": 6.0,
    "trailing_stop_pct": 3.0
  }
}
```

### Example 2: Breakout Strategy

**Goal:** Trade breakouts with volume confirmation

```json
{
  "id": "breakout_strategy",
  "name": "Volume Breakout",
  "description": "Buy breakouts above resistance with high volume",
  "entry_conditions": {
    "all": [
      {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "resistance_level"}},
      {"left": {"indicator": "volume"}, "op": "gt", "right": {"indicator": "volume_sma", "multiplier": 2.0}},
      {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 55}}
    ]
  },
  "exit_conditions": {
    "any": [
      {"left": {"indicator": "price"}, "op": "lt", "right": {"indicator": "resistance_level"}},
      {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 80}}
    ]
  },
  "risk": {
    "stop_loss_pct": 3.0,
    "take_profit_pct": 9.0,
    "position_size_pct": 8.0
  }
}
```

### Example 3: Mean Reversion Strategy

**Goal:** Trade reversals from extreme conditions

```json
{
  "id": "mean_reversion_strategy",
  "name": "RSI Mean Reversion",
  "description": "Buy oversold, sell overbought in ranging markets",
  "entry_conditions": {
    "all": [
      {"left": {"indicator": "rsi"}, "op": "lt", "right": {"value": 25}},
      {"left": {"indicator": "adx"}, "op": "lt", "right": {"value": 20}},
      {"left": {"indicator": "price"}, "op": "lt", "right": {"indicator": "bb_lower"}}
    ]
  },
  "exit_conditions": {
    "any": [
      {"left": {"indicator": "rsi"}, "op": "gt", "right": {"value": 75}},
      {"left": {"indicator": "price"}, "op": "gt", "right": {"indicator": "bb_upper"}}
    ]
  },
  "risk": {
    "stop_loss_pct": 1.5,
    "take_profit_pct": 3.0,
    "position_size_pct": 5.0
  }
}
```

---

## Best Practices

### 1. **Test Before Live Trading**

Always backtest strategies with:
- Minimum 6 months historical data
- Walk-forward validation (Phase 5)
- Multiple market conditions (bull, bear, sideways)

### 2. **Use Multiple Exit Conditions**

Don't rely on single exit signal. Combine:
- Technical indicators (RSI, MACD)
- Price action (support/resistance)
- Time-based stops (`max_holding_bars`)

### 3. **Document Strategy Logic**

```json
{
  "description": "This strategy buys pullbacks in uptrends by waiting for RSI to drop below 40 while price stays above 50 EMA. Exits when RSI reaches 70 or price crosses below 20 EMA. Risk/reward is 1:2 with 2.5% stop loss and 5% profit target."
}
```

### 4. **Avoid Overfitting**

Signs of overfitting:
- ❌ Perfect backtest results (100% win rate)
- ❌ Very specific conditions (e.g., RSI exactly 33.7)
- ❌ Performance degrades immediately in live trading

How to avoid:
- ✅ Use round numbers for thresholds (30, 50, 70)
- ✅ Test on out-of-sample data
- ✅ Keep strategies simple (3-5 conditions max)

---

## Next Steps

- **Read:** [Advanced Features Guide](05_Advanced_Features_Guide.md)
- **Practice:** Create 3-5 strategies for different market conditions
- **Backtest:** Validate strategies with Entry Analyzer
- **Optimize:** Use walk-forward validation (Phase 5)

---

**Examples:** See `03_JSON/Trading_Bot/` for production strategy definitions.
