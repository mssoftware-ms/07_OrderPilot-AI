#!/bin/bash
################################################################################
# rollback.sh - Automated Rollback Script
#
# Performs automated rollback to previous version:
# - Stop current running instances
# - Restore code from backup
# - Restore configuration files
# - Restore database (optional)
# - Start restored version
# - Verify rollback success
#
# Usage:
#   ./scripts/rollback.sh [--deployment-id ID] [--list-backups] [--skip-database]
#
# Exit Codes:
#   0 - Rollback successful
#   1 - Rollback failed
#   2 - Critical error
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
BACKUP_DIR="$PROJECT_ROOT/backups"
ROLLBACK_LOG_DIR="$PROJECT_ROOT/logs/rollback"
ROLLBACK_LOG="$ROLLBACK_LOG_DIR/rollback_$(date +%Y%m%d_%H%M%S).log"

# Options
DEPLOYMENT_ID=""
LIST_BACKUPS=false
SKIP_DATABASE=false

################################################################################
# Helper Functions
################################################################################

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $*" | tee -a "$ROLLBACK_LOG"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $*" | tee -a "$ROLLBACK_LOG"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*" | tee -a "$ROLLBACK_LOG"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*" | tee -a "$ROLLBACK_LOG"
}

log_error() {
    echo -e "${RED}✗${NC} $*" | tee -a "$ROLLBACK_LOG"
}

list_available_backups() {
    log_info "=== Available Backups ==="

    if [[ ! -d "$BACKUP_DIR" ]] || [[ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]]; then
        log_warning "No backups found in $BACKUP_DIR"
        return 0
    fi

    echo ""
    echo "Deployment ID                 | Timestamp            | Git Commit  | Environment"
    echo "-------------------------------------------------------------------------------------"

    for backup in "$BACKUP_DIR"/deploy_*; do
        if [[ -f "$backup/metadata.json" ]]; then
            local deployment_id=$(basename "$backup")
            local timestamp=$(jq -r '.timestamp // "unknown"' "$backup/metadata.json" 2>/dev/null || echo "unknown")
            local git_commit=$(jq -r '.git_commit // "unknown"' "$backup/metadata.json" 2>/dev/null | cut -c1-10)
            local environment=$(jq -r '.environment // "unknown"' "$backup/metadata.json" 2>/dev/null)

            printf "%-30s| %-20s | %-11s | %s\n" "$deployment_id" "$timestamp" "$git_commit" "$environment"
        fi
    done

    echo ""
}

select_backup() {
    if [[ -n "$DEPLOYMENT_ID" ]]; then
        log_info "Using specified deployment ID: $DEPLOYMENT_ID"
        return 0
    fi

    # Find latest backup
    local latest_backup=$(ls -t "$BACKUP_DIR" 2>/dev/null | head -n1)

    if [[ -z "$latest_backup" ]]; then
        log_error "No backups available for rollback"
        exit 1
    fi

    DEPLOYMENT_ID="$latest_backup"
    log_info "Using latest backup: $DEPLOYMENT_ID"

    return 0
}

