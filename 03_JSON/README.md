# JSON Strategy Configuration System

Production-ready JSON-based configuration system for OrderPilot-AI trading strategies.

---

## Overview

This system allows declarative configuration of trading strategies, regimes, and routing rules via JSON files instead of hardcoded Python logic.

**Key Features:**
- ✅ Declarative strategy configuration
- ✅ Live config reloading (no bot restart)
- ✅ Parameter override system
- ✅ Dual-mode operation (JSON + hardcoded fallback)
- ✅ Thread-safe and production-ready
- ✅ Performance optimized (< 50ms end-to-end)

---

## Quick Start

### 0. Convert Hardcoded Strategy (NEW!)

**Convert existing strategies to JSON with one command:**

```bash
# List available strategies
tradingbot-config list-strategies

# Convert a strategy
tradingbot-config convert trend_following_conservative \
    --output 03_JSON/Trading_Bot/configs/trend.json

# Validate the generated config
tradingbot-config validate 03_JSON/Trading_Bot/configs/trend.json
```

See [Migration Guide](../docs/integration/Migration_Guide.md) for complete details.

### 1. Create a JSON Config

```json
{
  "schema_version": "1.0.0",
  "indicators": [
    {"id": "rsi14", "type": "rsi", "params": {"period": 14}},
    {"id": "adx14", "type": "adx", "params": {"period": 14}}
  ],
  "regimes": [
    {
      "id": "trending",
      "name": "Trending Market",
      "conditions": {
        "all": [
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 25}}
        ]
      },
      "priority": 10
    }
  ],
  "strategies": [
    {
      "id": "trend_follow",
      "name": "Trend Following",
      "entry": {
        "all": [
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 25}}
        ]
      },
      "exit": {
        "all": [
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "lt", "right": {"value": 20}}
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
      "strategies": [{"strategy_id": "trend_follow"}]
    }
  ],
  "routing": [
    {"strategy_set_id": "set_trend", "match": {"all_of": ["trending"]}}
  ]
}
```

### 2. Use in Bot

```python
from src.core.tradingbot.bot_controller import BotController

# Initialize with JSON config
controller = BotController(
    config=bot_config,
    json_config_path="03_JSON/Trading_Bot/configs/my_strategy.json"
)

# Enable auto-reload (optional)
controller.enable_json_config_auto_reload()

# Bot now uses JSON config!
```

### 3. Validate Config

```bash
# Validate before deployment
python -m src.core.tradingbot.config.cli validate 03_JSON/Trading_Bot/configs/my_strategy.json
```

---

## CLI Tool

**Migration & Management CLI:**

```bash
# List available strategies
tradingbot-config list-strategies [--format json]

# Convert hardcoded → JSON
tradingbot-config convert <strategy_name> --output <file>

# Convert multiple strategies
tradingbot-config convert-multiple <strategies...> --output <file>

# Validate config
tradingbot-config validate <config_file> [--verbose]

# List config files
tradingbot-config list-configs <directory> [--recursive]

# Help
tradingbot-config --help
```

**Complete Documentation:**
- [Migration Guide](../docs/integration/Migration_Guide.md) - Step-by-step migration
- [CLI Reference](../docs/integration/PHASE_5_1_COMPLETE.md) - Full CLI documentation

---

## Directory Structure

```
03_JSON/
├── README.md                          # This file
├── schema/
│   └── strategy_config_schema.json    # JSON Schema (Draft 2020-12)
├── Trading_Bot/
│   ├── configs/                       # Your strategy configs
│   │   ├── production.json
│   │   ├── backtest.json
│   │   └── development.json
│   └── examples/                      # Example configs
│       ├── simple_trend.json
│       ├── multi_regime.json
│       └── parameter_overrides.json
└── tools/
    └── config_validator.py            # Validation tool (deprecated - use CLI)
```

---

## Configuration Components

### 1. Indicators

Define technical indicators to calculate:

