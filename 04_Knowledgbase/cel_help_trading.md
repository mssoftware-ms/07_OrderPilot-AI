# CEL Editor Hilfe – Trading-Tabellen (No Entry / Entry / Exit / Before Exit / Update Stop)

Stand: 2026-01-28

Diese Hilfe beschreibt, wie die fünf CEL‑Tabs im Code Editor gedacht sind, welche Variablen (Chart / Bot) es gibt, und liefert praxisnahe CEL‑Beispiele für typische Trading‑Abläufe.

---

## 1) Tab-Überblick – was macht welcher Tab?

### No Entry (🚫 Entry Blocker)
- **Zweck:** **Sicherheitsfilter**, der neue Trades unter gefährlichen oder ungünstigen Marktbedingungen **verhindert**.
- **Typische Inputs:** Volatilität (ATRP), Regime-Filter, Volumen, Spread, Choppiness, ADX.
- **Ergebnis:** `true` -> Trade wird **BLOCKIERT** (selbst wenn Entry-Signal vorliegt), `false` -> Trade erlaubt.
- **Wichtig:** Wird VOR Entry-Prüfung ausgewertet. Entry nur wenn: `entry_conditions_met && !no_entry_triggered`

### Entry
- **Zweck:** Bedingungen, wann ein Trade **geöffnet** werden soll (Kaufen/Shorten).
- **Typische Inputs:** Chart‑Preis, Indikatoren, Regime‑Status, Bot‑Regeln.
- **Ergebnis:** `true` -> Signal für Entry.

### Exit
- **Zweck:** Bedingungen, wann ein Trade **geschlossen** werden soll (Take Profit / Stop / Exit‑Signal).
- **Typische Inputs:** Trade‑Status (offen?), Preis‑Ziele, Regime‑Wechsel.
- **Ergebnis:** `true` -> Exit‑Signal.

### Before Exit
- **Zweck:** Prüfungen **vor** dem Exit. Hier werden meist zusätzliche Schutz‑ oder Bestätigungsregeln formuliert.
- **Typische Inputs:** Trade‑Status, Regime, Zeitbedingungen, Sicherheitsfilter.
- **Ergebnis:** `true` -> Freigabe oder Zusatzbedingung vor Exit.

### Update Stop
- **Zweck:** Bedingungen, wann der **Stop‑Loss nachgezogen** oder angepasst werden soll.
- **Typische Inputs:** Gewinn‑Schwellen, ATR, Trend‑Signale.
- **Ergebnis:** `true` -> Stop‑Update auslösen.

---

## 2) Chart‑Variablen (chart.*)
Diese kommen aus dem aktuellen Chart und werden pro Candle aktualisiert.

**Wichtigste Felder:**
- `chart.price` – letzter Close
- `chart.open` / `chart.high` / `chart.low` / `chart.volume`
- `chart.symbol` – aktuelles Symbol
- `chart.timeframe` – z. B. "1m", "5m", "1h"
- `chart.candle_count` – Anzahl geladener Kerzen
- `chart.range` – High-Low der letzten Kerze
- `chart.body` – Kerzenkörper
- `chart.is_bullish` / `chart.is_bearish`
- `chart.upper_wick` / `chart.lower_wick`
- `chart.prev_close` / `chart.prev_high` / `chart.prev_low`
- `chart.change` / `chart.change_pct`

Beispiele:
- `chart.price > chart.prev_high`
- `chart.is_bullish && chart.body > chart.range * 0.6`

---

## 3) Bot‑Variablen (bot.*)
Diese stammen aus der Bot‑Konfiguration (Risiko‑ und Session‑Regeln).

