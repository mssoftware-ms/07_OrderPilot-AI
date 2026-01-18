# Complete Workflow Testing Guide

## Overview

This guide covers testing the complete regime-based JSON strategy system from indicator optimization through bot execution.

**Workflow Steps:**
1. Indicator Optimization → Parameter search for best indicators per regime
2. Regime Set Creation → Combine best indicators into regime-specific sets
3. Backtesting → Validate strategy performance
4. Bot Start → Live/Paper trading with dynamic regime switching

---

## Prerequisites

### 1. Environment Setup

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/WSL
# or
.venv\Scripts\activate  # Windows

# Verify dependencies
pip list | grep -E "(pandas|numpy|PyQt6|alpaca)"
```

### 2. Required Files

✅ **Indicator Catalog**: `config/indicator_catalog.yaml` (28 indicators)
✅ **CLI Optimizer**: `tools/optimize_indicators.py`
✅ **JSON Configs Directory**: `03_JSON/Trading_Bot/`
✅ **Sample Configs**: `trend_following_conservative.json`, etc.

### 3. Market Data

- **Paper Trading**: Use Alpaca Paper account (free)
- **Historical Data**: Ensure data loader can fetch OHLCV data
- **Symbols**: Test with liquid symbols (SPY, AAPL, BTC/USD)

---

## Phase 1: Indicator Optimization Testing

### Test 1.1: CLI Optimizer - Single Regime

**Objective**: Verify CLI optimizer generates valid JSON configs for a single regime

**Steps:**
```bash
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI

# Test R1_trend (trend regime)
python tools/optimize_indicators.py \
    --regime R1_trend \
    --preset balanced \
    --output-dir 03_JSON/Trading_Bot

# Expected Output:
# - File created: 03_JSON/Trading_Bot/optimized_r1_trend.json
# - Log shows: "Total indicators: X", "Total combinations: Y"
# - No errors or exceptions
```

**Validation:**
```bash
# Check JSON is valid
python -m json.tool 03_JSON/Trading_Bot/optimized_r1_trend.json > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"

# Verify structure
cat 03_JSON/Trading_Bot/optimized_r1_trend.json | grep -E "(schema_version|indicators|regimes|strategies|routing)"
```

**Expected Results:**
- ✅ JSON file exists
- ✅ schema_version: "1.0.0"
- ✅ indicators array not empty
- ✅ regimes array has 1 entry (R1_trend)
- ✅ strategies array not empty
- ✅ routing array maps R1_trend to strategy set

### Test 1.2: CLI Optimizer - All Regimes

**Objective**: Batch optimization for all 4 regimes

**Steps:**
```bash
python tools/optimize_indicators.py \
    --all-regimes \
    --preset quick_scan \
    --output-dir 03_JSON/Trading_Bot

# Expected Output:
# - 4 JSON files created:
#   - optimized_r1_trend.json
#   - optimized_r2_range.json
#   - optimized_r3_breakout.json
#   - optimized_r4_volatile.json
```

**Validation:**
```bash
# Count generated files
ls -1 03_JSON/Trading_Bot/optimized_*.json | wc -l
# Expected: 4

# Verify each regime has different indicators
for file in 03_JSON/Trading_Bot/optimized_*.json; do
    echo "=== $file ==="
    grep -oP '"type"\s*:\s*"\K[^"]+' "$file" | sort -u
