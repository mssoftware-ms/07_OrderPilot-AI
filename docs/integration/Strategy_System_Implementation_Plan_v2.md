# Strategy System Implementation Plan v2.0
**Status Check & CEL Pattern Editor Integration**

**Datum:** 2026-01-20
**Status:** Aktueller Implementierungsstand analysiert

---

## 📋 EXECUTIVE SUMMARY

Basierend auf Code-Analyse wurden **ZWEI verschiedene Strategie-Systeme** identifiert:

### **TYPE 1: TECHNISCHE STRATEGIEN (Indicator-Based)**
- **Location**: Entry Analyzer Popup
- **Status**: **✅ FAST FERTIG** (User komplettiert mit Testing)
- **Technologie**: Rein technische Indikatoren (RSI, MACD, EMA, Stochastic)
- **KEINE CEL-Skripte benötigt**
- **Workflow**: Einzelne Indikatoren testen → Pro Regime optimieren → Indicator-Sets erstellen → Backtesten → Bot geben

### **TYPE 2: PATTERN-BASIERTE STRATEGIEN (Pattern-Based with CEL)**
- **Location**: Strategy Concept Window
- **Status**: **⚠️ TEILWEISE IMPLEMENTIERT** (CEL Editor fehlt)
- **Technologie**: Chartmuster + CEL-Skripte für komplexe Logik
- **CEL-Skripte ERFORDERLICH** für Entry/Exit/BeforeExit Workflow
- **Benötigt**: CEL Editor mit KI-Integration

---

## 1. AKTUELLER IMPLEMENTIERUNGSSTAND

### 1.1 Entry Analyzer (Technische Strategien)

**File**: `src/ui/dialogs/entry_analyzer_popup.py` (1900+ lines)

#### ✅ VOLLSTÄNDIG IMPLEMENTIERT:

**3 Worker Threads:**
```python
BacktestWorker      # Full history backtesting
CopilotWorker       # AI Copilot analysis
ValidationWorker    # Walk-forward validation
```

**5 Tabs:**
1. **Backtest Setup**: JSON loader, date range, capital, symbol, "Run Backtest" button
2. **Visible Range Analysis**: Current entry analysis
3. **Backtest Results**: Performance summary, trade list
4. **AI Copilot**: AI entry recommendations
5. **Validation**: Walk-forward validation

**Backend-Funktionen:**
```python
_on_run_backtest_clicked()          # Runs backtest with JSON config
_on_load_strategy_clicked()         # Loads JSON strategy config
_on_analyze_current_regime_clicked()  # Analyzes current market regime
_draw_regime_boundaries()           # Draws regime boundaries on chart
_on_optimize_indicators_clicked()   # Starts indicator optimization
_on_optimization_finished()         # Callback after optimization
_on_create_regime_set_clicked()     # Creates regime set from optimization
```

**Indicator Optimization System:**
- Test einzelne Indikatoren mit verschiedenen Parametern (z.B. RSI(10), RSI(12), RSI(14))
- Test pro Regime (TREND_UP, TREND_DOWN, RANGE)
- Finde beste Indikatoren für jedes Regime (long/short entry und exit)
- Erstelle "Indicator Sets" aus besten Performern
- Backtest komplette Indicator-Sets
- Übergebe Sets an Trading Bot

**User-Status**: "Entry analyzer ist so gut wie fertig, den werde ich mit testen selber komplettieren"

---

### 1.2 Strategy Concept Window (Pattern-Basierte Strategien)

**File**: `src/ui/dialogs/strategy_concept_window.py` (287 lines)

#### ✅ IMPLEMENTIERT (Basic Structure):

```python
class StrategyConceptWindow(QDialog):
    """Main window for Pattern-Based Strategy Development."""

    # Signals
    strategy_applied = pyqtSignal(str, dict)
    closed = pyqtSignal()

    # Tabs
    Tab 1: PatternRecognitionWidget (detects patterns in current chart)
    Tab 2: PatternIntegrationWidget (maps patterns to trading strategies)

    # Footer
    "Apply to Bot" button
    Close button
```

**Tab 1: Pattern Recognition Widget**
**File**: `src/ui/widgets/pattern_recognition_widget.py` (954 lines)

**Status**: ✅ **VOLLSTÄNDIG IMPLEMENTIERT**

**Capabilities:**
- Pattern analysis using `PatternService`
- Background thread for async analysis (`PatternAnalysisThread`)
- Database refresh/update capabilities (`PatternUpdateManager`)
- Event bus integration for live data updates
- Pattern matches table (similar historical patterns)
- Drawing patterns on chart
- Export patterns to JSON/CSV

**UI Components:**
```python
# Left Column (30%)
PatternAnalysisSettings       # Window size, similarity threshold, etc.
"Analyze Patterns" button     # Runs pattern recognition
Progress bar + status         # Analysis progress
PatternResultsDisplay         # Analysis summary
Action buttons                # Draw, Clear, Export
Database Management           # Refresh database button

# Right Column (70%)
PatternMatchesTable          # Similar patterns (historical)
```

**Backend Integration:**
```python
PatternService              # Core pattern matching service
ConditionEvaluator          # Evaluates conditions
RegimeDetector              # Detects market regimes
PatternUpdateManager        # Background database updates
```

**Tab 2: Pattern Integration Widget**
**File**: `src/ui/widgets/pattern_integration_widget.py` (440 lines)

**Status**: ⚠️ **BASIC IMPLEMENTATION** (CEL Editor fehlt)

**Current Capabilities:**
- Pattern-strategy mapping table (6 columns)
- Filter by category (REVERSAL, CONTINUATION, SMART_MONEY, etc.)
- Strategy details display (success rate, risk-reward, best practices)
- Trade setup preview (entry, stop-loss, target, expected success)
- "Apply Strategy" button (placeholder - Phase 6)
- "Export to CEL" button (placeholder - Phase 4)

**UI Components:**
```python
# Header
"Pattern-Strategy Integration" label

# Filter
Category filter combo box (All, REVERSAL, CONTINUATION, etc.)

# Table (6 columns)
Pattern Name | Category | Success Rate | Strategy Type | Avg Profit | Phase

# Details
Strategy Details (HTML formatted)
Trade Setup Preview (table with Entry/Stop/Target)

# Actions
"Apply Strategy" button (disabled until selection)
"Export to CEL" button (disabled until selection)
```

**Pattern-Strategy Mappings:**
**File**: `src/strategies/strategy_models.py`

