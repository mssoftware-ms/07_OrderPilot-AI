# CEL Neue Funktionen v2.4
## No Entry Filter, Regime Functions & Variablen

**Datum:** 28. Januar 2026
**Version:** 2.4
**Ergänzung zu:** CEL_Befehle_Liste_v2.md

---

## 🚫 NO ENTRY FILTER (ENTRY BLOCKER)

**Workflow-Typ:** `no_entry` (seit v2.4)
**Purpose:** Verhindert neue Trades unter gefährlichen oder ungünstigen Marktbedingungen
**Return:** `boolean` (true = BLOCKIEREN, false = ERLAUBEN)

### 📌 Was ist "no_entry"?

Der `no_entry` Workflow ist ein **Sicherheitsfilter**, der proaktiv verhindert, dass neue Positionen eröffnet werden, wenn bestimmte Risikobedingungen erfüllt sind. Im Gegensatz zu `entry`-Conditions (die prüfen OB ein Setup vorliegt) prüft `no_entry` OB Bedingungen GEGEN einen Trade sprechen.

**Logik:**
```cel
// Entry-Decision kombiniert beide Checks
can_enter = entry_conditions_met && !no_entry_triggered

// Wenn no_entry = true → kein Trade (selbst wenn entry = true)
```

### 🎯 Use Cases

| Use Case | Beschreibung | CEL Expression |
|----------|-------------|----------------|
| **News Events** | Keine Trades während wichtiger News (hohe Volatilität) | `atrp > cfg.news_atrp_threshold` |
| **Hohe Volatilität** | Zu gefährlich, unberechenbare Moves | `atrp > 5.0` |
| **Niedrige Volatilität** | Trendloser Markt, keine klaren Signale | `chop14.value < 38.2` |
| **Choppy Markets** | Range-bound, keine Trends | `adx14.value < 20 && chop14.value > 61.8` |
| **Blackout Zeiten** | Vor Weekend, Feiertagen, Low-Liquidity | `is_time_in_blackout()` |
| **Regime Filter** | Bestimmte Regimes blockieren | `has(cfg.no_trade_regimes, regime)` |
| **Spread zu hoch** | Slippage-Risiko | `spread_bps > cfg.max_spread_bps` |
| **Volumen zu niedrig** | Keine Liquidität | `volume_ratio_20.value < 0.5` |

### 💡 Beispiele

#### Beispiel 1: Hohe Volatilität blockieren
```cel
// Keine Trades wenn ATRP > 5%
atrp > 5.0
```
**Ergebnis:** `true` = Trade blockiert (zu volatil)

#### Beispiel 2: Bestimmte Regimes blockieren
```cel
// Keine Trades in "No-Trade" Regimes
has(cfg.no_trade_regimes, regime)
```
**Ergebnis:** `true` = Trade blockiert (Regime nicht erlaubt)

#### Beispiel 3: Niedrige Choppiness (Trendlos)
```cel
// Keine Trades wenn Markt trendlos (Choppiness < 38.2)
chop14.value < 38.2
```
**Ergebnis:** `true` = Trade blockiert (kein Trend)

#### Beispiel 4: Kombiniert - Hohe Volatilität ODER schlechtes Regime
```cel
// Blockiere wenn ATRP zu hoch ODER Regime nicht erlaubt
atrp > cfg.max_atrp_pct || has(cfg.no_trade_regimes, regime)
```
**Ergebnis:** `true` = Trade blockiert (eine der Bedingungen erfüllt)

#### Beispiel 5: Multi-Layer Filter
```cel
// Blockiere NUR wenn ALLE Bedingungen zutreffen:
// - Hohe Volatilität (ATRP > 5%)
// - Niedriger ADX (kein Trend)
// - Schlechtes Regime
(atrp > 5.0) && (adx14.value < 20) && has(cfg.no_trade_regimes, regime)
```
**Ergebnis:** `true` = Trade blockiert (alle 3 Bedingungen erfüllt)

#### Beispiel 6: Spread + Volumen Check
```cel
// Blockiere wenn Spread zu hoch ODER Volumen zu niedrig
(spread_bps > cfg.max_spread_bps) || (volume_ratio_20.value < 0.5)
```
**Ergebnis:** `true` = Trade blockiert (Liquiditätsproblem)

### ✅ Best Practices

1. **Nutze no_entry als Sicherheitsfilter**
   - `no_entry` sollte IMMER vor `entry` geprüft werden
   - Verhindert gefährliche Trades proaktiv

2. **Kombiniere mit entry-Bedingungen**
   ```python
   # Backend Logic
   can_enter = (
       evaluate_entry_conditions(context) and
       not evaluate_no_entry_conditions(context)
   )
   ```