done
```

**Expected Results:**
- ✅ 4 JSON files created
- ✅ Each file has regime-specific indicators (e.g., MACD for trend, RSI for range)
- ✅ All files have valid schema

### Test 1.3: UI Indicator Optimization Thread

**Objective**: Verify UI thread uses CLI orchestrator correctly

**Steps:**
1. Launch OrderPilot-AI application
2. Open Entry Analyzer popup (button in Trading Tab)
3. Navigate to "Indicator Optimization" tab
4. Select indicators: RSI, MACD, ADX
5. Set preset: "balanced"
6. Click "🚀 Optimize Indicators"

**Expected Behavior:**
- ✅ Progress bar shows regime processing (R1_trend → R2_range → R3_breakout → R4_volatile)
- ✅ Progress messages: "Optimizing R1_trend (1/4)...", etc.
- ✅ Results table populates with scores
- ✅ Each indicator has entries for all 4 regimes
- ✅ Scores are in range 0-100
- ✅ Win rate, profit factor, sharpe ratio displayed

**Log Verification:**
```bash
# Check logs for CLI orchestrator usage
tail -f logs/orderpilot.log | grep -E "(CLI-based optimization|IndicatorOptimizationOrchestrator|Running optimization for)"
```

**Expected Log Output:**
```
INFO Starting CLI-based optimization for 3 indicators
INFO Running optimization for R1_trend with preset 'balanced'
INFO Running optimization for R2_range with preset 'balanced'
INFO Running optimization for R3_breakout with preset 'balanced'
INFO Running optimization for R4_volatile with preset 'balanced'
INFO Optimization completed: XX total results
```

---

## Phase 2: Regime Set Creation Testing

### Test 2.1: Regime Set Builder - UI

**Objective**: Create regime set from optimization results

**Steps:**
1. In Entry Analyzer, after optimization completes
2. Click "📦 Create Regime Set" button
3. Review auto-selected top indicators per regime
4. Click "Generate JSON Config"

**Expected Behavior:**
- ✅ Dialog shows top 3 indicators per regime
- ✅ Weights are displayed (normalized scores)
- ✅ JSON config preview shown
- ✅ File saved to `03_JSON/Trading_Bot/regime_set_YYYYMMDD_HHMMSS.json`

**Validation:**
```bash
# Check generated regime set
latest_file=$(ls -t 03_JSON/Trading_Bot/regime_set_*.json | head -1)
echo "Latest regime set: $latest_file"

# Verify structure
python -c "
import json
with open('$latest_file') as f:
    config = json.load(f)
    print(f'Regimes: {len(config[\"regimes\"])}')
    print(f'Indicators: {len(config[\"indicators\"])}')
    print(f'Strategies: {len(config[\"strategies\"])}')
    print(f'Routing rules: {len(config[\"routing\"])}')
