from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QTableWidgetItem

logger = logging.getLogger(__name__)

class BotCallbacksPositionLifecycleMixin:
    """Position lifecycle callbacks (enter, exit, adjust)"""

    def _on_bot_decision(self, decision: Any) -> None:
        """Handle bot decision callback.

        This method is called by the bot controller when a trading decision is made.
        It dispatches to appropriate handlers based on the action type.

        Args:
            decision: BotDecision object containing action, prices, and reasons
        """
        from src.core.trading_bot.bot_types import BotAction

        action = getattr(decision, 'action', None)
        if not action:
            logger.warning("Bot decision has no action")
            return

        logger.info(f"Bot decision: {action}")

        if action == BotAction.ENTER:
            self._handle_bot_enter(decision)
        elif action == BotAction.ADJUST_STOP:
            self._handle_bot_adjust_stop(decision)
        elif action == BotAction.EXIT:
            self._handle_bot_exit(decision)
        elif action == BotAction.HOLD:
            # No action needed for HOLD
            pass
        else:
            logger.warning(f"Unknown bot action: {action}")

    def _handle_bot_enter(self, decision: Any) -> None:
        """Handle BotAction.ENTER."""
        stop_price = getattr(decision, 'stop_price_after', None)
        self._add_ki_log_entry("DEBUG", f"ENTER: stop_price_after={stop_price}")
        if not stop_price:
            self._add_ki_log_entry("ERROR", "stop_price_after ist None - keine Stop-Line!")
            return

        # Prevent entering if an open position already exists
        if self._has_open_signal():
            self._add_ki_log_entry("WARN", "ENTER ignoriert – bereits offene Position. Erst nach Exit/SL neue Trades.")
            logger.warning("ENTER ignored: open position exists")
            return

        initial_sl_pct = self.initial_sl_spin.value() if hasattr(self, 'initial_sl_spin') else 0.0
        sl_label = f"SL @ {stop_price:.2f} ({initial_sl_pct:.2f}%)" if initial_sl_pct > 0 else f"SL @ {stop_price:.2f}"

        self.chart_widget.add_stop_line(
            "initial_stop",
            stop_price,
            line_type="initial",
            color="#ef5350",
            label=sl_label
        )
        self._add_ki_log_entry("STOP", f"Initial Stop-Line gezeichnet @ {stop_price:.2f} ({initial_sl_pct:.2f}%)")

        active_sig = self._find_active_signal()
        if active_sig:
            active_sig["stop_price"] = stop_price
            active_sig["initial_sl_pct"] = initial_sl_pct
            self._save_signal_history()

    def _handle_bot_adjust_stop(self, decision: Any) -> None:
        """Handle BotAction.ADJUST_STOP."""
        new_stop = getattr(decision, 'stop_price_after', None)
        old_stop = getattr(decision, 'stop_price_before', None)
        if not new_stop:
            return

        if old_stop:
            change_pct = ((new_stop - old_stop) / old_stop) * 100
            self._add_ki_log_entry(
                "TRAILING",
                f"Stop angepasst: {old_stop:.2f} -> {new_stop:.2f} ({change_pct:+.2f}%)"
            )
        else:
            self._add_ki_log_entry("TRAILING", f"Trailing Stop aktiviert @ {new_stop:.2f}")

        trailing_pct = self.trailing_distance_spin.value() if hasattr(self, 'trailing_distance_spin') else 0.0
        tra_pct = self._calculate_tra_pct(new_stop)

        active_sig = self._find_active_signal()
        if not active_sig:
            return

        active_sig["stop_price"] = new_stop
        active_sig["trailing_stop_price"] = new_stop
        active_sig["trailing_stop_pct"] = trailing_pct

        if active_sig.get("tr_active", False):
            tr_label = f"TSL @ {new_stop:.2f} ({trailing_pct:.2f}% / TRA: {tra_pct:.2f}%)"
            self.chart_widget.add_stop_line(
                "trailing_stop",
                new_stop,
                line_type="trailing",
                color="#ff9800",
                label=tr_label
            )

        self._save_signal_history()

    def _handle_bot_exit(self, decision: Any) -> None:
        """Handle BotAction.EXIT."""
        reason_codes = getattr(decision, 'reason_codes', [])
        exit_status, is_trailing_stop_exit, is_rsi_exit = self._map_exit_status(reason_codes)

        if is_rsi_exit and self._should_block_rsi_exit(reason_codes):
            return

        if is_trailing_stop_exit and self._should_block_trailing_exit():
            return

        current_price = self._get_current_price()
        active_sig = self._find_active_signal()
        if active_sig:
            active_sig["status"] = exit_status
            active_sig["is_open"] = False
            active_sig["exit_timestamp"] = int(datetime.now().timestamp())
            if current_price > 0:
                active_sig["exit_price"] = current_price

            # Calculate P&L for WhatsApp notification
            entry_price = active_sig.get("price", 0)
            side = active_sig.get("side", "long")
            quantity = active_sig.get("quantity", 0)
            invested = active_sig.get("invested", 0)

            if entry_price > 0 and current_price > 0:
                # Calculate P&L percentage
                if side.lower() == "long":
                    pnl_percent = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_percent = ((entry_price - current_price) / entry_price) * 100

                # Calculate P&L in USDT (based on invested amount)
                pnl_usdt = invested * (pnl_percent / 100)

                # Update signal with P&L
                active_sig["pnl_percent"] = pnl_percent
                active_sig["pnl_currency"] = pnl_usdt

                # Send WhatsApp notification for position exit
                try:
                    # Use WhatsApp widget's working UI form mechanism
                    if hasattr(self, 'whatsapp_tab') and self.whatsapp_tab:
                        symbol = getattr(self, 'current_symbol', 'UNKNOWN')

                        # Map exit status to reason
                        reason_map = {
                            "SL": "STOP_LOSS",
                            "TR": "TAKE_PROFIT",
                            "MACD": "SELL",
                            "RSI": "SELL",
                            "Sell": "SELL",
                            "CLOSED": "SELL"
                        }
                        action = reason_map.get(exit_status, "SELL")

                        # Create TradeNotification and format message
                        notification = TradeNotification(
                            action=action,
                            symbol=symbol,
                            side=side,
                            quantity=quantity if quantity > 0 else invested / entry_price,
                            entry_price=entry_price,
                            exit_price=current_price,
                            pnl=pnl_usdt,
                            pnl_percent=pnl_percent,
                            timestamp=datetime.now()
                        )
                        message = notification.format_message()

                        # Send via WhatsApp widget (uses working UI form)
                        self.whatsapp_tab.send_trade_notification(message)
                        logger.info(f"WhatsApp notification sent: Position closed {exit_status} @ {current_price:.2f}, P&L: {pnl_usdt:.2f} USDT ({pnl_percent:.2f}%)")
                    else:
                        logger.warning("WhatsApp widget not available for notification")
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp notification: {e}")

            self._save_signal_history()
            self._add_ki_log_entry("EXIT", f"Position geschlossen: {exit_status} @ {current_price:.2f}")

        self._remove_position_lines()
        self._reset_state_machine()

        # Issue #31: Keep bot in RUNNING state after closing a trade
        if hasattr(self, "_set_bot_run_status_label"):
            self._set_bot_run_status_label(True)
        if hasattr(self, "_update_bot_status"):
            self._update_bot_status("RUNNING", "#26a69a")

    def _should_block_rsi_exit(self, reason_codes: list[str]) -> bool:
        if hasattr(self, 'disable_rsi_exit_cb') and self.disable_rsi_exit_cb.isChecked():
            current_price = self._get_current_price()
            if hasattr(self, 'chart_widget') and current_price > 0:
                is_overbought = "RSI_EXTREME_OVERBOUGHT" in reason_codes
                rsi_text = "RSI↓" if is_overbought else "RSI↑"

                # Get timestamp from bot controller's last features (candle time, not now())
                timestamp = int(datetime.now().timestamp())  # Fallback
                if self._bot_controller and self._bot_controller._last_features:
                    features_dt = self._bot_controller._last_features.timestamp
                    timestamp = self._get_chart_timestamp(features_dt)

                self.chart_widget.add_bot_marker(
                    timestamp=timestamp,
                    price=current_price,
                    marker_type=MarkerType.EXIT_SIGNAL,
                    side="rsi",
                    text=rsi_text
                )
            self._add_ki_log_entry(
                "BLOCK",
                f"RSI Exit BLOCKIERT (Checkbox aktiv) - Marker gezeichnet @ {current_price:.2f}"
            )
            return True
        return False

