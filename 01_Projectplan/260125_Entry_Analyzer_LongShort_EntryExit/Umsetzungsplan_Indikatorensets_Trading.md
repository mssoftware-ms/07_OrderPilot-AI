# Umsetzungsplan – Entry Analyzer Tabs 4–6 (Indikatorensets & Trading)

Stand: 2026-01-25  
Scope: Neuschreibung der Tabs 4–6 im Entry Analyzer (Indicator Setup, Indicator Optimization, Indicator Result) inklusive Risikomanagement-Integration und Backtesting nach Vorgaben aus `Projektziel.md` und `Indikatorensets`.

---

## 1) Kontext & Zielbild
- Ziel: Die drei Indicator-Tabs sollen analog zum Regime-Flow funktionieren, aber für Long/Short Entry/Exit-Indikatorensets inkl. Risiko-/P&L-Berechnung. Alte Implementierungen in Tabs 4–6 werden vollständig ersetzt (kein Backup).
- Datenquelle: JSON V2 Datei mit Indikatorliste (ohne Parameter-Ranges) wird in Tab 4 geladen. Parameter-Ranges werden dort neu erfasst (bis zu 10 Parameter je Indikator, Min/Max/Step).
- Optimierung: Tab 5 führt Variantentests über definierte Schleifen (Feld für Laufanzahl nötig). Ergebnisse für Entry Long, Entry Short, Exit Long, Exit Short.
- Ergebnisse/Backtest: Tab 6 zeigt beste Parameter-Sets; zusätzlich Risk-Management-Logik (ATR-basiertes Sizing, Multi-TP, Trailing SL) aus `Indikatorensets` und P&L-Backtesting, optional eigenes Tab falls UI-Layout es erfordert.
- Defaults: Alle Signal-Typen sind vorgewählt (Entry/Exit Long/Short), Regime-Selection-Goupbox entfällt in Tab 4, Groupbox „Regime Selection” wird entfernt, „Signal Types to Optimize” vorgecheckt.

## 2) Annahmen & Randbedingungen
- Trading-Sicherheit: Standard = Paper-Trading, keine Live-Endpoints. Klare Trennung Live/Paper in Config beibehalten.
- JSON-Governance: Schema-First, `schema_version` Pflicht, Validierung über vorhandenen `SchemaValidator` falls verfügbar (Datei `docs/JSON_INTERFACE_RULES.md` nicht gefunden – vor Umsetzung klären/ergänzen).
- Architektur: Schichtenmodell aus `ARCHITECTURE.md` wahren; EntryAnalyzer bleibt UI-Layer, Optimierungs-/Backtest-Logik als Services/Worker ohne direkte Broker-Calls.
- Performance: Optimization runs können groß werden; Worker muss stoppbar bleiben und UI darf Event-Loop nicht blockieren.
- Persistenz: JSON-Dateien in `03_JSON/Entry_Analyzer/...` wie bisher, keine echten Keys/Secrets speichern.

## 3) Betroffene Komponenten (Ist-Map)
- UI: `src/ui/dialogs/entry_analyzer/entry_analyzer_popup.py` + Mixins `indicator_setup_v2_mixin`, `indicator_optimization_v2_mixin`, `indicator_results_v2_mixin`.
- Worker: `entry_analyzer_indicator_worker.py` (derzeit Platzhalter-Logik, Random-Scores).
- Datenpfade: `03_JSON/Entry_Analyzer/Regime/STUFE_1_Regime/optimized_regime_*`, `.../STUFE_2_Indicators/` (Export-Ziel).
- Anforderungen: `01_Projectplan/260125_Entry_Analyzer_LongShort_EntryExit/Projektziel.md`, Fachlogik: `.../Indikatorensets`.

## 4) Zielbild pro Tab / Feature
- Tab 4 Indicator Setup
  - Entfernt: Regime Selection Group, alte „Select Indicators to Test“ UI.
  - Neu: Tabelle „Indicator Parameter Optimization Ranges“ (10 Parameter-Spalten: Name, Min, Max, Step), dynamisch basierend auf Indikatoren aus geladener JSON-Liste.
  - Signal Types Group: vier Checkboxen (Entry/Exit Long/Short) standardmäßig **checked**.
  - JSON-Import: nimmt reine Indikatorliste; validiert Schema; füllt Tabellenzeilen; ermöglicht manuelle Range-Anpassung + Defaults aus `Indikatorensets` (Supertrend/EMA/RSI/ATR/...).
