"""Tests for Cryptocurrency Integration.

Tests Alpaca cryptocurrency data provider and streaming functionality.
"""

import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.core.market_data import (
    AlpacaCryptoProvider,
    AlpacaCryptoStreamClient,
    AssetClass,
    DataRequest,
    DataSource,
    HistoryManager,
    Timeframe
)
from src.config import DatabaseConfig
from src.database.database import initialize_database


# Skip tests if Alpaca credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("ALPACA_API_KEY") or not os.getenv("ALPACA_API_SECRET"),
    reason="Alpaca credentials not found in environment"
)


@pytest.fixture
def alpaca_credentials():
    """Get Alpaca credentials from environment."""
    return {
        "api_key": os.getenv("ALPACA_API_KEY"),
        "api_secret": os.getenv("ALPACA_API_SECRET")
    }


@pytest.fixture
def crypto_provider(alpaca_credentials):
    """Create Alpaca crypto provider."""
    return AlpacaCryptoProvider(
        api_key=alpaca_credentials["api_key"],
        api_secret=alpaca_credentials["api_secret"]
    )


@pytest.fixture
def crypto_stream_client(alpaca_credentials):
    """Create Alpaca crypto stream client."""
    return AlpacaCryptoStreamClient(
        api_key=alpaca_credentials["api_key"],
        api_secret=alpaca_credentials["api_secret"]
    )


