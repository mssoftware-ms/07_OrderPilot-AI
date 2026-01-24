# RegimeResultsManager - Stufe 1 Ergebnisse verwalten

## Übersicht

`RegimeResultsManager` verwaltet Regime-Optimierungs-Ergebnisse (Stufe 1) für den Entry Analyzer:

- **Sortierung & Ranking** nach Composite Score
- **Export regime_optimization_results.json** (alle Ergebnisse)
- **Export optimized_regime.json** (gewählte Konfiguration)
- **JSON Schema Validation** mit `SchemaValidator`

## Installation

```bash
# Benötigte Dependencies
pip install jsonschema>=4.26.0
```

## Verwendung

### 1. Basic Workflow

```python
from src.core.regime_results_manager import RegimeResultsManager

# Initialize manager
manager = RegimeResultsManager()

# Add results
manager.add_result(
    score=78.5,
    params={
        "adx_period": 14,
        "adx_threshold": 25.0,
        "sma_fast_period": 50,
        "sma_slow_period": 200,
        "rsi_period": 14,
        "rsi_sideways_low": 40,
        "rsi_sideways_high": 60,
        "bb_period": 20,
        "bb_std_dev": 2.0,
        "bb_width_percentile": 0.20,
    },
    metrics={
        "regime_count": 15,
        "avg_duration_bars": 26.7,
        "stability_score": 0.73,
        "f1_bull": 0.82,
        "f1_bear": 0.79,
        "f1_sideways": 0.71,
        "bull_bars": 180,
        "bear_bars": 101,
        "sideways_bars": 120,
    }
)

# Rank results
manager.rank_results()

# Select best result
manager.select_result(rank=1)
```

### 2. Export Optimization Results

```python
# Export all results to regime_optimization_results.json
manager.export_optimization_results(
    output_path="regime_optimization_results_BTCUSDT_5m.json",
    meta={
        "stage": "regime_optimization",
        "created_at": "2026-01-24T14:30:00Z",
        "total_combinations": 150,
        "method": "tpe_multivariate",
        "source": {
            "symbol": "BTCUSDT",
            "timeframe": "5m",
            "bars": 401,
        }
    },
    optimization_config={...},
    param_ranges={...},
    validate=True  # Validate against schema
)
```

### 3. Export Optimized Regime Config

```python
# Export selected config to optimized_regime.json
manager.export_optimized_regime(
    output_path="optimized_regime_BTCUSDT_5m.json",
    symbol="BTCUSDT",
    timeframe="5m",
    bars=401,
    data_range={
        "start": "2026-01-22T12:10:00Z",
        "end": "2026-01-23T21:30:00Z",
    },
    regime_periods=[...],  # Bar indices for each regime
    validate=True
)
```

## Datenstrukturen

### Parameters (params)

```python
{
    "adx_period": int,           # ADX Periode (z.B. 14)
    "adx_threshold": float,      # ADX Schwellwert (z.B. 25.0)
    "sma_fast_period": int,      # SMA Fast Periode (z.B. 50)
    "sma_slow_period": int,      # SMA Slow Periode (z.B. 200)
    "rsi_period": int,           # RSI Periode (z.B. 14)
    "rsi_sideways_low": int,     # RSI Low für Sideways (z.B. 40)
    "rsi_sideways_high": int,    # RSI High für Sideways (z.B. 60)
    "bb_period": int,            # Bollinger Bands Periode (z.B. 20)
    "bb_std_dev": float,         # BB Standardabweichung (z.B. 2.0)
    "bb_width_percentile": float # BB Width Percentile (z.B. 0.20)
}
```

### Metrics

