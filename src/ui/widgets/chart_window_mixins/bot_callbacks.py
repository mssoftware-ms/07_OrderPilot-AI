"""Bot Callbacks - Bot controller callbacks and control.

Contains methods for starting/stopping the bot and handling callbacks:
- _start_bot_with_config, _stop_bot
- _on_bot_signal, _on_bot_decision
- _on_bot_order, _on_bot_log
- _on_macd_signal, _on_trading_blocked
- _on_bot_state_change
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QTimer

from src.ui.widgets.chart_mixins.bot_overlay_mixin import MarkerType

if TYPE_CHECKING:
    from src.core.tradingbot import BotController

logger = logging.getLogger(__name__)


class BotCallbacksMixin:
    """Mixin providing bot controller callbacks and control methods."""

    def _start_bot_with_config(self) -> None:
        """Start bot with current UI configuration."""
        from src.core.tradingbot import (
            BotConfig,
            FullBotConfig,
            KIMode,
            MarketType,
            RiskConfig,
            TrailingMode,
        )

        # Get symbol from chart
        symbol = getattr(self, 'current_symbol', 'AAPL')
        if hasattr(self, 'chart_widget'):
            symbol = getattr(self.chart_widget, 'current_symbol', symbol)

        # Build config
        ki_mode = KIMode(self.ki_mode_combo.currentText().lower())
        trailing_mode = TrailingMode(self.trailing_mode_combo.currentText().lower())

        # Determine market type from symbol
        market_type = MarketType.CRYPTO if '/' in symbol else MarketType.NASDAQ

        config = FullBotConfig.create_default(symbol, market_type)

        # Override with UI values
        config.bot.ki_mode = ki_mode
        config.bot.trailing_mode = trailing_mode
        config.bot.disable_restrictions = self.disable_restrictions_cb.isChecked()
        config.bot.disable_macd_exit = self.disable_macd_exit_cb.isChecked()
        config.risk.initial_stop_loss_pct = self.initial_sl_spin.value()
        config.risk.risk_per_trade_pct = self.risk_per_trade_spin.value()
        config.risk.max_trades_per_day = self.max_trades_spin.value()
        config.risk.max_daily_loss_pct = self.max_daily_loss_spin.value()

        # Trailing stop settings
        config.risk.regime_adaptive_trailing = self.regime_adaptive_cb.isChecked()
        config.risk.trailing_atr_multiple = self.atr_multiplier_spin.value()
        config.risk.trailing_atr_trending = self.atr_trending_spin.value()
        config.risk.trailing_atr_ranging = self.atr_ranging_spin.value()
        config.risk.trailing_volatility_bonus = self.volatility_bonus_spin.value()
        config.risk.trailing_min_step_pct = self.min_step_spin.value()
        config.risk.trailing_activation_pct = self.trailing_activation_spin.value()
        config.risk.trailing_pct_distance = self.trailing_distance_spin.value()

        # Create and start controller with callbacks
        from src.core.tradingbot.bot_controller import BotController

        self._bot_controller = BotController(
            config,
            on_signal=self._on_bot_signal,
            on_decision=self._on_bot_decision,
            on_order=self._on_bot_order,
            on_log=self._on_bot_log,
            on_trading_blocked=self._on_trading_blocked,
            on_macd_signal=self._on_macd_signal,
        )

        # Register state change callback
        self._bot_controller._state_machine._on_transition = lambda t: (
            self._on_bot_state_change(t.from_state.value, t.to_state.value)
        )

        # Warmup from chart data
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
            try:
                chart_data = self.chart_widget.data
                warmup_bars = []
                for timestamp, row in chart_data.iterrows():
                    warmup_bars.append({
                        'timestamp': timestamp,
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row.get('volume', 0)),
                    })
                loaded = self._bot_controller.warmup_from_history(warmup_bars)
                logger.info(f"Bot warmup: {loaded} bars from chart history")
            except Exception as e:
                logger.warning(f"Could not warmup from chart data: {e}")

        # Start the bot
        self._bot_controller.start()
        self._update_bot_status("RUNNING", "#26a69a")

        # Start update timer
        if not self._bot_update_timer:
            self._bot_update_timer = QTimer()
            self._bot_update_timer.timeout.connect(self._update_bot_display)
        self._bot_update_timer.start(1000)

        # Save settings for this symbol
        self._save_bot_settings(symbol)

        logger.info(f"Bot started for {symbol} with {ki_mode.value} mode")

    def _stop_bot(self) -> None:
        """Stop the running bot."""
        if self._bot_controller:
            self._bot_controller.stop()
            self._bot_controller = None

        if self._bot_update_timer:
            self._bot_update_timer.stop()

        logger.info("Bot stopped")

    # ==================== CALLBACKS ====================

    def _on_bot_signal(self, signal: Any) -> None:
        """Handle bot signal event."""
        signal_type = signal.signal_type.value if hasattr(signal, 'signal_type') else "unknown"
        side = signal.side.value if hasattr(signal, 'side') else "unknown"
        entry_price = getattr(signal, 'entry_price', 0)
        score = getattr(signal, 'score', 0)
        # Get stop_loss_price from signal (this is calculated by the bot based on initial_stop_loss_pct)
        signal_stop_price = getattr(signal, 'stop_loss_price', 0)

        # Determine status based on signal type
        if signal_type == "confirmed":
            status = "ENTERED"
        elif signal_type == "candidate":
            status = "PENDING"
        else:
            status = "ACTIVE"

        self._add_ki_log_entry(
            "SIGNAL",
            f"Signal empfangen: type={signal_type} side={side} @ {entry_price:.4f} SL={signal_stop_price:.4f} -> status={status}"
        )

        logger.info(
            f"Bot signal received: {signal_type} {side} @ {entry_price:.4f} (Score: {score:.2f}, SL: {signal_stop_price:.4f})"
        )

        # Get initial values from UI for new signals
        capital = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000
        risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10
        invested = capital * (risk_pct / 100)
        initial_sl_pct = self.initial_sl_spin.value() if hasattr(self, 'initial_sl_spin') else 2.0
        trailing_pct = self.trailing_distance_spin.value() if hasattr(self, 'trailing_distance_spin') else 1.5
        trailing_activation = self.trailing_activation_spin.value() if hasattr(self, 'trailing_activation_spin') else 0.0

        # Debug: log the values we're setting
        self._add_ki_log_entry(
            "DEBUG",
            f"Signal UI values: capital={capital}, risk%={risk_pct}, invested={invested}, "
            f"SL%={initial_sl_pct}, TR%={trailing_pct}, TRA_threshold={trailing_activation}"
        )

        # For confirmed signals, update existing candidate instead of adding new
        if signal_type == "confirmed":
            for sig in reversed(self._signal_history):
                if sig["type"] == "candidate" and sig["side"] == side and sig["status"] == "PENDING":
                    sig["type"] = "confirmed"
                    sig["status"] = "ENTERED"
                    sig["score"] = score
                    sig["price"] = entry_price
                    sig["is_open"] = True
                    sig["label"] = f"E:{int(score * 100)}"
                    sig["entry_timestamp"] = int(datetime.now().timestamp())
                    # Set stop_price from signal (calculated by bot)
                    if signal_stop_price > 0:
                        sig["stop_price"] = signal_stop_price
                    # Set initial invested, TR% values from UI
                    sig["invested"] = invested
                    sig["initial_sl_pct"] = initial_sl_pct
                    sig["trailing_stop_pct"] = trailing_pct
                    sig["trailing_activation_pct"] = trailing_activation
                    # Calculate initial trailing_stop_price from entry +/- TR%
                    # TR is NOT active until price moves past activation threshold
                    sig["tr_active"] = False  # Will activate when price > entry + TRA%
                    if trailing_pct > 0:
                        if side.lower() == "long":
                            sig["trailing_stop_price"] = entry_price * (1 - trailing_pct / 100)
                        else:
                            sig["trailing_stop_price"] = entry_price * (1 + trailing_pct / 100)
                    logger.info(f"Updated candidate to confirmed: {side} @ {entry_price:.4f}, SL={signal_stop_price:.4f}, invested={invested}, TR%={trailing_pct}")
                    break
            else:
                # No candidate found - add new confirmed entry
                # Calculate initial trailing_stop_price from entry +/- TR%
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
                    "price": entry_price,
                    "stop_price": signal_stop_price if signal_stop_price > 0 else 0,
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
                    "tr_active": False,  # Will activate when price > entry + TRA%
                })
        else:
            # Candidate signal - add new entry
            self._signal_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": signal_type,
                "side": side,
                "score": score,
                "price": entry_price,
                "status": status,
                "quantity": 0.0,
                "current_price": entry_price,
                "pnl_currency": 0.0,
                "pnl_percent": 0.0,
                "is_open": False,
                "label": ""
            })

        self._update_signals_table()

        # For confirmed signals, draw chart elements directly as backup
        # (in case _on_bot_decision doesn't fire or has issues)
        if signal_type == "confirmed" and hasattr(self, 'chart_widget'):
            try:
                # Draw Entry Marker
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

                # Draw Stop Loss Line
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

                # Save signal history with chart elements
                self._save_signal_history()

            except Exception as e:
                logger.error(f"Error drawing chart elements in _on_bot_signal: {e}")

    def _on_bot_decision(self, decision: Any) -> None:
        """Handle bot decision event."""
        from src.core.tradingbot.models import BotAction

        action = decision.action if hasattr(decision, 'action') else None
        self._add_ki_log_entry("DEBUG", f"_on_bot_decision called: action={action.value if action else 'unknown'}")

        # Handle stop line updates on chart
        if hasattr(self, 'chart_widget') and action:
            try:
                if action == BotAction.ENTER:
                    # Draw initial stop line
                    stop_price = getattr(decision, 'stop_price_after', None)
                    self._add_ki_log_entry("DEBUG", f"ENTER: stop_price_after={stop_price}")
                    if stop_price:
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

                        for sig in reversed(self._signal_history):
                            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                                sig["stop_price"] = stop_price
                                sig["initial_sl_pct"] = initial_sl_pct
                                self._save_signal_history()
                                break
                    else:
                        self._add_ki_log_entry("ERROR", "stop_price_after ist None - keine Stop-Line!")

                elif action == BotAction.ADJUST_STOP:
                    # Update trailing stop line
                    new_stop = getattr(decision, 'stop_price_after', None)
                    old_stop = getattr(decision, 'stop_price_before', None)
                    if new_stop:
                        if old_stop:
                            change_pct = ((new_stop - old_stop) / old_stop) * 100
                            self._add_ki_log_entry(
                                "TRAILING",
                                f"Stop angepasst: {old_stop:.2f} -> {new_stop:.2f} ({change_pct:+.2f}%)"
                            )
                        else:
                            self._add_ki_log_entry("TRAILING", f"Trailing Stop aktiviert @ {new_stop:.2f}")

                        trailing_pct = self.trailing_distance_spin.value() if hasattr(self, 'trailing_distance_spin') else 0.0
                        tra_pct = 0.0
                        if self._bot_controller and self._bot_controller._last_features:
                            current_price = self._bot_controller._last_features.close
                            if current_price > 0:
                                tra_pct = abs((current_price - new_stop) / current_price) * 100

                        # Update signal history
                        for sig in reversed(self._signal_history):
                            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                                sig["stop_price"] = new_stop
                                sig["trailing_stop_price"] = new_stop
                                sig["trailing_stop_pct"] = trailing_pct

                                # Only draw TR line if tr_active (activation threshold crossed)
                                tr_is_active = sig.get("tr_active", False)
                                if tr_is_active:
                                    tr_label = f"TSL @ {new_stop:.2f} ({trailing_pct:.2f}% / TRA: {tra_pct:.2f}%)"
                                    self.chart_widget.add_stop_line(
                                        "trailing_stop",
                                        new_stop,
                                        line_type="trailing",
                                        color="#ff9800",
                                        label=tr_label
                                    )
                                self._save_signal_history()
                                break

                elif action == BotAction.EXIT:
                    # Determine exit reason from decision
                    reason_codes = getattr(decision, 'reason_codes', [])
                    exit_status = "CLOSED"  # Default

                    # Map reason codes to display status
                    if "STOP_HIT" in reason_codes:
                        exit_status = "SL"
                    elif "TRAILING_STOP" in reason_codes or "TRAILING_STOP_HIT" in reason_codes:
                        exit_status = "TR Stop"
                    elif "MACD_CROSS" in reason_codes:
                        exit_status = "MACD"
                    elif "RSI_EXTREME" in reason_codes or "RSI_EXTREME_OVERBOUGHT" in reason_codes or "RSI_EXTREME_OVERSOLD" in reason_codes:
                        exit_status = "RSI"
                    elif "TIME_STOP" in reason_codes:
                        exit_status = "Time"
                    elif "MANUAL" in reason_codes:
                        exit_status = "Sold"

                    # Get current price for P&L
                    current_price = 0.0
                    if self._bot_controller and self._bot_controller._last_features:
                        current_price = self._bot_controller._last_features.close

                    # Update signal history - close the position
                    for sig in reversed(self._signal_history):
                        if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                            sig["status"] = exit_status
                            sig["is_open"] = False
                            sig["exit_timestamp"] = int(datetime.now().timestamp())
                            if current_price > 0:
                                sig["exit_price"] = current_price
                            self._save_signal_history()
                            self._add_ki_log_entry("EXIT", f"Position geschlossen: {exit_status} @ {current_price:.2f}")
                            break

                    # Remove stop lines
                    self.chart_widget.remove_stop_line("initial_stop")
                    self.chart_widget.remove_stop_line("trailing_stop")
                    self._add_ki_log_entry("CHART", "Stop-Linien entfernt (Position geschlossen)")

            except Exception as e:
                logger.error(f"Error updating chart for decision: {e}")

    def _on_bot_log(self, log_type: str, message: str) -> None:
        """Handle bot log event."""
        self._add_ki_log_entry(log_type.upper(), message)

    def _on_bot_order(self, order: Any) -> None:
        """Handle bot order event."""
        order_id = getattr(order, 'order_id', getattr(order, 'id', 'unknown'))
        side = order.side.value if hasattr(order, 'side') else 'unknown'
        quantity = getattr(order, 'quantity', 0)
        fill_price = getattr(order, 'fill_price', 0)
        status = order.status.value if hasattr(order, 'status') else 'pending'
        symbol = getattr(order, 'symbol', 'unknown')

        logger.info(f"Bot order: {order_id} {side} {quantity} @ {fill_price:.4f} ({status})")

        # For Paper Trading: simulate fill immediately if order is pending
        # This creates the position in the bot controller
        if status == "pending" and self._bot_controller:
            from src.core.tradingbot.config import TradingEnvironment
            if self._bot_controller.config.bot.environment == TradingEnvironment.PAPER:
                # Get fill price from signal entry price or order
                if fill_price <= 0:
                    for sig in reversed(self._signal_history):
                        if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                            fill_price = sig.get("price", 0)
                            break

                if fill_price > 0 and quantity > 0:
                    # Simulate the fill in the bot controller
                    self._bot_controller.simulate_fill(fill_price, quantity, order_id)
                    status = "filled"
                    self._add_ki_log_entry(
                        "PAPER",
                        f"Paper-Fill simuliert: {side.upper()} {quantity:.4f} @ {fill_price:.4f}"
                    )
                    logger.info(f"Paper fill simulated: {side} {quantity} @ {fill_price:.4f}")

        self._add_ki_log_entry(
            "ORDER",
            f"{side.upper()} {quantity:.4f} {symbol} @ {fill_price:.4f} ({status})"
        )

        # Update signal history on fill
        if status == "filled":
            for sig in reversed(self._signal_history):
                if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                    if side.lower() in ("buy", "long"):
                        sig["quantity"] = quantity
                        sig["fill_price"] = fill_price
                        # Calculate invested amount
                        capital = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000
                        risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10
                        invested = capital * (risk_pct / 100)
                        sig["invested"] = invested
                        logger.info(f"Updated signal with fill: qty={quantity}, invested={invested}")
                    break

            # Add entry marker to chart
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_bot_marker'):
                try:
                    # Use fill_price or entry_price
                    entry_price = fill_price if fill_price > 0 else 0
                    for sig in reversed(self._signal_history):
                        if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                            sig_side = sig.get("side", "long")
                            label = sig.get("label", "E")
                            timestamp = sig.get("entry_timestamp", int(datetime.now().timestamp()))

                            if entry_price <= 0:
                                entry_price = sig.get("price", 0)

                            if entry_price > 0:
                                self.chart_widget.add_bot_marker(
                                    timestamp=timestamp,
                                    price=entry_price,
                                    marker_type=MarkerType.ENTRY_CONFIRMED,
                                    side=sig_side,
                                    text=label
                                )
                                self._add_ki_log_entry(
                                    "CHART",
                                    f"Entry-Marker hinzugefuegt: {label} @ {entry_price:.2f} ({sig_side})"
                                )
                            break
                except Exception as e:
                    logger.error(f"Failed to add entry marker: {e}")

            self._save_signal_history()
            self._update_signals_table()

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

    def _on_chart_candle_closed(self, previous_close: float, new_open: float) -> None:
        """Handle candle close event from chart - feed bar to bot.

        This is the main entry point for bot bar processing when using
        tick-based streaming (not event-bus MARKET_BAR).

        Args:
            previous_close: The close price of the completed candle
            new_open: The open price of the new candle
        """
        import asyncio

        # First, call the TR% lock handler if it exists
        if hasattr(self, '_on_candle_closed'):
            try:
                self._on_candle_closed(previous_close, new_open)
            except Exception as e:
                logger.error(f"Error in TR% lock handler: {e}")

        # Feed the closed candle to the bot if running
        if not hasattr(self, '_bot_controller') or self._bot_controller is None:
            return

        if not self._bot_controller._running:
            return

        # Build bar data from chart's last closed candle
        if not hasattr(self, 'chart_widget'):
            return

        try:
            # Get the last closed candle data from chart widget
            bar_data = None

            # Try to get candle data from streaming mixin attributes
            if hasattr(self.chart_widget, '_current_candle_time'):
                # The streaming mixin tracks the current candle
                # When candle_closed fires, the previous candle data is:
                chart = self.chart_widget
                candle_time = getattr(chart, '_current_candle_time', 0) - 60  # Previous minute
                candle_open = getattr(chart, '_current_candle_open', previous_close)
                candle_high = getattr(chart, '_current_candle_high', previous_close)
                candle_low = getattr(chart, '_current_candle_low', previous_close)
                candle_volume = getattr(chart, '_current_candle_volume', 0)

                bar_data = {
                    'timestamp': datetime.fromtimestamp(candle_time),
                    'time': candle_time,
                    'open': float(candle_open),
                    'high': float(candle_high),
                    'low': float(candle_low),
                    'close': float(previous_close),
                    'volume': float(candle_volume),
                }

            # Fallback: get from chart's DataFrame if available
            if bar_data is None and hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                try:
                    df = self.chart_widget.data
                    if len(df) > 0:
                        last_row = df.iloc[-1]
                        bar_data = {
                            'timestamp': df.index[-1] if hasattr(df.index[-1], 'timestamp') else datetime.now(),
                            'open': float(last_row.get('open', previous_close)),
                            'high': float(last_row.get('high', previous_close)),
                            'low': float(last_row.get('low', previous_close)),
                            'close': float(previous_close),
                            'volume': float(last_row.get('volume', 0)),
                        }
                except Exception as e:
                    logger.warning(f"Could not get bar data from chart DataFrame: {e}")

            if bar_data:
                logger.info(f"Feeding candle to bot: O:{bar_data['open']:.2f} H:{bar_data['high']:.2f} L:{bar_data['low']:.2f} C:{bar_data['close']:.2f}")
                # Use asyncio.ensure_future for qasync compatibility
                asyncio.ensure_future(self._bot_controller.on_bar(bar_data))
            else:
                logger.warning("Could not build bar data for bot - no candle data available")

        except Exception as e:
            logger.error(f"Error feeding candle to bot: {e}")
