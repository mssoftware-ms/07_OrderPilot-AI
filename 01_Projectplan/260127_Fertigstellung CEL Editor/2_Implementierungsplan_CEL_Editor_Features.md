# 🚀 IMPLEMENTIERUNGSPLAN - Fehlende CEL Editor Features

**Datum:** 2026-01-21
**Aktualisiert:** 2026-01-27
**CEL Editor Status:** ✅ Läuft (4,125 LOC, 5.3% der Codebasis)
**Fehlende Features:** 20 (40% der Planung)
**Geschätzte Gesamtzeit:** 55-80 Stunden (7-10 Arbeitstage)

---

## ⚠️ WICHTIG: Vollständiger Umsetzungsplan verfügbar

**Dieser Plan fokussiert sich nur auf CEL Editor UI-Features.**

Für die **100% Fertigstellung des gesamten CEL Systems** (inkl. CEL Engine Funktionen, Dokumentation, Tests) siehe:
📄 **`3_Umsetzungsplan_CEL_System_100_Prozent.md`**

Der vollständige Plan umfasst:
- **Phase 0:** Dokumentations-Audit (8-10h)
- **Phase 1:** CEL Engine - 20 fehlende Core-Funktionen (20-25h)
- **Phase 2:** CEL Editor - UI Features (18-22h) ← *Dieser Plan*
- **Phase 3:** Advanced Features (12-15h)
- **Phase 4:** Testing & Validation (10-12h)
- **Phase 5:** Dokumentation & Finalisierung (6-8h)

**Gesamt:** 74-92 Stunden (9-12 Arbeitstage)

---

## Übersicht

### Was bereits funktioniert (60%)
✅ Pattern Builder (95%): Drag & Drop, Undo/Redo, 8 Kerzentypen, Properties
✅ CEL Code Editor (85%): Syntax Highlighting, Autocomplete, 4 Workflows
✅ View-Switching: 4 Modi (Pattern, Code, Chart Placeholder, Split)
✅ OpenAI AI Integration: GPT-5.x für Code-Generierung

### Was fehlt (40%)
❌ Anthropic/Gemini AI Integration
❌ CEL Validation Backend
❌ File Operations (Save/Load/Export)
❌ Pattern → CEL Translation
❌ Chart View (nur Placeholder)
❌ Pattern Library
❌ AI Assistant Panel
❌ 13 weitere Features

---

## SOFORT (CRITICAL) - App stabilisieren

### Feature 1: ✅ Import-Fehler behoben
**Status:** ✅ Erledigt durch Benutzer
**Datei:** `src/ui/windows/cel_editor/main_window.py:24`
**Zeit:** 5 Minuten
**Impact:** App startet jetzt

---

## KURZFRISTIG (HIGH) - Kernfunktionalität (20-25h)

### Feature 2: Anthropic Claude AI Integration

**Datei:** `src/ui/widgets/cel_ai_helper.py`
**Status:** Code vorbereitet, nur SDK fehlt
**Aufwand:** 2-3 Stunden
**Priorität:** 🟠 HIGH

#### Implementation

```python
# In _generate_code_anthropic():
import anthropic

client = anthropic.Anthropic(api_key=self.anthropic_api_key)
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{"role": "user", "content": prompt}]
)
return message.content[0].text
```

#### Abhängigkeiten
```bash
pip install anthropic
```

#### Test
1. Anthropic API Key in Umgebungsvariable setzen
2. AI Generate Button testen mit "Calculate RSI > 70"
3. Prüfen: CEL Code wird generiert

---

### Feature 3: Google Gemini AI Integration

**Datei:** `src/ui/widgets/cel_ai_helper.py`
**Status:** Code vorbereitet, nur SDK fehlt
**Aufwand:** 2-3 Stunden
**Priorität:** 🟠 HIGH

#### Implementation

```python
# In _generate_code_gemini():
import google.generativeai as genai

genai.configure(api_key=self.gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content(prompt)
return response.text
```

#### Abhängigkeiten
```bash
pip install google-generativeai
```

