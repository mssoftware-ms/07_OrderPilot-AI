# CEL Skriptsprache - Vollständige Befehls- und Funktionsliste
## Trading Bot & Entry Analyzer Implementation (Aligned Version)

**Datum:** 20. Januar 2026
**Version:** 2.0 (Abgeglichen mit tatsächlichen Implementierungen)
**Zielumgebung:** CEL Expression Language für TradingBot Analyzer

---

## 📋 INHALTSÜBERSICHT

1. [Mathematische Funktionen](#mathematische-funktionen)
2. [Logische & Vergleichsoperatoren](#logische--vergleichsoperatoren)
3. [String & Datentyp-Funktionen](#string--datentyp-funktionen)
4. [Array & Collection-Funktionen](#array--collection-funktionen)
5. [Trading-spezifische Funktionen](#trading-spezifische-funktionen)
6. [Technische Indikatoren (IMPLEMENTIERT)](#technische-indikatoren-implementiert)
7. [Pattern-Erkennung (TA-Lib)](#pattern-erkennung-ta-lib)
8. [Entry Analyzer Methoden](#entry-analyzer-methoden)
9. [Config System API](#config-system-api)
10. [Zeitfunktionen](#zeitfunktionen)
11. [Variable & Kontext-Zugriff](#variable--kontext-zugriff)
12. [Rückgabeparameter nach Regeltyp](#rückgabeparameter-nach-regeltyp)

---

## 🔢 MATHEMATISCHE FUNKTIONEN

| Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|-----------|----------|-------------|----------|
| `abs(x)` | `x: number` | `number` | Absoluter Wert (ohne Vorzeichen) | `abs(-5.5)` → `5.5` |
| `min(a, b)` | `a, b: number` | `number` | Minimum von zwei Werten | `min(10, 5)` → `5` |
| `max(a, b)` | `a, b: number` | `number` | Maximum von zwei Werten | `max(10, 5)` → `10` |
| `round(x)` | `x: number` | `number` | Auf nächste ganze Zahl runden | `round(5.7)` → `6` |
| `floor(x)` | `x: number` | `number` | Abrunden (Boden) | `floor(5.7)` → `5` |
| `ceil(x)` | `x: number` | `number` | Aufrunden (Decke) | `ceil(5.3)` → `6` |
| `pow(x, y)` | `x: number, y: number` | `number` | x hoch y (Potenz) | `pow(2, 3)` → `8` |
| `sqrt(x)` | `x: number` | `number` | Quadratwurzel | `sqrt(9)` → `3` |
| `log(x)` | `x: number` | `number` | Natürlicher Logarithmus | `log(2.718)` → `1` |
| `log10(x)` | `x: number` | `number` | 10er Logarithmus | `log10(100)` → `2` |
| `sin(x)` | `x: number (Radiant)` | `number` | Sinus | `sin(0)` → `0` |
| `cos(x)` | `x: number (Radiant)` | `number` | Cosinus | `cos(0)` → `1` |
| `tan(x)` | `x: number (Radiant)` | `number` | Tangens | `tan(π/4)` → `1` |
| `sum(a, b, ...)` | `a, b, ...: number[]` | `number` | Summe mehrerer Werte | `sum(1, 2, 3)` → `6` |

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

## 📝 STRING & DATENTYP-FUNKTIONEN

| Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|-----------|----------|-------------|----------|
| `type(x)` | `x: any` | `string` | Datentyp als String | `type(atrp)` → `"number"` |
| `string(x)` | `x: any` | `string` | Konvertierung zu String | `string(123)` → `"123"` |
| `int(x)` | `x: number/string` | `int` | Konvertierung zu Integer | `int(5.7)` → `5` |
| `double(x)` | `x: any` | `number` | Konvertierung zu Double/Float | `double("3.14")` → `3.14` |
| `bool(x)` | `x: any` | `bool` | Konvertierung zu Boolean | `bool("true")` → `true` |
| `contains(s, substr)` | `s: string, substr: string` | `bool` | String enthält Substring | `contains("LONG_TREND", "LONG")` → `true` |
| `startsWith(s, prefix)` | `s: string, prefix: string` | `bool` | String beginnt mit Prefix | `startsWith(strategy, "trend")` → `true/false` |
| `endsWith(s, suffix)` | `s: string, suffix: string` | `bool` | String endet mit Suffix | `endsWith(strategy, "conservative")` → `true/false` |
| `toLowerCase(s)` | `s: string` | `string` | String zu Kleinbuchstaben | `toLowerCase("BULLISH")` → `"bullish"` |
| `toUpperCase(s)` | `s: string` | `string` | String zu Großbuchstaben | `toUpperCase("long")` → `"LONG"` |
| `length(s)` | `s: string` | `int` | Länge eines Strings | `length("strategy")` → `8` |
| `substring(s, start, end)` | `s: string, start: int, end: int` | `string` | Substring extrahieren | `substring("BTC_USDT", 0, 3)` → `"BTC"` |
| `split(s, delimiter)` | `s: string, delimiter: string` | `string[]` | String splitten | `split("R0,R1,R2", ",")` → `["R0", "R1", "R2"]` |
| `join(arr, delimiter)` | `arr: string[], delimiter: string` | `string` | Array zu String verbinden | `join(["a","b"], "-")` → `"a-b"` |

---

## 🔗 ARRAY & COLLECTION-FUNKTIONEN

| Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|-----------|----------|-------------|----------|
| `size(arr)` / `length(arr)` | `arr: any[]` | `int` | Länge/Größe eines Arrays | `size([1,2,3])` → `3` |
| `has(arr, element)` | `arr: any[], element: any` | `bool` | Array enthält Element | `has(regimes, "R1")` → `true/false` |
| `all(arr, condition)` | `arr: any[], condition: bool` | `bool` | Alle Elemente erfüllen Bedingung | `all(volumes > 500)` → `true/false` |
| `any(arr, condition)` | `arr: any[], condition: bool` | `bool` | Mindestens ein Element erfüllt | `any(values > 10)` → `true/false` |
| `map(arr, expr)` | `arr: any[], expr: expr` | `any[]` | Transformation auf Array | `map(prices, x * 1.1)` |
| `filter(arr, condition)` | `arr: any[], condition: bool` | `any[]` | Filtern nach Bedingung | `filter(volumes, x > 500)` |
| `first(arr)` | `arr: any[]` | `any` | Erstes Element | `first(regimes)` → Element |
| `last(arr)` | `arr: any[]` | `any` | Letztes Element | `last(regimes)` → Element |
| `sum(arr)` | `arr: number[]` | `number` | Summe aller Elemente | `sum([1,2,3,4])` → `10` |
| `avg(arr)` / `average(arr)` | `arr: number[]` | `number` | Durchschnitt | `avg([10,20,30])` → `20` |
| `min(arr)` | `arr: number[]` | `number` | Minimum im Array | `min([5,10,3])` → `3` |
| `max(arr)` | `arr: number[]` | `number` | Maximum im Array | `max([5,10,3])` → `10` |
| `distinct(arr)` | `arr: any[]` | `any[]` | Duplikate entfernen | `distinct([1,1,2,2,3])` → `[1,2,3]` |
| `sort(arr)` | `arr: number[]` | `number[]` | Array sortieren | `sort([3,1,2])` → `[1,2,3]` |
| `reverse(arr)` | `arr: any[]` | `any[]` | Array umkehren | `reverse([1,2,3])` → `[3,2,1]` |
| `contains(arr, element)` | `arr: any[], element: any` | `bool` | Array enthält Element | `contains(no_trade_regimes, regime)` |
| `indexOf(arr, element)` | `arr: any[], element: any` | `int` | Index eines Elements (-1 wenn nicht gefunden) | `indexOf(regimes, "R1")` → `1` |
| `slice(arr, start, end)` | `arr: any[], start: int, end: int` | `any[]` | Array-Ausschnitt | `slice(arr, 0, 3)` |

---

## 🎯 TRADING-SPEZIFISCHE FUNKTIONEN

### Basis-Funktionen

| Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|-----------|----------|-------------|----------|
| `isnull(x)` | `x: any` | `bool` | Wert ist null/undefined | `isnull(spread_bps)` → `true/false` |
| `isnotnull(x)` | `x: any` | `bool` | Wert ist NICHT null | `isnotnull(obi)` → `true/false` |
| `nz(x, default)` | `x: any, default: any` | `any` | Null-Ersatz (coalesce) | `nz(obi, 0)` → Wert oder 0 |
| `coalesce(a, b, c, ...)` | `a, b, c, ...: any` | `any` | Erstes nicht-null Element | `coalesce(trade.tr_stop_price, trade.stop_price)` |
| `clamp(x, min, max)` | `x, min, max: number` | `number` | Wert zwischen min und max | `clamp(atrp, 0.1, 2.5)` |

### Prozentuale Berechnungen

| Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|-----------|----------|-------------|----------|
| `pct_change(old, new)` | `old, new: number` | `number` | Prozentuale Veränderung | `pct_change(95336, 95159)` → `-0.18` |
| `pct_from_level(price, level)` | `price, level: number` | `number` | % Abstand zu Level | `pct_from_level(95336, 95159)` → `0.18` |
| `level_at_pct(entry, pct, side)` | `entry: number, pct: number, side: string` | `number` | Preis bei % Abstand | `level_at_pct(100, 1.0, "long")` → `99` |
| `retracement(from, to, pct)` | `from, to, pct: number` | `number` | Fibonacci Retracement Level | `retracement(95000, 96000, 0.618)` |
| `extension(from, to, pct)` | `from, to, pct: number` | `number` | Fibonacci Extension Level | `extension(95000, 96000, 1.618)` |

### Statusprüfung

| Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|-----------|----------|-------------|----------|
| `is_trade_open()` | keine | `bool` | Ist Trade aktuell offen | `is_trade_open()` → `true/false` |
| `is_long()` | keine | `bool` | Ist aktueller Trade long | `is_long()` → `true/false` |
| `is_short()` | keine | `bool` | Ist aktueller Trade short | `is_short()` → `true/false` |
| `is_bullish_signal()` | keine | `bool` | Übergeordneter Bias bullish | `is_bullish_signal()` → `true/false` |
| `is_bearish_signal()` | keine | `bool` | Übergeordneter Bias bearish | `is_bearish_signal()` → `true/false` |
| `in_regime(r)` | `r: string` | `bool` | Bin ich in Regime R | `in_regime("R1")` → `true/false` |

### Preisfunktionen

| Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|-----------|----------|-------------|----------|
| `stop_hit_long()` | keine | `bool` | Long StopLoss getroffen | `stop_hit_long()` → `current_price <= stop_price` |
| `stop_hit_short()` | keine | `bool` | Short StopLoss getroffen | `stop_hit_short()` → `current_price >= stop_price` |
| `tp_hit()` | keine | `bool` | TakeProfit getroffen | `tp_hit()` → `true/false` |
| `price_above_ema(period)` | `period: int` | `bool` | Preis über EMA(period) | `price_above_ema(34)` → `true/false` |
| `price_below_ema(period)` | `period: int` | `bool` | Preis unter EMA(period) | `price_below_ema(34)` → `true/false` |
| `price_above_level(level)` | `level: number` | `bool` | Preis über Level | `price_above_level(95000)` → `true/false` |
| `price_below_level(level)` | `level: number` | `bool` | Preis unter Level | `price_below_level(95000)` → `true/false` |

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

### ❌ NICHT Implementiert (aus v1.0 entfernt)

Die folgenden Pattern-Funktionen aus v1.0 sind **NICHT implementiert** und wurden entfernt:
- `pin_bar_bullish()` / `pin_bar_bearish()` (nur via Strategy Models verfügbar)
- `inside_bar()`
- `inverted_hammer()`
- `bull_flag()` / `bear_flag()`
- `cup_and_handle()`
- `double_bottom()` / `double_top()`
- `ascending_triangle()` / `descending_triangle()`
- `breakout_above()` / `breakdown_below()`
- `false_breakout()`
- `break_of_structure()`
- Smart Money Concepts (`liquidity_swept()`, `fvg_exists()`, `order_block_retest()`)

**Hinweis:** Diese Patterns sind in `strategy_models.py` dokumentiert (40 Patterns), aber nicht als CEL-Funktionen verfügbar.

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

| Befehl | Parameter | Rückgabe | Beschreibung | Beispiel |
|--------|-----------|----------|-------------|----------|
| `now()` | keine | `int` | Aktuelle Unix-Zeit in Sekunden | `now()` → `1737350640` |
| `timestamp()` | keine | `int` | Aktueller Bar-Timestamp | `timestamp()` → `1737350000` |
| `bar_age()` | keine | `int` | Alter des aktuellen Bars in Sekunden | `bar_age()` → `87` |
| `bars_since(condition)` | `condition: bool` | `int` | Bars seit Bedingung wahr war | `bars_since(close > 95000)` → `5` |
| `is_time_in_range(start, end)` | `start, end: string (HH:MM)` | `bool` | Zeit im Bereich | `is_time_in_range("09:00", "16:00")` → `true/false` |
| `is_new_day()` | keine | `bool` | Ist neuer Handelstag | `is_new_day()` → `true/false` |
| `is_new_hour()` | keine | `bool` | Ist neue Stunde | `is_new_hour()` → `true/false` |
| `time_hours_ago(hours)` | `hours: int` | `int` | Timestamp von vor N Stunden | `time_hours_ago(1)` |
| `seconds_since(timestamp)` | `timestamp: int` | `int` | Sekunden seit Timestamp | `seconds_since(entry_timestamp)` |

---

## 🔍 VARIABLE & KONTEXT-ZUGRIFF

### Markt/Regime-Variablen (Top-Level)

```cel
// Timeframe
tf                    // "5m", "1D", "1H", etc.

// Regime-Klassifikation
regime                // "R0" (Choppy), "R1" (Uptrend), "R2" (Choppy/Range), etc.
direction             // "UP", "DOWN", "NONE"

// OHLCV
open, high, low, close, volume    // Bar-Daten

// Volatilität
atrp                  // ATR in Prozent
atr                   // ATR absolut (optional)
bbwidth               // Bollinger Bandwidth
range_pct             // Bar-Range in %
squeeze_on            // boolean - ist Squeeze aktiv

// Markttiefe/Orderbook
spread_bps            // Spread in Basis Points (kann null sein)
depth_bid             // Tiefe bid-side (kann null sein)
depth_ask             // Tiefe ask-side (kann null sein)
obi                   // Orderbook Imbalance [-1..1] (kann null sein)
```

### Trade-Variablen (unter `trade.`)

```cel
// Basis-Info
trade.id              // string: Type/interne ID
trade.strategy        // string: Strategy Name
trade.side            // "long" oder "short"

// Eingangsposition
trade.entry_price     // number: Entry-Kurs
trade.current_price   // number: Aktueller Kurs
trade.leverage        // number: Hebel (z.B. 20)
trade.invest_usdt     // number: Investierte Summe

// Stop & Risk Management
trade.stop_price      // number: Aktueller SL
trade.sl_pct          // number: SL in %

// Trailing Stop Parameter
trade.tr_pct          // number: Trailing-Distanz in %
trade.tra_pct         // number: Trailing-Activation in %
trade.tr_lock_pct     // number: Lock/Break-Even Schwelle in %
trade.tr_stop_price   // number|null: Aktueller Trailing Stop (null wenn inaktiv)

// P&L & Fees
trade.status          // string: "OPEN", "SL", "TP", "MANUAL_CLOSE"
trade.pnl_pct         // number: Profit/Loss in %
trade.pnl_usdt        // number: Profit/Loss in USDT
trade.fees_pct        // number: Gebühren in %
trade.fees_usdt       // number: Gebühren in USDT
trade.stick           // number: Interne Kennzahl

// Zeit-Metriken (optional aber empfohlen)
trade.age_sec         // number: Sekunden seit Entry
trade.bars_in_trade   // int: Anzahl der Bars seit Entry

// Performance-Metriken (optional aber empfohlen)
trade.mfe_pct         // number: Max Favorable Excursion %
trade.mae_pct         // number: Max Adverse Excursion %
trade.is_open         // bool: Ist Trade noch offen
```

### Konfigurationsvariablen (unter `cfg.`)

```cel
// Volumen-Filter
cfg.min_volume_pctl           // int: Perzentil-Schwelle (z.B. 20)
cfg.min_volume_window         // int: Lookback-Fenster (z.B. 288)

// Volatilität-Filter
cfg.min_atrp_pct              // number: Mindest-ATR%
cfg.max_atrp_pct              // number: Maximal-ATR%

// Markttiefe-Filter
cfg.max_spread_bps            // number: Maximal Spread
cfg.min_depth                 // number: Mindest-Tiefe

// Risiko-Limits
cfg.max_leverage              // number: Maximal-Hebel
cfg.max_fees_pct              // number: Maximal-Gebühr%

// Regime & Richtung Filter
cfg.no_trade_regimes          // string[]: Array von Regimen zum Ausschließen
cfg.min_obi                   // number: Mindest-OBI bei Orderflow
cfg.min_range_pct             // number: Mindest-Range für bestimmte Regime
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

### NICE TO HAVE (Optional) ❌

**Folgende Funktionen aus v1.0 sind NICHT implementiert:**
- [ ] Advanced Pattern Functions (pin_bar, inside_bar, bull_flag, etc.)
- [ ] `breakout_above()`, `breakdown_below()`, `false_breakout()`
- [ ] Smart Money Concepts (OB, FVG, Liquidity Sweep)
- [ ] Harmonic Pattern Functions
- [ ] `fibonacci_support()`, `fibonacci_resistance()`

**Ersatz:** Diese Patterns sind in `strategy_models.py` dokumentiert (40 Patterns), können aber nicht als CEL-Funktionen verwendet werden.

---

## 📌 WICHTIGE ÄNDERUNGEN VON v1.0 → v2.0

### ✅ NEU Hinzugefügt

1. **IndicatorType Enum** - 18 definierte Indikatoren mit exakten Parametern
2. **TA-Lib Pattern Detection** - 8 Candlestick Patterns
3. **Entry Analyzer Methoden** - Vollständige UI-API-Dokumentation
4. **Config System API** - ConditionEvaluator, RegimeDetector, Router, Executor
5. **CEL Expression Unterstützung** - Komplexe Conditions mit `cel_expression`
6. **Custom Indicators** - PIVOTS, SUPPORT_RESISTANCE, PATTERN

### ❌ ENTFERNT

1. **Nicht-implementierte Pattern Functions:**
   - `pin_bar_bullish/bearish`, `inside_bar`, `inverted_hammer`
   - `bull_flag`, `bear_flag`, `cup_and_handle`
   - `double_bottom`, `double_top`
   - `ascending_triangle`, `descending_triangle`

2. **Nicht-implementierte Breakout Functions:**
   - `breakout_above()`, `breakdown_below()`, `false_breakout()`
   - `break_of_structure()`

3. **Smart Money Concepts:**
   - `liquidity_swept()`, `fvg_exists()`, `order_block_retest()`
   - `harmonic_pattern_detected()`

### 🔧 AKTUALISIERT

1. **Indicator Zugriff** - Von `ema(period)` zu `ema34.value` (via indicator_id)
2. **Pattern Detection** - Von direkten Funktionen zu TA-Lib Integration
3. **Condition Evaluation** - Zwei Modi: Operator-basiert + CEL

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

**Version:** 2.0 (Aligned)
**Erstellt:** 20. Januar 2026
**Status:** Produktionsbereit
**Zielgruppe:** Trading Bot CEL Engine Entwicklung