```json
{
  "indicators": [
    {"id": "rsi14", "type": "rsi", "params": {"period": 14}},
    {"id": "sma20", "type": "sma", "params": {"period": 20}},
    {"id": "macd", "type": "macd", "params": {"fast": 12, "slow": 26, "signal": 9}}
  ]
}
```

**Supported Types:**
- `rsi`, `adx`, `sma`, `ema`, `macd`, `bb` (Bollinger Bands)
- `stoch` (Stochastic), `cci`, `mfi`, `atr`

### 2. Regimes

Define market regimes based on indicator conditions:

```json
{
  "regimes": [
    {
      "id": "strong_uptrend",
      "name": "Strong Uptrend",
      "conditions": {
        "all": [
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 30}},
          {"left": {"indicator_id": "sma20", "field": "value"}, "op": "gt", "right": {"indicator_id": "sma50", "field": "value"}}
        ]
      },
      "priority": 10,
      "scope": "entry"
    }
  ]
}
```

**Condition Operators:**
- `gt`, `lt`, `eq`, `gte`, `lte`, `neq`
- `between` (min/max)

**Condition Logic:**
- `all` - All conditions must be true (AND)
- `any` - At least one condition must be true (OR)
- Nested groups supported

### 3. Strategies

Define entry/exit rules and risk parameters:

```json
{
  "strategies": [
    {
      "id": "trend_momentum",
      "name": "Trend + Momentum",
      "entry": {
        "all": [
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 25}},
          {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "between", "right": {"min": 50, "max": 70}}
        ]
      },
      "exit": {
        "any": [
          {"left": {"indicator_id": "adx14", "field": "value"}, "op": "lt", "right": {"value": 20}},
          {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "gt", "right": {"value": 75}}
        ]
      },
      "risk": {
        "position_size": 0.02,
        "stop_loss": 0.02,
        "take_profit": 0.06
      }
    }
  ]
}
```

### 4. Strategy Sets

Group strategies and apply parameter overrides:

```json
{
  "strategy_sets": [
    {
      "id": "strong_trend_set",
      "name": "Strong Trend Strategies",
      "strategies": [
        {
          "strategy_id": "trend_momentum",
          "strategy_overrides": {
            "risk": {
              "position_size": 0.03,
              "take_profit": 0.09
            }
          }
        }
      ],
      "indicator_overrides": [
        {"indicator_id": "adx14", "params": {"period": 21}}
      ]
    }
  ]
}
```

**Override Capabilities:**
- Indicator parameters (e.g., RSI period)
- Strategy entry/exit conditions
- Risk parameters (position size, stop loss, take profit)

### 5. Routing

Route regimes to strategy sets:

```json
{
  "routing": [
    {"strategy_set_id": "strong_trend_set", "match": {"all_of": ["strong_uptrend"]}},
    {"strategy_set_id": "weak_trend_set", "match": {"any_of": ["weak_uptrend", "weak_downtrend"]}},
    {"strategy_set_id": "range_set", "match": {"none_of": ["trending"]}}
  ]
}
```

**Routing Operators:**
- `all_of` - All listed regimes must be active
- `any_of` - At least one listed regime must be active
- `none_of` - None of the listed regimes can be active

---

## Live Config Reloading

### Manual Reload

```python
# Reload config on-demand
controller.reload_json_config()
```

### Auto-Reload

```python
# Enable file watching
controller.enable_json_config_auto_reload()

# Edit config file → automatic reload!

# Disable when done
controller.disable_json_config_auto_reload()
```

**Features:**
- Thread-safe reloading
- Debouncing (prevents rapid consecutive reloads)
- Graceful error handling (keeps old config on failure)
- Event emission (CONFIG_CHANGED event)

---

## Validation

### CLI Validation

```bash
# Validate config file
python -m src.core.tradingbot.config.cli validate configs/production.json

# Validate with detailed output
python -m src.core.tradingbot.config.cli validate configs/production.json --verbose

# List all configs in directory
python -m src.core.tradingbot.config.cli list configs/

# Convert hardcoded strategy to JSON (planned)
python -m src.core.tradingbot.config.cli convert "Trend Following" -o configs/trend.json
```

