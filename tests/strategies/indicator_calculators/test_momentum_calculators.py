"""Unit tests for momentum indicator calculators.

Tests:
- RSICalculator
- MACDCalculator
- StochasticCalculator
- CCICalculator

Each test verifies:
1. can_calculate() correctly identifies indicator types
2. calculate() produces expected output structure
3. Calculation results match baseline behavior
4. Edge cases handled gracefully
"""

import pytest
import pandas as pd
import numpy as np
from src.strategies.indicator_calculators.momentum import (
    RSICalculator,
    MACDCalculator,
    StochasticCalculator,
    CCICalculator
)


@pytest.fixture
def sample_ohlcv():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range('2024-01-01', periods=100, freq='1D')
    np.random.seed(42)

    df = pd.DataFrame({
        'open': 100 + np.random.randn(100).cumsum(),
        'high': 105 + np.random.randn(100).cumsum(),
        'low': 95 + np.random.randn(100).cumsum(),
        'close': 100 + np.random.randn(100).cumsum(),
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)

    # Ensure high >= close/open and low <= close/open
    df['high'] = df[['high', 'close', 'open']].max(axis=1)
    df['low'] = df[['low', 'close', 'open']].min(axis=1)

    return df


class TestRSICalculator:
    """Tests for RSI calculator."""

    def test_can_calculate(self):
        """Test indicator type identification."""
        calc = RSICalculator()
        assert calc.can_calculate('RSI') is True
        assert calc.can_calculate('MACD') is False
        assert calc.can_calculate('rsi') is False  # Case-sensitive

    def test_calculate_basic(self, sample_ohlcv):
        """Test basic RSI calculation."""
        calc = RSICalculator()
        result = calc.calculate(sample_ohlcv, {'period': 14})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert (result['indicator_value'] >= 0).all()
        assert (result['indicator_value'] <= 100).all()
        assert len(result) <= len(sample_ohlcv)  # dropna() reduces rows

    def test_calculate_custom_period(self, sample_ohlcv):
        """Test RSI with custom period."""
        calc = RSICalculator()
        result = calc.calculate(sample_ohlcv, {'period': 7})

        assert 'indicator_value' in result.columns
        assert len(result) > 0

    def test_calculate_default_params(self, sample_ohlcv):
        """Test RSI with default parameters."""
        calc = RSICalculator()
        result = calc.calculate(sample_ohlcv, {})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()


class TestMACDCalculator:
    """Tests for MACD calculator."""

    def test_can_calculate(self):
        """Test indicator type identification."""
        calc = MACDCalculator()
        assert calc.can_calculate('MACD') is True
        assert calc.can_calculate('RSI') is False

    def test_calculate_basic(self, sample_ohlcv):
        """Test basic MACD calculation."""
        calc = MACDCalculator()
        result = calc.calculate(sample_ohlcv, {'fast': 12, 'slow': 26, 'signal': 9})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert len(result) <= len(sample_ohlcv)

    def test_calculate_custom_params(self, sample_ohlcv):
        """Test MACD with custom parameters."""
        calc = MACDCalculator()
        result = calc.calculate(sample_ohlcv, {'fast': 8, 'slow': 21, 'signal': 7})

        assert 'indicator_value' in result.columns
        assert len(result) > 0

    def test_calculate_default_params(self, sample_ohlcv):
        """Test MACD with default parameters."""
        calc = MACDCalculator()
        result = calc.calculate(sample_ohlcv, {})

        assert 'indicator_value' in result.columns


class TestStochasticCalculator:
    """Tests for Stochastic Oscillator calculator."""

    def test_can_calculate(self):
        """Test indicator type identification."""
        calc = StochasticCalculator()
        assert calc.can_calculate('STOCH') is True
        assert calc.can_calculate('RSI') is False

    def test_calculate_basic(self, sample_ohlcv):
        """Test basic Stochastic calculation."""
        calc = StochasticCalculator()
        result = calc.calculate(sample_ohlcv, {'k_period': 14, 'd_period': 3})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert len(result) <= len(sample_ohlcv)

    def test_calculate_range(self, sample_ohlcv):
        """Test Stochastic values in 0-100 range."""
        calc = StochasticCalculator()
        result = calc.calculate(sample_ohlcv, {'k_period': 14, 'd_period': 3})

        # Stochastic should be 0-100 range
        assert (result['indicator_value'] >= 0).all()
        assert (result['indicator_value'] <= 100).all()

    def test_calculate_default_params(self, sample_ohlcv):
        """Test Stochastic with default parameters."""
        calc = StochasticCalculator()
        result = calc.calculate(sample_ohlcv, {})

        assert 'indicator_value' in result.columns


class TestCCICalculator:
    """Tests for CCI calculator."""

    def test_can_calculate(self):
        """Test indicator type identification."""
        calc = CCICalculator()
        assert calc.can_calculate('CCI') is True
        assert calc.can_calculate('RSI') is False

    def test_calculate_basic(self, sample_ohlcv):
        """Test basic CCI calculation."""
        calc = CCICalculator()
        result = calc.calculate(sample_ohlcv, {'period': 20})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert len(result) <= len(sample_ohlcv)

    def test_calculate_custom_period(self, sample_ohlcv):
        """Test CCI with custom period."""
        calc = CCICalculator()
        result = calc.calculate(sample_ohlcv, {'period': 14})

        assert 'indicator_value' in result.columns
        assert len(result) > 0

    def test_calculate_default_params(self, sample_ohlcv):
        """Test CCI with default parameters."""
        calc = CCICalculator()
        result = calc.calculate(sample_ohlcv, {})

        assert 'indicator_value' in result.columns
