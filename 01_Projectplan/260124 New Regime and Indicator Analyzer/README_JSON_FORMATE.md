# Neue JSON-Formate für Orderpilot Regime-Optimierung

## Übersicht: 2-Stufen Sequentieller Workflow

Das System arbeitet in **zwei aufeinanderfolgenden Optimierungsstufen**:

1. **Stufe 1:** Regime-Erkennung optimieren → Beste Parameter für BULL/BEAR/SIDEWAYS
2. **Stufe 2:** Indikator-Sets optimieren → Pro Regime separat Entry/Exit Signale testen

---

## 🔄 Vollständiger Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    STUFE 1: REGIME-OPTIMIERUNG                          │
│  ════════════════════════════════════════════════════════════════════   │
│                                                                          │
│  Einstellbar: Auto-Modus oder feste Parameter-Ranges                    │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Parameter-Varianten:                                            │    │
│  │ • ADX Period:    10-20 (Step 2) → 6 Werte                      │    │
│  │ • ADX Threshold: 17-40 (Step 3) → 8 Werte                      │    │
│  │ • RSI Period:    9-21 (Step 3)  → 5 Werte                      │    │
│  │ = 240 Kombinationen (oder Auto: bis 1000)                      │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Ergebnis-Tabelle (sortiert nach Score):                                │
│  ┌──────┬───────┬───────────┬────────────┬──────────────────────────┐  │
│  │ Rank │ Score │ ADX Prd   │ ADX Thresh │ F1 Bull/Bear/Sideways    │  │
│  ├──────┼───────┼───────────┼────────────┼──────────────────────────┤  │
│  │ ✓ 1  │ 78.5  │ 10        │ 17         │ 82% / 79% / 71%          │  │
│  │   2  │ 76.2  │ 10        │ 20         │ 80% / 77% / 73%          │  │
│  └──────┴───────┴───────────┴────────────┴──────────────────────────┘  │
│                                                                          │
│  Speichern:                                                             │
│  • regime_optimization_results_BTCUSDT_5m.json  (alle Ergebnisse)      │
│  • optimized_regime_BTCUSDT_5m.json             (gewählte Config)      │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
                    Regime wird auf Testdaten angewandt
                    Chart zeigt BULL/BEAR/SIDEWAYS Perioden
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    STUFE 2: INDIKATOR-SET-OPTIMIERUNG                   │
│  ════════════════════════════════════════════════════════════════════   │
│                                                                          │
│  Einstellbar: Auto-Modus oder feste Parameter-Ranges                    │
│                                                                          │
│  Für JEDES Regime SEPARAT (nur dessen Bars verwenden!):                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🟢 BULL-Perioden (z.B. 45% der Bars)                            │   │
│  │                                                                  │   │
│  │ Indikatoren testen:                                             │   │
│  │ • RSI: Period 7-21 × Threshold 20-80                            │   │
│  │ • MACD: Fast 8-16 × Slow 20-30 × Signal 5-12                    │   │
│  │ • Stochastic: K 5-21 × D 3-9                                    │   │
│  │ • Bollinger: Period 10-30 × StdDev 1.5-3.0                      │   │
│  │                                                                  │   │
│  │ 4 Durchläufe (jeweils alle Kombinationen):                      │   │
│  │ ├── Entry-Long  → Score, Win Rate, Profit Factor               │   │
│  │ ├── Entry-Short → Score, Win Rate, Profit Factor               │   │
│  │ ├── Exit-Long   → Score, Win Rate, Profit Factor               │   │
│  │ └── Exit-Short  → Score, Win Rate, Profit Factor               │   │
│  │                                                                  │   │
│  │ Ergebnis-Tabellen (4 Stück, sortiert nach Score):               │   │
│  │ indicator_optimization_results_BULL_BTCUSDT_5m.json             │   │
│  │                                                                  │   │
│  │ Beste Sets auswählen → Speichern als:                           │   │
│  │ indicator_sets_BULL_BTCUSDT_5m.json                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🔴 BEAR-Perioden (z.B. 25% der Bars)                            │   │
│  │ ... (gleicher Prozess wie BULL)                                 │   │
│  │                                                                  │   │
│  │ Ergebnis:                                                       │   │
│  │ indicator_optimization_results_BEAR_BTCUSDT_5m.json             │   │
│  │ indicator_sets_BEAR_BTCUSDT_5m.json                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ ⚪ SIDEWAYS-Perioden (z.B. 30% der Bars)                        │   │
│  │ ... (gleicher Prozess wie BULL)                                 │   │
│  │                                                                  │   │
│  │ Ergebnis:                                                       │   │
│  │ indicator_optimization_results_SIDEWAYS_BTCUSDT_5m.json         │   │
│  │ indicator_sets_SIDEWAYS_BTCUSDT_5m.json                         │   │
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

**Zweck:** Alle getesteten Parameter-Kombinationen mit Scores

