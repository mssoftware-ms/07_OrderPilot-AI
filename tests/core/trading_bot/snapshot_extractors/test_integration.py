"""
Integration tests for snapshot extractor system.

Tests the complete extraction pipeline with all extractors.
"""

import pandas as pd
import pytest
from datetime import datetime, timezone

from src.core.trading_bot.snapshot_extractors import (
    FieldExtractorRegistry,
    EMAExtractor,
    RSIExtractor,
    MACDExtractor,
    BollingerExtractor,
    ATRExtractor,
    ADXExtractor,
    VolumeExtractor,
    PriceTimestampExtractor,
)


class TestSnapshotExtractorIntegration:
    """Integration tests for complete extractor pipeline."""

    @pytest.fixture
    def registry(self):
        """Create registry with all extractors."""
        registry = FieldExtractorRegistry()
        registry.register(PriceTimestampExtractor())
        registry.register(EMAExtractor())
        registry.register(RSIExtractor())
        registry.register(MACDExtractor())
        registry.register(BollingerExtractor())
        registry.register(ATRExtractor())
        registry.register(ADXExtractor())
        registry.register(VolumeExtractor())
        return registry

    @pytest.fixture
    def complete_df(self):
        """Create complete DataFrame with all indicators."""
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

    def test_complete_extraction(self, registry, complete_df):
        """Test extraction with all indicators present."""
        fields = registry.extract_all(complete_df)

        # Verify all expected fields present
        expected_fields = {
            'current_price', 'timestamp',
            'ema_20', 'ema_50', 'ema_200', 'ema_20_distance_pct',
            'rsi_14', 'rsi_state',
            'macd_line', 'macd_signal', 'macd_histogram', 'macd_crossover',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_pct_b', 'bb_width',
            'atr_14', 'atr_percent',
            'adx_14', 'plus_di', 'minus_di',
            'volume', 'volume_sma_20', 'volume_ratio'
        }

        assert set(fields.keys()) == expected_fields

        # Verify values
        assert fields['current_price'] == 100.0
        assert fields['ema_20'] == 98.0
        assert fields['rsi_14'] == 75.0
        assert fields['rsi_state'] == 'OVERBOUGHT'
        assert fields['macd_line'] == 1.5
        assert fields['macd_crossover'] == 'BULLISH'

    def test_empty_dataframe(self, registry):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        fields = registry.extract_all(df)

        assert fields == {}

    def test_minimal_dataframe(self, registry):
        """Test with minimal data (only price)."""
        df = pd.DataFrame({'close': [100.0]})
        fields = registry.extract_all(df)

        # Should have price and timestamp, but other fields None
        assert fields['current_price'] == 100.0
        assert fields['timestamp'] is not None
        assert fields['ema_20'] is None
        assert fields['rsi_14'] is None

    def test_uppercase_column_names(self, registry):
        """Test with uppercase column names."""
        df = pd.DataFrame({
            'close': [100.0],
            'EMA_20': [98.0],
            'RSI_14': [50.0],
            'MACD': [1.5],
            'BB_upper': [105.0]
        })
        fields = registry.extract_all(df)

        assert fields['ema_20'] == 98.0
        assert fields['rsi_14'] == 50.0
        assert fields['macd_line'] == 1.5
        assert fields['bb_upper'] == 105.0

    def test_mixed_column_names(self, registry):
        """Test with mixed case column names."""
        df = pd.DataFrame({
            'close': [100.0],
            'ema_20': [98.0],  # lowercase
            'RSI_14': [50.0],  # uppercase
            'macd': [1.5],     # lowercase
            'BB_upper': [105.0]  # uppercase
        })
        fields = registry.extract_all(df)

        # All should be found despite mixed case
        assert fields['ema_20'] == 98.0
        assert fields['rsi_14'] == 50.0
        assert fields['macd_line'] == 1.5
        assert fields['bb_upper'] == 105.0

    def test_extractor_independence(self, registry, complete_df):
        """Test that extractors are independent (can work with missing data)."""
        # Remove MACD data
        df = complete_df.copy()
        df = df.drop(['macd', 'macd_signal', 'macd_hist'], axis=1)

        fields = registry.extract_all(df)

        # MACD fields should be None
        assert fields['macd_line'] is None
        assert fields['macd_signal'] is None
        assert fields['macd_histogram'] is None
        assert fields['macd_crossover'] is None

        # But other fields should still work
        assert fields['ema_20'] == 98.0
        assert fields['rsi_14'] == 75.0

    def test_calculations_accuracy(self, registry):
        """Test accuracy of calculated fields."""
        df = pd.DataFrame({
            'close': [100.0],
            'ema_20': [95.0],
            'bb_upper': [110.0],
            'bb_middle': [100.0],
            'bb_lower': [90.0],
            'atr_14': [5.0],
            'volume': [1000000.0],
            'volume_sma_20': [500000.0]
        })
        fields = registry.extract_all(df)

        # EMA distance
        expected_ema_dist = ((100.0 - 95.0) / 95.0) * 100
        assert abs(fields['ema_20_distance_pct'] - expected_ema_dist) < 0.01

        # BB %B
        expected_pct_b = (100.0 - 90.0) / (110.0 - 90.0)
        assert abs(fields['bb_pct_b'] - expected_pct_b) < 0.01

        # BB Width
        expected_width = (110.0 - 90.0) / 100.0
        assert abs(fields['bb_width'] - expected_width) < 0.01

        # ATR %
        expected_atr_pct = (5.0 / 100.0) * 100
        assert abs(fields['atr_percent'] - expected_atr_pct) < 0.01

        # Volume ratio
        expected_ratio = 1000000.0 / 500000.0
        assert abs(fields['volume_ratio'] - expected_ratio) < 0.01

    def test_type_safety(self, registry):
        """Test that all numeric fields are floats or None."""
        df = pd.DataFrame({
            'close': [100.0],
            'ema_20': [98.0],
            'rsi_14': [50.0],
        })
        fields = registry.extract_all(df)

        # Check types
        assert isinstance(fields['current_price'], float)
        assert isinstance(fields['ema_20'], float)
        assert isinstance(fields['rsi_14'], float)

        # None fields should be None, not strings
        assert fields['macd_line'] is None
        assert fields['bb_upper'] is None

    def test_extractor_order_independence(self):
        """Test that extractor registration order doesn't matter."""
        # Registry 1: normal order
        registry1 = FieldExtractorRegistry()
        registry1.register(EMAExtractor())
        registry1.register(RSIExtractor())
        registry1.register(MACDExtractor())

        # Registry 2: reverse order
        registry2 = FieldExtractorRegistry()
        registry2.register(MACDExtractor())
        registry2.register(RSIExtractor())
        registry2.register(EMAExtractor())

        df = pd.DataFrame({
            'close': [100.0],
            'ema_20': [98.0],
            'rsi_14': [50.0],
            'macd': [1.5]
        })

        fields1 = registry1.extract_all(df)
        fields2 = registry2.extract_all(df)

        # Results should be identical
        assert fields1 == fields2
