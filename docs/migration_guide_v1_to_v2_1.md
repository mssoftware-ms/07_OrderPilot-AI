# Migration Guide v1 -> v2.1

Date: 2026-02-08

## Summary

v2.1 introduces a required `kind` field and strict JSON Schema validation. Strategy Settings now use a unified pipeline and will reject invalid JSON.

Key changes:
- `kind` is required (`strategy_config`, `indicator_set`, `regime_optimization_results`).
- `schema_version` must be valid SemVer.
- Missing `entry_expression` disables entry evaluation (fail-closed).

## strategy_config

Required updates:
- Add `"kind": "strategy_config"` at root.
- Ensure `schema_version` is SemVer (recommend `2.1.0`).
- Validate against `schemas/strategy_config.schema.json`.

Example:

```json
{
  "kind": "strategy_config",
  "schema_version": "2.1.0",
  "indicators": [...],
  "regimes": [...],
  "strategies": [...],
  "strategy_sets": [...],
  "routing": [...]
}
```

Entry notes:
- If you want Strategy Settings to evaluate entry, add a valid `entry_expression`.
- If missing, entry is disabled and will not boost score.

## regime_optimization_results

Required updates:
- Add `"kind": "regime_optimization_results"` at root.
- Update `schema_version` to SemVer (recommend `2.1.0`).
- Keep `optimization_results[]` structure.

Example:

```json
{
  "kind": "regime_optimization_results",
  "schema_version": "2.1.0",
  "optimization_results": [ ... ],
  "entry_expression": "..."  
}
```

## indicator_set (new)

Indicator sets are now standalone templates.

Required fields:
- `kind`, `schema_version`, `indicators[]`, `regimes[]`, `entry_enabled`, `entry_expression`

Example:

```json
{
  "kind": "indicator_set",
  "schema_version": "2.1.0",
  "indicators": [...],
  "regimes": [...],
  "entry_enabled": false,
  "entry_expression": null
}
```

## Validation

Use the kind-aware loader:

```python
from src.core.tradingbot.config.kind_loader import KindConfigLoader

loader = KindConfigLoader()
config = loader.load("path/to/config.json")
```

## Important Behavior Changes

- Strategy Settings will mark JSON without `kind` as INVALID and block scoring.
- Missing or NaN indicators produce data-quality penalties.
- 100 score is only possible when regime match, entry true, and data quality is 10/10.
