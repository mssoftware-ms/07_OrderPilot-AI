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
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon
from src.ui.widgets.collapsible_section import CollapsibleSection, AccordionWidget

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
    """

    # Type hints for parent class attributes
    _regime_setup_indicators_table: QTableWidget
    _regime_setup_params_table: QTableWidget
    _regime_setup_thresholds_table: QTableWidget
    _regime_setup_param_ranges: dict[str, tuple[QSpinBox | QDoubleSpinBox, QSpinBox | QDoubleSpinBox]]
    _regime_setup_apply_btn: QPushButton
    _regime_config: object | None

    def _setup_regime_setup_tab(self, tab: QWidget) -> None:
        """Setup dynamic Regime Setup tab with accordion-style collapsible sections.

        Reads optimization_ranges from JSON and generates UI automatically.
        """
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Initialize state
        self._regime_setup_param_ranges = {}

        # Create accordion container
        self._regime_setup_accordion = AccordionWidget()

        # Section 1: Current Regime Indicators (collapsed by default)
        indicators_section = CollapsibleSection("Current Regime Indicators", expanded=False, icon="analytics")
        self._regime_setup_indicators_table = QTableWidget()
        self._regime_setup_indicators_table.setColumnCount(3)
        self._regime_setup_indicators_table.setHorizontalHeaderLabels([
            "Indicator ID", "Type", "Current Parameters"
        ])
        ind_header = self._regime_setup_indicators_table.horizontalHeader()
        ind_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        ind_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ind_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._regime_setup_indicators_table.setAlternatingRowColors(True)
        self._regime_setup_indicators_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._regime_setup_indicators_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._regime_setup_indicators_table.setMinimumHeight(120)
        indicators_section.set_content(self._regime_setup_indicators_table)
        self._regime_setup_accordion.add_section(indicators_section)

        # Section 2: Indicator Parameter Optimization Ranges (expanded by default)
        params_section = CollapsibleSection("Indicator Parameter Ranges", expanded=True, icon="tune")
        self._regime_setup_params_table = QTableWidget()
        self._regime_setup_params_table.setColumnCount(52)

        headers = ["Indicator", "Type"]
        for i in range(1, 11):
            headers.extend([f"P{i} Name", f"P{i} Val", f"P{i} Min", f"P{i} Max", f"P{i} Step"])
        self._regime_setup_params_table.setHorizontalHeaderLabels(headers)

        params_header = self._regime_setup_params_table.horizontalHeader()
        params_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        params_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for col in range(2, 52):
            params_header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self._regime_setup_params_table.setAlternatingRowColors(True)
        self._regime_setup_params_table.setMinimumHeight(150)
        params_section.set_content(self._regime_setup_params_table)
        self._regime_setup_accordion.add_section(params_section)

        # Section 3: Regime Threshold Optimization Ranges (collapsed by default)
        thresholds_section = CollapsibleSection("Regime Threshold Ranges", expanded=False, icon="settings")
        self._regime_setup_thresholds_table = QTableWidget()
        self._regime_setup_thresholds_table.setColumnCount(52)

        thresh_headers = ["Regime", "Priority"]
        for i in range(1, 11):
            thresh_headers.extend([f"T{i} Name", f"T{i} Val", f"T{i} Min", f"T{i} Max", f"T{i} Step"])
        self._regime_setup_thresholds_table.setHorizontalHeaderLabels(thresh_headers)

        thresh_header = self._regime_setup_thresholds_table.horizontalHeader()
        thresh_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        thresh_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for col in range(2, 52):
            thresh_header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self._regime_setup_thresholds_table.setAlternatingRowColors(True)
        self._regime_setup_thresholds_table.setMinimumHeight(150)
        thresholds_section.set_content(self._regime_setup_thresholds_table)
        self._regime_setup_accordion.add_section(thresholds_section)

        layout.addWidget(self._regime_setup_accordion, stretch=1)

        # Action Buttons
        button_layout = QHBoxLayout()

        # Load from Regime Tab Button (uses JSON loaded in Regime tab)
        self._regime_setup_load_from_regime_btn = QPushButton(get_icon("sync"), "Load Regime JSON")
        self._regime_setup_load_from_regime_btn.setToolTip(
            "Load the JSON config that's currently loaded in the 'Regime' tab.\n"
            "This synchronizes the Regime Setup with the Regime tab."
        )
        self._regime_setup_load_from_regime_btn.clicked.connect(self._on_load_from_regime_tab)
        button_layout.addWidget(self._regime_setup_load_from_regime_btn)

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
            config: Config dict (v2.0 format) or legacy Pydantic object

        Returns:
            Dict with optimized params (e.g. {"adx.period": 10, "rsi.period": 13})
        """
        optimized_params = {}

        # Handle v2.0 dict format
        if isinstance(config, dict):
            opt_results = config.get("optimization_results", [])
            if not opt_results:
                return optimized_params

            # Find the latest applied result (or newest if none applied)
            applied = [r for r in opt_results if r.get("applied", False)]
            if applied:
                result = applied[-1]  # Newest applied
            else:
                result = opt_results[0]  # First result

            # v2.0 format: Convert params array to flat dict
            # indicators[].params[] = [{name, value, range}] -> {"indicator.param": value}
            for indicator in result.get("indicators", []):
                indicator_name = indicator.get("name", "")
                for param in indicator.get("params", []):
                    param_name = param.get("name", "")
                    param_value = param.get("value")
                    if indicator_name and param_name and param_value is not None:
                        optimized_params[f"{indicator_name}.{param_name}"] = param_value

            return optimized_params

        # Handle legacy Pydantic format (backward compatibility)
        if not hasattr(config, "optimization_results") or not config.optimization_results:
            return optimized_params

        applied = [r for r in config.optimization_results if r.get("applied", False)]
        if applied:
            result = applied[-1]
        else:
            result = config.optimization_results[0]

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
            config_path = Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")
            repo_root = Path(__file__).resolve().parents[3]
            template = repo_root / "03_JSON/Entry_Analyzer/Regime/JSON Template/v2_schema_reference.json"

            candidates = [config_path, repo_root / config_path, template]
            loaded = False
            for p in candidates:
                try:
                    if not p.exists():
                        continue
                    from src.core.tradingbot.config.regime_loader_v2 import RegimeConfigLoaderV2
                    loader = RegimeConfigLoaderV2()
                    self._regime_config = loader.load_config(p)
                    loaded = True
                    break
                except OSError as exc:
                    logger.warning("Cannot access regime config %s: %s", p, exc)
                    continue
                except Exception as e:
                    logger.warning(f"Could not load regime config for indicators table: {e}")
                    continue

            if not loaded:
                logger.warning("No regime config loaded, indicators table empty")
                return

        config = self._regime_config

        # Get optimized params from optimization_results (if any)
        optimized_params = self._get_optimized_params_from_config(config)

        # Handle v2.0 dict format
        if isinstance(config, dict):
            # Get indicators from first optimization result
            opt_results = config.get("optimization_results", [])
            if not opt_results:
                logger.warning("No optimization_results in v2.0 config")
                return

            # Get applied result (or first result)
            applied = [r for r in opt_results if r.get("applied", False)]
            result = applied[-1] if applied else opt_results[0]
            indicators = result.get("indicators", [])

            # Populate table with indicators
            for indicator in indicators:
                row = self._regime_setup_indicators_table.rowCount()
                self._regime_setup_indicators_table.insertRow(row)

                # Indicator ID
                indicator_name = indicator.get("name", "")
                id_item = QTableWidgetItem(indicator_name)
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_setup_indicators_table.setItem(row, 0, id_item)

                # Indicator Type
                indicator_type = indicator.get("type", "")
                type_item = QTableWidgetItem(indicator_type)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_setup_indicators_table.setItem(row, 1, type_item)

                # Current Parameters - v2.0 format has params array
                params_array = indicator.get("params", [])
                effective_params = {p["name"]: p["value"] for p in params_array}

                # Format params string with ⚡ (all v2.0 params are optimized)
                params_str = ", ".join([f"{k}: {v}" for k, v in effective_params.items()])
                params_str = f"⚡ {params_str}"

                params_item = QTableWidgetItem(params_str)
                params_item.setToolTip(
                    f"Optimized params from v2.0 config:\n"
                    f"{json.dumps(effective_params, indent=2)}"
                )
                params_item.setForeground(QColor("#22c55e"))  # Green for optimized
                self._regime_setup_indicators_table.setItem(row, 2, params_item)

            logger.info(
                f"Populated indicators table with {len(indicators)} indicators (v2.0 format, "
                f"{len(optimized_params)} optimized params)"
            )
            return

        # Legacy Pydantic format (backward compatibility)
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

        # Determine format: v2.0 dict or legacy Pydantic
        if isinstance(config, dict):
            # v2.0 format
            schema_version = config.get("schema_version", "2.0.0")
            opt_results = config.get("optimization_results", [])
            if not opt_results:
                logger.warning("No optimization_results in v2.0 config")
                return

            # Get the applied result (or first result)
            applied = [r for r in opt_results if r.get("applied", False)]
            result = applied[-1] if applied else opt_results[0]

            indicators_data = result.get("indicators", [])
        else:
            # Legacy Pydantic format
            schema_version = getattr(config, "schema_version", "1.0.0")

            if schema_version.startswith("2."):
                # Legacy v2.0 Pydantic format
                if not hasattr(config, "optimization_results") or not config.optimization_results:
                    logger.warning("No optimization_results in v2.0 config")
                    return

                applied = [r for r in config.optimization_results if r.get("applied", False)]
                result = applied[-1] if applied else config.optimization_results[0]
                indicators_data = result.get("indicators", [])
            else:
                # v1.0: Convert to v2.0-like structure
                indicators_data = self._convert_v1_to_v2_format(config.indicators, config)

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

        # 2. Populate Regime Thresholds Table (Wide Format - one row per regime)
        if isinstance(config, dict):
            # v2.0 dict format: regimes from optimization_results
            regimes_data = result.get("regimes", [])
        elif schema_version.startswith("2."):
            # Legacy v2.0 Pydantic format
            regimes_data = result.get("regimes", [])
        else:
            # v1.0: Convert to v2.0-like structure
            regimes_data = self._convert_v1_regimes_to_v2_format(config.regimes)

        for regime in regimes_data:
            # Check if regime has thresholds
            thresholds = regime.get("thresholds", []) if isinstance(regime, dict) else []
            regime_id = regime.get("id") if isinstance(regime, dict) else regime.id
            regime_priority = regime.get("priority", 50) if isinstance(regime, dict) else 50

            # Create one row per regime
            row = self._regime_setup_thresholds_table.rowCount()
            self._regime_setup_thresholds_table.insertRow(row)

            # Column 0: Regime ID
            regime_item = QTableWidgetItem(regime_id)
            regime_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Color code based on regime type
            if "BULL" in regime_id.upper():
                regime_item.setForeground(Qt.GlobalColor.darkGreen)
            elif "BEAR" in regime_id.upper():
                regime_item.setForeground(Qt.GlobalColor.darkRed)
            elif "SIDEWAYS" in regime_id.upper():
                regime_item.setForeground(Qt.GlobalColor.darkYellow)
            elif "TF" in regime_id.upper() or "STRONG" in regime_id.upper():
                regime_item.setForeground(QColor("#8b5cf6"))  # Purple for strong trends
            self._regime_setup_thresholds_table.setItem(row, 0, regime_item)

            # Column 1: Priority
            priority_item = QTableWidgetItem(str(regime_priority))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            priority_item.setForeground(Qt.GlobalColor.gray)
            self._regime_setup_thresholds_table.setItem(row, 1, priority_item)

            # Populate threshold columns (up to 10 thresholds)
            thresholds_list = thresholds[:10]  # Limit to 10 thresholds
            for thresh_idx, threshold in enumerate(thresholds_list):
                base_col = 2 + (thresh_idx * 5)  # 5 columns per threshold

                threshold_name = threshold.get("name", "")
                threshold_value = threshold.get("value", 0)
                threshold_range = threshold.get("range", {})

                # Column base+0: Threshold Name
                name_item = QTableWidgetItem(threshold_name)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                name_item.setToolTip(f"Threshold: {threshold_name}")
                self._regime_setup_thresholds_table.setItem(row, base_col, name_item)

                # Column base+1: Current Value (read-only)
                value_item = QTableWidgetItem(f"⚡ {threshold_value}")
                value_item.setForeground(QColor("#22c55e"))  # Green for optimized
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                value_item.setToolTip(f"Current value from JSON: {threshold_value}")
                self._regime_setup_thresholds_table.setItem(row, base_col + 1, value_item)

                # Min/Max/Step from range
                min_val = threshold_range.get("min", threshold_value * 0.5 if threshold_value else 0)
                max_val = threshold_range.get("max", threshold_value * 1.5 if threshold_value else 100)
                step_val = threshold_range.get("step", 1)

                # Column base+2: Min SpinBox
                min_spin = self._create_spinbox(min_val, max_val, step_val)
                min_spin.setValue(min_val)
                self._regime_setup_thresholds_table.setCellWidget(row, base_col + 2, min_spin)

                # Column base+3: Max SpinBox
                max_spin = self._create_spinbox(min_val, max_val, step_val)
                max_spin.setValue(max_val)
                self._regime_setup_thresholds_table.setCellWidget(row, base_col + 3, max_spin)

                # Column base+4: Step
                step_item = QTableWidgetItem(str(step_val))
                step_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                step_item.setForeground(Qt.GlobalColor.gray)
                self._regime_setup_thresholds_table.setItem(row, base_col + 4, step_item)

                # Store reference for this threshold
                threshold_key = f"{regime_id}.{threshold_name}"
                self._regime_setup_param_ranges[threshold_key] = (min_spin, max_spin)

            # Fill remaining threshold slots with empty cells (if <10 thresholds)
            for empty_idx in range(len(thresholds_list), 10):
                base_col = 2 + (empty_idx * 5)
                for offset in range(5):
                    empty_item = QTableWidgetItem("")
                    empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Disable empty cells
                    empty_item.setBackground(QColor("#f0f0f0"))  # Light gray background
                    self._regime_setup_thresholds_table.setItem(row, base_col + offset, empty_item)

        logger.info(
            f"Populated {self._regime_setup_params_table.rowCount()} indicators and "
            f"{self._regime_setup_thresholds_table.rowCount()} regimes (wide format with thresholds)"
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
    def _on_load_from_regime_tab(self) -> None:
        """Load the JSON config that's currently loaded in the Regime tab.

        This synchronizes the Regime Setup tab with the Regime tab by loading
        the same JSON configuration file.
        """
        # Check if a JSON config is loaded in the Regime tab
        # Try multiple attribute names for compatibility
        config_path = getattr(self, "_regime_config_path", None)
        if config_path is None:
            config_path = getattr(self, "_current_json_config_path", None)

        if not config_path:
            QMessageBox.warning(
                self,
                "No Regime Config Loaded",
                "No JSON configuration is currently loaded in the 'Regime' tab.\n\n"
                "Please load a regime JSON file in the 'Regime' tab first, "
                "then click this button to synchronize."
            )
            return

        try:
            config_path = Path(config_path)
            if not config_path.exists():
                QMessageBox.warning(
                    self,
                    "Config File Not Found",
                    f"The previously loaded config file no longer exists:\n{config_path}\n\n"
                    "Please load a valid JSON file in the 'Regime' tab."
                )
                return

            # Load JSON file
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load config using RegimeConfigLoaderV2
            from src.core.tradingbot.config.regime_loader_v2 import RegimeConfigLoaderV2
            loader = RegimeConfigLoaderV2()
            self._regime_config = loader.load_config(config_path)

            # Reload all tables
            self._populate_regime_setup_indicators_table()
            self._populate_regime_setup_tables()

            # Update max_trials if present
            max_trials_meta = data.get("metadata", {}).get("max_trials")
            if max_trials_meta and hasattr(self, "_regime_opt_max_trials"):
                self._regime_opt_max_trials.setValue(max_trials_meta)

            # Count indicators based on format
            if isinstance(self._regime_config, dict):
                opt_results = self._regime_config.get("optimization_results", [])
                num_indicators = 0
                num_regimes = 0
                if opt_results:
                    applied = [r for r in opt_results if r.get("applied", False)]
                    result = applied[-1] if applied else opt_results[0]
                    num_indicators = len(result.get("indicators", []))
                    num_regimes = len(result.get("regimes", []))
            else:
                num_indicators = len(getattr(self._regime_config, "indicators", []))
                num_regimes = len(getattr(self._regime_config, "regimes", []))

            QMessageBox.information(
                self,
                "Regime Config Loaded",
                f"Successfully loaded regime configuration from Regime tab:\n\n"
                f"File: {config_path.name}\n"
                f"Indicators: {num_indicators}\n"
                f"Regimes: {num_regimes}\n\n"
                "The Regime Setup tables have been synchronized."
            )

            logger.info(f"Loaded regime config from Regime tab: {config_path}")

        except Exception as e:
            logger.error(f"Failed to load regime config from Regime tab: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Load Failed",
                f"Failed to load regime configuration:\n\n{str(e)}"
            )

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

            # Load config using RegimeConfigLoaderV2
            from src.core.tradingbot.config.regime_loader_v2 import RegimeConfigLoaderV2
            loader = RegimeConfigLoaderV2()
            self._regime_config = loader.load_config(Path(file_path))

            # Reload all tables
            self._populate_regime_setup_indicators_table()
            self._populate_regime_setup_tables()

            # Update max_trials if present
            max_trials_meta = data.get("metadata", {}).get("max_trials")
            if max_trials_meta and hasattr(self, "_regime_opt_max_trials"):
                self._regime_opt_max_trials.setValue(max_trials_meta)

            # Count indicators based on format
            if isinstance(self._regime_config, dict):
                opt_results = self._regime_config.get("optimization_results", [])
                num_indicators = 0
                if opt_results:
                    applied = [r for r in opt_results if r.get("applied", False)]
                    result = applied[-1] if applied else opt_results[0]
                    num_indicators = len(result.get("indicators", []))
            else:
                num_indicators = len(self._regime_config.indicators)

            QMessageBox.information(
                self,
                "Import Successful",
                f"Successfully imported regime configuration from:\n{file_path}\n\n"
                f"Loaded {num_indicators} indicators with optimization ranges."
            )

            logger.info(f"Imported regime config from {file_path}")

        except Exception as e:
            logger.error(f"Failed to import regime config: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import regime configuration:\n\n{str(e)}"
            )
