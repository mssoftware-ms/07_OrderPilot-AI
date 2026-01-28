# Detaillierter Setup-Plan: AI-gestütztes Python Vibe-Coding
## OrderPilot-AI Migration & Optimierung

**Deine aktuelle Situation:**
- ✅ WSL2 (Ubuntu 24.04.3) läuft
- ✅ Claude Code installiert & eingerichtet
- ✅ Docker Desktop mit WSL2 Backend
- ⚠️ OrderPilot-AI liegt auf D: (`/mnt/d/03_Git/02_Python/07_OrderPilot-AI`)
- ⚠️ Performance-Problem durch Windows-Dateisystem (9P-Protokoll)
- 🎯 Ziel: 200k+ Zeilen Code effizient managen mit AI-Assistenten

**Geschätzte Gesamtdauer:** 2-3 Stunden (einmalig)
**Performance-Gewinn nach Abschluss:** 10-20x schnellere Builds/Tests

---

## Phase 0: Vorbereitung & Backup (15 Min)

### Schritt 0.1: Aktuellen Zustand dokumentieren ✅

```bash
# 1. Ins Projekt-Verzeichnis wechseln
cd /mnt/d/03_Git/02_Python/07_OrderPilot-AI

# 2. Git Remote URL notieren (für späteren Clone)
git remote get-url origin > ~/orderpilot-remote.txt
cat ~/orderpilot-remote.txt
# Beispiel: https://github.com/maikwoehl/OrderPilot-AI.git

# 3. Aktuellen Branch notieren
git branch --show-current > ~/orderpilot-branch.txt
cat ~/orderpilot-branch.txt

# 4. Alle Branches auflisten (falls mehrere)
git branch -a > ~/orderpilot-branches.txt

# 5. Uncommitted Changes prüfen
git status --porcelain
# Falls Output: ERST COMMITTEN vor Migration!
```

**Wichtig:** Falls uncommitted changes existieren:
```bash
# Entweder committen:
git add .
git commit -m "feat: Pre-migration commit"
git push

# ODER stashen (für später):
git stash save "Pre-migration WIP"
```

### Schritt 0.2: Projekt-Größe & Dependencies erfassen

```bash
# Projekt-Größe
du -sh /mnt/d/03_Git/02_Python/07_OrderPilot-AI

# Python-Version im Projekt prüfen
cd /mnt/d/03_Git/02_Python/07_OrderPilot-AI
if [ -f ".python-version" ]; then
    cat .python-version
elif [ -f "pyproject.toml" ]; then
    grep "requires-python" pyproject.toml
fi

# Dependencies-Datei prüfen
ls -la | grep -E "(requirements|pyproject|Pipfile|setup.py)"
```

### Schritt 0.3: Windows-Pfad für späteren Zugriff notieren

```bash
# WSL-Pfad nach Migration (für Windows):
echo "\\\\wsl\$\\Ubuntu\\home\\$(whoami)\\projects\\OrderPilot-AI" > ~/windows-path.txt
cat ~/windows-path.txt
```

**Checkpoint:** 
- ✅ Git Remote URL bekannt
- ✅ Keine uncommitted changes (oder gestashed)
- ✅ Projekt-Größe bekannt
- ✅ Windows-Pfad notiert

---

## Phase 1: WSL2-Optimierung & Git-Konfiguration (20 Min)

### Schritt 1.1: WSL-Konfiguration optimieren

```bash
# 1. /etc/wsl.conf bearbeiten (mit sudo)
sudo nano /etc/wsl.conf

# Diesen Inhalt einfügen (falls nicht vorhanden):
```

```ini
[automount]
enabled = true
root = /mnt/
options = "metadata,umask=022,fmask=111"
mountFsTab = false

[network]
generateHosts = true
generateResolvConf = true

[interop]
enabled = true
appendWindowsPath = true

[boot]
systemd = true
```

```bash
# 2. Speichern: Ctrl+O, Enter, Ctrl+X

# 3. ~/.wslconfig für Memory-Limits erstellen (in Windows PowerShell!)
# Wechsle zu PowerShell (Windows-Seite) und führe aus:
# notepad $env:USERPROFILE\.wslconfig
```

In Windows PowerShell ausführen und `.wslconfig` erstellen:
```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
```

```bash
# 4. WSL neu starten (in PowerShell/CMD - Windows-Seite!)
wsl --shutdown
# Warte 10 Sekunden, dann WSL-Terminal neu öffnen
```

### Schritt 1.2: Git für Cross-Platform konfigurieren

```bash
# 1. Git-User prüfen (falls noch nicht gesetzt)
git config --global user.name || git config --global user.name "Dein Name"
git config --global user.email || git config --global user.email "deine@email.com"

# 2. Line-Endings für WSL/Windows korrekt setzen
git config --global core.autocrlf input
git config --global core.eol lf
git config --global core.filemode true

# 3. Prüfen ob gesetzt
git config --global --list | grep -E "(autocrlf|eol|filemode)"

# Erwartete Ausgabe:
# core.autocrlf=input
# core.eol=lf
# core.filemode=true
```

### Schritt 1.3: ~/projects Verzeichnis vorbereiten

```bash
# 1. Verzeichnis erstellen
mkdir -p ~/projects

# 2. Permissions setzen
chmod 755 ~/projects

# 3. In Verzeichnis wechseln
cd ~/projects

# 4. Prüfen dass wir im nativen WSL2-Dateisystem sind
pwd
# Sollte sein: /home/maik/projects (NICHT /mnt/...)
```

**Checkpoint:**
- ✅ `/etc/wsl.conf` konfiguriert
- ✅ `~/.wslconfig` erstellt (Windows-Seite)
- ✅ WSL neu gestartet
- ✅ Git Line-Endings konfiguriert
- ✅ `~/projects/` existiert

