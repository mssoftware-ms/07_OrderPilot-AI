# CEL Editor - UI Design Study
## Interaktiver CEL-Regel-Editor mit KI-Unterstützung

> **Design-Studie für PySide6** - Visuelle Modellierung von Trading-Strategien

---

## 📋 Übersicht

Diese Design-Studie implementiert ein vollständiges UI-Framework für einen interaktiven CEL-Editor (Common Expression Language) mit folgenden Hauptmerkmalen:

- **Visueller Pattern-Builder** - Drag & Drop von Candle-Patterns
- **CEL Code Editor** - Syntax-Highlighting für Trading-Regeln
- **KI-Assistenz** - Intelligente Vorschläge und Pattern-Erkennung
- **Multi-Timeframe Support** - Strategien über mehrere Zeitebenen
- **Professionelles Trading-Design** - Dark & Dark-White Themes

---

## 🎨 Theme-Varianten

### Dark Theme (Standard)
```
Primärer Hintergrund: #0d0f12
Sekundärer Hintergrund: #14161a
Akzentfarbe: #00d9ff (Cyan)
Erfolg: #00c853
Warnung: #ffab00
Fehler: #ff3d71
```

### Dark-White Theme (Softer)
```
Primärer Hintergrund: #1a1d23
Sekundärer Hintergrund: #22262e
Akzentfarbe: #4fc3f7 (Light Blue)
Text: Higher Contrast
```

---

## 📁 Projektstruktur

```
cel_editor_ui/
├── __init__.py              # Package-Initialisierung
├── main.py                  # Einstiegspunkt / Runner
├── main_window.py           # Hauptfenster mit Dock-Widgets
│
├── themes/
│   ├── __init__.py
│   ├── dark_theme.py        # Dark Theme QSS + Farbpalette
│   └── dark_white_theme.py  # Dark-White Theme QSS + Farbpalette
│
├── widgets/
│   ├── __init__.py
│   ├── pattern_builder.py   # Pattern-Builder Canvas
│   ├── cel_editor.py        # CEL Code Editor mit Highlighting
│   ├── ai_assistant.py      # KI-Assistenz-Panel
│   └── panels.py            # Library, Filter, Templates
│
└── dialogs/
    ├── __init__.py
    └── dialogs.py           # Export, Import, Settings, etc.
```

---

## 🖼️ UI-Komponenten

### 1. Hauptfenster (`main_window.py`)
- **Toolbar**: Strategie-Auswahl, Speichern, Validieren, Backtest
- **Linker Dock**: Pattern Library, Strategie-Vorlagen, Filter, Snippets
- **Zentraler Bereich**: Pattern Builder Canvas + CEL Code Editor (Split)
- **Rechter Dock**: Properties, Regel-Übersicht, KI-Assistent
- **Statusleiste**: Validierungsstatus, Regel-Zähler, AI-Status

### 2. Pattern Builder (`widgets/pattern_builder.py`)
- **CandleItem**: Draggable Kerzen-Grafiken (Bullish/Bearish/Doji)
- **RelationLine**: Visuelle Verbindungen zwischen Kerzen
- **PatternBuilderCanvas**: Hauptfläche mit Grid und Toolbar
- **CandlePropertiesPanel**: Eigenschaften der ausgewählten Kerze

### 3. CEL Code Editor (`widgets/cel_editor.py`)
- **CELSyntaxHighlighter**: Syntax-Highlighting für CEL
- **LineNumberArea**: Zeilennummern mit Current-Line-Highlight
- **CELCodeEditor**: Monospace Editor mit Tabs
- **CELEditorWidget**: Komplett-Widget mit Tabs und Validation
- **CELSnippetsPanel**: Durchsuchbare Code-Snippet-Bibliothek

### 4. KI-Assistenz (`widgets/ai_assistant.py`)
- **AISuggestionCard**: Vorschlagskarten mit Typisierung
- **AIAssistantPanel**: Hauptpanel mit Status und Input
- **PatternRecognitionPanel**: Erkannte Patterns im Chart