verify_backup() {
    log_info "=== Verifying Backup ==="

    local backup_path="$BACKUP_DIR/$DEPLOYMENT_ID"

    if [[ ! -d "$backup_path" ]]; then
        log_error "Backup not found: $backup_path"
        exit 1
    fi

    log_success "Backup directory exists: $backup_path"

    # Verify required components
    if [[ ! -d "$backup_path/src" ]]; then
        log_error "Source code backup missing"
        exit 1
    fi
    log_success "Source code backup found"

    if [[ ! -f "$backup_path/metadata.json" ]]; then
        log_warning "Metadata file missing (non-critical)"
    else
        log_success "Metadata file found"

        # Display backup info
        local timestamp=$(jq -r '.timestamp' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
        local git_commit=$(jq -r '.git_commit' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
        local environment=$(jq -r '.environment' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")

        log_info "Backup timestamp: $timestamp"
        log_info "Git commit: $git_commit"
        log_info "Environment: $environment"
    fi

    return 0
}

stop_current_bot() {
    log_info "=== Stopping Current Bot Instances ==="

    local bot_pids=$(pgrep -f "python.*main.py" || true)

    if [[ -z "$bot_pids" ]]; then
        log_info "No running bot instances found"
        return 0
    fi

    log_info "Found running processes: $bot_pids"

    # Graceful shutdown
    log_info "Sending SIGTERM for graceful shutdown..."
    echo "$bot_pids" | xargs -r kill -TERM 2>/dev/null || true

    # Wait for shutdown (max 30 seconds)
    local wait_time=0
    while [[ -n "$(pgrep -f 'python.*main.py' || true)" ]] && [[ $wait_time -lt 30 ]]; do
        sleep 1
        ((wait_time++))
    done

    # Force kill if needed
    if [[ -n "$(pgrep -f 'python.*main.py' || true)" ]]; then
        log_warning "Graceful shutdown timeout, forcing kill..."
        pgrep -f "python.*main.py" | xargs -r kill -9 2>/dev/null || true
        sleep 2
    fi

    if [[ -z "$(pgrep -f 'python.*main.py' || true)" ]]; then
        log_success "All bot instances stopped"
        return 0
    else
        log_error "Failed to stop bot instances"
        return 1
    fi
}

restore_files() {
    log_info "=== Restoring Files from Backup ==="

    local backup_path="$BACKUP_DIR/$DEPLOYMENT_ID"

    # Backup current state (just in case)
    local temp_backup="$PROJECT_ROOT/.rollback_temp_$(date +%s)"
    log_info "Creating temporary backup of current state..."
    mkdir -p "$temp_backup"
    cp -r "$PROJECT_ROOT/src" "$temp_backup/src" 2>/dev/null || true

    # Restore source code
    log_info "Restoring source code..."
    if [[ -d "$backup_path/src" ]]; then
        rm -rf "$PROJECT_ROOT/src"
        cp -r "$backup_path/src" "$PROJECT_ROOT/src"
        log_success "Source code restored"
    else
        log_error "Source code backup not found"
        return 1
    fi

    # Restore configuration
    log_info "Restoring configuration..."
    if [[ -d "$backup_path/config" ]]; then
        rm -rf "$PROJECT_ROOT/config"
        cp -r "$backup_path/config" "$PROJECT_ROOT/config"
        log_success "Configuration restored"
    else
        log_warning "Configuration backup not found (skipping)"
    fi

    if [[ -d "$backup_path/03_JSON" ]]; then
        rm -rf "$PROJECT_ROOT/03_JSON"
        cp -r "$backup_path/03_JSON" "$PROJECT_ROOT/03_JSON"
        log_success "JSON configs restored"
    else
        log_warning "JSON configs backup not found (skipping)"
    fi

    # Restore database
    if [[ "$SKIP_DATABASE" == "false" ]]; then
        log_info "Restoring database..."
        if [[ -f "$backup_path/data/tradingbot.db" ]]; then
            mkdir -p "$PROJECT_ROOT/data"
            cp "$backup_path/data/tradingbot.db" "$PROJECT_ROOT/data/tradingbot.db"
            log_success "Database restored"
        else
            log_warning "Database backup not found (skipping)"
        fi
    else
        log_warning "Skipping database restore (--skip-database flag)"
    fi

    # Remove temp backup on success
    rm -rf "$temp_backup"

    log_success "All files restored successfully"
    return 0
}

reinstall_dependencies() {
    log_info "=== Reinstalling Dependencies ==="

    # Activate virtual environment
    if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
        log_success "Virtual environment activated"
    else
        log_warning "Virtual environment not found"
    fi

    # Reinstall dependencies
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log_info "Installing dependencies from requirements.txt..."
        if pip3 install -q -r "$PROJECT_ROOT/requirements.txt" >> "$ROLLBACK_LOG" 2>&1; then
            log_success "Dependencies installed"
            return 0
        else
            log_error "Dependency installation failed"
            return 1
        fi
    else
        log_warning "requirements.txt not found"
        return 0
    fi
}

start_restored_bot() {
    log_info "=== Starting Restored Bot ==="

    # Activate virtual environment
    if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi

    # Determine environment from backup metadata
    local environment="staging"
    local backup_path="$BACKUP_DIR/$DEPLOYMENT_ID"

    if [[ -f "$backup_path/metadata.json" ]]; then
        environment=$(jq -r '.environment // "staging"' "$backup_path/metadata.json")
    fi

    log_info "Starting bot in $environment environment..."

    # Start bot
    cd "$PROJECT_ROOT"
    nohup python3 -m src.main --environment "$environment" > "$ROLLBACK_LOG_DIR/bot_stdout.log" 2>&1 &
    local bot_pid=$!

    log_info "Bot started with PID: $bot_pid"

    # Wait for startup
    sleep 5

    # Verify running
    if ps -p "$bot_pid" > /dev/null; then
        log_success "Bot process running (PID: $bot_pid)"
        echo "$bot_pid" > "$PROJECT_ROOT/bot.pid"
        return 0
    else
        log_error "Bot process died immediately after start"
        return 1
    fi
}

verify_rollback() {
    log_info "=== Verifying Rollback ==="

    # Wait for initialization
    log_info "Waiting for bot initialization (30s)..."
    sleep 30

    # Run health checks
    if "$SCRIPT_DIR/health_check.sh" >> "$ROLLBACK_LOG" 2>&1; then
        log_success "Health checks passed"
        return 0
    else
        log_error "Health checks failed after rollback"
        return 1
    fi
}

create_rollback_report() {
    log_info "=== Generating Rollback Report ==="

    local report_path="$ROLLBACK_LOG_DIR/rollback_report_$(date +%Y%m%d_%H%M%S).json"

    cat > "$report_path" <<EOF
{
  "rollback_timestamp": "$(date -Iseconds)",
  "deployment_id": "$DEPLOYMENT_ID",
  "backup_path": "$BACKUP_DIR/$DEPLOYMENT_ID",
  "status": "success",
  "bot_pid": "$(cat "$PROJECT_ROOT/bot.pid" 2>/dev/null || echo 'unknown')",
  "log_file": "$ROLLBACK_LOG",
  "steps": {
    "stop_current": "completed",
    "restore_files": "completed",
    "reinstall_dependencies": "completed",
    "start_restored": "completed",
    "health_checks": "passed"
  }
}
EOF

    log_success "Rollback report: $report_path"
}

################################################################################
# Main Execution
################################################################################

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --deployment-id)
                DEPLOYMENT_ID="$2"
                shift 2
                ;;
            --list-backups)
                LIST_BACKUPS=true
                shift
                ;;
            --skip-database)
                SKIP_DATABASE=true
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Automated rollback script for OrderPilot-AI trading bot.

