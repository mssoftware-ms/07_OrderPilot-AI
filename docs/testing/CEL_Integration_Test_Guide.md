# CEL Integration Test Guide (Phase 1 + Phase 2)

**Status:** Phase 1 (CEL Editor) + Phase 2 (AI Integration) COMPLETE
**Date:** 2026-01-20
**Components:** CEL Editor, Function Palette, AI Helper, Pattern Integration Widget

---

## 📋 Prerequisites

### 1. Environment Setup

**Required Python Packages:**
```bash
# Verify installations
pip list | grep -E "PyQt6|QScintilla|openai"

# Expected output:
# PyQt6                  6.x.x
# PyQt6-QScintilla       2.x.x
# openai                 1.x.x
```

**Required Environment Variables (Windows 11):**
```powershell
# Check if API key is set
$env:OPENAI_API_KEY

# If not set, add to System Environment Variables:
# 1. Win + X → System → Advanced system settings
# 2. Environment Variables → System variables → New
# 3. Variable name: OPENAI_API_KEY
# 4. Variable value: sk-...your-key...
```

### 2. Application Settings

**Settings → AI Tab Configuration:**
- ✅ AI Features: **Enabled**
- ✅ Default Provider: **OpenAI**
- ✅ OpenAI Model: **gpt-5.2 (GPT-5.2 Latest)**
- ✅ Reasoning Effort: **medium (Balanced)** or higher
- ℹ️ API Key: (should show "Loaded from environment")

---

## 🧪 Test Plan

### Test 1: Component Initialization

**Objective:** Verify all CEL components load without errors

**Steps:**
1. Start application: `python main.py`
2. Navigate to: **Strategy Concept Window** → **Tab 2: Pattern Integration**
3. Verify visible components:
   - ✅ Pattern selection table (left side)
   - ✅ CEL workflow selector (dropdown: Entry/Exit/Before Exit/Update Stop)
   - ✅ CEL editor with dark theme (center)
   - ✅ Function palette with 8 categories (right side)
   - ✅ Toolbar buttons: 🤖 Generate, ✓ Validate, 🔧 Format, 🗑️ Clear

**Expected Result:**
```
✅ All components visible
✅ No error messages in console
✅ Syntax highlighting active (dark theme colors)
✅ Line numbers visible in editor
```

**Screenshot Location:** `docs/testing/screenshots/test1_initialization.png`

---

### Test 2: Pattern Selection & Strategy Mapping

**Objective:** Verify pattern selection loads strategy details

**Steps:**
1. In Pattern table, select: **Pin Bar (Bullish)**
2. Verify right panel shows:
   - ✅ Pattern Name: "Pin Bar (Bullish)"
   - ✅ Category: REVERSAL
   - ✅ Strategy Type: TREND_REVERSAL
   - ✅ Success Rate: ~65%
   - ✅ Risk-Reward: 1:2 minimum
   - ✅ Entry Rules, Exit Rules, Best Practices

**Expected Result:**
```
✅ Strategy details populated
✅ No console errors
✅ Trade Setup Preview shows Stop Loss/Target calculations
```

---

### Test 3: CEL Editor Features

**Objective:** Test editor functionality (autocomplete, validation, formatting)

#### 3.1 Autocomplete Test

**Steps:**
1. Select workflow: **Entry**
2. Type in editor: `rsi`
3. Wait 0.5 seconds (autocomplete threshold = 2 chars)
4. Verify autocomplete shows:
   - `rsi5.value`
   - `rsi7.value`
   - `rsi14.value`
   - `rsi21.value`

**Expected Result:**
```
✅ Autocomplete popup appears
✅ Shows 4 RSI variants
✅ Arrow keys navigate options
✅ Enter key inserts selected item
```

#### 3.2 Syntax Highlighting Test

**Steps:**
1. Type complex expression:
   ```cel
   rsi14.value > 50 && ema34.value > ema89.value && macd_12_26_9.value > macd_12_26_9.signal
   ```
2. Verify color highlighting:
   - **Indicators** (cyan): `rsi14.value`, `ema34.value`, `macd_12_26_9.signal`
   - **Operators** (white): `>`, `&&`
   - **Numbers** (green): `50`

