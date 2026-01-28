################################################################################
# CEL Editor UI Tests - PowerShell Execution Script
#
# This script runs pytest tests for CEL Editor UI fixes (Issues #1 and #5).
#
# Usage:
#   .\tests\run_ui_tests.ps1 [-Options]
#
# Options:
#   -All              Run all tests (default)
#   -Issue1           Run only Issue #1 tests (UI-Duplikate)
#   -Issue5           Run only Issue #5 tests (Variablenwerte)
#   -Integration      Run only integration tests
#   -Performance      Run only performance tests
#   -EdgeCases        Run only edge case tests
#   -Coverage         Run with coverage report
#   -Html             Generate HTML test report
#   -Verbose          Verbose output
#   -Help             Show this help message
#
# Examples:
#   .\tests\run_ui_tests.ps1 -All -Verbose
#   .\tests\run_ui_tests.ps1 -Issue1 -Coverage
#   .\tests\run_ui_tests.ps1 -Performance
#
# Author: OrderPilot-AI Development Team
# Created: 2026-01-28
################################################################################

param(
    [switch]$All = $false,
    [switch]$Issue1 = $false,
    [switch]$Issue5 = $false,
    [switch]$Integration = $false,
    [switch]$Performance = $false,
    [switch]$EdgeCases = $false,
    [switch]$Coverage = $false,
    [switch]$Html = $false,
    [switch]$Verbose = $false,
    [switch]$Help = $false
)

# Colors
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Show help
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

# Default to all tests if no specific option
if (-not ($Issue1 -or $Issue5 -or $Integration -or $Performance -or $EdgeCases)) {
    $All = $true
}

# Print header
Write-ColorOutput "╔══════════════════════════════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║                   CEL Editor UI Tests - Test Runner                     ║" "Cyan"
Write-ColorOutput "║                        Issues #1 and #5                                  ║" "Cyan"
Write-ColorOutput "╚══════════════════════════════════════════════════════════════════════════╝" "Cyan"
Write-Host ""

# Check dependencies
Write-ColorOutput "Checking dependencies..." "Yellow"

try {
    python -c "import pytest" 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-ColorOutput "ERROR: pytest not installed" "Red"
    Write-Host "Install with: pip install pytest pytest-qt"
    exit 1
}

try {
    python -c "import PyQt6" 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-ColorOutput "ERROR: PyQt6 not installed" "Red"
    Write-Host "Install with: pip install PyQt6"
    exit 1
}

Write-ColorOutput "✓ All dependencies installed" "Green"
Write-Host ""

# Build pytest command
$PytestCmd = "pytest tests/ui/test_cel_editor_ui_fixes.py"

# Add verbosity
if ($Verbose) {
    $PytestCmd += " -v --tb=short"
} else {
    $PytestCmd += " -v"
}

# Add coverage
if ($Coverage) {
    $PytestCmd += " --cov=src/ui --cov=src/core/variables --cov-report=term-missing"

    if ($Html) {
        $PytestCmd += " --cov-report=html"
    }
}

# Add HTML report
if ($Html -and -not $Coverage) {
    $PytestCmd += " --html=tests/report_ui_tests.html --self-contained-html"
}

# Function to run test class
function Run-TestClass {
    param(
        [string]$ClassName,
        [string]$Description
    )

    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-ColorOutput "Running: $Description" "Yellow"
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"

    $cmd = "$PytestCmd::$ClassName"
    Invoke-Expression $cmd

    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ $Description PASSED" "Green"
        return $true
    } else {
        Write-ColorOutput "✗ $Description FAILED" "Red"
        return $false
    }
}

# Track failures
$Failures = 0

# Run tests based on options
if ($All) {
    Write-ColorOutput "Running ALL tests..." "Yellow"
    Write-Host ""

    if (-not (Run-TestClass "TestUIStructure" "Issue #1: UI Structure Tests")) { $Failures++ }
    Write-Host ""

    if (-not (Run-TestClass "TestTabFunctionality" "Issue #1: Tab Functionality Tests")) { $Failures++ }
    Write-Host ""

    if (-not (Run-TestClass "TestVariableValues" "Issue #5: Variable Values Tests")) { $Failures++ }
    Write-Host ""

    if (-not (Run-TestClass "TestVariableRefresh" "Issue #5: Variable Refresh Tests")) { $Failures++ }
    Write-Host ""

    if (-not (Run-TestClass "TestIntegration" "Integration Tests")) { $Failures++ }
    Write-Host ""

    if (-not (Run-TestClass "TestEdgeCases" "Edge Case Tests")) { $Failures++ }
    Write-Host ""

    if (-not (Run-TestClass "TestPerformance" "Performance Tests")) { $Failures++ }

} else {
    if ($Issue1) {
        if (-not (Run-TestClass "TestUIStructure" "Issue #1: UI Structure Tests")) { $Failures++ }
        Write-Host ""
        if (-not (Run-TestClass "TestTabFunctionality" "Issue #1: Tab Functionality Tests")) { $Failures++ }
    }

    if ($Issue5) {
        if (-not (Run-TestClass "TestVariableValues" "Issue #5: Variable Values Tests")) { $Failures++ }
        Write-Host ""
        if (-not (Run-TestClass "TestVariableRefresh" "Issue #5: Variable Refresh Tests")) { $Failures++ }
    }

    if ($Integration) {
        if (-not (Run-TestClass "TestIntegration" "Integration Tests")) { $Failures++ }
    }

    if ($EdgeCases) {
        if (-not (Run-TestClass "TestEdgeCases" "Edge Case Tests")) { $Failures++ }
    }

    if ($Performance) {
        if (-not (Run-TestClass "TestPerformance" "Performance Tests")) { $Failures++ }
    }
}

# Print summary
Write-Host ""
Write-ColorOutput "╔══════════════════════════════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║                            TEST SUMMARY                                  ║" "Cyan"
Write-ColorOutput "╚══════════════════════════════════════════════════════════════════════════╝" "Cyan"
Write-Host ""

if ($Failures -eq 0) {
    Write-ColorOutput "✓ ALL TESTS PASSED" "Green"
    Write-Host ""

    if ($Coverage -and $Html) {
        Write-ColorOutput "Coverage report: htmlcov\index.html" "Yellow"
    }

    if ($Html) {
        Write-ColorOutput "HTML report: tests\report_ui_tests.html" "Yellow"
    }

    exit 0
} else {
    Write-ColorOutput "✗ $Failures TEST SUITE(S) FAILED" "Red"
    Write-Host ""
    Write-ColorOutput "Review failed tests above for details." "Yellow"
    exit 1
}
