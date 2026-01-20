# PowerShell script to clear OrderPilot-AI chart states from Windows Registry
# This accesses the Windows Registry where PyQt6 QSettings stores data
#
# Usage:
#   # List all saved charts
#   .\scripts\clear_chart_state.ps1 -List
#
#   # Clear drawings for a specific symbol
#   .\scripts\clear_chart_state.ps1 -Symbol "BTCUSD" -ClearDrawings
#
#   # Clear entire state for a symbol
#   .\scripts\clear_chart_state.ps1 -Symbol "BTCUSD" -ClearAll
#

param(
    [switch]$List,
    [string]$Symbol,
    [switch]$ClearDrawings,
    [switch]$ClearAll,
    [switch]$ClearAllStates,
    [switch]$Confirm
)

$RegistryPath = "HKCU:\Software\OrderPilot\TradingApp"

function Get-ChartStates {
    <#
    .SYNOPSIS
    List all saved chart states from registry
    #>

    if (-not (Test-Path $RegistryPath)) {
        Write-Host "ℹ️  No OrderPilot settings found in registry" -ForegroundColor Yellow
        return @()
    }

    $chartsPath = Join-Path $RegistryPath "charts"

    if (-not (Test-Path $chartsPath)) {
        Write-Host "ℹ️  No saved chart states found" -ForegroundColor Yellow
        return @()
    }

    $charts = @()
    $symbols = Get-ChildItem -Path $chartsPath -ErrorAction SilentlyContinue

    foreach ($symbolKey in $symbols) {
        $symbolPath = $symbolKey.PSPath

        # Get values
        $indicators = Get-ItemProperty -Path $symbolPath -Name "indicators" -ErrorAction SilentlyContinue
        $drawings = Get-ItemProperty -Path $symbolPath -Name "drawings" -ErrorAction SilentlyContinue
        $timeframe = Get-ItemProperty -Path $symbolPath -Name "timeframe" -ErrorAction SilentlyContinue
        $chartType = Get-ItemProperty -Path $symbolPath -Name "chart_type" -ErrorAction SilentlyContinue

        # Parse JSON to count items
        $indicatorCount = 0
        $drawingCount = 0

        if ($indicators.indicators) {
            try {
                $indicatorArray = $indicators.indicators | ConvertFrom-Json
                $indicatorCount = $indicatorArray.Count
            } catch {
                $indicatorCount = 0
            }
        }

        if ($drawings.drawings) {
            try {
                $drawingArray = $drawings.drawings | ConvertFrom-Json
                $drawingCount = $drawingArray.Count
            } catch {
                $drawingCount = 0
            }
        }

        $charts += [PSCustomObject]@{
            Symbol = $symbolKey.PSChildName
            Indicators = $indicatorCount
            Drawings = $drawingCount
            Timeframe = if ($timeframe.timeframe) { $timeframe.timeframe } else { "Unknown" }
            ChartType = if ($chartType.chart_type) { $chartType.chart_type } else { "Unknown" }
            Path = $symbolPath
        }
    }

    return $charts
}

function Show-ChartStates {
    <#
    .SYNOPSIS
    Display all chart states
    #>

    $charts = Get-ChartStates

    if ($charts.Count -eq 0) {
        return
    }

    Write-Host "`n📊 Saved Chart States:" -ForegroundColor Cyan
    Write-Host ("-" * 80) -ForegroundColor Gray

    foreach ($chart in $charts | Sort-Object Symbol) {
        Write-Host "`n🔸 Symbol: $($chart.Symbol)" -ForegroundColor White
        Write-Host "   Timeframe: $($chart.Timeframe)" -ForegroundColor Gray
        Write-Host "   Chart Type: $($chart.ChartType)" -ForegroundColor Gray
        Write-Host "   Indicators: $($chart.Indicators)" -ForegroundColor Gray

        $drawingColor = if ($chart.Drawings -gt 50) { "Red" } else { "Gray" }
        $warning = if ($chart.Drawings -gt 50) { " ⚠️  HIGH!" } else { "" }
        Write-Host "   Drawings/Annotations: $($chart.Drawings)$warning" -ForegroundColor $drawingColor
    }

    Write-Host "`n$("-" * 80)" -ForegroundColor Gray
}

