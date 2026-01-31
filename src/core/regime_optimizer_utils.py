"""Regime Optimizer Utils - Utility Functions & JSON Support.

This module contains utility functions for JSON config support and
custom indicator calculations.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import numpy as np
import pandas as pd
from datetime import datetime

if TYPE_CHECKING:
    from .regime_optimizer_core import RegimeOptimizer
    import optuna.trial

from .regime_optimizer_core import RegimePeriod

# Try to import talib
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

# Try to import pandas_ta
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False

logger = logging.getLogger(__name__)

def _build_indicator_type_maps(optimizer: "RegimeOptimizer") -> None:
    """Build dynamic type→name and name→type mappings from JSON indicators.

    This enables flexible indicator usage without hardcoded mappings.
    """
    if not optimizer._json_indicators_cache:
        return

    optimizer._indicator_type_map.clear()
    optimizer._indicator_name_to_type.clear()

    for ind in optimizer._json_indicators_cache:
        name = ind['name']
        ind_type = ind['type'].upper()

        # Store both mappings
        optimizer._indicator_type_map[ind_type] = name
        optimizer._indicator_name_to_type[name] = ind_type

    logger.debug(
        f"Built indicator type maps: {len(optimizer._indicator_type_map)} types, "
        f"mappings: {optimizer._indicator_type_map}"
    )



def build_indicator_type_maps(optimizer: "RegimeOptimizer") -> None:
    """Build dynamic type→name and name→type mappings from JSON indicators.

    Args:
    optimizer: RegimeOptimizer instance
    """
    return _build_indicator_type_maps(optimizer)

def _calculate_chandelier_stop(
    self,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    lookback: int = 22,
    atr_period: int = 22,
    multiplier: float = 3.0,
    ) -> dict[str, pd.Series]:
    """Calculate Chandelier Stop (pipCharlie style).

    Chandelier Stop is an ATR-based trailing stop indicator:
    - Long Stop: highest(lookback) - multiplier * ATR
    - Short Stop: lowest(lookback) + multiplier * ATR
    - Direction: 1 (bullish) when close > short_stop, -1 (bearish) when close < long_stop

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        lookback: Lookback period for highest/lowest
        atr_period: ATR calculation period
        multiplier: ATR multiplier

    Returns:
        Dictionary with 'long_stop', 'short_stop', 'direction', 'color_change'
    """
    # Calculate ATR
    if TALIB_AVAILABLE:
        atr = pd.Series(
            talib.ATR(high, low, close, timeperiod=atr_period),
            index=close.index
        )
    elif PANDAS_TA_AVAILABLE:
        atr = ta.atr(high, low, close, length=atr_period)
    else:
        # Simple ATR approximation
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_period).mean()

    # Calculate highest high and lowest low
    highest_high = high.rolling(window=lookback).max()
    lowest_low = low.rolling(window=lookback).min()

    # Calculate stops
    long_stop = highest_high - multiplier * atr
    short_stop = lowest_low + multiplier * atr

    # Determine direction: 1 = bullish, -1 = bearish
    direction = pd.Series(0, index=close.index)
    direction[close > short_stop] = 1
    direction[close < long_stop] = -1

    # Forward fill for bars where neither condition is met
    direction = direction.replace(0, np.nan).ffill().fillna(0).astype(int)

    # Detect color/direction changes
    color_change = (direction != direction.shift(1)).astype(int)

    return {
        'long_stop': long_stop,
        'short_stop': short_stop,
        'direction': direction,
        'color_change': color_change,
    }


def calculate_chandelier_stop(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    lookback: int = 22,
    atr_period: int = 22,
    multiplier: float = 3.0,
) -> dict[str, pd.Series]:
    """Calculate Chandelier Stop (pipCharlie style).

    Chandelier Stop is an ATR-based trailing stop indicator:
    - Long Stop: highest(lookback) - multiplier * ATR
    - Short Stop: lowest(lookback) + multiplier * ATR
    - Direction: 1 (bullish) when close > short_stop, -1 (bearish) when close < long_stop

    Args:
    high: High prices
    low: Low prices
    close: Close prices
    lookback: Lookback period for highest/lowest
    atr_period: ATR calculation period
    multiplier: ATR multiplier

    Returns:
    Dictionary with 'long_stop', 'short_stop', 'direction', 'color_change'
    """
    # Calculate ATR
    if TALIB_AVAILABLE:
    atr = pd.Series(
        talib.ATR(high, low, close, timeperiod=atr_period),
        index=close.index
    )
    elif PANDAS_TA_AVAILABLE:
    atr = ta.atr(high, low, close, length=atr_period)
    else:
    # Simple ATR approximation
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_period).mean()

    # Calculate highest high and lowest low
    highest_high = high.rolling(window=lookback).max()
    lowest_low = low.rolling(window=lookback).min()

    # Calculate stops
    long_stop = highest_high - multiplier * atr
    short_stop = lowest_low + multiplier * atr

    # Determine direction: 1 = bullish, -1 = bearish
    direction = pd.Series(0, index=close.index)
    direction[close > short_stop] = 1
    direction[close < long_stop] = -1

    # Forward fill for bars where neither condition is met
    direction = direction.replace(0, np.nan).ffill().fillna(0).astype(int)

    # Detect color/direction changes
    color_change = (direction != direction.shift(1)).astype(int)

    return {
    'long_stop': long_stop,
    'short_stop': short_stop,
    'direction': direction,
    'color_change': color_change,
    }

def _calculate_adx_leaf_west(
    self,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    adx_length: int = 8,
    dmi_length: int = 9,
    ) -> dict[str, pd.Series]:
    """Calculate ADX Leaf West style (shorter periods for faster signals).

    This is an ADX/DMI variant with different period settings for ADX vs DMI.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        adx_length: ADX smoothing period (default 8)
        dmi_length: DMI calculation period (default 9)

    Returns:
        Dictionary with 'adx', 'plus_di', 'minus_di', 'di_diff'
    """
    # Calculate True Range
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)

    # Calculate +DM and -DM
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = pd.Series(0.0, index=close.index)
    minus_dm = pd.Series(0.0, index=close.index)

    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

    # Smooth TR, +DM, -DM with Wilder's smoothing (using DMI length)
    smoothed_tr = tr.ewm(alpha=1/dmi_length, adjust=False).mean()
    smoothed_plus_dm = plus_dm.ewm(alpha=1/dmi_length, adjust=False).mean()
    smoothed_minus_dm = minus_dm.ewm(alpha=1/dmi_length, adjust=False).mean()

    # Calculate +DI and -DI
    plus_di = 100 * smoothed_plus_dm / smoothed_tr
    minus_di = 100 * smoothed_minus_dm / smoothed_tr

    # Calculate DX
    di_sum = plus_di + minus_di
    di_diff_abs = (plus_di - minus_di).abs()
    dx = 100 * di_diff_abs / di_sum.replace(0, np.nan)

    # Calculate ADX (smoothed DX using ADX length)
    adx = dx.ewm(alpha=1/adx_length, adjust=False).mean()

    return {
        'adx': adx,
        'plus_di': plus_di,
        'minus_di': minus_di,
        'di_diff': plus_di - minus_di,
    }


def calculate_adx_leaf_west(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    adx_length: int = 8,
    dmi_length: int = 9,
) -> dict[str, pd.Series]:
    """Calculate ADX Leaf West style (shorter periods for faster signals).

    This is an ADX/DMI variant with different period settings for ADX vs DMI.

    Args:
    high: High prices
    low: Low prices
    close: Close prices
    adx_length: ADX smoothing period (default 8)
    dmi_length: DMI calculation period (default 9)

    Returns:
    Dictionary with 'adx', 'plus_di', 'minus_di', 'di_diff'
    """
    # Calculate True Range
    tr = pd.concat([
    high - low,
    (high - close.shift(1)).abs(),
    (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)

    # Calculate +DM and -DM
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = pd.Series(0.0, index=close.index)
    minus_dm = pd.Series(0.0, index=close.index)

    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

    # Smooth TR, +DM, -DM with Wilder's smoothing (using DMI length)
    smoothed_tr = tr.ewm(alpha=1/dmi_length, adjust=False).mean()
    smoothed_plus_dm = plus_dm.ewm(alpha=1/dmi_length, adjust=False).mean()
    smoothed_minus_dm = minus_dm.ewm(alpha=1/dmi_length, adjust=False).mean()

    # Calculate +DI and -DI
    plus_di = 100 * smoothed_plus_dm / smoothed_tr
    minus_di = 100 * smoothed_minus_dm / smoothed_tr

    # Calculate DX
    di_sum = plus_di + minus_di
    di_diff_abs = (plus_di - minus_di).abs()
    dx = 100 * di_diff_abs / di_sum.replace(0, np.nan)

    # Calculate ADX (smoothed DX using ADX length)
    adx = dx.ewm(alpha=1/adx_length, adjust=False).mean()

    return {
    'adx': adx,
    'plus_di': plus_di,
    'minus_di': minus_di,
    'di_diff': plus_di - minus_di,
    }

def _get_json_param_value(
    self, scope: str, param: dict, fallback: float | int | None = None
    ) -> float | int:
    """Get parameter value from trial-suggested params or fallback to JSON value.

    Args:
        scope: Indicator name or regime ID
        param: Parameter dict with 'name' and 'value' keys
        fallback: Optional fallback if not found anywhere

    Returns:
        Parameter value (trial-suggested or JSON default)
    """
    key = f"{scope}.{param['name']}"

    # First check trial-suggested params
    if key in optimizer._trial_params:
        return optimizer._trial_params[key]

    # Fallback to JSON value
    if 'value' in param:
        return param['value']

    # Final fallback
    if fallback is not None:
        return fallback

    raise KeyError(f"No value found for parameter: {key}")


def get_json_param_value(
    optimizer: "RegimeOptimizer",
    scope: str,
    param: dict,
    fallback: float | int | None = None
) -> float | int:
    """Get parameter value from trial or JSON.

    Args:
    optimizer: RegimeOptimizer instance
    scope: Indicator name or regime ID
    param: Parameter dict
    fallback: Optional fallback

    Returns:
    Parameter value
    """
    return _get_json_param_value(optimizer, scope, param, fallback)

def _load_trial_params(optimizer: "RegimeOptimizer", trial: optuna.trial.FrozenTrial) -> None:
    """Load trial-suggested params from a completed trial's stored params.

    Used post-optimization to reload the params for result extraction.
    Only loads keys that match the JSON param pattern (e.g., "STRENGTH_ADX.period").

    Args:
        trial: Completed Optuna trial with stored params
    """
    optimizer._trial_params.clear()

    for key, value in trial.params.items():
        # Only load JSON-style params (contain dots like "INDICATOR.param" or "REGIME.thresh")
        if '.' in key:
            optimizer._trial_params[key] = value



def load_trial_params(optimizer: "RegimeOptimizer", trial: "optuna.trial.FrozenTrial") -> None:
    """Load trial parameters.

    Args:
    optimizer: RegimeOptimizer instance
    trial: Frozen trial
    """
    return _load_trial_params(optimizer, trial)

def _resolve_indicator_name(optimizer: "RegimeOptimizer", base: str, suffix: str = '') -> str:
    """Dynamically resolve indicator name from type or threshold base name.

    Uses the type→name mapping built from JSON indicators.
    Falls back to uppercase base name if no mapping exists.

    Args:
        base: Threshold base name (e.g., 'adx', 'rsi', 'chandelier')
        suffix: Optional suffix (e.g., '_DI_DIFF', '_DIRECTION')

    Returns:
        Resolved indicator name (e.g., 'STRENGTH_ADX_DI_DIFF')
    """
    base_upper = base.upper()

    # Check if we have a direct mapping for this type
    if base_upper in optimizer._indicator_type_map:
        ind_name = optimizer._indicator_type_map[base_upper]
        return f"{ind_name}{suffix}" if suffix else ind_name

    # Check common aliases - find any alias that exists in the type map
    alias_groups = [
        ['ADX', 'ADX_LEAF_WEST'],  # ADX-family indicators
        ['RSI'],
        ['ATR'],
        ['CHANDELIER', 'CKSP', 'CHANDELIER_STOP'],  # Chandelier-family indicators
        ['BB', 'BOLLINGER'],
        ['SMA'],
        ['EMA'],
    ]

    for alias_list in alias_groups:
        if base_upper in alias_list:
            # Find any alias from this group that exists in the type map
            for alias in alias_list:
                if alias in optimizer._indicator_type_map:
                    ind_name = optimizer._indicator_type_map[alias]
                    return f"{ind_name}{suffix}" if suffix else ind_name

    # Fallback: return base name with suffix
    return f"{base_upper}{suffix}" if suffix else base_upper


def resolve_indicator_name(optimizer: "RegimeOptimizer", base: str, suffix: str = '') -> str:
    """Resolve indicator name dynamically.

    Args:
    optimizer: RegimeOptimizer instance
    base: Base name
    suffix: Optional suffix

    Returns:
    Resolved indicator name
    """
    return _resolve_indicator_name(optimizer, base, suffix)

def _extract_regime_periods(optimizer: "RegimeOptimizer", regimes: pd.Series) -> list[RegimePeriod]:
    """Extract regime periods with bar indices.

    Args:
        regimes: Classified regimes

    Returns:
        List of regime periods
    """
    def infer_base_type(regime_id: str) -> str:
        """Infer base regime type from regime ID for color coding."""
        regime_upper = regime_id.upper()
        if 'BULL' in regime_upper:
            return 'BULL'
        elif 'BEAR' in regime_upper:
            return 'BEAR'
        else:
            return 'SIDEWAYS'

    periods = []

    if len(regimes) == 0:
        return periods

    current_regime = str(regimes.iloc[0])
    start_idx = 0

    for i in range(1, len(regimes)):
        if regimes.iloc[i] != current_regime:
            # End of current regime
            end_idx = i - 1

            # Get timestamps if index is datetime
            start_ts = None
            end_ts = None
            if isinstance(optimizer.data.index, pd.DatetimeIndex):
                start_ts = optimizer.data.index[start_idx].to_pydatetime()
                end_ts = optimizer.data.index[end_idx].to_pydatetime()

            periods.append(
                RegimePeriod(
                    regime=current_regime,
                    base_type=infer_base_type(current_regime),
                    start_idx=start_idx,
                    end_idx=end_idx,
                    start_timestamp=start_ts,
                    end_timestamp=end_ts,
                    bars=end_idx - start_idx + 1,
                )
            )

            # Start new regime
            current_regime = str(regimes.iloc[i])
            start_idx = i

    # Add final regime
    end_idx = len(regimes) - 1
    start_ts = None
    end_ts = None
    if isinstance(optimizer.data.index, pd.DatetimeIndex):
        start_ts = optimizer.data.index[start_idx].to_pydatetime()
        end_ts = optimizer.data.index[end_idx].to_pydatetime()

    periods.append(
        RegimePeriod(
            regime=current_regime,
            base_type=infer_base_type(current_regime),
            start_idx=start_idx,
            end_idx=end_idx,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            bars=end_idx - start_idx + 1,
        )
    )

    return periods


def extract_regime_periods(optimizer: "RegimeOptimizer", regimes: pd.Series) -> list[RegimePeriod]:
    """Extract regime periods with bar indices.

    Args:
    optimizer: RegimeOptimizer instance
    regimes: Classified regimes

    Returns:
    List of regime periods
    """
    return _extract_regime_periods(optimizer, regimes)
