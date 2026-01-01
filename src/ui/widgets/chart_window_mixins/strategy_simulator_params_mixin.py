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
        }
        strategy = strategy_map.get(index, StrategyName.BREAKOUT)
        self._populate_simulator_parameter_widgets(strategy)
        self._update_trials_hint(strategy)

        if self._all_run_active:
            self.simulator_params_group.setEnabled(False)
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
                    param_def.max_value or 100,
                )
                widget.setValue(param_def.default)
                if param_def.step:
                    widget.setSingleStep(param_def.step)
            elif param_def.param_type == "float":
                widget = QDoubleSpinBox()
                widget.setRange(
                    param_def.min_value or 0.0,
                    param_def.max_value or 100.0,
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
        self._on_entry_lookahead_changed()
    def _on_entry_lookahead_changed(self) -> None:
        if not hasattr(self, "simulator_entry_lookahead_combo"):
            return
        enabled = self._is_entry_only_selected()
        mode = self.simulator_entry_lookahead_combo.currentData()
        is_fixed = mode == "fixed_bars"
        self.simulator_entry_lookahead_combo.setEnabled(enabled)
        if hasattr(self, "simulator_entry_lookahead_bars"):
            self.simulator_entry_lookahead_bars.setEnabled(enabled and is_fixed)
    def _get_entry_lookahead_mode(self) -> str:
        if not hasattr(self, "simulator_entry_lookahead_combo"):
            return "session_end"
        data = self.simulator_entry_lookahead_combo.currentData()
        return data or "session_end"
    def _get_entry_lookahead_bars(self) -> int | None:
        if not hasattr(self, "simulator_entry_lookahead_bars"):
            return None
        if self._get_entry_lookahead_mode() != "fixed_bars":
            return None
        return int(self.simulator_entry_lookahead_bars.value())
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
    def _on_save_params_to_bot(self) -> None:
        """Save current parameters for production bot use."""
        from src.core.simulator import save_strategy_params_to_path

        strategy_name = self._get_simulator_strategy_name()
        params = self._get_simulator_parameters()

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
        """Get currently selected strategy name."""
        if self._is_all_strategy_selected():
            return "all"

        strategy_map = {
            0: "breakout",
            1: "momentum",
            2: "mean_reversion",
            3: "trend_following",
            4: "scalping",
            5: "bollinger_squeeze",
            6: "trend_pullback",
            7: "opening_range",
            8: "regime_hybrid",
        }
        return strategy_map.get(
            self.simulator_strategy_combo.currentIndex(), "breakout"
        )
    def _get_strategy_index_by_name(self, strategy_name: str) -> int | None:
        """Get combo index for a strategy name."""
        strategy_map = {
            "breakout": 0,
            "momentum": 1,
            "mean_reversion": 2,
            "trend_following": 3,
            "scalping": 4,
            "bollinger_squeeze": 5,
            "trend_pullback": 6,
            "opening_range": 7,
            "regime_hybrid": 8,
        }
        return strategy_map.get(strategy_name)
    def _is_all_strategy_selected(self) -> bool:
        """Check if ALL is selected in strategy dropdown."""
        return self.simulator_strategy_combo.currentText().strip().upper() == "ALL"
