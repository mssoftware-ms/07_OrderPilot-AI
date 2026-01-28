# 📊 Variable Reference Popup - Design Spezifikation

**Version:** 1.0
**Erstellt:** 2026-01-28
**Feature:** Quick Reference Dialog für alle verfügbaren CEL-Variablen

---

## 🎯 Zweck

Ein **schnelles Popup-Fenster** im CEL Editor, das ALLE verfügbaren Variablen in einer übersichtlichen Tabelle anzeigt:
- **Chart-Variablen** (chart.price, chart.volume, etc.)
- **Bot-Konfiguration** (bot.leverage, bot.entry.*, etc.)
- **Projekt-Variablen** (project.*, user-defined)
- **Indikatoren** (atr.value, ema_fast.*, etc.)
- **Regime** (regime.id, regime.name, etc.)

Mit **Live-Werten** (wenn verfügbar) und **Copy-to-Clipboard** Funktionalität.

---

## 🖼️ UI Design

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 Variable Reference                          [Search] [x]     │
├─────────────────────────────────────────────────────────────────┤
│  🔍 Search: [____________]  Category: [All ▼]  Show: [All ▼]   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─ 📊 Chart Data (8) ─────────────────────────────────┐       │
│  │ Variable          │ Type   │ Current Value │ Action │       │
│  │──────────────────┼────────┼───────────────┼────────│       │
│  │ chart.price      │ float  │ 95250.0       │ [Copy] │       │
│  │ chart.open       │ float  │ 95100.0       │ [Copy] │       │
│  │ chart.high       │ float  │ 95300.0       │ [Copy] │       │
│  │ chart.low        │ float  │ 95050.0       │ [Copy] │       │
│  │ chart.volume     │ float  │ 125.5         │ [Copy] │       │
│  │ chart.timestamp  │ int    │ 1706400000    │ [Copy] │       │
│  │ chart.timeframe  │ string │ "1h"          │ [Copy] │       │
│  │ chart.symbol     │ string │ "BTCUSDT"     │ [Copy] │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─ 🤖 Bot Configuration (25) ──────────────────────────┐       │
│  │ Variable                    │ Type  │ Value  │ Action │      │
│  │────────────────────────────┼───────┼────────┼────────│      │
│  │ bot.symbol                  │ string│ "BTC..." │ [Copy] │    │
│  │ bot.leverage                │ int   │ 10      │ [Copy] │    │
│  │ bot.paper_mode              │ bool  │ true    │ [Copy] │    │
│  │ bot.risk_per_trade_pct      │ float │ 1.0     │ [Copy] │    │
│  │ bot.sl_atr_multiplier       │ float │ 1.5     │ [Copy] │    │
│  │ bot.tp_atr_multiplier       │ float │ 2.0     │ [Copy] │    │
│  │ bot.trailing_enabled        │ bool  │ true    │ [Copy] │    │
│  │ ▶ bot.entry.* (15 more...)                    │ [Expand]│   │
│  │ ▶ bot.llm.* (4 more...)                       │ [Expand]│   │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─ 🎨 Project Variables (12) ──────────────────────────┐       │
│  │ Variable                 │ Type  │ Value     │ Action │      │
│  │─────────────────────────┼───────┼───────────┼────────│      │
│  │ project.my_min_price     │ float │ 90000.0   │ [Copy] │      │
│  │ project.my_max_leverage  │ int   │ 15        │ [Copy] │      │
│  │ project.my_atrp_thresh.. │ float │ 0.5       │ [Copy] │      │
│  │ ... (9 more)                                  │        │      │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─ 📈 Indicators (8) ───────────────────────────────────┐      │
│  │ Variable              │ Type  │ Value    │ Action │          │
│  │──────────────────────┼───────┼──────────┼────────│          │
│  │ atr.value             │ float │ 550.0    │ [Copy] │          │
│  │ atr.signal            │ string│ "neutral"│ [Copy] │          │
│  │ atrp.value            │ float │ 0.58     │ [Copy] │          │
│  │ ema_fast.value        │ float │ 95200.0  │ [Copy] │          │
│  │ ema_fast.cross_up     │ bool  │ false    │ [Copy] │          │
│  │ ema_slow.value        │ float │ 94800.0  │ [Copy] │          │
│  │ rsi.value             │ float │ 62.5     │ [Copy] │          │
│  │ rsi.signal            │ string│ "neutral"│ [Copy] │          │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─ 🌍 Regime (4) ───────────────────────────────────────┐      │
│  │ Variable       │ Type   │ Value           │ Action │         │
│  │───────────────┼────────┼─────────────────┼────────│         │
│  │ regime.id      │ string │ "R1"            │ [Copy] │         │
│  │ regime.name    │ string │ "Strong Bull"   │ [Copy] │         │
│  │ regime.scope   │ string │ "GLOBAL"        │ [Copy] │         │
│  │ regime.active  │ bool   │ true            │ [Copy] │         │
│  └──────────────────────────────────────────────────────┘       │
├─────────────────────────────────────────────────────────────────┤
│  Total: 57 variables (8 chart, 25 bot, 12 project, 8 ind, 4 reg)│
│  [Copy All Names] [Export CSV] [Refresh Values]      [Close]    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Features

