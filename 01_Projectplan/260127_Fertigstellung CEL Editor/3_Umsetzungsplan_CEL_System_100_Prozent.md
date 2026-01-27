# ✅ Checkliste: CEL System 100% Fertigstellung

**Start:** 2026-01-27
**Letzte Aktualisierung:** 2026-01-27
**Gesamtfortschritt:** 0% (0/89 Tasks)
**Ziel:** Vollständig funktionsfähiges CEL System mit Editor, Engine und Dokumentation

---

## 🛠️ **CODE-QUALITÄTS-STANDARDS (vor jedem Task lesen!)**

### **✅ ERFORDERLICH für jeden Task:**
1. **Vollständige Implementation** - Keine TODO/Platzhalter
2. **Error Handling** - try/catch für alle kritischen Operationen
3. **Input Validation** - Alle Parameter validieren
4. **Type Hints** - Alle Function Signatures typisiert
5. **Docstrings** - Alle public Functions dokumentiert
6. **Logging** - Angemessene Log-Level verwenden
7. **Tests** - Unit Tests für neue Funktionalität
8. **Clean Code** - Alter Code vollständig entfernt

### **❌ VERBOTEN:**
1. **Platzhalter-Code:** `# TODO: Implement later`
2. **Auskommentierte Blöcke:** `# def old_function():`
3. **Silent Failures:** `except: pass`
4. **Hardcoded Values:** `max_tokens = 4000`
5. **Vague Errors:** `raise Exception("Error")`
6. **Missing Validation:** Keine Input-Checks
7. **Dummy Returns:** `return "Not implemented"`
8. **Incomplete UI:** Buttons ohne Funktionalität

### **🔍 BEFORE MARKING COMPLETE:**
- [ ] Code funktioniert (getestet)
- [ ] Keine TODOs im Code
- [ ] Error Handling implementiert
- [ ] Tests geschrieben
- [ ] Alter Code entfernt
- [ ] Logging hinzugefügt
- [ ] Input Validation vorhanden
- [ ] Type Hints vollständig

---

## 📊 Status-Legende
- ⬜ Offen / Nicht begonnen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

## 🛠️ **TRACKING-FORMAT (PFLICHT)**

### **Erfolgreicher Task:**
```markdown
- [ ] **1.2.3 Task Name**
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM) → *Was wurde implementiert*
  Code: `dateipfad:zeilen` (wo implementiert)
  Tests: `test_datei:TestClass` (welche Tests)
  Nachweis: Screenshot/Log-Ausgabe der Funktionalität
```

### **Fehlgeschlagener Task:**
```markdown
- [ ] **1.2.3 Task Name**
  Status: ❌ Fehler (YYYY-MM-DD HH:MM) → *Fehlerbeschreibung*
  Fehler: `Exakte Error Message hier`
  Ursache: Was war das Problem
  Lösung: Wie wird es behoben
  Retry: Geplant für YYYY-MM-DD HH:MM
```

### **Task in Arbeit:**
```markdown
- [ ] **1.2.3 Task Name**
  Status: 🔄 In Arbeit (Start: YYYY-MM-DD HH:MM) → *Aktueller Fortschritt*
  Fortschritt: 60% - Database Schema erstellt, Tests ausstehend
  Geschätzt: 2h verbleibend
  Blocker: Keine
```

---

## Phase 0: Vorbereitung & Dokumentations-Audit (8-10 Stunden)

### 0.1 Dokumentations-Analyse & Korrektur (4-5 Stunden)
- [ ] **0.1.1 CEL_Befehle_Liste_v2.md Audit**
  Status: ⬜ → *Nicht-implementierte Funktionen markieren*
  - Markiere ~60% nicht-implementierte Funktionen als "⚠️ NICHT IMPLEMENTIERT"
  - Erstelle Abschnitt "Roadmap v3.0" für geplante Features
  - Liste alle tatsächlich verfügbaren Funktionen

- [ ] **0.1.2 Operator Precedence Dokumentation**
  Status: ⬜ → *CEL Operator-Reihenfolge hinzufügen*
  - Tabelle mit Precedence-Levels (1-10)
  - Beispiele für komplexe Ausdrücke
  - Klammer-Regeln dokumentieren