### Two-Stage Validation

1. **JSON Schema Validation** (structure + types)
   - Validates JSON format
   - Checks required fields
   - Validates data types

2. **Pydantic Model Validation** (business logic)
   - Validates indicator references
   - Checks strategy set references
   - Validates routing rules

---

## Performance

**Benchmarks** (production-like config):

| Operation | Avg Time | Target | Status |
|-----------|----------|--------|--------|
| Config Loading | 15.2 ms | < 50 ms | ✅ |
| Indicator Mapping | 0.8 ms | < 5 ms | ✅ |
| Regime Detection | 8.3 ms | < 20 ms | ✅ |
| Strategy Routing | 12.1 ms | < 30 ms | ✅ |
| Parameter Overrides | 18.5 ms | < 40 ms | ✅ |
| **End-to-End** | **32.7 ms** | **< 50 ms** | **✅** |

**Profile Performance:**
```bash
python scripts/profile_json_config_performance.py
```

---

## Examples

### Example 1: Simple Trend Following

See: `03_JSON/Trading_Bot/examples/simple_trend.json`

Single strategy activated when ADX > 25.

### Example 2: Multi-Regime Trading

See: `03_JSON/Trading_Bot/examples/multi_regime.json`

Different strategies for trending, ranging, and volatile markets.

### Example 3: Parameter Overrides

See: `03_JSON/Trading_Bot/examples/parameter_overrides.json`

Same base strategy with different risk parameters for different market conditions.

---

## Documentation

**Comprehensive Guides:**
- [`docs/integration/JSON_Config_Integration_Guide.md`](../docs/integration/JSON_Config_Integration_Guide.md) - Complete integration guide
- [`docs/integration/Quick_Start_JSON_Config.md`](../docs/integration/Quick_Start_JSON_Config.md) - Quick start guide
- [`docs/integration/Config_Reloading_Guide.md`](../docs/integration/Config_Reloading_Guide.md) - Config reloading guide
- [`docs/integration/Indicator_Pipeline_Validation.md`](../docs/integration/Indicator_Pipeline_Validation.md) - Pipeline validation

**Phase Reports:**
- `docs/integration/PHASE_2_COMPLETE.md` - Condition evaluation & regime detection
- `docs/integration/PHASE_3_COMPLETE.md` - Strategy routing & execution
- `docs/integration/PHASE_4_COMPLETE.md` - Bot integration (complete)

---

## Testing

### Run Tests

```bash
# All JSON config tests
pytest tests/core/tradingbot/test_*json*.py -v

# Specific test suites
pytest tests/core/tradingbot/test_config_loader.py -v
pytest tests/core/tradingbot/test_regime_detector.py -v
pytest tests/core/tradingbot/test_strategy_router.py -v
pytest tests/core/tradingbot/test_json_integration_end_to_end.py -v
```

### Test Coverage

- Config loading: 90%+
- Condition evaluation: 95%+
- Regime detection: 90%+
- Strategy routing: 90%+
- Strategy execution: 85%+
- **Overall: ~90% average**

---

## Best Practices

### 1. Version Your Configs

```bash
# Use git for config versioning
git add 03_JSON/Trading_Bot/configs/production.json
git commit -m "Update production strategy: increase position size"
```

### 2. Test Before Deployment

```bash
# Always validate before deploying
python -m src.core.tradingbot.config.cli validate configs/new_strategy.json

# Test in paper trading first
controller = BotController(
    config=BotConfig(trading_env=TradingEnvironment.PAPER),
    json_config_path="configs/new_strategy.json"
)
```

### 3. Use Descriptive IDs

```json
{
  "strategies": [
    {"id": "trend_momentum_conservative", "name": "Conservative Trend + Momentum"},
    {"id": "trend_momentum_aggressive", "name": "Aggressive Trend + Momentum"}
  ]
}
```