"
```

**Expected Results:**
- ✅ 4 regimes defined
- ✅ Multiple indicators (3+ per regime)
- ✅ 4 strategies (1 per regime)
- ✅ 4 routing rules (regime → strategy set mapping)

---

## Phase 3: Backtesting Testing

### Test 3.1: Backtest Engine - Single Strategy

**Objective**: Run backtest with generated regime set config

**Steps:**
1. In Entry Analyzer, go to "Backtest Setup" tab
2. Click "Browse" and select `regime_set_YYYYMMDD_HHMMSS.json`
3. Set parameters:
   - Symbol: SPY
   - Start Date: 2024-01-01
   - End Date: 2024-12-31
   - Capital: 10,000
4. Click "▶ Run Backtest"

**Expected Behavior:**
- ✅ Progress bar shows completion (0% → 100%)
- ✅ Status updates: "Loading data...", "Calculating indicators...", "Evaluating regimes...", "Simulating trades..."
- ✅ Backtest completes in < 2 minutes (for 1 year of data)
- ✅ No errors or exceptions

**Validation:**
```bash
# Check backtest logs
tail -f logs/orderpilot.log | grep -E "(BacktestEngine|run_backtest|Performance Summary)"
```

**Expected Log Output:**
```
INFO Initializing Backtest for SPY (2024-01-01 to 2024-12-31)
INFO Loading OHLCV data...
INFO Loaded 252 bars
INFO Calculating indicators...
INFO Evaluating regimes...
INFO Simulating trades...
INFO Performance Summary:
INFO   Net Profit: $XXX.XX (XX.XX%)
INFO   Win Rate: XX.XX%
INFO   Profit Factor: X.XX
INFO   Sharpe Ratio: X.XX
INFO   Max Drawdown: XX.XX%
INFO   Total Trades: XXX
```

### Test 3.2: Backtest Results - UI Display

**Objective**: Verify results display correctly in UI

**Expected Results Tab Content:**
- ✅ **Performance Summary Card**:
  - Net Profit ($ and %)
  - Win Rate (%)
  - Profit Factor
  - Sharpe Ratio
  - Max Drawdown (%)
  - Total Trades
- ✅ **Trade List Table**:
  - Entry Date
  - Exit Date
  - Symbol
  - Side (LONG/SHORT)
  - Entry Price
  - Exit Price
  - P&L ($)
  - P&L (%)
  - Strategy Name

### Test 3.3: Regime Visualization

**Objective**: Verify regime boundaries are drawn on chart

**Steps:**
1. After backtest completes
2. Click "📍 Draw on Chart" button

**Expected Behavior:**
- ✅ Vertical lines appear on chart at regime change points
- ✅ Line colors:
  - Green (#26a69a) - TREND_UP
  - Red (#ef5350) - TREND_DOWN
  - Orange (#ffa726) - RANGE
- ✅ Labels show regime type and volatility
- ✅ Tooltip on hover shows timestamp

**Verification:**
- Zoom in/out on chart - lines should scale correctly
- Pan chart - lines should stay at correct timestamps
- Click "🗑️ Clear Entries" - lines should be removed

---

## Phase 4: Bot Start with JSON Strategy

### Test 4.1: Bot Start Strategy Dialog

**Objective**: Verify strategy selection dialog works before bot start

**Steps:**
1. In Trading Tab, click "▶ Start Bot" button
2. "Bot Start Strategy Selection" dialog should open

**Expected Dialog Content:**
- ✅ **Trading Style Selector**:
  - Radio buttons: Daytrading / Swing / Position
- ✅ **JSON Config Selector**:
  - Browse button
  - Path display
  - Config preview (readonly text)
- ✅ **Market Analysis Section**:
  - "🔍 Analyze Current Market" button
  - Regime display (initially "Not analyzed")
  - Strategy match display
- ✅ **Action Buttons**:
  - "✓ Apply Strategy" (disabled initially)
  - "Cancel"

### Test 4.2: Market Analysis Integration

**Objective**: Verify current regime detection and strategy matching

**Steps:**
1. In dialog, click "Browse" and select `regime_set_*.json`
2. Click "🔍 Analyze Current Market"

**Expected Behavior:**
- ✅ Status changes to "Analyzing market..."
- ✅ After 2-5 seconds:
  - Current regime displayed (e.g., "TREND_UP - NORMAL")
  - Regime metrics shown (ADX, ATR%, Confidence)
  - Matched strategy displayed (e.g., "✓ Matched: Strategy R1_trend")
  - Entry/Exit conditions listed
  - "✓ Apply Strategy" button enabled

**Log Verification:**
```bash
tail -f logs/orderpilot.log | grep -E "(RegimeEngine|classify|StrategyRouter|route)"
```

**Expected Log Output:**
```
INFO Getting current market data for analysis
INFO Detected regime: RegimeType.TREND_UP, Volatility.NORMAL
INFO ADX: XX.XX, ATR%: X.XX%, Confidence: 0.XX
INFO Routing regimes to strategy...
INFO Matched strategy set: set_r1_trend
INFO Strategy applied: strategy_r1_trend
```

### Test 4.3: Bot Start with JSON Config

**Objective**: Start bot with JSON-based strategy

**Steps:**
1. Click "✓ Apply Strategy" in dialog
2. Dialog closes, bot should start

**Expected Behavior:**
- ✅ Bot status label changes: "Status: RUNNING"
- ✅ Start button disabled
- ✅ Stop button enabled
- ✅ Regime badge shows current regime
- ✅ Strategy badge shows matched strategy name

**Validation:**
```bash
# Check BotController logs
tail -f logs/orderpilot.log | grep -E "(BotController|start|JSON config loaded)"
```

**Expected Log Output:**
```
INFO BotController starting with JSON config: regime_set_YYYYMMDD_HHMMSS.json
INFO Loaded JSON config successfully
INFO Initial regime: R1_trend
INFO Initial strategy: strategy_r1_trend
INFO BotController running
```

---

## Phase 5: Dynamic Strategy Switching

### Test 5.1: Regime Change Detection

**Objective**: Verify bot detects regime changes and switches strategies

**Prerequisites:**
- Bot must be running with JSON config
- Market data must show regime transitions (use historical data or simulated data)

**Expected Behavior:**
1. **Bar Processing**:
   - Every new bar, regime is evaluated
   - If regime changes significantly, strategy switch triggered

2. **Strategy Switch**:
   - Old strategy parameters saved
   - New strategy loaded from JSON config
   - Parameter overrides applied
   - Positions adjusted if needed (close incompatible positions)

3. **Event Emission**:
   - `regime_changed` event emitted to event-bus
   - Event data contains:
     - `old_strategy`: Previous strategy ID
     - `new_strategy`: New strategy ID
     - `new_regimes`: List of active regime IDs

**Log Verification:**
```bash
tail -f logs/orderpilot.log | grep -E "(Regime changed|Switching to strategy|strategy_changed event)"
```

**Expected Log Output:**
```
INFO Regime changed: TREND_UP -> RANGE
INFO Routing to new strategy set...
INFO Matched new strategy: strategy_r2_range
INFO Switching to strategy: set_r2_range
INFO Applying parameter overrides...
INFO Strategy switch complete
INFO Emitted regime_changed event
```

### Test 5.2: UI Notification Display

**Objective**: Verify UI shows visual notification on regime/strategy change

**Expected Behavior:**
1. **Regime Badge Update**:
   - Badge text changes to new regime (e.g., "RANGE - HIGH")
   - Tooltip shows strategy name

2. **Visual Notification Banner**:
   - Yellow banner appears below bot controls
   - Text: "⚠ Regime-Wechsel: Neue Strategie '[strategy_name]' aktiv (Regimes: [regime_ids])"
   - Auto-hides after 10 seconds

3. **Bot Activity Log**:
   - Entry added with type "STRATEGY_SWITCH"
   - Timestamp, old strategy, new strategy

**Manual Verification:**
- Observer UI while bot is running
- Trigger regime change (if using simulated data)
- Verify notification appears and auto-hides

---

## Edge Cases and Error Handling

### Edge Case 1: No Regime Match

**Scenario**: Current market doesn't match any defined regime in JSON config

**Expected Behavior:**
- ✅ Bot continues with current strategy (no switch)
- ✅ Warning logged: "No strategy matched current regime"
- ✅ UI shows warning badge: "⚠ No Strategy Match"

**Test Steps:**
1. Create JSON config with very narrow regime conditions
2. Start bot in market that doesn't match
3. Verify warning handling

### Edge Case 2: Invalid JSON Config

**Scenario**: User selects malformed JSON file

**Expected Behavior:**
- ✅ Validation error during load
- ✅ Error message shown: "Invalid JSON config: [specific error]"
- ✅ Bot does NOT start
- ✅ User can select different config

**Test Steps:**
1. Create invalid JSON file (missing required fields)
2. Try to select in dialog
3. Verify validation error shown

### Edge Case 3: Optimization with No Results

**Scenario**: Optimization completes but no indicators meet thresholds

**Expected Behavior:**
- ✅ Empty results table shown
- ✅ Info message: "No indicators met minimum score threshold"
- ✅ Suggest lowering thresholds or changing preset

**Test Steps:**
1. Run optimization with very high min_compatibility_score (e.g., 0.95)
2. Verify graceful handling

### Edge Case 4: Backtest Data Loading Failure

**Scenario**: Cannot load historical data for backtest

**Expected Behavior:**
- ✅ Error message: "Failed to load data for [symbol]"
- ✅ Backtest does NOT run
- ✅ Suggest checking data source connection

**Test Steps:**
1. Disconnect from data source
2. Try to run backtest
3. Verify error handling

---

## Integration Points Verification

### Integration Point 1: CLI Optimizer → UI Thread

**Files:**
- `tools/optimize_indicators.py` (IndicatorOptimizationOrchestrator)
- `src/ui/threads/indicator_optimization_thread.py` (IndicatorOptimizationThread)

**Verification:**
```python
# Check import is correct
grep -n "from tools.optimize_indicators import IndicatorOptimizationOrchestrator" \
    src/ui/threads/indicator_optimization_thread.py
