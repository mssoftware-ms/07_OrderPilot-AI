# Unified Regime Configuration - JSON v2.0

## Überblick

Die neue **Unified Regime Configuration** (v2.0) konsolidiert alle regime-bezogenen Daten in einer einzigen JSON-Datei, die von allen Regime-Tabs genutzt wird.

## Dateistruktur

```
03_JSON/Entry_Analyzer/Regime/
└── entry_analyzer_regime.json  (v2.0 - Unified Format)
```

## JSON-Struktur

### 1. **Indicators** (mit Optimization Ranges)

Jeder Indikator enthält:
- **params**: Aktuelle aktive Parameter
- **optimization_ranges**: Min/Max-Bereiche für Optimierung

```json
{
  "id": "adx14",
  "type": "ADX",
  "params": {
    "period": 14
  },
  "optimization_ranges": {
    "period": {
      "min": 10,
      "max": 30,
      "step": 1
    }
  },
  "enabled": true
}
```

**Beliebige Indikatoren mit beliebig vielen Parametern:**

Die Struktur ist vollständig dynamisch! Beispiele:

- **Standard-Indikatoren:**
  - ADX: `period`
  - MACD: `fast`, `slow`, `signal`
  - RSI: `period`
  - BB: `period`, `std_dev`

- **Komplexe Custom-Indikatoren:**
  - Ichimoku: `tenkan`, `kijun`, `senkou_b`, `displacement`
  - Custom Composite: `param1`, `param2`, ... , `param8`

**WICHTIG:** Das System unterstützt automatisch JEDEN Indikator mit BELIEBIG VIELEN Parametern!

### 2. **Regimes** (mit Threshold Ranges)

Jedes Regime enthält:
- **conditions**: CEL-basierte Erkennungslogik
- **optimization_ranges**: Thresholds für Regime-Erkennung

```json
{
  "id": "BULL",
  "name": "Bull Market",
  "conditions": {
    "all": [
      {
        "left": {"indicator_id": "adx14", "field": "value"},
        "op": "gt",
        "right": {"value": 25}
      }
    ]
  },
  "optimization_ranges": {
    "adx_threshold": {
      "min": 20,
      "max": 35,
      "step": 1,
      "description": "ADX threshold for trend strength"
    }
  },
  "priority": 80,
  "scope": "entry",
  "enabled": true
}
```

**Regime IDs:**
- `BULL` - Bull Market
- `BEAR` - Bear Market
- `SIDEWAYS` - Sideways (neutral)
- `SIDEWAYS_OVERBOUGHT` - Sideways Overbought
- `SIDEWAYS_OVERSOLD` - Sideways Oversold

### 3. **Optimization Results** (Historie)

Speichert Top-Optimierungsergebnisse:

```json
{
  "timestamp": "2026-01-24T05:15:00Z",
  "score": 87.5,
  "rank": 1,
  "params": {
    "adx14.period": 14,
    "rsi14.period": 12,
    "bb20.period": 22,
    "bb20.std_dev": 2.2,
    "BULL.adx_threshold": 28,
    "SIDEWAYS.rsi_low": 32,
    "SIDEWAYS.rsi_high": 68
  },
  "metrics": {
    "regime_clarity": 0.92,
    "regime_stability": 0.85,
    "regime_coverage": 0.88,
    "regime_balance": 0.86
  },
  "trial_number": 142,
  "optimization_config": {
    "mode": "QUICK",
    "max_trials": 150,
    "symbol": "BTCUSDT",
    "timeframe": "5m"
  },
  "applied": true
}
```

## Workflow: 3-Tab-Integration

### **Tab 1: Regime (Anzeige)**

**Liest:**
- `indicators[].params` → Zeigt aktuelle Indikator-Parameter
- `regimes[]` → Zeigt Regime-Definitionen mit Bedingungen
- `optimization_results[]` → Zeigt Historie der angewendeten Optimierungen

**Tabelle:**
```
┌──────────┬─────────────┬─────────────────┬──────────────────┐
│ Type     │ ID          │ Name/Type       │ Params/Conditions│
├──────────┼─────────────┼─────────────────┼──────────────────┤
│Indicator │ adx14       │ ADX             │ period: 14       │
│Indicator │ rsi14       │ RSI             │ period: 14       │
│Indicator │ bb20        │ BB              │ period: 20, ...  │
│Regime    │ BULL        │ Bull Market     │ adx > 25 AND ... │
│Regime    │ BEAR        │ Bear Market     │ adx > 25 AND ... │
└──────────┴─────────────┴─────────────────┴──────────────────┘
```

### **Tab 2: Regime Setup (Parameter-Ranges)**

**Liest:**
- `indicators[].optimization_ranges` → Erstellt dynamisch Min/Max-Felder
- `regimes[].optimization_ranges` → Threshold-Ranges

