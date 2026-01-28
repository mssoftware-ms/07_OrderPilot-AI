# CEL Skriptsprache - Vollständige Befehls- und Funktionsliste
## Trading Bot & Entry Analyzer Implementation (Aligned Version)

**Datum:** 28. Januar 2026
**Version:** 2.4 (Aktualisiert - Neue Funktionen & Variablen)
**Zielumgebung:** CEL Expression Language für TradingBot Analyzer
**Audit Datum:** 2026-01-28
**Status:** ✅ **Aktualisiert – Implementierungsstand 2026-01-28 (97 Funktionen)**

---

## ✅ IMPLEMENTIERUNGSSTATUS (AKTUELL)

**Stand:** 2026-01-28

- Implementiert in `src/core/tradingbot/cel_engine.py`: **97 Funktionen**
- Aktuelle Referenz: `04_Knowledgbase/CEL_Functions_Reference_v3.md` (v3.1)
- Nicht implementiert (bewusst): `log`, `log10`, `sin`, `cos`, `tan`, `is_time_in_range`
- **NEU (v2.4)**: `last_closed_regime()`, `trigger_regime_analysis()`, `no_entry` Workflow, 69+ Variablen dokumentiert

---

## 📋 INHALTSÜBERSICHT

1. [Mathematische Funktionen](#mathematische-funktionen)
2. [Logische & Vergleichsoperatoren](#logische--vergleichsoperatoren)
3. [String & Datentyp-Funktionen](#string--datentyp-funktionen)
4. [Array & Collection-Funktionen](#array--collection-funktionen)
5. [Trading-spezifische Funktionen](#trading-spezifische-funktionen)
6. [No Entry Filter (Entry Blocker)](#no-entry-filter-entry-blocker)
7. [Regime Functions (NEU)](#regime-functions-neu)
8. [Technische Indikatoren (IMPLEMENTIERT)](#technische-indikatoren-implementiert)
9. [Pattern-Erkennung (TA-Lib)](#pattern-erkennung-ta-lib)
10. [Entry Analyzer Methoden](#entry-analyzer-methoden)
11. [Config System API](#config-system-api)
12. [Zeitfunktionen](#zeitfunktionen)
13. [Variable & Kontext-Zugriff](#variable--kontext-zugriff)
14. [Verfügbare Variablen (69+)](#verfügbare-variablen)
15. [Rückgabeparameter nach Regeltyp](#rückgabeparameter-nach-regeltyp)

---

## 🔢 MATHEMATISCHE FUNKTIONEN

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `abs(x)` | `x: number` | `number` | Absoluter Wert (ohne Vorzeichen) | `abs(-5.5)` → `5.5` |
| ✅ | `min(a, b)` | `a, b: number` | `number` | Minimum von zwei Werten | `min(10, 5)` → `5` |
| ✅ | `max(a, b)` | `a, b: number` | `number` | Maximum von zwei Werten | `max(10, 5)` → `10` |
| ✅ | `round(x)` | `x: number` | `number` | Auf nächste ganze Zahl runden | `round(5.7)` → `6` |
| ✅ | `floor(x)` | `x: number` | `number` | Abrunden (Boden) | `floor(5.7)` → `5` |
| ✅ | `ceil(x)` | `x: number` | `number` | Aufrunden (Decke) | `ceil(5.3)` → `6` |
| ✅ | `pow(x, y)` | `x: number, y: number` | `number` | x hoch y (Potenz) | `pow(2, 3)` → `8` |
| ✅ | `sqrt(x)` | `x: number` | `number` | Quadratwurzel | `sqrt(9)` → `3` |
| ❌ | `log(x)` | `x: number` | `number` | Natürlicher Logarithmus | `log(2.718)` → `1` |
| ❌ | `log10(x)` | `x: number` | `number` | 10er Logarithmus | `log10(100)` → `2` |
| ❌ | `sin(x)` | `x: number (Radiant)` | `number` | Sinus | `sin(0)` → `0` |
| ❌ | `cos(x)` | `x: number (Radiant)` | `number` | Cosinus | `cos(0)` → `1` |
| ❌ | `tan(x)` | `x: number (Radiant)` | `number` | Tangens | `tan(π/4)` → `1` |
| ✅ | `sum(arr)` | `arr: number[]` | `number` | Summe aller Werte im Array | `sum([1, 2, 3])` → `6` |

---

## ⚖️ LOGISCHE & VERGLEICHSOPERATOREN

| Operator | Typ | Rückgabe | Beschreibung | Beispiel |
|----------|-----|----------|-------------|----------|
| `==` | Vergleich | `bool` | Gleichheit | `atrp == 0.6` |
| `!=` | Vergleich | `bool` | Ungleichheit | `regime != "R0"` |
| `<` | Vergleich | `bool` | Kleiner als | `volume < 1000` |
| `>` | Vergleich | `bool` | Größer als | `trade.pnl_pct > 0` |
| `<=` | Vergleich | `bool` | Kleiner oder gleich | `atrp <= 2.5` |
| `>=` | Vergleich | `bool` | Größer oder gleich | `trade.leverage >= 20` |
| `&&` | Logisch AND | `bool` | Beide Bedingungen wahr | `atrp > 0.2 && volume > 500` |
| `\|\|` | Logisch OR | `bool` | Mindestens eine wahr | `regime == "R0" \|\| regime == "R5"` |
| `!` | Logisch NOT | `bool` | Negation (Umkehrung) | `!squeeze_on` |
| `in` | Mitgliedschaft | `bool` | Element in Array/Liste | `regime in cfg.no_trade_regimes` |
| `?:` | Ternär (if-then-else) | `any` | Bedingter Ausdruck | `trade.side == "long" ? 1 : -1` |

---

## 📐 OPERATOR PRECEDENCE (Auswertungsreihenfolge)

**Wichtig:** CEL wertet Operatoren in festgelegter Reihenfolge aus. Verwende Klammern `()` für explizite Kontrolle!

### Precedence-Tabelle (1 = höchste Priorität)

| Level | Kategorie | Operatoren | Assoziativität | Beschreibung | Beispiel |
|-------|-----------|------------|----------------|--------------|----------|
| **1** | Primär | `()` `.` `[]` | Links → Rechts | Klammern, Member-Zugriff, Index | `(a + b)`, `trade.pnl`, `arr[0]` |
| **2** | Funktionsaufruf | `func()` | Links → Rechts | Funktionsaufrufe | `abs(-5)`, `nz(value, 0)` |
| **3** | Unär | `!` `-` (unary) | Rechts → Links | Negation, Minus | `!squeeze_on`, `-atrp` |
| **4** | Multiplikativ | `*` `/` `%` | Links → Rechts | Multiplikation, Division, Modulo | `atrp * 100`, `close / open` |
| **5** | Additiv | `+` `-` | Links → Rechts | Addition, Subtraktion | `high + atr`, `close - low` |
| **6** | Relational | `<` `<=` `>` `>=` | Links → Rechts | Vergleiche | `atrp > 0.5`, `volume <= 1000` |
| **7** | Equality | `==` `!=` | Links → Rechts | Gleichheit, Ungleichheit | `regime == "R1"`, `side != "long"` |
| **8** | Membership | `in` | Links → Rechts | Element in Collection | `regime in ["R0", "R1"]` |
| **9** | Logical AND | `&&` | Links → Rechts | Logisches UND | `atrp > 0.2 && volume > 500` |
| **10** | Logical OR | `\|\|` | Links → Rechts | Logisches ODER | `regime == "R0" \|\| regime == "R5"` |
| **11** | Ternär | `? :` | Rechts → Links | Bedingter Ausdruck | `side == "long" ? 1 : -1` |

### 🔍 Komplexe Ausdrücke - Beispiele

#### Beispiel 1: Multiplikation vor Addition
```cel
// ❌ FALSCH interpretiert als: (atrp * 100) + 50
atrp * 100 + 50

// ✅ KORREKT: Wenn du (100 + 50) meinst:
atrp * (100 + 50)
```

#### Beispiel 2: Logische Operatoren
```cel
// ❌ FALSCH interpretiert als: atrp > 0.2 && (volume > 500 || squeeze_on)
atrp > 0.2 && volume > 500 || squeeze_on

// ✅ KORREKT: Explizite Gruppierung
(atrp > 0.2 && volume > 500) || squeeze_on
```

#### Beispiel 3: Vergleiche vor AND
```cel
// ✅ Wird korrekt interpretiert als: (atrp > 0.5) && (rsi < 70)
atrp > 0.5 && rsi < 70

// ✅ Gleichwertig mit expliziten Klammern (empfohlen für Lesbarkeit):
(atrp > 0.5) && (rsi < 70)
```

#### Beispiel 4: Ternär mit AND/OR
```cel
// ❌ FALSCH interpretiert als: is_long(trade) ? (tp_pct > 1.5 && trade.bars_held) > 10 : false
is_long(trade) ? tp_pct > 1.5 && trade.bars_held > 10 : false

// ✅ KORREKT: Klammern um Bedingung
is_long(trade) ? (tp_pct > 1.5 && trade.bars_held > 10) : false
```

#### Beispiel 5: Member-Zugriff hat höchste Priorität
```cel
// ✅ Wird korrekt interpretiert als: (trade.pnl_pct) > 2.0
trade.pnl_pct > 2.0

// ✅ Verschachtelte Member-Zugriffe
cfg.regimes.no_trade[0]  // cfg → regimes → no_trade → Index 0
```

### 📋 Klammer-Regeln

#### ✅ EMPFOHLEN: Explizite Klammern verwenden

**Vorteile:**
- Verbessert Lesbarkeit
- Verhindert Fehler
- Macht Intention klar
- Reduziert mentale Last

```cel
// ✅ EMPFOHLEN: Immer Klammern bei komplexen Ausdrücken
((atrp > 0.5) && (volume > 1000)) || (squeeze_on && (rsi < 30))

// ❌ NICHT EMPFOHLEN: Verlass dich nicht auf Operator Precedence
atrp > 0.5 && volume > 1000 || squeeze_on && rsi < 30
```

#### ⚠️ Häufige Fehlerquellen

**1. AND vor OR verwechseln:**
```cel
// ❌ FEHLER: Wird als (a && b) || c interpretiert
a && b || c

// ✅ FIX: Explizite Klammern
a && (b || c)  // ODER
(a && b) || c  // je nach Intention
```

**2. Ternär-Operator:**
```cel
// ❌ FEHLER: Bedingung nicht geklammert
is_long(trade) ? tp_pct > 1.5 && bars > 10 : false

// ✅ FIX: Bedingung in Klammern
is_long(trade) ? (tp_pct > 1.5 && bars > 10) : false
```

**3. Negation bei AND/OR:**
```cel
// ❌ FEHLER: Wird als (!squeeze_on) && (atrp > 0.5) interpretiert
!squeeze_on && atrp > 0.5

// ✅ OK wenn gemeint, aber für Klarheit:
(!squeeze_on) && (atrp > 0.5)
```

### 🎯 Best Practices

1. **Verwende IMMER Klammern bei gemischten AND/OR:**
   ```cel
   // ✅ KLAR
   (condition1 && condition2) || (condition3 && condition4)
   ```

2. **Klammere komplexe Bedingungen in Ternär-Operatoren:**
   ```cel
   // ✅ KLAR
   condition ? (expr1 && expr2) : (expr3 || expr4)
   ```

3. **Verwende Klammern für Lesbarkeit, auch wenn nicht nötig:**
   ```cel
   // ✅ LESBARER (auch wenn technisch nicht nötig)
   (atrp > 0.5) && (rsi < 70)
   ```

4. **Bei Unsicherheit: Klammern hinzufügen!**
   - Zusätzliche Klammern schaden nie
   - Fehlende Klammern können zu subtilen Bugs führen

---

## 🛡️ ERROR HANDLING & FEHLERBEHANDLUNG

CEL ist eine **sichere Expression Language** - sie wirft bei den meisten Fehlern keine Exceptions, sondern gibt standardmäßig `false` zurück oder verwendet sichere Defaults. Trotzdem ist explizites Error-Handling wichtig für robuste Rules.

### 1️⃣ Null-Werte Handling

**Problem:** Fehlende oder undefinierte Werte können zu unerwarteten Ergebnissen führen.

#### ✅ Implementierte Lösungen:

| Funktion | Status | Beschreibung | Beispiel |
|----------|--------|--------------|----------|
| `isnull(x)` | ✅ | Prüft ob Wert null/undefined ist | `isnull(spread_bps)` → `true/false` |
| `nz(x, default)` | ✅ | Gibt Default zurück wenn null | `nz(obi, 0)` → `0` wenn obi null |
| `coalesce(a, b, c)` | ✅ | Erstes nicht-null Element | `coalesce(tr_stop, stop, 0)` |

#### 📋 Best Practices:

```cel
// ❌ UNSICHER: Direkter Zugriff kann null sein
trade.spread_bps > 5

// ✅ SICHER: Null-Check mit Default
nz(trade.spread_bps, 0) > 5

// ✅ SICHER: Expliziter Null-Check
!isnull(trade.spread_bps) && trade.spread_bps > 5

// ✅ SEHR SICHER: Mehrere Fallbacks
coalesce(trade.spread_bps, historical_spread, 0) > 5
```

#### ⚠️ Häufige Null-Szenarien:

1. **Optionale Trade-Felder:**
   ```cel
   // Felder wie spread_bps, funding_fee können null sein
   nz(trade.spread_bps, 0)
   ```

2. **Berechnete Indikatoren:**
   ```cel
   // Indikatoren in ersten Bars können null sein (nicht genug Daten)
   !isnull(rsi14.value) && rsi14.value > 70
   ```

3. **Config-Optionen:**
   ```cel
   // Optionale Config-Werte
   nz(cfg.max_leverage, 20)
   ```

### 2️⃣ Division durch Null

**Problem:** Division durch 0 sollte vermieden werden.

#### ✅ Sichere Patterns:

```cel
// ❌ UNSICHER: Kann durch 0 teilen
profit / volume

// ✅ SICHER: Prüfe Divisor
volume > 0 ? (profit / volume) : 0

// ✅ SICHER: Mit Minimum-Threshold
volume > 100 ? (profit / volume) : 0

// ✅ SEHR SICHER: Kombiniert mit Null-Check
!isnull(volume) && volume > 0 ? (profit / volume) : 0
```

#### 🎯 Empfehlung:

**Verwende IMMER einen Null-Check + Divisor-Check:**
```cel
(!isnull(divisor) && divisor != 0) ? (numerator / divisor) : default_value
```

### 3️⃣ Array/Index Out of Bounds

**Problem:** Zugriff auf nicht-existierende Array-Elemente.

#### ✅ IMPLEMENTIERT (aktuell verfügbar):

Nutze Array‑Helper, um sichere Zugriffe zu bauen:

```cel
size(arr) > 0 && first(arr) == "value"
has(arr, "R1")
```

**Hinweis:** Direkter Indexzugriff (`arr[0]`) ist möglich, aber nur sicher, wenn `size(arr) > 0` geprüft wurde.

### 4️⃣ Type Errors

**Problem:** Operationen auf falschen Datentypen.

#### ⚠️ CEL ist NICHT streng typisiert:

```cel
// ❌ Type Error: String + Number
"value" + 5  // → Fehler oder unerwartetes Verhalten

// ❌ Type Error: Number-Vergleich mit String
atrp > "0.5"  // → Fehler
```

#### ✅ Sichere Patterns:

**1. Verwende konsistente Typen:**
```cel
// ✅ Beide Seiten Number
atrp > 0.5

// ✅ Beide Seiten String
regime == "R1"
```

**2. Type-Konvertierung (implementiert):**
```cel
type(value)
int(value)
double(value)
string(value)
bool(value)
```

**3. Backend-Validierung:**
- Context-Variablen werden vom Backend typisiert
- JSON-Schema definiert erwartete Typen
- Pydantic Models erzwingen Type-Safety

### 5️⃣ Indicator-Zugriff Fehler

**Problem:** Zugriff auf nicht-berechnete oder nicht-existierende Indikatoren.

#### ✅ Best Practices:

```cel
// ❌ UNSICHER: Indicator könnte nicht existieren
rsi14.value > 70

// ✅ SICHER: Null-Check vor Zugriff
!isnull(rsi14.value) && rsi14.value > 70

// ✅ SEHR SICHER: Mit Default
nz(rsi14.value, 50) > 70
```

#### 📋 Indicator-Spezifische Checks:

```cel
// Bollinger Bands: Alle 3 Werte prüfen
!isnull(bb_20_2.upper) && close > bb_20_2.upper

// MACD: Signal-Crossover sicher prüfen
!isnull(macd.value) && !isnull(macd.signal) &&
macd.value > macd.signal

// ADX: Alle DI-Werte prüfen
!isnull(adx14.value) && !isnull(adx14.plus_di) &&
adx14.value > 25 && adx14.plus_di > adx14.minus_di
```

### 6️⃣ Condition Evaluation Fehler

**Problem:** CEL-Expressions können Syntax- oder Runtime-Fehler haben.

#### 🔧 Validation vor Execution:

```python
# Backend: CEL Validation in cel_engine.py
engine = CELEngine()
result = engine.validate_expression("atrp > 0.5 && volume > 1000")
if not result.valid:
    logger.error(f"CEL Syntax Error: {result.error}")
```

#### ⚠️ Runtime Error Handling:

**Aktuelles Verhalten (cel_engine.py:120-140):**
- Bei Syntax-Fehler: Returns `False` + Log-Warnung
- Bei Runtime-Fehler: Returns `False` + Exception-Log
- Keine Exception-Propagation → Fail-Safe

```python
try:
    result = program(context)
    return result
except Exception as e:
    logger.error(f"CEL Runtime Error: {e}")
    return False  # Fail-safe: False bei Fehler
```

### 7️⃣ Error Handling Patterns - Zusammenfassung

#### ✅ GOLDEN RULES:

1. **IMMER Null-Checks für optionale Felder:**
   ```cel
   !isnull(field) && field > threshold
   ```

2. **IMMER Divisor-Check vor Division:**
   ```cel
   divisor > 0 ? (numerator / divisor) : 0
   ```

3. **IMMER Defaults mit `nz()` für kritische Werte:**
   ```cel
   nz(optional_value, safe_default)
   ```

4. **Verwende `coalesce()` für Fallback-Ketten:**
   ```cel
   coalesce(primary, secondary, tertiary, default)
   ```

5. **Klammere komplexe Null-Checks:**
   ```cel
   (!isnull(a) && a > 0) && (!isnull(b) && b > 0)
   ```

#### 📊 Error Handling Priority:

| Priority | Check | Beispiel |
|----------|-------|----------|
| 🔴 **KRITISCH** | Null-Check bei optionalen Feldern | `!isnull(spread_bps)` |
| 🟠 **HOCH** | Division durch Null vermeiden | `divisor > 0 ?` |
| 🟡 **MITTEL** | Indicator-Verfügbarkeit prüfen | `!isnull(rsi.value)` |
| 🟢 **NIEDRIG** | Type-Consistency (Backend-Job) | Pydantic Models |

#### 🎯 Template für sichere Rules:

```cel
// Template: Sicherer Regel-Ausdruck
(
  // 1. Null-Checks
  !isnull(required_field1) &&
  !isnull(required_field2) &&

  // 2. Value-Checks mit Defaults
  nz(optional_field, default_value) > threshold &&

  // 3. Division-Safe
  divisor > 0 &&

  // 4. Eigentliche Logik
  (numerator / divisor) > ratio &&

  // 5. Indicator-Checks
  !isnull(indicator.value) &&
  indicator.value > indicator_threshold
)
```

### 🚨 Debugging CEL Expressions

**Bei Problemen mit CEL Rules:**

1. **Prüfe Logs:**
   ```bash
   # cel_engine.py logged alle Errors
   grep "CEL" logs/trading_bot.log
   ```

2. **Teste Expression isoliert:**
   ```python
   from src.core.tradingbot.cel_engine import CELEngine
   engine = CELEngine()
   result = engine.validate_expression("your_expression")
   print(result.error if not result.valid else "OK")
   ```

3. **Reduziere Komplexität schrittweise:**
   ```cel
   // Start einfach
   atrp > 0.5

   // Füge Checks hinzu
   !isnull(atrp) && atrp > 0.5

   // Kombiniere
   !isnull(atrp) && atrp > 0.5 && volume > 1000
   ```

4. **Verwende explizite Klammern:**
   ```cel
   // Schwer zu debuggen
   a && b || c && d

   // Leicht zu debuggen
   (a && b) || (c && d)
   ```

---

## 📝 STRING & DATENTYP-FUNKTIONEN

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `type(x)` | `x: any` | `string` | Datentyp als String | `type(atrp)` → `"number"` |
| ✅ | `string(x)` | `x: any` | `string` | Konvertierung zu String | `string(123)` → `"123"` |
| ✅ | `int(x)` | `x: number/string` | `int` | Konvertierung zu Integer | `int(5.7)` → `5` |
| ✅ | `double(x)` | `x: any` | `number` | Konvertierung zu Double/Float | `double("3.14")` → `3.14` |
| ✅ | `bool(x)` | `x: any` | `bool` | Konvertierung zu Boolean | `bool("true")` → `true` |
| ✅ | `contains(s, substr)` | `s: string, substr: string` | `bool` | String enthält Substring | `contains("LONG_TREND", "LONG")` → `true` |
| ✅ | `startsWith(s, prefix)` | `s: string, prefix: string` | `bool` | String beginnt mit Prefix | `startsWith(strategy, "trend")` → `true/false` |
| ✅ | `endsWith(s, suffix)` | `s: string, suffix: string` | `bool` | String endet mit Suffix | `endsWith(strategy, "conservative")` → `true/false` |
| ✅ | `toLowerCase(s)` | `s: string` | `string` | String zu Kleinbuchstaben | `toLowerCase("BULLISH")` → `"bullish"` |
| ✅ | `toUpperCase(s)` | `s: string` | `string` | String zu Großbuchstaben | `toUpperCase("long")` → `"LONG"` |
| ✅ | `substring(s, start, end)` | `s: string, start: int, end: int` | `string` | Substring extrahieren | `substring("BTC_USDT", 0, 3)` → `"BTC"` |
| ✅ | `split(s, delimiter)` | `s: string, delimiter: string` | `string[]` | String splitten | `split("R0,R1,R2", ",")` → `["R0", "R1", "R2"]` |
| ✅ | `join(arr, delimiter)` | `arr: string[], delimiter: string` | `string` | Array zu String verbinden | `join(["a","b"], "-")` → `"a-b"` |

---

## 🔗 ARRAY & COLLECTION-FUNKTIONEN

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `size(arr)` / `length(arr)` | `arr: any[]` | `int` | Länge/Größe eines Arrays | `size([1,2,3])` → `3` |
| ✅ | `has(arr, element)` | `arr: any[], element: any` | `bool` | Array enthält Element | `has(regimes, "R1")` → `true/false` |
| ✅ | `all(arr, condition)` | `arr: any[], condition: bool` | `bool` | Alle Elemente erfüllen Bedingung | `all(volumes > 500)` → `true/false` |
| ✅ | `any(arr, condition)` | `arr: any[], condition: bool` | `bool` | Mindestens ein Element erfüllt | `any(values > 10)` → `true/false` |
| ✅ | `map(arr, expr)` | `arr: any[], expr: expr` | `any[]` | Transformation auf Array | `map(prices, x * 1.1)` |
| ✅ | `filter(arr, condition)` | `arr: any[], condition: bool` | `any[]` | Filtern nach Bedingung | `filter(volumes, x > 500)` |
| ✅ | `first(arr)` | `arr: any[]` | `any` | Erstes Element | `first(regimes)` → Element |
| ✅ | `last(arr)` | `arr: any[]` | `any` | Letztes Element | `last(regimes)` → Element |
| ✅ | `sum(arr)` | `arr: number[]` | `number` | Summe aller Elemente | `sum([1,2,3,4])` → `10` |
| ✅ | `avg(arr)` / `average(arr)` | `arr: number[]` | `number` | Durchschnitt | `avg([10,20,30])` → `20` |
| ✅ | `min(arr)` | `arr: number[]` | `number` | Minimum im Array | `min([5,10,3])` → `3` |
| ✅ | `max(arr)` | `arr: number[]` | `number` | Maximum im Array | `max([5,10,3])` → `10` |
| ✅ | `distinct(arr)` | `arr: any[]` | `any[]` | Duplikate entfernen | `distinct([1,1,2,2,3])` → `[1,2,3]` |
| ✅ | `sort(arr)` | `arr: number[]` | `number[]` | Array sortieren | `sort([3,1,2])` → `[1,2,3]` |
| ✅ | `reverse(arr)` | `arr: any[]` | `any[]` | Array umkehren | `reverse([1,2,3])` → `[3,2,1]` |
| ❌ | `contains(arr, element)` | `arr: any[], element: any` | `bool` | Nicht verfügbar für Arrays (nutze `has(arr, element)`) | `has(no_trade_regimes, regime)` |
| ✅ | `indexOf(arr, element)` | `arr: any[], element: any` | `int` | Index eines Elements (-1 wenn nicht gefunden) | `indexOf(regimes, "R1")` → `1` |
| ✅ | `slice(arr, start, end)` | `arr: any[], start: int, end: int` | `any[]` | Array-Ausschnitt | `slice(arr, 0, 3)` |

---

## 🎯 TRADING-SPEZIFISCHE FUNKTIONEN

### Basis-Funktionen

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `isnull(x)` | `x: any` | `bool` | Wert ist null/undefined | `isnull(spread_bps)` → `true/false` |
| ❌ | `isnotnull(x)` | `x: any` | `bool` | Wert ist NICHT null | `isnotnull(obi)` → `true/false` |
| ✅ | `nz(x, default)` | `x: any, default: any` | `any` | Null-Ersatz (coalesce) | `nz(obi, 0)` → Wert oder 0 |
| ✅ | `coalesce(a, b, c, ...)` | `a, b, c, ...: any` | `any` | Erstes nicht-null Element | `coalesce(trade.tr_stop_price, trade.stop_price)` |
| ✅ | `clamp(x, min, max)` | `x, min, max: number` | `number` | Wert zwischen min und max | `clamp(atrp, 0.1, 2.5)` |

### Prozentuale Berechnungen

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `pct_change(old, new)` | `old, new: number` | `number` | Prozentuale Veränderung | `pct_change(95336, 95159)` → `-0.18` |
| ✅ | `pct_from_level(price, level)` | `price, level: number` | `number` | % Abstand zu Level | `pct_from_level(95336, 95159)` → `0.18` |
| ✅ | `level_at_pct(entry, pct, side)` | `entry: number, pct: number, side: string` | `number` | Preis bei % Abstand | `level_at_pct(100, 1.0, "long")` → `99` |
| ✅ | `retracement(from, to, pct)` | `from, to, pct: number` | `number` | Fibonacci Retracement Level | `retracement(95000, 96000, 0.618)` |
| ✅ | `extension(from, to, pct)` | `from, to, pct: number` | `number` | Fibonacci Extension Level | `extension(95000, 96000, 1.618)` |

### Statusprüfung

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `is_trade_open(trade)` | `trade: dict` | `bool` | Ist Trade aktuell offen | `is_trade_open(trade)` |
| ✅ | `is_long(trade)` | `trade: dict` | `bool` | Ist aktueller Trade long | `is_long(trade)` |
| ✅ | `is_short(trade)` | `trade: dict` | `bool` | Ist aktueller Trade short | `is_short(trade)` |
| ✅ | `is_bullish_signal(strategy)` | `strategy: dict` | `bool` | Übergeordneter Bias bullish | `is_bullish_signal(strategy)` |
| ✅ | `is_bearish_signal(strategy)` | `strategy: dict` | `bool` | Übergeordneter Bias bearish | `is_bearish_signal(strategy)` |
| ✅ | `in_regime(regime, r)` | `regime: string|list, r: string` | `bool` | Bin ich in Regime R | `in_regime(regime.current, "R1")` |

### Preisfunktionen

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `stop_hit_long(trade, current_price)` | `trade: dict, current_price: number` | `bool` | Long StopLoss getroffen | `stop_hit_long(trade, chart.price)` |
| ✅ | `stop_hit_short(trade, current_price)` | `trade: dict, current_price: number` | `bool` | Short StopLoss getroffen | `stop_hit_short(trade, chart.price)` |
| ✅ | `tp_hit(trade, current_price)` | `trade: dict, current_price: number` | `bool` | TakeProfit getroffen | `tp_hit(trade, chart.price)` |
| ✅ | `price_above_ema(price, ema)` | `price: number, ema: number` | `bool` | Preis über EMA | `price_above_ema(chart.price, ema21.value)` |
| ✅ | `price_below_ema(price, ema)` | `price: number, ema: number` | `bool` | Preis unter EMA | `price_below_ema(chart.price, ema21.value)` |
| ✅ | `price_above_level(price, level)` | `price: number, level: number` | `bool` | Preis über Level | `price_above_level(chart.price, 95000)` |
| ✅ | `price_below_level(price, level)` | `price: number, level: number` | `bool` | Preis unter Level | `price_below_level(chart.price, 95000)` |

### Pattern Functions (Candlestick & Chart Patterns)

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `pin_bar_bullish()` | keine | `bool` | Bullish Pin Bar erkannt | `pin_bar_bullish()` |
| ✅ | `pin_bar_bearish()` | keine | `bool` | Bearish Pin Bar erkannt | `pin_bar_bearish()` |
| ✅ | `inside_bar()` | keine | `bool` | Inside Bar erkannt | `inside_bar()` |
| ✅ | `inverted_hammer()` | keine | `bool` | Inverted Hammer erkannt | `inverted_hammer()` |
| ✅ | `bull_flag()` | keine | `bool` | Bull Flag erkannt | `bull_flag()` |
| ✅ | `bear_flag()` | keine | `bool` | Bear Flag erkannt | `bear_flag()` |
| ✅ | `cup_and_handle()` | keine | `bool` | Cup & Handle erkannt | `cup_and_handle()` |
| ✅ | `double_bottom()` | keine | `bool` | Double Bottom erkannt | `double_bottom()` |
| ✅ | `double_top()` | keine | `bool` | Double Top erkannt | `double_top()` |
| ✅ | `ascending_triangle()` | keine | `bool` | Ascending Triangle erkannt | `ascending_triangle()` |
| ✅ | `descending_triangle()` | keine | `bool` | Descending Triangle erkannt | `descending_triangle()` |

### Breakout Functions

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `breakout_above()` | keine | `bool` | Breakout über Level/Pivot | `breakout_above()` |
| ✅ | `breakdown_below()` | keine | `bool` | Breakdown unter Level/Pivot | `breakdown_below()` |
| ✅ | `false_breakout()` | keine | `bool` | False Breakout erkannt | `false_breakout()` |
| ✅ | `break_of_structure()` | keine | `bool` | Break of Structure (BOS) | `break_of_structure()` |

### Smart Money Concepts (SMC)

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `liquidity_swept()` | keine | `bool` | Liquidity Sweep erkannt | `liquidity_swept()` |
| ✅ | `fvg_exists()` | keine | `bool` | Fair Value Gap erkannt | `fvg_exists()` |
| ✅ | `order_block_retest()` | keine | `bool` | Order Block Retest | `order_block_retest()` |
| ✅ | `harmonic_pattern_detected()` | keine | `bool` | Harmonic Pattern erkannt | `harmonic_pattern_detected()` |

---

## 🚫 NO ENTRY FILTER & 🎯 REGIME FUNCTIONS

**NEU in Version 2.4 (2026-01-28)**

Diese neuen Funktionen und Workflows sind **vollständig dokumentiert** in:

📄 **`04_Knowledgbase/CEL_Neue_Funktionen_v2.4.md`**

### Kurz-Übersicht:

**No Entry Workflow:**
- Sicherheitsfilter zum Blockieren von Trades unter gefährlichen Bedingungen
- Use Cases: News Events, Hohe Volatilität, Choppy Markets, Regime Filter
- Beispiel: `atrp > cfg.max_atrp_pct || has(cfg.no_trade_regimes, regime)`

**Regime Functions (2 neue Funktionen):**

| Function | Return | Beschreibung | Beispiel |
|----------|--------|-------------|----------|
| ✅ `last_closed_regime()` | `string` | Regime der letzten geschlossenen Kerze | `last_closed_regime() == 'EXTREME_BULL'` |
| ✅ `trigger_regime_analysis()` | `bool` | Löst Regime-Analyse aus | `trigger_regime_analysis() && last_closed_regime() == 'BULL'` |

**Verfügbare Variablen (69+):**
- **bot.*** (27 Variablen) - Bot Configuration, Risk Management, SL/TP
- **chart.*** (18 Variablen) - OHLCV, Chart Info, Candle Analysis
- **market** (9 Variablen) - Price, Volume, Regime
- **trade.*** (9 Variablen) - Position, Performance, Duration
- **cfg.*** (6 Variablen) - Trading Rules, Filters
- **project.*** (dynamisch) - User-defined custom variables

**Vollständige Dokumentation:** Siehe `CEL_Neue_Funktionen_v2.4.md`

---

## 📊 TECHNISCHE INDIKATOREN (IMPLEMENTIERT)

### ✅ Verfügbare Indikatoren (IndicatorType Enum)

Die folgenden Indikatoren sind über `config/models.py` definiert und können in JSON-Configs verwendet werden:

| Indikator | Type | Parameter | Rückgabe | Beschreibung |
|-----------|------|-----------|----------|-------------|
| **SMA** | `SMA` | `period: int` | `{value: number}` | Simple Moving Average |
| **EMA** | `EMA` | `period: int` | `{value: number}` | Exponential Moving Average |
| **WMA** | `WMA` | `period: int` | `{value: number}` | Weighted Moving Average |
| **RSI** | `RSI` | `period: int` | `{value: number}` | Relative Strength Index (0-100) |
| **MACD** | `MACD` | `fast: int, slow: int, signal: int` | `{value: number, signal: number, histogram: number}` | MACD |
| **STOCH** | `STOCH` | `k_period: int, k_smooth: int, d_period: int` | `{k: number, d: number}` | Stochastic Oscillator |
| **CCI** | `CCI` | `period: int` | `{value: number}` | Commodity Channel Index |
| **MFI** | `MFI` | `period: int` | `{value: number}` | Money Flow Index |
| **ATR** | `ATR` | `period: int` | `{value: number}` | Average True Range |
| **BB** | `BB` | `period: int, std_dev: number` | `{upper: number, middle: number, lower: number, width: number}` | Bollinger Bands |
| **ADX** | `ADX` | `period: int` | `{value: number, plus_di: number, minus_di: number}` | Average Directional Index |
| **VOLUME** | `VOLUME` | - | `{value: number}` | Volumen |
| **VOLUME_RATIO** | `VOLUME_RATIO` | `period: int` | `{value: number}` | Volumen-Verhältnis zu Durchschnitt |
| **PRICE** | `PRICE` | - | `{value: number}` | Aktueller Preis |
| **PRICE_CHANGE** | `PRICE_CHANGE` | `period: int` | `{value: number}` | Preisänderung in % |
| **MOMENTUM_SCORE** | `MOMENTUM_SCORE` | `period: int` | `{value: number}` | Momentum Score |
| **PRICE_STRENGTH** | `PRICE_STRENGTH` | `period: int` | `{value: number}` | Price Strength |
| **CHOP** | `CHOP` | `period: int` | `{value: number}` | Choppiness Index |

### 📖 Verwendung in CEL-Expressions

```cel
// Zugriff auf Indikator-Werte via indicator_id
"expr": "rsi14.value > 60"  // RSI(14) > 60

"expr": "macd_12_26_9.value > macd_12_26_9.signal"  // MACD Cross

"expr": "close > bb_20_2.upper"  // Preis über oberer BB

"expr": "adx14.value > 25 && adx14.plus_di > adx14.minus_di"  // Starker Uptrend

"expr": "volume_ratio_20.value > 1.5"  // Volumen 50% über Durchschnitt
```

### 🔧 Custom Indicators

| Indikator | Type | Parameter | Rückgabe | Beschreibung |
|-----------|------|-----------|----------|-------------|
| **PIVOTS** | `PIVOTS` | `method: string ("traditional", "fibonacci", "camarilla")` | `{pivot, r1, r2, r3, s1, s2, s3}` | Pivot Points |
| **SUPPORT_RESISTANCE** | `SUPPORT_RESISTANCE` | `window: int, num_levels: int` | `{support_levels: number[], resistance_levels: number[]}` | S/R Levels |
| **PATTERN** | `PATTERN` | - | `{patterns: array, count: int}` | Pattern Detection (siehe unten) |

---

## 🎯 PATTERN-ERKENNUNG (TA-LIB)

### ✅ Implementierte Patterns (via TA-Lib)

Die folgenden Candlestick-Patterns werden über TA-Lib erkannt (`custom.py`):

| Pattern | TA-Lib Funktion | Signal | Beschreibung |
|---------|-----------------|--------|-------------|
| **Hammer** | `talib.CDLHAMMER` | `+100` (bullish) | Hammer Pattern |
| **Doji** | `talib.CDLDOJI` | `±100` | Doji Pattern |
| **Engulfing** | `talib.CDLENGULFING` | `+100` (bull) / `-100` (bear) | Engulfing Pattern |
| **Harami** | `talib.CDLHARAMI` | `+100` (bull) / `-100` (bear) | Harami Pattern |
| **Morning Star** | `talib.CDLMORNINGSTAR` | `+100` | Morning Star (bullish reversal) |
| **Evening Star** | `talib.CDLEVENINGSTAR` | `-100` | Evening Star (bearish reversal) |
| **Three White Soldiers** | `talib.CDL3WHITESOLDIERS` | `+100` | Three White Soldiers |
| **Three Black Crows** | `talib.CDL3BLACKCROWS` | `-100` | Three Black Crows |

### 📖 Verwendung

Pattern-Erkennung erfolgt über `IndicatorType.PATTERN`:

```python
# JSON Config
{
  "id": "candlestick_patterns",
  "type": "PATTERN",
  "params": {}
}
```

```cel
// CEL Expression - Pattern-Check
"expr": "candlestick_patterns.count > 0"  // Mind. 1 Pattern erkannt

"expr": "has(candlestick_patterns.patterns.map(p => p.pattern), \"engulfing\")"  // Engulfing erkannt
```

### ✅ CEL Pattern-/Breakout-/SMC-Funktionen (Context-basiert)

Die folgenden Funktionen sind **implementiert** und werden über Kontext-Flags aus der
Pattern-/Breakout-/SMC-Erkennung bereitgestellt:

- Pattern: `pin_bar_bullish()`, `pin_bar_bearish()`, `inside_bar()`, `inverted_hammer()`,
  `bull_flag()`, `bear_flag()`, `cup_and_handle()`, `double_bottom()`, `double_top()`,
  `ascending_triangle()`, `descending_triangle()`
- Breakout: `breakout_above()`, `breakdown_below()`, `false_breakout()`, `break_of_structure()`
- SMC: `liquidity_swept()`, `fvg_exists()`, `order_block_retest()`, `harmonic_pattern_detected()`

**Kontext-Quellen (Beispiele):**

```json
{
  "pattern": {"pin_bar_bullish": true, "double_top": false},
  "breakout": {"breakout_above": true},
  "smc": {"fvg_exists": true}
}
```

Die CEL-Funktionen lesen diese Flags automatisch aus `pattern.*`, `breakout.*` und `smc.*`.

---

## 🚀 ENTRY ANALYZER METHODEN

### UI Methoden (entry_analyzer_popup.py)

Diese Methoden stehen über die Entry Analyzer UI zur Verfügung:

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `_on_run_backtest_clicked()` | - | `None` | Führt Backtest mit JSON-Config aus |
| `_on_load_strategy_clicked()` | - | `None` | Lädt JSON-Strategy-Config |
| `_on_analyze_current_regime_clicked()` | - | `None` | Analysiert aktuelles Marktregime |
| `_convert_candles_to_dataframe()` | `candles: list[dict]` | `pd.DataFrame` | Konvertiert Candles zu DataFrame |
| `_on_backtest_finished()` | `results: dict` | `None` | Callback nach Backtest-Completion |
| `_on_backtest_error()` | `error: str` | `None` | Fehlerbehandlung für Backtest |
| `_draw_regime_boundaries()` | `results: dict` | `None` | Zeichnet Regime-Grenzen im Chart |
| `_on_optimize_indicators_clicked()` | - | `None` | Startet Indicator-Optimization |
| `_on_optimization_finished()` | `results: list` | `None` | Callback nach Optimization |
| `_on_create_regime_set_clicked()` | - | `None` | Erstellt Regime-Set aus Optimization |
| `_generate_regime_set_json()` | `regime_set: dict, set_name: str` | `dict` | Generiert JSON-Config aus Regime-Set |
| `_generate_regime_conditions()` | `regime_name: str` | `dict` | Generiert Regime-Conditions |
| `_generate_entry_conditions()` | `indicator_ids: list` | `dict` | Generiert Entry-Conditions |
| `_backtest_regime_set()` | `config_path: Path` | `None` | Testet Regime-Set-Config |
| `_on_pattern_analyze_clicked()` | - | `None` | Analysiert Patterns im Chart |

### Backtest Workflow

```
1. User klickt "Run Backtest"
   ↓
2. _on_run_backtest_clicked()
   → Lädt JSON-Config
   → Validiert Parameter
   → Startet BacktestThread
   ↓
3. BacktestEngine.run()
   → Lädt Multi-Timeframe-Daten
   → Berechnet Indikatoren
   → Evaluiert Regimes
   → Routet zu Strategy Sets
   → Simuliert Trades
   ↓
4. _on_backtest_finished(results)
   → Zeigt Performance-Metriken
   → Zeichnet Regime-Grenzen
   → Listet Trades
```

---

## ⚙️ CONFIG SYSTEM API

### ConditionEvaluator

**Klasse:** `src/core/tradingbot/config/evaluator.py`

**Zwei Evaluation-Modi:**

1. **Operator-basiert (legacy):**
```python
# JSON
{
  "left": {"indicator_id": "rsi14", "field": "value"},
  "op": "gt",
  "right": {"value": 60}
}
```

2. **CEL Expressions (neu):**
```python
# JSON
{
  "cel_expression": "rsi14.value > 60 && adx14.value > 25"
}
```

**Methoden:**

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `evaluate_condition()` | `condition: Condition` | `bool` | Evaluiert Single Condition |
| `evaluate_group()` | `group: ConditionGroup` | `bool` | Evaluiert Logic Group (AND/OR) |
| `_resolve_operand()` | `operand: IndicatorRef \| ConstantValue` | `float` | Löst Indicator-Referenz oder Konstante auf |

### RegimeDetector

**Klasse:** `src/core/tradingbot/config/detector.py`

**Methoden:**

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `detect_active_regimes()` | `indicator_values: dict, scope: str = 'entry'` | `list[RegimeMatch]` | Erkennt aktive Regimes |
| `get_highest_priority_regime()` | `active_regimes: list` | `RegimeMatch \| None` | Höchste Priorität |
| `is_regime_active()` | `regime_id: str, indicator_values: dict` | `bool` | Ist Regime aktiv? |
| `get_active_regimes_by_scope()` | `active_regimes: list, scope: str` | `list[RegimeMatch]` | Filtert nach Scope |
| `get_regime_definition()` | `regime_id: str` | `RegimeDefinition \| None` | Gibt Regime-Definition zurück |

### StrategyRouter

**Klasse:** `src/core/tradingbot/config/router.py`

**Methoden:**

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `route_regimes()` | `active_regimes: list` | `MatchedStrategySet \| None` | Routet Regimes zu Strategy Set |
| `get_strategy_set()` | `strategy_set_id: str` | `StrategySetDefinition \| None` | Gibt Strategy Set zurück |
| `get_all_strategy_sets()` | - | `list[StrategySetDefinition]` | Alle Strategy Sets |
| `get_routing_rules_for_regime()` | `regime_id: str` | `list[RoutingRule]` | Routing-Regeln für Regime |

### StrategySetExecutor

**Klasse:** `src/core/tradingbot/config/executor.py`

**Methoden:**

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `prepare_execution()` | `matched_set: MatchedStrategySet` | `None` | Wendet Parameter-Overrides an |
| `restore_state()` | - | `None` | Stellt Original-Parameter wieder her |
| `get_current_indicator()` | `indicator_id: str` | `IndicatorDefinition \| None` | Aktueller Indicator |
| `get_current_strategy()` | `strategy_id: str` | `StrategyDefinition \| None` | Aktuelle Strategy |
| `get_strategy_ids_from_set()` | `strategy_set_id: str` | `list[str]` | Strategy-IDs aus Set |

### Workflow: Regime Detection → Routing → Execution

```
1. indicator_values = IndicatorValueCalculator.calculate(features)
   ↓
2. active_regimes = RegimeDetector.detect_active_regimes(indicator_values, scope='entry')
   ↓
3. matched_set = StrategyRouter.route_regimes(active_regimes)
   ↓
4. StrategySetExecutor.prepare_execution(matched_set)
   → Wendet Indicator-Overrides an
   → Wendet Strategy-Overrides an
   ↓
5. Entry-Evaluation mit angepassten Parametern
```

---

## ⏰ ZEITFUNKTIONEN

| Status | Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|--------|-----------|----------|-------------|----------|
| ✅ | `now()` | keine | `int` | Aktuelle Unix-Zeit (Sekunden) | `now()` → `1737350640` |
| ✅ | `timestamp(dt)` | `dt: datetime|string|int` | `int` | Datum → Unix‑Timestamp | `timestamp("2024-01-15")` |
| ✅ | `bar_age(bar_time)` | `bar_time: datetime|string|int` | `int` | Alter eines Bars in Sekunden | `bar_age(trade.entry_time)` |
| ✅ | `bars_since(trade, current_bar)` | `trade: dict, current_bar: int` | `int` | Bars seit Entry | `bars_since(trade, chart.candle_count)` |
| ❌ | `is_time_in_range(start, end)` | `start, end: string (HH:MM)` | `bool` | Zeit im Bereich | `is_time_in_range("09:00", "16:00")` |
| ✅ | `is_new_day(prev_time, curr_time)` | `prev_time, curr_time: datetime|string|int` | `bool` | Tageswechsel erkannt | `is_new_day(trade.prev_time, trade.curr_time)` |
| ✅ | `is_new_hour(prev_time, curr_time)` | `prev_time, curr_time: datetime|string|int` | `bool` | Stundenwechsel erkannt | `is_new_hour(prev_time, curr_time)` |
| ✅ | `is_new_week(prev_time, curr_time)` | `prev_time, curr_time: datetime|string|int` | `bool` | Wochenwechsel erkannt | `is_new_week(prev_time, curr_time)` |
| ✅ | `is_new_month(prev_time, curr_time)` | `prev_time, curr_time: datetime|string|int` | `bool` | Monatswechsel erkannt | `is_new_month(prev_time, curr_time)` |
| ❌ | `time_hours_ago(hours)` | `hours: int` | `int` | Timestamp von vor N Stunden | `time_hours_ago(1)` |
| ❌ | `seconds_since(timestamp)` | `timestamp: int` | `int` | Sekunden seit Timestamp | `seconds_since(entry_timestamp)` |

---

## 🔍 VARIABLE & KONTEXT-ZUGRIFF (AKTUELLER STAND)

Der CEL‑Kontext wird über `CELContextBuilder` aufgebaut und nutzt **Namespaces**.

### Chart‑Variablen (`chart.*`)
Aus `ChartDataProvider` (aktuelle/letzte Kerze):

```cel
chart.price, chart.open, chart.high, chart.low, chart.volume
chart.symbol, chart.timeframe, chart.candle_count
chart.range, chart.body, chart.is_bullish, chart.is_bearish
chart.upper_wick, chart.lower_wick
chart.prev_close, chart.prev_high, chart.prev_low
chart.change, chart.change_pct
```

### Bot‑Variablen (`bot.*`)
Aus `BotConfigProvider` (Risk/Session/AI):

```cel
bot.symbol, bot.leverage, bot.paper_mode
bot.risk_per_trade_pct, bot.max_daily_loss_pct, bot.max_position_size_btc
bot.sl_atr_multiplier, bot.tp_atr_multiplier
bot.trailing_stop_enabled, bot.trailing_stop_atr_mult, bot.trailing_stop_activation_pct
bot.min_confluence_score, bot.require_regime_alignment
bot.session.enabled, bot.session.start_utc, bot.session.end_utc, bot.session.close_at_end
bot.ai.enabled, bot.ai.confidence_threshold, bot.ai.min_confluence_for_ai, bot.ai.fallback_to_technical
```

### Project‑Variablen (`project.*`)
Aus `.cel_variables.json` (projektweit definierte Variablen):

```cel
project.entry_min_price, project.max_spread_bps, project.allowed_regimes, ...
```

### Regime‑Variablen (`regime.*`)
Nur verfügbar, wenn Regime‑Daten geliefert werden:

```cel
regime.current, regime.strength, regime.trend, ...
```

### Trade‑Variablen (`trade.*`)
Vom Trading‑System bereitgestellt:

```cel
trade.side, trade.entry_price, trade.avg_entry_price
trade.stop_price, trade.stop_loss, trade.tp_price, trade.take_profit
trade.pnl_pct, trade.pnl_usdt, trade.status
trade.bars_in_trade, trade.entry_bar
```

**Robuste Nutzung (falls Werte fehlen):**

```cel
coalesce(trade.entry_price, trade.avg_entry_price)
```

---

## 📤 RÜCKGABEPARAMETER NACH REGELTYP

### 1. **EXIT Regeln** (Severity: "exit")
```
Rückgabe: boolean
- true  → Position SOFORT schließen
- false → Keine Aktion

Beispiele:
"expr": "trade.side == \"long\" ? trade.current_price <= trade.stop_price : trade.current_price >= trade.stop_price"
→ true = SL getroffen, Position schließen

"expr": "trade.fees_pct >= cfg.max_fees_pct"
→ true = Gebühren zu hoch, Position schließen
```

### 2. **UPDATE_STOP Regeln** (Severity: "update_stop", Result_Type: "number_or_null")
```
Rückgabe: number | null
- number → Neuen Stop setzen (ABER: monotonic!)
  * Long: stop = max(old_stop, new_stop)   [nie lockern]
  * Short: stop = min(old_stop, new_stop)  [nie lockern]
- null   → Ignorieren, keinen neuen Stop setzen

Beispiele:
"expr": "trade.pnl_pct >= trade.tr_lock_pct ? (trade.side == \"long\" ? max(trade.stop_price, trade.entry_price) : min(trade.stop_price, trade.entry_price)) : null"
→ Rückkehr: neuer Stop bei Break-Even ODER null

"expr": "trade.pnl_pct >= trade.tra_pct ? (trade.side == \"long\" ? max(trade.stop_price, trade.current_price * (1.0 - (trade.tr_pct/100.0))) : min(trade.stop_price, trade.current_price * (1.0 + (trade.tr_pct/100.0)))) : null"
→ Rückkehr: neuer Trailing Stop ODER null
```

### 3. **BLOCK Regeln** (Severity: "block")
```
Rückgabe: boolean
- true  → BLOCKIEREN (Bedingung erfüllt = nicht handeln)
- false → ERLAUBEN (Bedingung nicht erfüllt = handeln OK)

Abhängig von Kontext:
- no_trade Pack: true = kein neuer Trade
- entry Pack: true = kein Entry erlaubt
- risk Pack: true = Risiko nicht akzeptabel

Beispiele:
"expr": "volume < pctl(volume, cfg.min_volume_pctl, cfg.min_volume_window) && atrp < cfg.min_atrp_pct"
→ true = blockieren, zu wenig Volumen UND zu niedrig Volatilität

"expr": "!isnull(spread_bps) && spread_bps > cfg.max_spread_bps"
→ true = blockieren, Spread zu hoch
```

---

## 🎯 PRAKTISCHE BEISPIELE

### Scalping (EMA + Stochastic + Volume)

```cel
// Entry-Blocker: Volumen zu niedrig
"expr": "volume_ratio_20.value < 1.5"
// → true = blockieren (zu wenig Volumen)

// Entry-Blocker: RSI zu extrem
"expr": "rsi5.value > 80 || rsi5.value < 20"
// → true = blockieren, RSI zu extrem (falsches Signal)

// Entry-Signal: EMA Cross + Stochastic
"expr": "close > ema34.value && stoch_5_3_3.k < 20 && volume_ratio_20.value > 1.5"
// → true = Entry erlaubt (alle Bedingungen erfüllt)

// Exit: Stop Hit
"expr": "trade.side == \"long\" ? close <= trade.stop_price : close >= trade.stop_price"
// → true = Exit (Stop getroffen)
```

### Day Trading (Engulfing + Volume)

```cel
// Pattern-Erkennung
"expr": "candlestick_patterns.count > 0 && volume_ratio_20.value > 1.5"
// → true = Pattern mit Volume-Bestätigung

// Entry-Gate: Regime Check
"expr": "!(regime in cfg.no_trade_regimes)"
// → true = Entry erlaubt (Regime ist nicht blockiert)

// Risk-Check: Maximale Gebühren
"expr": "trade.fees_pct < cfg.max_fees_pct"
// → true = Erlaubt (Gebühren OK)
```

### Range Trading (Grid)

```cel
// Entry-Blocker: Nicht in Range
"expr": "close > resistance_level || close < support_level"
// → true = blockieren (außerhalb Range)

// Entry: Am Support
"expr": "close <= support_level + (atr14.value * 0.5) && close > support_level - (atr14.value * 0.5)"
// → true = Entry bei Support

// Breakout Stop-Loss: Außerhalb Range
"expr": "close > resistance_level"
// → true = Exit (Range durchbrochen)
```

### Breakout (3-Layer Confirmation)

```cel
// Layer 1: Struktureller Breakout
"expr": "close > resistance_level"
// → true = Echter Ausbruch

// Layer 2: Volume-Bestätigung
"expr": "volume_ratio_20.value > 1.5"
// → true = Volume bestätigt

// Layer 3: Confluence (Technisch)
"expr": "close > ema50.value && stoch_14_3_3.k > 50"
// → true = Technische Bestätigung

// Gesamtregel kombiniert
"expr": "close > resistance_level && volume_ratio_20.value > 1.5 && close > ema50.value"
// → true = Entry (alle 3 Layer bestätigt)
```

---

## ⚙️ IMPLEMENTIERUNGS-CHECKLIST

### MUST HAVE (Essentiell) ✅

- [x] Alle mathematischen Operatoren (`+`, `-`, `*`, `/`, `%`, `^`)
- [x] Alle Vergleichsoperatoren (`==`, `!=`, `<`, `>`, `<=`, `>=`)
- [x] Logische Operatoren (`&&`, `||`, `!`)
- [x] Ternär-Operator (`? :`)
- [x] `min()`, `max()`, `abs()`
- [x] `isnull()`, `nz()`
- [x] Array-Operationen (`in`, `contains()`)
- [x] String-Operationen (`contains()`, `startsWith()`, `endsWith()`)

### SHOULD HAVE (Stark empfohlen) ✅

- [x] `ConditionEvaluator` - Operator-basiert + CEL Expressions
- [x] 18 Indikatoren über `IndicatorType` enum
- [x] 8 TA-Lib Candlestick Patterns
- [x] `RegimeDetector` - Regime-Klassifikation
- [x] `StrategyRouter` - Strategy Set Routing
- [x] `StrategySetExecutor` - Parameter Overrides
- [x] Entry Analyzer UI - Backtesting + Optimization

### NICE TO HAVE (Optional) ✅

- [x] Advanced Pattern Functions (pin_bar, inside_bar, bull_flag, etc.)
- [x] `breakout_above()`, `breakdown_below()`, `false_breakout()`
- [x] Smart Money Concepts (OB, FVG, Liquidity Sweep)
- [x] Harmonic Pattern Functions
- [ ] `fibonacci_support()`, `fibonacci_resistance()`

---

## 📌 WICHTIGE ÄNDERUNGEN VON v1.0 → v2.0

### ✅ NEU Hinzugefügt

1. **IndicatorType Enum** - 18 definierte Indikatoren mit exakten Parametern
2. **TA-Lib Pattern Detection** - 8 Candlestick Patterns
3. **Entry Analyzer Methoden** - Vollständige UI-API-Dokumentation
4. **Config System API** - ConditionEvaluator, RegimeDetector, Router, Executor
5. **CEL Expression Unterstützung** - Komplexe Conditions mit `cel_expression`
6. **Custom Indicators** - PIVOTS, SUPPORT_RESISTANCE, PATTERN

### ✅ REAKTIVIERT (Stand 2026-01-28)

1. **Pattern Functions** (pin_bar, inside_bar, bull/bear_flag, cup_and_handle, double_top/bottom, triangles)
2. **Breakout Functions** (breakout_above/below, false_breakout, break_of_structure)
3. **Smart Money Concepts** (liquidity_swept, fvg_exists, order_block_retest, harmonic_pattern_detected)

### 🔧 AKTUALISIERT

1. **Indicator Zugriff** - Von `ema(period)` zu `ema34.value` (via indicator_id)
2. **Pattern Detection** - Von direkten Funktionen zu TA-Lib Integration
3. **Condition Evaluation** - Zwei Modi: Operator-basiert + CEL

---

## 🗺️ ROADMAP – Restliche (nicht implementierte) Funktionen

Aktuell sind **93 Funktionen implementiert**. Nicht implementiert (bewusst):
- `log()`, `log10()`
- `sin()`, `cos()`, `tan()`
- `is_time_in_range()`

Alle weiteren Funktionen aus Phase 1 sind abgeschlossen.

---

## 📚 REFERENZEN

**Implementierte Dateien:**
- `src/core/tradingbot/config/models.py` - Pydantic Models (IndicatorType, ConditionOperator, etc.)
- `src/core/tradingbot/config/evaluator.py` - ConditionEvaluator
- `src/core/tradingbot/config/detector.py` - RegimeDetector
- `src/core/tradingbot/config/router.py` - StrategyRouter
- `src/core/tradingbot/config/executor.py` - StrategySetExecutor
- `src/core/indicators/custom.py` - PIVOTS, SUPPORT_RESISTANCE, PATTERN
- `src/ui/dialogs/entry_analyzer_popup.py` - Entry Analyzer UI
- `src/strategies/strategy_models.py` - 40 Pattern Strategies

**Version:** 2.3 (Aktualisiert - Implementierungsstatus & Signaturen)
**Erstellt:** 20. Januar 2026
**Audit:** 28. Januar 2026
**Status:** ✅ **Aktueller Stand übernommen (93 Funktionen implementiert)**
**Zielgruppe:** Trading Bot CEL Engine Entwicklung
**Implementierungsplan:** `01_Projectplan/260127_Fertigstellung CEL Editor/3_Umsetzungsplan_CEL_System_100_Prozent.md`
