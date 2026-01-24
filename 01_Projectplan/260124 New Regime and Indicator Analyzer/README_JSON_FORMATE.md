# Neue JSON-Formate für Orderpilot Regime-Optimierung

## Übersicht: 2-Stufen Sequentieller Workflow

Das System arbeitet in **zwei aufeinanderfolgenden Optimierungsstufen**:

1. **Stufe 1:** Regime-Erkennung optimieren → Beste Parameter für BULL/BEAR/SIDEWAYS
2. **Stufe 2:** Indikator-Sets optimieren → Pro Regime separat Entry/Exit Signale testen

---

## ⚠️ KRITISCHE INFORMATION: Korrekte Indikatoren

### Stufe 1: Regime-Erkennung (5 Indikatoren)

| Indikator | Zweck | Parameter |
|-----------|-------|-----------|
| **ADX** | Trendstärke | period, threshold |
| **SMA_Fast** | Trendrichtung (schnell) | period |
| **SMA_Slow** | Trendrichtung (langsam) | period |
| **RSI** | Sideways-Erkennung | period, sideways_low, sideways_high |
| **BB Width** | Volatilität | period, std_dev, width_percentile |

### Stufe 2: Entry/Exit Signale (7 Indikatoren)

| Indikator | Zweck |
|-----------|-------|
| **RSI** | Momentum |
| **MACD** | Trend-Momentum |
| **STOCH** | Mean-Reversion |
| **BB** | Volatilitäts-Bands |
| **ATR** | Trailing Stops |
| **EMA** | Trend-Following |
| **CCI** | Überkauft/Überverkauft |

---

## ⚡ Performance-Optimierung

### Problem: Kombinatorische Explosion

| Stufe | Grid Search | Mit TPE | Speedup |
|-------|-------------|---------|---------|
| Stufe 1 | 303,750 | 150 | **2,025x** |
| Stufe 2 | ~125,000 | ~280 | **446x** |

### Lösung: Optuna TPE + Hyperband

```json
{
  "optimization_config": {
    "mode": "standard",
    "method": "tpe_multivariate",
    "max_trials": 150,
    "early_stopping": {
      "enabled": true,
      "pruner": "hyperband"
    }
  }
}
```

**Details:** Siehe `PERFORMANCE_OPTIMIERUNG.md`

---

