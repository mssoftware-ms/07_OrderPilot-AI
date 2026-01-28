# 🔧 CEL Project Variables System - Umsetzungsplan

**Version:** 1.0
**Erstellt:** 2026-01-28
**Status:** 📋 Planning
**Gesamtaufwand:** 16-28 Stunden

---

## 🎯 Projektziele

### Primary Goals
- ✅ **Chart-Daten** (OHLCV, Timestamp) in CEL verfügbar machen
- ✅ **Bot-Konfiguration** (Leverage, SL/TP, Entry Weights) in CEL verfügbar machen
- ✅ **Projektspezifische User-Variablen** (`.cel_variables.json`)
- ✅ **Variable Manager UI** im CEL Editor
- ✅ **Autocomplete** für alle Variablen im Code Editor

### Secondary Goals (Optional - Phase 4)
- 🔄 Variable Dependency Graph (welche Rules nutzen welche Variablen)
- 🔄 Import/Export von Variablen-Sets
- 🔄 Variable Validation (Typ-Checks, Range-Checks)
- 🔄 Variable Inspector (Live-Werte während Evaluation)

---

## 📋 Phase 1: Core Architecture & JSON Schema (4-6h)

### 1.1 JSON Schema für `.cel_variables.json` (1h)

**Deliverables:**
- `src/core/tradingbot/cel/variable_models.py` - Pydantic Models
- `schema/cel_variables.schema.json` - JSON Schema
- `examples/.cel_variables.example.json` - Beispiel-Datei

**Pydantic Models:**
```python
class ProjectVariable:
    name: str
    type: VariableType  # Enum: float, int, string, bool, array, dict
    value: Any
    description: str
    category: VariableCategory  # Enum: entry, exit, risk, time, custom

class ProjectVariables:
    version: str = "1.0"
    project_name: str
    variables: dict[str, ProjectVariable]
```

**Tests:**
- `test_variable_models.py` - Pydantic validation tests

---

### 1.2 Variable Storage & Persistence (2h)

**Deliverables:**
- `src/core/tradingbot/cel/variable_storage.py` - `VariableStorage` Klasse

**Class Structure:**
```python
class VariableStorage:
    """Load/Save/Cache .cel_variables.json"""

    def load(project_path: Path) -> ProjectVariables
    def save(project_path: Path, variables: ProjectVariables)
    def get(key: str) -> ProjectVariable | None
    def set(key: str, variable: ProjectVariable)
    def delete(key: str)
    def list() -> list[ProjectVariable]
    def search(query: str, category: str) -> list[ProjectVariable]
    def validate() -> list[ValidationError]
```

**Features:**
- ✅ LRU Cache (64 Einträge) für schnelle Lookups
- ✅ QFileSystemWatcher für Auto-Reload bei Änderungen
- ✅ JSON Schema Validation

**Tests:**
- `test_variable_storage.py` - Load/Save/Get/Set/Delete Tests

---

### 1.3 Chart Data Provider (2h)

**Deliverables:**
- `src/core/tradingbot/cel/providers/chart_data_provider.py`

**Class Structure:**
```python
class ChartDataProvider:
    """Export Chart-Daten als CEL Context"""

    def get_context(chart_window: ChartWindow) -> dict
```

**Context Keys:**
```python
{
    "chart.price": 95250.0,        # Close des letzten Candles
    "chart.open": 95100.0,         # Open
    "chart.high": 95300.0,         # High
    "chart.low": 95050.0,          # Low
    "chart.volume": 125.5,         # Volume
    "chart.timestamp": 1706400000, # Unix timestamp
    "chart.timeframe": "1h",       # Timeframe
    "chart.symbol": "BTCUSDT"      # Symbol
}
```

**Integration Point:**
- `ChartWindow` - Zugriff auf lightweight-charts data
- **Risk:** ChartWindow API könnte nicht direkt Candle-Daten exportieren
- **Mitigation:** Fallback via `ChartDataHelper` oder `ChartBridge`

