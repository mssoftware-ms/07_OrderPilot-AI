"""Entry Analyzer - Indicator Setup V2 Mixin (Stage 2).

Handles Indicator Optimization Setup UI for Stage 2:
- Regime selection dropdown (BULL, BEAR, SIDEWAYS)
- Signal type selection (Entry Long/Short, Exit Long/Short)
- 7 indicator selection with checkboxes (RSI, MACD, STOCH, BB, ATR, EMA, CCI)
- Dynamic parameter range configuration
- Loads bar indices from optimized_regime_*.json

Date: 2026-01-24
Stage: 2 (Indicator Optimization)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IndicatorSetupV2Mixin:
    """Stage 2: Indicator Setup UI for regime-specific optimization.

    Provides:
    - Regime selection dropdown (loads bar indices from JSON)
    - Signal type checkboxes (entry_long, entry_short, exit_long, exit_short)
    - 7 indicator checkboxes (RSI, MACD, STOCH, BB, ATR, EMA, CCI)
    - Dynamic parameter range widgets per indicator
    - Validation and UI state management

    Attributes (defined in parent):
        _ind_v2_regime_combo: QComboBox - Regime selector
        _ind_v2_signal_types: dict[str, QCheckBox] - Signal type checkboxes
        _ind_v2_indicator_checkboxes: dict[str, QCheckBox] - Indicator selection
        _ind_v2_param_widgets: dict - Parameter range widgets
        _ind_v2_param_layout: QFormLayout - Dynamic parameter layout
        _regime_bar_indices: dict[str, list[int]] - Bar indices per regime
        _optimized_regime_config: dict - Loaded regime config
    """

    # Type hints for parent attributes
    _ind_v2_regime_combo: QComboBox
    _ind_v2_signal_types: dict[str, QCheckBox]
    _ind_v2_indicator_checkboxes: dict[str, QCheckBox]
    _ind_v2_param_widgets: dict
    _ind_v2_param_layout: QFormLayout
    _regime_bar_indices: dict[str, list[int]]
    _optimized_regime_config: dict | None
    _symbol: str
    _timeframe: str

    def _setup_indicator_setup_v2_tab(self, tab: QWidget) -> None:
        """Setup Indicator Setup V2 tab (Stage 2).

        Creates:
        - Regime selection dropdown
        - Signal type selector (4 checkboxes)
        - Indicator selection (7 checkboxes)
        - Dynamic parameter ranges
        """
        layout = QVBoxLayout(tab)

        # ===== Regime Selection Group =====
        regime_group = QGroupBox("Regime Selection")
        regime_layout = QHBoxLayout(regime_group)

        regime_layout.addWidget(QLabel("Select Regime:"))
        self._ind_v2_regime_combo = QComboBox()
        self._ind_v2_regime_combo.addItems(["BULL", "BEAR", "SIDEWAYS"])
        self._ind_v2_regime_combo.currentTextChanged.connect(self._on_indicator_v2_regime_changed)
        regime_layout.addWidget(self._ind_v2_regime_combo)

        # Regime info label
        self._ind_v2_regime_info = QLabel("No regime config loaded")
        self._ind_v2_regime_info.setStyleSheet("color: #888; font-style: italic;")
        regime_layout.addWidget(self._ind_v2_regime_info)
        regime_layout.addStretch()

        layout.addWidget(regime_group)

        # ===== Signal Type Selection Group =====
        signal_group = QGroupBox("Signal Types to Optimize")
        signal_layout = QVBoxLayout(signal_group)

        info_label = QLabel("Select which signal types to optimize for the selected regime:")
        info_label.setStyleSheet("color: #888; font-style: italic;")
        signal_layout.addWidget(info_label)

        # 4 signal type checkboxes
        signal_checkbox_layout = QHBoxLayout()
        self._ind_v2_signal_types = {
            "entry_long": QCheckBox("Entry Long"),
            "entry_short": QCheckBox("Entry Short"),
            "exit_long": QCheckBox("Exit Long"),
            "exit_short": QCheckBox("Exit Short"),
        }

        # Default: Entry Long and Exit Long enabled
        self._ind_v2_signal_types["entry_long"].setChecked(True)
        self._ind_v2_signal_types["exit_long"].setChecked(True)

        for signal_type, checkbox in self._ind_v2_signal_types.items():
            signal_checkbox_layout.addWidget(checkbox)

        signal_checkbox_layout.addStretch()
        signal_layout.addLayout(signal_checkbox_layout)
        layout.addWidget(signal_group)

        # ===== Indicator Selection Group =====
        indicator_group = QGroupBox("Select Indicators to Test (Stage 2)")
        indicator_layout = QVBoxLayout(indicator_group)

        # Info about Stage 2 indicators
        stage_info = QLabel("Stage 2 Indicators: RSI, MACD, STOCH, BB, ATR, EMA, CCI (7 total)")
        stage_info.setStyleSheet("color: #555; font-weight: bold;")
        indicator_layout.addWidget(stage_info)

        # 7 indicator checkboxes in 2 rows
        indicators_grid = QHBoxLayout()
        self._ind_v2_indicator_checkboxes = {
            "RSI": QCheckBox("RSI (Momentum)"),
            "MACD": QCheckBox("MACD (Trend-Momentum)"),
            "STOCH": QCheckBox("Stochastic (Mean-Reversion)"),
            "BB": QCheckBox("Bollinger Bands (Volatility)"),
            "ATR": QCheckBox("ATR (Trailing Stops)"),
            "EMA": QCheckBox("EMA (Trend-Following)"),
            "CCI": QCheckBox("CCI (Overbought/Oversold)"),
        }

        # Default: Select RSI, MACD, ATR (most common for entries/exits)
        self._ind_v2_indicator_checkboxes["RSI"].setChecked(True)
        self._ind_v2_indicator_checkboxes["MACD"].setChecked(True)
        self._ind_v2_indicator_checkboxes["ATR"].setChecked(True)

        # Add checkboxes to layout (2 columns)
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        for idx, (ind_name, checkbox) in enumerate(self._ind_v2_indicator_checkboxes.items()):
            checkbox.stateChanged.connect(self._on_indicator_v2_selection_changed)
            if idx < 4:
                col1.addWidget(checkbox)
            else:
                col2.addWidget(checkbox)

        col1.addStretch()
        col2.addStretch()
        indicators_grid.addLayout(col1)
        indicators_grid.addLayout(col2)

        indicator_layout.addLayout(indicators_grid)
        layout.addWidget(indicator_group)

        # ===== Parameter Ranges Group =====
        param_group = QGroupBox("Parameter Ranges (Dynamic)")
        param_layout = QVBoxLayout(param_group)

        param_info = QLabel("Select indicators above to configure their optimization ranges.")
        param_info.setStyleSheet("color: #888; font-style: italic;")
        param_layout.addWidget(param_info)

        # Scrollable area for parameter widgets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)

        param_widget = QWidget()
        self._ind_v2_param_layout = QFormLayout(param_widget)
        scroll.setWidget(param_widget)

        param_layout.addWidget(scroll)
        layout.addWidget(param_group)

        # Initialize state
        self._regime_bar_indices = {}
        self._optimized_regime_config = None
        self._ind_v2_param_widgets = {}

        # Initial parameter range update
        self._update_indicator_v2_parameter_ranges()

        layout.addStretch()

    def _on_indicator_v2_regime_changed(self, regime: str) -> None:
        """Handle regime selection change.

        Loads bar indices for the selected regime from optimized_regime_*.json.

        Args:
            regime: Selected regime name (BULL, BEAR, SIDEWAYS)
        """
        logger.info(f"Stage 2: Regime changed to {regime}")

        # Try to load bar indices from optimized_regime_*.json
        self._load_regime_bar_indices(regime)

        # Update UI info
        if regime in self._regime_bar_indices:
            bar_count = len(self._regime_bar_indices[regime])
            self._ind_v2_regime_info.setText(
                f"{regime}: {bar_count} bars available for optimization"
            )
            self._ind_v2_regime_info.setStyleSheet("color: #22c55e; font-weight: bold;")
        else:
            self._ind_v2_regime_info.setText(
                f"{regime}: No regime config loaded (load from Stage 1 results)"
            )
            self._ind_v2_regime_info.setStyleSheet("color: #ef4444; font-style: italic;")

    def _load_regime_bar_indices(self, regime: str) -> None:
        """Load bar indices for regime from optimized_regime_*.json.

        Searches for file:
        - 03_JSON/Entry_Analyzer/Regime/STUFE_1_Regime/optimized_regime_{symbol}_{timeframe}.json

        Args:
            regime: Regime name (BULL, BEAR, SIDEWAYS)
        """
        try:
            # Build path to optimized_regime_*.json
            project_root = Path(__file__).parents[4]  # Go up to project root
            regime_file = (
                project_root
                / "03_JSON"
                / "Entry_Analyzer"
                / "Regime"
                / "STUFE_1_Regime"
                / f"optimized_regime_{self._symbol}_{self._timeframe}.json"
            )

            if not regime_file.exists():
                logger.warning(f"Regime config not found: {regime_file}")
                return

            # Load regime config
            with open(regime_file, "r", encoding="utf-8") as f:
                self._optimized_regime_config = json.load(f)

            # Extract bar indices for each regime
            regimes = self._optimized_regime_config.get("regimes", [])
            for regime_data in regimes:
                regime_name = regime_data.get("name")
                periods = regime_data.get("periods", [])

                # Collect all bar indices for this regime
                bar_indices = []
                for period in periods:
                    start_idx = period.get("start_index", 0)
                    end_idx = period.get("end_index", 0)
                    bar_indices.extend(range(start_idx, end_idx + 1))

                self._regime_bar_indices[regime_name] = sorted(set(bar_indices))

            logger.info(f"Loaded regime config with {len(self._regime_bar_indices)} regimes")
            logger.debug(
                f"Regime bar counts: {[(r, len(idxs)) for r, idxs in self._regime_bar_indices.items()]}"
            )

        except Exception as e:
            logger.error(f"Failed to load regime config: {e}", exc_info=True)
            self._regime_bar_indices = {}
            self._optimized_regime_config = None

    def _on_indicator_v2_selection_changed(self) -> None:
        """Handle indicator selection change.

        Updates parameter range widgets based on selected indicators.
        """
        self._update_indicator_v2_parameter_ranges()

    def _update_indicator_v2_parameter_ranges(self) -> None:
        """Dynamically update parameter range widgets for selected indicators.

        Creates Min/Max/Step spinboxes for each parameter of selected indicators.
        Follows the parameter configurations from Stage 2 (7 indicators).
        """
        # Clear existing widgets
        while self._ind_v2_param_layout.count():
            item = self._ind_v2_param_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        self._ind_v2_param_widgets.clear()

        # Get selected indicators
        selected_indicators = [
            ind_id for ind_id, cb in self._ind_v2_indicator_checkboxes.items() if cb.isChecked()
        ]

        if not selected_indicators:
            self._ind_v2_param_layout.addRow(QLabel("No indicators selected"))
            return

        # Define parameter configurations for Stage 2 indicators
        # Format: (param_name, min, max, default_min, default_max, step)
        param_configs = {
            "RSI": [("period", 5, 50, 9, 21, 2)],
            "MACD": [
                ("fast", 5, 30, 8, 16, 2),
                ("slow", 15, 50, 20, 30, 5),
                ("signal", 5, 20, 7, 11, 2),
            ],
            "STOCH": [
                ("k_period", 5, 30, 10, 18, 2),
                ("d_period", 3, 10, 3, 5, 1),
            ],
            "BB": [
                ("period", 10, 40, 20, 30, 5),
                ("std", 1.5, 3.0, 2.0, 2.5, 0.5),
            ],
            "ATR": [
                ("period", 5, 30, 10, 20, 2),
                ("multiplier", 1.0, 4.0, 2.0, 3.0, 0.5),
            ],
            "EMA": [("period", 10, 200, 20, 100, 10)],
            "CCI": [("period", 10, 40, 15, 25, 5)],
        }

        # Create parameter widgets for selected indicators
        for indicator_id in selected_indicators:
            if indicator_id not in param_configs:
                continue

            # Add indicator header
            header_label = QLabel(f"<b>{indicator_id}</b>")
            self._ind_v2_param_layout.addRow(header_label)

            self._ind_v2_param_widgets[indicator_id] = {}

            for param_config in param_configs[indicator_id]:
                param_name, abs_min, abs_max, default_min, default_max, step = param_config

                # Create horizontal layout for Min/Max/Step
                param_layout = QHBoxLayout()

                # Determine if float or int parameter
                is_float = isinstance(step, float)

                # Min spinbox
                if is_float:
                    min_spin = QDoubleSpinBox()
                    min_spin.setDecimals(2)
                else:
                    min_spin = QSpinBox()

                min_spin.setMinimum(abs_min)
                min_spin.setMaximum(abs_max)
                min_spin.setValue(default_min)
                min_spin.setSingleStep(step)
                min_spin.setPrefix("Min: ")
                param_layout.addWidget(min_spin)

                # Max spinbox
                if is_float:
                    max_spin = QDoubleSpinBox()
                    max_spin.setDecimals(2)
                else:
                    max_spin = QSpinBox()

                max_spin.setMinimum(abs_min)
                max_spin.setMaximum(abs_max)
                max_spin.setValue(default_max)
                max_spin.setSingleStep(step)
                max_spin.setPrefix("Max: ")
                param_layout.addWidget(max_spin)

                # Step spinbox
                if is_float:
                    step_spin = QDoubleSpinBox()
                    step_spin.setDecimals(2)
                else:
                    step_spin = QSpinBox()

                step_spin.setMinimum(step)
                step_spin.setMaximum(abs_max - abs_min)
                step_spin.setValue(step)
                step_spin.setSingleStep(step)
                step_spin.setPrefix("Step: ")
                param_layout.addWidget(step_spin)

                # Store widgets
                self._ind_v2_param_widgets[indicator_id][param_name] = {
                    "min": min_spin,
                    "max": max_spin,
                    "step": step_spin,
                }

                # Add to form
                self._ind_v2_param_layout.addRow(f"{param_name}:", param_layout)
