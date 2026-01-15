# Batch Test Parameter Documentation

## Overview

This document describes the 17 parameters used in the "Run Batch Test" feature within Trading Bot > Backtesting > Tab Batch/WF.

**Problem:** With 17 parameters, each having multiple variations, a Grid Search generates an exponential number of combinations that can exceed available memory (17 billion+ possibilities).

---

## The 17 Parameters (from Issue #39 Log)

Based on the log output:
```
📋 Parameter Space: ['weight_trend_alignment', 'weight_rsi', 'weight_macd', 'weight_adx',
'weight_volatility', 'weight_volume', 'gate_block_in_chop', 'gate_block_against_strong_trend',
'gate_allow_counter_trend_sfp', 'min_touches', 'significance_threshold', 'min_score_for_entry',
'base_leverage', 'max_leverage', 'tp_atr_multiplier', 'risk_per_trade_pct', 'sl_atr_multiplier']
```

---

## Detailed Parameter Specifications

### Category 1: Entry Score Weights (6 Parameters)

| # | Parameter | Description | Type | Min | Max | Default Variations |
|---|-----------|-------------|------|-----|-----|-------------------|
| 1 | `weight_trend_alignment` | EMA-Stack Trend Gewichtung | float | 0.0 | 0.5 | [0.15, 0.25, 0.35] |
| 2 | `weight_rsi` | RSI Momentum Gewichtung | float | 0.0 | 0.5 | [0.05, 0.15, 0.25] |
| 3 | `weight_macd` | MACD Crossover Gewichtung | float | 0.0 | 0.5 | [0.10, 0.20, 0.30] |
| 4 | `weight_adx` | ADX Trendstaerke Gewichtung | float | 0.0 | 0.5 | [0.05, 0.15, 0.25] |
| 5 | `weight_volatility` | ATR/BB Volatilitaet Gewichtung | float | 0.0 | 0.5 | [0.05, 0.10, 0.15] |
| 6 | `weight_volume` | Volumen Confirmation Gewichtung | float | 0.0 | 0.5 | [0.05, 0.15, 0.25] |

**Note:** All weights should sum to 1.0 (100%).

### Category 2: Entry Score Gates (3 Parameters)

| # | Parameter | Description | Type | Variations |
|---|-----------|-------------|------|------------|
| 7 | `gate_block_in_chop` | Block bei Seitwaertsbewegung | bool | [True, False] |
| 8 | `gate_block_against_strong_trend` | Block gegen starken Trend | bool | [True, False] |
| 9 | `gate_allow_counter_trend_sfp` | SFP Counter-Trend erlauben | bool | [True, False] |

### Category 3: Level Detection (2 Parameters)

| # | Parameter | Description | Type | Min | Max | Variations |
|---|-----------|-------------|------|-----|-----|------------|
| 10 | `min_touches` | Min. Touches fuer Level | int | 1 | 10 | [2, 3, 4] |
| 11 | `significance_threshold` | Signifikanz-Schwelle | float | 0.3 | 1.0 | [0.5, 0.7, 0.9] |

### Category 4: Entry Requirements (1 Parameter)

| # | Parameter | Description | Type | Min | Max | Variations |
|---|-----------|-------------|------|-----|-----|------------|
| 12 | `min_score_for_entry` | Minimum Score fuer gueltiges Signal | float | 0.1 | 0.9 | [0.40, 0.50, 0.60, 0.70] |

### Category 5: Leverage (2 Parameters)

| # | Parameter | Description | Type | Min | Max | Variations |
|---|-----------|-------------|------|-----|-----|------------|
| 13 | `base_leverage` | Basis-Leverage | int | 1 | 50 | [3, 5, 10, 15] |
| 14 | `max_leverage` | Maximum Leverage | int | 5 | 125 | [10, 20, 30] |

### Category 6: Trigger/Exit (2 Parameters)

| # | Parameter | Description | Type | Min | Max | Variations |
|---|-----------|-------------|------|-----|-----|------------|
| 15 | `tp_atr_multiplier` | Take Profit ATR Multiplikator | float | 1.0 | 5.0 | [1.5, 2.0, 2.5, 3.0] |
| 16 | `sl_atr_multiplier` | Stop Loss ATR Multiplikator | float | 0.5 | 3.0 | [1.0, 1.5, 2.0] |

### Category 7: Risk Management (1 Parameter)

| # | Parameter | Description | Type | Min | Max | Variations |
|---|-----------|-------------|------|-----|-----|------------|
| 17 | `risk_per_trade_pct` | Prozent des Kapitals pro Trade | float | 0.1 | 10.0 | [0.5, 1.0, 1.5, 2.0, 3.0] |

---

## Combination Calculation

### Current Default Variations per Parameter:

