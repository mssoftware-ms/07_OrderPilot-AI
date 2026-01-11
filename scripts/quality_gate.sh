#!/bin/bash
# Quality gate script for OrderPilot-AI
# Runs: ruff format, ruff check, pytest, line-limit check
# Exit code 0 = all pass, non-zero = failure

set -e

echo "🔍 OrderPilot-AI Quality Gate"
echo "=============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Track failures
FAILED=0

# Step 1: Ruff format check
echo -e "\n${YELLOW}Step 1/4: Ruff Format Check${NC}"
if ruff format --check . 2>/dev/null; then
    echo -e "${GREEN}✅ Format check passed${NC}"
else
    echo -e "${RED}❌ Format issues found. Run: ruff format .${NC}"
    FAILED=1
fi

# Step 2: Ruff linting
echo -e "\n${YELLOW}Step 2/4: Ruff Linting${NC}"
if ruff check . 2>/dev/null; then
    echo -e "${GREEN}✅ Linting passed${NC}"
else
    echo -e "${RED}❌ Linting issues found. Run: ruff check . --fix${NC}"
    FAILED=1
fi

# Step 3: Pytest (quick)
echo -e "\n${YELLOW}Step 3/4: Pytest${NC}"
if pytest -q --tb=no 2>/dev/null; then
    echo -e "${GREEN}✅ Tests passed${NC}"
else
    echo -e "${RED}❌ Tests failed${NC}"
    FAILED=1
fi

# Step 4: Line limit check
echo -e "\n${YELLOW}Step 4/4: Line Limit Check (≤600)${NC}"
if python scripts/check_line_limit.py 2>/dev/null; then
    echo -e "${GREEN}✅ Line limit check passed${NC}"
else
    echo -e "${RED}❌ Files exceed 600 lines${NC}"
    FAILED=1
fi

echo -e "\n=============================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All quality gates passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Quality gate FAILED${NC}"
    exit 1
fi
