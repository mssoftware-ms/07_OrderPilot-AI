# Migration Guide: Hardcoded → JSON Configuration

Complete guide for migrating hardcoded trading strategies to JSON-based configuration.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Migration Workflow](#migration-workflow)
4. [CLI Tool Usage](#cli-tool-usage)
5. [Step-by-Step Migration](#step-by-step-migration)
6. [Validation & Testing](#validation--testing)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [Rollback Procedures](#rollback-procedures)

---

## Overview

### Why Migrate?

**Benefits of JSON Configuration:**
- ✅ **No code changes needed** - Adjust strategies without touching Python code
- ✅ **Live reloading** - Update strategies without restarting the bot
- ✅ **Version control friendly** - Track strategy changes in git
- ✅ **Easy A/B testing** - Compare different configurations side-by-side
- ✅ **Parameter optimization** - Quickly iterate on strategy parameters
- ✅ **Reduced development time** - Non-programmers can create strategies

**Migration Strategy:**
- Gradual migration (both modes coexist)
- Zero breaking changes to existing code
- Automated conversion tools
- Comprehensive validation

---

## Prerequisites

### 1. Install Dependencies

```bash
# Ensure latest dependencies are installed
pip install -r requirements.txt

# Install package in development mode (for CLI access)
pip install -e .
```

**New Dependencies:**
- `click>=8.1` - CLI framework
- `rich>=13.7` - Terminal output formatting
- `watchdog>=6.0` - File watching (already installed in Phase 4.5)

### 2. Verify CLI Installation

```bash
# Check CLI is available
tradingbot-config --help

# Expected output:
# TradingBot JSON Configuration CLI Tool
# Commands:
#   validate         Validate a JSON configuration file
#   convert          Convert a hardcoded strategy to JSON
#   list-strategies  List all available hardcoded strategies
#   ...
```

### 3. Verify Python Module Access

```bash
# Alternative: run as module
python -m src.core.tradingbot.config.cli --help
```

---

## Migration Workflow

```
┌─────────────────┐
│ 1. List         │  tradingbot-config list-strategies
│    Strategies   │  → Identify strategies to migrate
└────────┬────────┘
         │
┌────────▼────────┐
│ 2. Convert      │  tradingbot-config convert <name> -o <file>
│    Strategy     │  → Generate JSON config
└────────┬────────┘
         │
┌────────▼────────┐
│ 3. Validate     │  tradingbot-config validate <file>
│    Config       │  → Verify correctness
└────────┬────────┘
         │
┌────────▼────────┐
│ 4. Test Paper   │  BotController(config, json_config_path=<file>)
│    Trading      │  → Test in paper trading environment
└────────┬────────┘
         │
┌────────▼────────┐
│ 5. Compare      │  tradingbot-config compare <file> <strategy>
│    Results      │  → Verify equivalence (Phase 5.2)
└────────┬────────┘
         │
┌────────▼────────┐
│ 6. Deploy       │  Deploy to production
│    Production   │  → Enable live config reloading
└─────────────────┘
```

---

## CLI Tool Usage

### List Available Strategies

**Command:**
```bash
tradingbot-config list-strategies
```

**Output (Table Format):**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                       ┃ Type              ┃ Regimes                   ┃ Description                     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ trend_following_conserv... │ trend_following   │ trend_up, trend_down      │ Conservative trend following... │
│ mean_reversion_bb          │ mean_reversion    │ range_bound, volatile     │ Mean reversion using Bolling... │
│ ...                        │ ...               │ ...                       │ ...                             │
└────────────────────────────┴───────────────────┴───────────────────────────┴─────────────────────────────────┘

Total: 9 strategies
```

**JSON Format:**
```bash
tradingbot-config list-strategies --format json
```

### Convert Single Strategy

**Command:**
```bash
tradingbot-config convert <strategy_name> --output <output_file>
```

**Example:**
```bash
tradingbot-config convert trend_following_conservative \
    --output 03_JSON/Trading_Bot/configs/trend_conservative.json
```

**Options:**
- `--no-regime` - Skip auto-generating regime from strategy conditions
- `--no-set` - Skip generating strategy set and routing
- `--compact` - Generate compact JSON (no indentation)

**Output:**
```
Analyzing strategy: trend_following_conservative
  Entry conditions: 4
  Exit conditions: 3
  Required indicators: 5
  Strategy type: trend_following

Generating JSON configuration...
✓ Configuration saved to: 03_JSON/Trading_Bot/configs/trend_conservative.json

Generated config contains:
  Indicators: 5
  Regimes: 1
  Strategies: 1
  Strategy Sets: 1
  Routing Rules: 1

Next steps:
  1. Validate: tradingbot-config validate 03_JSON/Trading_Bot/configs/trend_conservative.json
  2. Test in paper trading
  3. Review and adjust parameters
```

### Convert Multiple Strategies

**Command:**
```bash
tradingbot-config convert-multiple <strategy_names...> --output <output_file>
```

**Examples:**

Convert specific strategies:
```bash
tradingbot-config convert-multiple \
    trend_following_conservative \
    trend_following_aggressive \
    --output 03_JSON/Trading_Bot/configs/trend_strategies.json
```

Convert all trend strategies (wildcard):
```bash
tradingbot-config convert-multiple trend_following_* \
    --output 03_JSON/Trading_Bot/configs/all_trends.json
```

Convert all strategies:
```bash
tradingbot-config convert-multiple \
    trend_following_* mean_reversion_* breakout_* momentum_* scalping_* sideways_* \
    --output 03_JSON/Trading_Bot/configs/all_strategies.json
```

### Validate Configuration

**Command:**
```bash
tradingbot-config validate <config_file>
```

**Example:**
```bash
tradingbot-config validate 03_JSON/Trading_Bot/configs/trend_conservative.json
```

**Output (Success):**
```
✓ Configuration valid!
  Schema version: 1.0.0
  Indicators: 5
  Regimes: 1
  Strategies: 1
  Strategy Sets: 1
  Routing Rules: 1
```

**Verbose Mode:**
```bash
tradingbot-config validate 03_JSON/Trading_Bot/configs/trend_conservative.json --verbose
```

**Output (Verbose):**
```
✓ Configuration valid!
  Schema version: 1.0.0
  Indicators: 5
  Regimes: 1
  Strategies: 1
  Strategy Sets: 1
  Routing Rules: 1

Indicators:
  • rsi14 (rsi)
  • adx14 (adx)
  • sma20 (sma)
  • sma50 (sma)
  • macd (macd)

Regimes:
  • trend_following_regime: Trend Following Market (priority=10)

Strategies:
  • trend_following_conservative: Conservative Trend Following
```

**Output (Failure):**
```
✗ Validation failed: Field required: 'strategies'
  Missing required field 'strategies' in config
```

### List Config Files

**Command:**
```bash
tradingbot-config list-configs <directory>
```

**Example:**
```bash
tradingbot-config list-configs 03_JSON/Trading_Bot/configs
```

**Recursive Search:**
```bash
tradingbot-config list-configs 03_JSON/Trading_Bot/configs --recursive
```

---

## Step-by-Step Migration

### Example: Migrate "trend_following_conservative"

#### Step 1: Identify Strategy

```bash
# List available strategies
tradingbot-config list-strategies

# Find the one you want to migrate
# → trend_following_conservative
```

#### Step 2: Convert to JSON

```bash
# Convert strategy
tradingbot-config convert trend_following_conservative \
    --output 03_JSON/Trading_Bot/configs/trend_conservative.json \
    --pretty
```

**Generated File:**
```json
{
  "schema_version": "1.0.0",
  "indicators": [
    {"id": "rsi14", "type": "rsi", "params": {"period": 14}},
    {"id": "adx14", "type": "adx", "params": {"period": 14}},
    {"id": "sma20", "type": "sma", "params": {"period": 20}},
    {"id": "sma50", "type": "sma", "params": {"period": 50}},
    {"id": "macd", "type": "macd", "params": {"fast": 12, "slow": 26, "signal": 9}}
  ],
  "regimes": [
    {
      "id": "trend_following_regime",
      "name": "Trend Following Market",
      "conditions": {
        "all": [
          {"left": {"indicator_id": "sma20", "field": "value"}, "op": "gt", "right": {"value": 1.0}},
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 25.0}},
          {"left": {"indicator_id": "macd", "field": "value"}, "op": "gt", "right": {"value": 1.0}},
          {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "between", "right": {"min": 30.0, "max": 70.0}}
        ]
      },
      "priority": 10,
      "scope": "entry"
    }
  ],
  "strategies": [
    {
      "id": "trend_following_conservative",
      "name": "trend_following_conservative",
      "entry": {
        "all": [
          {"left": {"indicator_id": "sma20", "field": "value"}, "op": "gt", "right": {"value": 1.0}},
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 25.0}},
          {"left": {"indicator_id": "macd", "field": "value"}, "op": "gt", "right": {"value": 1.0}},
          {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "between", "right": {"min": 30.0, "max": 70.0}}
        ]
      },
      "exit": {
        "all": [
          {"left": {"indicator_id": "sma20", "field": "value"}, "op": "lt", "right": {"value": 0.0}},
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "lt", "right": {"value": 20.0}}
        ]
      },
      "risk": {
        "position_size": 0.025,
        "stop_loss": 0.025,
        "take_profit": 0.06
      }
    }
  ],
  "strategy_sets": [
    {
      "id": "set_trend_following_conservative",
      "name": "trend_following_conservative Set",
      "strategies": [
        {"strategy_id": "trend_following_conservative"}
      ]
    }
  ],
  "routing": [
    {
      "strategy_set_id": "set_trend_following_conservative",
      "match": {"all_of": ["trend_following_regime"]}
    }
  ]
}
```

#### Step 3: Validate Config

```bash
tradingbot-config validate 03_JSON/Trading_Bot/configs/trend_conservative.json --verbose
```

**Expected:** ✓ Configuration valid!

#### Step 4: Review & Adjust

**Common Adjustments:**

1. **Fine-tune indicator parameters:**
   ```json
   {"id": "adx14", "type": "adx", "params": {"period": 21}}  // Changed from 14
   ```

2. **Adjust entry thresholds:**
   ```json
   {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 30.0}}  // Changed from 25
   ```

3. **Modify risk parameters:**
   ```json
   "risk": {
     "position_size": 0.03,  // Increased from 0.025
     "stop_loss": 0.02,      // Tightened from 0.025
     "take_profit": 0.08     // Increased from 0.06
   }
   ```

4. **Add parameter overrides:**
   ```json
   {
     "id": "set_trend_conservative_strong",
     "name": "Strong Trend Set",
     "strategies": [
       {
         "strategy_id": "trend_following_conservative",
         "strategy_overrides": {
           "risk": {
             "position_size": 0.04,
             "take_profit": 0.10
           }
         }
       }
     ],
     "indicator_overrides": [
       {"indicator_id": "adx14", "params": {"period": 21}}
     ]
   }
   ```

#### Step 5: Test in Paper Trading

**Python Code:**
```python
from src.core.tradingbot.bot_controller import BotController
from src.core.tradingbot.config import FullBotConfig, BotConfig, RiskConfig

