"""Demo script for order and execution events.

Demonstrates:
- Creating and emitting order events
- Creating and emitting execution events (trade entry/exit)
- Listening to events for chart markers
- Full order and trade lifecycles

Usage:
    python tools/demo_execution_events.py
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import EventType, event_bus
from src.core.execution import OrderEventEmitter, ExecutionEventEmitter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_order_events():
    """Demonstrate order event lifecycle."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: Order Event Lifecycle")
    logger.info("="*80)

    emitter = OrderEventEmitter(symbol="AAPL", source="demo")

    # Step 1: Order Created
    logger.info("\n[1/5] Creating order...")
    emitter.emit_order_created(
        order_id="demo_order_1",
        order_type="limit",
        side="buy",
        quantity=100.0,
        price=150.0
    )

    # Step 2: Order Submitted
    logger.info("[2/5] Submitting order...")
    emitter.emit_order_submitted(order_id="demo_order_1")

    # Step 3: Order Filled
    logger.info("[3/5] Order filled...")
    emitter.emit_order_filled(
        order_id="demo_order_1",
        filled_quantity=100.0,
        avg_fill_price=149.95
    )

    # Show event history
    logger.info("\n[4/5] Event History:")
    for event_type in [EventType.ORDER_CREATED, EventType.ORDER_SUBMITTED, EventType.ORDER_FILLED]:
        events = event_bus.get_history(event_type)
        if events:
            logger.info(f"  • {event_type.value}: {len(events)} event(s)")

    logger.info("\n[5/5] Order lifecycle complete ✓")


def demo_execution_events():
    """Demonstrate execution event lifecycle (trade entry/exit)."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: Execution Event Lifecycle")
    logger.info("="*80)

    emitter = ExecutionEventEmitter(symbol="TSLA", source="demo")

    # Step 1: Trade Entry
    logger.info("\n[1/3] Trade Entry (Long)")
    emitter.emit_trade_entry(
        trade_id="demo_trade_1",
        side="long",
        quantity=50.0,
        price=700.0
    )

    # Step 2: Trade Exit (Profitable)
    logger.info("\n[2/3] Trade Exit (Take Profit)")
    emitter.emit_take_profit_hit(
        trade_id="demo_trade_1",
        side="long",
        quantity=50.0,
        price=720.0,
        pnl=1000.0,
        pnl_pct=2.86
    )

    # Step 3: Another trade with Stop Loss
    logger.info("\n[3/3] Trade with Stop Loss")
    emitter.emit_trade_entry(
        trade_id="demo_trade_2",
        side="long",
        quantity=100.0,
        price=700.0
    )

    emitter.emit_stop_loss_hit(
        trade_id="demo_trade_2",
        side="long",
        quantity=100.0,
        price=686.0,
        pnl=-1400.0,
        pnl_pct=-2.0
    )

    # Show event history
    logger.info("\nExecution Event Summary:")
    entry_events = event_bus.get_history(EventType.TRADE_ENTRY)
    logger.info(f"  • Trade Entries: {len(entry_events)}")

    tp_events = event_bus.get_history(EventType.TAKE_PROFIT_HIT)
    logger.info(f"  • Take Profits: {len(tp_events)}")

    sl_events = event_bus.get_history(EventType.STOP_LOSS_HIT)
    logger.info(f"  • Stop Losses: {len(sl_events)}")


def demo_event_listener():
    """Demonstrate listening to events (for chart markers)."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: Event Listener (Chart Markers)")
    logger.info("="*80)

    # Create event handlers
    def on_trade_entry(event):
        """Handler for trade entry events."""
        logger.info(
            f"  📈 CHART MARKER: {event.symbol} Entry @ ${event.price:.2f} "
            f"({event.side.upper()}) - Qty: {event.quantity}"
        )

    def on_trade_exit(event):
        """Handler for trade exit events."""
        pnl_symbol = "📗" if event.pnl >= 0 else "📕"
        logger.info(
            f"  {pnl_symbol} CHART MARKER: {event.symbol} Exit @ ${event.price:.2f} "
            f"- P&L: ${event.pnl:+.2f} ({event.pnl_pct:+.2f}%) - Reason: {event.reason}"
        )

    def on_stop_loss(event):
        """Handler for stop loss events."""
        logger.info(
            f"  🛑 CHART MARKER: {event.symbol} STOP LOSS @ ${event.price:.2f} "
            f"- Loss: ${event.pnl:.2f}"
        )

    def on_take_profit(event):
        """Handler for take profit events."""
        logger.info(
            f"  🎯 CHART MARKER: {event.symbol} TAKE PROFIT @ ${event.price:.2f} "
            f"- Profit: ${event.pnl:.2f}"
        )

    # Subscribe to events
    logger.info("\n[1/3] Subscribing to events...")
    event_bus.subscribe(EventType.TRADE_ENTRY, on_trade_entry)
    event_bus.subscribe(EventType.TRADE_EXIT, on_trade_exit)
    event_bus.subscribe(EventType.STOP_LOSS_HIT, on_stop_loss)
    event_bus.subscribe(EventType.TAKE_PROFIT_HIT, on_take_profit)
    logger.info("  ✓ Subscribed to 4 event types")

    # Emit some events
    logger.info("\n[2/3] Emitting events (will trigger handlers)...")
    emitter = ExecutionEventEmitter(symbol="MSFT", source="demo")

    # Trade 1: Profitable
    emitter.emit_trade_entry(
        trade_id="demo_listen_1",
        side="long",
        quantity=75.0,
        price=300.0
    )

    emitter.emit_take_profit_hit(
        trade_id="demo_listen_1",
        side="long",
        quantity=75.0,
        price=315.0,
        pnl=1125.0,
        pnl_pct=5.0
    )

    # Trade 2: Stop Loss
    emitter.emit_trade_entry(
        trade_id="demo_listen_2",
        side="long",
        quantity=100.0,
        price=300.0
    )

    emitter.emit_stop_loss_hit(
        trade_id="demo_listen_2",
        side="long",
        quantity=100.0,
        price=294.0,
        pnl=-600.0,
        pnl_pct=-2.0
    )

    # Unsubscribe
    logger.info("\n[3/3] Unsubscribing from events...")
    event_bus.unsubscribe(EventType.TRADE_ENTRY, on_trade_entry)
    event_bus.unsubscribe(EventType.TRADE_EXIT, on_trade_exit)
    event_bus.unsubscribe(EventType.STOP_LOSS_HIT, on_stop_loss)
    event_bus.unsubscribe(EventType.TAKE_PROFIT_HIT, on_take_profit)
    logger.info("  ✓ Unsubscribed from all events")


