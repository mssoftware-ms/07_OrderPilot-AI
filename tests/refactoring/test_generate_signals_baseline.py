"""Baseline tests for _generate_signals() refactoring.

This test suite captures the CURRENT behavior of _generate_signals() before refactoring.
All tests here must remain GREEN throughout the refactoring process.
"""

import pandas as pd
import numpy as np
import pytest
from src.ui.threads.indicator_optimization_thread import IndicatorOptimizationThread


@pytest.fixture
def sample_df():
    """Create sample dataframe with price data and indicators."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')

    df = pd.DataFrame({
        'close': 100 + np.cumsum(np.random.randn(100) * 0.5),
        'indicator_value': 50 + np.cumsum(np.random.randn(100) * 2),
    }, index=dates)

    # Add Bollinger Bands columns
    df['bb_lower'] = df['close'] - 2 * df['close'].rolling(20).std()
    df['bb_middle'] = df['close'].rolling(20).mean()
    df['bb_upper'] = df['close'] + 2 * df['close'].rolling(20).std()

    # Add Keltner Channels columns
    df['kc_lower'] = df['close'] - 1.5 * df['close'].rolling(20).std()
    df['kc_upper'] = df['close'] + 1.5 * df['close'].rolling(20).std()

    # Add Ichimoku cloud columns
    df['cloud_top'] = df['close'].rolling(26).max()
    df['cloud_bottom'] = df['close'].rolling(26).min()

    return df


@pytest.fixture
def optimizer_thread():
    """Create optimizer thread instance."""
    # Create a minimal thread instance
    # After refactoring, we need to initialize the signal registry
    thread = IndicatorOptimizationThread.__new__(IndicatorOptimizationThread)

    # Initialize signal registry manually (since we skip __init__)
    from src.strategies.signal_generators import SignalGeneratorRegistry
    thread._signal_registry = SignalGeneratorRegistry()

    return thread


class TestRSISignals:
    """Test RSI signal generation."""

    def test_rsi_entry_long_oversold(self, optimizer_thread, sample_df):
        """RSI < 30 should generate entry long signal."""
        df = sample_df.copy()
        df['indicator_value'] = 25  # Oversold

        signals = optimizer_thread._generate_signals(df, 'RSI', 'entry', 'long')

        assert signals.any(), "Should generate signals when RSI < 30"
        assert signals.sum() > 0

    def test_rsi_entry_short_overbought(self, optimizer_thread, sample_df):
        """RSI > 70 should generate entry short signal."""
        df = sample_df.copy()
        df['indicator_value'] = 75  # Overbought

        signals = optimizer_thread._generate_signals(df, 'RSI', 'entry', 'short')

        assert signals.any(), "Should generate signals when RSI > 70"

    def test_rsi_exit_long_overbought(self, optimizer_thread, sample_df):
        """RSI > 70 should generate exit long signal."""
        df = sample_df.copy()
        df['indicator_value'] = 75

        signals = optimizer_thread._generate_signals(df, 'RSI', 'exit', 'long')

        assert signals.any()

    def test_rsi_exit_short_oversold(self, optimizer_thread, sample_df):
        """RSI < 30 should generate exit short signal."""
        df = sample_df.copy()
        df['indicator_value'] = 25

        signals = optimizer_thread._generate_signals(df, 'RSI', 'exit', 'short')

        assert signals.any()


class TestMACDSignals:
    """Test MACD signal generation."""

    def test_macd_entry_long_cross_above_zero(self, optimizer_thread, sample_df):
        """MACD crossing above 0 should generate entry long signal."""
        df = sample_df.copy()
        df['indicator_value'] = [-1, 1, 1, 1, 1] + [0] * 95  # Cross above 0

        signals = optimizer_thread._generate_signals(df, 'MACD', 'entry', 'long')

        assert signals.iloc[1], "Should signal at crossover point"

    def test_macd_entry_short_cross_below_zero(self, optimizer_thread, sample_df):
        """MACD crossing below 0 should generate entry short signal."""
        df = sample_df.copy()
        df['indicator_value'] = [1, -1, -1, -1, -1] + [0] * 95

        signals = optimizer_thread._generate_signals(df, 'MACD', 'entry', 'short')

        assert signals.iloc[1]


class TestSMASignals:
    """Test SMA signal generation."""

    def test_sma_entry_long_price_cross_above(self, optimizer_thread, sample_df):
        """Price crossing above SMA should generate entry long."""
        df = sample_df.copy()
        df['close'] = [99, 101, 102] + [100] * 97
        df['indicator_value'] = 100

        signals = optimizer_thread._generate_signals(df, 'SMA', 'entry', 'long')

        assert signals.iloc[1], "Should signal when price crosses above SMA"

    def test_sma_entry_short_price_cross_below(self, optimizer_thread, sample_df):
        """Price crossing below SMA should generate entry short."""
        df = sample_df.copy()
        df['close'] = [101, 99, 98] + [100] * 97
        df['indicator_value'] = 100

        signals = optimizer_thread._generate_signals(df, 'SMA', 'entry', 'short')

        assert signals.iloc[1]


class TestEMASignals:
    """Test EMA signal generation (same logic as SMA)."""

    def test_ema_entry_long_price_cross_above(self, optimizer_thread, sample_df):
        """Price crossing above EMA should generate entry long."""
        df = sample_df.copy()
        df['close'] = [99, 101, 102] + [100] * 97
        df['indicator_value'] = 100

        signals = optimizer_thread._generate_signals(df, 'EMA', 'entry', 'long')

        assert signals.iloc[1]


class TestADXSignals:
    """Test ADX signal generation."""

    def test_adx_entry_strong_trend(self, optimizer_thread, sample_df):
        """ADX > 25 should generate entry signal."""
        df = sample_df.copy()
        df['indicator_value'] = 30

        signals = optimizer_thread._generate_signals(df, 'ADX', 'entry', 'long')

        assert signals.any()

    def test_adx_exit_weak_trend(self, optimizer_thread, sample_df):
        """ADX < 20 should generate exit signal."""
        df = sample_df.copy()
        df['indicator_value'] = 15

        signals = optimizer_thread._generate_signals(df, 'ADX', 'exit', 'long')

        assert signals.any()


class TestBollingerBandsSignals:
    """Test Bollinger Bands signal generation."""

    def test_bb_entry_long_touch_lower_band(self, optimizer_thread, sample_df):
        """Price touching lower BB should generate entry long."""
        df = sample_df.copy()
        df['close'] = 95
        df['bb_lower'] = 95
        df['bb_middle'] = 100
        df['bb_upper'] = 105

        signals = optimizer_thread._generate_signals(df, 'BB', 'entry', 'long')

        assert signals.any()

    def test_bb_entry_short_touch_upper_band(self, optimizer_thread, sample_df):
        """Price touching upper BB should generate entry short."""
        df = sample_df.copy()
        df['close'] = 105
        df['bb_upper'] = 105

        signals = optimizer_thread._generate_signals(df, 'BB', 'entry', 'short')

        assert signals.any()


class TestStochasticSignals:
    """Test Stochastic signal generation."""

    def test_stoch_entry_long_cross_above_20(self, optimizer_thread, sample_df):
        """Stoch crossing above 20 should generate entry long."""
        df = sample_df.copy()
        df['indicator_value'] = [15, 25, 30] + [50] * 97

        signals = optimizer_thread._generate_signals(df, 'STOCH', 'entry', 'long')

        assert signals.iloc[1]

    def test_stoch_entry_short_cross_below_80(self, optimizer_thread, sample_df):
        """Stoch crossing below 80 should generate entry short."""
        df = sample_df.copy()
        df['indicator_value'] = [85, 75, 70] + [50] * 97

        signals = optimizer_thread._generate_signals(df, 'STOCH', 'entry', 'short')

        assert signals.iloc[1]


class TestVolumeIndicators:
    """Test volume-based indicators."""

    def test_obv_entry_long_trending_up(self, optimizer_thread, sample_df):
        """OBV crossing above SMA should generate entry long."""
        df = sample_df.copy()
        # Create trending up OBV
        df['indicator_value'] = np.arange(100) + np.random.randn(100) * 2

        signals = optimizer_thread._generate_signals(df, 'OBV', 'entry', 'long')

        # Should have some signals where OBV crosses its SMA
        assert isinstance(signals, pd.Series)

    def test_mfi_entry_long_oversold(self, optimizer_thread, sample_df):
        """MFI < 20 should generate entry long."""
        df = sample_df.copy()
        df['indicator_value'] = 15

        signals = optimizer_thread._generate_signals(df, 'MFI', 'entry', 'long')

        assert signals.any()

    def test_cmf_entry_long_accumulation(self, optimizer_thread, sample_df):
        """CMF crossing above 0 should generate entry long."""
        df = sample_df.copy()
        df['indicator_value'] = [-0.05, 0.05, 0.1] + [0] * 97

        signals = optimizer_thread._generate_signals(df, 'CMF', 'entry', 'long')

        assert signals.iloc[1]


class TestVolatilityIndicators:
    """Test volatility indicators."""

    def test_atr_entry_high_volatility(self, optimizer_thread, sample_df):
        """High ATR should generate entry signal."""
        df = sample_df.copy()
        df['indicator_value'] = np.linspace(1, 3, 100)  # Increasing ATR

        signals = optimizer_thread._generate_signals(df, 'ATR', 'entry', 'long')

        # Should have signals where ATR > its SMA
        assert isinstance(signals, pd.Series)


class TestChannelIndicators:
    """Test channel and breakout indicators."""

    def test_kc_entry_long_breakout(self, optimizer_thread, sample_df):
        """Price breaking above upper Keltner should generate entry long."""
        df = sample_df.copy()
        df['close'] = [99, 101, 102] + [100] * 97
        df['kc_upper'] = 100

        signals = optimizer_thread._generate_signals(df, 'KC', 'entry', 'long')

        assert signals.iloc[1]


class TestTrendIndicators:
    """Test trend-following indicators."""

    def test_ichimoku_entry_long_above_cloud(self, optimizer_thread, sample_df):
        """Price crossing above cloud should generate entry long."""
        df = sample_df.copy()
        df['close'] = [99, 101, 102] + [100] * 97
        df['cloud_top'] = 100

        signals = optimizer_thread._generate_signals(df, 'ICHIMOKU', 'entry', 'long')

        assert signals.iloc[1]

    def test_psar_entry_long_reversal(self, optimizer_thread, sample_df):
        """Price crossing above PSAR should generate entry long."""
        df = sample_df.copy()
        df['close'] = [99, 101, 102] + [100] * 97
        df['indicator_value'] = 100

        signals = optimizer_thread._generate_signals(df, 'PSAR', 'entry', 'long')

        assert signals.iloc[1]

    def test_vwap_entry_long_cross_above(self, optimizer_thread, sample_df):
        """Price crossing above VWAP should generate entry long."""
        df = sample_df.copy()
        df['close'] = [99, 101, 102] + [100] * 97
        df['indicator_value'] = 100

        signals = optimizer_thread._generate_signals(df, 'VWAP', 'entry', 'long')

        assert signals.iloc[1]


class TestMomentumIndicators:
    """Test momentum indicators."""

    def test_cci_entry_long_oversold_recovery(self, optimizer_thread, sample_df):
        """CCI crossing above -100 should generate entry long."""
        df = sample_df.copy()
        df['indicator_value'] = [-110, -90, -80] + [0] * 97

        signals = optimizer_thread._generate_signals(df, 'CCI', 'entry', 'long')

        assert signals.iloc[1]


class TestRegimeIndicators:
    """Test regime detection indicators."""

    def test_chop_entry_low_chop(self, optimizer_thread, sample_df):
        """Low CHOP (trending) should generate entry signal."""
        df = sample_df.copy()
        df['indicator_value'] = 30  # Low chop = trending

        signals = optimizer_thread._generate_signals(df, 'CHOP', 'entry', 'long')

        assert signals.any()

    def test_chop_exit_high_chop(self, optimizer_thread, sample_df):
        """High CHOP (ranging) should generate exit signal."""
        df = sample_df.copy()
        df['indicator_value'] = 70  # High chop = ranging

        signals = optimizer_thread._generate_signals(df, 'CHOP', 'exit', 'long')

        assert signals.any()


class TestPivotPoints:
    """Test pivot point signals."""

    def test_pivots_entry_long_above_pivot(self, optimizer_thread, sample_df):
        """Price above pivot should generate entry long."""
        df = sample_df.copy()
        df['close'] = 105
        df['indicator_value'] = 100

        signals = optimizer_thread._generate_signals(df, 'PIVOTS', 'entry', 'long')

        assert signals.any()


class TestVolumeWeightedIndicators:
    """Test volume-weighted indicators."""

    def test_ad_entry_long_trending_up(self, optimizer_thread, sample_df):
        """A/D crossing above SMA should generate entry long."""
        df = sample_df.copy()
        df['indicator_value'] = np.arange(100)

        signals = optimizer_thread._generate_signals(df, 'AD', 'entry', 'long')

        assert isinstance(signals, pd.Series)


class TestBBWidth:
    """Test BB Width volatility indicator."""

    def test_bb_width_entry_high_volatility(self, optimizer_thread, sample_df):
        """High BB Width should generate entry signal."""
        df = sample_df.copy()
        df['indicator_value'] = np.linspace(1, 3, 100)

        signals = optimizer_thread._generate_signals(df, 'BB_WIDTH', 'entry', 'long')

        assert isinstance(signals, pd.Series)


# Summary test to ensure all 22 indicator types are covered
def test_all_indicator_types_covered(optimizer_thread, sample_df):
    """Ensure all 22 indicator types generate signals without errors."""
    indicator_types = [
        'RSI', 'MACD', 'ADX',  # Momentum/Trend Strength
        'SMA', 'EMA', 'ICHIMOKU', 'PSAR', 'VWAP', 'PIVOTS',  # Trend/Overlay
        'BB', 'KC',  # Channels
        'CHOP',  # Regime
        'STOCH', 'CCI',  # Momentum
        'ATR', 'BB_WIDTH',  # Volatility
        'OBV', 'MFI', 'AD', 'CMF',  # Volume
    ]

    for indicator_type in indicator_types:
        signals = optimizer_thread._generate_signals(
            sample_df.copy(),
            indicator_type,
            'entry',
            'long'
        )
        assert isinstance(signals, pd.Series), f"{indicator_type} failed to generate signals"
        assert len(signals) == len(sample_df), f"{indicator_type} signal length mismatch"