## 🔄 Vollständiger Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    STUFE 1: REGIME-OPTIMIERUNG                          │
│  ════════════════════════════════════════════════════════════════════   │
│                                                                          │
│  Indikatoren: ADX, SMA_Fast, SMA_Slow, RSI, BB Width                   │
│                                                                          │
│  Klassifikationslogik:                                                  │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ BULL:     ADX > threshold AND Close > SMA_Fast > SMA_Slow     │    │
│  │ BEAR:     ADX > threshold AND Close < SMA_Fast < SMA_Slow     │    │
│  │ SIDEWAYS: ADX < threshold AND BB_Width < percentile           │    │
│  │           AND RSI between sideways_low - sideways_high        │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Speichern:                                                             │
│  • regime_optimization_results_BTCUSDT_5m.json  (alle Ergebnisse)      │
│  • optimized_regime_BTCUSDT_5m.json             (gewählte Config)      │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    STUFE 2: INDIKATOR-SET-OPTIMIERUNG                   │
│  ════════════════════════════════════════════════════════════════════   │
│                                                                          │
│  Indikatoren: RSI, MACD, STOCH, BB, ATR, EMA, CCI (7 Stück)            │
│                                                                          │
│  Für JEDES Regime SEPARAT (nur dessen Bars verwenden!):                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🟢 BULL (#26a69a)                                               │   │
│  │ → indicator_sets_BULL_BTCUSDT_5m.json                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🔴 BEAR (#ef5350)                                               │   │
│  │ → indicator_sets_BEAR_BTCUSDT_5m.json                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ ⚪ SIDEWAYS (#9e9e9e)                                           │   │
│  │ → indicator_sets_SIDEWAYS_BTCUSDT_5m.json                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Datei-Struktur

```
03_JSON/Entry_Analyzer/Regime/
│
├── schemas/
│   ├── regime_optimization_results.schema.json      ← Stufe 1 Ergebnisse
│   ├── optimized_regime_config.schema.json          ← Stufe 1 Export
│   ├── indicator_optimization_results.schema.json   ← Stufe 2 Ergebnisse
│   └── optimized_indicator_sets.schema.json         ← Stufe 2 Export
│
├── STUFE_1_Regime/
│   ├── regime_optimization_results_BTCUSDT_5m.json  ← Alle Kombinationen
│   └── optimized_regime_BTCUSDT_5m.json             ← Gewählte Config
│
└── STUFE_2_Indicators/
    │
    ├── BULL/
    │   ├── indicator_optimization_results_BULL_BTCUSDT_5m.json
    │   └── indicator_sets_BULL_BTCUSDT_5m.json
    │
    ├── BEAR/
    │   ├── indicator_optimization_results_BEAR_BTCUSDT_5m.json
    │   └── indicator_sets_BEAR_BTCUSDT_5m.json
    │
    └── SIDEWAYS/
        ├── indicator_optimization_results_SIDEWAYS_BTCUSDT_5m.json
        └── indicator_sets_SIDEWAYS_BTCUSDT_5m.json
```

---

## 🎨 Regime-Farben

| Regime | Farbe | Hex Code | Verwendung |
|--------|-------|----------|------------|
| **BULL** | Grün | `#26a69a` | Chart-Linien, UI-Highlighting |
| **BEAR** | Rot | `#ef5350` | Chart-Linien, UI-Highlighting |
| **SIDEWAYS** | Grau | `#9e9e9e` | Chart-Linien, UI-Highlighting |

```python
REGIME_COLORS = {
    "BULL": "#26a69a",
    "BEAR": "#ef5350",
    "SIDEWAYS": "#9e9e9e",
}
```

---

## JSON-Dateien im Detail

### STUFE 1: Regime-Optimierung

#### 1.1 Ergebnistabelle (`regime_optimization_results_*.json`)

```json
{
  "version": "2.0",
  "meta": {
    "stage": "regime_optimization",
    "total_combinations": 150,
    "method": "tpe_multivariate"
  },
  "optimization_config": {
    "mode": "standard",
    "max_trials": 150,
    "early_stopping": { "enabled": true, "pruner": "hyperband" }
  },
  "param_ranges": {
    "adx": { "period": {...}, "threshold": {...} },
    "sma_fast": { "period": {...} },
    "sma_slow": { "period": {...} },
    "rsi": { "period": {...}, "sideways_low": {...}, "sideways_high": {...} },
    "bb": { "period": {...}, "width_percentile": {...} }
  },
  "results": [...]
}
```

#### 1.2 Gewählte Regime-Config (`optimized_regime_*.json`)

```json
{
  "version": "2.0",
  "meta": {
    "classification_logic": {
      "bull": "ADX > threshold AND Close > SMA_Fast AND SMA_Fast > SMA_Slow",
      "bear": "ADX > threshold AND Close < SMA_Fast AND SMA_Fast < SMA_Slow",
      "sideways": "ADX < threshold AND BB_Width < percentile AND RSI between low-high"
    }
  },
  "indicators": [
    { "id": "adx14", "name": "ADX", "purpose": "trend_strength" },
    { "id": "sma50", "name": "SMA", "purpose": "trend_direction_fast" },
    { "id": "sma200", "name": "SMA", "purpose": "trend_direction_slow" },
    { "id": "rsi14", "name": "RSI", "purpose": "sideways_momentum" },
    { "id": "bb20", "name": "BB", "purpose": "sideways_volatility" }
  ],
  "regimes": [...]
}
```

---

### STUFE 2: Indikator-Set-Optimierung

```json
{
  "version": "2.0",
  "meta": {
    "regime": "BULL",
    "tested_indicators": ["RSI", "MACD", "STOCH", "BB", "ATR", "EMA", "CCI"]
  },
  "signal_sets": {
    "entry_long": { "indicator": "RSI", "conditions": {...} },
    "entry_short": { "enabled": false },
    "exit_long": { "indicator": "ATR", "conditions": {...} },
    "exit_short": { "enabled": false }
  }
}
```

---

## Kompatibilität

Alle JSON-Formate sind kompatibel mit:
- `ConditionEvaluator` (left/op/right Format)
- `RegimeDetector.detect_active_regimes()`
- `IndicatorEngine.calculate()`
- `_draw_regime_lines()` (Farben aus JSON)

---

## Referenz-Dokumente

1. **PERFORMANCE_OPTIMIERUNG.md** - TPE/Optuna Best Practices
2. **PROMPT_Claude_CLI_Regime_Optimierung.md** - Implementierungs-Anleitung
3. **CHECKLISTE_Regime_Optimierung_Refactoring.md** - 68 Tasks