- [ ] **0.1.3 Error-Handling Dokumentation**
  Status: ⬜ → *Fehlerbehandlung vollständig dokumentieren*
  - Null-Werte Handling (`isnull()`, `nz()`)
  - Fehlende Indikatoren: `ConditionEvaluationError`
  - Default-Verhalten bei Fehlern
  - Division-by-Zero Handling

- [ ] **0.1.4 Regime JSON Rules Korrektur**
  Status: ⬜ → *Evaluierungslogik korrigieren*
  - Korrigiere "STOP"-Logik (ALLE Regimes werden geprüft)
  - Dokumentiere Threshold → Condition Mapping
  - Ergänze CEL-Support in Regimes
  - RegimeScope.GLOBAL dokumentieren

### 0.2 Code-Audit & Bestandsaufnahme (2-3 Stunden)
- [ ] **0.2.1 cel_engine.py Funktions-Audit**
  Status: ⬜ → *Alle implementierten Funktionen listen*
  - Liste: `pctl()`, `crossover()`, `isnull()`, `nz()`, `coalesce()`
  - Built-ins: `abs()`, `min()`, `max()`
  - Cache-System: LRU (128 entries)
  - Validation: `validate_expression()`

- [ ] **0.2.2 IndicatorType Synchronisation**
  Status: ⬜ → *Vergleich models.py vs types.py*
  - `models.py`: 18 Typen (dokumentiert)
  - `types.py`: 28 Typen (nicht dokumentiert)
  - Entscheide: Synchronisieren oder dokumentieren warum nicht

- [ ] **0.2.3 CEL Editor Status-Check**
  Status: ⬜ → *Bestehende Features prüfen*
  - Pattern Builder: 95% fertig
  - Code Editor: 85% fertig
  - AI Integration: OpenAI ✅, Anthropic ❌, Gemini ❌
  - File Operations: Placeholder
  - Chart View: Placeholder

### 0.3 Integration-Dokument erstellen (2-3 Stunden)
- [ ] **0.3.1 CEL_JSON_INTEGRATION.md**
  Status: ⬜ → *Neue Dokumentation: Verbindung zwischen CEL & JSON*
  - Workflow: Regime Detection → CEL Evaluation → Trading
  - Threshold-Syntax → CEL-Syntax Mapping
  - Beispiele für vollständigen Workflow
  - Glossar gemeinsamer Begriffe

---

## Phase 1: CEL Engine - Fehlende Core-Funktionen (20-25 Stunden)

### 1.1 Mathematische & Trading-Funktionen (8-10 Stunden)
- [ ] **1.1.1 clamp(x, min, max)**
  Status: ⬜ → *Wert zwischen min und max begrenzen*
  - Implementation in `cel_engine.py`
  - Unit Tests mit Randfällen
  - Dokumentation mit Beispielen

- [ ] **1.1.2 pct_change(old, new)**
  Status: ⬜ → *Prozentuale Veränderung berechnen*
  - Formula: `((new - old) / old) * 100`
  - Edge Cases: old=0, negative values
  - Tests mit Trading-Szenarien

- [ ] **1.1.3 pct_from_level(price, level)**
  Status: ⬜ → *Prozentuale Distanz zu Level*
  - Formula: `abs((price - level) / level) * 100`
  - Support für bullish/bearish Richtung
  - Tests mit realen Preis-Daten

- [ ] **1.1.4 level_at_pct(entry, pct, side)**
  Status: ⬜ → *Preislevel bei % Abstand berechnen*
  - Long: `entry * (1 - pct/100)`
  - Short: `entry * (1 + pct/100)`
  - Tests für Stop-Loss/Take-Profit Szenarien

- [ ] **1.1.5 retracement(from, to, pct)**
  Status: ⬜ → *Fibonacci Retracement Levels*
  - Formula: `from + (to - from) * pct`
  - Standard Levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
  - Tests mit Chart-Daten

- [ ] **1.1.6 extension(from, to, pct)**
  Status: ⬜ → *Fibonacci Extension Levels*
  - Formula: `to + (to - from) * pct`
  - Standard Levels: 127.2%, 161.8%, 261.8%
  - Tests mit Trend-Szenarien

### 1.2 Status-Prüfungsfunktionen (6-8 Stunden)
- [ ] **1.2.1 is_trade_open()**
  Status: ⬜ → *Check ob Trade aktuell offen*
  - Zugriff auf Trade-Context
  - Rückgabe: `bool`
  - Tests mit verschiedenen Trade-Status

