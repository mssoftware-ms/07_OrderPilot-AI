# 🔗 CEL Variables Integration Guide

**Version:** 1.0
**Date:** 2026-01-28
**Status:** ✅ Phase 2 Complete

---

## Overview

This guide explains how to use the new variable system with the CEL Engine.
Variables from multiple sources (chart data, bot config, project variables)
can now be used seamlessly in CEL expressions.

---

## Quick Start

### Basic Usage

```python
from src.core.tradingbot.cel_engine import CELEngine

cel = CELEngine()

# Simple evaluation with auto-context building
result = cel.evaluate_with_sources(
    expression="chart.price > 90000 and bot.paper_mode",
    chart_window=chart_window,
    bot_config=bot_config
)
```

### Full Example

```python
from src.core.tradingbot.cel_engine import CELEngine
from src.core.variables import CELContextBuilder, VariableStorage

# Initialize
cel = CELEngine()
builder = CELContextBuilder()

# Build context from all sources
context = builder.build(
    chart_window=chart_window,
    bot_config=bot_config,
    project_vars_path="project/.cel_variables.json",
    indicators={"rsi": 65.0, "sma_50": 94500.0},
    regime={"current": "bullish", "strength": 0.8}
)

# Evaluate expression
result = cel.evaluate(
    "chart.price > project.entry_min_price " +
    "and bot.leverage == 10 " +
    "and indicators.rsi < 70 " +
    "and regime.current == 'bullish'",
    context
)

print(f"Signal triggered: {result}")
```

---

## Available Variables

### Chart Variables (chart.*)

19 variables from current candle and chart state:

```python
chart.price           # Current close price (float)
chart.open            # Current open (float)
chart.high            # Current high (float)
chart.low             # Current low (float)
chart.volume          # Current volume (float)

chart.range           # High - Low (float)
chart.body            # abs(close - open) (float)
chart.is_bullish      # Close >= Open (bool)
chart.is_bearish      # Close < Open (bool)

chart.upper_wick      # Upper wick size (float)
chart.lower_wick      # Lower wick size (float)

chart.prev_close      # Previous candle close (float)
chart.prev_high       # Previous candle high (float)
chart.prev_low        # Previous candle low (float)

chart.change          # Price change from prev (float)
chart.change_pct      # Price change % (float)

chart.symbol          # Trading symbol (string)
chart.timeframe       # Current timeframe (string)
chart.candle_count    # Number of candles (int)
```

---

### Bot Configuration Variables (bot.*)

23 variables from BotConfig:

#### Trading
```python
bot.symbol                     # "BTCUSDT" (string)
bot.leverage                   # 10 (int)
bot.paper_mode                 # true (bool, always)
```

#### Risk Management
```python
bot.risk_per_trade_pct         # 1.0 (float)
bot.max_daily_loss_pct         # 3.0 (float)
bot.max_position_size_btc      # 0.1 (float)
```

#### Stop Loss / Take Profit
```python
bot.sl_atr_multiplier          # 1.5 (float)
bot.tp_atr_multiplier          # 2.0 (float)
```

#### Trailing Stop
```python
bot.trailing_stop_enabled      # true (bool)
bot.trailing_stop_atr_mult     # 1.0 (float)
bot.trailing_stop_activation_pct  # 0.5 (float)
```

#### Signal Generation
```python
bot.min_confluence_score       # 3 (int)
bot.require_regime_alignment   # true (bool)
```

#### Timing Intervals
```python
bot.analysis_interval_sec      # 60 (int)
bot.position_check_interval_ms # 1000 (int)
bot.macro_update_interval_min  # 60 (int)
bot.trend_update_interval_min  # 15 (int)
```

#### Session Management
```python
bot.session.enabled            # false (bool)
bot.session.start_utc          # "08:00" (string)
bot.session.end_utc            # "22:00" (string)
bot.session.close_at_end       # true (bool)
```

#### AI Validation
```python
bot.ai.enabled                 # false (bool)
bot.ai.confidence_threshold    # 70 (int)
bot.ai.min_confluence_for_ai   # 4 (int)
bot.ai.fallback_to_technical   # true (bool)
```

---

### Project Variables (custom names)

User-defined variables from `.cel_variables.json`:

```json
{
  "version": "1.0",
  "project_name": "BTC Scalping Strategy",
  "variables": {
    "entry_min_price": {
      "type": "float",
      "value": 90000.0,
      "description": "Minimum BTC price for entry",
      "category": "Entry Rules",
      "unit": "USD"
    },
    "max_risk_pct": {
      "type": "float",
      "value": 2.0,
      "description": "Maximum risk per trade",
      "category": "Risk Management",
      "unit": "%"
    }
  }
}
```