# Expected: Line 84

# Check orchestrator initialization
grep -n "IndicatorOptimizationOrchestrator" \
    src/ui/threads/indicator_optimization_thread.py
# Expected: Lines 84, 88-90
```

**Test:**
1. Run optimization in UI
2. Check logs for "Starting CLI-based optimization"
3. Verify results match CLI output

### Integration Point 2: Backtest Engine → UI Dialog

**Files:**
- `src/backtesting/engine.py` (BacktestEngine)
- `src/ui/dialogs/entry_analyzer_popup.py` (EntryAnalyzerPopup)
- `src/ui/threads/backtest_thread.py` (BacktestThread)

**Verification:**
```python
# Check BacktestThread uses BacktestEngine
grep -n "BacktestEngine" src/ui/threads/backtest_thread.py

# Check signal/slot connection
grep -n "backtest_thread.*connect" src/ui/dialogs/entry_analyzer_popup.py
```

**Test:**
1. Run backtest in UI
2. Verify progress updates
3. Check results display

### Integration Point 3: RegimeEngine → BotController

**Files:**
- `src/core/tradingbot/regime_engine.py` (RegimeEngine)
- `src/core/tradingbot/bot_controller.py` (BotController)

**Verification:**
```python
# Check regime change detection
grep -n "_check_regime_change_and_switch" src/core/tradingbot/bot_controller.py
# Expected: Method definition at line ~659

