# Regime Configuration v2.0 - Ausführliche Dokumentation

**Datei:** `260124_empty_template.json`
**Schema Version:** 2.0.0
**Datum:** 2026-01-24
**Zweck:** Leeres Template für Regime-Konfiguration mit Optimierungsparametern

---

## 📋 Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Schema Version](#schema-version)
3. [Metadata](#metadata)
4. [Optimization Results](#optimization-results)
5. [Indicators](#indicators)
6. [Regimes](#regimes)
7. [Entry Params](#entry-params)
8. [Evaluation Params](#evaluation-params)
9. [Unterstützte Indikatoren](#unterstützte-indikatoren)
10. [Verwendungsbeispiele](#verwendungsbeispiele)

---

## Überblick

Diese JSON-Datei definiert die Konfiguration für **Regime Detection** (Marktphasen-Erkennung) im Entry Analyzer. Sie enthält:

- **Indikatoren** mit ihren Parametern und Optimierungsbereichen
- **Regimes** (Marktphasen) mit Erkennungs-Schwellenwerten
- **Entry-Parameter** für Signal-Generierung
- **Evaluations-Parameter** für Backtesting

### Was macht diese Datei?

1. **Regime Setup Tab**: Zeigt Indikatoren und deren Parameter-Ranges in **52-Spalten-Tabelle**
2. **Regime Optimization Tab**: Verwendet diese Ranges für **Optuna TPE-Optimierung**
3. **Analyze Visible Range**: Verwendet optimierte Parameter für Regime-Erkennung
4. **Trading Bot**: Importiert finale optimierte Parameter für Live-Handel

---

## Schema Version

```json
"schema_version": "2.0.0"
```

**Typ:** `string`
**Wert:** `"2.0.0"` (fix)
**Pflicht:** ✅ Ja

### Bedeutung:
- Definiert das Format dieser JSON-Datei
- **v2.0** = Generische Parameterstruktur (bis zu 10 Parameter pro Indikator)
- **v1.0** = Alte hardcoded Struktur (deprecated)

### Unterschiede v1.0 vs v2.0:

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Parameter-Struktur | `indicators[].params` (dict) | `optimization_results[].indicators[].params` (array) |
| Max Parameter/Indikator | Fest (1-3) | Flexibel (1-10) |
| Indikatoren-Namen | `adx14`, `rsi14`, `bb20` | `ADX1`, `RSI1`, `BB1` |
| UI-Darstellung | 6 Spalten (hardcoded) | 52 Spalten (dynamisch) |
| Backward Compatibility | - | ✅ Auto-Konvertierung |

---

## Metadata

```json
"metadata": {
  "author": "OrderPilot-AI",
  "created_at": "2026-01-24T00:00:00Z",
  "updated_at": "2026-01-24T00:00:00Z",
  "tags": ["entry-analyzer", "regime", "template"],
  "notes": "Empty template for v2.0 regime configuration."
}
```

**Typ:** `object`
**Pflicht:** ❌ Optional

### Felder:

| Feld | Typ | Beschreibung | Beispiel |
|------|-----|--------------|----------|
| `author` | string | Ersteller der Konfiguration | `"OrderPilot-AI"`, `"John Doe"` |
| `created_at` | string (ISO 8601) | Erstellungszeitpunkt | `"2026-01-24T20:33:23Z"` |
| `updated_at` | string (ISO 8601) | Letzte Änderung | `"2026-01-24T20:33:23Z"` |
| `tags` | array[string] | Kategorisierung | `["regime", "btc", "5m"]` |
| `notes` | string | Freitext-Notizen | `"Best config for BTC 5m"` |

### Verwendung:
- **GUI**: Wird in Tooltips und Info-Dialogen angezeigt
- **Export**: Automatisch ausgefüllt beim Export
- **Import**: Wird gelesen, aber nicht zwingend validiert

---

## Optimization Results

```json
"optimization_results": [
  {
    "timestamp": "2026-01-24T20:33:23Z",
    "score": 81.0,
    "trial_number": 1,
    "applied": true,
    "indicators": [...],
    "regimes": [...]
  }
]
```

**Typ:** `array`
**Pflicht:** ✅ Ja (min. 1 Element)

### Struktur:

Jedes Element im Array repräsentiert **ein Optimierungsergebnis** (einen Trial von Optuna).

### Felder:

| Feld | Typ | Beschreibung | Pflicht |
|------|-----|--------------|---------|
| `timestamp` | string (ISO 8601) | Wann dieser Trial durchgeführt wurde | ✅ |
| `score` | number (0-100) | Composite Score (höher = besser) | ✅ |
| `trial_number` | integer (≥1) | Trial-Nummer in Optimierungslauf | ✅ |
| `applied` | boolean | Ist dieser Trial aktuell aktiv? | ✅ |
| `indicators` | array | Liste der Indikatoren mit Parametern | ✅ |
| `regimes` | array | Liste der Regimes mit Schwellenwerten | ❌ |

### Score-Berechnung:

Der **Score** ist ein Composite Score (0-100) basierend auf:
- **F1-Scores** für Bull/Bear/Sideways Erkennung (30%)
- **Regime Stability** (wenige Wechsel) (20%)
- **Regime Coverage** (alle Bars klassifiziert) (20%)
- **Durchschnittliche Regime-Dauer** (15%)
- **Anzahl erkannter Regimes** (15%)

**Formel:**
```python
score = (
    0.30 * (f1_bull + f1_bear + f1_sideways) / 3 +
    0.20 * stability_score +
    0.20 * coverage +
    0.15 * (1 - min(switch_count / bar_count, 1)) +
    0.15 * (avg_duration_bars / target_duration)
) * 100
```

### `applied` Flag:

- **`true`**: Dieser Trial ist **aktuell aktiv** und wird von "Analyze Visible Range" verwendet
- **`false`**: Dieser Trial ist **historisch** (nur zur Referenz)

⚠️ **Wichtig:** Nur **EIN** Trial sollte `applied: true` haben!

### Verwendung:

1. **Regime Setup Tab**: Zeigt den **aktiven Trial** (`applied: true`) in der oberen Tabelle
2. **Regime Optimization Tab**: Fügt **neue Trials** zu diesem Array hinzu
3. **Regime Results Tab**: Zeigt **alle Trials** sortiert nach Score
4. **Analyze Visible Range**: Liest **nur den aktiven Trial** (`applied: true`)

---

## Indicators

```json
"indicators": [
  {
    "name": "ADX1",
    "type": "ADX",
    "params": [
      {
        "name": "period",
        "value": 10,
        "range": {
          "min": 7,
          "max": 21,
          "step": 1
        }
      }
    ]
  }
]
```

**Pfad:** `optimization_results[].indicators[]`
**Typ:** `array`
**Pflicht:** ✅ Ja (min. 1 Indikator)

### Struktur:

Jeder Indikator hat:
- **Name** (eindeutig, z.B. `ADX1`, `RSI1`, `BB1`)
- **Type** (Indikator-Typ aus Enum)
- **Params** (bis zu 10 Parameter)

### Felder:

| Feld | Typ | Beschreibung | Pflicht | Pattern |
|------|-----|--------------|---------|---------|
| `name` | string | Eindeutiger Name | ✅ | `^[A-Z0-9_]+$` |
| `type` | string | Indikator-Typ | ✅ | Siehe [Unterstützte Indikatoren](#unterstützte-indikatoren) |
| `params` | array | Parameter-Liste | ✅ | 1-10 Elemente |

### Parameter-Struktur:

```json
{
  "name": "period",
  "value": 14,
  "range": {
    "min": 7,
    "max": 21,
    "step": 1
  }
}
```

| Feld | Typ | Beschreibung | Beispiel |
|------|-----|--------------|----------|
| `name` | string | Parameter-Name | `"period"`, `"std_dev"`, `"multiplier"` |
| `value` | number/int/bool | Aktueller/optimierter Wert | `14`, `2.0`, `true` |
| `range.min` | number | Minimum für Optimierung | `7` |
| `range.max` | number | Maximum für Optimierung | `21` |
| `range.step` | number | Schrittweite für Optimierung | `1`, `0.1` |

### Namens-Konvention:

**Format:** `<TYPE><NUMBER>`

- **TYPE**: Indikator-Typ in Großbuchstaben (ADX, RSI, BB, SMA, EMA)
- **NUMBER**: Laufende Nummer (1, 2, 3, ...)

**Beispiele:**
- `ADX1`, `ADX2` (zwei ADX mit unterschiedlichen Perioden)
- `RSI1`, `RSI2`, `RSI3` (drei RSI-Indikatoren)
- `SMA_FAST1`, `SMA_SLOW1` (Fast/Slow SMA mit beschreibendem Prefix)

⚠️ **Wichtig:**
- Namen müssen **eindeutig** sein innerhalb eines Trials
- Empfehlung: Beschreibende Namen für mehrere Indikatoren desselben Typs
- **KEINE** Period im Namen (nicht `ADX14`, sondern `ADX1`)

### UI-Darstellung:

**Regime Setup Tab** zeigt diese in einer **52-Spalten-Tabelle**:

| Indicator | Type | Param1 Name | Param1 Value | Param1 Min | Param1 Max | Param1 Step | Param2 Name | ... | Param10 Step |
|-----------|------|-------------|--------------|------------|------------|-------------|-------------|-----|--------------|
| ADX1 | ADX | period | 14 | 7 | 21 | 1 | - | ... | - |
| BB1 | BB | period | 20 | 15 | 30 | 1 | std_dev | ... | 1 |

---

## Regimes

```json
"regimes": [
  {
    "id": "BULL",
    "name": "Bull Market",
    "thresholds": [
      {
        "name": "adx_threshold",
        "value": 25.0,
        "range": {
          "min": 15,
          "max": 35,
          "step": 1
        }
      }
    ],
    "priority": 80,
    "scope": "entry"
  }
]
```

**Pfad:** `optimization_results[].regimes[]`
**Typ:** `array`
**Pflicht:** ❌ Optional

### Struktur:

Jedes Regime definiert **eine Marktphase** mit:
- **Erkennungskriterien** (thresholds)
- **Priorität** (für Konfliktauflösung)
- **Scope** (wann angewendet: entry, exit, in_trade)

### Felder:

| Feld | Typ | Beschreibung | Pflicht | Pattern |
|------|-----|--------------|---------|---------|
| `id` | string | Regime-ID (eindeutig) | ✅ | `^[A-Z_]+$` |
| `name` | string | Human-readable Name | ✅ | Beliebig |
| `thresholds` | array | Erkennungs-Schwellenwerte | ✅ | 0-10 Elemente |
| `priority` | integer | Priorität (0-100, höher = wichtiger) | ✅ | 0-100 |
| `scope` | string | Anwendungsbereich | ✅ | `"entry"`, `"exit"`, `"in_trade"` |

### Threshold-Struktur:

Identisch zu Indikator-Parametern:

```json
{
  "name": "adx_threshold",
  "value": 25.0,
  "range": {
    "min": 15,
    "max": 35,
    "step": 1
  }
}
```

### Standard-Regimes:

| Regime ID | Name | Beschreibung | Typische Thresholds |
|-----------|------|--------------|---------------------|
| `BULL` | Bull Market | Starker Aufwärtstrend | `adx_threshold` (ADX > 25) |
| `BEAR` | Bear Market | Starker Abwärtstrend | `adx_threshold` (ADX > 25) |
| `SIDEWAYS` | Sideways Market | Seitwärtsbewegung | `rsi_low` (RSI 30-40), `rsi_high` (RSI 60-70) |
| `SQUEEZE` | Squeeze (Low Volatility) | Niedrige Volatilität | `bb_width_threshold` (BB Width < 0.015) |
| `HIGH_VOL` | High Volatility | Hohe Volatilität | `atr_pct_threshold` (ATR% > 0.018) |

### Prioritäts-System:

Wenn **mehrere Regimes gleichzeitig zutreffen**, wird das Regime mit der **höchsten Priorität** gewählt.

**Empfohlene Prioritäten:**
- `BULL`: 80 (hohe Priorität)
- `BEAR`: 75 (hohe Priorität)
- `SQUEEZE`: 70 (mittlere Priorität)
- `HIGH_VOL`: 65 (mittlere Priorität)
- `SIDEWAYS`: 60 (niedrige Priorität, Fallback)

### Scope:

- **`entry`**: Regime wird bei **Entry-Signal-Suche** verwendet
- **`exit`**: Regime wird bei **Exit-Entscheidungen** verwendet
- **`in_trade`**: Regime wird **während offener Position** verwendet

⚠️ **Aktuell:** Nur `"entry"` implementiert. Andere Scopes für zukünftige Features reserviert.

---

## Entry Params

```json
"entry_params": {
  "pullback_atr": 0.8,
  "pullback_rsi": 45.0,
  "wick_reject": 0.55,
  "bb_entry": 0.15,
  "rsi_oversold": 35.0,
  "rsi_overbought": 65.0,
  "vol_spike_factor": 1.2,
  "breakout_atr": 0.2,
  "min_confidence": 0.58,
  "cooldown_bars": 10,
  "cluster_window_bars": 6
}
```

**Typ:** `object`
**Pflicht:** ❌ Optional

### Zweck:

Diese Parameter werden von **"Analyze Visible Range"** verwendet, um **Entry-Signale** zu generieren.

### Parameter-Beschreibung:

| Parameter | Typ | Bereich | Beschreibung |
|-----------|-----|---------|--------------|
| `pullback_atr` | float | 0.5-1.5 | Pullback-Tiefe in ATR-Vielfachen (Entry nach Pullback) |
| `pullback_rsi` | float | 30-60 | RSI-Level für Pullback-Entry (im Trend) |
| `wick_reject` | float | 0.3-0.8 | Wick-Länge (% der Candle) für Rejection-Pattern |
| `bb_entry` | float | 0.1-0.3 | Abstand zu BB-Band für Entry (0.15 = 15% von Band-Mitte) |
| `rsi_oversold` | float | 20-40 | RSI-Oversold-Level (für Long-Entries) |
| `rsi_overbought` | float | 60-80 | RSI-Overbought-Level (für Short-Entries) |
| `vol_spike_factor` | float | 1.1-1.5 | Volume-Spike-Faktor (1.2 = 120% von Durchschnitt) |
| `breakout_atr` | float | 0.1-0.5 | Breakout-Schwelle in ATR (für Momentum-Entries) |
| `min_confidence` | float | 0.4-0.8 | Minimale Confidence (0-1) für Signal-Aktivierung |
| `cooldown_bars` | int | 5-20 | Abstand zwischen Signalen (Bars) |
| `cluster_window_bars` | int | 3-10 | Zeitfenster für Signal-Clustering (Bars) |

### ATR-Normalisierung:

Die meisten Parameter sind **ATR-normalisiert**, d.h. sie passen sich automatisch an die **Marktvolatilität** an:

- `pullback_atr = 0.8` bedeutet: "Entry nach Pullback von 0.8 × ATR"
- Bei **BTC (ATR=500)**: Pullback von 400 USD
- Bei **EUR/USD (ATR=0.001)**: Pullback von 0.0008

### Verwendung:

1. **Analyze Visible Range**: Liest diese Parameter aus JSON
2. **Entry Signal Engine**: Wendet diese Kriterien auf Chart-Daten an
3. **Backtesting**: Evaluiert Signale mit diesen Parametern

---

## Evaluation Params

```json
"evaluation_params": {
  "eval_horizon_bars": 40,
  "eval_tp_atr": 1.0,
  "eval_sl_atr": 0.8,
  "min_trades_gate": 8,
  "target_trades_soft": 30
}
```

**Typ:** `object`
**Pflicht:** ❌ Optional

### Zweck:

Diese Parameter werden vom **Regime Optimizer** verwendet, um die **Qualität** einer Regime-Konfiguration zu bewerten.

### Parameter-Beschreibung:

| Parameter | Typ | Bereich | Beschreibung |
|-----------|-----|---------|--------------|
| `eval_horizon_bars` | int | 20-100 | Zeitfenster für Regime-Evaluierung (Bars) |
| `eval_tp_atr` | float | 0.5-2.0 | Take-Profit in ATR-Vielfachen (für Score-Berechnung) |
| `eval_sl_atr` | float | 0.3-1.5 | Stop-Loss in ATR-Vielfachen (für Score-Berechnung) |
| `min_trades_gate` | int | 5-20 | Minimale Anzahl Trades für gültigen Score |
| `target_trades_soft` | int | 20-50 | Ziel-Anzahl Trades (Soft-Constraint für Score) |

### Verwendung im Optimizer:

1. **Regime Detection**: Wende Indikator-Parameter und Thresholds an
2. **Signal Generation**: Generiere Entry-Signale mit `entry_params`
3. **Evaluation**: Berechne P&L mit `eval_tp_atr` und `eval_sl_atr`
4. **Score Calculation**: Bewerte basierend auf:
   - Anzahl profitable Trades
   - Durchschnittlicher Gewinn
   - Regime Stability (wenige Wechsel)
   - Trade-Anzahl (Penalty wenn < `min_trades_gate`)

### Trade-Anzahl-Constraint:

- **< min_trades_gate (8)**: Score wird **stark penalized** (×0.5)
- **> target_trades_soft (30)**: Bonus (+10% Score)
- **Zwischen 8-30**: Linearer Bonus (0% → +10%)

**Formel:**
```python
if trade_count < min_trades_gate:
    score_penalty = 0.5  # Halbierung
elif trade_count < target_trades_soft:
    score_bonus = 1.0 + 0.1 * (trade_count - min_trades_gate) / (target_trades_soft - min_trades_gate)
else:
    score_bonus = 1.1  # +10% Bonus
```

---

## Unterstützte Indikatoren

### Standard-Indikatoren (immer verfügbar):

| Type | Name | Parameter | Beschreibung |
|------|------|-----------|--------------|
| `ADX` | Average Directional Index | `period` | Trendstärke (0-100) |
| `RSI` | Relative Strength Index | `period` | Momentum (0-100) |
| `BB` | Bollinger Bands | `period`, `std_dev`, `width_percentile` | Volatilitätsbänder |
| `SMA` | Simple Moving Average | `period` | Gleitender Durchschnitt |
| `EMA` | Exponential Moving Average | `period` | Exponentieller Durchschnitt |
| `ATR` | Average True Range | `period` | Volatilität (absolute Werte) |

### Erweiterte Indikatoren (optional):

| Type | Name | Parameter | Beschreibung |
|------|------|-----------|--------------|
| `MACD` | Moving Average Convergence Divergence | `fast`, `slow`, `signal` | Momentum-Oszillator |
| `STOCH` | Stochastic Oscillator | `period`, `smooth_k`, `smooth_d` | Überkauft/Überverkauft |
| `CCI` | Commodity Channel Index | `period` | Zyklischer Oszillator |
| `SUPERTREND` | SuperTrend | `period`, `multiplier` | Trend-Following |
| `VWAP` | Volume Weighted Average Price | - | Volumen-gewichteter Durchschnitt |
| `OBV` | On Balance Volume | - | Volumen-Akkumulation |

### Parameter-Typen:

| Parameter Name | Typ | Typischer Bereich | Beschreibung |
|----------------|-----|-------------------|--------------|
| `period` | int | 5-200 | Anzahl Bars für Berechnung |
| `std_dev` | float | 1.0-3.0 | Standard-Abweichungen (BB) |
| `multiplier` | float | 1.0-5.0 | Multiplikator (SuperTrend, ATR) |
| `fast` | int | 8-20 | Schnelle MA-Periode (MACD) |
| `slow` | int | 20-50 | Langsame MA-Periode (MACD) |
| `signal` | int | 5-15 | Signal-Linien-Periode (MACD) |
| `smooth_k` | int | 1-10 | K-Linie Glättung (Stochastic) |
| `smooth_d` | int | 1-10 | D-Linie Glättung (Stochastic) |
| `width_percentile` | float | 10-40 | BB-Width-Percentile (für Squeeze) |

---

## Verwendungsbeispiele

### 1. Minimale Konfiguration (1 Indikator, 1 Regime)

```json
{
  "schema_version": "2.0.0",
  "optimization_results": [
    {
      "timestamp": "2026-01-24T00:00:00Z",
      "score": 0.0,
      "trial_number": 1,
      "applied": true,
      "indicators": [
        {
          "name": "RSI1",
          "type": "RSI",
          "params": [
            {
              "name": "period",
              "value": 14,
              "range": {"min": 9, "max": 20, "step": 1}
            }
          ]
        }
      ],
      "regimes": [
        {
          "id": "SIDEWAYS",
          "name": "Sideways Market",
          "thresholds": [
            {
              "name": "rsi_low",
              "value": 35,
              "range": {"min": 25, "max": 45, "step": 1}
            },
            {
              "name": "rsi_high",
              "value": 65,
              "range": {"min": 55, "max": 75, "step": 1}
            }
          ],
          "priority": 60,
          "scope": "entry"
        }
      ]
    }
  ]
}
```

### 2. Mehrere Indikatoren desselben Typs

```json
"indicators": [
  {
    "name": "SMA_FAST1",
    "type": "SMA",
    "params": [
      {"name": "period", "value": 20, "range": {"min": 10, "max": 50, "step": 1}}
    ]
  },
  {
    "name": "SMA_SLOW1",
    "type": "SMA",
    "params": [
      {"name": "period", "value": 100, "range": {"min": 50, "max": 200, "step": 1}}
    ]
  }
]
```

### 3. Indikator mit vielen Parametern (MACD)

```json
{
  "name": "MACD1",
  "type": "MACD",
  "params": [
    {"name": "fast", "value": 12, "range": {"min": 8, "max": 20, "step": 1}},
    {"name": "slow", "value": 26, "range": {"min": 20, "max": 40, "step": 1}},
    {"name": "signal", "value": 9, "range": {"min": 5, "max": 15, "step": 1}}
  ]
}
```

### 4. Boolean-Parameter

```json
{
  "name": "SUPERTREND1",
  "type": "SUPERTREND",
  "params": [
    {"name": "period", "value": 10, "range": {"min": 7, "max": 20, "step": 1}},
    {"name": "multiplier", "value": 3.0, "range": {"min": 1.0, "max": 5.0, "step": 0.1}},
    {"name": "use_ema", "value": true, "range": null}
  ]
}
```

**Note:** Boolean-Parameter haben **kein `range`** (werden nicht optimiert).

### 5. Multiple Optimization Results (Historie)

```json
"optimization_results": [
  {
    "timestamp": "2026-01-24T20:33:23Z",
    "score": 85.0,
    "trial_number": 15,
    "applied": true,
    "indicators": [...]
  },
  {
    "timestamp": "2026-01-24T20:30:00Z",
    "score": 81.0,
    "trial_number": 8,
    "applied": false,
    "indicators": [...]
  },
  {
    "timestamp": "2026-01-24T20:25:00Z",
    "score": 78.0,
    "trial_number": 3,
    "applied": false,
    "indicators": [...]
  }
]
```

**Usage:**
- **Tab "Regime Results"**: Zeigt ALLE Trials (sortiert nach Score)
- **"Analyze Visible Range"**: Verwendet NUR Trial mit `applied: true`

---

## 🚀 Workflow-Anleitung

### Schritt 1: Template anpassen

1. Öffne `260124_empty_template.json`
2. Passe **Indikatoren** an:
   - Ändere `name` (z.B. `ADX1` → `ADX_MAIN`)
   - Ändere `value` (aktueller Wert)
   - Ändere `range.min` und `range.max` (Optimierungsbereich)
3. Passe **Regimes** an:
   - Füge neue Regimes hinzu oder entferne ungenutzte
   - Ändere `priority` (höher = wichtiger)
4. Passe **Entry-Parameter** an (optional)

### Schritt 2: In UI importieren

1. Öffne **Entry Analyzer**
2. Gehe zu **Tab "1. Regime Setup"**
3. Klicke **"Import Config (JSON)"**
4. Wähle deine angepasste JSON-Datei
5. ✅ Tabellen werden automatisch ausgefüllt

### Schritt 3: Parameter-Ranges anpassen

1. In der **52-Spalten-Tabelle**:
   - Ändere **Min/Max-Werte** mit SpinBoxen
   - Jede Zeile = 1 Indikator
   - Bis zu 10 Parameter pro Zeile
2. In der **Regime Thresholds-Tabelle**:
   - Ändere Min/Max für Schwellenwerte
3. Klicke **"Apply & Continue to Optimization"**

### Schritt 4: Optimierung starten

1. **Tab "2. Regime Optimization"** öffnet automatisch
2. Setze **Max Trials** (z.B. 150)
3. Klicke **"Start Optimization"**
4. ⏳ Warte auf Fertigstellung (~2 Minuten)
5. ✅ Top-Ergebnisse werden live angezeigt

### Schritt 5: Bestes Ergebnis exportieren

1. **Tab "3. Regime Results"** öffnen
2. Klicke auf **beste Zeile** (höchster Score)
3. Klicke **"Export to JSON"**
4. 💾 Neue JSON-Datei wird erstellt mit `applied: true`

### Schritt 6: In "Analyze Visible Range" verwenden

1. **Tab "Regime"** öffnen
2. Klicke **"Load Config"**
3. Wähle exportierte JSON-Datei
4. Klicke **"Analyze Visible Range"**
5. 🎯 Optimierte Parameter werden verwendet!

---

## 🔍 Troubleshooting

### Fehler: "Missing required parameter range"

**Ursache:** Parameter im `optimization_results[].indicators[].params[]` hat kein `range`-Feld.

**Lösung:** Füge `range` hinzu:
```json
{
  "name": "period",
  "value": 14,
  "range": {"min": 7, "max": 21, "step": 1}
}
```

### Fehler: "No optimization_results"

**Ursache:** Array `optimization_results` ist leer.

**Lösung:** Mindestens **1 Element** muss vorhanden sein:
```json
"optimization_results": [
  {
    "timestamp": "2026-01-24T00:00:00Z",
    "score": 0.0,
    "trial_number": 1,
    "applied": false,
    "indicators": [...]
  }
]
```

### Warnung: "Multiple trials with applied: true"

**Ursache:** Mehr als 1 Trial hat `applied: true`.

**Lösung:** Setze alle außer dem besten auf `false`:
```json
{"applied": true},   // Nur das beste Ergebnis
{"applied": false},  // Alle anderen
{"applied": false}
```

### Tabelle zeigt falsche Werte

**Ursache:** UI zeigt Base-Values statt optimierte Values.

**Lösung:** Klicke **"Reload from JSON"** im Regime Setup Tab.

---

## 📚 Referenzen

- **JSON Schema:** `config/schemas/regime_optimization/optimized_regime_config_v2.schema.json`
- **Design-Dokument:** `.ai_exchange/Regime_Analyse/GENERIC_PARAMETER_DESIGN.md`
- **Beispiel-Datei:** `entry_analyzer_regime_v2_example.json`
- **Alte v1.0-Dateien:** `entry_analyzer_regime.json` (deprecated)

---

## ✅ Checkliste für neue Configs

- [ ] `schema_version` ist `"2.0.0"`
- [ ] Mindestens **1 Element** in `optimization_results`
- [ ] Jeder Indikator hat `name`, `type`, `params`
- [ ] Jeder Parameter hat `name`, `value`, `range` (mit min/max/step)
- [ ] Indikator-Namen sind **eindeutig** (z.B. `ADX1`, `RSI1`)
- [ ] Mindestens **1 Regime** definiert
- [ ] Jedes Regime hat `id`, `name`, `priority`, `scope`
- [ ] Nur **1 Trial** hat `applied: true`
- [ ] `entry_params` und `evaluation_params` vorhanden (optional)

---

**Version:** 1.0
**Letzte Aktualisierung:** 2026-01-24
**Autor:** OrderPilot-AI Development Team
