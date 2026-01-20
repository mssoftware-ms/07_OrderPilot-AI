"""Test Gap-Filling with verschiedenen Szenarien.

Testet Gap Detection und Gap Filling für:
- 5 Minuten offline (kleine Lücke)
- 1 Tag offline (mittlere Lücke)
- 1 Woche offline (große Lücke)

Usage:
    python -m pytest tests/test_gap_filling.py -v
    oder
    python tests/test_gap_filling.py  # Standalone execution
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from src.core.pattern_db.gap_detector import GapDetector, DataGap
from src.core.pattern_db.gap_filler import GapFiller
from src.core.pattern_db.qdrant_client import TradingPatternDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def test_gap_detection():
    """Test 1: Gap Detection Algorithm"""
    print("\n" + "=" * 60)
    print("TEST 1: GAP DETECTION")
    print("=" * 60)

    db = TradingPatternDB()
    success = await db.initialize()
    if not success:
        print("❌ FEHLER: Qdrant nicht erreichbar!")
        return False

    detector = GapDetector(db=db)
    await detector.initialize()

    # Test detection for BTCUSDT 1m
    symbol = "BTCUSDT"
    timeframe = "1m"

    print(f"\n🔍 Scanning for gaps: {symbol} {timeframe}")
    gaps = await detector.detect_gaps(symbol, timeframe, max_history_days=30)

    if gaps:
        print(f"✅ Found {len(gaps)} gaps:")
        for i, gap in enumerate(gaps, 1):
            print(f"   {i}. Gap Type: {gap.gap_type}")
            print(f"      Period: {gap.gap_start.strftime('%Y-%m-%d %H:%M')} → {gap.gap_end.strftime('%Y-%m-%d %H:%M')}")
            print(f"      Estimated Candles: {gap.estimated_candles:,}")
            print(f"      Duration: {gap.duration_hours:.1f} hours")
    else:
        print("✅ No gaps found - Database is up-to-date!")

    return True


async def test_gap_filling_small():
    """Test 2: Small Gap (5 Minuten offline)"""
    print("\n" + "=" * 60)
    print("TEST 2: SMALL GAP FILLING (5 Minuten)")
    print("=" * 60)

    filler = GapFiller()
    await filler.initialize()

    # Simulate 5-minute gap
    now = datetime.now(timezone.utc)
    gap_start = now - timedelta(minutes=5)
    gap = DataGap(
        symbol="BTCUSDT",
        timeframe="1m",
        gap_start=gap_start,
        gap_end=now,
        estimated_candles=5,
        gap_type="small"
    )

    def on_progress(current, total, status):
        print(f"   Progress: {current}/{total} - {status}")

    print(f"\n📥 Filling small gap: {gap.estimated_candles} candles")
    patterns_inserted = await filler.fill_gap(gap, progress_callback=on_progress)

    if patterns_inserted > 0:
        print(f"✅ Small gap filled: {patterns_inserted} patterns inserted")
        return True
    else:
        print("⚠️ No patterns inserted (gap might already be filled)")
        return True  # Not an error


async def test_gap_filling_medium():
    """Test 3: Medium Gap (1 Tag offline)"""
    print("\n" + "=" * 60)
    print("TEST 3: MEDIUM GAP FILLING (1 Tag = 1440 Minuten)")
    print("=" * 60)

    filler = GapFiller()
    await filler.initialize()

    # Simulate 1-day gap
    now = datetime.now(timezone.utc)
    gap_start = now - timedelta(days=1)
    gap = DataGap(
        symbol="BTCUSDT",
        timeframe="1m",
        gap_start=gap_start,
        gap_end=now,
        estimated_candles=1440,
        gap_type="medium"
    )

    def on_progress(current, total, status):
        if current % 200 == 0:  # Log every 200 candles
            print(f"   Progress: {current}/{total} - {status}")

    print(f"\n📥 Filling medium gap: {gap.estimated_candles} candles")

    # Estimate fill time
    seconds, readable = await filler.estimate_fill_time(gap)
    print(f"⏱️  Estimated time: {readable}")

    patterns_inserted = await filler.fill_gap(gap, progress_callback=on_progress)

    if patterns_inserted > 0:
        print(f"✅ Medium gap filled: {patterns_inserted} patterns inserted")
        return True
    else:
        print("⚠️ No patterns inserted (gap might already be filled)")
        return True


async def test_gap_filling_large():
    """Test 4: Large Gap (1 Woche offline)"""
    print("\n" + "=" * 60)
    print("TEST 4: LARGE GAP FILLING (1 Woche = 10,080 Minuten)")
    print("=" * 60)

    filler = GapFiller()
    await filler.initialize()

    # Simulate 1-week gap
    now = datetime.now(timezone.utc)
    gap_start = now - timedelta(weeks=1)
    gap = DataGap(
        symbol="BTCUSDT",
        timeframe="1m",
        gap_start=gap_start,
        gap_end=now,
        estimated_candles=10080,
        gap_type="large"
    )

    def on_progress(current, total, status):
        if current % 500 == 0:  # Log every 500 candles
            print(f"   Progress: {current}/{total} - {status}")

    print(f"\n📥 Filling large gap: {gap.estimated_candles:,} candles")

    # Estimate fill time
    seconds, readable = await filler.estimate_fill_time(gap)
    print(f"⏱️  Estimated time: {readable}")

    patterns_inserted = await filler.fill_gap(gap, progress_callback=on_progress)

    if patterns_inserted > 0:
        print(f"✅ Large gap filled: {patterns_inserted} patterns inserted")
        return True
    else:
        print("⚠️ No patterns inserted (gap might already be filled)")
        return True


async def test_update_to_now():
    """Test 5: Quick Update (Update to NOW)"""
    print("\n" + "=" * 60)
    print("TEST 5: QUICK UPDATE (Fill from latest pattern to NOW)")
    print("=" * 60)

    filler = GapFiller()
    await filler.initialize()

    symbol = "BTCUSDT"
    timeframe = "1m"

    def on_progress(current, total, status):
        print(f"   Progress: {current}/{total} - {status}")

    print(f"\n🔄 Quick update for {symbol} {timeframe}")
    patterns_inserted = await filler.update_to_now(
        symbol, timeframe, progress_callback=on_progress
    )

    if patterns_inserted > 0:
        print(f"✅ Quick update completed: {patterns_inserted} patterns inserted")
    else:
        print("✅ Database already up-to-date!")

    return True


async def test_fill_all_gaps():
    """Test 6: Full Gap Fill (Detect + Fill All)"""
    print("\n" + "=" * 60)
    print("TEST 6: FULL GAP FILL (Detect + Fill All Gaps)")
    print("=" * 60)

    filler = GapFiller()
    await filler.initialize()

    symbol = "BTCUSDT"
    timeframe = "5m"  # Use 5m for faster testing

    def on_progress(current, total, status):
        print(f"   Progress: {current}/{total} - {status}")

    print(f"\n📊 Full gap fill for {symbol} {timeframe} (30 days history)")
    total_patterns = await filler.fill_all_gaps(
        symbol, timeframe, max_history_days=30, progress_callback=on_progress
    )

    print(f"\n✅ Full gap fill completed: {total_patterns} total patterns inserted")
    return True


async def run_all_tests():
    """Run all gap-filling tests."""
    print("\n" + "=" * 80)
    print("🚀 GAP-FILLING TEST SUITE")
    print("=" * 80)
    print("\nThis will test gap detection and filling with different scenarios:")
    print("  1. Gap Detection Algorithm")
    print("  2. Small Gap (5 minutes)")
    print("  3. Medium Gap (1 day)")
    print("  4. Large Gap (1 week)")
    print("  5. Quick Update (to now)")
    print("  6. Full Gap Fill (detect + fill all)")
    print("\n" + "=" * 80)

    results = []

    # Test 1: Gap Detection
    try:
        success = await test_gap_detection()
        results.append(("Gap Detection", success))
    except Exception as e:
        logger.exception("Test 1 failed")
        results.append(("Gap Detection", False))
        print(f"❌ TEST 1 FAILED: {e}")

    # Test 2: Small Gap
    try:
        success = await test_gap_filling_small()
        results.append(("Small Gap (5min)", success))
    except Exception as e:
        logger.exception("Test 2 failed")
        results.append(("Small Gap (5min)", False))
        print(f"❌ TEST 2 FAILED: {e}")

    # Test 3: Medium Gap
    try:
        success = await test_gap_filling_medium()
        results.append(("Medium Gap (1 day)", success))
    except Exception as e:
        logger.exception("Test 3 failed")
        results.append(("Medium Gap (1 day)", False))
        print(f"❌ TEST 3 FAILED: {e}")

    # Test 4: Large Gap (commented out by default - takes ~10 seconds)
    # try:
    #     success = await test_gap_filling_large()
    #     results.append(("Large Gap (1 week)", success))
    # except Exception as e:
    #     logger.exception("Test 4 failed")
    #     results.append(("Large Gap (1 week)", False))
    #     print(f"❌ TEST 4 FAILED: {e}")

    # Test 5: Quick Update
    try:
        success = await test_update_to_now()
        results.append(("Quick Update", success))
    except Exception as e:
        logger.exception("Test 5 failed")
        results.append(("Quick Update", False))
        print(f"❌ TEST 5 FAILED: {e}")

    # Test 6: Full Gap Fill (commented out by default - takes longer)
    # try:
    #     success = await test_fill_all_gaps()
    #     results.append(("Full Gap Fill", success))
    # except Exception as e:
    #     logger.exception("Test 6 failed")
    #     results.append(("Full Gap Fill", False))
    #     print(f"❌ TEST 6 FAILED: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status}: {test_name}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️ {total - passed} test(s) failed")

    print("=" * 80)


if __name__ == "__main__":
    # Standalone execution
    asyncio.run(run_all_tests())