---

### Feature 4: CEL Validation Backend

**Neue Datei:** `src/ui/widgets/cel_validator.py`
**Status:** Button vorhanden, kein Backend
**Aufwand:** 4-6 Stunden
**Priorität:** 🟠 HIGH (Risiko: 🔴 Hoch)

#### Anforderungen
- CEL Syntax Parser (Lexer bereits vorhanden)
- AST-basierte Validierung
- Error Markers im Editor (QScintilla)
- Live-Validierung (onChange mit Debounce 500ms)

#### Implementation Sketch

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ValidationError:
    line: int
    column: int
    message: str
    severity: str  # 'error' | 'warning' | 'info'

class CelValidator:
    def __init__(self):
        self.lexer = CelLexer()  # Bereits vorhanden

    def validate(self, code: str) -> List[ValidationError]:
        """Validate CEL code and return errors."""
        errors = []

        # 1. Lexer-basierte Token-Prüfung
        tokens = self.lexer.tokenize(code)
        errors.extend(self._validate_tokens(tokens))

        # 2. Syntax-Prüfung (Klammern, Operatoren)
        errors.extend(self._validate_syntax(code))

        # 3. Semantik-Prüfung (Funktionen existieren?)
        errors.extend(self._validate_semantics(tokens))

        # 4. Type-Checking (wo möglich)
        errors.extend(self._validate_types(tokens))

        return errors

    def _validate_tokens(self, tokens: List) -> List[ValidationError]:
        # Prüfe auf unbekannte Tokens
        pass

    def _validate_syntax(self, code: str) -> List[ValidationError]:
        # Prüfe Klammern, Operatoren, Semikolons
        pass

    def _validate_semantics(self, tokens: List) -> List[ValidationError]:
        # Prüfe ob Funktionen/Indikatoren existieren
        pass

    def _validate_types(self, tokens: List) -> List[ValidationError]:
        # Einfaches Type-Checking
        pass
```

#### Integration in Editor

```python
# In CelEditorWidget:
def setup_validation(self):
    self.validator = CelValidator()
    self.validation_timer = QTimer()
    self.validation_timer.setSingleShot(True)
    self.validation_timer.timeout.connect(self._run_validation)

    # Trigger validation on text change (debounced)
    self.textChanged.connect(lambda: self.validation_timer.start(500))

def _run_validation(self):
    code = self.text()
    errors = self.validator.validate(code)
    self._show_error_markers(errors)

def _show_error_markers(self, errors: List[ValidationError]):
    # Clear old markers
    self.clearAnnotations()

    # Add new markers
    for error in errors:
        if error.severity == 'error':
            self.annotate(error.line, error.message,
                         style=QsciScintilla.ErrorAnnotation)
```

---

### Feature 5: File Operations (Save/Load/Export)

**Datei:** `src/ui/windows/cel_editor/main_window.py`
**Status:** Nur Placeholder-Meldungen
**Aufwand:** 3-4 Stunden
**Priorität:** 🟠 HIGH

#### JSON Schema

```json
{
  "schema_version": "1.0",
  "metadata": {
    "created": "2026-01-21T10:30:00Z",
    "modified": "2026-01-21T14:20:00Z",
    "author": "OrderPilot-AI"
  },
  "pattern": {
    "candles": [...],
    "relations": [...]
  },
  "workflows": {
    "entry": "CEL code...",
    "exit": "CEL code...",
    "before_exit": "CEL code...",
    "update_stop": "CEL code..."
  }
}
```

#### Implementation

```python
def _new_strategy(self):
    """Create new strategy (clear all editors)."""
    # Confirm unsaved changes
    if self.has_unsaved_changes():
        reply = QMessageBox.question(self, "Unsaved Changes",
                                     "Discard unsaved changes?")
        if reply != QMessageBox.Yes:
            return

    # Clear all editors
    self.pattern_canvas.clear()
    self.code_editor.clear_all()
    self.current_file = None
    self.statusBar().showMessage("New strategy created", 3000)

