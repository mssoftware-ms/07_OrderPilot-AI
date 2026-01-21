# QScintilla Installation für Windows

## ⚠️ KRITISCHES PROBLEM

Die Anwendung läuft unter **Windows**, aber `PyQt6-QScintilla` fehlt in der Windows-Python-Umgebung.

**Fehler:**
```
ModuleNotFoundError: No module named 'PyQt6.Qsci'
```

---

## ✅ LÖSUNG (Windows PowerShell/CMD)

### Option 1: Mit aktivierter Virtual Environment

```powershell
# 1. Navigiere zum Projekt
cd D:\03_Git\02_Python\07_OrderPilot-AI

# 2. Aktiviere Virtual Environment
.venv\Scripts\Activate.ps1

# 3. Installiere QScintilla
pip install PyQt6-QScintilla

# 4. Verifiziere Installation
python -c "from PyQt6.Qsci import QsciScintilla; print('✅ QScintilla installed')"

# 5. Starte Anwendung neu
python main.py
```

### Option 2: Direkt in System-Python (falls keine venv)

```powershell
# 1. Finde Python-Installation
where python
# Beispiel Output: C:\Python312\python.exe

# 2. Installiere mit vollem Pfad
C:\Python312\python.exe -m pip install PyQt6-QScintilla

# 3. Verifiziere
C:\Python312\python.exe -c "from PyQt6.Qsci import QsciScintilla; print('✅ QScintilla installed')"
```

---

## 🔍 Diagnoseschritte

### 1. Prüfe welches Python verwendet wird:

```powershell
# In PowerShell/CMD (NICHT WSL)
where python
python --version
pip list | findstr PyQt6
```

**Erwartetes Ergebnis:**
```
Python 3.12.x (oder 3.11.x)
PyQt6               6.x.x
PyQt6-QScintilla    FEHLT oder veraltet
```

### 2. Prüfe Virtual Environment:

```powershell
# Ist eine venv aktiv?
$env:VIRTUAL_ENV

# Wenn leer, keine venv aktiv
# Wenn Pfad sichtbar, venv ist aktiv
```

---

## 📦 Vollständige Paketliste (Windows)

Nach erfolgreicher Installation sollte `pip list` zeigen:

```
Package              Version
-------------------- -------
PyQt6                6.10.0 (or higher)
PyQt6-Qt6            6.10.1 (or higher)
PyQt6-QScintilla     2.14.1 (or higher)
PyQt6-sip            13.10.3 (or higher)
openai               1.62.0 (or higher)
```

---

## ⚡ SCHNELL-FIX (Copy-Paste)

```powershell
# Navigiere zum Projekt und installiere (Methode 1 - mit venv)
cd D:\03_Git\02_Python\07_OrderPilot-AI
.venv\Scripts\Activate.ps1
pip install PyQt6-QScintilla
python main.py
```

ODER (wenn keine venv):

```powershell
# Direkt installieren (Methode 2 - ohne venv)
python -m pip install PyQt6-QScintilla
cd D:\03_Git\02_Python\07_OrderPilot-AI
python main.py
```

---

## 🐛 Troubleshooting

### Problem 1: "pip: command not found"

**Lösung:**
```powershell
# Verwende python -m pip
python -m pip install PyQt6-QScintilla
```

### Problem 2: "Permission denied"

**Lösung:**
```powershell
# Als Administrator ausführen (PowerShell → Rechtsklick → Als Admin ausführen)
# ODER mit --user Flag
pip install --user PyQt6-QScintilla
```

### Problem 3: "Could not find a version that satisfies the requirement"

**Lösung:**
```powershell
# Update pip zuerst
python -m pip install --upgrade pip

# Dann QScintilla
pip install PyQt6-QScintilla
```

### Problem 4: Mehrere Python-Installationen

**Symptom:**
- QScintilla in WSL installiert, aber Windows nutzt andere Python-Installation

**Lösung:**
```powershell
# 1. Prüfe ALLE Python-Installationen
where python

# Beispiel Output:
# C:\Python312\python.exe        <- System Python
# C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe  <- User Python
# D:\03_Git\02_Python\07_OrderPilot-AI\.venv\Scripts\python.exe     <- venv

# 2. Installiere in JEDE Installation die du nutzen willst
C:\Python312\python.exe -m pip install PyQt6-QScintilla

# 3. Stelle sicher, dass main.py die richtige verwendet
# Option A: Aktiviere venv BEVOR du main.py startest
.venv\Scripts\Activate.ps1
python main.py

# Option B: Nutze vollen Pfad
C:\Python312\python.exe main.py
```

---

## ✅ Erfolgsüberprüfung

Nach Installation sollte dies funktionieren:

```powershell
# Test 1: Import
python -c "from PyQt6.Qsci import QsciScintilla, QsciAPIs; print('✅ All imports successful')"

# Test 2: CEL Editor
python -c "import sys; sys.path.insert(0, 'src'); from ui.widgets.cel_editor_widget import CelEditorWidget; print('✅ CEL Editor import successful')"

# Test 3: Starte Anwendung
python main.py
# → Klicke "Strategy Concept" Button
# → Sollte KEINE ModuleNotFoundError mehr geben
```

---

## 📝 Nach erfolgreicher Installation

1. Starte `main.py`
2. Klicke auf **"Strategy Concept"** Button (Toolbar)
3. Gehe zu **Tab 2: Pattern Integration**
4. Verifiziere sichtbar:
   - ✅ CEL Editor mit Syntax Highlighting
   - ✅ Function Palette rechts
   - ✅ Workflow Selector (Entry/Exit/Before Exit/Update Stop)
   - ✅ Toolbar mit Buttons: 🤖 Generate, ✓ Validate, 🔧 Format, 🗑️ Clear

---

## 🔄 WSL vs Windows - Wichtiger Hinweis

**Problem:**
- Code-Entwicklung in WSL (Claude Code CLI)
- Anwendung läuft unter Windows
- Separate Python-Umgebungen!

**Lösung:**
```bash
# In WSL (für Code-Entwicklung):
pip install PyQt6-QScintilla

# In Windows PowerShell (für Anwendung):
pip install PyQt6-QScintilla
```

**Beide müssen installiert werden!**

---

## 🎯 Nächste Schritte nach Installation

Folge der Test-Anleitung:
```
docs/testing/CEL_Integration_Test_Guide.md
```

Test-Szenarien:
1. ✅ Component Initialization
2. ✅ Pattern Selection
3. ✅ CEL Editor Features
4. ✅ Function Palette
5. ✅ AI Code Generation (OpenAI GPT-5.2)
6. ✅ JSON Export

---

**Support:**
Bei weiteren Problemen, Logs prüfen oder GitHub Issue erstellen.