**Expected Result:**
```
✅ Correct color coding
✅ No syntax errors
✅ Readable with dark theme
```

#### 3.3 Validation Test

**Steps:**
1. Enter valid code: `rsi14.value > 50 && close > ema34.value`
2. Click **✓ Validate** button
3. Verify message: "✓ Syntax valid (balanced parentheses)"
4. Enter invalid code: `rsi14.value > 50 && (close > ema34.value`
5. Click **✓ Validate** button again

**Expected Result:**
```
✅ Valid code: Green success message
❌ Invalid code: Red error message "Unbalanced parentheses"
🔴 Error marker on problematic line
```

#### 3.4 Format Test

**Steps:**
1. Enter unformatted code: `rsi14.value>50&&close>ema34.value`
2. Click **🔧 Format** button
3. Verify output: `rsi14.value > 50 && close > ema34.value`

**Expected Result:**
```
✅ Spaces added around operators
✅ Readable formatting
```

---

### Test 4: Function Palette

**Objective:** Test function browser and insertion

#### 4.1 Category Browsing

**Steps:**
1. In Function Palette, expand **Indicators** category
2. Verify items visible:
   - RSI
   - EMA
   - MACD
   - Stochastic K/D
   - ADX
   - Bollinger Bands
   - Volume Ratio

**Expected Result:**
```
✅ All 15+ indicators visible
✅ Each item shows: Name, Code snippet, Description
```

#### 4.2 Search Test

**Steps:**
1. In search box, type: `macd`
2. Verify filtered results show:
   - MACD (under Indicators)
   - MACD Signal (under Indicators)
   - MACD Histogram (under Indicators)
3. Clear search, type: `trade`
4. Verify shows:
   - Is Trade Open (Trading Functions)
   - Entry Price (Trade Variables)
   - Current Price (Trade Variables)
   - All other `trade.*` variables

**Expected Result:**
```
✅ Real-time filtering works
✅ Matches in name, code, AND description
✅ Categories expand when child matches
```

#### 4.3 Insert Function Test

**Steps:**
1. Click on item: **RSI** (`rsi14.value`)
2. Verify description panel shows:
   - Name: RSI
   - Code: `rsi14.value`
   - Description: "Relative Strength Index (0-100)"
3. Double-click item OR click **↑ Insert at Cursor** button
4. Verify `rsi14.value` inserted at cursor position in editor

**Expected Result:**
```
✅ Description panel updates on click
✅ Double-click inserts function
✅ Insert button inserts function
✅ Cursor position maintained
```

---

### Test 5: AI Code Generation (CRITICAL TEST)

**Objective:** Test OpenAI GPT-5.2 integration end-to-end

#### Prerequisites Check:
```powershell
# 1. Verify API key
$env:OPENAI_API_KEY  # Should show: sk-...

# 2. Verify Settings → AI tab
# - AI Enabled: ✅
# - Provider: OpenAI
# - Model: gpt-5.2 (GPT-5.2 Latest)

# 3. Verify internet connection
Test-NetConnection -ComputerName api.openai.com -Port 443
```

#### 5.1 Entry Condition Generation

**Steps:**
1. Select pattern: **Pin Bar (Bullish)**
2. Select workflow: **Entry**
3. Click **🤖 Generate** button
4. Verify progress dialog appears:
   ```
   🤖 Generating ENTRY CEL code with OpenAI GPT-5.2...
   [Progress bar indeterminate]
   ```
5. Wait 5-30 seconds (depends on reasoning_effort)
6. Verify success dialog:
   ```
   ✓ Generated 87 characters!

   Please review and validate.
   ```
7. Verify editor contains generated code (example):
   ```cel
   rsi14.value < 30 && close < bb_20_2.lower && volume_ratio_20.value > 1.2 && adx14.value > 20
   ```

**Expected Result:**
```
✅ Progress dialog shows during generation
✅ Success message shows character count
✅ Generated code is valid CEL syntax
✅ Code matches pattern characteristics:
   - Pin Bar Bullish → Mean reversion entry (RSI < 30)
   - Bollinger Band lower touch
   - Volume confirmation
✅ No API errors in console
```

