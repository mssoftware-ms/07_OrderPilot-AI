# JSON Entry System - Workflow Update (2026-01-29)

**Version:** 2.0
**Date:** 2026-01-29
**Status:** ✅ Critical Updates - READ THIS FIRST
**Previous Version:** JSON_Entry_System_Complete_Guide.md v1.0

---

## 🚨 CRITICAL CHANGES - Breaking Documentation Updates

This document corrects **critical errors** in the previous documentation regarding the workflow between Entry Analyzer, CEL-Editor, and Trading Bot.

### ⚠️ What Changed?

1. **Entry Analyzer does NOT generate `entry_expression`**
2. **Regime names are DYNAMIC** (from JSON `regimes[].id`), not fixed
3. **`side` parameter is REQUIRED** for Long/Short differentiation
4. **New CEL functions added**: `trigger_regime_analysis()` and `last_closed_regime()`
5. **JSON controls ONLY Entry** - Exit/Stop-Loss/Take-Profit are in Bot code

---

## ✅ Correct Workflow (3 Phases)

### Phase 1: Entry Analyzer → JSON (WITHOUT entry_expression)

```
Entry Analyzer
   ├─> Optimizes Regime Configuration
   │   ├─> Indicators (ADX, RSI, ATR, etc.)
   │   └─> Regimes (with dynamic IDs)
   └─> Saves JSON WITHOUT entry_expression
       └─> Location: 03_JSON/Entry_Analyzer/Regime/<timestamp>_<symbol>_<tf>_#<rank>.json
```

**❌ OLD (WRONG)**:
```json
{
  "entry_expression": "regime == 'EXTREME_BULL' && rsi > 50"
}
```

**✅ NEW (CORRECT)**:
```json
{
  "indicators": [...],
  "regimes": [
    { "id": "STRONG_BULL", "name": "Strong Bull Trend", ... },
    { "id": "STRONG_TF", "name": "Extreme Trend", ... }
  ]
  // ❌ NO entry_expression field!
}
```

**Key Points:**
- ✅ Entry Analyzer generates indicators + regimes
- ❌ NO `entry_expression` in output
- ✅ Regime IDs are dynamic (e.g., "STRONG_BULL", "STRONG_TF")
- ✅ User must add `entry_expression` manually in CEL-Editor

---

### Phase 2: CEL-Editor → Add entry_expression MANUALLY

```
User opens JSON in CEL-Editor
   ├─> Reads regime IDs from regimes[].id
   ├─> Writes entry_expression using CEL
   └─> Saves JSON with entry_expression
```

**❌ OLD (WRONG)** - Fixed regime names:
```json
{
  "entry_expression": "(side == 'long' && regime == 'EXTREME_BULL') || (side == 'short' && regime == 'EXTREME_BEAR')"
}
```

**Problems:**
1. Regime names "EXTREME_BULL", "EXTREME_BEAR" may not exist in JSON
2. Using `regime` instead of `last_closed_regime()`
3. Missing `trigger_regime_analysis()`

**✅ NEW (CORRECT)** - Dynamic regime names from JSON:
```json
{
  "entry_expression": "trigger_regime_analysis() && ((side == 'long' && (last_closed_regime() == 'STRONG_BULL' || last_closed_regime() == 'STRONG_TF')) || (side == 'short' && last_closed_regime() == 'STRONG_BEAR'))"
}
```

**Key Points:**
- ✅ `trigger_regime_analysis()` - Triggers regime update after candle close
- ✅ `last_closed_regime()` - Returns regime of last CLOSED candle (not current)
- ✅ `side == 'long'` / `side == 'short'` - Differentiates Long/Short entry
- ✅ Regime names from JSON `regimes[].id` (e.g., "STRONG_BULL", "STRONG_TF")

---

### Phase 3: Trading Bot → Load JSON + Evaluate CEL

```
Trading Bot
   ├─> JsonEntryLoader.from_files()
   │   └─> Loads JSON with entry_expression
   ├─> JsonEntryScorer.__init__()
   │   └─> Compiles CEL expression (cached)
   └─> JsonEntryScorer.should_enter_long/short()
       ├─> Builds CEL context (features + regime + chart_window + prev_regime)
       ├─> Evaluates CEL expression
       └─> Returns (should_enter, score, reasons)
```

**Key Points:**
- ✅ JSON controls ONLY Entry logic
- ❌ Exit/Stop-Loss/Take-Profit are in Bot code
- ✅ CEL expression evaluated < 1ms per bar
- ✅ Compiled expression cached for performance

---

## 🔧 New CEL Functions (v2.4)

### `trigger_regime_analysis()` - Trigger Regime Update

**Signature:** `trigger_regime_analysis() -> bool`

**What it does:**
1. Triggers regime update on visible chart (in Backtest)
2. In Bot Tab without chart: Returns `false`
3. Ensures regime data is fresh before entry decision

