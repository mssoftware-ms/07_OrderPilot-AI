# OrderPilot-AI – Backtesting/Optimierung Umsetzung (Abhak-Checkliste, UI-Pflicht)

> Zweck: **konkrete Umsetzung** des Backtesting-Stacks inkl. Batch-Optimierung, Walk-Forward und UI-Verdrahtung.  
> Fokus: „Done“ nur, wenn **UI vollständig verdrahtet** + **Exports** + **Nachweise** vorhanden sind.

---

## Status-Legende
- ⬜ Offen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Blockiert/Fehler

---

## Tracking-Format (PFLICHT je Task)

```markdown
- [ ] **X.Y Task Name**
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM)
  Code: `path:line-range`
  UI: `ui_path:widget → signal/slot`
  Tests: `tests/path:test_name`
  Nachweis: Screenshot + Log-Auszug + Export-Datei
```

---

## UI-GATE (hart, vor jedem ✅)

- [ ] UI-Element existiert (Button/Toggle/Settings)
- [ ] Signal/Slot verdrahtet (klickbar, reagiert)
- [ ] Ergebnis sichtbar (Charts/Tabelle/Status + Logs)
- [ ] Persistenz korrekt (QSettings/Config)
- [ ] Export funktioniert (CSV/JSON)
- [ ] Nachweis: Screenshot + Log-Auszug

---

# Phase 1 – Datenbasis & Replay Provider

- [ ] **1.1 Datenformat festlegen (Parquet/SQLite/CSV-Import)**
- [ ] **1.2 Loader implementieren (1m OHLCV)**
  - [ ] Timezone/Index sauber (DatetimeIndex)
  - [ ] Lücken-Handling (fehlende Minuten)
  - [ ] Duplicate-Ticks entfernen
- [ ] **1.3 Replay Iterator (candle-by-candle)**
  - [ ] `next()` liefert aktuelle Candle + „history window“
  - [ ] deterministische Reihenfolge, reproduzierbar
- [ ] **1.4 Resampling Multi-Timeframe (No Leak)**
  - [ ] 1m → 5m/15m/1h/4h/1D
  - [ ] higher TF nur „closed candle“
  - [ ] Validierungs-Test: kein Future-Bar Zugriff
- [ ] **1.5 Data-Preflight zentral (Freshness/Volume/Outlier/Index)**
  - [ ] Fehlermeldungen klar + logbar (nicht silent)

---

# Phase 2 – BacktestRunner (Single Run)

- [ ] **2.1 BacktestRunConfig (Pydantic)**
  - [ ] symbol, start/end, base_tf, mtf list
  - [ ] fees/slippage settings
  - [ ] leverage settings
  - [ ] risk settings (risk%, daily limit, streak cooldown)
- [ ] **2.2 Strategy/Workflow Registry**
  - [ ] Auswahl per Name/ID (Preset)
  - [ ] Parameter Override (dict)
- [ ] **2.3 Runner Loop (Context → Signal → Exec → Monitor → Risk)**
  - [ ] deterministischer Seed/Run-ID
  - [ ] Schrittweite (1m) fest
- [ ] **2.4 Trade Lifecycle (OPEN → MANAGE → CLOSE)**
  - [ ] SL/TP/Trailing Updates pro Schritt
  - [ ] Exit-Reason codes
- [ ] **2.5 ResultStore**
  - [ ] Trades Table
  - [ ] Equity Curve
  - [ ] KPIs Basis (PF, DD, Expectancy, Trades/Tag)
- [ ] **2.6 Export Single Run**
  - [ ] `report.json`
  - [ ] `trades.csv`
  - [ ] `equity.csv`

---

# Phase 3 – ExecutionSimulator (Realismus-MVP)

- [ ] **3.1 Fees/Commission Modell**
  - [ ] pro Trade/Side
  - [ ] Maker/Taker optional
- [ ] **3.2 Slippage/Spread Modell**
  - [ ] bps-basiert ODER ATR-Anteil
  - [ ] optional abhängig von Volatilität/Volumen
- [ ] **3.3 Leverage Modell (Basis)**
  - [ ] notional, margin used
  - [ ] liquidation buffer (vereinfachtes Rule-Set)
- [ ] **3.4 Unit-Tests ExecutionSimulator**
  - [ ] Fee-Rechnung korrekt
  - [ ] Slippage korrekt angewendet
  - [ ] Leverage caps greifen

---

# Phase 4 – BatchRunner (Set-Tests)

- [ ] **4.1 ParameterSet Schema**
  - [ ] Name, params, tags
- [ ] **4.2 Grid Search Runner**
  - [ ] generiert Kombinationen
  - [ ] parallel optional (Thread/Process) – muss deterministisch bleiben
