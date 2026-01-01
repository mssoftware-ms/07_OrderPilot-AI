# 🚀 OrderPilot-AI Startup Guide

## Quick Start

### Windows
```bash
# Einfachster Start (Doppelklick oder Kommandozeile)
START.bat
```

### Linux/Mac
```bash
# Ausführbar machen (nur einmal nötig)
chmod +x start.sh

# Starten
./start.sh
```

### Python Direct
```bash
# Mit aktiviertem Virtual Environment
python start_orderpilot.py

# Oder die minimale Version
python run_app.py
```

---

## 📋 Verfügbare Startdateien

| Datei | Beschreibung | Features |
|-------|-------------|----------|
| **START.bat** | Windows Batch-Datei | Auto-Installation, Venv-Management |
| **start.sh** | Linux/Mac Shell-Script | Auto-Installation, Display-Check |
| **start_orderpilot.py** | Erweiterter Python-Launcher | CLI-Argumente, Logging, Checks |
| **run_app.py** | Minimaler Python-Launcher | Einfacher Start ohne Extras |

---

## ⚙️ Startoptionen (start_orderpilot.py)

### Grundlegende Optionen

```bash
# Standard-Start (Paper Trading)
python start_orderpilot.py

# Production-Modus
python start_orderpilot.py --env production

# Mit speziellem Profil
python start_orderpilot.py --profile aggressive

# Mock-Broker für Tests
python start_orderpilot.py --mock

# Nur Dependency-Check
python start_orderpilot.py --check
```

### Erweiterte Optionen

```bash
# Mit Debug-Logging
python start_orderpilot.py --log-level DEBUG

# Ohne Banner
python start_orderpilot.py --no-banner

# Kombinierte Optionen
python start_orderpilot.py --env paper --mock --log-level INFO
```

### Verfügbare Umgebungen

| Environment | Beschreibung | Verwendung |
|-------------|--------------|------------|
| **development** | Entwicklungsmodus | Debugging, Tests |
| **paper** | Paper Trading (Standard) | Simulation mit Fake-Geld |
| **production** | Live Trading | Echtes Geld - VORSICHT! |

---

## 🔧 Erste Schritte

### 1. Installation prüfen
```bash
python start_orderpilot.py --check
```

### 2. Paper Trading starten
```bash
python start_orderpilot.py --env paper --mock
```

### 3. Logs überprüfen
```bash
# Logs befinden sich im logs/ Verzeichnis
ls -la logs/
```

---

## 🗂️ Verzeichnisstruktur nach dem Start

```
OrderPilot-AI/
├── data/               # Datenbank und Datendateien
│   └── orderpilot.db  # SQLite Datenbank
├── logs/              # Log-Dateien
│   └── orderpilot_*.log
├── config/            # Konfigurationsdateien
│   ├── paper.yaml    # Paper Trading Profil
│   └── *.yaml        # Weitere Profile
└── venv/             # Python Virtual Environment
```

---

## 🚨 Troubleshooting

### Problem: "No module named PyQt6"
**Lösung:**
```bash
pip install -r requirements.txt
```

### Problem: "No display detected"
**Lösung für WSL/SSH:**
```bash
# X11 Forwarding aktivieren
export DISPLAY=:0

# Oder VcXsrv/Xming auf Windows starten
```

### Problem: "Database locked"
**Lösung:**
```bash
# Alte Prozesse beenden
pkill -f orderpilot
# oder
taskkill /F /IM python.exe
```

### Problem: "Permission denied"
**Lösung für Linux/Mac:**
```bash
chmod +x start.sh
chmod +x start_orderpilot.py
```

---

## 📱 GUI-Features beim Start

Nach erfolgreichem Start öffnet sich das Hauptfenster mit:

1. **Dashboard Tab** - Portfolio-Übersicht
2. **Positions Tab** - Aktuelle Positionen
3. **Orders Tab** - Order-Management
4. **Chart Tab** - Marktdaten-Visualisierung
5. **Alerts Tab** - Trading-Benachrichtigungen

### Menüleiste
- **File** → Settings, Import/Export, Exit
- **Trading** → Place Order, View Positions
- **Analysis** → Backtest, Strategy Builder
- **View** → Theme Toggle (Dark/Light)
- **Help** → Documentation, About

---

## 🔐 Sicherheitshinweise

⚠️ **WICHTIG für Production-Modus:**
1. Testen Sie IMMER zuerst im Paper-Modus
2. Setzen Sie Stop-Loss und Position-Limits
3. Aktivieren Sie den Kill-Switch
4. Überwachen Sie die Logs kontinuierlich
5. Starten Sie mit kleinen Beträgen

---

## 📊 Performance-Empfehlungen

### Minimale Systemanforderungen
- **CPU:** 2 Cores
- **RAM:** 4 GB
- **Disk:** 1 GB freier Speicher
- **Python:** 3.10+

### Empfohlene Systemanforderungen
- **CPU:** 4+ Cores
- **RAM:** 8+ GB
- **Disk:** 10+ GB für historische Daten
- **Python:** 3.11+
- **Display:** 1920x1080 oder höher

---

## 🆘 Support

Bei Problemen:
1. Prüfen Sie die Logs in `logs/orderpilot_*.log`
2. Führen Sie `python start_orderpilot.py --check` aus
3. Konsultieren Sie die Dokumentation in `docs/`
4. Erstellen Sie ein Issue im GitHub-Repository

---

## 🎯 Nächste Schritte

1. **Konfiguration anpassen:** Editieren Sie `config/paper.yaml`
2. **API-Keys einrichten:** Für Broker und OpenAI
3. **Strategien konfigurieren:** Im Strategy-Tab
4. **Backtesting durchführen:** Testen Sie Ihre Strategien
5. **Paper Trading:** Üben Sie ohne Risiko

---

*Happy Trading! 📈*