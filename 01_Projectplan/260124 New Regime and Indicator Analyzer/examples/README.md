# Example JSON Files

This directory contains example JSON files demonstrating the complete 2-stage optimization workflow for the Regime and Indicator Analyzer.

## Overview

The optimization process consists of two stages:

1. **Stage 1: Regime Optimization** - Identifies optimal market regime parameters
2. **Stage 2: Indicator Optimization** - Finds best indicator settings for each regime

## File Structure

```
examples/
├── STUFE_1_Regime/
│   ├── regime_optimization_results_BTCUSDT_5m.json   # All 150 trials
│   └── optimized_regime_BTCUSDT_5m.json              # Selected config with bar_indices
│
└── STUFE_2_Indicators/
    ├── BULL/
    │   ├── indicator_optimization_results_BULL_BTCUSDT_5m.json   # 280 trials
    │   └── indicator_sets_BULL_BTCUSDT_5m.json                   # Selected indicators
    │
    ├── BEAR/
    │   ├── indicator_optimization_results_BEAR_BTCUSDT_5m.json
    │   └── indicator_sets_BEAR_BTCUSDT_5m.json
    │
    └── SIDEWAYS/
        ├── indicator_optimization_results_SIDEWAYS_BTCUSDT_5m.json
        └── indicator_sets_SIDEWAYS_BTCUSDT_5m.json
```

## Stage 1: Regime Optimization

### regime_optimization_results_BTCUSDT_5m.json

**Purpose:** Complete results from regime optimization process

**Content:**
- All 150 trials tested
- Parameter combinations for RSI, ADX, ATR
- Performance metrics per trial
- Ranking and scoring

**Size:** ~21.6 KB
**Validation:** ✓ Against `regime_optimization_results.schema.json`

### optimized_regime_BTCUSDT_5m.json

**Purpose:** Selected optimal regime configuration for production use

**Content:**
- Best performing regime parameters
- Bar indices for each regime period (BULL/BEAR/SIDEWAYS)
- Performance metrics
- Quality scores

**Size:** ~7.3 KB
**Validation:** ✓ Against `optimized_regime_config.schema.json`

## Stage 2: Indicator Optimization

For each regime (BULL, BEAR, SIDEWAYS), two files are generated:

### indicator_optimization_results_{REGIME}_BTCUSDT_5m.json

**Purpose:** Complete results from indicator optimization for specific regime

**Content:**
- 280 trials total (40 per indicator × 7 indicators)
- Tested indicators: RSI, MACD, STOCH, BB, ATR, EMA, CCI
- Results for 4 signal types:
  - `entry_long` - Long entry signals
  - `entry_short` - Short entry signals
  - `exit_long` - Long exit signals
  - `exit_short` - Short exit signals
- Performance metrics (win_rate, profit_factor, sharpe_ratio, etc.)
- Parameter ranges used
- Optimization config (method, early stopping, etc.)

**Size:** ~12.7 KB per file
**Validation:** ✓ Against `indicator_optimization_results.schema.json`

### indicator_sets_{REGIME}_BTCUSDT_5m.json

**Purpose:** Selected best indicators for production use in specific regime

**Content:**
- Top-ranked indicator for each signal type
- Complete parameter configuration
- CEL-compatible conditions
- Performance metrics
- Research notes

**Special Notes:**
- **BULL Regime:** Only `entry_long` and `exit_long` enabled (no short trading)
- **BEAR/SIDEWAYS:** All 4 signal types enabled

**Size:** 2.5 KB (BULL), 4.2 KB (BEAR/SIDEWAYS)
**Validation:** ✓ Against `optimized_indicator_sets.schema.json`

## Regime-Specific Characteristics

### BULL Regime (#26a69a)
- **Focus:** Long-only trading
- **Best Entry:** RSI (score: 78.5)
- **Best Exit:** ATR (score: 82.1)
- **Signals Enabled:** entry_long, exit_long

### BEAR Regime (#ef5350)
- **Focus:** Both long and short trading
- **Best Entry Long:** RSI (score: 60.3)
- **Best Entry Short:** STOCH (score: 75.8)
- **Best Exit Long:** ATR (score: 68.5)
- **Best Exit Short:** BB (score: 79.2)
- **Signals Enabled:** All 4 signal types

