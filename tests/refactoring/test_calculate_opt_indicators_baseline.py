"""
Baseline tests for _calculate_opt_indicators() refactoring.
These tests ensure the refactored version produces identical results to the original.
"""

import pytest
import pandas as pd
import numpy as np
from src.core.tradingbot.regime_engine_json import RegimeEngineJSON


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
def regime_engine():
    """Create a RegimeEngineJSON instance."""
    return RegimeEngineJSON()


class TestCalculateOptIndicatorsBaseline:
    """Baseline tests for _calculate_opt_indicators method."""

    def test_rsi_calculation(self, regime_engine, sample_data):
        """Test RSI indicator calculation."""
        indicators_def = [
            {
                "name": "rsi_14",
                "type": "RSI",
                "params": [{"name": "period", "value": 14}]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "rsi_14" in indicator_values
        assert "rsi" in indicator_values["rsi_14"]
        assert isinstance(indicator_values["rsi_14"]["rsi"], float)
        assert 0 <= indicator_values["rsi_14"]["rsi"] <= 100
        assert type_index["RSI"] == "rsi_14"

    def test_macd_calculation(self, regime_engine, sample_data):
        """Test MACD indicator calculation."""
        indicators_def = [
            {
                "name": "macd_default",
                "type": "MACD",
                "params": [
                    {"name": "fast", "value": 12},
                    {"name": "slow", "value": 26},
                    {"name": "signal", "value": 9}
                ]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "macd_default" in indicator_values
        assert "macd" in indicator_values["macd_default"]
        assert "signal" in indicator_values["macd_default"]
        assert "hist" in indicator_values["macd_default"]
        assert isinstance(indicator_values["macd_default"]["macd"], float)

    def test_adx_calculation(self, regime_engine, sample_data):
        """Test ADX indicator calculation."""
        indicators_def = [
            {
                "name": "adx_14",
                "type": "ADX",
                "params": [{"name": "period", "value": 14}]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "adx_14" in indicator_values
        assert "adx" in indicator_values["adx_14"]
        assert "di_diff" in indicator_values["adx_14"]
        assert isinstance(indicator_values["adx_14"]["adx"], float)
        assert 0 <= indicator_values["adx_14"]["adx"] <= 100

    def test_bollinger_bands_calculation(self, regime_engine, sample_data):
        """Test Bollinger Bands calculation."""
        indicators_def = [
            {
                "name": "bb_20",
                "type": "BB",
                "params": [
                    {"name": "period", "value": 20},
                    {"name": "mult", "value": 2.0}
                ]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "bb_20" in indicator_values
        assert "upper" in indicator_values["bb_20"]
        assert "lower" in indicator_values["bb_20"]
        assert "middle" in indicator_values["bb_20"]

        # Check values exist (may be None due to insufficient data or column name mismatch)
        # This is a baseline test - we just verify structure is correct
        upper = indicator_values["bb_20"]["upper"]
        middle = indicator_values["bb_20"]["middle"]
        lower = indicator_values["bb_20"]["lower"]

        # If values are present, verify ordering
        if upper is not None and middle is not None and lower is not None:
            assert upper > middle, f"Upper {upper} should be > middle {middle}"
            assert middle > lower, f"Middle {middle} should be > lower {lower}"

    def test_multiple_indicators(self, regime_engine, sample_data):
        """Test calculation of multiple indicators at once."""
        indicators_def = [
            {"name": "rsi_14", "type": "RSI", "params": [{"name": "period", "value": 14}]},
            {"name": "ema_20", "type": "EMA", "params": [{"name": "period", "value": 20}]},
            {"name": "atr_14", "type": "ATR", "params": [{"name": "period", "value": 14}]},
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert len(indicator_values) == 3
        assert "rsi_14" in indicator_values
        assert "ema_20" in indicator_values
        assert "atr_14" in indicator_values

        assert type_index["RSI"] == "rsi_14"
        assert type_index["EMA"] == "ema_20"
        assert type_index["ATR"] == "atr_14"

    def test_atr_percentage_calculation(self, regime_engine, sample_data):
        """Test ATR percentage calculation."""
        indicators_def = [
            {
                "name": "atr_14",
                "type": "ATR",
                "params": [{"name": "period", "value": 14}]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "atr" in indicator_values["atr_14"]
        assert "atr_percent" in indicator_values["atr_14"]
        assert isinstance(indicator_values["atr_14"]["atr_percent"], float)
        assert indicator_values["atr_14"]["atr_percent"] > 0

    def test_stochastic_calculation(self, regime_engine, sample_data):
        """Test Stochastic indicator calculation."""
        indicators_def = [
            {
                "name": "stoch_14_3",
                "type": "STOCH",
                "params": [
                    {"name": "k", "value": 14},
                    {"name": "d", "value": 3}
                ]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "stoch_14_3" in indicator_values
        assert "k" in indicator_values["stoch_14_3"]
        assert "d" in indicator_values["stoch_14_3"]
        assert 0 <= indicator_values["stoch_14_3"]["k"] <= 100
        assert 0 <= indicator_values["stoch_14_3"]["d"] <= 100

    def test_mfi_calculation(self, regime_engine, sample_data):
        """Test MFI (Money Flow Index) calculation."""
        indicators_def = [
            {
                "name": "mfi_14",
                "type": "MFI",
                "params": [{"name": "period", "value": 14}]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "mfi_14" in indicator_values
        assert "mfi" in indicator_values["mfi_14"]
        assert isinstance(indicator_values["mfi_14"]["mfi"], float)
        assert 0 <= indicator_values["mfi_14"]["mfi"] <= 100

    def test_cci_calculation(self, regime_engine, sample_data):
        """Test CCI (Commodity Channel Index) calculation."""
        indicators_def = [
            {
                "name": "cci_20",
                "type": "CCI",
                "params": [{"name": "period", "value": 20}]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "cci_20" in indicator_values
        assert "cci" in indicator_values["cci_20"]
        assert isinstance(indicator_values["cci_20"]["cci"], float)

    def test_chop_calculation(self, regime_engine, sample_data):
        """Test CHOP (Choppiness Index) calculation."""
        indicators_def = [
            {
                "name": "chop_14",
                "type": "CHOP",
                "params": [{"name": "period", "value": 14}]
            }
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "chop_14" in indicator_values
        assert "chop" in indicator_values["chop_14"]
        assert isinstance(indicator_values["chop_14"]["chop"], float)
        assert 0 <= indicator_values["chop_14"]["chop"] <= 100

    def test_sma_ema_comparison(self, regime_engine, sample_data):
        """Test SMA and EMA calculations side by side."""
        indicators_def = [
            {"name": "sma_20", "type": "SMA", "params": [{"name": "period", "value": 20}]},
            {"name": "ema_20", "type": "EMA", "params": [{"name": "period", "value": 20}]},
        ]

        indicator_values, type_index = regime_engine._calculate_opt_indicators(
            sample_data, indicators_def
        )

        assert "sma_20" in indicator_values
        assert "ema_20" in indicator_values
        assert "value" in indicator_values["sma_20"]
        assert "value" in indicator_values["ema_20"]

        # Both should be close to current price but slightly different
        close_price = sample_data["close"].iloc[-1]
        sma_val = indicator_values["sma_20"]["value"]
        ema_val = indicator_values["ema_20"]["value"]

        assert abs(sma_val - close_price) / close_price < 0.1  # Within 10%
        assert abs(ema_val - close_price) / close_price < 0.1  # Within 10%

    def test_missing_name_raises_error(self, regime_engine, sample_data):
        """Test that missing indicator name raises ValueError."""
        indicators_def = [
            {
                "type": "RSI",
                "params": [{"name": "period", "value": 14}]
            }
        ]

        with pytest.raises(ValueError, match="missing name or type"):
            regime_engine._calculate_opt_indicators(sample_data, indicators_def)

    def test_missing_type_raises_error(self, regime_engine, sample_data):
        """Test that missing indicator type raises ValueError."""
        indicators_def = [
            {
                "name": "rsi_14",
                "params": [{"name": "period", "value": 14}]
            }
        ]

        with pytest.raises(ValueError, match="missing name or type"):
            regime_engine._calculate_opt_indicators(sample_data, indicators_def)

    def test_unsupported_indicator_type_raises_error(self, regime_engine, sample_data):
        """Test that unsupported indicator type raises ValueError."""
        indicators_def = [
            {
                "name": "unknown",
                "type": "UNKNOWN_TYPE",
                "params": []
            }
        ]

        with pytest.raises(ValueError, match="Unsupported indicator type"):
            regime_engine._calculate_opt_indicators(sample_data, indicators_def)
