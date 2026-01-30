"""
Baseline tests for extract_indicator_snapshot() refactoring.

Tests the ORIGINAL implementation to establish baseline behavior.
These tests will be reused after refactoring to ensure identical behavior.
"""

import pandas as pd
import pytest
from datetime import datetime, timezone


class TestExtractIndicatorSnapshotBaseline:
    """Baseline tests for extract_indicator_snapshot()."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with indicator data."""
        return pd.DataFrame({
            'close': [100.0],
            'ema_20': [98.0],
            'ema_50': [95.0],
            'ema_200': [90.0],
            'rsi_14': [75.0],
            'macd': [1.5],
            'macd_signal': [1.2],
            'macd_hist': [0.3],
            'bb_upper': [105.0],
            'bb_middle': [100.0],
            'bb_lower': [95.0],
            'atr_14': [2.5],
            'adx_14': [25.0],
            'plus_di': [30.0],
            'minus_di': [20.0],
            'volume': [1000000.0],
            'volume_sma_20': [800000.0],
            'timestamp': [datetime.now(timezone.utc)]
        })

    @pytest.fixture
    def empty_df(self):
        """Create empty DataFrame."""
        return pd.DataFrame()

    @pytest.fixture
    def signal_generator_snapshot(self):
        """Create SignalGeneratorIndicatorSnapshot instance."""
        from src.core.trading_bot.signal_generator_indicator_snapshot import SignalGeneratorIndicatorSnapshot

        # Mock parent
        class MockParent:
            pass

        return SignalGeneratorIndicatorSnapshot(MockParent())

    def test_empty_dataframe(self, signal_generator_snapshot, empty_df):
        """Test with empty DataFrame."""
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(empty_df)

        assert snapshot is not None
        assert snapshot.timestamp is not None
        assert snapshot.ema_20 is None
        assert snapshot.current_price is None

    def test_complete_snapshot_extraction(self, signal_generator_snapshot, sample_df):
        """Test complete snapshot extraction with all indicators."""
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(sample_df)

        # Basic checks
        assert snapshot is not None
        assert snapshot.timestamp is not None
        assert snapshot.current_price == 100.0

        # EMA values
        assert snapshot.ema_20 == 98.0
        assert snapshot.ema_50 == 95.0
        assert snapshot.ema_200 == 90.0

        # EMA distance calculation
        assert snapshot.ema_20_distance_pct is not None
        expected_ema_dist = ((100.0 - 98.0) / 98.0) * 100
        assert abs(snapshot.ema_20_distance_pct - expected_ema_dist) < 0.01

        # RSI
        assert snapshot.rsi_14 == 75.0
        assert snapshot.rsi_state == "OVERBOUGHT"

        # MACD
        assert snapshot.macd_line == 1.5
        assert snapshot.macd_signal == 1.2
        assert snapshot.macd_histogram == 0.3
        assert snapshot.macd_crossover == "BULLISH"

        # Bollinger Bands
        assert snapshot.bb_upper == 105.0
        assert snapshot.bb_middle == 100.0
        assert snapshot.bb_lower == 95.0
        assert snapshot.bb_pct_b is not None
        assert snapshot.bb_width is not None

        # ATR
        assert snapshot.atr_14 == 2.5
        assert snapshot.atr_percent is not None

        # ADX
        assert snapshot.adx_14 == 25.0
        assert snapshot.plus_di == 30.0
        assert snapshot.minus_di == 20.0

        # Volume
        assert snapshot.volume == 1000000.0
        assert snapshot.volume_sma_20 == 800000.0
        assert snapshot.volume_ratio == 1.25

    def test_rsi_states(self, signal_generator_snapshot):
        """Test RSI state classification."""
        # Oversold
        df = pd.DataFrame({'close': [100.0], 'rsi_14': [25.0]})
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)
        assert snapshot.rsi_state == "OVERSOLD"

        # Overbought
        df = pd.DataFrame({'close': [100.0], 'rsi_14': [75.0]})
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)
        assert snapshot.rsi_state == "OVERBOUGHT"

        # Neutral
        df = pd.DataFrame({'close': [100.0], 'rsi_14': [50.0]})
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)
        assert snapshot.rsi_state == "NEUTRAL"

    def test_macd_crossover(self, signal_generator_snapshot):
        """Test MACD crossover detection."""
        # Bullish
        df = pd.DataFrame({
            'close': [100.0],
            'macd': [1.5],
            'macd_signal': [1.2]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)
        assert snapshot.macd_crossover == "BULLISH"

        # Bearish
        df = pd.DataFrame({
            'close': [100.0],
            'macd': [1.2],
            'macd_signal': [1.5]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)
        assert snapshot.macd_crossover == "BEARISH"

    def test_missing_indicators(self, signal_generator_snapshot):
        """Test with missing indicators."""
        df = pd.DataFrame({'close': [100.0]})
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)

        assert snapshot.current_price == 100.0
        assert snapshot.ema_20 is None
        assert snapshot.rsi_14 is None
        assert snapshot.macd_line is None

    def test_alternative_column_names(self, signal_generator_snapshot):
        """Test with alternative column names (uppercase)."""
        df = pd.DataFrame({
            'close': [100.0],
            'EMA_20': [98.0],
            'RSI_14': [50.0],
            'MACD': [1.5],
            'MACD_signal': [1.2],
            'BB_upper': [105.0],
            'BB_middle': [100.0],
            'BB_lower': [95.0],
            'ATR_14': [2.5],
            'ADX_14': [25.0]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)

        assert snapshot.ema_20 == 98.0
        assert snapshot.rsi_14 == 50.0
        assert snapshot.macd_line == 1.5
        assert snapshot.bb_upper == 105.0
        assert snapshot.atr_14 == 2.5
        assert snapshot.adx_14 == 25.0

    def test_bollinger_band_calculations(self, signal_generator_snapshot):
        """Test Bollinger Band calculations."""
        df = pd.DataFrame({
            'close': [100.0],
            'bb_upper': [105.0],
            'bb_middle': [100.0],
            'bb_lower': [95.0]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)

        # %B calculation
        expected_pct_b = (100.0 - 95.0) / (105.0 - 95.0)
        assert abs(snapshot.bb_pct_b - expected_pct_b) < 0.01

        # Width calculation
        expected_width = (105.0 - 95.0) / 100.0
        assert abs(snapshot.bb_width - expected_width) < 0.01

    def test_atr_percentage_calculation(self, signal_generator_snapshot):
        """Test ATR percentage calculation."""
        df = pd.DataFrame({
            'close': [100.0],
            'atr_14': [2.5]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)

        expected_atr_pct = (2.5 / 100.0) * 100
        assert abs(snapshot.atr_percent - expected_atr_pct) < 0.01

    def test_volume_ratio_calculation(self, signal_generator_snapshot):
        """Test volume ratio calculation."""
        df = pd.DataFrame({
            'close': [100.0],
            'volume': [1000000.0],
            'volume_sma_20': [800000.0]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)

        expected_ratio = 1000000.0 / 800000.0
        assert abs(snapshot.volume_ratio - expected_ratio) < 0.01

    def test_zero_volume_sma(self, signal_generator_snapshot):
        """Test with zero volume SMA (should not crash)."""
        df = pd.DataFrame({
            'close': [100.0],
            'volume': [1000000.0],
            'volume_sma_20': [0.0]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)

        assert snapshot.volume_ratio is None  # Should handle division by zero

    def test_timestamp_handling(self, signal_generator_snapshot):
        """Test timestamp handling."""
        now = datetime.now(timezone.utc)

        # With timestamp
        df = pd.DataFrame({
            'close': [100.0],
            'timestamp': [now]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)
        assert snapshot.timestamp == now

        # Without timestamp
        df = pd.DataFrame({'close': [100.0]})
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)
        assert snapshot.timestamp is not None
        assert isinstance(snapshot.timestamp, datetime)

    def test_string_timestamp(self, signal_generator_snapshot):
        """Test with string timestamp."""
        timestamp_str = "2024-01-01T12:00:00+00:00"
        df = pd.DataFrame({
            'close': [100.0],
            'timestamp': [timestamp_str]
        })
        snapshot = signal_generator_snapshot.extract_indicator_snapshot(df)

        assert isinstance(snapshot.timestamp, datetime)
