# OrderPilot-AI Production Deployment Checklist

> **Last Updated**: 2026-01-21
> **Version**: 1.0.0
> **Status**: Pre-Production Validation

This comprehensive checklist ensures the OrderPilot-AI trading bot is production-ready. Complete all items before deploying to live trading environments.

---

## Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Security Checklist](#2-security-checklist)
3. [Configuration Checklist](#3-configuration-checklist)
4. [Infrastructure Checklist](#4-infrastructure-checklist)
5. [Monitoring & Alerting](#5-monitoring--alerting)
6. [Testing & Validation](#6-testing--validation)
7. [Deployment Process](#7-deployment-process)
8. [Post-Deployment Verification](#8-post-deployment-verification)
9. [Rollback Procedures](#9-rollback-procedures)
10. [Documentation & Handover](#10-documentation--handover)

---

## 1. Pre-Deployment Checklist

### 1.1 Code Quality & Standards

- [ ] **All unit tests passing** (minimum 80% code coverage)
  - Run: `pytest tests/ --cov=src --cov-report=term-missing`
  - Verify coverage: `coverage report --fail-under=80`

- [ ] **Integration tests passing**
  - Alpaca API integration tests
  - LLM provider integration tests
  - Database integration tests

- [ ] **No critical linting issues**
  - Run: `flake8 src/ --max-line-length=120`
  - Fix all errors, warnings can be reviewed

- [ ] **Type checking passing**
  - Run: `mypy src/ --ignore-missing-imports`
  - Resolve all type errors

- [ ] **Code formatting consistent**
  - Run: `black --check src/`
  - Apply: `black src/` if needed

- [ ] **No security vulnerabilities**
  - Run: `bandit -r src/ --severity-level medium`
  - Run: `safety check`
  - Review and fix all HIGH/CRITICAL findings

### 1.2 Version Control & Code Freeze

- [ ] **All changes committed to version control**
  - `git status` shows clean working tree
  - No uncommitted changes

- [ ] **Release branch created**
  - Branch: `release/v{version}`
  - Tagged: `git tag -a v{version} -m "Production release {version}"`

- [ ] **Changelog updated**
  - Document all changes since last release
  - Include: features, bug fixes, breaking changes

- [ ] **Code review completed**
  - All PRs reviewed and approved
  - No open critical issues

- [ ] **Production hotfix process documented**
  - Emergency patch procedures
  - Rollback procedures tested

### 1.3 Dependencies & Environment

- [ ] **Python version verified**
  - Production: Python 3.10+ (recommended: 3.11)
  - Development: Same version as production

- [ ] **All dependencies pinned**
  - `requirements.txt` has exact versions (e.g., `pydantic==2.5.3`)
  - No version ranges (avoid `>=`, `~=`)

- [ ] **Virtual environment clean**
  - Fresh venv created: `python3 -m venv .venv`
  - Dependencies installed: `pip install -r requirements.txt`
  - No extra packages installed

- [ ] **OS-level dependencies documented**
  - System packages (e.g., `sqlite3`, `git`)
  - External services (e.g., PostgreSQL, Redis)

---

## 2. Security Checklist

### 2.1 Secrets Management

- [ ] **No secrets in code**
  - Search: `git grep -E "(password|api_key|secret|token)\s*=\s*['\"]"`
  - All secrets in environment variables or secret manager

- [ ] **Environment variables configured**
  - `ALPACA_API_KEY` (production key, NOT paper trading)
  - `ALPACA_SECRET_KEY` (production secret)
  - `OPENAI_API_KEY` (if using AI features)
  - `ANTHROPIC_API_KEY` (if using AI features)
  - `GOOGLE_AI_API_KEY` (if using AI features)

- [ ] **Secret rotation policy established**
  - API keys rotated quarterly
  - Emergency rotation procedure documented
  - Old keys revoked after rotation

- [ ] **Access control implemented**
  - API keys have minimum required permissions
  - Trading API keys NOT shared across environments
  - Separate keys for staging/production

### 2.2 Data Protection

- [ ] **Sensitive data encrypted at rest**
  - Database encryption enabled
  - File-based configs encrypted (if applicable)

- [ ] **Sensitive data encrypted in transit**
  - HTTPS for all API calls (Alpaca, LLM providers)
  - TLS 1.2+ required

- [ ] **Logs sanitized**
  - No API keys, passwords, or PII in logs
  - Audit log retention policy defined (90 days recommended)

- [ ] **Backup encryption**
  - Database backups encrypted
  - Config backups encrypted
  - Backup access restricted

### 2.3 Network Security

- [ ] **Firewall rules configured**
  - Outbound: Allow Alpaca API (*.alpaca.markets)
  - Outbound: Allow LLM providers (api.openai.com, etc.)
  - Inbound: SSH only (if applicable)

- [ ] **IP whitelisting (if required)**
  - Alpaca API whitelist configured
  - LLM provider whitelist configured

- [ ] **VPN/bastion host configured (if required)**
  - Production server only accessible via VPN
  - SSH keys enforced (no password auth)

### 2.4 Compliance & Auditing

- [ ] **Trading regulations reviewed**
  - SEC/FINRA regulations understood
  - Algorithmic trading disclosure (if required)
  - Pattern day trading rules understood

- [ ] **Audit logging enabled**
  - All trades logged with timestamp, strategy, regime
  - All configuration changes logged
  - All API calls logged (for debugging)

- [ ] **Data retention policy defined**
  - Trade logs: 7 years (SEC requirement)
  - Application logs: 90 days
  - Backups: 30 days

---

## 3. Configuration Checklist

### 3.1 Trading Configuration

- [ ] **JSON strategy configs validated**
  - Schema validation: `./scripts/validate.sh`
  - All configs in `03_JSON/Trading_Bot/` tested
  - Backtest results reviewed

- [ ] **Risk parameters verified**
  - `position_size_pct`: Max 5% per trade (recommended)
  - `max_leverage`: Max 2x (conservative)
  - `stop_loss_pct`: Minimum 1% (protect capital)
  - `take_profit_pct`: Risk/reward ratio >= 2:1

- [ ] **Trading hours configured**
  - Market hours: 9:30 AM - 4:00 PM ET (stock market)
  - Extended hours: Disabled (unless explicitly needed)
  - Holiday calendar: Alpaca calendar synced

- [ ] **Position limits set**
  - Max open positions: 5 (recommended for diversification)
  - Max position value: $10,000 per symbol (or as per risk tolerance)
  - Total portfolio exposure: Max 25% of capital

### 3.2 Environment Configuration

- [ ] **Environment variables set**
  ```bash
  # Trading Environment
  TRADING_ENV=production  # NOT 'paper'!

  # Alpaca Configuration
  ALPACA_API_KEY=<production-key>
  ALPACA_SECRET_KEY=<production-secret>
  ALPACA_BASE_URL=https://api.alpaca.markets  # Live trading
  ALPACA_DATA_URL=https://data.alpaca.markets

  # AI Providers (optional)
  OPENAI_API_KEY=<key>
  ANTHROPIC_API_KEY=<key>
  GOOGLE_AI_API_KEY=<key>

  # Application Settings
  LOG_LEVEL=INFO  # DEBUG in staging, INFO in production
  LOG_FILE=/var/log/orderpilot/bot.log
  DATA_DIR=/var/lib/orderpilot/data
  CONFIG_DIR=/etc/orderpilot/configs
  ```

- [ ] **Bot configuration file validated**
  - Location: `/etc/orderpilot/bot_config.json`
  - Backup location: `/etc/orderpilot/backups/`
  - Auto-reload enabled: `true` (production monitoring)

- [ ] **Logging configuration**
  - Log level: `INFO` (or `WARNING` for low-noise production)
  - Log rotation: Daily, keep 90 days
  - Log destination: File + syslog (for centralized logging)

### 3.3 Database Configuration

- [ ] **Database initialized**
  - SQLite: `data/tradingbot.db` created
  - PostgreSQL: Schema created (if using)
  - Indexes created for performance

- [ ] **Database backups scheduled**
  - Frequency: Daily at 2:00 AM (off-market hours)
  - Retention: 30 days
  - Backup location: `/var/backups/orderpilot/`

- [ ] **Database performance tuned**
  - SQLite: `PRAGMA journal_mode=WAL` (write-ahead logging)
  - SQLite: `PRAGMA synchronous=NORMAL` (balance safety/speed)
  - PostgreSQL: Connection pooling configured

---

## 4. Infrastructure Checklist

### 4.1 Server Requirements

- [ ] **Server specifications verified**
  - CPU: 2+ cores (4+ recommended)
  - RAM: 4GB minimum (8GB recommended)
  - Disk: 20GB minimum (SSD recommended)
  - Network: Stable, low latency (<50ms to Alpaca)

- [ ] **Operating system hardened**
  - OS: Ubuntu 22.04 LTS (or RHEL/CentOS 8+)
  - Security updates: Auto-applied
  - Unnecessary services: Disabled

- [ ] **System monitoring configured**
  - CPU usage alerts (>80% for 5 minutes)
  - Memory usage alerts (>90%)
  - Disk space alerts (<10% free)

### 4.2 Application Deployment

- [ ] **Deployment directory structure**
  ```
  /opt/orderpilot/           # Application root
  ├── src/                   # Source code
  ├── .venv/                 # Virtual environment
  ├── logs/                  # Application logs
  ├── data/                  # Database, cache
  ├── backups/               # Automated backups
  ├── scripts/               # Deployment scripts
  └── bot.pid                # Process ID file
  ```

- [ ] **File permissions set**
  - Application files: `orderpilot:orderpilot` (dedicated user)
  - Log files: `644` (read-only for others)
  - Config files: `600` (owner read/write only)

- [ ] **Process management configured**
  - Systemd service: `/etc/systemd/system/orderpilot.service`
  - Auto-restart on failure: `Restart=always`
  - Restart delay: `RestartSec=10s`

### 4.3 High Availability (Optional)

- [ ] **Redundancy configured**
  - Primary server + hot standby (recommended)
  - Load balancer (if multiple instances)

- [ ] **Failover tested**
  - Manual failover procedure documented
  - Automatic failover (if configured)

- [ ] **Database replication**
  - Master-slave replication (if using PostgreSQL)
  - Backup verification (restore tested)

---

## 5. Monitoring & Alerting

### 5.1 Application Monitoring

- [ ] **Health checks automated**
  - Schedule: Every 5 minutes
  - Script: `./scripts/health_check.sh --environment prod --alert-on-failure`
  - Cron: `*/5 * * * * /opt/orderpilot/scripts/health_check.sh`

- [ ] **Performance monitoring**
  - RegimeEngine classification speed (>1000/sec)
  - Entry scoring latency (<10ms)
  - API response times (<500ms)

- [ ] **Business metrics tracked**
  - Trades per day
  - Win rate (daily, weekly, monthly)
  - Profit/loss (daily, cumulative)
  - Max drawdown (alert if >10%)

### 5.2 Alerting Configuration

- [ ] **Alert channels configured**
  - Email: Critical alerts
  - SMS/Phone: Emergency alerts (bot stopped, critical error)
  - Slack/Discord: Info/warning alerts

- [ ] **Alert rules defined**

  **CRITICAL (Immediate Action Required)**:
  - Bot process stopped
  - Alpaca API connection lost
  - Database corruption detected
  - Position loss exceeds daily limit (e.g., -5%)

  **HIGH (Action Within 1 Hour)**:
  - High error rate in logs (>10 errors/minute)
  - Memory usage >90%
  - Disk space <10%
  - API rate limit approaching (>80%)

  **WARNING (Review Within 24 Hours)**:
  - Config reload failed
  - Strategy performance degraded
  - Unusual trading volume

- [ ] **On-call rotation established**
  - Primary on-call: [Name/Contact]
  - Secondary on-call: [Name/Contact]
  - Escalation path documented

### 5.3 Log Aggregation

- [ ] **Centralized logging configured**
  - Tool: ELK Stack, Splunk, or CloudWatch
  - All logs forwarded to central system
  - Retention: 90 days

- [ ] **Log dashboards created**
  - Error rate over time
  - Trade activity timeline
  - API response times
  - Regime transitions

---

## 6. Testing & Validation

### 6.1 Pre-Production Testing

- [ ] **Unit tests: 100% passing**
  - Command: `pytest tests/unit/`
  - Coverage: ≥80%

- [ ] **Integration tests: 100% passing**
  - Command: `pytest tests/integration/`
  - Alpaca API (paper trading)
  - Database operations
  - Config reloading

- [ ] **End-to-end tests: Passing**
  - Command: `pytest tests/e2e/`
  - Full trading workflow (paper trading)
  - Multi-regime scenarios
  - Error recovery

### 6.2 Backtesting Validation

- [ ] **Historical backtests completed**
  - Dataset: Last 2 years of data
  - Timeframes: 1m, 5m, 15m, 1h
  - Results: Positive Sharpe ratio (>1.0)

- [ ] **Walk-forward validation passed**
  - Training window: 180 days
  - Test window: 60 days
  - Degradation: <20% (in-sample vs out-of-sample)

- [ ] **Robustness checks passed**
  - Min trades: ≥100 per test period
  - Max drawdown: ≤15%
  - Sharpe ratio: ≥1.0

### 6.3 Paper Trading Validation

- [ ] **Paper trading period completed**
  - Duration: Minimum 30 days
  - Environment: Alpaca Paper Trading
  - Performance: Meets expectations

- [ ] **Paper trading metrics reviewed**
  - Total trades: [Number]
  - Win rate: [Percentage] (target: ≥55%)
  - Profit factor: [Ratio] (target: ≥1.5)
  - Max drawdown: [Percentage] (target: ≤10%)
  - Sharpe ratio: [Ratio] (target: ≥1.0)

- [ ] **Edge cases tested in paper trading**
  - Market gaps (open different from previous close)
  - High volatility periods
  - Regime transitions
  - API outages (simulated)

### 6.4 Load & Stress Testing

- [ ] **Concurrent operation tested**
  - Multiple strategies active
  - High-frequency regime changes
  - Rapid position updates

- [ ] **API rate limit handling tested**
  - Alpaca rate limits respected (200 req/min)
  - Exponential backoff implemented
  - Graceful degradation

- [ ] **Database performance tested**
  - Large number of trades (>10,000)
  - Concurrent reads/writes
  - Backup/restore under load

---

## 7. Deployment Process

### 7.1 Pre-Deployment Steps

- [ ] **Deployment window scheduled**
  - Date/Time: [YYYY-MM-DD HH:MM]
  - Duration: 2 hours (expected)
  - Off-market hours: Recommended (after 4:00 PM ET)

- [ ] **Stakeholders notified**
  - Operations team
  - Finance/Risk management
  - On-call engineers

- [ ] **Rollback plan prepared**
  - Previous version backup verified
  - Rollback script tested: `./scripts/rollback.sh --list-backups`

- [ ] **Production credentials verified**
  - Alpaca production API keys ready
  - LLM provider keys ready (if used)
  - Database credentials ready

### 7.2 Deployment Execution

- [ ] **Step 1: Pre-deployment validation**
  ```bash
  ./scripts/validate.sh --environment prod
  ```
  - All checks must pass
  - Review validation report

- [ ] **Step 2: Create backup**
  ```bash
  ./scripts/deploy.sh --environment prod
  # Automatically creates backup
  ```
  - Backup ID: [Record here]
  - Backup location: [Record here]

- [ ] **Step 3: Deploy new version**
  - Git pull to production branch
  - Install dependencies
  - Run database migrations

- [ ] **Step 4: Start production bot**
  - Start bot with production config
  - Verify process started (PID: [Record here])

- [ ] **Step 5: Health checks**
  ```bash
  ./scripts/health_check.sh --environment prod --alert-on-failure
  ```
  - All checks must pass
  - Review health report

### 7.3 Deployment Verification

- [ ] **Bot process running**
  - PID file created: `/opt/orderpilot/bot.pid`
  - Process visible: `ps aux | grep python.*main.py`

- [ ] **Logs clean**
  - No errors in last 100 lines: `tail -100 /var/log/orderpilot/bot.log`
  - Regime detection working
  - API connections established

- [ ] **Configuration loaded**
  - JSON config parsed successfully
  - Strategies loaded: [Number]
  - Regimes configured: [Number]

---

## 8. Post-Deployment Verification

### 8.1 Immediate Verification (0-1 Hour)

- [ ] **Process stability**
  - Bot running for 1 hour without crashes
  - Memory usage stable (<500 MB growth/hour)
  - No error spikes in logs

- [ ] **API connectivity**
  - Alpaca Trading API: Responding
  - Alpaca Market Data API: Responding
  - Account status: ACTIVE
  - Buying power: Correct

- [ ] **Market data streaming**
  - Real-time quotes received
  - Indicators calculated correctly
  - Regime detection working

### 8.2 Short-term Verification (1-24 Hours)

- [ ] **First trades executed**
  - Entry conditions met and executed
  - Order fills confirmed
  - Positions opened correctly

- [ ] **Risk management active**
  - Stop losses set correctly
  - Take profits set correctly
  - Position sizing correct

- [ ] **Monitoring alerts working**
  - Health check cron running
  - Alerts received (test alert sent)

### 8.3 Long-term Verification (1-7 Days)

- [ ] **Trading performance**
  - Win rate tracking correctly
  - P&L calculation accurate
  - Drawdown within limits

- [ ] **Strategy adaptation**
  - Regime changes detected
  - Strategy switching working
  - Parameter overrides applied

- [ ] **System stability**
  - No memory leaks (memory usage flat)
  - No disk space issues (log rotation working)
  - Uptime: 99.9%+

---

## 9. Rollback Procedures

### 9.1 Rollback Triggers

**Immediate Rollback Required**:
- [ ] Bot crashes repeatedly (>3 crashes in 1 hour)
- [ ] Critical data corruption detected
- [ ] Unauthorized trades executed
- [ ] Position loss exceeds emergency threshold (e.g., -10% in 1 hour)

**Scheduled Rollback (Within 1 Hour)**:
- [ ] Error rate >50 errors/minute sustained
- [ ] API connectivity issues (>5 failed requests/minute)
- [ ] Memory leak detected (>2GB/hour growth)
- [ ] Trading performance severely degraded (win rate <30%)

### 9.2 Rollback Execution

- [ ] **Step 1: Stop current bot**
  ```bash
  sudo systemctl stop orderpilot
  # Or: pkill -TERM -f "python.*main.py"
  ```

- [ ] **Step 2: List available backups**
  ```bash
  ./scripts/rollback.sh --list-backups
  ```

- [ ] **Step 3: Execute rollback**
  ```bash
  ./scripts/rollback.sh --deployment-id [DEPLOYMENT_ID]
  ```

- [ ] **Step 4: Verify rollback**
  ```bash
  ./scripts/health_check.sh --environment prod
  ```

- [ ] **Step 5: Document incident**
  - Root cause: [Description]
  - Actions taken: [List]
  - Lessons learned: [List]

### 9.3 Post-Rollback Actions

- [ ] **Review logs from failed deployment**
  - Error patterns identified
  - Root cause determined

- [ ] **Create hotfix branch (if needed)**
  - Branch: `hotfix/issue-description`
  - Fix applied and tested
  - Re-deploy when ready

- [ ] **Update monitoring**
  - Add alerts for identified issues
  - Improve health checks

---

## 10. Documentation & Handover

### 10.1 Technical Documentation

- [ ] **Architecture documentation updated**
  - `ARCHITECTURE.md` reflects production setup
  - Data flows documented
  - Component interactions documented

- [ ] **API documentation complete**
  - Sphinx docs generated: `cd docs/api && make html`
  - All 19 modules documented
  - Examples tested and working

- [ ] **Configuration guide complete**
  - JSON config format documented
  - Example configs provided
  - Migration guide (if applicable)

### 10.2 Operational Documentation

- [ ] **Runbook created**
  - Daily operations: Health checks, log review
  - Weekly operations: Performance review, config updates
  - Monthly operations: Strategy backtesting, parameter optimization

- [ ] **Incident response guide**
  - Bot crash: [Procedure]
  - API outage: [Procedure]
  - Database corruption: [Procedure]
  - Unexpected trades: [Procedure]

- [ ] **Troubleshooting guide**
  - Common errors and solutions
  - Debug mode activation
  - Log analysis tips

### 10.3 Training & Handover

- [ ] **Operations team trained**
  - Deployment process walkthrough
  - Health check interpretation
  - Incident response procedures

- [ ] **Knowledge transfer sessions completed**
  - Architecture overview
  - Configuration management
  - Monitoring & alerting

- [ ] **Access credentials transferred**
  - API keys documented (secure vault)
  - Server access (SSH keys)
  - Monitoring dashboards (logins)

### 10.4 Compliance & Legal

- [ ] **Trading disclosures filed (if required)**
  - SEC Form 13F (if managing >$100M)
  - FINRA algorithmic trading disclosure

- [ ] **Risk disclosures documented**
  - Maximum position size
  - Maximum leverage
  - Stop loss policies

- [ ] **Audit trail enabled**
  - All trades logged with timestamps
  - All configuration changes logged
  - Logs tamper-proof (write-once storage)

---

## Deployment Sign-Off

### Production Readiness Certification

By signing below, I certify that:
1. All items in this checklist have been completed
2. The system has been tested in paper trading for minimum 30 days
3. Rollback procedures have been tested and verified
4. Monitoring and alerting are configured and functional
5. The system is ready for production deployment

**Deployment Lead**: ________________________
**Date**: ________________________

**Technical Reviewer**: ________________________
**Date**: ________________________

**Risk Manager**: ________________________
**Date**: ________________________

---

## Appendices

### A. Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Primary On-Call | [Name] | [Phone] | [Email] |
| Secondary On-Call | [Name] | [Phone] | [Email] |
| Infrastructure Team | [Name] | [Phone] | [Email] |
| Risk Management | [Name] | [Phone] | [Email] |

### B. Critical Commands Reference

```bash
# Check bot status
sudo systemctl status orderpilot
ps aux | grep python.*main.py

# View recent logs
tail -f /var/log/orderpilot/bot.log
tail -100 /var/log/orderpilot/bot.log | grep ERROR

# Health check
./scripts/health_check.sh --environment prod --detailed

# Emergency stop
sudo systemctl stop orderpilot
# Or: pkill -TERM -f "python.*main.py"

# Emergency rollback
./scripts/rollback.sh --deployment-id [LATEST]

# Validate before restart
./scripts/validate.sh --environment prod

# Start bot
sudo systemctl start orderpilot
```

### C. Performance Baselines

| Metric | Baseline | Alert Threshold |
|--------|----------|-----------------|
| RegimeEngine Speed | 2000+/sec | <1000/sec |
| Entry Scoring Latency | <5ms | >20ms |
| API Response Time | <200ms | >500ms |
| Memory Usage | ~300MB | >2GB |
| CPU Usage | <20% | >80% |
| Win Rate | 55%+ | <45% |
| Max Drawdown | <10% | >15% |
| Sharpe Ratio | >1.0 | <0.5 |

### D. Rollback Decision Matrix

| Severity | Condition | Action | Timeframe |
|----------|-----------|--------|-----------|
| P0 (Critical) | Bot crash loop, data corruption, unauthorized trades | Immediate rollback | <5 minutes |
| P1 (High) | Error rate >50/min, position loss >5%/hour | Rollback | <30 minutes |
| P2 (Medium) | Memory leak, API errors >10/min | Investigate, rollback if not resolved | <2 hours |
| P3 (Low) | Performance degradation, config reload failed | Monitor, rollback if worsens | <24 hours |

### E. Post-Deployment Monitoring Schedule

| Day | Activity | Success Criteria |
|-----|----------|------------------|
| Day 0 (Deploy) | Continuous monitoring (24h) | No errors, stable memory/CPU |
| Day 1 | Hourly health checks | First trades executed correctly |
| Day 2-7 | 4x daily health checks | Win rate >50%, no crashes |
| Week 2-4 | 2x daily health checks | Performance meets backtests ±10% |
| Month 2+ | Daily automated checks | Long-term stability confirmed |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-21 | OrderPilot Team | Initial production checklist |

---

**End of Production Deployment Checklist**