**Console Log Check:**
```python
# Expected log output:
# INFO - AI Settings loaded: Provider=OpenAI, OpenAI=gpt-5.2
# INFO - Generating CEL code with OpenAI gpt-5.2 (reasoning_effort=medium)
# INFO - Generated 87 chars CEL code (tokens: 1523)
```

#### 5.2 Exit Condition Generation

**Steps:**
1. Select workflow: **Exit**
2. Click **🤖 Generate** button
3. Verify generated code includes exit logic (example):
   ```cel
   rsi14.value > 70 || trade.pnl_pct > 3.0 || stop_hit_long()
   ```

**Expected Result:**
```
✅ Exit conditions appropriate for pattern
✅ Includes take profit OR stop loss logic
```

#### 5.3 Stop Update Logic Generation

**Steps:**
1. Select workflow: **Update Stop**
2. Click **🤖 Generate** button
3. Verify generated code includes trailing stop logic (example):
   ```cel
   trade.pnl_pct > 1.5 && ema21.value > ema50.value
   ```

**Expected Result:**
```
✅ Stop update conditions present
✅ References trade.pnl_pct for profit threshold
✅ May include trend confirmation
```

#### 5.4 Error Handling Test

**Steps:**
1. Temporarily remove OPENAI_API_KEY environment variable:
   ```powershell
   $env:OPENAI_API_KEY = ""
   ```
2. Restart application
3. Click **🤖 Generate** button
4. Verify error message:
   ```
   ❌ AI Generation Failed

   Check:
   • AI enabled in Settings
   • OPENAI_API_KEY set
   • Internet connection
   ```
5. Restore API key and restart

**Expected Result:**
```
✅ Graceful error handling
✅ Clear error message with troubleshooting steps
✅ No application crash
```

---

### Test 6: JSON Export

**Objective:** Verify complete strategy export to JSON

**Steps:**
1. Select pattern: **Pin Bar (Bullish)**
2. Generate CEL code for all 4 workflows:
   - Entry: `rsi14.value < 30 && close < bb_20_2.lower && volume_ratio_20.value > 1.2`
   - Exit: `rsi14.value > 70 || trade.pnl_pct > 3.0`
   - Before Exit: `trade.pnl_pct > 2.0`
   - Update Stop: `trade.pnl_pct > 1.5`
3. Click **💾 Export to CEL** button
4. Verify success message:
   ```
   ✓ Exported to: D:\03_Git\02_Python\07_OrderPilot-AI\03_JSON\Trading_Bot\ptrn_pin_bar_bullish.json
   ```
5. Open exported file and verify structure:
   ```json
   {
     "schema_version": "1.0.0",
     "strategy_type": "PATTERN_BASED",
     "name": "ptrn_pin_bar_bullish",
     "patterns": [
       {
         "id": "PIN_BAR_BULLISH",
         "name": "Pin Bar (Bullish)",
         "category": "REVERSAL"
       }
     ],
     "workflow": {
       "entry": {
         "language": "CEL",
         "expression": "rsi14.value < 30 && close < bb_20_2.lower && volume_ratio_20.value > 1.2",
         "enabled": true
       },
       "exit": {
         "language": "CEL",
         "expression": "rsi14.value > 70 || trade.pnl_pct > 3.0",
         "enabled": true
       },
       "before_exit": {
         "language": "CEL",
         "expression": "trade.pnl_pct > 2.0",
         "enabled": true
       },
       "update_stop": {
         "language": "CEL",
         "expression": "trade.pnl_pct > 1.5",
         "enabled": true
       }
     },
     "metadata": {
       "strategy_type": "TREND_REVERSAL",
       "risk_reward_ratio": "1:2",
       "success_rate": 65.0,
       "timeframes": ["15m", "1h", "4h"],
       "exported_at": "2026-01-20T..."
     }
   }
   ```

**Expected Result:**
```
✅ JSON file created in 03_JSON/Trading_Bot/
✅ Valid JSON syntax (use jsonlint.com or VS Code formatter)
✅ All 4 workflows present
✅ Enabled=true only for non-empty expressions
✅ Metadata includes strategy details
✅ Schema version 1.0.0
```