### 5. Zusätzliche Panels (`widgets/panels.py`)
- **PatternLibraryPanel**: Kategorisierte Pattern-Bibliothek
- **FilterPanel**: Timeframe, Volume, Trend, Volatility Filter
- **StrategyTemplatesPanel**: Vorgefertigte Strategie-Templates

### 6. Dialoge (`dialogs/dialogs.py`)
- **ExportDialog**: RulePack JSON Export
- **ImportDialog**: Drag & Drop Import
- **SettingsDialog**: Multi-Tab Einstellungen
- **PatternDetailsDialog**: Pattern-Statistiken und Regeln
- **ValidationResultDialog**: Erfolg/Fehler Anzeige

---

## 🚀 Verwendung

### Voraussetzungen
```bash
pip install PySide6>=6.5.0
```

### Starten
```bash
# Standard Dark Theme
python main.py

# Dark-White Theme
python main.py --theme light

# Demo-Modus (zeigt alle Dialoge)
python main.py --demo

# Vollbildmodus
python main.py --fullscreen
```

---

## 🎯 Design-Prinzipien

### Typografie
- **Code/Technical**: JetBrains Mono (Monospace)
- **UI Text**: System Sans-Serif (Segoe UI / SF Pro)
- **Headings**: Bold, etwas größer

### Abstände
- **Basis**: 8px
- **Small**: 4px
- **Medium**: 12px
- **Large**: 16-24px

### Farb-Semantik
- **Bullish/Erfolg**: `#00c853` (Grün)
- **Bearish/Fehler**: `#ff3d71` (Rot)
- **Warnung**: `#ffab00` (Amber)
- **Info/Akzent**: `#00d9ff` (Cyan)
- **Neutral**: `#8b8f98` (Grau)

### Interaktion
- **Hover**: +5% Helligkeit, optionale Border
- **Focus**: Akzentfarbe Border
- **Active/Pressed**: +8% Helligkeit
- **Disabled**: 50% Opacity

---

## 📊 Komponenten-Übersicht

| Komponente | Datei | Beschreibung |
|------------|-------|--------------|
| Hauptfenster | `main_window.py` | Dock-Layout, Menüs, Toolbar |
| Dark Theme | `themes/dark_theme.py` | QSS Styles + Farbwerte |
| Dark-White Theme | `themes/dark_white_theme.py` | Hellere Variante |
| Pattern Builder | `widgets/pattern_builder.py` | Visueller Kerzen-Editor |
| CEL Editor | `widgets/cel_editor.py` | Code-Editor mit Highlighting |
| AI Assistent | `widgets/ai_assistant.py` | Vorschläge und Erkennung |
| Library/Filter | `widgets/panels.py` | Pattern-Bibliothek, Filter |
| Dialoge | `dialogs/dialogs.py` | Export, Import, Settings |

---

## 🔧 Anpassung

### Theme wechseln
```python
from main_window import CELEditorMainWindow

window = CELEditorMainWindow(use_dark_white_theme=True)
# oder
window.toggle_theme()
```

### Farbpalette anpassen
```python
from themes.dark_theme import DARK_COLORS

DARK_COLORS['accent'] = '#ff6b6b'  # Andere Akzentfarbe
```

---

## 📝 Hinweise

1. **Design-Studie**: Diese Implementierung zeigt nur das UI-Design ohne Backend-Logik
2. **Keine Funktionalität**: Buttons, Menüs und Aktionen sind nicht verbunden
3. **Erweiterbar**: Signals/Slots für echte Funktionalität vorbereitet
4. **Performance**: Alle Widgets verwenden Qt's native Rendering

---

## 🗓️ Version

- **Version**: 2.0.0-beta
- **Stand**: Januar 2026
- **Framework**: PySide6 6.5+
- **Python**: 3.10+

---

## 📄 Lizenz

Proprietär - Nur für interne Verwendung

---

*CEL Editor - Professionelles Trading-Pattern-Design*
