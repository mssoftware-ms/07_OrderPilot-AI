#!/bin/bash
# Run all tests for Regime-Based JSON Strategy System

set -e  # Exit on error

echo "============================================"
echo "Regime-Based JSON Strategy System - Test Suite"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-qt pytest-cov"
    exit 1
fi

# Create reports directory
mkdir -p test_reports

echo -e "${YELLOW}Running Unit Tests...${NC}"
echo "-----------------------------------"

# Run unit tests with coverage
pytest tests/ui/test_regime_set_builder.py \
    tests/core/test_dynamic_strategy_switching.py \
    tests/ui/test_backtest_worker.py \
    -v \
    --tb=short \
    --cov=src/ui/dialogs \
    --cov=src/core/tradingbot \
    --cov-report=html:test_reports/coverage_unit \
    --cov-report=term-missing \
    --junit-xml=test_reports/junit_unit.xml

UNIT_EXIT_CODE=$?

echo ""
echo -e "${YELLOW}Running Integration Tests...${NC}"
echo "-----------------------------------"

# Run integration tests
pytest tests/integration/test_regime_based_workflow.py \
    -v \
    --tb=short \
    --junit-xml=test_reports/junit_integration.xml

INTEGRATION_EXIT_CODE=$?

echo ""
echo "============================================"
echo "Test Results Summary"
echo "============================================"

if [ $UNIT_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Unit Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Unit Tests: FAILED${NC}"
fi

if [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Integration Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Integration Tests: FAILED${NC}"
fi

echo ""
echo "Reports generated in test_reports/"
echo "- coverage_unit/index.html - Unit test coverage report"
echo "- junit_unit.xml - Unit test JUnit report"
echo "- junit_integration.xml - Integration test JUnit report"

# Overall exit code
if [ $UNIT_EXIT_CODE -eq 0 ] && [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Some tests failed. See details above.${NC}"
    exit 1
fi
