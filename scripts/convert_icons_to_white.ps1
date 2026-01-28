# Icon Conversion Script - Black to White with Transparent Background
# PowerShell script for Windows (no external dependencies required if .NET is available)
# Author: OrderPilot-AI Development Team
# Created: 2026-01-28

$ErrorActionPreference = "Continue"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Icon Color Converter - Black to White" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$IconsDir = "src\ui\icons"

# Check if directory exists
if (-not (Test-Path $IconsDir)) {
    Write-Host "ERROR: Directory not found: $IconsDir" -ForegroundColor Red
    Write-Host "Please run from project root." -ForegroundColor Red
    exit 1
}

# List of icons to convert
$Icons = @(
    "search", "copy", "refresh", "save", "download",
    "chevron_down", "chevron_up", "close", "filter",
    "add", "edit", "delete", "import", "export",
    "code", "play", "check", "error", "warning", "info"
)

$Success = 0
$Failed = 0
$Skipped = 0

Write-Host "Checking for conversion tools..." -ForegroundColor Yellow
Write-Host ""

# Check for ImageMagick
$MagickCmd = $null
foreach ($cmd in @("magick", "convert")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $MagickCmd = $cmd
        break
    }
}

# Check for Python with Pillow
$PythonPillow = $false
try {
    $pythonCheck = python -c "import PIL; print('OK')" 2>$null
    if ($pythonCheck -eq "OK") {
        $PythonPillow = $true
    }
} catch {}

if ($MagickCmd) {
    Write-Host "Found ImageMagick: $MagickCmd" -ForegroundColor Green
    $ConversionMethod = "imagemagick"
} elseif ($PythonPillow) {
    Write-Host "Found Python with Pillow" -ForegroundColor Green
    $ConversionMethod = "python"
} else {
    Write-Host "ERROR: No conversion tool found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install one of the following:" -ForegroundColor Yellow
    Write-Host "  1. ImageMagick: https://imagemagick.org/script/download.php#windows" -ForegroundColor Yellow
    Write-Host "  2. Python with Pillow: pip install Pillow" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Converting icons using: $ConversionMethod" -ForegroundColor Cyan
Write-Host ""

foreach ($icon in $Icons) {
    $SourceFile = Join-Path $IconsDir "${icon}_black.png"
    $DestFile = Join-Path $IconsDir "${icon}_white.png"

    if (-not (Test-Path $SourceFile)) {
        Write-Host "Source not found: ${icon}_black.png" -ForegroundColor Red
        $Failed++
        continue
    }

    if (Test-Path $DestFile) {
        Write-Host "Skipping (exists): ${icon}_white.png" -ForegroundColor Gray
        $Skipped++
        continue
    }

    Write-Host "Converting: $icon..." -NoNewline

    try {
        if ($ConversionMethod -eq "imagemagick") {
            # ImageMagick conversion
            & $MagickCmd convert $SourceFile -negate -fuzz 10% -transparent black $DestFile 2>$null
        } elseif ($ConversionMethod -eq "python") {
            # Python + Pillow conversion
            $pythonCode = @"
from PIL import Image
img = Image.open('$SourceFile').convert('RGBA')
data = img.getdata()
new_data = []
for item in data:
    r, g, b, a = item
    avg = (r + g + b) / 3
    if avg < 128:
        new_data.append((255, 255, 255, a))
    else:
        new_data.append((255, 255, 255, 0))
img.putdata(new_data)
img.save('$DestFile', 'PNG')
"@
            python -c $pythonCode 2>$null
        }

        if (Test-Path $DestFile) {
            Write-Host " Done" -ForegroundColor Green
            $Success++
        } else {
            Write-Host " Failed" -ForegroundColor Red
            $Failed++
        }
    } catch {
        Write-Host " Failed: $_" -ForegroundColor Red
        $Failed++
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Success: $Success/20" -ForegroundColor Green
Write-Host "  Failed:  $Failed/20" -ForegroundColor $(if ($Failed -gt 0) { "Red" } else { "Green" })
Write-Host "  Skipped: $Skipped/20" -ForegroundColor Gray
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if ($Failed -eq 0 -and $Success -gt 0) {
    Write-Host "All icons converted successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can delete black icons if you want:" -ForegroundColor Yellow
    Write-Host "  Remove-Item $IconsDir\*_black.png" -ForegroundColor Yellow
} elseif ($Failed -gt 0) {
    Write-Host "Some icons failed to convert." -ForegroundColor Red
    Write-Host "Check errors above." -ForegroundColor Red
} elseif ($Skipped -eq 20) {
    Write-Host "All icons already converted (skipped all)." -ForegroundColor Green
}

Write-Host ""