**Wichtigste Felder:**
- `bot.symbol`, `bot.leverage`, `bot.paper_mode`
- `bot.risk_per_trade_pct`
- `bot.max_daily_loss_pct`
- `bot.max_position_size_btc`
- `bot.sl_atr_multiplier`, `bot.tp_atr_multiplier`
- `bot.trailing_stop_enabled`
- `bot.trailing_stop_atr_mult`
- `bot.trailing_stop_activation_pct`
- `bot.min_confluence_score`
- `bot.require_regime_alignment`
- `bot.session.enabled`, `bot.session.start_utc`, `bot.session.end_utc`
- `bot.ai.enabled`, `bot.ai.confidence_threshold`, `bot.ai.min_confluence_for_ai`

Beispiele:
- `bot.paper_mode == true`
- `bot.trailing_stop_enabled == true && chart.change_pct > bot.trailing_stop_activation_pct`

---

## 4) Regime‑Variablen (regime.*)
Regime ist optional und nur verfügbar, wenn der Regime‑Detector Werte liefert.

Beispiel‑Keys:
- `regime.current` – aktuelles Regime (z. B. "bullish", "bearish")
- `regime.strength` – Stärke

Regime prüfen (robust):
- `!isnull(regime.current) && in_regime(regime.current, "bullish")`
- `regime.current == "bullish"`

---

## 5) CEL‑Beispiele für jeden Tab (Trading‑Praxis)

### A) No Entry – Trade blockieren bei ungünstigen Bedingungen
**Ziel:** Neue Trades verhindern, wenn Marktbedingungen zu riskant sind.

```cel
// Hohe Volatilität blockieren (ATRP > 5%)
atrp > 5.0
```

**Bestimmte Regimes blockieren:**
```cel
// Keine Trades in bestimmten Regimes
has(cfg.no_trade_regimes, regime)
```

**Kombinierte Filter (Volatilität ODER schlechtes Regime):**
```cel
// Blockiere wenn ATRP zu hoch ODER Regime nicht erlaubt
atrp > cfg.max_atrp_pct || has(cfg.no_trade_regimes, regime)
```

**Multi-Layer Filter (alle Bedingungen müssen zutreffen):**
```cel
// Blockiere NUR wenn hohe Volatilität UND niedriger ADX UND schlechtes Regime
(atrp > 5.0) && (adx14.value < 20) && has(cfg.no_trade_regimes, regime)
```

---

### B) Entry – Kaufen / Long öffnen
**Ziel:** Einsteigen, wenn Trend + Momentum stimmen und Regime passt.

```cel
// Long Entry
chart.price > ema21.value
&& ema21.value > ema50.value
&& rsi14.value > 50
&& (!bot.require_regime_alignment || in_regime(regime.current, "bullish"))
```

**Alternative: Breakout Entry**
```cel
chart.price > chart.prev_high
&& chart.change_pct > 0.3
&& volume_ratio_20.value > 1.2
```

---

### C) Exit – Take Profit / Verkauf bei festem Gewinn
**Ziel:** Position schließen, sobald ein fixer Gewinn erreicht ist.

```cel
// Exit bei +2.5% Gewinn (falls trade.entry_price vorhanden ist)
pct_change(trade.entry_price, chart.price) >= 2.5
```

**Robuster (falls entry_price variabel):**
```cel
// nutzt first non-null entry price
pct_change(coalesce(trade.entry_price, trade.avg_entry_price), chart.price) >= 2.5
```

**Take Profit über TP‑Preis (falls tp im Trade gesetzt):**
```cel
tp_hit(trade, chart.price)
```

---

### D) Before Exit – Sicherheitsfilter vor Exit
**Ziel:** Exit nur zulassen, wenn Trade offen ist und kein „falscher Exit" passiert.

```cel
// Nur wenn Trade offen ist und kein bullish regime mehr aktiv ist
is_trade_open(trade)
&& (isnull(regime.current) || !in_regime(regime.current, "bullish"))
```

**Alternative: Exit nur nach X% Gewinn erlauben**
```cel
is_trade_open(trade)
&& pct_change(coalesce(trade.entry_price, trade.avg_entry_price), chart.price) >= 1.0
```

---