**Tests:**
- `test_chart_data_provider.py` - Mock ChartWindow Tests

---

### 1.4 Bot Config Provider (1.5h)

**Deliverables:**
- `src/core/tradingbot/cel/providers/bot_config_provider.py`

**Class Structure:**
```python
class BotConfigProvider:
    """Export Bot-Config als CEL Context"""

    def get_context(bot_config: BotConfig) -> dict
```

**Context Keys:**
```python
{
    # Trading
    "bot.symbol": "BTCUSDT",
    "bot.leverage": 10,
    "bot.paper_mode": true,

    # Risk Management
    "bot.risk_per_trade_pct": 1.0,
    "bot.max_daily_loss_pct": 3.0,
    "bot.sl_atr_multiplier": 1.5,
    "bot.tp_atr_multiplier": 2.0,

    # Trailing Stop
    "bot.trailing_enabled": true,
    "bot.trailing_activation_pct": 50.0,
    "bot.trailing_offset_pct": 10.0,

    # Entry Score Weights
    "bot.entry.weight_confluence": 0.3,
    "bot.entry.weight_regime": 0.25,
    "bot.entry.weight_atrp": 0.15,
    # ... (15+ Entry Weights)

    # LLM Validation
    "bot.llm.enabled": false,
    "bot.llm.confidence_threshold": 70,
    "bot.llm.fallback_to_technical": true
}
```

**Integration Point:**
- `BotConfig` dataclass (`src/core/trading_bot/bot_config.py`)

**Tests:**
- `test_bot_config_provider.py` - BotConfig to context mapping

---

## 📋 Phase 2: CEL Engine Integration (3-4h)

### 2.1 Context Builder & Resolver (2h)

**Deliverables:**
- `src/core/tradingbot/cel/context_builder.py`

**Class Structure:**
```python
class CELContextBuilder:
    """Merge alle Variable-Sources zu einem CEL Context"""

    def build(
        chart: ChartWindow,
        bot: BotConfig,
        project_vars: ProjectVariables,
        indicators: dict,
        regime: dict
    ) -> dict
```

**Merge Strategy:**
- **Priority:** `1. project.* (highest)` → `2. chart.*` → `3. bot.*` → `4. indicators.*` → `5. regime.*`
- **Conflict Resolution:** Namespace-basiert (kein Konflikt durch Prefixes)
- **Validation:** Type-Checks für alle Werte

**Example Merged Context:**
```python
{
    # Project Variables
    "project.my_min_price": 90000.0,
    "project.my_max_leverage": 15,

    # Chart Data
    "chart.price": 95250.0,
    "chart.volume": 125.5,

    # Bot Config
    "bot.leverage": 10,
    "bot.sl_atr_multiplier": 1.5,

    # Indicators
    "atr.value": 550.0,
    "ema_fast.value": 95200.0,

    # Regime
    "regime.id": "R1",
    "regime.name": "Strong Bull"
}
```

**Tests:**
- `test_context_builder.py` - Multi-source merge tests

---

### 2.2 CEL Engine Context Integration (1.5h)

**Deliverables:**
- `src/core/tradingbot/cel_engine.py` (MODIFIED)

**New Method:**
```python
class CELEngine:
    def evaluate_with_sources(
        self,
        expression: str,
        chart: ChartWindow,
        bot: BotConfig,
        project_vars: ProjectVariables,
        indicators: dict,
        regime: dict
    ) -> Any:
        """Evaluate CEL expression with multi-source context."""
        context = self.context_builder.build(chart, bot, project_vars, indicators, regime)
        return self.evaluate(expression, context)
```

**Changes:**
- ✅ `evaluate()` behält alte Signatur (Backward Compatibility)
- ✅ `evaluate_with_sources()` nutzt `ContextBuilder`
- ✅ Caching berücksichtigt alle Context-Sources (`cache_key = hash(expression + sources)`)

**Tests:**
- `test_cel_engine_variables.py` - Context integration tests

---

## 📋 Phase 3: Variable Manager UI (6-8h)