---

## Phase 2: OrderPilot-AI Migration (30 Min)

### Option A: Frischer Git-Clone (EMPFOHLEN)

**Vorteile:**
- ✅ Saubere History ohne Windows-Artefakte
- ✅ Keine CRLF/LF-Probleme
- ✅ Keine alten Cache-Dateien
- ✅ Kleinere Größe (keine .git Objekt-Bloat)

```bash
# 1. Remote URL laden
REMOTE_URL=$(cat ~/orderpilot-remote.txt)
echo "Klone von: $REMOTE_URL"

# 2. Frisch klonen
cd ~/projects
git clone --recurse-submodules "$REMOTE_URL" OrderPilot-AI

# 3. Ins neue Verzeichnis wechseln
cd ~/projects/OrderPilot-AI

# 4. Zum korrekten Branch wechseln (falls nicht main/master)
ORIG_BRANCH=$(cat ~/orderpilot-branch.txt)
if [ "$ORIG_BRANCH" != "main" ] && [ "$ORIG_BRANCH" != "master" ]; then
    git checkout "$ORIG_BRANCH"
fi

# 5. .gitattributes erstellen (für Line-Endings)
cat > .gitattributes << 'EOF'
# Auto detect text files and normalize to LF
* text=auto eol=lf

# Windows-spezifische Dateien
*.{cmd,[cC][mM][dD]} text eol=crlf
*.{bat,[bB][aA][tT]} text eol=crlf
*.ps1 text eol=crlf

# Binärdateien
*.png binary
*.jpg binary
*.jpeg binary
*.pdf binary
*.db binary
*.sqlite binary
*.pkl binary
EOF

git add .gitattributes
git commit -m "chore: Add .gitattributes for cross-platform line endings"

# 6. Falls du Stash hattest - von alter Location holen
# (Optional, nur falls du in Schritt 0.1 gestashed hast)
cd /mnt/d/03_Git/02_Python/07_OrderPilot-AI
git stash list  # Liste anschauen
git stash show -p stash@{0} > ~/stash.patch  # Als Patch exportieren
cd ~/projects/OrderPilot-AI
git apply ~/stash.patch  # Patch anwenden
```

### Option B: Direktes Kopieren (schneller, aber mit Risiken)

**Nur nutzen wenn:**
- Du viele lokale Branches hast, die nicht gepusht sind
- Du Work-in-Progress hast, der nicht committed werden soll

```bash
# 1. Mit rsync kopieren (erhält Permissions, filtert Junk)
rsync -av --progress \
    --exclude='.venv' \
    --exclude='.wsl_venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.mypy_cache' \
    --exclude='.pytest_cache' \
    --exclude='.ruff_cache' \
    --exclude='node_modules' \
    --exclude='dist' \
    --exclude='build' \
    /mnt/d/03_Git/02_Python/07_OrderPilot-AI/ \
    ~/projects/OrderPilot-AI/

# 2. In neues Verzeichnis wechseln
cd ~/projects/OrderPilot-AI

# 3. Git-Konfiguration für WSL anpassen
git config core.autocrlf input
git config core.eol lf
git config core.filemode true

# 4. .gitattributes erstellen (siehe Option A)
```

### Schritt 2.1: Migration validieren

```bash
cd ~/projects/OrderPilot-AI

# 1. Git-Integrität prüfen
git fsck --no-progress
# Erwartete Ausgabe: keine Fehler

# 2. Remote prüfen
git remote -v
# Sollte deine GitHub/GitLab URL zeigen

# 3. Status prüfen
git status
# Sollte "nothing to commit, working tree clean" zeigen
# (außer .gitattributes falls neu erstellt)

# 4. Dateianzahl vergleichen
echo "Neue Location:"
find ~/projects/OrderPilot-AI -type f -not -path '*/.git/*' | wc -l
echo "Alte Location:"
find /mnt/d/03_Git/02_Python/07_OrderPilot-AI -type f -not -path '*/.git/*' | wc -l
# Sollten ähnlich sein (kleine Differenz durch Caches OK)

# 5. Größe vergleichen
du -sh ~/projects/OrderPilot-AI
du -sh /mnt/d/03_Git/02_Python/07_OrderPilot-AI
```

**Checkpoint:**
- ✅ Projekt in `~/projects/OrderPilot-AI` liegt
- ✅ Git-Repository funktioniert
- ✅ `.gitattributes` existiert
- ✅ Dateianzahl stimmt ungefähr

---

## Phase 3: Python-Umgebung einrichten (30 Min)

### Schritt 3.1: uv Package Manager installieren (falls noch nicht da)

```bash
# 1. Prüfen ob uv bereits installiert
command -v uv && uv --version

# Falls nicht installiert:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Shell neu laden
source ~/.bashrc

# 3. Verifizieren
uv --version
# Erwartete Ausgabe: uv 0.5.x oder höher
```

### Schritt 3.2: Python-Projekt initialisieren

```bash
cd ~/projects/OrderPilot-AI

# 1. Prüfe ob pyproject.toml existiert
if [ -f "pyproject.toml" ]; then
    echo "✓ pyproject.toml gefunden"
    
    # Dependencies installieren mit uv
    uv sync --dev
    
elif [ -f "requirements.txt" ]; then
    echo "⚠ Nur requirements.txt gefunden - konvertiere zu pyproject.toml"
    
    # Erstelle pyproject.toml
    cat > pyproject.toml << 'EOF'
[project]
name = "orderpilot-ai"
version = "0.1.0"
description = "AI-powered trading system for Bitcoin futures"
requires-python = ">=3.10"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-xdist>=3.5.0",
    "ruff>=0.8.0",
    "mypy>=1.8.0",
]
EOF
    
    # Dependencies aus requirements.txt importieren
    uv add $(cat requirements.txt | grep -v "^#" | grep -v "^$" | tr '\n' ' ')
    
else
    echo "❌ Keine Dependencies-Datei gefunden"
    echo "Erstelle minimale pyproject.toml"
    
    cat > pyproject.toml << 'EOF'
[project]
name = "orderpilot-ai"
version = "0.1.0"
description = "AI-powered trading system"
requires-python = ">=3.10"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF
fi

# 2. Development-Tools installieren
uv sync --dev
```

