# JSON Template Rules - Regime Configuration v2.0

> **Schema Version:** 2.0.0
> **Letzte Aktualisierung:** 2026-01-25
> **Referenzdatei:** `260124_hardcodet_defaults_v2.json`

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Struktur-Übersicht](#struktur-übersicht)
3. [Pflichtfelder](#pflichtfelder)
4. [Optionale Felder](#optionale-felder)
5. [Detaillierte Feldbeschreibungen](#detaillierte-feldbeschreibungen)
6. [Regime-Hierarchie (9-Level)](#regime-hierarchie-9-level)
7. [Validierungsregeln](#validierungsregeln)
8. [Beispiele](#beispiele)

---

## Überblick

Das Regime Configuration v2.0 Format definiert:
- **Indikatoren** mit optimierbaren Parametern (ADX, RSI, ATR, etc.)
- **Regime-Definitionen** mit Schwellenwerten und Prioritäten
- **Entry-Parameter** für Signal-Erkennung
- **Evaluation-Parameter** für Backtesting

### Wichtige Änderungen zu v1.0
- Generische Indikator-Struktur (max. 10 Parameter pro Indikator)
- Regimes mit dynamischen Thresholds statt fester Felder
- Optimization Range für jeden Parameter

---

## Struktur-Übersicht

```
{
  "schema_version": "2.0.0",           // PFLICHT
  "metadata": { ... },                  // OPTIONAL
  "optimization_results": [ ... ],      // PFLICHT (min. 1 Eintrag)
  "entry_params": { ... },              // OPTIONAL
  "evaluation_params": { ... }          // OPTIONAL
}
```

---

## Pflichtfelder

### Root-Level

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `schema_version` | `string` | **MUSS** `"2.0.0"` sein |
| `optimization_results` | `array` | Min. 1 Optimization Result erforderlich |

### optimization_results[*] (Pflicht)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `timestamp` | `string` | ISO 8601 Datum/Zeit (z.B. `"2026-01-25T15:00:00Z"`) |
| `score` | `number` | Composite Score (0-100) |
| `trial_number` | `integer` | Trial-Nummer (min. 1) |
| `applied` | `boolean` | `true` wenn aktiv |
| `indicators` | `array` | Min. 1 Indikator erforderlich |

### indicators[*] (Pflicht)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | `string` | Eindeutiger Name, Pattern: `^[A-Z0-9_]+$` |
| `type` | `string` | Indikator-Typ (siehe erlaubte Werte) |
| `params` | `array` | Min. 1, max. 10 Parameter |

**Erlaubte Indikator-Typen:**
```
ADX, RSI, BB, SMA, EMA, MACD, ATR, STOCH, CCI, SUPERTREND, VWAP, OBV
```

### params[*] (Pflicht)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | `string` | Parameter-Name (z.B. `"period"`, `"std_dev"`) |
| `value` | `number\|boolean` | Aktueller/optimierter Wert |

### regimes[*] (Pflicht wenn vorhanden)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | `string` | Regime-ID, Pattern: `^[A-Z_]+$` |
| `name` | `string` | Menschenlesbarer Name |
| `priority` | `integer` | 0-100, höher = wird zuerst ausgewertet |
| `scope` | `string` | `"entry"`, `"exit"`, oder `"in_trade"` |

### thresholds[*] (Pflicht wenn vorhanden)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | `string` | Threshold-Name (z.B. `"adx_min"`, `"rsi_confirm_bull"`) |
| `value` | `number` | Aktueller Schwellenwert |

---

## Optionale Felder

### metadata (Optional)

| Feld | Typ | Beschreibung | Beispiel |
|------|-----|--------------|----------|
| `author` | `string` | Ersteller | `"OrderPilot-AI"` |
| `created_at` | `string` | Erstelldatum (ISO 8601) | `"2026-01-24T00:00:00Z"` |
| `updated_at` | `string` | Letzte Änderung (ISO 8601) | `"2026-01-25T16:30:00Z"` |
| `tags` | `array[string]` | Kategorisierung | `["daytrading", "adx-based"]` |
| `notes` | `string` | Freitext-Beschreibung | `"ADX/DI-based Regime..."` |
| `trading_style` | `string` | Trading-Ansatz | `"Daytrading"`, `"Scalping"`, `"Swing Trading"` |
| `description` | `string` | Strategie-Beschreibung | - |

### range (Optional, für Optimierung)

Kann bei `params[*]` und `thresholds[*]` hinzugefügt werden:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `min` | `number` | Minimum für Optimierung |
| `max` | `number` | Maximum für Optimierung |
| `step` | `number` | Schrittweite (muss > 0 sein) |

### entry_params (Optional)

Freie Struktur für Entry-Signal-Parameter:

| Feld | Typ | Beschreibung | Default |
|------|-----|--------------|---------|
| `pullback_atr` | `number` | ATR-Multiplikator für Pullback | 0.8 |
| `pullback_rsi` | `number` | RSI-Schwelle für Pullback | 45.0 |
| `wick_reject` | `number` | Wick-Rejection-Ratio | 0.55 |
| `bb_entry` | `number` | BB-Entry-Threshold | 0.15 |
| `rsi_oversold` | `number` | RSI Oversold Level | 35.0 |
| `rsi_overbought` | `number` | RSI Overbought Level | 65.0 |
| `vol_spike_factor` | `number` | Volumen-Spike-Faktor | 1.2 |
| `breakout_atr` | `number` | ATR für Breakout | 0.2 |
| `min_confidence` | `number` | Mindest-Konfidenz | 0.58 |
| `cooldown_bars` | `integer` | Cooldown in Bars | 10 |
| `cluster_window_bars` | `integer` | Cluster-Window | 6 |

### evaluation_params (Optional)

Freie Struktur für Backtesting/Evaluation:

| Feld | Typ | Beschreibung | Default |
|------|-----|--------------|---------|
| `eval_horizon_bars` | `integer` | Evaluation-Horizont | 40 |
| `eval_tp_atr` | `number` | Take-Profit in ATR | 1.0 |
| `eval_sl_atr` | `number` | Stop-Loss in ATR | 0.8 |
| `min_trades_gate` | `integer` | Min. Trades für Validierung | 8 |
| `target_trades_soft` | `integer` | Ziel-Anzahl Trades | 30 |

---

## Detaillierte Feldbeschreibungen

### Indikatoren

#### ADX (Average Directional Index)
```json
{
  "name": "STRENGTH_ADX",
  "type": "ADX",
  "params": [
    {"name": "period", "value": 14, "range": {"min": 10, "max": 25, "step": 1}},
    {"name": "di_diff_threshold", "value": 5.0, "range": {"min": 3, "max": 15, "step": 1}}
  ]
}
```

#### RSI (Relative Strength Index)
```json
{
  "name": "MOMENTUM_RSI",
  "type": "RSI",
  "params": [
    {"name": "period", "value": 14, "range": {"min": 9, "max": 21, "step": 1}}
  ]
}
```

#### ATR (Average True Range)
```json
{
  "name": "VOLATILITY_ATR",
  "type": "ATR",
  "params": [
    {"name": "period", "value": 14, "range": {"min": 10, "max": 20, "step": 1}},
    {"name": "strong_move_pct", "value": 1.5, "range": {"min": 0.5, "max": 3.0, "step": 0.1}},
    {"name": "extreme_move_pct", "value": 3.0, "range": {"min": 2.0, "max": 5.0, "step": 0.5}}
  ]
}
```

### Threshold-Namen (Konvention)

| Name | Beschreibung | Verwendung |
|------|--------------|------------|
| `adx_min` | Minimum ADX-Wert | Trend-Stärke |
| `adx_max` | Maximum ADX-Wert | Range-Erkennung |
| `di_diff_min` | Minimum DI+ - DI- | Trend-Richtung |
| `rsi_confirm_bull` | RSI für Bull-Bestätigung | > Wert = bullish |
| `rsi_confirm_bear` | RSI für Bear-Bestätigung | < Wert = bearish |
| `rsi_exhaustion_max` | RSI Erschöpfung (Bull) | Trendwende-Warnung |
| `rsi_exhaustion_min` | RSI Erschöpfung (Bear) | Trendwende-Warnung |

---

## Regime-Hierarchie (9-Level)

Die Regimes werden nach **Priority** (absteigend) ausgewertet. Höhere Priority = wird zuerst geprüft.

| Priority | Regime ID | Name | Beschreibung |
|----------|-----------|------|--------------|
| **100** | `STRONG_TF` | Extremer Trend | ADX > 40, DI-Diff > 20 |
| **95** | `STRONG_BULL` | Starker Aufwärtstrend | RSI > 55 bestätigt |
| **94** | `STRONG_BEAR` | Starker Abwärtstrend | RSI < 45 bestätigt |
| **85** | `TF` | Trend Following | ADX > 25, DI-Diff > 8 |
| **82** | `BULL_EXHAUSTION` | Bull Erschöpfung | RSI < 40 (Trendwende-Warnung) |
| **81** | `BEAR_EXHAUSTION` | Bear Erschöpfung | RSI > 60 (Trendwende-Warnung) |
| **80** | `BULL` | Aufwärtstrend | DI+ > DI- |
| **79** | `BEAR` | Abwärtstrend | DI- > DI+ |
| **50** | `SIDEWAYS` | Seitwärts/Range | ADX < 20 |

### Auswertungslogik

```
1. Sortiere Regimes nach Priority (absteigend)
2. Für jedes Regime:
   a. Prüfe alle Thresholds
   b. Wenn alle erfüllt → Regime aktiv, STOP
3. Fallback: SIDEWAYS (niedrigste Priority)
```

---

## Validierungsregeln

### Schema-Validierung

1. `schema_version` **MUSS** exakt `"2.0.0"` sein
2. `optimization_results` **MUSS** mindestens 1 Element enthalten
3. Jeder Indikator **MUSS** `name`, `type`, `params` haben
4. Jedes Regime **MUSS** `id`, `name`, `priority`, `scope` haben

### Naming-Conventions

| Feld | Pattern | Beispiele |
|------|---------|-----------|
| `indicators[*].name` | `^[A-Z0-9_]+$` | `STRENGTH_ADX`, `RSI1` |
| `regimes[*].id` | `^[A-Z_]+$` | `STRONG_TF`, `BULL_EXHAUSTION` |

### Wertebereiche

| Feld | Min | Max |
|------|-----|-----|
| `score` | 0 | 100 |
| `priority` | 0 | 100 |
| `trial_number` | 1 | - |
| `params[*].range.step` | > 0 | - |

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
  "optimization_results": [
    {
      "timestamp": "2026-01-25T12:00:00Z",
      "score": 75.5,
      "trial_number": 1,
      "applied": true,
      "indicators": [
        {
          "name": "ADX1",
          "type": "ADX",
          "params": [
            {"name": "period", "value": 14}
          ]
        }
      ]
    }
  ]
}
```

### Vollständiges Beispiel mit Regimes

```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "author": "OrderPilot-AI",
    "created_at": "2026-01-25T00:00:00Z",
    "tags": ["btc", "5min", "scalping"],
    "trading_style": "Scalping"
  },
  "optimization_results": [
    {
      "timestamp": "2026-01-25T12:00:00Z",
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
            {"name": "period", "value": 14}
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
  }
}
```

---

## Referenzen

- **Schema-Datei:** `config/schemas/regime_optimization/optimized_regime_config_v2.schema.json`
- **Referenz-Config:** `03_JSON/Entry_Analyzer/Regime/260124_hardcodet_defaults_v2.json`
- **Loader-Code:** `src/analysis/visible_chart/params_loader.py`

---

*Erstellt von OrderPilot-AI | Schema Version 2.0.0*