def _open_strategy(self):
    """Load strategy from JSON file."""
    file_path, _ = QFileDialog.getOpenFileName(
        self, "Open Strategy", "",
        "CEL Strategy (*.json);;All Files (*)"
    )
    if not file_path:
        return

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Validate schema
        if data.get('schema_version') != '1.0':
            raise ValueError("Unsupported schema version")

        # Load pattern
        self.pattern_canvas.from_json(data['pattern'])

        # Load workflows
        workflows = data['workflows']
        self.code_editor.set_entry_code(workflows.get('entry', ''))
        self.code_editor.set_exit_code(workflows.get('exit', ''))
        self.code_editor.set_before_exit_code(workflows.get('before_exit', ''))
        self.code_editor.set_update_stop_code(workflows.get('update_stop', ''))

        self.current_file = file_path
        self.statusBar().showMessage(f"Loaded: {file_path}", 3000)

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load: {e}")

def _save_strategy(self):
    """Save strategy to current file."""
    if not self.current_file:
        return self._save_strategy_as()

    try:
        data = {
            "schema_version": "1.0",
            "metadata": {
                "created": self.creation_time.isoformat(),
                "modified": datetime.now().isoformat(),
                "author": "OrderPilot-AI"
            },
            "pattern": self.pattern_canvas.to_json(),
            "workflows": {
                "entry": self.code_editor.get_entry_code(),
                "exit": self.code_editor.get_exit_code(),
                "before_exit": self.code_editor.get_before_exit_code(),
                "update_stop": self.code_editor.get_update_stop_code()
            }
        }

        with open(self.current_file, 'w') as f:
            json.dump(data, f, indent=2)

        self.statusBar().showMessage(f"Saved: {self.current_file}", 3000)

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to save: {e}")

def _save_strategy_as(self):
    """Save strategy to new file."""
    file_path, _ = QFileDialog.getSaveFileName(
        self, "Save Strategy As", "",
        "CEL Strategy (*.json);;All Files (*)"
    )
    if not file_path:
        return

    self.current_file = file_path
    self._save_strategy()

def _export_json_rulepack(self):
    """Export as RulePack JSON (für CEL Engine)."""
    file_path, _ = QFileDialog.getSaveFileName(
        self, "Export RulePack", "",
        "RulePack JSON (*.json);;All Files (*)"
    )
    if not file_path:
        return

    # TODO: Convert to RulePack format
    QMessageBox.information(self, "Export", "RulePack export not implemented yet")
```

---

### Feature 6: Pattern → CEL Translation

**Neue Datei:** `src/ui/widgets/pattern_builder/pattern_to_cel.py`
**Status:** Nicht vorhanden
**Aufwand:** 6-8 Stunden
**Priorität:** 🟠 HIGH (Risiko: 🔴 Hoch)

#### Anforderungen
- Pattern JSON → CEL Code Generator
- 8 Kerzentypen → CEL Conditions
- 4 Relationstypen → CEL Operators (>, <, ≈, ~)
- Button "Generate CEL from Pattern"

#### Beispiel-Translation

**Pattern:**
```json
{
  "candles": [
    {"index": -2, "type": "bullish"},
    {"index": -1, "type": "bearish"}
  ],
  "relations": [
    {"from": -1, "to": -2, "type": "greater", "field": "high"}
  ]
}
```

**Generated CEL:**
```cel
candle(-2).type == "bullish" and
candle(-1).type == "bearish" and
candle(-1).high > candle(-2).high
```

#### Implementation

```python
class PatternToCelTranslator:
    RELATION_OPERATORS = {
        'greater': '>',
        'less': '<',
        'equal': '==',
        'near': '~='  # Custom operator
    }

    def translate(self, pattern_json: dict) -> str:
        """Translate pattern JSON to CEL code."""
        conditions = []

        # 1. Candle type conditions
        for candle in pattern_json['candles']:
            cond = f'candle({candle["index"]}).type == "{candle["type"]}"'
            conditions.append(cond)

        # 2. Relation conditions
        for rel in pattern_json.get('relations', []):
            from_idx = rel['from']
            to_idx = rel['to']
            op = self.RELATION_OPERATORS[rel['type']]
            field = rel['field']

            cond = f'candle({from_idx}).{field} {op} candle({to_idx}).{field}'
            conditions.append(cond)

        # Join with 'and'
        return ' and\n'.join(conditions)