```
weight_trend_alignment:              3 variations
weight_rsi:                          3 variations
weight_macd:                         3 variations
weight_adx:                          3 variations
weight_volatility:                   3 variations
weight_volume:                       3 variations
gate_block_in_chop:                  2 variations (bool)
gate_block_against_strong_trend:    2 variations (bool)
gate_allow_counter_trend_sfp:        2 variations (bool)
min_touches:                         3 variations
significance_threshold:              3 variations
min_score_for_entry:                 4 variations
base_leverage:                       4 variations
max_leverage:                        3 variations
tp_atr_multiplier:                   4 variations
sl_atr_multiplier:                   3 variations
risk_per_trade_pct:                  5 variations
```

### Total Combinations (Grid Search):

```
3 * 3 * 3 * 3 * 3 * 3 * 2 * 2 * 2 * 3 * 3 * 4 * 4 * 3 * 4 * 3 * 5
= 729 * 8 * 9 * 4 * 4 * 3 * 4 * 3 * 5
= 729 * 8 * 9 * 2,880
= 729 * 8 * 25,920
= 729 * 207,360
= 151,165,440 combinations (~151 million)
```

**Worst Case (if each parameter has 5+ variations):**
```
5^17 = ~762 billion combinations
```

This is why the system runs out of memory!

---

## Recommendations for Reducing Combinations

### Option 1: Reduce to Essential Parameters Only

Select only the most impactful parameters for optimization. Recommended core set:

```json
{
  "min_score_for_entry": [0.40, 0.50, 0.60],
  "base_leverage": [5, 10, 15],
  "risk_per_trade_pct": [1.0, 1.5, 2.0],
  "tp_atr_multiplier": [2.0, 2.5, 3.0],
  "sl_atr_multiplier": [1.0, 1.5]
}
```

**Combinations:** 3 * 3 * 3 * 3 * 2 = **162 runs**

### Option 2: Use Random Search Instead of Grid

The BatchRunner already supports this. Change search method to "Random" with a fixed number of iterations (e.g., 50-200).

### Option 3: Category-Based Optimization

Optimize one category at a time:

**Phase 1 - Entry Score Weights:**
```json
{
  "weight_trend_alignment": [0.15, 0.25, 0.35],
  "weight_rsi": [0.10, 0.15, 0.20],
  "weight_macd": [0.15, 0.20, 0.25]
}
```
= 27 runs

**Phase 2 - Leverage & Risk (using best weights from Phase 1):**
```json
{
  "base_leverage": [5, 10, 15],
  "risk_per_trade_pct": [1.0, 1.5, 2.0]
}
```
= 9 runs

### Option 4: Binary-Only Gates as Separate Test

Test gate combinations separately since they're boolean:
```json
{
  "gate_block_in_chop": [true, false],
  "gate_block_against_strong_trend": [true, false],
  "gate_allow_counter_trend_sfp": [true, false]
}
```
= 8 runs

---

## Implementation Recommendations

### Current Safeguard in Code

The `BatchRunner._generate_grid_combinations()` method already has a safeguard:

```python
# batch_runner.py line 214
if theoretical_count > max_combinations * 10:  # 10x Buffer fuer Sicherheit
    logger.warning(
        f"Grid wuerde {theoretical_count:,} Kombinationen erzeugen - "
        f"wechsle zu Random-Sampling mit {max_combinations} Iterationen"
    )
    return self._generate_random_combinations(param_space)
```

### Suggested UI Improvements

1. **Show estimated combinations before starting:**
   - Display "This will generate X combinations" warning
   - Block Grid Search if X > 10,000

2. **Add parameter group selection:**
   - Checkbox groups for: Weights, Gates, Levels, Leverage, TP/SL, Risk
   - Allow user to select which groups to vary

3. **Pre-defined optimization templates:**
   - "Quick (50 runs)" - Random search, core parameters only
   - "Standard (200 runs)" - Random search, all parameters
   - "Deep (1000 runs)" - Random search, fine-grained
   - "Grid Essential (< 500 runs)" - Grid search, limited parameters

---

## Summary

| Scenario | Parameters | Variations/Param | Total Combinations |
|----------|------------|------------------|-------------------|
| Full Grid (17 params) | 17 | 3 avg | ~151 million |
| Essential Only (5 params) | 5 | 3 avg | ~162 |
| Category-Based | 3-4 | 3 | 27-81 per phase |
| Random Search | 17 | N/A | User-defined (50-500) |

**Recommendation:** Use Random Search with 100-200 iterations, or reduce to 5-8 most important parameters for Grid Search.

---

## Source Files

- `src/ui/widgets/bitunix_trading/backtest_config_param_spec.py` - Parameter specifications
- `src/ui/widgets/bitunix_trading/backtest_config_param_space.py` - Parameter space generation
- `src/core/backtesting/batch_runner.py` - BatchRunner with safeguards
- `src/ui/widgets/bitunix_trading/backtest_tab_batch_execution.py` - Batch execution handler

---

*Document created: 2026-01-09*
*Issue: #42 - "Zu viele Moeglichkeiten in 'Run Batch Test'"*
