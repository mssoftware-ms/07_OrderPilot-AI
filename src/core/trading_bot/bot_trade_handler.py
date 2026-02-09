"""
Bot Trade Handler - Trade Execution and Position Management

Handles trade execution and position management:
- Execute trades (open position with risk calculation)
- Close positions (market orders + trade logging)
- Position monitor callbacks (exit, trailing, price updates)
- Manual position controls

Module 3/4 of bot_engine.py split (Lines 513-733, 979-986)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.broker.broker_types import OrderSide, OrderType
    from .position_monitor import ExitResult, MonitoredPosition
    from .signal_generator import TradeSignal
    from .trade_logger import ExitReason, TradeLogEntry
    from .bot_engine import TradingBotEngine

from .bot_types import BotState

logger = logging.getLogger(__name__)


class BotTradeHandler:
    """
    Verwaltet Trade-Ausführung und Position-Management.

    Wird von TradingBotEngine als Helper verwendet um Trades zu öffnen,
    zu schließen und Position-Updates zu verarbeiten.
    """

    def __init__(self, parent_engine: "TradingBotEngine"):
        """
        Args:
            parent_engine: Referenz zur TradingBotEngine
        """
        self.engine = parent_engine

    # =========================================================================
    # TRADE EXECUTION
    # =========================================================================

    async def execute_trade(
        self,
        signal: "TradeSignal",
        indicators: dict,
        market_context: dict,
    ) -> None:
        """
        Führt Trade aus (öffnet Position).

        Args:
            signal: Trade-Signal
            indicators: Indikator-Snapshot
            market_context: Markt-Kontext
        """
        self.engine._set_state(BotState.OPENING_POSITION)

        try:
            # Aktuellen Preis holen
            from src.core.broker.broker_types import OrderRequest, OrderSide, OrderType

            symbol = self.engine.config.symbol
            side = OrderSide.BUY if signal.is_long else OrderSide.SELL

            # Balance prüfen
            balance = await self.engine._get_balance()
            if balance <= 0:
                self.engine._log("No balance available")
                self.engine._set_state(BotState.WAITING_SIGNAL)
                return

            # Risk Calculation
            risk_calc = self.engine.risk_manager.calculate_position_size(
                signal=signal,
                balance=balance,
                atr=signal.details.get("atr"),
            )

            if not risk_calc.should_trade:
                self.engine._log(f"Risk check failed: {risk_calc.rejection_reason}")
                self.engine._set_state(BotState.WAITING_SIGNAL)
                return

            # Order erstellen
            order = OrderRequest(
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=risk_calc.quantity,
                leverage=self.engine.strategy_config.risk_config.leverage,
                stop_loss=risk_calc.stop_loss,
                take_profit=risk_calc.take_profit,
                notes=f"Bot trade: {signal.direction.value}",
            )

            # Order platzieren
            response = await self.engine.adapter.place_order(order)

            if response and response.status == "FILLED":
                # Trade Log erstellen
                entry_price = response.average_price or signal.price

                from .trade_logger import TradeLogEntry

                self.engine._current_trade_log = TradeLogEntry(
                    symbol=symbol,
                    direction=signal.direction.value,
                    entry_time=datetime.now(timezone.utc),
                    entry_price=entry_price,
                    quantity=risk_calc.quantity,
                    stop_loss=risk_calc.stop_loss,
                    take_profit=risk_calc.take_profit,
                    entry_order_id=response.broker_order_id,
                    entry_signal=signal.to_dict(),
                    entry_indicators=indicators,
                    market_context=market_context,
                )
                self.engine._current_trade_log.leverage = self.engine.strategy_config.risk_config.leverage

                # Position Monitor setzen
                atr = signal.details.get("atr")
                monitored_pos = self.engine.position_monitor.set_position(
                    symbol=symbol,
                    side=side.value,
                    entry_price=entry_price,
                    quantity=risk_calc.quantity,
                    stop_loss=risk_calc.stop_loss,
                    take_profit=risk_calc.take_profit,
                    trailing_atr=atr if self.engine.strategy_config.trailing_stop_enabled else None,
                    trade_log=self.engine._current_trade_log,
                )

                self.engine._set_state(BotState.IN_POSITION)
                self.engine._log(
                    f"Position opened: {side.value} {risk_calc.quantity} BTC @ {entry_price}"
                )
                self.engine._log(f"SL: {risk_calc.stop_loss}, TP: {risk_calc.take_profit}")

                if self.engine._on_position_opened:
                    self.engine._on_position_opened(monitored_pos)

            else:
                self.engine._log("Order failed")
                self.engine._set_state(BotState.WAITING_SIGNAL)

        except Exception as e:
            self.engine._log(f"Trade execution failed: {e}")
            logger.exception("Trade execution error")
            self.engine._set_state(BotState.WAITING_SIGNAL)

    # =========================================================================
    # POSITION CLOSING
    # =========================================================================

    async def close_position(self, exit_result: "ExitResult") -> None:
        """
        Schließt Position.

        Args:
            exit_result: Exit-Ergebnis mit Trigger und Preis
        """
        if not self.engine.position_monitor.has_position:
            return

        self.engine._set_state(BotState.CLOSING_POSITION)

        pos = self.engine.position_monitor.position
        exit_price = exit_result.trigger_price or pos.current_price

        try:
            # Gegen-Order erstellen
            from src.core.broker.broker_types import OrderRequest, OrderSide, OrderType

            close_side = OrderSide.SELL if pos.side == "BUY" else OrderSide.BUY

            order = OrderRequest(
                symbol=pos.symbol,
                side=close_side,
                order_type=OrderType.MARKET,
                quantity=pos.quantity,
                notes=f"Bot close: {exit_result.trigger.value}",
            )

            response = await self.engine.adapter.place_order(order)

            # Trade Log aktualisieren
            if self.engine._current_trade_log:
                from .trade_logger import ExitReason

                self.engine._current_trade_log.exit_time = datetime.now(timezone.utc)
                self.engine._current_trade_log.exit_price = exit_price
                self.engine._current_trade_log.exit_reason = ExitReason(exit_result.trigger.value)
                self.engine._current_trade_log.exit_order_id = (
                    response.broker_order_id if response else None
                )

                # Exit Indicators
                df = await self.engine.market_analyzer.fetch_market_data()
                if df is not None and not df.empty:
                    self.engine._current_trade_log.exit_indicators = (
                        self.engine.signal_generator.extract_indicator_snapshot(df)
                    )

                # Fees (geschätzt)
                fee_rate = Decimal("0.0006")  # 0.06% Taker
                self.engine._current_trade_log.fees_paid = (
                    pos.quantity * pos.entry_price * fee_rate * 2  # Entry + Exit
                )

                # Trade Log speichern
                self.engine.trade_logger.save_trade_log(self.engine._current_trade_log)

                # Statistics aktualisieren
                self.engine._update_statistics(self.engine._current_trade_log)

                if self.engine._on_position_closed:
                    self.engine._on_position_closed(self.engine._current_trade_log)

            # Position Monitor clearen
            self.engine.position_monitor.clear_position()
            self.engine._current_trade_log = None

            self.engine._log(
                f"Position closed: {exit_result.trigger.value} @ {exit_price}"
            )

            self.engine._set_state(BotState.WAITING_SIGNAL)

        except Exception as e:
            self.engine._log(f"Failed to close position: {e}")
            logger.exception("Position close error")
            self.engine._set_state(BotState.IN_POSITION)  # Bleibe in Position

    # =========================================================================
    # POSITION MONITOR CALLBACKS
    # =========================================================================

    async def on_exit_triggered(
        self, position: "MonitoredPosition", exit_result: "ExitResult"
    ) -> None:
        """Callback wenn Exit getriggert wird."""
        await self.close_position(exit_result)

    async def on_trailing_updated(
        self, position: "MonitoredPosition", old_sl: Decimal, new_sl: Decimal
    ) -> None:
        """Callback bei Trailing-Stop Update."""
        self.engine._log(f"Trailing stop updated: {old_sl} → {new_sl}")

    async def on_price_updated(self, position: "MonitoredPosition") -> None:
        """Callback bei Preis-Update."""
        # Kann für UI-Updates verwendet werden
        pass

    # =========================================================================
    # PRICE UPDATES
    # =========================================================================

    async def on_price_update(self, price: Decimal) -> None:
        """
        Wird von außen aufgerufen bei Preis-Updates (Streaming).

        Args:
            price: Aktueller Marktpreis
        """
        if self.engine._state == BotState.IN_POSITION:
            await self.engine.position_monitor.on_price_update(price)

    # =========================================================================
    # MANUAL CONTROLS
    # =========================================================================

    async def manual_close_position(self) -> None:
        """Schließt Position manuell."""
        if not self.engine.position_monitor.has_position:
            self.engine._log("No position to close")
            return

        exit_result = self.engine.position_monitor.trigger_manual_exit("Manual close by user")
        await self.close_position(exit_result)