- [ ] **1.2.2 is_long() & is_short()**
  Status: ⬜ → *Check Trade-Richtung*
  - Zugriff auf `trade.side`
  - Rückgabe: `bool`
  - Tests für Long/Short Szenarien

- [ ] **1.2.3 is_bullish_signal() & is_bearish_signal()**
  Status: ⬜ → *Übergeordneter Bias-Check*
  - Zugriff auf Strategy-Context
  - Rückgabe: `bool`
  - Tests mit Signal-States

- [ ] **1.2.4 in_regime(r)**
  Status: ⬜ → *Check ob in bestimmtem Regime*
  - Parameter: `r: string` (Regime-ID)
  - Zugriff auf aktives Regime
  - Tests mit verschiedenen Regimes

### 1.3 Preis-Funktionen (3-4 Stunden)
- [ ] **1.3.1 stop_hit_long() & stop_hit_short()**
  Status: ⬜ → *Stop-Loss Hit Detection*
  - Long: `current_price <= stop_price`
  - Short: `current_price >= stop_price`
  - Tests mit verschiedenen Preis-Szenarien

- [ ] **1.3.2 tp_hit()**
  Status: ⬜ → *Take-Profit Hit Detection*
  - Zugriff auf `trade.tp_price` und `current_price`
  - Rückgabe: `bool`
  - Tests für TP-Szenarien

- [ ] **1.3.3 price_above_ema(period) & price_below_ema(period)**
  Status: ⬜ → *Preis vs EMA Vergleich*
  - Zugriff auf EMA-Indikator-Werte
  - Parameter: `period: int`
  - Tests mit verschiedenen EMA-Perioden

- [ ] **1.3.4 price_above_level(level) & price_below_level(level)**
  Status: ⬜ → *Preis vs Level Vergleich*
  - Parameter: `level: number`
  - Zugriff auf `current_price`
  - Tests mit Support/Resistance

### 1.4 Zeit-Funktionen (3-4 Stunden)
- [ ] **1.4.1 now() & timestamp()**
  Status: ⬜ → *Aktuelle Zeit & Bar-Timestamp*
  - `now()`: Unix-Zeit in Sekunden
  - `timestamp()`: Aktueller Bar-Timestamp
  - Tests mit verschiedenen Timeframes

- [ ] **1.4.2 bar_age()**
  Status: ⬜ → *Alter des aktuellen Bars*
  - Formula: `now() - timestamp()`
  - Rückgabe: Sekunden
  - Tests mit Live-Daten

- [ ] **1.4.3 bars_since(condition)**
  Status: ⬜ → *Bars seit Bedingung wahr*
  - Zugriff auf historische Bar-Daten
  - Rückgabe: `int` (Anzahl Bars)
  - Tests mit verschiedenen Conditions

- [ ] **1.4.4 is_time_in_range(start, end)**
  Status: ⬜ → *Zeit-Range Check*
  - Parameter: `start, end: string` (HH:MM Format)
  - Rückgabe: `bool`
  - Tests mit verschiedenen Zeitzonen

- [ ] **1.4.5 is_new_day() & is_new_hour()**
  Status: ⬜ → *Neue Zeitperiode Detection*
  - Vergleich mit vorherigem Bar
  - Rückgabe: `bool`
  - Tests für Day/Hour Transitions

---

## Phase 2: CEL Editor - Core Features (18-22 Stunden)

### 2.1 AI Integration (4-6 Stunden)
- [ ] **2.1.1 Anthropic Claude Integration**
  Status: ⬜ → *Claude API in cel_ai_helper.py*
  - SDK Installation: `pip install anthropic`
  - Model: `claude-sonnet-4-20250514`
  - API Key aus Umgebungsvariable
  - Tests mit Code-Generierung

- [ ] **2.1.2 Google Gemini Integration**
  Status: ⬜ → *Gemini API in cel_ai_helper.py*
  - SDK Installation: `pip install google-generativeai`
  - Model: `gemini-2.0-flash-exp`
  - API Key aus Umgebungsvariable
  - Tests mit Pattern-Beschreibungen