# Check RegimeEngine usage
grep -n "RegimeEngine" src/core/tradingbot/bot_controller.py
```

**Test:**
1. Start bot with JSON config
2. Simulate regime change
3. Verify strategy switch

### Integration Point 4: BotController → UI Notifications

**Files:**
- `src/core/tradingbot/bot_controller.py` (Event emission)
- `src/ui/widgets/chart_window_mixins/bot_event_handlers.py` (Event subscription)

**Verification:**
```python
# Check event emission
grep -n "self.event_bus.emit.*regime_changed" src/core/tradingbot/bot_controller.py

# Check event subscription
grep -n "subscribe.*regime_changed" src/ui/widgets/chart_window_mixins/bot_event_handlers.py
```

**Test:**
1. Start bot
2. Trigger regime change
3. Verify UI notification appears

---

## Performance Testing

### Performance Test 1: Optimization Speed

**Objective**: Measure optimization time for different presets

**Test Cases:**
```bash
# Quick scan (5 combinations)
time python tools/optimize_indicators.py --regime R1_trend --preset quick_scan --output-dir /tmp

# Balanced (10 combinations)
time python tools/optimize_indicators.py --regime R1_trend --preset balanced --output-dir /tmp

# Exhaustive (20 combinations)
time python tools/optimize_indicators.py --regime R1_trend --preset exhaustive --output-dir /tmp
```

**Expected Times:**
- Quick scan: < 30 seconds
- Balanced: < 60 seconds
- Exhaustive: < 120 seconds

### Performance Test 2: Backtest Speed

**Objective**: Measure backtest engine performance

**Test Cases:**
```python
# 1 month of data (21 bars)
# Expected: < 5 seconds

# 1 year of data (252 bars)
# Expected: < 30 seconds

# 5 years of data (1260 bars)
# Expected: < 2 minutes
```

### Performance Test 3: UI Responsiveness

**Objective**: Ensure UI remains responsive during background operations

**Test:**
1. Start indicator optimization (long-running)
2. While running, try to:
   - Resize window
   - Switch tabs
   - Zoom/pan chart
   - Open other dialogs

**Expected Behavior:**
- ✅ UI remains responsive
- ✅ No freezing or lag
- ✅ Cancel button works immediately

---

## Automated Test Script

Create `tests/integration/test_complete_workflow.py`:

```python
"""Integration test for complete optimization → backtest → bot start workflow."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from tools.optimize_indicators import IndicatorOptimizationOrchestrator
from src.backtesting.engine import BacktestEngine
from src.core.tradingbot.config.loader import ConfigLoader
from src.core.tradingbot.bot_controller import BotController


class TestCompleteWorkflow:
    """Test end-to-end workflow from optimization to bot execution."""

    def test_optimization_generates_valid_config(self):
        """Test CLI optimizer generates valid JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = IndicatorOptimizationOrchestrator()

            output_path = orchestrator.run_full_workflow(
                regime_id="R1_trend",
                preset="quick_scan",
                output_dir=tmpdir
            )

            # Verify file exists
            assert Path(output_path).exists()

            # Verify config is valid
            config = ConfigLoader().load_config(output_path)
            assert config.schema_version == "1.0.0"
            assert len(config.indicators) > 0
            assert len(config.regimes) > 0
            assert len(config.strategies) > 0

    def test_backtest_engine_runs_with_generated_config(self):
        """Test backtest engine can run with generated config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate config
            orchestrator = IndicatorOptimizationOrchestrator()
            output_path = orchestrator.run_full_workflow(
                regime_id="R1_trend",
                preset="quick_scan",
                output_dir=tmpdir
            )

            # Load config
            config = ConfigLoader().load_config(output_path)

            # Run backtest
            engine = BacktestEngine()
            results = engine.run(
                config=config,
                symbol="SPY",
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                initial_capital=10000.0
            )

            # Verify results
            assert results['net_profit_pct'] is not None
            assert results['win_rate'] >= 0 and results['win_rate'] <= 1
            assert results['total_trades'] >= 0

    def test_bot_controller_loads_json_config(self):
        """Test BotController can load and use JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate config
            orchestrator = IndicatorOptimizationOrchestrator()
            output_path = orchestrator.run_full_workflow(
                regime_id="R1_trend",
                preset="quick_scan",
                output_dir=tmpdir
            )

            # Initialize BotController with config
            bot = BotController(
                symbol="SPY",
                trading_env="paper"
            )

            # Load JSON config
            bot._load_json_config(output_path)

            # Verify config loaded
            assert hasattr(bot, '_json_config')
            assert bot._json_config is not None

    def test_regime_change_triggers_strategy_switch(self):
        """Test bot switches strategy when regime changes."""
        # This test would require mocking regime changes
        # and verifying strategy switch logic

        # TODO: Implement with mocked FeatureVector
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Manual Testing Checklist

