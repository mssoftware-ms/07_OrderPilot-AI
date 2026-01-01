@echo off
REM OrderPilot-AI - Windows Dependency Installation
echo ========================================
echo OrderPilot-AI Dependency Installation
echo ========================================
echo.

REM Activate venv
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Could not activate .venv
    echo Please create it first with: python -m venv .venv
    exit /b 1
)

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip wheel

REM Install core dependencies
echo.
echo Installing core dependencies...
pip install pydantic sqlalchemy blinker cryptography aiohttp pandas numpy

REM Install Qt and GUI dependencies  
echo.
echo Installing Qt and GUI dependencies...
pip install PyQt6 qasync matplotlib plotly

REM Install AI and web dependencies
echo.
echo Installing AI and web dependencies...
pip install openai requests beautifulsoup4 lxml flask flask-cors

REM Install testing dependencies
echo.
echo Installing testing dependencies...
pip install pytest pytest-asyncio pytest-cov pytest-qt

REM Verify installation
echo.
echo ========================================
echo Verifying installation...
echo ========================================
python -c "import aiohttp; import PyQt6; import pandas; print('✓ All core packages imported successfully')"

if %ERRORLEVEL% EQ 0 (
    echo.
    echo ========================================
    echo SUCCESS! All dependencies installed
    echo ========================================
    echo.
    echo You can now run:
    echo   python start_orderpilot.py --check
    echo   python start_orderpilot.py --mock
) else (
    echo.
    echo ERROR: Some packages failed to import
    exit /b 1
)

echo.
pause
