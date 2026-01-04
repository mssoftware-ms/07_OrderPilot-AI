# Krypto-Trading: Strategien, Zeiteinheiten, Indikator-Sets & Trendkontext (Higher Timeframes)

Diese Übersicht führt **beide Ausarbeitungen** zusammen:
1) *Strategie-spezifische* **Zeitintervalle + Indikator-Sets** (global definierbar)  
2) *Übergeordnete* **Trendkontext-Charts** (Higher Timeframes) inkl. Zeitraum & Kerzentyp

> **Hinweis (wichtig):** Das ist ein praxisnahes **Best-Practice-Setup** für generelles Krypto-Trading (BTC/ETH/Alts). Für Futures/Perps bleiben die Logiken identisch – nur Risiko-/Fee-Handling wird strenger.

---

## Kompakt-Definitionen

- **Execution TF**: Zeiteinheit, auf der du *Entries/Stops* triggert (feinste Signale).  
- **Context TF**: Zeiteinheit, die die *lokale Struktur* (Range/Trend, SFP-Level, Micro-Structure) stabil abbildet.  
- **Trend/Macro TF**: Zeiteinheit, die den *übergeordneten Trendkontext* + Key-Levels liefert (wo du **nicht gegen** den Markt arbeiten willst).

---

## Gesamtübersicht als Tabelle

| Strategie | Execution TF (Entry/Trigger) | Context TF (Struktur) | Trend/Macro TF (Trendkontext) | Empfohlener Betrachtungszeitraum (Lookback) | Kerzen (typisch) | Globales Indikator-Set (praxisnah) | Wofür dieses Set gut ist |
|---|---|---|---|---|---|---|---|
| **Scalping** | **1m** (optional 3m) | **5m** (optional 15m) | **1h + 1D** (optional 1W für Major-Level) | 1m: **6–24h** · 5m: **2–7 Tage** · 1h: **2–4 Wochen** · 1D: **3–6 Monate** · 1W: **1–2 Jahre** | 1m/5m für Trades, 1h/1D/1W für Kontext | **EMA(9/21)**, **RSI(14)**, **Bollinger(20,2)** + **%B/BBWidth**, **ATR(14)**, **Stoch(14,3,3)**, **ADX(14)**, **Volumen** | Sehr schnelle Reaktionsfähigkeit, Range/Mean-Reversion & Micro-Impulse. BB/RSI/Stoch für Overextension, ATR für SL/Noise, EMAs für Micro-Trend, ADX als Chop-/Trend-Filter. |
| **Daytrading** | **5m oder 15m** | **1h** | **4h + 1D** (optional 1W) | 5m/15m: **2–10 Tage** · 1h: **2–8 Wochen** · 4h: **3–6 Monate** · 1D: **6–12 Monate** · 1W: **1–3 Jahre** | 5m/15m für Entries, 1h/4h/1D für Trend & Levels | **EMA(20/50/200)**, **RSI(14)**, **MACD(12,26,9)**, **Bollinger(20,2)** + **BBWidth**, **ATR(14)**, **ADX(14)**, **Volumen** | Intraday-Trend + Range-Phasen zuverlässig trennen. EMA-Struktur für Trendrichtung, MACD für Momentumwechsel, ADX/BBWidth für Regime, ATR für dynamische Stops/Targets, Volumen für Breakout-/Fakeout-Qualität. |
| **Swingtrading** | **4h oder 1D** | **1D** (wenn Entry 4h) oder **1W** (wenn Entry 1D) | **1W + 1M** | 4h: **3–6 Monate** · 1D: **6–18 Monate** · 1W: **1–4 Jahre** · 1M: **3–8 Jahre** | 4h/1D für Setup/Entry, 1W/1M für Makrotrend | **EMA(20/50/200)**, **RSI(14)**, **MACD(12,26,9)**, **ATR(14)**, **ADX(14)**, **Bollinger(20,2)** (optional), **Volumen** | Trendfolge & Pullbacks im Haupttrend. EMAs/ADX definieren Trendqualität, RSI/MACD helfen bei Pullback-„Reset“ & Divergenz, ATR steuert SL/Trade-Luft, Weekly/Monthly Levels verhindern Trades gegen Makro-Zonen. |

---

## Konkrete Higher-Timeframe-Empfehlungen (Trendkontext)

