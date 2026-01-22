# Regime Parameter - Sinnvolle Wertebereiche

**Datum:** 2026-01-22
**Quelle:** Research-basierte Analyse + Quantitative Trading Best Practices

---

## Übersicht

Dieses Dokument definiert **sinnvolle Wertebereiche** für alle Parameter, die bei der Regime-Erkennung verwendet werden. Die Bereiche basieren auf:
- Web-Recherche zu technischen Indikatoren ([Schwab](https://www.schwab.com/learn/story/spot-and-stick-to-trends-with-adx-and-rsi), [TradingView](https://www.tradingview.com/scripts/averagedirectionalindex/), [QuantifiedStrategies](https://www.quantifiedstrategies.com/indicators-for-technical-analysis/))
- Quantitative Trading Literatur
- Backtesting-Erfahrungen
- Marktregime-Klassifikation Standards

---

## 1. ADX (Average Directional Index)

### Parameter: `period`

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **3-5** | Ultra-kurzfristig | Scalping, hochfrequenter Handel |
| **7-10** | Kurzfristig | Day Trading (5-15 min Charts) |
| **14** | **Standard** (empfohlen) | Swing Trading, alle Timeframes |
| **20-25** | Mittelfristig | Position Trading (Daily/4H) |
| **30+** | Langfristig | Wochenanalyse, Makrotrends |

**Optimaler Bereich für Entry Analyzer:** `10-20` (anpassbar je Timeframe)

### Threshold: ADX-Level für Trendstärke

| Threshold | Interpretation | Regime |
|-----------|----------------|--------|
| **< 17** | Sehr schwacher Trend | Range / Konsolidierung |
| **17-25** | Schwacher bis neutraler Trend | Range oder beginnender Trend |
| **25-40** | **Starker Trend** (empfohlen) | Trend-basierte Strategien |
| **40-50** | Sehr starker Trend | Extreme Trends, nahe Peak |
| **> 50** | Extremer Trend | Reversal-Warnung, Momentum-Peak |

**Quellen:**
- [Schwab: ADX and RSI](https://www.schwab.com/learn/story/spot-and-stick-to-trends-with-adx-and-rsi)
- [TradingView: ADX](https://www.tradingview.com/scripts/averagedirectionalindex/)

---

## 2. RSI (Relative Strength Index)

### Parameter: `period`

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **5-7** | Ultra-schnell | Day Trading (1-5 min Charts), mehr Signale |
| **9** | Schnell | Intraday Trading (15 min Charts) |
| **14** | **Standard** (empfohlen) | Universell, alle Timeframes |
| **21** | Langsamer | Swing Trading, weniger False Positives |
| **25-30** | Sehr langsam | Position Trading (Daily+) |

**Optimaler Bereich für Entry Analyzer:** `9-21` (je nach Timeframe)

### Threshold: Overbought/Oversold Levels

| Threshold | Level | Interpretation | Regime |
|-----------|-------|----------------|--------|
| **< 20** | Extrem Oversold | Starkes Reversal-Signal | Range - Extreme Oversold |
| **20-30** | **Oversold (Standard)** | Mean-Reversion Kandidat | Range - Oversold |
| **30-40** | Leicht Bearish | Untere Neutralzone | Schwacher Downtrend |
| **40-60** | **Neutral** | Keine klare Richtung | Range |
| **60-70** | Leicht Bullish | Obere Neutralzone | Schwacher Uptrend |
| **70-80** | **Overbought (Standard)** | Mean-Reversion Kandidat | Range - Overbought |
| **> 80** | Extrem Overbought | Starkes Reversal-Signal | Range - Extreme Overbought |

**Trading-Spezifisch:**
- **Day Trading:** 80/20 (extremere Levels für weniger False Signals)
- **Swing Trading:** 70/30 (Standard)
- **Range-Bound Markets:** 70/30 mit ADX < 25
- **Trending Markets:** 80/20 (Trends können länger "überkauft" bleiben)

**Quellen:**
- [TradingView: RSI](https://www.tradingview.com/scripts/relativestrengthindex/)
- [QuantifiedStrategies: RSI Trading](https://www.quantifiedstrategies.com/rsi-trading-strategy/)

---

## 3. MACD (Moving Average Convergence Divergence)

### Parameter: `fast` (Fast EMA Period)

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **8-10** | Ultra-schnell | Scalping, kurzfristige Signale |
| **12** | **Standard** (empfohlen) | Universell |
| **15-18** | Mittelfristig | Weniger Whipsaws |

**Optimaler Bereich:** `8-15`

### Parameter: `slow` (Slow EMA Period)

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **21-24** | Schnell | Day Trading |
| **26** | **Standard** (empfohlen) | Universell |
| **30-34** | Langsam | Swing Trading, geglättete Signale |

**Optimaler Bereich:** `21-34`

### Parameter: `signal` (Signal Line Period)

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **7-8** | Schnell | Frühere Crossover-Signale |
| **9** | **Standard** (empfohlen) | Balancierte Signale |
| **11-12** | Langsam | Konservativere Signale |

**Optimaler Bereich:** `7-12`

### Threshold: Histogram für Regime

| Wert | Interpretation | Regime |
|------|----------------|--------|
| **> 0** | Bullish Momentum | Uptrend (wenn ADX > 25) |
| **≈ 0** | Kein Momentum | Range / Neutral |
| **< 0** | Bearish Momentum | Downtrend (wenn ADX > 25) |

**Kombination mit ADX:** MACD-Richtung bestimmt Trend-Richtung, ADX bestimmt Trend-Stärke

---

## 4. Bollinger Bands (BB)

### Parameter: `period` (Moving Average Period)

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **10-15** | Kurz | Day Trading, schnelle Reaktion |
| **20** | **Standard** (empfohlen) | Universell |
| **30-50** | Lang | Position Trading, geglättete Bänder |

**Optimaler Bereich:** `15-30`

### Parameter: `std_dev` (Standard Deviation Multiplier)

| Wert | Beschreibung | Interpretation |
|------|--------------|----------------|
| **1.5** | Eng | Mehr Touchpoints, mehr Signale |
| **2.0** | **Standard** (empfohlen) | Balanciert (~95% der Daten) |
| **2.5** | Weit | Weniger False Breakouts |
| **3.0** | Sehr weit | Nur extreme Bewegungen |

**Optimaler Bereich:** `1.5-2.5`

### Threshold: %B Indicator (Preis-Position in Bändern)

| %B Wert | Interpretation | Regime |
|---------|----------------|--------|
| **< 0** | Unter unterem Band | Extreme Oversold |
| **0-0.2** | Nahe unterem Band | **Oversold** |
| **0.2-0.4** | Untere Hälfte | Leicht Bearish |
| **0.4-0.6** | **Neutral** | Range / Mittlerer Bereich |
| **0.6-0.8** | Obere Hälfte | Leicht Bullish |
| **0.8-1.0** | Nahe oberem Band | **Overbought** |
| **> 1.0** | Über oberem Band | Extreme Overbought |

**Quellen:**
- [Britannica: Bollinger Bands](https://www.britannica.com/money/bollinger-bands-indicator)
- [StockCharts: %B Indicator](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator)

---

## 5. ATR (Average True Range)

### Parameter: `period`

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **7-10** | Kurzfristig | Day Trading, schnelle Volatilität |
| **14** | **Standard** (empfohlen) | Universell |
| **20-22** | Mittelfristig | Swing Trading |
| **30+** | Langfristig | Position Trading |

**Optimaler Bereich:** `10-20`

### Threshold: ATR% (ATR als % vom Preis)

| ATR% | Interpretation | Volatility Level |
|------|----------------|------------------|
| **< 0.5%** | Sehr niedrig | LOW |
| **0.5-1.0%** | Niedrig | LOW-NORMAL |
| **1.0-2.0%** | **Normal** | NORMAL |
| **2.0-3.0%** | Erhöht | HIGH |
| **3.0-5.0%** | Hoch | HIGH-EXTREME |
| **> 5.0%** | Sehr hoch | EXTREME |

**Anwendung:** Stop-Loss-Distanz = ATR × Multiplier (typisch 1.5-3.0)

---

## 6. Volume Ratio (Volume vs. Moving Average)

### Parameter: `period` (Volume MA Period)

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **10-15** | Kurzfristig | Day Trading |
| **20** | **Standard** (empfohlen) | Universell |
| **30-50** | Langfristig | Position Trading |

**Optimaler Bereich:** `15-30`

### Threshold: Volume Ratio Level

| Ratio | Interpretation | Regime Impact |
|-------|----------------|---------------|
| **< 0.5** | Sehr niedrig | Schwache Konviction, Konsolidierung |
| **0.5-0.8** | Niedrig | Leichte Aktivität |
| **0.8-1.2** | **Normal** | Durchschnittliches Volumen |
| **1.2-1.5** | Erhöht | Bestätigung (für Trend: 1.5+) |
| **1.5-2.5** | Hoch | **Starke Bestätigung** (Trend/Breakout) |
| **> 2.5** | Extrem | **Extreme Bewegung** (News, Volatilität) |

**Verwendung:**
- Trend-Bestätigung: Volume Ratio > 1.5 bei Trend-Start
- Range-Erkennung: Volume Ratio < 1.0 bei niedrigem ADX

---

## 7. Momentum Score (Custom Composite)

Berechnung: `(SMA_Fast - SMA_Slow) / SMA_Slow × 100 × 0.6 + (Close - SMA_Fast) / SMA_Fast × 100 × 0.4`

### Parameter: `sma_fast`

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **10-15** | Sehr schnell | Day Trading |
| **20** | **Standard** (empfohlen) | Universell |
| **30** | Langsam | Swing Trading |

**Optimaler Bereich:** `10-30`

### Parameter: `sma_slow`

| Wert | Beschreibung | Einsatz |
|------|--------------|---------|
| **50** | **Standard** (empfohlen) | Mittelfristig |
| **100** | Langsam | Langfristig |
| **200** | Sehr langsam | Makrotrends |

**Optimaler Bereich:** `50-100`

### Threshold: Momentum Score Level

| Score | Interpretation | Regime |
|-------|----------------|--------|
| **< -4.0** | Extreme Downtrend | **Extreme Downtrend** |
| **-4.0 to -2.0** | Strong Downtrend | **Strong Downtrend** |
| **-2.0 to -0.5** | Moderate Downtrend | Moderate Downtrend |
| **-0.5 to 0.5** | **Neutral** | Range |
| **0.5 to 2.0** | Moderate Uptrend | Moderate Uptrend |
| **2.0 to 4.0** | Strong Uptrend | **Strong Uptrend** |
| **> 4.0** | Extreme Uptrend | **Extreme Uptrend** |

---

## 8. Zusammenfassende Parameter-Matrix

| Indikator | Parameter | Minimum | Standard | Maximum | Schritte |
|-----------|-----------|---------|----------|---------|----------|
| **ADX** | period | 10 | 14 | 20 | 2 |
| **ADX** | threshold | 17 | 25 | 50 | 5 |
| **RSI** | period | 9 | 14 | 21 | 3 |
| **RSI** | oversold | 20 | 30 | 40 | 5 |
| **RSI** | overbought | 60 | 70 | 80 | 5 |
| **MACD** | fast | 8 | 12 | 15 | 1 |
| **MACD** | slow | 21 | 26 | 34 | 2 |
| **MACD** | signal | 7 | 9 | 12 | 1 |
| **BB** | period | 15 | 20 | 30 | 5 |
| **BB** | std_dev | 1.5 | 2.0 | 2.5 | 0.25 |
| **ATR** | period | 10 | 14 | 20 | 2 |
| **Volume** | period | 15 | 20 | 30 | 5 |
| **Volume** | ratio_threshold | 1.0 | 1.5 | 2.5 | 0.5 |
| **Momentum** | sma_fast | 10 | 20 | 30 | 5 |
| **Momentum** | sma_slow | 50 | 50 | 100 | 25 |
| **Momentum** | score_threshold | -4.0 | -2.0 | 4.0 | 1.0 |

---

## 9. Simulationsstrategie

### Grid Search Parameters

Für die Regime-Parameter-Optimierung empfohlene Grid-Search-Dimensionen:

**Minimal (schnell):**
- ADX threshold: [17, 25, 40] → 3 Werte
- RSI oversold/overbought: [20/80, 30/70] → 2 Kombinationen
- → **6 Kombinationen** (~30 Sekunden)

**Balanced (empfohlen):**
- ADX: period [10, 14, 20], threshold [17, 25, 40] → 9 Kombinationen
- RSI: period [9, 14, 21], oversold [20, 30], overbought [70, 80] → 12 Kombinationen
- MACD: [8/21/7, 12/26/9, 15/34/12] → 3 Kombinationen
- → **324 Kombinationen** (~10-15 Minuten)

**Exhaustive (langsam):**
- Alle Parameter mit minimalen Schritten
- → **~10,000+ Kombinationen** (~2-4 Stunden)

### Evaluationsmetriken

Für jede Parameter-Kombination:
1. **Regime Detection Accuracy:** Wie oft werden Regimes korrekt erkannt?
2. **Regime Duration:** Durchschnittliche Dauer pro Regime (Stabilität)
3. **Regime Switches:** Anzahl der Regime-Wechsel (weniger = stabiler)
4. **Profit Factor:** Wenn mit Trades kombiniert
5. **Win Rate:** Wenn mit Entry/Exit-Signalen kombiniert

---

## 10. Quellen

### Web-Recherche
- [Schwab: Spot and Stick to Trends with ADX and RSI](https://www.schwab.com/learn/story/spot-and-stick-to-trends-with-adx-and-rsi)
- [TradingView: Average Directional Index (ADX)](https://www.tradingview.com/scripts/averagedirectionalindex/)
- [TradingView: Relative Strength Index (RSI)](https://www.tradingview.com/scripts/relativestrengthindex/)
- [QuantifiedStrategies: Best Indicators for Technical Analysis 2025](https://www.quantifiedstrategies.com/indicators-for-technical-analysis/)
- [QuantifiedStrategies: RSI Trading Strategy](https://www.quantifiedstrategies.com/rsi-trading-strategy/)
- [Mind Math Money: Trading Indicators Masterclass 2025](https://www.mindmathmoney.com/articles/the-complete-trading-indicators-masterclass-transform-your-technical-analysis-in-2025)
- [Britannica: Bollinger Bands Explained](https://www.britannica.com/money/bollinger-bands-indicator)
- [StockCharts: %B Indicator](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/b-indicator)
- [High Strike: Bollinger Bands Strategy 2025](https://highstrike.com/bollinger-bands-strategy/)
- [EODHD: ADX and RSI Trading Strategy](https://eodhd.com/financial-academy/backtesting-strategies-examples/does-combining-adx-and-rsi-create-a-better-profitable-trading-strategy)

### Code-Referenzen
- `src/core/tradingbot/regime_engine_json.py`
- `03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json`
- `03_JSON/Trading_Bot/*.json`

---

## Zusammenfassung

✅ **Research-basierte Wertebereiche** für alle Regime-Parameter
✅ **Quellen dokumentiert** mit direkten Links
✅ **Timeframe-spezifische Empfehlungen**
✅ **Parameter-Matrix** für Grid-Search-Optimierung
✅ **Simulationsstrategie** (Minimal/Balanced/Exhaustive)
✅ **Evaluationsmetriken** für Regime-Qualität
