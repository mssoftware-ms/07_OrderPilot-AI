# IndicatorSetOptimizer - Stage 2 Implementation

## Overview

The `IndicatorSetOptimizer` implements **Stage 2** of the regime-based trading system optimization pipeline. It optimizes entry and exit signals for each market regime using all 7 technical indicators.

## Features

### ✅ All Requirements Implemented

1. **Regime-Specific Filtering**
   - Only uses bars classified under the selected regime (BULL/BEAR/SIDEWAYS)
   - Bar indices loaded from `optimized_regime.json` (Stage 1 output)

2. **All 7 Indicators Tested**
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - STOCH (Stochastic Oscillator)
   - BB (Bollinger Bands)
   - ATR (Average True Range)
   - EMA (Exponential Moving Average)
   - CCI (Commodity Channel Index)

3. **TPE Optimization**
   - Multivariate TPE (Tree-structured Parzen Estimator)
   - 40 trials per indicator
   - Hyperband pruning for early stopping
   - Multi-fidelity evaluation (10%, 25%, 50%, 100% of data)

4. **Signal Backtest Simulation**
   - **Entry-Long**: Simulates long trades with slippage/fees
   - **Entry-Short**: Simulates short trades with slippage/fees
   - **Exit-Long**: Evaluates exit timing quality (near peaks)
   - **Exit-Short**: Evaluates exit timing quality (near troughs)

5. **Comprehensive Metrics**
   - Win Rate
   - Profit Factor
   - Sharpe Ratio
   - Max Drawdown
   - Expectancy
   - Total Return
   - Wins/Losses count

6. **Condition Generator**
   - Generates `left/op/right` format for `ConditionEvaluator`
   - Compatible with existing JSON schemas
   - Supports all operators: `gt`, `lt`, `gte`, `lte`, `eq`, `neq`, `crosses_above`, `crosses_below`

## Architecture

```
IndicatorSetOptimizer
│
├── SignalBacktest
│   ├── backtest_entry_long()      # Simulate long entries with P&L
│   ├── backtest_entry_short()     # Simulate short entries with P&L
│   ├── backtest_exit_timing()     # Evaluate exit quality
│   └── _calculate_metrics()       # Compute all 9 metrics
│
├── Optimization
│   ├── optimize_all_signals()     # Optimize all 4 signal types
│   ├── _optimize_signal_type()    # Optimize single signal type
│   ├── _create_study()            # Create Optuna study (TPE + Hyperband)
│   └── _objective()               # Objective function with pruning
│
├── Indicator Calculation
│   ├── _calculate_indicator()     # Calculate indicator values
│   ├── _suggest_params()          # Suggest parameters per indicator
│   └── _generate_signal()         # Generate signal + conditions
│
└── Export
    ├── export_to_json()           # Export to JSON schema
    └── _calculate_aggregate_metrics()  # Calculate combined metrics
```

## Usage

### Basic Example

```python
from pathlib import Path
import pandas as pd
from src.core.indicator_set_optimizer import IndicatorSetOptimizer

# Load regime config from Stage 1
regime_config_path = "optimized_regime_BTCUSDT_5m.json"

# Extract BULL regime bar indices
regime_indices = [100, 101, 102, ..., 250]  # From regime_periods in config

# Create optimizer
optimizer = IndicatorSetOptimizer(
    df=price_data,
    regime='BULL',
    regime_indices=regime_indices,
    symbol='BTCUSDT',
    timeframe='5m',
    regime_config_path=regime_config_path
)

# Optimize all signals
results = optimizer.optimize_all_signals(n_trials_per_indicator=40)

# Export to JSON
optimizer.export_to_json(results, output_dir=Path("./output"))
```

### Complete Workflow

See `indicator_set_optimizer_example.py` for complete workflow including:
- Loading Stage 1 results
- Extracting regime periods
- Optimizing all 3 regimes
- Exporting all results

## Signal Backtest Details

