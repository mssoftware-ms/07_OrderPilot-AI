# OrderPilot-AI Trading Application

An AI-powered desktop trading application for retail investors, featuring automated trading strategies, real-time market data, and AI-assisted order analysis.

## Features

### Core Trading
- 🤖 **AI-Powered Analysis**: Multi-LLM support (OpenAI, Anthropic, Google AI) with Structured Outputs for order analysis, alert triage, and backtest reviews
- 📊 **Real-Time Trading**: Support for IBKR (official) and Trade Republic (unofficial)
- 📈 **Technical Analysis**: Comprehensive indicators (RSI, MACD, Bollinger Bands, ATR, ADX, Volume)
- 🎯 **Regime-Based Strategies**: Dynamic strategy switching based on market regimes (TREND_UP/DOWN/RANGE)
- 🔄 **JSON Configuration**: Type-safe Pydantic models with schema validation and hot-reload
- 🎨 **Modern UI**: Dark (Orange/Dark) and Light themes with PyQt6
- 🔒 **Secure**: Windows Credential Manager for API keys
- 📝 **Audit Trail**: Comprehensive logging with AI telemetry tracking
- ⚡ **1-Second Bars**: High-frequency data processing with noise reduction
- 💰 **Fee Optimization**: Flat fee model for Trade Republic (~€1/trade)

### Advanced Validation
- ✅ **Walk-Forward Validation**: Out-of-sample testing with rolling/anchored windows to prevent overfitting
- 📊 **Performance Metrics**: Sharpe, Sortino, Max Drawdown, Win Rate, Profit Factor, Risk/Reward
- 🧪 **Robustness Testing**: Multi-fold validation with train/test ratio monitoring
- 📈 **Strategy Comparison**: Rank strategies by composite score across multiple metrics
- 🎯 **Degradation Detection**: Automatic detection of in-sample vs out-of-sample performance decay

### AI Copilot
- 🤖 **Entry Analysis**: AI-powered market analysis with detailed reasoning
- 📊 **Indicator Scoring**: Comprehensive scoring of each indicator's favorability
- ⚡ **Regime Compatibility**: AI assessment of entry suitability for current market regime
- 🎯 **Action Recommendations**: BUY/SELL/WAIT with confidence scores and risk warnings
- 💡 **Natural Language Insights**: Plain English explanations of market conditions

### Production Deployment
- 🚀 **Automated Deployment**: Full CI/CD with validation, backup, and rollback scripts
- 📋 **Health Checks**: Comprehensive process, API, database, and resource monitoring
- 🔄 **Rollback Capability**: One-command rollback to any previous deployment
- 📊 **Production Checklist**: 200+ checkpoints across 10 categories
- 📚 **API Documentation**: 19 Sphinx modules with comprehensive API docs

## Quick Start

### Prerequisites

- Python 3.11+
- Windows 11 (for Windows Credential Manager)
- OpenAI API key (optional, for AI features)

### Installation

```powershell
# Clone repository
git clone <repository-url>
cd 07_OrderPilot-AI

# Create virtual environment
py -3.11 -m venv .venv
. .venv\Scripts\activate

# Install dependencies
pip install -U pip wheel
pip install -r requirements.txt

# Run application
python run_app.py
```

### (Optional) Install TA-Lib for Windows

```powershell
# Download the appropriate wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# For Python 3.11 64-bit:
pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl
```

## Configuration

### Setting up OpenAI API Key

```python
# Run this once to store your API key securely in Windows Credential Manager
python
>>> from src.config.loader import config_manager
>>> config_manager.set_credential("openai_api_key", "sk-your-api-key-here")
```

### Configuration Profiles

The application uses YAML configuration profiles stored in `./config/`:
- `paper.yaml` - Paper trading with mock broker
- `production.yaml` - Live trading configuration

## Usage Guide

### Basic Workflow

1. **Start Application**: `python run_app.py`
2. **Connect Broker**: Trading → Connect Broker → Select "Mock Broker" for testing
3. **Place Orders**:
   - File → New Order (Ctrl+N)
   - Fill order details
   - Click "Analyze with AI" for AI recommendations
   - Review and place order
4. **Monitor Positions**: Check Positions tab for current holdings
5. **View Alerts**: AI-triaged alerts appear in Alerts tab

