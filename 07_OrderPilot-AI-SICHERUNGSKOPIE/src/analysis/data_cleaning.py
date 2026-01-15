"""Data Cleaning and Bad Tick Detection - Main Module.

Refactored main module that imports all detector classes and provides
convenience functions for historical data cleaning.

Module 6/6 of data_cleaning.py split - Main orchestrator.
"""

import logging

import pandas as pd

from .cleaning_types import CleaningStats
from .basic_bad_tick_detector import BadTickDetector
from .hampel_bad_tick_detector import HampelBadTickDetector
from .zscore_volatility_filter import ZScoreVolatilityFilter
from .stream_bad_tick_filter import StreamBadTickFilter

logger = logging.getLogger(__name__)


# Re-export all classes for backward compatibility
__all__ = [
    "CleaningStats",
    "BadTickDetector",
    "HampelBadTickDetector",
    "ZScoreVolatilityFilter",
    "StreamBadTickFilter",
    "clean_historical_data",
]


def clean_historical_data(
    symbol: str,
    source: str = "alpaca_crypto",
    db_path: str = "./data/orderpilot_historical.db",
    method: str = "remove",
    save_cleaned: bool = True,
) -> CleaningStats:
    """Clean historical data from database.

    Args:
        symbol: Symbol to clean (e.g., "alpaca_crypto:BTC/USD")
        source: Data source filter
        db_path: Path to SQLite database
        method: Cleaning method ("remove", "interpolate", "forward_fill")
        save_cleaned: Save cleaned data back to database

    Returns:
        Cleaning statistics
    """
    import sqlite3

    logger.info(f"🧹 Starting data cleaning for {symbol}...")

    # Load data from database
    conn = sqlite3.connect(db_path)
    query = f"""
        SELECT timestamp, open, high, low, close, volume
        FROM market_bars
        WHERE symbol = '{symbol}'
        ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn, parse_dates=['timestamp'])

    if df.empty:
        logger.warning(f"No data found for {symbol}")
        conn.close()
        return CleaningStats(0, 0, {}, 0.0)

    logger.info(f"Loaded {len(df)} bars for cleaning")

    # Clean data
    detector = BadTickDetector()
    df_clean, stats = detector.clean_data(df, method=method)

    if save_cleaned and stats.bad_ticks_removed > 0:
        # TODO: Implement database update
        # For now, we keep original data and mark bad ticks
        logger.info("💾 Would save cleaned data (not implemented yet)")

    conn.close()

    logger.info(f"✅ Cleaning complete: {stats.bad_ticks_removed}/{stats.total_bars} "
                f"bad ticks ({stats.cleaning_percentage:.2f}%)")

    return stats


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Clean Alpaca historical data
    stats = clean_historical_data(
        symbol="alpaca_crypto:BTC/USD",
        method="remove",
        save_cleaned=False
    )

    print(f"\n{'='*60}")
    print("CLEANING SUMMARY")
    print(f"{'='*60}")
    print(f"Total Bars: {stats.total_bars:,}")
    print(f"Bad Ticks Removed: {stats.bad_ticks_removed:,}")
    print(f"Cleaning Percentage: {stats.cleaning_percentage:.2f}%")
    print(f"{'='*60}")
