"""Bitunix Trading State Manager - Central State Management for Master/Mirror Pattern.

Provides single source of truth for trading state across multiple widgets:
- Mode (Paper/Live)
- Symbol
- Current Price
- Adapter Status
- Order Execution Guard (prevents duplicate orders)

Usage:
    state_manager = BitunixTradingStateManager()
    state_manager.register_widget(master_widget, is_master=True)
    state_manager.register_widget(mirror_widget, is_master=False)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional, Set
from weakref import WeakSet

from PyQt6.QtCore import QObject, pyqtSignal

if TYPE_CHECKING:
    from src.core.broker.bitunix_adapter import BitunixAdapter

logger = logging.getLogger(__name__)


class AdapterStatus(Enum):
    """Adapter connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class TradingMode(Enum):
    """Trading mode."""
    PAPER = "paper"
    LIVE = "live"


@dataclass
class TradingState:
    """Immutable snapshot of current trading state."""
    mode: TradingMode = TradingMode.PAPER
    symbol: str = "BTCUSDT"
    current_price: float = 0.0
    adapter_status: AdapterStatus = AdapterStatus.DISCONNECTED
    is_trading_enabled: bool = False

    def can_trade(self) -> bool:
        """Check if trading is allowed in current state."""
        return (
            self.adapter_status == AdapterStatus.CONNECTED
            and self.is_trading_enabled
            and self.current_price > 0
            and bool(self.symbol)
        )


class OrderExecutionGuard:
    """Prevents duplicate order execution across multiple widgets.

    Thread-safe guard that ensures each order is only executed once,
    even if multiple widgets attempt to place the same order simultaneously.
    """

    def __init__(self):
        self._pending_orders: Set[str] = set()
        self._lock = asyncio.Lock()
        self._order_history: dict[str, dict] = {}  # order_id -> metadata

    def generate_order_id(self) -> str:
        """Generate unique order ID for tracking."""
        return f"ord_{uuid.uuid4().hex[:12]}"

    async def try_acquire(self, order_id: str) -> bool:
        """Try to acquire lock for order execution.

        Args:
            order_id: Unique order identifier

        Returns:
            True if lock acquired, False if order already pending
        """
        async with self._lock:
            if order_id in self._pending_orders:
                logger.warning(f"Order {order_id} already pending - preventing duplicate")
                return False
            self._pending_orders.add(order_id)
            logger.debug(f"Order {order_id} acquired execution lock")
            return True

    async def release(self, order_id: str, success: bool = True, metadata: dict = None) -> None:
        """Release lock after order execution.

        Args:
            order_id: Unique order identifier
            success: Whether order was successfully executed
            metadata: Optional metadata to store in history
        """
        async with self._lock:
            self._pending_orders.discard(order_id)
            if metadata:
                self._order_history[order_id] = {
                    "success": success,
                    **metadata
                }
            logger.debug(f"Order {order_id} released (success={success})")

    def is_pending(self, order_id: str) -> bool:
        """Check if order is currently pending."""
        return order_id in self._pending_orders

    @property
    def pending_count(self) -> int:
        """Number of currently pending orders."""
        return len(self._pending_orders)


