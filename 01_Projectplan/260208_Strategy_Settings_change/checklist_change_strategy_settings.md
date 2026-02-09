Nachfolgend ist die **Checkliste als Umsetzungsplan** im **gleichen Tracking-Stil** wie deine Vorlage aufgebaut.
Fokus: **Strategy Settings Pipelines** (Regime-Erkennung + JSON-Score + Format-Konsolidierung + UI-Anpassungen) – mit **harten Leitplanken**, damit sich keine “Heuristik-Bugs” und keine “100%-Bullshit-Scores” mehr einschleichen.

---

# ✅ Checkliste: Strategy Settings Pipeline – Regime/Score/JSON v2.1 Konsolidierung

**Start:** 2026-02-08
**Letzte Aktualisierung:** 2026-02-08 20:30
**Gesamtfortschritt:** 65%

---

## 🛡️ HARTE LEITPLANKEN (vor JEDEM Task lesen)

### ✅ PFLICHT (für jeden Task)

1. **Fail-Closed**: Missing `entry_expression`, missing Indicators, invalid JSON ⇒ **kein Signal**, **kein Score-Boost**, **klare UI-Warnung**.
2. **Schema-Validation Pflicht**: JSON wird **nicht** geladen, bevor es **gegen Schema** validiert wurde.
3. **Single Source of Truth**: Regime + Indicator-Values + Entry-Eval + Score kommen aus **einer** Pipeline (kein Parallel-Legacy).
4. **Explainability Pflicht**: UI muss für jeden Score **Begründungen** liefern (Regime-Match, Entry-Result, Missing/NaN, Penalties).
5. **Keine Heuristik-Rettungsanker**: Keine stillen Defaults wie `entry_expression="true"`.
6. **Keine Patchfiles**: Änderungen werden als **vollständige Dateien/Commits** umgesetzt, nicht als Patch-Artefakte.

### ❌ VERBOTEN

* `except: pass` / Silent Failures
* “Quick Fixes” nur in der UI (Symptombekämpfung)
* Regime in UI A anders als in UI B
* JSON-Loader, der “rät”, was ein File ist, statt über `kind` + Schema zu entscheiden
* Scores als “Prozent” darstellen, wenn es nur ein Match-Status ist

### 🔍 BEFORE MARKING COMPLETE (für jeden Task)

* [ ] Validierung/Fehlerfälle getestet (inkl. invalid JSON, missing fields)
* [ ] Logs vorhanden (keine Spam-Logs, aber aussagekräftig)
* [ ] Unit-Tests ergänzt/angepasst
* [ ] UI zeigt konkrete Ursachen (nicht “Fehler”)
* [ ] Keine TODOs/Platzhalter
* [ ] Keine Breaking Changes ohne SemVer-Major + Migration

---

## 📊 Status-Legende

* ⬜ Offen / Nicht begonnen
* 🔄 In Arbeit
* ✅ Abgeschlossen
* ❌ Fehler / Blockiert
* ⭐ Übersprungen / Nicht benötigt

---

## 🧾 TRACKING-FORMAT (PFLICHT)

### Erfolgreicher Task

```markdown
- [ ] **X.Y.Z Task Name**
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM) → *Was wurde implementiert*
  Code: `pfad/datei.py:zeilen` (wo implementiert)
  Tests: `tests/test_*.py::TestClass::test_*`
  Nachweis: Screenshot/Log-Ausgabe/Beispiel-JSON-Load mit Ergebnis
```

### Fehlgeschlagener Task

```markdown
- [ ] **X.Y.Z Task Name**
  Status: ❌ Fehler (YYYY-MM-DD HH:MM) → *Fehlerbeschreibung*
  Fehler: `Exakte Error Message`
  Ursache: *Root Cause*
  Lösung: *Fix-Plan*
  Retry: Geplant für YYYY-MM-DD HH:MM
```

---

# Phase 0: Vorbereitung & Ist-Analyse (Stabilitätsgrundlage)

