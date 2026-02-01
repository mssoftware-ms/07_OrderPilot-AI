#!/bin/bash
# ============================================================
# Antigravity AI Verify Script - WSL2 Version
# Auto-detecting verification for Python projects
# ============================================================

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Activate .wsl_venv if present
WSL_VENV="$PROJECT_ROOT/.wsl_venv"
if [ -d "$WSL_VENV" ]; then
    source "$WSL_VENV/bin/activate"
fi

# Run the Python verify script
cd "$PROJECT_ROOT"
python .antigravity/scripts/ai-verify.py "$@"