### Entry Signals (Long/Short)

```python
def backtest_entry_long(signal, hold_bars=10):
    """
    For each signal:
    1. Enter at close + slippage
    2. Pay entry fee
    3. Hold for N bars
    4. Exit at close - slippage
    5. Pay exit fee
    6. Calculate P&L percentage
    """
```

**Realism Features:**
- Slippage: 0.05% (configurable)
- Fees: 0.075% per side (configurable)
- No overlapping trades (waits for exit before next entry)
- Actual trade execution simulation

### Exit Signals (Long/Short)

```python
def backtest_exit_timing(signal, direction='long'):
    """
    For each signal:
    1. Look ahead 5 bars
    2. Find best possible exit (peak for long, trough for short)
    3. Score how close signal is to optimal exit
    4. Higher score = better timing
    """
```

This evaluates **exit quality** rather than full trades.

## Metric Calculation

### 1. Win Rate
```
win_rate = wins / total_trades
```

### 2. Profit Factor
```
profit_factor = sum(winning_trades) / abs(sum(losing_trades))
```

### 3. Sharpe Ratio
```
sharpe = (mean_return / std_return) * sqrt(252 * 24 * 12)  # Annualized for 5m bars
```

### 4. Max Drawdown
```
cumulative = cumsum(returns)
running_max = maximum.accumulate(cumulative)
drawdown = running_max - cumulative
max_drawdown = max(drawdown)
```

### 5. Expectancy
```
expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
```

## Scoring System

Each optimization result receives a composite score (0-100):

```python
score = (
    0.30 * win_rate_score +        # 30% weight
    0.25 * profit_factor_score +   # 25% weight
    0.20 * sharpe_score +          # 20% weight
    0.15 * expectancy_score +      # 15% weight
    0.10 * drawdown_penalty        # 10% weight (inverted)
)
```

**Trade Count Penalty:**
- If trades < 10: `score *= (trades / 10)`
- Ensures statistical significance

## Condition Format

All generated conditions follow the `left/op/right` format:

### Simple Comparison
```json
{
  "left": {"indicator_id": "rsi_14", "field": "value"},
  "op": "lt",
  "right": {"value": 30}
}
```

### Indicator Cross
```json
{
  "left": {"indicator_id": "macd_12_26_9", "field": "macd"},
  "op": "crosses_above",
  "right": {"indicator_id": "macd_12_26_9", "field": "signal"}
}
```

### Multiple Conditions (AND)
```json
{
  "all": [
    {"left": {...}, "op": "gt", "right": {...}},
    {"left": {...}, "op": "lt", "right": {...}}
  ]
}
```

## JSON Output Structure

```json
{
  "version": "2.0",
  "meta": {
    "stage": "indicator_sets",
    "regime": "BULL",
    "regime_color": "#26a69a",
    "created_at": "2024-01-24T12:00:00",
    "regime_config_ref": "optimized_regime_BTCUSDT_5m.json",
    "aggregate_metrics": {
      "total_signals_enabled": 3,
      "combined_win_rate": 0.58,
      "combined_profit_factor": 1.85
    }
  },
  "signal_sets": {
    "entry_long": {
      "enabled": true,
      "selected_rank": 1,
      "score": 72.5,
      "indicator": "RSI",
      "indicator_id": "rsi_14",
      "params": {
        "period": 14,
        "oversold": 28,
        "overbought": 72
      },
      "conditions": {
        "all": [
          {
            "left": {"indicator_id": "rsi_14", "field": "value"},
            "op": "lt",
            "right": {"value": 28}
          }
        ]
      },
      "metrics": {
        "signals": 45,
        "trades": 22,
        "win_rate": 0.59,
        "profit_factor": 1.92,
        "sharpe_ratio": 1.35,
        "max_drawdown": 0.065,
        "expectancy": 0.0085
      }
    },
    "entry_short": {...},
    "exit_long": {...},
    "exit_short": {...}
  }
}
```

