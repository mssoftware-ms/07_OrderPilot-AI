"""Compiled Strategy Implementation.

This module contains the dynamically compiled strategy class that executes
trading strategies based on StrategyDefinition configurations.
"""

import logging
from typing import Any, Optional

import backtrader as bt

from .definition import StrategyDefinition
from .evaluation import ConditionEvaluator
from ..execution.events import CompilationError

logger = logging.getLogger(__name__)


class CompiledStrategy(bt.Strategy):
    """Dynamically compiled strategy from StrategyDefinition."""

    def __init__(self, definition: StrategyDefinition):
        """Initialize strategy with definition.

        Args:
            definition: Strategy definition containing rules and indicators
        """
        super().__init__()

        self.definition = definition
        self.__strategy_name__ = definition.name
        self.__strategy_version__ = definition.version

        # Initialize components
        self._setup_indicators()
        self._setup_evaluators()
        self._setup_risk_management()

        # Track orders and positions
        self.order = None
        self.entry_price = None

        logger.info(
            f"Strategy initialized: {definition.name} "
            f"(Indicators: {len(self.indicators_map)})"
        )

    def _setup_indicators(self):
        """Create and setup all indicators."""
        self.indicators_map = {}

        for ind_config in self.definition.indicators:
            try:
                # Import here to avoid circular dependency
                from .compiler import IndicatorFactory
                indicator = IndicatorFactory.create_indicator(
                    ind_config,
                    self.data
                )
                # Store with alias
                setattr(self, f"ind_{ind_config.alias}", indicator)
                self.indicators_map[ind_config.alias] = indicator

                logger.debug(
                    f"Created indicator: {ind_config.alias} = "
                    f"{ind_config.type}({ind_config.params})"
                )
            except Exception as e:
                raise CompilationError(
                    f"Failed to create indicator {ind_config.alias}: {e}"
                ) from e

    def _setup_evaluators(self):
        """Setup condition evaluators for entry/exit signals."""
        self.entry_long_evaluator = ConditionEvaluator(self)
        self.exit_long_evaluator = ConditionEvaluator(self)

        # Optional short evaluators
        self.entry_short_evaluator = (
            ConditionEvaluator(self) if self.definition.entry_short else None
        )
        self.exit_short_evaluator = (
            ConditionEvaluator(self) if self.definition.exit_short else None
        )

    def _setup_risk_management(self):
        """Setup risk management configuration."""
        self.risk_mgmt = self.definition.risk_management

    def next(self):
        """Execute strategy logic on each bar."""
        # Skip if order pending
        if self.order:
            return

        if not self.position:
            self._check_entry_signals()
        else:
            self._check_exit_signals()

    def _check_entry_signals(self):
        """Check for entry signals when no position exists."""
        # Check LONG entry
        if self.entry_long_evaluator.evaluate(self.definition.entry_long):
            self._enter_long()

        # Check SHORT entry (if defined) - CRITICAL: Use elif to prevent both signals
        elif (self.definition.entry_short and
              self.entry_short_evaluator and
              self.entry_short_evaluator.evaluate(self.definition.entry_short)):
            self._enter_short()

    def _check_exit_signals(self):
        """Check for exit signals when position exists."""
        if self.position.size > 0:
            # Long position: check exit
            if self.exit_long_evaluator.evaluate(self.definition.exit_long):
                self._exit_position("LONG EXIT SIGNAL")
            else:
                self._check_risk_management()

        elif self.position.size < 0:
            # Short position: check exit
            if (self.definition.exit_short and
                self.exit_short_evaluator and
                self.exit_short_evaluator.evaluate(self.definition.exit_short)):
                self._exit_position("SHORT EXIT SIGNAL")
            else:
                self._check_risk_management()

    def _enter_long(self):
        """Enter long position."""
        logger.info(f"LONG ENTRY @ {self.data.close[0]:.2f}")
        self.order = self.buy()
        self.entry_price = self.data.close[0]

    def _enter_short(self):
        """Enter short position."""
        logger.info(f"SHORT ENTRY @ {self.data.close[0]:.2f}")
        self.order = self.sell()
        self.entry_price = self.data.close[0]

    def _exit_position(self, reason: str = "EXIT"):
        """Exit current position."""
        logger.info(
            f"{reason} @ {self.data.close[0]:.2f} "
            f"(P&L: {self.position.size * (self.data.close[0] - self.entry_price):.2f})"
        )
        self.order = self.close()
        self.entry_price = None

    def _check_risk_management(self):
        """Check stop loss and take profit conditions."""
        if not self.entry_price:
            return

        current_price = self.data.close[0]

        # Calculate P&L percentage
        pnl_pct = self._calculate_pnl_percentage(current_price)

        # Check stop loss conditions
        if self._check_stop_loss(current_price, pnl_pct):
            return

        # Check take profit conditions
        self._check_take_profit(current_price, pnl_pct)

    def _calculate_pnl_percentage(self, current_price: float) -> float:
        """Calculate P&L percentage based on position direction."""
        if self.position.size > 0:  # Long
            return (current_price - self.entry_price) / self.entry_price * 100
        else:  # Short
            return (self.entry_price - current_price) / self.entry_price * 100

    def _check_stop_loss(self, current_price: float, pnl_pct: float) -> bool:
        """Check stop loss conditions. Returns True if position was closed."""
        # Percentage-based stop loss
        if self.risk_mgmt.stop_loss_pct:
            if pnl_pct <= -self.risk_mgmt.stop_loss_pct:
                self._exit_position(f"STOP LOSS ({pnl_pct:.2f}%)")
                return True

        # ATR-based stop loss
        if self.risk_mgmt.stop_loss_atr and hasattr(self, "ind_atr"):
            atr_value = self.ind_atr[0]
            stop_distance = self.risk_mgmt.stop_loss_atr * atr_value

            if self.position.size > 0:  # Long
                if current_price <= self.entry_price - stop_distance:
                    self._exit_position("STOP LOSS (ATR)")
                    return True
            else:  # Short
                if current_price >= self.entry_price + stop_distance:
                    self._exit_position("STOP LOSS (ATR)")
                    return True

        return False

    def _check_take_profit(self, current_price: float, pnl_pct: float):
        """Check take profit conditions."""
        # Percentage-based take profit
        if self.risk_mgmt.take_profit_pct:
            if pnl_pct >= self.risk_mgmt.take_profit_pct:
                self._exit_position(f"TAKE PROFIT ({pnl_pct:.2f}%)")
                return

        # ATR-based take profit
        if self.risk_mgmt.take_profit_atr and hasattr(self, "ind_atr"):
            atr_value = self.ind_atr[0]
            target_distance = self.risk_mgmt.take_profit_atr * atr_value

            if self.position.size > 0:  # Long
                if current_price >= self.entry_price + target_distance:
                    self._exit_position("TAKE PROFIT (ATR)")
            else:  # Short
                if current_price <= self.entry_price - target_distance:
                    self._exit_position("TAKE PROFIT (ATR)")

    def notify_order(self, order):
        """Handle order notifications."""
        if order.status in [order.Completed]:
            if order.isbuy():
                logger.debug(
                    f"BUY EXECUTED @ {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}"
                )
            elif order.issell():
                logger.debug(
                    f"SELL EXECUTED @ {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}"
                )

            self.order = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.warning(f"Order {order.status}")
            self.order = None