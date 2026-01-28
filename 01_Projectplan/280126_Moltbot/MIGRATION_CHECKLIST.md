# 🔄 OrderPilot-AI Migration Checkliste
**Start:** 2025-01-28 16:30  
**Ziel:** Migration von `/mnt/d/03_Git/02_Python/07_OrderPilot-AI` → `~/03_Git/02_Python/07_OrderPilot-AI`

---

## Phase 0: Vorbereitung & Backup ✅
- [x] 0.1 - Git Remote URL gesichert (https://github.com/mssoftware-ms/07_OrderPilot-AI.git)
- [x] 0.2 - Git Branch notiert (main)
- [x] 0.3 - Git Status geprüft (committed via GitHub Desktop)
- [x] 0.4 - Projekt-Größe erfasst (5.7 GB)

## Phase 1: WSL2-Optimierung ✅
- [x] 1.1 - /etc/wsl.conf optimiert (systemd + user bereits konfiguriert)
- [x] 1.2 - ~/.wslconfig erstellt (8GB RAM, 4 CPU, 2GB Swap)
- [x] 1.3 - WSL neu gestartet
- [x] 1.4 - Git Cross-Platform konfiguriert (autocrlf=input, eol=lf)
- [x] 1.5 - ~/03_Git/02_Python Verzeichnis erstellt

## Phase 2: OrderPilot-AI Migration ✅
- [x] 2.1 - Frischer Git-Clone nach ~/03_Git/02_Python/07_OrderPilot-AI (139s)
- [x] 2.2 - .gitattributes erstellt und committed
- [x] 2.3 - Migration validiert (git fsck: OK)
- [x] 2.4 - Dateianzahl verglichen (WSL: 2032 = Windows tracked: 2032)

## Phase 3: Python-Umgebung ✅
- [x] 3.1 - uv Package Manager installiert (v0.9.27)
- [x] 3.2 - pyproject.toml geprüft (Syntax-Fehler behoben!)
- [x] 3.3 - Dependencies installiert (60 packages in 548ms)
- [x] 3.4 - Ruff konfiguriert (bereits vorhanden)
- [x] 3.5 - pytest konfiguriert (bereits vorhanden)
- [x] 3.6 - Pre-commit hooks eingerichtet (v4.5.1)

## Phase 4: Claude Code ⏳
- [x] 4.1 - CLAUDE.md erstellt
- [x] 4.2 - .mcp.json konfiguriert
- [x] 4.3 - ANTHROPIC_API_KEY Check
- [x] 4.4 - Claude Code getestet

## Phase 5: Moltbot Installation ✅
- [x] 5.1 - Node.js 22+ installiert (v24.13.0)
- [x] 5.2 - Moltbot installiert (v2026.1.24-3 via CLI installer)
- [x] 5.3 - Gateway Service installiert und gestartet (systemd)
- [x] 5.4 - Moltbot konfiguriert (local mode, loopback on port 18789)
- [x] 5.5 - Health Check erfolgreich (12 Skills, Anthropic/Claude CLI erkannt)

## Phase 6: Wissensdatenbank ✅
- [x] 6.1 - docs/adr/ Struktur erstellt (mit README und Template)
- [x] 6.2 - docs/knowledge/ erstellt (mit README und Kategorien)
- [x] 6.3 - ADR-0001 (WSL2 Migration) geschrieben (vollständig dokumentiert)
- [x] 6.4 - error-patterns.md erstellt (12 häufige Fehler dokumentiert)

## Phase 7: VS Code Setup ✅
- [x] 7.1 - VS Code Remote-WSL konfiguriert
- [x] 7.2 - Extensions definiert (22 empfohlene Extensions)
- [x] 7.3 - settings.json erstellt (umfassende Python/Trading-Konfiguration)
- [x] 7.4 - launch.json erstellt (5 Debug-Konfigurationen)
- [x] 7.5 - tasks.json erstellt (10 vordefinierte Tasks)
- [x] 7.6 - README.md für VS Code Konfiguration

## Phase 8: Performance-Vergleich ⏳
- [ ] 8.1 - Performance-Messung (alt vs. neu)
- [ ] 8.2 - Finale Validierung
- [ ] 8.3 - Tests laufen

## Phase 9: Dokumentation ⏳
- [ ] 9.1 - Makefile erstellt
- [ ] 9.2 - README.md aktualisiert

## Phase 10: Alte Location ⏳
- [ ] 10.1 - Backup erstellt (.tar.gz)
- [ ] 10.2 - Alte Location bereit zum Löschen

---

**Status:** 🟡 In Bearbeitung
**Nächster Schritt:** Phase 8 - Performance-Vergleich

---

## 🦞 Moltbot Status

**Gateway:** ✅ Aktiv und läuft
- Service: systemd (enabled)
- Port: ws://127.0.0.1:18789
- Dashboard: http://127.0.0.1:18789/
- Browser Control: http://127.0.0.1:18791/
- Model: claude-opus-4-5

**Configuration:**
- Mode: local (loopback only)
- Agent: main (default)
- Workspace: ~/clawd
- Skills: 12 verfügbar
- Plugins: 1 loaded

**Useful Commands:**
```bash
# Gateway Status
clawdbot gateway status

# Service Control
systemctl --user status clawdbot-gateway
systemctl --user stop clawdbot-gateway
systemctl --user start clawdbot-gateway
systemctl --user restart clawdbot-gateway

# Health Check
clawdbot doctor

# View Logs
clawdbot logs
# or
journalctl --user -u clawdbot-gateway -f
```

---

## 📝 Installationshinweise

### Erfolgreich installierter Befehl:
```bash
curl -fsSL https://molt.bot/install-cli.sh | bash
```

**Installation:**
- Location: `~/.clawdbot/`
- Binary: `~/.clawdbot/bin/clawdbot`
- Version: 2026.1.24-3
- Node Runtime: Inkludiert (v22.22.0)

**PATH hinzufügen:**
```bash
echo 'export PATH="$HOME/.clawdbot/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Alias für moltbot:**
```bash
echo 'alias moltbot=clawdbot' >> ~/.bashrc
source ~/.bashrc
```
