# Migration Tools

This directory contains tools for migrating old JSON formats to v2.1.

## Quick Start

### Dry-Run (Recommended First Step)
```bash
python migrations/migrate_v1_to_v2.py --dir 03_JSON/Trading_Bot --dry-run
```

### Migrate Directory (In-Place)
```bash
python migrations/migrate_v1_to_v2.py --dir 03_JSON/Trading_Bot
```

### Migrate Single File
```bash
python migrations/migrate_v1_to_v2.py --input old.json --output new.json
```

## What It Does

1. **Detects** JSON kind (strategy_config, indicator_set, regime_optimization_results)
2. **Adds** required fields:
   - `kind`
   - `schema_version: "2.1.0"`
3. **Standardizes** structure
4. **Validates** against schemas
5. **Reports** success/failure

## Safety

- ✅ Validates output before writing
- ✅ Skips already-migrated files
- ✅ Dry-run mode available
- ⚠️ **Backup your files first!**

## Output

```
📂 Found 15 JSON files in 03_JSON/Trading_Bot
================================================================================
✅ trend_following.json: Detected as 'strategy_config'
✅ trend_following.json: Validation passed
💾 trend_following.json → trend_following.json
...
================================================================================

📊 RESULTS:
  ✅ Migrated: 12
  ⏭️  Skipped:  3
  ❌ Failed:   0
```
