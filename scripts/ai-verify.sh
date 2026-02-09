#!/bin/bash
# AI Verification Script for Large Scale Projects (Python)
# Usage: ./scripts/ai-verify.sh [module_path]

echo "--- 🔍 QA Verification Started ---"

# Ensure headless-friendly test env (matplotlib/Qt)
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/matplotlib
export QT_QPA_PLATFORM=offscreen
mkdir -p "$MPLCONFIGDIR"

# 1. Syntax & Linting
echo "Step 1: Linting check..."
LINT_TARGETS="${AG_LINT_TARGETS:-${LINT_TARGETS:-src/}}"
read -r -a LINT_TARGET_ARR <<< "$LINT_TARGETS"
python -m flake8 "${LINT_TARGET_ARR[@]}" --jobs=1 || { echo "❌ Linting failed"; exit 1; }

# 2. Type Check (besonders wichtig bei 250k LOC)
echo "Step 2: Type checking..."
if python - <<'PY'
import importlib.util, sys
sys.exit(0 if importlib.util.find_spec("mypy") else 1)
PY
then
    python -m mypy src/ --ignore-missing-imports --no-error-summary || { echo "❌ Type check failed"; exit 1; }
else
    echo "⚠️  mypy not installed; skipping type check."
fi

# 3. Unit Tests (Scoped auf das geänderte Modul)
TEST_TARGETS="${AG_TEST_TARGETS:-${TEST_TARGETS:-}}"
if [ -n "$TEST_TARGETS" ]; then
    echo "Step 3: Running targeted tests: $TEST_TARGETS"
    read -r -a TEST_TARGET_ARR <<< "$TEST_TARGETS"
    python -m pytest "${TEST_TARGET_ARR[@]}" -v --tb=short
elif [ -z "$1" ]; then
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