```python
PATTERN_STRATEGIES = {
    "pin_bar_bullish": PatternStrategyMapping(...),
    "pin_bar_bearish": PatternStrategyMapping(...),
    "inside_bar": PatternStrategyMapping(...),
    "engulfing_bullish": PatternStrategyMapping(...),
    "engulfing_bearish": PatternStrategyMapping(...),
    "cup_and_handle": PatternStrategyMapping(...),
    "bull_flag": PatternStrategyMapping(...),
    "double_bottom": PatternStrategyMapping(...),
    # ... more patterns
}
```

#### ❌ NICHT IMPLEMENTIERT (CRITICAL GAPS):

1. **CEL Script Editor** (HAUPTANFORDERUNG)
   - Kein CEL-Code-Editor Widget
   - Keine Syntax-Highlighting für CEL
   - Keine CEL-Validierung
   - Keine CEL-Debugging-Hilfen

2. **KI-Integration für CEL-Code-Generierung**
   - Kein Prompt-Input für KI
   - Keine AI API Integration
   - Kein CEL-Code-Generator
   - Keine Template-Bibliothek

3. **Pattern-Bibliothek aus Chartmuster_Erweitert_2026.md**
   - 50+ Patterns NICHT in UI verfügbar
   - Keine visuellen Pattern-Templates
   - Keine Pattern-Parametrisierung
   - Keine Pattern-Kombinations-Editor

4. **JSON Export mit CEL-Skripten**
   - Export-Button ist Placeholder
   - Kein JSON-Generator mit CEL-Embedding
   - Keine JSON-Schema-Validierung

---

### 1.3 CEL System (Backend)

**Files**: `src/core/tradingbot/cel/*.py`

#### ✅ VOLLSTÄNDIG IMPLEMENTIERT:

**Google CEL Expression Language:**
```python
# Syntax
"close > ema34.value && stoch_5_3_3.k < 20 && volume_ratio_20.value > 1.5"
```

**Two Evaluation Modes:**
```python
# 1. Operator-based (legacy)
{"left": {"indicator_id": "rsi14"}, "op": "gt", "right": {"value": 60}}

# 2. CEL Expressions (new)
{"cel_expression": "rsi14.value > 60 && adx14.value > 25"}
```

**Core Components:**
```python
ConditionEvaluator      # Evaluates single conditions and groups
RegimeDetector          # Detects regimes from JSON config
StrategyRouter          # Routes regimes to strategy sets
StrategySetExecutor     # Applies parameter overrides
enforce_monotonic_stop() # Ensures stop-loss only moves favorably
```

**18 Indicators Implemented:**
```cel
// Moving Averages
sma_20, ema_34, ema_89, wma_50

// Oscillators
rsi14, stoch_5_3_3, cci_20, mfi_14

// Trend
macd_12_26_9, adx14, chop_14

// Volatility
atr_14, bb_20_2

// Volume
volume, volume_ratio_20

// Price
close, price_change, momentum_score, price_strength
```

**8 TA-Lib Patterns Implemented:**
```python
"Hammer", "Doji", "Engulfing", "Harami"
"Morning Star", "Evening Star"
"Three White Soldiers", "Three Black Crows"
```

**Integration in BotController:**
```python
# FLAT state (entry detection) - bot_state_handlers_flat.py
allowed, reason, summary = self.parent._evaluate_rules(
    features,
    pack_types=["risk", "entry"]
)

# MANAGE state (position management) - bot_state_handlers_manage.py
allowed, reason, summary = self.parent._evaluate_rules(
    features,
    pack_types=["exit"]
)

allowed, reason, summary = self.parent._evaluate_rules(
    features,
    pack_types=["update_stop"]
)
```

#### ❌ MISSING Advanced Pattern Functions:

**NOT Implemented (from CEL_Befehle_Liste_v2.md):**
```cel
// Pin Bars
pin_bar_bullish()      # ❌ NOT IMPLEMENTED
pin_bar_bearish()      # ❌ NOT IMPLEMENTED
inverted_hammer()      # ❌ NOT IMPLEMENTED

// Inside Bars
inside_bar()           # ❌ NOT IMPLEMENTED

// Flags
bull_flag()            # ❌ NOT IMPLEMENTED
bear_flag()            # ❌ NOT IMPLEMENTED

// Cup & Handle
cup_and_handle()       # ❌ NOT IMPLEMENTED

// Double Top/Bottom
double_bottom()        # ❌ NOT IMPLEMENTED
double_top()           # ❌ NOT IMPLEMENTED

// Smart Money Concepts
order_block_retest()   # ❌ NOT IMPLEMENTED
fvg_exists()           # ❌ NOT IMPLEMENTED
liquidity_swept()      # ❌ NOT IMPLEMENTED

// Breakouts
breakout_above()       # ❌ NOT IMPLEMENTED
false_breakout()       # ❌ NOT IMPLEMENTED
```

---

### 1.4 Pattern-Bibliothek (Chartmuster_Erweitert_2026.md)

**File**: `01_Projectplan/01_bisher nicht umgesetzt/Chartmuster_Erkennung/weitere patterns/Chartmuster_Erweitert_2026.md` (802 lines)

#### ✅ DOKUMENTIERT (50+ Patterns in 7 Kategorien):

**1. SCALPING (1-5 Min Charts)**
```
EMA(34) + Stochastic(5,3,3) + RSI(5-7) + Pin Bar
Win Rate: 86%
Setup: Price retests EMA(34), Pin Bar forms, Stochastic oversold
```

**2. DAYTRADING (5-60 Min Charts)**
```
Cup & Handle         95% Win Rate, 35-50% Profit
Bull Flag            High Win Rate, 15-25% Profit
Double Bottom        88% Win Rate, 18-25% Profit
Ascending Triangle   83% Win Rate, 25-35% Profit
Engulfing            High Win Rate, 10-20% Profit
```

**3. RANGE TRADING (Seitwärtsmarkt)**
```
Grid Trading         Multiple small profits in range
BB + RSI 70/30       Overbought/Oversold mean reversion
Support/Resistance   Buy near support, sell near resistance
```

**4. BREAKOUT (mit Volume Confirmation)**
```
3-Layer Filter       82-88% Win Rate mit Volume
Volume 150%+ Avg     Essential for valid breakouts
False Breakout Reduction: 56%
```

