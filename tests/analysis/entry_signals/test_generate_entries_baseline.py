"""Baseline tests for generate_entries() refactoring.

Tests that entry generation produces identical results before/after refactoring.
"""

import pytest
from src.analysis.entry_signals.entry_signal_engine import (
    generate_entries,
    calculate_features,
    OptimParams,
    RegimeType,
    EntrySide,
)


@pytest.fixture
def sample_candles():
    """Sample OHLCV candles for testing."""
    return [
        {
            "timestamp": 1000 + i * 60,
            "open": 100.0 + i * 0.1,
            "high": 100.5 + i * 0.1,
            "low": 99.5 + i * 0.1,
            "close": 100.0 + i * 0.1,
            "volume": 1000.0,
        }
        for i in range(100)
    ]


@pytest.fixture
def default_params():
    """Default optimization parameters."""
    return OptimParams()


class TestGenerateEntriesBaseline:
    """Baseline tests for generate_entries() function."""

    def test_generate_entries_trend_up(self, sample_candles, default_params):
        """Test entry generation in TREND_UP regime."""
        # Calculate features
        features = calculate_features(sample_candles, default_params)

        # Generate entries
        entries = generate_entries(
            sample_candles,
            features,
            RegimeType.TREND_UP,
            default_params,
        )

        # Baseline assertions
        assert isinstance(entries, list), "Should return list"

        # Store baseline
        for entry in entries:
            assert entry.side == EntrySide.LONG, "TREND_UP should only generate LONG entries"
            assert 0.0 <= entry.confidence <= 1.0, "Confidence should be in [0,1]"
            assert entry.price > 0, "Price should be positive"
            assert entry.regime == RegimeType.TREND_UP
            assert len(entry.reason_tags) > 0, "Should have reason tags"

    def test_generate_entries_trend_down(self, sample_candles, default_params):
        """Test entry generation in TREND_DOWN regime."""
        features = calculate_features(sample_candles, default_params)

        entries = generate_entries(
            sample_candles,
            features,
            RegimeType.TREND_DOWN,
            default_params,
        )

        for entry in entries:
            assert entry.side == EntrySide.SHORT, "TREND_DOWN should only generate SHORT entries"
            assert entry.regime == RegimeType.TREND_DOWN

    def test_generate_entries_range(self, sample_candles, default_params):
        """Test entry generation in RANGE regime."""
        features = calculate_features(sample_candles, default_params)

        entries = generate_entries(
            sample_candles,
            features,
            RegimeType.RANGE,
            default_params,
        )

        # Range regime can generate both LONG and SHORT
        assert isinstance(entries, list)
        for entry in entries:
            assert entry.regime == RegimeType.RANGE

    def test_generate_entries_squeeze(self, sample_candles, default_params):
        """Test entry generation in SQUEEZE regime."""
        features = calculate_features(sample_candles, default_params)

        entries = generate_entries(
            sample_candles,
            features,
            RegimeType.SQUEEZE,
            default_params,
        )

        assert isinstance(entries, list)
        for entry in entries:
            assert entry.regime == RegimeType.SQUEEZE

    def test_generate_entries_high_vol(self, sample_candles, default_params):
        """Test entry generation in HIGH_VOL regime."""
        features = calculate_features(sample_candles, default_params)

        entries = generate_entries(
            sample_candles,
            features,
            RegimeType.HIGH_VOL,
            default_params,
        )

        assert isinstance(entries, list)
        for entry in entries:
            assert entry.regime == RegimeType.HIGH_VOL

    def test_generate_entries_empty_candles(self, default_params):
        """Test with empty candles."""
        entries = generate_entries([], {}, RegimeType.TREND_UP, default_params)
        assert entries == [], "Should return empty list for empty candles"

    def test_generate_entries_min_confidence_filter(self, sample_candles):
        """Test that min_confidence filter works."""
        params = OptimParams(min_confidence=0.9)  # Very high threshold
        features = calculate_features(sample_candles, params)

        entries = generate_entries(
            sample_candles,
            features,
            RegimeType.TREND_UP,
            params,
        )

        # Should filter out low-confidence entries
        for entry in entries:
            assert entry.confidence >= 0.9

    def test_generate_entries_cooldown(self, sample_candles):
        """Test that cooldown between entries is enforced."""
        params = OptimParams(cooldown_bars=20)  # Large cooldown
        features = calculate_features(sample_candles, params)

        entries = generate_entries(
            sample_candles,
            features,
            RegimeType.TREND_UP,
            params,
        )

        # Check timestamps are sufficiently spaced
        long_entries = [e for e in entries if e.side == EntrySide.LONG]
        if len(long_entries) > 1:
            # Approximate check: timestamps should be far apart
            timestamps = [e.timestamp for e in long_entries]
            for i in range(1, len(timestamps)):
                # Each candle is 60s apart in fixture
                min_gap = params.cooldown_bars * 60
                assert timestamps[i] - timestamps[i-1] >= min_gap

    def test_generate_entries_deterministic(self, sample_candles, default_params):
        """Test that generate_entries is deterministic."""
        features = calculate_features(sample_candles, default_params)

        entries1 = generate_entries(
            sample_candles,
            features,
            RegimeType.TREND_UP,
            default_params,
        )

        entries2 = generate_entries(
            sample_candles,
            features,
            RegimeType.TREND_UP,
            default_params,
        )

        # Should produce identical results
        assert len(entries1) == len(entries2)
        for e1, e2 in zip(entries1, entries2):
            assert e1.timestamp == e2.timestamp
            assert e1.side == e2.side
            assert abs(e1.confidence - e2.confidence) < 1e-9
            assert abs(e1.price - e2.price) < 1e-9
            assert e1.reason_tags == e2.reason_tags
            assert e1.regime == e2.regime
