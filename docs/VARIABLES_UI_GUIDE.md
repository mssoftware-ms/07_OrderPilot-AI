# Variable System - UI Guide

## 🎯 Wo sind die neuen UI-Elemente?

### 1. ChartWindow Toolbar (Hauptfenster)

**Neue Buttons in der oberen Toolbar:**

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Chart │ 📋 Variables │ 📝 Manage │ 🔍 Zoom │ ← Back ... │
└─────────────────────────────────────────────────────────────┘
```

**Position:** Rechts nach den Zoom-Buttons in `toolbar_row1`

**Buttons:**
- **📋 Variables** - Variable Reference Dialog (Read-Only Tabelle)
- **📝 Manage** - Variable Manager Dialog (CRUD Interface)

**Keyboard Shortcuts:**
- `Ctrl+Shift+V` → Variable Reference Dialog
- `Ctrl+Shift+M` → Variable Manager Dialog

---

## 📊 Variable Reference Dialog (📋 Variables Button)

**Was es zeigt:**

```
╔════════════════════════════════════════════════════════════╗
║           Variable Reference - All Available Variables      ║
╠════════════════════════════════════════════════════════════╣
║                                                             ║
║  🔍 Search: [_________________________]  Category: [All ▼] ║
║                                                             ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ Variable                  │ Value      │ Type        │ ║
║  ├──────────────────────────────────────────────────────┤ ║
║  │ 📊 CHART VARIABLES (19)                              │ ║
║  │   chart.close             │ 88,097.60  │ float       │ ║
║  │   chart.open              │ 88,050.00  │ float       │ ║
║  │   chart.high              │ 88,200.00  │ float       │ ║
║  │   chart.low               │ 88,000.00  │ float       │ ║
║  │   chart.volume            │ 1,234.56   │ float       │ ║
║  │   chart.symbol            │ BTCUSDT    │ string      │ ║
║  │   chart.timeframe         │ 5m         │ string      │ ║
║  │   ...                                                 │ ║
║  │                                                       │ ║
║  │ 🤖 BOT VARIABLES (23)                                │ ║
║  │   bot.trading_enabled     │ true       │ bool        │ ║
║  │   bot.max_position_size   │ 0.1        │ float       │ ║
║  │   bot.stop_loss_pct       │ 2.0        │ float       │ ║
║  │   ...                                                 │ ║
║  │                                                       │ ║
║  │ 📁 PROJECT VARIABLES (User-Defined)                  │ ║
║  │   project.my_custom_var   │ 100        │ int         │ ║
║  │   ...                                                 │ ║
║  │                                                       │ ║
║  │ 📈 INDICATORS (from JSON)                            │ ║
║  │   indicators.rsi_14       │ 65.3       │ float       │ ║
║  │   indicators.ema_20       │ 88,100.00  │ float       │ ║
║  │   ...                                                 │ ║
║  │                                                       │ ║
║  │ 🎯 REGIME (from JSON)                                │ ║
║  │   regime.current          │ trending   │ string      │ ║
║  │   regime.strength         │ 0.75       │ float       │ ║
║  │   ...                                                 │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                             ║
║  [📋 Copy Selected] [📋 Copy All] [🔄 Refresh] [❌ Close]  ║
║                                                             ║
╚════════════════════════════════════════════════════════════╝
```

**Features:**
- ✅ Live-Werte von Chart (OHLCV)
- ✅ Bot Config Variablen
- ✅ Project Variablen (.cel_variables.json)
- ✅ **Indicators aus JSON** (wenn Bot Config geladen)
- ✅ **Regime aus JSON** (wenn Bot Config geladen)
- ✅ Suchfunktion
- ✅ Category Filter
- ✅ Copy to Clipboard

---

## 📝 Variable Manager Dialog (📝 Manage Button)

**Was es macht:**

```
╔════════════════════════════════════════════════════════════╗
║           Variable Manager - Project Variables CRUD        ║
╠════════════════════════════════════════════════════════════╣
║                                                             ║
║  🔍 Search: [_________________________]                    ║
║                                                             ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ Name                      │ Value      │ Type        │ ║
║  ├──────────────────────────────────────────────────────┤ ║
║  │ project.max_trades_daily  │ 10         │ int         │ ║
║  │ project.risk_per_trade    │ 0.02       │ float       │ ║
║  │ project.use_trailing_stop │ true       │ bool        │ ║
║  │ project.custom_threshold  │ 0.5        │ float       │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                             ║
║  ┌─────────────────── Edit Variable ──────────────────┐   ║
║  │  Name:  [project.custom_threshold              ]  │   ║
║  │  Value: [0.5                                   ]  │   ║
║  │  Type:  [float ▼]                                │   ║
║  │  Desc:  [Custom threshold for entry signals   ]  │   ║
║  └───────────────────────────────────────────────────┘   ║
║                                                             ║
║  [➕ Add New] [✏️ Edit] [🗑️ Delete] [💾 Save] [❌ Close]   ║
║                                                             ║
╚════════════════════════════════════════════════════════════╝
```

**Features:**
- ✅ Create/Edit/Delete Project Variables
- ✅ Type-safe (int, float, bool, string)
- ✅ Validation
- ✅ Speichert in `.cel_variables.json`
- ✅ Suchfunktion

---

## 🔌 Regime JSON Einbindung

### Wie Regime Variablen geladen werden:

**1. Bot Config JSON enthält Regime:**
```json
{
  "regime": {
    "current_regime": "trending",
    "regime_strength": 0.75,
    "regime_confidence": 0.85,
    "atr_value": 250.5
  }
}
```

**2. Im Variable Reference Dialog:**
```
🎯 REGIME VARIABLES
  regime.current_regime     → "trending"
  regime.regime_strength    → 0.75
  regime.regime_confidence  → 0.85
  regime.atr_value          → 250.5