**5. VOLATILITY SQUEEZE**
```
BB Squeeze-Surge     70-80% Win Rate
BBW < 20%            Extreme consolidation
Entry: Close outside band + Volume spike + MACD confirmation
```

**6. PRICE ACTION**
```
Pin Bar              Wick ≥ 2× Body, rejection signal
Inside Bar           Consolidation after movement
Pin+Inside Combo     Power setup with tighter entry/stop
Engulfing            2-candle reversal pattern
```

**7. HARMONIC PATTERNS**
```
Gartley              Existing implementation
Bat                  70-75% Win Rate, conservative
Butterfly            70-75% Win Rate, aggressive (35-60% profit)
Crab                 70-75% Win Rate, precision (40-70% profit)
```

**8. SMART MONEY CONCEPTS**
```
Liquidity Sweeps     False breakout + rejection
FVG (Fair Value Gap) 3-candle imbalance gap
Order Blocks         Last candle before displacement
3-Act Model          Inducement → Displacement → FVG
```

**Implementation Phases (1-7)**:
```
Phase 1: Scalping Module (High Frequency)
Phase 2: Daytrading Module (Medium Frequency)
Phase 3: Range Trading Module (Conditional)
Phase 4: Breakout Module (Advanced)
Phase 5: Harmonic Module (Precision)
Phase 6: Smart Money Module (Advanced)
Phase 7: Price Action Module (Support)
```

---

## 2. UNTERSCHEIDUNG: TECHNISCHE vs. PATTERN-BASIERTE STRATEGIEN

### 2.1 Naming Conventions (User-Request)

**Vorschlag:**

| Type | Prefix | Example File | Description |
|------|--------|--------------|-------------|
| **Technische Strategien** | `tech_` | `tech_trend_following_conservative.json` | Rein indikatorbasiert, kein CEL |
| **Pattern-Basierte Strategien** | `ptrn_` | `ptrn_pin_bar_ema_scalping.json` | Chartmuster + CEL-Skripte |

**JSON Schema Unterschiede:**

**Technische Strategie (NO CEL):**
```json
{
  "schema_version": "1.0.0",
  "strategy_type": "TECHNICAL",
  "name": "Trend Following Conservative",
  "indicators": [
    {"id": "ema_34", "type": "EMA", "params": {"period": 34}},
    {"id": "rsi14", "type": "RSI", "params": {"period": 14}}
  ],
  "regimes": [
    {"id": "trend_up", "name": "Trend Up", "conditions": {...}}
  ],
  "strategies": [
    {
      "id": "long_entry",
      "entry_conditions": {
        "operator_expression": {
          "left": {"indicator_id": "close"},
          "op": "gt",
          "right": {"indicator_id": "ema_34"}
        }
      }
    }
  ],
  "routing": [
    {"regimes": {"all_of": ["trend_up"]}, "strategy_set_id": "long_set"}
  ]
}
```

**Pattern-Basierte Strategie (WITH CEL):**
```json
{
  "schema_version": "1.0.0",
  "strategy_type": "PATTERN_BASED",
  "name": "Pin Bar EMA Scalping",
  "patterns": [
    {
      "id": "pin_bar_bullish",
      "type": "PIN_BAR",
      "direction": "BULLISH",
      "recognition_script": {
        "language": "CEL",
        "expression": "pin_bar_bullish() && close > ema34.value"
      }
    }
  ],
  "workflow": {
    "entry": {
      "language": "CEL",
      "expression": "pin_bar_bullish() && close > ema34.value && stoch_5_3_3.k < 20 && volume_ratio_20.value > 1.5"
    },
    "exit": {
      "language": "CEL",
      "expression": "close >= (entry_price * 1.02) || rsi14.value > 80"
    },
    "before_exit": {
      "language": "CEL",
      "expression": "trade.pnl_pct >= 1.0 ? (close > ema34.value ? 'TRAIL' : 'HOLD') : 'HOLD'"
    },
    "update_stop": {
      "language": "CEL",
      "expression": "trade.pnl_pct >= 1.0 ? max(trade.stop_price, close * 0.995) : null"
    }
  },
  "risk": {
    "stop_loss": {
      "language": "CEL",
      "expression": "min_of_candles(bars, -5, 'low') - (atr_14.value * 0.5)"
    }
  }
}
```

**Key Unterschiede:**
1. **strategy_type**: `"TECHNICAL"` vs. `"PATTERN_BASED"`
2. **Technische**: Nur `entry_conditions` mit Operator-Expressions
3. **Pattern-Basierte**: `patterns[]` + `workflow{}` mit CEL-Scripts
4. **Dateinamen**: `tech_*.json` vs. `ptrn_*.json`

---

## 3. FEHLENDE KOMPONENTEN FÜR PATTERN-BASIERTE STRATEGIEN

### 3.1 CEL Script Editor (CRITICAL)

**Was fehlt:**
- Kein Code-Editor Widget für CEL
- Keine Syntax-Highlighting
- Keine Autocomplete für CEL-Funktionen
- Keine Validierung/Linting
- Keine Debugging-Hilfen

**Benötigte Komponenten:**

#### **3.1.1 CEL Code Editor Widget**
```python
# File: src/ui/widgets/cel_editor_widget.py

from PyQt6.QtWidgets import QWidget, QTextEdit, QVBoxLayout
from PyQt6.Qsci import QsciScintilla, QsciLexerJSON

class CelEditorWidget(QWidget):
    """CEL Script Editor with syntax highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = QsciScintilla()

        # Syntax highlighting
        lexer = CelLexer()  # Custom lexer for CEL
        self.editor.setLexer(lexer)

        # Autocomplete
        self.api = QsciAPIs(lexer)
        self._load_cel_functions()  # Load CEL function signatures

        # Error markers
        self.error_marker = self.editor.markerDefine(QsciScintilla.Circle)

    def _load_cel_functions(self):
        """Load CEL function signatures for autocomplete."""
        # From CEL_Befehle_Liste_v2.md
        functions = [
            "abs(value)",
            "min(a, b)",
            "max(a, b)",
            "round(value, decimals)",
            "sqrt(value)",
            "pin_bar_bullish()",
            "inside_bar()",
            "volume_ratio_20.value",
            # ... alle 18 Indikatoren + 8 Patterns + Advanced Functions
        ]
        for func in functions:
            self.api.add(func)
        self.api.prepare()

    def validate_cel(self, expression: str) -> bool:
        """Validate CEL expression syntax."""
        # Call backend CEL validator
        try:
            from src.core.tradingbot.cel import ConditionEvaluator
            evaluator = ConditionEvaluator()
            # Dry-run with dummy features
            evaluator.evaluate_cel(expression, features={})
            return True
        except Exception as e:
            self.show_error(str(e))
            return False
```

