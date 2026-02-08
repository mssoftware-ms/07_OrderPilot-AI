CLI-KI Implementierungs-Prompt (STRIKT, von oben nach unten abarbeiten)
§1 verwende die checkliste "\01_Projectplan\260208_Strategy_Settings_change\checklist_change_strategy_settings.md" um dieses projekt zu realisieren
Projekt: 07_OrderPilot-AI
Repo-Root (lokal): D:\03_Git\02_Python\07_OrderPilot-AI

Eingangsdatei (JSON-Vorlage / Referenz)

"\03_JSON\Entry_Analyzer\Regime\JSON Template\260130024721_regime_optimization_results_BTCUSDT_5m_#1.json"

Ziel: Neues Template erzeugen (IndicatorSets Trading Bot)

Speicherort neues Template:
D:\03_Git\02_Python\07_OrderPilot-AI\03_JSON\Trading_Bot\templates\template_indicatorsets_trading_bot.json

1) NICHT VERHANDELBAR (HARTE LEITPLANKEN)

Fail-Closed:

Missing entry_expression, missing Indicators, invalid JSON ⇒ kein Signal, kein Score-Boost, sichtbare Warnung in UI/Logs.

Verboten: irgendein Default wie entry_expression = "true".

Single Source of Truth:
Regime + Indicator Values + Entry Eval + Score dürfen nicht aus zwei Engines kommen. Keine parallele Legacy-Regime-Erkennung im Strategy-Settings-Scoring.

Schema-Validation Pflicht:
JSON darf nicht geladen werden, bevor es gegen ein JSON-Schema validiert ist.

Explainability Pflicht:
Jede Score-Zeile muss eine maschinenlesbare Erklärung haben (welches Regime, welche thresholds erfüllt, entry eval, missing/NaN, penalties).

Keine Minimalversionen:
Bestehende Funktionen bleiben erhalten, notwendige Funktionalität wird nicht „weggekürzt“.
Änderungen sind sauber integriert, nicht “nur fürs Problem”.

Kein Silent Fail:
Kein except: pass, kein “zur Sicherheit True”.

Arbeitsweise:

Abarbeitung streng sequenziell (Abschnitte 1 → 8).

Wenn ein Gate fehlschlägt ⇒ STOP, Fehler reporten, erst dann weiter.

1) IST-ANALYSE (GATE 1)
Aufgaben

Repo scannen: finde alle relevanten Module der Strategy-Settings-Pipeline:

JSON Loader / Entry Loader

Regime Engine / Regime Detector (legacy + json)

Scoring / Evaluator

UI: Strategy Settings Dialog

Router (Regime→StrategySet)

Output (Pflicht)

Erstelle eine Datei docs/strategy_settings_pipeline_audit.md mit:

Liste der Dateien/Module + kurze Funktion

Welche UI-Buttons welche Pfade/Engines nutzen

Wo aktuell Defaults/Heuristiken existieren (insb. entry_expression="true")

Gate 1 – Bestehen wenn

Die Audit-Datei existiert und eindeutig zeigt, wo Regime+Score aktuell berechnet werden.

2) JSON-KONSOLIDIERUNG: “KIND” + SCHEMA (GATE 2)
Ziel

Ein eindeutiges, validierbares Format, damit Loader nicht raten.

Aufgaben

JSON-Schema Ordner einführen: schemas/

Drei Schemas erstellen (Draft 2020-12):

schemas/strategy_config.schema.json

schemas/indicator_set.schema.json

schemas/regime_optimization_results.schema.json

Pflichtfeld einführen: kind ∈
strategy_config | indicator_set | regime_optimization_results

schema_version strikt nach SemVer behandeln.

Gate 2 – Bestehen wenn

Mindestens ein valid/invalid Testfall pro Schema existiert (pytest).

Loader verweigert invalid JSON (keine Berechnung, klare Fehlermeldung).

3) LOADER FIX: FAIL-CLOSED ENTRY (GATE 3)
Aufgaben

Entferne jeden Fallback, der fehlendes entry_expression auf "true" setzt.

Loader-Verhalten:

Wenn kind in (strategy_config, regime_optimization_results) und entry_expression fehlt/leer ⇒

entry_enabled = False

Fehler/Warnung in UI/Logs: ENTRY_EXPRESSION_MISSING

Die UI muss das sichtbar anzeigen (Banner/Status/Tooltip).

Gate 3 – Bestehen wenn

Ein JSON ohne entry_expression kann geladen werden nur als “invalid/disabled entry”, niemals als “enter true”.

Unit-Test deckt das ab.

4) UNIFIED PIPELINE (Single Source of Truth) (GATE 4)
Ziel

Eine einzige Pipeline, die UI-Buttons/Scoring/Regime-Detector identisch nutzen.

Aufgaben

Neues Modul erstellen (Beispielname):
src/.../strategy_settings_pipeline.py

Pipeline API (Pflichtfunktionen):

load_validate(path) -> model

compute_indicators(candles, indicators_def) -> values

detect_regime(values, regimes_def) -> active_regime + explain

evaluate_entry(entry_expression, context) -> bool + explain

