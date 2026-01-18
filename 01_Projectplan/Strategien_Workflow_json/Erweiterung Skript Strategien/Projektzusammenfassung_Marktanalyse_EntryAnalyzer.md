# Projekt-Zusammenfassung: Entry Analyzer + Marktanalyse (Regime) + Indikator-Backtesting + Bot-RegimeSet

## 1) Projektbeschreibung

### Ausgangslage
Du entwickelst in deiner Python-Tradingsoftware (Bitunix **BTCUSDT Futures**) zwei eng gekoppelte Bausteine:

1. **Chartfenster → Button „Entry Analyzer“**  
   Öffnet eine UI zur Analyse des aktuell geöffneten Charts.

2. **Trading Bot → Tab Bot → Button „Start Bot“**  
   Benötigt eine JSON-Datei **„Marktanalyse“** und daraus abgeleitet ein **regime-abhängiges Indikatorenset / StrategySet**.

### Ziel
Ein System, das den geöffneten Chart **automatisch in Marktregime segmentiert**, visuell im Chart markiert, danach **Indikatoren einzeln backtestet**, pro Regime **0–100 Scores** berechnet und daraus ein **RegimeSet** (Entry-/Exit-Indikatoren + Gewichte) generiert, das der Bot live nutzen kann.

### Kerneinschränkungen / Anforderungen
- **Zeitebenen**
  - **Daytrading/Scalping:** 24h auf **5m Kerzen**
  - **Swing Trading:** 7 Tage auf **1D Kerzen**
- **Markt/Instrument:** Bitunix **BTCUSDT Futures**
- **Wichtige Regimes:** Trendfolge, Seitwärtsmarkt (mit **Kursrange in %**), Breakout-Setups, High-Volatility, ggf. Orderflow-/Liquidity-Regime
- **Daten:** Volumen **und** (wenn verfügbar) **Orderbuch/Orderflow**
- **Realtime:** Bestmöglich, Verzögerungen **> 1 Minute** vermeiden
- **Prozess:** Zuerst **Einzelindikatoren** testen; Kombinationen kommen später.

---

## 2) Indikatoren – erweitert, strukturiert (Overlay / Bottom / Orderflow)

### Overlay-Indikatoren (im Chart)
**Trend**
- SMA, EMA (MA-Crossover / Price > MA als Trend-Bias)
- Ichimoku Cloud (Preis über/unter/in Wolke)
- Supertrend (ATR-basiert, auch als Trailing Exit)
- Parabolic SAR (Stop-and-Reverse)

**Breakout / Struktur**
- Donchian Channels (Breakout über Upper / unter Lower)
- Bollinger Bands (Band-Break, Band-Expansion)
- Keltner Channels (EMA ± ATR; Breakouts)
- Pivot Points (Levels als Trigger-/Target-Zonen)
- VWAP (intraday Bias/Level)

**Volatilität (Overlay/Envelope)**
- Bollinger, Keltner (auch über Bandbreite/Channel-Width ableitbar)

---

### Bottom/Panel-Indikatoren (unter dem Chart)
**Trendstärke & Regime**
- ADX (+DI/-DI)
- Choppiness Index (CHOP)
- Aroon (Up/Down)
- Vortex Indicator (VI+/VI-)
- Hurst Exponent (als Regime-Feature für Trend vs Mean-Reversion)

**Momentum**
- RSI
- MACD
- Stochastic
- CCI

**Volatilität**
- ATR / ATR% (ATRP)
- Bollinger BandWidth (BBWidth)

**Volumen**
- OBV (On-Balance Volume)
- MFI (Money Flow Index)
- A/D Line (Accumulation/Distribution)
- CMF (Chaikin Money Flow) (als weitere Kandidaten)

---

### Orderflow/Orderbuch (wenn Bitunix API es hergibt)
- Order Book Imbalance (OBI) z. B. (BidVol − AskVol)/(BidVol + AskVol) auf L1 oder Depth-N
- Spread (bps), Depth Bid/Ask (Liquidität)
- Optional: „Thin book“ / Depth-Delta als Liquiditätsregime

---

## 3) Marktregime-Taxonomie (Regime-IDs)

**R0 – Neutral/Unklar**  
Kein klares Signal (Übergangsphase).

**R1 – Trend (Up/Down)**  
Trendfolge / Trendhandel.

**R2 – Range/Chop (Seitwärtsmarkt)**  
Mean-Reversion/Range-Handel. Zusätzlich: **Range%** als Kernfeature.

**R3 – Breakout-Setup (Compression → Expansion)**  
Squeeze/Kompression, anschließend Ausbruch (Donchian/Keltner/BB).

**R4 – High Volatility (Wild)**  
Hohe Schwankung; Stop-/Risk-Logik anders.

**R5 – Orderflow/Liquidity Dominant**  
Orderbuchdruck dominiert kurzfristig.

---

## 4) Regime-Detektion: Single-Indicator-Classifier (isoliert backtestbar)