### Pre-Test Setup
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Alpaca API keys configured (paper account)
- [ ] Application launches without errors
- [ ] Sample JSON configs present in `03_JSON/Trading_Bot/`

### Phase 1: Indicator Optimization
- [ ] CLI optimizer runs for single regime
- [ ] CLI optimizer runs for all regimes
- [ ] Generated JSON files are valid
- [ ] UI optimization tab opens without errors
- [ ] UI optimization shows progress updates
- [ ] Results table displays correct data
- [ ] Results can be sorted by score

### Phase 2: Regime Set Creation
- [ ] Regime set builder opens
- [ ] Top indicators are auto-selected
- [ ] Weights are calculated and displayed
- [ ] JSON preview is generated
- [ ] Config file is saved correctly
- [ ] Saved config is valid JSON

### Phase 3: Backtesting
- [ ] Backtest setup tab loads
- [ ] JSON file browser works
- [ ] Date picker works
- [ ] Capital input accepts values
- [ ] Run backtest button starts backtest
- [ ] Progress bar updates
- [ ] Results tab shows performance metrics
- [ ] Trade list shows all trades
- [ ] Regime boundaries draw on chart
- [ ] Clear button removes regime lines

### Phase 4: Bot Start
- [ ] Start bot button opens strategy dialog
- [ ] Trading style selector works
- [ ] JSON config browser works
- [ ] Config preview displays correctly
- [ ] Analyze button runs market analysis
- [ ] Current regime is detected
- [ ] Strategy is matched correctly
- [ ] Entry/exit conditions are displayed
- [ ] Apply button starts bot
- [ ] Bot status changes to RUNNING
- [ ] Regime badge shows current regime
- [ ] Strategy badge shows matched strategy

### Phase 5: Dynamic Switching
- [ ] Bot detects regime changes
- [ ] Strategy switches automatically
- [ ] UI notification appears
- [ ] Notification auto-hides after 10 seconds
- [ ] Regime badge updates
- [ ] Strategy badge updates
- [ ] Bot activity log shows switch
- [ ] No errors or exceptions during switch

### Edge Cases
- [ ] Handles invalid JSON gracefully
- [ ] Shows warning if no regime matches
- [ ] Handles data loading failures
- [ ] Cancels optimization on user request
- [ ] Stops bot cleanly
- [ ] Handles missing indicators in catalog

### Performance
- [ ] UI remains responsive during optimization
- [ ] Backtest completes in reasonable time
- [ ] No memory leaks during long runs
- [ ] Chart drawing is smooth

---

## Known Issues and Workarounds

### Issue 1: First Optimization Slow
**Symptom**: First optimization run takes longer than subsequent runs

**Cause**: Catalog loading and caching

**Workaround**: Expected behavior, wait for completion

### Issue 2: Regime Lines Overlap
**Symptom**: Many regime changes cause overlapping lines on chart

**Cause**: High-frequency regime switching

**Workaround**: Use smoothing in regime detection or filter rapid changes

