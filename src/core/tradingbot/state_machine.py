"""Tradingbot State Machine.

Finite state machine for bot operation with defined states,
transitions, and guards.

States:
    FLAT     - No position, waiting for signal
    SIGNAL   - Signal detected, awaiting confirmation
    ENTERED  - Position entered, initial stop set
    MANAGE   - Active management (trailing stops)
    EXITED   - Position closed, ready for next trade
    PAUSED   - Bot paused (manual or automatic)
    ERROR    - Error state requiring intervention
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .models import BotDecision, PositionState, Signal

logger = logging.getLogger(__name__)


class BotState(str, Enum):
    """Bot operation states."""
    FLAT = "flat"           # No position
    SIGNAL = "signal"       # Signal detected
    ENTERED = "entered"     # Position entered
    MANAGE = "manage"       # Active management
    EXITED = "exited"       # Position closed
    PAUSED = "paused"       # Bot paused
    ERROR = "error"         # Error state


class BotTrigger(str, Enum):
    """State transition triggers."""
    # Market events
    CANDLE_CLOSE = "candle_close"
    TICK_UPDATE = "tick_update"

    # Signal events
    SIGNAL_CANDIDATE = "signal_candidate"
    SIGNAL_CONFIRMED = "signal_confirmed"
    SIGNAL_EXPIRED = "signal_expired"

    # Order events
    ORDER_FILLED = "order_filled"
    ORDER_REJECTED = "order_rejected"
    ORDER_CANCELLED = "order_cancelled"

    # Stop events
    STOP_HIT = "stop_hit"
    STOP_UPDATED = "stop_updated"

    # Exit events
    EXIT_SIGNAL = "exit_signal"
    MANUAL_EXIT = "manual_exit"
    TIME_STOP = "time_stop"

    # Control events
    MANUAL_PAUSE = "manual_pause"
    MANUAL_RESUME = "manual_resume"
    ERROR_OCCURRED = "error_occurred"
    ERROR_CLEARED = "error_cleared"
    RESET = "reset"

    # Strategy events
    REGIME_FLIP = "regime_flip"
    STRATEGY_SELECTED = "strategy_selected"


class StateTransition(BaseModel):
    """Record of a state transition."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    from_state: BotState
    to_state: BotState
    trigger: BotTrigger
    data: dict[str, Any] = Field(default_factory=dict)


class StateMachineError(Exception):
    """State machine operation error."""
    pass


class InvalidTransitionError(StateMachineError):
    """Invalid state transition attempted."""
    pass


