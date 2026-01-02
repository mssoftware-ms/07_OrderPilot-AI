@echo off
REM ========================================
REM  OrderPilot-AI Trading Application
REM  Windows Startup Script
REM ========================================

echo.
echo ===================================================
echo    OrderPilot-AI Trading Application Launcher
echo ===================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
    echo.
)

REM Start the application
echo Starting OrderPilot-AI...
echo.
REM Launch minimized without keeping this console open
start "" /min pythonw start_orderpilot.py %*
exit /b