```python
{
    "regime_count": int,         # Anzahl Regime-Wechsel
    "avg_duration_bars": float,  # Durchschnittliche Regime-Dauer
    "switch_count": int,         # Anzahl Switches
    "stability_score": float,    # Stabilitäts-Score (0-1)
    "coverage": float,           # Abdeckung (0-1)
    "f1_bull": float,            # F1-Score BULL (0-1)
    "f1_bear": float,            # F1-Score BEAR (0-1)
    "f1_sideways": float,        # F1-Score SIDEWAYS (0-1)
    "bull_bars": int,            # Anzahl BULL bars
    "bear_bars": int,            # Anzahl BEAR bars
    "sideways_bars": int         # Anzahl SIDEWAYS bars
}
```

### Regime Periods

```python
[
    {
        "regime": "BULL|BEAR|SIDEWAYS",
        "start_idx": int,              # Start Bar-Index
        "end_idx": int,                # End Bar-Index
        "start_timestamp": str,        # ISO timestamp
        "end_timestamp": str,          # ISO timestamp
        "bars": int                    # Anzahl Bars
    }
]
```

## JSON Schemas

### regime_optimization_results.schema.json

Schema für **alle** Optimierungs-Ergebnisse:

```json
{
  "version": "2.0",
  "meta": {...},
  "optimization_config": {...},
  "param_ranges": {...},
  "results": [
    {
      "rank": 1,
      "score": 78.5,
      "selected": true,
      "exported": true,
      "params": {...},
      "metrics": {...}
    }
  ]
}
```

**Schema-Pfad:**
- `01_Projectplan/260124 New Regime and Indicator Analyzer/schemas/regime_optimization_results.schema.json`

### optimized_regime_config.schema.json

Schema für **gewählte** Regime-Konfiguration:

```json
{
  "version": "2.0",
  "meta": {
    "optimization_score": 78.5,
    "selected_rank": 1,
    "optimized_params": {...},
    "classification_logic": {...}
  },
  "indicators": [...],
  "regimes": [...],
  "regime_periods": [...]
}
```

**Schema-Pfad:**
- `01_Projectplan/260124 New Regime and Indicator Analyzer/schemas/optimized_regime_config.schema.json`

## API Referenz

### RegimeResultsManager

#### `__init__(schemas_dir=None)`

Initialize manager.

**Args:**
- `schemas_dir` (Path, optional): Directory containing JSON schemas

#### `add_result(score, params, metrics, timestamp=None)`

Add optimization result.

**Args:**
- `score` (float): Composite score (0-100)
- `params` (dict): Regime parameters
- `metrics` (dict): Performance metrics
- `timestamp` (str, optional): ISO timestamp

**Returns:**
- `RegimeResult`: Created result

#### `rank_results()`

Sort results by score (descending) and assign ranks.

#### `select_result(rank=1)`

Select a result by rank.

**Args:**
- `rank` (int): Rank to select (1-based)

**Returns:**
- `RegimeResult`: Selected result

**Raises:**
- `ValueError`: If rank is invalid

#### `get_selected_result()`

Get currently selected result.

**Returns:**
- `RegimeResult | None`: Selected result or None

#### `export_optimization_results(output_path, meta, optimization_config, param_ranges, validate=True)`

Export all optimization results to JSON.

**Args:**
- `output_path` (str|Path): Path to output JSON file
- `meta` (dict): Metadata
- `optimization_config` (dict): Optimization configuration
- `param_ranges` (dict): Parameter ranges
- `validate` (bool): Whether to validate against schema

**Returns:**
- `Path`: Path to exported file

**Raises:**
- `ValidationError`: If validation fails

#### `export_optimized_regime(output_path, symbol, timeframe, bars, data_range, regime_periods, validate=True)`

Export selected regime configuration.

**Args:**
- `output_path` (str|Path): Path to output JSON file
- `symbol` (str): Trading symbol
- `timeframe` (str): Timeframe
- `bars` (int): Number of bars
- `data_range` (dict): Data range (start, end)
- `regime_periods` (list): Regime periods with bar indices
- `validate` (bool): Whether to validate against schema

**Returns:**
- `Path`: Path to exported file

**Raises:**
- `ValueError`: If no result is selected
- `ValidationError`: If validation fails