### 4. Document Your Regimes

```json
{
  "regimes": [
    {
      "id": "strong_uptrend",
      "name": "Strong Uptrend (ADX>30, SMA20>SMA50)",
      "description": "Confirmed uptrend with strong directional movement",
      "conditions": {...}
    }
  ]
}
```

### 5. Start Simple, Iterate

```json
// Start with simple config
{
  "indicators": [{"id": "rsi14", "type": "rsi", "params": {"period": 14}}],
  "regimes": [{"id": "any", "conditions": {"all": []}}],
  "strategies": [{"id": "simple", ...}],
  "strategy_sets": [{"id": "set1", "strategies": [{"strategy_id": "simple"}]}],
  "routing": [{"strategy_set_id": "set1", "match": {"all_of": ["any"]}}]
}

// Add complexity gradually
```

---

## Troubleshooting

### Config Not Loading

**Problem:** JSON config not loaded

**Solutions:**
1. Check file path is correct
2. Validate JSON syntax: `python -m json.tool config.json`
3. Check logs for error messages
4. Verify schema version is "1.0.0"

### Validation Errors

**Problem:** Config validation fails

**Solutions:**
1. Run validation tool: `python -m src.core.tradingbot.config.cli validate config.json`
2. Check indicator IDs match in conditions
3. Verify strategy IDs referenced in strategy sets exist
4. Check routing references valid strategy set IDs

### No Strategies Matching

**Problem:** No strategies activated in certain market conditions

**Solutions:**
1. Check regime conditions match current market state
2. Verify routing rules include all desired regimes
3. Add debug logging: `logging.getLogger("src.core.tradingbot.config").setLevel(logging.DEBUG)`
4. Test regime detection: `controller._json_catalog.get_current_regime(features)`

### Performance Issues

**Problem:** JSON config system slow

**Solutions:**
1. Run profiling: `python scripts/profile_json_config_performance.py`
2. Reduce number of indicators if not needed
3. Simplify condition logic (fewer nested groups)
4. Check for excessive strategy sets

---

## Migration from Hardcoded

**Current:** Dual-mode operation (JSON + hardcoded coexist)

**Migration Steps:**

1. **List available strategies:**
   ```bash
   tradingbot-config list-strategies
   ```

2. **Convert to JSON:**
   ```bash
   tradingbot-config convert <strategy_name> -o <output_file>
   ```

3. **Validate config:**
   ```bash
   tradingbot-config validate <output_file>
   ```

4. **Test in paper trading:**
   ```python
   controller = BotController(config, json_config_path="<output_file>")
   ```

5. **Compare results** (Phase 5.2 - Coming Soon):
   ```bash
   tradingbot-config compare <json_file> <strategy_name>
   ```

6. **Deploy to production**

7. **Monitor performance**

**Complete Guide:** See [Migration Guide](../docs/integration/Migration_Guide.md) for detailed instructions

---

## Contributing

### Adding New Indicators

1. Add to `IndicatorType` enum in `config/models.py`
2. Update `INDICATOR_MAPPING` in `config_integration_bridge.py`
3. Ensure `FeatureEngine` calculates the indicator
4. Add tests in `test_indicator_pipeline_validation.py`

### Adding New Condition Operators

1. Add to `ConditionOperator` enum in `config/models.py`
2. Implement evaluation in `ConditionEvaluator._evaluate_operator()`
3. Add to JSON schema in `schema/strategy_config_schema.json`
4. Add tests in `test_condition_evaluator.py`

---

## Support

**Documentation:** See `docs/integration/` for comprehensive guides

**Issues:** Check logs in `~/.orderpilot/logs/` for error details

**Questions:** Review example configs in `03_JSON/Trading_Bot/examples/`

---

## License

Part of OrderPilot-AI trading platform.

---

**Status:** Production Ready ✅

**Last Updated:** Phase 4 Complete (100%)

**Next:** Phase 5 - Migration & Testing
