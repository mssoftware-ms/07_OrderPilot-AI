#!/bin/bash

################################################################################
# CEL Editor UI Tests - Execution Script
#
# This script runs pytest tests for CEL Editor UI fixes (Issues #1 and #5).
#
# Usage:
#   ./tests/run_ui_tests.sh [options]
#
# Options:
#   --all              Run all tests (default)
#   --issue1           Run only Issue #1 tests (UI-Duplikate)
#   --issue5           Run only Issue #5 tests (Variablenwerte)
#   --integration      Run only integration tests
#   --performance      Run only performance tests
#   --edge-cases       Run only edge case tests
#   --coverage         Run with coverage report
#   --html             Generate HTML test report
#   --verbose          Verbose output
#   --help             Show this help message
#
# Examples:
#   ./tests/run_ui_tests.sh --all --verbose
#   ./tests/run_ui_tests.sh --issue1 --coverage
#   ./tests/run_ui_tests.sh --performance
#
# Author: OrderPilot-AI Development Team
# Created: 2026-01-28
################################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_ALL=true
RUN_ISSUE1=false
RUN_ISSUE5=false
RUN_INTEGRATION=false
RUN_PERFORMANCE=false
RUN_EDGE_CASES=false
COVERAGE=false
HTML_REPORT=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            shift
            ;;
        --issue1)
            RUN_ALL=false
            RUN_ISSUE1=true
            shift
            ;;
        --issue5)
            RUN_ALL=false
            RUN_ISSUE5=true
            shift
            ;;
        --integration)
            RUN_ALL=false
            RUN_INTEGRATION=true
            shift
            ;;
        --performance)
            RUN_ALL=false
            RUN_PERFORMANCE=true
            shift
            ;;
        --edge-cases)
            RUN_ALL=false
            RUN_EDGE_CASES=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            head -n 30 "$0" | tail -n +3
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print header
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   CEL Editor UI Tests - Test Runner                     ║${NC}"
echo -e "${BLUE}║                        Issues #1 and #5                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
python -c "import pytest" 2>/dev/null || {
    echo -e "${RED}ERROR: pytest not installed${NC}"
    echo "Install with: pip install pytest pytest-qt"
    exit 1
}

python -c "import PyQt6" 2>/dev/null || {
    echo -e "${RED}ERROR: PyQt6 not installed${NC}"
    echo "Install with: pip install PyQt6"
    exit 1
}

echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# Build pytest command
PYTEST_CMD="pytest tests/ui/test_cel_editor_ui_fixes.py"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v --tb=short"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src/ui --cov=src/core/variables --cov-report=term-missing"

    if [ "$HTML_REPORT" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi
fi

# Add HTML report
if [ "$HTML_REPORT" = true ] && [ "$COVERAGE" = false ]; then
    PYTEST_CMD="$PYTEST_CMD --html=tests/report_ui_tests.html --self-contained-html"
fi

# Function to run test class
run_test_class() {
    local class_name=$1
    local description=$2

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Running: $description${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if eval "$PYTEST_CMD::$class_name"; then
        echo -e "${GREEN}✓ $description PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ $description FAILED${NC}"
        return 1
    fi
}

# Track failures
FAILURES=0

# Run tests based on options
if [ "$RUN_ALL" = true ]; then
    echo -e "${YELLOW}Running ALL tests...${NC}"
    echo ""

    run_test_class "TestUIStructure" "Issue #1: UI Structure Tests" || ((FAILURES++))
    echo ""

    run_test_class "TestTabFunctionality" "Issue #1: Tab Functionality Tests" || ((FAILURES++))
    echo ""

    run_test_class "TestVariableValues" "Issue #5: Variable Values Tests" || ((FAILURES++))
    echo ""

    run_test_class "TestVariableRefresh" "Issue #5: Variable Refresh Tests" || ((FAILURES++))
    echo ""

    run_test_class "TestIntegration" "Integration Tests" || ((FAILURES++))
    echo ""

    run_test_class "TestEdgeCases" "Edge Case Tests" || ((FAILURES++))
    echo ""

    run_test_class "TestPerformance" "Performance Tests" || ((FAILURES++))

else
    if [ "$RUN_ISSUE1" = true ]; then
        run_test_class "TestUIStructure" "Issue #1: UI Structure Tests" || ((FAILURES++))
        echo ""
        run_test_class "TestTabFunctionality" "Issue #1: Tab Functionality Tests" || ((FAILURES++))
    fi

    if [ "$RUN_ISSUE5" = true ]; then
        run_test_class "TestVariableValues" "Issue #5: Variable Values Tests" || ((FAILURES++))
        echo ""
        run_test_class "TestVariableRefresh" "Issue #5: Variable Refresh Tests" || ((FAILURES++))
    fi

    if [ "$RUN_INTEGRATION" = true ]; then
        run_test_class "TestIntegration" "Integration Tests" || ((FAILURES++))
    fi

    if [ "$RUN_EDGE_CASES" = true ]; then
        run_test_class "TestEdgeCases" "Edge Case Tests" || ((FAILURES++))
    fi

    if [ "$RUN_PERFORMANCE" = true ]; then
        run_test_class "TestPerformance" "Performance Tests" || ((FAILURES++))
    fi
fi

# Print summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                            TEST SUMMARY                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""

    if [ "$COVERAGE" = true ] && [ "$HTML_REPORT" = true ]; then
        echo -e "${YELLOW}Coverage report: htmlcov/index.html${NC}"
    fi

    if [ "$HTML_REPORT" = true ]; then
        echo -e "${YELLOW}HTML report: tests/report_ui_tests.html${NC}"
    fi

    exit 0
else
    echo -e "${RED}✗ $FAILURES TEST SUITE(S) FAILED${NC}"
    echo ""
    echo -e "${YELLOW}Review failed tests above for details.${NC}"
    exit 1
fi