#### **3.1.2 CEL Function Palette**
```python
# File: src/ui/widgets/cel_function_palette.py

class CelFunctionPalette(QWidget):
    """Draggable palette of CEL functions."""

    function_selected = pyqtSignal(str, str)  # (category, function)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.categories = {
            "Indicators": ["rsi14.value", "macd_12_26_9.value", "ema_34.value"],
            "Patterns": ["pin_bar_bullish()", "inside_bar()", "engulfing()"],
            "Math": ["abs()", "min()", "max()", "round()"],
            "Logic": ["&&", "||", "!", "? :"],
            "Trading": ["is_trade_open()", "is_long()", "stop_hit_long()"]
        }
        self._setup_ui()

    def _setup_ui(self):
        """Create palette with categories and draggable buttons."""
        layout = QVBoxLayout(self)

        for category, functions in self.categories.items():
            group = QGroupBox(category)
            group_layout = QVBoxLayout(group)

            for func in functions:
                btn = QPushButton(func)
                btn.clicked.connect(lambda checked, f=func: self._insert_function(f))
                group_layout.addWidget(btn)

            layout.addWidget(group)

    def _insert_function(self, function: str):
        """Emit signal to insert function into editor."""
        # Extract category
        category = [cat for cat, funcs in self.categories.items() if function in funcs][0]
        self.function_selected.emit(category, function)
```

---

### 3.2 KI-Integration für CEL-Code-Generierung (CRITICAL)

**Was fehlt:**
- Kein Prompt-Input-Feld
- Keine OpenAI/Anthropic API Integration
- Kein CEL-Code-Generator
- Keine Template-Bibliothek

**Benötigte Komponenten:**

#### **3.2.1 AI CEL Generator Widget**
```python
# File: src/ui/widgets/ai_cel_generator.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal
import openai  # oder anthropic

class CelGeneratorThread(QThread):
    """Background thread for AI CEL code generation."""

    code_generated = pyqtSignal(str)  # Generated CEL code
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt: str, pattern_context: dict):
        super().__init__()
        self.prompt = prompt
        self.pattern_context = pattern_context

    def run(self):
        """Generate CEL code from prompt using AI."""
        try:
            # Load CEL command reference
            with open("01_Projectplan/Strategien_Workflow_json/Erweiterung Skript Strategien/CEL_Befehle_Liste_v2.md") as f:
                cel_reference = f.read()

            # Construct AI prompt
            system_prompt = f"""You are a CEL (Common Expression Language) code generator for trading strategies.

Available CEL Functions:
{cel_reference}

Pattern Context:
{self.pattern_context}

Generate CEL code that implements the user's trading logic.
Return ONLY the CEL expression, no explanations.
"""

            # Call AI API (Anthropic Claude)
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            message = client.messages.create(
                model="claude-sonnet-4",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": f"{system_prompt}\n\nUser Request: {self.prompt}"}
                ]
            )

            cel_code = message.content[0].text.strip()

            # Validate generated code
            from src.core.tradingbot.cel import ConditionEvaluator
            evaluator = ConditionEvaluator()
            # Dry-run validation
            evaluator.evaluate_cel(cel_code, features={})  # Will raise if invalid

            self.code_generated.emit(cel_code)

        except Exception as e:
            self.error_occurred.emit(str(e))


class AICelGeneratorWidget(QWidget):
    """AI-powered CEL code generator."""

    cel_code_generated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI with prompt input and generate button."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🤖 AI CEL Code Generator")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffa726;")
        layout.addWidget(header)

        # Prompt input
        prompt_label = QLabel("Beschreibe deine Trading-Logik:")
        layout.addWidget(prompt_label)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            'Beispiel: "Eröffne Long-Position wenn Pin Bar bullish ist, '
            'Preis über EMA(34) liegt, Stochastic unter 20 ist und Volumen über 150% Durchschnitt"'
        )
        self.prompt_input.setMaximumHeight(100)
        layout.addWidget(self.prompt_input)

        # Generate button
        self.generate_btn = QPushButton("🚀 CEL Code Generieren")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffa726;
                color: white;
                padding: 10px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffb74d;
            }
        """)
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_btn)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Generated code display
        code_label = QLabel("Generierter CEL Code:")
        layout.addWidget(code_label)

        self.code_display = QTextEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #26a69a;
                font-family: 'Courier New', monospace;
                border: 1px solid #404040;
            }
        """)
        layout.addWidget(self.code_display)

        # Apply button
        self.apply_btn = QPushButton("✓ CEL Code Übernehmen")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._on_apply_code)
        layout.addWidget(self.apply_btn)

    def _on_generate_clicked(self):
        """Generate CEL code from prompt."""
        prompt = self.prompt_input.toPlainText()
        if not prompt.strip():
            return

        # Show progress
        self.progress.setVisible(True)
        self.generate_btn.setEnabled(False)

        # Start generation thread
        self.generator_thread = CelGeneratorThread(
            prompt=prompt,
            pattern_context=self._get_pattern_context()
        )
        self.generator_thread.code_generated.connect(self._on_code_generated)
        self.generator_thread.error_occurred.connect(self._on_error)
        self.generator_thread.finished.connect(self._on_thread_finished)
        self.generator_thread.start()

    def _get_pattern_context(self) -> dict:
        """Get current pattern context (if any pattern selected)."""
        # TODO: Get from parent PatternIntegrationWidget
        return {
            "pattern_type": "pin_bar_bullish",
            "available_indicators": ["ema_34", "rsi14", "stoch_5_3_3", "volume_ratio_20"]
        }

    def _on_code_generated(self, cel_code: str):
        """Handle generated CEL code."""
        self.code_display.setText(cel_code)
        self.apply_btn.setEnabled(True)

    def _on_error(self, error_msg: str):
        """Handle generation error."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self,
            "CEL Generation Error",
            f"Failed to generate CEL code:\n{error_msg}"
        )

    def _on_thread_finished(self):
        """Thread cleanup."""
        self.progress.setVisible(False)
        self.generate_btn.setEnabled(True)

    def _on_apply_code(self):
        """Apply generated CEL code to strategy."""
        cel_code = self.code_display.toPlainText()
        self.cel_code_generated.emit(cel_code)
```