### Schritt 3.3: Ruff für Code-Quality konfigurieren

```bash
cd ~/projects/OrderPilot-AI

# Prüfe ob [tool.ruff] bereits in pyproject.toml existiert
if ! grep -q "\[tool.ruff\]" pyproject.toml; then
    echo "Füge Ruff-Konfiguration zu pyproject.toml hinzu"
    
    cat >> pyproject.toml << 'EOF'

[tool.ruff]
line-length = 88
target-version = "py310"
exclude = [
    ".git", ".venv", "__pycache__", "build", "dist",
    "migrations", "*.egg-info",
]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # Pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "S",    # Bandit security
    "UP",   # pyupgrade
    "RUF",  # Ruff-specific
]
ignore = [
    "E501",   # Line too long (formatter handles this)
    "S101",   # Use of assert (OK in tests)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "S105", "S106"]
"__init__.py" = ["F401"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
EOF
fi

# Ruff installieren
uv tool install ruff

# Ersten Check ausführen
uv run ruff check .

# Auto-Fix für einfache Issues
uv run ruff check --fix .

# Formatierung anwenden
uv run ruff format .
```

### Schritt 3.4: pytest konfigurieren

```bash
cd ~/projects/OrderPilot-AI

# Prüfe ob tests/ Verzeichnis existiert
if [ ! -d "tests" ]; then
    mkdir -p tests
    touch tests/__init__.py
    
    # Beispiel-Test erstellen
    cat > tests/test_example.py << 'EOF'
"""Beispiel-Test für pytest-Setup."""

def test_example():
    """Einfacher Test um Setup zu validieren."""
    assert 1 + 1 == 2
EOF
fi

# pytest-Konfiguration zu pyproject.toml hinzufügen
if ! grep -q "\[tool.pytest" pyproject.toml; then
    cat >> pyproject.toml << 'EOF'

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = [
    "-ra",                    # Extra test summary
    "--strict-markers",
    "--strict-config",
    "--cov=src",              # Passe an deine Struktur an
    "--cov-report=term-missing",
]
markers = [
    "slow: Slow tests",
    "integration: Integration tests",
    "unit: Fast unit tests",
]
EOF
fi

# Tests ausführen
uv run pytest -v
```

### Schritt 3.5: Pre-commit Hooks einrichten

```bash
cd ~/projects/OrderPilot-AI

# pre-commit installieren
uv tool install pre-commit

# .pre-commit-config.yaml erstellen
cat > .pre-commit-config.yaml << 'EOF'
default_language_version:
  python: python3.10

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
EOF

# Pre-commit hooks installieren
uv run pre-commit install

# Ersten Run auf allen Dateien
uv run pre-commit run --all-files
```

**Checkpoint:**
- ✅ uv installiert
- ✅ Python-Umgebung mit `pyproject.toml`
- ✅ Ruff konfiguriert & ausgeführt
- ✅ pytest funktioniert
- ✅ Pre-commit hooks aktiv

---

## Phase 4: Claude Code einrichten (20 Min)

### Schritt 4.1: CLAUDE.md erstellen (Projekt-Kontext)

```bash
cd ~/projects/OrderPilot-AI

cat > CLAUDE.md << 'EOF'
# OrderPilot-AI

## Projekt-Überblick
AI-gestütztes Trading-System für Bitcoin-Futures mit über 200.000 Zeilen Code.
Entwickelt für algorithmisches Trading mit technischen Indikatoren und Backtesting.

## Architektur
```
src/
├── strategies/      # Trading-Strategien
├── indicators/      # Technische Indikatoren
├── backtesting/     # Backtesting-Framework
├── execution/       # Order-Execution
└── utils/           # Hilfsfunktionen

tests/              # pytest Test-Suite
docs/               # Dokumentation
scripts/            # Utility-Skripte
```

## Entwicklungs-Workflow

### Wichtige Kommandos
```bash
# Tests ausführen
uv run pytest -x --tb=short

# Mit Coverage
uv run pytest --cov=src --cov-report=term-missing

# Linting + Auto-Fix
uv run ruff check --fix .

# Formatierung
uv run ruff format .

# Type-Checking
uv run mypy src/
```

### Code-Style
- Python 3.10+
- Type Hints für alle öffentlichen Funktionen
- Docstrings im Google-Format
- Max 88 Zeichen pro Zeile (Ruff)

### Git-Workflow
- Feature-Branches von `main`
- Konventionelle Commits: `feat:`, `fix:`, `refactor:`, `docs:`
- Tests müssen grün sein vor Commit
- Pre-commit hooks laufen automatisch

### Nicht ändern ohne Rücksprache
- `src/legacy/` - Depreciated Code (Entfernung geplant)
- Database Migrations - SQL-Änderungen brauchen Review
- API-Contracts - Breaking Changes vermeiden

## Wichtige Dateien
@README.md
@pyproject.toml
@docs/ARCHITECTURE.md

## Bekannte Issues
- Performance bei sehr großen Backtests (>1M Bars) optimierungsbedürftig
- Einige Legacy-Tests nutzen noch `unittest` statt `pytest`

## Trading-spezifische Hinweise
⚠️ **KRITISCH**: Nie Echtgeld-Trading-Code ohne umfassende Tests committen
- Alle Strategien MÜSSEN Backtest-validated sein
- Risk-Management-Parameter niemals in Code hardcoden
- API-Keys ausschließlich über Umgebungsvariablen
EOF

# CLAUDE.md zu Git hinzufügen
git add CLAUDE.md
git commit -m "docs: Add CLAUDE.md for AI context"
```