- [ ] **2.1.3 AI Provider Selection UI**
  Status: ⬜ → *Dropdown für AI-Auswahl*
  - Options: OpenAI, Anthropic, Gemini
  - Persistent Settings (QSettings)
  - Fallback-Logik bei API-Fehlern

### 2.2 CEL Validation Backend (6-8 Stunden)
- [ ] **2.2.1 CelValidator Klasse**
  Status: ⬜ → *Neue Datei: cel_validator.py*
  - Lexer-basierte Token-Prüfung
  - Syntax-Prüfung (Klammern, Operatoren)
  - Semantik-Prüfung (Funktionen existieren?)
  - Type-Checking (wo möglich)

- [ ] **2.2.2 ValidationError Model**
  Status: ⬜ → *Error-Datenklasse mit Position*
  - Fields: `line`, `column`, `message`, `severity`
  - Severity: 'error', 'warning', 'info'
  - JSON-Serialisierung für API

- [ ] **2.2.3 Live Validation Integration**
  Status: ⬜ → *Editor onChange mit Debounce*
  - QTimer mit 500ms Debounce
  - Async Validation (kein UI-Freeze)
  - Error Markers in QScintilla

- [ ] **2.2.4 Validation Error Display**
  Status: ⬜ → *Visual Feedback im Editor*
  - QScintilla Annotations
  - Error Underlines (Squiggly)
  - Hover-Tooltips mit Error-Details
  - Error List Panel

### 2.3 File Operations (4-5 Stunden)
- [ ] **2.3.1 JSON Schema Definition**
  Status: ⬜ → *Strategy JSON Format v1.0*
  - Schema: `schema_version`, `metadata`, `pattern`, `workflows`
  - Validation mit jsonschema
  - Beispiel-Datei erstellen

- [ ] **2.3.2 New Strategy**
  Status: ⬜ → *Neue Strategy erstellen*
  - Bestätige ungespeicherte Änderungen
  - Clear Pattern Canvas
  - Clear Code Editors
  - Reset aktuellen File-Path

- [ ] **2.3.3 Open Strategy**
  Status: ⬜ → *Strategy aus JSON laden*
  - File Dialog (*.json)
  - JSON-Validierung
  - Pattern Canvas laden
  - Workflows laden (4 Tabs)

- [ ] **2.3.4 Save Strategy & Save As**
  Status: ⬜ → *Strategy speichern*
  - Aktuellen File-Path verwenden
  - Save As: File Dialog
  - Metadata aktualisieren (modified timestamp)
  - Statusbar Feedback

- [ ] **2.3.5 Export JSON RulePack**
  Status: ⬜ → *Export für CEL Engine*
  - Konvertiere zu RulePack-Format
  - File Dialog (*.json)
  - Validierung vor Export

### 2.4 Pattern → CEL Translation (4-6 Stunden)
- [ ] **2.4.1 PatternToCelTranslator Klasse**
  Status: ⬜ → *Neue Datei: pattern_to_cel.py*
  - Candle-Type → CEL Conditions
  - Relations → CEL Operators
  - 8 Kerzentypen unterstützen
  - 4 Relations-Typen unterstützen

- [ ] **2.4.2 Candle Type Mapping**
  Status: ⬜ → *8 Typen zu CEL*
  - Bullish, Bearish, Doji, Hammer, etc.
  - Formula: `candle(index).type == "type"`
  - Tests für alle Typen

- [ ] **2.4.3 Relation Mapping**
  Status: ⬜ → *4 Relations zu Operatoren*
  - greater: `>`
  - less: `<`
  - equal: `==`
  - near: `~=` (custom)
  - Tests mit verschiedenen Fields (high, low, close, etc.)

- [ ] **2.4.4 "Generate CEL" Button**
  Status: ⬜ → *UI Integration*
  - Button in Pattern Canvas Toolbar
  - Generiere CEL aus aktuellem Pattern
  - Füge in Entry-Workflow Tab ein
  - User Feedback (Toast/Statusbar)

---

## Phase 3: CEL Editor - Advanced Features (12-15 Stunden)

### 3.1 Chart View Integration (6-8 Stunden)
- [ ] **3.1.1 TradingView Chart Widget**
  Status: ⬜ → *Chart Placeholder ersetzen*
  - Import: `TradingViewChartWidget`
  - Integration in `central_stack`
  - Initial Chart Data laden