**Validation Commands:**
```bash
# Validate JSON syntax
python -m json.tool 03_JSON/Trading_Bot/ptrn_pin_bar_bullish.json

# Verify file size
ls -lh 03_JSON/Trading_Bot/ptrn_pin_bar_bullish.json
# Expected: 1-3 KB depending on complexity
```

---

## 🐛 Common Issues & Solutions

### Issue 1: QScintilla Import Error

**Symptom:**
```
ModuleNotFoundError: No module named 'PyQt6.Qsci'
```

**Solution:**
```bash
pip install PyQt6-QScintilla
```

---

### Issue 2: OpenAI API Key Not Found

**Symptom:**
```
WARNING - OPENAI_API_KEY not found in environment variables
```

**Solution:**
1. Check current value:
   ```powershell
   $env:OPENAI_API_KEY
   ```
2. If empty, add to System Environment Variables (requires admin):
   ```powershell
   # Temporary (session only):
   $env:OPENAI_API_KEY = "sk-..."

   # Permanent (System):
   # Win + X → System → Advanced → Environment Variables → System → New
   ```
3. Restart application

---

### Issue 3: AI Generation Timeout

**Symptom:**
```
asyncio.TimeoutError: OpenAI API request timed out
```

**Solution:**
1. Check internet connection:
   ```powershell
   Test-NetConnection -ComputerName api.openai.com -Port 443
   ```
2. Reduce reasoning_effort in Settings → AI → OpenAI:
   - Change from "high" to "medium" or "low"
3. Verify API key has credits:
   - Login to https://platform.openai.com/usage
   - Check remaining credits

---

### Issue 4: JSON Export Permission Error

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '03_JSON/Trading_Bot/...'
```

**Solution:**
1. Close any programs that might have the file open (Excel, text editor)
2. Check folder exists:
   ```bash
   mkdir -p 03_JSON/Trading_Bot
   ```
3. Check write permissions:
   ```bash
   chmod 755 03_JSON/Trading_Bot
   ```

---

### Issue 5: Syntax Highlighting Not Working

**Symptom:**
- All text appears white (no color coding)

**Solution:**
1. Verify lexer is set:
   ```python
   # In cel_editor_widget.py
   self.editor.setLexer(self.lexer)
   ```
2. Check if lexer is None:
   - Restart application
   - Check console for errors during initialization

---

## 📊 Performance Benchmarks

**Expected Performance:**

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Editor initialization | < 500ms | First load |
| Pattern selection | < 100ms | UI update |
| Autocomplete popup | < 200ms | After 2nd char |
| Syntax highlighting | Real-time | Immediate |
| AI generation (low) | 3-8 sec | GPT-5.2 low effort |
| AI generation (medium) | 8-15 sec | GPT-5.2 medium effort |
| AI generation (high) | 15-30 sec | GPT-5.2 high effort |
| JSON export | < 200ms | File write |

**Token Usage (OpenAI):**

| Workflow | Prompt Tokens | Completion Tokens | Total Cost (GPT-5.2) |
|----------|---------------|-------------------|----------------------|
| Entry | ~1,200 | ~150 | $0.02 |
| Exit | ~1,200 | ~100 | $0.015 |
| Before Exit | ~1,200 | ~80 | $0.012 |
| Update Stop | ~1,200 | ~90 | $0.013 |
| **Total** | **~4,800** | **~420** | **~$0.06** |

---

## ✅ Test Checklist

**Phase 1 (CEL Editor):**
- [ ] CEL Lexer initialization
- [ ] Syntax highlighting (10 token types)
- [ ] Autocomplete (100+ functions)
- [ ] Editor UI (4 workflow types)
- [ ] Function Palette (8 categories)
- [ ] Validation button
- [ ] Format button
- [ ] Clear button

**Phase 2 (AI Integration):**
- [ ] Settings loading (QSettings)
- [ ] Model ID extraction
- [ ] Environment variable loading
- [ ] Provider configuration
- [ ] Prompt building
- [ ] OpenAI API call (GPT-5.2)
- [ ] Reasoning effort parameter
- [ ] Markdown cleanup
- [ ] Error handling
- [ ] Progress dialog
- [ ] Success/error messages
- [ ] Code insertion

**Integration:**
- [ ] Pattern selection → Strategy mapping
- [ ] Workflow selector → Editor switching
- [ ] Function palette → Code insertion
- [ ] AI button → Generation → Editor update
- [ ] All 4 workflows → JSON export
- [ ] JSON schema validation
- [ ] File creation in 03_JSON/Trading_Bot/

---

## 📝 Test Results Template

```markdown
## Test Results - CEL Integration (Phase 1 + Phase 2)

