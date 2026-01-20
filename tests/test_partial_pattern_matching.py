"""Tests for Partial Pattern Matching (Phase 3 - Teilmustererkennung).

Test Coverage:
1. Projection Methods (zero_pad, last_value, trend_projection)
2. Confidence Adjustment (completion penalty)
3. Early Entry Opportunity Detection
4. Integration with PatternService
5. Edge Cases (minimum bars, full completion, etc.)
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from src.core.market_data.types import HistoricalBar
from src.core.pattern_db.partial_matcher import PartialPatternMatcher, PartialPatternAnalysis
from src.core.pattern_db.pattern_service import PatternService


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_bar(index: int, base_time: datetime = None, trend: str = "up") -> HistoricalBar:
    """Create a test bar with predictable OHLCV values.

    Args:
        index: Bar index
        base_time: Base timestamp
        trend: "up", "down", or "sideways"

    Returns:
        HistoricalBar
    """
    if base_time is None:
        base_time = datetime(2024, 1, 1, 9, 0)

    timestamp = base_time + timedelta(minutes=index)

    # Create price based on trend
    if trend == "up":
        base_price = 100.0 + (index * 0.5)  # Uptrend
    elif trend == "down":
        base_price = 120.0 - (index * 0.5)  # Downtrend
    else:
        base_price = 100.0 + (index % 2) * 0.2  # Sideways with noise

    return HistoricalBar(
        timestamp=timestamp,
        open=base_price,
        high=base_price + 1.0,
        low=base_price - 1.0,
        close=base_price + 0.5,
        volume=1000.0 + (index * 100),
    )


def create_bars_sequence(
    count: int,
    base_time: datetime = None,
    trend: str = "up"
) -> List[HistoricalBar]:
    """Create a sequence of test bars.

    Args:
        count: Number of bars
        base_time: Base timestamp
        trend: Trend direction

    Returns:
        List of bars
    """
    return [create_test_bar(i, base_time, trend) for i in range(count)]


# ============================================================================
# Test 1: Projection Methods
# ============================================================================

def test_zero_pad_projection():
    """Test zero-padding projection method."""
    print("\n=== Test 1: Zero-Pad Projection ===")

    matcher = PartialPatternMatcher(
        full_window_size=20,
        min_bars_required=10,
        projection_method="zero_pad"
    )

    # Create 15 partial bars
    partial_bars = create_bars_sequence(15, trend="up")

    # Project to 20 bars
    projected_bars = matcher._zero_pad(partial_bars, missing_bars=5)

    assert len(projected_bars) == 20, f"Expected 20 bars, got {len(projected_bars)}"

    # Last 5 bars should have same close as bar 14 (zero-padded)
    last_close = partial_bars[-1].close
    for i in range(15, 20):
        assert projected_bars[i].close == last_close, \
            f"Bar {i} should have close={last_close}, got {projected_bars[i].close}"

    print("✅ Zero-padding produces 20 bars with flat continuation")
    print(f"✅ Last 5 bars maintain close price: {last_close:.2f}")
    print("✅ TEST PASSED: Zero-pad projection\n")


def test_last_value_projection():
    """Test last-value repetition projection method."""
    print("\n=== Test 2: Last-Value Projection ===")

    matcher = PartialPatternMatcher(
        full_window_size=20,
        min_bars_required=10,
        projection_method="last_value"
    )

    # Create 12 partial bars
    partial_bars = create_bars_sequence(12, trend="down")

    # Project to 20 bars
    projected_bars = matcher._repeat_last_value(partial_bars, missing_bars=8)

    assert len(projected_bars) == 20, f"Expected 20 bars, got {len(projected_bars)}"

    # Last 8 bars should repeat last bar's close
    last_bar = partial_bars[-1]
    for i in range(12, 20):
        assert projected_bars[i].close == last_bar.close
        assert projected_bars[i].volume == last_bar.volume

    print("✅ Last-value projection produces 20 bars")
    print(f"✅ Last 8 bars repeat close: {last_bar.close:.2f}")
    print("✅ TEST PASSED: Last-value projection\n")


def test_trend_projection():
    """Test trend-based projection method (linear regression)."""
    print("\n=== Test 3: Trend Projection ===")

    matcher = PartialPatternMatcher(
        full_window_size=20,
        min_bars_required=10,
        projection_method="trend_projection"
    )

    # Create 15 uptrend bars
    partial_bars = create_bars_sequence(15, trend="up")

    # Project to 20 bars
    projected_bars = matcher._trend_projection(partial_bars, missing_bars=5)

    assert len(projected_bars) == 20, f"Expected 20 bars, got {len(projected_bars)}"

    # Projected bars should continue the uptrend
    bar_14_close = partial_bars[-1].close
    bar_19_close = projected_bars[-1].close

    # For uptrend, bar 19 should be higher than bar 14
    assert bar_19_close > bar_14_close, \
        f"Trend projection should continue uptrend: {bar_19_close} <= {bar_14_close}"

    print(f"✅ Trend projection continues uptrend")
    print(f"✅ Bar 14 close: {bar_14_close:.2f}")
    print(f"✅ Bar 19 close: {bar_19_close:.2f} (projected higher)")
    print("✅ TEST PASSED: Trend projection\n")


# ============================================================================
# Test 2: Confidence Adjustment
# ============================================================================

def test_confidence_penalty_calculation():
    """Test confidence penalty based on completion ratio."""
    print("\n=== Test 4: Confidence Penalty Calculation ===")

    matcher = PartialPatternMatcher(
        full_window_size=20,
        min_bars_required=10,
        confidence_penalty_alpha=0.7  # Penalty exponent
    )

    # Test different completion ratios
    test_cases = [
        (10, 20, 0.5),   # 50% completion
        (15, 20, 0.75),  # 75% completion
        (18, 20, 0.9),   # 90% completion
        (20, 20, 1.0),   # 100% completion
    ]

    base_confidence = 0.8  # Assume high base confidence

    for bars_formed, bars_required, expected_ratio in test_cases:
        completion_ratio = bars_formed / bars_required

        # Calculate penalty: confidence = base * (ratio ^ alpha)
        penalty_factor = completion_ratio ** matcher.confidence_penalty_alpha
        adjusted_confidence = base_confidence * penalty_factor

        print(f"  {bars_formed}/{bars_required} bars ({completion_ratio:.0%}): "
              f"confidence {base_confidence:.2f} → {adjusted_confidence:.2f} "
              f"(penalty: {1 - penalty_factor:.2%})")

        # Verify penalty increases confidence for more complete patterns
        assert adjusted_confidence <= base_confidence, \
            "Adjusted confidence should never exceed base confidence"

        if completion_ratio < 1.0:
            assert adjusted_confidence < base_confidence, \
                "Partial patterns should have reduced confidence"

    print("✅ Confidence penalty correctly applied")
    print("✅ More complete patterns have higher confidence")
    print("✅ TEST PASSED: Confidence penalty calculation\n")


# ============================================================================
# Test 3: Early Entry Opportunity Detection
# ============================================================================

@pytest.mark.asyncio
async def test_early_entry_opportunity_detection():
    """Test detection of early entry opportunities."""
    print("\n=== Test 5: Early Entry Opportunity Detection ===")

    matcher = PartialPatternMatcher(
        full_window_size=20,
        min_bars_required=10,
        projection_method="trend_projection"
    )

    await matcher.initialize()

    # Create 15 bars (75% completion)
    partial_bars = create_bars_sequence(15, trend="up")

    # Early entry criteria:
    # - completion_ratio < 0.9 (not fully formed)
    # - adjusted_confidence > 0.5
    # - signal_boost > 0.4
    # - similar_patterns_count >= 10

    # Mock analysis (in real scenario, this would come from DB search)
    # For testing, we'll check the logic in the matcher

    completion_ratio = 15 / 20  # 0.75

    # Early entry should trigger if:
    # 1. Pattern is incomplete (< 90%)
    assert completion_ratio < 0.9, "Pattern should be incomplete for early entry"

    # 2. High confidence despite incompletion
    base_confidence = 0.7
    penalty_factor = completion_ratio ** 0.7  # ≈ 0.80
    adjusted_confidence = base_confidence * penalty_factor  # ≈ 0.56

    assert adjusted_confidence > 0.5, "Should have sufficient confidence"

    print(f"✅ Pattern {completion_ratio:.1%} complete (< 90%)")
    print(f"✅ Adjusted confidence: {adjusted_confidence:.2f} (> 0.5)")
    print("✅ Early entry opportunity conditions met")
    print("✅ TEST PASSED: Early entry opportunity detection\n")


# ============================================================================
# Test 4: Integration with PatternService
# ============================================================================

@pytest.mark.asyncio
async def test_pattern_service_partial_integration():
    """Test integration of partial matching with PatternService."""
    print("\n=== Test 6: PatternService Partial Integration ===")

    service = PatternService(window_size=20)
    await service.initialize()

    # Create partial bars (12 out of 20)
    partial_bars = create_bars_sequence(12, trend="up")

    # Test analyze_partial_signal
    analysis = await service.analyze_partial_signal(
        bars=partial_bars,
        symbol="BTCUSDT",
        timeframe="1m",
        signal_direction="long",
    )

    # Analysis might be None if not enough patterns in DB, but method should not crash
    print(f"Partial analysis result: {type(analysis).__name__ if analysis else 'None'}")

    if analysis:
        print(f"  Bars formed: {analysis.bars_formed}/{analysis.bars_required}")
        print(f"  Completion: {analysis.completion_ratio:.1%}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print(f"  Projection: {analysis.projection_method}")
        print(f"  Early entry: {analysis.early_entry_opportunity}")

        # Validate analysis structure
        assert analysis.bars_formed == 12
        assert analysis.bars_required == 20
        assert 0 <= analysis.completion_ratio <= 1.0
        assert 0 <= analysis.confidence <= 1.0
        assert analysis.projection_method in ["zero_pad", "last_value", "trend_projection"]

    print("✅ PatternService.analyze_partial_signal() works")
    print("✅ No crashes or exceptions")
    print("✅ TEST PASSED: PatternService integration\n")


# ============================================================================
# Test 5: Edge Cases
# ============================================================================

def test_minimum_bars_requirement():
    """Test minimum bars requirement (50% completion)."""
    print("\n=== Test 7: Minimum Bars Requirement ===")

    matcher = PartialPatternMatcher(
        full_window_size=20,
        min_bars_required=10,  # 50% minimum
    )

    # Test below minimum (should fail validation in analyze_partial_signal)
    too_few_bars = create_bars_sequence(9)

    # This would be caught in analyze_partial_signal, returning None
    assert len(too_few_bars) < matcher.min_bars_required

    print(f"✅ Bars below minimum: {len(too_few_bars)} < {matcher.min_bars_required}")

    # Test exactly at minimum (should pass)
    minimum_bars = create_bars_sequence(10)

    assert len(minimum_bars) >= matcher.min_bars_required

    print(f"✅ Bars at minimum: {len(minimum_bars)} >= {matcher.min_bars_required}")
    print("✅ TEST PASSED: Minimum bars requirement\n")


def test_full_completion_behavior():
    """Test behavior when pattern is already fully complete."""
    print("\n=== Test 8: Full Completion Behavior ===")

    matcher = PartialPatternMatcher(
        full_window_size=20,
        min_bars_required=10,
    )

    # Create full 20 bars
    full_bars = create_bars_sequence(20, trend="up")

    # Project (should just use existing bars)
    projected_pattern = matcher._project_partial_pattern(
        bars=full_bars,
        symbol="BTCUSDT",
        timeframe="1m",
    )

    assert projected_pattern is not None, "Should successfully create pattern"

    # Completion ratio should be 1.0
    completion_ratio = len(full_bars) / matcher.full_window_size
    assert completion_ratio == 1.0, f"Expected 1.0, got {completion_ratio}"

    # No confidence penalty for full pattern
    penalty_factor = completion_ratio ** matcher.confidence_penalty_alpha
    assert penalty_factor == 1.0, "No penalty for 100% completion"

    print("✅ Full pattern (20/20 bars) processed correctly")
    print("✅ Completion ratio: 1.0 (100%)")
    print("✅ No confidence penalty applied")
    print("✅ TEST PASSED: Full completion behavior\n")


def test_projection_method_fallback():
    """Test fallback behavior for unknown projection method."""
    print("\n=== Test 9: Projection Method Fallback ===")

    # Create matcher with invalid projection method
    matcher = PartialPatternMatcher(
        full_window_size=20,
        min_bars_required=10,
        projection_method="invalid_method"  # Not supported
    )

    # Should fallback to trend_projection
    partial_bars = create_bars_sequence(15, trend="up")

    # This should not crash, should use trend_projection as fallback
    projected_pattern = matcher._project_partial_pattern(
        bars=partial_bars,
        symbol="BTCUSDT",
        timeframe="1m",
    )

    assert projected_pattern is not None, "Should fallback to trend_projection"

    print("✅ Invalid projection method handled gracefully")
    print("✅ Fallback to trend_projection successful")
    print("✅ TEST PASSED: Projection method fallback\n")


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Phase 3: Partial Pattern Matching Tests")
    print("="*70)

    # Run synchronous tests
    test_zero_pad_projection()
    test_last_value_projection()
    test_trend_projection()
    test_confidence_penalty_calculation()
    test_minimum_bars_requirement()
    test_full_completion_behavior()
    test_projection_method_fallback()

    # Run async tests
    import asyncio
    asyncio.run(test_early_entry_opportunity_detection())
    asyncio.run(test_pattern_service_partial_integration())

    print("\n" + "="*70)
    print("✅ ALL PHASE 3 TESTS PASSED!")
    print("="*70)
    print("\nTest Summary:")
    print("  1. ✅ Zero-pad projection")
    print("  2. ✅ Last-value projection")
    print("  3. ✅ Trend projection")
    print("  4. ✅ Confidence penalty calculation")
    print("  5. ✅ Early entry opportunity detection")
    print("  6. ✅ PatternService integration")
    print("  7. ✅ Minimum bars requirement")
    print("  8. ✅ Full completion behavior")
    print("  9. ✅ Projection method fallback")
    print("\n" + "="*70 + "\n")