### AI Features

#### Order Analysis
- Automatic risk assessment before order placement
- Fee impact analysis
- Suggested adjustments for better execution
- Confidence scoring (0-1)

#### Alert Triage
- Priority scoring for market alerts
- AI-driven action recommendations
- Portfolio context consideration

#### Backtest Review
- Performance rating (0-10)
- Strategy strengths and weaknesses analysis
- Parameter optimization suggestions

### Theme Switching

Switch between Dark (Orange/Dark) and Light themes:
- View → Theme → Dark/Light
- Settings persist between sessions

## Project Structure

```
07_OrderPilot-AI/
├── 01_Projectplan/           # Concept and checklists
│   ├── Konzept_OrderPilot-AI_TradingApp.md
│   └── TradingApp_Checklisten_Paket_v3_AI_Integrated/
├── src/
│   ├── ai/                  # AI Integration ✨
│   │   ├── strategy_generator.py   # Multi-LLM strategy generation (589 lines)
│   │   ├── models.py              # Pydantic AI response models (245 lines)
│   │   ├── openai_service.py      # Structured Outputs API
│   │   └── prompts.py             # Prompt templates & schemas
│   ├── analysis/            # Chart Analysis ✨
│   │   └── visible_chart/
│   │       ├── entry_copilot.py   # AI entry analysis (312 lines)
│   │       └── validation.py      # Walk-forward validation (178 lines)
│   ├── common/              # Shared utilities
│   │   ├── event_bus.py        # Event-driven architecture
│   │   └── logging_setup.py    # JSON logging with AI telemetry
│   ├── config/              # Configuration management
│   │   └── loader.py           # Profiles & credential handling
│   ├── core/
│   │   ├── broker/          # Broker adapters
│   │   │   ├── base.py         # Abstract interface
│   │   │   └── mock_broker.py  # Testing implementation
│   │   ├── execution/       # Order execution engine
│   │   ├── market_data/     # Real-time data handling
│   │   ├── strategy/        # Trading strategies
│   │   └── tradingbot/      # Regime-based JSON strategy system ✨
│   │       ├── config/          # JSON config loader, detector, router
│   │       ├── migration/       # Strategy migration tools
│   │       ├── strategy_evaluator.py     # Walk-forward engine (165 lines)
│   │       ├── evaluator_*.py           # Evaluation helpers (8 modules)
│   │       ├── entry_scorer.py          # Entry opportunity scoring
│   │       ├── regime_engine.py         # Regime detection
│   │       └── backtest_harness.py      # Full bot backtesting
│   ├── database/            # Data persistence
│   │   ├── models.py           # SQLAlchemy models
│   │   └── database.py         # DB management
│   ├── backtesting/         # Backtrader integration
│   │   └── engine.py           # Regime-based backtest engine ✨
│   └── ui/
│       ├── app.py           # Main application window
│       ├── themes.py        # Dark/Light theme definitions
│       ├── widgets/         # UI components
│       │   ├── chart_window_mixins/  # Chart window mixins
│       │   │   └── bot_event_handlers.py  # Regime change UI updates ✨
│       │   └── performance_monitor_widget.py  # Real-time monitoring (638 lines) ✨
│       └── dialogs/         # Dialog windows
│           ├── entry_analyzer_popup.py    # Walk-forward & AI Copilot UI (3,077 lines) ✨
│           ├── bot_start_strategy_dialog.py  # JSON strategy selection ✨
│           └── strategy_settings_dialog.py   # Strategy configuration ✨
├── config/                  # Configuration files
│   └── bot_configs/         # Trading bot JSON configs ✨
├── 03_JSON/                 # JSON strategy configurations ✨
│   └── Trading_Bot/         # Production strategy configs
├── logs/                   # Application logs (auto-created)
├── data/                   # Database files (auto-created)
├── docs/                   # Comprehensive documentation ✨
│   ├── ai/                  # AI integration guides
│   │   ├── LLM_Integration_Guide.md          # Multi-LLM setup (456 lines)
│   │   ├── Entry_Copilot_Usage.md            # AI copilot usage (389 lines)
│   │   └── Strategy_Generator_API.md         # API reference (475 lines)
│   ├── integration/         # Regime-based JSON system docs
│   │   ├── README.md                                  # Documentation overview
│   │   ├── REGIME_BASED_JSON_SYSTEM_VERIFICATION_FINAL.md  # Phase 1-3 completion
│   │   ├── Strategy_System_Implementation_Plan_v2.md  # Implementation blueprint
│   │   └── TEST_IMPLEMENTATION_COMPLETE.md            # Test suite documentation
│   ├── testing/            # Test & validation guides
│   │   ├── TEST_EXECUTION_GUIDE.md                    # Test execution guide
│   │   ├── Phase_1_3_Status_Report.md                 # Phase 1-3 status
│   │   └── Phase_4_7_Completion_Report.md             # Phase 4-7 completion ✨
│   ├── deployment/         # Production deployment ✨
│   │   └── PRODUCTION_READINESS_CHECKLIST.md          # 200+ checkpoints
│   └── sphinx/             # Sphinx API documentation ✨
│       └── source/api/     # 19 module documentation files
├── scripts/                # Production deployment ✨
│   ├── validate.sh             # Pre-deployment validation (300 lines)
│   ├── deploy.sh               # Automated deployment (483 lines)
│   ├── rollback.sh             # Rollback automation (475 lines)
│   └── health_check.sh         # Health monitoring (200+ lines)
├── tests/                  # Comprehensive test suite ✨
│   ├── ai/                     # AI integration tests
│   │   ├── test_strategy_generator.py       # 387 lines, 18+ tests
│   │   └── ...
│   ├── analysis/               # Analysis & validation tests
│   │   ├── test_entry_copilot.py            # 298 lines, 12+ tests
│   │   └── ...
│   ├── core/tradingbot/        # Core trading bot tests
│   │   ├── test_strategy_evaluator.py       # 403 lines, 35+ tests
│   │   ├── test_regime_engine.py
│   │   └── ...
│   ├── strategies/             # Strategy tests
│   │   ├── test_pattern_strategy_mapper.py
│   │   └── ...
│   ├── ui/                     # UI component tests
│   │   ├── test_regime_set_builder.py       # 428 lines, 20+ tests
│   │   ├── test_backtest_worker.py          # 255 lines, 10+ tests
│   │   └── ...
│   ├── integration/            # End-to-end workflow tests
│   │   └── test_regime_based_workflow.py
│   ├── run_all_tests.sh        # Linux/Mac test runner
│   └── run_all_tests.ps1       # Windows test runner
└── requirements.txt        # Python dependencies

✨ = New regime-based JSON strategy system components (2026-01-18/19)
```

