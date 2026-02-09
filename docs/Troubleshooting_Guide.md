# Strategy Settings Pipeline - Troubleshooting Guide

**Version:** 2.1
**Date:** 2026-02-08

---

## Common Issues & Solutions

### 1. Schema Validation Errors

**Symptom:**
```
ValidationError: 'kind' is a required property
```

**Cause:** Old v1 JSON without `kind` field.

**Solution:**
```bash
# Option 1: Auto-migration (Legacy Shim)
# The system auto-detects kind and warns you

# Option 2: Manual migration
python migrations/migrate_v1_to_v2.py --input old.json --output new.json

# Option 3: Batch migration
python migrations/migrate_v1_to_v2.py --dir 03_JSON/Trading_Bot --dry-run
python migrations/migrate_v1_to_v2.py --dir 03_JSON/Trading_Bot
```

---

### 2. Entry Expression Fails

**Symptom:**
- Score = 0/100
- Entry disabled in logs

**Cause:** Invalid CEL expression or missing context variables.

**Debug:**
1. Check logs for `CEL validation failed`
2. Use Validate JSON button in UI
3. Double-click strategy → See "Entry Evaluation" section

**Common CEL Errors:**
```
❌ rsi_14 > 70        // Indicator name must match exactly
✅ rsi_14 > 70

❌ trend = 'UP'       // Use == not =
✅ trend == 'UP'

❌ ema20 > ema50      // Underscores required
✅ ema_20 > ema_50
```

**Available Context:**
- `trend`, `volume`, `volatility` (regime state)
- All indicator names (lowercase with underscores)

---

### 3. Score Always 100% ("Bullshit Scores")

**Symptom:** Every strategy shows 100 despite being invalid.

**Cause:** (Fixed in v2.1) Fallback logic.

**If still happening:**
1. Click "✅ Validate JSON" button
2. Check for schema errors
3. Verify `entry_expression` is not empty string
4. Double-click row → Check "Entry Evaluation" errors

---

### 4. Missing Indicators (NaN Values)

**Symptom:**
- Low score (data quality penalty)
- "Missing Indicators" in explainability panel

**Cause:** Indicator calculation failed (insufficient data, invalid params).

**Solution:**
1. Ensure enough candles (50+ for most indicators)
2. Check indicator `params`:
   ```json
   {"period": 20}  // ✅ Correct
   {"Period": 20}  // ❌ Case-sensitive
   ```
3. Review logs for indicator errors

---

### 5. UI Freezes During Score Calculation

**Symptom:** Application becomes unresponsive.

**Cause:** (Fixed in v2.1) Score calculation now uses QThread workers.

**If still freezing:**
- Update to latest code (ThreadWorker integration)
- Check if `_score_worker` is properly initialized
- Verify `ScoreCalculationWorker` import

---

### 6. Regime Not Matched

**Symptom:**
- Regime Match Score = 0/60
- "Matched: ❌ No" in explainability

**Debug:**
1. Double-click strategy → See "Regime Evaluations"
2. Check which regimes passed/failed
3. Verify indicator values vs. regime conditions

**Common Issues:**
- Regime ID mismatch (case-sensitive)
- Indicator not calculated (see #4)
- Condition logic errors

---

### 7. Dialog Won't Load Strategies

**Symptom:** Empty strategy table.

**Check:**
1. JSON files in correct directory (`03_JSON/Trading_Bot/`)
2. Click "🔄 Aktualisieren" button
3. Check logs for load errors
4. Validate JSONs: "✅ Validate JSON" button

---

### 8. Progress Dialog Doesn't Appear

**Symptom:** No progress indicator during score calculation.

**Cause:** Worker thread not starting or `QProgressDialog` not created.

**Solution:**
1. Check `_score_worker` and `_progress_dialog` initialization in `__init__`
2. Verify imports:
   ```python
   from src.ui.dialogs.score_calculation_worker import ScoreCalculationWorker
   from PyQt6.QtWidgets import QProgressDialog
   ```

---

### 9. Cannot Cancel Score Calculation

**Symptom:** Cancel button doesn't work.

**Check:**
1. `_progress_dialog.canceled` signal connected to `_on_score_cancel`
2. `_score_worker.cancel()` is called in handler
3. Worker checks `_is_cancelled` flag in loop

---

### 10. Export Score Report Fails

**Symptom:** JSON export error.

**Common Issues:**
- Invalid file path (special characters)
- No write permissions
- `explain` dict missing (run Calculate Scores first)

**Solution:**
```python
# Ensure explain data exists
if row in self._score_explain_by_row:
    explain = self._score_explain_by_row[row]
else:
    # Run "Calculate Scores" first
```

---

## Diagnostic Checklist

Before reporting bugs, check:

- [ ] All JSONs validated (✅ Validate JSON button)
- [ ] Logs reviewed (`logs/` directory)
- [ ] Explainability panel checked (double-click row)
- [ ] Latest code pulled (`git pull`)
- [ ] Dependencies up to date (`pip install -r requirements.txt`)

---

## Logging

**View logs:**
```bash
cat logs/orderpilot.log | grep "ERROR"
cat logs/orderpilot.log | grep "WARNING"
```

**Increase verbosity:**
```python
# In code:
logging.getLogger("src.core.tradingbot").setLevel(logging.DEBUG)
```

---

## Get Help

1. **Check Documentation:**
   - [`JSON_Format_Spec_v2.1.md`](file:///d:/03_Git/02_Python/07_OrderPilot-AI/docs/JSON_Format_Spec_v2.1.md)
   - [`CEL_Regime_Entry_Pipeline.md`](file:///d:/03_Git/02_Python/07_OrderPilot-AI/docs/CEL_Regime_Entry_Pipeline.md)

2. **Use UI Tools:**
   - ✅ Validate JSON
   - 🔍 Explainability Panel
   - 📋 Copy Error Details

3. **Report Issue:**
   - Attach logs
   - Include JSON file (if possible)
   - Describe steps to reproduce

---

## FAQ

**Q: Can I mix v1 and v2.1 JSONs?**
A: Yes. Legacy Shim auto-detects v1 files (with warning).

**Q: How do I know my JSON is v2.1?**
A: It has `"kind"` and `"schema_version": "2.1.0"`.

**Q: What's the difference between `entry` and `entry_expression`?**
A: `entry_expression` (CEL) is preferred. `entry` (structured conditions) is legacy fallback.

**Q: Why does my score change randomly?**
A: Scores are deterministic. If changing, input data (candles, features) is different.

**Q: Can I edit regime optimization results?**
A: Not recommended. They're generated by backtester. Manual edits may break validation.
