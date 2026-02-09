# JSON Format v2.1

Version: 2.1.0
Schemas: `schemas/strategy_config.schema.json`, `schemas/indicator_set.schema.json`, `schemas/regime_optimization_results.schema.json`

## Common Rules

- `kind` is required and must be one of:
  - `strategy_config`
  - `indicator_set`
  - `regime_optimization_results`
- `schema_version` must be SemVer (e.g. `2.1.0`).
- Unknown fields are rejected by schema validation.
- `_comment_*` fields are allowed as strings for human notes.

## strategy_config

Required fields:
- `kind`, `schema_version`
- `indicators[]` (id, type, params)
- `regimes[]` (id, name, conditions)
- `strategies[]`, `strategy_sets[]`, `routing[]`

Regime conditions:
- `conditions.all[]` and/or `conditions.any[]`
- Each condition is either operator-based or CEL-based:
  - Operator-based: `left`, `op`, `right`
  - CEL-based: `cel_expression`

Entry rules:
- `entry_expression` is optional.
- Missing or empty `entry_expression` disables entry evaluation in Strategy Settings (fail-closed).

## indicator_set

Required fields:
- `kind`, `schema_version`
- `indicators[]` (name, type, params[])
- `regimes[]` (id, name, thresholds[])
- `entry_enabled`, `entry_expression`

Entry rules:
- If `entry_enabled` is `true`, `entry_expression` must be a non-empty string.
- Default template uses `entry_enabled=false` and `entry_expression=null`.

## regime_optimization_results

Required fields:
- `kind`, `schema_version`
- `optimization_results[]`

Each optimization result includes:
- `timestamp`, `score`, `trial_number`, `applied`
- `indicators[]`, `regimes[]`

Optional fields:
- `metadata`, `entry_params`, `evaluation_params`, `entry_expression`

Entry rules:
- Missing or empty `entry_expression` disables entry evaluation (fail-closed).

## Fail-Closed Behavior

- Missing `entry_expression` ⇒ entry disabled, no score boost.
- Missing or NaN indicators ⇒ regime evaluates to false and adds data quality penalties.
- Invalid JSON ⇒ not loaded, no computation.

## Validation

Use the kind-aware validator or loader:

```python
from src.core.tradingbot.config.kind_loader import KindConfigLoader

loader = KindConfigLoader()
config = loader.load("path/to/config.json")
```
