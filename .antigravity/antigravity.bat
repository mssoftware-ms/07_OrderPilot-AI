@echo off
REM ============================================================
REM Antigravity Control Center v2.0 - Main Menu
REM Executes scripts via WSL2 with .wsl_venv
REM ============================================================

:MENU
cls
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║         🚀 ANTIGRAVITY CONTROL CENTER v2.0 🚀            ║
echo  ║              (WSL2 + .wsl_venv Mode)                     ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║                                                          ║
echo  ║  === WORKFLOW (in dieser Reihenfolge) ===                ║
echo  ║                                                          ║
echo  ║  [C] Generate AI Context      (rules + ai_docs + code)   ║
echo  ║  [M] Generate Structure Map   (AST signatures only)      ║
echo  ║  [R] Generate Repomix Context (full codebase dump)       ║
echo  ║  [V] Run AI Verify            (lint + type + test)       ║
echo  ║                                                          ║
echo  ║  === REFERENZ ===                                        ║
echo  ║                                                          ║
echo  ║  [1] View Rules               (Das Grundgesetz)          ║
echo  ║  [2] List Agents              (available agents)         ║
echo  ║  [3] Open AI Docs             (architecture etc.)        ║
echo  ║                                                          ║
echo  ║  === TEMPLATES ===                                       ║
echo  ║                                                          ║
echo  ║  [4] Bug Report Template      (structured report)        ║
echo  ║  [5] CRISP Prompt Template    (better prompts)           ║
echo  ║  [6] UI Inspector Setup       (F12 for PyQt)             ║
echo  ║                                                          ║
echo  ║  === ADMIN ===                                           ║
echo  ║                                                          ║
echo  ║  [D] Deploy to all Projects   (copy .antigravity)        ║
echo  ║  [S] WSL2 Setup               (install tools)            ║
echo  ║  [0] Exit                                                ║
echo  ║                                                          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set /p CHOICE="Select option: "

if /i "%CHOICE%"=="C" goto AICONTEXT
if /i "%CHOICE%"=="M" goto STRUCTUREMAP
if /i "%CHOICE%"=="R" goto REPOMIX
if /i "%CHOICE%"=="V" goto VERIFY
if "%CHOICE%"=="1" goto RULES
if "%CHOICE%"=="2" goto AGENTS
if "%CHOICE%"=="3" goto AIDOCS
if "%CHOICE%"=="4" goto BUGREPORT
if "%CHOICE%"=="5" goto CRISP
if "%CHOICE%"=="6" goto UIINSPECTOR
if /i "%CHOICE%"=="D" goto DEPLOY
if /i "%CHOICE%"=="S" goto WSLSETUP
if "%CHOICE%"=="0" goto EXIT

echo Invalid option. Press any key...
pause >nul
goto MENU

