# JSON Entry System - User Guide

**Version:** 1.0
**Date:** 2026-01-28
**Author:** Claude Code

---

## 📋 Übersicht

Das JSON Entry System ermöglicht es, die Entry-Logik des Trading Bots via **CEL (Common Expression Language)** aus JSON-Dateien zu steuern, ohne den Code zu ändern.

### Was ist neu?

- ✅ **Neuer Button**: "Start Bot (JSON Entry)" parallel zu "Start Bot"
- ✅ **CEL-basierte Entry**: Entry-Entscheidungen via CEL Expression aus JSON
- ✅ **Zwei JSON-Quellen**: Regime JSON + optionale Indicator JSON
- ✅ **SL/TP aus UI**: Stop Loss / Take Profit bleiben in UI-Eingabefeldern
- ✅ **70+ CEL Functions**: Umfangreiche Trading-Funktionsbibliothek

---

## 🚀 Quick Start

### 1. Beispiel-JSON vorbereiten

Erstelle eine Regime JSON mit `entry_expression` Feld:

```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "name": "RSI ADX Scalping",
    "description": "RSI oversold + strong trend"
  },
  "indicators": {
    "rsi14": {
      "type": "RSI",
      "period": 14
    },
    "adx14": {
      "type": "ADX",
      "period": 14
    }
  },
  "regimes": {
    "EXTREME_BULL": {
      "rsi_min": 60,
      "adx_min": 30
    }
  },
  "entry_expression": "rsi < 35 && adx > 25 && macd_hist > 0"
}
```

**Speicherort:** `03_JSON/Entry_Analyzer/Regime/my_strategy.json`

### 2. Bot mit JSON Entry starten

1. Öffne Trading Bot Tab
2. Klicke **"▶ Start Bot (JSON Entry)"**
3. Wähle Regime JSON aus
4. Optional: Wähle Indicator JSON aus
5. Prüfe Entry Expression im Log
6. SL/TP/Trailing Stop in UI-Feldern einstellen
7. Bot läuft!

---

## 📁 JSON-Dateien Struktur

### Regime JSON (erforderlich)

```json
{
  "schema_version": "2.0.0",
  "metadata": { ... },
  "indicators": {
    "rsi14": { "type": "RSI", "period": 14 },
    "adx14": { "type": "ADX", "period": 14 }
  },
  "regimes": {
    "EXTREME_BULL": { ... },
    "TREND_UP": { ... }
  },
  "entry_expression": "rsi < 35 && adx > 25 && macd_hist > 0"
}
```

**Wichtigste Felder:**
- `entry_expression` (String): CEL Expression für Entry-Logik
- `indicators` (Object): Indicator-Definitionen
- `regimes` (Object): Regime-Schwellenwerte

### Indicator JSON (optional)

```json
{
  "schema_version": "1.0.0",
  "metadata": { ... },
  "indicators": {
    "macd": {
      "type": "MACD",
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    "bb": {
      "type": "BOLLINGER_BANDS",
      "period": 20,
      "std_dev": 2.0
    }
  }
}
```

**Verhalten:**
- Indicator JSON hat **Vorrang** bei gleichen Indicator-IDs
- Indicators werden kombiniert (Indicator JSON + Regime JSON)

---

## 🔧 CEL Entry Expression

### Verfügbare Variablen

#### Price Data
```cel
close, open, high, low, volume
```

#### Trend Indicators
```cel
sma_20, sma_50, ema_12, ema_26
```

#### Momentum Indicators (flat)
```cel
rsi, macd, macd_signal, macd_hist, stoch_k, stoch_d, cci, mfi
```

#### Momentum Indicators (nested)
```cel
rsi14.value, adx14.value, macd_obj.histogram
```

#### Trend Strength
```cel
adx
```

#### Volatility
```cel
atr, bb_pct, bb_width, bb_upper, bb_middle, bb_lower, chop
```

#### Volume
```cel
volume_ratio
```

#### Regime
```cel
regime  // "BULL", "BEAR", "NEUTRAL", etc.
regime_obj.confidence, regime_obj.strength, regime_obj.volatility
```

### CEL Expression Beispiele

**Simple RSI Oversold:**
```cel
rsi < 30
```

