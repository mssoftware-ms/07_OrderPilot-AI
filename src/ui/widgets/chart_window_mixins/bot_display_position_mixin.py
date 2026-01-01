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
            side = position.side.value.upper() if hasattr(position.side, 'value') else str(position.side)
            self.position_side_label.setText(side)
            if side == "LONG":
                self.position_side_label.setStyleSheet("font-weight: bold; color: #26a69a;")
            elif side == "SHORT":
                self.position_side_label.setStyleSheet("font-weight: bold; color: #ef5350;")

            # Strategy from bot controller or signal history
            strategy = getattr(self._bot_controller, 'strategy_name', "Manual")
            if hasattr(self, 'position_strategy_label'):
                self.position_strategy_label.setText(strategy)

            self.position_entry_label.setText(f"{position.entry_price:.4f}")

            self.position_size_label.setText(f"{position.quantity:.4f}")

            # Invested amount from signal history
            invested = 0
            for sig in reversed(self._signal_history):
                if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                    invested = sig.get("invested", 0)
                    break
            if invested > 0:
                self.position_invested_label.setText(f"{invested:.0f}")
            else:
                capital = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000
                risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10
                invested = capital * (risk_pct / 100)
                self.position_invested_label.setText(f"~{invested:.0f}")

            # Stop price
            trailing = getattr(position, 'trailing', None)
            if trailing:
                stop = trailing.current_stop_price
                self.position_stop_label.setText(f"{stop:.4f}")

            # Current price and P&L - get from _last_features or chart data
            current = 0.0
            if self._bot_controller._last_features:
                current = self._bot_controller._last_features.close

            # Fallback: get current price from chart widget data
            if current <= 0 and hasattr(self, 'chart_widget'):
                if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                    try:
                        current = float(self.chart_widget.data['close'].iloc[-1])
                    except Exception:
                        pass

            if current > 0:
                self.position_current_label.setText(f"{current:.4f}")

                # Calculate P&L
                if side == "LONG":
                    pnl_pct = ((current - position.entry_price) / position.entry_price) * 100
                else:
                    pnl_pct = ((position.entry_price - current) / position.entry_price) * 100

                pnl_currency = invested * (pnl_pct / 100)

                color = "#26a69a" if pnl_pct >= 0 else "#ef5350"
                sign = "+" if pnl_pct >= 0 else ""
                self.position_pnl_label.setText(f"{sign}{pnl_pct:.2f}% ({sign}{pnl_currency:.2f})")
                self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")

            # Bars held
            bars = position.bars_held
            self.position_bars_held_label.setText(str(bars))

            # Update right column (Score, TR Kurs, Derivative)
            self._update_position_right_column()

        else:
            # No position in bot_controller - check signal_history for open positions
            open_signal = None
            for sig in reversed(self._signal_history):
                if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                    open_signal = sig
                    break

            if open_signal:
                # Show position from signal history
                side = open_signal.get("side", "unknown").upper()
                self.position_side_label.setText(side)
                if side == "LONG":
                    self.position_side_label.setStyleSheet("font-weight: bold; color: #26a69a;")
                elif side == "SHORT":
                    self.position_side_label.setStyleSheet("font-weight: bold; color: #ef5350;")

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

                # Get current price from chart
                current = 0.0
                if hasattr(self, 'chart_widget'):
                    if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                        try:
                            current = float(self.chart_widget.data['close'].iloc[-1])
                        except Exception:
                            pass

                if current > 0:
                    self.position_current_label.setText(f"{current:.4f}")
                    open_signal["current_price"] = current

                    # Calculate P&L
                    if entry_price > 0:
                        if side == "LONG":
                            pnl_pct = ((current - entry_price) / entry_price) * 100
                        else:
                            pnl_pct = ((entry_price - current) / entry_price) * 100

                        pnl_currency = invested * (pnl_pct / 100) if invested > 0 else 0
                        open_signal["pnl_percent"] = pnl_pct
                        open_signal["pnl_currency"] = pnl_currency

                        color = "#26a69a" if pnl_pct >= 0 else "#ef5350"
                        sign = "+" if pnl_pct >= 0 else ""
                        self.position_pnl_label.setText(f"{sign}{pnl_pct:.2f}% ({sign}{pnl_currency:.2f})")
                        self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")
                    else:
                        self.position_pnl_label.setText("-")
                else:
                    self.position_current_label.setText("-")
                    self.position_pnl_label.setText("-")

                self.position_bars_held_label.setText("-")  # Not tracked without bot position

                # Update right column for signal from history
                self._update_position_right_column()
            else:
                # Truly flat - no position anywhere
                self.position_side_label.setText("FLAT")
                self.position_side_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
                if hasattr(self, 'position_strategy_label'):
                    self.position_strategy_label.setText("-")
                self.position_entry_label.setText("-")

                self.position_size_label.setText("-")
                self.position_invested_label.setText("-")
                self.position_stop_label.setText("-")
                self.position_current_label.setText("-")
                self.position_pnl_label.setText("-")
                self.position_bars_held_label.setText("-")

                # Reset right column
                self._reset_position_right_column()

        # Update signals P&L
        self._update_signals_pnl()
    def _update_daily_strategy_panel(self) -> None:
        """Update Daily Strategy tab from current selection state."""
        if not hasattr(self, "active_strategy_label"):
            return
        if not self._bot_controller:
            return

        selection = None
        if hasattr(self._bot_controller, "get_strategy_selection"):
            selection = self._bot_controller.get_strategy_selection()

        # Active strategy label
        active_name = None
        if selection and selection.selected_strategy:
            active_name = selection.selected_strategy
            if selection.fallback_used:
                active_name = f"{active_name} (fallback)"
        elif getattr(self._bot_controller, "active_strategy", None):
            strategy = self._bot_controller.active_strategy
            active_name = strategy.name if strategy else None

        if active_name:
            self.active_strategy_label.setText(active_name)
        else:
            self.active_strategy_label.setText("None")

        # Regime + volatility
        if selection:
            if hasattr(self, "regime_label"):
                self.regime_label.setText(selection.regime.value)
            if hasattr(self, "volatility_label"):
                self.volatility_label.setText(selection.volatility.value)
        else:
            regime = getattr(self._bot_controller, "regime", None)
            if regime:
                if hasattr(self, "regime_label"):
                    self.regime_label.setText(regime.regime.value)
                if hasattr(self, "volatility_label"):
                    self.volatility_label.setText(regime.volatility.value)

        # Selection timing
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

        # Strategy scores table
        if hasattr(self._bot_controller, "get_strategy_score_rows"):
            rows = self._bot_controller.get_strategy_score_rows()
            if rows:
                self.update_strategy_scores(rows)
            elif hasattr(self, "strategy_scores_table"):
                self.strategy_scores_table.setRowCount(0)

        # Walk-forward results
        if hasattr(self, "wf_results_text"):
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

        if hasattr(self, "position_strategy_label"):
            self.position_strategy_label.setText(signal.get("strategy", "-"))

        entry_price = signal.get("price", 0.0)
        if hasattr(self, "position_entry_label"):
            self.position_entry_label.setText(f"{entry_price:.4f}" if entry_price > 0 else "-")

        quantity = signal.get("quantity", 0.0)
        if hasattr(self, "position_size_label"):
            self.position_size_label.setText(f"{quantity:.4f}" if quantity > 0 else "-")

        invested = signal.get("invested", 0.0)
        if hasattr(self, "position_invested_label"):
            self.position_invested_label.setText(f"{invested:.0f}" if invested > 0 else "-")

        stop_price = signal.get("trailing_stop_price", signal.get("stop_price", 0.0))
        if hasattr(self, "position_stop_label"):
            self.position_stop_label.setText(f"{stop_price:.4f}" if stop_price > 0 else "-")

        status = signal.get("status", "")
        is_closed = status.startswith("CLOSED") or status in ("SL", "TR", "MACD", "RSI", "Sell")
        current_price = signal.get("current_price", 0.0)
        if is_closed:
            current_price = signal.get("exit_price", current_price)
        if current_price <= 0 and entry_price > 0:
            current_price = entry_price

        if hasattr(self, "position_current_label"):
            self.position_current_label.setText(f"{current_price:.4f}" if current_price > 0 else "-")

        # P&L
        pnl_percent = signal.get("pnl_percent")
        pnl_currency = signal.get("pnl_currency")
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

        if hasattr(self, "position_pnl_label"):
            if pnl_percent is None:
                self.position_pnl_label.setText("-")
                self.position_pnl_label.setStyleSheet("")
            else:
                sign = "+" if pnl_percent >= 0 else ""
                color = "#26a69a" if pnl_percent >= 0 else "#ef5350"
                self.position_pnl_label.setText(f"{sign}{pnl_percent:.2f}% ({sign}{pnl_currency:.2f})")
                self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {color};")

        bars_held = signal.get("bars_held")
        if hasattr(self, "position_bars_held_label"):
            self.position_bars_held_label.setText(str(bars_held) if bars_held is not None else "-")

        self._update_position_right_column_from_signal(signal)
    def _update_position_right_column_from_signal(self, signal: dict) -> None:
        """Update right column (Score, TR, Derivative) from a signal dict."""
        score = signal.get("score")
        if hasattr(self, "position_score_label"):
            if score is None:
                self.position_score_label.setText("-")
            else:
                self.position_score_label.setText(f"{score * 100:.0f}")

        tr_price = signal.get("trailing_stop_price", 0.0)
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

        current_price = signal.get("current_price", 0.0)
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
    def _update_position_right_column(self) -> None:
        """Update the right column of Current Position groupbox (Score, TR, Derivative)."""
        # Find the active signal
        open_signal = None
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                open_signal = sig
                break

        if not open_signal:
            self._reset_position_right_column()
            return

        # Update Score
        score = open_signal.get("score", 0)
        if hasattr(self, "position_score_label"):
            self.position_score_label.setText(f"{score * 100:.0f}")

        # Update TR Kurs
        tr_price = open_signal.get("trailing_stop_price", 0)
        tr_active = open_signal.get("tr_active", False)
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

        # Update Derivative section
        deriv = open_signal.get("derivative")
        if deriv:
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

            # Calculate derivative P&L
            current_price = open_signal.get("current_price", 0)
            if current_price > 0 and hasattr(self, "_calculate_derivative_pnl_for_signal"):
                deriv_pnl = self._calculate_derivative_pnl_for_signal(open_signal, current_price)
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
        else:
            self._reset_derivative_labels()
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
