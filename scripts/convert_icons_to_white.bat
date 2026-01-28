@echo off
REM ========================================
REM Icon Color Converter - Black to White
REM Requires: ImageMagick installed
REM ========================================

setlocal enabledelayedexpansion

set ICONS_DIR=src\ui\icons

echo ========================================
echo Icon Color Converter - Black to White
echo ========================================
echo.

REM Check if ImageMagick is installed
where magick >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: ImageMagick not found!
    echo.
    echo Please install ImageMagick:
    echo https://imagemagick.org/script/download.php#windows
    echo.
    pause
    exit /b 1
)

echo ImageMagick found. Converting icons...
echo.

REM List of icons to convert
set ICONS=search copy refresh save download chevron_down chevron_up close filter add edit delete import export code play check error warning info

REM Convert each icon
set SUCCESS=0
set FAILED=0

for %%i in (%ICONS%) do (
    set "src=%ICONS_DIR%\%%i_black.png"
    set "dest=%ICONS_DIR%\%%i_white.png"

    if exist "!src!" (
        echo Converting %%i...
        magick convert "!src!" -negate -fuzz 10%% -transparent black "!dest!"

        if exist "!dest!" (
            echo   ✓ Created: %%i_white.png
            set /a SUCCESS+=1
        ) else (
            echo   ✗ Failed: %%i_white.png
            set /a FAILED+=1
        )
    ) else (
        echo   ✗ Source not found: %%i_black.png
        set /a FAILED+=1
    )
)

echo.
echo ========================================
echo Summary:
echo   Success: %SUCCESS%/20
echo   Failed:  %FAILED%/20
echo ========================================
echo.

if %FAILED% EQU 0 (
    echo ✓ All icons converted successfully!
    echo.
    echo Black icons can be deleted if you want:
    echo   del %ICONS_DIR%\*_black.png
) else (
    echo ⚠ Some icons failed to convert.
    echo Check errors above.
)

echo.
pause