### 1) Scalping – Trendkontext-Charts (Higher TF)
- **1h (2–4 Wochen)**: Lokaltrend, „saubere“ Struktur (HH/HL vs. LH/LL), intraday Key-Level.  
- **1D (3–6 Monate)**: Tagestrend + starke Zonen (PDH/PDL, Swing-High/Low).  
- **1W (1–2 Jahre, optional)**: *Nur* für „Major Levels“ (Makro-S/R, große Trendwechsel).

**Ziel:** Du scalptest nur fein – aber du willst **nicht** gegen einen klaren Tages-/Wochentrend in eine starke Zone rein scalpen.

---

### 2) Daytrading – Trendkontext-Charts (Higher TF)
- **4h (3–6 Monate)**: Primärer Trendfilter für Intraday (Trend/Range/Transition), saubere Swing-Struktur.  
- **1D (6–12 Monate)**: Starke Tageslevels, Range-Grenzen, Trendphasen-Wechsel.  
- **1W (1–3 Jahre, optional)**: Makro-Levels als „No-Go“-Zonen (z.B. direkt unter Weekly-Resistance Long jagen ist oft Mist).

**Ziel:** Intraday-Entries werden nur dann aggressiv, wenn 4h/D1 nicht dagegenstehen.

---

### 3) Swingtrading – Trendkontext-Charts (Higher TF)
- **1W (1–4 Jahre)**: Haupttrend + große Struktur (Marktzyklen, Break-of-Structure).  
- **1M (3–8 Jahre)**: Super-Makro-Levels (Zyklus-Tops, langfristige Unterstützungen).

**Ziel:** Swingtrading lebt von „Trend mit Rückenwind“. Weekly/Monthly sind die Realität, Daily ist die Ausführung.

---

## Empfohlene globale Parametrisierung (Defaults)

> Du kannst diese Defaults in deinen **globalen Settings** je Strategie ablegen.

- **EMA**:  
  - Scalping: 9 / 21  
  - Daytrading & Swing: 20 / 50 / 200  
- **RSI**: 14  
- **MACD**: 12 / 26 / 9  
- **Bollinger Bands**: 20 Perioden, 2 Std-Abw (zusätzlich: %B + Bandwidth)  
- **ATR**: 14  
- **ADX**: 14  
- **Stochastic** (nur Scalping): 14 / 3 / 3  
- **Volumen**: Roh-Volumen + (wenn vorhanden) Z-Score/RelVol (z.B. Vol / SMA(Vol,20))

---

## Minimaler Workflow (für deinen Analyse-Tab)

1. **Strategie auswählen** (Scalping/Day/Swing)  
2. **Automatisch benötigte Charts laden** (Execution + Context + Trend/Macro) gemäß Tabelle  
3. **Pro Chart** Indikator-Set des Strategietyps anwenden (globales Set)  
4. **Trendkontext bestimmen** (primär Trend/Macro TF): Trendrichtung + Key Levels  
5. **Execution TF analysieren** (Setup/Trigger)  
6. **Zusammenfassung**:  
   - Trendkontext (Higher TF)  
   - Regime (Trend/Range/High-Vol)  
   - Setup-Qualität (Setup ja/nein, Confidence, Invalidierung)  
7. **Artefakte**: im temporären Analyse-Ordner als `*.json` und `summary.md` speichern

---

## Vorschlag Dateinamen im temporären Analyse-Ordner (pro Run)

- `meta.json` (symbol, timestamps, provider, strategy, timeframes)  
- `features_<tf>.json` (komprimierte Features je TF)  
- `levels_<tf>.json` (S/R, Swingpoints, Range-Grenzen)  
- `analysis_result.json` (dein Output: setup_detected, setup_type, confidence_score, etc.)  
- `summary.md` (menschlich lesbarer Report)

---

Wenn du willst, erstelle ich dir als nächsten Schritt den **konkreten GUI-Tab-Workflow (Tab2/Tab3/Tab4)** inklusive:
- Tab-Struktur (Strategy → Timeframes → IndicatorSets → DataCollector → Summary)
- Datenmodell (Pydantic-Schemas für `StrategyConfig`, `TimeframeSpec`, `IndicatorPreset`, `RunArtifactIndex`)
- Orchestrator-Fluss (Chart-Automation, Sammeln, „Final Merge“, Übergabe an LLM)