### E) Update Stop – Stop‑Loss nachziehen (Trailing)
**Ziel:** SL nach oben ziehen, wenn Trade im Gewinn ist.

```cel
// Trailing Stop aktiv, wenn Gewinn > 1.0% und Trend intakt
bot.trailing_stop_enabled == true
&& pct_change(coalesce(trade.entry_price, trade.avg_entry_price), chart.price) >= 1.0
&& ema21.value > ema50.value
```

**Simpler Ansatz (nur Gewinn‑Trigger):**
```cel
pct_change(coalesce(trade.entry_price, trade.avg_entry_price), chart.price) >= 1.0
```

---

## 6) SL setzen und SL‑Hit prüfen

**Stop Hit Long/Short (Engine‑Funktionen):**
```cel
// Long Stop Loss getroffen?
stop_hit_long(trade, chart.price)

// Short Stop Loss getroffen?
stop_hit_short(trade, chart.price)
```

**Beispiel Exit-Regel (Stop ODER TP):**
```cel
stop_hit_long(trade, chart.price)
|| tp_hit(trade, chart.price)
```

---

## 7) Regime aus letzter Kerze verwenden
Wenn ein Regime‑Detector Regime‑Werte liefert, kannst du sie so einbinden:

```cel
!isnull(regime.current)
&& in_regime(regime.current, "bullish")
```

Fallback ohne Regime:
```cel
isnull(regime.current) || in_regime(regime.current, "bullish")
```

### Neue Regime-Funktionen (v2.4)

**Regime der letzten geschlossenen Kerze abrufen:**
```cel
// Entry nur wenn letztes Regime EXTREME_BULL oder EXTREME_BEAR
last_closed_regime() == 'EXTREME_BULL' || last_closed_regime() == 'EXTREME_BEAR'
```

**Regime-Analyse vor Entry-Prüfung auslösen:**
```cel
// Führe Regime-Analyse aus und prüfe dann letztes Regime
trigger_regime_analysis() && last_closed_regime() == 'EXTREME_BULL'
```

**Kombiniert mit Entry-Bedingungen:**
```cel
// Sicherstellen dass Regime-Daten aktuell sind, dann Entry
trigger_regime_analysis()
&& !is_trade_open(trade)
&& (last_closed_regime() == 'EXTREME_BULL' || last_closed_regime() == 'EXTREME_BEAR')
&& rsi14.value > 50
```

---

## 8) Typische Kombinationen (komplettes Beispiel)

**No Entry (Sicherheitsfilter):**
```cel
// Blockiere wenn Volatilität zu hoch ODER Regime nicht erlaubt
atrp > cfg.max_atrp_pct || has(cfg.no_trade_regimes, regime)
```

**Entry:**
```cel
chart.price > ema21.value
&& rsi14.value > 50
&& (!bot.require_regime_alignment || in_regime(regime.current, "bullish"))
```

**Exit (TP 2.5% oder SL hit):**
```cel
pct_change(coalesce(trade.entry_price, trade.avg_entry_price), chart.price) >= 2.5
|| stop_hit_long(trade, chart.price)
```

**Before Exit (nur wenn Trade offen):**
```cel
is_trade_open(trade)
```

**Update Stop (Trailing ab +1%):**
```cel
bot.trailing_stop_enabled == true
&& pct_change(coalesce(trade.entry_price, trade.avg_entry_price), chart.price) >= 1.0
```

---

## 9) Hinweise zu Variablen & Kontext

- **chart.*** kommt direkt vom Chartfenster (aktuelle Kerze + letzte Kerze).
- **bot.*** kommt aus der Bot‑Konfiguration.
- **regime.*** ist optional – nur wenn Regime‑Daten verfügbar sind.
- **trade.*** wird vom Trading‑System geliefert (z. B. entry_price, stop_loss, tp_price).
- Wenn Werte fehlen: nutze `isnull()` oder `coalesce()`.

---

## 10) Best Practices

