# VS Code Configuration for OrderPilot-AI

Diese Konfiguration ist optimiert für Python-Entwicklung mit WSL2, Trading-Anwendungen und Moltbot-Integration.

## 📦 Empfohlene Extensions

Die Datei `extensions.json` enthält alle empfohlenen Extensions. VS Code wird beim Öffnen des Projekts vorschlagen, diese zu installieren.

### Kern-Extensions (erforderlich)

| Extension | ID | Zweck |
|-----------|-----|-------|
| **Python** | `ms-python.python` | Python Language Support |
| **Pylance** | `ms-python.vscode-pylance` | Fast Python IntelliSense |
| **Ruff** | `charliermarsh.ruff` | Linting & Formatting |
| **Remote - WSL** | `ms-vscode-remote.remote-wsl` | WSL2 Development |

### Git & Version Control

| Extension | ID | Zweck |
|-----------|-----|-------|
| **GitLens** | `eamodio.gitlens` | Git Supercharge |
| **Git Graph** | `mhutchie.git-graph` | Visual Git History |
| **GitHub PR** | `github.vscode-pull-request-github` | Pull Request Management |

### Code Quality

| Extension | ID | Zweck |
|-----------|-----|-------|
| **Better Comments** | `aaron-bond.better-comments` | Kommentar-Highlighting |
| **Error Lens** | `usernamehw.errorlens` | Inline Error Display |
| **Code Spell Checker** | `streetsidesoftware.code-spell-checker` | Rechtschreibprüfung |

### File Formats

| Extension | ID | Zweck |
|-----------|-----|-------|
| **Even Better TOML** | `tamasfe.even-better-toml` | TOML Support |
| **YAML** | `redhat.vscode-yaml` | YAML Support |
| **Prettier** | `esbenp.prettier-vscode` | JSON/YAML Formatting |

## ⚙️ Settings Overview