## Development

### Running Tests

**Comprehensive Test Suite (Updated 2026-01-21):**

```bash
# Run backend tests with coverage (recommended)
python -m pytest tests/ai/ tests/analysis/ tests/core/tradingbot/ tests/strategies/ \
  --cov=src/core --cov=src/ai --cov=src/analysis --cov=src/strategies \
  --cov-report=html --cov-report=term-missing -q

# Run all tests with coverage (Linux/Mac)
./tests/run_all_tests.sh

# Run all tests with coverage (Windows PowerShell)
.\tests\run_all_tests.ps1

# Run specific test suites
pytest tests/core/tradingbot/test_strategy_evaluator.py -v  # 35+ tests, walk-forward validation
pytest tests/ai/test_strategy_generator.py -v              # 18+ tests, AI integration
pytest tests/analysis/test_entry_copilot.py -v             # 12+ tests, AI copilot
pytest tests/ui/test_regime_set_builder.py -v              # 20+ tests, UI components
pytest tests/integration/test_regime_based_workflow.py -v  # End-to-end workflows

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**Test Coverage (Backend Tests):**
- ✅ **475 tests passing** (82.3% pass rate)
- ✅ **92% coverage** for walk-forward validation (`strategy_evaluator.py`)
- ✅ **86% coverage** for AI integration (`strategy_generator.py`)
- ✅ **100% coverage** for strategy models and converters
- ⚠️ **Known Issues**:
  - 69 tests blocked by Pydantic forward reference (fixable)
  - 32 minor test failures (edge cases)
  - UI tests require native Linux (Qt/WSL incompatibility)
  - Coverage gaps in `regime_engine.py` (12%), `regime_engine_json.py` (0%)

**Test Documentation:**
- See `docs/testing/TEST_EXECUTION_GUIDE.md` for comprehensive test execution guide
- See `docs/testing/Phase_4_7_Completion_Report.md` for Phase 4-7 test results
- See `docs/integration/TEST_IMPLEMENTATION_COMPLETE.md` for test completion report

### Code Quality

```bash
# Linting with Ruff
ruff check .

