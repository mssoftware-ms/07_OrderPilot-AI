"""
Data Loader for Backtesting.

Fetches data from the SQLite database and handles resampling.
"""

import logging
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

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
        if not Path(self.db_path).exists():
            # Try backup path if main path doesn't exist
            backup_path = Path("backup_db/data/orderpilot.db") # Guessing structure based on listing
            if backup_path.exists():
                self.db_path = str(backup_path)
            else:
                # Try finding it
                found = list(Path(".").glob("**/orderpilot.db"))
                if found:
                    self.db_path = str(found[0])
                else:
                    logger.error(f"Database not found at {self.db_path}")
                    return pd.DataFrame()

        try:
            conn = sqlite3.connect(self.db_path)
            
            # Construct query
            query = "SELECT timestamp, open, high, low, close, volume FROM market_bars WHERE symbol = ?"
            params = [symbol] # e.g. "bitunix:BTCUSDT" or "BTCUSDT" depending on migration status
            
            # Check if source column exists (it might not in older schemas, but checked bitunix_historical_data_db.py and it uses it)
            # Actually, let's just query by symbol. The user said "bitunix:BTCUSDT" might be used or stripped.
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
                
            query += " ORDER BY timestamp ASC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if df.empty:
                logger.warning(f"No data found for {symbol} in {self.db_path}")
                return df

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
