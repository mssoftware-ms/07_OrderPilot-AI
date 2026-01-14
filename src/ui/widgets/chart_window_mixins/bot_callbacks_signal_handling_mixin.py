from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QTableWidgetItem

logger = logging.getLogger(__name__)

class BotCallbacksSignalHandlingMixin:
    """Signal callback handling and tracking"""

    def _on_bot_signal(self, signal: Any) -> None:
        """Handle bot signal event."""
        signal_type, side, entry_price, score, strategy_name, signal_stop_price = self._extract_signal_fields(signal)
        status = self._map_signal_status(signal_type)

        # Gate: only one open position allowed. Ignore new signals while open.
        if self._has_open_signal() and signal_type in {"candidate", "confirmed"}:
            msg = (
                "Signal ignoriert – bereits offene Position vorhanden. "
                "Neue Trades erst nach Exit/SL."
            )
            self._add_ki_log_entry("WARN", msg)
            logger.warning(msg)
            return

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
            # Enforce single open position after confirming/adding
            self._enforce_single_open_signal(refresh=False)

            # Start P&L update timer for live price updates in Signals Tab
            if hasattr(self, '_start_pnl_update_timer'):
                self._start_pnl_update_timer()
                logger.info("P&L update timer started for new ENTERED signal")
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

        # Get strategy details if available
        strategy_details = self._get_strategy_details(strategy_name)

        # Speichere Hebel beim Entry statisch (wird nicht mehr mit UI-Wert aktualisiert)
        leverage_at_entry = None
        if hasattr(self, 'leverage_spin'):
            leverage_at_entry = self.leverage_spin.value()
            logger.info(f"Hebel beim Entry gespeichert: {leverage_at_entry}x")

        self._signal_history.append({
            "time": self._format_entry_time(),
            "signal_id": self._next_signal_id,  # Fortlaufende dreistellige ID
            "type": signal_type,
            "side": side,
            "score": score,
            "strategy": strategy_name,
            "strategy_details": strategy_details,  # Strategie-Name und Parameter
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
            "entry_timestamp": self._get_chart_timestamp(),
            "entry_timestamp_utc": int(datetime.now(timezone.utc).timestamp()),
            "initial_sl_pct": initial_sl_pct,
            "trailing_stop_pct": trailing_pct,
            "trailing_stop_price": trailing_stop_price,
            "trailing_activation_pct": trailing_activation,
            "tr_active": False,
            "tr_lock_active": True,
            "leverage_at_entry": leverage_at_entry,  # Statischer Hebel beim Entry
        })

        # Increment signal ID for next signal
        self._next_signal_id += 1

        # Ensure we never keep more than one open position
        self._enforce_single_open_signal(refresh=False)

        # Send WhatsApp notification for position entry
        try:
            # Use WhatsApp widget's working UI form mechanism
            if hasattr(self, 'whatsapp_tab') and self.whatsapp_tab:
                symbol = getattr(self, 'current_symbol', 'UNKNOWN')
                leverage = leverage_at_entry

                # Create TradeNotification and format message
                notification = TradeNotification(
                    action="BUY",
                    symbol=symbol,
                    side=side,
                    quantity=invested / entry_price,  # Calculate quantity from invested amount
                    entry_price=entry_price,
                    leverage=leverage,
                    timestamp=datetime.now()
                )
                message = notification.format_message()

                # Send via WhatsApp widget (uses working UI form)
                self.whatsapp_tab.send_trade_notification(message)
                logger.info(f"WhatsApp notification sent: Position opened {side} @ {entry_price:.4f}")
            else:
                logger.warning("WhatsApp widget not available for notification")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp notification: {e}")

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
                entry_dt = datetime.now(timezone.utc)
                sig["entry_timestamp"] = self._get_chart_timestamp(entry_dt)
                sig["entry_timestamp_utc"] = int(entry_dt.timestamp())
                sig["time"] = self._format_entry_time(entry_dt)
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

                # Speichere Hebel beim Entry statisch (wird nicht mehr mit UI-Wert aktualisiert)
                leverage_at_entry = None
                if hasattr(self, 'leverage_spin'):
                    leverage_at_entry = self.leverage_spin.value()
                    sig["leverage_at_entry"] = leverage_at_entry
                    logger.info(f"Hebel beim Entry gespeichert: {leverage_at_entry}x")

                logger.info(
                    f"Updated candidate to confirmed: {side} @ {entry_price:.4f}, "
                    f"SL={signal_stop_price:.4f}, invested={invested}, TR%={trailing_pct}, TRA%={trailing_activation}, Hebel={leverage_at_entry}"
                )

                # Send WhatsApp notification for position entry
                try:
                    # Use WhatsApp widget's working UI form mechanism
                    if hasattr(self, 'whatsapp_tab') and self.whatsapp_tab:
                        symbol = getattr(self, 'current_symbol', 'UNKNOWN')
                        quantity = sig.get("quantity", 0.0)
                        leverage = leverage_at_entry

                        # Create TradeNotification and format message
                        notification = TradeNotification(
                            action="BUY",
                            symbol=symbol,
                            side=side,
                            quantity=quantity if quantity > 0 else invested / entry_price,
                            entry_price=entry_price,
                            leverage=leverage,
                            timestamp=datetime.now()
                        )
                        message = notification.format_message()

                        # Send via WhatsApp widget (uses working UI form)
                        self.whatsapp_tab.send_trade_notification(message)
                        logger.info(f"WhatsApp notification sent: Position opened {side} @ {entry_price:.4f}")
                    else:
                        logger.warning("WhatsApp widget not available for notification")
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp notification: {e}")

                return True
        return False

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
            entry_ts = self._get_chart_timestamp()
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

            # Issue #10: Draw trailing stop line immediately when position is opened
            # Get trailing stop info from the active signal
            active_sig = self._find_active_signal()
            if active_sig:
                trailing_stop_price = active_sig.get("trailing_stop_price", 0)
                trailing_pct = active_sig.get("trailing_stop_pct", 0)
                if trailing_stop_price > 0 and trailing_pct > 0:
                    # Gray color for inactive trailing stop
                    tr_color = "#888888"  # Gray when not yet active
                    tr_label = f"TSL @ {trailing_stop_price:.2f} ({trailing_pct:.2f}%) [wartend]"
                    self.chart_widget.add_stop_line(
                        "trailing_stop",
                        trailing_stop_price,
                        line_type="trailing",
                        color=tr_color,
                        label=tr_label
                    )
                    self._add_ki_log_entry("CHART", f"Trailing-Stop-Linie gezeichnet @ {trailing_stop_price:.2f} (wartend)")

            self._save_signal_history()
            self._maybe_fetch_derivative_for_confirmed()

        except Exception as e:
            logger.error(f"Error drawing chart elements in _on_bot_signal: {e}")
            self._add_ki_log_entry("ERROR", f"Chart-Fehler: {e}")

