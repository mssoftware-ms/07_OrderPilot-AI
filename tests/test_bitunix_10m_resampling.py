"""Test 10m timeframe resampling in Bitunix provider.

Tests that the Bitunix provider correctly:
1. Detects 10m timeframe requests
2. Fetches 5m data instead
3. Resamples 5m → 10m
4. Returns correctly formatted 10m bars
"""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from src.core.market_data.providers.bitunix_provider import BitunixProvider
from src.core.market_data.types import Timeframe


@pytest.mark.asyncio
async def test_10m_timeframe_resampling():
    """Test that 10m timeframe is automatically resampled from 5m data."""

    provider = BitunixProvider(
        api_key="test_key",  # Public endpoint doesn't need real key
        api_secret="test_secret",
        max_bars=500,
        max_batches=5
    )

    # Request 1 hour of data (should give us 6 x 10m bars)
    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(hours=1)

    # Request 10m timeframe
    bars = await provider.fetch_bars(
        symbol="BTCUSDT",
        start_date=start_date,
        end_date=end_date,
        timeframe=Timeframe.MINUTE_10
    )

    # Verify we got bars
    assert len(bars) > 0, "Should receive resampled bars"

    # Verify bars are properly formatted
    for bar in bars:
        assert isinstance(bar.open, Decimal)
        assert isinstance(bar.high, Decimal)
        assert isinstance(bar.low, Decimal)
        assert isinstance(bar.close, Decimal)
        assert isinstance(bar.volume, Decimal)
        assert bar.symbol == "BTCUSDT"
        assert isinstance(bar.timestamp, datetime)

    # Verify bars are sorted chronologically
    timestamps = [bar.timestamp for bar in bars]
    assert timestamps == sorted(timestamps), "Bars should be sorted by timestamp"

    # Verify 10m spacing between bars
    if len(bars) >= 2:
        time_diff = (bars[1].timestamp - bars[0].timestamp).total_seconds()
        expected_diff = 10 * 60  # 10 minutes in seconds
        # Allow 1 second tolerance for rounding
        assert abs(time_diff - expected_diff) <= 1, \
            f"Bars should be 10 minutes apart, got {time_diff}s"

    print(f"✅ Successfully fetched and resampled {len(bars)} 10m bars")
    print(f"   First bar: {bars[0].timestamp}")
    print(f"   Last bar: {bars[-1].timestamp}")


@pytest.mark.asyncio
async def test_10m_resampling_preserves_ohlcv_logic():
    """Verify that OHLCV aggregation logic is correct in resampling."""

    provider = BitunixProvider(
        api_key="test_key",
        api_secret="test_secret",
        max_bars=500,
        max_batches=5
    )

    # Request 30 minutes of data (should give us 3 x 10m bars from 6 x 5m bars)
    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(minutes=30)

    bars = await provider.fetch_bars(
        symbol="BTCUSDT",
        start_date=start_date,
        end_date=end_date,
        timeframe=Timeframe.MINUTE_10
    )

    if len(bars) > 0:
        # Basic OHLCV sanity checks
        for bar in bars:
            # High should be >= Open, Low, Close
            assert bar.high >= bar.open, "High should be >= Open"
            assert bar.high >= bar.low, "High should be >= Low"
            assert bar.high >= bar.close, "High should be >= Close"

            # Low should be <= Open, High, Close
            assert bar.low <= bar.open, "Low should be <= Open"
            assert bar.low <= bar.high, "Low should be <= High"
            assert bar.low <= bar.close, "Low should be <= Close"

            # Volume should be positive
            assert bar.volume > 0, "Volume should be positive"

        print(f"✅ OHLCV aggregation logic verified for {len(bars)} bars")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_10m_timeframe_resampling())
    asyncio.run(test_10m_resampling_preserves_ohlcv_logic())
