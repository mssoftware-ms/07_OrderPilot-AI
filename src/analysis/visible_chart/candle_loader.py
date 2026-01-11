"""Candle Data Loader for Visible Chart Analyzer.

Loads candle data from database or generates mock data for testing.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class CandleLoader:
    """Loads candle data for the visible chart range.

    Tries database first (MarketBar table), then falls back to mock data.
    Supports aggregation from 1-second bars to target timeframe.
    """

    def load(
        self,
        symbol: str,
        from_ts: int,
        to_ts: int,
        timeframe: str,
    ) -> list[dict]:
        """Load candle data for the visible range.

        Tries database first, then falls back to mock data for testing.

        Args:
            symbol: Trading symbol.
            from_ts: Start timestamp (Unix seconds).
            to_ts: End timestamp (Unix seconds).
            timeframe: Candle timeframe (1m, 5m, 15m, 1h).

        Returns:
            List of candle dicts with OHLCV data.
        """
        # Try loading from database
        candles = self._load_from_database(symbol, from_ts, to_ts, timeframe)

        if candles:
            logger.info(
                "Loaded %d candles from database for %s", len(candles), symbol
            )
            return candles

        # Fallback: Generate mock candles for testing
        logger.debug("No database data found, generating mock candles")
        return self._generate_mock_candles(from_ts, to_ts)

    def _load_from_database(
        self,
        symbol: str,
        from_ts: int,
        to_ts: int,
        timeframe: str,
    ) -> list[dict]:
        """Load candles from the MarketBar database table.

        Args:
            symbol: Trading symbol.
            from_ts: Start timestamp (Unix seconds).
            to_ts: End timestamp (Unix seconds).
            timeframe: Candle timeframe.

        Returns:
            List of candle dicts, or empty list if not available.
        """
        try:
            from datetime import datetime

            from sqlalchemy import and_

            from src.database import get_db_manager
            from src.database.models import MarketBar

            db = get_db_manager()
            session = db.get_session()

            try:
                # Convert timestamps to datetime
                start_dt = datetime.utcfromtimestamp(from_ts)
                end_dt = datetime.utcfromtimestamp(to_ts)

                # Query MarketBar table
                query = (
                    session.query(MarketBar)
                    .filter(
                        and_(
                            MarketBar.symbol == symbol.upper(),
                            MarketBar.timestamp >= start_dt,
                            MarketBar.timestamp <= end_dt,
                        )
                    )
                    .order_by(MarketBar.timestamp)
                )

                bars = query.all()

                if not bars:
                    return []

                # Convert to candle dicts
                candles = []
                for bar in bars:
                    candles.append(
                        {
                            "timestamp": int(bar.timestamp.timestamp()),
                            "open": float(bar.open),
                            "high": float(bar.high),
                            "low": float(bar.low),
                            "close": float(bar.close),
                            "volume": float(bar.volume) if bar.volume else 0.0,
                        }
                    )

                # For timeframes > 1 second, aggregate
                if timeframe in ("1m", "5m", "15m", "1h"):
                    candles = self._aggregate_candles(candles, timeframe)

                return candles

            finally:
                session.close()

        except ImportError as e:
            logger.debug("Database module not available: %s", e)
            return []
        except Exception as e:
            logger.warning("Failed to load from database: %s", e)
            return []

    def _aggregate_candles(
        self, candles: list[dict], timeframe: str
    ) -> list[dict]:
        """Aggregate 1-second candles to target timeframe.

        Args:
            candles: List of 1-second candles.
            timeframe: Target timeframe (1m, 5m, 15m, 1h).

        Returns:
            Aggregated candles.
        """
        if not candles:
            return []

        # Timeframe to seconds
        tf_seconds = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
        }.get(timeframe, 60)

        aggregated = []
        bucket: list[dict] = []
        bucket_start: int | None = None

        for candle in candles:
            ts = candle["timestamp"]
            bucket_key = (ts // tf_seconds) * tf_seconds

            if bucket_start is None:
                bucket_start = bucket_key

            if bucket_key != bucket_start:
                # Finish current bucket
                if bucket:
                    aggregated.append(self._merge_bucket(bucket, bucket_start))
                bucket = [candle]
                bucket_start = bucket_key
            else:
                bucket.append(candle)

        # Final bucket
        if bucket and bucket_start is not None:
            aggregated.append(self._merge_bucket(bucket, bucket_start))

        return aggregated

    def _merge_bucket(self, bucket: list[dict], bucket_ts: int) -> dict:
        """Merge a bucket of candles into one OHLCV candle.

        Args:
            bucket: List of candles in the bucket.
            bucket_ts: Timestamp for the aggregated candle.

        Returns:
            Aggregated candle dict.
        """
        return {
            "timestamp": bucket_ts,
            "open": bucket[0]["open"],
            "high": max(c["high"] for c in bucket),
            "low": min(c["low"] for c in bucket),
            "close": bucket[-1]["close"],
            "volume": sum(c["volume"] for c in bucket),
        }

    def _generate_mock_candles(self, from_ts: int, to_ts: int) -> list[dict]:
        """Generate mock candles for testing when no database data available.

        Args:
            from_ts: Start timestamp.
            to_ts: End timestamp.

        Returns:
            List of mock candle dicts.
        """
        import random

        candles = []
        current_ts = from_ts
        base_price = 45000.0  # Example BTC price

        while current_ts <= to_ts:
            # Random price movement
            change = random.uniform(-0.002, 0.002)
            open_price = base_price
            close_price = base_price * (1 + change)
            high_price = max(open_price, close_price) * (
                1 + random.uniform(0, 0.001)
            )
            low_price = min(open_price, close_price) * (
                1 - random.uniform(0, 0.001)
            )

            candles.append(
                {
                    "timestamp": current_ts,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": random.uniform(10, 100),
                }
            )

            base_price = close_price
            current_ts += 60  # 1 minute

        logger.debug("Generated %d mock candles", len(candles))
        return candles