### 3.1 Variable Manager Dialog (3h)

**Deliverables:**
- `src/ui/dialogs/variable_manager_dialog.py`

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│  Variable Manager                                [x]     │
├─────────────────────────────────────────────────────────┤
│  🔍 Search: [____________]  Category: [All ▼]           │
├────────────────────────────────┬────────────────────────┤
│ Name           │ Type  │ Value │ Variable Editor        │
│────────────────┼───────┼───────│                        │
│ my_min_price   │ float │ 90000 │ Name: my_min_price     │
│ my_max_leverage│ int   │ 15    │ Type: [float ▼]        │
│ my_atrp_thres..│ float │ 0.5   │ Value: [90000.0]       │
│ my_session_sta.│ string│ 08:00 │ Category: [Entry Rules]│
│ my_allow_shorts│ bool  │ false │ Description:           │
│                │       │       │ [Minimum BTC Preis für]│
│                │       │       │ [Entry                ]│
│                │       │       │                        │
│                │       │       │ [Save] [Cancel]        │
├────────────────────────────────┴────────────────────────┤
│ [+ New] [✏️ Edit] [🗑️ Delete] [Import] [Export]         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Live-Suche mit Highlighting
- ✅ Double-Click zum Bearbeiten
- ✅ Context Menu (Copy, Paste, Duplicate, Delete)
- ✅ Drag & Drop zum CEL Editor (Insert Variable)
- ✅ Keyboard Shortcuts (Ctrl+N, Del, Ctrl+D)

**Tests:**
- Manual UI Test - Variable CRUD Operations

---

### 3.2 Variable Editor Widget (2h)

**Deliverables:**
- `src/ui/widgets/variable_editor_widget.py`

**Fields:**
- `QLineEdit` - Variable Name (validation: `^[a-z_][a-z0-9_]*$`)
- `QComboBox` - Type Selection (float, int, string, bool, array)
- Type-Specific Input:
  - `QDoubleSpinBox` for float
  - `QSpinBox` for int
  - `QLineEdit` for string
  - `QCheckBox` for bool
  - `QPlainTextEdit` (JSON) for array
- `QLineEdit` - Category (Autocomplete)
- `QTextEdit` - Description
- `QPushButton` - Save/Cancel

**Validation:**
- ✅ Name: snake_case, no reserved keywords
- ✅ Type: Valid VariableType Enum
- ✅ Value: Type-specific validation
- ✅ Real-time Feedback (Red border on invalid)

**Tests:**
- Manual UI Test - Input Validation

---

### 3.3 CEL Editor Integration (2h)

**Deliverables:**
- `src/ui/windows/cel_editor/main_window.py` (MODIFIED)

**Changes:**
- ✅ **Menu:** Tools → Variable Manager (Ctrl+Shift+V)
- ✅ **Sidebar:** Variable Inspector Panel (Dockable)
  - Shows: chart.*, bot.*, project.*, indicators.*, regime.*
  - Collapsible Tree View
- ✅ **Statusbar:** Variable Count ("Variables: 12 project, 8 chart, 15 bot")
- ✅ **Signals:**
  - `variable_added` → Update Autocomplete
  - `variable_changed` → Re-validate CEL Code
  - `variable_deleted` → Check Dependencies

**Tests:**
- Manual UI Test - Variable Manager Integration

---

### 3.4 Autocomplete für Variablen (1.5h)

**Deliverables:**
- `src/ui/widgets/cel_editor_widget.py` (MODIFIED)

**Changes:**
- ✅ Load Variablen aus `VariableStorage`
- ✅ Format: `project.my_var [float]` (with type info)
- ✅ Auto-Update bei Variable-Änderungen
- ✅ Namespace-basierte Gruppierung

**Completion Trigger:**
- Nach `project.` → Zeige alle `project.*`
- Nach `chart.` → Zeige alle `chart.*`
- Nach `bot.` → Zeige alle `bot.*`
- Fuzzy-Matching für schnelle Suche