### Schritt 4.2: .mcp.json für Memory-Integration (optional)

```bash
cd ~/projects/OrderPilot-AI

cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/maik/projects/OrderPilot-AI"
      ]
    }
  }
}
EOF

git add .mcp.json
git commit -m "feat: Add MCP filesystem server config"
```

### Schritt 4.3: Claude Code API-Key Check

```bash
# WICHTIG: Prüfe dass KEIN API-Key gesetzt ist (für Subscription)
echo $ANTHROPIC_API_KEY

# Falls gesetzt (sollte leer sein!):
unset ANTHROPIC_API_KEY

# Permanent aus .bashrc/.zshrc entfernen falls vorhanden
grep -n "ANTHROPIC_API_KEY" ~/.bashrc
# Falls gefunden: entsprechende Zeile löschen
```

### Schritt 4.4: Claude Code testen

```bash
cd ~/projects/OrderPilot-AI

# Claude Code starten
claude

# Im Claude Code Interface:
# > Hallo! Kannst du mir einen Überblick über die Projekt-Struktur geben?
# > Zeige mir die wichtigsten Trading-Strategien in src/strategies/

# Status prüfen
/status

# Memory-Status prüfen
/memory

# Bei Problemen: Logs anschauen
claude --logs
```

**Checkpoint:**
- ✅ `CLAUDE.md` erstellt und committed
- ✅ `.mcp.json` konfiguriert (optional)
- ✅ `ANTHROPIC_API_KEY` nicht gesetzt
- ✅ Claude Code startet erfolgreich

---

## Phase 5: Moltbot installieren & konfigurieren (30 Min)

### Schritt 5.1: Node.js installieren (falls nicht vorhanden)

```bash
# 1. Prüfe ob Node.js installiert
node --version

# Falls nicht oder Version < 22:
# NodeSource Repository hinzufügen
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -

# Node.js installieren
sudo apt-get install -y nodejs

# Verifizieren
node --version  # Sollte v22.x.x sein
npm --version   # Sollte 10.x.x sein
```

### Schritt 5.2: Moltbot global installieren

```bash
# 1. Moltbot installieren
npm install -g moltbot@latest

# 2. Version prüfen
moltbot --version

# 3. Legacy-Kommando prüfen (sollte auch funktionieren)
clawdbot --version
```

### Schritt 5.3: Moltbot onboarden & Daemon einrichten

```bash
# 1. Onboarding-Prozess starten
moltbot onboard --install-daemon

# Folge den Anweisungen:
# - OAuth-Login mit Anthropic (Browser öffnet sich)
# - Messaging-Channel wählen (Discord/Slack/etc. - optional)
# - Daemon-Installation bestätigen

# 2. Daemon-Status prüfen
systemctl --user status moltbot

# Sollte "active (running)" zeigen

# 3. Logs anschauen
journalctl --user -u moltbot -f
# Ctrl+C zum Beenden
```

### Schritt 5.4: Moltbot-Konfiguration anpassen

```bash
# 1. Konfig-Verzeichnis anschauen
ls -la ~/.moltbot/

# 2. Config-Datei bearbeiten
nano ~/.moltbot/config.json

# Wichtige Einstellungen:
# - "workspaceRoot": "/home/maik/projects"  # Auf deine Projekte zeigen
# - "autoStart": true
# - "logLevel": "info"

# 3. Speichern: Ctrl+O, Enter, Ctrl+X

# 4. Daemon neu starten
systemctl --user restart moltbot
```

### Schritt 5.5: Moltbot mit OrderPilot-AI testen

```bash
cd ~/projects/OrderPilot-AI

# Moltbot im aktuellen Projekt nutzen
# (Messaging-Interface verwenden oder lokale Commands)

# Beispiel-Befehle (je nach Setup):
# "Analysiere die Trading-Strategien"
# "Finde Performance-Bottlenecks im Backtest-Code"
# "Erstelle Tests für die neuen Indikatoren"
```

**Checkpoint:**
- ✅ Node.js 22+ installiert
- ✅ Moltbot global installiert
- ✅ Daemon läuft
- ✅ Mit Anthropic verbunden

---

## Phase 6: Wissensdatenbank einrichten (30 Min)

### Option A: Einfache Markdown-Struktur (Empfohlen für Start)