```json
{
  "version": "2.0",
  "meta": {
    "stage": "regime_optimization",
    "total_combinations": 240,
    "method": "grid_search",
    "mode": "auto"
  },
  "param_ranges": {
    "adx_period": { "min": 10, "max": 20, "step": 2 },
    "adx_threshold": { "min": 17, "max": 40, "step": 3 }
  },
  "results": [
    {
      "rank": 1,
      "score": 78.5,
      "selected": true,
      "params": { "adx_period": 10, "adx_threshold": 17 },
      "metrics": { "f1_bull": 0.82, "f1_bear": 0.79, "f1_sideways": 0.71 }
    }
  ]
}
```

#### 1.2 Gewählte Regime-Config (`optimized_regime_*.json`)

**Zweck:** Die ausgewählte Regime-Erkennung für Stufe 2

```json
{
  "version": "2.0",
  "meta": {
    "stage": "regime_config",
    "optimization_score": 78.5,
    "source_file": "regime_optimization_results_BTCUSDT_5m.json"
  },
  "optimized_params": {
    "adx_period": 10,
    "adx_threshold": 17
  },
  "regimes": [
    { "id": "bull", "name": "BULL", "color": "#26a69a", "conditions": {...} },
    { "id": "bear", "name": "BEAR", "color": "#ef5350", "conditions": {...} },
    { "id": "sideways", "name": "SIDEWAYS", "color": "#9e9e9e", "conditions": {...} }
  ]
}
```

---

### STUFE 2: Indikator-Set-Optimierung (pro Regime)

#### 2.1 Ergebnistabelle (`indicator_optimization_results_*_*.json`)

**Zweck:** Alle getesteten Indikator-Kombinationen für EIN Regime

```json
{
  "version": "2.0",
  "meta": {
    "stage": "indicator_optimization",
    "regime": "BULL",
    "regime_config_ref": "optimized_regime_BTCUSDT_5m.json",
    "regime_bars": 180,
    "regime_percentage": 44.9,
    "total_combinations_per_signal": 1200,
    "method": "grid_search"
  },
  "param_ranges": {
    "rsi": { "period": {"min": 7, "max": 21, "step": 2}, "threshold": {"min": 20, "max": 80, "step": 5} },
    "macd": { "fast": {"min": 8, "max": 16, "step": 2}, "slow": {"min": 20, "max": 30, "step": 2} }
  },
  "results": {
    "entry_long": [
      { "rank": 1, "score": 82, "indicator": "RSI", "params": {"period": 9}, "conditions": {...}, "metrics": {...} },
      { "rank": 2, "score": 78, "indicator": "MACD", "params": {...}, "metrics": {...} }
    ],
    "entry_short": [...],
    "exit_long": [...],
    "exit_short": [...]
  }
}
```

#### 2.2 Beste Indikator-Sets (`indicator_sets_*_*.json`)

**Zweck:** Die ausgewählten besten Entry/Exit Signale für EIN Regime

```json
{
  "version": "2.0",
  "meta": {
    "stage": "indicator_sets",
    "regime": "BULL",
    "regime_config_ref": "optimized_regime_BTCUSDT_5m.json",
    "optimization_results_ref": "indicator_optimization_results_BULL_BTCUSDT_5m.json"
  },
  "signal_sets": {
    "entry_long": {
      "enabled": true,
      "selected_rank": 1,
      "indicator": "RSI",
      "params": { "period": 9 },
      "conditions": { "all": [{ "left": {"indicator_id": "rsi9"}, "op": "crosses_above", "right": {"value": 50} }] },
      "metrics": { "trades": 12, "win_rate": 0.75, "profit_factor": 2.4 }
    },
    "entry_short": { "enabled": false },
    "exit_long": { "enabled": true, ... },
    "exit_short": { "enabled": false }
  }
}
```

---

## UI-Workflow

### Tab 1: Regime Setup
- Parameter-Ranges einstellen (oder Auto-Modus)
- Kombinationen-Counter anzeigen
- "Start Regime Optimization" Button

### Tab 2: Regime Results
- Ergebnistabelle aller Kombinationen
- Sortierung nach Score
- Auswahl der besten Config
- "Apply & Continue to Indicator Optimization" Button
- Chart zeigt gewählte Regime-Perioden

### Tab 3: Indicator Setup
- Regime-Auswahl (BULL/BEAR/SIDEWAYS) - einzeln oder alle
- Indikator-Auswahl (RSI, MACD, Stoch, BB, etc.)
- Parameter-Ranges pro Indikator (oder Auto-Modus)
- Signal-Typ Auswahl (Entry-Long, Entry-Short, Exit-Long, Exit-Short)
- "Start Indicator Optimization" Button

### Tab 4: Indicator Results
- Dropdown: Regime wählen (BULL/BEAR/SIDEWAYS)
- 4 Sub-Tabellen: Entry-Long, Entry-Short, Exit-Long, Exit-Short
- Sortierung nach Score
- Auswahl der besten Kombinationen
- "Export Selected" Button

---

## Kompatibilität

Alle JSON-Formate sind kompatibel mit:
- `ConditionEvaluator` (left/op/right Format)
- `RegimeDetector.detect_active_regimes()`
- `IndicatorEngine.calculate()`
- `_draw_regime_lines()` (Farben aus JSON)