---

### 3.3 Pattern Library Integration (MEDIUM)

**Was fehlt:**
- 50+ Patterns aus Chartmuster_Erweitert_2026.md NICHT in UI
- Keine Pattern-Template-Auswahl
- Keine Parameter-Konfiguration pro Pattern
- Keine visuelle Pattern-Vorschau

**Benötigte Komponenten:**

#### **3.3.1 Pattern Template Selector**
```python
# File: src/ui/widgets/pattern_template_selector.py

class PatternTemplateSelector(QWidget):
    """Select pattern template from Chartmuster_Erweitert_2026.md library."""

    pattern_selected = pyqtSignal(dict)  # Pattern template data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_library = self._load_pattern_library()
        self._setup_ui()

    def _load_pattern_library(self) -> dict:
        """Parse Chartmuster_Erweitert_2026.md into structured data."""
        # TODO: Parse markdown file and extract patterns
        return {
            "SCALPING": {
                "ema_stoch_pinbar": {
                    "name": "EMA + Stochastic + Pin Bar",
                    "win_rate": 86,
                    "setup": "Price retests EMA(34), Pin Bar forms, Stochastic < 20",
                    "entry_cel": 'pin_bar_bullish() && close > ema34.value && stoch_5_3_3.k < 20',
                    "stop_cel": 'min_of_candles(bars, -5, "low") - (atr_14.value * 0.5)',
                    "target_cel": 'entry_price * 1.015'  # 1.5% target
                }
            },
            "DAYTRADING": {
                "cup_and_handle": {
                    "name": "Cup & Handle",
                    "win_rate": 95,
                    "avg_profit": "35-50%",
                    # ... CEL scripts
                },
                # ... more patterns
            },
            # ... more categories
        }

    def _setup_ui(self):
        """Create pattern selection UI with 7 categories."""
        layout = QVBoxLayout(self)

        # Category tabs
        self.category_tabs = QTabWidget()

        for category, patterns in self.pattern_library.items():
            category_widget = self._create_category_widget(category, patterns)
            self.category_tabs.addTab(category_widget, category)

        layout.addWidget(self.category_tabs)

    def _create_category_widget(self, category: str, patterns: dict):
        """Create widget for one pattern category."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Pattern list
        pattern_list = QListWidget()

        for pattern_id, pattern_data in patterns.items():
            item_text = f"{pattern_data['name']} ({pattern_data['win_rate']}% Win Rate)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, pattern_data)
            pattern_list.addItem(item)

        pattern_list.itemClicked.connect(self._on_pattern_clicked)
        layout.addWidget(pattern_list)

        return widget

    def _on_pattern_clicked(self, item):
        """Handle pattern template selection."""
        pattern_data = item.data(Qt.ItemDataRole.UserRole)
        self.pattern_selected.emit(pattern_data)
```

---

### 3.4 JSON Export mit CEL-Skripten (MEDIUM)

**Was fehlt:**
- Export-Button ist nur Placeholder
- Kein JSON-Generator
- Keine JSON-Schema-Validierung
- Keine Datei-Speicherung

**Benötigte Komponenten:**

#### **3.4.1 CEL Strategy JSON Exporter**
```python
# File: src/core/tradingbot/cel_strategy_exporter.py

from typing import Dict, List
import json
from pathlib import Path

class CelStrategyExporter:
    """Export pattern-based strategy with CEL scripts to JSON."""

    def export_strategy(
        self,
        pattern_id: str,
        pattern_data: dict,
        cel_scripts: dict,
        output_path: str
    ) -> bool:
        """Export strategy to JSON file.

        Args:
            pattern_id: Pattern identifier (e.g., "pin_bar_bullish")
            pattern_data: Pattern metadata (name, win_rate, etc.)
            cel_scripts: Dict with entry/exit/before_exit/update_stop CEL code
            output_path: Output JSON file path

        Returns:
            True if export successful
        """
        strategy_json = {
            "schema_version": "1.0.0",
            "strategy_type": "PATTERN_BASED",
            "name": pattern_data['name'],
            "pattern_id": pattern_id,
            "metadata": {
                "win_rate": pattern_data['win_rate'],
                "avg_profit": pattern_data.get('avg_profit'),
                "category": pattern_data.get('category'),
                "implementation_phase": pattern_data.get('phase', 1)
            },
            "patterns": [
                {
                    "id": pattern_id,
                    "type": pattern_data.get('type', 'CUSTOM'),
                    "recognition_script": {
                        "language": "CEL",
                        "expression": cel_scripts.get('recognition', 'true')
                    }
                }
            ],
            "workflow": {
                "entry": {
                    "language": "CEL",
                    "expression": cel_scripts['entry']
                },
                "exit": {
                    "language": "CEL",
                    "expression": cel_scripts['exit']
                },
                "before_exit": {
                    "language": "CEL",
                    "expression": cel_scripts.get('before_exit', 'HOLD')
                },
                "update_stop": {
                    "language": "CEL",
                    "expression": cel_scripts.get('update_stop', 'null')
                }
            },
            "risk": {
                "stop_loss": {
                    "language": "CEL",
                    "expression": cel_scripts.get('stop_loss', 'entry_price * 0.98')
                }
            }
        }

        # Validate JSON schema
        if not self._validate_schema(strategy_json):
            return False

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(strategy_json, f, indent=2, ensure_ascii=False)

        return True

    def _validate_schema(self, strategy_json: dict) -> bool:
        """Validate JSON against schema."""
        # TODO: Implement JSON schema validation
        required_fields = ["schema_version", "strategy_type", "name", "workflow"]
        return all(field in strategy_json for field in required_fields)
```

---

## 4. IMPLEMENTIERUNGSPLAN (PHASE-BY-PHASE)

### PHASE 1: CEL Editor Integration (CRITICAL - 2-3 Tage)

**Goal**: Add CEL Script Editor to Strategy Concept Window Tab 2

**Tasks**:
1. ✅ Create `CelEditorWidget` with syntax highlighting
2. ✅ Create `CelFunctionPalette` with draggable CEL functions
3. ✅ Add CEL validator (backend integration)
4. ✅ Integrate into `PatternIntegrationWidget` as new tab or section

**File Changes**:
- NEW: `src/ui/widgets/cel_editor_widget.py`
- NEW: `src/ui/widgets/cel_function_palette.py`
- MODIFY: `src/ui/widgets/pattern_integration_widget.py` (add editor section)

