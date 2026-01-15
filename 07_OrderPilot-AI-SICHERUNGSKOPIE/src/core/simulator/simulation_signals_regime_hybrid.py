from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import calculate_obv, calculate_rsi, true_range


def regime_hybrid_signals(
    df: pd.DataFrame,
    params: dict[str, Any],
    calculate_rsi=calculate_rsi,
    calculate_obv=calculate_obv,
    true_range=true_range,
) -> pd.Series:
    """Generate Regime Switching Hybrid signals.

    Detects market regime (Trending, Ranging, High Volatility) and applies
    the appropriate sub-strategy:
    - Trending: Trend following (buy dips in uptrend)
    - Ranging: Mean reversion (buy oversold, sell overbought)
    - High Vol: Reduced position sizing / stay out
    """
    adx_period = params.get("adx_period", 14)
    trend_threshold = params.get("trend_threshold", 25)
    range_threshold = params.get("range_threshold", 20)
    bb_period = params.get("bb_period", 20)
    bb_std = params.get("bb_std", 2.0)

    # Calculate ADX for regime detection
    tr = true_range(df)
    atr = tr.rolling(adx_period).mean()
    dm_plus = (df["high"].diff()).clip(lower=0)
    dm_minus = (-df["low"].diff()).clip(lower=0)
    di_plus = 100 * (dm_plus.rolling(adx_period).mean() / atr.replace(0, np.nan))
    di_minus = 100 * (dm_minus.rolling(adx_period).mean() / atr.replace(0, np.nan))
    di_sum = di_plus + di_minus
    dx = 100 * abs(di_plus - di_minus) / di_sum.replace(0, np.nan)
    adx = dx.rolling(adx_period).mean().fillna(0)

    # Regime detection
    trending = adx > trend_threshold
    ranging = adx < range_threshold
    # High volatility: ATR expanding
    atr_expanding = atr > atr.rolling(20).mean() * 1.5

    # Bollinger Bands for mean reversion in ranging markets
    bb_middle = df["close"].rolling(bb_period).mean()
    bb_std_val = df["close"].rolling(bb_period).std().fillna(0)
    bb_upper = bb_middle + bb_std * bb_std_val
    bb_lower = bb_middle - bb_std * bb_std_val
    bb_pct = (df["close"] - bb_lower) / (bb_upper - bb_lower).replace(0, np.nan)
    bb_pct = bb_pct.fillna(0.5)

    # RSI
    rsi = calculate_rsi(df["close"], 14)

    # Trend direction
    ema_fast = df["close"].ewm(span=12, adjust=False).mean()
    ema_slow = df["close"].ewm(span=26, adjust=False).mean()
    uptrend = ema_fast > ema_slow

    signals = pd.Series(0, index=df.index)

    # TRENDING REGIME: Buy pullbacks in uptrend
    trend_buy = trending & uptrend & (rsi < 50) & (rsi > 30)
    trend_sell = trending & ~uptrend

    # RANGING REGIME: Mean reversion
    range_buy = ranging & (bb_pct < 0.2) & (rsi < 35)
    range_sell = ranging & (bb_pct > 0.8) & (rsi > 65)

    # HIGH VOLATILITY: Stay cautious, only trade with strong signals
    vol_buy = atr_expanding & uptrend & (rsi < 40)
    vol_sell = atr_expanding & (rsi > 75)

    # Combine signals
    buy_condition = trend_buy | range_buy | vol_buy
    sell_condition = trend_sell | range_sell | vol_sell

    signals[buy_condition] = 1
    signals[sell_condition] = -1

    return signals
