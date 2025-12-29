"""Data conversion utilities for chart widgets.

This module provides the SINGLE implementation for data conversion functions
that were previously duplicated across:
- chart_view.py (lines 693-713): _convert_bars_to_dataframe
- base_chart_widget.py (lines 67-91): _convert_bars_to_dataframe
- lightweight_chart.py (implicit)
- embedded_tradingview_chart.py (implicit)

IMPORTANT: This is now the SINGLE SOURCE OF TRUTH for data conversion.
All chart widgets should use these functions instead of implementing their own.
"""

import logging
from datetime import datetime
from typing import List, Tuple, Any, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


def convert_bars_to_dataframe(
    bars: List[Any],
    timestamp_column: str = "timestamp"
) -> pd.DataFrame:
    """Convert bar objects to a pandas DataFrame.

    This function replaces the duplicated implementations in:
    - chart_view.py:693-713
    - base_chart_widget.py:67-91

    Args:
        bars: List of bar objects. Each bar should have attributes:
            - timestamp: datetime or Unix timestamp
            - open: Opening price
            - high: High price
            - low: Low price
            - close: Closing price
            - volume: Trading volume
        timestamp_column: Name of the timestamp column/attribute

    Returns:
        DataFrame with columns: timestamp (index), open, high, low, close, volume

    Example:
        >>> bars = [Bar(timestamp=dt, open=100, high=105, low=99, close=103, volume=1000)]
        >>> df = convert_bars_to_dataframe(bars)
        >>> df.columns  # ['open', 'high', 'low', 'close', 'volume']
    """
    if not bars:
        logger.debug("Empty bars list provided, returning empty DataFrame")
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

    try:
        data_dict = {
            'timestamp': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': []
        }

        for bar in bars:
            # Handle different timestamp formats
            timestamp = getattr(bar, timestamp_column, None) or getattr(bar, 'timestamp', None)
            if timestamp is None and hasattr(bar, 't'):
                timestamp = bar.t  # Alpaca uses 't' for timestamp

            # Convert to datetime if needed
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp)

            data_dict['timestamp'].append(timestamp)
            data_dict['open'].append(float(getattr(bar, 'open', 0) or getattr(bar, 'o', 0)))
            data_dict['high'].append(float(getattr(bar, 'high', 0) or getattr(bar, 'h', 0)))
            data_dict['low'].append(float(getattr(bar, 'low', 0) or getattr(bar, 'l', 0)))
            data_dict['close'].append(float(getattr(bar, 'close', 0) or getattr(bar, 'c', 0)))
            data_dict['volume'].append(int(getattr(bar, 'volume', 0) or getattr(bar, 'v', 0)))

        df = pd.DataFrame(data_dict)

        if not df.empty:
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)

        logger.debug(f"Converted {len(bars)} bars to DataFrame with shape {df.shape}")
        return df

    except Exception as e:
        logger.error(f"Error converting bars to DataFrame: {e}")
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])


def convert_dict_bars_to_dataframe(
    bars: List[dict],
    timestamp_key: str = "timestamp"
) -> pd.DataFrame:
    """Convert dictionary-format bars to a pandas DataFrame.

    Args:
        bars: List of dictionaries with OHLCV data
        timestamp_key: Key for the timestamp field

    Returns:
        DataFrame with OHLCV columns and timestamp as index
    """
    if not bars:
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

    try:
        df = pd.DataFrame(bars)

        # Standardize column names
        column_mapping = {
            't': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume',
        }
        df.rename(columns=column_mapping, inplace=True)

        # Set timestamp as index
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
        elif timestamp_key in df.columns:
            df.set_index(timestamp_key, inplace=True)

        # Ensure numeric types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df.sort_index(inplace=True)
        return df

    except Exception as e:
        logger.error(f"Error converting dict bars to DataFrame: {e}")
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])


