# 🚀 Antigravity AI Toolkit v2.0

Portables AI Agent System für strukturiertes Coding in großen Projekten.
**Multi-Stack-kompatibel:** PyQt, React, Next.js, Django, Tauri, und mehr.

## Quick Start

### Control Center starten
```batch
.antigravity\antigravity.bat
```

### Workflow (empfohlene Reihenfolge)

| Schritt | Taste | Beschreibung |
|---------|-------|--------------|
| 1. Context | `[C]` | Generiert AI-Context (rules + ai_docs + structure) |
| 2. Structure | `[M]` | Nur Code-Struktur (AST-basiert, token-effizient) |
| 3. Repomix | `[R]` | Vollständiger Code-Dump (50k+ Tokens) |
| 4. Verify | `[V]` | Lint + Type-Check + Tests |

### Scoped Verify Targets (Standard)

`ai-verify` akzeptiert Ziel-Scopes über Environment-Variablen, um große Testläufe zu verkürzen:

- `AG_LINT_TARGETS` (Fallback: `LINT_TARGETS`)
- `AG_TEST_TARGETS` (Fallback: `TEST_TARGETS`)

Beispiel:
```bash
AG_LINT_TARGETS="src/core/market_data" \
AG_TEST_TARGETS="tests/core/market_data/test_bad_tick_detection_integration.py" \
./scripts/ai-verify.sh
```

Hinweis: Wenn `AG_TEST_TARGETS` gesetzt ist, überschreibt es modul-spezifische Arguments.

## Neue Struktur (v2.0)

```
.antigravity/
├── core/                           # Stack-Detection & Lazy Loading
│   ├── __init__.py
│   └── environment.py              # Erkennt PyQt, React, Django, etc.
├── drivers/                        # UI-Abstraktion (Multi-Framework)
│   ├── __init__.py
│   ├── base.py                     # Einheitliches Protocol
│   └── pyqt_driver.py              # PyQt6/5, PySide6/2
├── analyzers/                      # Code-Analyse Tools
│   ├── __init__.py
│   └── structure_mapper.py         # AST → Signaturen (~3k Tokens)
├── agents/                         # Spezialisierte Rollen
│   ├── orchestrator.md             # Koordination (§1, §7)
│   ├── developer.md                # Implementation (§2, §3)
│   ├── qa-expert.md                # Verifikation (§5)
│   ├── architect.md                # Architektur-Prüfung
│   ├── researcher.md               # Context-Sammlung
│   ├── ui-specialist.md            # PyQt Layout & Styling
│   └── state-manager.md            # Race Conditions
├── scripts/
│   ├── context.py                  # NEU: Unified Context Generator
│   ├── ai-verify.py                # Auto-Detection Verify
│   ├── ai-verify.sh                # WSL Wrapper
│   ├── generate-context.sh         # Repomix Wrapper
│   ├── generate-context.bat
│   └── setup-wsl.sh                # venv + Tools Setup
├── templates/
│   ├── bug-report.md
│   ├── crisp-prompt.md
│   └── pyqt/                       # Lazy Loading (kein Crash in Web!)
│       ├── __init__.py
│       └── ui_inspector.py
├── guides/
│   └── ui-inspector-setup.md
├── context/                        # Output (auto-generiert)
│   ├── ai-context.md               # Unified Context Packet
│   ├── structure.md                # Code-Struktur
│   └── codebase-context.txt        # Repomix Output
├── rules                           # Das Grundgesetz (§1-§7)
├── antigravity.bat                 # Control Center v2.0
├── deploy-to-projects.bat          # Force-Deploy zu allen Projekten
└── README.md                       # Diese Datei
```

## Das Grundgesetz

```
§1 [Planung]: Erst Plan (3-7 Schritte), dann Code.
§2 [Search]: Erst rg/grep, dann Änderung.
§3 [Atomic]: Patches müssen klein und einzeln testbar sein.
§4 [Kommunikation]: Max. 5 Fragen. Annahmen explizit markieren.
§5 [QA]: Kein Merge ohne Verify-Script Durchlauf.
§6 [Safety]: Keine Secrets, keine destruktiven Aktionen ohne Erlaubnis.
§7 [Hierarchie]: Orchestrator plant, Dev codet, QA prüft.
```

## Stack-Detection

Die `core/environment.py` erkennt automatisch:

| Stack | Marker |
|-------|--------|
| PyQt6/5 | `requirements.txt` oder `pyproject.toml` |
| PySide6/2 | `requirements.txt` oder `pyproject.toml` |
| React | `package.json` mit `"react"` |
| Next.js | `next.config.js` oder `next.config.mjs` |
| Django | `manage.py` |
| Tauri | `tauri.conf.json` oder `src-tauri/` |

## Context-Generierung

### Quick Context (für tägliche Arbeit)
```bash
python .antigravity/scripts/context.py --quick
# Output: ai-context.md (rules + ai_docs, ~500 Tokens)
```

### Full Context (mit Code-Struktur)
```bash
python .antigravity/scripts/context.py
# Output: ai-context.md (rules + ai_docs + structure, ~3k Tokens)
```

### Structure Only (Token-effizient)
```bash
python .antigravity/scripts/context.py --structure-only
# Output: structure.md (nur Klassen/Methoden-Signaturen)
```

### Full Repomix (Deep Dive)
```bash
repomix --output .antigravity/context/codebase-context.txt
# Output: 50k+ Tokens vollständiger Code
```

## UI Inspector (PyQt)

1. Kopiere `templates/pyqt/ui_inspector.py` nach `src/ui/debug/`
2. Importiere und nutze das Mixin:
   ```python
   from src.ui.debug.ui_inspector import UIInspectorMixin

   class MainWindow(QMainWindow, UIInspectorMixin):
       def __init__(self):
           super().__init__()
           self.setup_ui_inspector()  # F12 aktivieren
   ```
3. Drücke **F12** → Hover über Elemente → Klick kopiert Pfad

## Agenten-Referenz

| Agent | Rolle | Wann nutzen |
|-------|-------|-------------|
| `orchestrator` | Koordination | Projektplanung, große Features |
| `developer` | Implementation | Code schreiben |
| `qa-expert` | Verifikation | Tests, Review |
| `architect` | Architektur | Dependency-Prüfung, SRP |
| `researcher` | Context | Vor großen Änderungen |
| `ui-specialist` | Layout | PyQt Widget-Arbeit |
| `state-manager` | Race Conditions | Flackernde UI |

## Migration von v1

Wenn du eine ältere Version hast:
1. Führe `[D] Deploy to all Projects` aus
2. Die neuen Module (`core/`, `drivers/`, `analyzers/`) werden automatisch kopiert
3. `antigravity.bat` hat jetzt v2.0 mit Workflow-Optionen (C, M, R, V)

---

**Maintained by:** OrderPilot-AI Team
**Version:** 2.0.0
