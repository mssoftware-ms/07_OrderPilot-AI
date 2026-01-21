Unten bekommst du **(1) eine saubere Marktregime-Taxonomie** für BTCUSDT-Futures (5m/1D) **und (2) eine maschinenlesbare Indikator-Liste** (Overlay/Panel/Orderflow), jeweils mit **Eignung pro Regime** sowie **Rolle: Regime-Detektion / Entry / Exit** und **Parameter-Grids** fürs Backtesting.

---

## 1) Marktregime, die einen Strategiewechsel erzwingen

### R0 – Neutral / “Unklar”

**Definition:** Kein klares Trend- oder Range-Signal, Übergangsphase.
**Typisch:** ADX im Graubereich 20–25. ([ChartSchool][1])
**Aktion:** Positionsgröße runter, keine aggressiven Breakouts handeln.

---

### R1 – Trend (Up/Down) – “Trend-Following”

**Detektion (Single-Indikatoren):**

* **ADX**: Trend stark wenn **>25**, kein Trend wenn **<20**. ([ChartSchool][1])
* **Aroon**: systematisch “trending or not”, misst Zeit seit Hoch/Tief. ([ChartSchool][2])
* **Vortex (VI+/VI-)**: Trendrichtung/Trendwechsel via Cross der Linien. ([ChartSchool][3])
* Optional “Quant”: **Hurst Exponent** > 0.5 = eher trendig, < 0.5 = eher mean-reverting. ([Macrosynergy][4])

**Entry-Kandidaten (trend):**

* **Supertrend** (ATR+Multiplikator) ([Investopedia][5])
* **EMA/SMA-Crossover / Price>MA** (klassisch trendfolgend)
* **VWAP-Bias** intraday (Preis über/unter VWAP) ([ChartSchool][6])

**Exit-Kandidaten (trend):**

* **Chandelier Exit** (HighestHigh − k×ATR) ([Investopedia][7])
* **Parabolic SAR** (Stop-and-Reverse Punkte) ([ChartSchool][8])
* **Supertrend Flip** ([Investopedia][5])

---

### R2 – Range / Seitwärts / “Chop”

**Detektion:**

* **ADX < 20** ⇒ “no trend”. ([ChartSchool][1])
* **Choppiness Index (CHOP)**: misst explizit “choppy (sideways) vs trend”. ([TradingView][9])
* **Hurst < 0.5**: eher mean-reverting. ([Robot Wealth][10])

**Range in % (für deine UI-Anforderung):**

* **Range% (Fenster N)** = (HighestHigh(N) − LowestLow(N)) / MidPrice(N) × 100
  → Das ist kein “Indikator” im klassischen Sinn, aber ein extrem brauchbares **Regime-Feature** (und perfekt für deine Tabelle/Scoring).

**Entry (Range):**

* **Bollinger Bands** Touch/Rejection (Range-Logik) + **RSI/MFI** Extrembereiche (später kombinieren). ([Investopedia][11])

**Exit (Range):**

* **Midline/Mean** (z. B. BB-Middle) oder feste Range-Ziele (Range% basiert).

---

### R3 – Breakout-Setup (Compression → Expansion)

**Detektion:**

* **TTM Squeeze**: BB komplett *innerhalb* Keltner ⇒ Low-Vol; “Squeeze fired” bei Expansion. ([ChartSchool][12])
* **Bollinger Band Squeeze** als Konzept (Volatilitätskontraktion vor Breakout). ([Investopedia][11])

**Entry (Breakout):**

* **Donchian Channels**: Break über Upper/unter Lower. ([Investopedia][13])
* **Keltner Break** (EMA±ATR-Envelopes). ([ChartSchool][14])

**Exit (Breakout):**

* **Chandelier / ATR-Trail** (schnell, robust) ([Investopedia][7])
* **Failed Breakout**: Rückfall in Kanal/Band.

---

### R4 – High-Volatility “Wild”

**Detektion:** ATR/BB-Width hoch (relativ zum eigenen Durchschnitt); viele Whipsaws. (ATR als Volatilitätsmaß ist Standard.) ([Investopedia][7])
**Aktion:** Stops dynamisch (ATR), Entries strenger (z. B. nur Breakouts mit Volumen/Orderflow-Bestätigung).

