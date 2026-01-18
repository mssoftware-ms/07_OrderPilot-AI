"""
Data Loader for Backtesting.

Fetches data from SQLite database with automatic fallback to Bitunix API for live data.
"""

import logging
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Lazy import API client (only when needed)
_api_client = None


def _get_api_client():
    """Lazy initialization of Bitunix API client"""
    global _api_client
    if _api_client is None:
        try:
            from src.brokers.bitunix.api_client import BitunixAPIClient
            _api_client = BitunixAPIClient()
            logger.info("Bitunix API client initialized")
        except ImportError as e:
            logger.warning(f"Could not import Bitunix API client: {e}")
            _api_client = False  # Mark as unavailable
    return _api_client if _api_client is not False else None

class DataLoader:
    def __init__(self, db_path: str = "data/orderpilot.db"):
        self.db_path = db_path

    def load_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source: str = "bitunix"
    ) -> pd.DataFrame:
        """
        Load market data from SQLite.

        Returns:
            DataFrame with index as DatetimeIndex and columns: open, high, low, close, volume
        """
        # Try multiple database paths in order
        db_paths = [
            self.db_path,
            "data/orderpilot_historical.db",  # Historical data fallback
            "backup_db/data/orderpilot.db",    # Backup fallback
        ]

        working_db = None
        for db_path in db_paths:
            if Path(db_path).exists():
                # Test if database is readable
                try:
                    test_conn = sqlite3.connect(db_path)
                    test_conn.execute("SELECT 1")
                    test_conn.close()
                    working_db = db_path
                    logger.info(f"Using database: {db_path}")
                    break
                except Exception as e:
                    logger.warning(f"Database {db_path} is not readable: {e}")
                    continue

        if not working_db:
            logger.error("No readable database found")
            return pd.DataFrame()

        self.db_path = working_db

        try:
            conn = sqlite3.connect(self.db_path)

            # Try both symbol formats (with and without prefix)
            symbol_variants = [
                symbol,                           # Original (e.g., "BTCUSDT")
                f"bitunix:{symbol}",             # With bitunix prefix
                symbol.replace("bitunix:", ""),  # Without prefix (if already prefixed)
            ]

            df = pd.DataFrame()
            for sym in symbol_variants:
                # Construct query
                query = "SELECT timestamp, open, high, low, close, volume FROM market_bars WHERE symbol = ?"
                params = [sym]

                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())

                query += " ORDER BY timestamp ASC"

                df = pd.read_sql_query(query, conn, params=params)

                if not df.empty:
                    logger.info(f"Found {len(df)} rows for symbol '{sym}'")
                    break

            conn.close()

            if df.empty:
                logger.warning(f"No data found in database for {symbol} (tried variants: {symbol_variants})")

                # Fallback to Bitunix API if dates are provided
                if start_date and end_date:
                    logger.info("Attempting to fetch data from Bitunix API...")
                    api_client = _get_api_client()

                    if api_client:
                        try:
                            # Strip 'bitunix:' prefix if present for API call
                            api_symbol = symbol.replace("bitunix:", "")

                            # Fetch from API (defaults to 1m interval)
                            df = api_client.get_klines_range(
                                symbol=api_symbol,
                                interval="1m",
                                start_date=start_date,
                                end_date=end_date
                            )

                            if not df.empty:
                                logger.info(f"✅ Successfully fetched {len(df)} candles from Bitunix API")
                                return df
                            else:
                                logger.warning("API returned no data")
                        except Exception as e:
                            logger.error(f"Error fetching from API: {e}")

                return df  # Return empty DataFrame if all methods fail

            # Parse timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

            # Ensure numeric columns
            cols = ['open', 'high', 'low', 'close', 'volume']
            for col in cols:
                df[col] = pd.to_numeric(df[col])

            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return pd.DataFrame()

    def resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample 1m data to target timeframe.
        
        Args:
            df: 1m DataFrame
            timeframe: e.g. '5m', '1h', '1d'
        """
        if df.empty:
            return df
            
        # Map generic timeframes to pandas offsets
        tf_map = {
            '1m': '1T', '3m': '3T', '5m': '5T', '15m': '15T', '30m': '30T',
            '1h': '1H', '2h': '2H', '4h': '4H', '6h': '6H', '8h': '8H', '12h': '12H',
            '1d': '1D', '1w': '1W'
        }
        
        offset = tf_map.get(timeframe)
        if not offset:
            logger.warning(f"Unknown timeframe format: {timeframe}, defaulting to 1m")
            return df
            
        # Resample logic
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        resampled = df.resample(offset).agg(agg_dict).dropna()
        return resampled