### Issue 3: Memory Usage Growth
**Symptom**: Memory usage increases over long backtest

**Cause**: Results accumulation

**Workaround**: Clear results periodically or limit lookback window

---

## Troubleshooting

### Problem: Optimization produces no results

**Checks:**
1. Verify catalog file exists: `config/indicator_catalog.yaml`
2. Check min_compatibility_score is not too high (should be ≤ 0.7)
3. Verify indicators have parameters defined in catalog
4. Check logs for errors

### Problem: Backtest fails to load data

**Checks:**
1. Verify Alpaca API keys are valid
2. Check symbol is supported by Alpaca
3. Verify date range is valid (not future dates)
4. Check network connection
5. Review data loader logs

### Problem: Bot doesn't switch strategies

**Checks:**
1. Verify JSON config has routing rules
2. Check regime detection is working (logs)
3. Verify regimes match routing conditions
4. Check event-bus is initialized
5. Review bot controller logs

### Problem: UI freezes during operation

**Checks:**
1. Verify operations use QThread (not blocking main thread)
2. Check for infinite loops in event handlers
3. Review CPU usage (should not be 100% on UI thread)
4. Check for missing signal/slot connections

---

## Success Criteria

### ✅ Complete Workflow Success
All of the following must pass:

1. **Optimization**: CLI and UI optimization both produce valid JSON configs with indicators, regimes, strategies, and routing
2. **Backtesting**: Backtest engine runs successfully with generated configs, produces valid performance metrics, and visualizes regime boundaries
3. **Bot Start**: Bot controller loads JSON config, detects current regime, matches strategy, and starts successfully
4. **Dynamic Switching**: Bot detects regime changes, switches strategies automatically, and displays UI notifications
5. **No Errors**: No unhandled exceptions, no memory leaks, no UI freezes during any phase

### 📊 Quality Metrics
- Optimization completes in < 2 minutes (balanced preset, 1 regime)
- Backtest processes 1 year of data in < 30 seconds
- UI response time < 100ms for all interactions
- Strategy switch latency < 1 second
- Zero critical errors during 1-hour continuous run

---

## Next Steps After Testing

1. **Document Issues**: Create GitHub issues for any bugs found
2. **Performance Optimization**: Profile and optimize slow operations
3. **User Feedback**: Gather feedback on UI/UX
4. **Additional Features**: Implement based on testing insights
5. **Production Readiness**: Security audit, error handling review

---

## Appendix: Test Data Generation

### Generate Sample Market Data

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_regime_test_data(regime_type: str, bars: int = 1000) -> pd.DataFrame:
    """Generate synthetic data with specific regime characteristics."""

    if regime_type == "trend":
        # Strong trend: increasing prices
        trend = np.linspace(100, 150, bars)
        noise = np.random.normal(0, 1, bars)
        close = trend + noise

    elif regime_type == "range":
        # Range-bound: oscillating prices
        close = 125 + 10 * np.sin(np.linspace(0, 10 * np.pi, bars))
        close += np.random.normal(0, 0.5, bars)

    elif regime_type == "volatile":
        # High volatility: random walk with large moves
        returns = np.random.normal(0, 0.05, bars)
        close = 100 * (1 + returns).cumprod()

    else:  # breakout
        # Consolidation then breakout
        consolidation = np.ones(bars // 2) * 100
        breakout = np.linspace(100, 140, bars // 2)
        close = np.concatenate([consolidation, breakout])
        close += np.random.normal(0, 1, bars)

    # Generate OHLC
    high = close * (1 + np.abs(np.random.normal(0, 0.01, bars)))
    low = close * (1 - np.abs(np.random.normal(0, 0.01, bars)))
    open_prices = close + np.random.normal(0, 0.5, bars)
    volume = np.random.lognormal(15, 1, bars)

    df = pd.DataFrame({
        'datetime': pd.date_range(datetime.now() - timedelta(days=bars), periods=bars, freq='1H'),
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

    return df


# Save test data
for regime in ['trend', 'range', 'volatile', 'breakout']:
    df = generate_regime_test_data(regime, bars=252)
    df.to_csv(f'tests/data/{regime}_test_data.csv', index=False)
```

---

**Testing Guide Version**: 1.0.0
**Last Updated**: 2026-01-18
**Status**: Ready for testing