- [ ] **4.3 Random Search Runner**
  - [ ] seed fixierbar
  - [ ] param bounds validiert
- [ ] **4.4 Batch Aggregation**
  - [ ] Ranking nach Zielmetrik (z. B. Expectancy, PF, DD-penalized)
  - [ ] Top-N speichern
- [ ] **4.5 Export Batch**
  - [ ] `batch_summary.csv`
  - [ ] `top_params.json`
  - [ ] je Run `run_report.json`

---

# Phase 5 – Walk-Forward (Out-of-sample)

- [ ] **5.1 WalkForwardConfig**
  - [ ] train_window, test_window, step_size
- [ ] **5.2 Walk-Forward Runner**
  - [ ] pro Fold: optimize/train → evaluate/test
  - [ ] fold reports speichern
- [ ] **5.3 Stabilitätsmetriken**
  - [ ] Variation PF/Expectancy je Fold
  - [ ] Worst-Fold Performance
- [ ] **5.4 Export Walk-Forward**
  - [ ] `wf_summary.csv`
  - [ ] `wf_folds/…`

---

# Phase 6 – Pattern-Matching (Similarity) – optional aber sauber

- [ ] **6.1 Day/Session Fingerprint Builder**
  - [ ] returns path (bis Zeitpunkt T)
  - [ ] vol/trend/range features
  - [ ] No Leak: nur bis „now“
- [ ] **6.2 Similarity Search (Top-K)**
  - [ ] Distanzmetrik (cosine/euclid)
  - [ ] Ergebnis: ähnliche Tage + Outcome-Verteilung
- [ ] **6.3 UI Kontext-Panel**
  - [ ] Anzeige Top-K + Hinweise (kein Forecast)

---

# Phase 7 – UI Integration (Pflicht)

## 7A Backtest UI (Tab oder Window)
- [ ] **7.1 UI: Backtest Tab/Window erstellen**
- [ ] **7.2 UI: Eingaben**
  - [ ] Datenquelle wählen
  - [ ] Symbol/Zeitraum
  - [ ] Strategy Preset Dropdown
  - [ ] Param-Set Dropdown + Custom Overrides
  - [ ] Fees/Slippage/Leverage Felder
- [ ] **7.3 UI: Controls**
  - [ ] Start Single Run
  - [ ] Start Batch (Grid/Random)
  - [ ] Start Walk-Forward
  - [ ] Stop/Cancel
  - [ ] Progressbar + Status
- [ ] **7.4 UI: Output Panels**
  - [ ] Equity Curve Chart
  - [ ] KPI Cards
  - [ ] Trades Table (filter/sort)
  - [ ] Regime/Setup Breakdown Table
- [ ] **7.5 UI: Export Buttons**
  - [ ] Export Report JSON
  - [ ] Export Trades CSV
  - [ ] Export Equity CSV
  - [ ] Export Top Params (Preset speichern)

## 7B UI Wiring – Nachweis
- [ ] **7.6 Signal/Slot Verdrahtung prüfen**
  - [ ] jeder Button löst tatsächlich Run aus
  - [ ] Fehler zeigen UI-Alert + Log (kein silent fail)
- [ ] **7.7 Persistenz**
  - [ ] letzte Auswahl (Symbol/Zeitraum/Presets) wird gespeichert
- [ ] **7.8 Nachweis-Sammlung**
  - [ ] Screenshot: Setup
  - [ ] Screenshot: Result Dashboard
  - [ ] Log-Auszug: Run-ID + Exporte
  - [ ] Export-Dateien im Output-Ordner

---

# Phase 8 – Tests & QA Gates

- [ ] **8.1 Unit Tests**
  - [ ] Resample No-Leak
  - [ ] Execution Simulator (fees/slippage/leverage)
  - [ ] KPI Berechnung
- [ ] **8.2 Integration Tests**
  - [ ] Single Run End-to-End (kleiner Zeitraum)
  - [ ] Batch Run (mind. 10 Sets)
  - [ ] Walk-Forward (mind. 2 Folds)
- [ ] **8.3 UI Smoke-Test**
  - [ ] Start/Stop klickbar
  - [ ] Ergebnisse erscheinen
  - [ ] Exporte erzeugt

---

# Final DoD (hart)

- [ ] Single Backtest läuft reproduzierbar und erzeugt Exporte.
- [ ] BatchRunner testet automatisch mind. 20 Sets, Ranking + Top Params Export.
- [ ] Walk-Forward liefert out-of-sample Summary + Fold-Reports.
- [ ] UI vollständig verdrahtet (UI-Gate erfüllt) + Nachweise vorhanden.
- [ ] No-Leak Regeln für MTF + Pattern-Matching sind getestet.
- [ ] Fees + Slippage werden korrekt berücksichtigt (mindestens MVP).