class BotStateMachine:
    """Finite state machine for trading bot operation.

    Manages state transitions with guards and callbacks.
    Thread-safe design for async operation.
    """

    # Valid transitions: {from_state: {trigger: to_state}}
    TRANSITIONS: dict[BotState, dict[BotTrigger, BotState]] = {
        BotState.FLAT: {
            BotTrigger.SIGNAL_CANDIDATE: BotState.SIGNAL,
            BotTrigger.SIGNAL_CONFIRMED: BotState.ENTERED,  # Direct entry
            BotTrigger.MANUAL_PAUSE: BotState.PAUSED,
            BotTrigger.ERROR_OCCURRED: BotState.ERROR,
        },
        BotState.SIGNAL: {
            BotTrigger.SIGNAL_CONFIRMED: BotState.ENTERED,
            BotTrigger.SIGNAL_EXPIRED: BotState.FLAT,
            BotTrigger.CANDLE_CLOSE: BotState.SIGNAL,  # Stay in signal
            BotTrigger.MANUAL_PAUSE: BotState.PAUSED,
            BotTrigger.ERROR_OCCURRED: BotState.ERROR,
            BotTrigger.RESET: BotState.FLAT,
        },
        BotState.ENTERED: {
            BotTrigger.ORDER_FILLED: BotState.MANAGE,
            BotTrigger.ORDER_REJECTED: BotState.FLAT,
            BotTrigger.ORDER_CANCELLED: BotState.FLAT,
            BotTrigger.STOP_HIT: BotState.EXITED,
            BotTrigger.MANUAL_PAUSE: BotState.PAUSED,
            BotTrigger.ERROR_OCCURRED: BotState.ERROR,
        },
        BotState.MANAGE: {
            BotTrigger.CANDLE_CLOSE: BotState.MANAGE,  # Continue managing
            BotTrigger.TICK_UPDATE: BotState.MANAGE,
            BotTrigger.STOP_HIT: BotState.EXITED,
            BotTrigger.STOP_UPDATED: BotState.MANAGE,
            BotTrigger.EXIT_SIGNAL: BotState.EXITED,
            BotTrigger.MANUAL_EXIT: BotState.EXITED,
            BotTrigger.TIME_STOP: BotState.EXITED,
            BotTrigger.MANUAL_PAUSE: BotState.PAUSED,
            BotTrigger.ERROR_OCCURRED: BotState.ERROR,
        },
        BotState.EXITED: {
            BotTrigger.RESET: BotState.FLAT,
            BotTrigger.MANUAL_PAUSE: BotState.PAUSED,
            BotTrigger.CANDLE_CLOSE: BotState.FLAT,  # Auto-reset on next bar
        },
        BotState.PAUSED: {
            BotTrigger.MANUAL_RESUME: BotState.FLAT,
            BotTrigger.ERROR_OCCURRED: BotState.ERROR,
        },
        BotState.ERROR: {
            BotTrigger.ERROR_CLEARED: BotState.FLAT,
            BotTrigger.RESET: BotState.FLAT,
        },
    }

    def __init__(
        self,
        symbol: str,
        initial_state: BotState = BotState.FLAT,
        on_transition: Callable[[StateTransition], None] | None = None
    ):
        """Initialize state machine.

        Args:
            symbol: Trading symbol this machine manages
            initial_state: Starting state
            on_transition: Callback for state transitions
        """
        self.symbol = symbol
        self._state = initial_state
        self._on_transition = on_transition
        self._history: list[StateTransition] = []
        self._context: dict[str, Any] = {}

        logger.info(
            f"StateMachine initialized: symbol={symbol}, state={initial_state.value}"
        )

    @property
    def state(self) -> BotState:
        """Current state."""
        return self._state

    @property
    def history(self) -> list[StateTransition]:
        """Transition history."""
        return self._history.copy()

    @property
    def context(self) -> dict[str, Any]:
        """State context data."""
        return self._context.copy()

    def can_transition(self, trigger: BotTrigger) -> bool:
        """Check if transition is valid from current state.

        Args:
            trigger: Transition trigger

        Returns:
            True if transition is valid
        """
        return trigger in self.TRANSITIONS.get(self._state, {})

    def get_valid_triggers(self) -> list[BotTrigger]:
        """Get all valid triggers from current state.

        Returns:
            List of valid triggers
        """
        return list(self.TRANSITIONS.get(self._state, {}).keys())

    def trigger(
        self,
        trigger: BotTrigger,
        data: dict[str, Any] | None = None,
        force: bool = False
    ) -> BotState:
        """Execute a state transition.

        Args:
            trigger: Transition trigger
            data: Additional context data
            force: Force transition even if invalid (for error recovery)

        Returns:
            New state after transition

        Raises:
            InvalidTransitionError: If transition is invalid and not forced
        """
        data = data or {}

        if not force and not self.can_transition(trigger):
            raise InvalidTransitionError(
                f"Invalid transition: {self._state.value} + {trigger.value}"
            )

        # Get target state
        if force and not self.can_transition(trigger):
            # Force to FLAT or ERROR
            to_state = BotState.FLAT if trigger == BotTrigger.RESET else BotState.ERROR
            logger.warning(
                f"Forced transition: {self._state.value} -> {to_state.value}"
            )
        else:
            to_state = self.TRANSITIONS[self._state][trigger]

        # Record transition
        transition = StateTransition(
            from_state=self._state,
            to_state=to_state,
            trigger=trigger,
            data=data
        )
        self._history.append(transition)

        # Keep history bounded
        if len(self._history) > 1000:
            self._history = self._history[-500:]

        # Update state
        old_state = self._state
        self._state = to_state

        # Update context
        self._context.update(data)

        # Log transition
        logger.info(
            f"State transition: {old_state.value} -> {to_state.value} "
            f"(trigger={trigger.value}, symbol={self.symbol})"
        )

        # Callback
        if self._on_transition:
            try:
                self._on_transition(transition)
            except Exception as e:
                logger.error(f"Transition callback error: {e}")

        return to_state

    def reset(self, clear_history: bool = False) -> None:
        """Reset state machine to FLAT.

        Args:
            clear_history: Also clear transition history
        """
        self._state = BotState.FLAT
        self._context.clear()
        if clear_history:
            self._history.clear()
        logger.info(f"StateMachine reset: symbol={self.symbol}")

    def set_context(self, key: str, value: Any) -> None:
        """Set context value.

        Args:
            key: Context key
            value: Context value
        """
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value.

        Args:
            key: Context key
            default: Default value if not found

        Returns:
            Context value or default
        """
        return self._context.get(key, default)

    # ==================== State Queries ====================

    def is_flat(self) -> bool:
        """Check if no position."""
        return self._state == BotState.FLAT

    def is_in_trade(self) -> bool:
        """Check if in active trade."""
        return self._state in (BotState.ENTERED, BotState.MANAGE)

    def is_waiting_fill(self) -> bool:
        """Check if waiting for order fill."""
        return self._state == BotState.ENTERED

    def is_managing(self) -> bool:
        """Check if actively managing position."""
        return self._state == BotState.MANAGE

    def is_paused(self) -> bool:
        """Check if paused."""
        return self._state == BotState.PAUSED

    def is_error(self) -> bool:
        """Check if in error state."""
        return self._state == BotState.ERROR

    def can_enter_trade(self) -> bool:
        """Check if can enter new trade."""
        return self._state in (BotState.FLAT, BotState.SIGNAL)

    # ==================== Event Handlers ====================

    def on_candle_close(self, bar_data: dict[str, Any]) -> BotState:
        """Handle candle close event.

        Args:
            bar_data: Bar data dict

        Returns:
            New state
        """
        if self.can_transition(BotTrigger.CANDLE_CLOSE):
            return self.trigger(BotTrigger.CANDLE_CLOSE, bar_data)
        return self._state

    def on_signal(
        self,
        signal: "Signal",
        confirmed: bool = False
    ) -> BotState:
        """Handle signal event.

        Args:
            signal: Trading signal
            confirmed: Whether signal is confirmed

        Returns:
            New state
        """
        trigger = BotTrigger.SIGNAL_CONFIRMED if confirmed else BotTrigger.SIGNAL_CANDIDATE
        data = {"signal": signal.model_dump()}

        if self.can_transition(trigger):
            return self.trigger(trigger, data)
        return self._state

    def on_order_fill(
        self,
        fill_price: float,
        fill_qty: float,
        order_id: str
    ) -> BotState:
        """Handle order fill event.

        Args:
            fill_price: Fill price
            fill_qty: Filled quantity
            order_id: Order ID

        Returns:
            New state
        """
        data = {
            "fill_price": fill_price,
            "fill_qty": fill_qty,
            "order_id": order_id
        }
        if self.can_transition(BotTrigger.ORDER_FILLED):
            return self.trigger(BotTrigger.ORDER_FILLED, data)
        return self._state

    def on_stop_hit(self, exit_price: float) -> BotState:
        """Handle stop-loss hit event.

        Args:
            exit_price: Exit price

        Returns:
            New state
        """
        data = {"exit_price": exit_price, "exit_reason": "stop_hit"}
        if self.can_transition(BotTrigger.STOP_HIT):
            return self.trigger(BotTrigger.STOP_HIT, data)
        return self._state

    def on_exit_signal(self, reason: str) -> BotState:
        """Handle exit signal event.

        Args:
            reason: Exit reason

        Returns:
            New state
        """
        data = {"exit_reason": reason}
        if self.can_transition(BotTrigger.EXIT_SIGNAL):
            return self.trigger(BotTrigger.EXIT_SIGNAL, data)
        return self._state

    def pause(self, reason: str = "manual") -> BotState:
        """Pause the bot.

        Args:
            reason: Pause reason

        Returns:
            New state
        """
        data = {"pause_reason": reason}
        if self.can_transition(BotTrigger.MANUAL_PAUSE):
            return self.trigger(BotTrigger.MANUAL_PAUSE, data)
        return self._state

    def resume(self) -> BotState:
        """Resume the bot.

        Returns:
            New state
        """
        if self.can_transition(BotTrigger.MANUAL_RESUME):
            return self.trigger(BotTrigger.MANUAL_RESUME)
        return self._state

    def error(self, error_msg: str) -> BotState:
        """Transition to error state.

        Args:
            error_msg: Error message

        Returns:
            New state
        """
        data = {"error": error_msg}
        return self.trigger(BotTrigger.ERROR_OCCURRED, data, force=True)

    def clear_error(self) -> BotState:
        """Clear error and return to FLAT.

        Returns:
            New state
        """
        if self.can_transition(BotTrigger.ERROR_CLEARED):
            return self.trigger(BotTrigger.ERROR_CLEARED)
        return self._state

    # ==================== Serialization ====================

    def to_dict(self) -> dict[str, Any]:
        """Serialize state machine to dict.

        Returns:
            State machine as dict
        """
        return {
            "symbol": self.symbol,
            "state": self._state.value,
            "context": self._context,
            "history_length": len(self._history)
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        on_transition: Callable[[StateTransition], None] | None = None
    ) -> "BotStateMachine":
        """Deserialize state machine from dict.

        Args:
            data: Serialized data
            on_transition: Transition callback

        Returns:
            BotStateMachine instance
        """
        machine = cls(
            symbol=data["symbol"],
            initial_state=BotState(data["state"]),
            on_transition=on_transition
        )
        machine._context = data.get("context", {})
        return machine