def validate_ohlcv_data(df: pd.DataFrame) -> bool:
    """Validate that a DataFrame contains valid OHLCV data.

    This function replaces the duplicated validation in:
    - base_chart_widget.py:_validate_ohlcv_data

    Args:
        df: DataFrame to validate

    Returns:
        True if the DataFrame is valid OHLCV data, False otherwise

    Validation checks:
    - Required columns exist (open, high, low, close, volume)
    - No NaN values in price columns
    - high >= low for all rows
    - high >= open and high >= close for all rows
    - low <= open and low <= close for all rows
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for validation")
        return False

    required_columns = ['open', 'high', 'low', 'close', 'volume']

    # Check required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Missing required columns: {missing_columns}")
        return False

    # Check for NaN values in price columns
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if df[col].isna().any():
            logger.warning(f"NaN values found in column '{col}'")
            return False

    # Validate price relationships
    if not (df['high'] >= df['low']).all():
        logger.warning("Invalid OHLCV data: high < low for some rows")
        return False

    if not ((df['high'] >= df['open']) & (df['high'] >= df['close'])).all():
        logger.warning("Invalid OHLCV data: high is not the highest price")
        return False

    if not ((df['low'] <= df['open']) & (df['low'] <= df['close'])).all():
        logger.warning("Invalid OHLCV data: low is not the lowest price")
        return False

    return True


def convert_dataframe_to_ohlcv_list(
    df: pd.DataFrame,
    use_unix_timestamp: bool = True
) -> List[Tuple[Union[int, datetime], float, float, float, float, float]]:
    """Convert a DataFrame back to a list of OHLCV tuples.

    Useful for passing data to chart rendering functions that expect
    list format rather than DataFrame.

    Args:
        df: DataFrame with OHLCV data (timestamp as index)
        use_unix_timestamp: If True, convert timestamps to Unix epoch seconds

    Returns:
        List of (timestamp, open, high, low, close, volume) tuples
    """
    if df.empty:
        return []

    result = []
    for timestamp, row in df.iterrows():
        if use_unix_timestamp and isinstance(timestamp, datetime):
            ts = int(timestamp.timestamp())
        else:
            ts = timestamp

        result.append((
            ts,
            float(row['open']),
            float(row['high']),
            float(row['low']),
            float(row['close']),
            float(row.get('volume', 0))
        ))

    return result


def convert_dataframe_to_js_format(
    df: pd.DataFrame,
    include_volume: bool = True
) -> List[dict]:
    """Convert DataFrame to JavaScript-compatible format for TradingView charts.

    This is the format expected by lightweight-charts library.

    Args:
        df: DataFrame with OHLCV data
        include_volume: If True, include volume in output

    Returns:
        List of dictionaries in TradingView format:
        [{"time": 1234567890, "open": 100.0, "high": 105.0, "low": 99.0, "close": 103.0}]
    """
    if df.empty:
        return []

    result = []
    for timestamp, row in df.iterrows():
        # Convert timestamp to Unix epoch seconds
        if isinstance(timestamp, datetime):
            time_value = int(timestamp.timestamp())
        elif isinstance(timestamp, pd.Timestamp):
            time_value = int(timestamp.timestamp())
        else:
            time_value = int(timestamp)

        candle = {
            "time": time_value,
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
        }

        if include_volume and 'volume' in row:
            candle["volume"] = float(row['volume'])

        result.append(candle)

    return result


def resample_ohlcv(
    df: pd.DataFrame,
    target_timeframe: str = "1H"
) -> pd.DataFrame:
    """Resample OHLCV data to a different timeframe.

    Args:
        df: DataFrame with OHLCV data (timestamp as index)
        target_timeframe: Pandas-compatible timeframe string (e.g., '1H', '4H', '1D')

    Returns:
        Resampled DataFrame with OHLCV data
    """
    if df.empty:
        return df

    try:
        resampled = df.resample(target_timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        return resampled

    except Exception as e:
        logger.error(f"Error resampling OHLCV data: {e}")
        return df
