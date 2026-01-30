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
        # Validate entry conditions
        if not self._validate_entry_conditions():
            return

        # Execute trade
        try:
            await self._execute_trade(symbol, context)
        except Exception as e:
            logger.exception(f"Failed to execute trade: {e}")
            self.parent._log(f"❌ Trade execution error: {e}")

    def _validate_entry_conditions(self) -> bool:
        """Validate all entry conditions.

        Supports two modes:
        1. Standard mode: Requires trigger status = TRIGGERED
        2. JSON Entry mode: CEL expression result (LONG/SHORT) is the trigger

        Returns:
            True if all conditions met, False otherwise.
        """
        bot = self.parent.parent

        # Check if position already open
        if bot._current_position is not None:
            logger.debug("Position already open - skipping entry")
            return False

        # === JSON ENTRY MODE ===
        # In JSON Entry mode, the CEL expression result IS the trigger
        # If entry_score direction is LONG or SHORT, the CEL expression matched
        if self._is_json_entry_mode_active():
            # Check if CEL expression returned a valid direction (LONG/SHORT)
            if not bot._last_entry_score:
                logger.debug("JSON Entry: No entry score available")
                return False

            direction = bot._last_entry_score.direction.value
            if direction not in ["long", "short"]:
                logger.debug(f"JSON Entry: No entry signal (direction={direction})")
                return False

            logger.info(f"JSON Entry: CEL expression matched → {direction.upper()} signal")
            # Skip trigger check and quality check for JSON mode
            # The CEL expression already did all the filtering
            return True

        # === STANDARD MODE ===
        # Check if trigger active
        if not bot._last_trigger_result or bot._last_trigger_result.status.value != "triggered":
            logger.debug(
                f"No trigger - status: {bot._last_trigger_result.status.value if bot._last_trigger_result else 'None'}"
            )
            return False

        # Check entry score quality
        if not self._is_entry_score_acceptable():
            return False

        # Check LLM veto
        if self._has_llm_veto():
            return False

        return True

    def _is_json_entry_mode_active(self) -> bool:
        """Check if JSON Entry mode is active.

        Returns:
            True if JSON Entry mode is active, False otherwise.
        """
        # Check BotTabControl for JSON scorer
        control = getattr(self.parent, '_control', None)
        if control and hasattr(control, '_json_entry_scorer') and control._json_entry_scorer:
            return True
        return False

    def _is_entry_score_acceptable(self) -> bool:
        """Check if entry score meets minimum quality.

        Returns:
            True if acceptable, False otherwise.
        """
        bot = self.parent.parent
        if (
            not bot._last_entry_score
            or bot._last_entry_score.quality.value not in ["excellent", "good", "acceptable"]
        ):
            quality = bot._last_entry_score.quality.value if bot._last_entry_score else 'None'
            logger.warning(f"Entry score quality too low: {quality}")
            self.parent._log(f"⚠️ Entry Score zu niedrig: {quality}")
            return False
        return True

    def _has_llm_veto(self) -> bool:
        """Check if LLM vetoed the trade.

        Returns:
            True if veto, False otherwise.
        """
        bot = self.parent.parent
        if bot._last_llm_result and bot._last_llm_result.action.value == "veto":
            logger.warning(f"LLM VETO - blocking trade: {bot._last_llm_result.reasoning[:100]}")
            self.parent._log(f"🚫 LLM VETO: {bot._last_llm_result.reasoning[:50]}...")
            return True
        return False

    async def _execute_trade(self, symbol: str, context: "MarketContext") -> None:
        """Execute the trade after validation passed.

        Args:
            symbol: Trading symbol.
            context: Market context.
        """
        # Calculate trade parameters
        trade_params = await self._calculate_trade_parameters(symbol, context)
        if not trade_params:
            return

        # Place order
        order_result = await self._place_order(symbol, trade_params)

        # Handle order result
        if order_result and order_result.get("status") == "filled":
            self._handle_successful_order(symbol, context, trade_params)
        else:
            logger.error(f"Order failed: {order_result}")
            self.parent._log(f"❌ Order failed: {order_result}")

    async def _calculate_trade_parameters(
        self, symbol: str, context: "MarketContext"
    ) -> dict | None:
        """Calculate all trade parameters (size, SL, TP, etc.).

        Supports two modes:
        1. Standard mode: Uses exit levels from TriggerExitEngine
        2. JSON Entry mode: Uses ATR-based SL/TP calculation

        Returns:
            Dictionary with trade parameters or None if calculation failed.
        """
        bot = self.parent.parent
        direction = bot._last_entry_score.direction.value
        entry_price = context.current_price

        # Get leverage (default to 1.0 if not set)
        leverage = bot._last_leverage_result.final_leverage if bot._last_leverage_result else 1.0

        # Get risk settings
        config = self.parent._persistence_helper._get_current_config()
        risk_per_trade_pct = config.risk_per_trade_pct

        # Get account balance
        account_balance = await bot._adapter.get_balance()
        risk_amount = account_balance * (risk_per_trade_pct / 100.0)

        # === GET SL/TP LEVELS ===
        sl_price = None
        tp_price = None

        # Try standard mode: exit levels from TriggerExitEngine
        if bot._last_trigger_result and bot._last_trigger_result.exit_levels:
            exit_levels = bot._last_trigger_result.exit_levels
            sl_price = exit_levels.stop_loss
            tp_price = exit_levels.take_profit
            logger.debug(f"Using TriggerExitEngine SL/TP: SL={sl_price:.2f}, TP={tp_price:.2f}")

        # Fallback for JSON Entry mode: ATR-based SL/TP
        if sl_price is None or tp_price is None:
            # Use ATR from MarketContext features for SL/TP calculation
            atr = getattr(context.features, 'atr_14', None)
            if atr is None:
                atr = entry_price * 0.02  # Fallback: 2% of price as ATR
                logger.warning(f"No ATR available, using 2% fallback: {atr:.2f}")

            # SL = 2x ATR, TP = 3x ATR (1:1.5 Risk/Reward)
            sl_multiplier = 2.0
            tp_multiplier = 3.0

            if direction == "long":
                sl_price = entry_price - (atr * sl_multiplier)
                tp_price = entry_price + (atr * tp_multiplier)
            else:  # short
                sl_price = entry_price + (atr * sl_multiplier)
                tp_price = entry_price - (atr * tp_multiplier)

            logger.info(f"JSON Entry ATR-based SL/TP: SL={sl_price:.2f}, TP={tp_price:.2f} (ATR={atr:.2f})")
            self.parent._log(f"📊 ATR-based SL/TP: SL={sl_price:.2f} | TP={tp_price:.2f}")

        # Calculate SL distance
        if direction == "long":
            sl_distance_pct = abs((entry_price - sl_price) / entry_price)
        else:
            sl_distance_pct = abs((sl_price - entry_price) / entry_price)

        # Ensure SL distance is reasonable (min 0.5%, max 10%)
        sl_distance_pct = max(0.005, min(0.10, sl_distance_pct))

        # Calculate quantity
        quantity = (risk_amount / (entry_price * sl_distance_pct)) * leverage

        return {
            "direction": direction,
            "entry_price": entry_price,
            "quantity": quantity,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "leverage": leverage,
        }

    async def _place_order(self, symbol: str, trade_params: dict) -> dict:
        """Place market order.

        Args:
            symbol: Trading symbol.
            trade_params: Trade parameters dictionary.

        Returns:
            Order result dictionary.
        """
        direction = trade_params["direction"]
        quantity = trade_params["quantity"]
        entry_price = trade_params["entry_price"]
        sl_price = trade_params["sl_price"]
        tp_price = trade_params["tp_price"]
        leverage = trade_params["leverage"]

        self.parent._log(
            f"🚀 Opening {direction.upper()} position: {quantity:.4f} {symbol} @ {entry_price:.2f}"
        )
        self.parent._log(f"   SL: {sl_price:.2f} | TP: {tp_price:.2f} | Leverage: {leverage:.1f}x")

        return await self.parent.parent._adapter.place_order(
            symbol=symbol,
            side="buy" if direction == "long" else "sell",
            quantity=quantity,
            order_type="market",
        )

    def _handle_successful_order(
        self, symbol: str, context: "MarketContext", trade_params: dict
    ) -> None:
        """Handle successful order execution.

        Args:
            symbol: Trading symbol.
            context: Market context.
            trade_params: Trade parameters dictionary.
        """
        bot = self.parent.parent

        # Create position data
        trigger_type = (
            bot._last_trigger_result.trigger_type.value
            if bot._last_trigger_result.trigger_type
            else "unknown"
        )

        bot._current_position = {
            "symbol": symbol,
            "side": trade_params["direction"],
            "entry_price": trade_params["entry_price"],
            "quantity": trade_params["quantity"],
            "stop_loss": trade_params["sl_price"],
            "take_profit": trade_params["tp_price"],
            "leverage": trade_params["leverage"],
            "entry_time": datetime.now(timezone.utc),
            "context_id": context.context_id,
            "trigger_type": trigger_type,
        }

        # Update position attributes
        bot._position_entry_price = trade_params["entry_price"]
        bot._position_side = trade_params["direction"]
        bot._position_quantity = trade_params["quantity"]
        bot._position_stop_loss = trade_params["sl_price"]
        bot._position_take_profit = trade_params["tp_price"]

        # Log success
        self.parent._log(
            f"✅ Position opened: {trade_params['direction'].upper()} "
            f"{trade_params['quantity']:.4f} @ {trade_params['entry_price']:.2f}"
        )

        # Show SL/TP visual bar
        bot.sltp_container.setVisible(True)
        self.parent._ui_helper._update_sltp_bar(trade_params["entry_price"])

        # Add to journal
        self._add_trade_to_journal(context, trade_params, trigger_type)

    def _add_trade_to_journal(
        self, context: "MarketContext", trade_params: dict, trigger_type: str
    ) -> None:
        """Add trade to journal widget.

        Args:
            context: Market context.
            trade_params: Trade parameters dictionary.
            trigger_type: Trigger type string.
        """
        bot = self.parent.parent
        if not bot._journal_widget:
            return

        trade_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "context_id": context.context_id,
            "action": "ENTRY",
            "side": trade_params["direction"],
            "price": trade_params["entry_price"],
            "quantity": trade_params["quantity"],
            "stop_loss": trade_params["sl_price"],
            "take_profit": trade_params["tp_price"],
            "leverage": trade_params["leverage"],
            "trigger": trigger_type,
            "entry_score": bot._last_entry_score.final_score,
            "llm_action": bot._last_llm_result.action.value if bot._last_llm_result else "none",
        }
        bot._journal_widget.add_trade(trade_data)

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