```bash
cd ~/projects/OrderPilot-AI

# 1. Dokumentations-Struktur erstellen
mkdir -p docs/{adr,knowledge,snippets}

# 2. ADR-Template erstellen
cat > docs/adr/template.md << 'EOF'
# ADR-XXX: [Titel]

**Status:** [Proposed | Accepted | Deprecated]  
**Datum:** YYYY-MM-DD  
**Autor:** [Name]

## Kontext
Welche Situation hat diese Entscheidung ausgelöst?

## Entscheidung
Wie gehen wir vor? Was ist die Lösung?

## Konsequenzen
### Positiv
- Was wird dadurch besser?

### Negativ
- Welche Trade-offs gibt es?

## Alternativen
Welche anderen Optionen wurden evaluiert und warum verworfen?

## Referenzen
- Link zu Issues, PRs, Diskussionen
EOF

# 3. Erste ADR erstellen
cat > docs/adr/0001-migration-to-wsl.md << 'EOF'
# ADR-001: Migration von D: zu WSL2-native Dateisystem

**Status:** Accepted  
**Datum:** 2026-01-28  
**Autor:** Maik

## Kontext
OrderPilot-AI lag auf D: (/mnt/d) was zu 10-20x langsameren Builds führte
durch 9P-Protokoll-Overhead zwischen WSL2 und Windows.

## Entscheidung
Migration nach ~/projects/OrderPilot-AI im nativen WSL2-Dateisystem.
Frischer Git-Clone statt Kopieren für saubere History.

## Konsequenzen
### Positiv
- Build-Zeit von ~60s → ~5s
- Native inotify-Events (File-Watchers funktionieren)
- Keine CRLF/LF-Probleme mehr
- Volle Unix-Permissions

### Negativ
- Windows-Programme brauchen \\wsl$-Pfad
- Initial-Migration dauert 30 Min

## Alternativen
- Docker Volumes: Zu komplex, keine Performance-Vorteile
- Auf D: bleiben: Nicht akzeptabel für 200k LOC Projekt

## Referenzen
- https://docs.docker.com/desktop/features/wsl/best-practices/
EOF

# 4. knowledge/error-patterns.md erstellen
cat > docs/knowledge/error-patterns.md << 'EOF'
# Bekannte Fehler & Lösungen

## Performance-Issues

### Backtest langsam bei >1M Bars
**Symptom:** Backtest dauert >30 Minuten für große Datasets
**Ursache:** Pandas DataFrames werden bei jedem Schritt neu kopiert
**Lösung:** Numpy-Arrays direkt nutzen für Performance-kritische Loops
**Code-Location:** `src/backtesting/engine.py:execute_backtest()`

## Deployment-Issues

### Docker-Build schlägt fehl
**Symptom:** `ERROR: Could not build wheels for...`
**Ursache:** Fehlende Build-Dependencies
**Lösung:** `apt-get install -y build-essential python3-dev`
**Letzte Aktualisierung:** 2026-01-28
EOF

# 5. useful-commands.md erstellen
cat > docs/knowledge/useful-commands.md << 'EOF'
# Nützliche Kommandos

## Development

### Vollständiger Test-Run mit Coverage
```bash
uv run pytest -n auto --cov=src --cov-report=html
# → htmlcov/index.html öffnen
```

### Performance-Profiling
```bash
uv run python -m cProfile -o profile.stats src/main.py
uv run python -m pstats profile.stats
# > sort cumulative
# > stats 20
```

### Dependency-Graph erstellen
```bash
uv run pipdeptree --graph-output png > deps.png
```

## Trading-spezifisch

### Backtest lokal ausführen
```bash
uv run python scripts/run_backtest.py \
    --strategy aggressive_trend \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --output results/backtest_$(date +%Y%m%d).json
```

### Live-Trading-Status (Test-Mode)
```bash
uv run python src/main.py --mode test --dry-run
```
EOF

# 6. In CLAUDE.md referenzieren
cat >> CLAUDE.md << 'EOF'

## Wissensdatenbank
Die folgenden Dokumente enthalten wichtige Projekt-Entscheidungen und Patterns:

@docs/adr/
@docs/knowledge/error-patterns.md
@docs/knowledge/useful-commands.md

Bei Änderungen an Architektur: ADR erstellen!
Bei Bugfixes: error-patterns.md updaten!
EOF

git add docs/ CLAUDE.md
git commit -m "docs: Add knowledge base structure"
```

### Option B: SQLite Knowledge-DB (für Fortgeschrittene)

```bash
cd ~/projects/OrderPilot-AI

# 1. Verzeichnis für Memory erstellen
mkdir -p memory

# 2. SQLite-DB erstellen
sqlite3 memory/knowledge.db << 'SQL'
-- Entscheidungen
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT CHECK(status IN ('proposed', 'accepted', 'deprecated')),
    context TEXT NOT NULL,
    decision TEXT NOT NULL,
    consequences TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    tags TEXT
);

-- Code-Snippets
CREATE TABLE code_snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    language TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    use_case TEXT,
    tags TEXT,
    file_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Fehler-Patterns
CREATE TABLE error_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    root_cause TEXT,
    solution TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    tags TEXT
);

-- Full-Text Search
CREATE VIRTUAL TABLE decisions_fts USING fts5(
    title, context, decision, consequences,
    content=decisions
);

-- Trigger für FTS-Sync
CREATE TRIGGER decisions_fts_insert AFTER INSERT ON decisions BEGIN
    INSERT INTO decisions_fts(rowid, title, context, decision, consequences)
    VALUES (new.id, new.title, new.context, new.decision, new.consequences);
END;
SQL

echo "✓ SQLite Knowledge-DB erstellt"

# 3. Beispiel-Eintrag hinzufügen
sqlite3 memory/knowledge.db << 'SQL'
INSERT INTO decisions (title, status, context, decision, consequences, tags)
VALUES (
    'Migration zu WSL2-native Dateisystem',
    'accepted',
    'OrderPilot-AI lag auf D: mit 10-20x Performance-Penalty',
    'Migration nach ~/projects für natives WSL2-Dateisystem',
    'Pro: 10-20x schneller, native inotify. Con: Windows-Apps brauchen \\wsl$-Pfad',
    'performance,infrastructure'
);
SQL

# 4. Query-Skript erstellen
cat > scripts/query_knowledge.sh << 'EOF'
#!/bin/bash
# Query Knowledge Base

DB="memory/knowledge.db"

case "$1" in
    search)
        sqlite3 "$DB" "SELECT title, decision FROM decisions_fts WHERE decisions_fts MATCH '$2';"
        ;;
    recent)
        sqlite3 "$DB" "SELECT title, created_at FROM decisions ORDER BY created_at DESC LIMIT 10;"
        ;;
    tags)
        sqlite3 "$DB" "SELECT DISTINCT tags FROM decisions WHERE tags LIKE '%$2%';"
        ;;
    *)
        echo "Usage: $0 {search|recent|tags} [query]"
        exit 1
        ;;
esac
EOF

chmod +x scripts/query_knowledge.sh

# 5. memory/ zu .gitignore hinzufügen
echo "memory/*.db" >> .gitignore
```

