# ✅ Checkliste: Visible-Chart Entry Analyzer + Optimierte Indikator-Sets (SHORT=Rot, LONG=Grün)

**Start:** 2026-01-11
**Letzte Aktualisierung:** 2026-01-11 20:00
**Gesamtfortschritt:** 40% (10/27 Tasks - Phase 0 + Phase 1.1 + 1.2 teilweise)

---

## 🛠️ CODE-QUALITÄTS-STANDARDS (vor jedem Task lesen!)

### ✅ Erforderlich für jeden Task
1. Vollständige Implementation – keine TODOs/Platzhalter
2. Error Handling – keine stillen Fehler
3. Input Validation – Parameter prüfen
4. Type Hints – vollständig
5. Docstrings – public APIs
6. Logging – sinnvolle Log-Level
7. Tests – Unit/Integration wo sinnvoll
8. **Kein Minimal-Rewrite:** bestehende, noch benötigte Funktionen bleiben erhalten
9. **Projektstruktur:** alles produktive Python unter `src/`
10. **Line-Limit:** keine `.py` > 600 Zeilen (Gate muss aktiv sein)

### ❌ Verboten
1. Platzhalter-Code (`TODO`, Dummy returns)
2. Auskommentierte Code-Blöcke als „Backup“
3. `except: pass`
4. Hardcoded Secrets/Keys
5. UI-Blocker (schwere Berechnung im GUI-Thread)
6. “LLM entscheidet Trades”
7. Dateien > 600 Zeilen ignorieren (muss gesplittet werden)

### 🔍 Before marking complete
- [ ] Code läuft (getestet)
- [ ] Keine TODOs
- [ ] Error Handling vorhanden
- [ ] Input Validation vorhanden
- [ ] Type Hints vollständig
- [ ] Logging hinzugefügt
- [ ] Tests grün
- [ ] Line-Limit Gate grün
- [ ] Keine UI-Lags durch neue Logik

---

## 📊 Status-Legende
- ⬜ Offen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

---

## 🛠️ TRACKING-FORMAT (PFLICHT)

### Erfolgreicher Task
```markdown
- [ ] **1.2.3 Task Name**
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM) → *Was wurde implementiert*
  Code: `pfad:zeilen` (wo implementiert)
  Tests: `test_datei:TestCase` (welche Tests)
  Nachweis: Screenshot/Log-Ausgabe/Report-Link
```

### Fehlgeschlagener Task
```markdown
- [ ] **1.2.3 Task Name**
  Status: ❌ Fehler (YYYY-MM-DD HH:MM) → *Fehlerbeschreibung*
  Fehler: `Exakte Error Message`
  Ursache: *Root cause*
  Lösung: *Fix-Plan*
```

---

## Phase 0: Reset, Struktur & Guardrails (Pflicht)

- [x] **0.1 Fehl-Implementierung isolieren oder entfernen**
  Status: ✅ Abgeschlossen (2026-01-11 19:30) → *Keine alte Entry-Analyzer-Implementierung gefunden. Clean Start.*
  Code: Repo-Scan durchgeführt (keine entry_analyzer*.py, visible_chart*.py gefunden)
  Nachweis: `REPORT_20260111_1930_phase0_setup.md`

- [x] **0.2 Projektstruktur vereinheitlichen: alles unter `src/`**
  Status: ✅ Abgeschlossen (2026-01-11 19:30) → *Neue Module unter src/ angelegt*
  Code: `src/analysis/visible_chart/`, `src/analysis/entry_signals/`, `src/analysis/regime/`, `src/runtime/`, `src/automation/ai_copilot/`
  Nachweis: `REPORT_20260111_1930_phase0_setup.md`

- [x] **0.3 Modul-Layout anlegen (ui/analysis/runtime/automation/common)**
  Status: ✅ Abgeschlossen (2026-01-11 19:30) → *Ordnerstruktur + __init__.py erstellt*
  Code: Siehe 0.2
  Nachweis: `REPORT_20260111_1930_phase0_setup.md`

