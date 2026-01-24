#!/bin/bash

###############################################################################
# End-to-End Integration Test Runner
#
# Usage:
#   ./run_e2e_tests.sh [all|stage1|stage2|handoff|schema|perf|ui|quick]
#
# Examples:
#   ./run_e2e_tests.sh all          # All tests with coverage
#   ./run_e2e_tests.sh stage1       # Only Stage 1 tests
#   ./run_e2e_tests.sh quick        # Quick tests (exclude slow/ui)
###############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${PROJECT_ROOT}"

# Default mode
MODE="${1:-all}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}E2E Integration Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print section header
print_header() {
    echo -e "${YELLOW}▶ ${1}${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Generate fixtures if needed
print_header "Setup: Generating test fixtures..."
if [ ! -f "tests/fixtures/regime_optimization/regime_optimization_results_BTCUSDT_5m.json" ]; then
    python tests/fixtures/generate_test_data.py || print_error "Failed to generate fixtures"
else
    print_success "Test fixtures already present"
fi
echo ""

# Run tests based on mode
case "$MODE" in
    all)
        print_header "Running ALL E2E tests with coverage..."
        pytest tests/integration/test_regime_optimization_e2e.py \
            -v \
            --cov=src \
            --cov-report=html \
            --cov-report=term-missing \
            --tb=short
        ;;

    stage1)
        print_header "Running Stage 1 tests..."
        pytest tests/integration/test_regime_optimization_e2e.py::TestStage1RegimeOptimization \
            -v \
            --tb=short
        ;;

    stage2)
        print_header "Running Stage 2 tests..."
        pytest tests/integration/test_regime_optimization_e2e.py::TestStage2IndicatorOptimization \
            -v \
            --tb=short
        ;;

    handoff)
        print_header "Running Stage 1→2 Handoff tests..."
        pytest tests/integration/test_regime_optimization_e2e.py::TestStage1ToStage2Handoff \
            -v \
            --tb=short
        ;;

    schema)
        print_header "Running JSON Schema Validation tests..."
        pytest tests/integration/test_regime_optimization_e2e.py::TestJSONSchemaCompliance \
            -v \
            --tb=short
        ;;

    perf)
        print_header "Running Performance Benchmark tests..."
        pytest tests/integration/test_regime_optimization_e2e.py::TestPerformanceBenchmark \
            -v \
            --tb=short
        ;;

    ui)
        print_header "Running UI Integration tests..."
        pytest tests/integration/test_regime_optimization_e2e.py::TestEntryAnalyzerUIIntegration \
            -v \
            -m ui \
            --tb=short
        ;;

    quick)
        print_header "Running QUICK tests (excluding slow and UI)..."
        pytest tests/integration/test_regime_optimization_e2e.py \
            -v \
            -m "not slow and not ui" \
            --tb=short \
            --timeout=60
        ;;

    *)
        print_error "Unknown mode: $MODE"
        echo ""
        echo "Available modes:"
        echo "  all      - All tests with coverage"
        echo "  stage1   - Stage 1 regime optimization"
        echo "  stage2   - Stage 2 indicator optimization"
        echo "  handoff  - Stage 1→2 handoff"
        echo "  schema   - JSON schema validation"
        echo "  perf     - Performance benchmark"
        echo "  ui       - UI integration (requires PyQt6)"
        echo "  quick    - Quick tests (exclude slow/ui)"
        exit 1
        ;;
esac

TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}========================================${NC}"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "All tests passed!"
    echo ""
    echo -e "${GREEN}Coverage Report:${NC}"
    if [ -f "htmlcov/index.html" ]; then
        echo "  Open: htmlcov/index.html"
    fi
else
    print_error "Some tests failed (exit code: $TEST_EXIT_CODE)"
fi

echo -e "${BLUE}========================================${NC}"
echo ""

exit $TEST_EXIT_CODE