- Halte Entry‑Regeln strikt, Exit‑Regeln klar und defensiv.
- Verwende Regime‑Checks nur, wenn Regime‑Daten wirklich vorhanden sind.
- Trailing Stop logisch in Update Stop, nicht im Entry.
- Nutze `coalesce()` für robuste Expressions.
- **No Entry Filter** als Sicherheitsfilter nutzen - wird VOR Entry geprüft.
- **Regime-Analyse** mit `trigger_regime_analysis()` sicherstellen, dass Daten aktuell sind.

---

## 11) JSON Entry System (Alternative zum CEL Editor)

### Was ist das JSON Entry System?

Neben dem CEL Editor (mit 5 Tabs: No Entry, Entry, Exit, Before Exit, Update Stop) gibt es nun ein **vereinfachtes JSON Entry System**, das sich **nur auf Entry-Logik** fokussiert.

**Hauptunterschiede:**

| Feature | CEL Editor (dieser Guide) | JSON Entry System |
|---------|---------------------------|-------------------|
| **Komplexität** | Hoch (5 Tabs, volle Pipeline) | Niedrig (nur Entry) |
| **Entry Logik** | CEL Rules via UI Editor | CEL Expression in JSON |
| **Exit/Stop** | CEL Rules via UI Editor | Aus UI-Feldern (SL/TP) |
| **Use Case** | Vollständige Strategy-Engine | Entry-Prototyping, A/B Tests |
| **Button** | "Start Bot" | "Start Bot (JSON Entry)" |

### Wann JSON Entry System nutzen?

✅ **Nutze JSON Entry wenn:**
- Du nur Entry-Bedingungen testen willst
- Du SL/TP/Trailing manuell aus UI-Feldern nutzt
- Du schnell verschiedene Entry-Expressions ausprobieren willst
- Du einfache CEL Expressions bevorzugst

✅ **Nutze CEL Editor wenn:**
- Du vollständige Kontrolle über Entry/Exit/Stop brauchst
- Du komplexe Multi-Stage-Strategien entwickelst
- Du No Entry Filter, Before Exit, Update Stop nutzt
- Du alle 5 Trading-Phasen in CEL steuern willst

### JSON Entry Expression Beispiel

**Regime JSON:**
```json
{
  "schema_version": "2.0.0",
  "indicators": {
    "rsi14": {"type": "RSI", "period": 14},
    "adx14": {"type": "ADX", "period": 14}
  },
  "entry_expression": "rsi < 35 && adx > 25 && macd_hist > 0"
}
```

**Verfügbare Variablen (ähnlich wie chart.* / bot.*):**
```cel
// Price
close, open, high, low, volume

// Indicators
rsi, adx, macd, macd_hist, sma_20, ema_12, bb_pct, atr

// Regime
regime  // "BULL", "BEAR", "NEUTRAL"

// Side
side  // "long" or "short"
```

**Simple Entry Expression:**
```cel
// RSI oversold + strong trend
rsi < 35 && adx > 25
```

**Complex Entry Expression:**
```cel
// Multi-indicator confluence
rsi < 35 && adx > 25 && macd_hist > 0 && (regime == 'BULL' || regime == 'EXTREME_BULL')
```

### Vollständige JSON Entry Dokumentation

Siehe für Details:
- **Complete Guide:** `04_Knowledgbase/JSON_Entry_System_Complete_Guide.md`
- **User Guide:** `docs/260128_JSON_Entry_System_README.md`
- **Help UI:** `Help/index.html#bot-json-entry`

---

## 12) Weitere Dokumentation

Für umfassende Dokumentation zu neuen Features siehe:

- **CEL_Neue_Funktionen_v2.4.md** - No Entry Workflow, Regime-Funktionen, 69+ Variablen
- **CEL_Befehle_Liste_v2.md** - Vollständige CEL Funktionsreferenz (97 Funktionen)
- **CEL_Functions_Reference_v3.md** - Detaillierte Funktionsbeschreibungen (v3.1)

