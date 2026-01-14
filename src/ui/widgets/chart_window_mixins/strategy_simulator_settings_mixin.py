from __future__ import annotations

import logging
import pandas as pd
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class StrategySimulatorSettingsMixin:
    """Settings collection from UI widgets"""

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
            Dictionary with all bot settings for simulation.
        """
        settings = self._get_default_bot_settings()
        self._read_basic_settings(settings)
        self._read_trailing_settings(settings)
        self._read_fee_settings(settings)
        self._read_leverage_settings(settings)
        self._read_exit_trigger_settings(settings)
        self._log_bot_settings(settings)
        return settings

    def _get_default_bot_settings(self) -> dict:
        """Get default bot settings."""
        return {
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

    def _read_widget_value(self, widget_attr: str, method: str = "value"):
        """Helper to safely read widget value.

        Args:
            widget_attr: Widget attribute name (e.g., "bot_capital_spin")
            method: Method to call on widget (default: "value")

        Returns:
            Widget value or None if widget doesn't exist or error occurs
        """
        if not hasattr(self, widget_attr):
            return None

        try:
            widget = getattr(self, widget_attr)
            return getattr(widget, method)()
        except Exception:
            return None

    def _read_basic_settings(self, settings: dict) -> None:
        """Read basic bot settings from widgets."""
        # Capital
        value = self._read_widget_value("bot_capital_spin")
        if value is not None:
            settings["capital"] = value

        # Risk per Trade (convert to fraction: 50% -> 0.5)
        value = self._read_widget_value("risk_per_trade_spin")
        if value is not None:
            settings["risk_per_trade_pct"] = value / 100.0

        # Initial Stop Loss (convert to fraction: 1.5% -> 0.015)
        value = self._read_widget_value("initial_sl_spin")
        if value is not None:
            settings["initial_sl_pct"] = value / 100.0

        # Trade Direction
        value = self._read_widget_value("trade_direction_combo", "currentText")
        if value is not None:
            settings["trade_direction"] = value

    def _read_trailing_settings(self, settings: dict) -> None:
        """Read trailing stop settings from widgets."""
        # Trailing Mode
        value = self._read_widget_value("trailing_mode_combo", "currentText")
        if value is not None:
            settings["trailing_mode"] = value

        # Trailing Distance
        value = self._read_widget_value("trailing_distance_spin")
        if value is not None:
            settings["trailing_pct_distance"] = value

        # Trailing Activation
        value = self._read_widget_value("trailing_activation_spin")
        if value is not None:
            settings["trailing_activation_pct"] = value

        # ATR Multiplier
        value = self._read_widget_value("atr_multiplier_spin")
        if value is not None:
            settings["trailing_atr_multiplier"] = value

        # ATR Trending
        value = self._read_widget_value("atr_trending_spin")
        if value is not None:
            settings["atr_trending_mult"] = value

        # ATR Ranging
        value = self._read_widget_value("atr_ranging_spin")
        if value is not None:
            settings["atr_ranging_mult"] = value

        # Regime Adaptive
        value = self._read_widget_value("regime_adaptive_cb", "isChecked")
        if value is not None:
            settings["regime_adaptive"] = value

    def _read_fee_settings(self, settings: dict) -> None:
        """Read fee settings from widgets (convert to fraction)."""
        # Maker Fee (convert: 0.02% -> 0.0002)
        value = self._read_widget_value("futures_maker_fee_spin")
        if value is not None:
            settings["maker_fee_pct"] = value / 100.0

        # Taker Fee (convert: 0.06% -> 0.0006)
        value = self._read_widget_value("futures_taker_fee_spin")
        if value is not None:
            settings["taker_fee_pct"] = value / 100.0

    def _read_leverage_settings(self, settings: dict) -> None:
        """Read leverage settings from widgets."""
        value = self._read_widget_value("leverage_slider")
        if value is not None:
            settings["leverage"] = float(value)

    def _read_exit_trigger_settings(self, settings: dict) -> None:
        """Read SL/TP ATR settings from trigger_exit_settings widget."""
        if not hasattr(self, "trigger_exit_settings") or self.trigger_exit_settings is None:
            return

        try:
            widget = self.trigger_exit_settings
            settings["sl_atr_multiplier"] = widget._sl_atr_mult.value()
            settings["tp_atr_multiplier"] = widget._tp_atr_mult.value()
            settings["trailing_enabled"] = widget._trailing_enabled.isChecked()
        except Exception as e:
            logger.warning(f"Could not read trigger_exit_settings: {e}")

    def _log_bot_settings(self, settings: dict) -> None:
        """Log bot settings with mode-specific info."""
        trailing_info = self._format_trailing_info(settings)

        logger.info(
            f"Bot-Tab settings: capital=€{settings['capital']:.0f}, "
            f"risk={settings['risk_per_trade_pct']*100:.1f}%, "
            f"SL={settings['initial_sl_pct']*100:.2f}%, "
            f"direction={settings['trade_direction']}, "
            f"trailing={trailing_info}, "
            f"fees=M{settings['maker_fee_pct']*100:.3f}%/T{settings['taker_fee_pct']*100:.3f}%"
        )

    def _format_trailing_info(self, settings: dict) -> str:
        """Format trailing stop info for logging."""
        trailing_mode = settings["trailing_mode"]

        if trailing_mode == "PCT":
            return f"PCT({settings['trailing_pct_distance']:.1f}%)"
        elif trailing_mode == "ATR":
            if settings["regime_adaptive"]:
                return f"ATR(trend={settings['atr_trending_mult']:.2f}x, range={settings['atr_ranging_mult']:.2f}x)"
            else:
                return f"ATR({settings['trailing_atr_multiplier']:.2f}x)"
        else:  # SWING
            return "SWING(BB 20/2)"

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

