# UI Inspector Integration Guide

Der F12 UI Inspector funktioniert für **PyQt6/PyQt5/PySide6** Projekte.

## Quick Setup (3 Schritte)

### 1. Datei kopieren

Kopiere `src/ui/debug/ui_inspector.py` in dein Projekt:
```
dein_projekt/
├── src/
│   └── ui/
│       └── debug/
│           ├── __init__.py
│           └── ui_inspector.py   ← Diese Datei
```

### 2. Mixin importieren

In deinem Hauptfenster:
```python
from src.ui.debug.ui_inspector import UIInspectorMixin

class MainWindow(QMainWindow, UIInspectorMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... dein Setup ...

        # F12 UI Inspector aktivieren
        self.setup_ui_inspector()
```

### 3. Import prüfen

`src/ui/debug/__init__.py`:
```python
from .ui_inspector import UIInspectorMixin

__all__ = ['UIInspectorMixin']
```

## Verwendung

| Aktion    | Funktion                  |
| --------- | ------------------------- |
| **F12**   | Inspector Ein/Aus         |
| **Hover** | Zeigt objectName + Pfad   |
| **Klick** | Kopiert Pfad in Clipboard |

## Wichtig: objectNames setzen!

Damit der Inspector nützlich ist, setze `objectName` für alle wichtigen Widgets:

```python
# RICHTIG
self.btn_start = QPushButton("Start")
self.btn_start.setObjectName("btn_start")

# FALSCH (Inspector zeigt nur Klassennamen)
self.btn_start = QPushButton("Start")
```

## Naming Convention

| Widget-Typ | Prefix | Beispiel                  |
| ---------- | ------ | ------------------------- |
| Button     | `btn_` | `btn_save`, `btn_cancel`  |
| Label      | `lbl_` | `lbl_status`, `lbl_price` |
| LineEdit   | `txt_` | `txt_username`            |
| ComboBox   | `cmb_` | `cmb_theme`               |
| CheckBox   | `chk_` | `chk_enabled`             |

## Troubleshooting

**Inspector zeigt nur `<QPushButton>` statt Namen?**
→ `setObjectName()` wurde nicht aufgerufen

**F12 funktioniert nicht?**
→ `setup_ui_inspector()` in `__init__` aufrufen
→ Mixin vor QMainWindow in der Vererbung