**Checkpoint:**
- ✅ Dokumentations-Struktur erstellt
- ✅ ADR-Template und erste ADR
- ✅ Error-Patterns dokumentiert
- ✅ Useful-Commands Referenz
- ✅ (Optional) SQLite Knowledge-DB

---

## Phase 7: VS Code einrichten (15 Min)

### Schritt 7.1: VS Code Remote-WSL Extension

```bash
# In WSL:
cd ~/projects/OrderPilot-AI

# VS Code von WSL aus öffnen (installiert automatisch Server)
code .

# Warte bis "WSL: Ubuntu" unten links angezeigt wird
```

### Schritt 7.2: Empfohlene VS Code Extensions

In VS Code (nach Öffnen via WSL):
1. `Ctrl+Shift+X` → Extensions öffnen
2. Folgende Extensions installieren:

```
ms-python.python              # Python-Support
ms-python.vscode-pylance      # Language Server
charliermarsh.ruff            # Ruff Linter/Formatter
ms-python.debugpy             # Python Debugger
eamodio.gitlens               # Git-Integration
tamasfe.even-better-toml      # TOML-Support
GitHub.copilot                # Falls du Copilot hast
```

### Schritt 7.3: VS Code Settings für Projekt

```bash
cd ~/projects/OrderPilot-AI

mkdir -p .vscode

# settings.json erstellen
cat > .vscode/settings.json << 'EOF'
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  },
  
  "ruff.enable": true,
  "ruff.organizeImports": true,
  
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true,
    "**/*.pyc": true
  },
  
  "editor.rulers": [88],
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
EOF

# launch.json für Debugging
cat > .vscode/launch.json << 'EOF'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: pytest",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "${file}"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
EOF

git add .vscode/
git commit -m "chore: Add VS Code workspace settings"
```

**Checkpoint:**
- ✅ VS Code über Remote-WSL geöffnet
- ✅ Python & Ruff Extensions installiert
- ✅ Workspace-Settings konfiguriert
- ✅ Debugging funktioniert

---

## Phase 8: Performance-Vergleich & Validierung (15 Min)

### Schritt 8.1: Performance-Messung

```bash
# 1. Test-Run auf neuer Location (WSL2-nativ)
cd ~/projects/OrderPilot-AI
time uv run pytest -x -q
# Notiere die Zeit: ______s

# 2. Zum Vergleich: Test-Run auf alter Location
cd /mnt/d/03_Git/02_Python/07_OrderPilot-AI
time uv run pytest -x -q  
# Notiere die Zeit: ______s (sollte 10-20x langsamer sein!)

# 3. Build-Performance (falls du eine hast)
cd ~/projects/OrderPilot-AI
time uv run python setup.py build  # oder dein Build-Kommando
```

### Schritt 8.2: Finale Validierung

```bash
cd ~/projects/OrderPilot-AI

# 1. Git-Status
git status
# Sollte clean sein (außer uncommitted new files)

# 2. Tests grün?
uv run pytest --co -q  # Zeigt alle Tests an
uv run pytest -x       # Führt aus, stoppt bei erstem Fehler

# 3. Linting OK?
uv run ruff check .

# 4. Pre-commit funktioniert?
uv run pre-commit run --all-files

# 5. Claude Code funktioniert?
claude
# > /status
# > Zeige mir die Projekt-Struktur
```

**Checkpoint:**
- ✅ Tests laufen 10-20x schneller
- ✅ Alle Quality-Checks grün
- ✅ Git-Repository funktioniert
- ✅ Claude Code & Moltbot verbunden

---

## Phase 9: Alte Location aufräumen (10 Min)

### Schritt 9.1: Backup erstellen (Sicherheit)

```bash
# 1. Alte Location als .tar.gz archivieren
cd /mnt/d/03_Git/02_Python
tar -czf 07_OrderPilot-AI.backup.$(date +%Y%m%d).tar.gz 07_OrderPilot-AI/

# 2. Backup-Größe prüfen
ls -lh 07_OrderPilot-AI.backup.*.tar.gz

# 3. Backup verschieben (optional - auf externe Festplatte?)
# mv 07_OrderPilot-AI.backup.*.tar.gz /mnt/e/Backups/
```

### Schritt 9.2: Alte Location löschen (Optional)

```bash
# NUR nach erfolgreicher Validierung!
# Warte 1-2 Wochen bis du sicher bist, dass alles funktioniert

# Dann:
rm -rf /mnt/d/03_Git/02_Python/07_OrderPilot-AI
```

**Checkpoint:**
- ✅ Backup erstellt
- ✅ (Optional) Alte Location gelöscht

---

## Phase 10: Dokumentation & Workflow-Templates (20 Min)

### Schritt 10.1: Makefile für häufige Kommandos

