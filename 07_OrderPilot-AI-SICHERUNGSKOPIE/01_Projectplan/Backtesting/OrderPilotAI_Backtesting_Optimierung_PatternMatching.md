# OrderPilot-AI – Backtesting, Optimierung & Pattern-Matching (Konzept + Checkliste)

> Fokus: Historische Tests für Strategien/Workflows/Indikator-Sets auf Basis deiner **1-Minuten-Daten (1 Jahr)**.  
> Gilt **ab jetzt** (aktueller Integrationsstand muss nicht erneut dokumentiert werden).

---

## Ziele (kurz, Vibe-Coding-tauglich)

- [ ] **Replay/Backtest**: Strategien/Workflows auf historischen Daten reproduzierbar testen (Candle-by-Candle).
- [ ] **Multi-Timeframe**: 1m → resample zu 5m/15m/1h/4h/1D ohne Data-Leak.
- [ ] **Realistische Execution**: Gebühren, Slippage/Spread, (optional) Funding, Leverage-Rules.
- [ ] **Batch-Tests**: Automatisch verschiedene Parameter-/Indikator-Sets testen (Grid/Random/Opt).
- [ ] **Walk-Forward**: Train/Test Rolling Windows zur Overfitting-Vermeidung.
- [ ] **Pattern-Matching**: „Heute bis jetzt“ vs. ähnliche historische Tage zur Kontext-Einschätzung.
- [ ] **UI Pflicht**: Alles ist über UI startbar + Ergebnisse sichtbar + exportierbar (kein „nur Code“).

---

## Architektur-Blueprint (Minimal aber richtig)

### 1) ReplayMarketDataProvider (historische Daten als „Live“-Stream)
- Input: 1m OHLCV (CSV/Parquet/DB)
- Output:
  - candle-by-candle Feed (simuliert Live)
  - resampled Bars (z. B. 5m/15m/1h/4h/1D)
- Regeln:
  - **No Leak**: Higher-TF Candle ist nur verfügbar, wenn sie „geschlossen“ ist (letzte 1m Candle der Periode durch).

### 2) BacktestRunner (Strategy Runner)
Je Simulations-Schritt (z. B. je 1m Candle):
1. MarketContext/Features/Regime/Levels berechnen (deterministisch)
2. Entry-/Exit-Engine laufen lassen (Score/Confluence/Gates)
3. ExecutionSimulator füllt Orders (Fees/Slippage)
4. PositionMonitor (SL/TP/Trailing) aktualisieren
5. RiskManager Limits prüfen (Daily Loss, Loss Streak, Max Trades/Tag)

### 3) ExecutionSimulator (realistisch, aber incremental)
**MVP (Pflicht):**
- Fees/Commission
- Spread + Slippage (bps oder ATR-Anteil)
- Basic Leverage (Margin Use, Liquidation Buffer – vereinfachtes Modell)

**Optional (später):**
- Funding (Futures)
- Partial fills
- Latency/Order-Delay

### 4) ResultStore + Reporting
- Equity Curve / PnL
- Trades Liste (Entry/Exit, R, Reason Codes)
- Breakdown pro Regime / Setup-Typ / Timeframe
- Exporte: CSV/JSON + „Best Params“ Preset speichern

---

## Batch-Testing: Parameter & Set-Sweeps

### Sweep-Methoden (empfohlen in Reihenfolge)
- **Grid Search**: klein & kontrolliert
- **Random Search**: besser bei vielen Parametern
- **Bayesian/Optuna**: effizient bei großem Suchraum (optional)

### Beispiel-Parameter (typisch)
- Entry: Score-Threshold, Weights, Confluence min(3/5 vs 4/5)
- Regime-Gates: ADX Threshold (z. B. 18/20/22), Trend/Range Rules
- Risk: Risk% pro Trade, SL/TP (ATR-Mults), Trailing Activation, Max Trades/Tag
- Leverage: Max-Leverage pro Asset/Volatilität, Liquidation Buffer

---

## Walk-Forward (Pflicht gegen Overfitting)

**Standard-Setup (Beispiel):**
- Train: 3 Monate (Optimierung)
- Test: 1 Monat (Evaluation)
- Rolling (z. B. 12 Iterationen)

**Ziel:**
- Parameter wählen, die **out-of-sample** stabil bleiben.

---

## Metriken (die wirklich zählen)

Pflicht:
- Profit Factor
- Expectancy (Ø R pro Trade)
- Max Drawdown + Recovery Time
- Trade Count / Trades pro Tag
- Regime-Breakdown (Trend vs Range)
- Tail Risk: Worst N Trades / Longest Loss Streak

