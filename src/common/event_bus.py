"""Event Bus Implementation for OrderPilot-AI Trading Application.

This module provides a centralized event system using the blinker library
for decoupled communication between different components of the trading app.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from blinker import Namespace

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of all event types in the system."""
    # Application Events
    APP_START = "app_start"
    APP_STOP = "app_stop"
    APP_ERROR = "app_error"
    CONFIG_CHANGED = "config_changed"

    # UI Events
    UI_ACTION = "ui_action"

    # Market Data Events
    MARKET_TICK = "market_tick"
    MARKET_BAR = "market_bar"
    MARKET_DATA_FETCHED = "market_data_fetched"
    MARKET_CONNECTED = "market_connected"
    MARKET_DISCONNECTED = "market_disconnected"
    MARKET_DATA_CONNECTED = "market_data_connected"
    MARKET_DATA_DISCONNECTED = "market_data_disconnected"
    MARKET_DATA_TICK = "market_data_tick"

    # Indicator Events
    INDICATOR_CALCULATED = "indicator_calculated"

    # Order Events
    ORDER_CREATED = "order_created"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_FILLED = "order_filled"
    ORDER_PARTIAL_FILL = "order_partial_fill"
    ORDER_MODIFIED = "order_modified"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    ORDER_APPROVAL_REQUEST = "order_approval_request"

    # Position Events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_MODIFIED = "position_modified"

    # Execution Events (for chart markers)
    TRADE_ENTRY = "trade_entry"  # Entry point for trade
    TRADE_EXIT = "trade_exit"    # Exit point for trade
    STOP_LOSS_HIT = "stop_loss_hit"
    TAKE_PROFIT_HIT = "take_profit_hit"

    # Strategy Events
    STRATEGY_SIGNAL = "strategy_signal"
    STRATEGY_START = "strategy_start"
    STRATEGY_STOP = "strategy_stop"

    # Alert Events
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_CLEARED = "alert_cleared"

    # AI Events
    AI_ANALYSIS_REQUEST = "ai_analysis_request"
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"
    AI_ERROR = "ai_error"
    AI_COST_UPDATE = "ai_cost_update"

    # Backtest Events
    BACKTEST_START = "backtest_start"
    BACKTEST_PROGRESS = "backtest_progress"
    BACKTEST_COMPLETE = "backtest_complete"


@dataclass
class Event:
    """Base event data structure."""
    type: EventType
    timestamp: datetime
    data: dict[str, Any]
    source: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class OrderEvent(Event):
    """Order-specific event with chart-relevant information."""
    symbol: str | None = None
    order_id: str | None = None
    order_type: str | None = None  # market, limit, stop, etc.
    side: str | None = None  # buy, sell, long, short
    quantity: float | None = None
    price: float | None = None
    filled_quantity: float | None = None
    avg_fill_price: float | None = None
    status: str | None = None  # pending, submitted, filled, cancelled, rejected

    def __post_init__(self):
        """Ensure data dict contains chart-relevant info."""
        if self.data is None:
            self.data = {}
        # Sync fields to data dict for compatibility
        for field in ['symbol', 'order_id', 'order_type', 'side', 'quantity',
                      'price', 'filled_quantity', 'avg_fill_price', 'status']:
            value = getattr(self, field, None)
            if value is not None:
                self.data[field] = value


@dataclass
class ExecutionEvent(Event):
    """Execution event for chart markers (entry/exit points)."""
    symbol: str | None = None
    trade_id: str | None = None
    action: str | None = None  # entry, exit, stop_loss, take_profit
    side: str | None = None  # long, short
    quantity: float | None = None
    price: float | None = None
    pnl: float | None = None  # For exits
    pnl_pct: float | None = None  # For exits
    reason: str | None = None  # exit_signal, stop_loss, take_profit, etc.

    def __post_init__(self):
        """Ensure data dict contains chart-relevant info."""
        if self.data is None:
            self.data = {}
        # Sync fields to data dict
        for field in ['symbol', 'trade_id', 'action', 'side', 'quantity',
                      'price', 'pnl', 'pnl_pct', 'reason']:
            value = getattr(self, field, None)
            if value is not None:
                self.data[field] = value


class EventBus:
    """Centralized event bus for the trading application."""

    def __init__(self):
        """Initialize the event bus with namespaced signals."""
        self._signals = Namespace()
        self._signal_cache = {}
        self._event_history = []
        self._max_history_size = 10000

    def get_signal(self, event_type: EventType):
        """Get or create a signal for the given event type."""
        if event_type not in self._signal_cache:
            self._signal_cache[event_type] = self._signals.signal(event_type.value)
        return self._signal_cache[event_type]

    def emit(self, event: Event) -> None:
        """Emit an event to all registered listeners.

        Args:
            event: The event to emit
        """
        try:
            signal = self.get_signal(event.type)
            signal.send(event)

            # Store in history (with size limit)
            self._event_history.append(event)
            if len(self._event_history) > self._max_history_size:
                self._event_history.pop(0)

            logger.debug(f"Event emitted: {event.type.value} from {event.source}")
        except Exception as e:
            logger.error(f"Error emitting event {event.type}: {e}")

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type.

        Args:
            event_type: The type of event to subscribe to
            handler: The callback function to handle the event
        """
        signal = self.get_signal(event_type)
        signal.connect(handler)
        logger.debug(f"Handler registered for {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The callback function to remove
        """
        signal = self.get_signal(event_type)
        signal.disconnect(handler)
        logger.debug(f"Handler unregistered for {event_type.value}")

    def get_history(self, event_type: EventType | None = None,
                    limit: int = 100) -> list[Event]:
        """Get event history, optionally filtered by type.

        Args:
            event_type: Optional filter for specific event type
            limit: Maximum number of events to return

        Returns:
            List of events matching the criteria
        """
        if event_type:
            filtered = [e for e in self._event_history if e.type == event_type]
            return filtered[-limit:]
        return self._event_history[-limit:]

    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()
        logger.info("Event history cleared")


# Global event bus instance
event_bus = EventBus()

# Convenience functions for backward compatibility
app_event = event_bus.get_signal(EventType.APP_START)
market_event = event_bus.get_signal(EventType.MARKET_TICK)
order_event = event_bus.get_signal(EventType.ORDER_CREATED)