**UI Layout (Tab 2 Erweiterung)**:
```
+--------------------------------------------------+
| 🎯 Pattern-Strategy Integration                 |
+--------------------------------------------------+
| [Filter: All Categories ▼]                      |
+--------------------------------------------------+
| Pattern-Strategy Table (existing)                |
+--------------------------------------------------+
| Strategy Details (existing)                      |
+--------------------------------------------------+
| ✨ NEW: CEL Script Editor                       |
| +----------------------------------------------+ |
| | Workflow:          [Entry ▼]                | |
| | +------------------------------------------+ | |
| | | pin_bar_bullish() &&                     | | |
| | | close > ema34.value &&                   | | |
| | | stoch_5_3_3.k < 20 &&                    | | |
| | | volume_ratio_20.value > 1.5              | | |
| | +------------------------------------------+ | |
| | [Validate CEL] [Format Code]                | |
| +----------------------------------------------+ |
+--------------------------------------------------+
| ✨ NEW: CEL Function Palette                    |
| [Indicators] [Patterns] [Math] [Logic] [Trading]|
+--------------------------------------------------+
| [✓ Apply Strategy] [💾 Export to JSON]          |
+--------------------------------------------------+
```

**Acceptance Criteria**:
- ✅ CEL code editor with syntax highlighting works
- ✅ Function palette can insert CEL functions into editor
- ✅ CEL validation shows errors with line numbers
- ✅ Can edit Entry/Exit/BeforeExit/UpdateStop scripts separately

---

### PHASE 2: KI-Integration (CRITICAL - 3-4 Tage)

**Goal**: Add AI-powered CEL code generation from user prompts

**Tasks**:
1. ✅ Create `AICelGeneratorWidget`
2. ✅ Integrate Anthropic Claude API (or OpenAI)
3. ✅ Load CEL_Befehle_Liste_v2.md as context for AI
4. ✅ Add validation for AI-generated code
5. ✅ Integrate into Strategy Concept Window Tab 2

**File Changes**:
- NEW: `src/ui/widgets/ai_cel_generator.py`
- MODIFY: `src/ui/widgets/pattern_integration_widget.py` (add AI generator section)
- MODIFY: `src/core/tradingbot/cel_strategy_exporter.py` (generate JSON from AI code)

**UI Layout (Tab 2 weitere Erweiterung)**:
```
+--------------------------------------------------+
| 🤖 AI CEL Code Generator                        |
+--------------------------------------------------+
| Beschreibe deine Trading-Logik:                  |
| +----------------------------------------------+ |
| | Eröffne Long-Position wenn Pin Bar bullish   | |
| | ist, Preis über EMA(34), Stochastic < 20,    | |
| | und Volumen über 150% Durchschnitt           | |
| +----------------------------------------------+ |
| [🚀 CEL Code Generieren]                         |
+--------------------------------------------------+
| Generierter CEL Code:                            |
| +----------------------------------------------+ |
| | pin_bar_bullish() &&                         | |
| | close > ema34.value &&                       | |
| | stoch_5_3_3.k < 20 &&                        | |
| | volume_ratio_20.value > 1.5                  | |
| +----------------------------------------------+ |
| [✓ CEL Code Übernehmen]                          |
+--------------------------------------------------+
```

**API Integration**:
```python
# Use Anthropic Claude API
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4",
    max_tokens=1000,
    system=f"""CEL Code Generator

Available Functions:
{cel_reference}

Pattern Context:
{pattern_context}
""",
    messages=[{"role": "user", "content": user_prompt}]
)
```

**Acceptance Criteria**:
- ✅ User can enter natural language prompt
- ✅ AI generates valid CEL code
- ✅ Generated code is validated automatically
- ✅ User can apply generated code to strategy
- ✅ Error handling for invalid AI output

---

### PHASE 3: Pattern Library Integration (MEDIUM - 2-3 Tage)

**Goal**: Integrate 50+ patterns from Chartmuster_Erweitert_2026.md

**Tasks**:
1. ✅ Parse Chartmuster_Erweitert_2026.md into structured data
2. ✅ Create `PatternTemplateSelector` widget
3. ✅ Add pattern templates to Strategy Concept Window
4. ✅ Pre-fill CEL editor with template CEL scripts

**File Changes**:
- NEW: `src/ui/widgets/pattern_template_selector.py`
- NEW: `src/strategies/chartmuster_parser.py` (parse markdown)
- MODIFY: `src/ui/dialogs/strategy_concept_window.py` (add template tab)

**UI Layout (Neuer Tab 3)**:
```
+--------------------------------------------------+
| Tab 1: Pattern Recognition                       |
| Tab 2: Pattern Integration (with CEL Editor)     |
| ✨ Tab 3: Pattern Template Library               |
+--------------------------------------------------+
| 📚 Pattern Templates from Chartmuster_2026.md   |
+--------------------------------------------------+
| Categories:                                      |
| [SCALPING] [DAYTRADING] [RANGE] [BREAKOUT]      |
| [VOLATILITY] [PRICE_ACTION] [HARMONIC]          |
| [SMART_MONEY]                                    |
+--------------------------------------------------+
| SCALPING Patterns:                               |
| +----------------------------------------------+ |
| | ○ EMA + Stochastic + Pin Bar (86% Win)       | |
| | ○ Fast Stochastic (5,3,3) Scalping           | |
| +----------------------------------------------+ |
+--------------------------------------------------+
| Selected Pattern: EMA + Stochastic + Pin Bar     |
| +----------------------------------------------+ |
| | Win Rate: 86%                                | |
| | Timeframe: 1-Min                             | |
| | Entry CEL: pin_bar_bullish() && ...         | |
| | Stop CEL: min_of_candles(...) - atr * 0.5  | |
| +----------------------------------------------+ |
| [Use Template] [Customize in Editor]             |
+--------------------------------------------------+
```

**Acceptance Criteria**:
- ✅ All 7 pattern categories visible
- ✅ 50+ patterns loaded from markdown
- ✅ User can select pattern template
- ✅ Template CEL code is pre-filled in editor
- ✅ User can customize template and save

---

### PHASE 4: JSON Export Functionality (MEDIUM - 1-2 Tage)

**Goal**: Export complete strategy with CEL scripts to JSON

**Tasks**:
1. ✅ Implement `CelStrategyExporter`
2. ✅ Add JSON schema validation
3. ✅ Wire "Export to JSON" button
4. ✅ Test JSON compatibility with BotController

