"""
State Processing Mixin for BotController (REFACTORED).

REFACTORED: Split into focused helper modules using composition pattern.

Provides state machine processing methods:
- _process_state: Main state dispatcher
- _process_flat: Entry signal detection
- _process_signal: Signal confirmation
- _process_manage: Position management
- _handle_stop_hit: Stop-loss handling
- _handle_exit_signal: Exit signal handling
- _check_exit_signals: Exit condition checking
- _check_strategy_selection: Daily strategy selection
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

# Import helper modules
from .bot_state_handlers_dispatcher import BotStateHandlersDispatcher
from .bot_state_handlers_exit import BotStateHandlersExit
from .bot_state_handlers_flat import BotStateHandlersFlat
from .bot_state_handlers_manage import BotStateHandlersManage
from .bot_state_handlers_signal import BotStateHandlersSignal
from .models import FeatureVector

if TYPE_CHECKING:
    from .models import BotDecision


class BotStateHandlersMixin:
    """Mixin providing state processing methods (REFACTORED).

    Expected attributes from BotController:
        config: FullBotConfig
        symbol: str
        _running: bool
        _state_machine: BotStateMachine
        _regime: RegimeState
        _active_strategy: StrategyProfile | None
        _current_signal: Signal | None
        _position: PositionState | None
        _trades_today: int
        _daily_pnl: float
        _consecutive_losses: int
        _bar_count: int
        _trading_blocked: bool
        _last_block_reasons: list[str]
        _last_strategy_selection_date: datetime | None
        _strategy_selector: StrategySelector
        _strategy_catalog: StrategyCatalog
        _log_activity: Callable[[str, str], None]
        _on_signal: Callable[[Signal], None] | None
        _on_order: Callable[[OrderIntent], None] | None
        _on_trading_blocked: Callable[[list[str]], None] | None
        _on_macd_signal: Callable[[str, float], None] | None
        can_trade: property
    """

    def __init_state_handlers__(self):
        """Initialize state handler helpers (composition pattern).

        Call this from BotController.__init__ after all attributes are set.
        """
        # Create helpers (composition pattern)
        self._dispatcher = BotStateHandlersDispatcher(self)
        self._flat = BotStateHandlersFlat(self)
        self._signal = BotStateHandlersSignal(self)
        self._manage = BotStateHandlersManage(self)
        self._exit = BotStateHandlersExit(self)

    async def _process_state(
        self, features: FeatureVector, bar: dict[str, Any]
    ) -> BotDecision | None:
        """Process current state and generate decision (delegiert).

        Args:
            features: Current feature vector
            bar: Current bar data

        Returns:
            BotDecision or None
        """
        return await self._dispatcher.process_state(features, bar)

    async def _check_strategy_selection(self, features: FeatureVector) -> None:
        """Check if strategy selection is needed (daily or forced) (delegiert).

        Args:
            features: Current feature vector
        """
        return await self._flat.check_strategy_selection(features)