3. **Priorisierung**
   - Hohe Priorität für kritische Filter (News, extreme Volatilität)
   - Niedrige Priorität für Regime-basierte Filter

4. **Teste gründlich im Backtest**
   - Vergleiche Performance MIT vs. OHNE `no_entry` Filter
   - Prüfe False-Positive Rate (verpasste gute Trades)

5. **Dokumentiere alle Filter-Gründe**
   - Jede `no_entry` Regel sollte klare `description` haben
   - Logging bei Blockierung für spätere Analyse

6. **Verwende Config-basierte Thresholds**
   ```cel
   // ✅ EMPFOHLEN: Config-gesteuert
   atrp > cfg.max_atrp_pct

   // ❌ NICHT EMPFOHLEN: Hardcoded
   atrp > 5.0
   ```

---

## 🎯 REGIME FUNCTIONS (NEU v2.4)

**Seit:** Version 2.4 (2026-01-28)
**Zweck:** Zugriff auf Regime-Daten und Regime-Analyse-Trigger
**Anzahl:** 2 Funktionen

### last_closed_regime()

| Eigenschaft | Wert |
|-------------|------|
| **Signatur** | `last_closed_regime() -> string` |
| **Parameter** | keine |
| **Return** | `string` - Regime der letzten geschlossenen Kerze |
| **Status** | ✅ Implementiert |
| **Code** | `src/core/tradingbot/cel_engine.py` (Zeile 2038-2078) |

**Beschreibung:**
Gibt das Regime der **letzten geschlossenen Kerze** zurück (nicht die aktuelle). Nützlich für Entry-Entscheidungen basierend auf dem Regime der vorherigen Kerze.

**Rückgabewerte:**
- `'EXTREME_BULL'` - Extreme bullische Bedingungen
- `'BULL'` - Bullischer Trend
- `'NEUTRAL'` - Neutral/Range-bound
- `'BEAR'` - Bearischer Trend
- `'EXTREME_BEAR'` - Extreme bearische Bedingungen
- `'UNKNOWN'` - Regime-Daten nicht verfügbar

**Context Requirements:**
- `last_closed_candle.regime` - Direct candle data (preferred)
- `chart_data[-2].regime` - From chart history
- `prev_regime` - Fallback field

**Verwendung:**
```cel
// Entry nur wenn letztes Regime bullish
last_closed_regime() == 'EXTREME_BULL'

// Regime-Wechsel erkennen
last_closed_regime() == 'NEUTRAL' && regime == 'BULL'

// Multi-Regime Filter
(last_closed_regime() == 'BULL' || last_closed_regime() == 'EXTREME_BULL')

// Mit anderen Bedingungen kombinieren
last_closed_regime() == 'EXTREME_BULL' && !is_trade_open(trade) && rsi14.value > 50
```

---

### trigger_regime_analysis()

| Eigenschaft | Wert |
|-------------|------|
| **Signatur** | `trigger_regime_analysis() -> boolean` |
| **Parameter** | keine |
| **Return** | `bool` - `true` wenn erfolgreich, `false` bei Fehler |
| **Status** | ✅ Implementiert |
| **Code** | `src/core/tradingbot/cel_engine.py` (Zeile 1987-2036) |
| **Update** | 2026-01-30 - Zeichnet jetzt automatisch Regime-Linien im Chart |

**Beschreibung:**
Löst Regime-Erkennung aus und **zeichnet automatisch vertikale Linien im Chart bei Regime-Wechseln**.

**Was diese Funktion macht:**
1. Triggert `RegimeDisplayMixin._update_regime_from_data()`
2. Erkennt aktuelles Regime basierend auf Chart-Daten (z.B. "STRONG_BULL", "SIDEWAYS")
3. **NEU (2026-01-30):** Zeichnet **vertikale Linie im Chart** bei Regime-Wechsel
4. Updated Regime-Badge in Toolbar
5. Gibt `true` zurück bei Erfolg

**Regime-Detektion:**
- Nutzt `RegimeDetectorService` (nicht Entry Designer JSON!)
- Analysiert ADX, RSI, DI+/DI- aus aktuellen Chart-Daten
- Erkennt 9 Regime-Level: STRONG_TF, STRONG_BULL, STRONG_BEAR, TF, BULL_EXHAUSTION, BEAR_EXHAUSTION, BULL, BEAR, SIDEWAYS

**Automatische Chart-Linien:**
Bei Regime-Wechsel (z.B. SIDEWAYS → BULL):
- ✅ Vertikale Linie wird gezeichnet
- ✅ Farbe entsprechend Regime (BULL = grün, BEAR = rot, etc.)
- ✅ Label mit Regime-Name
- ✅ Linie bleibt persistent