---

### R5 – Liquidity / Orderflow Regime (Orderbuch dominiert)

**Detektion/Features:**

* **Order Book Imbalance (OBI)**: (BidVol−AskVol)/(BidVol+AskVol) ∈ [-1,1]. ([QuestDB][15])
* Depth/Spread (wenn Bitunix liefert): “Thin book” ⇒ Ausbrüche unzuverlässiger, Slippage höher.

**Entry/Exit:**

* OBI-Shift als *sehr* kurzfristiger Trigger/Exit (noisy, aber reaktionsschnell). ([QuestDB][15])

---

## 2) Maschinenlesbarer Indikator-Katalog (Overlay / Panel / Orderflow)

Format: **YAML** (leicht nach JSON zu konvertieren).
Felder:

* `type`: overlay | panel | orderflow
* `roles`: regime | entry | exit
* `best_regimes`: R1..R5
* `grid`: sinnvolle Testbereiche (nicht “alles”, sondern backtestbar ohne OOM)

```yaml
indicators:

  - id: adx
    name: "ADX (+DI/-DI)"
    type: panel
    category: trend_strength
    roles: [regime, entry, exit]
    best_regimes: [R1, R0, R2]
    notes: "Wilder: <20 kein Trend, >25 starker Trend."
    sources: [turn0search9]
    grid:
      "5m": {length: [7, 10, 14, 20]}
      "1D": {length: [10, 14, 20, 28]}

  - id: chop
    name: "Choppiness Index (CHOP)"
    type: panel
    category: regime_chop
    roles: [regime]
    best_regimes: [R2, R0]
    notes: "Nicht-direktional: choppy vs trending."
    sources: [turn3search5]
    grid:
      "5m": {length: [14, 21, 34]}
      "1D": {length: [14, 21, 34]}

  - id: hurst
    name: "Hurst Exponent"
    type: panel
    category: regime_memory
    roles: [regime]
    best_regimes: [R1, R2]
    notes: "H>0.5 trendig, H<0.5 mean-reverting (als Regime-Feature)."
    sources: [turn3search19, turn3search3]
    grid:
      "5m": {window: [128, 256, 512]}
      "1D": {window: [64, 128, 256]}

  - id: aroon
    name: "Aroon Up/Down"
    type: panel
    category: trend_detection
    roles: [regime, entry]
    best_regimes: [R1, R0]
    notes: "Misst Perioden seit Hoch/Tief, zeigt Trendbeginn/Trendphase."
    sources: [turn3search0]
    grid:
      "5m": {length: [14, 25, 50]}
      "1D": {length: [14, 25, 50]}

  - id: vortex
    name: "Vortex Indicator (VI+/VI-)"
    type: panel
    category: trend_direction
    roles: [regime, entry, exit]
    best_regimes: [R1, R0]
    notes: "Cross von VI+/VI- für Richtung/Wechsel."
    sources: [turn4search3, turn4search0]
    grid:
      "5m": {length: [7, 14, 21]}
      "1D": {length: [14, 21, 34]}

  - id: vwap
    name: "VWAP (intraday)"
    type: overlay
    category: volume_price
    roles: [regime, entry, exit]
    best_regimes: [R1, R3, R5]
    notes: "Volumen-gewichteter Durchschnittspreis für den Tag."
    sources: [turn1search0, turn1search12]
    grid:
      "5m": {mode: ["session_vwap"], bands: ["none", "stdev_1", "stdev_2"]}
      "1D": {mode: ["n/a"]}

  - id: keltner
    name: "Keltner Channels (EMA ± ATR)"
    type: overlay
    category: volatility_envelope
    roles: [regime, entry, exit]
    best_regimes: [R3, R1]
    notes: "Typisch 20-EMA, Bänder via ATR (z.B. 2×ATR)."
    sources: [turn0search1]
    grid:
      "5m": {ema: [20], atr_len: [10,14,20], mult: [1.5,2.0,2.5]}
      "1D": {ema: [20], atr_len: [14,20], mult: [1.5,2.0,2.5]}

  - id: ttm_squeeze
    name: "TTM Squeeze (BB inside Keltner)"
    type: panel
    category: compression_breakout
    roles: [regime, entry]
    best_regimes: [R3]
    notes: "BB innerhalb Keltner = Squeeze; 'fired' bei Expansion."
    sources: [turn2search12]
    grid:
      "5m": {bb_len: [20], bb_k: [2.0], kc_ema: [20], kc_atr: [14], kc_mult: [1.5,2.0]}
      "1D": {bb_len: [20], bb_k: [2.0], kc_ema: [20], kc_atr: [14], kc_mult: [1.5,2.0]}

  - id: donchian
    name: "Donchian Channels"
    type: overlay
    category: breakout_channel
    roles: [regime, entry, exit]
    best_regimes: [R3, R1]
    notes: "Highest high / lowest low über Lookback; Breakouts."
    sources: [turn0search0, turn0search3]
    grid:
      "5m": {length: [10, 20, 34, 55]}
      "1D": {length: [20, 50]}

  - id: supertrend
    name: "Supertrend (ATR × Mult)"
    type: overlay
    category: trend_trailing
    roles: [regime, entry, exit]
    best_regimes: [R1, R3]
    notes: "ATR-Länge + Multiplikator steuern Empfindlichkeit."
    sources: [turn1search2, turn1search6]
    grid:
      "5m": {atr_len: [7,10,14], mult: [2.0, 2.5, 3.0, 4.0]}
      "1D": {atr_len: [10,14,20], mult: [2.0, 3.0, 4.0]}

  - id: psar
    name: "Parabolic SAR"
    type: overlay
    category: stop_and_reverse
    roles: [entry, exit]
    best_regimes: [R1]
    notes: "Am besten in Trends; whipsaws in Range."
    sources: [turn1search1, turn1news44]
    grid:
      "5m": {step: [0.01, 0.02], max: [0.1, 0.2]}
      "1D": {step: [0.01, 0.02], max: [0.1, 0.2]}

  - id: chandelier
    name: "Chandelier Exit (HighestHigh - k*ATR)"
    type: overlay
    category: volatility_trailing_exit
    roles: [exit]
    best_regimes: [R1, R3, R4]
    notes: "ATR-basiertes Trailing; robust für schnelle Exits."
    sources: [turn0search2, turn0search5]
    grid:
      "5m": {atr_len: [10,14,20], mult: [2.0, 2.5, 3.0, 4.0]}
      "1D": {atr_len: [14,20], mult: [2.0, 3.0, 4.0]}

  - id: obv
    name: "On-Balance Volume (OBV)"
    type: panel
    category: volume_flow
    roles: [regime, entry, exit]
    best_regimes: [R1, R3, R5]
    notes: "Kumulatives Volumen: addiert bei Up-Close, subtrahiert bei Down-Close."
    sources: [turn2search0]
    grid:
      "5m": {smoothing: ["none", "ema_10", "ema_20"]}
      "1D": {smoothing: ["none", "ema_10", "ema_20"]}

  - id: mfi
    name: "Money Flow Index (MFI)"
    type: panel
    category: volume_oscillator
    roles: [entry, exit, regime]
    best_regimes: [R2, R3, R5]
    notes: "Volumen-gewichteter RSI; misst Kauf-/Verkaufsdruck."
    sources: [turn2search1]
    grid:
      "5m": {length: [7, 10, 14, 20], levels: [[20,80],[25,75]]}
      "1D": {length: [10, 14, 20], levels: [[20,80],[25,75]]}

  - id: adl
    name: "Accumulation/Distribution Line (A/D)"
    type: panel
    category: volume_supply_demand
    roles: [regime, entry, exit]
    best_regimes: [R1, R3, R5]
    notes: "Kumulativer Money-Flow (Chaikin) → Angebot/Nachfrage."
    sources: [turn2search2]
    grid:
      "5m": {smoothing: ["none", "ema_10", "ema_20"]}
      "1D": {smoothing: ["none", "ema_10", "ema_20"]}

  - id: obi
    name: "Order Book Imbalance (OBI)"
    type: orderflow
    category: orderbook_pressure
    roles: [regime, entry, exit]
    best_regimes: [R5, R3]
    notes: "OBI=(BidVol-AskVol)/(BidVol+AskVol) auf L1 oder Depth-N."
    sources: [turn1search3, turn1search11]
    grid:
      "5m": {depth_levels: [1, 5, 10], smooth_ms: [0, 250, 500, 1000]}
      "1D": {depth_levels: [1, 5, 10], smooth_ms: [0, 500, 1000]}
```