* [ ] **0.1 Code-Freeze für Strategy Settings Scope definieren**
* [ ] **0.2 Betroffene Module inventarisieren (Loader/Scorer/Detector/UI/Engine)**
* [ ] **0.3 Alle JSON-Typen im Projekt klassifizieren (strategy_config, indicator_set, regime_optimization_results)**
* [ ] **0.4 Bestehende UI-Pfade dokumentieren (welcher Button ruft welche Engine?)**
* [ ] **0.5 “Truth Table” definieren: Welche Inputs ⇒ welches Regime/Score erwartet**
* [ ] **0.6 Minimal-Regression-JSON-Korpus zusammenstellen (5–10 repräsentative Dateien)**
* [ ] **0.7 Logging-Policy für Pipeline definieren (debug/info/warn)**
* [ ] **0.8 Test-Framework Standard festlegen (pytest) + Test-Ordnerstruktur prüfen**
* [ ] **0.9 Performance-Budget festlegen (Scoring darf UI nicht blockieren ⇒ optional Threading/Worker)**
* [ ] **0.10 Abbruchkriterien definieren (bei Schema-Fehler: UI zeigt Liste, keine Berechnung)**

**Review Checkpoint Phase 0**

* [ ] Nachweis: Dokument “Pipeline-Istzustand” + JSON-Korpus liegt vor

---

# Phase 1: JSON-Format v2.1 + Schema-Validation (Fail-Closed erzwingen)

## 1.1 Format-Entscheidung & Versionierung

* [ ] **1.1.1 `kind` Feld als Pflicht einführen (strategy_config | indicator_set | regime_optimization_results)**
* [ ] **1.1.2 `schema_version` Regeln festschreiben (SemVer; breaking ⇒ Major)**
* [ ] **1.1.3 “Bausteine” standardisieren:**

  * [ ] Indicators: `id`, `type`, `params[]` (name/value/range)
  * [ ] Regimes: `id`, `priority`, `scope`, `thresholds[]`
* [ ] **1.1.4 Verbot: `optimization_results[]` in strategy_config/indicator_set**

## 1.2 JSON Schema hinzufügen

* [ ] **1.2.1 Ordner `schemas/` anlegen**
* [ ] **1.2.2 `schemas/strategy_config.schema.json` erstellen**
* [ ] **1.2.3 `schemas/indicator_set.schema.json` erstellen**
* [ ] **1.2.4 `schemas/regime_optimization_results.schema.json` erstellen**
* [ ] **1.2.5 Gemeinsame Definitionen auslagern (`defs.json`: IndicatorDef, RegimeDef, ThresholdDef, ParamDef)**
* [ ] **1.2.6 Schema: disallow unknown fields (strict)**
* [ ] **1.2.7 Schema: required Felder (insb. `kind`, `schema_version`)**
* [ ] **1.2.8 Schema: entry_expression Regeln (explizit; nie implizit “true”)**

## 1.3 Loader-Validation erzwingen

* [ ] **1.3.1 JSON Loader so umbauen, dass zuerst Schema validiert wird**
* [ ] **1.3.2 Fehlerobjekt standardisieren (machine + human readable)**
* [ ] **1.3.3 UI-Fehleranzeige für Schema-Fehler (Liste, klickbar, copyable)**
* [ ] **1.3.4 “Fail-Closed”: Invalid JSON ⇒ Strategy nicht ladbar ⇒ Score/Regime deaktiviert**
* [ ] **1.3.5 Unit Tests: Valid/Invalid JSON je `kind`**

**Review Checkpoint Phase 1**

* [ ] Nachweis: Ein invalides JSON wird sauber abgelehnt (UI + Logs + Tests)

---

# Phase 2: Unified Strategy Settings Pipeline (Single Source of Truth)

## 2.1 Neue Pipeline-Komponente einführen

* [ ] **2.1.1 Modul `strategy_settings_pipeline.py` (oder ähnlich) erstellen**
* [ ] **2.1.2 Pipeline API definieren:**

  * [ ] `load_and_validate(json_path) -> Model`
  * [ ] `compute_indicators(candles, indicators_def) -> IndicatorValues`
  * [ ] `detect_regime(indicator_values, regimes_def) -> ActiveRegime`
  * [ ] `evaluate_entry(entry_expression, context) -> bool`
  * [ ] `score(strategy, results, penalties) -> ScoreResult`
* [ ] **2.1.3 Context Contract fixieren (welche Keys existieren garantiert?)**
* [ ] **2.1.4 Penalty-System definieren (missing indicator, NaN, insufficient candles)**

## 2.2 Legacy/Parallelpfade eliminieren