## Parameter Ranges

### RSI
- `period`: 7-21
- `oversold`: 20-35 (for entries)
- `overbought`: 65-80 (for entries)

### MACD
- `fast`: 8-16
- `slow`: 20-30
- `signal`: 7-11

### STOCH
- `k_period`: 10-20
- `d_period`: 2-5
- `smooth`: 2-4
- `oversold`: 15-25
- `overbought`: 75-85

### BB
- `period`: 15-25
- `std_dev`: 1.5-2.5

### ATR
- `period`: 10-20
- `multiplier`: 1.5-3.5

### EMA
- `period`: 10-50 (step 5)

### CCI
- `period`: 14-30
- `oversold`: -150 to -80
- `overbought`: 80-150

## Performance

### Optimization Speed

| Mode | Trials/Indicator | Total Trials | Estimated Time |
|------|------------------|--------------|----------------|
| Quick | 10 | 70 | ~30 seconds |
| Standard | 40 | 280 | ~2 minutes |
| Thorough | 100 | 700 | ~5 minutes |

**Per Regime:** ~2-5 minutes for standard mode
**All 3 Regimes:** ~6-15 minutes total

### Speedup vs Grid Search

| Indicator | Grid Combinations | TPE Trials | Speedup |
|-----------|-------------------|------------|---------|
| RSI | ~500 | 40 | **12.5x** |
| MACD | ~200 | 40 | **5x** |
| STOCH | ~300 | 40 | **7.5x** |
| **Total** | ~5,280 | ~280 | **~19x** |

## Testing

Run comprehensive tests:

```bash
pytest tests/core/test_indicator_set_optimizer.py -v
```

Test coverage includes:
- All 7 indicators
- All 4 signal types
- Signal backtest with slippage/fees
- Metrics calculation
- Condition generation
- JSON export
- Edge cases

## Dependencies

Required packages:
```
pandas>=2.0.0
numpy>=1.24.0
optuna>=3.0.0
talib  # Optional, falls back to pandas_ta
pandas_ta  # Fallback for talib
```

Install:
```bash
pip install optuna pandas numpy pandas_ta
```

## Integration with Stage 1

The optimizer requires Stage 1 (`RegimeOptimizer`) output:

```
01_STUFE_1_Regime/
└── optimized_regime_BTCUSDT_5m.json  ← Input for Stage 2
```

This file contains:
- Regime classification logic
- `regime_periods`: Start/end indices per regime
- Optimized parameters for regime detection

## Next Steps (Stage 3)

After Stage 2, combine results into full trading bot config:

```json
{
  "regime_detection": {/* From Stage 1 */},
  "signal_sets": {
    "BULL": {/* From Stage 2 BULL */},
    "BEAR": {/* From Stage 2 BEAR */},
    "SIDEWAYS": {/* From Stage 2 SIDEWAYS */}
  }
}
```

## Troubleshooting

### Not Enough Regime Bars
```
WARNING: Not enough BEAR bars for optimization!
```
**Solution:** Increase historical data range in Stage 1

### Low Trade Counts
```
Best score: 15.2 (trades: 3)
```
**Solution:** Adjust parameter ranges or increase regime bars

### All Indicators Score Low
```
All indicators < 30 score
```
**Solution:**
- Check if regime classification is accurate
- Verify price data quality
- Consider different indicator combinations

## References

- **Optuna TPE**: [Tree-structured Parzen Estimator](https://optuna.readthedocs.io/en/stable/reference/samplers.html#optuna.samplers.TPESampler)
- **Hyperband**: [Successive Halving Algorithm](https://arxiv.org/abs/1603.06560)
- **Sharpe Ratio**: [Risk-Adjusted Returns](https://en.wikipedia.org/wiki/Sharpe_ratio)
- **Expectancy**: [Trading System Expectancy](https://www.investopedia.com/articles/trading/08/trading-expectancy.asp)

## License

Part of OrderPilot-AI trading system.