### 1. Kategorisierte Anzeige
- ✅ **Collapsible Gruppen** (Chart Data, Bot Config, Project Variables, etc.)
- ✅ **Expand/Collapse All** Button
- ✅ **Count Badge** (z.B. "Bot Configuration (25)")
- ✅ **Icons** für jede Kategorie (📊 Chart, 🤖 Bot, 🎨 Project, etc.)

### 2. Tabellen-Columns
| Column | Beschreibung | Width |
|--------|--------------|-------|
| **Variable** | Vollständiger Name (z.B. `chart.price`) | 40% |
| **Type** | Data Type (float, int, string, bool, array) | 15% |
| **Current Value** | Live-Wert (wenn verfügbar) oder "N/A" | 30% |
| **Action** | Copy-Button | 15% |

### 3. Interactive Elements

**Copy Button:**
```python
# Click: Kopiere Variable-Name (z.B. "chart.price") in Clipboard
# Double-Click auf Row: Füge Variable in CEL Editor an Cursor-Position ein
# Right-Click: Context Menu (Copy Name, Copy Value, Insert at Cursor)
```

**Search:**
```python
# Live-Suche: Filtere Tabelle nach Variable-Name
# Fuzzy-Matching: "price" findet "chart.price", "my_min_price", etc.
# Highlight: Matched Text wird hervorgehoben
```

**Category Filter:**
```python
# Dropdown: [All, Chart, Bot, Project, Indicators, Regime]
# Multi-Select: z.B. nur "Chart + Indicators" anzeigen
```

**Show Filter:**
```python
# [All] - Zeige alle Variablen
# [Defined] - Nur Variablen mit aktuellem Wert
# [Undefined] - Nur Variablen ohne Wert (N/A)
```

### 4. Live Value Updates

**Static Values (immer verfügbar):**
- `bot.*` - Aus BotConfig geladen
- `project.*` - Aus .cel_variables.json geladen

**Dynamic Values (wenn verfügbar):**
- `chart.*` - Wenn ChartWindow aktiv
- `indicators.*` - Wenn Indikatoren berechnet
- `regime.*` - Wenn Regime erkannt

**Update-Modi:**
- 🔵 **Manual Refresh:** Button "Refresh Values" (lädt Live-Daten neu)
- 🟢 **Auto-Refresh:** Checkbox "Auto-refresh every 1s" (nur bei aktivem Bot)
- 🟡 **On-Demand:** Popup wird beim Öffnen mit aktuellen Werten gefüllt

