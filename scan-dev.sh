#!/bin/bash
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== WSL2 Basis ===${NC}"
grep -qi microsoft /proc/version && echo -e "${GREEN}✓ WSL2${NC}" || echo -e "${RED}✗ Kein WSL${NC}"
grep VERSION_ID /etc/os-release | grep -q "24.04" && echo -e "${GREEN}✓ Ubuntu 24.04${NC}" || echo -e "${YELLOW}⚠ Andere Version${NC}"
systemctl --version &>/dev/null && echo -e "${GREEN}✓ Systemd${NC}" || echo -e "${YELLOW}⚠ Kein Systemd${NC}"

echo -e "\n${BLUE}=== Performance-Check ===${NC}"
if [ -d "/mnt/d/03_Git/02_Python/07_OrderPilot-AI" ]; then
    echo -e "${YELLOW}⚠ OrderPilot-AI liegt auf D: (Windows) → LANGSAM!${NC}"
    du -sh "/mnt/d/03_Git/02_Python/07_OrderPilot-AI" 2>/dev/null | awk '{print "  Größe: " $1}'
fi
[ -d "$HOME/projects" ] && echo -e "${GREEN}✓ ~/projects/ existiert${NC}" || echo -e "${YELLOW}⚠ ~/projects/ fehlt${NC}"

echo -e "\n${BLUE}=== Docker ===${NC}"
docker info &>/dev/null && echo -e "${GREEN}✓ Docker läuft${NC}" || echo -e "${RED}✗ Docker nicht erreichbar${NC}"
docker compose version &>/dev/null && echo -e "${GREEN}✓ Docker Compose${NC}" || echo -e "${YELLOW}⚠ Compose fehlt${NC}"

echo -e "\n${BLUE}=== Python Stack ===${NC}"
command -v python3 &>/dev/null && echo -e "${GREEN}✓ Python: $(python3 --version 2>&1 | awk '{print $2}')${NC}" || echo -e "${RED}✗ Kein Python3${NC}"
command -v uv &>/dev/null && echo -e "${GREEN}✓ uv installiert${NC}" || echo -e "${YELLOW}⚠ uv fehlt${NC}"
command -v git &>/dev/null && echo -e "${GREEN}✓ Git: $(git --version | awk '{print $3}')${NC}" || echo -e "${RED}✗ Git fehlt${NC}"

echo -e "\n${BLUE}=== AI Tools ===${NC}"
command -v claude &>/dev/null && echo -e "${GREEN}✓ Claude Code installiert${NC}" || echo -e "${YELLOW}⚠ Claude Code fehlt${NC}"
[ -n "${ANTHROPIC_API_KEY:-}" ] && echo -e "${YELLOW}⚠ ANTHROPIC_API_KEY gesetzt${NC}" || echo -e "${GREEN}✓ API-Key leer (Subscription)${NC}"
command -v node &>/dev/null && echo -e "${GREEN}✓ Node.js: $(node --version)${NC}" || echo -e "${YELLOW}⚠ Node.js fehlt${NC}"

echo -e "\n${BLUE}=== Quality Tools ===${NC}"
command -v ruff &>/dev/null && echo -e "${GREEN}✓ Ruff installiert${NC}" || echo -e "${YELLOW}⚠ Ruff fehlt${NC}"

echo -e "\n${BLUE}=== OrderPilot-AI ===${NC}"
if [ -d "/mnt/d/03_Git/02_Python/07_OrderPilot-AI" ]; then
    cd "/mnt/d/03_Git/02_Python/07_OrderPilot-AI"
    [ -d ".git" ] && echo -e "${GREEN}✓ Git Repo${NC}" || echo -e "${RED}✗ Kein Git${NC}"
    [ -f "pyproject.toml" ] && echo -e "${GREEN}✓ pyproject.toml${NC}" || echo -e "${YELLOW}⚠ Kein pyproject.toml${NC}"
fi

echo -e "\n${BLUE}=== Fertig ===${NC}"
