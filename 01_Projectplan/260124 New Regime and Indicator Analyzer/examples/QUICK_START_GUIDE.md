# Quick Start Guide - IndicatorSetOptimizer

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install optuna pandas numpy pandas_ta
```

### 2. Run Example
```bash
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI
python "01_Projectplan/260124 New Regime and Indicator Analyzer/examples/indicator_set_optimizer_example.py"
```

### 3. Check Output
```bash
ls "03_JSON/Entry_Analyzer/Regime/STUFE_2_Indicators/"

# Should see:
# BULL/indicator_sets_BULL_BTCUSDT_5m.json
# BEAR/indicator_sets_BEAR_BTCUSDT_5m.json
# SIDEWAYS/indicator_sets_SIDEWAYS_BTCUSDT_5m.json
```

---

## Basic Usage (Copy-Paste Ready)

```python
import json
import pandas as pd
from pathlib import Path
from src.core.indicator_set_optimizer import IndicatorSetOptimizer

# 1. Load regime config from Stage 1
with open('optimized_regime_BTCUSDT_5m.json') as f:
    regime_config = json.load(f)

# 2. Extract BULL regime bar indices
bull_indices = []
for period in regime_config['regime_periods']:
    if period['regime'] == 'BULL':
        bull_indices.extend(range(period['start_idx'], period['end_idx'] + 1))

# 3. Load your price data
df = pd.read_csv('BTCUSDT_5m.csv')  # Your data source

# 4. Create optimizer
optimizer = IndicatorSetOptimizer(
    df=df,
    regime='BULL',
    regime_indices=bull_indices,
    symbol='BTCUSDT',
    timeframe='5m',
    regime_config_path='optimized_regime_BTCUSDT_5m.json'
)

# 5. Optimize (fast mode = 10 trials, standard = 40)
results = optimizer.optimize_all_signals(n_trials_per_indicator=10)

# 6. Export
optimizer.export_to_json(results, Path('./output'))

# 7. Print results
for signal_type, result in results.items():
    print(f"\n{signal_type}:")
    print(f"  Indicator: {result.indicator}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Win Rate: {result.metrics.win_rate:.2%}")
    print(f"  Trades: {result.metrics.trades}")
```

---

## Common Tasks

### Change Optimization Speed

```python
# Fast (testing)
results = optimizer.optimize_all_signals(n_trials_per_indicator=5)  # ~30s

# Standard (production)
results = optimizer.optimize_all_signals(n_trials_per_indicator=40)  # ~2min

# Thorough (final optimization)
results = optimizer.optimize_all_signals(n_trials_per_indicator=100)  # ~5min
```

### Adjust Slippage/Fees

```python
from src.core.indicator_set_optimizer import SignalBacktest

# Custom backtester
backtester = SignalBacktest(
    df=df,
    slippage_pct=0.1,   # 0.1% slippage
    fee_pct=0.1         # 0.1% fees (maker/taker combined)
)

# Use in optimizer (modify _evaluate_indicator_on_df method)
```

### Access Individual Results

```python
results = optimizer.optimize_all_signals(n_trials_per_indicator=40)

# Get entry long result
entry_long = results['entry_long']

print(f"Best Indicator: {entry_long.indicator}")
print(f"Parameters: {entry_long.params}")
print(f"Conditions: {entry_long.conditions}")

# Get metrics
m = entry_long.metrics
print(f"Win Rate: {m.win_rate:.2%}")
print(f"Profit Factor: {m.profit_factor:.2f}")
print(f"Sharpe: {m.sharpe_ratio:.2f}")
print(f"Max DD: {m.max_drawdown:.2%}")
```

---

## Understanding Output

### Enabled vs Disabled Signals

Signals with **score > 30** are automatically enabled:

```json
{
  "entry_long": {
    "enabled": true,    // Score = 72.5 > 30
    "score": 72.5
  },
  "entry_short": {
    "enabled": false,   // Score = 25.3 < 30
    "score": 25.3
  }
}
```

### Reading Conditions

```json
{
  "conditions": {
    "all": [  // AND condition
      {
        "left": {"indicator_id": "rsi_14", "field": "value"},
        "op": "lt",
        "right": {"value": 28}
      }
    ]
  }
}
```

**Means:** RSI(14) < 28

### Metrics Interpretation

| Metric | Good | Poor | Meaning |
|--------|------|------|---------|
| Win Rate | >60% | <40% | Percentage of winning trades |
| Profit Factor | >2.0 | <1.0 | Gross wins / Gross losses |
| Sharpe Ratio | >1.0 | <0.0 | Risk-adjusted returns |
| Max Drawdown | <5% | >15% | Largest peak-to-trough decline |
| Expectancy | >1% | <0% | Expected return per trade |

---

## Troubleshooting

### "Not enough bars for optimization"

**Problem:** Regime has < 100 bars

**Solution:**
```python
# Check regime bar count
print(f"Regime bars: {len(optimizer.regime_df)}")

# Need more historical data or different regime detection
```

### "All scores below 30"

**Problem:** No good signals found

**Solutions:**
1. Check regime classification accuracy
2. Verify price data quality
3. Try different parameter ranges
4. Increase regime bars

### "Optimization too slow"

**Solution:**
```python
# Reduce trials
results = optimizer.optimize_all_signals(n_trials_per_indicator=10)