# Create bot config
bot_config = FullBotConfig(
    bot=BotConfig(
        symbol="BTCUSDT",
        timeframe="1m",
        trading_env=TradingEnvironment.PAPER  # PAPER mode!
    ),
    risk=RiskConfig(risk_per_trade_pct=1.0)
)

# Initialize with JSON config
controller = BotController(
    config=bot_config,
    json_config_path="03_JSON/Trading_Bot/configs/trend_conservative.json"
)

# Enable auto-reload (optional)
controller.enable_json_config_auto_reload()

# Run paper trading...
# (Your existing paper trading loop)
```

**What to Verify:**
1. ✅ Config loads without errors
2. ✅ Indicators calculated correctly
3. ✅ Regimes detected as expected
4. ✅ Strategies activated in correct market conditions
5. ✅ Entry/exit signals match hardcoded behavior
6. ✅ Risk parameters applied correctly

#### Step 6: Compare Results

**Validate equivalence with the compare command:**

```bash
# Compare JSON config vs hardcoded strategy
tradingbot-config compare \
    03_JSON/Trading_Bot/configs/trend_conservative.json \
    trend_following_conservative
```

**Expected Output (Equivalent):**
```
Comparing JSON config vs hardcoded strategy...
  JSON config: 03_JSON/Trading_Bot/configs/trend_conservative.json
  Strategy ID: trend_following_conservative
  Hardcoded: trend_following_conservative