### Python Konfiguration

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.wsl_venv/bin/python",
  "python.testing.pytestEnabled": true
}
```

- Virtual Environment: `.wsl_venv/` (WSL2-native)
- Python Version: 3.12.3
- Test Framework: pytest

### Linting & Formatting

**Ruff** wird verwendet für:
- Linting (ersetzt flake8, pylint)
- Formatting (ersetzt black)
- Import Sorting (ersetzt isort)

**Format on Save:** Aktiviert
**Auto-Fix on Save:** Aktiviert
**Organize Imports on Save:** Aktiviert

### Type Checking

**Pylance** mit `basic` Type Checking Mode:
- Auto-Import Completions
- Workspace-weite Diagnostics
- IntelliSense für Python 3.12+

### File Handling

**Line Endings:** LF (Unix-style)
- Wichtig für WSL2/Linux-Kompatibilität
- Git auto-conversion aktiviert

**Auto-Save:** Nach 1 Sekunde Verzögerung

**Exclude from Explorer:**
- `__pycache__/`, `*.pyc`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `.venv/`, `.wsl_venv/`

## 🚀 Launch Configurations

Verfügbare Debug-Konfigurationen (F5 → Auswählen):

### 1. Python: Current File
Führt die aktuell geöffnete Python-Datei aus.

**Use Case:** Schnelles Testen einzelner Skripte

### 2. Python: Trading Bot (Paper)
Startet den Trading Bot in Paper-Trading-Modus.

**Environment:**
- `TRADING_ENV=paper`
- `LOG_LEVEL=DEBUG`

**Use Case:** Bot-Entwicklung und Debugging

### 3. Python: Pytest Current File
Führt Tests in der aktuellen Datei aus.

**Use Case:** TDD Workflow, einzelne Testdateien debuggen

### 4. Python: Pytest All
Führt alle Tests im `tests/` Verzeichnis aus.

**Use Case:** Kompletter Test-Suite-Run mit Debugging

### 5. Python: Alpaca Connection Test
Testet die Alpaca API-Verbindung.

**Use Case:** API-Credentials validieren, Verbindungsprobleme debuggen

## 🔧 Tasks

Vordefinierte Tasks (Strg+Shift+P → "Tasks: Run Task"):

### Build & Install
- **Install Dependencies:** `uv pip install -e .`

### Testing
- **Run All Tests:** `pytest tests/ -v` ⭐ (Default Test Task)
- **Run Tests with Coverage:** Mit HTML-Report

### Code Quality
- **Lint with Ruff:** Check Code-Quality
- **Format with Ruff:** Auto-Format Code
- **Type Check with mypy:** Statische Typ-Analyse
- **Pre-commit All Files:** Führe alle Pre-commit Hooks aus

### Development
- **Start Trading Bot (Paper):** Bot im Paper-Modus starten

### Moltbot
- **Moltbot Gateway Status:** Prüfe Gateway-Status
- **Moltbot Health Check:** Vollständiger Health-Check

## 📐 Code Style

### Python (PEP 8 + Project-specific)

**Line Length:**
- Soft Limit: 88 Zeichen (Ruff default)
- Hard Limit: 120 Zeichen (sichtbarer Ruler)

**Indentation:**
- 4 Spaces (no tabs)
- Auto-conversion aktiviert

**Imports:**
- Automatisch sortiert (Ruff)
- Gruppierung: stdlib → third-party → local

**Type Hints:**
- Empfohlen für alle Public Functions
- Pylance zeigt Warnings bei fehlenden Types

### Other Files

**JSON/YAML:**
- Auto-Format mit Prettier
- YAML: 2 Spaces Indentation

**Markdown:**
- Word Wrap aktiviert
- Auto-Format mit Markdown All-in-One

## 🎨 Better Comments

Farbige Kommentare für bessere Lesbarkeit:

```python
# ! IMPORTANT: Kritische Information (Rot)
# ? QUESTION: Frage oder Unklarheit (Blau)
# // DEPRECATED: Veralteter Code (Durchgestrichen)
# todo: TODO-Item (Orange)
# * HIGHLIGHT: Wichtiger Hinweis (Grün)
```

## 🔍 Keyboard Shortcuts

### Häufig genutzte Shortcuts

| Shortcut | Aktion |
|----------|--------|
| `F5` | Start Debugging |
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+Shift+B` | Run Build Task |
| `Ctrl+Shift+T` | Run Test Task |
| `Ctrl+K Ctrl+T` | Select Color Theme |
| `Ctrl+` ` | Toggle Terminal |
| `Ctrl+Shift+G` | Git View |
| `Ctrl+Shift+E` | Explorer View |
| `Ctrl+Shift+X` | Extensions View |

### Python-spezifisch

| Shortcut | Aktion |
|----------|--------|
| `Shift+Alt+F` | Format Document |
| `Ctrl+Shift+I` | Format Selection |
| `F12` | Go to Definition |
| `Alt+F12` | Peek Definition |
| `Shift+F12` | Find All References |
| `F2` | Rename Symbol |

### Testing

| Shortcut | Aktion |
|----------|--------|
| `Ctrl+; Ctrl+A` | Run All Tests |
| `Ctrl+; Ctrl+F` | Run Failed Tests |
| `Ctrl+; Ctrl+L` | Run Last Test Run |
| `Ctrl+; Ctrl+C` | Run Test at Cursor |

## 🔗 Integration mit WSL2

### Remote-WSL Extension

**Projekt öffnen in WSL:**
```bash
# Von Windows Command Prompt/PowerShell
wsl
cd ~/03_Git/02_Python/07_OrderPilot-AI
code .
```

**Von WSL-Terminal:**
```bash
cd ~/03_Git/02_Python/07_OrderPilot-AI
code .
```

### Terminal Integration

**Default Shell:** Bash (WSL2)
**Environment:** `PYTHONPATH` automatisch gesetzt auf `${workspaceFolder}/src`

**Terminal öffnen:**
- `Ctrl+` ` (Backtick)
- Automatisch im Projekt-Root
- Virtual Environment automatisch aktiviert