```

---

### Feature 7: Chart View Implementation

**Datei:** `src/ui/windows/cel_editor/main_window.py`
**Status:** Nur QLabel Placeholder
**Aufwand:** 6-8 Stunden
**Priorität:** 🟠 HIGH (Risiko: 🟠 Mittel)

#### Integration

```python
from ...widgets.embedded_tradingview_chart_ui_mixin import TradingViewChartWidget

# In __init__:
self.chart_view = TradingViewChartWidget(self)
self.central_stack.addWidget(self.chart_view)  # Statt QLabel

# Pattern Overlay auf Chart
self.chart_view.set_pattern(self.pattern_canvas.to_json())
self.pattern_canvas.pattern_changed.connect(
    lambda: self.chart_view.set_pattern(self.pattern_canvas.to_json())
)
```

#### Pattern Overlay Features
- Pattern Canvas Kerzen → Chart zeichnen
- Sync zwischen Pattern Builder ↔ Chart
- Hover/Click Events
- Zoom/Pan Synchronisation

---

## MITTELFRISTIG (MEDIUM) - UX Features (15-20h)

### Feature 8: Pattern Library
**Neue Datei:** `src/ui/widgets/pattern_builder/pattern_library.py`
**Aufwand:** 4-5 Stunden
**Priorität:** 🟡 MEDIUM

#### Features
- Vordefinierte Pattern Templates
- Kategorien: Reversal, Continuation, Indecision
- Drag & Drop aus Library → Canvas
- Custom Pattern speichern

---

### Feature 9: Relation Drawing UI
**Datei:** `src/ui/widgets/pattern_builder/pattern_canvas.py`
**Aufwand:** 3-4 Stunden
**Priorität:** 🟡 MEDIUM

#### Aktuell
Relationen nur via `add_relation()` API

#### Ziel
Drag-Mechanismus (Candle A → Candle B)

---

### Feature 10: AI Assistant Panel
**Datei:** `src/ui/windows/cel_editor/main_window.py`
**Aufwand:** 4-6 Stunden
**Priorität:** 🟡 MEDIUM

#### Features
- Rechtes Dock Widget "AI Assistant"
- Pattern Suggestions basierend auf Code
- Code Suggestions basierend auf Pattern
- Error Explanations

---

### Features 11-12
- Split View Synchronisation (2-3h)
- JSON RulePack Integration (3-4h)

---

## LANGFRISTIG (LOW) - Nice-to-have (10-15h)

### Features 13-20
- Undo/Redo im CEL Editor
- Multi-Candle Operations (Copy/Paste)
- Pattern Statistics Panel
- Help & Documentation Dialog
- Properties Panel Live-Update
- CEL → Pattern Reverse Engineering
- Unit Tests für CEL Editor
- Integration Tests

---

## Zeitplan (40h Woche)

### Woche 1 (KW 04)
```
Mo: Dead Code + Kommentare (3-4h)
Di: Entry Analyzer Refactoring (8h)
Mi: Entry Analyzer Refactoring (8h)
Do: CEL Validation Backend (6h)
Fr: File Operations (4h) + Testing (4h)
```

### Woche 2 (KW 05)
```
Mo: Anthropic/Gemini AI (6h)
Di: Pattern → CEL Translation (8h)
Mi: Pattern → CEL Translation (8h)
Do: Chart View Implementation (8h)
Fr: Pattern Library (4h) + Relation UI (4h)
```

### Woche 3 (KW 06)
```
Mo-Di: AI Assistant Panel (8h)
Mi: Split View Sync (3h) + RulePack (4h)
Do-Fr: Testing, Bugfixing, Docs (16h)
```

---

**Status:** Ready for Implementation ✅
