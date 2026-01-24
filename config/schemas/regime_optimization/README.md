# Regime Optimization JSON Schemas

Version: 2.0
Date: 2026-01-24

## Schemas

### Stufe 1: Regime Optimization
1. **regime_optimization_results.schema.json** - All optimization results
2. **optimized_regime_config.schema.json** - Selected regime configuration

### Stufe 2: Indicator Optimization
3. **indicator_optimization_results.schema.json** - All indicator results per regime
4. **optimized_indicator_sets.schema.json** - Selected indicator sets per regime

## Usage

```python
from src.core.tradingbot.config.validator import SchemaValidator

validator = SchemaValidator()
validator.validate_file("output.json", schema_name="regime_optimization_results")
```

## Schema Location

Schemas are deployed to: `config/schemas/regime_optimization/`

Original source: `01_Projectplan/260124 New Regime and Indicator Analyzer/schemas/`

## Schema Details

### regime_optimization_results.schema.json
- **Purpose**: Stores all regime optimization results from Optuna trials
- **Contains**:
  - Trial results with parameters and metrics
  - Best regime parameters
  - Optimization metadata
- **Used by**: Regime Optimizer output

### optimized_regime_config.schema.json
- **Purpose**: Final selected regime configuration for production
- **Contains**:
  - Best regime thresholds
  - Detection parameters
  - Performance metrics
- **Used by**: Trading bot regime detection

### indicator_optimization_results.schema.json
- **Purpose**: Stores all indicator optimization results per regime
- **Contains**:
  - Per-regime trial results
  - Best indicator sets for each regime
  - Performance comparisons
- **Used by**: Indicator Optimizer output

### optimized_indicator_sets.schema.json
- **Purpose**: Final selected indicator sets per regime for production
- **Contains**:
  - Regime-specific indicator configurations
  - Optimized parameters
  - Expected performance
- **Used by**: Trading bot strategy selection