**Tests:**
- Manual UI Test - Autocomplete Functionality

---

## 📋 Phase 4: Advanced Features (4-6h) ⭐ OPTIONAL

### 4.1 Variable Dependency Graph (2h)

**Deliverables:**
- `src/core/tradingbot/cel/variable_dependency.py`

**Use Cases:**
- ✅ Vor Variable löschen: Warnung "Variable wird in 3 Rules verwendet"
- ✅ Variable Inspector: Zeige Usages pro Variable
- ✅ Dependency Graph Visualization (optional)

---

### 4.2 Import/Export Variable-Sets (1.5h)

**Features:**
- ✅ Export ausgewählter Variablen als JSON
- ✅ Import mit Merge-Optionen (Overwrite, Skip, Rename)
- ✅ Template-Sets (z.B. "BTC Scalping Variables")

---

### 4.3 Variable Inspector (Live-Werte) (2h)

**Features:**
- ✅ Real-time Updates während Bot läuft
- ✅ Highlight geänderte Werte (Farb-Fade-Animation)
- ✅ Copy Value to Clipboard
- ✅ Set Watchpoints (Alert bei Wert-Änderung)

---

## 📋 Phase 5: Testing & Documentation (3-4h)

### 5.1 Unit Tests für Core (2h)

**Deliverables:**
- `tests/unit/test_variable_models.py` (~200 LOC)
- `tests/unit/test_variable_storage.py` (~250 LOC)
- `tests/unit/test_chart_data_provider.py` (~150 LOC)
- `tests/unit/test_bot_config_provider.py` (~150 LOC)
- `tests/unit/test_context_builder.py` (~200 LOC)
- `tests/unit/test_cel_engine_variables.py` (~150 LOC)

**Coverage Target:** >85%

---

### 5.2 Integration Tests (1h)

**Test Scenarios:**
1. Variable erstellen → In CEL verwenden → Evaluieren → Ergebnis prüfen
2. Chart Data → CEL Context → Evaluation → chart.price verfügbar
3. Bot Config ändern → Context Update → CEL Re-Evaluation
4. Variable löschen → Dependency Check → Warnung anzeigen
5. Import Variable-Set → Merge → Alle Variablen verfügbar

---

### 5.3 Help Documentation Update (1h)

**Deliverables:**
- `help/CEL_Variables_Guide.md` (UPDATE - Status zu "Implemented")
- `help/Variable_Manager_Guide.md` (NEU - UI Screenshots + Workflows)
- `04_Knowledgbase/CEL_Variables_Architecture.md` (NEU - Technical Deep-Dive)

---

## 📂 File Structure

### Neue Dateien (21)

**Core:**
- `src/core/tradingbot/cel/variable_models.py`
- `src/core/tradingbot/cel/variable_storage.py`
- `src/core/tradingbot/cel/providers/__init__.py`
- `src/core/tradingbot/cel/providers/chart_data_provider.py`
- `src/core/tradingbot/cel/providers/bot_config_provider.py`
- `src/core/tradingbot/cel/context_builder.py`
- `src/core/tradingbot/cel/variable_dependency.py`

**UI:**
- `src/ui/dialogs/variable_manager_dialog.py`
- `src/ui/widgets/variable_editor_widget.py`
- `src/ui/widgets/variable_inspector_widget.py`

**Schema & Examples:**
- `schema/cel_variables.schema.json`
- `examples/.cel_variables.example.json`

**Tests:**
- `tests/unit/test_variable_models.py`
- `tests/unit/test_variable_storage.py`
- `tests/unit/test_chart_data_provider.py`
- `tests/unit/test_bot_config_provider.py`
- `tests/unit/test_context_builder.py`
- `tests/unit/test_cel_engine_variables.py`
- `tests/unit/test_variable_dependency.py`
- `tests/integration/test_variable_workflows.py`

**Documentation:**
- `help/Variable_Manager_Guide.md`
- `04_Knowledgbase/CEL_Variables_Architecture.md`