**Usage:**
```javascript
// ✅ CORRECT: Trigger before checking regime
trigger_regime_analysis() && last_closed_regime() == 'STRONG_BULL'

// ❌ WRONG: No trigger - regime might be stale
last_closed_regime() == 'STRONG_BULL'
```

**Context Requirements:**
- Requires `chart_window` in CEL context (with `trigger_regime_update()` method)
- If `chart_window` is `None`: Returns `false` (no error)
- In Bot Tab: `chart_window = None` → function returns `false`

---

### `last_closed_regime()` - Last Closed Candle Regime

**Signature:** `last_closed_regime() -> string`

**What it returns:**
- Regime string of last CLOSED candle (e.g., "STRONG_BULL")
- `"UNKNOWN"` if no data available

**Usage:**
```javascript
// ✅ CORRECT: Dynamic regime names from JSON
last_closed_regime() == 'STRONG_BULL'    // from regimes[].id
last_closed_regime() == 'STRONG_TF'      // from regimes[].id
last_closed_regime() == 'SIDEWAYS'       // from regimes[].id

// ❌ WRONG: Fixed names not in JSON
last_closed_regime() == 'EXTREME_BULL'   // Does not exist in JSON!
last_closed_regime() == 'EXTREME_BEAR'   // Does not exist in JSON!
```

**Context Requirements:**
- Requires `last_closed_candle` dict with `regime` field in CEL context
- Fallbacks:
  1. `last_closed_candle['regime']` (primary)
  2. `chart_data[-2]['regime']` (from history)
  3. `prev_regime` (from context)
  4. `"UNKNOWN"` (default)

---

## 📝 Updated CEL Context Structure

### JsonEntryScorer._build_context() now includes:

```python
context = {
    # Meta
    "side": "long" | "short",  # ← NEW: Long/Short differentiation

    # Price Data
    "close": 49500.0,
    "open": 49450.0,
    "high": 49550.0,
    "low": 49400.0,
    "volume": 1250000.0,

    # Indicators (flat access)
    "rsi": 55.0,
    "adx": 32.0,
    "macd_hist": 0.05,
    "bb_pct": 0.6,
    # ... all other indicators

    # Indicators (nested access for compatibility)
    "rsi14": {"value": 55.0},
    "adx14": {"value": 32.0},
    "macd_obj": {"value": 0.02, "signal": 0.01, "histogram": 0.05},

    # Regime (flat + nested)
    "regime": "STRONG_BULL",  # Current regime
    "regime_obj": {
        "regime": "STRONG_BULL",
        "confidence": 0.85,
        "strength": 0.8,
        "volatility": "MEDIUM"
    },

    # ← NEW: Chart Window Reference
    "chart_window": <ChartWindow> | None,  # For trigger_regime_analysis()

    # ← NEW: Last Closed Candle with Regime
    "last_closed_candle": {
        "regime": "STRONG_BULL"  # For last_closed_regime()
    } | None
}
```

**Changes:**
1. ✅ Added `side` parameter
2. ✅ Added `chart_window` (for `trigger_regime_analysis()`)
3. ✅ Added `last_closed_candle` (for `last_closed_regime()`)

---

## 🎯 Complete Entry Expression Examples

### Example 1: Conservative (Only Strongest Trends)

```javascript
trigger_regime_analysis() &&
side == 'long' &&
last_closed_regime() == 'STRONG_TF'
```

**When it enters:**
- Long only
- Only on STRONG_TF regime (extreme trend)
- After candle close (last_closed_regime)

---

### Example 2: Moderate (Multiple Strong Regimes)

```javascript
trigger_regime_analysis() &&
((side == 'long' && (last_closed_regime() == 'STRONG_BULL' || last_closed_regime() == 'STRONG_TF')) ||
 (side == 'short' && last_closed_regime() == 'STRONG_BEAR'))
```

**When it enters:**
- Long: STRONG_BULL or STRONG_TF
- Short: STRONG_BEAR
- After candle close

---

### Example 3: Indicator Enhanced (Regime + Confirmation)

```javascript
trigger_regime_analysis() &&
((side == 'long' && last_closed_regime() == 'STRONG_BULL' && rsi > 50 && adx > 25) ||
 (side == 'short' && last_closed_regime() == 'STRONG_BEAR' && rsi < 50 && adx > 25))
```

**When it enters:**
- Long: STRONG_BULL + RSI > 50 + ADX > 25
- Short: STRONG_BEAR + RSI < 50 + ADX > 25
- Double confirmation (Regime + Indicators)

---

### Example 4: Mean-Reversion (Trend Exhaustion)

