from __future__ import annotations

import logging

import pandas as pd
from PyQt6.QtWidgets import QMessageBox
from .strategy_simulator_worker import SimulationWorker

logger = logging.getLogger(__name__)

class StrategySimulatorRunMixin:
    """StrategySimulatorRunMixin extracted from StrategySimulatorMixin."""
    def _on_run_simulation(self) -> None:
        """Run simulation with current settings.

        Uses the selected time range from the UI to filter data.
        Options: visible chart range, fixed time periods, or all data.
        """
        # Get chart data
        if not hasattr(self, "chart_widget"):
            QMessageBox.warning(self, "Error", "No chart widget available")
            return

        # First check if we have data at all
        full_data = self._get_full_chart_dataframe()
        if full_data is None or (hasattr(full_data, "empty") and full_data.empty):
            QMessageBox.warning(
                self, "Error", "No chart data available. Load a chart first."
            )
            return

        # Get selected time range
        time_range = self._get_selected_time_range()

        if time_range == "visible":
            # Use visible chart range (async callback)
            if hasattr(self.chart_widget, "get_visible_range"):
                self.chart_widget.get_visible_range(
                    lambda visible_range: self._start_simulation_with_visible_range(
                        full_data, visible_range
                    )
                )
            else:
                # Fallback: use all data if visible range not supported
                logger.info("Chart does not support visible range - using all data")
                self._start_simulation_with_data(full_data)
        elif time_range == "all":
            # Use all available data
            logger.info(f"Using all data: {len(full_data)} bars")
            self._start_simulation_with_data(full_data)
        else:
            # Use fixed time range (hours)
            filtered_data = self._filter_data_to_time_range(full_data, time_range)
            if filtered_data is None or filtered_data.empty:
                QMessageBox.warning(
                    self, "Error",
                    f"Not enough data for selected time range. "
                    f"Available: {len(full_data)} bars"
                )
                return
            self._start_simulation_with_data(filtered_data)

    def _filter_data_to_time_range(
        self, full_data: pd.DataFrame, hours: int
    ) -> pd.DataFrame:
        """Filter DataFrame to the last N hours of data.

        Args:
            full_data: Full chart DataFrame
            hours: Number of hours to include

        Returns:
            Filtered DataFrame containing the last N hours
        """
        # Calculate number of bars needed
        bars_needed = self._calculate_bars_for_time_range(hours)

        # Take the last N bars
        if len(full_data) <= bars_needed:
            logger.info(
                f"Data has only {len(full_data)} bars, "
                f"using all (requested {bars_needed} for {hours}h)"
            )
            return full_data

        filtered_data = full_data.iloc[-bars_needed:].copy()
        logger.info(
            f"Filtered data to last {hours}h: {len(filtered_data)} bars "
            f"(from {len(full_data)} total)"
        )
        return filtered_data

    def _start_simulation_with_visible_range(
        self, full_data: pd.DataFrame, visible_range: dict | None
    ) -> None:
        """Start simulation after getting visible range.

        Args:
            full_data: Full chart DataFrame
            visible_range: Dict with 'from' and 'to' logical indices, or None
        """
        # Filter data to visible range
        data = self._filter_data_to_visible_range(full_data, visible_range)

        if data is None or data.empty:
            QMessageBox.warning(
                self, "Error", "No data in visible range. Adjust chart zoom."
            )
            return

        self._start_simulation_with_data(data)

    def _filter_data_to_visible_range(
        self, full_data: pd.DataFrame, visible_range: dict | None
    ) -> pd.DataFrame:
        """Filter DataFrame to only include data in the visible chart range.

        Args:
            full_data: Full chart DataFrame
            visible_range: Dict with 'from' and 'to' logical indices

        Returns:
            Filtered DataFrame containing only visible data
        """
        if visible_range is None:
            logger.info("No visible range available - using all data")
            return full_data

        # Get from/to indices from visible range
        from_idx = visible_range.get("from")
        to_idx = visible_range.get("to")

        if from_idx is None or to_idx is None:
            logger.warning("Invalid visible range - using all data")
            return full_data

        # Convert to integers and clamp to valid range
        from_idx = max(0, int(from_idx))
        to_idx = min(len(full_data), int(to_idx) + 1)  # +1 because iloc is exclusive

        if from_idx >= to_idx:
            logger.warning(f"Invalid range [{from_idx}:{to_idx}] - using all data")
            return full_data

        # Filter using iloc (position-based indexing)
        filtered_data = full_data.iloc[from_idx:to_idx].copy()

        logger.info(
            f"Filtered data to visible range: [{from_idx}:{to_idx}] "
            f"({len(filtered_data)} of {len(full_data)} bars)"
        )

        return filtered_data

    def _start_simulation_with_data(self, data: pd.DataFrame) -> None:
        """Start the simulation with the given data.

        Args:
            data: DataFrame to use for simulation (already filtered to time range)
        """
        # Get symbol from chart_widget or ChartWindow
        symbol = self._get_simulation_symbol()

        # Get current parameters
        (
            params,
            strategy_name,
            entry_only,
            objective_metric,
        ) = self._collect_simulation_params()
        self._prepare_simulation_run(entry_only)

        # Determine mode
        mode = self._resolve_simulation_mode()
        self._current_simulation_mode = mode
        if entry_only and mode == "manual" and self.simulator_opt_trials_spin.value() > 1:
            self._append_simulator_log(
                "Entry-Only: Manual ignores trials. Switch to Grid/Bayesian to use trials."
            )

        # Disable UI
        self._set_simulation_ui_state()

        # Get time range info for logging
        time_range_name = self._get_time_range_display_name()

        self._log_simulation_start(
            mode,
            strategy_name,
            entry_only,
            objective_metric,
            time_range_name,
            data,
            symbol,
        )

        # Get ALL Bot-Tab settings for simulation
        bot_settings = self._get_all_bot_settings()

        # Log trailing settings to simulation log (mode-specific)
        trailing_mode = bot_settings["trailing_mode"]
        if trailing_mode == "PCT":
            trailing_log = f"PCT ({bot_settings['trailing_pct_distance']:.1f}%)"
        elif trailing_mode == "ATR":
            if bot_settings["regime_adaptive"]:
                trailing_log = (
                    f"ATR Regime-Adaptiv "
                    f"(Trend={bot_settings['atr_trending_mult']:.2f}x, "
                    f"Range={bot_settings['atr_ranging_mult']:.2f}x)"
                )
            else:
                trailing_log = f"ATR ({bot_settings['trailing_atr_multiplier']:.2f}x)"
        else:
            trailing_log = "SWING (BB 20/2)"

        if bot_settings["trailing_enabled"]:
            self._append_simulator_log(
                f"Trailing Mode: {trailing_log} | "
                f"Aktivierung: {bot_settings['trailing_activation_pct']:.1f}%"
            )
        else:
            self._append_simulator_log("Trailing Stop: DEAKTIVIERT")

        # Log SL/TP settings
        if bot_settings["sl_atr_multiplier"] > 0 or bot_settings["tp_atr_multiplier"] > 0:
            self._append_simulator_log(
                f"SL/TP: SL={bot_settings['sl_atr_multiplier']:.1f}x ATR, "
                f"TP={bot_settings['tp_atr_multiplier']:.1f}x ATR"
            )

        # Check if auto-strategy mode is enabled
        auto_strategy = self._is_auto_strategy_enabled()
        if auto_strategy:
            # In auto-strategy mode, use "all" to test all strategies
            strategy_name = "all"
            self._append_simulator_log(
                "Auto-Strategy: Alle Strategien werden getestet, beste wird ausgewählt"
            )

        # Create worker with all Bot-Tab settings
        self._current_worker = self._create_simulation_worker(
            data=data,
            symbol=symbol,
            strategy_name=strategy_name,
            parameters=params,
            mode=mode,
            opt_trials=self.simulator_opt_trials_spin.value(),
            objective_metric=objective_metric,
            entry_only=entry_only,
            # Auto-strategy mode
            auto_strategy=auto_strategy,
            # Capital and position sizing
            initial_capital=bot_settings["capital"],
            position_size_pct=bot_settings["risk_per_trade_pct"],
            # ATR-based SL/TP from Bot-Tab settings
            sl_atr_multiplier=bot_settings["sl_atr_multiplier"],
            tp_atr_multiplier=bot_settings["tp_atr_multiplier"],
            atr_period=14,  # Standard ATR period
            # Trailing Stop from Bot-Tab settings
            trailing_stop_enabled=bot_settings["trailing_enabled"],
            trailing_stop_atr_multiplier=bot_settings["trailing_atr_multiplier"],
            trailing_stop_mode=bot_settings["trailing_mode"],
            trailing_pct_distance=bot_settings["trailing_pct_distance"],
            trailing_activation_pct=bot_settings["trailing_activation_pct"],
            # Regime-adaptive trailing
            regime_adaptive=bot_settings["regime_adaptive"],
            atr_trending_mult=bot_settings["atr_trending_mult"],
            atr_ranging_mult=bot_settings["atr_ranging_mult"],
            # Trading fees
            maker_fee_pct=bot_settings["maker_fee_pct"],
            taker_fee_pct=bot_settings["taker_fee_pct"],
            # Trade direction filter
            trade_direction=bot_settings["trade_direction"],
            # Leverage
            leverage=bot_settings["leverage"],
        )
        self._wire_simulation_worker(self._current_worker)
        self._current_worker.start()

    def _get_trigger_exit_settings(self) -> tuple[float, float, bool, float, str]:
        """Get SL/TP and Trailing Stop settings from Bot-Tab widgets.

        Returns:
            Tuple of (sl_atr_mult, tp_atr_mult, trailing_enabled, trailing_distance, trailing_mode)
        """
        # Default values if settings not available
        sl_atr_mult = 0.0  # 0 = use strategy defaults
        tp_atr_mult = 0.0
        trailing_enabled = False
        trailing_distance = 1.5
        trailing_mode = "ATR"

        # Try to get settings from trigger_exit_settings widget
        if hasattr(self, "trigger_exit_settings") and self.trigger_exit_settings is not None:
            try:
                widget = self.trigger_exit_settings
                # Note: Widget attributes have underscore prefix
                sl_atr_mult = widget._sl_atr_mult.value()
                tp_atr_mult = widget._tp_atr_mult.value()
                trailing_enabled = widget._trailing_enabled.isChecked()
                # trailing_distance comes from Bot-Tab, not trigger_exit_settings
            except Exception as e:
                logger.warning(f"Could not read trigger_exit_settings: {e}")

        # Try to get trailing mode from trailing_mode_combo (in Bot-Tab settings)
        if hasattr(self, "trailing_mode_combo") and self.trailing_mode_combo is not None:
            try:
                trailing_mode = self.trailing_mode_combo.currentText()
            except Exception as e:
                logger.warning(f"Could not read trailing_mode_combo: {e}")

        logger.info(
            f"Using Bot-Tab settings: SL={sl_atr_mult}x ATR, TP={tp_atr_mult}x ATR, "
            f"Trailing={'ON' if trailing_enabled else 'OFF'} ({trailing_mode}, {trailing_distance}x)"
        )

        return sl_atr_mult, tp_atr_mult, trailing_enabled, trailing_distance, trailing_mode

    def _get_all_bot_settings(self) -> dict:
        """Get ALL Bot-Tab settings for simulation.

        Reads all configurable settings from the Bot-Tab widgets.

        Returns:
            Dictionary with all bot settings for simulation:
            - capital: Initial capital
            - risk_per_trade_pct: Position size as % of capital
            - initial_sl_pct: Initial stop loss %
            - trade_direction: AUTO, BOTH, LONG_ONLY, SHORT_ONLY
            - trailing_mode: PCT, ATR, SWING
            - trailing_pct_distance: Distance for PCT mode
            - trailing_activation_pct: Activation threshold
            - trailing_atr_multiplier: ATR multiplier for trailing
            - atr_trending_mult: ATR mult for trending markets
            - atr_ranging_mult: ATR mult for ranging markets
            - regime_adaptive: Enable regime-adaptive trailing
            - maker_fee_pct: Maker fee (0.0002 = 0.02%)
            - taker_fee_pct: Taker fee (0.0006 = 0.06%)
            - leverage: Leverage multiplier
            - sl_atr_multiplier: SL in ATR multiples
            - tp_atr_multiplier: TP in ATR multiples
        """
        settings = {
            # Default values
            "capital": 1000.0,
            "risk_per_trade_pct": 1.0,  # 100% = full position
            "initial_sl_pct": 0.02,  # 2%
            "trade_direction": "BOTH",
            "trailing_mode": "ATR",
            "trailing_pct_distance": 1.0,
            "trailing_activation_pct": 5.0,
            "trailing_atr_multiplier": 1.5,
            "atr_trending_mult": 1.2,
            "atr_ranging_mult": 2.0,
            "regime_adaptive": True,
            "maker_fee_pct": 0.0002,  # 0.02%
            "taker_fee_pct": 0.0006,  # 0.06%
            "leverage": 1.0,
            "sl_atr_multiplier": 0.0,
            "tp_atr_multiplier": 0.0,
            "trailing_enabled": False,
        }

        # Capital
        if hasattr(self, "bot_capital_spin"):
            try:
                settings["capital"] = self.bot_capital_spin.value()
            except Exception:
                pass

        # Risk per Trade (convert to fraction: 50% -> 0.5)
        if hasattr(self, "risk_per_trade_spin"):
            try:
                settings["risk_per_trade_pct"] = self.risk_per_trade_spin.value() / 100.0
            except Exception:
                pass

        # Initial Stop Loss (convert to fraction: 1.5% -> 0.015)
        if hasattr(self, "initial_sl_spin"):
            try:
                settings["initial_sl_pct"] = self.initial_sl_spin.value() / 100.0
            except Exception:
                pass

        # Trade Direction
        if hasattr(self, "trade_direction_combo"):
            try:
                settings["trade_direction"] = self.trade_direction_combo.currentText()
            except Exception:
                pass

        # Trailing Mode
        if hasattr(self, "trailing_mode_combo"):
            try:
                settings["trailing_mode"] = self.trailing_mode_combo.currentText()
            except Exception:
                pass

        # Trailing Settings
        if hasattr(self, "trailing_distance_spin"):
            try:
                settings["trailing_pct_distance"] = self.trailing_distance_spin.value()
            except Exception:
                pass

        if hasattr(self, "trailing_activation_spin"):
            try:
                settings["trailing_activation_pct"] = self.trailing_activation_spin.value()
            except Exception:
                pass

        if hasattr(self, "atr_multiplier_spin"):
            try:
                settings["trailing_atr_multiplier"] = self.atr_multiplier_spin.value()
            except Exception:
                pass

        if hasattr(self, "atr_trending_spin"):
            try:
                settings["atr_trending_mult"] = self.atr_trending_spin.value()
            except Exception:
                pass

        if hasattr(self, "atr_ranging_spin"):
            try:
                settings["atr_ranging_mult"] = self.atr_ranging_spin.value()
            except Exception:
                pass

        if hasattr(self, "regime_adaptive_cb"):
            try:
                settings["regime_adaptive"] = self.regime_adaptive_cb.isChecked()
            except Exception:
                pass

        # Fees (convert to fraction: 0.02% -> 0.0002)
        if hasattr(self, "futures_maker_fee_spin"):
            try:
                settings["maker_fee_pct"] = self.futures_maker_fee_spin.value() / 100.0
            except Exception:
                pass

        if hasattr(self, "futures_taker_fee_spin"):
            try:
                settings["taker_fee_pct"] = self.futures_taker_fee_spin.value() / 100.0
            except Exception:
                pass

        # Leverage
        if hasattr(self, "leverage_slider"):
            try:
                settings["leverage"] = float(self.leverage_slider.value())
            except Exception:
                pass

        # SL/TP ATR settings from trigger_exit_settings
        if hasattr(self, "trigger_exit_settings") and self.trigger_exit_settings is not None:
            try:
                widget = self.trigger_exit_settings
                # Note: Widget attributes have underscore prefix
                settings["sl_atr_multiplier"] = widget._sl_atr_mult.value()
                settings["tp_atr_multiplier"] = widget._tp_atr_mult.value()
                settings["trailing_enabled"] = widget._trailing_enabled.isChecked()
            except Exception as e:
                logger.warning(f"Could not read trigger_exit_settings: {e}")

        # Log settings with mode-specific info
        trailing_mode = settings["trailing_mode"]
        if trailing_mode == "PCT":
            trailing_info = f"PCT({settings['trailing_pct_distance']:.1f}%)"
        elif trailing_mode == "ATR":
            if settings["regime_adaptive"]:
                trailing_info = f"ATR(trend={settings['atr_trending_mult']:.2f}x, range={settings['atr_ranging_mult']:.2f}x)"
            else:
                trailing_info = f"ATR({settings['trailing_atr_multiplier']:.2f}x)"
        else:  # SWING
            trailing_info = "SWING(BB 20/2)"

        logger.info(
            f"Bot-Tab settings: capital=€{settings['capital']:.0f}, "
            f"risk={settings['risk_per_trade_pct']*100:.1f}%, "
            f"SL={settings['initial_sl_pct']*100:.2f}%, "
            f"direction={settings['trade_direction']}, "
            f"trailing={trailing_info}, "
            f"fees=M{settings['maker_fee_pct']*100:.3f}%/T{settings['taker_fee_pct']*100:.3f}%"
        )

        return settings

    def _get_chart_dataframe(self):
        """Get chart dataframe - for backward compatibility.

        Note: This returns all data. Use _get_full_chart_dataframe() explicitly
        when you need all data, or use _on_run_simulation() which handles
        visible range filtering automatically.
        """
        return self._get_full_chart_dataframe()

    def _get_full_chart_dataframe(self):
        """Get the full chart DataFrame without visible range filtering."""
        if hasattr(self.chart_widget, "data") and self.chart_widget.data is not None:
            return self.chart_widget.data
        if hasattr(self.chart_widget, "get_dataframe"):
            return self.chart_widget.get_dataframe()
        if hasattr(self.chart_widget, "_df"):
            return self.chart_widget._df
        return None

    def _get_simulation_symbol(self) -> str:
        symbol = getattr(self, "symbol", "UNKNOWN")
        if hasattr(self.chart_widget, "current_symbol") and self.chart_widget.current_symbol:
            return self.chart_widget.current_symbol
        if hasattr(self.chart_widget, "symbol"):
            return self.chart_widget.symbol
        return symbol

    def _collect_simulation_params(self):
        params = self._get_simulator_parameters()
        strategy_name = self._get_simulator_strategy_name()
        entry_only = self._is_entry_only_selected()
        objective_metric = "entry_score" if entry_only else self._get_selected_objective_metric()
        self._current_objective_metric = objective_metric
        self._current_entry_only = entry_only
        return (
            params,
            strategy_name,
            entry_only,
            objective_metric,
        )

    def _prepare_simulation_run(self, entry_only: bool) -> None:
        if hasattr(self, "simulator_log_view"):
            self.simulator_log_view.clear()
        if self._is_all_strategy_selected():
            self._all_run_active = True
            self._all_run_restore_index = self.simulator_strategy_combo.currentIndex()
            self.simulator_params_group.setEnabled(False)
            self.simulator_strategy_combo.setEnabled(False)

    def _resolve_simulation_mode(self) -> str:
        mode_id = self.simulator_opt_mode_group.checkedId()
        mode_map = {0: "manual", 1: "grid", 2: "bayesian"}
        return mode_map.get(mode_id, "manual")

    def _set_simulation_ui_state(self) -> None:
        self.simulator_run_btn.setEnabled(False)
        self.simulator_stop_btn.setEnabled(True)
        self.simulator_progress.setVisible(True)
        self.simulator_progress.setValue(0)
        self.simulator_status_label.setText("Running simulation...")

    def _log_simulation_start(
        self,
        mode: str,
        strategy_name: str,
        entry_only: bool,
        objective_metric: str,
        time_range_name: str,
        data,
        symbol: str,
    ) -> None:
        objective_label = self._get_objective_label(objective_metric)
        entry_label = "entry-only" if entry_only else "full"
        side_label = "long+short" if entry_only else "long"
        trials = self.simulator_opt_trials_spin.value()
        timeframe = self._get_chart_timeframe()

        self._log_simulator_to_ki(
            "START",
            f"Running {mode} simulation: {strategy_name}, "
            f"mode: {entry_label} ({side_label}), objective: {objective_label}, "
            f"Zeitraum: {time_range_name}, Timeframe: {timeframe}, "
            f"trials: {trials}, "
            f"data rows: {len(data)}, symbol: {symbol}"
        )
        self._append_simulator_log(
            f"START | {mode} | {strategy_name} | {entry_label} ({side_label}) | "
            f"{objective_label} | {time_range_name} ({timeframe}) | "
            f"trials={trials}"
        )

    def _create_simulation_worker(self, **kwargs) -> SimulationWorker:
        return SimulationWorker(**kwargs)

    def _wire_simulation_worker(self, worker: SimulationWorker) -> None:
        worker.finished.connect(self._on_simulation_finished)
        worker.partial_result.connect(self._on_simulation_partial_result)
        worker.progress.connect(self._on_simulation_progress)
        worker.strategy_started.connect(self._on_simulation_strategy_started)
        worker.error.connect(self._on_simulation_error)
    def _on_stop_simulation(self) -> None:
        """Stop running simulation."""
        if self._current_worker:
            # Signal cancellation; keep reference so thread can exit cleanly
            self._current_worker.cancel()
            self.simulator_status_label.setText("Stopping...")
    def _on_simulation_progress(self, current: int, total: int, best: float) -> None:
        """Update progress bar."""
        pct = int((current / total) * 100) if total > 0 else 0
        self.simulator_progress.setValue(pct)
        strategy_prefix = ""
        if self._current_sim_strategy_name:
            index = self._current_sim_strategy_index or 1
            total_strategies = self._current_sim_strategy_total or 1
            display_name = self._get_strategy_display_name(self._current_sim_strategy_name)
            if self._current_entry_only and self._current_sim_strategy_side:
                side_label = self._current_sim_strategy_side.upper()
                strategy_prefix = f"{index}/{total_strategies} {display_name} {side_label} | "
            else:
                strategy_prefix = f"{index}/{total_strategies} {display_name} | "
        objective_label = self._get_objective_label(self._current_objective_metric or "score")
        self.simulator_status_label.setText(
            f"{strategy_prefix}Trial {current}/{total} | Best {objective_label}: {best:.4f}"
        )
        log_prefix = strategy_prefix.replace(" | ", " ").strip()
        self._append_simulator_log(
            f"{log_prefix}Trial {current}/{total} | Best {objective_label}: {best:.4f}".strip()
        )
    def _on_simulation_finished(self, result) -> None:
        """Handle simulation completion."""
        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)
        self._finalize_all_run()

        if isinstance(result, dict) and result.get("batch_done"):
            count = result.get("count", 0)
            label = "runs" if self._current_entry_only else "strategies"
            status_msg = f"Completed batch run: {count} {label}"
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)
            self._append_simulator_log(status_msg)
            self._append_simulator_log(status_msg)
        elif isinstance(result, list):
            for item in result:
                self._handle_simulation_result(item)

            label = "runs" if self._current_entry_only else "strategies"
            status_msg = f"Completed batch run: {len(result)} {label}"
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)
        else:
            self._handle_simulation_result(result)

        self.simulator_export_btn.setEnabled(bool(self._simulation_results))
        # Ensure thread is fully stopped before dropping reference
        self._cleanup_simulation_worker(wait_ms=200)
    def _handle_simulation_result(self, result) -> None:
        """Handle a single simulation or optimization result."""
        from src.core.simulator import SimulationResult, OptimizationRun

        if isinstance(result, SimulationResult):
            self._handle_simulation_run_result(result)

        elif isinstance(result, OptimizationRun):
            self._handle_optimization_result(result)

    def _handle_simulation_run_result(self, result) -> None:
        self._simulation_results.append(result)
        objective_label = self._resolve_result_objective_label(result)
        self._add_result_to_table(result, objective_label=objective_label)
        status_msg = self._build_simulation_status(result)
        self.simulator_status_label.setText(status_msg)
        self._log_simulator_to_ki("OK", status_msg)

    def _resolve_result_objective_label(self, result) -> str:
        if result.entry_only:
            return self._get_objective_label("entry_score")
        if self._current_simulation_mode == "manual":
            return "Manual"
        return self._get_objective_label(self._current_objective_metric or "score")

    def _build_simulation_status(self, result) -> str:
        if result.entry_only:
            entry_score = result.entry_score or 0.0
            return f"Entry-Only: {result.entry_count} entries, Score: {entry_score:.1f}"
        return f"Completed: {result.total_trades} trades, P&L: {result.total_pnl:.2f}"

    def _handle_optimization_result(self, result) -> None:
        self._last_optimization_run = result
        self._log_optimization_errors(result)

        if result.total_trials == 0:
            self._handle_no_trials(result)
            return

        seen_params = self._add_best_result(result)
        self._add_top_trials(result, seen_params)
        status_msg = self._build_optimization_status(result)
        self.simulator_status_label.setText(status_msg)
        self._log_simulator_to_ki("OK", status_msg)
        self._append_simulator_log(status_msg)

    def _log_optimization_errors(self, result) -> None:
        if not result.errors:
            return
        for error in result.errors[:5]:
            self._log_simulator_to_ki("ERROR", error)
        if len(result.errors) > 5:
            self._log_simulator_to_ki(
                "ERROR", f"... and {len(result.errors) - 5} more errors"
            )

    def _handle_no_trials(self, result) -> None:
        error_msg = "No optimization trials completed successfully."
        if result.errors:
            error_msg += f" First error: {result.errors[0]}"
        self.simulator_status_label.setText(f"Error: {error_msg}")
        self._log_simulator_to_ki("ERROR", error_msg)
        QMessageBox.warning(
            self,
            "Optimization Warning",
            "No trials completed.\n\nCheck KI Logs for error details.",
        )

    def _add_best_result(self, result) -> set[tuple]:
        seen_params: set[tuple] = set()
        if not result.best_result:
            return seen_params
        self._simulation_results.append(result.best_result)
        objective_label = self._get_objective_label(result.objective_metric)
        self._add_result_to_table(
            result.best_result,
            objective_label=objective_label,
            entry_side=result.entry_side,
        )
        best_side = (
            result.best_result.entry_side
            if getattr(result.best_result, "entry_only", False)
            else None
        )
        seen_params.add(
            self._make_param_fingerprint(
                result.strategy_name,
                result.best_result.parameters,
                best_side,
            )
        )
        return seen_params

    def _add_top_trials(self, result, seen_params: set[tuple]) -> None:
        objective_label = self._get_objective_label(result.objective_metric)
        for trial in result.get_top_n_trials(10):
            trial_side = trial.entry_side if result.entry_only else None
            fingerprint = self._make_param_fingerprint(
                result.strategy_name, trial.parameters, trial_side
            )
            if fingerprint in seen_params:
                continue
            seen_params.add(fingerprint)
            self._add_trial_to_table(
                trial,
                result.strategy_name,
                objective_label=objective_label,
                entry_side=result.entry_side,
            )

    def _build_optimization_status(self, result) -> str:
        status_msg = (
            f"Optimization complete: {result.total_trials} trials, "
            f"Best score: {result.best_score:.4f}"
        )
        if result.entry_only:
            status_msg += f" ({result.entry_side.upper()})"
        if result.errors:
            status_msg += f" ({len(result.errors)} failed)"
        return status_msg
    def _on_simulation_error(self, error_msg: str) -> None:
        """Handle simulation error."""
        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)
        self.simulator_status_label.setText(f"Error: {error_msg}")
        self._append_simulator_log(f"ERROR: {error_msg}")
        self._finalize_all_run()

        # Log to KI Logs
        self._log_simulator_to_ki("ERROR", f"Simulation failed: {error_msg}")

        QMessageBox.critical(self, "Simulation Error", error_msg)
        self._cleanup_simulation_worker(wait_ms=200)
    def _on_simulation_partial_result(self, result) -> None:
        """Handle partial results for batch runs."""
        self._handle_simulation_result(result)
    def _on_simulation_strategy_started(
        self,
        index: int,
        total: int,
        strategy_name: str,
        side: str,
    ) -> None:
        """Update UI when a strategy run starts."""
        self._current_sim_strategy_name = strategy_name
        self._current_sim_strategy_index = index
        self._current_sim_strategy_total = total
        self._current_sim_strategy_side = side
        if self._all_run_active:
            combo_index = self._get_strategy_index_by_name(strategy_name)
            if combo_index is not None:
                self.simulator_strategy_combo.setCurrentIndex(combo_index)
            try:
                from src.core.simulator import StrategyName, get_default_parameters, load_strategy_params

                strategy_enum = StrategyName(strategy_name)
                saved_params = load_strategy_params(strategy_name)
                seed_params = saved_params or get_default_parameters(strategy_enum)
                self._apply_params_to_widgets(seed_params)
                seed_source = "saved" if saved_params else "default"
                self._append_simulator_log(
                    f"Seed params: {seed_source} ({strategy_name})"
                )
            except Exception:
                pass
        display_name = self._get_strategy_display_name(strategy_name)
        mode = self._current_simulation_mode or "manual"
        side_label = ""
        if self._current_entry_only and side:
            side_label = f" {side.upper()}"
        status_msg = f"Running {index}/{total}: {display_name}{side_label} ({mode})"
        self.simulator_status_label.setText(status_msg)
        self._log_simulator_to_ki("INFO", status_msg)
        self._append_simulator_log(status_msg)
    def _cleanup_simulation_worker(self, wait_ms: int = 0, cancel: bool = False) -> None:
        """Safely stop and dispose the simulation worker thread.

        Args:
            wait_ms: How long to wait for the thread to finish. 0 = no wait.
            cancel: Whether to request cancellation first.
        """
        worker = self._current_worker
        if not worker:
            return

        if cancel:
            worker.cancel()

        finished = not worker.isRunning()
        if wait_ms and not finished:
            finished = worker.wait(wait_ms)

        if finished:
            worker.deleteLater()
            self._current_worker = None
        else:
            logger.warning("Simulation worker still running after %d ms", wait_ms)
    def _finalize_all_run(self) -> None:
        """Restore UI state after ALL batch runs."""
        if not self._all_run_active:
            return
        self._all_run_active = False
        self.simulator_strategy_combo.setEnabled(True)
        if self._all_run_restore_index is not None:
            self.simulator_strategy_combo.setCurrentIndex(self._all_run_restore_index)
        self._all_run_restore_index = None
        self.simulator_params_group.setEnabled(not self._is_all_strategy_selected())
    def _log_simulator_to_ki(self, entry_type: str, message: str) -> None:
        """Log simulator messages to KI Logs tab.

        Uses _add_ki_log_entry from BotDisplayManagerMixin if available.
        """
        prefixed_msg = f"[Simulator] {message}"
        if hasattr(self, '_add_ki_log_entry'):
            self._add_ki_log_entry(entry_type, prefixed_msg)
        else:
            # Fallback to standard logging
            logger.info(f"[{entry_type}] {prefixed_msg}")

    def _on_show_test_parameters(self) -> None:
        """Show popup dialog with all current test parameters."""
        from .strategy_simulator_params_dialog import TestParametersDialog

        # Collect all parameters from various sources
        parameters = self._collect_all_test_parameters()

        # Create and show dialog
        dialog = TestParametersDialog(self, parameters)
        dialog.exec()

    def _collect_all_test_parameters(self) -> dict:
        """Collect all test parameters from UI and settings.

        Returns:
            Dictionary with parameter categories:
            - simulation: mode, trials, strategy, entry_only, etc.
            - strategy_params: current strategy parameters
            - sl_tp: stop loss / take profit settings
            - trailing: trailing stop settings
            - data_range: symbol, timeframe, bars, etc.
            - capital: capital and position sizing settings
            - fees: trading fees settings
        """
        parameters = {}

        # Get all Bot-Tab settings
        bot_settings = self._get_all_bot_settings()

        # 1. Simulation settings
        strategy_name = self._get_simulator_strategy_name()
        mode = self._resolve_simulation_mode()
        entry_only = self._is_entry_only_selected()
        time_range = self._get_selected_time_range()
        time_range_name = self._get_time_range_display_name()
        objective = self._get_selected_objective_metric()
        trials = self.simulator_opt_trials_spin.value()
        timeframe = self._get_chart_timeframe()

        # Calculate bars for time range
        if isinstance(time_range, int):
            bars_for_range = self._calculate_bars_for_time_range(time_range)
        else:
            bars_for_range = None

        parameters["simulation"] = {
            "strategy": strategy_name,
            "mode": mode.capitalize(),
            "trials": trials,
            "objective": self._get_objective_label(objective),
            "entry_only": entry_only,
            "time_range": time_range_name,
            "timeframe": timeframe,
            "bars_for_range": bars_for_range,
        }

        # 2. Strategy parameters
        try:
            strategy_params = self._get_simulator_parameters()
            parameters["strategy_params"] = strategy_params
        except Exception as e:
            logger.warning(f"Could not get strategy params: {e}")
            parameters["strategy_params"] = {}

        # 3. SL/TP settings from Bot-Tab
        parameters["sl_tp"] = {
            "sl_atr_multiplier": bot_settings["sl_atr_multiplier"],
            "tp_atr_multiplier": bot_settings["tp_atr_multiplier"],
            "atr_period": 14,
            "initial_sl_pct": bot_settings["initial_sl_pct"] * 100,  # Convert to %
        }

        # 4. Trailing Stop settings
        parameters["trailing"] = {
            "enabled": bot_settings["trailing_enabled"],
            "mode": bot_settings["trailing_mode"],  # PCT, ATR, SWING
            "pct_distance": bot_settings["trailing_pct_distance"],
            "atr_multiplier": bot_settings["trailing_atr_multiplier"],
            "activation_pct": bot_settings["trailing_activation_pct"],
            "regime_adaptive": bot_settings["regime_adaptive"],
            "atr_trending": bot_settings["atr_trending_mult"],
            "atr_ranging": bot_settings["atr_ranging_mult"],
        }

        # 5. Capital and Position Sizing
        parameters["capital"] = {
            "initial_capital": bot_settings["capital"],
            "risk_per_trade_pct": bot_settings["risk_per_trade_pct"] * 100,  # Convert to %
            "leverage": bot_settings["leverage"],
            "trade_direction": bot_settings["trade_direction"],
        }

        # 6. Trading Fees
        parameters["fees"] = {
            "maker_fee_pct": bot_settings["maker_fee_pct"] * 100,  # Convert to %
            "taker_fee_pct": bot_settings["taker_fee_pct"] * 100,  # Convert to %
        }

        # 7. Data range info
        parameters["data_range"] = self._get_data_range_info()

        return parameters

    def _get_data_range_info(self) -> dict:
        """Get information about the data range based on selected time range.

        Returns:
            Dictionary with data range information for the SELECTED time range,
            not the full data.
        """
        info = {
            "symbol": "N/A",
            "timeframe": "N/A",
            "total_bars": 0,
            "selected_bars": 0,
            "visible_bars": "N/A",
            "start_date": None,
            "end_date": None,
        }

        # Get symbol
        info["symbol"] = self._get_simulation_symbol()

        # Get timeframe from chart
        timeframe = self._get_chart_timeframe()
        info["timeframe"] = timeframe

        # Get full data info
        full_data = self._get_full_chart_dataframe()
        if full_data is None or full_data.empty:
            return info

        info["total_bars"] = len(full_data)

        # Get selected time range from UI
        time_range = self._get_selected_time_range()

        # Calculate bars and dates based on selected time range
        if time_range == "visible":
            # For visible range, estimate based on typical chart view
            info["selected_bars"] = f"~{min(200, len(full_data))} (sichtbar)"
            info["visible_bars"] = info["selected_bars"]
            # Show last portion of data as estimate
            estimate_bars = min(200, len(full_data))
            if estimate_bars > 0:
                subset = full_data.iloc[-estimate_bars:]
                self._fill_date_range(info, subset)
        elif time_range == "all":
            # All data
            info["selected_bars"] = len(full_data)
            info["visible_bars"] = len(full_data)
            self._fill_date_range(info, full_data)
        else:
            # Fixed time range in hours
            hours = int(time_range)
            bars_needed = self._calculate_bars_for_time_range(hours)
            actual_bars = min(bars_needed, len(full_data))
            info["selected_bars"] = actual_bars
            info["visible_bars"] = actual_bars

            # Get the subset of data that will actually be used
            if actual_bars > 0:
                subset = full_data.iloc[-actual_bars:]
                self._fill_date_range(info, subset)

        return info

    def _fill_date_range(self, info: dict, data) -> None:
        """Fill start_date and end_date in info dict from DataFrame.

        Args:
            info: Dictionary to update with date information
            data: DataFrame with datetime index
        """
        try:
            if data is not None and not data.empty:
                if hasattr(data.index, "min") and hasattr(data.index, "max"):
                    start = data.index.min()
                    end = data.index.max()
                    if hasattr(start, "strftime"):
                        info["start_date"] = start.strftime("%Y-%m-%d %H:%M")
                        info["end_date"] = end.strftime("%Y-%m-%d %H:%M")
                    else:
                        info["start_date"] = str(start)
                        info["end_date"] = str(end)
        except Exception as e:
            logger.debug(f"Could not get date range: {e}")