┌─────────────────────────────────────────────┐
│ Comparison: trend_following_conservative    │
│                                             │
│ ✓ Strategies are EQUIVALENT                │
│ Similarity: 100.0%                          │
└─────────────────────────────────────────────┘

Component Comparison:
  Entry Conditions: ✓ Match
  Exit Conditions: ✓ Match
  Risk Parameters: ✓ Match
  Indicators: ✓ Match
  Regimes: ✓ Match

Notes:
  • Strategies are functionally equivalent

Recommendations:
  ✓ JSON config is equivalent to hardcoded strategy
  ✓ Safe to deploy to production
```

**Output with Differences:**
```
┌─────────────────────────────────────────────┐
│ Comparison: trend_following_conservative    │
│                                             │
│ ✗ Strategies DIFFER                        │
│ Similarity: 85.0%                           │
└─────────────────────────────────────────────┘

Component Comparison:
  Entry Conditions: ✗ Differ
  Exit Conditions: ✓ Match
  Risk Parameters: ✓ Match

Condition Differences:
  Field: entry, Index: 1
  JSON: adx14 gt 30.0
  Hardcoded: adx14 gt 25.0
  Type: different_threshold, Severity: major

Warnings:
  ⚠ Major differences detected - strategy behavior may differ significantly

Recommendations:
  ⚠ Moderate differences detected
  ⚠ Carefully test in paper trading before production
