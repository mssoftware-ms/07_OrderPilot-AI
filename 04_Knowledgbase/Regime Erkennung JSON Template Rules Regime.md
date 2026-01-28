# JSON Template Rules - Regime Configuration v2.0

> **Schema Version:** 2.0.0
> **Letzte Aktualisierung:** 2026-01-26
> **Referenzdatei:** `260124_hardcodet_defaults_v2.json`

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Struktur-Übersicht](#struktur-übersicht)
3. [Pflichtfelder](#pflichtfelder)
4. [Optionale Felder](#optionale-felder)
5. [Detaillierte Feldbeschreibungen](#detaillierte-feldbeschreibungen)
6. [Score-Gewichtungen (5-Komponenten System)](#score-gewichtungen-5-komponenten-system)
7. [Regime-Hierarchie (9-Level)](#regime-hierarchie-9-level)
8. [Threshold-Typen](#threshold-typen)
9. [Validierungsregeln](#validierungsregeln)
10. [Beispiele](#beispiele)

---

## Überblick

Das Regime Configuration v2.0 Format definiert:
- **Indikatoren** mit optimierbaren Parametern (ADX, RSI, ATR, etc.)
- **Regime-Definitionen** mit Schwellenwerten und Prioritäten
- **Entry-Parameter** für Signal-Erkennung
- **Evaluation-Parameter** für Backtesting und Scoring

### Wichtige Änderungen zu v1.0
- Generische Indikator-Struktur (max. 10 Parameter pro Indikator)
- Regimes mit dynamischen Thresholds statt fester Felder
- Optimization Range für jeden Parameter
- **NEU: 5-Komponenten Score-System** (Separability, Coherence, Fidelity, Boundary, Coverage)

---

## Struktur-Übersicht

```json
{
  "schema_version": "2.0.0",           // PFLICHT
  "metadata": { ... },                  // PFLICHT
  "optimization_results": [ ... ],      // PFLICHT (min. 1 Eintrag)
  "entry_params": { ... },              // OPTIONAL
  "evaluation_params": { ... }          // OPTIONAL (enthält score_weights)
}
```

---

## Pflichtfelder

### Root-Level Felder

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `schema_version` | `string` | ✅ JA | **MUSS** `"2.0.0"` sein |
| `metadata` | `object` | ✅ JA | Metadaten zur Konfiguration |
| `optimization_results` | `array` | ✅ JA | Min. 1 Optimization Result erforderlich |

### metadata (Pflicht)

| Feld | Typ | Pflicht | Beschreibung | Beispiel |
|------|-----|---------|--------------|----------|
| `author` | `string` | ✅ JA | Ersteller der Config | `"OrderPilot-AI"` |
| `created_at` | `string` | ✅ JA | Erstelldatum (ISO 8601) | `"2026-01-26T00:00:00Z"` |
| `updated_at` | `string` | ✅ JA | Letzte Änderung (ISO 8601) | `"2026-01-26T16:30:00Z"` |
| `tags` | `array[string]` | ❌ NEIN | Kategorisierung/Tags | `["btcusdt", "5min", "scalping"]` |
| `notes` | `string` | ❌ NEIN | Freitext-Beschreibung | `"ADX/DI-based regime..."` |
| `trading_style` | `string` | ❌ NEIN | Trading-Stil | `"Daytrading"`, `"Scalping"`, `"Swing"` |
| `description` | `string` | ❌ NEIN | Strategie-Beschreibung | - |
| `symbol` | `string` | ❌ NEIN | Handelssymbol | `"BTCUSDT"` |
| `timeframe` | `string` | ❌ NEIN | Zeitrahmen | `"5m"`, `"15m"`, `"1h"` |

### optimization_results[*] (Pflicht)

| Feld | Typ | Pflicht | Beschreibung | Beispiel |
|------|-----|---------|--------------|----------|
| `timestamp` | `string` | ✅ JA | ISO 8601 Datum/Zeit | `"2026-01-26T15:00:00Z"` |
| `score` | `number` | ✅ JA | Composite Score (0-100) | `75.5` |
| `trial_number` | `integer` | ✅ JA | Trial-Nummer (min. 1) | `42` |
| `applied` | `boolean` | ✅ JA | `true` = aktive Config | `true` |
| `indicators` | `array` | ✅ JA | Min. 1 Indikator erforderlich | - |
| `regimes` | `array` | ✅ JA | Min. 1 Regime erforderlich | - |

### indicators[*] (Pflicht)

| Feld | Typ | Pflicht | Beschreibung | Beispiel |
|------|-----|---------|--------------|----------|
| `name` | `string` | ✅ JA | Eindeutiger Name, Pattern: `^[A-Z0-9_]+$` | `"STRENGTH_ADX"` |
| `type` | `string` | ✅ JA | Indikator-Typ (siehe erlaubte Werte) | `"ADX"` |
| `params` | `array` | ✅ JA | Min. 1, max. 10 Parameter | - |
| `description` | `string` | ❌ NEIN | Beschreibung des Indikators | `"Trend-Stärke"` |
| `weight` | `number` | ❌ NEIN | Gewichtung (0-1) | `0.40` |

**Erlaubte Indikator-Typen:**
```
Standard:    ADX, RSI, BB, SMA, EMA, MACD, ATR, STOCH, CCI, SUPERTREND, VWAP, OBV
Custom:      CHANDELIER, CKSP, ADX_LEAF_WEST
```

**Custom-Indikatoren (neu in v2.1):**

| Typ | Beschreibung | Parameter |
|-----|--------------|-----------|
| `CHANDELIER` | ATR-basierter Trailing Stop (pipCharlie) | `lookback`, `atr_period`, `multiplier` |
| `CKSP` | Chande Kroll Stop (Alias für CHANDELIER) | `lookback`, `atr_period`, `multiplier` |
| `ADX_LEAF_WEST` | ADX/DMI Variante mit separaten Perioden | `adx_length`, `dmi_length` |

### params[*] (Pflicht)

| Feld | Typ | Pflicht | Beschreibung | Beispiel |
|------|-----|---------|--------------|----------|
| `name` | `string` | ✅ JA | Parameter-Name | `"period"`, `"std_dev"` |
| `value` | `number` | ✅ JA | Aktueller/optimierter Wert | `14` |
| `range` | `object` | ❌ NEIN | Optimierungs-Range | siehe unten |
| `notes` | `string` | ❌ NEIN | Erklärung zum Parameter | `"Scalping: 5-7"` |

### range (Optional, für Optimierung)

| Feld | Typ | Pflicht | Beschreibung | Beispiel |
|------|-----|---------|--------------|----------|
| `min` | `number` | ✅ JA* | Minimum für Optimierung | `10` |
| `max` | `number` | ✅ JA* | Maximum für Optimierung | `25` |
| `step` | `number` | ✅ JA* | Schrittweite (> 0) | `1` |

*Pflicht wenn `range` vorhanden ist

### regimes[*] (Pflicht)

| Feld | Typ | Pflicht | Beschreibung | Beispiel |
|------|-----|---------|--------------|----------|
| `id` | `string` | ✅ JA | Regime-ID, Pattern: `^[A-Z_]+$` | `"STRONG_BULL"` |
| `name` | `string` | ✅ JA | Menschenlesbarer Name | `"Starker Aufwärtstrend"` |
| `thresholds` | `array` | ✅ JA | Min. 1 Threshold erforderlich | - |
| `priority` | `integer` | ✅ JA | 0-100, höher = wird zuerst geprüft | `95` |
| `scope` | `string` | ✅ JA | `"entry"`, `"exit"`, `"in_trade"` | `"entry"` |
| `description` | `string` | ❌ NEIN | Regime-Beschreibung | `"RSI-bestätigt"` |
| `color` | `string` | ❌ NEIN | HEX-Farbcode für UI | `"#16a34a"` |
| `trading_bias` | `string` | ❌ NEIN | Trading-Bias | `"bullish_confirmed"` |
| `recommended_action` | `string` | ❌ NEIN | Empfohlene Aktion | `"Long Entries"` |

### thresholds[*] (Pflicht)

| Feld | Typ | Pflicht | Beschreibung | Beispiel |
|------|-----|---------|--------------|----------|
| `name` | `string` | ✅ JA | Threshold-Name | `"adx_min"` |
| `value` | `number` | ✅ JA | Aktueller Schwellenwert | `25.0` |
| `range` | `object` | ❌ NEIN | Optimierungs-Range | siehe oben |
| `notes` | `string` | ❌ NEIN | Erklärung zum Threshold | `"ADX > 25 = trending"` |

---

## Optionale Felder

### entry_params (Optional)

Parameter für Entry-Signal-Erkennung:

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `pullback_atr` | `number` | `0.8` | ATR-Multiplikator für Pullback-Erkennung |
| `pullback_rsi` | `number` | `45.0` | RSI-Schwelle für Pullback-Entries |
| `wick_reject` | `number` | `0.55` | Wick-Rejection-Ratio (0-1) |
| `bb_entry` | `number` | `0.15` | Bollinger Band Entry-Threshold |
| `rsi_oversold` | `number` | `35.0` | RSI Oversold Level |
| `rsi_overbought` | `number` | `65.0` | RSI Overbought Level |
| `vol_spike_factor` | `number` | `1.2` | Volumen-Spike-Faktor |
| `breakout_atr` | `number` | `0.2` | ATR für Breakout-Bestätigung |
| `min_confidence` | `number` | `0.58` | Mindest-Konfidenz (0-1) |
| `cooldown_bars` | `integer` | `10` | Cooldown in Bars nach Signal |
| `cluster_window_bars` | `integer` | `6` | Cluster-Window für Signal-Gruppierung |
| `min_score` | `integer` | `70` | Mindest-Score für Entry |
| `require_regime_match` | `boolean` | `true` | Regime-Match erforderlich |
| `max_signals_per_regime` | `integer` | `5` | Max. Signale pro Regime |

### evaluation_params (Optional)

Parameter für Backtesting und Scoring:

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `lookback_periods` | `integer` | `200` | Anzahl Bars für Lookback |
| `min_regime_duration` | `integer` | `3` | Mindest-Dauer eines Regimes in Bars |
| `eval_horizon_bars` | `integer` | `40` | Evaluation-Horizont |
| `eval_tp_atr` | `number` | `1.0` | Take-Profit in ATR |
| `eval_sl_atr` | `number` | `0.8` | Stop-Loss in ATR |
| `min_trades_gate` | `integer` | `8` | Min. Trades für Validierung |
| `target_trades_soft` | `integer` | `30` | Ziel-Anzahl Trades |
| `score_weights` | `object` | siehe unten | **5-Komponenten Score-Gewichtungen** |

---

## Score-Gewichtungen (5-Komponenten System)

Das RegimeScore-System bewertet die Qualität der Regime-Erkennung anhand von 5 Komponenten. Die Gewichtungen können in `evaluation_params.score_weights` definiert werden.

### score_weights Struktur

```json
"score_weights": {
  "separability": 0.30,
  "coherence": 0.25,
  "fidelity": 0.25,
  "boundary": 0.10,
  "coverage": 0.10
}
```

### Komponenten-Beschreibungen

| Komponente | Default | Min | Max | Beschreibung |
|------------|---------|-----|-----|--------------|
| `separability` | `0.30` | 0 | 1 | **Cluster-Trennbarkeit** (30%): Wie gut sind die Regimes voneinander getrennt? Basiert auf Silhouette-Score, Calinski-Harabasz und Davies-Bouldin. |
| `coherence` | `0.25` | 0 | 1 | **Zeitliche Kohärenz** (25%): Wie stabil sind die Regimes über die Zeit? Misst Switch-Rate, durchschnittliche Dauer und Markov-Selbstübergänge. |
| `fidelity` | `0.25` | 0 | 1 | **Regime-Treue** (25%): Verhält sich das Regime wie erwartet? Trend-Regimes sollten Hurst > 0.5 haben (trending), Range-Regimes Hurst < 0.5 (mean-reverting). |
| `boundary` | `0.10` | 0 | 1 | **Grenzstärke** (10%): Wie klar sind die Übergänge zwischen Regimes? Basiert auf Mahalanobis-Distanz bei Regime-Wechseln. |
| `coverage` | `0.10` | 0 | 1 | **Abdeckung & Balance** (10%): Wie gleichmäßig sind die Regimes verteilt? Bestraft extreme Dominanz eines einzelnen Regimes. |

### Wichtige Regeln

1. **Summe = 1.0**: Die Summe aller Gewichtungen muss 1.0 ergeben
2. **Automatische Normalisierung**: Falls Summe ≠ 1.0, werden die Werte automatisch normalisiert
3. **Backwards-Compatibility**: Alte Namen werden automatisch gemappt:
   - `regime_distribution` → `coverage`
   - `regime_stability` → `coherence`
   - `indicator_quality` → `fidelity`

### Beispiel-Anpassungen

**Für Trending-Märkte** (z.B. starke Crypto-Trends):
```json
"score_weights": {
  "separability": 0.35,
  "coherence": 0.20,
  "fidelity": 0.25,
  "boundary": 0.10,
  "coverage": 0.10
}
```

**Für Range-Bound Märkte**:
```json
"score_weights": {
  "separability": 0.25,
  "coherence": 0.30,
  "fidelity": 0.20,
  "boundary": 0.15,
  "coverage": 0.10
}
```

---

## Regime-Hierarchie (9-Level)

Die Regimes werden nach **Priority** (absteigend) **sortiert**. Höhere Priority = höhere Relevanz.

⚠️ **KORREKTUR (2026-01-27):** Priority bestimmt **NICHT** die Evaluierungs-Reihenfolge!
**Alle Regimes werden immer evaluiert.** Priority dient nur zur Sortierung aktiver Regimes.

| Priority | Regime ID | Name | Beschreibung |
|----------|-----------|------|--------------|
| **100** | `STRONG_TF` | Extremer Trend | ADX > 35-40, DI-Diff > 15-20 |
| **95** | `STRONG_BULL` | Starker Aufwärtstrend | RSI > 55 bestätigt, DI+ > DI- |
| **94** | `STRONG_BEAR` | Starker Abwärtstrend | RSI < 45 bestätigt, DI- > DI+ |
| **85** | `TF` | Trend Following | ADX > 22-25, moderate DI-Diff |
| **82** | `BULL_EXHAUSTION` | Bull Erschöpfung | DI+ > DI- aber RSI < 40 (Warnung) |
| **81** | `BEAR_EXHAUSTION` | Bear Erschöpfung | DI- > DI+ aber RSI > 60 (Warnung) |
| **80** | `BULL` | Aufwärtstrend | DI+ > DI-, ohne RSI-Bestätigung |
| **79** | `BEAR` | Abwärtstrend | DI- > DI+, ohne RSI-Bestätigung |
| **50** | `SIDEWAYS` | Seitwärts/Range | ADX < 18-20 |

### Auswertungslogik

⚠️ **WICHTIG: Multi-Regime System** - Mehrere Regimes können **gleichzeitig aktiv** sein!

```python
# Tatsächliche Implementierung (src/core/tradingbot/config/detector.py)
# ALLE Regimes werden evaluiert (kein Early-Exit!)

active_regimes = []

1. Für JEDES Regime in der Config:
   a. Prüfe ALLE Thresholds des Regimes
   b. Wenn ALLE Thresholds erfüllt → Füge zu active_regimes hinzu
   # KEIN STOP! Weiter mit nächstem Regime

2. Sortiere active_regimes nach Priority (absteigend)

3. Return ALLE aktiven Regimes als Liste

# Beispiel: Mehrere Regimes gleichzeitig aktiv
# Input: ADX=32, DI+>DI-, RSI=58
# Output: [
#   ActiveRegime(id='STRONG_BULL', priority=95),  # RSI > 55
#   ActiveRegime(id='TF', priority=85),           # ADX > 25
#   ActiveRegime(id='BULL', priority=80)          # DI+ > DI-
# ]
```

**WICHTIG - Unterschiede zu Early-Exit Pattern:**
- ❌ **KEIN** Early-Exit / STOP bei erstem Match
- ✅ **ALLE** Regimes werden immer evaluiert
- ✅ **Mehrere** Regimes können gleichzeitig aktiv sein
- ✅ Priority bestimmt nur die **Sortierung**, nicht die Evaluierung
- ✅ Downstream-Consumer (Router, Executor) entscheiden, welches Regime verwendet wird

**Design-Rationale:**
Das Multi-Regime System erlaubt:
- Gleichzeitige Trend-Stärke + Richtungs-Signale (z.B. STRONG_BULL + TF + BULL)
- Warnsignale parallel zu Haupt-Regime (z.B. BULL_EXHAUSTION + BULL)
- Flexible Strategie-Auswahl durch Router basierend auf ALLEN aktiven Regimes

---

## Threshold-Typen

### ADX-basierte Thresholds

| Name | Typ | Beschreibung | Typische Werte |
|------|-----|--------------|----------------|
| `adx_min` | `_min` | Minimum ADX für Trend-Stärke | 18-40 |
| `adx_max` | `_max` | Maximum ADX für Range-Erkennung | 15-25 |

### DI-Differenz Thresholds

| Name | Typ | Beschreibung | Typische Werte |
|------|-----|--------------|----------------|
| `di_diff_min` | `_min` | Minimum DI+ - DI- Differenz | 3-20 |

**Wichtig:** Bei BULL-Regimes muss `DI+ - DI- > Threshold` gelten, bei BEAR-Regimes `DI- - DI+ > Threshold`.

### RSI-Bestätigung Thresholds

| Name | Typ | Beschreibung | Typische Werte |
|------|-----|--------------|----------------|
| `rsi_confirm_bull` | custom | RSI muss > Wert sein für Bull | 50-65 |
| `rsi_confirm_bear` | custom | RSI muss < Wert sein für Bear | 35-50 |
| `rsi_strong_bull` | custom | Starke Bull-Bestätigung | 55-70 |
| `rsi_strong_bear` | custom | Starke Bear-Bestätigung | 30-45 |

### RSI-Exhaustion Thresholds (Trendwende-Warnung)

| Name | Typ | Beschreibung | Typische Werte |
|------|-----|--------------|----------------|
| `rsi_exhaustion_max` | custom | RSI < Wert während Bull = Erschöpfung | 35-45 |
| `rsi_exhaustion_min` | custom | RSI > Wert während Bear = Erschöpfung | 55-65 |

### ATR-Bewegung Thresholds

| Name | Typ | Beschreibung | Typische Werte |
|------|-----|--------------|----------------|
| `extreme_move_pct` | custom | Prozentuale Preisbewegung für Extremfall | 2.0-5.0 |
| `strong_move_pct` | custom | Prozentuale Preisbewegung für starke Bewegung | 0.5-3.0 |

### Chandelier Stop Thresholds (Custom-Indikator)

| Name | Typ | Beschreibung | Typische Werte |
|------|-----|--------------|----------------|
| `chandelier_direction_eq` | custom | Richtungsgleichheit: 1=bullish, -1=bearish | 1, -1 |
| `chandelier_color_change` | custom | Farbwechsel: 1=Wechsel erkannt, 0=kein Wechsel | 0, 1 |
| `chandelier_above` | `_above` | Chandelier über Schwellenwert | - |
| `chandelier_below` | `_below` | Chandelier unter Schwellenwert | - |

### Generische Threshold-Suffixe (Dynamisch)

Diese Suffixe können mit **jedem Indikator-Typ** kombiniert werden:

| Suffix | Beschreibung | Beispiel |
|--------|--------------|----------|
| `_min` | Wert muss >= Threshold sein | `adx_min`, `chandelier_min` |
| `_max` | Wert muss < Threshold sein | `adx_max`, `rsi_max` |
| `_above` | Wert muss > Threshold sein | `ema_above`, `sma_above` |
| `_below` | Wert muss < Threshold sein | `bb_below` |
| `_direction_eq` | Richtung muss gleich sein (1/-1) | `chandelier_direction_eq` |
| `_color_change` | Farbwechsel erkannt (0/1) | `chandelier_color_change` |

---

## Validierungsregeln

### Schema-Validierung

1. `schema_version` **MUSS** exakt `"2.0.0"` sein
2. `optimization_results` **MUSS** mindestens 1 Element enthalten
3. Jeder Indikator **MUSS** `name`, `type`, `params` haben
4. Jedes Regime **MUSS** `id`, `name`, `priority`, `scope`, `thresholds` haben
5. Jeder Threshold **MUSS** `name` und `value` haben

### Naming-Conventions

| Feld | Pattern | Beispiele |
|------|---------|-----------|
| `indicators[*].name` | `^[A-Z0-9_]+$` | `STRENGTH_ADX`, `MOMENTUM_RSI` |
| `regimes[*].id` | `^[A-Z_]+$` | `STRONG_TF`, `BULL_EXHAUSTION` |

### Wertebereiche

| Feld | Min | Max |
|------|-----|-----|
| `score` | 0 | 100 |
| `priority` | 0 | 100 |
| `trial_number` | 1 | - |
| `params[*].range.step` | > 0 | - |
| `score_weights.*` | 0 | 1 |

### Scope-Werte

```
"entry"    - Für Entry-Signale
"exit"     - Für Exit-Signale
"in_trade" - Während offener Position
```

---

## Beispiele

### Minimales gültiges JSON

```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "author": "OrderPilot-AI",
    "created_at": "2026-01-26T00:00:00Z",
    "updated_at": "2026-01-26T00:00:00Z"
  },
  "optimization_results": [
    {
      "timestamp": "2026-01-26T12:00:00Z",
      "score": 75.5,
      "trial_number": 1,
      "applied": true,
      "indicators": [
        {
          "name": "STRENGTH_ADX",
          "type": "ADX",
          "params": [
            {"name": "period", "value": 14}
          ]
        }
      ],
      "regimes": [
        {
          "id": "BULL",
          "name": "Bullish",
          "thresholds": [{"name": "adx_min", "value": 25}],
          "priority": 90,
          "scope": "entry"
        },
        {
          "id": "SIDEWAYS",
          "name": "Range",
          "thresholds": [{"name": "adx_max", "value": 20}],
          "priority": 50,
          "scope": "entry"
        }
      ]
    }
  ]
}
```

### Vollständiges Beispiel mit Score-Gewichtungen

```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "author": "OrderPilot-AI",
    "created_at": "2026-01-26T00:00:00Z",
    "updated_at": "2026-01-26T00:00:00Z",
    "tags": ["btcusdt", "5min", "scalping"],
    "trading_style": "Scalping",
    "symbol": "BTCUSDT",
    "timeframe": "5m"
  },
  "optimization_results": [
    {
      "timestamp": "2026-01-26T12:00:00Z",
      "score": 82.3,
      "trial_number": 15,
      "applied": true,
      "indicators": [
        {
          "name": "STRENGTH_ADX",
          "type": "ADX",
          "params": [
            {"name": "period", "value": 14, "range": {"min": 10, "max": 20, "step": 1}}
          ]
        },
        {
          "name": "MOMENTUM_RSI",
          "type": "RSI",
          "params": [
            {"name": "period", "value": 14, "range": {"min": 9, "max": 21, "step": 1}}
          ]
        },
        {
          "name": "VOLATILITY_ATR",
          "type": "ATR",
          "params": [
            {"name": "period", "value": 14, "range": {"min": 10, "max": 20, "step": 1}}
          ]
        }
      ],
      "regimes": [
        {
          "id": "STRONG_TF",
          "name": "Strong Trend",
          "thresholds": [
            {"name": "adx_min", "value": 40.0},
            {"name": "di_diff_min", "value": 20.0}
          ],
          "priority": 100,
          "scope": "entry"
        },
        {
          "id": "STRONG_BULL",
          "name": "Strong Bull (RSI confirmed)",
          "thresholds": [
            {"name": "adx_min", "value": 25.0},
            {"name": "di_diff_min", "value": 8.0},
            {"name": "rsi_confirm_bull", "value": 55.0}
          ],
          "priority": 95,
          "scope": "entry"
        },
        {
          "id": "SIDEWAYS",
          "name": "Range",
          "thresholds": [
            {"name": "adx_max", "value": 20.0}
          ],
          "priority": 50,
          "scope": "entry"
        }
      ]
    }
  ],
  "entry_params": {
    "min_confidence": 0.6,
    "cooldown_bars": 5
  },
  "evaluation_params": {
    "lookback_periods": 200,
    "min_regime_duration": 3,
    "score_weights": {
      "separability": 0.30,
      "coherence": 0.25,
      "fidelity": 0.25,
      "boundary": 0.10,
      "coverage": 0.10
    }
  }
}
```

### Beispiel: Chandelier Stop + ADX Leaf West (2-Indikator Setup)

Dieses Beispiel zeigt ein minimales Setup mit nur 2 Custom-Indikatoren (ohne RSI/Standard-ADX):

```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "author": "OrderPilot-AI",
    "created_at": "2026-01-26T00:00:00Z",
    "updated_at": "2026-01-26T00:00:00Z",
    "tags": ["btcusdt", "5min", "chandelier", "leaf-west"],
    "trading_style": "Scalping",
    "notes": "Chandelier Stop (pipCharlie) + ADX Leaf West Style für Regime-Erkennung",
    "symbol": "BTCUSDT",
    "timeframe": "5m"
  },
  "optimization_results": [
    {
      "timestamp": "2026-01-26T12:00:00Z",
      "score": 78.5,
      "trial_number": 1,
      "applied": true,
      "indicators": [
        {
          "name": "DIRECTION_CHANDELIER",
          "type": "CHANDELIER",
          "description": "Chandelier Stop (pipCharlie) - ATR-basierter Trailing Stop",
          "params": [
            {"name": "lookback", "value": 22, "range": {"min": 15, "max": 30, "step": 1}},
            {"name": "atr_period", "value": 22, "range": {"min": 14, "max": 28, "step": 1}},
            {"name": "multiplier", "value": 3.0, "range": {"min": 2.0, "max": 4.0, "step": 0.5}}
          ]
        },
        {
          "name": "STRENGTH_ADX_LW",
          "type": "ADX_LEAF_WEST",
          "description": "ADX Leaf West Style - Schnellere ADX/DMI Variante",
          "params": [
            {"name": "adx_length", "value": 8, "range": {"min": 5, "max": 12, "step": 1}},
            {"name": "dmi_length", "value": 9, "range": {"min": 7, "max": 14, "step": 1}}
          ]
        }
      ],
      "regimes": [
        {
          "id": "BULL_ENTRY",
          "name": "Bullish Entry (Chandelier + ADX)",
          "description": "Chandelier bullish + ADX bestätigt Trend (nicht zu stark)",
          "thresholds": [
            {"name": "chandelier_direction_eq", "value": 1, "notes": "Chandelier bullish (grün)"},
            {"name": "chandelier_color_change", "value": 1, "notes": "Farbwechsel = Entry-Trigger"},
            {"name": "adx_below", "value": 35, "notes": "ADX < 35 = noch nicht überkauft"}
          ],
          "priority": 95,
          "scope": "entry",
          "color": "#16a34a",
          "trading_bias": "bullish_confirmed"
        },
        {
          "id": "BEAR_ENTRY",
          "name": "Bearish Entry (Chandelier + ADX)",
          "description": "Chandelier bearish + ADX bestätigt Trend",
          "thresholds": [
            {"name": "chandelier_direction_eq", "value": -1, "notes": "Chandelier bearish (rot)"},
            {"name": "chandelier_color_change", "value": 1, "notes": "Farbwechsel = Entry-Trigger"},
            {"name": "adx_below", "value": 35}
          ],
          "priority": 94,
          "scope": "entry",
          "color": "#dc2626",
          "trading_bias": "bearish_confirmed"
        },
        {
          "id": "TREND_FOLLOW",
          "name": "Trend Following (ohne Farbwechsel)",
          "description": "Starker Trend, kein Farbwechsel erforderlich",
          "thresholds": [
            {"name": "adx_min", "value": 25, "notes": "ADX > 25 = trending"},
            {"name": "di_diff_min", "value": 8}
          ],
          "priority": 80,
          "scope": "entry",
          "color": "#2563eb"
        },
        {
          "id": "SIDEWAYS",
          "name": "Seitwärts / Kein Handel",
          "description": "ADX zu niedrig für Entry",
          "thresholds": [
            {"name": "adx_max", "value": 20}
          ],
          "priority": 50,
          "scope": "entry",
          "color": "#6b7280"
        }
      ]
    }
  ],
  "evaluation_params": {
    "lookback_periods": 200,
    "min_regime_duration": 3,
    "score_weights": {
      "separability": 0.30,
      "coherence": 0.25,
      "fidelity": 0.25,
      "boundary": 0.10,
      "coverage": 0.10
    }
  }
}
```

**Entry-Logik:**
1. **Chandelier Farbwechsel** (grün → rot oder rot → grün) = Richtungswechsel erkannt
2. **ADX < 35** = Trend noch nicht überkauft/überverkauft
3. Kombiniert: Chandelier gibt Richtung, ADX bestätigt Timing

---

## Referenzen

- **Schema-Datei:** `v2_schema_reference.json`
- **Template-Config:** `260124_hardcodet_defaults_v2.json`
- **Loader-Code:** `src/analysis/visible_chart/params_loader.py`
- **Scoring-Code:** `src/core/scoring/regime_score.py`
- **Indicator Calculation:** `src/core/regime_optimizer.py`

---

*Erstellt von OrderPilot-AI | Schema Version 2.0.0 | Aktualisiert 2026-01-26*