Options:
  --deployment-id ID   Rollback to specific deployment (default: latest)
  --list-backups       List available backups and exit
  --skip-database      Skip database restoration
  -h, --help          Show this help message

Rollback Steps:
  1. Stop current running instances
  2. Restore source code from backup
  3. Restore configuration files
  4. Restore database (optional)
  5. Reinstall dependencies
  6. Start restored version
  7. Run health checks

Exit Codes:
  0 - Rollback successful
  1 - Rollback failed
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
    parse_arguments "$@"

    # Setup
    mkdir -p "$ROLLBACK_LOG_DIR"

    # List backups if requested
    if [[ "$LIST_BACKUPS" == "true" ]]; then
        list_available_backups
        exit 0
    fi

    # Print header
    echo "=================================="
    echo "  OrderPilot-AI Rollback"
    echo "=================================="
    echo "Log: $ROLLBACK_LOG"
    echo ""

    log_info "Starting rollback at $(date)"

    # Run rollback steps
    select_backup
    verify_backup

    # Confirm rollback
    echo ""
    echo -e "${YELLOW}⚠ WARNING:${NC} About to rollback to deployment: $DEPLOYMENT_ID"
    echo -n "Continue? [y/N] "
    read -r confirm

    if [[ "$confirm" != "y" ]] && [[ "$confirm" != "Y" ]]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi

    echo ""

    stop_current_bot
    restore_files
    reinstall_dependencies
    start_restored_bot
    verify_rollback
    create_rollback_report

    # Print summary
    echo ""
    echo "=================================="
    echo "  Rollback Successful!"
    echo "=================================="
    echo -e "${GREEN}✓${NC} Rolled back to: $DEPLOYMENT_ID"
    echo -e "${GREEN}✓${NC} Bot PID: $(cat "$PROJECT_ROOT/bot.pid" 2>/dev/null || echo 'unknown')"
    echo -e "${GREEN}✓${NC} Log: $ROLLBACK_LOG"
    echo ""

    log_success "Rollback completed successfully!"
    exit 0
}

main "$@"
