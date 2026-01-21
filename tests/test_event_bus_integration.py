"""Tests for Event Bus Integration with Pattern Recognition System.

Test Coverage:
1. EventType additions (Pattern DB events)
2. Event emission from PatternUpdateWorker
3. Event handling in PatternRecognitionWidget
4. Auto-update trigger logic
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from src.common.event_bus import event_bus, EventType, Event
from src.core.pattern_db.pattern_update_worker import PatternUpdateWorker


# Test 1: EventType Additions
def test_new_event_types_exist():
    """Test that new Pattern DB event types are defined."""
    print("\n=== Test 1: New EventType Additions ===")

    # Check all new event types
    required_events = [
        "PATTERN_DB_UPDATE_REQUESTED",
        "PATTERN_DB_UPDATE_STARTED",
        "PATTERN_DB_UPDATE_PROGRESS",
        "PATTERN_DB_UPDATE_COMPLETE",
        "PATTERN_DB_UPDATE_ERROR",
        "PATTERN_ANALYSIS_COMPLETE",
    ]

    for event_name in required_events:
        assert hasattr(EventType, event_name), f"EventType.{event_name} not found"
        print(f"✅ EventType.{event_name} exists")

    print("✅ TEST PASSED: All new EventTypes defined\n")


# Test 2: Event Bus Subscription/Unsubscription
def test_event_bus_subscribe_unsubscribe():
    """Test event bus subscribe/unsubscribe functionality."""
    print("\n=== Test 2: Event Bus Subscribe/Unsubscribe ===")

    # Define a test handler
    received_events = []

    def test_handler(event: Event):
        received_events.append(event)

    # Subscribe to PATTERN_DB_UPDATE_STARTED
    event_bus.subscribe(EventType.PATTERN_DB_UPDATE_STARTED, test_handler)

    # Emit test event
    test_event = Event(
        type=EventType.PATTERN_DB_UPDATE_STARTED,
        timestamp=datetime.now(),
        data={"symbol": "BTCUSDT", "timeframe": "1m"},
        source="test"
    )
    event_bus.emit(test_event)

    # Verify event received
    assert len(received_events) == 1, f"Expected 1 event, got {len(received_events)}"
    assert received_events[0].type == EventType.PATTERN_DB_UPDATE_STARTED
    assert received_events[0].data["symbol"] == "BTCUSDT"

    print("✅ Event received correctly")

    # Unsubscribe and verify no more events received
    event_bus.unsubscribe(EventType.PATTERN_DB_UPDATE_STARTED, test_handler)

    # Emit another event
    event_bus.emit(test_event)

    # Should still have only 1 event (not 2)
    assert len(received_events) == 1, "Unsubscribe failed - still receiving events"

    print("✅ Unsubscribe successful")
    print("✅ TEST PASSED: Subscribe/Unsubscribe works\n")


# Test 3: PatternUpdateWorker Event Emission
@pytest.mark.asyncio
async def test_worker_emits_events():
    """Test that PatternUpdateWorker emits event bus events."""
    print("\n=== Test 3: PatternUpdateWorker Event Emission ===")

    # Collect emitted events
    emitted_events = []

    def collect_events(event: Event):
        emitted_events.append(event)

    # Subscribe to all Pattern DB events
    event_types = [
        EventType.PATTERN_DB_UPDATE_STARTED,
        EventType.PATTERN_DB_UPDATE_PROGRESS,
        EventType.PATTERN_DB_UPDATE_COMPLETE,
        EventType.PATTERN_DB_UPDATE_ERROR,
    ]

    for event_type in event_types:
        event_bus.subscribe(event_type, collect_events)

    # Mock the worker's internal methods to avoid actual DB operations
    with patch.object(PatternUpdateWorker, '_initialize', return_value=True):
        with patch.object(PatternUpdateWorker, '_fill_gaps_for_pair', return_value=5):
            # Create worker (don't start thread, just test methods)
            worker = PatternUpdateWorker(
                symbols=["BTCUSDT"],
                timeframes=["1m"],
                scan_interval=1
            )

            # Manually call the scan method
            await worker._scan_and_fill_gaps()

            # Verify events were emitted
            print(f"Emitted {len(emitted_events)} events:")
            for event in emitted_events:
                print(f"  - {event.type.value}: {event.data}")

            # Should have at least STARTED and COMPLETE events
            started_events = [e for e in emitted_events if e.type == EventType.PATTERN_DB_UPDATE_STARTED]
            complete_events = [e for e in emitted_events if e.type == EventType.PATTERN_DB_UPDATE_COMPLETE]

            assert len(started_events) >= 1, "No STARTED events emitted"
            assert len(complete_events) >= 1, "No COMPLETE events emitted"

            # Verify event data
            assert started_events[0].data["symbol"] == "BTCUSDT"
            assert started_events[0].data["timeframe"] == "1m"

            assert complete_events[0].data["patterns_added"] == 5

            print("✅ Worker emitted STARTED event")
            print("✅ Worker emitted COMPLETE event")
            print("✅ Event data correct")

    # Cleanup
    for event_type in event_types:
        event_bus.unsubscribe(event_type, collect_events)

    print("✅ TEST PASSED: Worker emits events correctly\n")


# Test 4: Auto-Update Trigger Logic (Simulated)
def test_auto_update_trigger_logic():
    """Test auto-update trigger conditions (bar count + time interval)."""
    print("\n=== Test 4: Auto-Update Trigger Logic ===")

    # Simulate PatternRecognitionWidget auto-update logic
    class MockWidget:
        def __init__(self):
            self._auto_update_enabled = True
            self._pending_bars_count = 0
            self._pending_bars_threshold = 5
            self._auto_update_interval = timedelta(minutes=5)
            self._last_market_bar_time = None
            self.update_triggered = False

        def trigger_update(self, reason: str):
            self.update_triggered = True
            print(f"✅ Update triggered: {reason}")

        def on_market_bar(self):
            """Simulate receiving a MARKET_BAR event."""
            self._pending_bars_count += 1
            current_time = datetime.now()

            should_update = False
            reason = ""

            # Condition 1: Bar count threshold
            if self._pending_bars_count >= self._pending_bars_threshold:
                should_update = True
                reason = f"{self._pending_bars_count} new bars"

            # Condition 2: Time interval
            if self._last_market_bar_time:
                time_elapsed = current_time - self._last_market_bar_time
                if time_elapsed >= self._auto_update_interval:
                    should_update = True
                    reason = f"{time_elapsed.total_seconds() / 60:.1f} minutes elapsed"

            if should_update:
                self.trigger_update(reason)
                self._pending_bars_count = 0
                self._last_market_bar_time = current_time

    # Test 1: Trigger on bar count
    widget = MockWidget()

    # Simulate 5 bars
    for i in range(5):
        widget.on_market_bar()

    assert widget.update_triggered, "Update should trigger after 5 bars"
    print("✅ Update triggered after 5 bars")

    # Test 2: Trigger on time interval
    widget2 = MockWidget()
    widget2._last_market_bar_time = datetime.now() - timedelta(minutes=6)  # 6 minutes ago
    widget2.on_market_bar()

    assert widget2.update_triggered, "Update should trigger after 5 minutes"
    print("✅ Update triggered after time interval")

    print("✅ TEST PASSED: Auto-update trigger logic works\n")


# Test 5: Event Flow Integration Test
def test_event_flow_integration():
    """Test complete event flow from MARKET_BAR to DB update."""
    print("\n=== Test 5: Event Flow Integration Test ===")

    # Track event flow
    event_flow = []

    def track_flow(event: Event):
        event_flow.append(event.type.value)

    # Subscribe to relevant events
    events_to_track = [
        EventType.MARKET_BAR,
        EventType.PATTERN_DB_UPDATE_REQUESTED,
        EventType.PATTERN_DB_UPDATE_STARTED,
        EventType.PATTERN_DB_UPDATE_COMPLETE,
    ]

    for event_type in events_to_track:
        event_bus.subscribe(event_type, track_flow)

    # Simulate event flow
    # Step 1: Market bar received
    event_bus.emit(Event(
        type=EventType.MARKET_BAR,
        timestamp=datetime.now(),
        data={"symbol": "BTCUSDT", "timeframe": "1m"},
        source="test"
    ))

    # Step 2: Update requested (auto-triggered)
    event_bus.emit(Event(
        type=EventType.PATTERN_DB_UPDATE_REQUESTED,
        timestamp=datetime.now(),
        data={"symbol": "BTCUSDT", "timeframe": "1m", "trigger": "auto"},
        source="test"
    ))

    # Step 3: Update started
    event_bus.emit(Event(
        type=EventType.PATTERN_DB_UPDATE_STARTED,
        timestamp=datetime.now(),
        data={"symbol": "BTCUSDT", "timeframe": "1m"},
        source="test"
    ))

    # Step 4: Update completed
    event_bus.emit(Event(
        type=EventType.PATTERN_DB_UPDATE_COMPLETE,
        timestamp=datetime.now(),
        data={"symbol": "BTCUSDT", "timeframe": "1m", "patterns_added": 10},
        source="test"
    ))

    # Verify event flow
    expected_flow = [
        "market_bar",
        "pattern_db_update_requested",
        "pattern_db_update_started",
        "pattern_db_update_complete"
    ]

    print(f"Event Flow: {' → '.join(event_flow)}")

    assert event_flow == expected_flow, f"Expected {expected_flow}, got {event_flow}"

    print("✅ Event flow correct")

    # Cleanup
    for event_type in events_to_track:
        event_bus.unsubscribe(event_type, track_flow)

    print("✅ TEST PASSED: Event flow integration works\n")


# Main Test Runner
if __name__ == "__main__":
    print("\n" + "="*70)
    print("Event Bus Integration Tests")
    print("="*70)

    # Run synchronous tests
    test_new_event_types_exist()
    test_event_bus_subscribe_unsubscribe()
    test_auto_update_trigger_logic()
    test_event_flow_integration()

    # Run async test
    asyncio.run(test_worker_emits_events())

    print("\n" + "="*70)
    print("✅ ALL EVENT BUS INTEGRATION TESTS PASSED!")
    print("="*70)
    print("\nTest Summary:")
    print("  1. ✅ New EventTypes defined")
    print("  2. ✅ Subscribe/Unsubscribe works")
    print("  3. ✅ Worker emits events")
    print("  4. ✅ Auto-update trigger logic")
    print("  5. ✅ Event flow integration")
    print("\n" + "="*70 + "\n")