class TestAlpacaCryptoProvider:
    """Tests for Alpaca cryptocurrency data provider."""

    @pytest.mark.asyncio
    async def test_provider_initialization(self, crypto_provider):
        """Test crypto provider initialization."""
        assert crypto_provider.name == "AlpacaCrypto"
        assert await crypto_provider.is_available()

    @pytest.mark.asyncio
    async def test_fetch_btc_bars(self, crypto_provider):
        """Test fetching BTC/USD historical bars."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)

        bars = await crypto_provider.fetch_bars(
            symbol="BTC/USD",
            start_date=start_date,
            end_date=end_date,
            timeframe=Timeframe.HOUR_1
        )

        if getattr(crypto_provider, "auth_failed", False):
            pytest.skip("Alpaca credentials invalid or unauthorized")

        assert len(bars) > 0, "Should fetch at least some bars"
        assert all(bar.symbol == "BTC/USD" for bar in bars if hasattr(bar, 'symbol')), \
            "All bars should be for BTC/USD"
        assert all(isinstance(bar.close, Decimal) for bar in bars), \
            "Prices should be Decimal"
        assert all(bar.source == "alpaca_crypto" for bar in bars), \
            "Source should be alpaca_crypto"

    @pytest.mark.asyncio
    async def test_fetch_eth_bars(self, crypto_provider):
        """Test fetching ETH/USD historical bars."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=6)

        bars = await crypto_provider.fetch_bars(
            symbol="ETH/USD",
            start_date=start_date,
            end_date=end_date,
            timeframe=Timeframe.MINUTE_15
        )

        if getattr(crypto_provider, "auth_failed", False):
            pytest.skip("Alpaca credentials invalid or unauthorized")

        assert len(bars) > 0, "Should fetch at least some bars"
        assert all(bar.volume >= 0 for bar in bars), "Volume should be non-negative"

    @pytest.mark.asyncio
    async def test_fetch_multiple_crypto_pairs(self, crypto_provider):
        """Test fetching data for multiple crypto trading pairs."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=3)

        crypto_pairs = ["BTC/USD", "ETH/USD", "SOL/USD"]

        for symbol in crypto_pairs:
            bars = await crypto_provider.fetch_bars(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=Timeframe.MINUTE_30
            )
            if getattr(crypto_provider, "auth_failed", False):
                pytest.skip("Alpaca credentials invalid or unauthorized")
            assert len(bars) > 0, f"Should fetch bars for {symbol}"


class TestAlpacaCryptoStreamClient:
    """Tests for Alpaca cryptocurrency stream client."""

    @pytest.mark.asyncio
    async def test_stream_initialization(self, crypto_stream_client):
        """Test crypto stream client initialization."""
        assert crypto_stream_client.name == "AlpacaCryptoStream"
        assert not crypto_stream_client.connected

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, crypto_stream_client):
        """Test connecting and disconnecting crypto stream."""
        # Connect
        connected = await crypto_stream_client.connect()
        assert connected, "Should connect successfully"
        assert crypto_stream_client.connected

        # Disconnect
        await crypto_stream_client.disconnect()
        assert not crypto_stream_client.connected

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Live streaming test - requires manual verification")
    async def test_subscribe_to_crypto(self, crypto_stream_client):
        """Test subscribing to crypto symbols."""
        symbols = ["BTC/USD", "ETH/USD"]

        # Connect
        await crypto_stream_client.connect()

        # Subscribe
        await crypto_stream_client.subscribe(symbols)
        assert symbols[0] in crypto_stream_client.metrics.subscribed_symbols
        assert symbols[1] in crypto_stream_client.metrics.subscribed_symbols

        # Wait for some data (manual test)
        await asyncio.sleep(5)

        # Unsubscribe
        await crypto_stream_client.unsubscribe(symbols)

        # Disconnect
        await crypto_stream_client.disconnect()


class TestHistoryManagerCrypto:
    """Tests for HistoryManager cryptocurrency integration."""

    @pytest.fixture
    def history_manager(self, alpaca_credentials):
        """Create history manager with crypto support."""
        temp_dir = tempfile.mkdtemp()
        initialize_database(DatabaseConfig(path=os.path.join(temp_dir, "orderpilot.db")))
        # Create manager (will auto-register Alpaca crypto provider if enabled)
        manager = HistoryManager()
        return manager

    @pytest.mark.asyncio
    async def test_fetch_crypto_data(self, history_manager):
        """Test fetching crypto data through HistoryManager."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=6)

        request = DataRequest(
            symbol="BTC/USD",
            start_date=start_date,
            end_date=end_date,
            timeframe=Timeframe.HOUR_1,
            asset_class=AssetClass.CRYPTO
        )

        bars, source = await history_manager.fetch_data(request)

        provider = history_manager.providers.get(DataSource.ALPACA_CRYPTO)
        if not provider or not getattr(provider, "api_key", None) or not getattr(provider, "api_secret", None):
            pytest.skip("Alpaca credentials not configured")
        if getattr(provider, "auth_failed", False):
            pytest.skip("Alpaca credentials invalid or unauthorized")

        assert len(bars) > 0, "Should fetch crypto bars"
        assert source in ["alpaca_crypto", "database"], \
            f"Source should be crypto-compatible, got: {source}"

    @pytest.mark.asyncio
    async def test_asset_class_filtering(self, history_manager):
        """Test that crypto requests only use crypto providers."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=2)

        # Request with CRYPTO asset class
        crypto_request = DataRequest(
            symbol="ETH/USD",
            start_date=start_date,
            end_date=end_date,
            timeframe=Timeframe.MINUTE_30,
            asset_class=AssetClass.CRYPTO
        )

        bars, source = await history_manager.fetch_data(crypto_request)

        provider = history_manager.providers.get(DataSource.ALPACA_CRYPTO)
        if provider and getattr(provider, "auth_failed", False):
            pytest.skip("Alpaca credentials invalid or unauthorized")

        # Should use crypto provider if available
        if bars:
            assert source in ["alpaca_crypto", "database"], \
                "Crypto request should use crypto provider"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Live streaming test - requires manual verification")
    async def test_start_crypto_stream(self, history_manager):
        """Test starting crypto real-time stream."""
        symbols = ["BTC/USD", "ETH/USD"]

        # Start crypto stream
        started = await history_manager.start_crypto_realtime_stream(symbols)
        assert started, "Should start crypto stream"

        # Wait for some data
        await asyncio.sleep(5)

        # Stop stream
        await history_manager.stop_crypto_realtime_stream()


class TestCryptoDataValidation:
    """Tests for crypto data validation and correctness."""

    @pytest.mark.asyncio
    async def test_crypto_price_ranges(self, crypto_provider):
        """Test that crypto prices are within reasonable ranges."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=1)

        bars = await crypto_provider.fetch_bars(
            symbol="BTC/USD",
            start_date=start_date,
            end_date=end_date,
            timeframe=Timeframe.MINUTE_15
        )

        for bar in bars:
            # BTC should be > $1,000 and < $1,000,000
            assert 1000 < bar.close < 1000000, \
                f"BTC price seems unreasonable: ${bar.close}"
            # OHLC validation
            assert bar.low <= bar.high, "Low should be <= High"
            assert bar.low <= bar.open <= bar.high, "Open should be between Low and High"
            assert bar.low <= bar.close <= bar.high, "Close should be between Low and High"

    @pytest.mark.asyncio
    async def test_crypto_timestamp_ordering(self, crypto_provider):
        """Test that crypto bars are properly ordered by timestamp."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=2)

        bars = await crypto_provider.fetch_bars(
            symbol="ETH/USD",
            start_date=start_date,
            end_date=end_date,
            timeframe=Timeframe.MINUTE_30
        )

        # Check timestamps are in ascending order
        for i in range(len(bars) - 1):
            assert bars[i].timestamp <= bars[i + 1].timestamp, \
                "Bars should be ordered by timestamp"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
