from __future__ import annotations

import logging
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)

class BotCallbacksSignalMixin:
    """BotCallbacksSignalMixin extracted from BotCallbacksMixin."""
    def _on_bot_signal(self, signal: Any) -> None:
        """Handle bot signal event."""
        signal_type, side, entry_price, score, strategy_name, signal_stop_price = self._extract_signal_fields(signal)
        status = self._map_signal_status(signal_type)

        self._add_ki_log_entry(
            "SIGNAL",
            f"Signal empfangen: type={signal_type} strategy={strategy_name} side={side} @ {entry_price:.4f} SL={signal_stop_price:.4f} -> status={status}"
        )

        logger.info(
            f"Bot signal received: {signal_type} ({strategy_name}) {side} @ {entry_price:.4f} (Score: {score:.2f}, SL: {signal_stop_price:.4f})"
        )


        capital, risk_pct, invested, initial_sl_pct, trailing_pct, trailing_activation = self._get_signal_ui_values()

        # Debug: log the values we're setting
        self._add_ki_log_entry(
            "DEBUG",
            f"Signal UI values: capital={capital}, risk%={risk_pct}, invested={invested}, "
            f"SL%={initial_sl_pct}, TR%={trailing_pct}, TRA%={trailing_activation}"
        )

        signal_stop_price = self._ensure_stop_price(
            signal_stop_price, entry_price, initial_sl_pct, side
        )

        # For confirmed signals, update existing candidate instead of adding new
        if signal_type == "confirmed":
            updated = self._update_candidate_to_confirmed(
                side,
                score,
                strategy_name,
                entry_price,
                signal_stop_price,
                invested,
                initial_sl_pct,
                trailing_pct,
                trailing_activation,
            )
            if not updated:
                self._add_confirmed_signal(
                    signal_type,
                    side,
                    score,
                    strategy_name,
                    entry_price,
                    signal_stop_price,
                    invested,
                    initial_sl_pct,
                    trailing_pct,
                    trailing_activation,
                )
        else:
            self._update_or_add_candidate(
                signal_type, side, score, strategy_name, entry_price, status
            )

        self._update_signals_table()

        # For confirmed signals, draw chart elements directly as backup
        # (in case _on_bot_decision doesn't fire or has issues)
        if signal_type == "confirmed" and hasattr(self, 'chart_widget'):
            self._draw_chart_for_confirmed_signal(
                entry_price,
                score,
                side,
                signal_stop_price,
                initial_sl_pct,
            )

    def _extract_signal_fields(self, signal: Any) -> tuple[str, str, float, float, str, float]:
        signal_type = signal.signal_type.value if hasattr(signal, 'signal_type') else "unknown"
        side = signal.side.value if hasattr(signal, 'side') else "unknown"
        entry_price = getattr(signal, 'entry_price', 0)
        score = getattr(signal, 'score', 0)
        strategy_name = getattr(signal, 'strategy_name', "Manual")
        signal_stop_price = getattr(signal, 'stop_loss_price', 0)
        return signal_type, side, entry_price, score, strategy_name, signal_stop_price

    def _map_signal_status(self, signal_type: str) -> str:
        if signal_type == "confirmed":
            return "ENTERED"
        if signal_type == "candidate":
            return "PENDING"
        return "ACTIVE"

    def _get_signal_ui_values(self) -> tuple[float, float, float, float, float, float]:
        capital = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000
        risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10
        invested = capital * (risk_pct / 100)
        initial_sl_pct = self.initial_sl_spin.value() if hasattr(self, 'initial_sl_spin') else 2.0
        trailing_pct = self.trailing_distance_spin.value() if hasattr(self, 'trailing_distance_spin') else 1.5
        trailing_activation = self.tra_percent_spin.value() if hasattr(self, 'tra_percent_spin') else 0.0
        return capital, risk_pct, invested, initial_sl_pct, trailing_pct, trailing_activation

    def _ensure_stop_price(self, signal_stop_price: float, entry_price: float, initial_sl_pct: float, side: str) -> float:
        if signal_stop_price <= 0 and entry_price > 0 and initial_sl_pct > 0:
            if side.lower() == "long":
                signal_stop_price = entry_price * (1 - initial_sl_pct / 100)
            else:
                signal_stop_price = entry_price * (1 + initial_sl_pct / 100)
            self._add_ki_log_entry(
                "DEBUG",
                f"Stop-Preis aus UI berechnet: {side.upper()} entry={entry_price:.2f} SL%={initial_sl_pct:.2f} -> SL={signal_stop_price:.2f}"
            )
        return signal_stop_price

    def _update_candidate_to_confirmed(
        self,
        side: str,
        score: float,
        strategy_name: str,
        entry_price: float,
        signal_stop_price: float,
        invested: float,
        initial_sl_pct: float,
        trailing_pct: float,
        trailing_activation: float,
    ) -> bool:
        for sig in reversed(self._signal_history):
            if sig["type"] == "candidate" and sig["side"] == side and sig["status"] == "PENDING":
                sig["type"] = "confirmed"
                sig["status"] = "ENTERED"
                sig["score"] = score
                sig["strategy"] = strategy_name
                sig["price"] = entry_price
                sig["is_open"] = True
                sig["label"] = f"E:{int(score * 100)}"
                sig["entry_timestamp"] = int(datetime.now().timestamp())
                sig["stop_price"] = signal_stop_price
                sig["invested"] = invested
                sig["initial_sl_pct"] = initial_sl_pct
                sig["trailing_stop_pct"] = trailing_pct
                sig["trailing_activation_pct"] = trailing_activation
                sig["tr_lock_active"] = True
                sig["tr_active"] = False
                if trailing_pct > 0:
                    if side.lower() == "long":
                        sig["trailing_stop_price"] = entry_price * (1 - trailing_pct / 100)
                    else:
                        sig["trailing_stop_price"] = entry_price * (1 + trailing_pct / 100)
                logger.info(
                    f"Updated candidate to confirmed: {side} @ {entry_price:.4f}, "
                    f"SL={signal_stop_price:.4f}, invested={invested}, TR%={trailing_pct}, TRA%={trailing_activation}"
                )
                return True
        return False

    def _add_confirmed_signal(
        self,
        signal_type: str,
        side: str,
        score: float,
        strategy_name: str,
        entry_price: float,
        signal_stop_price: float,
        invested: float,
        initial_sl_pct: float,
        trailing_pct: float,
        trailing_activation: float,
    ) -> None:
        trailing_stop_price = 0.0
        if trailing_pct > 0:
            if side.lower() == "long":
                trailing_stop_price = entry_price * (1 - trailing_pct / 100)
            else:
                trailing_stop_price = entry_price * (1 + trailing_pct / 100)

        self._signal_history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": signal_type,
            "side": side,
            "score": score,
            "strategy": strategy_name,
            "price": entry_price,
            "stop_price": signal_stop_price,
            "status": "ENTERED",
            "quantity": 0.0,
            "invested": invested,
            "current_price": entry_price,
            "pnl_currency": 0.0,
            "pnl_percent": 0.0,
            "is_open": True,
            "label": f"E:{int(score * 100)}",
            "entry_timestamp": int(datetime.now().timestamp()),
            "initial_sl_pct": initial_sl_pct,
            "trailing_stop_pct": trailing_pct,
            "trailing_stop_price": trailing_stop_price,
            "trailing_activation_pct": trailing_activation,
            "tr_active": False,
            "tr_lock_active": True,
        })

    def _update_or_add_candidate(
        self,
        signal_type: str,
        side: str,
        score: float,
        strategy_name: str,
        entry_price: float,
        status: str,
    ) -> None:
        existing_candidate = None
        for sig in reversed(self._signal_history):
            if sig["type"] == "candidate" and sig["side"] == side and sig["status"] == "PENDING":
                existing_candidate = sig
                break

        if existing_candidate:
            existing_candidate["time"] = datetime.now().strftime("%H:%M:%S")
            existing_candidate["score"] = score
            existing_candidate["strategy"] = strategy_name
            existing_candidate["price"] = entry_price
            existing_candidate["current_price"] = entry_price
            logger.info(
                f"Updated existing candidate: {side} @ {entry_price:.4f} "
                f"(Score: {score:.2f}, Strategy: {strategy_name})"
            )
            self._add_ki_log_entry("SIGNAL", f"Kandidat aktualisiert: {side} @ {entry_price:.4f} ({strategy_name})")

            if (
                hasattr(self, "enable_derivathandel_cb")
                and self.enable_derivathandel_cb.isChecked()
                and hasattr(self, "_fetch_derivative_for_signal")
                and not existing_candidate.get("derivative")
            ):
                self._add_ki_log_entry("DERIV", f"KO-Suche gestartet (Kandidat {side.upper()} aktualisiert)")
                self._fetch_derivative_for_signal(existing_candidate)
            return

        new_signal = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": signal_type,
            "side": side,
            "score": score,
            "strategy": strategy_name,
            "price": entry_price,
            "status": status,
            "quantity": 0.0,
            "current_price": entry_price,
            "pnl_currency": 0.0,
            "pnl_percent": 0.0,
            "is_open": False,
            "label": ""
        }
        self._signal_history.append(new_signal)

        if (
            hasattr(self, "enable_derivathandel_cb")
            and self.enable_derivathandel_cb.isChecked()
            and hasattr(self, "_fetch_derivative_for_signal")
        ):
            self._add_ki_log_entry("DERIV", f"KO-Suche gestartet (Kandidat {side.upper()})")
            self._fetch_derivative_for_signal(new_signal)

    def _draw_chart_for_confirmed_signal(
        self,
        entry_price: float,
        score: float,
        side: str,
        signal_stop_price: float,
        initial_sl_pct: float,
    ) -> None:
        self._add_ki_log_entry("DEBUG", f"Chart-Elemente zeichnen: entry={entry_price:.2f}, SL={signal_stop_price:.2f}")
        try:
            entry_ts = int(datetime.now().timestamp())
            label = f"E:{int(score * 100)}"
            self.chart_widget.add_bot_marker(
                timestamp=entry_ts,
                price=entry_price,
                marker_type=MarkerType.ENTRY_CONFIRMED,
                side=side,
                text=label
            )
            self._add_ki_log_entry("CHART", f"Entry-Marker gezeichnet: {label} @ {entry_price:.2f}")

            entry_label = f"Entry @ {entry_price:.2f}"
            entry_color = "#26a69a" if side.lower() == "long" else "#ef5350"
            self.chart_widget.add_stop_line(
                "entry_line",
                entry_price,
                line_type="target",
                color=entry_color,
                label=entry_label
            )
            self._add_ki_log_entry("CHART", f"Entry-Linie gezeichnet @ {entry_price:.2f}")

            if signal_stop_price > 0:
                sl_label = f"SL @ {signal_stop_price:.2f} ({initial_sl_pct:.2f}%)"
                self.chart_widget.add_stop_line(
                    "initial_stop",
                    signal_stop_price,
                    line_type="initial",
                    color="#ef5350",
                    label=sl_label
                )
                self._add_ki_log_entry("CHART", f"Stop-Loss-Linie gezeichnet @ {signal_stop_price:.2f}")
            else:
                self._add_ki_log_entry("WARN", f"Kein Stop-Preis! signal_stop_price={signal_stop_price}")

            self._save_signal_history()
            self._maybe_fetch_derivative_for_confirmed()

        except Exception as e:
            logger.error(f"Error drawing chart elements in _on_bot_signal: {e}")
            self._add_ki_log_entry("ERROR", f"Chart-Fehler: {e}")

    def _maybe_fetch_derivative_for_confirmed(self) -> None:
        if (
            hasattr(self, "enable_derivathandel_cb")
            and self.enable_derivathandel_cb.isChecked()
            and hasattr(self, "_fetch_derivative_for_signal")
        ):
            for sig in reversed(self._signal_history):
                if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                    if not sig.get("derivative"):
                        self._add_ki_log_entry("DERIV", "KO-Suche (Fallback bei Bestätigung)")
                        self._fetch_derivative_for_signal(sig)
                    break
    def _on_bot_decision(self, decision: Any) -> None:
        """Handle bot decision event."""
        from src.core.tradingbot.models import BotAction

        action = decision.action if hasattr(decision, 'action') else None
        self._add_ki_log_entry("DEBUG", f"_on_bot_decision called: action={action.value if action else 'unknown'}")

        # Handle stop line updates on chart
        if hasattr(self, 'chart_widget') and action:
            try:
                if action == BotAction.ENTER:
                    self._handle_bot_enter(decision)
                elif action == BotAction.ADJUST_STOP:
                    self._handle_bot_adjust_stop(decision)
                elif action == BotAction.EXIT:
                    self._handle_bot_exit(decision)

            except Exception as e:
                logger.error(f"Error updating chart for decision: {e}")

    def _handle_bot_enter(self, decision: Any) -> None:
        """Handle BotAction.ENTER."""
        stop_price = getattr(decision, 'stop_price_after', None)
        self._add_ki_log_entry("DEBUG", f"ENTER: stop_price_after={stop_price}")
        if not stop_price:
            self._add_ki_log_entry("ERROR", "stop_price_after ist None - keine Stop-Line!")
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
            self._save_signal_history()
            self._add_ki_log_entry("EXIT", f"Position geschlossen: {exit_status} @ {current_price:.2f}")

        self._remove_position_lines()
        self._reset_state_machine()

    def _find_active_signal(self) -> dict[str, Any] | None:
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                return sig
        return None

    def _get_current_price(self) -> float:
        if self._bot_controller and self._bot_controller._last_features:
            return self._bot_controller._last_features.close
        return 0.0

    def _calculate_tra_pct(self, new_stop: float) -> float:
        current_price = self._get_current_price()
        if current_price > 0:
            return abs((current_price - new_stop) / current_price) * 100
        return 0.0

    def _map_exit_status(self, reason_codes: list[str]) -> tuple[str, bool, bool]:
        exit_status = "CLOSED"
        is_trailing_stop_exit = False
        is_rsi_exit = False
        if "STOP_HIT" in reason_codes:
            exit_status = "SL"
        elif "TRAILING_STOP" in reason_codes or "TRAILING_STOP_HIT" in reason_codes:
            exit_status = "TR"
            is_trailing_stop_exit = True
        elif "MACD_CROSS" in reason_codes:
            exit_status = "MACD"
        elif (
            "RSI_EXTREME" in reason_codes
            or "RSI_EXTREME_OVERBOUGHT" in reason_codes
            or "RSI_EXTREME_OVERSOLD" in reason_codes
        ):
            exit_status = "RSI"
            is_rsi_exit = True
        elif "MANUAL" in reason_codes:
            exit_status = "Sell"
        return exit_status, is_trailing_stop_exit, is_rsi_exit

    def _should_block_rsi_exit(self, reason_codes: list[str]) -> bool:
        if hasattr(self, 'disable_rsi_exit_cb') and self.disable_rsi_exit_cb.isChecked():
            current_price = self._get_current_price()
            if hasattr(self, 'chart_widget') and current_price > 0:
                is_overbought = "RSI_EXTREME_OVERBOUGHT" in reason_codes
                rsi_text = "RSI↓" if is_overbought else "RSI↑"
                self.chart_widget.add_bot_marker(
                    timestamp=int(datetime.now().timestamp()),
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

    def _should_block_trailing_exit(self) -> bool:
        active_sig = self._find_active_signal()
        if active_sig and not active_sig.get("tr_active", False):
            self._add_ki_log_entry(
                "BLOCK",
                "TR Exit BLOCKIERT! tr_active=False (Aktivierungsschwelle nicht erreicht)"
            )
            logger.warning("Blocked TR exit because tr_active=False")
            return True
        return False

    def _remove_position_lines(self) -> None:
        self.chart_widget.remove_stop_line("initial_stop")
        self.chart_widget.remove_stop_line("trailing_stop")
        self.chart_widget.remove_stop_line("entry_line")
        self._add_ki_log_entry("CHART", "Alle Linien entfernt (Position geschlossen)")

    def _reset_state_machine(self) -> None:
        if self._bot_controller and hasattr(self._bot_controller, '_state_machine'):
            from src.core.tradingbot.state_machine import BotTrigger
            try:
                self._bot_controller._state_machine.trigger(BotTrigger.RESET, force=True)
                self._add_ki_log_entry("BOT", "State Machine zurückgesetzt -> FLAT (bereit für neue Signale)")
            except Exception as reset_e:
                logger.error(f"Failed to reset state machine: {reset_e}")
    def _on_macd_signal(self, signal_type: str, price: float) -> None:
        """Handle MACD signal from bot controller."""
        logger.info(f"MACD signal received: {signal_type} @ {price:.4f}")
        self._add_ki_log_entry("MACD", f"{signal_type.upper()} @ {price:.4f}")

        # Add MACD marker to chart
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_bot_marker'):
            try:
                is_bullish = "bullish" in signal_type.lower()
                marker_type = MarkerType.MACD_BULLISH if is_bullish else MarkerType.MACD_BEARISH
                self.chart_widget.add_bot_marker(
                    timestamp=int(datetime.now().timestamp()),
                    price=price,
                    marker_type=marker_type,
                    side="long" if is_bullish else "short",
                    text="MACD"
                )
            except Exception as e:
                logger.error(f"Failed to add MACD marker: {e}")
    def _on_trading_blocked(self, reasons: list[str]) -> None:
        """Handle trading blocked event."""
        reason_str = ", ".join(reasons)
        logger.warning(f"Trading blocked: {reason_str}")
        self._add_ki_log_entry("BLOCKED", f"Trading gesperrt: {reason_str}")

        # Update position labels if currently flat
        if hasattr(self, 'position_side_label'):
            self.position_side_label.setText(f"BLOCKED")
            self.position_side_label.setStyleSheet("font-weight: bold; color: #ff9800;")
    def _on_bot_state_change(self, old_state: str, new_state: str) -> None:
        """Handle bot state change."""
        logger.info(f"Bot state change: {old_state} -> {new_state}")
        self._add_ki_log_entry("STATE", f"{old_state} -> {new_state}")

        # Map state to status display
        state_colors = {
            "idle": ("#9e9e9e", "IDLE"),
            "waiting_signal": ("#2196f3", "WAITING"),
            "in_position": ("#26a69a", "IN POSITION"),
            "paused": ("#ff9800", "PAUSED"),
            "error": ("#f44336", "ERROR"),
            "stopped": ("#9e9e9e", "STOPPED"),
        }

        if new_state.lower() in state_colors:
            color, status = state_colors[new_state.lower()]
            self._update_bot_status(status, color)