**Funktionsweise:**
```
1. Chart Window Reference holen (aus CEL Context)
2. chart_window.trigger_regime_update(debounce_ms=0) aufrufen
3. RegimeDisplayMixin._update_regime_from_data() läuft
4. Regime wird erkannt (z.B. "BULL")
5. Bei Wechsel: add_regime_line() → JavaScript addVerticalLine()
6. Return true/false
```

**Context Requirements:**
- `chart_window` - Reference zum Chart Window (automatisch im JSON Entry Context)
- `chart_window.trigger_regime_update()` - Methode muss verfügbar sein (✅ seit 2026-01-30)

**Verwendung:**
```cel
// Regime-Analyse + Entry bei STRONG_BULL
trigger_regime_analysis() && last_closed_regime() == 'STRONG_BULL'

// Exhaustion-Filter (keine Entries bei Reversal Warnings)
trigger_regime_analysis() &&
last_closed_regime() != 'BULL_EXHAUSTION' &&
last_closed_regime() != 'BEAR_EXHAUSTION' &&
(last_closed_regime() == 'BULL' || last_closed_regime() == 'STRONG_BULL')

// Mit Trade-Richtung
trigger_regime_analysis() && (
  (side == 'long' && last_closed_regime() == 'STRONG_BULL') ||
  (side == 'short' && last_closed_regime() == 'STRONG_BEAR')
)
```

**Log-Ausgabe (Beispiel):**
```
[REGIME] _update_regime_from_data called
[REGIME] 🔄 Data changed, detecting regime...
[REGIME] Current: BULL, Last: SIDEWAYS
[REGIME] 🎨 Regime changed! Drawing line for BULL
[BOT_OVERLAY] add_regime_line called: id=regime_BULL_1738281600, ts=1738281600
[BOT_OVERLAY] ✅ JS executed for regime line regime_BULL_1738281600
```

**Wichtig:** 
- Diese Funktion sollte am **Anfang** der Entry-Logik aufgerufen werden
- Bei **5-Minuten-Kerzen** wechselt Regime nur alle 5 Minuten (beim Candle-Close)
- Linien erscheinen **nur bei Wechsel**, nicht bei jedem Aufruf

---

## 📊 VERFÜGBARE VARIABLEN (69+ Variablen)

**Seit:** Version 2.4 (2026-01-28)
**Integration:** AI CEL Code-Generierung (`cel_ai_helper.py`)
**Zweck:** Vollständige Liste aller verfügbaren Variablen für CEL Expressions

### 1. BOT VARIABLES (bot.*) - 27 Variablen

#### Trading Configuration
- `bot.symbol` - Trading symbol (e.g., "BTCUSDT")
- `bot.leverage` - Trading leverage (e.g., 10)
- `bot.paper_mode` - Is paper trading? (always True)

#### Risk Management
- `bot.risk_per_trade_pct` - Risk per trade in % (e.g., 2.0)
- `bot.max_daily_loss_pct` - Max daily loss in % (e.g., 10.0)
- `bot.max_position_size_btc` - Max position size in BTC

#### Stop Loss & Take Profit
- `bot.sl_atr_multiplier` - Stop Loss ATR multiplier (e.g., 2.0)
- `bot.tp_atr_multiplier` - Take Profit ATR multiplier (e.g., 3.0)
- `bot.trailing_stop_enabled` - Trailing stop enabled (true/false)
- `bot.trailing_stop_atr_mult` - Trailing stop ATR multiplier
- `bot.trailing_stop_activation_pct` - Trailing stop activation % (e.g., 2.0)

#### Signal Generation
- `bot.min_confluence_score` - Minimum confluence score (e.g., 3)
- `bot.require_regime_alignment` - Require regime alignment (true/false)

#### Timing
- `bot.analysis_interval_sec` - Analysis interval in seconds
- `bot.position_check_interval_ms` - Position check interval in ms
- `bot.macro_update_interval_min` - Macro update interval in minutes
- `bot.trend_update_interval_min` - Trend update interval in minutes

#### Session Management
- `bot.session.enabled` - Session management enabled (true/false)
- `bot.session.start_utc` - Session start time (UTC, e.g., "08:00")
- `bot.session.end_utc` - Session end time (UTC, e.g., "16:00")
- `bot.session.close_at_end` - Close positions at session end (true/false)

#### AI Configuration
- `bot.ai.enabled` - AI validation enabled (true/false)
- `bot.ai.confidence_threshold` - AI confidence threshold (0-100)
- `bot.ai.min_confluence_for_ai` - Min confluence to trigger AI (e.g., 3)
- `bot.ai.fallback_to_technical` - Fallback to technical analysis (true/false)

