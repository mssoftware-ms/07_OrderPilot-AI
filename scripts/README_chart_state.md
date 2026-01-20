# Chart State Management Tools

Diese Tools helfen beim Verwalten und Zurücksetzen von gespeicherten Chart-Zuständen in OrderPilot-AI.

## Problem

Wenn ein Chart-Fenster geschlossen wird, speichert OrderPilot-AI den kompletten Zustand (Indikatoren, Zeichnungen, Zoom, etc.) in QSettings. Wenn zu viele Zeichnungen/Annotationen (z.B. 200+) gespeichert wurden, können diese nicht mehr gelöscht werden und der Chart wird beim Öffnen langsam oder unbrauchbar.

## Lösung

Es gibt zwei Skripte, um gespeicherte Chart-Zustände zu verwalten:

### 1. PowerShell-Skript (empfohlen für Windows)

**Verwendung auf Windows:**

```powershell
# 1. PowerShell als Administrator öffnen (optional, meist nicht nötig)

# 2. Ins Projektverzeichnis wechseln
cd D:\03_Git\02_Python\07_OrderPilot-AI

# 3. Alle gespeicherten Charts auflisten
.\scripts\clear_chart_state.ps1 -List

# 4. Nur Zeichnungen für ein Symbol löschen (Indikatoren bleiben erhalten)
.\scripts\clear_chart_state.ps1 -Symbol "BTCUSD" -ClearDrawings -Confirm

# 5. Kompletten Chart-Zustand für ein Symbol löschen
.\scripts\clear_chart_state.ps1 -Symbol "BTCUSD" -ClearAll -Confirm

# 6. ALLE Chart-Zustände löschen (VORSICHT!)
.\scripts\clear_chart_state.ps1 -ClearAllStates -Confirm
```

### 2. Python-Skript (für WSL/Linux oder Windows-Python)

**Verwendung auf Windows (mit Python):**

```bash
# 1. Cmd oder PowerShell öffnen
# 2. Ins Projektverzeichnis wechseln
cd D:\03_Git\02_Python\07_OrderPilot-AI

# 3. Virtual Environment aktivieren (falls vorhanden)
.venv\Scripts\activate

# 4. Alle gespeicherten Charts auflisten
python scripts\clear_chart_state.py --list

# 5. Details zu Zeichnungen anzeigen
python scripts\clear_chart_state.py --symbol BTCUSD --show-drawings

# 6. Nur Zeichnungen löschen
python scripts\clear_chart_state.py --symbol BTCUSD --clear-drawings --confirm

# 7. Kompletten Chart-Zustand löschen
python scripts\clear_chart_state.py --symbol BTCUSD --clear-all --confirm
```

## Wo werden die Daten gespeichert?

PyQt6 QSettings speichert Daten platform-spezifisch:

- **Windows**: Windows Registry unter `HKEY_CURRENT_USER\Software\OrderPilot\TradingApp`
- **Linux/WSL**: `~/.config/OrderPilot/TradingApp.conf`

## Workflow-Empfehlung

### Szenario: Chart mit 200+ Annotationen zurücksetzen

1. **Identifizieren welches Symbol betroffen ist:**
   ```powershell
   .\scripts\clear_chart_state.ps1 -List
   ```
   Ausgabe zeigt alle Symbole mit Anzahl der Zeichnungen:
   ```
   📊 Saved Chart States:
   --------------------------------------------------------------------------------

   🔸 Symbol: BTCUSD
      Timeframe: 1H
      Chart Type: tradingview
      Indicators: 5
      Drawings/Annotations: 237 ⚠️  HIGH!
   ```

2. **Nur Zeichnungen löschen (empfohlen):**
   ```powershell
   .\scripts\clear_chart_state.ps1 -Symbol "BTCUSD" -ClearDrawings -Confirm
   ```
   Dies löscht nur die 237 Zeichnungen, aber behält Indikatoren, Timeframe und andere Einstellungen.