---

## 3) Was du damit im Entry Analyzer sofort sauber abbilden kannst

1. **Regime-Split im Chart**

* Regime-Engine tickt z. B. alle 1–5 Sekunden (Orderflow) + pro Candle-Close (klassische Indikatoren).
* Vertikale Linien da, wo `regime_id` wechselt (R1↔R2↔R3…).
* Seitwärtsmarkt zusätzlich mit **Range%** je Segment ausgeben (deine Anforderung).

2. **Einzelindikator-Backtests je Regime**

* Für jedes Segment: pro Indikator aus YAML `grid` iterieren → Score 0–100.
* Indikatoren, die “Regime” können (ADX/CHOP/TTM/Hurst), getrennt bewerten: *Regime-Quality* vs *Trade-Performance*.

3. **Entry- & Exit-Indikatoren trennen**

* “Entry-Indikatoren” (Donchian/Supertrend/VWAP) nicht mit “Exit-Indikatoren” (Chandelier/PSAR) vermischen – getrennte Scores.
  Das verhindert, dass dir ein guter Exit-Stop fälschlich als guter Entry getarnt wird.

---

Wenn du als Nächstes willst, liefere ich dir daraus eine **konkrete “Regime Rules”-Matrix** (z. B. `R1 if ADX>25 and CHOP low …`) – bewusst so designt, dass du sie **ohne Kombi-Logik** erstmal als **einzelne “Gates”** testen kannst.

