# Error Patterns & Solutions

Sammlung häufiger Fehler im OrderPilot-AI Projekt mit bewährten Lösungen.

**Ziel:** Schnelle Problemlösung durch Muster-Erkennung
**Prinzip:** Symptom → Diagnose → Lösung
**Letzte Aktualisierung:** 2026-01-28

---

## 📋 Kategorien

- [Git & Version Control](#git--version-control)
- [Python Environment](#python-environment)
- [Dependencies & Packages](#dependencies--packages)
- [WSL2 & File System](#wsl2--file-system)
- [Moltbot/Clawdbot](#moltbotclawdbot)
- [Alpaca API](#alpaca-api)
- [Testing & CI/CD](#testing--cicd)

---

## Git & Version Control

### 1. CRLF Line Ending Konflikte

**Symptom:**
```
warning: LF will be replaced by CRLF in [file]
git diff zeigt unterschiede obwohl nichts geändert wurde
```

**Diagnose:**
- Windows (CRLF) und Unix (LF) Line Endings vermischt
- `.gitattributes` fehlt oder nicht korrekt

**Lösung:**
```bash
# 1. .gitattributes erstellen/aktualisieren
cat > .gitattributes << 'EOF'
* text=auto eol=lf
*.py text eol=lf
*.sh text eol=lf
*.md text eol=lf
*.json text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
EOF

# 2. Git config setzen
git config --global core.autocrlf input
git config --global core.eol lf

# 3. Alle Dateien neu normalisieren
git add --renormalize .
git commit -m "Normalize line endings"
```

**Prevention:**
- Immer `.gitattributes` im Projekt-Root
- Git global config richtig setzen
- Editor auf LF umstellen

**References:**
- ADR-0001: WSL2 Migration
- https://docs.github.com/en/get-started/getting-started-with-git/configuring-git-to-handle-line-endings

---

### 2. Git Performance auf NTFS/9P langsam

**Symptom:**
```
git status dauert 3-10 Sekunden
git diff extrem langsam
git add/commit verzögert
```

**Diagnose:**
- Repository liegt in `/mnt/c/` oder `/mnt/d/` (Windows NTFS)
- 9P-Dateisystem-Protokoll zu langsam für Git

**Lösung:**
```bash
# Migration zu nativem WSL2-Dateisystem
cd ~
git clone <repository-url> 03_Git/02_Python/07_OrderPilot-AI
cd 03_Git/02_Python/07_OrderPilot-AI

# Alte Location kann nach Validierung gelöscht werden
```

**Performance-Vergleich:**
| Operation | NTFS (/mnt/d/) | ext4 (~/) | Verbesserung |
|-----------|----------------|-----------|--------------|
| git status | ~800ms | ~150ms | ~5.3x |
| git diff | ~2-3s | ~400ms | ~5-7x |

**Prevention:**
- Alle aktiven Entwicklungs-Repos in WSL2-Home
- NTFS nur für Archive/Backups nutzen

**References:**
- ADR-0001: WSL2 Migration

---

## Python Environment

### 3. Import Errors trotz installierter Packages

**Symptom:**
```python
ModuleNotFoundError: No module named 'alpaca'
# Oder
ImportError: cannot import name 'TradingClient' from 'alpaca'
```

**Diagnose:**
- Falsches Virtual Environment aktiv
- Package in anderem Environment installiert
- PATH zeigt auf falschen Python-Interpreter

**Lösung:**
```bash
# 1. Prüfe aktuelles Environment
which python
python --version
pip list | grep alpaca

# 2. Richtiges Environment aktivieren
source .venv/bin/activate
# oder bei uv:
source .wsl_venv/bin/activate

# 3. Packages neu installieren falls nötig
uv pip install -e .

# 4. Verify
python -c "import alpaca; print(alpaca.__version__)"
```

**Prevention:**
- Immer Virtual Environment aktivieren vor Arbeit
- `.venv` oder `.wsl_venv` im Projekt-Root
- Shell-Prompt zeigt aktuelles Environment

---

### 4. pyproject.toml Syntax Error

**Symptom:**
```
ERROR: Failed to build package from pyproject.toml
TOML parsing error: ...
```

**Diagnose:**
- Ungültiges TOML-Format
- Fehlende Quotes um Strings
- Falsche Einrückung
- Ungültige Escape-Sequenzen

**Lösung:**
```bash
# 1. Validiere TOML-Syntax
uv pip install toml-cli
toml-cli check pyproject.toml

# 2. Typische Fehler prüfen:
# - Strings ohne Quotes
# - Backslashes ohne Escaping
# - Falsche Array-Syntax

# 3. Korrigiere Datei
# Beispiel: src = "my\\path" → src = "my/path" oder "my\\\\path"
```

**Häufige Fehler:**
```toml
# ❌ FALSCH
name = my-package
path = C:\Users\...

# ✅ RICHTIG
name = "my-package"
path = "C:/Users/..."
# oder
path = "C:\\Users\\..."
```

**Prevention:**
- Editor mit TOML-Syntax-Highlighting
- Pre-commit Hook für TOML-Validierung
- CI-Check für pyproject.toml

---

## Dependencies & Packages

### 5. Dependency Resolution Conflicts

**Symptom:**
```
ERROR: Cannot install package-a and package-b
  package-a requires numpy>=1.20,<1.25
  package-b requires numpy>=1.25
```

**Diagnose:**
- Inkompatible Versionsanforderungen
- Transitive Dependencies kollidieren

**Lösung:**
```bash
# 1. Analyse mit uv
uv pip tree
uv pip check

# 2. Finde konfligierende Packages
uv pip show package-a package-b

# 3. Optionen:
# a) Update auf kompatible Versionen
uv pip install "package-a>=2.0" "package-b>=3.0"

# b) Pin auf funktionierende Version
# pyproject.toml:
dependencies = [
    "package-a>=2.0,<3.0",
    "package-b>=3.0,<4.0",
    "numpy>=1.25,<1.26"  # Explizit pinnen
]

# 4. Lock File regenerieren
uv pip compile pyproject.toml -o requirements.lock
```

**Prevention:**
- Regelmäßig Dependencies aktualisieren
- Lock Files verwenden
- CI testet mit minimalen & maximalen Versionen

---

## WSL2 & File System

### 6. Permission Denied in WSL2

**Symptom:**
```
chmod: changing permissions of 'file.sh': Operation not permitted
chown: changing ownership of 'file': Operation not permitted
```

**Diagnose:**
- Datei liegt auf Windows NTFS Mount (`/mnt/c/`, `/mnt/d/`)
- NTFS unterstützt keine Unix-Permissions vollständig

**Lösung:**
```bash
# 1. Prüfe Datei-Location
pwd
# Wenn /mnt/c/ oder /mnt/d/ → Problem!

# 2. Verschiebe zu nativem WSL2-Dateisystem
cp /mnt/d/script.sh ~/script.sh
chmod +x ~/script.sh

# 3. Für systemd Services: MUSS in WSL2-Home sein
sudo cp service-file.service /etc/systemd/system/
```

**Prevention:**
- Entwicklungs-Code in `~/` statt `/mnt/`
- Windows-Dateien nur lesen, nicht ausführen

---

### 7. Moltbot Gateway Service kann nicht starten

**Symptom:**
```bash
systemctl --user status clawdbot-gateway
● clawdbot-gateway.service - failed
   Error: Cannot execute binary in /mnt/d/...
```

**Diagnose:**
- Service-Binary liegt auf NTFS
- systemd kann keine Binaries von NTFS ausführen
- PATH-Variable zeigt auf NTFS

**Lösung:**
```bash
# 1. Prüfe Service-Datei
cat ~/.config/systemd/user/clawdbot-gateway.service

# 2. Sicherstellen dass Binary in WSL2-Home ist
which clawdbot
# Sollte: /home/user/.clawdbot/bin/clawdbot

# 3. Service neu installieren
~/.clawdbot/bin/clawdbot gateway install

# 4. Daemon reload
systemctl --user daemon-reload
systemctl --user restart clawdbot-gateway
```

**Prevention:**
- Moltbot IMMER via CLI-Installer installieren
- Nie manuell von NTFS kopieren
- ADR-0001 Migration-Steps befolgen

---

## Moltbot/Clawdbot

### 8. Gateway nicht erreichbar (Connection Refused)

**Symptom:**
```bash
clawdbot gateway status
RPC probe: failed
  gateway closed (1006 abnormal closure)
```

**Diagnose:**
- Gateway nicht gestartet
- Port-Konflikt
- Firewall blockiert

**Lösung:**
```bash
# 1. Prüfe Gateway Status
systemctl --user status clawdbot-gateway

# 2. Falls stopped → Starten
systemctl --user start clawdbot-gateway

# 3. Prüfe Logs
journalctl --user -u clawdbot-gateway -f

# 4. Port-Check
netstat -tlnp | grep 18789
# Sollte Listening zeigen

# 5. Health Check
clawdbot doctor --non-interactive
```

**Häufige Ursachen:**
- Service nicht enabled: `systemctl --user enable clawdbot-gateway`
- Node.js Version zu alt: Nutze embedded Node (`~/.clawdbot/tools/node-v22.22.0`)
- Config fehlt: `clawdbot config set gateway.mode local`

**Prevention:**
- Service auto-start: `systemctl --user enable`
- Regelmäßig `clawdbot doctor` laufen lassen

---

### 9. Anthropic API Key expired/invalid

**Symptom:**
```
Model auth: anthropic:claude-cli: expiring (1h)
```

**Diagnose:**
- Claude CLI Token abgelaufen
- Moltbot kann nicht auf Anthropic API zugreifen

**Lösung:**
```bash
# 1. Neuen Token generieren
claude setup-token

# 2. Verify
claude --version
claude auth status

# 3. Gateway neu starten
systemctl --user restart clawdbot-gateway

# 4. Test
clawdbot doctor | grep anthropic
```

**Prevention:**
- `claude setup-token` regelmäßig erneuern
- Monitoring für Token-Ablauf einrichten

---

## Alpaca API

### 10. 401 Unauthorized bei Alpaca API Calls

**Symptom:**
```python
alpaca_trade_api.rest.APIError: 401 Unauthorized
```

**Diagnose:**
- API Keys falsch oder abgelaufen
- Falsche Environment-Variablen
- Paper vs Live Keys verwechselt

**Lösung:**
```bash
# 1. Prüfe Environment Variablen
echo $ALPACA_API_KEY
echo $ALPACA_SECRET_KEY
echo $ALPACA_BASE_URL

# 2. Verify Keys auf Alpaca Dashboard
# https://app.alpaca.markets/

# 3. Setze korrekte URLs
# Paper Trading:
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"
# Live Trading:
export ALPACA_BASE_URL="https://api.alpaca.markets"

# 4. Test mit curl
curl -X GET "https://paper-api.alpaca.markets/v2/account" \
  -H "APCA-API-KEY-ID: $ALPACA_API_KEY" \
  -H "APCA-API-SECRET-KEY: $ALPACA_SECRET_KEY"
```

**Prevention:**
- Keys in `.env` (nicht in Git!)
- Immer Paper-Keys für Entwicklung
- CI/CD verwendet separate Test-Keys

**References:**
- `docs/alpaca/` für API-Dokumentation
- CLAUDE.md Trading-Sicherheitsregeln

---

### 11. Rate Limit Exceeded

**Symptom:**
```
alpaca_trade_api.rest.APIError: 429 Too Many Requests
Retry-After: 60
```

**Diagnose:**
- Zu viele API-Requests in kurzer Zeit
- Alpaca Rate Limits überschritten
- Missing exponential backoff

**Lösung:**
```python
# Implementiere Retry-Logik mit Backoff
import time
from alpaca.common.exceptions import APIError

def api_call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except APIError as e:
            if e.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 60))
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            raise
    raise Exception("Max retries exceeded")

# Nutze Caching für häufige Abfragen
from functools import lru_cache

@lru_cache(maxsize=100)
def get_asset_info(symbol):
    return trading_client.get_asset(symbol)
```

**Alpaca Rate Limits (Paper Trading):**
- 200 requests per minute per API key
- Burst: 200 requests immediately
- Websocket: Unlimited (use for real-time data!)

**Prevention:**
- Batching: Mehrere Symbols in einem Call
- Caching: Wiederverwendung von Daten
- WebSocket: Für Streaming statt Polling
- Exponential Backoff implementieren

---

## Testing & CI/CD

### 12. Tests schlagen in CI fehl, lokal funktionieren sie

**Symptom:**
```
pytest: FAILED (some tests failed locally pass)
CI/CD: Test failed with different error
```

**Diagnose:**
- Environment-Variablen fehlen in CI
- Dependencies unterschiedlich
- File paths Windows vs Linux
- Timezone/Locale unterschiedlich

**Lösung:**
```bash
# 1. Reproduziere CI-Umgebung lokal
docker run -it python:3.11 bash
cd /app
pip install -e .
pytest

# 2. Prüfe Dependencies
pip freeze > requirements-ci.txt
# Vergleiche mit requirements.lock

# 3. Prüfe Environment
env | sort
# Setze fehlende Variablen in CI-Config

# 4. Path-Probleme
# ❌ Absolut: /home/user/project/file
# ✅ Relativ: Path(__file__).parent / "file"

# 5. Mock External Services
# API-Calls, Datenbank, Filesystem
```

**Prevention:**
- `pyproject.toml` mit pinned dependencies
- `.env.example` für alle benötigten Variablen
- Tests nutzen `pytest.fixtures` für Setup
- Mock externe Dependencies

---

## 📚 Weiterführende Ressourcen

- **ADRs:** `../adr/` für Architektur-Entscheidungen
- **Troubleshooting:** `troubleshooting.md` für systematische Problemlösung
- **Development Setup:** `development-setup.md` für Umgebungs-Setup
- **Alpaca Docs:** `../alpaca/docs.alpaca.markets/` für API-Details

---

## 🤝 Beitragen

Wenn du einen neuen Error Pattern gefunden hast:

1. **Dokumentiere:**
   - Symptom (was sah man?)
   - Diagnose (was war die Ursache?)
   - Lösung (wie wurde es behoben?)
   - Prevention (wie vermeiden?)

2. **Kategorisiere:**
   - Welche Kategorie passt?
   - Neuer Abschnitt nötig?

3. **Update:**
   - Nummerierung fortsetzen
   - Index aktualisieren
   - Commit mit Message: `docs: add error pattern #XX`

---

**Fragen?** Öffne ein Issue mit Label `documentation`.
**Veralteter Inhalt?** Erstelle PR mit Korrektur.

**Letzte Aktualisierung:** 2026-01-28
