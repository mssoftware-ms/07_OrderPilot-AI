from __future__ import annotations

from datetime import datetime


class BotDisplayLoggingMixin:
    """BotDisplayLoggingMixin extracted from BotDisplayManagerMixin."""
    def _add_ki_log_entry(self, entry_type: str, message: str) -> None:
        """Add entry to KI log (uses local time)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{entry_type}] {message}"
        self.ki_log_text.appendPlainText(entry)
        self._ki_log_entries.append({
            "time": timestamp,
            "type": entry_type,
            "message": message
        })
        # Mirror into Trading Bot Log (Signals tab) if available (Issue #23)
        if hasattr(self, "_append_bot_log"):
            self._append_bot_log(entry_type, message, timestamp)
    def _log_bot_diagnostics(self) -> None:
        """Log periodic bot diagnostics for debugging."""
        if not self._bot_controller:
            return

        bc = self._bot_controller
        state = bc.state.value if hasattr(bc.state, 'value') else str(bc.state)
        can_trade = bc.can_trade
        reasons = []

        if hasattr(bc, '_state_machine'):
            if bc._state_machine.is_paused():
                reasons.append("PAUSED")
            if bc._state_machine.is_error():
                reasons.append("ERROR")

        if not bc.config.bot.disable_restrictions:
            if bc._trades_today >= bc.config.risk.max_trades_per_day:
                reasons.append(f"MAX_TRADES({bc._trades_today}/{bc.config.risk.max_trades_per_day})")

            account_value = 10000.0
            daily_pnl_pct = (bc._daily_pnl / account_value) * 100
            if daily_pnl_pct <= -bc.config.risk.max_daily_loss_pct:
                reasons.append(f"MAX_LOSS({daily_pnl_pct:.2f}%)")

            if bc._consecutive_losses >= bc.config.risk.loss_streak_cooldown:
                reasons.append(f"LOSS_STREAK({bc._consecutive_losses}/{bc.config.risk.loss_streak_cooldown})")
        else:
            reasons.append("UNRESTRICTED")

        pos_status = "None"
        if bc.position:
            pos_status = f"{bc.position.side.value.upper()} @ {bc.position.entry_price:.2f}"

        status_str = "OK" if can_trade else "X"
        reason_str = ", ".join(reasons) if reasons else "OK"

        self._add_ki_log_entry(
            "DIAG",
            f"State={state} | CanTrade={status_str} [{reason_str}] | Pos={pos_status} | Trades={bc._trades_today}"
        )
    def log_ki_request(self, request: dict, response: dict | None = None) -> None:
        """Log a KI request/response pair.

        Args:
            request: Request data sent to KI
            response: Response received (if any)
        """
        self._add_ki_log_entry("REQUEST", f"Sent: {len(str(request))} chars")
        if response:
            if response.get("error"):
                self._add_ki_log_entry("ERROR", response["error"])
            else:
                action = response.get("action", "unknown")
                confidence = response.get("confidence", 0)
                self._add_ki_log_entry(
                    "RESPONSE",
                    f"Action: {action}, Confidence: {confidence:.2f}"
                )

        calls = int(self.ki_calls_today_label.text()) + 1
        self.ki_calls_today_label.setText(str(calls))
        self.ki_last_call_label.setText(datetime.now().strftime("%H:%M:%S"))