[1]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx?utm_source=chatgpt.com "Average Directional Index (ADX) - ChartSchool"
[2]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/aroon?utm_source=chatgpt.com "Aroon - ChartSchool - StockCharts.com"
[3]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/vortex-indicator?utm_source=chatgpt.com "Vortex Indicator - ChartSchool - StockCharts.com"
[4]: https://macrosynergy.com/research/detecting-trends-and-mean-reversion-with-the-hurst-exponent/?utm_source=chatgpt.com "Detecting trends and mean reversion with the Hurst exponent"
[5]: https://www.investopedia.com/supertrend-indicator-7976167?utm_source=chatgpt.com "Supertrend Indicator: What It Is and How It Works"
[6]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/volume-weighted-average-price-vwap?utm_source=chatgpt.com "Volume-Weighted Average Price (VWAP) - ChartSchool"
[7]: https://www.investopedia.com/articles/trading/08/atr.asp?utm_source=chatgpt.com "Enter Profitable Territory With Average True Range"
[8]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/parabolic-sar?utm_source=chatgpt.com "Parabolic SAR - ChartSchool - StockCharts.com"
[9]: https://www.tradingview.com/support/solutions/43000501980-choppiness-index-chop/?utm_source=chatgpt.com "Choppiness Index (CHOP)"
[10]: https://robotwealth.com/demystifying-the-hurst-exponent-part-2/?utm_source=chatgpt.com "Hurst Exponent in Algo Trading"
[11]: https://www.investopedia.com/trading/using-bollinger-bands-to-gauge-trends/?utm_source=chatgpt.com "How to Use Bollinger Bands to Gauge Trends"
[12]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/ttm-squeeze?utm_source=chatgpt.com "TTM Squeeze - ChartSchool - StockCharts.com"
[13]: https://www.investopedia.com/terms/d/donchianchannels.asp?utm_source=chatgpt.com "Understanding Donchian Channels: Formula, Calculation, ..."
[14]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/keltner-channels?utm_source=chatgpt.com "Keltner Channels - ChartSchool - StockCharts.com"
[15]: https://questdb.com/glossary/order-book-imbalance/?utm_source=chatgpt.com "Order Book Imbalance"