def demo_event_history():
    """Demonstrate event history retrieval."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: Event History")
    logger.info("="*80)

    # Get all events
    logger.info("\n[1/2] Retrieving all events...")
    all_events = event_bus.get_history(limit=100)
    logger.info(f"  Total events in history: {len(all_events)}")

    # Group by type
    event_counts = {}
    for event in all_events:
        event_type = event.type.value
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    logger.info("\n[2/2] Events by type:")
    for event_type, count in sorted(event_counts.items()):
        logger.info(f"  • {event_type}: {count}")


def main():
    """Run all demos."""
    logger.info("="*80)
    logger.info("ORDER AND EXECUTION EVENTS DEMO")
    logger.info("="*80)

    try:
        # Clear history at start
        event_bus.clear_history()

        # Run demos
        demo_order_events()
        demo_execution_events()
        demo_event_listener()
        demo_event_history()

        logger.info("\n" + "="*80)
        logger.info("DEMO COMPLETE")
        logger.info("="*80)
        logger.info("\nKey Takeaways:")
        logger.info("  1. OrderEventEmitter tracks order lifecycle (create, submit, fill, cancel)")
        logger.info("  2. ExecutionEventEmitter tracks trade lifecycle (entry, exit, stop loss, take profit)")
        logger.info("  3. Subscribe to events to add real-time chart markers")
        logger.info("  4. Event history allows retrospective analysis")
        logger.info("  5. BacktraderEventAdapter integrates with Backtrader strategies")

        return 0

    except Exception as e:
        logger.exception(f"Demo failed: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Demo crashed: {e}")
        sys.exit(1)