* [ ] **2.2.1 RegimeEngine (Legacy) aus Strategy Settings Scoring entfernen**
* [ ] **2.2.2 RegimeDetector/Threshold-Evaluator vereinheitlichen**
* [ ] **2.2.3 `_perform_regime_detection()` im UI auf Unified Pipeline umstellen (oder deaktivieren bis fertig)**
* [ ] **2.2.4 Router/Scorer ausschließlich über Unified Pipeline füttern**

## 2.3 Fail-Closed Entry Evaluation

* [ ] **2.3.1 Entfernen: Default `entry_expression="true"`**
* [ ] **2.3.2 Wenn Entry fehlt ⇒ `EntryResult = False` + UI Warnung**
* [ ] **2.3.3 CEL Evaluator:**

  * [ ] Compile/Check vor Ausführung
  * [ ] Fehlerdetails (Zeile/Spalte/Token)
  * [ ] Whitelist erlaubter Functions
* [ ] **2.3.4 Unit Tests: Entry True/False/Error Fälle**

## 2.4 Indikator-Values deterministisch

* [ ] **2.4.1 Indikator-Berechnung: deterministischer Output (Series/Scalar Normalisierung)**
* [ ] **2.4.2 Mapping: threshold `name` ⇒ IndicatorValue Key eindeutig**
* [ ] **2.4.3 Missing Indicator ⇒ Value=NaN ⇒ comparisons False**
* [ ] **2.4.4 Unit Tests: Missing/NaN führt nicht zu Regime True**

**Review Checkpoint Phase 2**

* [ ] Nachweis: Für identische Candles liefert jeder UI-Pfad identisches Regime + identischen Score

---

# Phase 3: Scoring korrekt & nicht missverständlich (keine Fake-“100%”)

## 3.1 Score-Modell neu definieren

* [ ] **3.1.1 Score ist kein Prozent: UI-Label ändern (MatchScore/SignalScore)**
* [ ] **3.1.2 Score-Komponenten einführen:**

  * [ ] `regime_match_score` (0..60)
  * [ ] `entry_signal_score` (0..30)
  * [ ] `data_quality_score` (0..10)
* [ ] **3.1.3 Regel: 100 nur möglich bei vollständiger Datenlage + erklärtem Match**
* [ ] **3.1.4 Penalties sichtbar machen (z. B. -10 bei missing critical indicator)**

## 3.2 Explainability verpflichtend

* [ ] **3.2.1 ScoreResult enthält:**

  * [ ] ActiveRegime + erfüllte/nicht erfüllte thresholds
  * [ ] Entry eval result + verwendete Variablen
  * [ ] Missing/NaN Liste
  * [ ] Penalties Liste
* [ ] **3.2.2 UI zeigt “Warum” (Tooltip/Detailpanel)**
* [ ] **3.2.3 Export: ScoreReport als JSON/Markdown (für Debugging)**

## 3.3 Tests gegen “Score-Pumping”

* [ ] **3.3.1 Test: Missing entry_expression darf niemals Score erhöhen**
* [ ] **3.3.2 Test: Missing indicators ⇒ Regime False ⇒ kein 100**
* [ ] **3.3.3 Test: CEL Compile Error ⇒ Entry False + UI Warnung**

**Review Checkpoint Phase 3**

* [ ] Nachweis: Ein “Always-True” ist unmöglich ohne explizite, validierte Expression + DataQuality=10

---

# Phase 4: UI Anpassungen (Strategy Settings Dialog)

## 4.1 UI-Bugs/Inkonsistenzen beseitigen

* [ ] **4.1.1 Tabellen-Spaltenzugriff: Name-Spalte korrekt (nicht Score-Spalte)**
* [ ] **4.1.2 Router-Aufruf: nur existierende Methode verwenden**
* [ ] **4.1.3 Einheitliche Datenquelle (Unified Pipeline) für Analyse/Scoring/Regime-View**
* [ ] **4.1.4 UI-Statusanzeigen: “invalid config”, “missing data”, “compiled ok”**

## 4.2 UX für Debugging

* [ ] **4.2.1 Detailpanel: Regime/Entry/Score Erklärung**
* [ ] **4.2.2 Copy-Buttons (JSON Path, Error List, Context Snapshot)**
* [ ] **4.2.3 Filter: nur gültige Strategien / nur active regime matches**
* [ ] **4.2.4 “Validate JSON” Button (zeigt Schema-Report ohne Scoring)**

## 4.3 Performance & Responsiveness

