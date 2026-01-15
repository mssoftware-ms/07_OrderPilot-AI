"""Bot Tab Control Trade - Trade Execution and Position Monitoring.

Refactored from 1,160 LOC monolith using composition pattern.

Module 3/6 of bot_tab_control.py split.

Contains:
- _execute_trade_if_triggered(): Entry condition checks and trade execution
- _monitor_open_position(): Exit monitoring (SL/TP, trailing, exit signals)
- _close_position(): Position closing and P&L calculation
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.trading_bot import MarketContext

logger = logging.getLogger(__name__)


class BotTabControlTrade:
    """Helper für Trade Execution und Position Monitoring."""

    def __init__(self, parent):
        """
        Args:
            parent: BotTabControl Instanz
        """
        self.parent = parent

    async def _execute_trade_if_triggered(self, symbol: str, context: "MarketContext") -> None:
        """Führt Trade aus wenn alle Bedingungen erfüllt sind.

        Bedingungen für Entry:
        1. Kein offener Trade (self.parent.parent._current_position is None)
        2. Trigger-Status = TRIGGERED
        3. Entry Score Quality >= ACCEPTABLE
        4. LLM Validation != VETO

        Args:
            symbol: Trading-Symbol
            context: Aktueller MarketContext
        """
        # 1. Prüfen ob bereits Position offen
        if self.parent.parent._current_position is not None:
            logger.debug("Position already open - skipping entry")
            return

        # 2. Prüfen ob Trigger aktiv
        if not self.parent.parent._last_trigger_result or self.parent.parent._last_trigger_result.status.value != "triggered":
            logger.debug(
                f"No trigger - status: {self.parent.parent._last_trigger_result.status.value if self.parent.parent._last_trigger_result else 'None'}"
            )
            return

        # 3. Prüfen ob Entry Score gut genug
        if (
            not self.parent.parent._last_entry_score
            or self.parent.parent._last_entry_score.quality.value not in ["excellent", "good", "acceptable"]
        ):
            logger.warning(
                f"Entry score quality too low: {self.parent.parent._last_entry_score.quality.value if self.parent.parent._last_entry_score else 'None'}"
            )
            self.parent._log(
                f"⚠️ Entry Score zu niedrig: {self.parent.parent._last_entry_score.quality.value if self.parent.parent._last_entry_score else 'None'}"
            )
            return

        # 4. Prüfen ob LLM Veto
        if self.parent.parent._last_llm_result and self.parent.parent._last_llm_result.action.value == "veto":
            logger.warning(f"LLM VETO - blocking trade: {self.parent.parent._last_llm_result.reasoning[:100]}")
            self.parent._log(f"🚫 LLM VETO: {self.parent.parent._last_llm_result.reasoning[:50]}...")
            return

        # Alle Bedingungen erfüllt → Trade ausführen
        try:
            direction = self.parent.parent._last_entry_score.direction.value  # "long" or "short"
            entry_price = context.current_price

            # Position Size berechnen (mit Leverage)
            leverage = (
                self.parent.parent._last_leverage_result.final_leverage if self.parent.parent._last_leverage_result else 1.0
            )

            # Hole Risk-Settings aus Config
            config = self.parent._persistence_helper._get_current_config()
            risk_per_trade_pct = config.risk_per_trade_pct  # z.B. 1.0 = 1% des Kapitals

            # Hole Kontogröße vom Adapter
            account_balance = await self.parent.parent._adapter.get_balance()

            # Berechne Position Size
            risk_amount = account_balance * (risk_per_trade_pct / 100.0)

            # Stop Loss Distanz aus TriggerExitEngine
            exit_levels = self.parent.parent._last_trigger_result.exit_levels
            if not exit_levels:
                logger.error("No exit levels from TriggerExitEngine")
                return

            sl_price = exit_levels.stop_loss
            tp_price = exit_levels.take_profit

            # SL-Distanz in %
            if direction == "long":
                sl_distance_pct = abs((entry_price - sl_price) / entry_price)
            else:
                sl_distance_pct = abs((sl_price - entry_price) / entry_price)

            # Quantity berechnen: Risk / SL-Distanz
            quantity = (risk_amount / (entry_price * sl_distance_pct)) * leverage

            # Position öffnen über Adapter
            self.parent._log(f"🚀 Opening {direction.upper()} position: {quantity:.4f} {symbol} @ {entry_price:.2f}")
            self.parent._log(f"   SL: {sl_price:.2f} | TP: {tp_price:.2f} | Leverage: {leverage:.1f}x")

            order_result = await self.parent.parent._adapter.place_order(
                symbol=symbol,
                side="buy" if direction == "long" else "sell",
                quantity=quantity,
                order_type="market",
            )

            if order_result and order_result.get("status") == "filled":
                # Position erfolgreich eröffnet
                self.parent.parent._current_position = {
                    "symbol": symbol,
                    "side": direction,
                    "entry_price": entry_price,
                    "quantity": quantity,
                    "stop_loss": sl_price,
                    "take_profit": tp_price,
                    "leverage": leverage,
                    "entry_time": datetime.now(timezone.utc),
                    "context_id": context.context_id,
                    "trigger_type": (
                        self.parent.parent._last_trigger_result.trigger_type.value
                        if self.parent.parent._last_trigger_result.trigger_type
                        else "unknown"
                    ),
                }

                self.parent.parent._position_entry_price = entry_price
                self.parent.parent._position_side = direction
                self.parent.parent._position_quantity = quantity
                self.parent.parent._position_stop_loss = sl_price
                self.parent.parent._position_take_profit = tp_price

                self.parent._log(f"✅ Position opened: {direction.upper()} {quantity:.4f} @ {entry_price:.2f}")

                # Show SL/TP Visual Bar
                self.parent.parent.sltp_container.setVisible(True)
                self.parent._ui_helper._update_sltp_bar(entry_price)

                # Journal Log
                if self.parent.parent._journal_widget:
                    trade_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "context_id": context.context_id,
                        "action": "ENTRY",
                        "side": direction,
                        "price": entry_price,
                        "quantity": quantity,
                        "stop_loss": sl_price,
                        "take_profit": tp_price,
                        "leverage": leverage,
                        "trigger": (
                            self.parent.parent._last_trigger_result.trigger_type.value
                            if self.parent.parent._last_trigger_result.trigger_type
                            else "unknown"
                        ),
                        "entry_score": self.parent.parent._last_entry_score.final_score,
                        "llm_action": (
                            self.parent.parent._last_llm_result.action.value if self.parent.parent._last_llm_result else "none"
                        ),
                    }
                    self.parent.parent._journal_widget.add_trade(trade_data)

                # NOTE: WhatsApp Notification erfolgt über das ChartWindow Trading Bot Panel
            else:
                logger.error(f"Order failed: {order_result}")
                self.parent._log(f"❌ Order failed: {order_result}")

        except Exception as e:
            logger.exception(f"Failed to execute trade: {e}")
            self.parent._log(f"❌ Trade execution error: {e}")

    async def _monitor_open_position(self, context: "MarketContext") -> None:
        """Überwacht offene Position und managed Exit.

        Exit-Bedingungen:
        1. Stop Loss hit
        2. Take Profit hit
        3. Trailing Stop triggered
        4. Exit-Signal von TriggerExitEngine

        Args:
            context: Aktueller MarketContext
        """
        if not self.parent.parent._current_position:
            return  # Keine offene Position

        try:
            current_price = context.current_price
            side = self.parent.parent._current_position["side"]
            entry_price = self.parent.parent._current_position["entry_price"]

            # Prüfe SL/TP
            should_exit = False
            exit_reason = ""

            if side == "long":
                # Long Position
                if current_price <= self.parent.parent._position_stop_loss:
                    should_exit = True
                    exit_reason = "Stop Loss hit"
                elif current_price >= self.parent.parent._position_take_profit:
                    should_exit = True
                    exit_reason = "Take Profit hit"
            else:
                # Short Position
                if current_price >= self.parent.parent._position_stop_loss:
                    should_exit = True
                    exit_reason = "Stop Loss hit"
                elif current_price <= self.parent.parent._position_take_profit:
                    should_exit = True
                    exit_reason = "Take Profit hit"

            # Trailing Stop Update (falls aktiviert)
            if self.parent.parent._trigger_exit_engine and not should_exit:
                # Hole neue Exit-Levels (mit Trailing)
                exit_signal = self.parent.parent._trigger_exit_engine.check_exit(
                    context=context,
                    entry_price=entry_price,
                    side=side,
                )

                if exit_signal and exit_signal.exit_type.value == "trailing_stop":
                    # Trailing Stop wurde getriggert
                    should_exit = True
                    exit_reason = "Trailing Stop triggered"
                elif exit_signal and exit_signal.updated_levels:
                    # SL/TP Update (Trailing)
                    new_sl = exit_signal.updated_levels.stop_loss
                    new_tp = exit_signal.updated_levels.take_profit

                    if (
                        new_sl != self.parent.parent._position_stop_loss
                        or new_tp != self.parent.parent._position_take_profit
                    ):
                        logger.info(
                            f"Updating SL/TP: SL {self.parent.parent._position_stop_loss:.2f} → {new_sl:.2f}, TP {self.parent.parent._position_take_profit:.2f} → {new_tp:.2f}"
                        )
                        self.parent.parent._position_stop_loss = new_sl
                        self.parent.parent._position_take_profit = new_tp
                        self.parent.parent._current_position["stop_loss"] = new_sl
                        self.parent.parent._current_position["take_profit"] = new_tp
                        self.parent._log(f"📊 Trailing Update: SL={new_sl:.2f} TP={new_tp:.2f}")

            # Exit ausführen falls nötig
            if should_exit:
                await self._close_position(
                    exit_price=current_price,
                    exit_reason=exit_reason,
                    context_id=context.context_id,
                )
            else:
                # Update SL/TP Visual Bar
                self.parent._ui_helper._update_sltp_bar(current_price)

        except Exception as e:
            logger.exception(f"Failed to monitor position: {e}")
            self.parent._log(f"❌ Position monitoring error: {e}")

    async def _close_position(self, exit_price: float, exit_reason: str, context_id: str) -> None:
        """Schließt die offene Position.

        Args:
            exit_price: Exit-Preis
            exit_reason: Grund für Exit
            context_id: MarketContext ID
        """
        if not self.parent.parent._current_position:
            return

        try:
            symbol = self.parent.parent._current_position["symbol"]
            side = self.parent.parent._current_position["side"]
            quantity = self.parent.parent._current_position["quantity"]
            entry_price = self.parent.parent._current_position["entry_price"]

            # Order platzieren (gegenläufig)
            close_side = "sell" if side == "long" else "buy"

            self.parent._log(f"🔴 Closing {side.upper()} position: {quantity:.4f} {symbol} @ {exit_price:.2f}")
            self.parent._log(f"   Reason: {exit_reason}")

            order_result = await self.parent.parent._adapter.place_order(
                symbol=symbol,
                side=close_side,
                quantity=quantity,
                order_type="market",
            )

            if order_result and order_result.get("status") == "filled":
                # P&L berechnen
                if side == "long":
                    pnl = (exit_price - entry_price) * quantity
                else:
                    pnl = (entry_price - exit_price) * quantity

                pnl_pct = (pnl / (entry_price * quantity)) * 100

                self.parent._log(f"✅ Position closed: P&L = ${pnl:.2f} ({pnl_pct:+.2f}%)")

                # Journal Log
                if self.parent.parent._journal_widget:
                    trade_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "context_id": context_id,
                        "action": "EXIT",
                        "side": side,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "quantity": quantity,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "exit_reason": exit_reason,
                        "hold_time": str(datetime.now(timezone.utc) - self.parent.parent._current_position["entry_time"]),
                    }
                    self.parent.parent._journal_widget.add_trade(trade_data)

                # NOTE: WhatsApp Notification erfolgt über das ChartWindow Trading Bot Panel

                # Position löschen
                self.parent.parent._current_position = None
                self.parent.parent._position_entry_price = 0.0
                self.parent.parent._position_side = ""
                self.parent.parent._position_quantity = 0.0
                self.parent.parent._position_stop_loss = 0.0
                self.parent.parent._position_take_profit = 0.0

                # Reset SL/TP Visual Bar (bleibt sichtbar, zeigt nur "keine Position")
                self.parent._ui_helper._reset_sltp_bar()
            else:
                logger.error(f"Close order failed: {order_result}")
                self.parent._log(f"❌ Close order failed: {order_result}")

        except Exception as e:
            logger.exception(f"Failed to close position: {e}")
            self.parent._log(f"❌ Position close error: {e}")