```javascript
trigger_regime_analysis() &&
((side == 'long' && last_closed_regime() == 'BEAR_EXHAUSTION') ||
 (side == 'short' && last_closed_regime() == 'BULL_EXHAUSTION'))
```

**When it enters:**
- Long at BEAR_EXHAUSTION (trend reversal)
- Short at BULL_EXHAUSTION (trend reversal)
- Counter-trend strategy

---

## 🚨 Common Mistakes & Fixes

### ❌ Mistake 1: Using Fixed Regime Names

```javascript
// ❌ WRONG
regime == 'EXTREME_BULL'
```

**Problem:** Regime names are NOT fixed! They come from JSON `regimes[].id`.

**✅ Fix:**
```javascript
// ✅ CORRECT - Names from JSON
last_closed_regime() == 'STRONG_BULL'  // from regimes[].id
```

---

### ❌ Mistake 2: Using `regime` instead of `last_closed_regime()`

```javascript
// ❌ WRONG
regime == 'STRONG_BULL'
```

**Problem:** `regime` is the CURRENT regime (open candle). For entry, you need the LAST CLOSED regime.

**✅ Fix:**
```javascript
// ✅ CORRECT
last_closed_regime() == 'STRONG_BULL'
```

---

### ❌ Mistake 3: No `side` Parameter

```javascript
// ❌ WRONG - Triggers for both Long and Short
last_closed_regime() == 'STRONG_BULL'
```

**Problem:** Entry would trigger for both Long and Short, even though STRONG_BULL is a bull regime.

**✅ Fix:**
```javascript
// ✅ CORRECT - Only Long
side == 'long' && last_closed_regime() == 'STRONG_BULL'
```

---

### ❌ Mistake 4: Missing `trigger_regime_analysis()`

```javascript
// ❌ WRONG - No regime update
side == 'long' && last_closed_regime() == 'STRONG_BULL'
```

**Problem:** Regime data might be stale (in Backtest with Chart).

**✅ Fix:**
```javascript
// ✅ CORRECT - Trigger update first
trigger_regime_analysis() && side == 'long' && last_closed_regime() == 'STRONG_BULL'
```

**Note:** In Bot Tab without chart, `trigger_regime_analysis()` returns `false` - Entry relies on `prev_regime` parameter.

---

### ❌ Mistake 5: Trying to Control Exit/SL/TP in JSON

```json
// ❌ WRONG - Exit is NOT in JSON!
{
  "entry_expression": "...",
  "exit_expression": "...",     // ← NOT SUPPORTED!
  "stop_loss": 2.0,             // ← NOT SUPPORTED!
  "take_profit": 4.0            // ← NOT SUPPORTED!
}
```

**Problem:** JSON controls ONLY Entry! Exit/Stop-Loss/Take-Profit are programmed in the Trading Bot.

**✅ Fix:** Only `entry_expression` in JSON. Exit logic is in Bot code:
- `TriggerExitEngine` for exits
- Position monitoring for SL/TP
- Trailing Stop in Bot logic

---

## 📊 Updated Code Examples

### Loading JSON with entry_expression

```python
from src.core.tradingbot.json_entry_loader import JsonEntryConfig
from src.core.tradingbot.cel_engine import CELEngine
from src.core.tradingbot.json_entry_scorer import JsonEntryScorer

# 1. Load JSON (with entry_expression added manually)
config = JsonEntryConfig.from_files(
    regime_json_path="03_JSON/Entry_Analyzer/Regime/my_strategy.json"
)

# 2. Verify entry_expression exists
if not config.entry_expression:
    raise ValueError("❌ entry_expression missing! Add it manually in CEL-Editor.")

print(f"✅ Entry Expression: {config.entry_expression[:80]}...")

# 3. Initialize CEL Engine
cel_engine = CELEngine()

# 4. Create Scorer (compiles expression)
scorer = JsonEntryScorer(config, cel_engine)

print(f"✅ Scorer ready: {scorer.get_expression_summary()}")
```

---

### Evaluating Entry with New Context

```python
# Build context with NEW fields
context = {
    # Meta
    "side": "long",  # ← NEW: Long/Short

    # Indicators
    "rsi": 55.0,
    "adx": 32.0,
    "macd_hist": 0.05,

    # Regime
    "regime": "STRONG_BULL",

    # ← NEW: Chart window (None in Bot Tab)
    "chart_window": None,

    # ← NEW: Last closed candle regime
    "last_closed_candle": {"regime": "STRONG_BULL"}
}

# Evaluate
should_enter, score, reasons = scorer.should_enter_long(
    features=feature_vector,
    regime=regime_state,
    chart_window=None,           # ← NEW parameter
    prev_regime="STRONG_BULL"    # ← NEW parameter
)

print(f"Entry: {should_enter}, Score: {score}, Reasons: {reasons}")
```

---

## 📚 Updated File Locations