#### `load_optimization_results(input_path, validate=True)`

Load optimization results from JSON file.

**Args:**
- `input_path` (str|Path): Path to JSON file
- `validate` (bool): Whether to validate against schema

**Returns:**
- `dict`: Loaded data

**Raises:**
- `ValidationError`: If validation fails

#### `get_statistics()`

Get statistics about current results.

**Returns:**
- `dict`: Statistics (count, score_min, score_max, score_avg, score_median)

#### `clear()`

Clear all results.

## Beispiele

### Vollständiges Beispiel

Siehe: `docs/examples/regime_results_manager_example.py`

```bash
# Run example
PYTHONPATH=/path/to/OrderPilot-AI python docs/examples/regime_results_manager_example.py
```

### Integration mit RegimeOptimizer

```python
from src.core.regime_optimizer import RegimeOptimizer
from src.core.regime_results_manager import RegimeResultsManager

# 1. Run optimization
optimizer = RegimeOptimizer(...)
results = optimizer.optimize(...)  # Returns list of (score, params, metrics)

# 2. Store results in manager
manager = RegimeResultsManager()
for score, params, metrics in results:
    manager.add_result(score, params, metrics)

# 3. Rank and select
manager.rank_results()
manager.select_result(rank=1)

# 4. Export
manager.export_optimization_results(...)
manager.export_optimized_regime(...)
```

## Validation

### Schema Validation aktivieren

```python
# Mit Validation (empfohlen für Production)
manager.export_optimization_results(..., validate=True)
manager.export_optimized_regime(..., validate=True)
```

### Schema Validation deaktivieren

```python
# Ohne Validation (nur für Tests/Debugging)
manager.export_optimization_results(..., validate=False)
manager.export_optimized_regime(..., validate=False)
```

### Custom Schema Directory

```python
from pathlib import Path

# Custom schemas directory
schemas_dir = Path("custom/path/to/schemas")
manager = RegimeResultsManager(schemas_dir=schemas_dir)
```

## Error Handling

```python
from src.core.tradingbot.config.validator import ValidationError

try:
    manager.export_optimization_results(..., validate=True)
except ValidationError as e:
    print(f"Schema Error: {e.message}")
    print(f"JSON Path: {e.json_path}")
    print(f"Schema Rule: {e.schema_rule}")
except ValueError as e:
    print(f"Value Error: {str(e)}")
```

## Tests

Unit-Tests befinden sich in: `tests/core/test_regime_results_manager.py`

```bash
# Run tests
pytest tests/core/test_regime_results_manager.py -v

# Run with coverage
pytest tests/core/test_regime_results_manager.py --cov=src/core/regime_results_manager
```

## Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("src.core.regime_results_manager")
logger.setLevel(logging.DEBUG)
```

## Nächste Schritte

1. **Integration mit RegimeOptimizer**: Automatisches Speichern von Optimierungs-Ergebnissen
2. **Integration mit UI**: Anzeige von Rankings und Ergebnissen
3. **Stufe 2**: Verwendung von `optimized_regime.json` für Indikator-Optimierung

## Siehe auch

- [JSON_INTERFACE_RULES.md](../JSON_INTERFACE_RULES.md)
- [regime_optimization_results.schema.json](../01_Projectplan/260124%20New%20Regime%20and%20Indicator%20Analyzer/schemas/regime_optimization_results.schema.json)
- [optimized_regime_config.schema.json](../01_Projectplan/260124%20New%20Regime%20and%20Indicator%20Analyzer/schemas/optimized_regime_config.schema.json)
- [SchemaValidator](../src/core/tradingbot/config/validator.py)

## Changelog

### Version 1.0.0 (2026-01-24)

- Initial implementation
- Support for regime optimization results (Stufe 1)
- JSON Schema validation
- Export to `regime_optimization_results.json`
- Export to `optimized_regime.json`
- Full test coverage (17 tests, 100% passing)