**Value Display:**
```python
# Value verfügbar: Zeige Wert (z.B. "95250.0")
# Value nicht verfügbar: Zeige "N/A" (grau)
# Value geändert: Highlight (gelber Fade-Out über 2s)
```

---

## 🛠️ Implementation

### Datei-Struktur

```
src/ui/dialogs/variable_reference_dialog.py
```

**Class:**
```python
class VariableReferenceDialog(QDialog):
    """Quick reference popup for all available CEL variables."""

    def __init__(self, parent, context_builder: CELContextBuilder):
        self.context_builder = context_builder
        self.auto_refresh = False
        self.refresh_timer = QTimer()

    def _setup_ui(self):
        # Search + Filter Row
        # Category Groups (Collapsible)
        # Buttons (Copy All, Export, Refresh, Close)

    def _populate_table(self):
        """Populate table with all variables from context."""
        context = self.context_builder.build(...)
        self._add_category("Chart Data", context, "chart.")
        self._add_category("Bot Configuration", context, "bot.")
        # ...

    def _add_category(self, title: str, context: dict, prefix: str):
        """Add collapsible category group."""
        # Create GroupBox mit QTableWidget
        # Filter context by prefix
        # Add rows to table

    def _on_copy_variable(self, variable_name: str):
        """Copy variable name to clipboard."""
        QApplication.clipboard().setText(variable_name)

    def _on_double_click(self, variable_name: str):
        """Insert variable at cursor position in CEL Editor."""
        self.variable_inserted.emit(variable_name)

    def _on_refresh(self):
        """Reload all values from live sources."""
        self._populate_table()

    def _on_auto_refresh_toggled(self, checked: bool):
        if checked:
            self.refresh_timer.start(1000)  # 1s interval
        else:
            self.refresh_timer.stop()
```

### Integration in CEL Editor

**Main Window Änderungen:**
```python
# src/ui/windows/cel_editor/main_window.py

def _setup_toolbar(self):
    # ...existing toolbar buttons...

    # NEU: Variable Reference Button
    self.var_ref_btn = QPushButton("📋 Variables")
    self.var_ref_btn.setToolTip(
        "Show all available variables (Ctrl+Shift+R)\n"
        "- Chart data (chart.price, chart.volume, etc.)\n"
        "- Bot configuration (bot.leverage, bot.entry.*, etc.)\n"
        "- Project variables (project.*, user-defined)\n"
        "- Indicators (atr.value, ema_fast.*, etc.)\n"
        "- Regime (regime.id, regime.name, etc.)"
    )
    self.var_ref_btn.clicked.connect(self._show_variable_reference)
    toolbar.addWidget(self.var_ref_btn)

    # Keyboard Shortcut
    QShortcut(QKeySequence("Ctrl+Shift+R"), self, self._show_variable_reference)

def _show_variable_reference(self):
    """Show Variable Reference Dialog."""
    from src.ui.dialogs.variable_reference_dialog import VariableReferenceDialog

    dialog = VariableReferenceDialog(self, self.context_builder)
    dialog.variable_inserted.connect(self._on_variable_inserted)
    dialog.exec()

def _on_variable_inserted(self, variable_name: str):
    """Insert variable at cursor position in active editor."""
    editor = self.editor_tabs.currentWidget()  # CelEditorWidget
    if editor:
        editor.insert_text(variable_name)
```

---

## 📋 Daten-Quellen

### Context Builder Integration