**Usage in CEL:**
```python
# Direct access (no prefix)
result = cel.evaluate("entry_min_price < chart.price")

# Or use project. prefix for clarity
result = cel.evaluate("project.entry_min_price < chart.price")  # Not implemented yet
```

---

### Indicators (indicators.*)

Custom indicator values (pass as dict):

```python
indicators = {
    "rsi": 65.0,
    "sma_50": 94500.0,
    "atr": 450.0
}

result = cel.evaluate_with_sources(
    "indicators.rsi > 70 or indicators.rsi < 30",
    indicators=indicators
)
```

---

### Regime (regime.*)

Regime detection values (pass as dict):

```python
regime = {
    "current": "bullish",  # bullish, bearish, ranging
    "strength": 0.8,       # 0.0 - 1.0
    "trend": "up"          # up, down, sideways
}

result = cel.evaluate_with_sources(
    "regime.current == 'bullish' and regime.strength > 0.7",
    regime=regime
)
```

---

## Usage Patterns

### Pattern 1: Simple Expression with Auto-Context

```python
# CEL Engine handles context building automatically
result = cel.evaluate_with_sources(
    expression="chart.price > 90000",
    chart_window=chart_window
)
```

### Pattern 2: Complex Expression with All Sources

```python
result = cel.evaluate_with_sources(
    expression="""
        chart.price > entry_min_price
        and chart.is_bullish
        and bot.leverage <= 10
        and indicators.rsi < 70
        and regime.current == 'bullish'
    """,
    chart_window=chart_window,
    bot_config=bot_config,
    project_vars_path="project/.cel_variables.json",
    indicators={"rsi": 65.0},
    regime={"current": "bullish"}
)
```

### Pattern 3: Manual Context Building (Advanced)

```python
from src.core.variables import CELContextBuilder

# Build context once
builder = CELContextBuilder()
context = builder.build(
    chart_window=chart_window,
    bot_config=bot_config,
    project_vars_path="project/.cel_variables.json"
)

# Reuse for multiple evaluations (faster)
result1 = cel.evaluate("chart.price > 90000", context)
result2 = cel.evaluate("bot.leverage == 10", context)
result3 = cel.evaluate("chart.is_bullish and bot.paper_mode", context)
```

### Pattern 4: Dynamic Project Variables

```python
from src.core.variables import VariableStorage, ProjectVariable, VariableType

# Load existing variables
storage = VariableStorage()
variables = storage.load("project/.cel_variables.json")

# Add/update variable dynamically
variables.add_variable(
    "dynamic_threshold",
    ProjectVariable(
        type=VariableType.FLOAT,
        value=95000.0,
        description="Dynamic entry threshold",
        category="Entry Rules",
        tags=["dynamic", "threshold"]
    )
)

# Save
storage.save("project/.cel_variables.json", variables)

# Use in expression
result = cel.evaluate_with_sources(
    "chart.price > dynamic_threshold",
    chart_window=chart_window,
    project_vars_path="project/.cel_variables.json"
)
```

---

## Performance Considerations

### Caching

Both CEL Engine and Variable Storage use LRU caching:

```python
# CEL Engine: 128 compiled expressions (default)
cel = CELEngine(enable_cache=True, cache_size=128)

# Variable Storage: 64 variable files (default)
storage = VariableStorage(cache_size=64)
```

### Reuse Context for Multiple Evaluations

```python
# ❌ SLOW - Rebuilds context each time
for expression in expressions:
    result = cel.evaluate_with_sources(
        expression,
        chart_window=chart_window,
        bot_config=bot_config
    )

# ✅ FAST - Build context once
builder = CELContextBuilder()
context = builder.build(chart_window, bot_config)

for expression in expressions:
    result = cel.evaluate(expression, context)
```

### Cache Statistics

```python
# CEL Engine cache info
info = cel.get_cache_info()
print(info)  # {'hits': 42, 'misses': 8, 'size': 50, 'maxsize': 128}

# Variable Storage cache info
info = storage.get_cache_info()
print(info)  # {'max_size': 64, 'current_size': 3, 'utilization_pct': 4.6}

# Context Builder stats
stats = builder.get_statistics()
print(stats)  # {'build_count': 15, 'cache_hits': 8, 'cache_misses': 7}
```

---

## Error Handling

### Graceful Degradation

```python
# Missing project variables? No problem
result = cel.evaluate_with_sources(
    "chart.price > 90000",  # Works without project vars
    chart_window=chart_window,
    project_vars_path="nonexistent.json"  # Warning logged, continues
)

# With default fallback
result = cel.evaluate_with_sources(
    "invalid_variable > 100",
    default=False,  # Returns False on error
    chart_window=chart_window
)
```

### Validation Before Evaluation

```python
from src.core.variables import VariableStorage

storage = VariableStorage()

# Validate without loading
valid, error = storage.validate_file("project/.cel_variables.json")
if not valid:
    print(f"Invalid variable file: {error}")
else:
    # Safe to load and use
    result = cel.evaluate_with_sources(...)
```