```bash
cd ~/projects/OrderPilot-AI

cat > Makefile << 'EOF'
.PHONY: help install test lint format typecheck check clean

help:
	@echo "OrderPilot-AI Makefile"
	@echo ""
	@echo "Verfügbare Targets:"
	@echo "  install    - Dependencies installieren"
	@echo "  test       - Tests ausführen"
	@echo "  test-cov   - Tests mit Coverage"
	@echo "  lint       - Ruff linting"
	@echo "  format     - Code formatieren"
	@echo "  typecheck  - mypy type checking"
	@echo "  check      - Alle Checks (lint+test+type)"
	@echo "  clean      - Cache-Dateien löschen"
	@echo "  claude     - Claude Code starten"

install:
	uv sync --dev

test:
	uv run pytest -x --tb=short -q

test-cov:
	uv run pytest -n auto --cov=src --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy src/

check: lint typecheck test
	@echo "✓ Alle Checks bestanden"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

claude:
	@cd $(PWD) && claude

.DEFAULT_GOAL := help
EOF

git add Makefile
git commit -m "chore: Add Makefile for common tasks"

# Test
make help
```

### Schritt 10.2: GitHub Actions CI (optional)

```bash
cd ~/projects/OrderPilot-AI

mkdir -p .github/workflows

cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.10"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
      
      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: uv sync --dev
      
      - name: Ruff lint
        run: uv run ruff check --output-format=github .
      
      - name: Ruff format check
        run: uv run ruff format --check .

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      
      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: uv sync --dev
      
      - name: Run tests
        run: |
          uv run pytest -n auto \
            --cov=src \
            --cov-report=xml \
            --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: github.event_name == 'push'
        with:
          file: ./coverage.xml
EOF

git add .github/workflows/ci.yml
git commit -m "ci: Add GitHub Actions workflow"
```

### Schritt 10.3: README.md aktualisieren

```bash
cd ~/projects/OrderPilot-AI

# Falls README.md noch nicht existiert oder aktualisiert werden soll:
cat > README.md << 'EOF'
# OrderPilot-AI

AI-powered algorithmic trading system for Bitcoin futures.

## 🚀 Quick Start

```bash
# Clone repository
git clone <your-repo-url>
cd OrderPilot-AI

# Install dependencies
make install

# Run tests
make test

# Start Claude Code
make claude
```

## 📊 Development

```bash
# Run all checks
make check

# Format code
make format

# Coverage report
make test-cov
```

## 🏗 Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 📚 Documentation

- [ADRs](docs/adr/) - Architecture Decision Records
- [Knowledge Base](docs/knowledge/) - Error patterns & solutions

## 🛠 Tools

- **uv** - Fast Python package manager
- **Ruff** - Lightning-fast linter & formatter
- **pytest** - Testing framework
- **Claude Code** - AI coding assistant
- **Moltbot** - AI automation daemon

## 📈 Performance

Optimized for WSL2 native filesystem:
- Build time: ~5s (vs. 60s on Windows filesystem)
- Test suite: ~2s for unit tests
- Full coverage run: ~10s

## 🔒 Security

- No API keys in code (use environment variables)
- Pre-commit hooks for secret detection
- All strategies must be backtested before deployment

## 📝 License

[Your License]
EOF

git add README.md
git commit -m "docs: Update README with setup instructions"
```

**Checkpoint:**
- ✅ Makefile für Kommandos
- ✅ CI/CD Pipeline (optional)
- ✅ README aktualisiert

---

## Phase 11: Windows-Integration & Zugriff (10 Min)

### Schritt 11.1: Windows Explorer Shortcut

1. **Windows Explorer öffnen**
2. **Adresszeile:** `\\wsl$\Ubuntu\home\maik\projects\OrderPilot-AI`
3. **Rechtsklick** → "An Schnellzugriff anheften"
4. Optional: Desktop-Verknüpfung erstellen

### Schritt 11.2: Windows Terminal Profil (optional)

In Windows Terminal (falls genutzt):
```json
// settings.json
{
    "profiles": {
        "list": [
            {
                "guid": "{neue-guid-generieren}",
                "name": "OrderPilot-AI (WSL)",
                "commandline": "wsl.exe -d Ubuntu -- bash -c 'cd ~/projects/OrderPilot-AI && exec bash'",
                "icon": "https://assets.ubuntu.com/v1/49a1a858-favicon-32x32.png",
                "startingDirectory": "//wsl$/Ubuntu/home/maik/projects/OrderPilot-AI"
            }
        ]
    }
}
```

### Schritt 11.3: Python aus Windows nutzen (falls nötig)

Falls du Python-Skripte von Windows aus starten musst:

```powershell
# PowerShell-Skript erstellen: run-orderpilot.ps1
$wslPath = "~/projects/OrderPilot-AI"
$script = $args[0]

wsl -d Ubuntu -- bash -c "cd $wslPath && uv run python $script"
```

**Checkpoint:**
- ✅ Windows Explorer Zugriff funktioniert
- ✅ (Optional) Terminal-Profile erstellt
- ✅ Python von Windows aus startbar

---

## Finale Checkliste - Abnahme aller Phasen

### System-Setup ✅
- [ ] WSL2 läuft mit Ubuntu 24.04.3
- [ ] `/etc/wsl.conf` konfiguriert
- [ ] `~/.wslconfig` mit Memory-Limits erstellt
- [ ] Docker Desktop mit WSL2-Backend funktioniert
- [ ] Git Line-Endings konfiguriert (autocrlf=input, eol=lf)

### Projekt-Migration ✅
- [ ] OrderPilot-AI liegt in `~/projects/OrderPilot-AI`
- [ ] Git-Repository funktioniert
- [ ] `.gitattributes` für Cross-Platform erstellt
- [ ] Performance 10-20x besser als auf D:
- [ ] Alte Location auf D: gebackuped

### Python-Umgebung ✅
- [ ] uv installiert
- [ ] `pyproject.toml` existiert und konfiguriert
- [ ] Dependencies installiert (`uv sync --dev`)
- [ ] Ruff konfiguriert und läuft
- [ ] pytest funktioniert
- [ ] Pre-commit hooks aktiv

