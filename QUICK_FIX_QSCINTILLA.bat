@echo off
echo ========================================
echo QScintilla Quick Fix for Windows
echo ========================================
echo.

echo Checking current directory...
cd /d D:\03_Git\02_Python\07_OrderPilot-AI
echo Current directory: %CD%
echo.

echo Activating virtual environment...
if exist .venv\Scripts\Activate.ps1 (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo WARNING: No virtual environment found at .venv
    echo Will install in system Python instead
)
echo.

echo Installing PyQt6-QScintilla...
python -m pip install PyQt6-QScintilla
echo.

echo Verifying installation...
python -c "from PyQt6.Qsci import QsciScintilla, QsciAPIs; print('✅ QScintilla installed successfully')"
if %errorlevel% neq 0 (
    echo ❌ Installation failed!
    echo.
    echo Try manual installation:
    echo 1. Open PowerShell as Administrator
    echo 2. Run: python -m pip install PyQt6-QScintilla
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✅ Installation successful!
echo ========================================
echo.
echo You can now run: python main.py
echo.
pause
