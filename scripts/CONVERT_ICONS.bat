@echo off
REM Quick launcher for icon conversion
REM Double-click this file to convert icons on Windows

cd /d "%~dp0\.."
echo.
echo ========================================
echo   Icon Conversion Launcher
echo ========================================
echo.
echo Current directory: %CD%
echo.

REM Try PowerShell script first (auto-detects tools)
if exist "scripts\convert_icons_to_white.ps1" (
    echo Running PowerShell script...
    echo.
    powershell -ExecutionPolicy Bypass -File "scripts\convert_icons_to_white.ps1"
    goto :done
)

REM Fallback to batch script (requires ImageMagick)
if exist "scripts\convert_icons_to_white.bat" (
    echo Running batch script...
    echo.
    call "scripts\convert_icons_to_white.bat"
    goto :done
)

echo ERROR: No conversion scripts found!
echo.

:done
echo.
pause
