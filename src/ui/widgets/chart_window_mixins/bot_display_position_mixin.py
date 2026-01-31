from __future__ import annotations



class BotDisplayPositionMixin:
    """BotDisplayPositionMixin extracted from BotDisplayManagerMixin."""
    def _update_bot_status(self, status: str, color: str) -> None:
        """Update bot status indicator."""
        if hasattr(self, 'bot_status_label'):
            self.bot_status_label.setText(f"Status: {status}")
            self.bot_status_label.setStyleSheet(
                f"font-weight: bold; color: {color}; font-size: 14px;"
            )
        # Mirror to Signals tab log status (Issue #23)
        if hasattr(self, '_set_bot_run_status_label'):
            self._set_bot_run_status_label(status.upper() == "RUNNING")

    def _ensure_bot_running_status(self) -> None:
        """Keep bot UI/status in RUNNING state after a position closes (Issue #6)."""
        bot_controller = getattr(self, "_bot_controller", None)
        if not bot_controller:
            return
        # If something set the running flag to False, restore it so the bot continues
        if hasattr(bot_controller, "_running") and not bot_controller._running:
            bot_controller._running = True
        self._update_bot_status("RUNNING", "#26a69a")
        if hasattr(self, "_ensure_bot_update_timer"):
            self._ensure_bot_update_timer()

    def _update_bot_display(self) -> None:
        """Update bot display with current state."""
        if self._bot_controller:
            self._update_daily_strategy_panel()

        # If a signals row is selected, reflect that in Current Position
        if self._update_current_position_from_selection():
            self._update_signals_pnl()
            return

        if not self._bot_controller:
            # Even without bot_controller, update P&L from chart data for restored positions
            self._update_signals_pnl()
            return

        # Update position display
        position = self._bot_controller.position
        if position:
            self._update_from_bot_position(position)
        else:
            open_signal = self._find_open_signal()
            if open_signal:
                self._update_from_signal_history(open_signal)
            else:
                self._reset_position_display()

        # Update signals P&L
        self._update_signals_pnl()

    def _update_from_bot_position(self, position) -> None:
        side = position.side.value.upper() if hasattr(position.side, 'value') else str(position.side)
        self._set_position_side(side)

        strategy = getattr(self._bot_controller, 'strategy_name', "Manual")
        if hasattr(self, 'position_strategy_label'):
            self.position_strategy_label.setText(strategy)

        self.position_entry_label.setText(f"{position.entry_price:.4f}")
        self.position_size_label.setText(f"{position.quantity:.4f}")

        invested = self._get_invested_from_history()
        if invested > 0:
            self.position_invested_label.setText(f"{invested:.0f}")
        else:
            capital = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000
            risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10
            invested = capital * (risk_pct / 100)
            self.position_invested_label.setText(f"~{invested:.0f}")

        trailing = getattr(position, 'trailing', None)
        if trailing:
            stop = trailing.current_stop_price
            self.position_stop_label.setText(f"{stop:.4f}")

        current = self._get_live_current_price()
        if current > 0:
            self.position_current_label.setText(f"{current:.4f}")
            pnl_pct, pnl_currency = self._calculate_simple_pnl(position.entry_price, current, invested, side)
            self._set_pnl_display(pnl_pct, pnl_currency)
        else:
            self.position_current_label.setText("")
            self.position_pnl_label.setText("-")

        self.position_bars_held_label.setText(str(position.bars_held))
        self._update_position_right_column()

    def _update_from_signal_history(self, open_signal: dict) -> None:
        side = open_signal.get("side", "unknown").upper()
        self._set_position_side(side)

        if hasattr(self, 'position_strategy_label'):
            self.position_strategy_label.setText(open_signal.get("strategy", "-"))

        entry_price = open_signal.get("price", 0)
        self.position_entry_label.setText(f"{entry_price:.4f}" if entry_price > 0 else "-")

        quantity = open_signal.get("quantity", 0)
        self.position_size_label.setText(f"{quantity:.4f}" if quantity > 0 else "-")

        invested = open_signal.get("invested", 0)
        self.position_invested_label.setText(f"{invested:.0f}" if invested > 0 else "-")

        stop_price = open_signal.get("trailing_stop_price", open_signal.get("stop_price", 0))
        self.position_stop_label.setText(f"{stop_price:.4f}" if stop_price > 0 else "-")

        current = self._get_live_current_price()
        if current > 0:
            self.position_current_label.setText(f"{current:.4f}")
            open_signal["current_price"] = current
            if entry_price > 0:
                # Issue #10: _calculate_pnl returns raw P&L (without leverage)
                # Store in raw fields, don't overwrite leveraged values in pnl_percent/pnl_currency
                pnl_pct, pnl_currency = self._calculate_simple_pnl(entry_price, current, invested, side)
                open_signal["pnl_percent_raw"] = pnl_pct
                open_signal["pnl_currency_raw"] = pnl_currency
                self._set_pnl_display(pnl_pct, pnl_currency)
            else:
                self.position_pnl_label.setText("-")
        else:
            self.position_current_label.setText("")
            self.position_pnl_label.setText("-")

        self.position_bars_held_label.setText("-")
        self._update_position_right_column()

    def _reset_position_display(self) -> None:
        self.position_side_label.setText("FLAT")
        self.position_side_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
        if hasattr(self, 'position_strategy_label'):
            self.position_strategy_label.setText("-")
        self.position_entry_label.setText("-")
        self.position_size_label.setText("-")
        self.position_invested_label.setText("-")
        self.position_stop_label.setText("-")
        self.position_current_label.setText("")
        self.position_pnl_label.setText("-")
        self.position_bars_held_label.setText("-")
        self._reset_position_right_column()
        # Reset SL/TP Progress Bar
        if hasattr(self, 'sltp_progress_bar'):
            self.sltp_progress_bar.reset_bar()

    def _set_position_side(self, side: str) -> None:
        self.position_side_label.setText(side)
        if side == "LONG":
            self.position_side_label.setStyleSheet("font-weight: bold; color: #26a69a;")
        elif side == "SHORT":
            self.position_side_label.setStyleSheet("font-weight: bold; color: #ef5350;")

    def _get_invested_from_history(self) -> float:
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                return sig.get("invested", 0)
        return 0.0

    def _find_open_signal(self) -> dict | None:
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                return sig
        return None

    def _get_current_price(self, from_bot: bool = True) -> float:
        """Get current market price.

        Prioritizes Live Streaming Price (from Chart/StreamingMixin) over Bitunix Trading Widget price.
        This prevents 'Price Jumping' where the P&L timer fetches stale polling data (e.g. 81k)
        while the Tick Signal pushes live data (e.g. 79k), causing flickering and false SL triggers.

        Priority:
        1. Live Tick Price (from _on_tick_price_updated) or Chart Stream
        2. Bitunix Trading Widget (Polling/API)
        3. Bot Controller (Last Closed Bar)
        4. Chart Data (DataFrame)
        """
        # Priority 1: Live tick price (from streaming mixin via BotPanelsMixin._on_tick_price_updated)
        if hasattr(self, '_last_tick_price') and self._last_tick_price > 0:
            return self._last_tick_price

        # Priority 2: Chart widget's streaming price (Direct access to StreamingMixin)
        if hasattr(self, 'chart_widget'):
            if hasattr(self.chart_widget, '_last_price') and self.chart_widget._last_price > 0:
                return float(self.chart_widget._last_price)

        # Priority 3: Bitunix Trading API widget's price (might be polling/stale)
        if hasattr(self, 'bitunix_trading_api_widget') and self.bitunix_trading_api_widget:
            if hasattr(self.bitunix_trading_api_widget, '_last_price'):
                price = self.bitunix_trading_api_widget._last_price
                if price > 0:
                    return float(price)

        # No live price available - log warning for active positions
        has_active_position = any(
            sig.get("is_open", False) and sig.get("status") == "ENTERED"
            for sig in getattr(self, '_signal_history', [])
        )
        if has_active_position and not (hasattr(self, '_last_tick_price') and self._last_tick_price > 0):
             # Only warn if we really have NO price source
            pass # Logger warning removed to reduce noise as we have fallbacks below

        # 4. Bot controller features (usually last closed bar) - only if no active position
        current = 0.0
        if from_bot and self._bot_controller and self._bot_controller._last_features:
            current = self._bot_controller._last_features.close

        # 5. Chart data fallback (last row of DataFrame) - only if no active position
        if current <= 0 and hasattr(self, 'chart_widget'):
            if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                try:
                    current = float(self.chart_widget.data['close'].iloc[-1])
                except Exception:
                    pass
        return current