score(result, penalties) -> score_result + explain

Entferne/entkoppel Legacy-Regime aus Strategy-Settings-Scoring:

Strategy Settings darf nicht “legacy classify” nutzen, wenn JSON-Regimes genutzt werden.

Jeder UI-Pfad ruft nur noch die Unified Pipeline auf:

Score berechnen

Regime-Ansicht / Detector

Analyzer Preview

Gate 4 – Bestehen wenn

Für denselben Candle-Input liefern alle UI-Pfade identisches Regime und identischen Score.

Tests/Logs belegen das.

5) SCORE MODELL REPARIEREN (GATE 5)
Ziel

Kein “Fake-100%”. Score ist kein Prozent, sondern ein erklärbarer Signal-/Match-Score.

Aufgaben

UI-Label ändern: weg von “%”, hin zu z. B. MatchScore oder SignalScore.

Score-Komponenten (konkret):

regime_match_score (0..60)

entry_signal_score (0..30)

data_quality_score (0..10) (Penalties bei missing/NaN/zu wenig Candles)

100 nur wenn:

Regime match TRUE

Entry TRUE

DataQuality 10/10

ScoreResult enthält explainability:

erfüllte/fehlende thresholds

entry eval + verwendete Variablen

missing/NaN + penalty liste

Gate 5 – Bestehen wenn

“100” ist ohne vollständige Datenlage + explizite entry_expression unmöglich.

Unit Tests: missing indicators ⇒ kein 100.

6) UI-FIXES (GATE 6)
Aufgaben

Korrigiere Tabellen-Spaltenzugriffe (Name-Spalte darf nicht aus Score-Spalte gelesen werden).

Router-Invocation: nur existierende Methoden (keine falschen Funktionsnamen).

UI zeigt:

JSON Schema Status (valid/invalid + Fehlerliste)

Pipeline Ergebnisse + Gründe (Detailpanel/Tooltip)

Missing indicators / NaN klar sichtbar

Gate 6 – Bestehen wenn

Keine UI-Aktion arbeitet mit falschem Strategy-Name/ID.

Analyse-Button funktioniert stabil.

7) TEMPLATE-ERZEUGUNG: IndicatorSet aus deiner Optimization-JSON ableiten (GATE 7)
Ziel

Aus der Referenzdatei ein sauberes, wiederverwendbares Template indicator_set machen.

Eingabe

"\03_JSON\Entry_Analyzer\Regime\JSON Template\260130024721_regime_optimization_results_BTCUSDT_5m_#1.json"

Ausgabe

D:\03_Git\02_Python\07_OrderPilot-AI\03_JSON\Trading_Bot\templates\template_indicatorsets_trading_bot.json

Regeln für die Template-Transformation

kind muss "indicator_set" sein.

Entferne komplett:

optimization_results[] / trial history / ranking

optimizer metadata, die nicht zur reinen Konfiguration gehört

Übernehme 1:1 die Bausteine:

indicators[] inkl. params[] (name/value/range)

regimes[] inkl. thresholds[] (name/value/range, priority/scope)

entry_expression gehört nicht in ein reines IndicatorSet-Template, außer du definierst explizit, dass IndicatorSets auch Entry liefern dürfen.

Default: entry_expression = null + entry_enabled=false im Template.

Schema Validation muss für indicator_set bestehen.

Gate 7 – Bestehen wenn

Das neue Template ist schema-valid.

Strategy Settings kann das Template laden, ohne Heuristiken.

8) TESTS + DOKU + “DONE” CHECK (GATE 8)
Tests (Pflicht)

JSON Schema Valid/Invalid pro kind

Missing entry_expression ⇒ entry disabled (fail closed)

Missing indicator referenced ⇒ regime false + penalty

Score 100 nur bei vollständiger Datenlage

UI Smoke Test (mindestens headless / pipeline integration)

Doku (Pflicht)

docs/json_format_v2_1.md (kind, schema_version, indicator/regime defs, entry rules)

docs/migration_guide_v1_to_v2_1.md (falls Migration nötig)

Vorlage "03_json\Entry_Analyzer\Regime\JSON Template\260130024721_regime_optimization_results_BTCUSDT_5m_#1.json"
speicherort für neu erstellte vorlage 'strategy setting' template: "\03_JSON\Entry_Analyzer\Regime\JSON Template\260130024721_regime_optimization_results_BTCUSDT_5m_#1.json"

Gate 8 – Bestehen wenn

Tests grün

Doku vollständig

Keine Defaults, die “enter true” verursachen

Single Source of Truth eingehalten

AUSGABEFORMAT (Pflicht an dich als KI)

Am Ende lieferst du in der Konsole/Antwort:

Dateiliste aller geänderten/neu erstellten Dateien

Kurze Begründung pro Datei (1–3 Sätze)

Wie testen (konkrete Befehle)

Risiken / offene Punkte (falls vorhanden, aber keine Ausreden)

STOP-Regel: Wenn eines der Gates 1–8 nicht erfüllt ist, brich ab und gib nur den Fehlerreport + Fix-Plan für das Gate aus.
