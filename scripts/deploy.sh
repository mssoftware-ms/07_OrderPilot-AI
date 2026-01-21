#!/bin/bash
################################################################################
# deploy.sh - Automated Deployment Script
#
# Performs automated deployment of OrderPilot-AI trading bot:
# - Pre-deployment validation
# - Backup current version
# - Stop running instances
# - Deploy new version
# - Database migrations (if needed)
# - Start new instances
# - Health checks
# - Rollback on failure
#
# Usage:
#   ./scripts/deploy.sh [--environment prod|staging] [--skip-validation] [--force]
#
# Exit Codes:
#   0 - Deployment successful
#   1 - Deployment failed (rolled back)
#   2 - Critical error (manual intervention required)
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
DEPLOY_LOG_DIR="$PROJECT_ROOT/logs/deployment"
DEPLOY_LOG="$DEPLOY_LOG_DIR/deploy_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="$PROJECT_ROOT/backups"
DEPLOYMENT_ID="deploy_$(date +%Y%m%d_%H%M%S)"

# Options
ENVIRONMENT="staging"
SKIP_VALIDATION=false
FORCE_DEPLOY=false

# Deployment state
DEPLOYMENT_STARTED=false
BACKUP_CREATED=false
OLD_VERSION_STOPPED=false
NEW_VERSION_STARTED=false

################################################################################
# Helper Functions
################################################################################

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $*" | tee -a "$DEPLOY_LOG"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $*" | tee -a "$DEPLOY_LOG"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*" | tee -a "$DEPLOY_LOG"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}✗${NC} $*" | tee -a "$DEPLOY_LOG"
}

cleanup_on_error() {
    log_error "Deployment failed! Initiating rollback..."

    if [[ "$NEW_VERSION_STARTED" == "true" ]]; then
        log_info "Stopping new version..."
        stop_bot
    fi

    if [[ "$BACKUP_CREATED" == "true" ]]; then
        log_info "Rolling back to previous version..."
        "$SCRIPT_DIR/rollback.sh" --deployment-id "$DEPLOYMENT_ID" || {
            log_error "Rollback failed! Manual intervention required"
            exit 2
        }
    fi

    exit 1
}

trap cleanup_on_error ERR

################################################################################
# Deployment Steps
################################################################################

run_validation() {
    if [[ "$SKIP_VALIDATION" == "true" ]]; then
        log_warning "Skipping validation (--skip-validation flag)"
        return 0
    fi

    log_info "=== Running Pre-Deployment Validation ==="

    if "$SCRIPT_DIR/validate.sh" --environment "$ENVIRONMENT" >> "$DEPLOY_LOG" 2>&1; then
        log_success "Validation passed"
        return 0
    else
        log_error "Validation failed"

        if [[ "$FORCE_DEPLOY" == "true" ]]; then
            log_warning "Continuing deployment despite validation failure (--force flag)"
            return 0
        else
            log_error "Aborting deployment. Use --force to override."
            exit 1
        fi
    fi
}

create_backup() {
    log_info "=== Creating Backup ==="

    local backup_path="$BACKUP_DIR/$DEPLOYMENT_ID"
    mkdir -p "$backup_path"

    # Backup source code
    log_info "Backing up source code..."
    if cp -r "$PROJECT_ROOT/src" "$backup_path/src"; then
        log_success "Source code backed up"
    else
        log_error "Source code backup failed"
        return 1
    fi

    # Backup configuration files
    log_info "Backing up configuration..."
    if [[ -d "$PROJECT_ROOT/config" ]]; then
        cp -r "$PROJECT_ROOT/config" "$backup_path/config"
        log_success "Configuration backed up"
    fi

    if [[ -d "$PROJECT_ROOT/03_JSON" ]]; then
        cp -r "$PROJECT_ROOT/03_JSON" "$backup_path/03_JSON"
        log_success "JSON configs backed up"
    fi

    # Backup database (if exists)
    if [[ -f "$PROJECT_ROOT/data/tradingbot.db" ]]; then
        log_info "Backing up database..."
        mkdir -p "$backup_path/data"
        cp "$PROJECT_ROOT/data/tradingbot.db" "$backup_path/data/tradingbot.db"
        log_success "Database backed up"
    fi

    # Create backup metadata
    cat > "$backup_path/metadata.json" <<EOF
{
  "deployment_id": "$DEPLOYMENT_ID",
  "timestamp": "$(date -Iseconds)",
  "environment": "$ENVIRONMENT",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "backup_path": "$backup_path"
}
EOF

    log_success "Backup created: $backup_path"
    BACKUP_CREATED=true

    # Cleanup old backups (keep last 10)
    log_info "Cleaning up old backups..."
    ls -t "$BACKUP_DIR" | tail -n +11 | xargs -I {} rm -rf "$BACKUP_DIR/{}" 2>/dev/null || true

    return 0
}