```

**3. In CEL Expressions verwenden:**
```python
# Beispiel CEL Expression
"regime.current_regime == 'trending' && regime.regime_strength > 0.7"
```

---

## 🧪 So testest du die neuen Features:

### Test 1: Variable Reference Dialog öffnen

```bash
# Starte App
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI
.wsl_venv/bin/python src/ui/app.py

# Im ChartWindow:
1. Klick auf "📋 Variables" Button (oder Ctrl+Shift+V)
2. Du siehst Tabelle mit allen Variablen
3. Kategorien: Chart, Bot, Project, Indicators, Regime
```

### Test 2: Project Variables erstellen

```bash
# Im ChartWindow:
1. Klick auf "📝 Manage" Button (oder Ctrl+Shift+M)
2. Klick auf "➕ Add New"
3. Erstelle Variable:
   - Name: project.my_test_var
   - Value: 42
   - Type: int
   - Description: Test variable
4. Klick "💾 Save"
5. Variable ist jetzt in .cel_variables.json gespeichert
```

### Test 3: Regime JSON laden

```bash
# 1. Lade Bot Config mit Regime Daten:
# Öffne: 03_JSON/Entry_Analyzer/Regime/260124_hardcodet_defaults_v2.json

# 2. Im Variable Reference Dialog:
# Klick "📋 Variables"
# Scroll zu "🎯 REGIME VARIABLES"
# Siehst alle Regime-Werte aus JSON
```

---

## 🎨 UI Integration Details

### ChartWindow Toolbar Layout:

```python
# src/ui/widgets/chart_window.py Zeile 40
class ChartWindow(
    VariablesMixin,  # ← Fügt Variable Features hinzu
    CelEditorMixin,
    BotPanelsMixin,
    ...
):
    def __init__(self):
        # ...
        self.setup_variables_integration()  # ← Zeile 126
        # Erstellt:
        # - 📋 Variables Button
        # - 📝 Manage Button
        # - Keyboard Shortcuts
```

### Variable Laden (Automatisch):

```python
# Wenn ChartWindow Bot Config lädt:
def load_bot_config(self, config_path):
    # ...
    self.bot_config = load_json(config_path)

    # Variables System lädt automatisch:
    # - bot.* Variablen aus Config
    # - indicators.* aus config["indicators"]
    # - regime.* aus config["regime"]

    # Variable Reference Dialog zeigt alles an!
```

---

## 📁 Dateien Struktur

```
src/
├── ui/
│   ├── dialogs/
│   │   └── variables/
│   │       ├── __init__.py
│   │       ├── variable_reference_dialog.py  ← 📋 Variables Dialog
│   │       └── variable_manager_dialog.py    ← 📝 Manage Dialog
│   │
│   └── widgets/
│       ├── chart_window.py                   ← Nutzt VariablesMixin
│       ├── chart_window_mixins/
│       │   ├── variables_mixin.py            ← Toolbar Buttons
│       │   └── __init__.py
│       │
│       └── cel_editor_variables_autocomplete.py  ← Autocomplete
│
├── core/
│   └── variables/
│       ├── __init__.py
│       ├── storage.py            ← .cel_variables.json Loader
│       ├── providers.py          ← Chart/Bot/Regime Data Provider
│       └── context_builder.py    ← Merges all sources
│
└── .cel_variables.json           ← Project Variables (erstellt bei Save)
```

---

## ❓ FAQ

### Q: Wo sind die Buttons?
**A:** In der ChartWindow Toolbar (oberste Zeile), rechts neben den Zoom-Buttons.

### Q: Ich sehe keine Regime Variablen?
**A:** Lade eine Bot Config JSON, die ein "regime" Feld enthält. Beispiel:
`03_JSON/Entry_Analyzer/Regime/260124_hardcodet_defaults_v2.json`

### Q: Wie erstelle ich Project Variables?
**A:** Klick "📝 Manage" → "➕ Add New" → Variable erstellen → "💾 Save"

### Q: Wo werden Project Variables gespeichert?
**A:** In `.cel_variables.json` im Projekt-Root oder Bot Config Verzeichnis.

### Q: Kann ich Variables im CEL Editor nutzen?
**A:** Ja! Autocomplete schlägt automatisch alle Variablen vor (Ctrl+Space).

---

## 🚀 Next Steps

1. **Starte die App** und öffne ChartWindow
2. **Klick "📋 Variables"** um alle verfügbaren Variablen zu sehen
3. **Klick "📝 Manage"** um eigene Project Variables zu erstellen
4. **Lade Bot Config JSON** um Regime/Indicators Variablen zu sehen
5. **Nutze im CEL Editor** die Autocomplete-Funktion (Ctrl+Space)

---

**Erstellt:** 2026-01-27
**Version:** MVP 1.0 (4 Stunden Entwicklungszeit)