<<<<<<< HEAD
    def _get_live_current_price(self) -> float:
        """Return live price only (no historical fallback)."""
        if hasattr(self, '_last_tick_price') and self._last_tick_price > 0:
            return self._last_tick_price

        if hasattr(self, 'chart_widget'):
            if hasattr(self.chart_widget, '_last_price') and self.chart_widget._last_price > 0:
                return float(self.chart_widget._last_price)

        return 0.0

    def _calculate_pnl(self, entry_price: float, current: float, invested: float, side: str) -> tuple[float, float]:
=======
    def _calculate_simple_pnl(self, entry_price: float, current: float, invested: float, side: str) -> tuple[float, float]:
        """Simple PnL calculation for position display (without leverage/fees)."""
>>>>>>> bd51450 (vor aufteilen livestream kaputt)
        if side == "LONG":
            pnl_pct = ((current - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current) / entry_price) * 100
        pnl_currency = invested * (pnl_pct / 100) if invested > 0 else 0
        return pnl_pct, pnl_currency

    def _set_pnl_display(self, pnl_pct: float, pnl_currency: float) -> None:
        color = "#26a69a" if pnl_pct >= 0 else "#ef5350"
        sign = "+" if pnl_pct >= 0 else ""
        self.position_pnl_label.setText(f"{sign}{pnl_pct:.2f}% ({sign}{pnl_currency:.2f})")
        self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")
    def _update_daily_strategy_panel(self) -> None:
        """Update Daily Strategy tab from current selection state."""
        if not hasattr(self, "active_strategy_label"):
            return
        if not self._bot_controller:
            return

        selection = self._get_strategy_selection()
        self._set_active_strategy_label(selection)
        self._update_strategy_indicators_display()  # Issue #2
        self._update_regime_labels(selection)
        self._update_selection_timing_labels(selection)
        self._refresh_strategy_scores_data()
        self._update_walk_forward_panel(selection)

    def _get_strategy_selection(self):
        if hasattr(self._bot_controller, "get_strategy_selection"):
            return self._bot_controller.get_strategy_selection()
        return None

    def _set_active_strategy_label(self, selection) -> None:
        active_name = None
        if selection and selection.selected_strategy:
            active_name = selection.selected_strategy
            if selection.fallback_used:
                active_name = f"{active_name} (fallback)"
        elif getattr(self._bot_controller, "active_strategy", None):
            strategy = self._bot_controller.active_strategy
            active_name = strategy.name if strategy else None

        self.active_strategy_label.setText(active_name if active_name else "None")

    def _update_strategy_indicators_display(self) -> None:
        """Issue #2: Update the indicators display for active strategy.

        Gets the active strategy from selection/controller and displays
        the indicators defined in the strategy catalog's entry_rules.
        """
        if not hasattr(self, 'update_strategy_indicators'):
            return

        # Get active strategy name
        strategy_name = None
        selection = self._get_strategy_selection()
        if selection and selection.selected_strategy:
            strategy_name = selection.selected_strategy
        elif hasattr(self._bot_controller, 'active_strategy') and self._bot_controller.active_strategy:
            strategy_name = self._bot_controller.active_strategy.name

        self.update_strategy_indicators(strategy_name)

    def _update_regime_labels(self, selection) -> None:
        if selection:
            if hasattr(self, "regime_label"):
                self.regime_label.setText(selection.regime.value)
            if hasattr(self, "volatility_label"):
                self.volatility_label.setText(selection.volatility.value)
            return

        regime = getattr(self._bot_controller, "regime", None)
        if regime:
            if hasattr(self, "regime_label"):
                self.regime_label.setText(regime.regime.value)
            if hasattr(self, "volatility_label"):
                self.volatility_label.setText(regime.volatility.value)

    def _update_selection_timing_labels(self, selection) -> None:
        if hasattr(self, "selection_time_label"):
            if selection and selection.selection_date:
                self.selection_time_label.setText(selection.selection_date.strftime("%Y-%m-%d %H:%M"))
            else:
                self.selection_time_label.setText("-")

        if hasattr(self, "next_selection_label"):
            if selection and selection.locked_until:
                self.next_selection_label.setText(selection.locked_until.strftime("%Y-%m-%d %H:%M"))
            else:
                self.next_selection_label.setText("-")

    def _refresh_strategy_scores_data(self) -> None:
        if hasattr(self._bot_controller, "get_strategy_score_rows"):
            rows = self._bot_controller.get_strategy_score_rows()
            if rows:
                self.update_strategy_scores(rows)
            elif hasattr(self, "strategy_scores_table"):
                self.strategy_scores_table.setRowCount(0)

    def _update_walk_forward_panel(self, selection) -> None:
        if not hasattr(self, "wf_results_text"):
            return
        if selection and selection.wf_result:
            config = None
            if hasattr(self._bot_controller, "get_walk_forward_config"):
                try:
                    config = self._bot_controller.get_walk_forward_config()
                except Exception:
                    config = None
            is_pf = selection.wf_result.get("in_sample_pf", 0) or 0
            oos_pf = selection.wf_result.get("oos_pf", 0) or 0
            degradation = 0.0
            if is_pf > 0:
                degradation = max(0.0, 1 - (oos_pf / is_pf))
            results = {
                "training_days": getattr(config, "training_window_days", "N/A") if config else "N/A",
                "test_days": getattr(config, "test_window_days", "N/A") if config else "N/A",
                "is_pf": is_pf,
                "oos_pf": oos_pf,
                "degradation": degradation,
                "passed": selection.wf_result.get("robustness_score", 0) >= 0.5,
            }
            self.update_walk_forward_results(results)
        else:
            self.wf_results_text.setText("")
    def _render_current_position_from_signal(self, signal: dict) -> None:
        """Render Current Position panel from a signal dict."""
        side_upper = self._set_signal_side_label(signal)
        entry_price = signal.get("price", 0.0)
        quantity = signal.get("quantity", 0.0)
        invested = signal.get("invested", 0.0)
        stop_price = signal.get("trailing_stop_price", signal.get("stop_price", 0.0))

        self._set_signal_basic_fields(signal, entry_price, quantity, invested, stop_price)

        current_price = self._get_live_current_price()
        if hasattr(self, "position_current_label"):
            self.position_current_label.setText(f"{current_price:.4f}" if current_price > 0 else "")

        pnl_percent, pnl_currency = self._resolve_signal_pnl(
            signal, side_upper, entry_price, current_price, invested, quantity
        )
        self._set_signal_pnl_label(pnl_percent, pnl_currency)

        bars_held = signal.get("bars_held")
        if hasattr(self, "position_bars_held_label"):
            self.position_bars_held_label.setText(str(bars_held) if bars_held is not None else "-")

        self._update_position_right_column_from_signal(signal)

    def _set_signal_side_label(self, signal: dict) -> str:
        side = signal.get("side", "")
        side_upper = side.upper() if side else "FLAT"
        if hasattr(self, "position_side_label"):
            self.position_side_label.setText(side_upper)
            if side_upper == "LONG":
                color = "#26a69a"
            elif side_upper == "SHORT":
                color = "#ef5350"
            else:
                color = "#9e9e9e"
            self.position_side_label.setStyleSheet(f"font-weight: bold; color: {color};")
        return side_upper

    def _set_signal_basic_fields(
        self,
        signal: dict,
        entry_price: float,
        quantity: float,
        invested: float,
        stop_price: float,
    ) -> None:
        if hasattr(self, "position_strategy_label"):
            self.position_strategy_label.setText(signal.get("strategy", "-"))
        if hasattr(self, "position_entry_label"):
            self.position_entry_label.setText(f"{entry_price:.4f}" if entry_price > 0 else "-")
        if hasattr(self, "position_size_label"):
            self.position_size_label.setText(f"{quantity:.4f}" if quantity > 0 else "-")
        if hasattr(self, "position_invested_label"):
            self.position_invested_label.setText(f"{invested:.0f}" if invested > 0 else "-")
        if hasattr(self, "position_stop_label"):
            self.position_stop_label.setText(f"{stop_price:.4f}" if stop_price > 0 else "-")

    def _resolve_signal_current_price(self, signal: dict, entry_price: float) -> float:
        status = signal.get("status", "")
        is_closed = status.startswith("CLOSED") or status in ("SL", "TR", "MACD", "RSI", "Sell")
        current_price = signal.get("current_price", 0.0)
        if is_closed:
            current_price = signal.get("exit_price", current_price)
        if current_price <= 0 and entry_price > 0:
            current_price = entry_price
        return current_price

    def _resolve_signal_pnl(
        self,
        signal: dict,
        side_upper: str,
        entry_price: float,
        current_price: float,
        invested: float,
        quantity: float,
    ) -> tuple[float | None, float | None]:
        # Issue #10: Use RAW P&L values (WITHOUT leverage) for Current Position display
        # pnl_percent_raw/pnl_currency_raw are stored without leverage,
        # pnl_percent/pnl_currency include leverage for the Trading Table
        pnl_percent = signal.get("pnl_percent_raw")
        pnl_currency = signal.get("pnl_currency_raw")

        # Fallback: calculate if raw values not available
        if pnl_percent is None and entry_price > 0 and current_price > 0:
            if side_upper == "SHORT":
                pnl_percent = ((entry_price - current_price) / entry_price) * 100
            else:
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
        if pnl_currency is None and pnl_percent is not None:
            if invested > 0:
                pnl_currency = invested * (pnl_percent / 100)
            elif quantity > 0 and current_price > 0:
                pnl_currency = quantity * (current_price - entry_price) if side_upper == "LONG" else quantity * (entry_price - current_price)
            else:
                pnl_currency = 0.0
        return pnl_percent, pnl_currency

    def _set_signal_pnl_label(self, pnl_percent: float | None, pnl_currency: float | None) -> None:
        if hasattr(self, "position_pnl_label"):
            if pnl_percent is None:
                self.position_pnl_label.setText("-")
                self.position_pnl_label.setStyleSheet("")
            else:
                sign = "+" if pnl_percent >= 0 else ""
                color = "#26a69a" if pnl_percent >= 0 else "#ef5350"
                self.position_pnl_label.setText(f"{sign}{pnl_percent:.2f}% ({sign}{pnl_currency:.2f})")
                self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")
    def _update_position_right_column_from_signal(self, signal: dict) -> None:
        """Update right column (Score, TR, Derivative) from a signal dict."""
        self._update_score_label_from_signal(signal)
        self._update_trailing_stop_label(signal)
        self._update_derivative_section(signal)

    def _update_score_label_from_signal(self, signal: dict) -> None:
        score = signal.get("score")
        if hasattr(self, "position_score_label"):
            if score is None:
                self.position_score_label.setText("-")
            else:
                self.position_score_label.setText(f"{score * 100:.0f}")
    def _update_position_right_column(self) -> None:
        """Update the right column of Current Position groupbox (Score, TR, Derivative)."""
        open_signal = self._get_open_signal()

        if not open_signal:
            self._reset_position_right_column()
            return

        # Update Score
        self._update_score_label(open_signal)

        # Update TR Kurs
        self._update_trailing_stop_label(open_signal)

        # Update Derivative section
        self._update_derivative_section(open_signal)

    def _get_open_signal(self) -> dict | None:
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                return sig
        return None

    def _update_score_label(self, signal: dict) -> None:
        score = signal.get("score", 0)
        if hasattr(self, "position_score_label"):
            self.position_score_label.setText(f"{score * 100:.0f}")

    def _update_trailing_stop_label(self, signal: dict) -> None:
        tr_price = signal.get("trailing_stop_price", 0)
        tr_active = signal.get("tr_active", False)
        if hasattr(self, "position_tr_price_label"):
            if tr_price > 0:
                if tr_active:
                    self.position_tr_price_label.setText(f"{tr_price:.2f}")
                    self.position_tr_price_label.setStyleSheet("color: #ff9800;")
                else:
                    self.position_tr_price_label.setText(f"{tr_price:.2f} (inaktiv)")
                    self.position_tr_price_label.setStyleSheet("color: #888888;")
            else:
                self.position_tr_price_label.setText("-")
                self.position_tr_price_label.setStyleSheet("")

    def _update_derivative_section(self, signal: dict) -> None:
        deriv = signal.get("derivative")
        if not deriv:
            self._reset_derivative_labels()
            return

        if hasattr(self, "deriv_wkn_label"):
            self.deriv_wkn_label.setText(deriv.get("wkn", "-"))
        if hasattr(self, "deriv_leverage_label"):
            lev = deriv.get("leverage", 0)
            self.deriv_leverage_label.setText(f"{lev:.1f}x" if lev else "-")
        if hasattr(self, "deriv_spread_label"):
            spread = deriv.get("spread_pct", 0)
            self.deriv_spread_label.setText(f"{spread:.2f}%" if spread else "-")
        if hasattr(self, "deriv_ask_label"):
            ask = deriv.get("ask", 0)
            self.deriv_ask_label.setText(f"{ask:.2f}" if ask else "-")

        current_price = signal.get("current_price", 0)
        if current_price > 0 and hasattr(self, "_calculate_derivative_pnl_for_signal"):
            deriv_pnl = self._calculate_derivative_pnl_for_signal(signal, current_price)
            if deriv_pnl and hasattr(self, "deriv_pnl_label"):
                sign = "+" if deriv_pnl["pnl_pct"] >= 0 else ""
                color = "#26a69a" if deriv_pnl["pnl_pct"] >= 0 else "#ef5350"
                self.deriv_pnl_label.setText(
                    f"{sign}{deriv_pnl['pnl_pct']:.2f}% ({sign}{deriv_pnl['pnl_eur']:.2f})"
                )
                self.deriv_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")
            elif hasattr(self, "deriv_pnl_label"):
                self.deriv_pnl_label.setText("-")
                self.deriv_pnl_label.setStyleSheet("")
        elif hasattr(self, "deriv_pnl_label"):
            self.deriv_pnl_label.setText("-")
            self.deriv_pnl_label.setStyleSheet("")
    def _reset_position_right_column(self) -> None:
        """Reset all labels in the right column of Current Position groupbox."""
        if hasattr(self, "position_score_label"):
            self.position_score_label.setText("-")
        if hasattr(self, "position_tr_price_label"):
            self.position_tr_price_label.setText("-")
            self.position_tr_price_label.setStyleSheet("")
        self._reset_derivative_labels()
    def _reset_derivative_labels(self) -> None:
        """Reset derivative labels to default state."""
        deriv_labels = ["deriv_wkn_label", "deriv_leverage_label", "deriv_spread_label",
                        "deriv_ask_label", "deriv_pnl_label"]
        for label_name in deriv_labels:
            label = getattr(self, label_name, None)
            if label:
                label.setText("-")
                label.setStyleSheet("")