**Dynamische Tabelle:**
```
┌──────────────────┬─────────┬─────────┬──────┐
│ Parameter        │ Min     │ Max     │ Step │
├──────────────────┼─────────┼─────────┼──────┤
│ adx14.period     │ [10]    │ [30]    │ 1    │
│ rsi14.period     │ [10]    │ [20]    │ 1    │
│ bb20.period      │ [15]    │ [30]    │ 1    │
│ bb20.std_dev     │ [1.5]   │ [3.0]   │ 0.1  │
│ BULL.adx_thresh  │ [20]    │ [35]    │ 1    │
│ SIDEWAYS.rsi_low │ [25]    │ [45]    │ 1    │
└──────────────────┴─────────┴─────────┴──────┘
```

**Features:**
- Spinboxes automatisch aus JSON generiert
- Alle Indikator-Parameter sichtbar
- Alle Regime-Thresholds konfigurierbar
- Export/Import der Ranges

### **Tab 3: Regime Optimization (Ergebnisse & Speichern)**

**Liest:**
- Optimization Ranges aus Tab 2
- Führt TPE-Optimierung aus

**Schreibt:**
- `optimization_results[]` → Fügt neue Top-Ergebnisse hinzu
- `indicators[].params` → Update bei "Apply Selected"
- `regimes[].conditions` → Update Thresholds bei "Apply Selected"
- `metadata.updated_at` → Timestamp

**Ergebnisse-Tabelle:**
```
┌──────┬───────┬──────────────┬─────────────┬─────────────┐
│ Rank │ Score │ adx14.period │ rsi14.period│ BULL.thresh │
├──────┼───────┼──────────────┼─────────────┼─────────────┤
│ 1    │ 87.5  │ 14           │ 12          │ 28          │
│ 2    │ 85.2  │ 15           │ 14          │ 25          │
│ 3    │ 83.1  │ 13           │ 13          │ 30          │
└──────┴───────┴──────────────┴─────────────┴─────────────┘
```

**Aktionen:**
- ✅ **Apply Selected**: Übernimmt ausgewählte Zeile in `params` und `conditions`
- 💾 **Save to History**: Speichert Top-5 in `optimization_results[]`
- 📤 **Export**: Exportiert nur ausgewählte Zeilen

## Parameter-Mapping

### Flat → Nested Conversion

**Optimizer Output (flat):**
```json
{
  "adx14.period": 14,
  "rsi14.period": 12,
  "bb20.period": 22,
  "bb20.std_dev": 2.2,
  "BULL.adx_threshold": 28,
  "SIDEWAYS.rsi_low": 32
}
```

**JSON Structure (nested):**
```json
{
  "indicators": [
    {
      "id": "adx14",
      "params": {"period": 14}
    },
    {
      "id": "rsi14",
      "params": {"period": 12}
    },
    {
      "id": "bb20",
      "params": {
        "period": 22,
        "std_dev": 2.2
      }
    }
  ],
  "regimes": [
    {
      "id": "BULL",
      "conditions": {
        "all": [
          {
            "right": {"value": 28}  // adx_threshold
          }
        ]
      }
    },
    {
      "id": "SIDEWAYS",
      "conditions": {
        "all": [
          {
            "right": {"min": 32, "max": 68}  // rsi_low/high
          }
        ]
      }
    }
  ]
}
```

## Migration von v1.0 → v2.0

**Alte Struktur (v1.0):**
```json
{
  "indicators": [
    {"id": "adx14", "type": "ADX", "params": {"period": 14}}
  ],
  "regimes": [...]
}
```

**Neue Struktur (v2.0):**
```json
{
  "indicators": [
    {
      "id": "adx14",
      "type": "ADX",
      "params": {"period": 14},
      "optimization_ranges": {
        "period": {"min": 10, "max": 30, "step": 1}
      },
      "enabled": true
    }
  ],
  "regimes": [...],
  "optimization_results": []
}
```

**Migrationsscript:**
```python
def migrate_v1_to_v2(old_config: dict) -> dict:
    """Migrate v1.0 config to v2.0 unified format."""
    new_config = old_config.copy()
    new_config["schema_version"] = "2.0.0"

    # Add optimization_ranges to indicators
    for indicator in new_config["indicators"]:
        indicator["optimization_ranges"] = get_default_ranges(indicator["type"])
        indicator["enabled"] = True

    # Add optimization_ranges to regimes
    for regime in new_config["regimes"]:
        regime["optimization_ranges"] = get_regime_threshold_ranges(regime["id"])
        regime["enabled"] = True

    # Add optimization_results
    new_config["optimization_results"] = []

    return new_config
```

## Beispiel: Kompletter Workflow

