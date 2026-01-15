from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import calculate_obv, calculate_rsi


def momentum_signals(
    df: pd.DataFrame,
    params: dict[str, Any],
    calculate_rsi=calculate_rsi,
    calculate_obv=calculate_obv,
) -> pd.Series:
    """Generate momentum strategy signals."""
    roc_period = params.get("roc_period", 10)
    mom_period = params.get("mom_period", 10)
    rsi_period = params.get("rsi_period", 14)
    roc_threshold = params.get("roc_threshold", 5.0)
    rsi_lower = params.get("rsi_lower", 50)
    rsi_upper = params.get("rsi_upper", 80)
    rsi_exit = params.get("rsi_exit_threshold", 85)

    # Rate of Change (use lower threshold for practical trading)
    close_shifted = df["close"].shift(roc_period)
    roc = (100 * (df["close"] - close_shifted) / close_shifted.replace(0, np.nan)).fillna(0)

    # Momentum
    mom = (df["close"] - df["close"].shift(mom_period)).fillna(0)

    # RSI
    rsi = calculate_rsi(df["close"], rsi_period)

    # OBV
    obv = calculate_obv(df)
    obv_change = (obv.pct_change(10) * 100).fillna(0)

    signals = pd.Series(0, index=df.index)

    # Buy: Momentum signals (relaxed - use OR instead of all AND)
    # Lower the ROC threshold significantly (was 5%, now dynamic based on param)
    effective_roc_threshold = roc_threshold / 5  # e.g., 5% -> 1%

    has_roc = roc > effective_roc_threshold
    has_momentum = mom > 0
    has_good_rsi = (rsi > rsi_lower) & (rsi < rsi_upper)
    has_obv = obv_change > 0  # Just positive OBV change

    # Buy when we have momentum AND RSI is in good range
    buy_condition = has_momentum & has_good_rsi & (has_roc | has_obv)

    # Sell: Momentum reversal (any of these)
    sell_condition = (roc < -effective_roc_threshold) | (rsi > rsi_exit)

    signals[buy_condition] = 1
    signals[sell_condition] = -1

    return signals
