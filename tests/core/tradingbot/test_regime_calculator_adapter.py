"""Unit tests for RegimeCalculatorAdapter.

Tests the adapter layer between regime_engine_json and IndicatorCalculatorFactory.
"""

import pytest
import pandas as pd
import numpy as np
from src.core.tradingbot.regime_calculator_adapter import RegimeCalculatorAdapter


@pytest.fixture
def sample_data():
    """Generate sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')

    close = 100 + np.cumsum(np.random.randn(100) * 0.5)
    high = close + np.abs(np.random.randn(100) * 0.3)
    low = close - np.abs(np.random.randn(100) * 0.3)
    open_price = close + np.random.randn(100) * 0.2
    volume = np.random.randint(1000, 10000, size=100)

    return pd.DataFrame({
        'timestamp': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })


@pytest.fixture
def adapter():
    """Create RegimeCalculatorAdapter instance."""
    return RegimeCalculatorAdapter()


class TestRegimeCalculatorAdapter:
    """Test suite for RegimeCalculatorAdapter."""

    def test_initialization_is_lazy(self):
        """Test that factory initialization is lazy."""
        adapter = RegimeCalculatorAdapter()
        assert not adapter._initialized
        assert adapter._factory is None

    def test_transform_params_simple(self, adapter):
        """Test parameter transformation from list to dict."""
        params = [{"name": "period", "value": 14}]
        result = adapter._transform_params(params)
        assert result == {"period": 14}

    def test_transform_params_multiple(self, adapter):
        """Test parameter transformation with multiple params."""
        params = [
            {"name": "fast", "value": 12},
            {"name": "slow", "value": 26},
            {"name": "signal", "value": 9}
        ]
        result = adapter._transform_params(params)
        assert result == {"fast": 12, "slow": 26, "signal": 9}

    def test_transform_params_empty(self, adapter):
        """Test parameter transformation with empty list."""
        result = adapter._transform_params([])
        assert result == {}

    def test_map_indicator_type_passthrough(self, adapter):
        """Test that all types pass through unchanged."""
        # Calculators use the same short codes as regime_engine_json
        assert adapter._map_indicator_type("BB") == "BB"
        assert adapter._map_indicator_type("STOCH") == "STOCH"
        assert adapter._map_indicator_type("RSI") == "RSI"
        assert adapter._map_indicator_type("MACD") == "MACD"
        assert adapter._map_indicator_type("ADX") == "ADX"

    def test_calculate_rsi(self, adapter, sample_data):
        """Test RSI calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "RSI",
            [{"name": "period", "value": 14}]
        )

        assert "rsi" in result
        assert isinstance(result["rsi"], float)
        assert 0 <= result["rsi"] <= 100

    def test_calculate_macd(self, adapter, sample_data):
        """Test MACD calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "MACD",
            [
                {"name": "fast", "value": 12},
                {"name": "slow", "value": 26},
                {"name": "signal", "value": 9}
            ]
        )

        assert "macd" in result
        assert "signal" in result
        assert "hist" in result
        assert all(isinstance(result[k], float) for k in ["macd", "signal", "hist"])

    def test_calculate_adx(self, adapter, sample_data):
        """Test ADX calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "ADX",
            [{"name": "period", "value": 14}]
        )

        assert "adx" in result
        assert "di_diff" in result
        assert isinstance(result["adx"], float)
        assert 0 <= result["adx"] <= 100

    def test_calculate_atr(self, adapter, sample_data):
        """Test ATR calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "ATR",
            [{"name": "period", "value": 14}]
        )

        assert "atr" in result
        assert "atr_percent" in result
        assert isinstance(result["atr"], float)
        assert isinstance(result["atr_percent"], float)
        assert result["atr"] > 0
        assert result["atr_percent"] > 0

    def test_calculate_bb(self, adapter, sample_data):
        """Test Bollinger Bands calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "BB",
            [
                {"name": "period", "value": 20},
                {"name": "mult", "value": 2.0}
            ]
        )

        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        # width may be None depending on calculator implementation

    def test_calculate_stochastic(self, adapter, sample_data):
        """Test Stochastic calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "STOCH",
            [
                {"name": "k", "value": 14},
                {"name": "d", "value": 3}
            ]
        )

        assert "k" in result
        assert "d" in result
        assert isinstance(result["k"], float)
        assert isinstance(result["d"], float)

    def test_calculate_mfi(self, adapter, sample_data):
        """Test MFI calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "MFI",
            [{"name": "period", "value": 14}]
        )

        assert "mfi" in result
        assert isinstance(result["mfi"], float)

    def test_calculate_cci(self, adapter, sample_data):
        """Test CCI calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "CCI",
            [{"name": "period", "value": 20}]
        )

        assert "cci" in result
        assert isinstance(result["cci"], float)

    def test_calculate_chop(self, adapter, sample_data):
        """Test CHOP calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "CHOP",
            [{"name": "period", "value": 14}]
        )

        assert "chop" in result
        assert isinstance(result["chop"], float)

    def test_calculate_ema(self, adapter, sample_data):
        """Test EMA calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "EMA",
            [{"name": "period", "value": 20}]
        )

        assert "value" in result
        assert isinstance(result["value"], float)

    def test_calculate_sma(self, adapter, sample_data):
        """Test SMA calculation through adapter."""
        result = adapter.calculate_indicator(
            sample_data,
            "SMA",
            [{"name": "period", "value": 20}]
        )

        assert "value" in result
        assert isinstance(result["value"], float)

    def test_unsupported_indicator_raises_error(self, adapter, sample_data):
        """Test that unsupported indicator types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported indicator type"):
            adapter.calculate_indicator(
                sample_data,
                "UNKNOWN_TYPE",
                []
            )

    def test_factory_initialized_after_first_call(self, adapter, sample_data):
        """Test that factory is initialized after first calculation."""
        assert not adapter._initialized

        adapter.calculate_indicator(
            sample_data,
            "RSI",
            [{"name": "period", "value": 14}]
        )

        assert adapter._initialized
        assert adapter._factory is not None

    def test_factory_not_reinitialized_on_second_call(self, adapter, sample_data):
        """Test that factory is not reinitialized on subsequent calls."""
        # First call
        adapter.calculate_indicator(
            sample_data,
            "RSI",
            [{"name": "period", "value": 14}]
        )

        factory_instance = adapter._factory

        # Second call
        adapter.calculate_indicator(
            sample_data,
            "EMA",
            [{"name": "period", "value": 20}]
        )

        # Same factory instance should be reused
        assert adapter._factory is factory_instance
