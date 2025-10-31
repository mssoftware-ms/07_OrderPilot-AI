"""Tests for Event Bus System."""

from datetime import datetime

from src.common.event_bus import Event, EventBus, EventType


class TestEventBus:
    """Test Event Bus functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.event_bus = EventBus()

    def test_event_creation(self):
        """Test event creation."""
        event = Event(
            type=EventType.APP_START,
            timestamp=datetime.utcnow(),
            data={'component': 'test'}
        )

        assert event.type == EventType.APP_START
        assert event.data['component'] == 'test'
        assert event.timestamp is not None

    def test_subscribe_and_emit(self):
        """Test subscribing and emitting events."""
        received_events = []

        def handler(event):
            received_events.append(event)

        # Subscribe to event
        self.event_bus.subscribe(EventType.ORDER_CREATED, handler)

        # Emit event
        test_event = Event(
            type=EventType.ORDER_CREATED,
            timestamp=datetime.utcnow(),
            data={'order_id': '123'}
        )
        self.event_bus.emit(test_event)

        # Check if received
        assert len(received_events) == 1
        assert received_events[0].data['order_id'] == '123'

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        received_events = []

        def handler(event):
            received_events.append(event)

        # Subscribe
        self.event_bus.subscribe(EventType.MARKET_TICK, handler)

        # Emit first event
        self.event_bus.emit(Event(
            type=EventType.MARKET_TICK,
            timestamp=datetime.utcnow(),
            data={'symbol': 'AAPL'}
        ))

        assert len(received_events) == 1

        # Unsubscribe
        self.event_bus.unsubscribe(EventType.MARKET_TICK, handler)

        # Emit second event
        self.event_bus.emit(Event(
            type=EventType.MARKET_TICK,
            timestamp=datetime.utcnow(),
            data={'symbol': 'GOOGL'}
        ))

        # Should still be 1
        assert len(received_events) == 1

    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        handler1_events = []
        handler2_events = []

        def handler1(event):
            handler1_events.append(event)

        def handler2(event):
            handler2_events.append(event)

        # Subscribe both handlers
        self.event_bus.subscribe(EventType.AI_ANALYSIS_REQUEST, handler1)
        self.event_bus.subscribe(EventType.AI_ANALYSIS_REQUEST, handler2)

        # Emit event
        self.event_bus.emit(Event(
            type=EventType.AI_ANALYSIS_REQUEST,
            timestamp=datetime.utcnow(),
            data={'request': 'analyze'}
        ))

        # Both should receive
        assert len(handler1_events) == 1
        assert len(handler2_events) == 1

    def test_event_filter(self):
        """Test event filtering."""
        strategy_events = []

        def strategy_handler(event):
            if event.source == 'strategy_engine':
                strategy_events.append(event)

        self.event_bus.subscribe(EventType.STRATEGY_SIGNAL, strategy_handler)

        # Emit from strategy engine
        self.event_bus.emit(Event(
            type=EventType.STRATEGY_SIGNAL,
            timestamp=datetime.utcnow(),
            data={'signal': 'buy'},
            source='strategy_engine'
        ))

        # Emit from other source
        self.event_bus.emit(Event(
            type=EventType.STRATEGY_SIGNAL,
            timestamp=datetime.utcnow(),
            data={'signal': 'sell'},
            source='other'
        ))

        # Only strategy_engine event should be in list
        assert len(strategy_events) == 1
        assert strategy_events[0].data['signal'] == 'buy'