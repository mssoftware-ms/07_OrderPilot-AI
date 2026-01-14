from __future__ import annotations

import logging
import pandas as pd
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class StrategySimulatorExecutionMixin:
    """Simulation execution flow and worker management"""

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

    def _on_stop_simulation(self) -> None:
        """Stop running simulation."""
        if self._current_worker:
            # Signal cancellation; keep reference so thread can exit cleanly
            self._current_worker.cancel()

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

    def _create_simulation_worker(self, **kwargs) -> SimulationWorker:
        return SimulationWorker(**kwargs)

    def _wire_simulation_worker(self, worker: SimulationWorker) -> None:
        worker.finished.connect(self._on_simulation_finished)
        worker.partial_result.connect(self._on_simulation_partial_result)
        worker.progress.connect(self._on_simulation_progress)
        worker.strategy_started.connect(self._on_simulation_strategy_started)

    def _resolve_simulation_mode(self) -> str:
        mode_id = self.simulator_opt_mode_group.checkedId()
        mode_map = {0: "manual", 1: "grid", 2: "bayesian"}
        return mode_map.get(mode_id, "manual")

