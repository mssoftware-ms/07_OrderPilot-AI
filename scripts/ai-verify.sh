#!/bin/bash
# AI Verification Script for Large Scale Projects (Python)
# Usage: ./scripts/ai-verify.sh [module_path]

echo "--- 🔍 QA Verification Started ---"

# 1. Syntax & Linting
echo "Step 1: Linting check..."
python -m flake8 src/ --max-line-length=120 --ignore=E501,W503 || { echo "❌ Linting failed"; exit 1; }

# 2. Type Check (besonders wichtig bei 250k LOC)
echo "Step 2: Type checking..."
python -m mypy src/ --ignore-missing-imports --no-error-summary || { echo "❌ Type check failed"; exit 1; }

# 3. Unit Tests (Scoped auf das geänderte Modul)
if [ -z "$1" ]; then
    echo "Step 3: Running all tests (No module specified)..."
    python -m pytest tests/ -v --tb=short
else
    echo "Step 3: Running scoped tests for: $1"
    python -m pytest "$1" -v --tb=short
fi

if [ $? -eq 0 ]; then
    echo "--- ✅ All checks passed! ---"
    exit 0
else
    echo "--- ❌ Tests failed. Check logs above. ---"
    exit 1
fi