---

### 2. CHART VARIABLES (chart.*) - 18 Variablen

#### Current Candle (OHLCV)
- `chart.price` / `chart.close` - Current close price (USD)
- `chart.open` - Current open price (USD)
- `chart.high` - Current high price (USD)
- `chart.low` - Current low price (USD)
- `chart.volume` - Current volume (BTC)

#### Chart Info
- `chart.symbol` - Trading symbol (e.g., "BTCUSDT")
- `chart.timeframe` - Chart timeframe (e.g., "1h", "4h", "1d")
- `chart.candle_count` - Number of loaded candles (int)

#### Candle Analysis
- `chart.range` - High-Low range (USD)
- `chart.body` - Absolute candle body size (USD)
- `chart.is_bullish` - Is current candle bullish? (bool)
- `chart.is_bearish` - Is current candle bearish? (bool)
- `chart.upper_wick` - Upper wick size (USD)
- `chart.lower_wick` - Lower wick size (USD)

#### Previous Candle
- `chart.prev_close` - Previous candle close (USD)
- `chart.prev_high` - Previous candle high (USD)
- `chart.prev_low` - Previous candle low (USD)
- `chart.change` - Price change from previous candle (USD)
- `chart.change_pct` - Price change percentage (%)

---

### 3. MARKET VARIABLES - 9 Variablen

#### Price & Volume
- `close` - Current close price
- `open` - Current open price
- `high` - Current high price
- `low` - Current low price
- `volume` - Current volume

#### Volatility & Regime
- `atrp` - ATR in percent (volatility measure)
- `regime` - Current market regime (string, e.g., "R0", "R1", "R2", "R3", "R4")
- `direction` - Trend direction (UP/DOWN/NONE)
- `squeeze_on` - Bollinger squeeze active (bool)

---

### 4. TRADE VARIABLES (trade.*) - 9 Variablen

#### Position Info
- `trade.entry_price` - Entry price
- `trade.current_price` - Current market price
- `trade.stop_price` - Current stop loss price
- `trade.side` - Trade side (long/short)
- `trade.leverage` - Trade leverage

#### Performance
- `trade.pnl_pct` - Profit/Loss in %
- `trade.pnl_usdt` - Profit/Loss in USDT
- `trade.fees_pct` - Fees in %

#### Duration
- `trade.bars_in_trade` - Bars since entry

---

### 5. CONFIG VARIABLES (cfg.*) - 6 Variablen

#### Trading Rules
- `cfg.min_volume_pctl` - Minimum volume percentile (e.g., 20.0)
- `cfg.min_atrp_pct` - Minimum ATR % (e.g., 0.5)
- `cfg.max_atrp_pct` - Maximum ATR % (e.g., 5.0)
- `cfg.max_leverage` - Maximum allowed leverage (e.g., 10)
- `cfg.max_fees_pct` - Maximum fee % (e.g., 0.2)
- `cfg.no_trade_regimes` - Array of blocked regimes (e.g., ["R0", "R4"])

---

### 6. PROJECT VARIABLES (project.*)

**Custom Variables from `.cel_variables.json`:**
- `project.*` - User-defined variables with custom values
- Define in Variables UI to create project-specific constants
- Example: `project.entry_min_price`, `project.max_drawdown_pct`

**Dynamisch:** Anzahl hängt von User-Definitionen ab

---

## 📝 WICHTIGE HINWEISE

### Variablen-Verwendung
- **chart.*** für aktuelle Marktdaten (OHLCV)
- **bot.*** für Bot-Konfiguration und Risk Management
- **trade.*** für aktive Position-Informationen
- **cfg.*** für Strategy-Level-Konfiguration
- **project.*** für Custom Project-spezifische Konstanten

### Prozentangaben
- Alle Prozentangaben sind in **Dezimalform** (e.g., 2.0 = 2%)
- `atrp = 2.5` bedeutet 2.5% ATR

### Null-Safety
- Verwende **null-safe operators** wenn Werte potenziell fehlen könnten:
  ```cel
  !isnull(bot.trailing_stop_enabled) && bot.trailing_stop_enabled
  nz(project.entry_min_price, 0)
  ```

---

## 📚 VOLLSTÄNDIGE REFERENZ

Für die vollständige CEL Funktionsliste siehe:
- `04_Knowledgbase/CEL_Befehle_Liste_v2.md` (Hauptdokumentation)
- `04_Knowledgbase/CEL_Functions_Reference_v3.md` (Funktionsreferenz v3.1)

---

**Version:** 2.4
**Datum:** 2026-01-28
**Status:** ✅ Produktionsbereit