stop_bot() {
    log_info "=== Stopping Running Instances ==="

    # Find running bot processes
    local bot_pids=$(pgrep -f "python.*main.py" || true)

    if [[ -z "$bot_pids" ]]; then
        log_info "No running bot instances found"
        return 0
    fi

    log_info "Found running processes: $bot_pids"

    # Graceful shutdown (SIGTERM)
    log_info "Sending SIGTERM for graceful shutdown..."
    echo "$bot_pids" | xargs -r kill -TERM 2>/dev/null || true

    # Wait for shutdown (max 30 seconds)
    local wait_time=0
    while [[ -n "$(pgrep -f 'python.*main.py' || true)" ]] && [[ $wait_time -lt 30 ]]; do
        sleep 1
        ((wait_time++))
        echo -n "." | tee -a "$DEPLOY_LOG"
    done
    echo "" | tee -a "$DEPLOY_LOG"

    # Force kill if still running
    if [[ -n "$(pgrep -f 'python.*main.py' || true)" ]]; then
        log_warning "Graceful shutdown timeout, forcing kill..."
        pgrep -f "python.*main.py" | xargs -r kill -9 2>/dev/null || true
        sleep 2
    fi

    # Verify stopped
    if [[ -z "$(pgrep -f 'python.*main.py' || true)" ]]; then
        log_success "All bot instances stopped"
        OLD_VERSION_STOPPED=true
        return 0
    else
        log_error "Failed to stop bot instances"
        return 1
    fi
}

deploy_code() {
    log_info "=== Deploying New Version ==="

    # Git pull (if using git deployment)
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        log_info "Pulling latest code from git..."

        cd "$PROJECT_ROOT"

        # Stash local changes
        if git diff --quiet; then
            log_info "No local changes to stash"
        else
            log_warning "Stashing local changes..."
            git stash save "auto-stash-before-deploy-$DEPLOYMENT_ID"
        fi

        # Pull latest
        if git pull origin "$(git rev-parse --abbrev-ref HEAD)" >> "$DEPLOY_LOG" 2>&1; then
            log_success "Code pulled from git"
        else
            log_error "Git pull failed"
            return 1
        fi

        # Log deployment commit
        local commit_hash=$(git rev-parse HEAD)
        local commit_msg=$(git log -1 --pretty=%B)
        log_info "Deployed commit: $commit_hash"
        log_info "Commit message: $commit_msg"
    fi

    # Install/update dependencies
    log_info "Installing dependencies..."
    if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi

    if pip3 install -q -r "$PROJECT_ROOT/requirements.txt" >> "$DEPLOY_LOG" 2>&1; then
        log_success "Dependencies installed"
    else
        log_error "Dependency installation failed"
        return 1
    fi

    # Run database migrations (if needed)
    if [[ -f "$PROJECT_ROOT/scripts/migrate.sh" ]]; then
        log_info "Running database migrations..."
        if "$PROJECT_ROOT/scripts/migrate.sh" >> "$DEPLOY_LOG" 2>&1; then
            log_success "Database migrations completed"
        else
            log_warning "Database migration failed (non-critical)"
        fi
    fi

    log_success "Deployment completed"
    return 0
}