### Geänderte Dateien (3)

- `src/core/tradingbot/cel_engine.py`
- `src/ui/windows/cel_editor/main_window.py`
- `src/ui/widgets/cel_editor_widget.py`

### Config-Dateien

- `.cel_variables.json` (per-project, NOT committed)
- `.cel_variables.example.json` (template, committed)

---

## ⏱️ Zeitschätzung

| Phase | Aufwand | Status | Priorität |
|-------|---------|--------|-----------|
| Phase 1: Core Architecture | 4-6h | Pending | ⭐⭐⭐ High |
| Phase 2: CEL Integration | 3-4h | Pending | ⭐⭐⭐ High |
| Phase 3: UI Development | 6-8h | Pending | ⭐⭐⭐ High |
| Phase 4: Advanced Features | 4-6h | Pending | ⭐ Low (Optional) |
| Phase 5: Testing & Docs | 3-4h | Pending | ⭐⭐ Medium |
| **TOTAL (ohne Phase 4)** | **16-22h** | | **MVP** |
| **TOTAL (mit Phase 4)** | **20-28h** | | **Complete** |

**Empfehlung:** Start mit Phase 1-3 (MVP), Add Phase 4 später basierend auf User-Feedback

---

## 🚨 Risiken & Mitigation

### ⚠️ High Risk

**Risk:** Chart Data Access
**Description:** ChartWindow API könnte nicht direkt Candle-Daten exportieren
**Mitigation:** Fallback via `ChartDataHelper` oder `ChartBridge`
**Probability:** Medium | **Impact:** Medium

---

### ⚠️ Medium Risk

**Risk:** Performance bei vielen Variablen
**Description:** >100 Projekt-Variablen könnten Autocomplete verlangsamen
**Mitigation:** Lazy-Loading, Virtual List, Indexing mit Caching
**Probability:** Low | **Impact:** Medium

---

### ⚠️ Low Risk

**Risk:** Namespace-Kollisionen
**Description:** User erstellt Variable "chart" die mit chart.* kollidiert
**Mitigation:** Reserved Keywords Validation, Prefix-Check
**Probability:** Low | **Impact:** Low

---

## ✅ Success Criteria

### Phase 1
- ✅ `.cel_variables.json` kann geladen/gespeichert werden
- ✅ Variablen mit allen Typen (float, int, string, bool, array) funktionieren
- ✅ Chart-Daten (chart.price, etc.) sind in CEL verfügbar
- ✅ Bot-Config (bot.leverage, etc.) ist in CEL verfügbar

### Phase 2
- ✅ CEL Engine evaluiert Expressions mit allen Variablen-Sources
- ✅ Context-Merge funktioniert ohne Konflikte
- ✅ Backward Compatibility: Alte `evaluate()` API funktioniert

### Phase 3
- ✅ Variable Manager UI zeigt alle Variablen an
- ✅ CRUD-Operationen funktionieren
- ✅ Autocomplete zeigt alle project.* Variablen
- ✅ Validation verhindert ungültige Variablen

### Phase 5
- ✅ >85% Code Coverage für Core-Module
- ✅ Integration Tests für alle Workflows passed
- ✅ Help Documentation vollständig und aktuell

---

## 🚀 Next Steps

### Immediate
1. ✅ Review dieses Plans mit User
2. ❓ Fragen klären (z.B. ChartWindow API für Candle-Daten)
3. 🔨 Start Phase 1.1: JSON Schema Design

### Before Start
- ❓ Prüfe ChartWindow Interface für Datenzugriff
- ❓ Prüfe BotConfig Struktur (Entry Weights, LLM Settings)
- 🎨 Erstelle UI Mockup für Variable Manager
- 💬 Diskutiere Namespace-Konvention (chart.*, bot.*, project.*)

---

**Erstellt:** 2026-01-28
**Version:** 1.0
**Status:** 📋 Planning → Bereit für Phase 1 Start
**Autor:** Claude Code (OrderPilot-AI Development Team)