**File Changes**:
- NEW: `src/core/tradingbot/cel_strategy_exporter.py`
- MODIFY: `src/ui/widgets/pattern_integration_widget.py` (_on_export_cel method)

**Export Flow**:
```
User clicks "💾 Export to JSON"
  ↓
PatternIntegrationWidget collects:
  - Selected pattern_id
  - CEL scripts (entry/exit/before_exit/update_stop)
  - Pattern metadata
  ↓
CelStrategyExporter.export_strategy()
  - Constructs JSON with PATTERN_BASED schema
  - Validates JSON schema
  - Writes to 03_JSON/Trading_Bot/ptrn_<name>.json
  ↓
Success message + file path shown to user
```

**Acceptance Criteria**:
- ✅ Export creates valid JSON file
- ✅ JSON follows PATTERN_BASED schema
- ✅ BotController can load exported JSON
- ✅ Filename uses `ptrn_` prefix

---

### PHASE 5: Advanced CEL Functions (NICE-TO-HAVE - 3-5 Tage)

**Goal**: Implement missing advanced pattern functions from CEL_Befehle_Liste_v2.md

**Tasks**:
1. ✅ Implement Pin Bar functions:
   - `pin_bar_bullish()`, `pin_bar_bearish()`, `inverted_hammer()`
2. ✅ Implement Inside Bar: `inside_bar()`
3. ✅ Implement Flags: `bull_flag()`, `bear_flag()`
4. ✅ Implement Cup & Handle: `cup_and_handle()`
5. ✅ Implement Double Top/Bottom: `double_bottom()`, `double_top()`
6. ✅ Implement Smart Money: `order_block_retest()`, `fvg_exists()`, `liquidity_swept()`
7. ✅ Implement Breakouts: `breakout_above()`, `false_breakout()`

**File Changes**:
- MODIFY: `src/core/tradingbot/cel/functions.py` (add pattern functions)
- MODIFY: `src/core/tradingbot/cel/evaluator.py` (register new functions)

**Implementation Example**:
```python
# File: src/core/tradingbot/cel/pattern_functions.py

def pin_bar_bullish(bars: list) -> bool:
    """Detect bullish pin bar pattern.

    Criteria:
    - Lower wick >= 2× body height
    - Upper wick <= 0.3× body height
    - Close in upper 1/3 of candle range

    Returns:
        True if bullish pin bar detected
    """
    if len(bars) < 1:
        return False

    last_bar = bars[-1]
    open_price = last_bar['open']
    high = last_bar['high']
    low = last_bar['low']
    close = last_bar['close']

    body = abs(close - open_price)
    lower_wick = min(open_price, close) - low
    upper_wick = high - max(open_price, close)
    candle_range = high - low

    # Criteria checks
    if lower_wick < body * 2:
        return False
    if upper_wick > body * 0.3:
        return False
    if (close - low) / candle_range < 0.66:  # Close in upper 1/3
        return False

    return True


def inside_bar(bars: list) -> bool:
    """Detect inside bar pattern.

    Criteria:
    - Current bar's high <= previous bar's high
    - Current bar's low >= previous bar's low

    Returns:
        True if inside bar detected
    """
    if len(bars) < 2:
        return False

    current = bars[-1]
    previous = bars[-2]

    return (current['high'] <= previous['high'] and
            current['low'] >= previous['low'])


# Register in evaluator
PATTERN_FUNCTIONS = {
    'pin_bar_bullish': pin_bar_bullish,
    'pin_bar_bearish': pin_bar_bearish,
    'inside_bar': inside_bar,
    'inverted_hammer': inverted_hammer,
    'bull_flag': bull_flag,
    'bear_flag': bear_flag,
    'cup_and_handle': cup_and_handle,
    'double_bottom': double_bottom,
    'double_top': double_top,
    'order_block_retest': order_block_retest,
    'fvg_exists': fvg_exists,
    'liquidity_swept': liquidity_swept,
    'breakout_above': breakout_above,
    'false_breakout': false_breakout,
}
```

**Acceptance Criteria**:
- ✅ All 14 advanced pattern functions implemented
- ✅ Functions return correct boolean values
- ✅ CEL evaluator can call these functions
- ✅ AI generator can suggest these functions

---

### PHASE 6: Bot Integration (FINAL - 2-3 Tage)

**Goal**: Wire "Apply to Bot" button to load pattern-based strategy into BotController

**Tasks**:
1. ✅ Implement `_on_apply_strategy()` in PatternIntegrationWidget
2. ✅ Create signal connection to ChartWindow
3. ✅ ChartWindow.bot_controller.load_cel_strategy(json_path)
4. ✅ Test end-to-end: Create strategy → Export JSON → Load in Bot → Execute

**File Changes**:
- MODIFY: `src/ui/widgets/pattern_integration_widget.py` (_on_apply_strategy)
- MODIFY: `src/ui/dialogs/strategy_concept_window.py` (signal routing)
- MODIFY: `src/ui/widgets/chart_window.py` (bot integration)
- MODIFY: `src/core/tradingbot/bot_controller.py` (load_cel_strategy method)

**Integration Flow**:
```
User clicks "✓ Apply Strategy" in Tab 2
  ↓
PatternIntegrationWidget emits strategy_applied signal
  ↓
StrategyConceptWindow.strategy_applied → ChartWindow
  ↓
ChartWindow.apply_pattern_strategy(pattern_type, strategy_data)
  ↓
BotController.load_cel_strategy(strategy_json)
  - Parses JSON
  - Validates CEL scripts
  - Loads into _rulepack
  - Sets active strategy
  ↓
Bot uses CEL scripts for Entry/Exit/BeforeExit/UpdateStop
```

**Acceptance Criteria**:
- ✅ Apply button loads strategy into bot
- ✅ Bot executes CEL scripts correctly
- ✅ Pattern recognition triggers entries
- ✅ Exit/UpdateStop CEL scripts work

---

## 5. ZEITSCHÄTZUNG & PRIORISIERUNG