- [ ] **3.1.2 Pattern Overlay System**
  Status: ⬜ → *Pattern auf Chart zeichnen*
  - Pattern Canvas → Chart Shapes
  - Sync bei Pattern-Änderungen
  - Signal: `pattern_changed.connect()`

- [ ] **3.1.3 Chart Events Handling**
  Status: ⬜ → *Hover, Click, Zoom*
  - Hover: Candle-Info anzeigen
  - Click: Candle auswählen
  - Zoom/Pan: Synchronisation mit Pattern

- [ ] **3.1.4 Split View Synchronisation**
  Status: ⬜ → *Pattern ↔ Chart Sync*
  - Scroll-Position synchronisieren
  - Zoom-Level synchronisieren
  - Selection synchronisieren

### 3.2 Pattern Library (4-5 Stunden)
- [ ] **3.2.1 PatternLibrary Widget**
  Status: ⬜ → *Neue Datei: pattern_library.py*
  - QListWidget mit Pattern-Templates
  - Kategorien: Reversal, Continuation, Indecision
  - Thumbnail-Preview

- [ ] **3.2.2 Vordefinierte Templates**
  Status: ⬜ → *JSON-Dateien für Templates*
  - Hammer, Shooting Star, Engulfing, etc.
  - JSON Format: gleich wie Strategy
  - 15-20 Standard-Patterns

- [ ] **3.2.3 Drag & Drop aus Library**
  Status: ⬜ → *Library → Canvas*
  - QDrag Event Handling
  - Pattern einfügen bei Drop
  - Position anpassen

- [ ] **3.2.4 Custom Pattern speichern**
  Status: ⬜ → *User-Patterns in Library*
  - "Save to Library" Button
  - Name & Beschreibung Dialog
  - Speichern in User-Library Folder

### 3.3 AI Assistant Panel (2-3 Stunden)
- [ ] **3.3.1 AI Assistant Dock Widget**
  Status: ⬜ → *Rechtes Panel erstellen*
  - QDockWidget mit Chat-Interface
  - Persistent Position (QSettings)
  - Toggle-Action in Menu

- [ ] **3.3.2 Pattern Suggestions**
  Status: ⬜ → *AI schlägt Pattern vor basierend auf Code*
  - Input: CEL Code
  - Output: Pattern-JSON
  - "Apply Suggestion" Button

- [ ] **3.3.3 Code Suggestions**
  Status: ⬜ → *AI schlägt Code vor basierend auf Pattern*
  - Input: Pattern-JSON
  - Output: CEL Code
  - Mehrere Varianten anbieten

- [ ] **3.3.4 Error Explanations**
  Status: ⬜ → *AI erklärt Validation-Errors*
  - Input: Validation Error
  - Output: Erklärung + Fix-Vorschlag
  - "Apply Fix" Button

---

## Phase 4: Testing & Validation (10-12 Stunden)

### 4.1 Unit Tests (6-7 Stunden)
- [ ] **4.1.1 cel_engine.py Tests**
  Status: ⬜ → *Alle neuen Funktionen testen*
  - Tests für alle 1.1-1.4 Funktionen
  - Edge Cases (null, NaN, Division-by-Zero)
  - Performance Tests (Caching)

- [ ] **4.1.2 pattern_to_cel.py Tests**
  Status: ⬜ → *Translation Tests*
  - Alle 8 Candle-Typen
  - Alle 4 Relations
  - Komplexe Multi-Candle Patterns

- [ ] **4.1.3 cel_validator.py Tests**
  Status: ⬜ → *Validation Tests*
  - Valid CEL Expressions
  - Invalid Syntax
  - Unknown Functions
  - Type Errors

- [ ] **4.1.4 File Operations Tests**
  Status: ⬜ → *JSON Save/Load Tests*
  - Round-trip Test (Save → Load)
  - Invalid JSON Handling
  - Schema Validation

### 4.2 Integration Tests (3-4 Stunden)
- [ ] **4.2.1 Pattern → CEL → Evaluation**
  Status: ⬜ → *End-to-End Test*
  - Pattern Builder → Generate CEL
  - CEL Code → Validation
  - Evaluation mit Test-Context

- [ ] **4.2.2 AI Code Generation → Validation**
  Status: ⬜ → *AI Integration Test*
  - AI generiert CEL Code
  - Validation prüft Code
  - Code ist ausführbar

