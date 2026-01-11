# Projektplan – Visible-Chart Entry Analyzer + Optimierte Indikator-Sets (SHORT=Rot, LONG=Grün)

Stand: 2026-01-11  
Ablage-Empfehlung im Projekt: `\01_Projectplan\Indikator_Engineer\`

---

## 0. Klartext (warum der letzte Versuch eine 6 war)

Das ursprüngliche Kernziel war **nicht** “einen Entry-Punkt finden”, sondern:

1) **Den aktuell sichtbaren Chartbereich vollständig analysieren** (historisch im sichtbaren Fenster, nicht nur ein Punkt).  
2) **Optimierte Indikator-Sets inkl. aller Parameter anzeigen** (regime-/marktsituationsabhängig).  
3) **Alle erkannten Entries in den Chart zeichnen** – **LONG = grüner Punkt**, **SHORT = roter Punkt** – über den gesamten sichtbaren Bereich.  
4) **Hintergrundlauf**: Live-Daten kontinuierlich auswerten und bei neu erkannten Entries **sofort einzeichnen**.  
5) **Zusatz:** Eine KI (API) soll Optimierungs- und Verbesserungsbedarf erfassen und daraus **Änderungsanweisungen/Prompts** generieren, die eine **CLI-KI** dann im Repo ausführt.

Wenn eine Umsetzung diese fünf Punkte nicht liefert, ist das Thema verfehlt.

---

## 1. Zielbild (Kernfunktion, messbar)

### 1.1 Input
- Live Feed: Tick/1s → Aufbau der aktuellen 1m-Kerze + Volumen.
- Historie: 1m-Kerzen (mind. 1 Jahr BTC vorhanden) und Aggregation zu 5m/15m/1h.
- Chart-Kontext: **sichtbarer Zeitbereich** (start_ts, end_ts), optional “aktiver Symbol/Market”.

### 1.2 Output (im Chart-Popup)
1) **Optimierte Indikator-Sets (für den aktuellen sichtbaren Bereich / aktuelles Regime)**  
   - Liste von Indikatoren (Familien) inkl. **Parametern**, ggf. pro Timeframe.
   - Zusätzlich: “Warum” (Regime/Feature-Relevanz), aber deterministisch (LLM optional nur als Text-Generator).

2) **Entry-Overlay im Chart**
   - LONG: **grüner Punkt** an den Kerzen, an denen ein Long-Entry erkannt wird.
   - SHORT: **roter Punkt** an den Kerzen, an denen ein Short-Entry erkannt wird.
   - Nicht nur “jetzt”, sondern **für den gesamten sichtbaren Chartbereich**.

3) **Live-Update**
   - Im Hintergrund wird der Feed ausgewertet.
   - Bei neuem Entry wird der Punkt **sofort** eingetragen (ohne UI-Lag).

---

## 2. Nicht-Ziele (Scope-Guard)
- Kein autonomes Live-Trading ohne Go/No-Go Kriterien.
- Kein LLM als Trade-Entscheider.
- Keine riesigen “All-indicators-everywhere” Overlays, die die UI kaputt machen.

---

## 3. Architektur (so, dass es wirklich funktioniert)

### 3.1 Projektstruktur-Regeln (verbindlich)
- Alles produktive Python liegt unter `src/`.
- Keine `.py` über **600 Zeilen** (harte Schranke, automatischer Check).
- Module in Unterordnern, klare Verantwortlichkeiten.

### 3.2 Module (MVP-fähig, erweiterbar)
Empfohlen:

- `src/ui/chart/`
  - `entry_analyzer_popup.py` (Popup UI)
  - `entry_overlay.py` (Marker Zeichnen LONG/SHORT)
  - `chart_visible_range.py` (sichtbaren Bereich abfragen/Events)

- `src/analysis/visible_chart/`
  - `visible_chart_analyzer.py` (Orchestrierung: sichtbarer Bereich → Features → Regime → Signals)
  - `analysis_jobs.py` (Job-Definitionen: FullRecompute, IncrementalUpdate)

- `src/analysis/features/`
  - `families/` (Trend, Momentum, Vol, MeanRev, Volume, Structure, Liquidity)
  - `multi_tf_join.py`
  - `leakage_guards.py`

- `src/analysis/regime/`
  - `rules.py` (MVP)
  - optional: `hmm.py`

- `src/analysis/indicator_optimization/`
  - `candidate_space.py` (Indikator-Familien + Parameter-Ranges)
  - `optimizer.py` (schnelle Suche im sichtbaren Fenster / regimebasiert)
  - `objective.py` (Trefferquote/CRV/Drawdown/Sig-Rate)

- `src/analysis/entry_signals/`
  - `scoring.py` (Signal-Scoring, LONG/SHORT)
  - `postprocess.py` (Cooldown/Clustering/No-Trade)
  - `calibration.py` (optional v1)

- `src/runtime/`
  - `background_worker.py` (Thread/Process + Queue)
  - `scheduler.py` (wann FullRecompute vs Incremental)
  - `state_cache.py` (Cache für Features/Regime/Overlay)

- `src/automation/ai_copilot/`
  - `telemetry_collector.py` (Logs/Metriken/Backtest-Summaries)
  - `prompt_generator.py` (ändert nichts am Code, erzeugt Change-Requests)
  - `change_requests/` (Ausgabe: Markdown/JSON an CLI-KI)

- `src/common/`
  - `types.py`, `logging.py`, `config.py`, `utils.py`

### 3.3 Datenfluss (entscheidend)

#### Sichtbarer Bereich → Full Recompute
1) UI liefert `visible_range = (t0, t1)`.
2) Analyzer lädt Candle-Slices (1m + Multi-TF).
3) Features berechnen / aus Cache.
4) Regime bestimmen (Rules).
5) Optimizer bestimmt **Indikator-Set + Parameter** (für diesen Bereich).
6) Signal-Scoring über **alle Kerzen** im sichtbaren Bereich.
7) Postprocess (Cooldown/Clustering) → Entry-Events.
8) UI erhält:
   - Indikator-Set (anzeigbar),
   - Entry-Events (Liste von timestamps + side),
   - optional Debug-Info.

#### Live → Incremental Update
1) Neue Tick/1s Updates bauen aktuelle 1m Kerze.
2) Bei Kerzenschluss (oder Debounce) → Features inkrementell updaten.
3) Signals für “neu hinzugekommenen Bereich” berechnen.
4) Neue Entry-Events → UI overlay append.

---

## 4. Kernmechanik: „Optimierte Indikator-Sets“ (praktikabel, schnell, deterministisch)

**Das ist Kernaufgabe #2.** „Optimiert“ bedeutet hier: Das System wählt **für den aktuell sichtbaren Chartbereich** (und das erkannte Regime) ein **Indikator-/Feature-Set inkl. Parameter**, das die **Entry-Qualität** maximiert – mit harten Nebenbedingungen (Signalrate, Kostenmodell, Drawdown).

### 4.1 Was wird konkret optimiert (Definition eines „Sets“)
Ein „Indikator-Set“ ist ein **Konfigurationsobjekt**, nicht nur eine Liste von Indikatoren:

- **Feature-/Indikator-Familien**: Trend, Momentum, Volatilität, Mean-Reversion, Volumen, Market-Structure (Swings), Liquidity/Wicks (Stop-Run-Heuristik)
- **Parameter pro Familie**: Ranges → konkreter Kandidat (z. B. RSI-Länge, Schwellen, ATR-Multiplikator, Swing-Lookback)
- **Regime-abhängige Schwellen**: z. B. andere Trigger in TREND als in RANGE
- **Scoring-Gewichte / Regel-Composer**: wie stark fließen Familien in das Entry-Scoring ein
- **Postprocessing-Regeln**: Cooldown, Clustering, Rate-Limiter, No-Trade-Zonen

**Output der Optimierung:**
1) Aktives Set (Top-1) + Alternativen (Top-3) inkl. Parameter  
2) Entry-Events über den gesamten sichtbaren Bereich (LONG grün / SHORT rot)  
3) Debug/Explain-Daten (deterministisch; LLM optional nur als Text)

### 4.2 Zielfunktion (Objective) – trifft dein Ziel „Trefferquote“ sauber
Primärziel: **Trefferquote**. Für MVP wird Trefferquote nicht über manuelle Labels erzwungen, sondern über eine **deterministische Trade-Simulation** mit deiner Exit-Logik:

- Entry: Signal-Kerze (oder nächste Kerze Open – konfigurierbar)
- Stop-Loss: Struktur (Swing ± Buffer) oder ATR-Stop (Set-Parameter)
- Exit: dein vorhandener Trailing-Stop + SL
- Optional: Max-Haltedauer (z. B. bis 8h)

Ein Signal zählt als „Treffer“, wenn es nach Kostenmodell (Fees/Slippage/Spread) **nicht zuerst in SL endet** und/oder ein Mindest-Outcome erreicht.

**Empfohlene Score-Funktion (MVP):**

- Score = w1·HitRate + w2·AvgR + w3·ProfitFactor − p1·MaxDD − p2·SignalRatePenalty − p3·CostPenalty

**Harte Gates (sonst Score = −∞):**
- Mindestanzahl Trades im Fenster (z. B. ≥ 10), sonst keine Aussagekraft
- Max Signalrate (z. B. ≤ 6/h, konfigurierbar)
- Max Drawdown im Slice (konfigurierbar)

### 4.3 Kandidatenraum (Search Space) – Regime reduziert Komplexität
Der Regime-Detektor bestimmt, **welche Template-Familien** überhaupt in Frage kommen.

Beispiele:
- **TREND**: Trendfilter (MA-Slope/Spread, ADX) + Pullback/Breakout + ATR-basierte Stops
- **RANGE/CHOP**: Mean-Reversion (BB%/Z-Score + RSI) + Strukturfilter + strikter Rate-Limiter
- **SQUEEZE**: BB-Bandwidth-Kompression + Breakout + Volumenimpuls

Parameter-Ranges (Beispiele, in `candidate_space.py`/Config):
- RSI length: 7–21; thresholds: long 25–40 / short 60–75
- BB length: 14–40; stdev: 1.5–2.8
- ATR length: 7–21; stop_mult: 1.0–3.0
- Swing lookback: 10–80; wick_ratio: 0.4–0.8
- Cooldown: 5–60 Minuten

**Wichtig:** Kein unendlicher Suchraum. Lieber klein, sinnvoll, erweiterbar.

### 4.4 Optimierungsmodus A: Fast Optimizer (UI/Visible Window) – Sekundenbereich
Ziel: Im Popup schnell ein gutes Set liefern, ohne UI zu blockieren.

Ablauf (immer Worker):
1) Features des sichtbaren Fensters **einmal** berechnen (Cache)
2) Kandidaten generieren (Regime → Templates → Parameter-Sampling)
3) Für jeden Kandidaten:
   - Signale erzeugen
   - Postprocess anwenden
   - Trades deterministisch simulieren (deine Exit-Logik)
   - Score berechnen
4) Top-K behalten (Top-1 aktiv, Top-3 anzeigen)

**Suchverfahren (MVP):**
- Random Search + Early Stopping
- Successive Halving (schlechte Kandidaten früh rauswerfen)

**Zeitbudget:** z. B. 1–3 Sekunden pro Re-Optimize. Wenn nicht fertig: bestes bisheriges Set ausliefern und weiter optimieren.

### 4.5 Optimierungsmodus B: Slow Optimizer (offline / Walk-Forward) – Robustheit statt Zufall
Ziel: Overfitting vermeiden und stabile Parameterbereiche pro Regime finden.

- Walk-Forward über viele Fenster
- pro Regime: robuste Templates/Parameterbereiche ableiten
- Ergebnis: **Priors/Defaults** (Startpunkte) für den Fast Optimizer

Ohne diese Ebene wird „optimiert“ live oft nur „zufällig gut im letzten Fenster“.

### 4.6 Re-Optimize Trigger (wann neu optimieren)
Optimierung darf nicht dauernd laufen.

Trigger (MVP):
- sichtbarer Bereich geändert (Zoom/Scroll)
- Symbol geändert
- Regime-Wechsel
- Timer (z. B. alle 15–30 min)
- Qualitätsdrift (HitRate sinkt, Signalrate steigt, False-Breakouts häufen sich)

### 4.7 Overfitting-Schutz (Pflicht)
- Mindestanzahl Trades (Gate)
- Komplexitätsstrafe (zu viele aktive Familien → Penalty)
- Stabilitätscheck: Set muss in Sub-Slices innerhalb des Fensters brauchbar sein
- Top-K + Fallback: wenn Top-1 fragil, fallback auf robustes Default-Set je Regime
- Purged/Embargo beim Offline-Optimieren (Leakage-Schutz)



## 5. Kernmechanik: „Punkte im Chart zeichnen“ (gesamter sichtbarer Chart)

### 5.1 Entry-Event Format
- `EntryEvent(ts, side, confidence, reason_tags)`
  - side ∈ {LONG, SHORT}
  - **LONG = Grün**, **SHORT = Rot**

### 5.2 Overlay-Rendering
- Renderer erhält Liste von Events (ts) + optional Preis/Index.
- Renderer zeichnet Punkte auf Candle-Index oder Zeit.
- Renderer muss:
  - Repaint effizient (diff statt full redraw),
  - Marker-Layer getrennt von Indicators,
  - “Clear & Recompute” bei sichtbarem Bereich Wechsel.

---

## 6. Hintergrundlauf (Live-Analyse, ohne UI-Lag)

### 6.1 Scheduling-Regeln (MVP)
- Inkrementelle Analyse bei:
  - Kerzenschluss 1m (Standard),
  - optional: alle X Sekunden für “Early Warning” (aber nur low-cost).
- Full Recompute bei:
  - sichtbarer Bereich geändert,
  - Symbol geändert,
  - Regime-Wechsel (oder spätestens alle N Minuten).

### 6.2 Threading/Async
- Worker-Thread (Qt: QThread oder Python Thread + Signal) oder Process.
- Kommunikation via Queue + Qt-Signals.
- UI bekommt nur fertige Ergebnisse.

---

## 7. KI-Anbindung: „Optimierungen erfassen → Änderungsanweisungen für CLI-KI schreiben“

### 7.1 Was diese KI NICHT macht
- Sie editiert **keinen** Code direkt.
- Sie triggert **keine** Trades.

### 7.2 Was sie macht (konkret)
- Sie sammelt Telemetrie:
  - Regime-Verteilung,
  - Signalrate,
  - Trefferquote (Paper/Backtest),
  - typische Failure-Muster (z. B. Chop-Spam, false breakouts),
  - Performance pro Indikator-Set.
- Sie erzeugt daraus **Change-Requests**:
  - `change_requests/YYYYMMDD_HHMM_<topic>.md`
  - plus optional JSON “execution hints”.

### 7.3 Inhalt eines Change-Request (MVP-Standard)
- Problemstatement + Nachweis (Log/Metric).
- Vermutete Ursache.
- Konkrete Änderungsvorschläge:
  - welche Module,
  - welche Funktionen,
  - Parameteränderungen,
  - Tests, die grün sein müssen.
- Entscheidungspunkte (Decision Gates), falls nötig.
- “Runbook” fürs CLI-Tool (Kommandos).

### 7.4 CLI-KI Workflow (operativ)
- Du gibst Change-Request an CLI-KI.
- CLI-KI arbeitet im Branch, führt `ruff/pytest` aus, schreibt Report.
- Du entscheidest Merge/Reject.

---

## 8. Umsetzungsphasen (neu, kernfunktionszentriert)

### Phase 0 – Reset & Schutzgitter (1–2 Tage)
- Alte Fehl-Implementierung isolieren:
  - Feature-Flag “entry_analyzer_v2” oder Branch-Rollback.
- Projektstruktur: alles unter `src/`, Line-Limit Gate aktiv.
- Logging/Config standardisieren.

**Abnahme:** App startet, keine Regression, Gate aktiv, keine `.py` > 600.

### Phase 1 – Visible-Chart Analyzer MVP (2–4 Tage)
- UI: Popup in Chartansicht + „Analyze Visible Range“ Button.
- Visible Range API: t0/t1 aus Chart ermitteln.
- Full Recompute Pipeline:
  - Candles slice,
  - Features MVP,
  - Regime Rules,
  - Entry scoring (einfach),
  - Overlay zeichnen für gesamten sichtbaren Bereich.

**Abnahme:** Beim Öffnen des Popups wird der komplette sichtbare Bereich analysiert und LONG/SHORT Punkte werden eingezeichnet.

### Phase 2 – Optimierte Indikator-Sets MVP (3–6 Tage)
- Kandidatenraum definieren (klein, sinnvoll).
- Optimizer implementieren (fast search) im sichtbaren Slice.
- Anzeige im Popup: aktives Set + Parameter.
- Optional: Indikator-Rendering anstoßen (wenn Chart das unterstützt).

**Abnahme:** Popup zeigt „Optimiertes Indikator-Set“ inkl. Parameter; Set passt sich bei Regime/Range-Wechsel sichtbar an.

### Phase 3 – Live Background Runner (3–6 Tage)
- Worker + Scheduler + Cache.
- Inkrementelle Updates bei Kerzenschluss.
- Neue Entry-Events werden live als Punkte ergänzt.
- Debounce + Performance-Messung (UI bleibt flüssig).

**Abnahme:** Live-Daten laufen, bei erkannten Entries werden sofort LONG/SHORT Punkte eingetragen – ohne UI-Lag.

### Phase 4 – Validierung & Qualitäts-Gates (parallel, 2–5 Tage)
- Walk-Forward (mind. MVP-Variante) für Signal-Qualität.
- Leakage Guards, Kostenmodell.
- Signalrate-Limiter + No-Trade-Zonen.

**Abnahme:** Reproduzierbarer Report, definierte Mindestkriterien (Paper-Go) möglich.

### Phase 5 – KI-Copilot für Change-Requests (2–4 Tage)
- Telemetrie-Sammlung + Reporting.
- Prompt/Anweisungs-Generator (für CLI-KI).
- UI: “Generate Change Request” Button im Popup.

**Abnahme:** System erzeugt automatisch Change-Request Dateien, die eine CLI-KI ausführen kann.

---

## 9. Definition of Done (global)
- Sichtbarer Bereich wird vollständig analysiert (nicht nur „ein Punkt“).
- Optimierte Indikator-Sets mit Parametern werden angezeigt.
- LONG (grün) / SHORT (rot) Punkte werden über den sichtbaren Chart eingezeichnet.
- Live-Hintergrundlauf ergänzt neue Punkte in Echtzeit.
- KI-Copilot erzeugt Change-Requests/Prompts für CLI-KI.
- Keine `.py` > 600 Zeilen, alles unter `src/`, Tests/Format/Lint grün.

---

## 10. Decision Gates (nur dann darf gefragt werden)
- DG-1 Objective Details (N, X·ATR, SL, Invalidation) – falls ML-Labeling/Training aktiviert wird.
- DG-2 Go-Live Kriterien.
- DG-3 Kostenmodell, falls unklar.
- DG-4 Modell-Komplexität (HMM/Sequence) – nur nach MVP-Stabilität.
