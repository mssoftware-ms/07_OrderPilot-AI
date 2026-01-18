"""
Bitunix API Client for live data fetching.

Provides direct access to Bitunix market data without requiring a database.
"""

import logging
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class BitunixAPIClient:
    """Client for Bitunix Futures API"""

    BASE_URL = "https://fapi.bitunix.com"

    INTERVALS = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "12h": "12h",
        "1d": "1d",
        "1w": "1w"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "15m",
        limit: int = 200,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch kline/candlestick data from Bitunix API.

        Args:
            symbol: Trading pair (e.g. BTCUSDT)
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w)
            limit: Number of candles (max 200)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds

        Returns:
            List of kline data dicts
        """
        endpoint = f"{self.BASE_URL}/api/v1/futures/market/kline"

        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 200)
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                klines = data.get("data", [])
                logger.info(f"Fetched {len(klines)} klines for {symbol} {interval}")
                return klines
            else:
                error_msg = data.get('msg', 'Unknown error')
                logger.error(f"API Error: {error_msg}")
                return []

        except requests.RequestException as e:
            logger.error(f"Request Error: {e}")
            return []

    def get_klines_range(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Fetch klines for a date range (handles pagination for >200 candles).

        Args:
            symbol: Trading pair
            interval: Timeframe
            start_date: Start datetime
            end_date: End datetime

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        all_klines = []
        current_start = start_ms

        # Calculate interval in milliseconds for pagination
        interval_ms = self._interval_to_milliseconds(interval)

        max_iterations = 100  # Safety limit
        iterations = 0

        while current_start < end_ms and iterations < max_iterations:
            iterations += 1

            # Fetch batch
            batch = self.get_klines(
                symbol=symbol,
                interval=interval,
                limit=200,
                start_time=current_start,
                end_time=end_ms
            )

            if not batch:
                break

            all_klines.extend(batch)

            # Update start time to last candle + 1 interval
            last_time = int(batch[-1].get("time", 0))
            current_start = last_time + interval_ms

            # Avoid rate limiting
            if len(batch) < 200:
                break  # Got all data

        if not all_klines:
            logger.warning(f"No klines fetched for {symbol} {interval}")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': pd.to_datetime(k.get("time", 0), unit='ms'),
                'open': float(k.get("open", 0)),
                'high': float(k.get("high", 0)),
                'low': float(k.get("low", 0)),
                'close': float(k.get("close", 0)),
                'volume': float(k.get("baseVol", 0) or 0)
            }
            for k in all_klines
        ])

        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        logger.info(f"Fetched {len(df)} total klines for {symbol} {interval} from {start_date} to {end_date}")

        return df

    def _interval_to_milliseconds(self, interval: str) -> int:
        """Convert interval string to milliseconds"""
        units = {
            'm': 60 * 1000,
            'h': 60 * 60 * 1000,
            'd': 24 * 60 * 60 * 1000,
            'w': 7 * 24 * 60 * 60 * 1000
        }

        if interval == '1m':
            return 1 * units['m']
        elif interval == '5m':
            return 5 * units['m']
        elif interval == '15m':
            return 15 * units['m']
        elif interval == '30m':
            return 30 * units['m']
        elif interval == '1h':
            return 1 * units['h']
        elif interval == '2h':
            return 2 * units['h']
        elif interval == '4h':
            return 4 * units['h']
        elif interval == '6h':
            return 6 * units['h']
        elif interval == '12h':
            return 12 * units['h']
        elif interval == '1d':
            return 1 * units['d']
        elif interval == '1w':
            return 1 * units['w']
        else:
            return 15 * units['m']  # Default to 15m
