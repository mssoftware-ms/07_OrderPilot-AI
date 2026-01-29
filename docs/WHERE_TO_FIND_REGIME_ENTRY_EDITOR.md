# 📍 Wo finde ich den Regime Entry Expression Editor?

**Version:** 1.0  
**Datum:** 2026-01-29

---

## 🎯 Schnellanleitung

### Schritt 1: Öffne den CEL Editor

1. Starte **OrderPilot-AI**
2. Öffne ein **Chart** (beliebiges Symbol/Timeframe)
3. In der **Chart-Toolbar** (oben): Klicke auf den **"CEL Editor"** Button
   - Icon: 📝 oder ähnliches
   - Tooltip: "CEL Editor" oder "Visual Pattern Builder"

**Ergebnis:** Ein neues Fenster **"CEL Editor - [Symbol] Strategy"** öffnet sich

---

### Schritt 2: Wechsle zum "JSON Editor" Tab

Im CEL Editor Fenster findest du **zentral** mehrere Tabs:

- Pattern Builder
- Code Editor
- Chart View
- Split View
- **JSON Editor** ← **HIER KLICKEN!**

**Ergebnis:** Der JSON Editor Tab öffnet sich

---

### Schritt 3: Wechsle zum "📊 Regime Entry" Sub-Tab

Im JSON Editor Tab gibt es **oben** weitere Sub-Tabs:

- JSON Editor
- AI Editor
- **📊 Regime Entry** ← **HIER IST DER NEUE EDITOR!**

**Ergebnis:** Der Regime Entry Expression Editor ist jetzt sichtbar!

---

## 📂 Vollständiger Pfad

```
OrderPilot-AI
  └─ Chart Window (beliebiges Symbol)
     └─ CEL Editor Button (Toolbar)
        └─ CEL Editor Window (neues Fenster)
           └─ JSON Editor Tab (zentral)
              └─ 📊 Regime Entry Sub-Tab
                 └─ REGIME ENTRY EXPRESSION EDITOR 🎉
```

---

## 🎨 Visual Guide

### 1. Chart Window Toolbar
```
┌─────────────────────────────────────────────────┐
│ 📊 Chart │ 🔍 Zoom │ 📝 CEL Editor │ ⚙️ ... │
│           ▲                                     │
│           └─ HIER KLICKEN!                      │
└─────────────────────────────────────────────────┘
```

### 2. CEL Editor Window (neues Fenster)
```
┌─────────────────────────────────────────────────┐
│ CEL Editor - BTCUSDT Strategy                   │
├─────────────────────────────────────────────────┤
│ Pattern Builder | Code Editor | JSON Editor ◄── │
│                   ▲                              │
│                   └─ HIER KLICKEN!               │
└─────────────────────────────────────────────────┘
```

### 3. JSON Editor Tab (Sub-Tabs oben)
```
┌─────────────────────────────────────────────────┐
│ JSON Editor | AI Editor | 📊 Regime Entry       │
│                            ▲                    │
│                            └─ HIER KLICKEN!     │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─ Regime Entry Expression Editor ─────────┐  │
│  │                                           │  │
│  │  📂 Regime JSON laden                     │  │
│  │  ☑ STRONG_BULL ☑ STRONG_TF               │  │
│  │  ⚡ Generate Expression                    │  │
│  │  💾 Save to JSON                          │  │
│  │                                           │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Workflow

### 1. Regime JSON erstellen (Entry Analyzer)
```
Entry Analyzer → Optimize → Save
  └─ Speichert JSON OHNE entry_expression
  └─ Location: 03_JSON/Entry_Analyzer/Regime/<timestamp>_*.json
```

### 2. Entry Expression hinzufügen (CEL Editor)
```
Chart → CEL Editor Button → JSON Editor Tab → 📊 Regime Entry
  └─ Lade Regime JSON (📂 Button)
  └─ Wähle Template oder Regimes
  └─ Generate Expression (⚡ Button)
  └─ Save to JSON (💾 Button)
```

### 3. Im Trading Bot verwenden
```
Bot Tab → ▶ Start Bot (JSON Entry)
  └─ Wähle die gespeicherte JSON mit entry_expression
```

---

## ❓ Troubleshooting

### Problem: "Ich finde den CEL Editor Button nicht!"

**Lösung:**
1. Stelle sicher, dass ein **Chart geöffnet** ist
2. Suche in der **Chart-Toolbar** (oben im Chart-Fenster)
3. Button-Icon: 📝 oder "CEL" Text
4. Falls nicht sichtbar: Prüfe ob Toolbar minimiert ist (View-Menü?)

---

### Problem: "Das CEL Editor Fenster öffnet sich nicht!"

**Lösung:**
1. Prüfe **Log-Dateien**: `logs/orderpilot-entrie.log`
2. Prüfe ob Fehler beim Import auftreten
3. Restart der Anwendung

---

### Problem: "Der 'Regime Entry' Tab ist nicht da!"

**Lösung:**
1. Stelle sicher, dass du im **JSON Editor Tab** bist (nicht Pattern Builder!)
2. Suche nach Sub-Tabs **oben** im Tab-Widget
3. Falls nicht sichtbar: Prüfe ob Updates installiert sind

---

### Problem: "Nach dem Laden einer JSON passiert nichts!"

**Lösung:**
1. Prüfe ob es eine **Regime JSON** ist (Schema 2.0, optimization_results vorhanden)
2. Normale Strategy JSONs werden NICHT automatisch im Regime Entry Editor geladen
3. Nutze den **"📂 Regime JSON laden"** Button direkt im Regime Entry Tab

---

## 📖 Weitere Dokumentation

- **Benutzerhandbuch:** `docs/REGIME_ENTRY_EDITOR_GUIDE.md`
- **Workflow-Korrektur:** `Help/entry_analyzer/WORKFLOW_KORREKTUR.md`
- **Complete Example:** `Help/entry_analyzer/COMPLETE_REGIME_EXAMPLE.json`
- **Code-Beispiele:** `test_regime_logic_only.py`

---

## 🔧 Entwickler-Info

### Module
- **UI Widget:** `src/ui/widgets/regime_entry_expression_editor.py`
- **Integration:** `src/ui/widgets/regime_editor_widget.py` (Zeile ~103, _create_regime_entry_tab)
- **CEL Editor Window:** `src/ui/windows/cel_editor/main_window.py`

### Code-Pfad (für Debugging)
```python
# Chart Window öffnet CEL Editor:
chart_window.show_cel_editor()
  └─ src/ui/widgets/chart_window_mixins/cel_editor_mixin.py
     └─ CelEditorWindow(...)

# CEL Editor lädt JSON Editor Tab:
cel_editor_window.central_tabs.addTab(regime_editor, "JSON Editor")
  └─ src/ui/widgets/regime_editor_widget.py
     └─ RegimeEditorWidget.tabs.addTab(regime_entry_tab, "📊 Regime Entry")
        └─ src/ui/widgets/regime_entry_expression_editor.py
           └─ RegimeEntryExpressionEditor (das ist der neue Editor!)
```

---

**Viel Erfolg beim Erstellen von Entry Expressions! 🚀**

**Autor:** Claude Code  
**Version:** 1.0  
**Datum:** 2026-01-29