```python
# src/core/tradingbot/cel/context_builder.py

class CELContextBuilder:
    def build_for_reference(
        self,
        chart: ChartWindow | None = None,
        bot: BotConfig | None = None,
        project_vars: ProjectVariables | None = None,
        indicators: dict | None = None,
        regime: dict | None = None
    ) -> dict:
        """Build context for Variable Reference Dialog.

        Returns dict with:
        - All available variables (with values if source present)
        - Metadata: type, category, description
        - Value availability flag (has_value: bool)
        """
        context = {}

        # Chart Data (only if ChartWindow provided)
        if chart:
            chart_data = self.chart_provider.get_context(chart)
            for key, value in chart_data.items():
                context[key] = {
                    "value": value,
                    "type": type(value).__name__,
                    "category": "Chart Data",
                    "has_value": True
                }
        else:
            # Add chart.* keys with N/A values
            for key in ["price", "open", "high", "low", "volume", "timestamp", "timeframe", "symbol"]:
                context[f"chart.{key}"] = {
                    "value": None,
                    "type": "float" if key != "timeframe" and key != "symbol" else "string",
                    "category": "Chart Data",
                    "has_value": False
                }

        # Bot Config (always available)
        if bot:
            bot_data = self.bot_provider.get_context(bot)
            for key, value in bot_data.items():
                context[key] = {
                    "value": value,
                    "type": type(value).__name__,
                    "category": "Bot Configuration",
                    "has_value": True
                }

        # Project Variables (from .cel_variables.json)
        if project_vars:
            for var_name, var_obj in project_vars.variables.items():
                context[f"project.{var_name}"] = {
                    "value": var_obj.value,
                    "type": var_obj.type.value,
                    "category": f"Project Variables ({var_obj.category.value})",
                    "description": var_obj.description,
                    "has_value": True
                }

        # Indicators (if provided)
        if indicators:
            for ind_name, ind_data in indicators.items():
                for field in ["value", "signal", "cross_up", "cross_down"]:
                    key = f"{ind_name}.{field}"
                    if field in ind_data:
                        context[key] = {
                            "value": ind_data[field],
                            "type": type(ind_data[field]).__name__,
                            "category": "Indicators",
                            "has_value": True
                        }

        # Regime (if provided)
        if regime:
            for key in ["id", "name", "scope", "active"]:
                if key in regime:
                    context[f"regime.{key}"] = {
                        "value": regime[key],
                        "type": type(regime[key]).__name__,
                        "category": "Regime",
                        "has_value": True
                    }

        return context
```

---

## 🎯 Use Cases

### Use Case 1: Schnelle Variable Lookup
**Szenario:** User schreibt CEL Code und erinnert sich nicht an exakten Variable-Namen

**Workflow:**
1. User drückt `Ctrl+Shift+R` (oder klickt "Variables" Button)
2. Popup öffnet mit allen Variablen
3. User sucht "price" → findet `chart.price`, `project.my_min_price`
4. User klickt "Copy" bei `chart.price`
5. User fügt in CEL Editor ein (Ctrl+V)

---

### Use Case 2: Werte-Debugging
**Szenario:** CEL Expression evaluiert zu `False`, User will verstehen warum

**Workflow:**
1. User öffnet Variable Reference
2. User aktiviert "Auto-refresh" (live updates)
3. User sieht: `chart.price = 95250.0`, `project.my_min_price = 96000.0`
4. → AHA: Preis ist unter Minimum, deshalb `False`
5. User ändert entweder Code oder Projekt-Variable

---

### Use Case 3: Template-Entwicklung
**Szenario:** User erstellt neue Strategy-Template, braucht Übersicht aller Bot-Settings

**Workflow:**
1. User öffnet Variable Reference
2. User wählt Category Filter: "Bot Configuration"
3. User sieht alle 25 bot.* Variablen mit aktuellen Werten
4. User klickt "Export CSV" → Speichert als Referenz-Tabelle
5. User nutzt Tabelle für Dokumentation

---

### Use Case 4: Entry Rule Design
**Szenario:** User entwickelt Entry Rule und will alle verfügbaren Indikatoren sehen

**Workflow:**
1. User öffnet Variable Reference
2. User expandiert "Indicators" Gruppe
3. User sieht: `atr.value`, `atrp.value`, `ema_fast.*`, `rsi.*`
4. User double-clicked auf `atrp.value` → Fügt in Editor ein
5. User schreibt weiter: `atrp.value > 0.5 && ...`

---

## 📊 Performance