- [ ] **4.2.3 File Operations → UI Update**
  Status: ⬜ → *UI Integration Test*
  - Save → Load
  - UI zeigt korrekte Daten
  - Alle 4 Workflow-Tabs gefüllt

### 4.3 Performance & Stress Tests (1-2 Stunden)
- [ ] **4.3.1 CEL Cache Performance**
  Status: ⬜ → *Cache Hit-Rate messen*
  - 1000 Evaluations
  - Cache Hit-Rate > 90%
  - Performance-Regression Test

- [ ] **4.3.2 Large Pattern Handling**
  Status: ⬜ → *50+ Candles im Pattern*
  - Rendering Performance
  - CEL Generation < 1s
  - UI bleibt responsive

---

## Phase 5: Dokumentation & Finalisierung (6-8 Stunden)

### 5.1 Dokumentation Updates (4-5 Stunden)
- [ ] **5.1.1 CEL_Befehle_Liste_v3.md**
  Status: ⬜ → *Vollständig aktualisierte Doku*
  - ALLE implementierten Funktionen
  - Operator Precedence Tabelle
  - Error-Handling Sektion
  - Performance-Hinweise (Caching)

- [ ] **5.1.2 Regime Erkennung JSON Template Rules v2.1.md**
  Status: ⬜ → *Korrigierte Evaluierungslogik*
  - Threshold → Condition Mapping
  - CEL-Support in Regimes
  - RegimeScope.GLOBAL

- [ ] **5.1.3 CEL_JSON_INTEGRATION.md**
  Status: ⬜ → *Neue Integrations-Dokumentation*
  - Workflow-Diagramm
  - Threshold-Syntax Mapping
  - Code-Beispiele

- [ ] **5.1.4 CEL_Editor_Benutzerhandbuch.md**
  Status: ⬜ → *User Guide für Editor*
  - Quick Start Guide
  - Feature-Übersicht
  - Workflow-Beispiele
  - Troubleshooting

### 5.2 Code-Cleanup & Finalisierung (2-3 Stunden)
- [ ] **5.2.1 Dead Code Removal**
  Status: ⬜ → *Alte Kommentare & TODOs entfernen*
  - Alle TODO-Kommentare beseitigen
  - Auskommentierter Code löschen
  - Unused Imports entfernen

- [ ] **5.2.2 Code-Review Checklist**
  Status: ⬜ → *Finale Code-Qualitätsprüfung*
  - Alle Type Hints vorhanden
  - Alle Docstrings vollständig
  - Logging konsistent
  - Error Messages aussagekräftig

- [ ] **5.2.3 Performance Profiling**
  Status: ⬜ → *Performance Bottlenecks identifizieren*
  - CEL Evaluation < 1ms
  - Pattern Rendering < 100ms
  - File Operations < 500ms

---

## 📈 Fortschritts-Tracking

### Gesamt-Statistik
- **Total Tasks:** 89
- **Abgeschlossen:** 0 (0%)
- **In Arbeit:** 0 (0%)
- **Offen:** 89 (100%)

### Phase-Statistik
| Phase | Tasks | Abgeschlossen | Fortschritt | Geschätzte Zeit |
|-------|-------|---------------|-------------|-----------------|
| Phase 0 | 9 | 0 | ⬜ 0% | 8-10h |
| Phase 1 | 20 | 0 | ⬜ 0% | 20-25h |
| Phase 2 | 17 | 0 | ⬜ 0% | 18-22h |
| Phase 3 | 13 | 0 | ⬜ 0% | 12-15h |
| Phase 4 | 10 | 0 | ⬜ 0% | 10-12h |
| Phase 5 | 7 | 0 | ⬜ 0% | 6-8h |

### Zeitschätzung
- **Geschätzte Gesamtzeit:** 74-92 Stunden (9-12 Arbeitstage @ 8h/Tag)
- **Bereits investiert:** 0 Stunden
- **Verbleibend:** 74-92 Stunden

---

## 🔥 Kritische Pfade

### Woche 1 (Phase 0 + Phase 1)
1. **Tag 1-2:** Dokumentations-Audit (0.1-0.3)
2. **Tag 3-4:** Mathematische Funktionen (1.1)
3. **Tag 5:** Status & Preis-Funktionen (1.2-1.3)