class BitunixTradingStateManager(QObject):
    """Central state manager for Bitunix trading widgets.

    Manages state synchronization between Master and Mirror widgets:
    - Master widget: Full functionality, owns state changes
    - Mirror widget: Synchronized view, delegates actions to master

    Signals:
        mode_changed: Emitted when trading mode changes (Paper/Live)
        symbol_changed: Emitted when trading symbol changes
        price_updated: Emitted when current price updates
        adapter_status_changed: Emitted when adapter connection status changes
        order_requested: Emitted when any widget requests an order
        order_completed: Emitted when order execution completes
        state_changed: Emitted for any state change (key, old_value, new_value)
        trading_enabled_changed: Emitted when trading enable/disable changes
    """

    # State change signals
    mode_changed = pyqtSignal(TradingMode)
    symbol_changed = pyqtSignal(str)
    price_updated = pyqtSignal(float)
    adapter_status_changed = pyqtSignal(AdapterStatus)
    trading_enabled_changed = pyqtSignal(bool)

    # Order signals
    order_requested = pyqtSignal(str, dict)  # order_id, order_params
    order_completed = pyqtSignal(str, bool, str)  # order_id, success, message

    # Generic state change signal
    state_changed = pyqtSignal(str, object, object)  # key, old_value, new_value

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        # Internal state
        self._state = TradingState()
        self._adapter: Optional["BitunixAdapter"] = None
        self._paper_adapter: Optional["BitunixAdapter"] = None
        self._live_adapter: Optional["BitunixAdapter"] = None

        # Order execution guard
        self._order_guard = OrderExecutionGuard()

        # Registered widgets (weak references to avoid circular refs)
        self._master_widgets: WeakSet = WeakSet()
        self._mirror_widgets: WeakSet = WeakSet()

        # Mode switch lock
        self._mode_switch_in_progress = False

        logger.info("BitunixTradingStateManager initialized")

    # ─────────────────────────────────────────────────────────────────────
    # Properties
    # ─────────────────────────────────────────────────────────────────────

    @property
    def state(self) -> TradingState:
        """Get current state snapshot."""
        return TradingState(
            mode=self._state.mode,
            symbol=self._state.symbol,
            current_price=self._state.current_price,
            adapter_status=self._state.adapter_status,
            is_trading_enabled=self._state.is_trading_enabled,
        )

    @property
    def mode(self) -> TradingMode:
        """Current trading mode."""
        return self._state.mode

    @property
    def is_paper_mode(self) -> bool:
        """Check if in paper trading mode."""
        return self._state.mode == TradingMode.PAPER

    @property
    def is_live_mode(self) -> bool:
        """Check if in live trading mode."""
        return self._state.mode == TradingMode.LIVE

    @property
    def symbol(self) -> str:
        """Current trading symbol."""
        return self._state.symbol

    @property
    def current_price(self) -> float:
        """Current market price."""
        return self._state.current_price

    @property
    def adapter(self) -> Optional["BitunixAdapter"]:
        """Active trading adapter (paper or live based on mode)."""
        return self._adapter

    @property
    def adapter_status(self) -> AdapterStatus:
        """Current adapter connection status."""
        return self._state.adapter_status

    @property
    def can_trade(self) -> bool:
        """Check if trading is currently allowed."""
        return self._state.can_trade()

    @property
    def order_guard(self) -> OrderExecutionGuard:
        """Access to order execution guard."""
        return self._order_guard

    # ─────────────────────────────────────────────────────────────────────
    # Widget Registration
    # ─────────────────────────────────────────────────────────────────────

    def register_widget(self, widget: Any, is_master: bool = False) -> None:
        """Register a trading widget with the state manager.

        Args:
            widget: Widget to register (must implement state sync interface)
            is_master: True if this is a master widget (can change state)
        """
        if is_master:
            self._master_widgets.add(widget)
            logger.info(f"Registered MASTER widget: {widget.__class__.__name__}")
        else:
            self._mirror_widgets.add(widget)
            logger.info(f"Registered MIRROR widget: {widget.__class__.__name__}")

        # Sync widget with current state
        self._sync_widget(widget)

    def unregister_widget(self, widget: Any) -> None:
        """Unregister a widget from state management."""
        self._master_widgets.discard(widget)
        self._mirror_widgets.discard(widget)
        logger.debug(f"Unregistered widget: {widget.__class__.__name__}")

    def _sync_widget(self, widget: Any) -> None:
        """Synchronize widget with current state."""
        if hasattr(widget, "sync_from_state"):
            widget.sync_from_state(self._state)
        else:
            # Fallback: call individual setters if available
            if hasattr(widget, "set_symbol"):
                widget.set_symbol(self._state.symbol)
            if hasattr(widget, "set_price"):
                widget.set_price(self._state.current_price)
            if hasattr(widget, "set_adapter"):
                widget.set_adapter(self._adapter)

    # ─────────────────────────────────────────────────────────────────────
    # State Setters
    # ─────────────────────────────────────────────────────────────────────

    def set_adapters(
        self,
        paper_adapter: "BitunixAdapter",
        live_adapter: "BitunixAdapter"
    ) -> None:
        """Set both paper and live adapters.

        Args:
            paper_adapter: Adapter for paper trading
            live_adapter: Adapter for live trading
        """
        self._paper_adapter = paper_adapter
        self._live_adapter = live_adapter

        # Set active adapter based on current mode
        self._adapter = paper_adapter if self.is_paper_mode else live_adapter

        logger.info("Trading adapters configured")

    def set_mode(self, mode: TradingMode) -> None:
        """Set trading mode (Paper/Live).

        Args:
            mode: New trading mode
        """
        if self._mode_switch_in_progress:
            logger.warning("Mode switch already in progress - ignoring")
            return

        if mode == self._state.mode:
            return

        old_mode = self._state.mode
        self._mode_switch_in_progress = True

        try:
            # Update state
            self._state.mode = mode

            # Switch adapter
            if mode == TradingMode.PAPER:
                self._adapter = self._paper_adapter
            else:
                self._adapter = self._live_adapter

            # Emit signals
            self._emit_state_change("mode", old_mode, mode)
            self.mode_changed.emit(mode)

            logger.info(f"Trading mode changed: {old_mode.value} -> {mode.value}")

        finally:
            self._mode_switch_in_progress = False

    def set_symbol(self, symbol: str) -> None:
        """Set trading symbol.

        Args:
            symbol: New trading symbol (e.g., "BTCUSDT")
        """
        if not symbol or symbol == self._state.symbol:
            return

        old_symbol = self._state.symbol
        self._state.symbol = symbol

        self._emit_state_change("symbol", old_symbol, symbol)
        self.symbol_changed.emit(symbol)

        logger.debug(f"Symbol changed: {old_symbol} -> {symbol}")

    def set_price(self, price: float) -> None:
        """Update current market price.

        Args:
            price: New market price
        """
        if price <= 0:
            return

        old_price = self._state.current_price
        self._state.current_price = price

        # Only emit if significant change (avoid spam)
        if abs(price - old_price) > 0.00001:
            self.price_updated.emit(price)

    def set_adapter_status(self, status: AdapterStatus) -> None:
        """Update adapter connection status.

        Args:
            status: New connection status
        """
        if status == self._state.adapter_status:
            return

        old_status = self._state.adapter_status
        self._state.adapter_status = status

        self._emit_state_change("adapter_status", old_status, status)
        self.adapter_status_changed.emit(status)

        logger.info(f"Adapter status: {old_status.value} -> {status.value}")

    def set_trading_enabled(self, enabled: bool) -> None:
        """Enable or disable trading.

        Args:
            enabled: Whether trading should be enabled
        """
        if enabled == self._state.is_trading_enabled:
            return

        old_enabled = self._state.is_trading_enabled
        self._state.is_trading_enabled = enabled

        self._emit_state_change("is_trading_enabled", old_enabled, enabled)
        self.trading_enabled_changed.emit(enabled)

        logger.info(f"Trading {'enabled' if enabled else 'disabled'}")

    def _emit_state_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """Emit generic state change signal."""
        self.state_changed.emit(key, old_value, new_value)

    # ─────────────────────────────────────────────────────────────────────
    # Order Execution
    # ─────────────────────────────────────────────────────────────────────

    async def request_order(
        self,
        order_params: dict,
        source_widget: Any = None
    ) -> tuple[bool, str]:
        """Request order execution through the state manager.

        This method ensures orders are only executed once, even if
        multiple widgets attempt to place the same order.

        Args:
            order_params: Order parameters (side, quantity, price, etc.)
            source_widget: Widget that initiated the order

        Returns:
            Tuple of (success, message)
        """
        if not self.can_trade:
            return False, "Trading not available (check connection and mode)"

        # Generate unique order ID
        order_id = self._order_guard.generate_order_id()

        # Try to acquire execution lock
        if not await self._order_guard.try_acquire(order_id):
            return False, "Order already being processed"

        try:
            # Emit order requested signal
            self.order_requested.emit(order_id, order_params)

            # Execute order via adapter
            if self._adapter is None:
                raise ValueError("No adapter available")

            result = await self._execute_order(order_id, order_params)

            # Emit completion signal
            self.order_completed.emit(order_id, result[0], result[1])

            return result

        except Exception as e:
            error_msg = f"Order execution failed: {e}"
            logger.error(error_msg, exc_info=True)
            self.order_completed.emit(order_id, False, error_msg)
            return False, error_msg

        finally:
            await self._order_guard.release(
                order_id,
                success=True,
                metadata={"params": order_params}
            )

    async def _execute_order(
        self,
        order_id: str,
        order_params: dict
    ) -> tuple[bool, str]:
        """Execute order through adapter.

        Args:
            order_id: Unique order identifier
            order_params: Order parameters

        Returns:
            Tuple of (success, message)
        """
        from src.core.broker.broker_types import OrderRequest, OrderSide
        from src.database.models import OrderType

        # Build OrderRequest from params
        order_request = OrderRequest(
            symbol=order_params.get("symbol", self._state.symbol),
            side=OrderSide[order_params.get("side", "BUY")],
            quantity=order_params.get("quantity", 0.0),
            order_type=OrderType[order_params.get("order_type", "MARKET")],
            limit_price=order_params.get("limit_price"),
            leverage=order_params.get("leverage", 1),
            take_profit_percent=order_params.get("take_profit_percent"),
            stop_loss_percent=order_params.get("stop_loss_percent"),
        )

        logger.info(f"Executing order {order_id}: {order_request}")

        # Place order via adapter
        result = await self._adapter.place_order(order_request)

        if result and result.success:
            return True, f"Order placed: {result.order_id}"
        else:
            error = result.error if result else "Unknown error"
            return False, f"Order failed: {error}"

    # ─────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────────

    def get_all_widgets(self) -> list:
        """Get all registered widgets (masters + mirrors)."""
        return list(self._master_widgets) + list(self._mirror_widgets)

    def sync_all_widgets(self) -> None:
        """Force sync all registered widgets with current state."""
        for widget in self.get_all_widgets():
            self._sync_widget(widget)

    def reset(self) -> None:
        """Reset state manager to initial state."""
        self._state = TradingState()
        self._order_guard = OrderExecutionGuard()
        self.sync_all_widgets()
        logger.info("State manager reset")