* [ ] **4.3.1 Pipeline in Worker/Thread ausführen (UI bleibt responsiv)**
* [ ] **4.3.2 Cancel/Abort Mechanismus für lange Berechnungen**
* [ ] **4.3.3 Progress Anzeige (Loading/Calculating/Scoring)**

**Review Checkpoint Phase 4**

* [ ] Nachweis: UI zeigt Regime + Score + Gründe nachvollziehbar, ohne Freeze

---

# Phase 5: Migration & Kompatibilität (Altbestände ohne Chaos)

## 5.1 Migrations-Tooling

* [ ] **5.1.1 Ordner `migrations/` anlegen**
* [ ] **5.1.2 Migration v1 → v2.1 für indicator_set**
* [ ] **5.1.3 Migration v1 → v2.1 für strategy_config**
* [ ] **5.1.4 Migration/Extraktion: regime_optimization_results bleibt eigenes `kind`**
* [ ] **5.1.5 Dry-Run Mode (zeigt geplante Änderungen, schreibt nichts)**

## 5.2 Backward Compatibility Policy

* [ ] **5.2.1 Policy: Welche Versionen werden noch gelesen?**
* [ ] **5.2.2 Deprecation Warning: UI zeigt “v1 wird ab Datum X entfernt”**
* [ ] **5.2.3 Konfig: “Allow legacy read” Flag (default OFF)**
* [ ] **5.2.4 Tests: v1 wird entweder migriert oder klar abgelehnt (keine Heuristik)**

**Review Checkpoint Phase 5**

* [ ] Nachweis: 10 Legacy-JSONs migrieren deterministisch, ohne semantische Überraschungen

---

# Phase 6: QA, Release, Dokumentation (Produktionsreife)

## 6.1 Test Suite

* [ ] **6.1.1 Unit Tests: Schema Validation**
* [ ] **6.1.2 Unit Tests: Indicator Calculation Contract**
* [ ] **6.1.3 Unit Tests: Regime Detection (thresholds)**
* [ ] **6.1.4 Unit Tests: CEL compile/eval + error cases**
* [ ] **6.1.5 Integration Tests: UI → Pipeline → ScoreReport**
* [ ] **6.1.6 Regression Tests: “vorher kaputte Fälle” als Fixtures**

## 6.2 Logging & Observability

* [ ] **6.2.1 Strukturierte Logs (strategy_id, kind, schema_version)**
* [ ] **6.2.2 Log-Level Review (kein Debug-Spam im Normalbetrieb)**
* [ ] **6.2.3 Fehlercodes standardisieren (z. B. `JSON_SCHEMA_INVALID`, `CEL_COMPILE_ERROR`)**

## 6.3 Dokumentation (für dich + für KI-Workflow)

* [ ] **6.3.1 “JSON Format Spec v2.1” (human readable)**
* [ ] **6.3.2 “Migration Guide v1 → v2.1”**
* [ ] **6.3.3 “Strategy Settings Pipeline Architecture”**
* [ ] **6.3.4 “CEL Context Variables Contract”**
* [ ] **6.3.5 “Troubleshooting: Regime/Score”**

## 6.4 Release Gate

* [ ] **6.4.1 Version bump + Changelog**
* [ ] **6.4.2 “Golden Run”: 5m BTCUSDT Beispiel-JSONs liefern erwartete Regimes**
* [ ] **6.4.3 Nutzer-Abnahme: UI zeigt keine Fake-100% mehr**
* [ ] **6.4.4 Tag/Release erstellen**

**Review Checkpoint Phase 6**

* [ ] Nachweis: Alle Tests grün + Dokumentation vollständig + keine Legacy-Heuristik aktiv

---

# 🔥 Kritischer Pfad (blockiert alles andere)

1. **Phase 1 (Schema + kind + Fail-Closed)**
2. **Phase 2 (Unified Pipeline + Legacy entfernen)**
3. **Phase 3 (Score-Definition + Explainability)**
4. Dann erst UI/UX-Politur & Migration

Wenn du diese Reihenfolge nicht einhältst, baust du wieder “symptomatische UI-Fixes” auf wackliger Logik – und das Problem kommt zurück.

---

Wenn du willst, erstelle ich dir als nächsten Schritt zusätzlich einen **harten “KI-Implementierungs-Prompt”** (für deine CLI-KI), der diese Checkliste **zwangsläufig von oben nach unten abarbeitet**, inkl. Abbruchregeln (“wenn Schema-Validation fehlt ⇒ STOP”).
