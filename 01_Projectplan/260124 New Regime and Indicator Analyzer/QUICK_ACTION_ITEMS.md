# ⚡ Quick Action Items - Regime Refactoring

**Date:** 2026-01-24
**Status:** 🔴 CRITICAL - 97.2% INCOMPLETE

> See `FINAL_REVIEW_EXECUTIVE_SUMMARY.md` for full review.

---

## 🚨 TOP 5 BLOCKERS (Fix This Week)

### 1. 🔴 Implement Optuna RegimeOptimizer
**Status:** NOT STARTED
**Impact:** Users stuck with 9-hour Grid Search instead of 2-minute TPE
**File:** Create `/src/core/regime_optimizer.py`
**Reference:** `/src/core/simulator/optimization_bayesian.py` (working example)

```python
# Required Implementation:
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import HyperbandPruner

class RegimeOptimizer:
    def optimize(self, n_trials=150):
        study = optuna.create_study(
            sampler=TPESampler(multivariate=True),
            pruner=HyperbandPruner()
        )
        study.optimize(self.objective, n_trials=n_trials)
```

**Time:** 6 hours
**Priority:** 🔴 CRITICAL

---

### 2. 🔴 Delete Old Grid Search Code
**Status:** STILL IN USE
**Impact:** 270x slower than required
**File:** `/src/ui/threads/regime_optimization_thread.py` lines 175-550
**Action:** DELETE or disable this entire file

```bash
# Current (WRONG):
for combo in product(*param_values):  # ❌ 303,750 combinations

# Required:
study.optimize(objective, n_trials=150)  # ✅ 150 trials
```

**Time:** 1 hour
**Priority:** 🔴 CRITICAL

---

### 3. 🔴 Store Bar-Indices in Stufe-1 Output
**Status:** NOT IMPLEMENTED
**Impact:** Stufe-2 cannot filter bars by regime (workflow broken)
**File:** Modify `RegimeOptimizer._evaluate_params()`

```python
# Required in optimized_regime_BTCUSDT_5m.json:
"regime_periods": [
    {
        "regime": "BULL",
        "start_idx": 25,      # ✅ REQUIRED
        "end_idx": 89,        # ✅ REQUIRED
        "bars": 65,
        "bar_indices": [25, 26, 27, ..., 89]  # ✅ CRITICAL FOR STUFE 2
    }
]
```

**Time:** 2 hours
**Priority:** 🔴 BLOCKER

---

### 4. 🔴 Create Minimal Unit Tests
**Status:** ZERO TESTS
**Impact:** Cannot verify correctness
**Files:** Create these 3 test files:

```bash
tests/core/test_regime_optimizer.py
tests/core/test_regime_classification_logic.py
tests/schemas/test_json_schemas.py
```

**Minimum Tests:**
- Test BULL classification: ADX > 25 AND Close > SMA50 > SMA200
- Test BEAR classification: ADX > 25 AND Close < SMA50 < SMA200
- Test SIDEWAYS classification: ADX < 25 AND BB_Width < 0.20
- Test JSON schema validation against examples

**Time:** 4 hours
**Priority:** 🔴 BLOCKER

---

### 5. 🔴 Remove Old UI Tabs
**Status:** STILL PRESENT (causing confusion)
**Impact:** Users see old Grid Search UI
**Action:** DELETE these 3 files:

```bash
src/ui/dialogs/entry_analyzer/entry_analyzer_setup_tab.py
src/ui/dialogs/entry_analyzer/entry_analyzer_presets_tab.py
src/ui/dialogs/entry_analyzer/entry_analyzer_results_tab.py
```

**Time:** 1 hour
**Priority:** 🔴 CRITICAL

---

## 📋 QUICK CHECKLIST