**RSI + ADX Strong Trend:**
```cel
rsi < 35 && adx > 25
```

**RSI + MACD + Regime Filter:**
```cel
rsi < 35 && macd_hist > 0 && (regime == 'EXTREME_BULL' || regime == 'BULL')
```

**Bollinger Band Reversal:**
```cel
bb_pct < 0.2 && rsi < 30 && adx > 20
```

**Complex Multi-Indicator:**
```cel
rsi < 35 &&
adx > 25 &&
macd_hist > 0 &&
bb_pct < 0.3 &&
volume_ratio > 1.1 &&
(regime == 'EXTREME_BULL' || regime == 'BULL')
```

**Price Above SMA20 + RSI:**
```cel
close > sma_20 && rsi > 50 && macd_hist > 0
```

---

## 📊 CEL Functions (70+ verfügbar)

### Price Functions
```cel
pct_change(from, to)         // Prozentuale Änderung
price_above_sma(price, sma)  // Preis über SMA
price_below_sma(price, sma)  // Preis unter SMA
```

### Indicator Functions
```cel
rsi_oversold(rsi, threshold)    // RSI < threshold
rsi_overbought(rsi, threshold)  // RSI > threshold
macd_bullish(macd_hist)         // MACD histogram > 0
macd_bearish(macd_hist)         // MACD histogram < 0
adx_strong(adx)                 // ADX > 25
```

### Regime Functions
```cel
in_regime(current, expected)  // Check regime match
has(list, value)              // Check if value in list
```

### Siehe: `04_Knowledgbase/CEL_Befehle_Liste_v2.md` für vollständige Liste

---

## ⚙️ Standard vs. JSON Entry

| Feature | Standard Entry | JSON Entry |
|---------|----------------|------------|
| Button | "Start Bot" | "Start Bot (JSON Entry)" |
| Entry Logic | EntryScoreEngine (7 Komponenten) | JsonEntryScorer (CEL Expression) |
| Configuration | Hardcoded im Code | JSON-Dateien (änderbar) |
| SL/TP/Trailing | UI-Felder | UI-Felder (identisch) |
| Flexibilität | Mittel | Hoch (CEL anpassbar) |
| Testing | Unit Tests | Unit Tests + JSON-Tests |

---

## 🧪 Testing

### Validierung beim Start

Beim Klick auf "Start Bot (JSON Entry)" werden automatisch geprüft:

1. ✅ JSON-Dateien existieren und sind valide
2. ✅ Entry Expression ist nicht leer
3. ✅ Indicators sind definiert
4. ✅ CEL Expression compiliert erfolgreich

**Warnings im Log:**
- Entry Expression ist `true` (always enter)
- Indicators nicht in Expression verwendet
- Keine Indicators definiert

### Manuelle Tests

**Test 1: Simple Entry**
```json
{
  "entry_expression": "rsi < 30"
}
```
- Expected: Entry Signal wenn RSI < 30

**Test 2: Complex Entry**
```json
{
  "entry_expression": "rsi < 35 && adx > 25 && macd_hist > 0"
}
```
- Expected: Entry Signal nur wenn ALLE Bedingungen erfüllt

**Test 3: Regime Filter**
```json
{
  "entry_expression": "(regime == 'EXTREME_BULL' || regime == 'BULL') && rsi < 40"
}
```
- Expected: Entry nur in bullischen Regimes

---

## 🔍 Debugging

### Log-Meldungen

**Beim Start:**
```
✅ Regime JSON: 260128_example_json_entry.json
✅ Indicator JSON: my_indicators.json
📝 Entry Expression: rsi < 35 && adx > 25 && macd_hist > 0...
✅ JSON Entry Scorer bereit
   Compiled Expression: True
```

**Bei Entry Signal:**
```
JSON Entry [long]: True (score=1.00, reasons=['JSON_CEL_ENTRY', 'RSI_OVERSOLD', 'STRONG_TREND'])
```

### Reason Codes

Der JsonEntryScorer generiert automatisch Reason Codes:

- `JSON_CEL_ENTRY` - Base reason (immer enthalten)
- `RSI_OVERSOLD` - RSI < 30
- `RSI_OVERBOUGHT` - RSI > 70
- `MACD_BULLISH` - MACD histogram > 0
- `MACD_BEARISH` - MACD histogram < 0
- `STRONG_TREND` - ADX > 25
- `WEAK_TREND` - ADX < 20
- `TREND_REGIME` - Regime enthält "TREND"
- `RANGE_REGIME` - Regime enthält "RANGE"
- `BB_LOWER_BAND` - BB % < 0.2
- `BB_UPPER_BAND` - BB % > 0.8
- `PRICE_ABOVE_SMA20` - Close > SMA20 (Long)
- `PRICE_BELOW_SMA20` - Close < SMA20 (Short)

---

## 🚨 Troubleshooting

### Problem: "CEL Expression compilation failed"

**Ursache:** Ungültige CEL Syntax in `entry_expression`

**Lösung:**
1. Prüfe Expression auf Syntax-Fehler
2. Validiere Variablennamen (z.B. `rsi` statt `RSI`)
3. Teste Expression einzeln

### Problem: "Indicator JSON nicht gefunden"

**Ursache:** Falscher Pfad oder Datei existiert nicht

**Lösung:**
1. Prüfe Pfad relativ zum Working Directory
2. Verwende absolute Pfade oder `03_JSON/Entry_Analyzer/Indicators/`

### Problem: "No Entry Signal" trotz erfüllter Bedingungen

**Ursache:** Context-Werte stimmen nicht mit Expression überein

**Lösung:**
1. Aktiviere Debug-Logging (`logger.debug`)
2. Prüfe Context-Werte im Log
3. Teste mit einfacherer Expression (z.B. `true`)

### Problem: Warnings über ungenutzte Indicators

**Ursache:** Indicators definiert, aber nicht in Expression verwendet

**Lösung:**
- Entferne ungenutzte Indicators aus JSON
- Oder ignoriere Warning (kein Fehler, nur Hinweis)

---

## 📚 Siehe auch

- **CEL Functions Reference:** `04_Knowledgbase/CEL_Befehle_Liste_v2.md` (97 Funktionen)
- **CEL Neue Funktionen:** `04_Knowledgbase/CEL_Neue_Funktionen_v2.4.md`
- **Trading Help:** `04_Knowledgbase/cel_help_trading.md`
- **Session Summary:** `docs/260128_Session_Summary_CEL_Updates.md`

---

## 🎯 Best Practices

### 1. Start Simple

Beginne mit einfachen Expressions:
```cel
rsi < 30
```

Dann erweitern:
```cel
rsi < 30 && adx > 20
```

### 2. Use Regime Filters

Vermeide Trades in ungünstigen Regimes:
```cel
(regime == 'EXTREME_BULL' || regime == 'BULL') && rsi < 35
```

### 3. Combine Multiple Indicators

Nutze Confluence für bessere Signals:
```cel
rsi < 35 && macd_hist > 0 && bb_pct < 0.3 && adx > 25
```

### 4. Test Incrementally

Teste jede neue Bedingung einzeln:
1. `rsi < 35` → OK?
2. `rsi < 35 && adx > 25` → OK?
3. `rsi < 35 && adx > 25 && macd_hist > 0` → OK?

### 5. Document Your Strategy

Nutze `entry_conditions_explained` in JSON:
```json
{
  "entry_expression": "rsi < 35 && adx > 25",
  "entry_conditions_explained": {
    "rsi_oversold": "RSI < 35 indicates oversold",
    "strong_trend": "ADX > 25 confirms strong trend"
  }
}
```

---

## 💡 Tipps & Tricks

### Expression Debugging

Teste Expression mit minimalem Context:
```cel
true  // Immer True (für Testing)
false  // Immer False (zum Deaktivieren)
```

### Multiple Entry Strategies

Erstelle verschiedene JSON-Dateien für verschiedene Strategien:
- `scalping_5m.json` - 5-Minuten Scalping
- `swing_1h.json` - 1-Stunden Swing Trading
- `breakout_15m.json` - 15-Minuten Breakout

### Regime-Based Strategies

Nutze Regime für adaptive Entry-Logik:
```cel
regime == 'EXTREME_BULL' ? (rsi < 40) : (rsi < 30)
```

---

**Version:** 1.0
**Last Updated:** 2026-01-28
**Support:** GitHub Issues

