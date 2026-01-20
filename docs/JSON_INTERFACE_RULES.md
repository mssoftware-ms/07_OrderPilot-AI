# JSON Interface Rules - OrderPilot-AI

## Übersicht

JSON-Dateien sind die **universelle Schnittstelle** zwischen allen Modulen in OrderPilot-AI:

```
Entry Designer ↔ JSON ↔ CEL Engine ↔ JSON ↔ Trading Bot ↔ JSON ↔ KI (zukünftig)
```

Alle Module müssen dieselben JSON-Formate verstehen und konsistent validieren.

---

## 1. Leitplankensystem (Guardrail System)

### Kernprinzipien

1. **Schema-First**: Jedes JSON-Format hat ein JSON Schema Draft 2020-12
2. **Pre-Validation**: Validierung BEVOR Dateien geladen werden
3. **Type-Safety**: Pydantic-Modelle für alle JSON-Strukturen
4. **Versionierung**: Alle Schemas haben `schema_version` Feld
5. **Migration**: Automatische Migration zwischen Schema-Versionen

### Validation-Pipeline

```
JSON File → JSON Schema Validation → Pydantic Model → Business Logic Validation → OK
            ↓                         ↓                 ↓
            Schema Error              Type Error        Logic Error
```

---

## 2. Unterstützte JSON-Formate

### 2.1 Trading Bot Config (TradingBotConfig)

**Schema**: `config/schemas/trading_bot_config.schema.json`
**Pydantic Model**: `src/core/tradingbot/config/models.py::TradingBotConfig`
**Verwendung**: Entry Designer, Trading Bot, Config Loader

**Struktur**:
```json
{
  "schema_version": "1.0.0",
  "indicators": [...],
  "regimes": [...],
  "strategies": [...],
  "strategy_sets": [...],
  "routing": [...]
}
```

**Validation-Regeln**:
- Alle `indicator_id` müssen in `indicators[]` definiert sein
- Alle `regime_id` müssen in `regimes[]` definiert sein
- Alle `strategy_id` müssen in `strategies[]` definiert sein
- Alle `strategy_set_id` müssen in `strategy_sets[]` definiert sein
- Routing-Regeln müssen existierende Regime-IDs referenzieren

---

### 2.2 CEL RulePack (RulePack)

**Schema**: `config/schemas/rulepack.schema.json`
**Pydantic Model**: `src/core/tradingbot/cel/models.py::RulePack`
**Verwendung**: CEL Editor, Trading Bot, Entry Analyzer

**Struktur**:
```json
{
  "rules_version": "1.0.0",
  "engine": "CEL",
  "metadata": {...},
  "packs": [
    {
      "pack_type": "entry",
      "rules": [
        {
          "id": "rule_1",
          "name": "RSI Oversold Entry",
          "enabled": true,
          "expression": "rsi14.value < 30 && adx14.value > 25",
          "severity": "block",
          "message": "RSI oversold condition met"
        }
      ]
    }
  ]
}
```

**Validation-Regeln**:
- `engine` muss "CEL" sein
- `rules_version` muss Semantic Versioning folgen (x.y.z)
- `pack_type` muss einer der: `no_trade`, `entry`, `exit`, `update_stop`, `risk` sein
- `severity` muss einer der: `block`, `exit`, `update_stop`, `warn` sein
- CEL-Expressions müssen syntaktisch korrekt sein

---

### 2.3 Backtest Config (BacktestConfig)

**Schema**: `config/schemas/backtest_config_v2.schema.json`
**Pydantic Model**: `src/backtesting/schema_types.py::BacktestConfig`
**Verwendung**: Entry Analyzer, Backtest Engine

**Struktur**:
```json
{
  "schema_version": "2.0.0",
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000.0,
  "strategy_config_path": "path/to/strategy.json"
}
```

---

## 3. Schema-Validator

### 3.1 Verwendung