- Tab 5 Indicator Optimization
  - Neues Eingabefeld „Optimization Loops“ (int) neben Start-Button.
  - Start/Stop nutzt Worker; Parameter-Sets werden aus Tab 4 generiert.
  - Scoring ersetzt Platzhalter: nutzt Backtest-Routine (Win-Rate, Profit Factor, Sharpe, Trades, P&L, Max DD).
  - Fortschrittsanzeigen pro Signal-Typ bleiben; Ergebnisse > Score 50 werden für Tab 6 persistiert.
- Tab 6 Indicator Results (+ evtl. neues Tab „Risk & Backtest“)
  - Tabellen pro Signal-Typ mit Top-N Filter (beste Parameter-Sets).
  - Export als `indicator_sets_{regime?}_{symbol}_{timeframe}.json` (Schema-Version aufnehmen).
  - Risk/P&L-Block: zeigt für gewähltes Set die Ergebnisse des integrierten Backtests (TP1/2/3, SL, Trailing, Position Size).
  - Optional separates Tab, falls UI-Platz: „Risk Management & P&L“ mit Parametern (max_risk_per_trade, ATR-Multiplikatoren) und Backtest-Button.

## 5) Daten- & JSON-Design (Schema-First)
- Input: `indicator_config_v2.json`
  - Felder: `schema_version`, `symbol`, `timeframe`, `indicators: [{id, name, defaults?, tags}]`.
  - Keine Parameter-Ranges im Input (werden in UI gesetzt).
  - Validierung: SchemaValidator (falls vorhanden) oder Pydantic-Modelle im UI/Service.
- Output Optimization Results (intern):
  - `indicator_optimization_results_{symbol}_{tf}.json` je Run; enthält alle getesteten Sets pro Signal-Typ mit Metriken, Loop-Anzahl, Seeds.
- Output Indicator Sets (Export):
  - `indicator_sets_{symbol}_{tf}.json`: enthält ausgewählte Sets pro Signal-Typ, Parameter, Metriken, Risk-Settings, Referenzen auf verwendete Daten (`regime_config_ref`, `optimization_results_ref`).
- Backtest Report:
  - Optional `indicator_backtest_report_{symbol}_{tf}.json` mit Equity Curve, Trades, P&L, Drawdown, Win-Rate je Signal-Typ.
- Versionierung: `schema_version` Pflicht, `created_at`, `source` (symbol/timeframe), `stage`.

## 6) Funktionale Arbeitspakete (Akzeptanzkriterien)
1. **AP1 Anforderungen/Daten klären**  
   - JSON-Schema-Entwurf für Input/Output fertig, abgestimmt; Pfade bestätigt.
2. **AP2 UI-Refactor Tab 4**  
   - Regime-Controls entfernt; neue Range-Tabelle mit bis zu 10 Parametern/Indikator; Signal-Typen default checked; JSON-Load füllt Tabelle.
3. **AP3 Optimierungs-Engine**  
   - Worker ersetzt Random-Ergebnisse durch deterministische Backtest/Evaluationslogik; berücksichtigt Loop-Count; stoppbar; liefert Score + Kernmetriken.
4. **AP4 Risk Management Integration**  
   - ATR-basiertes Sizing, SL/TP/Trailing aus `Indikatorensets` in Optimierungs-/Backtest-Pipeline eingebunden; Parameter konfigurierbar; Defaults dokumentiert.
5. **AP5 Results/Export**  
   - Tab 6 zeigt Top-N, erlaubt Auswahl/Export; gespeicherte JSON validiert; Referenzen (regime/optimization) gesetzt.
6. **AP6 Backtest-Reporting**  
   - P&L-Auswertung (Equity-Curve, PF, MaxDD) je Signal-Typ; UI-Preview + optionale Dateiablage.
