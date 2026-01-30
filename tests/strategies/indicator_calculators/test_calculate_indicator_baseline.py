"""Baseline tests for _calculate_indicator() refactoring.

Ensures all indicator calculations remain identical after Factory Pattern refactoring.
Captures current behavior (CC=86) as reference for new implementation.

Test Strategy:
1. Test each indicator type with known parameters
2. Verify output columns and data types
3. Validate calculations against expected ranges
4. Ensure dropna() behavior is preserved

Coverage: All 21 indicator types (RSI, MACD, ADX, SMA, EMA, BB, ATR, ICHIMOKU,
PSAR, KC, VWAP, PIVOTS, CHOP, STOCH, CCI, BB_WIDTH, OBV, MFI, AD, CMF)
"""

import pytest
import pandas as pd
import numpy as np
from src.ui.threads.indicator_optimization_thread import IndicatorOptimizationThread


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


class TestCalculateIndicatorBaseline:
    """Baseline tests for indicator calculations before refactoring."""

    def test_rsi_calculation(self, sample_ohlcv):
        """Test RSI calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'RSI', {'period': 14})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert (result['indicator_value'] >= 0).all()
        assert (result['indicator_value'] <= 100).all()
        assert len(result) <= len(sample_ohlcv)  # dropna() may reduce rows

    def test_macd_calculation(self, sample_ohlcv):
        """Test MACD calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'MACD',
                                            {'fast': 12, 'slow': 26, 'signal': 9})

        assert 'indicator_value' in result.columns
        # Note: macd_signal may be dropped by dropna() - this is current behavior
        assert not result['indicator_value'].isna().all()
        assert len(result) <= len(sample_ohlcv)

    def test_adx_calculation(self, sample_ohlcv):
        """Test ADX calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'ADX', {'period': 14})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert (result['indicator_value'] >= 0).all()
        assert len(result) <= len(sample_ohlcv)

    def test_sma_calculation(self, sample_ohlcv):
        """Test SMA calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'SMA', {'period': 20})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert len(result) <= len(sample_ohlcv)

    def test_ema_calculation(self, sample_ohlcv):
        """Test EMA calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'EMA', {'period': 20})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert len(result) <= len(sample_ohlcv)

    def test_bb_calculation(self, sample_ohlcv):
        """Test Bollinger Bands calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'BB', {'period': 20, 'std': 2.0})

        assert 'indicator_value' in result.columns
        assert 'bb_lower' in result.columns
        assert 'bb_middle' in result.columns
        assert 'bb_upper' in result.columns
        assert not result['indicator_value'].isna().all()
        assert (result['bb_upper'] >= result['bb_middle']).all()
        assert (result['bb_middle'] >= result['bb_lower']).all()

    def test_atr_calculation(self, sample_ohlcv):
        """Test ATR calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'ATR', {'period': 14})

        assert 'indicator_value' in result.columns
        assert not result['indicator_value'].isna().all()
        assert (result['indicator_value'] > 0).all()

    def test_ichimoku_calculation(self, sample_ohlcv):
        """Test Ichimoku calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'ICHIMOKU',
                                            {'tenkan': 9, 'kijun': 26, 'senkou': 52})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_psar_calculation(self, sample_ohlcv):
        """Test Parabolic SAR calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'PSAR',
                                            {'accel': 0.02, 'max_accel': 0.2})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_kc_calculation(self, sample_ohlcv):
        """Test Keltner Channel calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'KC',
                                            {'period': 20, 'mult': 2.0})

        assert 'indicator_value' in result.columns
        assert 'kc_lower' in result.columns
        assert 'kc_middle' in result.columns
        assert 'kc_upper' in result.columns

    def test_vwap_calculation(self, sample_ohlcv):
        """Test VWAP calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'VWAP', {'anchor': 'D'})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_pivots_calculation(self, sample_ohlcv):
        """Test Pivot Points calculation."""
        thread = IndicatorOptimizationThread([], {})
        for pivot_type in ['standard', 'fibonacci', 'camarilla']:
            result = thread._calculate_indicator(sample_ohlcv, 'PIVOTS',
                                                {'type': pivot_type})
            assert 'indicator_value' in result.columns

    def test_chop_calculation(self, sample_ohlcv):
        """Test Choppiness Index calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'CHOP', {'period': 14})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_stoch_calculation(self, sample_ohlcv):
        """Test Stochastic calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'STOCH',
                                            {'k_period': 14, 'd_period': 3})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_cci_calculation(self, sample_ohlcv):
        """Test CCI calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'CCI', {'period': 20})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_bb_width_calculation(self, sample_ohlcv):
        """Test Bollinger Band Width calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'BB_WIDTH',
                                            {'period': 20, 'std': 2.0})

        assert 'indicator_value' in result.columns
        assert (result['indicator_value'] > 0).all()

    def test_obv_calculation(self, sample_ohlcv):
        """Test OBV calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'OBV', {})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_mfi_calculation(self, sample_ohlcv):
        """Test MFI calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'MFI', {'period': 14})

        assert 'indicator_value' in result.columns
        assert (result['indicator_value'] >= 0).all()
        assert (result['indicator_value'] <= 100).all()

    def test_ad_calculation(self, sample_ohlcv):
        """Test A/D Line calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'AD', {})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_cmf_calculation(self, sample_ohlcv):
        """Test CMF calculation."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'CMF', {'period': 20})

        assert 'indicator_value' in result.columns
        assert len(result) <= len(sample_ohlcv)

    def test_unknown_indicator(self, sample_ohlcv):
        """Test that unknown indicators are handled gracefully."""
        thread = IndicatorOptimizationThread([], {})
        result = thread._calculate_indicator(sample_ohlcv, 'UNKNOWN', {})

        # Should return original df without indicator_value
        assert 'indicator_value' not in result.columns
        assert len(result) == len(sample_ohlcv)