```python
from src.core.tradingbot.config.validator import SchemaValidator

validator = SchemaValidator()

# Validierung mit klarem Error-Reporting
try:
    validator.validate_file(
        json_path="03_JSON/Trading_Bot/my_strategy.json",
        schema_name="trading_bot_config"
    )
    print("✅ Validation successful")
except ValidationError as e:
    print(f"❌ Validation failed: {e.message}")
    print(f"   JSON Path: {e.json_path}")
    print(f"   Schema Rule: {e.schema_rule}")
```

### 3.2 Verfügbare Schemas

| Schema Name | Datei | Beschreibung |
|-------------|-------|--------------|
| `trading_bot_config` | `trading_bot_config.schema.json` | Trading Bot Konfiguration |
| `rulepack` | `rulepack.schema.json` | CEL RulePack |
| `backtest_config` | `backtest_config_v2.schema.json` | Backtest Konfiguration |

---

## 4. Best Practices

### 4.1 JSON-Dateien erstellen

```python
import json
from pathlib import Path
from src.core.tradingbot.config.validator import SchemaValidator

# 1. Erstelle Datenstruktur
config_data = {
    "schema_version": "1.0.0",
    "indicators": [...],
    # ...
}

# 2. Validiere BEVOR du speicherst
validator = SchemaValidator()
validator.validate_data(config_data, schema_name="trading_bot_config")

# 3. Speichere validierte Daten
config_path = Path("03_JSON/Trading_Bot/my_strategy.json")
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config_data, f, indent=2, ensure_ascii=False)

print(f"✅ Config saved: {config_path}")
```

### 4.2 JSON-Dateien laden

```python
from src.core.tradingbot.config.loader import ConfigLoader

loader = ConfigLoader()

# Lädt, validiert und konvertiert zu Pydantic-Model
config = loader.load_config("03_JSON/Trading_Bot/my_strategy.json")

# config ist jetzt TradingBotConfig-Instanz mit Type-Safety
print(f"Loaded {len(config.strategies)} strategies")
```

### 4.3 Fehlerbehandlung

```python
from src.core.tradingbot.config.validator import ValidationError

try:
    config = loader.load_config("path/to/config.json")
except ValidationError as e:
    # JSON Schema Validation-Fehler
    print(f"Schema Error at {e.json_path}: {e.message}")
except ValueError as e:
    # Pydantic Type-Error oder Business Logic-Fehler
    print(f"Validation Error: {str(e)}")
except FileNotFoundError:
    # Datei existiert nicht
    print("Config file not found")
```

---

## 5. Schema-Versionierung

### 5.1 Version-Format

Alle Schemas verwenden **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking Changes (z.B. 1.0.0 → 2.0.0)
- **MINOR**: Neue Features, abwärtskompatibel (z.B. 1.0.0 → 1.1.0)
- **PATCH**: Bugfixes, abwärtskompatibel (z.B. 1.0.0 → 1.0.1)

### 5.2 Migration

Bei **Breaking Changes** (MAJOR-Versionswechsel):

1. Alter Schema bleibt verfügbar: `trading_bot_config_v1.schema.json`
2. Neuer Schema wird hinzugefügt: `trading_bot_config_v2.schema.json`
3. Migration-Script wird erstellt: `scripts/migrate_config_v1_to_v2.py`
4. Dokumentation wird aktualisiert

```python
# Beispiel: Migration Script
from src.core.tradingbot.config.migrator import ConfigMigrator

migrator = ConfigMigrator()
migrator.migrate_file(
    input_path="old_config_v1.json",
    output_path="new_config_v2.json",
    from_version="1.0.0",
    to_version="2.0.0"
)
```

---

## 6. Verzeichnisstruktur