### ADX-Classifier
- ADX < 20 ⇒ R2
- 20–25 ⇒ R0
- > 25 ⇒ R1  
Richtung optional über +DI/-DI.

### CHOP-Classifier
- CHOP ≥ 61.8 ⇒ R2
- 38.2–61.8 ⇒ R0
- ≤ 38.2 ⇒ R1

### Ichimoku-Classifier (inkl. Richtung)
- Preis über Cloud ⇒ R1, UP
- Preis in Cloud ⇒ R2 (oder R0), NONE
- Preis unter Cloud ⇒ R1, DOWN

### TTM Squeeze / BBWidth / ATRP
- Squeeze ON oder BBWidth sehr niedrig ⇒ R3
- ATRP / BBWidth sehr hoch ⇒ R4

### Donchian-Event
- Close > Upper ⇒ Breakout aktiv (R3 → R1), UP
- Close < Lower ⇒ Breakout aktiv (R3 → R1), DOWN

### OBI-Classifier (Orderflow)
- |OBI| sehr hoch (Perzentil) ⇒ R5; Richtung = sign(OBI)

---

## 5) Composite-Regime-Engine (live-tauglich, deterministisch)

**Priorität (Regime-Typ):**
1. R5 wenn |OBI| > P90
2. R3 wenn Squeeze ON oder BBWidth < P20
3. R4 wenn ATRP > P80 oder BBWidth > P80
4. R1 wenn ADX > 25 oder CHOP < 38.2 oder Ichimoku außerhalb Cloud
5. R2 wenn ADX < 20 oder CHOP > 61.8 oder Ichimoku in Cloud
6. sonst R0

**Richtung (Bias):**
- R5: sign(OBI)
- R1: UP wenn +DI > -DI sonst DOWN (oder Ichimoku)
- R3: NONE bis Donchian-Break, dann UP/DOWN
- sonst NONE

**Anti-Flap/Hysterese:**
- Wechsel nur nach `confirm_bars` in Folge
- Optional `cooldown_bars`
- Mindestsegmentlänge `min_segment_bars`

---

## 6) Segment-Features (für Tabelle + Scoring + Visualisierung)

Pflicht pro Segment:
- `range_pct(N)` = (HH(N) − LL(N)) / mid(N) * 100
- `atrp` (ATR in %)
- `bbwidth` + Perzentile (`bbwidth_pctl`, `atrp_pctl`)
- `squeeze_on`
- optional: `obi`, `obi_pctl`, `spread_bps`, `depth_bid`, `depth_ask`

---

## 7) Scoring-System 0–100 (zwei Tracks)

### 7.1 Zwei Scores
1) **Regime-Quality-Score (0–100)**  
Wie gut klassifiziert ein Regime-Indikator im Vergleich zu `regime_ref` (zunächst Composite, später manuell/High-confidence).

2) **Trade-Quality-Score (0–100)**  
Wie gut performt ein Entry- oder Exit-Indikator **innerhalb eines Regimes**.

### 7.2 Fairer Einzelindikator-Test (ohne Kombi)
- **Entry-Track:** Entry vom Kandidaten, Exit = **Baseline** (z. B. Chandelier/ATR-Trail + Hard-Stop).
- **Exit-Track:** Entry = **Baseline**, Exit vom Kandidaten.

### 7.3 Empfohlene Metriken (Trade)
- Profit Factor (GrossProfit / GrossLoss)
- Expectancy
- Sortino (empfohlen) / Sharpe (optional)
- Max Drawdown
- WinRate, AvgWin, AvgLoss
- Slippage/Fee falls modelliert

### 7.4 Regime-Quality-Metriken
- Balanced Accuracy
- Macro-F1
- MCC
- Regime-Churn-Penalty (Switches/Bars)

### 7.5 Mapping auf 0–100
**Percentile-Rank** über alle Kandidaten pro Regime/Timeframe:
- score = 100 * percentile_rank(metric)
- für „kleiner besser“ (z. B. MDD): score = 100 * (1 − percentile_rank(MDD))

### 7.6 Regime-spezifische Gewichte (Beispiele)
- R1 Trend: Expectancy/Sortino/MDD stark gewichten
- R2 Range: MDD besonders stark gewichten
- R3 Breakout: Expectancy & PF stärker
- R5 Orderflow: zusätzliche „Freshness/Latency“-Proxy-Komponente

---

## 8) Maschinenlesbarer Indikator-Katalog (YAML) – Kandidaten & Parameter-Grids

> Aus der Konzeption: Indikatoren werden mit `type`, `roles`, `best_regimes` und `grid` beschrieben.  
> Beispiel (Kurzform; in deinem Projekt als vollständige YAML-Liste pflegen):

