# OrderPilot-AI - Windows Installation Guide

## Abhängigkeiten installieren

### Voraussetzungen

- Python 3.9 oder höher
- pip installiert und aktuell

### Standard-Installation

```powershell
# Im Projektverzeichnis
cd D:\03_Git\02_Python\07_OrderPilot-AI

# Alle Abhängigkeiten installieren
pip install -r requirements.txt
```

### Spezifische Probleme & Lösungen

#### Issue #9: Compact Chart Widget

**Problem:** Widget erscheint nicht im Trading-Bot Tab

**Symptom in Logs:**
```
lightweight-charts not installed. Compact chart will not be available.
'CompactChartWidget' object has no attribute '_price_label'
```

**Ursache:**
- Die `lightweight-charts` Library ist nur in WSL `.wsl_venv` installiert
- Windows-Python-Umgebung hat die Library nicht

**Lösung:**
```powershell
# Im Projektverzeichnis in PowerShell oder CMD
pip install lightweight-charts>=2.0
```

**Zusätzliche Abhängigkeiten (werden automatisch installiert):**
- pywebview
- bottle
- proxy_tools

**Nach Installation:**
1. Trading-Bot App neu starten
2. Widget sollte zwischen "BitUnix Trading API" und "Current Position" GroupBoxes erscheinen
3. Chart zeigt live Candlestick-Daten mit Volume Histogram
4. 🔍 Button öffnet vergrößerte Chart-Ansicht

#### Bekannte Probleme

**PyQt6-WebEngine fehlt:**
```powershell
pip install PyQt6-WebEngine>=6.7.0
```

**Pandas-TA Installationsprobleme:**
```powershell
# Falls pip install fehlschlägt:
pip install --upgrade pip setuptools wheel
pip install pandas-ta==0.4.71b0
```

## Virtuelle Umgebung (Empfohlen)

### Neue venv erstellen:
```powershell
# Im Projektverzeichnis
python -m venv venv

# Aktivieren
.\venv\Scripts\Activate.ps1

# Dependencies installieren
pip install -r requirements.txt
```

### Bestehende venv verwenden:
```powershell
# Aktivieren
.\venv\Scripts\Activate.ps1

# Überprüfen
pip list
```

## Entwicklungsumgebung

### WSL vs Windows

**Wichtig:** Das Projekt wird in WSL entwickelt, aber die App läuft unter Windows.

**WSL-Umgebung (.wsl_venv):**
- Für Claude Code, CLI-Tools, Git
- Pfade: `/mnt/d/03_Git/02_Python/07_OrderPilot-API`

**Windows-Umgebung:**
- Für das Ausführen der Trading-Bot App
- Pfade: `D:\03_Git\02_Python\07_OrderPilot-AI`
- **Libraries müssen hier installiert sein!**

### Synchronisation

Nach Installation in WSL:
```bash
# WSL
source .wsl_venv/bin/activate
pip install <package>
```

Auch in Windows installieren:
```powershell
# Windows
pip install <package>
```

## Überprüfung

### Alle Dependencies prüfen:
```powershell
pip check
```

### Spezifische Library testen:
```python
# In Python REPL
>>> from lightweight_charts.widgets import QtChart
>>> print("✓ lightweight-charts installed")
```

### Version prüfen:
```powershell
pip show lightweight-charts
```

## Support

Bei Problemen:
1. Logs prüfen in `logs/` Verzeichnis
2. Issue in `/issues` Ordner erstellen
3. Vollständige Fehlermeldung und `pip list` Output anhängen
