from __future__ import annotations

import logging
from datetime import datetime


logger = logging.getLogger(__name__)

class BotCallbacksCandleMixin:
    """BotCallbacksCandleMixin extracted from BotCallbacksMixin."""
    def _on_chart_candle_closed(
        self,
        prev_open: float,
        prev_high: float,
        prev_low: float,
        prev_close: float,
        new_open: float
    ) -> None:
        """Handle candle close event from chart - feed bar to bot.

        This is the main entry point for bot bar processing when using
        tick-based streaming (not event-bus MARKET_BAR).

        Args:
            prev_open: Open price of the completed candle
            prev_high: High price of the completed candle
            prev_low: Low price of the completed candle
            prev_close: Close price of the completed candle
            new_open: Open price of the new candle
        """
        import asyncio

        # First, call the TR% lock handler if it exists
        if hasattr(self, '_on_candle_closed'):
            try:
                self._on_candle_closed(prev_close, new_open)
            except Exception as e:
                logger.error(f"Error in TR% lock handler: {e}")

        # =============================================================
        # SIMPLE STOP CHECK - directly against UI signal_history values
        # =============================================================
        self._check_stops_on_candle_close(prev_high, prev_low, prev_close)

        # Feed the closed candle to the bot if running
        if not hasattr(self, '_bot_controller') or self._bot_controller is None:
            return

        if not self._bot_controller._running:
            return

        # Build bar data from signal parameters (already have OHLC from signal)
        try:
            # Get candle time from chart widget
            candle_time = 0
            candle_volume = 0
            if hasattr(self, 'chart_widget'):
                chart = self.chart_widget
                # The current time is for the NEW candle, so subtract 60 for previous
                candle_time = getattr(chart, '_current_candle_time', int(datetime.now().timestamp())) - 60
                candle_volume = getattr(chart, '_prev_candle_volume', 0)

            bar_data = {
                'timestamp': datetime.fromtimestamp(candle_time) if candle_time > 0 else datetime.now(),
                'time': candle_time,
                'open': float(prev_open),
                'high': float(prev_high),
                'low': float(prev_low),
                'close': float(prev_close),
                'volume': float(candle_volume),
            }

            logger.info(
                f"Feeding candle to bot: O:{bar_data['open']:.2f} H:{bar_data['high']:.2f} "
                f"L:{bar_data['low']:.2f} C:{bar_data['close']:.2f}"
            )
            # Use asyncio.ensure_future for qasync compatibility
            asyncio.ensure_future(self._bot_controller.on_bar(bar_data))

        except Exception as e:
            logger.error(f"Error feeding candle to bot: {e}")
    def _check_stops_on_candle_close(
        self,
        candle_high: float,
        candle_low: float,
        candle_close: float
    ) -> None:
        """Check if any stops were hit by this candle (refactored).

        SIMPLE LOGIC:
        - SHORT: if candle_high >= stop_price → SELL (price went above stop)
        - LONG: if candle_low <= stop_price → SELL (price went below stop)

        Checks both initial stop (Stop column) and trailing stop (TR Stop).

        Args:
            candle_high: High price of the closed candle
            candle_low: Low price of the closed candle
            candle_close: Close price of the closed candle
        """
        # Guard: Find active position
        active_signal = self._find_active_position()
        if not active_signal:
            return

        # Extract stop data
        side = active_signal.get("side", "").lower()
        stop_data = {
            'stop_price': active_signal.get("stop_price", 0),
            'tr_stop_price': active_signal.get("trailing_stop_price", 0),
            'tr_active': active_signal.get("tr_active", False)
        }

        # Log check
        self._log_stop_check(candle_high, candle_low, side, stop_data)

        # Guard: No stops set
        if stop_data['stop_price'] <= 0 and stop_data['tr_stop_price'] <= 0:
            self._add_ki_log_entry("DEBUG", "Kein Stop gesetzt!")
            return

        # Check stops based on side
        stop_hit, exit_reason = self._check_stops_for_side(
            side, candle_high, candle_low, stop_data
        )

        if stop_hit:
            self._execute_stop_exit(active_signal, exit_reason, candle_close)

    def _find_active_position(self) -> dict | None:
        """Find active position in signal history."""
        for sig in self._signal_history:
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                return sig
        return None

    def _log_stop_check(
        self,
        candle_high: float,
        candle_low: float,
        side: str,
        stop_data: dict
    ) -> None:
        """Log stop check details."""
        self._add_ki_log_entry(
            "STOP_CHECK",
            f"Kerze H={candle_high:.2f} L={candle_low:.2f} | "
            f"Side={side.upper()} | SL={stop_data['stop_price']:.2f} | "
            f"TR-Stop={stop_data['tr_stop_price']:.2f} (aktiv={stop_data['tr_active']})"
        )

    def _check_stops_for_side(
        self,
        side: str,
        candle_high: float,
        candle_low: float,
        stop_data: dict
    ) -> tuple[bool, str]:
        """Check stops based on position side.

        Returns:
            (stop_hit, exit_reason) tuple
        """
        if side == "short":
            return self._check_short_stops(candle_high, stop_data)
        elif side == "long":
            return self._check_long_stops(candle_low, stop_data)
        return False, ""

    def _check_short_stops(
        self,
        candle_high: float,
        stop_data: dict
    ) -> tuple[bool, str]:
        """Check stops for SHORT position (price went UP).

        Returns:
            (stop_hit, exit_reason) tuple
        """
        # Check initial SL first
        if stop_data['stop_price'] > 0 and candle_high >= stop_data['stop_price']:
            self._add_ki_log_entry(
                "STOP",
                f"🛑 SL getroffen! HIGH={candle_high:.2f} >= SL={stop_data['stop_price']:.2f}"
            )
            return True, "SL"

        # Check trailing stop (only if active)
        if (stop_data['tr_active'] and
            stop_data['tr_stop_price'] > 0 and
            candle_high >= stop_data['tr_stop_price']):
            self._add_ki_log_entry(
                "STOP",
                f"🛑 TR getroffen! HIGH={candle_high:.2f} >= TR-Stop={stop_data['tr_stop_price']:.2f}"
            )
            return True, "TR"

        return False, ""

    def _check_long_stops(
        self,
        candle_low: float,
        stop_data: dict
    ) -> tuple[bool, str]:
        """Check stops for LONG position (price went DOWN).

        Returns:
            (stop_hit, exit_reason) tuple
        """
        # Check initial SL first
        if stop_data['stop_price'] > 0 and candle_low <= stop_data['stop_price']:
            self._add_ki_log_entry(
                "STOP",
                f"🛑 SL getroffen! LOW={candle_low:.2f} <= SL={stop_data['stop_price']:.2f}"
            )
            return True, "SL"

        # Check trailing stop (only if active)
        if (stop_data['tr_active'] and
            stop_data['tr_stop_price'] > 0 and
            candle_low <= stop_data['tr_stop_price']):
            self._add_ki_log_entry(
                "STOP",
                f"🛑 TR getroffen! LOW={candle_low:.2f} <= TR-Stop={stop_data['tr_stop_price']:.2f}"
            )
            return True, "TR"

        return False, ""
    def _execute_stop_exit(self, signal: dict, exit_reason: str, exit_price: float) -> None:
        """Execute stop exit - close the position.

        Args:
            signal: The signal dict from signal_history
            exit_reason: "SL" or "TR"
            exit_price: Price at which to exit (candle close)
        """
        self._add_ki_log_entry("EXIT", f"Position wird geschlossen: {exit_reason} @ {exit_price:.2f}")

        # Update signal in history
        signal["status"] = exit_reason
        signal["is_open"] = False
        signal["exit_price"] = exit_price
        signal["exit_timestamp"] = int(datetime.now().timestamp())

        # Calculate final P&L
        entry_price = signal.get("price", 0)
        invested = signal.get("invested", 0)
        side = signal.get("side", "long").lower()

        if entry_price > 0:
            if side == "long":
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - exit_price) / entry_price) * 100

            pnl_currency = invested * (pnl_pct / 100) if invested > 0 else 0
            signal["pnl_percent"] = pnl_pct
            signal["pnl_currency"] = pnl_currency

            self._add_ki_log_entry(
                "EXIT",
                f"P&L: {pnl_pct:+.2f}% ({pnl_currency:+.2f} EUR)"
            )

        # Remove all position lines from chart
        if hasattr(self, 'chart_widget'):
            try:
                self.chart_widget.remove_stop_line("initial_stop")
                self.chart_widget.remove_stop_line("trailing_stop")
                self.chart_widget.remove_stop_line("entry_line")
                self._add_ki_log_entry("CHART", "Alle Linien entfernt (Position geschlossen)")
            except Exception as e:
                logger.error(f"Error removing lines: {e}")

        # Save and update UI
        self._save_signal_history()
        self._update_signals_table()
        self._update_bot_display()

        # Reset bot controller position and state machine for new trades
        if self._bot_controller:
            self._bot_controller._position = None
            self._bot_controller._current_signal = None
            # Reset state machine to FLAT so bot can look for new entries
            if hasattr(self._bot_controller, '_state_machine'):
                from src.core.tradingbot.state_machine import BotTrigger
                try:
                    self._bot_controller._state_machine.trigger(BotTrigger.RESET, force=True)
                    self._add_ki_log_entry("BOT", "State Machine zurückgesetzt -> FLAT (bereit für neue Signale)")
                except Exception as e:
                    logger.error(f"Failed to reset state machine: {e}")