function Clear-Drawings {
    param([string]$SymbolName)

    $symbolPath = Join-Path $RegistryPath "charts\$SymbolName"

    if (-not (Test-Path $symbolPath)) {
        Write-Host "❌ No saved state found for symbol: $SymbolName" -ForegroundColor Red
        Write-Host "`nAvailable symbols:" -ForegroundColor Yellow
        $charts = Get-ChartStates
        foreach ($chart in $charts) {
            Write-Host "  - $($chart.Symbol)" -ForegroundColor Gray
        }
        return $false
    }

    try {
        Set-ItemProperty -Path $symbolPath -Name "drawings" -Value "[]"
        Write-Host "✅ Cleared drawings for $SymbolName" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Error clearing drawings: $_" -ForegroundColor Red
        return $false
    }
}

function Clear-ChartState {
    param([string]$SymbolName)

    $symbolPath = Join-Path $RegistryPath "charts\$SymbolName"

    if (-not (Test-Path $symbolPath)) {
        Write-Host "❌ No saved state found for symbol: $SymbolName" -ForegroundColor Red
        return $false
    }

    try {
        Remove-Item -Path $symbolPath -Recurse -Force
        Write-Host "✅ Cleared all state for $SymbolName" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Error clearing chart state: $_" -ForegroundColor Red
        return $false
    }
}

function Clear-AllStates {
    $chartsPath = Join-Path $RegistryPath "charts"

    if (-not (Test-Path $chartsPath)) {
        Write-Host "ℹ️  No saved chart states found" -ForegroundColor Yellow
        return $true
    }

    try {
        Remove-Item -Path $chartsPath -Recurse -Force
        Write-Host "✅ Cleared all chart states" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Error clearing all states: $_" -ForegroundColor Red
        return $false
    }
}

# Main logic
if ($List) {
    Show-ChartStates
    exit 0
}

if ($ClearDrawings) {
    if (-not $Symbol) {
        Write-Host "❌ -Symbol required for -ClearDrawings" -ForegroundColor Red
        exit 1
    }

    # Show current state
    $charts = Get-ChartStates
    $chart = $charts | Where-Object { $_.Symbol -eq $Symbol }

    if (-not $chart) {
        Write-Host "❌ No saved state found for symbol: $Symbol" -ForegroundColor Red
        Write-Host "`nAvailable symbols:" -ForegroundColor Yellow
        foreach ($c in $charts) {
            Write-Host "  - $($c.Symbol)" -ForegroundColor Gray
        }
        exit 1
    }

    Write-Host "`n📊 Current state for ${Symbol}:" -ForegroundColor Cyan
    Write-Host "   Drawings: $($chart.Drawings)" -ForegroundColor Gray
    Write-Host "   Indicators: $($chart.Indicators)" -ForegroundColor Gray

    if (-not $Confirm) {
        Write-Host "`n⚠️  Add -Confirm to proceed with clearing drawings" -ForegroundColor Yellow
        exit 1
    }

    if (Clear-Drawings -SymbolName $Symbol) {
        Write-Host "`n✅ Successfully cleared $($chart.Drawings) drawings for $Symbol" -ForegroundColor Green
        Write-Host "   (Indicators and other settings preserved)" -ForegroundColor Gray
        exit 0
    } else {
        exit 1
    }
}

if ($ClearAll) {
    if (-not $Symbol) {
        Write-Host "❌ -Symbol required for -ClearAll" -ForegroundColor Red
        exit 1
    }

    if (-not $Confirm) {
        Write-Host "⚠️  Add -Confirm to proceed with clearing entire chart state" -ForegroundColor Yellow
        exit 1
    }

    if (Clear-ChartState -SymbolName $Symbol) {
        exit 0
    } else {
        exit 1
    }
}

if ($ClearAllStates) {
    if (-not $Confirm) {
        Write-Host "⚠️  Add -Confirm to proceed with clearing ALL chart states" -ForegroundColor Yellow
        exit 1
    }

    if (Clear-AllStates) {
        exit 0
    } else {
        exit 1
    }
}

# No action specified
Write-Host @"

OrderPilot-AI Chart State Manager (PowerShell)

Usage:
  .\scripts\clear_chart_state.ps1 -List
  .\scripts\clear_chart_state.ps1 -Symbol BTCUSD -ClearDrawings -Confirm
  .\scripts\clear_chart_state.ps1 -Symbol BTCUSD -ClearAll -Confirm
  .\scripts\clear_chart_state.ps1 -ClearAllStates -Confirm

Options:
  -List              List all saved chart states
  -Symbol <name>     Symbol to operate on
  -ClearDrawings     Clear only drawings/annotations (keep indicators)
  -ClearAll          Clear entire chart state for a symbol
  -ClearAllStates    Clear ALL chart states
  -Confirm           Confirm destructive operations

"@ -ForegroundColor Cyan

exit 0
