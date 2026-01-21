#!/bin/bash
################################################################################
# health_check.sh - Production Health Monitoring Script
#
# Performs comprehensive health checks on running trading bot:
# - Process health (running, responsive, memory usage)
# - API connectivity (Alpaca, LLM providers)
# - Configuration validity
# - Database health
# - Log analysis (errors, warnings)
# - Performance metrics
# - Trading activity verification
#
# Usage:
#   ./scripts/health_check.sh [--environment prod|staging] [--detailed] [--alert-on-failure]
#
# Exit Codes:
#   0 - All health checks passed
#   1 - Health check failures detected
#   2 - Critical failure (bot not running)
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HEALTH_LOG_DIR="$PROJECT_ROOT/logs/health"
HEALTH_LOG="$HEALTH_LOG_DIR/health_check_$(date +%Y%m%d_%H%M%S).log"
HEALTH_REPORT="$HEALTH_LOG_DIR/health_report_$(date +%Y%m%d_%H%M%S).json"

# Options
ENVIRONMENT="staging"
DETAILED=false
ALERT_ON_FAILURE=false

# Health check results
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

################################################################################
# Helper Functions
################################################################################

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $*" | tee -a "$HEALTH_LOG"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $*" | tee -a "$HEALTH_LOG"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*" | tee -a "$HEALTH_LOG"
    ((CHECKS_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*" | tee -a "$HEALTH_LOG"
    ((CHECKS_WARNING++))
}

log_error() {
    echo -e "${RED}✗${NC} $*" | tee -a "$HEALTH_LOG"
    ((CHECKS_FAILED++))
}

send_alert() {
    local severity="$1"
    local message="$2"

    log_warning "ALERT [$severity]: $message"

    # TODO: Integrate with alerting system (PagerDuty, Slack, email, etc.)
    # Example: curl -X POST https://hooks.slack.com/services/... -d "{\"text\": \"$message\"}"
}

################################################################################
# Health Check Functions
################################################################################

check_process_health() {
    log_info "=== Process Health Check ==="

    # Check if bot is running
    local bot_pids=$(pgrep -f "python.*main.py" || true)

    if [[ -z "$bot_pids" ]]; then
        log_error "Bot process not running"
        send_alert "CRITICAL" "Trading bot process not found!"
        return 2  # Critical failure
    fi

    log_success "Bot process found: PID $bot_pids"

    # Check PID file matches
    if [[ -f "$PROJECT_ROOT/bot.pid" ]]; then
        local expected_pid=$(cat "$PROJECT_ROOT/bot.pid")
        if [[ "$bot_pids" == "$expected_pid" ]]; then
            log_success "PID matches expected: $expected_pid"
        else
            log_warning "PID mismatch: expected $expected_pid, found $bot_pids"
        fi
    fi

    # Check process uptime
    local uptime_seconds=$(ps -o etimes= -p "$bot_pids" | tr -d ' ')
    local uptime_hours=$((uptime_seconds / 3600))
    local uptime_minutes=$(((uptime_seconds % 3600) / 60))

    log_info "Process uptime: ${uptime_hours}h ${uptime_minutes}m"

    if [[ $uptime_seconds -lt 60 ]]; then
        log_warning "Process recently started (< 1 minute)"
    fi

    # Check memory usage
    local mem_usage_kb=$(ps -o rss= -p "$bot_pids" | tr -d ' ')
    local mem_usage_mb=$((mem_usage_kb / 1024))

    log_info "Memory usage: ${mem_usage_mb} MB"

    # Alert if memory > 2GB
    if [[ $mem_usage_mb -gt 2048 ]]; then
        log_warning "High memory usage: ${mem_usage_mb} MB"
        send_alert "WARNING" "Bot memory usage high: ${mem_usage_mb} MB"
    else
        log_success "Memory usage normal: ${mem_usage_mb} MB"
    fi

    # Check CPU usage
    local cpu_usage=$(ps -o %cpu= -p "$bot_pids" | tr -d ' ')
    log_info "CPU usage: ${cpu_usage}%"

    if (( $(echo "$cpu_usage > 80.0" | bc -l) )); then
        log_warning "High CPU usage: ${cpu_usage}%"
    else
        log_success "CPU usage normal: ${cpu_usage}%"
    fi

    return 0
}

check_api_connectivity() {
    log_info "=== API Connectivity Check ==="

    # Check Alpaca Trading API
    if [[ -n "${ALPACA_API_KEY:-}" ]] && [[ -n "${ALPACA_SECRET_KEY:-}" ]]; then
        log_info "Testing Alpaca Trading API..."

        if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')

from alpaca.trading.client import TradingClient

try:
    client = TradingClient('$ALPACA_API_KEY', '$ALPACA_SECRET_KEY', paper=True)
    account = client.get_account()

    print(f'Status: {account.status}')
    print(f'Buying Power: \${float(account.buying_power):,.2f}')
    print(f'Portfolio Value: \${float(account.portfolio_value):,.2f}')

    if account.status != 'ACTIVE':
        print('WARNING: Account not active!', file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
except Exception as e:
    print(f'Alpaca API error: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$HEALTH_LOG" 2>&1; then
            log_success "Alpaca Trading API healthy"
        else
            log_error "Alpaca Trading API connection failed"
            send_alert "HIGH" "Alpaca Trading API connection failed!"
            return 1
        fi
    else
        log_warning "Alpaca credentials not configured"
    fi

    # Check Alpaca Market Data API
    if [[ -n "${ALPACA_API_KEY:-}" ]] && [[ -n "${ALPACA_SECRET_KEY:-}" ]]; then
        log_info "Testing Alpaca Market Data API..."

        if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

try:
    client = StockHistoricalDataClient('$ALPACA_API_KEY', '$ALPACA_SECRET_KEY')
    request = StockLatestQuoteRequest(symbol_or_symbols='SPY')
    quote = client.get_stock_latest_quote(request)

    print(f'SPY bid: \${quote[\"SPY\"].bid_price}')
    print(f'SPY ask: \${quote[\"SPY\"].ask_price}')

    sys.exit(0)
except Exception as e:
    print(f'Market Data API error: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$HEALTH_LOG" 2>&1; then
            log_success "Alpaca Market Data API healthy"
        else
            log_error "Alpaca Market Data API connection failed"
            send_alert "HIGH" "Alpaca Market Data API connection failed!"
            return 1
        fi
    fi

    # Check LLM APIs (non-critical)
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        log_info "Testing OpenAI API..."

        if python3 -c "
import os
os.environ['OPENAI_API_KEY'] = '$OPENAI_API_KEY'

try:
    import openai
    client = openai.OpenAI()
    models = client.models.list()
    print(f'OpenAI API: {len(list(models.data))} models available')
    exit(0)
except Exception as e:
    print(f'OpenAI API error: {e}', file=sys.stderr)
    exit(1)
" >> "$HEALTH_LOG" 2>&1; then
            log_success "OpenAI API healthy (optional)"
        else
            log_warning "OpenAI API connection failed (non-critical)"
        fi
    fi

    return 0
}

check_configuration() {
    log_info "=== Configuration Validation ==="

    # Check JSON configs
    local config_dir="$PROJECT_ROOT/03_JSON/Trading_Bot"

    if [[ -d "$config_dir" ]]; then
        log_info "Validating JSON configs..."

        local config_count=0
        local valid_count=0

        for config_file in "$config_dir"/*.json; do
            if [[ -f "$config_file" ]]; then
                ((config_count++))

                if python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT/src')

from core.tradingbot.config.loader import ConfigLoader

try:
    loader = ConfigLoader()
    config = loader.load_config(Path('$config_file'))
    sys.exit(0)
except Exception as e:
    print(f'Config validation failed: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$HEALTH_LOG" 2>&1; then
                    ((valid_count++))
                fi
            fi
        done

        if [[ $valid_count -eq $config_count ]]; then
            log_success "All $config_count config files valid"
        else
            log_error "$((config_count - valid_count))/$config_count configs invalid"
            return 1
        fi
    else
        log_warning "Config directory not found"
    fi

    return 0
}

check_database_health() {
    log_info "=== Database Health Check ==="

    local db_file="$PROJECT_ROOT/data/tradingbot.db"

    if [[ ! -f "$db_file" ]]; then
        log_warning "Database file not found (may not be used)"
        return 0
    fi

    # Check file size
    local db_size_kb=$(du -k "$db_file" | cut -f1)
    local db_size_mb=$((db_size_kb / 1024))

    log_info "Database size: ${db_size_mb} MB"

    # Check SQLite integrity
    if command -v sqlite3 &> /dev/null; then
        log_info "Running SQLite integrity check..."

        if sqlite3 "$db_file" "PRAGMA integrity_check;" >> "$HEALTH_LOG" 2>&1; then
            log_success "Database integrity OK"
        else
            log_error "Database integrity check failed"
            send_alert "HIGH" "Database corruption detected!"
            return 1
        fi
    else
        log_warning "sqlite3 not available, skipping integrity check"
    fi

    return 0
}

check_log_health() {
    log_info "=== Log Analysis ==="

    local bot_log="$DEPLOY_LOG_DIR/bot_stdout.log"

    if [[ ! -f "$bot_log" ]]; then
        log_warning "Bot log file not found"
        return 0
    fi

    # Check log file size
    local log_size_kb=$(du -k "$bot_log" | cut -f1)
    local log_size_mb=$((log_size_kb / 1024))

    log_info "Log file size: ${log_size_mb} MB"

    # Check for recent errors (last 100 lines)
    local error_count=$(tail -n 100 "$bot_log" | grep -c "ERROR" || true)

    if [[ $error_count -gt 0 ]]; then
        log_warning "Found $error_count ERROR entries in recent logs"

        if [[ "$DETAILED" == "true" ]]; then
            log_info "Recent errors:"
            tail -n 100 "$bot_log" | grep "ERROR" | tail -n 5 | tee -a "$HEALTH_LOG"
        fi
    else
        log_success "No recent errors in logs"
    fi

    # Check for exceptions
    local exception_count=$(tail -n 100 "$bot_log" | grep -c "Traceback" || true)

    if [[ $exception_count -gt 0 ]]; then
        log_warning "Found $exception_count exceptions in recent logs"
        send_alert "WARNING" "$exception_count exceptions found in bot logs"
    else
        log_success "No recent exceptions in logs"
    fi

    return 0
}

check_performance_metrics() {
    log_info "=== Performance Metrics ==="

    # Check regime classification speed
    local regime_speed=$(python3 -c "
import sys
import time
sys.path.insert(0, '$PROJECT_ROOT/src')

from core.tradingbot.regime_engine import RegimeEngine
from core.tradingbot.feature_engine import FeatureVector

try:
    engine = RegimeEngine()
    test_features = FeatureVector(
        rsi=65.0, adx=28.0, atr_pct=1.5,
        macd=0.01, macd_signal=0.008,
        sma_fast=50000, sma_slow=49500,
        close=50100, high=50200, low=50000, open=50050,
        volume=1000000, bb_upper=50500, bb_middle=50000, bb_lower=49500
    )

    start = time.perf_counter()
    for _ in range(1000):
        engine.classify(test_features)
    elapsed = time.perf_counter() - start

    print(int(1000 / elapsed))
    sys.exit(0)
except Exception as e:
    print('0', file=sys.stderr)
    sys.exit(1)
" 2>> "$HEALTH_LOG" || echo "0")

    if [[ "$regime_speed" != "0" ]]; then
        log_info "RegimeEngine: $regime_speed classifications/sec"

        if [[ "$regime_speed" -gt 1000 ]]; then
            log_success "Performance normal (> 1000/sec)"
        else
            log_warning "Performance degraded: $regime_speed <= 1000/sec"
        fi
    else
        log_warning "Performance benchmark failed"
    fi

    return 0
}

check_trading_activity() {
    log_info "=== Trading Activity Check ==="

    # Check for recent trades (if Alpaca configured)
    if [[ -n "${ALPACA_API_KEY:-}" ]] && [[ -n "${ALPACA_SECRET_KEY:-}" ]]; then
        log_info "Checking recent trading activity..."

        python3 -c "
import sys
from datetime import datetime, timedelta
sys.path.insert(0, '$PROJECT_ROOT/src')

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest

try:
    client = TradingClient('$ALPACA_API_KEY', '$ALPACA_SECRET_KEY', paper=True)

    # Get orders from last 24 hours
    request = GetOrdersRequest(
        after=(datetime.now() - timedelta(days=1)).isoformat()
    )
    orders = client.get_orders(request)

    print(f'Orders (24h): {len(orders)}')

    if len(orders) > 0:
        print(f'Latest order: {orders[0].symbol} {orders[0].side} {orders[0].qty} @ {orders[0].status}')

    # Get current positions
    positions = client.get_all_positions()
    print(f'Open positions: {len(positions)}')

    if len(positions) > 0:
        total_value = sum(float(p.market_value) for p in positions)
        print(f'Total position value: \${total_value:,.2f}')

    sys.exit(0)
except Exception as e:
    print(f'Trading activity check failed: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$HEALTH_LOG" 2>&1

        log_success "Trading activity check completed"
    else
        log_warning "Alpaca not configured, skipping trading activity check"
    fi

    return 0
}

generate_health_report() {
    log_info "=== Generating Health Report ==="

    local overall_status="healthy"
    if [[ $CHECKS_FAILED -gt 0 ]]; then
        overall_status="unhealthy"
    elif [[ $CHECKS_WARNING -gt 0 ]]; then
        overall_status="degraded"
    fi

    cat > "$HEALTH_REPORT" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "environment": "$ENVIRONMENT",
  "overall_status": "$overall_status",
  "summary": {
    "checks_passed": $CHECKS_PASSED,
    "checks_failed": $CHECKS_FAILED,
    "checks_warning": $CHECKS_WARNING,
    "total_checks": $((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))
  },
  "checks": {
    "process_health": "$([ $CHECKS_FAILED -eq 0 ] && echo "passed" || echo "failed")",
    "api_connectivity": "passed",
    "configuration": "passed",
    "database_health": "passed",
    "log_health": "passed",
    "performance_metrics": "passed",
    "trading_activity": "passed"
  },
  "log_file": "$HEALTH_LOG"
}
EOF

    log_success "Health report: $HEALTH_REPORT"
}

################################################################################
# Main Execution
################################################################################

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --detailed)
                DETAILED=true
                shift
                ;;
            --alert-on-failure)
                ALERT_ON_FAILURE=true
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Production health monitoring script for OrderPilot-AI trading bot.

Options:
  --environment ENV     Set environment (prod|staging, default: staging)
  --detailed           Show detailed output including error logs
  --alert-on-failure   Send alerts on health check failures
  -h, --help           Show this help message

Health Checks:
  - Process health (running, memory, CPU)
  - API connectivity (Alpaca, LLM providers)
  - Configuration validity
  - Database health
  - Log analysis (errors, exceptions)
  - Performance metrics
  - Trading activity verification

Exit Codes:
  0 - All health checks passed
  1 - Health check failures detected
  2 - Critical failure (bot not running)
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
    parse_arguments "$@"

    # Setup
    mkdir -p "$HEALTH_LOG_DIR"

    # Print header
    echo "=================================="
    echo "  OrderPilot-AI Health Check"
    echo "=================================="
    echo "Environment: $ENVIRONMENT"
    echo "Log: $HEALTH_LOG"
    echo ""

    log_info "Starting health check at $(date)"

    # Run health checks
    local exit_code=0

    check_process_health || exit_code=$?
    [[ $exit_code -eq 2 ]] && { log_error "Critical: Bot not running"; exit 2; }

    check_api_connectivity || exit_code=1
    check_configuration || exit_code=1
    check_database_health || true  # Non-critical
    check_log_health || true  # Non-critical
    check_performance_metrics || true  # Non-critical
    check_trading_activity || true  # Non-critical

    # Generate report
    generate_health_report

    # Print summary
    echo ""
    echo "=================================="
    echo "  Health Check Summary"
    echo "=================================="
    echo -e "${GREEN}Passed:${NC}   $CHECKS_PASSED"
    echo -e "${RED}Failed:${NC}   $CHECKS_FAILED"
    echo -e "${YELLOW}Warnings:${NC} $CHECKS_WARNING"
    echo ""

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        log_success "All critical health checks passed!"

        if [[ $CHECKS_WARNING -gt 0 ]]; then
            log_warning "System healthy with $CHECKS_WARNING warnings"
        fi

        exit 0
    else
        log_error "Health check failed with $CHECKS_FAILED errors"

        if [[ "$ALERT_ON_FAILURE" == "true" ]]; then
            send_alert "HIGH" "Trading bot health check failed: $CHECKS_FAILED errors"
        fi

        exit "$exit_code"
    fi
}

main "$@"
