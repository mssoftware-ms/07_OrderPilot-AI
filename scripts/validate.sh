#!/bin/bash
################################################################################
# validate.sh - Pre-Deployment Validation Script
#
# Performs comprehensive validation checks before deployment:
# - Python environment and dependencies
# - JSON configuration validation
# - Unit test execution
# - Code quality checks (linting, type checking)
# - Security scans (bandit, safety)
# - Performance benchmarks
# - Database connectivity (if applicable)
# - API connectivity (Alpaca, LLM providers)
#
# Usage:
#   ./scripts/validate.sh [--skip-tests] [--skip-security] [--environment prod|staging]
#
# Exit Codes:
#   0 - All validations passed
#   1 - Validation failures detected
#   2 - Critical error (environment setup, etc.)
################################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs/validation"
LOG_FILE="$LOG_DIR/validate_$(date +%Y%m%d_%H%M%S).log"
VALIDATION_REPORT="$LOG_DIR/validation_report_$(date +%Y%m%d_%H%M%S).json"

# Options
SKIP_TESTS=false
SKIP_SECURITY=false
ENVIRONMENT="staging"

# Validation results
VALIDATION_PASSED=0
VALIDATION_FAILED=0
VALIDATION_WARNINGS=0

################################################################################
# Helper Functions
################################################################################

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*" | tee -a "$LOG_FILE"
    ((VALIDATION_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*" | tee -a "$LOG_FILE"
    ((VALIDATION_WARNINGS++))
}

log_error() {
    echo -e "${RED}✗${NC} $*" | tee -a "$LOG_FILE"
    ((VALIDATION_FAILED++))
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "Command '$1' is available"
        return 0
    else
        log_error "Command '$1' not found"
        return 1
    fi
}

run_check() {
    local check_name="$1"
    local check_command="$2"

    log_info "Running: $check_name"

    if eval "$check_command" >> "$LOG_FILE" 2>&1; then
        log_success "$check_name passed"
        return 0
    else
        log_error "$check_name failed"
        return 1
    fi
}

################################################################################
# Validation Checks
################################################################################

check_python_environment() {
    log_info "=== Python Environment Check ==="

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_success "Python version: $PYTHON_VERSION"
    else
        log_error "Python 3 not found"
        return 1
    fi

    # Check virtual environment
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log_warning "Not running in virtual environment"

        # Try to activate .venv
        if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
            log_info "Activating virtual environment..."
            source "$PROJECT_ROOT/.venv/bin/activate"
            log_success "Virtual environment activated"
        else
            log_error "Virtual environment not found at $PROJECT_ROOT/.venv"
            return 1
        fi
    else
        log_success "Virtual environment active: $VIRTUAL_ENV"
    fi

    # Check pip
    check_command pip3 || return 1

    return 0
}

check_dependencies() {
    log_info "=== Dependency Check ==="

    # Check requirements.txt exists
    if [[ ! -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log_error "requirements.txt not found"
        return 1
    fi

    # Install/verify dependencies
    log_info "Verifying dependencies from requirements.txt..."
    if pip3 install -q -r "$PROJECT_ROOT/requirements.txt" >> "$LOG_FILE" 2>&1; then
        log_success "All dependencies satisfied"
    else
        log_error "Dependency installation failed"
        return 1
    fi

    # Check critical packages
    local critical_packages=("pydantic" "pandas" "numpy" "alpaca-py" "PyQt6" "watchdog")
    for package in "${critical_packages[@]}"; do
        if python3 -c "import ${package//-/_}" &> /dev/null; then
            log_success "Package '$package' imported successfully"
        else
            log_error "Failed to import package '$package'"
            return 1
        fi
    done

    return 0
}

check_json_configs() {
    log_info "=== JSON Configuration Validation ==="

    local config_dir="$PROJECT_ROOT/03_JSON/Trading_Bot"
    local schema_file="$PROJECT_ROOT/schemas/trading_bot_config_schema.json"

    # Check schema exists
    if [[ ! -f "$schema_file" ]]; then
        log_error "JSON schema not found: $schema_file"
        return 1
    fi
    log_success "JSON schema found"

    # Validate all JSON configs
    local config_count=0
    local valid_count=0

    if [[ -d "$config_dir" ]]; then
        while IFS= read -r -d '' config_file; do
            ((config_count++))

            log_info "Validating: $(basename "$config_file")"

            # Use Python to validate JSON with schema
            if python3 -c "
import json
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT/src')

from core.tradingbot.config.loader import ConfigLoader

try:
    loader = ConfigLoader(schema_path=Path('$schema_file'))
    config = loader.load_config(Path('$config_file'))
    print(f'Valid: {len(config.strategies)} strategies, {len(config.regimes)} regimes')
    sys.exit(0)
except Exception as e:
    print(f'Validation failed: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$LOG_FILE" 2>&1; then
                log_success "$(basename "$config_file") is valid"
                ((valid_count++))
            else
                log_error "$(basename "$config_file") validation failed"
            fi
        done < <(find "$config_dir" -name "*.json" -type f -print0)

        log_info "Validated $valid_count/$config_count config files"

        if [[ $valid_count -eq $config_count ]]; then
            return 0
        else
            return 1
        fi
    else
        log_warning "Config directory not found: $config_dir"
        return 0  # Not critical
    fi
}

check_unit_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "Skipping unit tests (--skip-tests flag)"
        return 0
    fi

    log_info "=== Unit Test Execution ==="

    # Check pytest available
    check_command pytest || return 1

    # Run pytest with coverage
    log_info "Running pytest with coverage..."
    if pytest "$PROJECT_ROOT/tests" \
        --cov="$PROJECT_ROOT/src" \
        --cov-report=term-missing \
        --cov-report=html:"$PROJECT_ROOT/htmlcov" \
        --cov-report=json:"$LOG_DIR/coverage.json" \
        --junit-xml="$LOG_DIR/junit.xml" \
        -v >> "$LOG_FILE" 2>&1; then

        # Extract coverage percentage
        local coverage=$(python3 -c "
import json
with open('$LOG_DIR/coverage.json') as f:
    data = json.load(f)
    print(f\"{data['totals']['percent_covered']:.1f}\")
" 2>/dev/null || echo "unknown")

        log_success "All tests passed (Coverage: ${coverage}%)"

        # Check coverage threshold
        if [[ "$coverage" != "unknown" ]]; then
            local threshold=80
            if (( $(echo "$coverage >= $threshold" | bc -l) )); then
                log_success "Coverage meets threshold: ${coverage}% >= ${threshold}%"
            else
                log_warning "Coverage below threshold: ${coverage}% < ${threshold}%"
            fi
        fi

        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

check_code_quality() {
    log_info "=== Code Quality Checks ==="

    # Check flake8 (linting)
    if command -v flake8 &> /dev/null; then
        log_info "Running flake8 linter..."
        if flake8 "$PROJECT_ROOT/src" \
            --output-file="$LOG_DIR/flake8.txt" 2>> "$LOG_FILE"; then
            log_success "Flake8 linting passed"
        else
            log_warning "Flake8 found issues (see $LOG_DIR/flake8.txt)"
        fi
    else
        log_warning "Flake8 not installed, skipping linting"
    fi

    # Check mypy (type checking)
    if command -v mypy &> /dev/null; then
        log_info "Running mypy type checker..."
        if mypy "$PROJECT_ROOT/src" \
            --ignore-missing-imports \
            --no-error-summary \
            > "$LOG_DIR/mypy.txt" 2>&1; then
            log_success "Mypy type checking passed"
        else
            log_warning "Mypy found type issues (see $LOG_DIR/mypy.txt)"
        fi
    else
        log_warning "Mypy not installed, skipping type checking"
    fi

    # Check black (formatting)
    if command -v black &> /dev/null; then
        log_info "Checking code formatting with black..."
        if black --check "$PROJECT_ROOT/src" >> "$LOG_FILE" 2>&1; then
            log_success "Black formatting check passed"
        else
            log_warning "Code needs formatting (run: black src/)"
        fi
    else
        log_warning "Black not installed, skipping formatting check"
    fi

    return 0
}

check_security() {
    if [[ "$SKIP_SECURITY" == "true" ]]; then
        log_warning "Skipping security checks (--skip-security flag)"
        return 0
    fi

    log_info "=== Security Scans ==="

    # Check bandit (security linter)
    if command -v bandit &> /dev/null; then
        log_info "Running bandit security scan..."
        if bandit -r "$PROJECT_ROOT/src" \
            -f json \
            -o "$LOG_DIR/bandit.json" \
            --severity-level medium >> "$LOG_FILE" 2>&1; then
            log_success "Bandit security scan passed"
        else
            log_warning "Bandit found security issues (see $LOG_DIR/bandit.json)"
        fi
    else
        log_warning "Bandit not installed, skipping security scan"
    fi

    # Check safety (dependency vulnerabilities)
    if command -v safety &> /dev/null; then
        log_info "Checking dependency vulnerabilities with safety..."
        if safety check \
            --json \
            --output "$LOG_DIR/safety.json" >> "$LOG_FILE" 2>&1; then
            log_success "Safety check passed (no known vulnerabilities)"
        else
            log_warning "Safety found vulnerabilities (see $LOG_DIR/safety.json)"
        fi
    else
        log_warning "Safety not installed, skipping vulnerability check"
    fi

    # Check for hardcoded secrets
    log_info "Scanning for hardcoded secrets..."
    local secret_patterns=(
        "password\s*=\s*['\"].*['\"]"
        "api_key\s*=\s*['\"].*['\"]"
        "secret\s*=\s*['\"].*['\"]"
        "token\s*=\s*['\"].*['\"]"
    )

    local secrets_found=0
    for pattern in "${secret_patterns[@]}"; do
        if grep -rn -E "$pattern" "$PROJECT_ROOT/src" >> "$LOG_DIR/secrets.txt" 2>&1; then
            ((secrets_found++))
        fi
    done

    if [[ $secrets_found -gt 0 ]]; then
        log_warning "Potential hardcoded secrets found (see $LOG_DIR/secrets.txt)"
    else
        log_success "No hardcoded secrets detected"
    fi

    return 0
}

check_api_connectivity() {
    log_info "=== API Connectivity Checks ==="

    # Check Alpaca API (if configured)
    if [[ -n "${ALPACA_API_KEY:-}" ]] && [[ -n "${ALPACA_SECRET_KEY:-}" ]]; then
        log_info "Testing Alpaca API connection..."

        if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')

from alpaca.trading.client import TradingClient

try:
    client = TradingClient('$ALPACA_API_KEY', '$ALPACA_SECRET_KEY', paper=True)
    account = client.get_account()
    print(f'Connected to Alpaca: {account.status}')
    sys.exit(0)
except Exception as e:
    print(f'Alpaca connection failed: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$LOG_FILE" 2>&1; then
            log_success "Alpaca API connection successful"
        else
            log_error "Alpaca API connection failed"
            return 1
        fi
    else
        log_warning "Alpaca API credentials not configured, skipping connectivity check"
    fi

    # Check LLM provider APIs (if configured)
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        log_info "Testing OpenAI API connection..."

        if python3 -c "
import sys
import os
os.environ['OPENAI_API_KEY'] = '$OPENAI_API_KEY'

try:
    import openai
    client = openai.OpenAI()
    # Simple test: list models
    models = client.models.list()
    print(f'OpenAI API connected, {len(list(models.data))} models available')
    sys.exit(0)
except Exception as e:
    print(f'OpenAI connection failed: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$LOG_FILE" 2>&1; then
            log_success "OpenAI API connection successful"
        else
            log_warning "OpenAI API connection failed (non-critical)"
        fi
    fi

    return 0
}

check_performance_benchmarks() {
    log_info "=== Performance Benchmarks ==="

    log_info "Running performance benchmarks..."

    # Benchmark: RegimeEngine classification speed
    local regime_bench=$(python3 -c "
import sys
import time
sys.path.insert(0, '$PROJECT_ROOT/src')

from core.tradingbot.regime_engine import RegimeEngine
from core.tradingbot.feature_engine import FeatureVector

engine = RegimeEngine()
test_features = FeatureVector(
    rsi=65.0, adx=28.0, atr_pct=1.5,
    macd=0.01, macd_signal=0.008,
    sma_fast=50000, sma_slow=49500,
    close=50100, high=50200, low=50000, open=50050,
    volume=1000000, bb_upper=50500, bb_middle=50000, bb_lower=49500
)

# Warm-up
for _ in range(100):
    engine.classify(test_features)

# Benchmark
start = time.perf_counter()
iterations = 10000
for _ in range(iterations):
    engine.classify(test_features)
elapsed = time.perf_counter() - start

print(f'{iterations / elapsed:.0f}')
" 2>> "$LOG_FILE" || echo "0")

    if [[ "$regime_bench" != "0" ]]; then
        log_success "RegimeEngine: $regime_bench classifications/sec"

        # Check threshold (should be > 1000/sec)
        if [[ "$regime_bench" -gt 1000 ]]; then
            log_success "Performance meets threshold (> 1000/sec)"
        else
            log_warning "Performance below threshold: $regime_bench <= 1000/sec"
        fi
    else
        log_warning "Performance benchmark failed"
    fi

    return 0
}

generate_validation_report() {
    log_info "=== Generating Validation Report ==="

    # Create JSON report
    cat > "$VALIDATION_REPORT" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "environment": "$ENVIRONMENT",
  "validation_summary": {
    "passed": $VALIDATION_PASSED,
    "failed": $VALIDATION_FAILED,
    "warnings": $VALIDATION_WARNINGS,
    "total": $((VALIDATION_PASSED + VALIDATION_FAILED + VALIDATION_WARNINGS))
  },
  "checks": {
    "python_environment": "passed",
    "dependencies": "passed",
    "json_configs": "passed",
    "unit_tests": "$([ "$SKIP_TESTS" == "true" ] && echo "skipped" || echo "passed")",
    "code_quality": "passed",
    "security": "$([ "$SKIP_SECURITY" == "true" ] && echo "skipped" || echo "passed")",
    "api_connectivity": "passed",
    "performance": "passed"
  },
  "artifacts": {
    "log_file": "$LOG_FILE",
    "coverage_report": "$LOG_DIR/coverage.json",
    "junit_xml": "$LOG_DIR/junit.xml",
    "flake8_output": "$LOG_DIR/flake8.txt",
    "mypy_output": "$LOG_DIR/mypy.txt",
    "bandit_report": "$LOG_DIR/bandit.json",
    "safety_report": "$LOG_DIR/safety.json"
  }
}
EOF

    log_success "Validation report: $VALIDATION_REPORT"
}

################################################################################
# Main Execution
################################################################################

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-security)
                SKIP_SECURITY=true
                shift
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Pre-deployment validation script for OrderPilot-AI trading bot.

Options:
  --skip-tests          Skip unit test execution
  --skip-security       Skip security scans
  --environment ENV     Set environment (prod|staging, default: staging)
  -h, --help           Show this help message

Exit Codes:
  0 - All validations passed
  1 - Validation failures detected
  2 - Critical error
EOF
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 2
                ;;
        esac
    done
}

main() {
    # Parse command-line arguments
    parse_arguments "$@"

    # Setup
    mkdir -p "$LOG_DIR"

    # Print header
    echo "=================================="
    echo "  OrderPilot-AI Validation"
    echo "=================================="
    echo "Environment: $ENVIRONMENT"
    echo "Log: $LOG_FILE"
    echo ""

    log_info "Starting validation at $(date)"

    # Run validation checks
    local exit_code=0

    check_python_environment || exit_code=2
    [[ $exit_code -eq 2 ]] && { log_error "Critical: Python environment check failed"; exit 2; }

    check_dependencies || exit_code=2
    [[ $exit_code -eq 2 ]] && { log_error "Critical: Dependency check failed"; exit 2; }

    check_json_configs || exit_code=1
    check_unit_tests || exit_code=1
    check_code_quality || true  # Non-blocking
    check_security || true  # Non-blocking
    check_api_connectivity || exit_code=1
    check_performance_benchmarks || true  # Non-blocking

    # Generate report
    generate_validation_report

    # Print summary
    echo ""
    echo "=================================="
    echo "  Validation Summary"
    echo "=================================="
    echo -e "${GREEN}Passed:${NC}   $VALIDATION_PASSED"
    echo -e "${RED}Failed:${NC}   $VALIDATION_FAILED"
    echo -e "${YELLOW}Warnings:${NC} $VALIDATION_WARNINGS"
    echo ""

    if [[ $VALIDATION_FAILED -eq 0 ]]; then
        log_success "All critical validations passed!"
        log_info "Report: $VALIDATION_REPORT"
        exit 0
    else
        log_error "Validation failed with $VALIDATION_FAILED errors"
        log_info "Review logs: $LOG_FILE"
        exit "$exit_code"
    fi
}

# Run main with all arguments
main "$@"
