"""Candle Data Preprocessing for Feature Engine.

Contains utilities for preprocessing OHLCV candle data.
"""

from __future__ import annotations

import logging
from datetime import datetime, time

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Trading session definitions
NASDAQ_RTH = {
    'start': time(9, 30),
    'end': time(16, 0),
    'tz': 'America/New_York'
}

CRYPTO_24_7 = {
    'start': time(0, 0),
    'end': time(23, 59, 59),
    'tz': 'UTC'
}


def preprocess_candles(
    data: pd.DataFrame,
    market_type: str = "STOCK",
    target_tz: str = "America/New_York",
    fill_missing: bool = True,
    filter_sessions: bool = True
) -> pd.DataFrame:
    """Preprocess candles for feature calculation.

    Handles:
    - Timezone normalization
    - Missing candle detection and forward-fill
    - Session filtering (RTH for stocks, 24/7 for crypto)
    - Invalid price detection

    Args:
        data: DataFrame with OHLCV columns and datetime index
        market_type: "STOCK" or "CRYPTO"
        target_tz: Target timezone for normalization
        fill_missing: Whether to forward-fill missing candles
        filter_sessions: Whether to filter to valid trading sessions

    Returns:
        Preprocessed DataFrame
    """
    df = data.copy()

    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'timestamp' in df.columns:
            df = df.set_index('timestamp')
        elif 'datetime' in df.columns:
            df = df.set_index('datetime')
        elif 'date' in df.columns:
            df = df.set_index('date')

    # Sort by time
    df = df.sort_index()

    # === TIMEZONE NORMALIZATION ===
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    df.index = df.index.tz_convert(target_tz)

    # === INVALID PRICE DETECTION ===
    price_cols = ['open', 'high', 'low', 'close']
    for col in price_cols:
        if col in df.columns:
            df.loc[df[col] <= 0, col] = np.nan

    df = df.replace([np.inf, -np.inf], np.nan)

    # === MISSING CANDLE HANDLING ===
    if fill_missing and len(df) > 0:
        freq = pd.infer_freq(df.index)
        if freq is None and len(df) > 1:
            deltas = df.index.to_series().diff().dropna()
            if len(deltas) > 0:
                median_delta = deltas.median()
                freq = f"{int(median_delta.total_seconds() // 60)}T"

        if freq:
            expected_idx = pd.date_range(
                start=df.index.min(),
                end=df.index.max(),
                freq=freq,
                tz=df.index.tz
            )
            missing_count = len(expected_idx) - len(df)
            if missing_count > 0:
                logger.debug(f"Filling {missing_count} missing candles")

            df = df.reindex(expected_idx)

            for col in price_cols:
                if col in df.columns:
                    df[col] = df[col].ffill()

            if 'volume' in df.columns:
                df['volume'] = df['volume'].fillna(0)

    # === SESSION FILTERING ===
    if filter_sessions and market_type == "STOCK":
        session = NASDAQ_RTH
        df_time = df.index.time
        mask = (df_time >= session['start']) & (df_time <= session['end'])
        weekday_mask = df.index.dayofweek < 5
        df = df[mask & weekday_mask]

        if len(df) == 0:
            logger.warning("No candles in RTH session after filtering")

    df = df.dropna(subset=['close'])

    logger.debug(f"Preprocessed {len(df)} candles ({market_type}, tz={target_tz})")

    return df


def detect_missing_candles(
    data: pd.DataFrame,
    expected_freq: str = "1T"
) -> list[datetime]:
    """Detect timestamps where candles are missing.

    Args:
        data: DataFrame with datetime index
        expected_freq: Expected candle frequency (e.g., "1T", "5T", "1H")

    Returns:
        List of missing timestamps
    """
    if len(data) < 2:
        return []

    expected_idx = pd.date_range(
        start=data.index.min(),
        end=data.index.max(),
        freq=expected_freq
    )

    actual_idx = set(data.index)
    missing = [ts for ts in expected_idx if ts not in actual_idx]

    if missing:
        logger.info(f"Detected {len(missing)} missing candles")

    return missing


def validate_candles(data: pd.DataFrame) -> dict:
    """Validate candle data quality.

    Returns dict with validation results:
    - is_valid: Overall validity
    - issues: List of detected issues
    - stats: Data quality statistics
    """
    issues = []
    stats = {}

    # Check required columns
    required = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [c for c in required if c.lower() not in data.columns.str.lower()]
    if missing_cols:
        issues.append(f"Missing columns: {missing_cols}")

    # Check for NaN values
    nan_counts = data.isna().sum()
    stats['nan_counts'] = nan_counts.to_dict()
    if nan_counts.sum() > 0:
        issues.append(f"NaN values detected: {nan_counts.sum()} total")

    # Check OHLC consistency
    if 'high' in data.columns and 'low' in data.columns:
        inconsistent = (data['high'] < data['low']).sum()
        if inconsistent > 0:
            issues.append(f"OHLC inconsistency (high < low): {inconsistent} rows")
        stats['ohlc_inconsistent'] = inconsistent

    # Check for zero/negative prices
    for col in ['open', 'high', 'low', 'close']:
        if col in data.columns:
            invalid = (data[col] <= 0).sum()
            if invalid > 0:
                issues.append(f"Invalid {col} prices (<= 0): {invalid}")
            stats[f'{col}_invalid'] = invalid

    # Check for extreme price jumps
    if 'close' in data.columns and len(data) > 1:
        pct_change = data['close'].pct_change().abs()
        extreme_moves = (pct_change > 0.20).sum()
        if extreme_moves > 0:
            issues.append(f"Extreme price moves (>20%): {extreme_moves}")
        stats['extreme_moves'] = extreme_moves

    stats['total_rows'] = len(data)
    stats['issues_count'] = len(issues)

    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'stats': stats
    }