```

**Verbose Mode:**
```bash
tradingbot-config compare \
    configs/trend.json \
    trend_following_conservative \
    --verbose
```

**Exit Codes:**
- `0` - Strategies are equivalent (safe to deploy)
- `1` - Strategies differ (review required)

#### Step 7: Deploy to Production

**Production Checklist:**
- [ ] Validated config with `tradingbot-config validate`
- [ ] Tested in paper trading for at least 24 hours
- [ ] Verified signals match hardcoded behavior
- [ ] Reviewed risk parameters
- [ ] Committed config to git with descriptive message
- [ ] Created backup of existing config
- [ ] Documented changes in config file comments

**Deploy:**
```python
# Production bot with JSON config
controller = BotController(
    config=production_config,
    json_config_path="03_JSON/Trading_Bot/configs/production.json"
)

# Enable live reloading (optional)
controller.enable_json_config_auto_reload()

# Start trading...
```

---

### Understanding Comparison Results

**Similarity Score:**
- **100%** - Perfect match (safe to deploy)
- **90-99%** - Very similar (minor differences, review recommended)
- **75-89%** - Somewhat similar (moderate differences, test carefully)
- **<75%** - Significant differences (do not deploy without thorough testing)

**Component Status:**
- **✓ Match** - Component is identical
- **✗ Differ** - Component has differences (check details)

**Difference Types:**
- **different_threshold** - Condition threshold differs (e.g., ADX > 25 vs > 30)
- **different_operator** - Condition operator differs (e.g., gt vs lt)
- **missing** - Condition exists in hardcoded but not JSON
- **extra** - Condition exists in JSON but not hardcoded
- **different_count** - Different number of conditions

**Severity Levels:**
- **major** - Affects strategy behavior significantly
- **minor** - Small difference, minimal impact

---

## Validation & Testing

### Two-Stage Validation

**Stage 1: JSON Schema Validation**
- Validates JSON structure
- Checks required fields
- Validates data types
- Checks enum values

**Stage 2: Pydantic Model Validation**
- Validates indicator references
- Checks strategy set references
- Validates routing rules
- Verifies business logic

### Testing Checklist

**Unit Testing:**
```bash
# Test config loading
pytest tests/core/tradingbot/test_config_loader.py -v