Optional:
- Sharpe/Sortino
- Exposure (Time-in-market)

---

## Pattern-Matching: „heutiger Tageschart“ vs. historische Tage

### A) Day-Fingerprint (deterministisch)
Pro Tag/Session Feature-Vektor:
- Return-Pfad (z. B. 5m returns Sequenz bis Zeitpunkt T)
- Volatilität (ATR%, BB Width)
- Trend (ADX, EMA-Distanz)
- Range-Struktur (High/Low, Breakouts, Sweeps)
- Volumenprofil (falls zuverlässig)

### B) Similarity Search
- KNN/Nearest Neighbors auf Fingerprints
- „Heute bis jetzt“ nur mit „historisch bis gleicher Uhrzeit“ vergleichen (**No Leak**)
- Output:
  - Top-K ähnliche Tage
  - typische Fortsetzung/Verteilung (nicht als Prognose, sondern Kontext-Prior)

**Use Case:**
- dynamische Preset-Wahl: Range-Preset vs Trend-Preset
- Filter gegen Chop/Whipsaw

---

## UI-Pflichtumfang (damit nichts „unverdrahtet“ bleibt)

### Backtest UI – Mussfelder
- [ ] Datenquelle (Pfad/DB), Symbol, Zeitraum (Start/End)
- [ ] Strategy/Workflow Preset Auswahl
- [ ] Parameter-Set Auswahl (Preset/Custom)
- [ ] Modus: Single Run / Batch Run (Grid/Random)
- [ ] Start/Stop + Progress
- [ ] Ergebnis: Equity Curve, Kennzahlen, Trades Tabelle, Breakdown
- [ ] Export: CSV/JSON Report + „Best Params“ speichern

### UI-Gate (hart)
- [ ] UI-Element existiert (Button/Toggle/Settings)
- [ ] Signal/Slot verdrahtet (klickbar, reagiert)
- [ ] Ergebnis sichtbar (Charts/Tabelle/Status + Logs)
- [ ] Persistenz korrekt (QSettings/Config)
- [ ] Nachweis: Screenshot + Log-Auszug

---

## Umsetzungs-Checkliste (ab jetzt)

### Phase A – Replay + Single Backtest (MVP)
- [ ] A1 ReplayMarketDataProvider: 1m Loader + iterator (candle-by-candle)
- [ ] A2 Resampling MTF (5m/15m/1h/4h/1D) ohne Leak
- [ ] A3 BacktestRunner: Loop + Hooks (context → signal → exec → monitor → risk)
- [ ] A4 ExecutionSimulator MVP: fees + slippage/spread + basic leverage
- [ ] A5 Reporting MVP: equity + trades + KPIs + export

### Phase B – Batch Runner + Walk-Forward
- [ ] B1 BatchRunner: Grid/Random Sets
- [ ] B2 Walk-Forward Runner (rolling windows)
- [ ] B3 Best-Params Auswahl + Preset-Export (in Settings nutzbar)

### Phase C – Pattern-Matching (Similarity)
- [ ] C1 Fingerprint Builder (Day/Session)
- [ ] C2 Similarity Search (Top-K) + „Today so far“ Vergleich
- [ ] C3 Integration: Preset Vorschlag + Kontext-Panel in UI

### Phase D – UI-Integration (Pflicht vor Done)
- [ ] D1 Backtest Tab/Window + Controls
- [ ] D2 Ergebnis-Dashboard (Equity, KPIs, Trades)
- [ ] D3 Export-Buttons + Ablagepfad
- [ ] D4 Logs/Audit Trail sichtbar (Signal-IDs, Context-Hash, Errors)

---

## Definition of Done (DoD)

- [ ] Single Backtest (1 Symbol, frei wählbarer Zeitraum) läuft reproduzierbar durch.
- [ ] Batch-Tests laufen mit mind. 20 Param-Sets automatisch.
- [ ] Walk-Forward liefert out-of-sample Metriken.
- [ ] Ergebnisse sind in der UI sichtbar und exportierbar.
- [ ] UI-Gate ist für alle Backtest-Funktionen erfüllt.
- [ ] No-Leak Checks sind umgesetzt (MTF, Pattern-Matching).
- [ ] ExecutionSimulator berücksichtigt Fees + Slippage; Leverage-Regeln greifen (Basis).

---

## Hinweise (praktisch)

- Starte mit **Parquet** (schnell) oder SQLite (okay), CSV nur für Import.
- Resampling: „closed candles only“, sonst sind MTF-Ergebnisse wertlos.
- Overfitting: Ohne Walk-Forward ist jede Optimierung gefährlich.