```
WEEK 1 (This Week):
[ ] 1. Implement Optuna RegimeOptimizer (6h)
[ ] 2. Store bar-indices in Stufe-1 output (2h)
[ ] 3. Create RegimeResultsManager (4h)
[ ] 4. Write 3 unit test files (4h)
[ ] 5. Delete old Grid Search code (1h)
[ ] 6. Remove old UI tabs (1h)
TOTAL: ~18 hours

WEEK 2:
[ ] 7. Implement IndicatorSetOptimizer (8h)
[ ] 8. Create IndicatorResultsManager (4h)
[ ] 9. Build Stufe-1 UI tabs (8h)
[ ] 10. Test Stufe-1 end-to-end (2h)
TOTAL: ~22 hours

WEEK 3:
[ ] 11. Build Stufe-2 UI tabs (12h)
[ ] 12. Chart integration (3 colors) (2h)
[ ] 13. Integration tests (2h)
[ ] 14. Code cleanup (2h)
[ ] 15. Update ARCHITECTURE.md (2h)
TOTAL: ~20 hours
```

**TOTAL REMAINING: ~60 hours (2-3 weeks)**

---

## 🎯 MINIMUM VIABLE PRODUCT (Week 1)

To unblock users, deliver this by end of Week 1:

1. ✅ RegimeOptimizer with Optuna TPE (2 min optimization)
2. ✅ Bar-indices stored in output JSON
3. ✅ RegimeResultsManager (sorting, export)
4. ✅ 3 unit tests passing
5. ✅ Old Grid Search disabled

**Result:** Users can run Stufe-1 optimization in 2 minutes instead of 9 hours.

---

## 🔍 HOW TO VERIFY SUCCESS

### Test 1: Optuna TPE Works
```bash
# Run new optimizer on test data
python -m pytest tests/core/test_regime_optimizer.py

# Expected:
# ✅ Completes in ~2 minutes (not 9 hours)
# ✅ Runs 150 trials (not 303,750)
# ✅ Uses TPESampler (not Grid Search)
# ✅ Bar-indices present in output JSON
```

### Test 2: Classification Logic Correct
```bash
python -m pytest tests/core/test_regime_classification_logic.py

# Expected:
# ✅ BULL: ADX > threshold AND Close > SMA_Fast > SMA_Slow
# ✅ BEAR: ADX > threshold AND Close < SMA_Fast < SMA_Slow
# ✅ SIDEWAYS: ADX < threshold AND BB_Width < percentile
```

### Test 3: JSON Valid
```bash
# Validate example files against schemas
python -m pytest tests/schemas/test_json_schemas.py

# Expected:
# ✅ All 4 example JSONs pass schema validation
# ✅ Bar-indices array present in optimized_regime_*.json
```

---

## 📚 REFERENCE DOCS

| Document | Purpose |
|----------|---------|
| `FINAL_REVIEW_EXECUTIVE_SUMMARY.md` | Full review (36/70 score) |
| `CHECKLISTE_Regime_Optimierung_Refactoring.md` | 72 tasks tracker |
| `PERFORMANCE_OPTIMIERUNG.md` | Optuna TPE implementation guide |
| `README_JSON_FORMATE.md` | JSON format specifications |

---

## ⚠️ WARNINGS

1. **DO NOT commit** until minimum viable product works
2. **DO NOT enable** old Grid Search UI (confuses users)
3. **DO NOT skip** unit tests (high risk of bugs)
4. **DO verify** bar-indices are stored (Stufe-2 won't work without them)

---

## 🆘 IF STUCK

**Problem:** Don't know how to implement Optuna TPE?
**Solution:** Copy from `/src/core/simulator/optimization_bayesian.py` (lines 45-120)

**Problem:** How to store bar-indices?
**Solution:** See `examples/STUFE_1_Regime/optimized_regime_BTCUSDT_5m.json` line 169-179

**Problem:** How to test classification logic?
**Solution:** See `tests/core/tradingbot/test_regime_stability.py` for examples

---

**Last Updated:** 2026-01-24
**Estimated Completion:** Week 3 (if starting now)