| Phase | Priority | Effort | Description |
|-------|----------|--------|-------------|
| **Phase 1: CEL Editor** | 🔴 CRITICAL | 2-3 Tage | Add CEL code editor to Strategy Concept |
| **Phase 2: KI-Integration** | 🔴 CRITICAL | 3-4 Tage | AI-powered CEL code generation |
| **Phase 3: Pattern Library** | 🟡 MEDIUM | 2-3 Tage | Integrate 50+ patterns from markdown |
| **Phase 4: JSON Export** | 🟡 MEDIUM | 1-2 Tage | Export strategy with CEL to JSON |
| **Phase 5: Advanced CEL Functions** | 🟢 NICE-TO-HAVE | 3-5 Tage | Implement 14 advanced pattern functions |
| **Phase 6: Bot Integration** | 🔴 CRITICAL | 2-3 Tage | Wire "Apply to Bot" button |

**Total Effort (Critical Path)**: 7-10 Tage
**Total Effort (All Phases)**: 13-20 Tage

---

## 6. RISIKEN & ABHÄNGIGKEITEN

### Risiken:
1. **AI API Kosten**: Anthropic Claude API kostet Geld pro Request
   - **Mitigation**: Caching von AI-Responses, lokale Template-Library
2. **CEL Validation Komplexität**: Komplexe CEL-Ausdrücke schwer zu validieren
   - **Mitigation**: Dry-run mit Dummy-Features, schrittweise Validation
3. **Pattern Detection Accuracy**: Chartmuster-Erkennung kann False Positives haben
   - **Mitigation**: Multi-Confirmation (Volume, Regime, etc.)

### Abhängigkeiten:
- **PyQt6** für UI-Widgets (bereits installiert)
- **QScintilla** für Code-Editor (Syntax-Highlighting)
- **Anthropic API** für KI-Integration (API Key benötigt)
- **Entry Analyzer** fast fertig (User komplettiert)

---

## 7. TESTING-STRATEGIE

### Unit Tests:
```python
# Test CEL code generation
def test_ai_cel_generator():
    prompt = "Long wenn Pin Bar bullish und EMA(34) überschritten"
    expected_output = "pin_bar_bullish() && close > ema34.value"
    # Test AI generation

# Test CEL validation
def test_cel_validator():
    valid_expr = "rsi14.value > 60 && adx14.value > 25"
    assert cel_validator.validate(valid_expr) == True

    invalid_expr = "unknown_function()"
    assert cel_validator.validate(invalid_expr) == False

# Test pattern functions
def test_pin_bar_bullish():
    bars = [
        {'open': 100, 'high': 102, 'low': 95, 'close': 101}  # Pin bar
    ]
    assert pin_bar_bullish(bars) == True
```

### Integration Tests:
```python
# Test end-to-end workflow
def test_strategy_export_and_load():
    # 1. Create strategy in UI
    pattern_widget.select_pattern("pin_bar_bullish")
    cel_code = "pin_bar_bullish() && close > ema34.value"

    # 2. Export to JSON
    exporter.export_strategy(pattern_id, pattern_data, cel_code, output_path)

    # 3. Load in BotController
    bot_controller.load_cel_strategy(output_path)

    # 4. Verify CEL execution
    features = create_test_features()
    allowed, reason = bot_controller._evaluate_rules(features, pack_types=["entry"])
    assert allowed == True  # or False depending on features
```

---

## 8. NÄCHSTE SCHRITTE (ACTION ITEMS)

### IMMEDIATE (Diese Woche):

1. **User-Feedback einholen**:
   - ✅ Stimmt der Plan mit Anforderungen überein?
   - ✅ Priorisierung OK (Phase 1 → 2 → 6)?
   - ✅ Naming Conventions (`tech_*.json` vs. `ptrn_*.json`) OK?

2. **Phase 1 starten: CEL Editor Widget**:
   - ✅ Install QScintilla: `pip install QScintilla`
   - ✅ Create `src/ui/widgets/cel_editor_widget.py`
   - ✅ Create `src/ui/widgets/cel_function_palette.py`
   - ✅ Integrate into `pattern_integration_widget.py`

3. **Anthropic API Key Setup**:
   - ✅ Generate API Key: https://console.anthropic.com/
   - ✅ Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
   - ✅ Test API connection

### NEXT WEEK:

4. **Phase 2: KI-Integration**:
   - ✅ Create `src/ui/widgets/ai_cel_generator.py`
   - ✅ Test AI code generation with sample prompts
   - ✅ Validate AI-generated CEL code

5. **Phase 4: JSON Export**:
   - ✅ Create `src/core/tradingbot/cel_strategy_exporter.py`
   - ✅ Test JSON export/import cycle

6. **Phase 6: Bot Integration**:
   - ✅ Wire "Apply to Bot" button
   - ✅ End-to-end testing

---

## 9. OFFENE FRAGEN

1. **Entry Analyzer Status**:
   - ✅ User komplettiert selbst mit Testing
   - ❓ Gibt es fehlende Features die wir wissen sollten?

2. **Strategy Settings Dialog**:
   - ✅ Bleibt im Code (auch wenn redundant)
   - ❓ Soll er entfernt werden oder andere Funktion bekommen?

3. **Naming Conventions**:
   - ✅ `tech_*.json` für technische Strategien
   - ✅ `ptrn_*.json` für pattern-basierte Strategien
   - ❓ OK oder andere Vorschläge?

4. **AI Provider**:
   - Vorschlag: Anthropic Claude (Sonnet 4)
   - Alternative: OpenAI GPT-4
   - ❓ Präferenz?

---

## 10. ZUSAMMENFASSUNG

### Was ist FERTIG:
- ✅ Entry Analyzer (fast komplett - User finishing)
- ✅ Pattern Recognition Widget (vollständig)
- ✅ Pattern Integration Widget (Basis-UI)
- ✅ CEL Backend (18 Indikatoren + 8 Patterns)
- ✅ Bot Integration (CEL RulePacks in FLAT/MANAGE states)

### Was FEHLT (CRITICAL):
- ❌ CEL Script Editor Widget
- ❌ KI-Integration für CEL-Code-Generierung
- ❌ JSON Export mit CEL-Skripten
- ❌ "Apply to Bot" Button Verdrahtung

### Was FEHLT (NICE-TO-HAVE):
- ❌ Pattern Library UI (50+ Patterns)
- ❌ Advanced CEL Functions (14 Funktionen)

### CRITICAL PATH (7-10 Tage):
```
Phase 1 (CEL Editor) → Phase 2 (KI) → Phase 6 (Bot Integration)
```

---

**Status**: READY FOR USER APPROVAL & IMPLEMENTATION START
**Nächster Schritt**: User-Feedback zu Plan einholen, dann Phase 1 beginnen
