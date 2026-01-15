# OrderPilot-AI - Quick Start Guide

## Installation

### 1. Create Virtual Environment
```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip wheel
pip install -r requirements.txt

# Or manually:
pip install pydantic sqlalchemy blinker cryptography aiohttp pandas numpy PyQt6 qasync openai pytest
```

### 3. Verify Installation
```bash
python main.py --check
```

Expected output:
```
✅ PyQt6 is installed
✅ SQLAlchemy is installed
✅ pandas is installed
✅ numpy is installed
✅ OpenAI is installed
✅ Pydantic is installed
✅ aiohttp is installed
✅ cryptography is installed

✅ All dependencies are installed
```

## Starting the Application

### Standard Start
```bash
python main.py
```

### With Mock Broker (Testing)
```bash
python main.py --mock
```

### Production Mode
```bash
python main.py --env production --profile aggressive
```

### Check Dependencies Only
```bash
python main.py --check
```

### All Options
```bash
python main.py --help
```

## Available Start Files

| File | Purpose | Use Case |
|------|---------|----------|
| `main.py` | **Recommended Entry Point** | Standard usage ⭐ |
| `start_orderpilot.py` | Full-featured launcher | Same as main.py |
| `run_app.py` | Minimal launcher | Direct GUI start |

## Common Issues

### Windows: "No module named 'aiohttp'"
```cmd
.venv\Scripts\activate
pip install aiohttp blinker cryptography pandas numpy PyQt6 qasync openai
```

### WSL/Linux: Permission denied
```bash
chmod +x main.py
python3 main.py
```

### GUI doesn't start
```bash
# Check dependencies first:
python main.py --check

# Try mock mode:
python main.py --mock
```

## Testing

```bash
# Run all tests:
pytest -v

# Run specific test:
pytest tests/test_broker_adapter.py -v

# With coverage:
pytest --cov=src --cov-report=html
```

## (Optional) aider CLI + Ollama

This project includes a helper script to run `aider` against a local Ollama server.

### Prerequisites

```powershell
# Install Ollama (and make sure `ollama` is on PATH)
# https://ollama.com

# Install aider
python -m pip install aider-install
```

### Start Ollama

```powershell
ollama pull qwen2.5-coder:7b-instruct
ollama serve
```

### Run aider (from repo)

```powershell
./tools/aider_ollama.ps1 -Model qwen2.5-coder:7b-instruct
```

If your Ollama endpoint is non-default:

```powershell
./tools/aider_ollama.ps1 -ApiBase http://127.0.0.1:11434 -Model qwen2.5-coder:7b-instruct
```

## Project Structure

```
OrderPilot-AI/
├── main.py                  ⭐ Main entry point
├── start_orderpilot.py      Full launcher
├── run_app.py               Minimal launcher
├── src/                     Source code
│   ├── ui/                  User interface
│   ├── core/                Core trading logic
│   ├── database/            Database models
│   ├── config/              Configuration
│   └── ai/                  AI integration
├── tests/                   Test suite (93 tests)
├── config/                  Configuration files
└── requirements.txt         Dependencies

```

## Support

- Check logs in `logs/` directory
- Run tests: `pytest -v`
- Dependency check: `python main.py --check`
- E2E Report: `.reports/e2e/20251031_113121/`

---

**For detailed documentation, see:**
- `README.md` - Full project documentation
- `.reports/e2e/20251031_113121/FINAL_E2E_REPORT.md` - Test report