```
OrderPilot-AI/
├── 03_JSON/                          # JSON-Dateien (user-created)
│   ├── Trading_Bot/                  # Bot Configs
│   │   ├── trend_following.json
│   │   ├── mean_reversion.json
│   │   └── ...
│   ├── RulePacks/                    # CEL RulePacks
│   │   ├── default_rules.json
│   │   ├── scalping_rules.json
│   │   └── ...
│   └── Backtests/                    # Backtest Configs
│       └── ...
│
├── config/schemas/                   # JSON Schemas (code)
│   ├── trading_bot_config.schema.json
│   ├── rulepack.schema.json
│   ├── backtest_config_v2.schema.json
│   └── ...
│
├── src/core/tradingbot/
│   ├── config/
│   │   ├── validator.py             # SchemaValidator
│   │   ├── loader.py                # ConfigLoader
│   │   ├── migrator.py              # ConfigMigrator
│   │   └── models.py                # Pydantic Models
│   └── cel/
│       ├── models.py                # RulePack Pydantic Models
│       ├── engine.py                # CEL Engine
│       └── loader.py                # RulePack Loader
└── docs/
    └── JSON_INTERFACE_RULES.md      # Diese Datei
```

---

## 7. Integration mit anderen Modulen

### 7.1 Entry Designer

**Read**: Lädt existierende JSON-Configs mit `ConfigLoader`
**Write**: Speichert Configs nach Schema-Validation mit `SchemaValidator`

```python
# In Entry Designer
from src.core.tradingbot.config.loader import ConfigLoader
from src.core.tradingbot.config.validator import SchemaValidator

# Laden
config = ConfigLoader().load_config("03_JSON/Trading_Bot/my_strategy.json")

# Ändern
config.strategies.append(new_strategy)

# Validieren + Speichern
validator = SchemaValidator()
config_dict = config.model_dump()  # Pydantic → dict
validator.validate_data(config_dict, "trading_bot_config")
# ... speichern
```

### 7.2 CEL Engine

**Read**: Lädt RulePacks mit `RulePackLoader`
**Write**: N/A (CEL Editor ist Schreiber)

```python
from src.core.tradingbot.cel.loader import RulePackLoader

loader = RulePackLoader()
rulepack = loader.load("03_JSON/RulePacks/default_rules.json")

# rulepack ist RulePack-Instanz
for pack in rulepack.packs:
    print(f"Pack: {pack.pack_type}, Rules: {len(pack.rules)}")
```

### 7.3 Trading Bot

**Read**: Lädt Configs + RulePacks
**Write**: N/A (konfiguriert, schreibt nicht)

```python
# In BotController
from src.core.tradingbot.config.loader import ConfigLoader
from src.core.tradingbot.cel.loader import RulePackLoader

# Laden bei Bot-Start
self.config = ConfigLoader().load_config(config_path)
self.rules = RulePackLoader().load(rulepack_path)

# Verwenden während Laufzeit
# ... (siehe BotController Integration)
```

---

## 8. Entwickler-Checkliste

### Beim Hinzufügen eines neuen JSON-Formats:

- [ ] JSON Schema erstellen in `config/schemas/`
- [ ] Pydantic Model erstellen in entsprechendem Modul
- [ ] Validation-Regeln definieren
- [ ] Loader-Funktion implementieren
- [ ] Migration-Strategie definieren (wenn bestehende Formate betroffen)
- [ ] Dokumentation in dieser Datei aktualisieren
- [ ] Unit-Tests für Schema-Validation schreiben
- [ ] Integration-Tests für Loader schreiben
- [ ] Beispiel-JSON erstellen in `03_JSON/`

### Beim Ändern eines bestehenden JSON-Formats:

- [ ] Schema-Version erhöhen (MAJOR/MINOR/PATCH)
- [ ] JSON Schema aktualisieren
- [ ] Pydantic Model aktualisieren
- [ ] Migration-Script erstellen (bei Breaking Changes)
- [ ] Alle verwendenden Module anpassen
- [ ] Tests aktualisieren
- [ ] Dokumentation aktualisieren
- [ ] Changelog aktualisieren

---

## 9. Referenzen

- **JSON Schema Draft 2020-12**: https://json-schema.org/draft/2020-12/json-schema-validation.html
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **CEL Language Specification**: https://github.com/google/cel-spec
- **Semantic Versioning**: https://semver.org/

---

**Letzte Aktualisierung**: 2026-01-20
**Schema Version**: 1.0.0