---

## Integration Examples

### Example 1: Entry Signal Detection

```python
def check_entry_signal(chart_window, bot_config):
    """Check if entry conditions are met."""

    cel = CELEngine()

    entry_expression = """
        chart.price > project.entry_min_price
        and chart.is_bullish
        and chart.volume > project.min_volume
        and bot.paper_mode == true
        and indicators.rsi > 30 and indicators.rsi < 70
    """

    result = cel.evaluate_with_sources(
        entry_expression,
        chart_window=chart_window,
        bot_config=bot_config,
        project_vars_path="strategies/scalping/.cel_variables.json",
        indicators={
            "rsi": 55.0,
            "sma_50": 94500.0
        }
    )

    return result
```

### Example 2: Risk Check

```python
def check_risk_limits(chart_window, bot_config, current_daily_loss):
    """Check if risk limits are exceeded."""

    cel = CELEngine()

    risk_expression = """
        chart.price * bot.max_position_size_btc * bot.leverage < project.max_position_usd
        and current_daily_loss < bot.max_daily_loss_pct
    """

    # Build context manually for custom variables
    builder = CELContextBuilder()
    context = builder.build(chart_window, bot_config, "project/.cel_variables.json")

    # Add custom runtime variable
    context["current_daily_loss"] = current_daily_loss

    result = cel.evaluate(risk_expression, context)

    return result
```

### Example 3: Multi-Timeframe Check

```python
def check_multi_timeframe_alignment(charts, bot_config):
    """Check if multiple timeframes are aligned."""

    cel = CELEngine()
    builder = CELContextBuilder()

    # Build contexts for each timeframe
    contexts = {}
    for tf in ["1m", "5m", "15m"]:
        ctx = builder.build(
            chart_window=charts[tf],
            bot_config=bot_config
        )
        # Prefix with timeframe
        contexts[tf] = {f"{tf}.{k}": v for k, v in ctx.items()}

    # Merge all contexts
    full_context = {}
    for ctx in contexts.values():
        full_context.update(ctx)

    # Check alignment
    alignment_expression = """
        1m.chart.is_bullish
        and 5m.chart.is_bullish
        and 15m.chart.is_bullish
    """

    result = cel.evaluate(alignment_expression, full_context)

    return result
```

---

## Testing

### Unit Test Template

```python
import pytest
from src.core.tradingbot.cel_engine import CELEngine
from src.core.variables import CELContextBuilder

def test_cel_with_variables():
    """Test CEL evaluation with variable sources."""

    cel = CELEngine()

    # Mock chart window with test data
    # ... (create mock objects)

    result = cel.evaluate_with_sources(
        "chart.price > 90000 and bot.paper_mode",
        chart_window=mock_chart,
        bot_config=mock_bot
    )

    assert result == True
```

---

## Migration Guide

### Upgrading from Manual Context Building

**Before (old way):**
```python
context = {
    "price": chart_widget.data.iloc[-1]["close"],
    "leverage": bot_config.leverage,
    "user_threshold": 90000.0
}
result = cel.evaluate("price > user_threshold", context)
```

**After (new way):**
```python
# Save user_threshold to .cel_variables.json first
result = cel.evaluate_with_sources(
    "chart.price > entry_threshold",
    chart_window=chart_window,
    bot_config=bot_config,
    project_vars_path=".cel_variables.json"
)
```

---

## Best Practices

1. **Use descriptive variable names** in project variables
2. **Group related variables** by category
3. **Add units** to numeric variables for clarity
4. **Cache contexts** for repeated evaluations
5. **Validate expressions** before deployment
6. **Use type-safe variables** (int, float, bool, string)
7. **Document expressions** with comments in JSON
8. **Version control** .cel_variables.json files

---

## Troubleshooting

### "Variable not found"
Check that:
- Variable name is correct (case-sensitive)
- Source is provided (chart_window, bot_config, etc.)
- .cel_variables.json is valid and loadable

### "Invalid JSON"
Validate .cel_variables.json:
```python
storage = VariableStorage()
valid, error = storage.validate_file("project/.cel_variables.json")
print(error if not valid else "Valid")
```

### "Type mismatch"
Ensure variable types match CEL expectations:
- Numbers: Use float or int type
- Booleans: Use bool type
- Strings: Use string type

---

## See Also

- **CEL Variables Guide:** `help/CEL_Variables_Guide.md`
- **Implementation Progress:** `docs/260128_Variable_System_Implementation_Progress.md`
- **Variable Models API:** `src/core/variables/variable_models.py`
- **CEL Engine API:** `src/core/tradingbot/cel_engine.py`

---

**Last Updated:** 2026-01-28
**Status:** ✅ Ready for Production