**Blocker:** Keine - Phase 0 ist unabhängig

### Woche 2 (Phase 2 + Start Phase 3)
1. **Tag 1:** Zeit-Funktionen (1.4) + AI Integration Start (2.1)
2. **Tag 2-3:** CEL Validation Backend (2.2)
3. **Tag 4:** File Operations (2.3)
4. **Tag 5:** Pattern → CEL Translation (2.4)

**Blocker:** 2.2 blockiert 2.4 (Validation muss vor Translation)

### Woche 3 (Phase 3 + Phase 4)
1. **Tag 1-2:** Chart View Integration (3.1)
2. **Tag 3:** Pattern Library (3.2)
3. **Tag 4:** AI Assistant Panel (3.3)
4. **Tag 5:** Unit Tests (4.1)

**Blocker:** 3.1 benötigt 2.4 (Pattern → CEL)

### Woche 4 (Phase 4 + Phase 5)
1. **Tag 1:** Integration Tests (4.2)
2. **Tag 2:** Performance Tests (4.3)
3. **Tag 3-4:** Dokumentation (5.1)
4. **Tag 5:** Code Cleanup & Release (5.2)

**Blocker:** 5.1 benötigt alle Features (Phase 1-3)

---

## 📝 Risiken & Mitigation

### Identifizierte Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| **CEL Validation Komplexität** | 🔴 Hoch | 🔴 Hoch | Schrittweise Implementation, Web-Recherche zu AST-Parsern |
| **Pattern → CEL Translation Edge Cases** | 🟠 Mittel | 🟠 Mittel | Umfassende Unit Tests, Fallback auf manuelle Eingabe |
| **AI API Kosten** | 🟡 Niedrig | 🟡 Niedrig | Rate Limiting, Caching von AI-Responses |
| **Chart View Performance** | 🟠 Mittel | 🟠 Mittel | Virtualisierung, Lazy Loading von Candles |
| **Zeit-Funktionen Timezone Issues** | 🟡 Niedrig | 🟠 Mittel | UTC als Standard, explizite Timezone-Handling |

### Mitigation Strategies

1. **CEL Validation:** Nutze bestehende CEL-Libs (cel-python), inkrementelle Features
2. **Performance:** Profiling nach jedem Feature, Optimization als Task
3. **API Kosten:** Monitoring, User-Warning bei hoher Usage
4. **Testing:** Test-First Approach für kritische Features

---

## 🎯 Qualitätsziele

### Performance Targets
- **CEL Evaluation:** <1ms (mit Cache <0.1ms)
- **Pattern Canvas:** <100ms Rendering (50 Candles)
- **File Operations:** <500ms Save/Load
- **AI Code Generation:** <5s (Cloud API)
- **Chart View:** >30fps bei Pan/Zoom

### Quality Targets
- **Code Coverage:** >85% (Unit Tests)
- **CEL Function Coverage:** 100% (alle dokumentierten Funktionen)
- **Error Handling:** 100% (kein Silent Failure)
- **Documentation:** 100% (alle Public APIs)
- **Type Hints:** 100% (alle Functions)

---

## 📄 Review Checkpoints

### End of Week 1 (Phase 0-1)
- [ ] Dokumentation vollständig aktualisiert
- [ ] Alle CEL Core-Funktionen implementiert
- [ ] Unit Tests für CEL Engine >80% Coverage
- [ ] Performance: Evaluation <1ms

### End of Week 2 (Phase 2)
- [ ] AI Integration (alle 3 Provider) funktional
- [ ] CEL Validation mit Live-Feedback
- [ ] File Operations (Save/Load) funktional
- [ ] Pattern → CEL Translation funktional

### End of Week 3 (Phase 3)
- [ ] Chart View mit Pattern Overlay
- [ ] Pattern Library mit 15+ Templates
- [ ] AI Assistant Panel funktional
- [ ] Integration Tests >90% passed

### End of Week 4 (Phase 4-5)
- [ ] Alle Tests passed (Unit + Integration)
- [ ] Performance Targets erreicht
- [ ] Dokumentation vollständig
- [ ] Code Cleanup abgeschlossen
- [ ] **READY FOR PRODUCTION** ✅

---

## 🚀 Best Practices (aus Web-Recherche)