**Tester:** [Name]
**Date:** 2026-01-20
**Environment:**
- OS: Windows 11
- Python: 3.11.x
- PyQt6: 6.x.x
- OpenAI SDK: 1.x.x

### Test 1: Component Initialization
- Status: ✅ PASS / ❌ FAIL
- Notes: ...

### Test 2: Pattern Selection
- Status: ✅ PASS / ❌ FAIL
- Notes: ...

### Test 3: CEL Editor Features
- 3.1 Autocomplete: ✅ PASS / ❌ FAIL
- 3.2 Syntax Highlighting: ✅ PASS / ❌ FAIL
- 3.3 Validation: ✅ PASS / ❌ FAIL
- 3.4 Format: ✅ PASS / ❌ FAIL

### Test 4: Function Palette
- 4.1 Category Browsing: ✅ PASS / ❌ FAIL
- 4.2 Search: ✅ PASS / ❌ FAIL
- 4.3 Insert Function: ✅ PASS / ❌ FAIL

### Test 5: AI Code Generation
- 5.1 Entry Generation: ✅ PASS / ❌ FAIL
- 5.2 Exit Generation: ✅ PASS / ❌ FAIL
- 5.3 Stop Update Generation: ✅ PASS / ❌ FAIL
- 5.4 Error Handling: ✅ PASS / ❌ FAIL

**Generated Code Quality:**
- Syntax Valid: ✅ / ❌
- Relevant to Pattern: ✅ / ❌
- Uses Correct Indicators: ✅ / ❌
- Token Count: [tokens]
- Generation Time: [seconds]

### Test 6: JSON Export
- Status: ✅ PASS / ❌ FAIL
- File Created: ✅ / ❌
- Valid JSON: ✅ / ❌
- Correct Schema: ✅ / ❌

### Overall Result
- **Status:** ✅ ALL TESTS PASSED / ⚠️ ISSUES FOUND / ❌ CRITICAL FAILURES
- **Issues Found:** [count]
- **Recommendations:** ...
```

---

## 🎯 Success Criteria

**Phase 1 + Phase 2 is considered SUCCESSFUL if:**

1. ✅ All components initialize without errors
2. ✅ Syntax highlighting works with correct colors
3. ✅ Autocomplete shows 100+ functions
4. ✅ Function palette inserts code correctly
5. ✅ AI generation completes in < 30 seconds
6. ✅ Generated code is syntactically valid CEL
7. ✅ Generated code matches pattern characteristics
8. ✅ JSON export creates valid schema
9. ✅ No application crashes during testing
10. ✅ Console shows no critical errors

**Critical Failures (Block Production Use):**
- ❌ Application crashes on pattern selection
- ❌ AI generation always fails (API error)
- ❌ JSON export creates invalid schema
- ❌ Syntax highlighting completely broken

**Minor Issues (Can Deploy with Warnings):**
- ⚠️ Autocomplete sometimes slow (> 500ms)
- ⚠️ AI generation occasionally times out
- ⚠️ Format button doesn't handle all edge cases

---

## 📞 Support

**Issues/Questions:**
- GitHub Issues: https://github.com/[repo]/issues
- Documentation: `docs/integration/CEL_Integration.md`
- Logs Location: `logs/orderpilot.log`

**Next Steps After Testing:**
1. Document all findings in Test Results Template
2. Report critical failures immediately
3. Create GitHub issues for minor bugs
4. Proceed to Phase 3 (Pattern Library Integration) if all tests pass
