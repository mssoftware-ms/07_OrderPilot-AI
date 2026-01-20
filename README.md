# OrderPilot-AI Trading Application

An AI-powered desktop trading application for retail investors, featuring automated trading strategies, real-time market data, and AI-assisted order analysis.

## Features

- 🤖 **AI-Powered Analysis**: OpenAI integration with Structured Outputs for order analysis, alert triage, and backtest reviews
- 📊 **Real-Time Trading**: Support for IBKR (official) and Trade Republic (unofficial)
- 📈 **Technical Analysis**: Comprehensive indicators (RSI, MACD, Bollinger Bands, ATR)
- 🔄 **Backtesting**: Strategy testing with Backtrader
- 🎨 **Modern UI**: Dark (Orange/Dark) and Light themes with PyQt6
- 🔒 **Secure**: Windows Credential Manager for API keys
- 📝 **Audit Trail**: Comprehensive logging with AI telemetry tracking
- ⚡ **1-Second Bars**: High-frequency data processing with noise reduction
- 💰 **Fee Optimization**: Flat fee model for Trade Republic (~€1/trade)

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
│   ├── ai/                  # OpenAI integration
│   │   ├── openai_service.py    # Structured Outputs API
│   │   └── prompts.py           # Prompt templates & schemas
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
│   │       └── backtest_harness.py  # Full bot backtesting
│   ├── database/            # Data persistence
│   │   ├── models.py           # SQLAlchemy models
│   │   └── database.py         # DB management
│   ├── backtesting/         # Backtrader integration
│   │   └── engine.py           # Regime-based backtest engine ✨
│   └── ui/
│       ├── app.py           # Main application window
│       ├── themes.py        # Dark/Light theme definitions
│       ├── widgets/         # UI components
│       │   └── chart_window_mixins/  # Chart window mixins
│       │       └── bot_event_handlers.py  # Regime change UI updates ✨
│       └── dialogs/         # Dialog windows
│           ├── entry_analyzer_popup.py    # Regime-based backtesting UI ✨
│           ├── bot_start_strategy_dialog.py  # JSON strategy selection ✨
│           └── strategy_settings_dialog.py   # Strategy configuration ✨
├── config/                  # Configuration files
│   └── bot_configs/         # Trading bot JSON configs ✨
├── 03_JSON/                 # JSON strategy configurations ✨
│   └── Trading_Bot/         # Production strategy configs
├── logs/                   # Application logs (auto-created)
├── data/                   # Database files (auto-created)
├── docs/                   # Comprehensive documentation
│   ├── integration/         # Regime-based JSON system docs ✨
│   │   ├── README.md                                  # Documentation overview
│   │   ├── REGIME_BASED_JSON_SYSTEM_VERIFICATION_FINAL.md  # 100% completion report
│   │   └── TEST_IMPLEMENTATION_COMPLETE.md            # Test suite documentation
│   └── testing/            # Test execution guides ✨
│       └── TEST_EXECUTION_GUIDE.md                    # How to run tests
├── tests/                  # Comprehensive test suite ✨
│   ├── ui/                     # UI component tests
│   │   ├── test_regime_set_builder.py        # 428 lines, 20+ tests
│   │   └── test_backtest_worker.py           # 255 lines, 10+ tests
│   ├── core/                   # Core functionality tests
│   │   └── test_dynamic_strategy_switching.py  # 363 lines, 15+ tests
│   ├── integration/            # End-to-end workflow tests
│   │   └── test_regime_based_workflow.py
│   ├── run_all_tests.sh        # Linux/Mac test runner
│   └── run_all_tests.ps1       # Windows test runner
└── requirements.txt        # Python dependencies

✨ = New regime-based JSON strategy system components (2026-01-18/19)
```

## Development

### Running Tests

**Comprehensive Test Suite Available (2026-01-19):**

```bash
# Run all tests with coverage (Linux/Mac)
./tests/run_all_tests.sh

# Run all tests with coverage (Windows PowerShell)
.\tests\run_all_tests.ps1

# Run specific test suites
pytest tests/ui/test_regime_set_builder.py -v
pytest tests/core/test_dynamic_strategy_switching.py -v
pytest tests/ui/test_backtest_worker.py -v
pytest tests/integration/test_regime_based_workflow.py -v

# Run all tests (simple)
pytest tests/ -v
```

**Test Coverage:**
- 45+ unit test methods (~1,300 lines of test code)
- ~92% coverage for tested components
- Integration test structure for end-to-end workflows

**Test Documentation:**
- See `docs/testing/TEST_EXECUTION_GUIDE.md` for comprehensive test execution guide
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

## Roadmap

- [x] Core architecture and event bus
- [x] SQLite database schema
- [x] BrokerAdapter interface
- [x] Mock broker implementation
- [x] OpenAI Structured Outputs integration
- [x] PyQt6 UI with themes
- [ ] IBKR live trading implementation
- [ ] Trade Republic unofficial API integration
- [ ] Advanced Plotly charting
- [ ] Backtrader strategy implementation
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