### SIDEWAYS Regime (#9e9e9e)
- **Focus:** Both directions with balanced approach
- **Best Entry Long:** RSI (score: 68.7)
- **Best Entry Short:** STOCH (score: 67.4)
- **Best Exit Long:** ATR (score: 73.2)
- **Best Exit Short:** BB (score: 72.1)
- **Signals Enabled:** All 4 signal types

## Validation Status

All example files are validated against their respective JSON Schemas v2.0:

| File | Schema | Status |
|------|--------|--------|
| regime_optimization_results_BTCUSDT_5m.json | regime_optimization_results.schema.json | ✓ VALID |
| optimized_regime_BTCUSDT_5m.json | optimized_regime_config.schema.json | ✓ VALID |
| indicator_optimization_results_BULL_BTCUSDT_5m.json | indicator_optimization_results.schema.json | ✓ VALID |
| indicator_sets_BULL_BTCUSDT_5m.json | optimized_indicator_sets.schema.json | ✓ VALID |
| indicator_optimization_results_BEAR_BTCUSDT_5m.json | indicator_optimization_results.schema.json | ✓ VALID |
| indicator_sets_BEAR_BTCUSDT_5m.json | optimized_indicator_sets.schema.json | ✓ VALID |
| indicator_optimization_results_SIDEWAYS_BTCUSDT_5m.json | indicator_optimization_results.schema.json | ✓ VALID |
| indicator_sets_SIDEWAYS_BTCUSDT_5m.json | optimized_indicator_sets.schema.json | ✓ VALID |

**Total:** 8 files, 50.1 KB total size

## Usage

### Loading Examples in Python

```python
from pathlib import Path
import json
from src.core.tradingbot.config.validator import SchemaValidator

# Validate and load optimization results
validator = SchemaValidator()

# Load regime optimization results
file_path = Path("examples/STUFE_1_Regime/regime_optimization_results_BTCUSDT_5m.json")
validator.validate_file(str(file_path), schema_name="regime_optimization_results")
with open(file_path) as f:
    regime_results = json.load(f)

# Load indicator sets for BULL regime
file_path = Path("examples/STUFE_2_Indicators/BULL/indicator_sets_BULL_BTCUSDT_5m.json")
validator.validate_file(str(file_path), schema_name="optimized_indicator_sets")
with open(file_path) as f:
    bull_indicators = json.load(f)
```

### Understanding the Data Flow

```
1. Run Regime Optimization
   └─> regime_optimization_results_BTCUSDT_5m.json
       └─> Select best trial
           └─> optimized_regime_BTCUSDT_5m.json

2. For each regime in optimized_regime_BTCUSDT_5m.json:
   └─> Run Indicator Optimization
       └─> indicator_optimization_results_{REGIME}_BTCUSDT_5m.json
           └─> Select best indicators
               └─> indicator_sets_{REGIME}_BTCUSDT_5m.json

3. Combine all indicator_sets_*.json
   └─> Complete trading strategy configuration
```

## Schema Documentation

All schemas are located in `../schemas/` and documented in `../schemas/README.md`.

Key schemas:
- `regime_optimization_results.schema.json` - Full optimization results
- `optimized_regime_config.schema.json` - Production regime config
- `indicator_optimization_results.schema.json` - Full indicator optimization
- `optimized_indicator_sets.schema.json` - Production indicator config

## Generation

These example files were generated using:

```bash
python scripts/generate_stage1_examples.py  # Stage 1 examples
python scripts/generate_stage2_examples.py  # Stage 2 examples
```

## Notes

1. All timestamps are in ISO 8601 format
2. All scores are 0-100 normalized
3. All metrics are backtested values
4. Regime colors are hex codes for UI visualization
5. CEL conditions are compatible with the ConditionEvaluator

## References

- Main documentation: `../README_JSON_FORMATE.md`
- Schema definitions: `../schemas/`
- Performance optimization guide: `../PERFORMANCE_OPTIMIERUNG.md`