# Or optimize single signal type
result = optimizer._optimize_signal_type('entry_long', n_trials=20)
```

---

## Testing

### Run All Tests
```bash
pytest tests/core/test_indicator_set_optimizer.py -v
```

### Run Specific Test
```bash
pytest tests/core/test_indicator_set_optimizer.py::TestSignalBacktest::test_backtest_entry_long_basic -v
```

### Check Test Coverage
```bash
pytest tests/core/test_indicator_set_optimizer.py --cov=src.core.indicator_set_optimizer --cov-report=html
```

---

## Integration with Stage 1

### Complete Workflow

```python
# STAGE 1: Regime Optimization
from src.core.regime_optimizer import RegimeOptimizer

regime_opt = RegimeOptimizer(df, symbol, timeframe)
regime_results = regime_opt.optimize()
regime_config_path = regime_opt.export_to_json(regime_results, output_dir)

# STAGE 2: Indicator Optimization (for each regime)
for regime in ['BULL', 'BEAR', 'SIDEWAYS']:
    # Extract indices
    indices = extract_regime_indices(regime_config_path, regime)

    # Optimize
    indicator_opt = IndicatorSetOptimizer(
        df=df,
        regime=regime,
        regime_indices=indices,
        symbol=symbol,
        timeframe=timeframe,
        regime_config_path=regime_config_path
    )

    results = indicator_opt.optimize_all_signals(n_trials_per_indicator=40)
    indicator_opt.export_to_json(results, output_dir / regime)
```

---

## Advanced Usage

### Custom Indicator Parameters

```python
# Override suggest_params for custom ranges
def custom_suggest_params(trial, indicator, signal_type):
    if indicator == 'RSI':
        return {
            'period': trial.suggest_int('period', 10, 30),  # Wider range
            'oversold': trial.suggest_int('oversold', 15, 30),
            'overbought': trial.suggest_int('overbought', 70, 85)
        }
    # ... etc

# Monkey patch (not recommended for production)
optimizer._suggest_params = custom_suggest_params
```

### Access Optuna Study

```python
# During optimization, access study object
study = optimizer._create_study('entry_long', 'RSI')

# View trials
for trial in study.trials:
    print(f"Trial {trial.number}: {trial.params} -> {trial.value}")

# Get importance
from optuna.importance import get_param_importances
importance = get_param_importances(study)
print(importance)
```

### Batch Processing Multiple Symbols

```python
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

for symbol in symbols:
    # Load data
    df = load_data(symbol, '5m')

    # Load regime config
    regime_config = load_regime_config(f'optimized_regime_{symbol}_5m.json')

    # Optimize each regime
    for regime in ['BULL', 'BEAR', 'SIDEWAYS']:
        optimizer = IndicatorSetOptimizer(...)
        results = optimizer.optimize_all_signals(n_trials_per_indicator=40)
        optimizer.export_to_json(results, output_dir / symbol / regime)
```

---

## Visualization (Optional)

### Install Optuna Dashboard

```bash
pip install optuna-dashboard
```

### Create SQLite Storage

```python
from optuna.samplers import TPESampler

# Use persistent storage
sampler = TPESampler(multivariate=True, seed=42)

study = optuna.create_study(
    direction='maximize',
    sampler=sampler,
    storage='sqlite:///optuna_indicator_sets.db',  # Persistent DB
    study_name='BULL_entry_long_RSI',
    load_if_exists=True
)

# Run optimization...
```

### View Dashboard

```bash
optuna-dashboard sqlite:///optuna_indicator_sets.db
# Opens browser at http://localhost:8080
```

---

## Best Practices

1. **Always validate regime config first**
   ```python
   assert Path(regime_config_path).exists()
   assert len(regime_indices) >= 100
   ```

2. **Use appropriate trial counts**
   - Development: 5-10 trials
   - Testing: 20-30 trials
   - Production: 40-100 trials

3. **Monitor score distributions**
   ```python
   scores = [r.score for r in results.values()]
   print(f"Avg Score: {np.mean(scores):.2f}")
   print(f"Enabled: {sum(s > 30 for s in scores)}/4")
   ```

4. **Save intermediate results**
   ```python
   # After each regime
   optimizer.export_to_json(results, output_dir)
   ```

5. **Check data quality**
   ```python
   assert not df['close'].isna().any()
   assert (df['high'] >= df['low']).all()
   ```

---

## FAQ

**Q: Can I optimize fewer than 7 indicators?**
A: Yes, modify `INDICATORS` list in optimizer or filter results after.

**Q: Can I add custom indicators?**
A: Yes, extend `_calculate_indicator()` method with your indicator.

**Q: What if regime has no good signals?**
A: All signals will have `enabled: false`. Consider different regime detection.

**Q: Can I use different backtest logic?**
A: Yes, extend `SignalBacktest` class or create custom backtester.

**Q: How to handle crypto vs stocks?**
A: No changes needed. Works with any OHLCV data.

---

## Next Steps

After Stage 2 completion:

1. **Combine Results** (Stage 3)
   - Merge regime + indicator configs
   - Create final trading bot config

2. **UI Integration**
   - Add visualization
   - Interactive parameter tuning

3. **Live Testing**
   - Paper trading with optimized signals
   - Monitor performance

---

## Support

- **Documentation:** `INDICATOR_SET_OPTIMIZER_README.md`
- **Tests:** `tests/core/test_indicator_set_optimizer.py`
- **Example:** `indicator_set_optimizer_example.py`
- **Schema:** `schemas/optimized_indicator_sets.schema.json`

---

**Remember:** Start small (5-10 trials), validate results, then scale up to full optimization (40+ trials).