### 1. Laden im Regime Tab
```python
# UI loads JSON
config = load_regime_config("entry_analyzer_regime.json")

# Display indicators
for ind in config.indicators:
    table.add_row(ind.id, ind.type, ind.params)

# Display regimes
for regime in config.regimes:
    table.add_row(regime.id, regime.name, regime.conditions)
```

### Beispiel: Custom-Indikator mit 8 Parametern

```json
{
  "id": "custom_composite",
  "type": "CUSTOM_COMPOSITE",
  "params": {
    "fast_period": 12,
    "slow_period": 26,
    "signal_period": 9,
    "smoothing_factor": 2.5,
    "threshold_upper": 0.8,
    "threshold_lower": 0.2,
    "lookback_bars": 50,
    "volatility_multiplier": 1.5
  },
  "optimization_ranges": {
    "fast_period": {"min": 8, "max": 16, "step": 1},
    "slow_period": {"min": 20, "max": 32, "step": 2},
    "signal_period": {"min": 7, "max": 12, "step": 1},
    "smoothing_factor": {"min": 1.5, "max": 3.5, "step": 0.1},
    "threshold_upper": {"min": 0.7, "max": 0.9, "step": 0.05},
    "threshold_lower": {"min": 0.1, "max": 0.3, "step": 0.05},
    "lookback_bars": {"min": 30, "max": 100, "step": 5},
    "volatility_multiplier": {"min": 1.0, "max": 2.5, "step": 0.1}
  },
  "enabled": true
}
```

**Regime Setup Tab generiert automatisch:**
```
┌────────────────────────────────┬─────────┬─────────┬──────┐
│ Parameter                      │ Min     │ Max     │ Step │
├────────────────────────────────┼─────────┼─────────┼──────┤
│ custom_composite.fast_period   │ [8]     │ [16]    │ 1    │
│ custom_composite.slow_period   │ [20]    │ [32]    │ 2    │
│ custom_composite.signal_period │ [7]     │ [12]    │ 1    │
│ custom_composite.smoothing_...│ [1.5]   │ [3.5]   │ 0.1  │
│ custom_composite.threshold_... │ [0.7]   │ [0.9]   │ 0.05 │
│ custom_composite.threshold_... │ [0.1]   │ [0.3]   │ 0.05 │
│ custom_composite.lookback_bars │ [30]    │ [100]   │ 5    │
│ custom_composite.volatility_...│ [1.0]   │ [2.5]   │ 0.1  │
└────────────────────────────────┴─────────┴─────────┴──────┘
```

**Keine Code-Änderung nötig!** Die UI liest die Parameter aus der JSON und generiert die Spinboxes automatisch.

### 2. Setup im Regime Setup Tab
```python
# Read optimization ranges
for ind in config.indicators:
    for param_name, range_def in ind.optimization_ranges.items():
        create_spinbox(
            f"{ind.id}.{param_name}",
            min=range_def.min,
            max=range_def.max,
            step=range_def.step
        )

# Read regime threshold ranges
for regime in config.regimes:
    for threshold_name, range_def in regime.optimization_ranges.items():
        create_spinbox(
            f"{regime.id}.{threshold_name}",
            min=range_def.min,
            max=range_def.max
        )
```

### 3. Optimization & Save
```python
# Run optimization
results = optimizer.optimize(param_ranges)

# User selects best result (rank 1)
selected_result = results[0]

# Apply to config
apply_result_to_config(selected_result, config)

# Save to history
config.optimization_results.insert(0, {
    "timestamp": utcnow(),
    "score": selected_result.score,
    "params": selected_result.params,
    "applied": True
})

# Keep only top 10 in history
config.optimization_results = config.optimization_results[:10]

# Save JSON
save_regime_config("entry_analyzer_regime.json", config)
```

## Vorteile der Unified Structure

✅ **Eine einzige Datenquelle** - Keine Inkonsistenzen zwischen Tabs
✅ **Vollständige Historie** - Alle Optimierungen werden gespeichert
✅ **Dynamische UI** - Tabs generieren UI aus JSON-Struktur
✅ **Einfacher Export** - Eine Datei enthält alles
✅ **Versionierung** - Schema-Version ermöglicht Migration
✅ **Reproduzierbarkeit** - Optimization Config gespeichert
✅ **Auswahl-basiertes Apply** - Nur gewählte Ergebnisse übernehmen

## Nächste Schritte

1. ✅ Schema erstellt (`regime_config_unified.schema.json`)
2. ✅ Beispiel-JSON erstellt (`regime_config_unified_example.json`)
3. ⏳ Regime Setup Tab dynamisch machen
4. ⏳ Optimization Tab um Speichern erweitern
5. ⏳ Migration v1.0 → v2.0 implementieren
6. ⏳ Validation gegen Schema
