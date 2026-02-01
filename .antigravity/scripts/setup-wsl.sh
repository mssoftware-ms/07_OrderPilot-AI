#!/bin/bash
# ============================================================
# Antigravity WSL2 Setup Script
# Installs all required tools in WSL2 environment
# ============================================================

echo "============================================================"
echo "Antigravity WSL2 Setup"
echo "============================================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check for .wsl_venv
WSL_VENV="$PROJECT_ROOT/.wsl_venv"
if [ -d "$WSL_VENV" ]; then
    echo "[OK] Found .wsl_venv at $WSL_VENV"
    source "$WSL_VENV/bin/activate"
    echo "[OK] Activated virtual environment"
else
    echo "[WARN] .wsl_venv not found at $WSL_VENV"
    echo "       Creating new virtual environment..."
    python3 -m venv "$WSL_VENV"
    source "$WSL_VENV/bin/activate"
    echo "[OK] Created and activated .wsl_venv"
fi

echo ""
echo "Installing Python dependencies..."
echo "------------------------------------------------------------"

# Python linting/testing tools
pip install --upgrade pip
pip install flake8 mypy pytest pytest-cov

echo ""
echo "Installing Node.js tools..."
echo "------------------------------------------------------------"

# Check for npm
if command -v npm &> /dev/null; then
    echo "[OK] npm found"

    # Install repomix globally
    if ! command -v repomix &> /dev/null; then
        echo "[INSTALL] repomix..."
        npm install -g repomix
    else
        echo "[OK] repomix already installed"
    fi
else
    echo "[WARN] npm not found!"
    echo "       Install Node.js first: sudo apt install nodejs npm"
    echo "       Then run this script again."
fi

echo ""
echo "============================================================"
echo "[DONE] Antigravity WSL2 Setup Complete!"
echo "============================================================"
echo ""
echo "Installed tools:"
echo "  - flake8 (linting)"
echo "  - mypy (type checking)"
echo "  - pytest (testing)"
echo "  - repomix (codebase context)"
echo ""
echo "Usage:"
echo "  ./antigravity.sh          # Main menu"
echo "  ./scripts/ai-verify.sh    # Run verification"
echo ""
