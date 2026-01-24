"""Entry Analyzer - Regime Setup Tab (Mixin) - Dynamic v2.0.

Completely dynamic UI generation from JSON optimization_ranges.
Supports ANY indicator with ANY number of parameters.

Features:
- Automatically generates spinboxes from indicators[].optimization_ranges
- Automatically generates threshold spinboxes from regimes[].optimization_ranges
- No hardcoded parameter lists
- Two tables: Indicator Parameters & Regime Thresholds
- Import/Export optimization ranges
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RegimeSetupMixin:
    """Dynamic Regime Setup tab - generates UI from JSON.

    Reads optimization_ranges from entry_analyzer_regime.json and
    automatically creates spinboxes for ALL parameters.

    Attributes:
        _regime_setup_indicators_table: Table showing current indicators
        _regime_setup_params_table: Dynamic table with min/max spinboxes
        _regime_setup_thresholds_table: Dynamic table for regime thresholds
        _regime_setup_param_ranges: Dict storing {param_key: (min_spin, max_spin)}
        _regime_setup_max_trials: SpinBox for trial count
    """

    # Type hints for parent class attributes
    _regime_setup_indicators_table: QTableWidget
    _regime_setup_params_table: QTableWidget
    _regime_setup_thresholds_table: QTableWidget
    _regime_setup_param_ranges: dict[str, tuple[QSpinBox | QDoubleSpinBox, QSpinBox | QDoubleSpinBox]]
    _regime_setup_max_trials: QSpinBox
    _regime_setup_apply_btn: QPushButton
    _regime_config: object | None

    def _setup_regime_setup_tab(self, tab: QWidget) -> None:
        """Setup dynamic Regime Setup tab.

        Reads optimization_ranges from JSON and generates UI automatically.
        """
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel("Regime Setup (Dynamic)")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)

        description = QLabel(
            "Configure optimization ranges for ALL indicators and regime thresholds. "
            "The UI is dynamically generated from your JSON configuration."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(description)

        # Initialize state
        self._regime_setup_param_ranges = {}

        # Current Regime Indicators Table (Read-only reference)
        current_indicators_group = QGroupBox("Current Regime Indicators (from JSON)")
        current_indicators_layout = QVBoxLayout()

        self._regime_setup_indicators_table = QTableWidget()
        self._regime_setup_indicators_table.setColumnCount(3)
        self._regime_setup_indicators_table.setHorizontalHeaderLabels([
            "Indicator ID", "Type", "Current Parameters"
        ])
        header = self._regime_setup_indicators_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._regime_setup_indicators_table.setAlternatingRowColors(True)
        self._regime_setup_indicators_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._regime_setup_indicators_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._regime_setup_indicators_table.setMaximumHeight(150)

        current_indicators_layout.addWidget(self._regime_setup_indicators_table)
        current_indicators_group.setLayout(current_indicators_layout)
        layout.addWidget(current_indicators_group)

        # Indicator Parameters Optimization Ranges (Dynamic!)
        params_group = QGroupBox("Indicator Parameter Optimization Ranges")
        params_layout = QVBoxLayout()

        params_info = QLabel("Set Min/Max ranges for each indicator parameter. UI is generated from JSON.")
        params_info.setStyleSheet("color: #888; font-style: italic;")
        params_layout.addWidget(params_info)

        self._regime_setup_params_table = QTableWidget()
        # Wide table format (Variante A): 52 columns for up to 10 parameters per indicator
        # Structure: Indicator (1) + Type (1) + [Name, Value, Min, Max, Step] × 10 (50) = 52 columns
        self._regime_setup_params_table.setColumnCount(52)

        # Generate column headers dynamically
        headers = ["Indicator", "Type"]
        for i in range(1, 11):  # 10 parameter slots
            headers.extend([
                f"Param{i} Name",
                f"Param{i} Value",
                f"Param{i} Min",
                f"Param{i} Max",
                f"Param{i} Step"
            ])
        self._regime_setup_params_table.setHorizontalHeaderLabels(headers)

        # Configure column resize modes
        header = self._regime_setup_params_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Indicator
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        # All parameter columns: interactive (user can resize)
        for col in range(2, 52):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        self._regime_setup_params_table.setAlternatingRowColors(True)

        params_layout.addWidget(self._regime_setup_params_table)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group, stretch=2)

        # Regime Threshold Optimization Ranges (Dynamic!)
        thresholds_group = QGroupBox("Regime Threshold Optimization Ranges")
        thresholds_layout = QVBoxLayout()

        thresholds_info = QLabel("Set Min/Max ranges for regime detection thresholds.")
        thresholds_info.setStyleSheet("color: #888; font-style: italic;")
        thresholds_layout.addWidget(thresholds_info)

        self._regime_setup_thresholds_table = QTableWidget()
        self._regime_setup_thresholds_table.setColumnCount(5)
        self._regime_setup_thresholds_table.setHorizontalHeaderLabels([
            "Regime", "Threshold", "Min", "Max", "Step"
        ])
        header = self._regime_setup_thresholds_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._regime_setup_thresholds_table.setAlternatingRowColors(True)

        thresholds_layout.addWidget(self._regime_setup_thresholds_table)
        thresholds_group.setLayout(thresholds_layout)
        layout.addWidget(thresholds_group, stretch=1)

        # Max Trials Counter
        counter_layout = QHBoxLayout()
        counter_layout.addWidget(QLabel("Max Trials:"))
        self._regime_setup_max_trials = QSpinBox()
        self._regime_setup_max_trials.setRange(10, 9999)  # Increased upper limit to 9999 (unbegrenzt)
        self._regime_setup_max_trials.setValue(150)
        self._regime_setup_max_trials.setSingleStep(10)
        self._regime_setup_max_trials.setToolTip("Maximum number of optimization trials (10-9999, unbegrenzt)")
        self._regime_setup_max_trials.setMinimumWidth(150)  # Make input field 2x wider
        counter_layout.addWidget(self._regime_setup_max_trials)

        warning_label = QLabel("⚠️ More trials = better results, but slower")
        warning_label.setStyleSheet("color: #f59e0b;")
        counter_layout.addWidget(warning_label)
        counter_layout.addStretch()
        layout.addLayout(counter_layout)

        # Action Buttons
        button_layout = QHBoxLayout()

        # Import Button
        self._regime_setup_import_btn = QPushButton(get_icon("folder_open"), "Import Config (JSON)")
        self._regime_setup_import_btn.setToolTip("Import regime configuration with optimization ranges from JSON file")
        self._regime_setup_import_btn.clicked.connect(self._on_regime_setup_import)
        button_layout.addWidget(self._regime_setup_import_btn)

        # Reload Button
        reload_btn = QPushButton(get_icon("refresh"), "Reload from JSON")
        reload_btn.setToolTip("Reload optimization ranges from current regime config")
        reload_btn.clicked.connect(self._populate_regime_setup_tables)
        button_layout.addWidget(reload_btn)

        button_layout.addStretch()

        # Apply Button
        self._regime_setup_apply_btn = QPushButton(
            get_icon("check_circle"), "Apply & Continue to Optimization"
        )
        self._regime_setup_apply_btn.setProperty("class", "success")
        self._regime_setup_apply_btn.clicked.connect(self._on_regime_setup_apply)
        button_layout.addWidget(self._regime_setup_apply_btn)
        layout.addLayout(button_layout)

        # Populate tables from loaded regime config
        self._populate_regime_setup_indicators_table()
        self._populate_regime_setup_tables()

    def _get_optimized_params_from_config(self, config) -> dict[str, any]:
        """Extract optimized params from optimization_results if available.

        Args:
            config: TradingBotConfig object

        Returns:
            Dict with optimized params (e.g. {"adx14.period": 10, "rsi14.period": 13})
        """
        optimized_params = {}

        if not hasattr(config, "optimization_results") or not config.optimization_results:
            return optimized_params

        # Find the latest applied result (or newest if none applied)
        applied = [r for r in config.optimization_results if r.get("applied", False)]
        if applied:
            result = applied[-1]  # Newest applied
        else:
            result = config.optimization_results[0]  # First result

        return result.get("params", {})

    def _populate_regime_setup_indicators_table(self) -> None:
        """Populate indicators table with current regime config from JSON.

        Shows what indicators are currently configured in entry_analyzer_regime.json
        so users can see what they're optimizing.

        IMPORTANT: If optimization_results exist, shows the OPTIMIZED values
        with ⚡ marker, not the base indicator values!
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor
        from PyQt6.QtWidgets import QTableWidgetItem

        self._regime_setup_indicators_table.setRowCount(0)

        # Get regime config from parent (loaded in Regime tab)
        if not hasattr(self, "_regime_config") or self._regime_config is None:
            # Try to load default config
            config_path = Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")
            if config_path.exists():
                from src.core.tradingbot.config.loader import ConfigLoader
                loader = ConfigLoader()
                try:
                    self._regime_config = loader.load_config(config_path)
                except Exception as e:
                    logger.warning(f"Could not load regime config for indicators table: {e}")
                    return
            else:
                logger.warning("No regime config loaded, indicators table empty")
                return

        config = self._regime_config

        # Get optimized params from optimization_results (if any)
        optimized_params = self._get_optimized_params_from_config(config)

        # Populate table with indicators
        for indicator in config.indicators:
            row = self._regime_setup_indicators_table.rowCount()
            self._regime_setup_indicators_table.insertRow(row)

            # Indicator ID
            id_item = QTableWidgetItem(indicator.id)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_setup_indicators_table.setItem(row, 0, id_item)

            # Indicator Type
            indicator_type = (
                indicator.type.value if hasattr(indicator.type, "value") else str(indicator.type)
            )
            type_item = QTableWidgetItem(indicator_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_setup_indicators_table.setItem(row, 1, type_item)

            # Current Parameters - Apply optimized values if available!
            effective_params = dict(indicator.params)  # Start with base params
            has_optimization = False

            for key, value in optimized_params.items():
                if key.startswith(f"{indicator.id}."):
                    param_name = key.split(".", 1)[1]
                    if param_name in effective_params:
                        effective_params[param_name] = value
                        has_optimization = True

            # Format params string with ⚡ if optimized
            params_str = ", ".join([f"{k}: {v}" for k, v in effective_params.items()])
            if has_optimization:
                params_str = f"⚡ {params_str}"

            params_item = QTableWidgetItem(params_str)
            params_item.setToolTip(
                f"Effective params (used by Analyze Visible Range):\n"
                f"{json.dumps(effective_params, indent=2)}\n\n"
                f"Base params from indicators[]:\n"
                f"{json.dumps(indicator.params, indent=2)}"
            )
            if has_optimization:
                params_item.setForeground(QColor("#22c55e"))  # Green for optimized
            self._regime_setup_indicators_table.setItem(row, 2, params_item)

        logger.info(
            f"Populated indicators table with {len(config.indicators)} indicators "
            f"(optimized params: {len(optimized_params)})"
        )

    def _populate_regime_setup_tables(self) -> None:
        """Dynamically populate parameter and threshold tables from JSON v2.0.

        Wide table format (Variante A): One row per indicator with all parameters horizontal.
        Reads from optimization_results[].indicators[] (v2.0 format).
        Supports up to 10 parameters per indicator!

        Table structure: Indicator | Type | [Param1-10: Name, Value, Min, Max, Step] × 10
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor
        from PyQt6.QtWidgets import QTableWidgetItem

        # Clear existing
        self._regime_setup_params_table.setRowCount(0)
        self._regime_setup_thresholds_table.setRowCount(0)
        self._regime_setup_param_ranges.clear()

        # Get regime config
        if not hasattr(self, "_regime_config") or self._regime_config is None:
            logger.warning("No regime config loaded, cannot populate setup tables")
            return

        config = self._regime_config

        # Check schema version to determine data source
        schema_version = getattr(config, "schema_version", "1.0.0")

        # 1. Populate Indicator Parameters Table (WIDE FORMAT)
        if schema_version.startswith("2."):
            # v2.0: Read from optimization_results[].indicators[]
            if not hasattr(config, "optimization_results") or not config.optimization_results:
                logger.warning("No optimization_results in v2.0 config")
                return

            # Get the applied result (or first result)
            applied = [r for r in config.optimization_results if r.get("applied", False)]
            if applied:
                result = applied[-1]
            else:
                result = config.optimization_results[0]

            indicators_data = result.get("indicators", [])
        else:
            # v1.0: Read from indicators[] (backward compatibility)
            indicators_data = config.indicators
            # Need to convert v1.0 format to v2.0-like structure
            indicators_data = self._convert_v1_to_v2_format(indicators_data, config)

        # Populate one row per indicator (wide format)
        for indicator in indicators_data:
            row = self._regime_setup_params_table.rowCount()
            self._regime_setup_params_table.insertRow(row)

            # Column 0: Indicator Name/ID
            indicator_name = indicator.get("name") if isinstance(indicator, dict) else indicator.id
            ind_item = QTableWidgetItem(str(indicator_name))
            ind_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_setup_params_table.setItem(row, 0, ind_item)

            # Column 1: Indicator Type
            indicator_type = indicator.get("type") if isinstance(indicator, dict) else indicator.type
            type_item = QTableWidgetItem(str(indicator_type))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_setup_params_table.setItem(row, 1, type_item)

            # Columns 2-51: Parameter slots (10 slots × 5 columns each)
            params_list = indicator.get("params", []) if isinstance(indicator, dict) else []

            for param_idx, param in enumerate(params_list[:10]):  # Max 10 parameters
                # Base column for this parameter slot
                base_col = 2 + (param_idx * 5)

                param_name = param.get("name", "")
                param_value = param.get("value", 0)
                param_range = param.get("range", {})

                # Column +0: Parameter Name
                name_item = QTableWidgetItem(param_name)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_setup_params_table.setItem(row, base_col + 0, name_item)

                # Column +1: Current Value (read-only, shows optimized value)
                value_item = QTableWidgetItem(f"⚡ {param_value}")
                value_item.setForeground(QColor("#22c55e"))  # Green for optimized
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                value_item.setToolTip(f"Optimized value from v2.0 config: {param_value}")
                self._regime_setup_params_table.setItem(row, base_col + 1, value_item)

                # Column +2: Min SpinBox
                min_val = param_range.get("min", param_value * 0.5)
                max_val = param_range.get("max", param_value * 1.5)
                step_val = param_range.get("step", 1)

                min_spin = self._create_spinbox(min_val, max_val, step_val)
                min_spin.setValue(min_val)
                self._regime_setup_params_table.setCellWidget(row, base_col + 2, min_spin)

                # Column +3: Max SpinBox
                max_spin = self._create_spinbox(min_val, max_val, step_val)
                max_spin.setValue(max_val)
                self._regime_setup_params_table.setCellWidget(row, base_col + 3, max_spin)

                # Column +4: Step (read-only)
                step_item = QTableWidgetItem(str(step_val))
                step_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                step_item.setForeground(Qt.GlobalColor.gray)
                self._regime_setup_params_table.setItem(row, base_col + 4, step_item)

                # Store reference for this parameter
                param_key = f"{indicator_name}.{param_name}"
                self._regime_setup_param_ranges[param_key] = (min_spin, max_spin)

            # Fill remaining parameter slots with empty cells (if <10 parameters)
            for empty_idx in range(len(params_list), 10):
                base_col = 2 + (empty_idx * 5)
                for offset in range(5):
                    empty_item = QTableWidgetItem("")
                    empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Disable empty cells
                    empty_item.setBackground(QColor("#f0f0f0"))  # Light gray background
                    self._regime_setup_params_table.setItem(row, base_col + offset, empty_item)

        # 2. Populate Regime Thresholds Table
        if schema_version.startswith("2."):
            # v2.0: Read regimes from optimization_results
            regimes_data = result.get("regimes", [])
        else:
            # v1.0: Read from regimes[]
            regimes_data = config.regimes
            regimes_data = self._convert_v1_regimes_to_v2_format(regimes_data)

        for regime in regimes_data:
            # Check if regime has thresholds
            thresholds = regime.get("thresholds", []) if isinstance(regime, dict) else []
            if not thresholds:
                logger.debug(f"Regime {regime.get('id', 'UNKNOWN')} has no thresholds, skipping")
                continue

            # Create row for each threshold
            for threshold in thresholds:
                row = self._regime_setup_thresholds_table.rowCount()
                self._regime_setup_thresholds_table.insertRow(row)

                regime_id = regime.get("id") if isinstance(regime, dict) else regime.id

                # Regime ID
                regime_item = QTableWidgetItem(regime_id)
                regime_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Color code
                if "BULL" in regime_id:
                    regime_item.setForeground(Qt.GlobalColor.darkGreen)
                elif "BEAR" in regime_id:
                    regime_item.setForeground(Qt.GlobalColor.darkRed)
                elif "SIDEWAYS" in regime_id:
                    regime_item.setForeground(Qt.GlobalColor.darkYellow)
                self._regime_setup_thresholds_table.setItem(row, 0, regime_item)

                threshold_name = threshold.get("name", "")
                threshold_value = threshold.get("value", 0)
                threshold_range = threshold.get("range", {})

                # Threshold Name
                threshold_item = QTableWidgetItem(threshold_name)
                threshold_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_setup_thresholds_table.setItem(row, 1, threshold_item)

                # Min/Max/Step from range
                min_val = threshold_range.get("min", threshold_value * 0.5)
                max_val = threshold_range.get("max", threshold_value * 1.5)
                step_val = threshold_range.get("step", 1)

                # Min SpinBox
                min_spin = self._create_spinbox(min_val, max_val, step_val)
                min_spin.setValue(min_val)
                self._regime_setup_thresholds_table.setCellWidget(row, 2, min_spin)

                # Max SpinBox
                max_spin = self._create_spinbox(min_val, max_val, step_val)
                max_spin.setValue(max_val)
                self._regime_setup_thresholds_table.setCellWidget(row, 3, max_spin)

                # Step
                step_item = QTableWidgetItem(str(step_val))
                step_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                step_item.setForeground(Qt.GlobalColor.gray)
                self._regime_setup_thresholds_table.setItem(row, 4, step_item)

                # Store reference
                threshold_key = f"{regime_id}.{threshold_name}"
                self._regime_setup_param_ranges[threshold_key] = (min_spin, max_spin)

        logger.info(
            f"Populated {self._regime_setup_params_table.rowCount()} indicators (v2.0 wide format) and "
            f"{self._regime_setup_thresholds_table.rowCount()} regime thresholds"
        )

    def _create_spinbox(self, min_val: float, max_val: float, step: float) -> QSpinBox | QDoubleSpinBox:
        """Create appropriate spinbox based on value type.

        Args:
            min_val: Minimum value
            max_val: Maximum value
            step: Step size

        Returns:
            QSpinBox for integers, QDoubleSpinBox for floats
        """
        if isinstance(min_val, float) or isinstance(max_val, float) or isinstance(step, float):
            spin = QDoubleSpinBox()
            spin.setDecimals(2)
        else:
            spin = QSpinBox()

        spin.setRange(int(min_val) if isinstance(spin, QSpinBox) else min_val,
                     int(max_val) if isinstance(spin, QSpinBox) else max_val)
        spin.setSingleStep(int(step) if isinstance(spin, QSpinBox) else step)
        spin.setMinimumWidth(80)

        return spin

    def _create_default_ranges(self, params: dict) -> dict:
        """Create default optimization ranges for parameters without ranges.

        Args:
            params: Current parameter values

        Returns:
            Dict with default min/max/step for each parameter
        """
        default_ranges = {}
        for param_name, param_value in params.items():
            if isinstance(param_value, float):
                # Float parameter: ±50% range
                default_ranges[param_name] = {
                    "min": param_value * 0.5,
                    "max": param_value * 1.5,
                    "step": param_value * 0.1
                }
            else:
                # Integer parameter: ±50% range
                default_ranges[param_name] = {
                    "min": max(1, int(param_value * 0.5)),
                    "max": int(param_value * 1.5),
                    "step": 1
                }
        return default_ranges

    def _convert_v1_to_v2_format(self, indicators, config) -> list[dict]:
        """Convert v1.0 indicators to v2.0 format for display.

        Args:
            indicators: List of v1.0 indicator objects
            config: Full config object with optimization_results

        Returns:
            List of dicts in v2.0 format with params array
        """
        v2_indicators = []

        # Get optimized params from v1.0 optimization_results
        optimized_params = self._get_optimized_params_from_config(config)

        for indicator in indicators:
            # Get optimization ranges
            if hasattr(indicator, "optimization_ranges") and indicator.optimization_ranges:
                optimization_ranges = indicator.optimization_ranges
            else:
                optimization_ranges = self._create_default_ranges(indicator.params)

            # Build params array (v2.0 format)
            params_array = []
            for param_name, param_value in indicator.params.items():
                # Get optimized value if available
                opt_key = f"{indicator.id}.{param_name}"
                effective_value = optimized_params.get(opt_key, param_value)

                # Get range
                range_def = optimization_ranges.get(param_name, {
                    "min": param_value * 0.5,
                    "max": param_value * 1.5,
                    "step": 1 if isinstance(param_value, int) else 0.1
                })

                params_array.append({
                    "name": param_name,
                    "value": effective_value,
                    "range": range_def
                })

            v2_indicators.append({
                "name": indicator.id,
                "type": indicator.type.value if hasattr(indicator.type, "value") else str(indicator.type),
                "params": params_array
            })

        return v2_indicators

    def _convert_v1_regimes_to_v2_format(self, regimes) -> list[dict]:
        """Convert v1.0 regimes to v2.0 format with thresholds array.

        Args:
            regimes: List of v1.0 regime objects

        Returns:
            List of dicts in v2.0 format with thresholds array
        """
        v2_regimes = []

        for regime in regimes:
            # Check if regime has optimization_ranges
            if not hasattr(regime, "optimization_ranges") or not regime.optimization_ranges:
                continue

            # Build thresholds array (v2.0 format)
            thresholds_array = []
            for threshold_name, range_def in regime.optimization_ranges.items():
                thresholds_array.append({
                    "name": threshold_name,
                    "value": range_def.get("min", 0),  # Use min as placeholder
                    "range": range_def
                })

            v2_regimes.append({
                "id": regime.id,
                "name": regime.name,
                "thresholds": thresholds_array,
                "priority": regime.priority,
                "scope": regime.scope
            })

        return v2_regimes

    def _on_regime_setup_apply(self) -> None:
        """Apply settings and switch to Regime Optimization tab."""
        logger.info("Applying regime setup parameters")

        # Store config for next tab
        self._regime_setup_config = self._get_regime_setup_config()

        # Enable and switch to Regime Optimization tab (next tab)
        if hasattr(self, "_tabs"):
            # Find the Regime Optimization tab (should be next after Regime Setup)
            current_index = self._tabs.currentIndex()
            next_index = current_index + 1
            if next_index < self._tabs.count():
                self._tabs.setTabEnabled(next_index, True)
                self._tabs.setCurrentIndex(next_index)

        logger.info(f"Regime setup complete, {len(self._regime_setup_config)} parameter ranges configured")

    def _get_regime_setup_config(self) -> dict:
        """Get current regime setup configuration from spinboxes.

        Returns:
            Dict with parameter ranges: {param_key: {min: X, max: Y}}
        """
        config = {}

        for param_key, (min_spin, max_spin) in self._regime_setup_param_ranges.items():
            config[param_key] = {
                "min": min_spin.value(),
                "max": max_spin.value(),
            }

        logger.info(f"Collected {len(config)} parameter ranges")
        return config

    @pyqtSlot()
    def _on_regime_setup_import(self) -> None:
        """Import regime configuration with parameter ranges from JSON file."""
        # Path: src/ui/dialogs/entry_analyzer/this_file.py -> 5x parent = project root
        project_root = Path(__file__).parent.parent.parent.parent.parent
        base_dir = project_root / "03_JSON" / "Entry_Analyzer" / "Regime"
        base_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Regime Config", str(base_dir), "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            # Load JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load config using ConfigLoader
            from src.core.tradingbot.config.loader import ConfigLoader
            loader = ConfigLoader()
            self._regime_config = loader.load_config(Path(file_path))

            # Reload all tables
            self._populate_regime_setup_indicators_table()
            self._populate_regime_setup_tables()

            # Update max_trials if present
            max_trials_meta = data.get("metadata", {}).get("max_trials")
            if max_trials_meta and hasattr(self, "_regime_setup_max_trials"):
                self._regime_setup_max_trials.setValue(max_trials_meta)

            QMessageBox.information(
                self,
                "Import Successful",
                f"Successfully imported regime configuration from:\n{file_path}\n\n"
                f"Loaded {len(self._regime_config.indicators)} indicators with optimization ranges."
            )

            logger.info(f"Imported regime config from {file_path}")

        except Exception as e:
            logger.error(f"Failed to import regime config: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import regime configuration:\n\n{str(e)}"
            )
