@echo off
setlocal enabledelayedexpansion
title VENV & Requirements: 07_OrderPilot-AI
cd /d "D:\03_Git\02_Python\07_OrderPilot-AI"
echo ================================================
echo  VENV and Requirements Setup
echo  Project: 07_OrderPilot-AI
echo ================================================

echo.
echo Requirements.txt gefunden!
echo.
echo Wie moechten Sie die Abhaengigkeiten installieren?
echo   [1] Virtual Environment erstellen (empfohlen)
echo   [2] Global installieren (System-Python)
echo   [3] Ueberspringen
echo.
set /p choice=Ihre Wahl [1/2/3]: 

if "%choice%"=="2" (
    echo.
    echo Installation in globalem Python...
    "D:\03_Git\02_Python\00_Project_Launcher\.venv\Scripts\python.exe" -m pip install -r requirements.txt
    echo.
    echo Global installation abgeschlossen.
    goto :end
)
if "%choice%"=="3" (
    echo.
    echo Installation uebersprungen.
    goto :end
)
rem Default to venv creation (choice 1 or any other input)

echo.
echo [0/6] .gitignore: venv-Eintraege wurden sichergestellt.
echo      Info: .gitignore bereits mit venv-Einträgen

if not exist ".venv\Scripts\python.exe" (
  echo [1/6] Erstelle virtuelle Umgebung ...
  "D:\03_Git\02_Python\00_Project_Launcher\.venv\Scripts\python.exe" -m venv ".venv"
  if errorlevel 1 goto :error
) else (
  echo [1/6] Virtuelle Umgebung bereits vorhanden.
)

echo [2/6] Aktiviere virtuelle Umgebung ...
call ".venv\Scripts\activate"
if errorlevel 1 goto :error
echo       VIRTUAL_ENV=%VIRTUAL_ENV%
where python
python -V
pip -V

set "VPY=.venv\Scripts\python.exe"
echo [3/6] Aktualisiere pip ...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [4/6] Stelle pipreqs sicher ...
python -m pip show pipreqs >nul 2>&1
if errorlevel 1 (
  python -m pip install pipreqs
  if errorlevel 1 goto :error
) else (
  echo       pipreqs bereits installiert.
)

echo [5/6] Generiere requirements.txt ...
where pipreqs
pipreqs . --force --encoding=utf-8 --ignore .venv,venv,env,.env,__pycache__,.git,.idea,.vscode,build,dist,docs,doc,documentation,01_Documentation,01_documentation,notebooks,examples,tests --savepath "requirements.txt"
if errorlevel 1 (
  echo    UTF-8 fehlgeschlagen, versuche latin-1 ...
  pipreqs . --force --encoding=latin-1 --ignore .venv,venv,env,.env,__pycache__,.git,.idea,.vscode,build,dist,docs,doc,documentation,01_Documentation,01_documentation,notebooks,examples,tests --savepath "requirements.txt"
  if errorlevel 1 goto :error
)

echo [6/6] Installiere requirements in venv ...
python -m pip install -r "requirements.txt"
if errorlevel 1 goto :error

echo.
echo ✅ Fertig.
goto :end

:error
echo.
echo ❌ Fehler aufgetreten. Details siehe oben.
echo Das Fenster bleibt offen. Druecke eine Taste zum Schliessen.
pause >nul
goto :eof

:end
echo Vorgang erfolgreich abgeschlossen.
echo Druecke eine Taste zum Schliessen.
pause >nul
exit /b 0
