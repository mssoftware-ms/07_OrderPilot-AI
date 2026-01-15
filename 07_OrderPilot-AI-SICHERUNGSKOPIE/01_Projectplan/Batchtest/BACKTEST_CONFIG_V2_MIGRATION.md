# Backtest Config V2 - Migration Guide

## Überblick

Das neue BacktestConfigV2-Format bietet erweiterte Funktionen für variable Backtesting-Konfigurationen:

- **Optimierbare Parameter**: `optimize: true` + `range: [...]` für Grid/Random Search
- **Weight-Presets**: Vordefinierte Indikator-Gewichtungen (W0, W1, W2) gegen Overfitting
- **Vererbung/Extends**: Templates können von Basis-Templates erben
- **Parameter-Gruppen**: Parameter als Paare testen (z.B. SL + TP zusammen)
- **Conditionals**: If/Then-Logik für automatische Anpassungen
- **Walk-Forward-Support**: Integrierte WFA-Konfiguration

---

## Schnellstart

### 1. Aus Template laden

```python
from src.core.backtesting.batch_runner_v2 import BatchRunnerV2

# Aus vordefiniertem Template
runner = BatchRunnerV2.from_template("trendfollowing_conservative")

# Mit Overrides
runner = BatchRunnerV2.from_template(
    "scalping_micro_100eur",
    overrides={
        "risk_leverage.base_leverage.value": 15,
        "entry_score.thresholds.min_score_for_entry.value": 0.60
    }
)

# Batch ausführen
summary = await runner.run()
print(f"Bester Run: {summary.best_run.metrics}")
```

### 2. Eigene Konfiguration erstellen

```python
from src.core.backtesting.config_loader import load_config

# JSON-Datei laden (mit Extends-Support)
config = load_config("config/backtest_templates/my_custom.json")

# Grid-Kombinationen zählen
from src.core.backtesting.config_loader import count_grid_combinations
print(f"Kombinationen: {count_grid_combinations(config)}")
```

---

## Verfügbare Templates

### Basis-Templates (zum Erweitern)

| Template | Beschreibung | Timeframe |
|----------|--------------|-----------|
| `base_trendfollowing.json` | Trend-Following mit EMA/ADX | 5m |
| `base_scalping.json` | Schnelle Entries mit engem SL | 1m |
| `base_mean_reversion.json` | Range-Trading mit RSI | 15m |

### Spezialisierte Templates

| Template | Basis | Besonderheit |
|----------|-------|--------------|
| `trendfollowing_conservative.json` | base_trendfollowing | Breites SL, hohe Score-Threshold |
| `trendfollowing_aggressive.json` | base_trendfollowing | Früherer Entry, SFP aktiviert |
| `scalping_micro_100eur.json` | base_scalping | 100€ Micro-Account optimiert |

---

## JSON-Struktur

### Basis-Struktur

```json
{
  "$schema": "../schemas/backtest_config_v2.schema.json",
  "version": "2.0.0",

  "meta": {
    "name": "Meine Strategie",
    "description": "...",
    "tags": ["btc", "scalping"],
    "target_timeframe": "5m"
  },

  "strategy_profile": {
    "type": "trendfollowing",
    "preset": "W1"
  },

  "entry_score": { ... },
  "entry_triggers": { ... },
  "exit_management": { ... },
  "risk_leverage": { ... },
  "optimization": { ... },
  "constraints": { ... }
}
```

### Optimierbare Parameter

Parameter mit `optimize: true` und `range` werden im Grid expandiert:

```json
{
  "exit_management": {
    "stop_loss": {
      "atr_multiplier": {
        "value": 1.5,
        "optimize": true,
        "range": [1.0, 1.3, 1.5, 2.0]
      }
    }
  }
}
```

### Weight-Presets

Statt individuelle Weights zu optimieren (Overfitting-Gefahr), Presets nutzen:

```json
{
  "entry_score": {
    "weights": {
      "use_preset": "W1",
      "custom": null
    },
    "weight_presets": {
      "W0": { "trend": 0.25, "rsi": 0.15, "macd": 0.20, "adx": 0.15, "vol": 0.10, "volume": 0.15 },
      "W1": { "trend": 0.35, "rsi": 0.10, "macd": 0.15, "adx": 0.20, "vol": 0.10, "volume": 0.10 },
      "W2": { "trend": 0.25, "rsi": 0.20, "macd": 0.20, "adx": 0.10, "vol": 0.15, "volume": 0.10 }
    }
  }
}
```

### Vererbung (Extends)

Template von Basis erben und nur Änderungen definieren:

```json
{
  "extends": "base_trendfollowing.json",

  "meta": {
    "name": "Meine Variante"
  },

  "overrides": {
    "entry_score.thresholds.min_score_for_entry.value": 0.70,
    "exit_management.stop_loss.atr_multiplier.value": 2.0
  }
}
```

### Parameter-Gruppen

Parameter zusammen als Paare testen:

```json
{
  "parameter_groups": [
    {
      "name": "sl_tp_pair",
      "description": "SL und TP zusammen testen",
      "parameters": [
        "exit_management.stop_loss.atr_multiplier.value",
        "exit_management.take_profit.atr_multiplier.value"
      ],
      "combinations": [
        [1.0, 1.5],
        [1.5, 2.0],
        [2.0, 3.0]
      ]
    }
  ]
}
```

### Conditionals

Automatische Anpassungen basierend auf anderen Parametern:

```json
{
  "conditionals": [
    {
      "if": { "risk_leverage.base_leverage": { ">=": 20 } },
      "then": { "risk_leverage.min_liquidation_distance_pct": 7.0 }
    }
  ]
}
```

---

## Migration von V1

### V1-Config (alt)

```json
{
  "name": "Mein Backtest",
  "risk_per_trade_pct": 1.0,
  "base_leverage": 5,
  "sl_atr_multiplier": 1.5,
  "tp_atr_multiplier": 2.0
}
```

### V2-Config (neu)

```json
{
  "version": "2.0.0",
  "meta": {
    "name": "Mein Backtest"
  },
  "risk_leverage": {
    "risk_per_trade_pct": { "value": 1.0, "optimize": false },
    "base_leverage": { "value": 5, "optimize": false }
  },
  "exit_management": {
    "stop_loss": {
      "atr_multiplier": { "value": 1.5, "optimize": true, "range": [1.0, 1.5, 2.0] }
    },
    "take_profit": {
      "atr_multiplier": { "value": 2.0, "optimize": true, "range": [1.5, 2.0, 3.0] }
    }
  }
}
```

### Mapping-Tabelle

| V1 Parameter | V2 Pfad |
|--------------|---------|
| `risk_per_trade_pct` | `risk_leverage.risk_per_trade_pct.value` |
| `base_leverage` | `risk_leverage.base_leverage.value` |
| `sl_atr_multiplier` | `exit_management.stop_loss.atr_multiplier.value` |
| `tp_atr_multiplier` | `exit_management.take_profit.atr_multiplier.value` |
| `trailing_activation` | `exit_management.trailing_stop.activation_atr.value` |
| `trailing_distance` | `exit_management.trailing_stop.distance_atr.value` |
| `min_score_for_entry` | `entry_score.thresholds.min_score_for_entry.value` |
| `weight_*` | `entry_score.weights.use_preset` (W0/W1/W2) |
| `gate_block_in_chop` | `entry_score.gates.block_in_chop` |

---

## API-Referenz

### ConfigLoader

```python
from src.core.backtesting.config_loader import ConfigLoader, load_config

# Einfaches Laden
config = load_config("path/to/config.json")

# Mit Optionen
loader = ConfigLoader(
    base_path=Path("config/backtest_templates"),
    validate=True,
    resolve_conditionals=True
)
config = loader.load("my_template.json")
```

### GridSpaceGenerator

```python
from src.core.backtesting.config_loader import GridSpaceGenerator, count_grid_combinations

# Anzahl Kombinationen
count = count_grid_combinations(config)

# Alle Varianten generieren
variants = GridSpaceGenerator.generate(config)
```

### BatchRunnerV2

```python
from src.core.backtesting.batch_runner_v2 import BatchRunnerV2

# Erstellen
runner = BatchRunnerV2.from_template("trendfollowing_conservative")
runner = BatchRunnerV2.from_file("path/to/config.json")
runner = BatchRunnerV2(config_object)

# Progress Callback
runner.set_progress_callback(lambda pct, msg: print(f"{pct}%: {msg}"))

# Ausführen
summary = await runner.run()

# Ergebnisse
best = runner.best_result
all_results = runner.results
```

### ConfigValidator

```python
from src.core.backtesting.config_validator import ConfigValidator, validate_config

# Schnell validieren
result = validate_config(config)
if not result.valid:
    print(result.errors)

# Mit Validator-Instanz
validator = ConfigValidator()
result = validator.validate(config)
result = validator.validate_file(Path("config.json"))
```

---

## Best Practices

### 1. Grid-Größe kontrollieren

```python
# VORHER prüfen!
count = count_grid_combinations(config)
if count > 1000:
    print(f"WARNUNG: {count} Kombinationen - eventuell Random Search verwenden")
```

### 2. Parameter-Priorität beachten

Nach Forschung (Van Tharp) haben Parameter unterschiedliche Impacts:

| Priorität | Parameter | Impact |
|-----------|-----------|--------|
| 1 (Höchste) | TP/SL ATR Multipliers | ~30% |
| 2 (Hoch) | Trailing Activation/Distance | ~20% |
| 3 (Mittel) | Entry Score Threshold | ~15% |
| 4 (Niedrig) | Entry Weights | ~10% |

**Empfehlung**: Nur Tier 1-2 optimieren, Rest fixieren.

### 3. Overfitting vermeiden

- **Weights NICHT einzeln optimieren** - Presets nutzen
- **Parameter-Gruppen** für logische Paare (SL+TP)
- **Walk-Forward** aktivieren für Out-of-Sample Validierung
- **min_trades Constraint** hoch setzen (>50)

### 4. Micro-Account Besonderheiten

Bei 100€ Account:
- **Fee-Impact** beachten (0.06% Taker kann 30-75% des Profits auffressen)
- **Höherer Leverage** nötig, aber **min_liquidation_distance** einhalten
- **Mehr Trades** für statistische Signifikanz

---

## Dateien

| Pfad | Beschreibung |
|------|--------------|
| `config/schemas/backtest_config_v2.schema.json` | JSON Schema |
| `src/core/backtesting/config_v2.py` | Dataclasses |
| `src/core/backtesting/config_validator.py` | Validierung |
| `src/core/backtesting/config_loader.py` | Loader mit Extends |
| `src/core/backtesting/batch_runner_v2.py` | Batch-Runner V2 |
| `config/backtest_templates/base_*.json` | Basis-Templates |
| `config/backtest_templates/*_conservative.json` | Spezialisierte Templates |