3. **App neu starten:**
   Starte OrderPilot-AI neu. Der Chart für BTCUSD sollte jetzt ohne Zeichnungen geladen werden.

### Alternative: Kompletten Zustand löschen

Falls du ALLE Einstellungen für einen Chart zurücksetzen willst (auch Indikatoren, Zoom, etc.):

```powershell
.\scripts\clear_chart_state.ps1 -Symbol "BTCUSD" -ClearAll -Confirm
```

## Troubleshooting

### "No saved chart states found"

**Ursachen:**
- OrderPilot-AI wurde noch nie gestartet
- Charts wurden noch nie geschlossen (State wird nur beim Schließen gespeichert)
- Falsches Benutzer-Profil

**Lösung:**
1. Prüfe ob OrderPilot-AI schon mal auf diesem Windows-Benutzer lief
2. Öffne Registry-Editor (`regedit`) und suche nach `HKEY_CURRENT_USER\Software\OrderPilot`

### Symbol wird nicht gefunden

Das Symbol in QSettings ist "sanitized" (bereinigt):
- `/` wird zu `_`
- `:` wird zu `_`
- `*` wird zu `_`

Beispiele:
- `BTC/USD` → `BTC_USD`
- `ES:NASDAQ` → `ES_NASDAQ`

Verwende das bereinigte Symbol in den Befehlen.

### PowerShell Execution Policy Error

Wenn PowerShell das Skript nicht ausführen lässt:

```powershell
# Execution Policy für diese Session erlauben
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

Dann das Skript erneut ausführen.

## Integration in OrderPilot-AI

### Menü-Integration (zukünftig)

Diese Funktionalität könnte in die OrderPilot-AI GUI integriert werden:

**Vorschlag für Chart-Menü:**
```
Chart-Menü
├── Alle Zeichnungen löschen (aktuell)        ← löscht nur aktuelle, nicht gespeicherte
├── Gespeicherte Zeichnungen löschen (NEU)    ← löscht aus QSettings
└── Chart-Zustand zurücksetzen (NEU)          ← kompletter Reset
```

### Code-Integration

Die Funktionalität ist bereits in `ChartStateManager` verfügbar:

```python
from src.ui.widgets.chart_state_manager import get_chart_state_manager

# Chart State Manager holen
manager = get_chart_state_manager()

# Nur Zeichnungen löschen
manager.settings.setValue(f"charts/{symbol}/drawings", "[]")

# Kompletten Zustand löschen
manager.remove_chart_state(symbol)

# Alle Zustände löschen
manager.clear_all_states()
```

Oder im Chart-Widget mit Mixin:

```python
# Im Chart-Widget (hat TradingViewChartStateMixin)
self.clear_saved_state()  # Löscht gespeicherten Zustand für current_symbol
```

## Technische Details

### QSettings Struktur

```
OrderPilot/TradingApp
└── charts/
    └── {sanitized_symbol}/
        ├── indicators (JSON array)
        ├── drawings (JSON array)        ← Die 200+ Annotationen
        ├── timeframe (string)
        ├── chart_type (string)
        ├── view_range (JSON object)
        ├── pane_layout (JSON object)
        └── window_geometry (bytes)
```

### Drawings Format

Jede Zeichnung ist ein JSON-Objekt:

```json
{
  "type": "trendline",
  "id": "drawing_1234567890",
  "points": [
    {"time": 1234567890, "price": 42000.0},
    {"time": 1234567900, "price": 43000.0}
  ],
  "color": "#00FF00",
  "lineWidth": 2
}
```

Bei 200+ Zeichnungen wird dieses Array sehr groß und verlangsamt das Laden.

## Siehe auch

- `src/ui/widgets/chart_state_manager.py` - Backend für State Management
- `src/ui/widgets/chart_state_integration.py` - Mixin für Charts
- `ARCHITECTURE.md` - Projekt-Architektur Dokumentation
