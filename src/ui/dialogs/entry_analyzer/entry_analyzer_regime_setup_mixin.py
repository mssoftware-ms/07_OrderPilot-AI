"""Entry Analyzer - Regime Setup Tab (Mixin).

Stufe-1: Regime-Optimierung - Tab 1/3
Provides UI for regime parameter range configuration:
- ADX: period (10-30), threshold (20-35)
- SMA_Fast: period (20-100)
- SMA_Slow: period (100-300)
- RSI: period (10-20), sideways_low (30-45), sideways_high (55-70)
- BB: period (15-30), std_dev (1.5-3.0), width_percentile (10-40)
- Auto/Manual mode toggle
- Combination counter (max 150 for TPE)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RegimeSetupMixin:
    """Mixin for Regime Setup tab in Entry Analyzer.

    Provides:
        - Parameter range configuration (ADX, SMA, RSI, BB)
        - Auto mode: Load ranges from JSON preset
        - Manual mode: User adjusts spinboxes
        - Combination counter (estimates trial count)
    """

    # Type hints for parent class attributes
    _regime_setup_auto_mode: QCheckBox
    _regime_setup_preset_combo: QComboBox
    _regime_setup_param_widgets: dict[str, tuple[QSpinBox, QSpinBox]]
    _regime_setup_combinations_label: QLabel
    _regime_setup_apply_btn: QPushButton

    def _setup_regime_setup_tab(self, tab: QWidget) -> None:
        """Setup Regime Setup tab with parameter ranges.

        Args:
            tab: QWidget to populate
        """
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel("Regime Parameter Setup")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)

        description = QLabel(
            "Configure parameter ranges for regime optimization (Stage 1). "
            "The optimizer will test combinations using TPE algorithm."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(description)

        # Auto/Manual Mode
        mode_layout = QHBoxLayout()
        self._regime_setup_auto_mode = QCheckBox("Auto Mode (Load from Preset)")
        self._regime_setup_auto_mode.setChecked(True)
        self._regime_setup_auto_mode.stateChanged.connect(self._on_regime_setup_mode_changed)
        mode_layout.addWidget(self._regime_setup_auto_mode)

        self._regime_setup_preset_combo = QComboBox()
        self._regime_setup_preset_combo.addItems(
            [
                "Conservative (Narrow Ranges)",
                "Standard (Balanced)",
                "Aggressive (Wide Ranges)",
                "Custom",
            ]
        )
        self._regime_setup_preset_combo.currentIndexChanged.connect(
            self._on_regime_setup_preset_changed
        )
        mode_layout.addWidget(self._regime_setup_preset_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Initialize state BEFORE creating param ranges group
        self._regime_setup_param_widgets = {}

        # Parameter Ranges Group
        param_group = self._create_regime_param_ranges_group()
        layout.addWidget(param_group, stretch=1)

        # Combination Counter
        counter_layout = QHBoxLayout()
        counter_layout.addWidget(QLabel("Estimated Trials:"))
        self._regime_setup_combinations_label = QLabel("0")
        self._regime_setup_combinations_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        counter_layout.addWidget(self._regime_setup_combinations_label)
        counter_layout.addStretch()

        # Max Trials Input
        counter_layout.addWidget(QLabel("Max Trials:"))
        self._regime_setup_max_trials = QSpinBox()
        self._regime_setup_max_trials.setRange(10, 500)
        self._regime_setup_max_trials.setValue(150)
        self._regime_setup_max_trials.setSingleStep(10)
        self._regime_setup_max_trials.setToolTip("Maximum number of optimization trials (10-500)")
        counter_layout.addWidget(self._regime_setup_max_trials)

        warning_label = QLabel("⚠️ More trials = better results, but slower")
        warning_label.setStyleSheet("color: #f59e0b;")
        counter_layout.addWidget(warning_label)
        layout.addLayout(counter_layout)

        # Action Buttons
        button_layout = QHBoxLayout()

        # Import Button
        self._regime_setup_import_btn = QPushButton(get_icon("folder_open"), "Import Config (JSON)")
        self._regime_setup_import_btn.setToolTip("Import regime configuration with parameter ranges from JSON file")
        self._regime_setup_import_btn.clicked.connect(self._on_regime_setup_import)
        button_layout.addWidget(self._regime_setup_import_btn)

        button_layout.addStretch()

        # Apply Button
        self._regime_setup_apply_btn = QPushButton(
            get_icon("check_circle"), "Apply & Continue to Optimization"
        )
        self._regime_setup_apply_btn.setProperty("class", "success")
        self._regime_setup_apply_btn.clicked.connect(self._on_regime_setup_apply)
        button_layout.addWidget(self._regime_setup_apply_btn)
        layout.addLayout(button_layout)

        # Load default preset
        self._on_regime_setup_preset_changed(0)

    def _create_regime_param_ranges_group(self) -> QGroupBox:
        """Create parameter ranges group with spinboxes.

        Returns:
            QGroupBox with parameter range controls
        """
        group = QGroupBox("Parameter Ranges")
        form = QFormLayout(group)

        # ADX Period
        adx_period_layout = QHBoxLayout()
        adx_period_min = QSpinBox()
        adx_period_min.setRange(3, 50)
        adx_period_min.setValue(10)
        adx_period_min.valueChanged.connect(self._update_combinations_count)
        adx_period_layout.addWidget(QLabel("Min:"))
        adx_period_layout.addWidget(adx_period_min)

        adx_period_max = QSpinBox()
        adx_period_max.setRange(3, 50)
        adx_period_max.setValue(30)
        adx_period_max.valueChanged.connect(self._update_combinations_count)
        adx_period_layout.addWidget(QLabel("Max:"))
        adx_period_layout.addWidget(adx_period_max)
        adx_period_layout.addStretch()

        form.addRow("ADX Period:", adx_period_layout)
        self._regime_setup_param_widgets["adx_period"] = (adx_period_min, adx_period_max)

        # ADX Threshold
        adx_threshold_layout = QHBoxLayout()
        adx_threshold_min = QSpinBox()
        adx_threshold_min.setRange(10, 70)
        adx_threshold_min.setValue(20)
        adx_threshold_min.valueChanged.connect(self._update_combinations_count)
        adx_threshold_layout.addWidget(QLabel("Min:"))
        adx_threshold_layout.addWidget(adx_threshold_min)

        adx_threshold_max = QSpinBox()
        adx_threshold_max.setRange(10, 70)
        adx_threshold_max.setValue(35)
        adx_threshold_max.valueChanged.connect(self._update_combinations_count)
        adx_threshold_layout.addWidget(QLabel("Max:"))
        adx_threshold_layout.addWidget(adx_threshold_max)
        adx_threshold_layout.addStretch()

        form.addRow("ADX Threshold:", adx_threshold_layout)
        self._regime_setup_param_widgets["adx_threshold"] = (adx_threshold_min, adx_threshold_max)

        # SMA Fast Period
        sma_fast_layout = QHBoxLayout()
        sma_fast_min = QSpinBox()
        sma_fast_min.setRange(10, 200)
        sma_fast_min.setValue(20)
        sma_fast_min.valueChanged.connect(self._update_combinations_count)
        sma_fast_layout.addWidget(QLabel("Min:"))
        sma_fast_layout.addWidget(sma_fast_min)

        sma_fast_max = QSpinBox()
        sma_fast_max.setRange(10, 200)
        sma_fast_max.setValue(100)
        sma_fast_max.valueChanged.connect(self._update_combinations_count)
        sma_fast_layout.addWidget(QLabel("Max:"))
        sma_fast_layout.addWidget(sma_fast_max)
        sma_fast_layout.addStretch()

        form.addRow("SMA Fast Period:", sma_fast_layout)
        self._regime_setup_param_widgets["sma_fast_period"] = (sma_fast_min, sma_fast_max)

        # SMA Slow Period
        sma_slow_layout = QHBoxLayout()
        sma_slow_min = QSpinBox()
        sma_slow_min.setRange(50, 500)
        sma_slow_min.setValue(100)
        sma_slow_min.valueChanged.connect(self._update_combinations_count)
        sma_slow_layout.addWidget(QLabel("Min:"))
        sma_slow_layout.addWidget(sma_slow_min)

        sma_slow_max = QSpinBox()
        sma_slow_max.setRange(50, 500)
        sma_slow_max.setValue(300)
        sma_slow_max.valueChanged.connect(self._update_combinations_count)
        sma_slow_layout.addWidget(QLabel("Max:"))
        sma_slow_layout.addWidget(sma_slow_max)
        sma_slow_layout.addStretch()

        form.addRow("SMA Slow Period:", sma_slow_layout)
        self._regime_setup_param_widgets["sma_slow_period"] = (sma_slow_min, sma_slow_max)

        # RSI Period
        rsi_period_layout = QHBoxLayout()
        rsi_period_min = QSpinBox()
        rsi_period_min.setRange(5, 30)
        rsi_period_min.setValue(10)
        rsi_period_min.valueChanged.connect(self._update_combinations_count)
        rsi_period_layout.addWidget(QLabel("Min:"))
        rsi_period_layout.addWidget(rsi_period_min)

        rsi_period_max = QSpinBox()
        rsi_period_max.setRange(5, 30)
        rsi_period_max.setValue(20)
        rsi_period_max.valueChanged.connect(self._update_combinations_count)
        rsi_period_layout.addWidget(QLabel("Max:"))
        rsi_period_layout.addWidget(rsi_period_max)
        rsi_period_layout.addStretch()

        form.addRow("RSI Period:", rsi_period_layout)
        self._regime_setup_param_widgets["rsi_period"] = (rsi_period_min, rsi_period_max)

        # RSI Sideways Low
        rsi_low_layout = QHBoxLayout()
        rsi_low_min = QSpinBox()
        rsi_low_min.setRange(20, 50)
        rsi_low_min.setValue(30)
        rsi_low_min.valueChanged.connect(self._update_combinations_count)
        rsi_low_layout.addWidget(QLabel("Min:"))
        rsi_low_layout.addWidget(rsi_low_min)

        rsi_low_max = QSpinBox()
        rsi_low_max.setRange(20, 50)
        rsi_low_max.setValue(45)
        rsi_low_max.valueChanged.connect(self._update_combinations_count)
        rsi_low_layout.addWidget(QLabel("Max:"))
        rsi_low_layout.addWidget(rsi_low_max)
        rsi_low_layout.addStretch()

        form.addRow("RSI Sideways Low:", rsi_low_layout)
        self._regime_setup_param_widgets["rsi_sideways_low"] = (rsi_low_min, rsi_low_max)

        # RSI Sideways High
        rsi_high_layout = QHBoxLayout()
        rsi_high_min = QSpinBox()
        rsi_high_min.setRange(50, 80)
        rsi_high_min.setValue(55)
        rsi_high_min.valueChanged.connect(self._update_combinations_count)
        rsi_high_layout.addWidget(QLabel("Min:"))
        rsi_high_layout.addWidget(rsi_high_min)

        rsi_high_max = QSpinBox()
        rsi_high_max.setRange(50, 80)
        rsi_high_max.setValue(70)
        rsi_high_max.valueChanged.connect(self._update_combinations_count)
        rsi_high_layout.addWidget(QLabel("Max:"))
        rsi_high_layout.addWidget(rsi_high_max)
        rsi_high_layout.addStretch()

        form.addRow("RSI Sideways High:", rsi_high_layout)
        self._regime_setup_param_widgets["rsi_sideways_high"] = (rsi_high_min, rsi_high_max)

        # BB Period
        bb_period_layout = QHBoxLayout()
        bb_period_min = QSpinBox()
        bb_period_min.setRange(10, 50)
        bb_period_min.setValue(15)
        bb_period_min.valueChanged.connect(self._update_combinations_count)
        bb_period_layout.addWidget(QLabel("Min:"))
        bb_period_layout.addWidget(bb_period_min)

        bb_period_max = QSpinBox()
        bb_period_max.setRange(10, 50)
        bb_period_max.setValue(30)
        bb_period_max.valueChanged.connect(self._update_combinations_count)
        bb_period_layout.addWidget(QLabel("Max:"))
        bb_period_layout.addWidget(bb_period_max)
        bb_period_layout.addStretch()

        form.addRow("BB Period:", bb_period_layout)
        self._regime_setup_param_widgets["bb_period"] = (bb_period_min, bb_period_max)

        # BB Std Dev (Standard Deviation)
        bb_std_layout = QHBoxLayout()
        bb_std_min = QDoubleSpinBox()
        bb_std_min.setRange(0.5, 5.0)
        bb_std_min.setSingleStep(0.1)
        bb_std_min.setDecimals(1)
        bb_std_min.setValue(1.5)
        bb_std_min.valueChanged.connect(self._update_combinations_count)
        bb_std_layout.addWidget(QLabel("Min:"))
        bb_std_layout.addWidget(bb_std_min)

        bb_std_max = QDoubleSpinBox()
        bb_std_max.setRange(0.5, 5.0)
        bb_std_max.setSingleStep(0.1)
        bb_std_max.setDecimals(1)
        bb_std_max.setValue(3.0)
        bb_std_max.valueChanged.connect(self._update_combinations_count)
        bb_std_layout.addWidget(QLabel("Max:"))
        bb_std_layout.addWidget(bb_std_max)
        bb_std_layout.addStretch()

        form.addRow("BB Std Dev:", bb_std_layout)
        self._regime_setup_param_widgets["bb_std_dev"] = (bb_std_min, bb_std_max)

        # BB Width Percentile
        bb_width_layout = QHBoxLayout()
        bb_width_min = QSpinBox()
        bb_width_min.setRange(5, 50)
        bb_width_min.setValue(10)
        bb_width_min.valueChanged.connect(self._update_combinations_count)
        bb_width_layout.addWidget(QLabel("Min:"))
        bb_width_layout.addWidget(bb_width_min)

        bb_width_max = QSpinBox()
        bb_width_max.setRange(5, 50)
        bb_width_max.setValue(40)
        bb_width_max.valueChanged.connect(self._update_combinations_count)
        bb_width_layout.addWidget(QLabel("Max:"))
        bb_width_layout.addWidget(bb_width_max)
        bb_width_layout.addStretch()

        form.addRow("BB Width Percentile:", bb_width_layout)
        self._regime_setup_param_widgets["bb_width_percentile"] = (bb_width_min, bb_width_max)

        return group

    def _on_regime_setup_mode_changed(self, state: int) -> None:
        """Handle auto/manual mode toggle.

        Args:
            state: Qt.CheckState
        """
        auto_mode = state == Qt.CheckState.Checked.value
        self._regime_setup_preset_combo.setEnabled(auto_mode)

        # Enable/disable manual editing of spinboxes
        for min_spin, max_spin in self._regime_setup_param_widgets.values():
            min_spin.setEnabled(not auto_mode)
            max_spin.setEnabled(not auto_mode)

        if auto_mode:
            self._on_regime_setup_preset_changed(self._regime_setup_preset_combo.currentIndex())

    def _on_regime_setup_preset_changed(self, index: int) -> None:
        """Handle preset selection.

        Args:
            index: Preset index
        """
        presets = {
            0: {  # Conservative
                "adx_period": (12, 18),
                "adx_threshold": (23, 30),
                "sma_fast_period": (40, 60),
                "sma_slow_period": (150, 200),
                "rsi_period": (12, 16),
                "rsi_sideways_low": (35, 40),
                "rsi_sideways_high": (60, 65),
                "bb_period": (18, 24),
                "bb_std_dev": (1.8, 2.2),
                "bb_width_percentile": (15, 25),
            },
            1: {  # Standard
                "adx_period": (10, 30),
                "adx_threshold": (20, 35),
                "sma_fast_period": (20, 100),
                "sma_slow_period": (100, 300),
                "rsi_period": (10, 20),
                "rsi_sideways_low": (30, 45),
                "rsi_sideways_high": (55, 70),
                "bb_period": (15, 30),
                "bb_std_dev": (1.5, 3.0),
                "bb_width_percentile": (10, 40),
            },
            2: {  # Aggressive
                "adx_period": (7, 35),
                "adx_threshold": (15, 45),
                "sma_fast_period": (10, 150),
                "sma_slow_period": (50, 400),
                "rsi_period": (7, 25),
                "rsi_sideways_low": (25, 50),
                "rsi_sideways_high": (50, 75),
                "bb_period": (10, 40),
                "bb_std_dev": (1.0, 4.0),
                "bb_width_percentile": (5, 45),
            },
            3: {  # Custom (no change)
                "adx_period": None,
                "adx_threshold": None,
                "sma_fast_period": None,
                "sma_slow_period": None,
                "rsi_period": None,
                "rsi_sideways_low": None,
                "rsi_sideways_high": None,
                "bb_period": None,
                "bb_std_dev": None,
                "bb_width_percentile": None,
            },
        }

        preset = presets.get(index, presets[1])

        for param_name, (min_spin, max_spin) in self._regime_setup_param_widgets.items():
            if preset[param_name] is not None:
                min_val, max_val = preset[param_name]
                min_spin.setValue(min_val)
                max_spin.setValue(max_val)

        self._update_combinations_count()

    def _update_combinations_count(self) -> None:
        """Update estimated combinations counter."""
        # For TPE, we don't test all combinations
        # Just show the configured max_trials (150 default)
        max_trials = 150  # From OptimizationConfig.STANDARD

        self._regime_setup_combinations_label.setText(f"{max_trials} (TPE-optimized)")

        # Calculate actual grid search size for reference
        grid_size = 1
        for min_spin, max_spin in self._regime_setup_param_widgets.values():
            min_val = min_spin.value()
            max_val = max_spin.value()
            range_size = max(1, max_val - min_val + 1)
            grid_size *= range_size

        if grid_size > 1000000:
            grid_text = f"(Grid search would be {grid_size:,} trials - impractical!)"
            self._regime_setup_combinations_label.setToolTip(grid_text)

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

        logger.info(f"Regime setup complete, config: {self._regime_setup_config}")

    def _get_regime_setup_config(self) -> dict:
        """Get current regime setup configuration.

        Returns:
            Dict with parameter ranges
        """
        config = {}
        for param_name, (min_spin, max_spin) in self._regime_setup_param_widgets.items():
            config[param_name] = {
                "min": min_spin.value(),
                "max": max_spin.value(),
            }

        config["preset"] = self._regime_setup_preset_combo.currentText()
        config["auto_mode"] = self._regime_setup_auto_mode.isChecked()

        return config

    @pyqtSlot()
    def _on_regime_setup_import(self) -> None:
        """Import regime configuration with parameter ranges from JSON file."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json

        # Get default import directory
        project_root = Path(__file__).parent.parent.parent.parent
        default_dir = project_root / "03_JSON" / "Entry_Analyzer"
        default_dir.mkdir(parents=True, exist_ok=True)

        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Regime Configuration",
            str(default_dir),
            "JSON Files (*.json)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Load JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check version
            if data.get("version") != "2.0":
                QMessageBox.warning(
                    self,
                    "Version Mismatch",
                    f"File version {data.get('version')} may not be compatible with v2.0. Importing anyway..."
                )

            # Extract parameter ranges
            param_ranges = data.get("parameter_ranges", {})
            if not param_ranges:
                QMessageBox.warning(
                    self,
                    "No Parameter Ranges",
                    "File does not contain parameter_ranges. Cannot import."
                )
                return

            # Update UI with imported ranges
            for param_name, range_dict in param_ranges.items():
                if param_name in self._regime_setup_param_widgets:
                    min_spin, max_spin = self._regime_setup_param_widgets[param_name]

                    # Set values
                    min_val = range_dict.get("min")
                    max_val = range_dict.get("max")

                    if min_val is not None:
                        min_spin.setValue(min_val)
                    if max_val is not None:
                        max_spin.setValue(max_val)

            # Update max_trials if present
            max_trials_meta = data.get("meta", {}).get("max_trials")
            if max_trials_meta and hasattr(self, "_regime_setup_max_trials"):
                self._regime_setup_max_trials.setValue(max_trials_meta)

            # Switch to Custom preset
            self._regime_setup_preset_combo.setCurrentText("Custom")
            self._regime_setup_auto_mode.setChecked(False)

            # Update combination counter
            self._update_combinations_count()

            logger.info(f"Imported regime configuration from {file_path}")

            QMessageBox.information(
                self,
                "Import Successful",
                f"Imported parameter ranges from:\n{file_path}\n\nPreset set to 'Custom'."
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Invalid JSON",
                f"File is not valid JSON:\n{str(e)}"
            )
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import configuration:\n{str(e)}"
            )