```yaml
indicators:
  - id: adx
    type: panel
    roles: [regime, entry, exit]
    best_regimes: [R1, R0, R2]
    grid:
      "5m": {length: [7,10,14,20]}
      "1D": {length: [10,14,20,28]}

  - id: supertrend
    type: overlay
    roles: [regime, entry, exit]
    best_regimes: [R1, R3]
    grid:
      "5m": {atr_len: [7,10,14], mult: [2.0,2.5,3.0,4.0]}
      "1D": {atr_len: [10,14,20], mult: [2.0,3.0,4.0]}

  - id: chandelier
    type: overlay
    roles: [exit]
    best_regimes: [R1, R3, R4]
    grid:
      "5m": {atr_len: [10,14,20], mult: [2.0,2.5,3.0,4.0]}
      "1D": {atr_len: [14,20], mult: [2.0,3.0,4.0]}
```

---

## 9) JSON-Schema für `Marktanalyse.json` + Beispielinstanz

### Zweck der Datei
- Persistiert die **Regime-Segmente** + Features,
- dokumentiert **IndicatorRuns** (Entry/Exit/Regime) mit Metriken & Scores,
- liefert ein final abgeleitetes **regime_set** (Gewichte & Parameter pro Regime/Timeframe).

### Inhalt (High-Level)
- `meta`: Symbol, Exchange, Timeframes, Datenfenster, Fee-/Slippage-Model
- `regime_engine`: Regeln, Thresholds, Anti-Flap
- `segments[]`: Segment-Start/End, Regime + Features (Range%, ATRP, BBWidth, OBI…)
- `indicator_runs[]`: pro Indikator-Param-Set, Regime & Track Metriken + Scores
- `regime_set`: Ergebnis (Entries/Exits/Gates pro Regime)

> Im Chat wurde ein komplettes Schema (Draft 2020-12) und eine Beispiel-JSON geliefert.

---

## 10) Mini-DSL v1 für `when` & `direction_expr`

### Design
- CEL-ähnliche Syntax: Operatoren, Ternary `?:`, `in`, Functions
- Strict Typing (Fehler deterministisch)
- `when` → bool, Fehler → false
- `direction_expr` → "UP"|"DOWN"|"NONE", Fehler → "NONE"

### Operatoren/Funktionen (Auszug)
- Logik: `&& || !`
- Vergleich: `== != < <= > >=`
- Zugehörigkeit: `in`
- Ternär: `cond ? a : b`
- Timeseries: `x[-n]` oder `lag(x,n)`
- Rolling: `sma`, `ema`, `stdev`, `highest`, `lowest`, `zscore`
- Statistik: `pctl(x, p, window?)`
- Events: `crossover(a,b)`, `crossunder(a,b)`
- Null: `isnull`, `nz`, `coalesce`

---

## 11) DSL-Testset (Parser-Fixtures)
Es wurde ein umfangreiches JSON-Testset definiert:
- Fixtures (`ctx_basic`, `ctx_market_trend_up`, `ctx_market_range`, `ctx_orderflow_hot`, `ctx_percentiles_simple`)
- Tests für Precedence, Klammern, Unary, `in`, Ternary, Lookback, Crossovers, Nullhandling, pctl, Error-Fallbacks, Anti-Flap Gates.

---

## 12) Empfohlene nächste Schritte (konkret)

1) **Regime-Engine v1 implementieren** (Composite + Anti-Flap)  
   Ausgabe: `segments[]` + Marker im Chart.

2) **Feature-Pipeline**  
   Range%, ATRP, BBWidth + Perzentile; optional OBI/Spread/Depth.

3) **Backtest-Runner v1**  
   - Entry-Track: Kandidat-Entry, Baseline-Exit (Chandelier)
   - Exit-Track: Baseline-Entry, Kandidat-Exit
   - Regime-Track: Kandidat-Regime vs Composite-Regime

4) **Scoring v1**  
   Percentile-Rank, Regime-Quality + Trade-Quality.

5) **Marktanalyse.json Writer**  
   Schema-konform, mit Versionierung und `extensions`.

6) **RegimeSet Builder**  
   Top-N pro Regime/Timeframe nach Score + Constraints (max indicators, min trades, overlap family).

7) **UI-Entscheidung Entry Analyzer**  
   - Wenn UI schon stabil: erweitern (Segmente, Tabelle, Filter, Export)
   - Wenn UI instabil/overgrown: neu, aber kompatibel zur JSON-Schnittstelle

---

## 13) Kurzfazit
Das Chat-Ergebnis ist ein vollständiger, konsistenter Entwurf für:
- Indikator-Kandidaten (Overlay/Panel/Orderflow) inkl. Entry/Exit
- Marktregime-Definitionen + Detektionsregeln (Single + Composite)
- Scoring 0–100 (Regime-Quality vs Trade-Quality) + Anti-Overfit
- Persistenzformat `Marktanalyse.json` (Schema + Beispiel)
- Mini-DSL (Rules) + Parser-Testset

Damit kannst du jetzt in deiner Software den **Entry Analyzer als Backtest-/Analyse-Frontend** etablieren und dem Bot eine **stabile, versionierte Marktanalyse-Schnittstelle** geben.