## 🧪 Testing Workflow

### TDD Workflow mit VS Code

1. **Schreibe Test:**
   ```python
   # tests/test_feature.py
   def test_new_feature():
       assert feature() == expected_result
   ```

2. **Run Test:**
   - `Ctrl+; Ctrl+C` (Run Test at Cursor)
   - Oder: Click auf "Run Test" über der Funktion

3. **Debug Test (falls Failed):**
   - Setze Breakpoint (F9)
   - Right-click auf Test → "Debug Test"
   - Inspect Variables

4. **Implementiere Feature:**
   - Auto-Complete nutzen (Pylance)
   - Format on Save (Ruff)

5. **Re-run Tests:**
   - `Ctrl+; Ctrl+L` (Run Last Test)
   - Green ✓ = Success!

### Test Explorer

**Sidebar:**
- Tests automatisch entdeckt
- Hierarchische Ansicht
- Run/Debug Buttons
- Status-Icons (✓✗⊙)

## 🛡️ Security

### Environment Variables

**.env Dateien:**
- Automatisch erkannt (dotenv extension)
- Syntax-Highlighting
- **NIE in Git committen!**

**Empfohlen:**
```bash
# .env.example (in Git)
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here

# .env (local, in .gitignore)
ALPACA_API_KEY=actual_key
ALPACA_SECRET_KEY=actual_secret
```

### Secrets Scanning

**GitLens** zeigt Warnings bei potentiellen Secrets:
- API Keys
- Passwords
- Tokens

## 📊 Performance

### Optimierungen

**Files to Exclude:**
- Python Cache Files: `__pycache__/`, `*.pyc`
- Virtual Environments: `.venv/`, `.wsl_venv/`
- Test/Build Artifacts: `.pytest_cache/`, `.mypy_cache/`

**Search Exclude:**
- Gleiche wie Files Exclude
- Beschleunigt Suche erheblich

**Auto-Save:**
- Delay: 1 Sekunde
- Verhindert zu häufige Saves
- Balance zwischen Datenverlust-Schutz und Performance

## 🐛 Troubleshooting

### Python Interpreter nicht gefunden

**Problem:**
```
Python interpreter not found
```

**Lösung:**
1. `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Wähle `${workspaceFolder}/.wsl_venv/bin/python`
3. Oder: Virtual Environment aktivieren
   ```bash
   source .wsl_venv/bin/activate
   ```

### Linting funktioniert nicht

**Problem:**
```
Ruff not found
```

**Lösung:**
```bash
# Install Ruff in Virtual Environment
uv pip install ruff

# Oder: Install globally
pipx install ruff
```

### Tests werden nicht entdeckt

**Problem:** Test Explorer leer

**Lösung:**
1. Prüfe `settings.json`: `python.testing.pytestEnabled: true`
2. Install pytest: `uv pip install pytest`
3. Reload Window: `Ctrl+Shift+P` → "Developer: Reload Window"
4. Prüfe Test-Verzeichnis: `tests/` muss existieren

### Remote-WSL Verbindung schlägt fehl

**Problem:**
```
Failed to connect to the remote extension host server
```

**Lösung:**
1. WSL Version prüfen: `wsl --version`
2. WSL Update: `wsl --update`
3. VS Code Server neu installieren:
   ```bash
   rm -rf ~/.vscode-server
   # VS Code neu öffnen
   ```

## 📚 Weitere Ressourcen

- **VS Code Python:** https://code.visualstudio.com/docs/python/python-tutorial
- **Remote WSL:** https://code.visualstudio.com/docs/remote/wsl
- **Ruff:** https://docs.astral.sh/ruff/
- **Pytest:** https://docs.pytest.org/

---

**Fragen?** Siehe `docs/knowledge/error-patterns.md` oder öffne ein Issue.

**Letzte Aktualisierung:** 2026-01-28