### Loading Time
- **Initial Load:** <100ms (alle Variablen aus Context Builder)
- **Refresh:** <50ms (nur Werte aktualisieren, keine DOM-Änderungen)
- **Search:** <10ms (in-memory filtering)

### Memory
- **Static Memory:** ~2MB (UI + Table Data)
- **Dynamic Memory:** +500KB pro auto-refresh cycle

### Auto-Refresh Impact
- **Interval:** 1s (konfigurierbar)
- **CPU:** <1% (nur wenn Dialog sichtbar)
- **Network:** None (lokale Daten)

---

## ✅ Acceptance Criteria

### Functionality
- ✅ Zeigt ALLE Variablen aus allen Namespaces (chart, bot, project, indicators, regime)
- ✅ Copy-Button kopiert Variable-Name in Clipboard
- ✅ Double-Click fügt Variable in CEL Editor an Cursor-Position ein
- ✅ Live-Werte werden angezeigt (wenn verfügbar)
- ✅ "N/A" für nicht verfügbare Werte (grau dargestellt)
- ✅ Search funktioniert (Fuzzy-Matching)
- ✅ Category Filter funktioniert

### UI/UX
- ✅ Dialog öffnet in <200ms
- ✅ Responsive (scrollbar bei vielen Variablen)
- ✅ Keyboard Navigation (Tab, Arrow Keys, Enter = Copy)
- ✅ Keyboard Shortcut (Ctrl+Shift+R)
- ✅ Tooltip für jede Variable (Type + Description)

### Integration
- ✅ Button im CEL Editor Toolbar ("📋 Variables")
- ✅ Signal `variable_inserted` emitted bei Double-Click
- ✅ CEL Editor empfängt Signal und fügt Variable ein

---

## 🚀 Implementation Plan

### Phase 3.3b: Variable Reference Popup (2.5h)
**Hinzufügen zu Phase 3 (UI Development)**

**Tasks:**
- **3.3b.1** VariableReferenceDialog UI (1.5h)
  - QDialog mit Category Groups (Collapsible)
  - QTableWidget pro Kategorie
  - Search/Filter Widgets
  - Copy/Export Buttons

- **3.3b.2** Context Integration (0.5h)
  - CELContextBuilder.build_for_reference()
  - Handle missing sources (ChartWindow, Indicators, etc.)
  - Type + Description Metadata

- **3.3b.3** CEL Editor Integration (0.5h)
  - Toolbar Button + Shortcut (Ctrl+Shift+R)
  - Signal Handling (variable_inserted)
  - Insert at Cursor Position

**Tests:**
- Manual UI Test - Dialog öffnet mit allen Variablen
- Manual UI Test - Copy Button funktioniert
- Manual UI Test - Double-Click fügt Variable ein
- Manual UI Test - Search/Filter funktioniert
- Manual UI Test - Auto-Refresh aktualisiert Werte

---

## 📝 Notes

### Alternative Designs

**Option A: Sidebar Panel (anstatt Popup)**
- ✅ Permanent sichtbar während Code-Entwicklung
- ❌ Nimmt Platz weg (besonders auf kleinen Bildschirmen)
- 🤔 Könnte als Dockable Widget implementiert werden

**Option B: Autocomplete Enhancement (anstatt separates Popup)**
- ✅ Integriert in bestehenden Workflow
- ❌ Keine Werte-Anzeige möglich
- ❌ Keine Kategorie-Übersicht

**Entscheidung: Popup (Option Current)**
- ✅ Schnell zugänglich (Ctrl+Shift+R)
- ✅ Zeigt ALLE Variablen + Werte auf einen Blick
- ✅ Kein Platz-Verlust im Editor
- ✅ Kann später zu Dockable Widget erweitert werden

---

**Erstellt:** 2026-01-28
**Version:** 1.0
**Status:** 📋 Design Complete → Ready for Implementation
**Autor:** Claude Code (OrderPilot-AI Development Team)
