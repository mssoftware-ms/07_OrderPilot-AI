"""Tests for TimeframeConverter (Phase 2 - Timeframe-Konvertierung).

Test Coverage:
1. Basic Conversion (1m → 5m, 15m, 1h)
2. OHLC Aggregation Validation
3. Edge Cases (same timeframe, downsampling, non-multiples)
4. Integration with PatternService
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from src.core.market_data.types import HistoricalBar
from src.core.pattern_db.timeframe_converter import TimeframeConverter
from src.core.pattern_db.pattern_service import PatternService


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_bar(index: int, base_time: datetime = None) -> HistoricalBar:
    """Create a test bar with predictable OHLCV values."""
    if base_time is None:
        base_time = datetime(2024, 1, 1, 9, 0)

    timestamp = base_time + timedelta(minutes=index)

    return HistoricalBar(
        timestamp=timestamp,
        open=100.0 + index,
        high=105.0 + index,
        low=95.0 + index,
        close=102.0 + index,
        volume=1000.0 + (index * 100),
    )


def create_bars_sequence(count: int, base_time: datetime = None) -> List[HistoricalBar]:
    """Create a sequence of test bars."""
    return [create_test_bar(i, base_time) for i in range(count)]


# ============================================================================
# Test 1: Basic Conversions
# ============================================================================

def test_1m_to_5m_conversion():
    """Test 1min → 5min conversion (5:1 ratio)."""
    print("\n=== Test 1: 1m → 5m Conversion ===")

    # Create 10 x 1min bars
    bars_1m = create_bars_sequence(10)

    # Convert to 5min (should yield 2 bars)
    bars_5m = TimeframeConverter.resample_bars(bars_1m, "1m", "5m")

    print(f"Input: {len(bars_1m)} bars (1m)")
    print(f"Output: {len(bars_5m)} bars (5m)")

    # Assertions
    assert len(bars_5m) == 2, f"Expected 2 bars, got {len(bars_5m)}"

    # First 5m bar (aggregates bars 0-4)
    assert bars_5m[0].open == bars_1m[0].open, "First open should be preserved"
    assert bars_5m[0].high == max(bars_1m[i].high for i in range(5)), "High should be max"
    assert bars_5m[0].low == min(bars_1m[i].low for i in range(5)), "Low should be min"
    assert bars_5m[0].close == bars_1m[4].close, "Close should be last"
    assert bars_5m[0].volume == sum(bars_1m[i].volume for i in range(5)), "Volume should be summed"

    print("✅ First 5m bar aggregation correct")

    # Second 5m bar (aggregates bars 5-9)
    assert bars_5m[1].open == bars_1m[5].open
    assert bars_5m[1].close == bars_1m[9].close

    print("✅ Second 5m bar aggregation correct")
    print("✅ TEST PASSED: 1m → 5m conversion\n")


def test_1m_to_15m_conversion():
    """Test 1min → 15min conversion (15:1 ratio)."""
    print("\n=== Test 2: 1m → 15m Conversion ===")

    # Create 30 x 1min bars
    bars_1m = create_bars_sequence(30)

    # Convert to 15min (should yield 2 bars)
    bars_15m = TimeframeConverter.resample_bars(bars_1m, "1m", "15m")

    print(f"Input: {len(bars_1m)} bars (1m)")
    print(f"Output: {len(bars_15m)} bars (15m)")

    assert len(bars_15m) == 2, f"Expected 2 bars, got {len(bars_15m)}"

    # Validate first bar aggregation (0-14)
    assert bars_15m[0].open == bars_1m[0].open
    assert bars_15m[0].close == bars_1m[14].close
    assert bars_15m[0].volume == sum(bars_1m[i].volume for i in range(15))

    print("✅ TEST PASSED: 1m → 15m conversion\n")


def test_5m_to_15m_conversion():
    """Test 5min → 15min conversion (3:1 ratio)."""
    print("\n=== Test 3: 5m → 15m Conversion ===")

    # Create 6 x 5min bars
    bars_5m = create_bars_sequence(6)

    # Convert to 15min (should yield 2 bars)
    bars_15m = TimeframeConverter.resample_bars(bars_5m, "5m", "15m")

    print(f"Input: {len(bars_5m)} bars (5m)")
    print(f"Output: {len(bars_15m)} bars (15m)")

    assert len(bars_15m) == 2, f"Expected 2 bars, got {len(bars_15m)}"

    # Validate aggregation
    assert bars_15m[0].volume == sum(bars_5m[i].volume for i in range(3))

    print("✅ TEST PASSED: 5m → 15m conversion\n")


# ============================================================================
# Test 2: OHLC Aggregation Validation
# ============================================================================

def test_ohlc_aggregation_correctness():
    """Test that OHLC aggregation follows correct rules."""
    print("\n=== Test 4: OHLC Aggregation Rules ===")

    # Create 5 bars with specific OHLC patterns
    base_time = datetime(2024, 1, 1, 9, 0)
    bars = [
        HistoricalBar(base_time + timedelta(minutes=0), open=100, high=110, low=95, close=105, volume=1000),
        HistoricalBar(base_time + timedelta(minutes=1), open=105, high=115, low=100, close=110, volume=1500),
        HistoricalBar(base_time + timedelta(minutes=2), open=110, high=120, low=105, close=115, volume=2000),  # Highest high
        HistoricalBar(base_time + timedelta(minutes=3), open=115, high=118, low=90, close=95, volume=1200),   # Lowest low
        HistoricalBar(base_time + timedelta(minutes=4), open=95, high=100, low=92, close=98, volume=1800),    # Last close
    ]

    # Convert to 5min
    bars_5m = TimeframeConverter.resample_bars(bars, "1m", "5m")

    assert len(bars_5m) == 1

    aggregated = bars_5m[0]

    # Validate OHLC rules
    assert aggregated.open == 100, f"Open should be 100 (first), got {aggregated.open}"
    assert aggregated.high == 120, f"High should be 120 (max), got {aggregated.high}"
    assert aggregated.low == 90, f"Low should be 90 (min), got {aggregated.low}"
    assert aggregated.close == 98, f"Close should be 98 (last), got {aggregated.close}"
    assert aggregated.volume == 7500, f"Volume should be 7500 (sum), got {aggregated.volume}"

    print("✅ Open: First bar's open (100)")
    print("✅ High: Maximum high (120)")
    print("✅ Low: Minimum low (90)")
    print("✅ Close: Last bar's close (98)")
    print("✅ Volume: Sum of all volumes (7500)")
    print("✅ TEST PASSED: OHLC aggregation rules\n")


# ============================================================================
# Test 3: Edge Cases
# ============================================================================

def test_same_timeframe_no_conversion():
    """Test that same timeframe returns original bars."""
    print("\n=== Test 5: Same Timeframe (1m → 1m) ===")

    bars_1m = create_bars_sequence(10)

    # Convert 1m → 1m (no conversion)
    bars_out = TimeframeConverter.resample_bars(bars_1m, "1m", "1m")

    assert len(bars_out) == len(bars_1m), "Should return same number of bars"
    assert bars_out[0].open == bars_1m[0].open, "Bars should be unchanged"

    print("✅ TEST PASSED: Same timeframe returns original bars\n")


def test_downsampling_not_supported():
    """Test that downsampling raises ValueError."""
    print("\n=== Test 6: Downsampling (5m → 1m) Should Fail ===")

    bars_5m = create_bars_sequence(5)

    # Attempt downsampling (should raise ValueError)
    with pytest.raises(ValueError, match="Downsampling not supported"):
        TimeframeConverter.resample_bars(bars_5m, "5m", "1m")

    print("✅ TEST PASSED: Downsampling correctly rejected\n")


def test_non_multiple_timeframe_fails():
    """Test that non-multiple timeframes are rejected."""
    print("\n=== Test 7: Non-Multiple Timeframe (1m → 7m) Should Fail ===")

    bars_1m = create_bars_sequence(10)

    # Attempt conversion to non-multiple (1m → 7m)
    # Note: 7m is not in TIMEFRAME_MINUTES, so it should fail with ValueError
    with pytest.raises(ValueError, match="Invalid target timeframe"):
        TimeframeConverter.resample_bars(bars_1m, "1m", "7m")

    print("✅ TEST PASSED: Non-multiple timeframe correctly rejected\n")


def test_incomplete_bucket_handling():
    """Test handling of incomplete final bucket."""
    print("\n=== Test 8: Incomplete Final Bucket ===")

    # Create 12 x 1min bars (not divisible by 5)
    bars_1m = create_bars_sequence(12)

    # Convert to 5min (should yield 3 bars: 5+5+2)
    bars_5m = TimeframeConverter.resample_bars(bars_1m, "1m", "5m")

    print(f"Input: {len(bars_1m)} bars (1m)")
    print(f"Output: {len(bars_5m)} bars (5m)")

    assert len(bars_5m) == 3, f"Expected 3 bars, got {len(bars_5m)}"

    # Last bar should aggregate only 2 bars (10-11)
    assert bars_5m[2].open == bars_1m[10].open, "Last bucket should start at bar 10"
    assert bars_5m[2].close == bars_1m[11].close, "Last bucket should end at bar 11"
    assert bars_5m[2].volume == bars_1m[10].volume + bars_1m[11].volume, "Last bucket should sum 2 bars"

    print("✅ TEST PASSED: Incomplete final bucket handled correctly\n")


# ============================================================================
# Test 4: Validation Functions
# ============================================================================

def test_can_convert_validation():
    """Test can_convert() validation function."""
    print("\n=== Test 9: can_convert() Validation ===")

    # Valid conversions
    can, reason = TimeframeConverter.can_convert("1m", "5m")
    assert can is True, "1m → 5m should be valid"
    print(f"✅ 1m → 5m: {reason}")

    can, reason = TimeframeConverter.can_convert("5m", "15m")
    assert can is True, "5m → 15m should be valid"
    print(f"✅ 5m → 15m: {reason}")

    # Invalid conversions
    can, reason = TimeframeConverter.can_convert("5m", "1m")
    assert can is False, "5m → 1m should be invalid (downsampling)"
    print(f"✅ 5m → 1m: {reason}")

    can, reason = TimeframeConverter.can_convert("1m", "7m")
    assert can is False, "1m → 7m should be invalid (non-existent timeframe)"
    print(f"✅ 1m → 7m: {reason}")

    print("✅ TEST PASSED: can_convert() validation\n")


def test_get_supported_conversions():
    """Test get_supported_conversions() function."""
    print("\n=== Test 10: get_supported_conversions() ===")

    # Get supported conversions from 1m
    supported = TimeframeConverter.get_supported_conversions("1m")

    print(f"Supported conversions from 1m: {supported}")

    assert "1m" in supported, "Should include same timeframe"
    assert "5m" in supported, "Should include 5m"
    assert "15m" in supported, "Should include 15m"
    assert "1h" in supported, "Should include 1h"
    assert "1d" in supported, "Should include 1d"

    print("✅ TEST PASSED: get_supported_conversions()\n")


# ============================================================================
# Test 5: Integration with PatternService
# ============================================================================

@pytest.mark.asyncio
async def test_pattern_service_integration():
    """Test integration with PatternService (target_timeframe parameter)."""
    print("\n=== Test 11: PatternService Integration ===")

    # Create test bars (1m)
    bars_1m = create_bars_sequence(100)

    # Initialize pattern service
    service = PatternService(window_size=20)
    await service.initialize()

    # Test 1: No target_timeframe (should use original bars)
    print("Testing without target_timeframe...")
    analysis = await service.analyze_signal(
        bars=bars_1m,
        symbol="BTCUSDT",
        timeframe="1m",
        signal_direction="long",
        target_timeframe=None  # No conversion
    )

    # Analysis might be None if not enough patterns found, but no error should occur
    print(f"Analysis result (no conversion): {type(analysis).__name__ if analysis else 'None'}")

    # Test 2: With target_timeframe (should resample bars)
    print("Testing with target_timeframe=5m...")
    analysis_5m = await service.analyze_signal(
        bars=bars_1m,
        symbol="BTCUSDT",
        timeframe="1m",
        signal_direction="long",
        target_timeframe="5m"  # Convert to 5m
    )

    print(f"Analysis result (5m conversion): {type(analysis_5m).__name__ if analysis_5m else 'None'}")

    # Test 3: Invalid conversion (should return None)
    print("Testing with invalid target_timeframe (downsampling)...")
    analysis_invalid = await service.analyze_signal(
        bars=create_bars_sequence(100),  # 5m bars
        symbol="BTCUSDT",
        timeframe="5m",
        signal_direction="long",
        target_timeframe="1m"  # Invalid: downsampling
    )

    assert analysis_invalid is None, "Invalid conversion should return None"
    print("✅ Invalid conversion correctly returned None")

    print("✅ TEST PASSED: PatternService integration\n")


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Phase 2: Timeframe Conversion Tests")
    print("="*70)

    # Run synchronous tests
    test_1m_to_5m_conversion()
    test_1m_to_15m_conversion()
    test_5m_to_15m_conversion()
    test_ohlc_aggregation_correctness()
    test_same_timeframe_no_conversion()
    test_downsampling_not_supported()
    test_non_multiple_timeframe_fails()
    test_incomplete_bucket_handling()
    test_can_convert_validation()
    test_get_supported_conversions()

    # Run async test
    import asyncio
    asyncio.run(test_pattern_service_integration())

    print("\n" + "="*70)
    print("✅ ALL PHASE 2 TESTS PASSED!")
    print("="*70)
    print("\nTest Summary:")
    print("  1. ✅ 1m → 5m conversion")
    print("  2. ✅ 1m → 15m conversion")
    print("  3. ✅ 5m → 15m conversion")
    print("  4. ✅ OHLC aggregation rules")
    print("  5. ✅ Same timeframe (no conversion)")
    print("  6. ✅ Downsampling rejection")
    print("  7. ✅ Non-multiple rejection")
    print("  8. ✅ Incomplete bucket handling")
    print("  9. ✅ can_convert() validation")
    print(" 10. ✅ get_supported_conversions()")
    print(" 11. ✅ PatternService integration")
    print("\n" + "="*70 + "\n")
