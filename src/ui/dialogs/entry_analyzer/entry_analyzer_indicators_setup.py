"""Entry Analyzer - Indicator Optimization Setup Mixin.

Extracted from entry_analyzer_indicators.py to keep files under 550 LOC.
Handles indicator optimization UI setup:
- Indicator selection with 20 indicators in 6 categories
- Dynamic parameter range configuration with Min/Max/Step spinboxes
- Test mode selection (Entry/Exit)
- Trade side selection (Long/Short)
- Optimization setup and results tabs

Date: 2026-01-21
LOC: ~390
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IndicatorsSetupMixin:
    """Indicator optimization setup functionality.

    Provides UI configuration for indicator optimization with:
    - 20 indicators across 6 categories (TREND, BREAKOUT, REGIME, MOMENTUM, VOLATILITY, VOLUME)
    - Dynamic parameter range widgets (Min/Max/Step spinboxes)
    - Test mode selection (Entry/Exit)
    - Trade side selection (Long/Short)
    - Results table with 9 columns
    - Action buttons (Draw Indicators, Show Entries, Create Regime Set)

    Attributes (defined in parent class):
        _opt_indicator_checkboxes: dict[str, QCheckBox] - Indicator selection checkboxes
        _param_widgets: dict[str, dict[str, dict[str, QSpinBox | QDoubleSpinBox]]] - Parameter range widgets
        _param_layout: QFormLayout - Dynamic parameter layout
        _test_type_entry: QCheckBox - Entry test mode checkbox
        _test_type_exit: QCheckBox - Exit test mode checkbox
        _trade_side_long: QCheckBox - Long trade side checkbox
        _trade_side_short: QCheckBox - Short trade side checkbox
        _optimization_progress: QLabel - Progress indicator
        _optimize_btn: QPushButton - Optimize button
        _optimization_results_table: QTableWidget - Results table
        _draw_indicators_btn: QPushButton - Draw indicators button
        _show_entries_btn: QPushButton - Show entry signals button
        _create_regime_set_btn: QPushButton - Create regime set button
    """

    # Type hints for parent class attributes
    _opt_indicator_checkboxes: dict[str, QCheckBox]
    _param_widgets: dict[str, dict[str, dict[str, QSpinBox | QDoubleSpinBox]]]
    _param_layout: QFormLayout
    _test_type_entry: QCheckBox
    _test_type_exit: QCheckBox
    _trade_side_long: QCheckBox
    _trade_side_short: QCheckBox
    _optimization_progress: Any
    _optimize_btn: QPushButton
    _optimization_results_table: QTableWidget
    _draw_indicators_btn: QPushButton
    _show_entries_btn: QPushButton
    _create_regime_set_btn: QPushButton

    def _setup_indicator_optimization_tab(self, tab: QWidget) -> None:
        """Setup Indicator Optimization tab with sub-tabs.

        Original: entry_analyzer_indicators.py:112-136

        Creates:
        - Setup sub-tab: Indicator selection + parameter ranges
        - Results sub-tab: Optimization results table + action buttons
        """
        layout = QVBoxLayout(tab)

        # Create sub-tabs
        sub_tabs = QTabWidget()
        layout.addWidget(sub_tabs)

        # Setup tab
        setup_tab = QWidget()
        sub_tabs.addTab(setup_tab, "⚙️ Setup")
        self._setup_optimization_setup_tab(setup_tab)

        # Results tab
        results_tab = QWidget()
        sub_tabs.addTab(results_tab, "📊 Results")
        self._setup_optimization_results_tab(results_tab)

    def _setup_optimization_setup_tab(self, tab: QWidget) -> None:
        """Setup Optimization Setup sub-tab.

        Original: entry_analyzer_indicators.py:137-242

        Features:
        - 20 indicators in 6 categories (TREND, BREAKOUT, REGIME, MOMENTUM, VOLATILITY, VOLUME)
        - Dynamic parameter ranges (updated based on selection)
        - Test mode selection (Entry/Exit)
        - Trade side selection (Long/Short)
        - Progress bar and Optimize button
        """
        layout = QVBoxLayout(tab)

        # Indicator Selection Group
        indicator_group = QGroupBox("📊 Select Indicators to Optimize")
        indicator_layout = QVBoxLayout(indicator_group)

        # Indicator categories with indicators
        indicator_categories = [
            ("TREND & OVERLAY", ['SMA', 'EMA', 'ICHIMOKU', 'PSAR', 'VWAP', 'PIVOTS']),
            ("BREAKOUT & CHANNELS", ['BB', 'KC']),
            ("REGIME & TREND", ['ADX', 'CHOP']),
            ("MOMENTUM", ['RSI', 'MACD', 'STOCH', 'CCI']),
            ("VOLATILITY", ['ATR', 'BB_WIDTH']),
            ("VOLUME", ['OBV', 'MFI', 'AD', 'CMF']),
        ]

        self._opt_indicator_checkboxes = {}

        for category_name, indicators in indicator_categories:
            # Category label
            category_label = QLabel(f"<b>{category_name}</b>")
            indicator_layout.addWidget(category_label)

            # Grid for indicators (3 columns)
            grid = QGridLayout()
            for idx, ind in enumerate(indicators):
                row = idx // 3
                col = idx % 3
                checkbox = QCheckBox(ind)
                checkbox.stateChanged.connect(self._on_indicator_selection_changed)
                self._opt_indicator_checkboxes[ind] = checkbox
                grid.addWidget(checkbox, row, col)

            indicator_layout.addLayout(grid)

        layout.addWidget(indicator_group)

        # Test Mode Group
        test_mode_group = QGroupBox("🎯 Test Mode")
        test_mode_layout = QVBoxLayout(test_mode_group)

        # Test Type: Entry or Exit
        test_type_layout = QHBoxLayout()
        test_type_layout.addWidget(QLabel("Test Type:"))
        self._test_type_entry = QCheckBox("Entry")
        self._test_type_entry.setChecked(True)
        test_type_layout.addWidget(self._test_type_entry)
        self._test_type_exit = QCheckBox("Exit")
        test_type_layout.addWidget(self._test_type_exit)
        test_type_layout.addStretch()
        test_mode_layout.addLayout(test_type_layout)

        # Trade Side: Long or Short
        trade_side_layout = QHBoxLayout()
        trade_side_layout.addWidget(QLabel("Trade Side:"))
        self._trade_side_long = QCheckBox("Long")
        self._trade_side_long.setChecked(True)
        trade_side_layout.addWidget(self._trade_side_long)
        self._trade_side_short = QCheckBox("Short")
        trade_side_layout.addWidget(self._trade_side_short)
        trade_side_layout.addStretch()
        test_mode_layout.addLayout(trade_side_layout)

        layout.addWidget(test_mode_group)

        # Note: Parameter Ranges moved to separate "Parameter Configuration" tab
        # Initialize empty parameter widgets dict (used by Parameter Configuration tab)
        self._param_widgets = {}

        # Progress and Optimize Button
        progress_layout = QHBoxLayout()
        self._optimization_progress = QLabel("Ready")
        progress_layout.addWidget(self._optimization_progress)

        self._optimize_btn = QPushButton("🚀 Optimize Indicators")
        self._optimize_btn.clicked.connect(self._on_optimize_indicators_clicked)
        progress_layout.addWidget(self._optimize_btn)

        layout.addLayout(progress_layout)

    def _setup_optimization_results_tab(self, tab: QWidget) -> None:
        """Setup Optimization Results sub-tab.

        Original: entry_analyzer_indicators.py:244-309

        Features:
        - Results table with 9 columns (Indicator, Parameters, Regime, Test Type, Trade Side, Score, Win Rate, Profit Factor, Trades)
        - Action buttons (Draw Indicators, Show Entry Signals, Create Regime Set)
        - Color-coded score column (green >70, orange 40-70, red <40)
        """
        layout = QVBoxLayout(tab)

        # Results Table
        self._optimization_results_table = QTableWidget()
        self._optimization_results_table.setColumnCount(9)
        self._optimization_results_table.setHorizontalHeaderLabels([
            "Indicator",
            "Parameters",
            "Regime",
            "Test Type",
            "Trade Side",
            "Score (0-100)",
            "Win Rate",
            "Profit Factor",
            "Trades"
        ])

        # Configure table
        header = self._optimization_results_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Indicator
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Parameters
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Regime
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Test Type
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Trade Side
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Score
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Win Rate
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Profit Factor
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Trades

        self._optimization_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._optimization_results_table.setAlternatingRowColors(True)

        layout.addWidget(self._optimization_results_table)

        # Action Buttons
        action_layout = QHBoxLayout()

        self._draw_indicators_btn = QPushButton("📊 Draw Indicators")
        self._draw_indicators_btn.setEnabled(False)
        self._draw_indicators_btn.clicked.connect(self._on_draw_indicators_clicked)
        action_layout.addWidget(self._draw_indicators_btn)

        self._show_entries_btn = QPushButton("📍 Show Entry Signals")
        self._show_entries_btn.setEnabled(False)
        self._show_entries_btn.clicked.connect(self._on_show_entries_clicked)
        action_layout.addWidget(self._show_entries_btn)

        self._create_regime_set_btn = QPushButton("📦 Create Regime Set")
        self._create_regime_set_btn.setEnabled(False)
        # Connected in BacktestMixin: self._create_regime_set_btn.clicked.connect(self._on_create_regime_set_clicked)
        action_layout.addWidget(self._create_regime_set_btn)

        action_layout.addStretch()

        layout.addLayout(action_layout)

    def _on_indicator_selection_changed(self) -> None:
        """Handle indicator selection change.

        Original: entry_analyzer_indicators.py:311-318

        Updates parameter ranges based on selected indicators.
        """
        self._update_parameter_ranges()

    def _update_parameter_ranges(self) -> None:
        """Dynamically update parameter range widgets based on selected indicators.

        Original: entry_analyzer_indicators.py:320-462

        Creates spinboxes for each parameter of selected indicators:
        - Min/Max/Step controls
        - Supports int and float parameters
        - 15 indicators with parameter configurations
        """
        # Clear existing widgets
        while self._param_layout.count():
            item = self._param_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        self._param_widgets.clear()

        # Get selected indicators
        selected_indicators = [
            ind_id for ind_id, cb in self._opt_indicator_checkboxes.items()
            if cb.isChecked()
        ]

        if not selected_indicators:
            self._param_layout.addRow(QLabel("No indicators selected"))
            return

        # Define parameter configurations for each indicator
        # Format: (param_name, min, max, default_min, default_max, step)
        param_configs = {
            'RSI': [('period', 5, 50, 10, 20, 2)],
            'MACD': [
                ('fast', 5, 30, 8, 16, 2),
                ('slow', 15, 50, 20, 30, 5),
                ('signal', 5, 20, 7, 11, 2)
            ],
            'ADX': [('period', 5, 30, 10, 20, 2)],
            'SMA': [('period', 10, 200, 20, 100, 10)],
            'EMA': [('period', 10, 200, 20, 100, 10)],
            'BB': [
                ('period', 10, 40, 20, 30, 5),
                ('std', 1.5, 3.0, 2.0, 2.5, 0.5)
            ],
            'ATR': [('period', 5, 30, 10, 20, 2)],
            'STOCH': [
                ('k_period', 5, 30, 10, 18, 2),
                ('d_period', 3, 10, 3, 5, 1)
            ],
            'CCI': [('period', 10, 40, 15, 25, 5)],
            'KC': [
                ('period', 10, 40, 20, 30, 5),
                ('atr_mult', 1.0, 3.0, 1.5, 2.5, 0.5)
            ],
            'PSAR': [
                ('accel_start', 0.01, 0.05, 0.02, 0.03, 0.01),
                ('accel_max', 0.1, 0.3, 0.15, 0.25, 0.05)
            ],
            'ICHIMOKU': [
                ('conv_period', 5, 15, 8, 10, 1),
                ('base_period', 15, 35, 20, 28, 2)
            ],
            'CHOP': [('period', 10, 30, 12, 18, 2)],
            'BB_WIDTH': [
                ('period', 10, 40, 20, 30, 5),
                ('std', 1.5, 3.0, 2.0, 2.5, 0.5)
            ],
            'MFI': [('period', 10, 30, 12, 18, 2)],
        }

        # Create parameter widgets for selected indicators
        for indicator_id in selected_indicators:
            if indicator_id not in param_configs:
                continue

            # Add indicator header
            header_label = QLabel(f"<b>{indicator_id}</b>")
            self._param_layout.addRow(header_label)

            self._param_widgets[indicator_id] = {}

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
                self._param_widgets[indicator_id][param_name] = {
                    'min': min_spin,
                    'max': max_spin,
                    'step': step_spin
                }

                # Add to form
                self._param_layout.addRow(f"{param_name}:", param_layout)

    def _setup_parameter_configuration_tab(self, tab: QWidget) -> None:
        """Setup Parameter Configuration tab.

        New tab created to avoid UI overlapping in Indicator Optimization.
        Contains the Parameter Ranges GroupBox with dynamic parameter widgets.

        Date: 2026-01-22
        """
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel(
            "<h3>⚙️ Parameter Configuration</h3>"
            "<p>Configure parameter ranges for selected indicators. "
            "Min/Max values define the search space, Step controls optimization granularity.</p>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        # Parameter Ranges Group (dynamic, scrollable)
        param_ranges_group = QGroupBox("📊 Parameter Ranges (Dynamic)")
        param_ranges_layout = QVBoxLayout(param_ranges_group)

        # Info label
        info_label = QLabel(
            "💡 Tip: Select indicators in the <b>Indicator Optimization > Setup</b> tab first."
        )
        info_label.setStyleSheet("color: #888; font-style: italic;")
        param_ranges_layout.addWidget(info_label)

        # Scroll area for dynamic parameter widgets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)

        param_widget = QWidget()
        self._param_layout = QFormLayout(param_widget)
        scroll.setWidget(param_widget)

        param_ranges_layout.addWidget(scroll)
        layout.addWidget(param_ranges_group)

        layout.addStretch()