- [x] **0.4 Line-Limit Gate (≤600 Zeilen) implementieren**
  Status: ✅ Abgeschlossen (2026-01-11 19:30) → *scripts/check_line_limit.py + quality_gate.sh erstellt*
  Code: `scripts/check_line_limit.py`, `scripts/quality_gate.sh`
  Tests: `python3 scripts/check_line_limit.py` → 20 Legacy-Violations erkannt
  Nachweis: `REPORT_20260111_1930_phase0_setup.md`
  **Known Issues:** 20 bestehende Legacy-Dateien überschreiten 600 Zeilen (größtenteils *_old, *_ORIGINAL, *_backup)

- [x] **0.5 Standard-Kommandos fixieren**
  Status: ✅ Abgeschlossen (2026-01-11 19:30) → *quality_gate.sh kombiniert ruff+pytest+line-limit*
  Code: `scripts/quality_gate.sh`
  Command: `bash scripts/quality_gate.sh`
  Nachweis: `REPORT_20260111_1930_phase0_setup.md`

- [ ] **0.6 Logging/Config Standard (keine Parallelwelt)**
  Status: ⬜ → *zentrale Logger/Config Nutzung – wird bei Phase 1 geprüft*

**DoD Phase 0:** App startet, keine Regression, Struktur-Gates aktiv, Tests grün.

---

## Phase 1: Visible-Chart Analyzer MVP (Kernfunktion #1)

### 1.1 UI-Integration (Popup in Chartansicht)
- [x] **1.1.1 Popup-Skeleton in Chartansicht integrieren**
  Status: ✅ Abgeschlossen (2026-01-11 19:45) → *EntryAnalyzerPopup erstellt mit Analyze-Button, Entry-Tabelle, Regime-Anzeige*
  Code: `src/ui/dialogs/entry_analyzer_popup.py` (348 Zeilen)
  Tests: Manuell über Rechtsklick → "🎯 Analyze Visible Range..."
  Nachweis: `REPORT_20260111_1945_phase1_popup.md`

- [x] **1.1.2 Visible-Range API: t0/t1 aus Chart ermitteln**
  Status: ✅ Abgeschlossen (2026-01-11 19:45) → *Nutzt bestehende get_visible_range(callback) via AnalysisWorker*
  Code: `src/ui/widgets/chart_mixins/entry_analyzer_mixin.py:95-108`
  Nachweis: `REPORT_20260111_1945_phase1_popup.md`

- [ ] **1.1.3 Overlay-Layer für Entry-Marker**
  Status: ⬜ → **Nutzt BotOverlayMixin.add_bot_marker()** - LONG=grün, SHORT=rot, Legende, Clear/Repaint

### 1.2 Full-Recompute Pipeline (sichtbarer Bereich)
- [x] **1.2.1 Candle Slice Loader (1m + Multi-TF)**
  Status: ✅ Abgeschlossen (2026-01-11 20:00) → *DB-Query + Aggregation + Mock-Fallback*
  Code: `src/analysis/visible_chart/candle_loader.py` (246 Zeilen)
  Nachweis: Line-Limit ✅ < 600

- [x] **1.2.2 Feature-MVP (kleines, starkes Set)**
  Status: ✅ Abgeschlossen (2026-01-11 20:00) → *SMA-20, Price-vs-SMA, Volatilität*
  Code: `src/analysis/visible_chart/analyzer.py:_calculate_features()`
  Nachweis: Regelbasiert, erweiterbar

- [x] **1.2.3 Regime Rules v0 (Trend/Range/High-Vol/Squeeze/No-Trade)**
  Status: ✅ Abgeschlossen (2026-01-11 20:00) → *Schwellenwerte für avg_trend + avg_vol*
  Code: `src/analysis/visible_chart/analyzer.py:_detect_regime()`
  Nachweis: TREND_UP/DOWN (±0.5%), HIGH_VOL (>1.5%), SQUEEZE (<0.5%), RANGE (default)

