@echo off
REM ============================================================
REM Generate Repomix Context File
REM Packages entire codebase into AI-friendly format
REM ============================================================

echo ============================================================
echo Repomix Context Generation
echo ============================================================

REM Check if repomix is installed
where repomix >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] repomix not found. Installing...
    npm install -g repomix
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install repomix. Please run: npm install -g repomix
        pause
        exit /b 1
    )
)

REM Generate context file
echo [RUN] Generating codebase context...

repomix ^
    --ignore "**/*.json" ^
    --ignore "**/*.pyc" ^
    --ignore "**/__pycache__/**" ^
    --ignore "**/logs/**" ^
    --ignore "**/node_modules/**" ^
    --ignore "**/.venv/**" ^
    --ignore "**/dist/**" ^
    --ignore "**/build/**" ^
    --ignore "**/*.egg-info/**" ^
    --ignore "**/03_JSON/**" ^
    --ignore "**/docs/alpaca/**" ^
    --output ".antigravity/context/codebase-context.txt"

if %ERRORLEVEL% EQU 0 (
    echo [OK] Context file generated: .antigravity/context/codebase-context.txt
    for %%A in (".antigravity/context/codebase-context.txt") do echo [INFO] Size: %%~zA bytes
) else (
    echo [FAIL] repomix failed. Check output above.
)

echo ============================================================
pause