### CEL Implementation Best Practices

**Quelle:** [CEL.dev](https://cel.dev/), [Google CEL Spec](https://github.com/google/cel-spec)

1. **Validation Workflow:**
   - Parse → Check → Evaluate (3-Step Process)
   - Type-Checking BEVOR Evaluation
   - AST-Caching für Performance

2. **Performance:**
   - CEL evaluiert in **linearer Zeit** (O(n))
   - **Nicht Turing-complete** (keine Endlosschleifen)
   - Cache-Strategie: 128-256 Expressions optimal

3. **Security:**
   - Bounded Execution (kein Timeout nötig)
   - Mutation-free (keine Side-Effects)
   - Safe für User-Input

4. **Use Cases:**
   - Kubernetes: Validation Rules
   - Google Cloud: Certificate Identity Constraints
   - Firebase: Access Rules

### Implementation Learnings

1. **Type Conversion:**
   ```python
   # CEL erwartet celpy.celtypes, nicht Python natives
   context = _to_cel_types({"atrp": 0.6})  # BoolType, IntType, etc.
   result = _to_python_type(cel_result)    # Zurück zu Python
   ```

2. **Custom Functions:**
   ```python
   # Functions als Dict in Environment registrieren
   functions = {'pctl': _func_pctl, 'crossover': _func_crossover}
   program = env.program(ast, functions=functions)
   ```

3. **Error Handling:**
   ```python
   # Compilation-Errors: ValueError
   # Evaluation-Errors: RuntimeError mit default-Fallback
   result = engine.evaluate(expr, context, default=False)
   ```

---

## 🤝 Claude-Flow Integration

Dieses Projekt wird durch spezialisierte Agenten koordiniert:

```bash
npx claude-flow@alpha hive-mind spawn \
  "CEL System 100% Fertigstellung - OrderPilot-AI" \
  --agents "queen-orchestrator,architect-1,coder-backend,coder-frontend,cel-specialist,ui-developer,tester-1,documenter-1" \
  --tools "mcp_filesystem,code_executor,test_runner,terminal" \
  --mode "sequential-phases" \
  --claude \
  --verbose \
  --output ".AI_Exchange/cel_system_fertigstellung"
```

### Agent-Rollen:
- **queen-orchestrator:** Zentrale Koordination, Phase-Management
- **architect-1:** CEL Engine Architecture, Performance-Optimierung
- **coder-backend:** CEL Engine Implementation (Phase 1)
- **coder-frontend:** CEL Editor UI (Phase 2-3)
- **cel-specialist:** CEL Validation, AST-Parsing, Best Practices
- **ui-developer:** Qt/QScintilla Integration, Pattern Canvas
- **tester-1:** Unit/Integration Tests, Performance Tests
- **documenter-1:** Dokumentation (Phase 0, Phase 5)

---

## 📚 Referenzen

### Code-Dateien
- `src/core/tradingbot/cel_engine.py` - CEL Engine Core (427 LOC)
- `src/core/tradingbot/config/evaluator.py` - Condition Evaluator
- `src/ui/windows/cel_editor/main_window.py` - CEL Editor Main Window
- `src/ui/widgets/cel_ai_helper.py` - AI Integration
- `src/ui/widgets/pattern_builder/pattern_canvas.py` - Pattern Builder

### Dokumentation
- `04_Knowledgbase/CEL_Befehle_Liste_v2.md` - CEL Funktions-Referenz
- `04_Knowledgbase/Regime Erkennung JSON Template Rules Regime.md` - Regime Config
- `01_Projectplan/260127_Fertigstellung CEL Editor/2_Implementierungsplan_CEL_Editor_Features.md` - CEL Editor Plan

### Externe Referenzen
- [CEL Specification](https://github.com/google/cel-spec) - Google CEL Spec
- [cel-python](https://pypi.org/project/cel-python/) - Python Implementation
- [Kubernetes CEL](https://kubernetes.io/docs/reference/using-api/cel/) - K8s Usage
- [Google Cloud CEL](https://docs.cloud.google.com/certificate-authority-service/docs/using-cel) - GCP Usage

---

**Erstellt:** 2026-01-27
**Version:** 1.0
**Status:** Ready for Implementation ✅
**Nächste Review:** Nach Phase 0 (Woche 1)