### AI-Assistenten ✅
- [ ] Claude Code funktioniert (`claude` Kommando)
- [ ] `ANTHROPIC_API_KEY` NICHT gesetzt (Subscription-Nutzung)
- [ ] `CLAUDE.md` erstellt und informativ
- [ ] `.mcp.json` konfiguriert (optional)
- [ ] Moltbot installiert (`moltbot --version`)
- [ ] Moltbot Daemon läuft (`systemctl --user status moltbot`)

### Wissensdatenbank ✅
- [ ] `docs/adr/` mit Template und erster ADR
- [ ] `docs/knowledge/error-patterns.md` vorhanden
- [ ] `docs/knowledge/useful-commands.md` vorhanden
- [ ] (Optional) SQLite Knowledge-DB eingerichtet

### Development-Tools ✅
- [ ] VS Code Remote-WSL funktioniert
- [ ] Python & Ruff Extensions installiert
- [ ] `.vscode/settings.json` konfiguriert
- [ ] Makefile für häufige Kommandos
- [ ] (Optional) GitHub Actions CI konfiguriert

### Validierung ✅
- [ ] `make test` läuft erfolgreich
- [ ] `make check` (lint+test+typecheck) bestanden
- [ ] Claude Code kann Projekt-Struktur analysieren
- [ ] Moltbot kann auf Projekt zugreifen
- [ ] Windows-Zugriff via `\\wsl$\...` funktioniert

---

## Nächste Schritte nach Setup

### Tag 1-7: Eingewöhnung
- [ ] Teste Claude Code mit echten Tasks im Projekt
- [ ] Erstelle ADRs für vergangene wichtige Entscheidungen
- [ ] Dokumentiere bekannte Bugs in `error-patterns.md`
- [ ] Experimentiere mit Moltbot-Workflows

### Woche 2-4: Optimierung
- [ ] Erweitere `CLAUDE.md` mit Projekt-spezifischen Details
- [ ] Baue Memory/Wissensdatenbank auf (SQLite oder Markdown)
- [ ] Erstelle Shortcuts für häufige Workflows
- [ ] Optimiere Pre-commit Hooks nach Bedarf

### Monat 2+: Advanced
- [ ] Multi-Agent-Workflows definieren (Planner/Coder/Reviewer)
- [ ] RAG-System aufbauen (falls 200k LOC zu groß für Context)
- [ ] CI/CD weiter automatisieren
- [ ] Custom MCP-Server für Trading-spezifische Tools

---

## Troubleshooting & Häufige Probleme

### Problem: Tests auf D: laufen noch
**Lösung:** Shell-Prompt prüfen - bist du wirklich in `~/projects/...`?
```bash
pwd  # Sollte /home/maik/projects/... zeigen, NICHT /mnt/d/...
```

### Problem: Git zeigt alle Dateien als geändert
**Lösung:** Line-Endings normalisieren
```bash
cd ~/projects/OrderPilot-AI
git add --renormalize .
git commit -m "fix: Normalize line endings"
```

### Problem: Pre-commit dauert ewig
**Lösung:** Cache leeren
```bash
uv run pre-commit clean
uv run pre-commit run --all-files
```

### Problem: Claude Code nutzt API-Key statt Subscription
**Lösung:**
```bash
unset ANTHROPIC_API_KEY
# Aus ~/.bashrc entfernen falls drin
sed -i '/ANTHROPIC_API_KEY/d' ~/.bashrc
source ~/.bashrc
claude login  # Neu einloggen
```

### Problem: Moltbot Daemon startet nicht
**Lösung:**
```bash
# Logs prüfen
journalctl --user -u moltbot -n 50

# Daemon neu installieren
moltbot onboard --install-daemon --force
```

### Problem: Docker Container können nicht auf ~/projects zugreifen
**Lösung:** Docker Desktop Settings
1. Docker Desktop → Settings → Resources → WSL Integration
2. Aktiviere "Ubuntu" Distribution
3. "Apply & Restart"

---

## Performance-Benchmarks (Referenzwerte)

| Operation | D: (Windows FS) | ~/projects (WSL2) | Speedup |
|-----------|-----------------|-------------------|---------|
| pytest (full suite) | ~60s | ~5s | 12x |
| npm install (large project) | ~290s | ~30s | 10x |
| Git operations | ~3-5s | ~0.3s | 10-15x |
| File watching | ❌ Broken | ✅ Works | ∞ |
| Docker builds | ~120s | ~15s | 8x |

**Deine Werte:**
- pytest (full): D: _____s, WSL2: _____s
- Build: D: _____s, WSL2: _____s

---

## Support & Weiterführende Ressourcen

### Offizielle Dokumentation
- **Moltbot:** https://docs.molt.bot
- **Claude Code:** https://docs.anthropic.com/claude-code
- **uv:** https://docs.astral.sh/uv
- **Ruff:** https://docs.astral.sh/ruff
- **WSL2 Best Practices:** https://docs.docker.com/desktop/features/wsl/best-practices/

### Community
- **Moltbot Discord:** https://discord.gg/clawd
- **Anthropic Support:** https://support.anthropic.com

### Backup-Strategie
```bash
# Wöchentliches Backup (cron):
0 3 * * 0 tar -czf ~/backups/orderpilot-$(date +\%Y\%m\%d).tar.gz ~/projects/OrderPilot-AI
```

---

**🎉 Herzlichen Glückwunsch!**

Wenn du alle Phasen abgeschlossen hast, hast du jetzt:
- ✅ Ein 10-20x schnelleres Entwicklungs-Setup
- ✅ AI-Assistenten die deinen 200k LOC Code verstehen
- ✅ Automatisierte Quality-Checks
- ✅ Strukturierte Wissensdatenbank
- ✅ Professioneller Python-Workflow

**Viel Erfolg mit OrderPilot-AI! 🚀**