:AICONTEXT
cls
echo ============================================================
echo GENERATE AI CONTEXT (via WSL2)
echo ============================================================
echo.
echo This generates a unified AI context packet containing:
echo   - Rules (Das Grundgesetz)
echo   - ai_docs/ content (architecture, naming, pitfalls)
echo   - Code structure (AST-based signatures)
echo.
echo Output: .antigravity/context/ai-context.md
echo.
cd /d "%~dp0.."
wsl bash -c "cd \"$(wslpath '%CD%')\" && source .wsl_venv/bin/activate 2>/dev/null; python .antigravity/scripts/context.py"
echo.
echo ============================================================
echo Copy the content of ai-context.md to your AI chat.
echo ============================================================
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:STRUCTUREMAP
cls
echo ============================================================
echo GENERATE STRUCTURE MAP (via WSL2)
echo ============================================================
echo.
echo This generates a lightweight code structure containing:
echo   - Class names and inheritance
echo   - Method signatures (no code bodies)
echo   - First-line docstrings
echo.
echo Output: .antigravity/context/structure.md
echo Token-efficient: ~3k tokens vs ~50k for full repomix
echo.
cd /d "%~dp0.."
wsl bash -c "cd \"$(wslpath '%CD%')\" && source .wsl_venv/bin/activate 2>/dev/null; python .antigravity/scripts/context.py --structure-only"
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:REPOMIX
cls
echo ============================================================
echo GENERATE REPOMIX CONTEXT (via WSL2)
echo ============================================================
echo.
echo This generates a FULL codebase dump (50k+ tokens).
echo Use for deep dives or initial onboarding.
echo.
echo Output: .antigravity/context/codebase-context.txt
echo.
cd /d "%~dp0.."
wsl bash -c "cd \"$(wslpath '%CD%')\" && source .wsl_venv/bin/activate 2>/dev/null; bash .antigravity/scripts/generate-context.sh"
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:VERIFY
cls
echo ============================================================
echo AI VERIFY (via WSL2 + .wsl_venv)
echo ============================================================
echo.
echo Running: flake8 (lint) + mypy (types) + pytest (tests)
echo.
cd /d "%~dp0.."
wsl bash -c "cd \"$(wslpath '%CD%')\" && source .wsl_venv/bin/activate && python .antigravity/scripts/ai-verify.py"
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:RULES
cls
echo ============================================================
echo DAS GRUNDGESETZ (Rules)
echo ============================================================
echo.
type "%~dp0rules"
echo.
echo ============================================================
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:AGENTS
cls
echo ============================================================
echo AVAILABLE AGENTS
echo ============================================================
echo.
echo Location: .antigravity\agents\
echo.
for %%F in ("%~dp0agents\*.md") do (
    echo   [*] %%~nF
)
echo.
echo Usage: Reference agent in your prompt, e.g.
echo   "Acting as the qa-expert agent, verify this change..."
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:AIDOCS
cls
echo ============================================================
echo OPENING AI DOCS FOLDER
echo ============================================================
cd /d "%~dp0.."
if exist "ai_docs" (
    start explorer "ai_docs"
    echo Opened: ai_docs\
) else (
    echo [WARN] ai_docs folder not found!
    echo Creating ai_docs folder...
    mkdir ai_docs
    echo Created. Add your architecture docs here.
)
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:BUGREPORT
cls
echo ============================================================
echo BUG REPORT TEMPLATE
echo ============================================================
if exist "%~dp0templates\bug-report.md" (
    start notepad "%~dp0templates\bug-report.md"
    echo Opened in Notepad. Copy content for your report.
) else (
    echo [ERROR] Template not found!
)
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:CRISP
cls
echo ============================================================
echo CRISP PROMPT TEMPLATE
echo ============================================================
if exist "%~dp0templates\crisp-prompt.md" (
    start notepad "%~dp0templates\crisp-prompt.md"
    echo Opened in Notepad. Use for structured prompts.
) else (
    echo [ERROR] Template not found!
)
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:UIINSPECTOR
cls
echo ============================================================
echo UI INSPECTOR SETUP (PyQt)
echo ============================================================
echo.
echo Template files location:
echo   .antigravity\templates\pyqt\ui_inspector.py
echo   .antigravity\templates\pyqt\__init__.py
echo.
echo Setup guide:
echo   .antigravity\guides\ui-inspector-setup.md
echo.
if exist "%~dp0guides\ui-inspector-setup.md" (
    echo Opening guide in Notepad...
    start notepad "%~dp0guides\ui-inspector-setup.md"
) else (
    echo [ERROR] Guide not found!
)
echo.
echo Quick Steps:
echo   1. Copy templates\pyqt\* to src\ui\debug\
echo   2. Import UIInspectorMixin in your MainWindow
echo   3. Call self.setup_ui_inspector() in __init__
echo   4. Press F12 to activate
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:DEPLOY
cls
echo ============================================================
echo DEPLOY TO ALL PROJECTS (Windows)
echo ============================================================
call "%~dp0deploy-to-projects.bat"
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:WSLSETUP
cls
echo ============================================================
echo WSL2 SETUP (Installing tools in .wsl_venv)
echo ============================================================
cd /d "%~dp0.."
wsl bash -c "cd \"$(wslpath '%CD%')\" && bash .antigravity/scripts/setup-wsl.sh"
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:EXIT
cls
echo.
echo  Goodbye! Remember the workflow:
echo.
echo  1. [C] Generate AI Context  - for daily work
echo  2. [M] Structure Map        - lightweight overview
echo  3. [R] Repomix              - full dump (deep dives)
echo  4. [V] AI Verify            - before merge
echo.
echo  F12 in your app for UI Inspector (PyQt)
echo.
exit /b 0
