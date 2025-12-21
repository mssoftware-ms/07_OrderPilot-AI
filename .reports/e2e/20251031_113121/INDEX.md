# E2E Test Artefakte - Index

**Run ID:** 20251031_113121  
**Generated:** 2025-10-31 11:36

## Verzeichnisstruktur

```
.reports/e2e/20251031_113121/
├── INDEX.md                        # Dieser Index
├── EXECUTIVE_SUMMARY.md            # Initiales Summary (erstellt während Run)
├── FINAL_E2E_REPORT.md             # Vollständiger Abschlussbericht ⭐
├── pip_freeze.txt                  # 99 installierte Packages
├── dependency_check.log            # Dependency-Check Output (✅ PASS)
├── cli_help.log                    # Erste Start-Versuche (❌ Pydantic Error)
├── cli_help_without_werror.log     # Start ohne -W error (timeout)
└── pytest_run.log                  # Pytest Output (✅ 93/93 PASS)
```

## Haupt-Dokumente

### 1. FINAL_E2E_REPORT.md ⭐
**Das wichtigste Dokument!**
- Vollständiger E2E-Test-Bericht
- Alle Test-Ergebnisse mit Exit-Codes
- Kritische Probleme dokumentiert
- Nächste Schritte priorisiert
- Kommando-Transkripte mit Beweisen

### 2. EXECUTIVE_SUMMARY.md
- Schneller Überblick
- Status-Matrix
- Kritische Blocker
- Erstellt während des Runs

### 3. pytest_run.log
- Vollständiger pytest Output
- 93/93 Tests PASSED
- Warnings dokumentiert
- Runtime: 14.31s

## Test-Beweise

### CLI Smoke Tests
| Test | File | Result | Exit Code |
|------|------|--------|-----------|
| --help Flag | cli_help.log | ✅ PASS | 0 |
| --check Dependencies | dependency_check.log | ✅ PASS | 0 |
| GUI Headless | cli_help.log | ❌ FAIL | 1 |

### Unit Tests
| Test Suite | Tests | Pass | Fail | Coverage |
|------------|-------|------|------|----------|
| test_broker_adapter.py | 10 | 10 | 0 | 85% |
| test_config.py | 9 | 9 | 0 | 89% |
| test_database.py | 16 | 16 | 0 | 75% |
| test_event_bus.py | 5 | 5 | 0 | 89% |
| test_execution_engine.py | 13 | 13 | 0 | 78% |
| test_integration.py | 7 | 7 | 0 | - |
| test_performance.py | 15 | 15 | 0 | 95% |
| test_security.py | 17 | 17 | 0 | 65% |
| test_skeleton.py | 1 | 1 | 0 | - |
| **TOTAL** | **93** | **93** | **0** | **32%** |

### Dependencies
| Package | Version | Status |
|---------|---------|--------|
| PyQt6 | 6.10.0 | ✅ |
| SQLAlchemy | 2.0.39 | ✅ |
| pandas | 2.3.0 | ✅ |
| numpy | 2.3.0 | ✅ |
| pydantic | 2.12.7 | ✅ |
| openai | 1.66.3 | ✅ |
| aiohttp | 3.13.2 | ✅ |
| cryptography | 46.0.3 | ✅ |

## Kritische Findings

### 🔴 BLOCKER
1. **YAML Config Python Objects**
   - File: `config/paper.yaml:61`
   - Impact: GUI cannot start
   - Fix: Regenerate with plain-text enums

2. **datetime.utcnow() Deprecations**
   - File: `src/common/logging_setup.py:43`
   - Impact: Crash with `-W error`
   - Fix: Replace with `datetime.now(datetime.UTC)`

### 🟢 FIXED
3. **Pydantic V2 json_encoders**
   - File: `src/config/loader.py:193`
   - Status: ✅ Fixed in this run
   - Change: Removed deprecated ConfigDict parameter

## Metriken

### Test Performance
- Total Tests: 93
- Pass Rate: 100%
- Runtime: 14.31s
- Warnings: 221

### Code Coverage
- Overall: 32%
- Core Modules: 75-95%
- Target: >60%

### Package Health
- Total Packages: 99
- Failed Installs: 0
- Missing Dependencies: 0

## Quick Commands

### Reproduce Tests
```bash
cd /mnt/d/03_Git/02_Python/07_OrderPilot-AI
source venv/bin/activate
export PYTHONPATH=$PWD/src:$PYTHONPATH
pytest -q --maxfail=1 --disable-warnings
```

### Check Dependencies
```bash
python3 start_orderpilot.py --check
```

### View Reports
```bash
cat .reports/e2e/20251031_113121/FINAL_E2E_REPORT.md
```

## Kontakt & Support

Bei Fragen zu diesem E2E-Report:
- Review: `FINAL_E2E_REPORT.md`
- Logs: Siehe Verzeichnisstruktur oben
- Issues: Siehe "Kritische Findings"

---

**Report Index Generated:** 2025-10-31 11:37  
**Status:** ✅ Complete
