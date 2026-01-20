# Run all tests for Regime-Based JSON Strategy System (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Regime-Based JSON Strategy System - Test Suite" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if pytest is installed
if (-not (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Write-Host "Error: pytest is not installed" -ForegroundColor Red
    Write-Host "Install with: pip install pytest pytest-qt pytest-cov"
    exit 1
}

# Create reports directory
New-Item -ItemType Directory -Force -Path test_reports | Out-Null

Write-Host "Running Unit Tests..." -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

# Run unit tests with coverage
pytest tests/ui/test_regime_set_builder.py `
    tests/core/test_dynamic_strategy_switching.py `
    tests/ui/test_backtest_worker.py `
    -v `
    --tb=short `
    --cov=src/ui/dialogs `
    --cov=src/core/tradingbot `
    --cov-report=html:test_reports/coverage_unit `
    --cov-report=term-missing `
    --junit-xml=test_reports/junit_unit.xml

$UnitExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "Running Integration Tests..." -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

# Run integration tests
pytest tests/integration/test_regime_based_workflow.py `
    -v `
    --tb=short `
    --junit-xml=test_reports/junit_integration.xml

$IntegrationExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($UnitExitCode -eq 0) {
    Write-Host "✓ Unit Tests: PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Unit Tests: FAILED" -ForegroundColor Red
}

if ($IntegrationExitCode -eq 0) {
    Write-Host "✓ Integration Tests: PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Integration Tests: FAILED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Reports generated in test_reports/"
Write-Host "- coverage_unit/index.html - Unit test coverage report"
Write-Host "- junit_unit.xml - Unit test JUnit report"
Write-Host "- junit_integration.xml - Integration test JUnit report"

# Overall exit code
if (($UnitExitCode -eq 0) -and ($IntegrationExitCode -eq 0)) {
    Write-Host ""
    Write-Host "All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "Some tests failed. See details above." -ForegroundColor Red
    exit 1
}