7. **AP7 Tests & Doku**  
   - Unit-Tests für Param-Parsing, Worker-Scoring, JSON-Export; UI-Snapshot/Smoke-Test falls vorhanden; README/ARCHITECTURE-Update falls Schnittstellen geändert.

## 7) Technische Umsetzungsschritte (Reihenfolge)
1. Schema-Definitionen für Input/Output/Report entwerfen (JSON Schema + Pydantic Models) und Ablage unter `03_JSON/.../schemas` oder `schemas/entry_analyzer`.
2. Tab 4 Refactor: UI-Komponenten anpassen, Loader für Indikatorliste + Param-Tabelle, Defaults aus `Indikatorensets` hinterlegen, Validierungsfehler sichtbar machen.
3. Parameter-Generation: Utility, das aus Tabelle Range-Kombinationen erzeugt (mit Max-Kombinationen-Limit + Warnung).
4. Optimierungs-Worker: echte Evaluationspipeline (Indicator-Berechnung, Signal-Logik aus `Indikatorensets`, RiskManager, Backtest pro Signal-Typ). Parallelisierung prüfen (Threads/async) ohne Event-Loop-Block.
5. Ergebnis-Persistenz: Speicherformat für `indicator_optimization_results_*` implementieren, Laden in Tab 6 ermöglichen.
6. Export/Backtest UI: Auswahl + Export; P&L/Equity-Preview; optional neues Tab für Risk/P&L-Steuerung.
7. Tests + Dokumentation: neue Tests, kurze Dev-Notes im Projektplan/README; Checkliste (`3_CHECKLIST_OrderPilot_AI_Tradingbot.md`) abhaken mit Timestamp & Nachweis.

## 8) Test- & Validierungsplan
- Unit: Param-Range Parser, Kombinationserzeuger, RiskManager (Position Size, TP/SL), Score-Berechnung.
- Integration: Worker-Lauf mit kleinem Datensatz, Stop/Resume, Fortschritts-Events; JSON-Export/Import Roundtrip.
- UI/Smoke: Tabs laden, JSON importieren, Start/Stop Buttons, Tabellenfüllung, Export-Dialog.
- Backtest: deterministische Seeds, Vergleich mit Kontroll-CSV/JSON, Toleranzen für Metriken definieren.

## 9) Risiken & Mitigation
- **Fehlende JSON-Governance-Datei**: Blocker – vor Implementierung klären oder neue Regel-Datei anlegen.
- **Performance/Explosionsgefahr** bei Parameter-Kombis: harte Limits + Warnungen + Progress UI + Early-Stop.
- **Live-Handel versehentlich**: Paper-Default erzwingen, keine Live-Keys anfassen, klare Env-Schalter.
- **UI-Überladung**: ggf. separates Risk/P&L-Tab; Tooltips + Default-Werte hinterlegen.
- **Platzhalter-Logik** bleibt aktiv: Sicherstellen, dass Random-Code entfernt und mit Tests abgedeckt wird.

## 10) Deliverables & Nachweise
- Fertiger UI-Flow Tabs 4–6 (plus optionales Risk/P&L-Tab).
- JSON-Schemas + Beispiel-Dateien (Input, Optimization Results, Export, Backtest Report).
- Tests (Pfadvorschlag: `tests/ui/entry_analyzer/test_indicator_workflow.py`, `tests/core/strategy/test_btc_scalping_risk.py`).
- Aktualisierte Checkliste-Einträge mit Timestamp, Code-Referenzen, Log/Report-Pfaden.

## 11) Milestones (Iterationsempfehlung)
1. M1: Schemas + Tab-4-Refactor (Range-Tabelle, JSON-Load) – 1 Tag.
2. M2: Worker-Backtest-Engine + Loop-Feld Tab 5 – 1–2 Tage.
3. M3: Results/Export + Risk/P&L-Integration Tab 6 (+ optional neues Tab) – 1–2 Tage.
4. M4: Tests, Docs, Checkliste-Update – 0.5–1 Tag.

---

Nächste Schritte: (a) Schema-Governance klären/ergänzen, (b) Max-Kombinationen-Grenze definieren, (c) Backtest-Datensatz für Smoke-Tests festlegen.