### Corrected Documentation
- ✅ `Help/entry_analyzer/WORKFLOW_KORREKTUR.md` - Critical workflow corrections
- ✅ `Help/entry_analyzer/COMPLETE_REGIME_EXAMPLE.json` - Full working example with CEL
- ✅ `04_Knowledgbase/JSON_ENTRY_WORKFLOW_UPDATE.md` - This document

### Original Documentation (Now Outdated)
- ⚠️ `Help/entry_analyzer/How_to.html` - Contains errors (see WORKFLOW_KORREKTUR.md)
- ⚠️ `04_Knowledgbase/JSON_Entry_System_Complete_Guide.md` - Needs update

### Code Files (Updated)
- ✅ `src/core/tradingbot/json_entry_scorer.py` - Updated with chart_window + prev_regime
- ✅ `src/core/tradingbot/cel_engine.py` - Contains trigger_regime_analysis() + last_closed_regime()
- ✅ `src/ui/widgets/bitunix_trading/bot_tab_control_pipeline.py` - Passes new parameters

---

## 🎯 Migration Checklist

If you have existing JSON Entry configurations, follow these steps:

### Step 1: Check Regime Names
- [ ] Open your JSON file
- [ ] Find `regimes[].id` field
- [ ] Note all regime IDs (e.g., "STRONG_BULL", "STRONG_TF")

### Step 2: Update entry_expression
- [ ] Replace fixed names ("EXTREME_BULL") with JSON regime IDs
- [ ] Add `trigger_regime_analysis() &&` at the start
- [ ] Replace `regime ==` with `last_closed_regime() ==`
- [ ] Add `side == 'long'` or `side == 'short'` checks

### Step 3: Test CEL Expression
```python
from src.core.tradingbot.cel_engine import CELEngine

cel = CELEngine()
context = {
    "side": "long",
    "chart_window": None,
    "last_closed_candle": {"regime": "STRONG_BULL"},
    "rsi": 55, "adx": 32
}

result = cel.evaluate(your_expression, context)
print(f"Entry Signal: {result}")
```

### Step 4: Validate JSON Schema
```python
from src.core.tradingbot.config.validator import SchemaValidator

validator = SchemaValidator()
result = validator.validate_file("your_strategy.json", "regime_optimization")
```

### Step 5: Backtest
- [ ] Test in Entry Analyzer Backtest
- [ ] Verify entry signals occur at candle close
- [ ] Check regime names are correct

---

## 🚀 Quick Start with Corrected Workflow

### 1. Run Entry Analyzer (Generates JSON WITHOUT entry_expression)
```bash
# Entry Analyzer optimizes indicators + regimes
# Output: 03_JSON/Entry_Analyzer/Regime/<timestamp>.json
# ⚠️ NO entry_expression in output!
```

### 2. Open CEL-Editor and Add entry_expression
```json
{
  "regimes": [
    { "id": "STRONG_BULL", ... },
    { "id": "STRONG_TF", ... }
  ],
  "entry_expression": "trigger_regime_analysis() && ((side == 'long' && last_closed_regime() == 'STRONG_BULL') || (side == 'short' && last_closed_regime() == 'STRONG_BEAR'))"
}
```

### 3. Load in Trading Bot
```python
config = JsonEntryConfig.from_files("my_strategy.json")
scorer = JsonEntryScorer(config, cel_engine)
```

### 4. Start Trading
- ✅ Entry signals trigger at candle close
- ✅ Long/Short direction validated via `side` parameter
- ✅ Regime names from JSON `regimes[].id`

---

## 📞 Support & Resources

### Documentation
- **Workflow Correction:** `Help/entry_analyzer/WORKFLOW_KORREKTUR.md`
- **Complete Example:** `Help/entry_analyzer/COMPLETE_REGIME_EXAMPLE.json`
- **CEL Functions:** `04_Knowledgbase/CEL_Functions_Reference_v3.md`
- **This Update:** `04_Knowledgbase/JSON_ENTRY_WORKFLOW_UPDATE.md`

### Code
- **CEL Engine:** `src/core/tradingbot/cel_engine.py`
- **Entry Loader:** `src/core/tradingbot/json_entry_loader.py`
- **Entry Scorer:** `src/core/tradingbot/json_entry_scorer.py`

### Examples
- **Regime JSONs:** `03_JSON/Entry_Analyzer/Regime/`
- **Complete Example:** `Help/entry_analyzer/COMPLETE_REGIME_EXAMPLE.json`
- **Working Regime:** `03_JSON/Entry_Analyzer/Regime/EXAMPLE_WORKING_REGIME.json`

---

**Version History:**
- **v2.0** (2026-01-29): Critical workflow corrections, new CEL functions, updated context
- **v1.0** (2026-01-28): Initial documentation (now outdated)

**Status:** ✅ Production Ready with Corrections
