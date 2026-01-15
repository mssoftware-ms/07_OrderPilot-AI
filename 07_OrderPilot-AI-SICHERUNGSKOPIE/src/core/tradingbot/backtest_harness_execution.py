"""Backtest Harness Execution - Order Execution and Position Management.

Refactored from backtest_harness.py.

Contains:
- execute_entry: Simulate entry fill and create position
- close_position: Simulate exit fill and record trade
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .backtest_types import BacktestTrade
from .models import FeatureVector, PositionState, Signal, TradeSide, TrailingState

if TYPE_CHECKING:
    from .backtest_harness import BacktestHarness

logger = logging.getLogger(__name__)


class BacktestHarnessExecution:
    """Helper for order execution and position management."""

    def __init__(self, parent: "BacktestHarness"):
        self.parent = parent

    def execute_entry(self, signal: Signal, features: FeatureVector) -> None:
        """Execute entry order.

        Args:
            signal: Entry signal
            features: Current features
        """
        bar = self.parent._state.current_bar

        # Calculate position size
        risk_pct = self.parent.bot_config.risk.risk_per_trade_pct
        stop_distance = abs(features.close - signal.stop_loss_price)
        risk_amount = self.parent._state.capital * (risk_pct / 100)
        quantity = risk_amount / stop_distance if stop_distance > 0 else 0

        if quantity <= 0:
            return

        # Simulate fill
        fill_price, slippage, commission = self.parent._simulator.simulate_fill(
            signal.side,
            quantity,
            features.close,
            bar["high"],
            bar["low"]
        )

        # Deduct commission
        self.parent._state.capital -= commission

        # Create position
        trailing = TrailingState(
            mode=self.parent.bot_config.bot.trailing_mode,
            current_stop_price=signal.stop_loss_price,
            initial_stop_price=signal.stop_loss_price,
            highest_price=fill_price,
            lowest_price=fill_price,
            trailing_distance=abs(fill_price - signal.stop_loss_price)
        )

        self.parent._state.position = PositionState(
            symbol=signal.symbol,
            side=signal.side,
            entry_price=fill_price,
            entry_time=self.parent._state.current_time,
            quantity=quantity,
            current_price=fill_price,
            trailing=trailing
        )

        self.parent._state.orders_executed += 1
        logger.debug(
            f"Entry: {signal.side.value} {quantity:.4f} @ {fill_price:.4f}, "
            f"stop={signal.stop_loss_price:.4f}"
        )

    def close_position(
        self,
        reason: str,
        exit_price: float | None = None
    ) -> None:
        """Close current position.

        Args:
            reason: Exit reason
            exit_price: Exit price (uses current close if None)
        """
        position = self.parent._state.position
        if not position:
            return

        bar = self.parent._state.current_bar
        if exit_price is None:
            exit_price = bar["close"]

        # Simulate exit fill
        exit_side = TradeSide.SHORT if position.side == TradeSide.LONG else TradeSide.LONG
        fill_price, slippage, commission = self.parent._simulator.simulate_fill(
            exit_side,
            position.quantity,
            exit_price,
            bar["high"],
            bar["low"]
        )

        # Calculate P&L
        if position.side == TradeSide.LONG:
            pnl = (fill_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - fill_price) * position.quantity

        pnl -= commission  # Deduct exit commission
        pnl_pct = pnl / (position.entry_price * position.quantity) * 100

        # Update capital
        self.parent._state.capital += pnl

        # Record trade
        trade = BacktestTrade(
            trade_id=self.parent._simulator.generate_order_id(),
            symbol=position.symbol,
            side=position.side,
            entry_time=position.entry_time,
            entry_price=position.entry_price,
            entry_size=position.quantity,
            exit_time=self.parent._state.current_time,
            exit_price=fill_price,
            exit_reason=reason,
            pnl=pnl,
            pnl_pct=pnl_pct,
            bars_held=position.bars_held,
            max_favorable_excursion=position.max_favorable_excursion,
            max_adverse_excursion=position.max_adverse_excursion,
            fees=commission * 2,  # Entry + exit
            slippage=slippage
        )
        self.parent._state.trades.append(trade)
        self.parent._state.position = None

        logger.debug(
            f"Exit: {reason}, PnL=${pnl:.2f} ({pnl_pct:.1f}%), "
            f"bars={trade.bars_held}"
        )
