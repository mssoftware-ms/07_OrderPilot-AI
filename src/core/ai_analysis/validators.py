import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Tuple

class DataValidator:
    """
    Validates market data before analysis to prevent GIGO (Garbage In, Garbage Out).
    Implements checks for Lag, Bad Ticks, and Zero Volume.
    """
    
    def __init__(self, max_lag_multiplier: float = 1.5):
        self.max_lag_multiplier = max_lag_multiplier

    def validate_data(self, df: pd.DataFrame, interval_minutes: int) -> Tuple[bool, str]:
        """
        Runs all validation checks on the provided DataFrame.
        
        Args:
            df: OHLCV DataFrame
            interval_minutes: The chart interval in minutes
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if df is None or df.empty:
            return False, "DataFrame is empty or None."

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            return False, "DataFrame index is not DatetimeIndex."

        # 1. Timestamp Check
        if not self._check_timestamp(df, interval_minutes):
            last_time = df.index[-1]
            now = datetime.now(timezone.utc)
            return False, f"Data is stale. Last candle: {last_time}, Now: {now}"

        # 2. Zero Volume Check
        if not self._check_volume(df):
            return False, "Zero volume detected in critical recent candles."

        return True, ""

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns a cleaned copy of the DataFrame.
        Replaces extreme outliers (Z-Score > 4) in High/Low with rolling median.
        """
        df_clean = df.copy()
        
        # Calculate volatility (ATR-like or just StdDev of changes)
        # Here we use a simplified rolling Z-Score on High/Low relative to Close
        
        window = 20
        threshold = 4.0
        
        for col in ['high', 'low']:
            if col not in df_clean.columns:
                continue
                
            # Rolling Mean/Std
            rolling_mean = df_clean[col].rolling(window=window).mean()
            rolling_std = df_clean[col].rolling(window=window).std()
            
            # Z-Score
            z_score = (df_clean[col] - rolling_mean) / rolling_std.replace(0, 1) # Avoid div/0
            
            # Identify outliers
            outliers = z_score.abs() > threshold
            
            if outliers.any():
                # Replace with median of last 3
                # We can't easily do "median of last 3" in vector without a loop or shift
                # Simplified: Replace with rolling median
                rolling_median = df_clean[col].rolling(window=3).median()
                df_clean.loc[outliers, col] = rolling_median.loc[outliers]
                
        return df_clean

    def _check_timestamp(self, df: pd.DataFrame, interval_minutes: int) -> bool:
        """
        Checks if the last candle is within acceptable lag.
        """
        try:
            last_time = df.index[-1]
            
            # Handle timezone: Convert to UTC if tz-aware, else assume UTC if naive (or localize)
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            else:
                last_time = last_time.astimezone(timezone.utc)
                
            now = datetime.now(timezone.utc)
            
            # Allowed lag
            allowed_lag = timedelta(minutes=interval_minutes * self.max_lag_multiplier)
            
            # If weekend (Crypto is 24/7 so this is tricky. The checklist assumes Crypto/Alpaca)
            # If Stock, this might fail on weekends.
            # Assuming Crypto for now based on context ("Bitunix", "Crypto Analyst").
            # But let's be generous if lag is massive (e.g. > 1 week implies inactive chart)
            
            delta = now - last_time
            if delta > allowed_lag:
                # Debug log could go here
                return False
                
            return True
        except Exception:
            return False

    def _check_volume(self, df: pd.DataFrame, lookback: int = 5) -> bool:
        """
        Checks if any of the last N candles have 0 volume.
        """
        if 'volume' not in df.columns:
            # If no volume column, we can't check, assume valid? Or fail?
            # Alpaca/Bitunix usually have volume.
            return True 
            
        recent = df['volume'].tail(lookback)
        if (recent == 0).any():
            return False
            
        return True