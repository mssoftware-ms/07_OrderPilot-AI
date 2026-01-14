from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np

class SimulationIndicatorsMixin:
    """Indicator calculations (Bollinger Bands, ADX, ATR, RSI, OBV, True Range)"""

    def _calculate_bollinger_bands(
        self, df: pd.DataFrame, period: int = 20, std_mult: float = 2.0
    ) -> tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands for SWING trailing mode.

        Returns:
            Tuple of (lower_band, upper_band)
        """
        close = df["close"]
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        lower_band = sma - (std * std_mult)
        upper_band = sma + (std * std_mult)

        # Backfill NaN values
        lower_band = lower_band.bfill()
        upper_band = upper_band.bfill()

        return lower_band, upper_band

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX (Average Directional Index) for regime detection.

        ADX > 25 = Trending market
        ADX < 20 = Ranging market
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # True Range
        tr1 = high - low
        tr2 = np.abs(high - close.shift())
        tr3 = np.abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[(plus_dm < minus_dm) | (plus_dm < 0)] = 0
        minus_dm[(minus_dm < plus_dm) | (minus_dm < 0)] = 0

        # Wilder's smoothing
        alpha = 1.0 / period
        atr = tr.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean() / atr)

        # ADX calculation
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

        # Backfill NaN values
        adx = adx.bfill().fillna(25.0)

        return adx

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range using Wilder's Smoothing Method.

        Reference: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-atr
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Use Wilder's smoothing (EMA with alpha = 1/period)
        alpha = 1.0 / period
        atr = true_range.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

        # Fill NaN values with the first valid ATR (backfill)
        atr = atr.bfill()
        return atr

    def _true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range."""
        return self._signal_generator._true_range(df)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        return self._signal_generator._calculate_rsi(prices, period)

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        return self._signal_generator._calculate_obv(df)

