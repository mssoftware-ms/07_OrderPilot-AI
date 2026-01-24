#############################################################################
# End-to-End Integration Test Runner (PowerShell)
#
# Usage:
#   .\run_e2e_tests.ps1 -Mode all
#
# Modes:
#   all     - All tests with coverage
#   stage1  - Stage 1 regime optimization
#   stage2  - Stage 2 indicator optimization
#   quick   - Quick tests (exclude slow/ui)
#############################################################################

param(
    [ValidateSet('all', 'stage1', 'stage2', 'handoff', 'schema', 'perf', 'ui', 'quick')]
    [string]$Mode = 'all'
)

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "E2E Integration Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Generate fixtures if needed
Write-Host "► Setup: Generating test fixtures..." -ForegroundColor Yellow

if (-not (Test-Path "tests/fixtures/regime_optimization/regime_optimization_results_BTCUSDT_5m.json")) {
    Write-Host "  Generating test fixtures..."
    python tests/fixtures/generate_test_data.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to generate fixtures" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Test fixtures already present" -ForegroundColor Green
}

Write-Host ""

# Run tests based on mode
switch ($Mode) {
    'all' {
        Write-Host "► Running ALL E2E tests with coverage..." -ForegroundColor Yellow
        pytest tests/integration/test_regime_optimization_e2e.py `
            -v `
            --cov=src `
            --cov-report=html `
            --cov-report=term-missing `
            --tb=short
    }
    'stage1' {
        Write-Host "► Running Stage 1 tests..." -ForegroundColor Yellow
        pytest tests/integration/test_regime_optimization_e2e.py::TestStage1RegimeOptimization `
            -v `
            --tb=short
    }
    'stage2' {
        Write-Host "► Running Stage 2 tests..." -ForegroundColor Yellow
        pytest tests/integration/test_regime_optimization_e2e.py::TestStage2IndicatorOptimization `
            -v `
            --tb=short
    }
    'handoff' {
        Write-Host "► Running Stage 1→2 Handoff tests..." -ForegroundColor Yellow
        pytest tests/integration/test_regime_optimization_e2e.py::TestStage1ToStage2Handoff `
            -v `
            --tb=short
    }
    'schema' {
        Write-Host "► Running JSON Schema Validation tests..." -ForegroundColor Yellow
        pytest tests/integration/test_regime_optimization_e2e.py::TestJSONSchemaCompliance `
            -v `
            --tb=short
    }
    'perf' {
        Write-Host "► Running Performance Benchmark tests..." -ForegroundColor Yellow
        pytest tests/integration/test_regime_optimization_e2e.py::TestPerformanceBenchmark `
            -v `
            --tb=short
    }
    'ui' {
        Write-Host "► Running UI Integration tests..." -ForegroundColor Yellow
        pytest tests/integration/test_regime_optimization_e2e.py::TestEntryAnalyzerUIIntegration `
            -v `
            -m ui `
            --tb=short
    }
    'quick' {
        Write-Host "► Running QUICK tests (excluding slow and UI)..." -ForegroundColor Yellow
        pytest tests/integration/test_regime_optimization_e2e.py `
            -v `
            -m "not slow and not ui" `
            --tb=short `
            --timeout=60
    }
}

$TestExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($TestExitCode -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Coverage Report:" -ForegroundColor Green
    if (Test-Path "htmlcov/index.html") {
        Write-Host "  Open: htmlcov/index.html"
    }
} else {
    Write-Host "✗ Some tests failed (exit code: $TestExitCode)" -ForegroundColor Red
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

exit $TestExitCode