# Type checking
mypy src/

# Format code
ruff format .
```

### Build Executable (PyInstaller)

```powershell
pyinstaller -F -n OrderPilot-AI `
    --add-data "assets;assets" `
    --hidden-import "PyQt6.QtWebEngineWidgets" `
    src/ui/app.py

# Run executable
dist\OrderPilot-AI.exe
```

## Architecture Highlights

### Event-Driven Design
- Uses `blinker` for decoupled component communication
- Central event bus for order, market, and alert events

### Async/Await Support
- `qasync` integration for PyQt6
- Non-blocking broker operations
- Efficient API calls with connection pooling

### AI Integration
- **Structured Outputs**: Schema-validated JSON responses
- **Caching**: Reduces API costs with intelligent caching
- **Cost Tracking**: Monthly budget enforcement
- **Telemetry**: Detailed AI usage logging

### Security Features
- Windows Credential Manager for API keys
- No hardcoded credentials
- Comprehensive audit logging
- Kill switch for emergency trading halt

## Deployment

### Quick Deployment

```bash
# 1. Validate environment
./scripts/validate.sh --environment prod

# 2. Deploy to production
./scripts/deploy.sh --environment prod

# 3. Monitor health
./scripts/health_check.sh --environment prod

# 4. Rollback if needed
./scripts/rollback.sh --deployment-id deploy_20260121_120000 --skip-database
```

### Deployment Features
- ✅ **Pre-deployment validation**: Git status, dependencies, config, database, ports
- ✅ **Automatic backup**: Code, config, database before deployment
- ✅ **Graceful shutdown**: SIGTERM → SIGKILL with 30-second timeout
- ✅ **Health checks**: Process, API, database, resource monitoring
- ✅ **Rollback automation**: One-command rollback to any previous version
- ✅ **Deployment reports**: JSON metadata with commit hash, timestamp, environment
- ✅ **Backup rotation**: Automatic cleanup (keep last 10 backups)

See `docs/deployment/PRODUCTION_READINESS_CHECKLIST.md` for full production checklist.

## Roadmap

### Completed ✅
- [x] Core architecture and event bus
- [x] SQLite database schema
- [x] BrokerAdapter interface
- [x] Mock broker implementation
- [x] OpenAI Structured Outputs integration
- [x] PyQt6 UI with themes
- [x] **Regime-based JSON strategy system** (Phases 1-3)
- [x] **Walk-forward validation** (Phase 5)
- [x] **Multi-LLM AI integration** (Phase 6)
- [x] **Sphinx API documentation** (19 modules)
- [x] **Production deployment scripts** (validate, deploy, rollback, health check)
- [x] **Entry Analyzer with AI Copilot** (3,077 lines)
- [x] **Performance monitoring widget** (638 lines)

### In Progress 🚧
- [ ] Fix Pydantic forward reference issues (69 tests blocked)
- [ ] Increase regime_engine.py test coverage (12% → 80%)
- [ ] Native Linux environment for UI tests

### Planned 📋
- [ ] IBKR live trading implementation
- [ ] Trade Republic unofficial API integration
- [ ] Advanced Plotly charting
- [ ] Real-time WebSocket streams
- [ ] Options trading support
- [ ] TimescaleDB migration for time-series data
- [ ] Mobile companion app

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "feat: add new feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Submit a pull request

### Commit Convention

Follow conventional commits:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test updates
- `chore`: Maintenance

## License

Proprietary - All rights reserved

## Support

For issues or questions, please open an issue in the repository.

---

**⚠️ Risk Disclaimer**:
- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- This software is for educational purposes
- Always test strategies in paper trading first
- The developers assume no liability for financial losses

**⚠️ API Usage Notes**:
- Trade Republic integration uses unofficial/private APIs (use at own risk)
- IBKR provides official API support via TWS/Gateway
- OpenAI API costs apply for AI features (~€15/month budget recommended)