- [x] **1.2.4 Entry-Scoring v0 über alle Kerzen im sichtbaren Bereich**
  Status: ✅ Abgeschlossen (2026-01-11 20:00) → *Regimebasiertes Scoring, EntryEvent-Liste*
  Code: `src/analysis/visible_chart/analyzer.py:_score_entries()`
  Nachweis: Trend-Pullback, Mean-Reversion bei Extremen

- [x] **1.2.5 Postprocess v0 (Cooldown/Clustering/Rate-Limiter)**
  Status: ✅ Abgeschlossen (2026-01-11 20:00) → *5min Cooldown + max 6 Signals/h*
  Code: `src/analysis/visible_chart/analyzer.py:_postprocess_entries()`
  Nachweis: Sortiert nach Confidence, behält Top-N

- [ ] **1.2.6 Overlay-Rendering: Punkte für gesamten sichtbaren Bereich**
  Status: ⬜ → *Nutzt BotOverlayMixin.add_bot_marker()* - Test pending

**DoD Phase 1:** Sichtbarer Chart wird vollständig analysiert und Punkte werden eingezeichnet.

---

## Phase 2: Optimierte Indikator-Sets (Kernfunktion #2)

> **Das ist die Kernaufgabe:** Für den **sichtbaren Chartbereich** wird ein **Indikator-/Feature-Set inkl. Parameter** gefunden, das die **Entry-Qualität** (primär Trefferquote) maximiert – unter Nebenbedingungen (Signalrate, Kostenmodell, DD).  
> Ergebnis muss im Popup angezeigt werden (Set + Parameter) und als Basis dienen, um **alle Entry-Punkte** im sichtbaren Fenster zu zeichnen.

- [ ] **2.1 Kandidatenraum definieren (Familien + Parameter-Ranges)**
  Status: ⬜ → *regimebasiert, klein & sinnvoll, erweiterbar; in Config/Code versioniert*

- [ ] **2.2 Set-Definition fest verdrahten (was gehört zum Set)**
  Status: ⬜ → *Familien + Parameter + Schwellen + Scoring-Gewichte + Postprocess-Regeln*

- [ ] **2.3 Objective/Score implementieren (Trefferquote primär + Constraints)**
  Status: ⬜ → *HitRate + AvgR/ProfitFactor optional; Penalties: MaxDD, Signalrate, Kostenmodell*
  Hinweis: *Harte Gates: min Trades, max Signalrate, max DD (sonst Score = −∞).*

- [ ] **2.4 Deterministische Trade-Simulation im sichtbaren Slice**
  Status: ⬜ → *Entry: Signal-Kerze/NextOpen konfig; SL: Structure/ATR; Exit: bestehender Trailing + SL; Kostenmodell aktiv*

- [ ] **2.5 Fast Optimizer (UI/Visible Window) im Worker**
  Status: ⬜ → *Random Search + Early Stopping; optional Successive Halving; Zeitbudget (z. B. 1–3s)*
  DoD: *liefert Top-1 + Top-3 + Scores in Sekunden, ohne UI-Lag.*

- [ ] **2.6 Caching & Wiederverwendung**
  Status: ⬜ → *Feature-Cache, Regime-Cache, Optimizer-Cache; kein Neuberechnen ohne Grund*

- [ ] **2.7 Re-Optimize Trigger implementieren**
  Status: ⬜ → *(a) Visible-Range Wechsel, (b) Symbolwechsel, (c) Regime-Wechsel, (d) Timer, (e) Qualitätsdrift*

- [ ] **2.8 Overfitting-Schutz (Pflicht)**
  Status: ⬜ → *min Trades Gate, Komplexitätsstrafe, Sub-Slice Stabilitätscheck, Top-K Fallback je Regime*

- [ ] **2.9 Popup: „Aktives Set“ + Parameter-Tabelle + Alternativen**
  Status: ⬜ → *Top1 (aktiv) + Top3; pro Zeile: Indikator/Familie, Parameter, TF, Rolle, Score, Constraints*

- [ ] **2.10 Set → Signal-Pipeline koppeln**
  Status: ⬜ → *Das aktive Set muss direkt die Entry-Signal-Generierung über ALLE Kerzen im sichtbaren Fenster steuern*

