# 🔄 OrderPilot-AI Migration Checkliste
**Start:** 2025-01-28 16:30  
**Ziel:** Migration von `/mnt/d/03_Git/02_Python/07_OrderPilot-AI` → `~/03_Git/02_Python/07_OrderPilot-AI`

---

## Phase 0: Vorbereitung & Backup ⏳
- [ ] 0.1 - Git Remote URL gesichert
- [ ] 0.2 - Git Branch notiert
- [ ] 0.3 - Git Status geprüft (clean)
- [ ] 0.4 - Projekt-Größe erfasst

## Phase 1: WSL2-Optimierung ⏳
- [ ] 1.1 - /etc/wsl.conf optimiert
- [ ] 1.2 - ~/.wslconfig erstellt (Windows)
- [ ] 1.3 - WSL neu gestartet
- [ ] 1.4 - Git Cross-Platform konfiguriert
- [ ] 1.5 - ~/03_Git/02_Python Verzeichnis erstellt

## Phase 2: OrderPilot-AI Migration ⏳
- [ ] 2.1 - Frischer Git-Clone nach ~/03_Git/02_Python/07_OrderPilot-AI
- [ ] 2.2 - .gitattributes erstellt
- [ ] 2.3 - Migration validiert
- [ ] 2.4 - Dateianzahl verglichen

## Phase 3: Python-Umgebung ⏳
- [ ] 3.1 - uv Package Manager installiert
- [ ] 3.2 - pyproject.toml geprüft/erstellt
- [ ] 3.3 - Dependencies installiert (uv sync)
- [ ] 3.4 - Ruff konfiguriert
- [ ] 3.5 - pytest konfiguriert
- [ ] 3.6 - Pre-commit hooks eingerichtet

## Phase 4: Claude Code ⏳
- [ ] 4.1 - CLAUDE.md erstellt
- [ ] 4.2 - .mcp.json konfiguriert
- [ ] 4.3 - ANTHROPIC_API_KEY Check
- [ ] 4.4 - Claude Code getestet

## Phase 5: Moltbot Installation ⏳
- [ ] 5.1 - Node.js 22+ installiert
- [ ] 5.2 - Moltbot global installiert
- [ ] 5.3 - Moltbot onboarded & Daemon eingerichtet
- [ ] 5.4 - Moltbot konfiguriert
- [ ] 5.5 - Moltbot mit Projekt getestet

## Phase 6: Wissensdatenbank ⏳
- [ ] 6.1 - docs/adr/ Struktur erstellt
- [ ] 6.2 - docs/knowledge/ erstellt
- [ ] 6.3 - Erste ADR (Migration) geschrieben
- [ ] 6.4 - error-patterns.md erstellt

## Phase 7: VS Code Setup ⏳
- [ ] 7.1 - VS Code Remote-WSL geöffnet
- [ ] 7.2 - Extensions installiert
- [ ] 7.3 - .vscode/settings.json erstellt

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
**Nächster Schritt:** Phase 0 - Vorbereitung
