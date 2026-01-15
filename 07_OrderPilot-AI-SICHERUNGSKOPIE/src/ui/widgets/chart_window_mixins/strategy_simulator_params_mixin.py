from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QDoubleSpinBox, QFileDialog, QMessageBox, QSpinBox

class StrategySimulatorParamsMixin:
    """StrategySimulatorParamsMixin extracted from StrategySimulatorMixin."""
    def _on_simulator_strategy_changed(self, index: int) -> None:
        """Update parameter widgets when strategy changes."""
        from src.core.simulator import StrategyName

        if self._is_all_strategy_selected() and not self._all_run_active:
            self.simulator_params_group.setEnabled(False)
            self._update_trials_hint(None)
            return

        self.simulator_params_group.setEnabled(True)

        # Get catalog strategy name from dropdown
        catalog_name = self.simulator_strategy_combo.currentText().strip()

        # Map catalog name to simulator StrategyName enum
        strategy = self._catalog_to_strategy_enum(catalog_name)
        self._populate_simulator_parameter_widgets(strategy)
        self._update_trials_hint(strategy)

        if self._all_run_active:
            self.simulator_params_group.setEnabled(False)

    def _catalog_to_strategy_enum(self, catalog_name: str):
        """Map catalog strategy name to simulator StrategyName enum."""
        from src.core.simulator import StrategyName

        # Mapping from catalog strategy names to simulator family enums
        catalog_to_enum = {
            "breakout_volatility": StrategyName.BREAKOUT,
            "breakout_momentum": StrategyName.BREAKOUT,
            "momentum_macd": StrategyName.MOMENTUM,
            "mean_reversion_bb": StrategyName.MEAN_REVERSION,
            "mean_reversion_rsi": StrategyName.MEAN_REVERSION,
            "trend_following_conservative": StrategyName.TREND_FOLLOWING,
            "trend_following_aggressive": StrategyName.TREND_FOLLOWING,
            "scalping_range": StrategyName.SCALPING,
            "sideways_range_bounce": StrategyName.SIDEWAYS_RANGE,
        }
        return catalog_to_enum.get(catalog_name, StrategyName.TREND_FOLLOWING)
    def _populate_simulator_parameter_widgets(self, strategy) -> None:
        """Create parameter input widgets for selected strategy."""
        from src.core.simulator import get_strategy_parameters

        # Clear existing
        while self.simulator_params_layout.count():
            item = self.simulator_params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._simulator_param_widgets.clear()

        # Get parameter definitions
        param_config = get_strategy_parameters(strategy)

        for param_def in param_config.parameters:
            if param_def.param_type == "int":
                widget = QSpinBox()
                widget.setRange(
                    param_def.min_value or 0,
                    param_def.max_value or 999999,
                )
                widget.setValue(param_def.default)
                if param_def.step:
                    widget.setSingleStep(param_def.step)
            elif param_def.param_type == "float":
                widget = QDoubleSpinBox()
                widget.setRange(
                    param_def.min_value or 0.0,
                    param_def.max_value or 999999.0,
                )
                widget.setValue(param_def.default)
                if param_def.step:
                    widget.setSingleStep(param_def.step)
                widget.setDecimals(3)
            else:
                continue  # Skip bool for now

            widget.setToolTip(param_def.description)
            self._simulator_param_widgets[param_def.name] = widget
            self.simulator_params_layout.addRow(
                f"{param_def.display_name}:", widget
            )
    def _apply_params_to_widgets(self, params: dict[str, Any]) -> None:
        """Apply parameter values to the current widgets."""
        for param_name, value in params.items():
            widget = self._simulator_param_widgets.get(param_name)
            if widget and isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)
    def _estimate_grid_combinations(self, strategy) -> int:
        """Estimate grid combinations using the same coarse steps as grid search."""
        from src.core.simulator import get_strategy_parameters

        param_config = get_strategy_parameters(strategy)
        total = 1
        for param_def in param_config.parameters:
            values = self._get_grid_values_for_param(param_def)
            total *= len(values)
        return total
    def _get_grid_values_for_param(self, param_def) -> list[Any]:
        if param_def.param_type == "bool":
            return [True, False]

        if param_def.min_value is None or param_def.max_value is None:
            return [param_def.default]

        step = param_def.step or (1 if param_def.param_type == "int" else 0.1)
        grid_step = step * 2
        values = []
        current = param_def.min_value
        while current <= param_def.max_value:
            if param_def.param_type == "int":
                values.append(int(current))
            else:
                values.append(round(current, 4))
            current += grid_step

        for value in (param_def.min_value, param_def.max_value, param_def.default):
            if value not in values:
                values.append(value)
        return sorted(values)
    def _update_trials_hint(self, strategy) -> None:
        """Update suggested trials label."""
        if strategy is None:
            self.simulator_trials_hint_label.setText(
                "Suggested Trials: per-strategy (ALL)"
            )
            self.simulator_opt_trials_spin.setToolTip(
                "Suggested Trials: per-strategy (ALL)"
            )
            return
        try:
            total = self._estimate_grid_combinations(strategy)
            suggested = min(total, 1000)
            self.simulator_trials_hint_label.setText(
                f"Suggested Trials (grid): {suggested} / {total} combos"
            )
            self.simulator_opt_trials_spin.setToolTip(
                f"Suggested (grid): {suggested} of {total} combos"
            )
        except Exception:
            self.simulator_trials_hint_label.setText("")
    def _get_selected_objective_metric(self) -> str:
        """Get selected optimization objective metric."""
        if self._is_entry_only_selected():
            return "entry_score"
        if hasattr(self, "simulator_opt_metric_combo"):
            data = self.simulator_opt_metric_combo.currentData()
            if data:
                return str(data)
        return "score"
    def _get_objective_label(self, metric: str) -> str:
        labels = {
            "score": "Score",
            "entry_score": "Entry Score",
            "total_pnl_pct": "P&L %",
            "profit_factor": "PF",
            "sharpe_ratio": "Sharpe",
            "win_rate": "Win %",
            "max_drawdown_pct": "Max DD",
        }
        return labels.get(metric, metric)
    def _is_entry_only_selected(self) -> bool:
        return bool(
            hasattr(self, "simulator_entry_only_checkbox")
            and self.simulator_entry_only_checkbox.isChecked()
        )
    def _on_entry_only_toggled(self, checked: bool) -> None:
        if not hasattr(self, "simulator_opt_metric_combo"):
            return
        if checked:
            idx = self.simulator_opt_metric_combo.findData("entry_score")
            if idx >= 0:
                self.simulator_opt_metric_combo.setCurrentIndex(idx)
            self.simulator_opt_metric_combo.setEnabled(False)
        else:
            self.simulator_opt_metric_combo.setEnabled(True)

    def _on_auto_strategy_toggled(self, checked: bool) -> None:
        """Handle Auto-Strategy checkbox toggle.

        When enabled, the strategy selector is disabled and ALL strategies
        will be evaluated for each signal to find the best one.
        """
        if not hasattr(self, "simulator_strategy_combo"):
            return

        if checked:
            # Disable strategy selection - will use all strategies
            self.simulator_strategy_combo.setEnabled(False)
            # Set status hint
            if hasattr(self, "simulator_trials_hint_label"):
                self.simulator_trials_hint_label.setText(
                    "⚠️ Auto-Strategy: Testet alle Strategien pro Signal. "
                    "Rechenzeit erhöht sich deutlich!"
                )
            self._append_simulator_log(
                "Auto-Strategy aktiviert: Alle Strategien werden pro Signal getestet"
            )
        else:
            # Re-enable strategy selection
            self.simulator_strategy_combo.setEnabled(True)
            if hasattr(self, "simulator_trials_hint_label"):
                self.simulator_trials_hint_label.setText("")

    def _is_auto_strategy_enabled(self) -> bool:
        """Check if Auto-Strategy mode is enabled."""
        if hasattr(self, "simulator_auto_strategy_checkbox"):
            return self.simulator_auto_strategy_checkbox.isChecked()
        return False

    def _get_selected_time_range(self) -> str | int:
        """Get the selected time range value.

        Returns:
            - "visible": Use visible chart range
            - "all": Use all available data
            - int: Number of hours for the time range
        """
        if not hasattr(self, "simulator_time_range_combo"):
            return "visible"
        data = self.simulator_time_range_combo.currentData()
        return data if data is not None else "visible"

    def _get_time_range_display_name(self) -> str:
        """Get the display name of the selected time range."""
        if not hasattr(self, "simulator_time_range_combo"):
            return "Chart-Ansicht"
        return self.simulator_time_range_combo.currentText()

    def _calculate_bars_for_time_range(self, hours: int) -> int:
        """Calculate number of bars for a given time range in hours.

        Uses the chart's current timeframe to determine bar count.

        Args:
            hours: Time range in hours

        Returns:
            Number of bars for the time range
        """
        # Get chart timeframe
        timeframe = self._get_chart_timeframe()

        # Convert timeframe to minutes
        timeframe_minutes = self._timeframe_to_minutes(timeframe)

        # Calculate number of bars
        total_minutes = hours * 60
        return total_minutes // timeframe_minutes

    def _get_chart_timeframe(self) -> str:
        """Get the current chart timeframe."""
        if hasattr(self, "chart_widget"):
            if hasattr(self.chart_widget, "current_timeframe"):
                return self.chart_widget.current_timeframe
            if hasattr(self.chart_widget, "timeframe"):
                return self.chart_widget.timeframe
        return "1m"  # Default fallback

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes.

        Args:
            timeframe: Timeframe string like "1m", "5m", "1h", "1D"

        Returns:
            Number of minutes per candle
        """
        tf = timeframe.lower().strip()

        # Parse numeric part
        import re
        match = re.match(r"(\d+)([mhdwM])", tf)
        if not match:
            return 1  # Default to 1 minute

        value = int(match.group(1))
        unit = match.group(2)

        multipliers = {
            "m": 1,          # minutes
            "h": 60,         # hours
            "d": 1440,       # days (24*60)
            "w": 10080,      # weeks (7*24*60)
            "M": 43200,      # months (30*24*60, approximate)
        }

        return value * multipliers.get(unit, 1)
    def _normalize_param_value(self, value: Any) -> Any:
        if isinstance(value, float):
            return round(value, 8)
        if isinstance(value, (list, tuple)):
            return tuple(self._normalize_param_value(v) for v in value)
        if isinstance(value, dict):
            return tuple(
                (k, self._normalize_param_value(v))
                for k, v in sorted(value.items())
            )
        return value
    def _make_param_fingerprint(
        self,
        strategy_name: str,
        params: dict[str, Any],
        entry_side: str | None = None,
    ) -> tuple:
        items = tuple(
            (k, self._normalize_param_value(v))
            for k, v in sorted(params.items())
        )
        return (strategy_name, entry_side or "", items)
    def _get_simulator_parameters(self) -> dict[str, Any]:
        """Get current parameter values from widgets."""
        params = {}
        for name, widget in self._simulator_param_widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                params[name] = widget.value()
        return params
    def _on_reset_simulator_params(self) -> None:
        """Reset all parameter widgets to their default values."""
        from src.core.simulator import StrategyName, get_strategy_parameters

        if self._is_all_strategy_selected():
            self.simulator_status_label.setText(
                "ALL selected: parameters are not used for batch runs"
            )
            return

        strategy_map = {
            0: StrategyName.BREAKOUT,
            1: StrategyName.MOMENTUM,
            2: StrategyName.MEAN_REVERSION,
            3: StrategyName.TREND_FOLLOWING,
            4: StrategyName.SCALPING,
            5: StrategyName.BOLLINGER_SQUEEZE,
            6: StrategyName.TREND_PULLBACK,
            7: StrategyName.OPENING_RANGE,
            8: StrategyName.REGIME_HYBRID,
            9: StrategyName.SIDEWAYS_RANGE,
        }
        strategy = strategy_map.get(
            self.simulator_strategy_combo.currentIndex(), StrategyName.BREAKOUT
        )
        param_config = get_strategy_parameters(strategy)

        for param_def in param_config.parameters:
            widget = self._simulator_param_widgets.get(param_def.name)
            if widget and isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(param_def.default)

        self.simulator_status_label.setText("Parameters reset to default")
    def _on_apply_to_active_strategy(self) -> None:
        """Apply current parameters to the active trading strategy.

        Uses the Strategy Bridge to sync simulator params with the active
        catalog strategy used by the trading bot.
        """
        from src.core.tradingbot.strategy_bridge import get_strategy_bridge

        strategy_name = self._get_simulator_strategy_name()
        params = self._get_simulator_parameters()

        # Check if bot controller is available
        bot_controller = getattr(self, '_bot_controller', None)

        if not bot_controller:
            QMessageBox.warning(
                self,
                "No Active Bot",
                "No active trading bot found.\n\n"
                "Start the trading bot first, then apply parameters.",
            )
            return

        bridge = get_strategy_bridge()

        # Get active strategy name for display
        active_strategy = None
        if hasattr(bot_controller, 'get_strategy_selection'):
            selection = bot_controller.get_strategy_selection()
            if selection and selection.selected_strategy:
                active_strategy = selection.selected_strategy

        if not active_strategy:
            QMessageBox.warning(
                self,
                "No Active Strategy",
                "No strategy is currently active in the trading bot.\n\n"
                "The bot needs to select a strategy first (Daily Strategy selection).",
            )
            return

        # Check compatibility - now uses direct catalog name comparison
        if strategy_name != active_strategy:
            reply = QMessageBox.question(
                self,
                "Strategy Mismatch",
                f"The active strategy is '{active_strategy}',\n"
                f"but you're trying to apply '{strategy_name}' parameters.\n\n"
                "This may cause unexpected behavior.\n\n"
                "Apply anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Apply parameters
        success = bridge.apply_to_active_strategy(
            bot_controller=bot_controller,
            simulator_strategy=strategy_name,
            simulator_params=params,
        )

        if success:
            self.simulator_status_label.setText(
                f"✓ Parameters applied to: {active_strategy}"
            )
            QMessageBox.information(
                self,
                "Parameters Applied",
                f"Simulator parameters successfully applied!\n\n"
                f"Simulator Strategy: {strategy_name}\n"
                f"Active Strategy: {active_strategy}\n\n"
                f"Parameters:\n" + "\n".join(f"  • {k}: {v}" for k, v in params.items()),
            )
        else:
            QMessageBox.warning(
                self,
                "Apply Failed",
                "Failed to apply parameters to active strategy.\n\n"
                "Check the logs for details.",
            )

    def _on_save_params_to_bot(self) -> None:
        """Save current parameters for production bot use."""
        from src.core.simulator import save_strategy_params_to_path
        from src.core.tradingbot.strategy_bridge import get_strategy_bridge

        strategy_name = self._get_simulator_strategy_name()
        params = self._get_simulator_parameters()

        # Also save via bridge for catalog integration
        bridge = get_strategy_bridge()
        try:
            bridge.save_bridged_params(
                simulator_strategy=strategy_name,
                simulator_params=params,
                symbol=getattr(self, 'current_symbol', None),
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to save bridged params: {e}")

        # Get symbol from current chart if available
        symbol = None
        if hasattr(self, "current_symbol"):
            symbol = self.current_symbol

        default_dir = Path("config/strategy_params")
        default_name = f"{strategy_name}_params.json"
        default_path = default_dir / default_name
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Strategy Parameters",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )
        if not filepath:
            return

        path = Path(filepath)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        try:
            saved_path = save_strategy_params_to_path(
                filepath=path,
                strategy_name=strategy_name,
                params=params,
                symbol=symbol,
            )
            self.simulator_status_label.setText(f"Parameters saved: {strategy_name}")
            QMessageBox.information(
                self,
                "Parameters Saved",
                f"Strategy parameters saved for production bot.\n\n"
                f"Strategy: {strategy_name}\n"
                f"File: {saved_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save parameters: {e}")
    def _on_load_params_from_bot(self) -> None:
        """Load saved parameters from production bot config."""
        from src.core.simulator import load_strategy_params, get_params_metadata

        strategy_name = self._get_simulator_strategy_name()

        params = load_strategy_params(strategy_name)

        if params is None:
            QMessageBox.warning(
                self,
                "No Saved Parameters",
                f"No saved parameters found for strategy: {strategy_name}\n\n"
                "Use 'Save to Bot' to save optimized parameters first.",
            )
            return

        # Apply loaded parameters to widgets
        for param_name, value in params.items():
            widget = self._simulator_param_widgets.get(param_name)
            if widget and isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)

        # Show metadata info
        metadata = get_params_metadata(strategy_name)
        info_text = f"Loaded parameters for {strategy_name}"
        if metadata:
            if metadata.get("saved_at"):
                info_text += f"\nSaved: {metadata['saved_at'][:19]}"
            if metadata.get("symbol"):
                info_text += f"\nOptimized for: {metadata['symbol']}"

        self.simulator_status_label.setText(f"Parameters loaded: {strategy_name}")
        QMessageBox.information(self, "Parameters Loaded", info_text)
    def _get_simulator_strategy_name(self) -> str:
        """Get currently selected strategy name (catalog strategy name directly)."""
        if self._is_all_strategy_selected():
            return "all"
        # Return catalog strategy name directly from dropdown
        return self.simulator_strategy_combo.currentText().strip()

    def _get_strategy_index_by_name(self, strategy_name: str) -> int | None:
        """Get combo index for a strategy name."""
        # Search for strategy name in combo box
        for i in range(self.simulator_strategy_combo.count()):
            if self.simulator_strategy_combo.itemText(i) == strategy_name:
                return i
        return None
    def _is_all_strategy_selected(self) -> bool:
        """Check if ALL is selected in strategy dropdown."""
        return self.simulator_strategy_combo.currentText().strip().upper() == "ALL"