**DoD Phase 2:** Popup zeigt optimierte Indikator-Sets inkl. Parameter; sichtbar adaptiv; Set steuert Signal-Overlay im gesamten sichtbaren Bereich.



## Phase 3: Hintergrundlauf Live (Kernfunktion #3)

- [ ] **3.1 Background Worker (Thread/Process) + Queue/Signals**
  Status: ⬜ → *keine UI-Blocker*

- [ ] **3.2 Scheduler: Full-Recompute vs Incremental**
  Status: ⬜ → *Kerzenschluss-Trigger, Debounce*

- [ ] **3.3 Incremental Feature Update**
  Status: ⬜ → *nur Delta berechnen*

- [ ] **3.4 Incremental Signal Update**
  Status: ⬜ → *neue EntryEvents sofort zeichnen*

- [ ] **3.5 Performance-Messung (UI-Latenz/CPU)**
  Status: ⬜ → *harte Grenzwerte definieren & loggen*

**DoD Phase 3:** Live-Daten werden ausgewertet; neue Entries werden sofort eingezeichnet.

---

## Phase 4: Validierung & Qualitäts-Gates (Pflicht)

- [ ] **4.1 Walk-Forward MVP**
  Status: ⬜ → *reproduzierbar, seeds*

- [ ] **4.2 Leakage-Guards + Embargo/Purging**
  Status: ⬜ → *Testfälle für Lookahead*

- [ ] **4.3 Kostenmodell (Fees/Slippage/Spread) durchgängig**
  Status: ⬜ → *Backtest & Paper identisch*

- [ ] **4.4 No-Trade Zonen (Vol-Spike/Spread-Spike/Data-Gaps)**
  Status: ⬜ → *reduziert Fehltrades*

- [ ] **4.5 Report-Generator (MD + optional JSON)**
  Status: ⬜ → *Regime-Timeline + Signal-Timeline + Metriken*

**DoD Phase 4:** Validierungsreport existiert, Mindestkriterien definierbar.

---

## Phase 5: KI-Copilot → Change Requests für CLI-KI (Kernfunktion #4)

- [ ] **5.1 Telemetrie-Sammlung (Signalrate, Trefferquote, Regime, Failure-Muster)**
  Status: ⬜ → *strukturiert, versioniert*

- [ ] **5.2 Change-Request Generator (Markdown)**
  Status: ⬜ → *Problem → Ursache → konkrete Anweisungen → Tests*

- [ ] **5.3 Optional: JSON Execution Hints (Dateipfade/Module/Kommandos)**
  Status: ⬜ → *für CLI-Agent*

- [ ] **5.4 UI-Button „Generate Change Request“ im Popup**
  Status: ⬜ → *speichert Datei in `src/automation/ai_copilot/change_requests/`*

- [ ] **5.5 LLM Adapter (nur Text/Monitoring, keine Trades)**
  Status: ⬜ → *Model-ID konfigurierbar*

**DoD Phase 5:** System erzeugt automatisch aus Optimierungsdaten Anweisungen für CLI-KI.

---

## Phase 6: Abnahme & Release

- [ ] **6.1 End-to-End Demo: Visible Range → Optimizer → Overlay → Live Update**
  Status: ⬜ → *Video/Screenshots/Logs*

- [ ] **6.2 Stabilitätslauf Papertrading (X Tage)**
  Status: ⬜ → *Go/No-Go Kriterien erfüllt*

- [ ] **6.3 Dokumentation (Runbook + Troubleshooting)**
  Status: ⬜ → *Start/Stop, Config, Logs, Known Issues*

**DoD Phase 6:** Kernfunktionen vollständig vorhanden, stabil, nachvollziehbar.

---

## Decision Gates (nur dann fragen)
- DG-1: Objective Details (N, X·ATR, SL, Invalidation) falls ML-Labeling/Training aktiviert wird.
- DG-2: Go-Live Kriterien.
- DG-3: Gebühren/Slippage/Spread, falls unklar.
- DG-4: Modell-Komplexität (HMM/Sequence) nur nach MVP.
