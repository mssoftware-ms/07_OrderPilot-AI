@echo off
REM ============================================================
REM Deploy Antigravity Toolkit to all Python Projects
REM Copies .antigravity folder + config files with --force
REM ============================================================

setlocal enabledelayedexpansion

set "SOURCE_DIR=D:\03_Git\02_Python\07_OrderPilot-AI"
set "TARGET_ROOT=D:\03_Git\02_Python"

echo ============================================================
echo Antigravity Toolkit Deployment (FORCE OVERWRITE)
echo ============================================================
echo Source: %SOURCE_DIR%\.antigravity
echo Config: AGENTS.md, CLAUDE.md, GEMINI.md
echo Target: %TARGET_ROOT%\*
echo ============================================================
echo.

REM Check if source exists
if not exist "%SOURCE_DIR%\.antigravity" (
    echo [ERROR] Source folder not found: %SOURCE_DIR%\.antigravity
    pause
    exit /b 1
)

set COUNT=0

REM Loop through first-level directories only
for /d %%D in ("%TARGET_ROOT%\*") do (
    REM Skip the source project itself
    if /i not "%%~nxD"=="07_OrderPilot-AI" (
        echo [DEPLOY] %%~nxD

        REM Force remove existing .antigravity
        if exist "%%D\.antigravity" (
            rmdir /s /q "%%D\.antigravity" 2>nul
        )

        REM Force copy .antigravity folder
        xcopy "%SOURCE_DIR%\.antigravity" "%%D\.antigravity\" /e /i /q /y >nul
        echo         [OK] .antigravity/

        REM Force copy agent config files to project ROOT
        copy /y "%SOURCE_DIR%\AGENTS.md" "%%D\AGENTS.md" >nul 2>&1
        if exist "%%D\AGENTS.md" echo         [OK] AGENTS.md

        copy /y "%SOURCE_DIR%\CLAUDE.md" "%%D\CLAUDE.md" >nul 2>&1
        if exist "%%D\CLAUDE.md" echo         [OK] CLAUDE.md

        copy /y "%SOURCE_DIR%\GEMINI.md" "%%D\GEMINI.md" >nul 2>&1
        if exist "%%D\GEMINI.md" echo         [OK] GEMINI.md

        set /a COUNT+=1
    ) else (
        echo [SKIP] %%~nxD (source project)
    )
)

echo.
echo ============================================================
echo [DONE] Deployed to %COUNT% projects (force overwrite)
echo ============================================================
echo.
echo Files deployed per project:
echo   - .antigravity/ (folder)
echo   - AGENTS.md (Codex CLI)
echo   - CLAUDE.md (Claude Code)
echo   - GEMINI.md (Gemini CLI)
echo.
pause