# Test regime detection
pytest tests/core/tradingbot/test_regime_detector.py -v

# Test strategy execution
pytest tests/core/tradingbot/test_strategy_executor.py -v
```

**Integration Testing:**
```bash
# End-to-end pipeline
pytest tests/core/tradingbot/test_json_integration_end_to_end.py -v

# Backtest integration
pytest tests/core/tradingbot/test_backtest_json_config.py -v
```

**Manual Testing:**

1. **Warmup Test:**
   ```python
   controller.warmup_from_bars(historical_bars[:100])
   assert controller._feature_engine is not None
   ```

2. **Regime Detection Test:**
   ```python
   features = await controller._calculate_features(bar)
   regime = await controller._update_regime(features)
   assert regime is not None
   ```

3. **Strategy Execution Test:**
   ```python
   result = controller._execute_json_strategy_sets_with_overrides(features)
   assert len(result["active_strategy_ids"]) > 0
   ```

---

## Troubleshooting

### Common Issues

#### 1. Config Validation Fails

**Error:** `Field required: 'strategies'`

**Solution:** Ensure all required top-level fields are present:
```json
{
  "schema_version": "1.0.0",
  "indicators": [...],     // Required
  "regimes": [...],        // Required
  "strategies": [...],     // Required
  "strategy_sets": [...],  // Required
  "routing": [...]         // Required
}
```

#### 2. Indicator Reference Not Found

**Error:** `Indicator 'rsi_14' not found in indicators list`

**Solution:** Ensure indicator IDs are normalized:
- Use: `rsi14` (not `rsi_14` or `rsi`)
- Use: `adx14` (not `adx_14` or `adx`)
- Use: `sma20` (not `sma_fast` or `sma_20`)

#### 3. Strategy Not Activating

**Symptom:** No strategies matched in certain market conditions

**Debug Steps:**
1. Check regime conditions:
   ```python
   active_regimes = catalog.regime_detector.detect_active_regimes(indicator_values)
   print(f"Active regimes: {[r.regime_id for r in active_regimes]}")
   ```

2. Check routing rules:
   ```python
   matched_sets = catalog.strategy_router.route_regimes(active_regimes)
   print(f"Matched sets: {[s.strategy_set_id for s in matched_sets]}")
   ```

3. Enable debug logging:
   ```python
   logging.getLogger("src.core.tradingbot.config").setLevel(logging.DEBUG)
   ```

#### 4. CLI Command Not Found

**Error:** `tradingbot-config: command not found`

**Solutions:**

1. **Reinstall package:**
   ```bash
   pip install -e .
   ```

2. **Use module syntax:**
   ```bash
   python -m src.core.tradingbot.config.cli --help
   ```

3. **Check PATH:**
   ```bash
   which tradingbot-config
   # Should show path to script
   ```

#### 5. Conversion Generates Wrong Conditions

**Symptom:** Converted conditions don't match hardcoded logic

**Solutions:**

1. **Manual review required:** Some complex conditions may not convert automatically
2. **Adjust after conversion:** Edit JSON file to fix condition logic
3. **Report issue:** Document pattern in GitHub issue for improvement

---

## Best Practices

### 1. Incremental Migration

**Don't migrate everything at once!**

```
Week 1: Migrate 1 strategy → test thoroughly
Week 2: Migrate 2-3 more strategies → compare results
Week 3: Migrate all remaining → full integration test
```

### 2. Git Workflow

**Commit conventions:**
```bash
# Good commit message
git add 03_JSON/Trading_Bot/configs/trend_conservative.json
git commit -m "Add JSON config for trend_following_conservative strategy