start_bot() {
    log_info "=== Starting New Version ==="

    # Activate virtual environment
    if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi

    # Determine start command based on environment
    local start_command
    case "$ENVIRONMENT" in
        prod)
            start_command="python3 -m src.main --environment production --config /etc/tradingbot/config.json"
            ;;
        staging)
            start_command="python3 -m src.main --environment staging"
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            return 1
            ;;
    esac

    # Start bot in background
    log_info "Starting bot with: $start_command"

    cd "$PROJECT_ROOT"
    nohup $start_command > "$DEPLOY_LOG_DIR/bot_stdout.log" 2>&1 &
    local bot_pid=$!

    log_info "Bot started with PID: $bot_pid"

    # Wait for startup (5 seconds)
    sleep 5

    # Verify process is running
    if ps -p "$bot_pid" > /dev/null; then
        log_success "Bot process running (PID: $bot_pid)"
        NEW_VERSION_STARTED=true

        # Save PID for monitoring
        echo "$bot_pid" > "$PROJECT_ROOT/bot.pid"

        return 0
    else
        log_error "Bot process died immediately after start"
        return 1
    fi
}

run_health_checks() {
    log_info "=== Running Health Checks ==="

    # Wait for bot to initialize (30 seconds)
    log_info "Waiting for bot initialization (30s)..."
    sleep 30

    # Run health check script
    if "$SCRIPT_DIR/health_check.sh" --environment "$ENVIRONMENT" >> "$DEPLOY_LOG" 2>&1; then
        log_success "Health checks passed"
        return 0
    else
        log_error "Health checks failed"
        return 1
    fi
}

create_deployment_report() {
    log_info "=== Generating Deployment Report ==="

    local report_path="$DEPLOY_LOG_DIR/deployment_report_$DEPLOYMENT_ID.json"

    cat > "$report_path" <<EOF
{
  "deployment_id": "$DEPLOYMENT_ID",
  "timestamp": "$(date -Iseconds)",
  "environment": "$ENVIRONMENT",
  "status": "success",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "backup_path": "$BACKUP_DIR/$DEPLOYMENT_ID",
  "log_file": "$DEPLOY_LOG",
  "bot_pid": "$(cat "$PROJECT_ROOT/bot.pid" 2>/dev/null || echo 'unknown')",
  "steps": {
    "validation": "$([ "$SKIP_VALIDATION" == "true" ] && echo "skipped" || echo "passed")",
    "backup": "completed",
    "stop_old": "completed",
    "deploy_code": "completed",
    "start_new": "completed",
    "health_checks": "passed"
  }
}
EOF

    log_success "Deployment report: $report_path"
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
            --skip-validation)
                SKIP_VALIDATION=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Automated deployment script for OrderPilot-AI trading bot.

Options:
  --environment ENV     Set environment (prod|staging, default: staging)
  --skip-validation    Skip pre-deployment validation
  --force              Force deployment even if validation fails
  -h, --help           Show this help message

Deployment Steps:
  1. Pre-deployment validation
  2. Backup current version
  3. Stop running instances
  4. Deploy new code (git pull + pip install)
  5. Run database migrations
  6. Start new instances
  7. Health checks
  8. Rollback on failure

Exit Codes:
  0 - Deployment successful
  1 - Deployment failed (rolled back)
  2 - Critical error (manual intervention required)
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
    mkdir -p "$DEPLOY_LOG_DIR" "$BACKUP_DIR"

    # Print header
    echo "=================================="
    echo "  OrderPilot-AI Deployment"
    echo "=================================="
    echo "Deployment ID: $DEPLOYMENT_ID"
    echo "Environment: $ENVIRONMENT"
    echo "Log: $DEPLOY_LOG"
    echo ""

    log_info "Starting deployment at $(date)"
    DEPLOYMENT_STARTED=true

    # Run deployment steps
    run_validation
    create_backup
    stop_bot
    deploy_code
    start_bot
    run_health_checks
    create_deployment_report

    # Print summary
    echo ""
    echo "=================================="
    echo "  Deployment Successful!"
    echo "=================================="
    echo -e "${GREEN}✓${NC} Deployment ID: $DEPLOYMENT_ID"
    echo -e "${GREEN}✓${NC} Environment: $ENVIRONMENT"
    echo -e "${GREEN}✓${NC} Bot PID: $(cat "$PROJECT_ROOT/bot.pid" 2>/dev/null || echo 'unknown')"
    echo -e "${GREEN}✓${NC} Backup: $BACKUP_DIR/$DEPLOYMENT_ID"
    echo -e "${GREEN}✓${NC} Log: $DEPLOY_LOG"
    echo ""

    log_success "Deployment completed successfully!"
    exit 0
}

main "$@"
