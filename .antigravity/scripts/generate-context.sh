#!/bin/bash
# ============================================================
# Generate Repomix Context - WSL2 Version
# Packages entire codebase into AI-friendly format
# ============================================================

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "============================================================"
echo "Repomix Context Generation (WSL2)"
echo "============================================================"

# Check if repomix is installed
if ! command -v repomix &> /dev/null; then
    echo "[WARN] repomix not found. Installing..."
    npm install -g repomix
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install repomix. Please run: npm install -g repomix"
        exit 1
    fi
fi

# Create context directory if not exists
mkdir -p "$PROJECT_ROOT/.antigravity/context"

# Generate context file
echo "[RUN] Generating codebase context..."

cd "$PROJECT_ROOT"
repomix \
    --ignore "**/*.json" \
    --ignore "**/*.pyc" \
    --ignore "**/__pycache__/**" \
    --ignore "**/logs/**" \
    --ignore "**/node_modules/**" \
    --ignore "**/.venv/**" \
    --ignore "**/.wsl_venv/**" \
    --ignore "**/dist/**" \
    --ignore "**/build/**" \
    --ignore "**/*.egg-info/**" \
    --ignore "**/03_JSON/**" \
    --ignore "**/docs/alpaca/**" \
    --output ".antigravity/context/codebase-context.txt"

if [ $? -eq 0 ]; then
    SIZE=$(stat -f%z ".antigravity/context/codebase-context.txt" 2>/dev/null || stat -c%s ".antigravity/context/codebase-context.txt" 2>/dev/null)
    echo "[OK] Context file generated: .antigravity/context/codebase-context.txt"
    echo "[INFO] Size: $SIZE bytes"
else
    echo "[FAIL] repomix failed. Check output above."
fi

echo "============================================================"