- Converted from hardcoded StrategyCatalog
- ADX threshold: 25 (unchanged)
- Position size: 2.5% (increased from 2.0%)
- Tested in paper trading for 24h"

# Tag releases
git tag -a v1.0.0-json-migration -m "Complete JSON migration"
```

### 3. Documentation

**Add comments to JSON configs:**
```json
{
  "strategies": [
    {
      "id": "trend_conservative",
      "name": "Conservative Trend Following",
      "_comment": "Updated 2024-01-15: Increased ADX threshold from 25 to 30 for stronger trends",
      "entry": {
        "all": [
          {
            "_comment": "Strong trend confirmation",
            "left": {"indicator_id": "adx14", "field": "value"},
            "op": "gt",
            "right": {"value": 30.0}
          }
        ]
      }
    }
  ]
}
```

*(Note: JSON doesn't officially support comments, but most parsers ignore `_comment` fields)*

### 4. Version Control

**Keep old configs:**
```
03_JSON/Trading_Bot/configs/
├── production.json           # Current production
├── production_v1.0.0.json    # Backup
├── production_v1.1.0.json    # Previous version
└── archive/
    └── production_2024-01.json
```

### 5. Testing Matrix

Test each config in multiple scenarios:

| Scenario | Test Duration | Expected Behavior |
|----------|---------------|-------------------|
| Strong uptrend | 4 hours | Long signals, ADX > 30 |
| Weak uptrend | 4 hours | No signals, ADX < 25 |
| Range-bound | 4 hours | No signals (regime filter) |
| High volatility | 2 hours | Reduced position size |
| After news event | 2 hours | Wait for stabilization |

---

## Rollback Procedures

### If JSON Config Fails

**Scenario 1: Config validation fails after edit**

```bash
# Revert to last good config
cp 03_JSON/Trading_Bot/configs/production_backup.json \
   03_JSON/Trading_Bot/configs/production.json

# Reload config (if auto-reload enabled)
# Bot will automatically use reverted config
```

**Scenario 2: Strategies behaving incorrectly**

```python
# Stop using JSON config (revert to hardcoded)
# Option 1: Set json_config_path=None
controller = BotController(config=bot_config, json_config_path=None)

# Option 2: Restart bot without json_config_path
controller = BotController(config=bot_config)

# Bot will fall back to hardcoded StrategyCatalog
```

**Scenario 3: Performance degradation**

1. **Disable auto-reload:**
   ```python
   controller.disable_json_config_auto_reload()
   ```

2. **Profile performance:**
   ```bash
   python scripts/profile_json_config_performance.py
   ```

3. **Check logs:**
   ```bash
   tail -f ~/.orderpilot/logs/bot.log | grep ERROR
   ```

---

## Next Steps

After successful migration:

1. **Phase 5.2:** Strategy comparison framework
2. **Phase 5.3:** Automated migration testing
3. **Phase 5.4:** Load testing & stress tests
4. **Phase 6:** AI-powered strategy suggestions
5. **Phase 7:** Production monitoring & alerting

---

## Support

**Documentation:**
- `docs/integration/JSON_Config_Integration_Guide.md` - Complete integration guide
- `docs/integration/Quick_Start_JSON_Config.md` - Quick start guide
- `03_JSON/README.md` - Main README for JSON config system

**Issues:**
- Check logs: `~/.orderpilot/logs/`
- Review examples: `03_JSON/Trading_Bot/examples/`
- GitHub Issues: Report bugs or request features

---

**Migration Status:** Phase 5.1 Complete (CLI Tools Available)

**Next:** Phase 5.2 - Strategy Comparison Framework

**Last Updated:** Phase 5 Start
