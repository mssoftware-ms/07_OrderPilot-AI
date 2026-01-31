"""Backtest Config UI - Widget setup and layout.

Extracted from entry_analyzer_backtest_config.py (lines 83-227)
Handles UI setup for the Regime Analysis tab.

Components:
- Chart data information group (start/end day, period, bars)
- Analyze visible range button
- Detected regimes results table (8 columns)
- Regime config table (52 columns wide format)
- Load/Save/Save As buttons

Date: 2026-01-31 (Task 3.2.1 - Patch 1)
LOC: ~280
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)

# Import icon provider (Issue #12)
from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass


class BacktestConfigUIMixin:
    """UI setup for regime analysis tab.

    Provides widget creation and layout management for:
    - Chart data information display
    - Regime analysis controls
    - Detected regimes results table
    - Regime config editing table

    Attributes (defined in parent class):
        _regime_start_day: QLabel - Chart start day
        _regime_end_day: QLabel - Chart end day
        _regime_period_days: QLabel - Period in days
        _regime_num_bars: QLabel - Number of bars
        _detected_regimes_table: QTableWidget - Results table
        _regime_config_path_label: QLabel - Config path display
        _regime_config_table: QTableWidget - Config table (52 columns)
        _regime_config_load_btn: QPushButton - Load button
        _regime_config_save_btn: QPushButton - Save button
        _regime_config_save_as_btn: QPushButton - Save as button
        _regime_config_dirty: bool - Unsaved changes flag
    """

    def _setup_backtest_config_tab(self, tab: QWidget) -> None:
        """Setup Regime Analysis tab.

        Issue #21: Completely refactored from "Backtest Setup" to "Regime"
        - Removed: Load Strategy, Run Backtest, Regime Set Dropdown
        - Added: Chart data fields (Start/End Day, Period, Bars)
        - Added: Analyze Visible Range button
        - Added: Regime detection table with timestamps
        """
        layout = QVBoxLayout(tab)

        # ===== Chart Data Information Section =====
        chart_info_group = self._create_chart_info_group()
        layout.addWidget(chart_info_group)

        # ===== Analyze Visible Range Button =====
        analyze_range_btn = self._create_analyze_button()
        layout.addWidget(analyze_range_btn)

        # ===== Regime Detection Results Table =====
        results_group = self._create_results_table_group()
        layout.addWidget(results_group)

        # ===== Regime Config (JSON) Table =====
        config_group = self._create_config_table_group()
        layout.addWidget(config_group, stretch=2)  # Give more vertical space

        # Load default config
        self._load_default_regime_config()

        layout.addStretch()

    def _create_chart_info_group(self) -> QGroupBox:
        """Create chart data information group box.

        Returns:
            QGroupBox with chart data fields (start/end day, period, bars)
        """
        chart_info_group = QGroupBox("Chart Data Information")
        chart_info_layout = QFormLayout()

        # Start Day (read-only, filled from chart)
        self._regime_start_day = QLabel("Not loaded")
        self._regime_start_day.setStyleSheet("color: #888;")
        chart_info_layout.addRow("Start Day:", self._regime_start_day)

        # End Day (read-only, filled from chart)
        self._regime_end_day = QLabel("Not loaded")
        self._regime_end_day.setStyleSheet("color: #888;")
        chart_info_layout.addRow("End Day:", self._regime_end_day)

        # Period in Days (read-only, calculated)
        self._regime_period_days = QLabel("0 days")
        self._regime_period_days.setStyleSheet("color: #888;")
        chart_info_layout.addRow("Period (Days):", self._regime_period_days)

        # Number of Bars (read-only, from chart)
        self._regime_num_bars = QLabel("0 bars")
        self._regime_num_bars.setStyleSheet("color: #888;")
        chart_info_layout.addRow("Number of Bars:", self._regime_num_bars)

        chart_info_group.setLayout(chart_info_layout)
        return chart_info_group

    def _create_analyze_button(self) -> QPushButton:
        """Create analyze visible range button.

        Returns:
            QPushButton connected to analysis handler
        """
        analyze_range_btn = QPushButton(" Analyze Visible Range")
        analyze_range_btn.setIcon(get_icon("timeline"))  # Timeline icon for range analysis
        analyze_range_btn.setProperty("class", "success")  # Use theme success color
        analyze_range_btn.clicked.connect(self._on_analyze_visible_range_clicked)
        return analyze_range_btn

    def _create_results_table_group(self) -> QGroupBox:
        """Create regime detection results table group box.

        Returns:
            QGroupBox with 8-column results table showing regime periods
        """
        results_group = QGroupBox("Detected Regimes (Periods)")
        results_layout = QVBoxLayout()

        # Create results table (8 columns: Start Date/Time, End Date/Time, Regime, Score, Duration)
        self._detected_regimes_table = QTableWidget()
        self._detected_regimes_table.setColumnCount(8)
        self._detected_regimes_table.setHorizontalHeaderLabels(
            [
                "Start Date",
                "Start Time",
                "End Date",
                "End Time",
                "Regime",
                "Score",
                "Duration (Bars)",
                "Duration (Time)",
            ]
        )
        self._detected_regimes_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._detected_regimes_table.setAlternatingRowColors(True)
        self._detected_regimes_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )  # Read-only
        self._detected_regimes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        results_layout.addWidget(self._detected_regimes_table)
        results_group.setLayout(results_layout)
        return results_group

    def _create_config_table_group(self) -> QGroupBox:
        """Create regime config editing table group box.

        Returns:
            QGroupBox with 52-column config table and load/save buttons
        """
        config_group = QGroupBox("Regime Config (JSON)")
        config_layout = QVBoxLayout()

        # ===== Path and buttons row =====
        path_layout = self._create_config_path_layout()
        config_layout.addLayout(path_layout)

        # ===== Wide config table (52 columns) =====
        self._regime_config_table = self._create_config_table()
        config_layout.addWidget(self._regime_config_table)

        config_group.setLayout(config_layout)
        return config_group

    def _create_config_path_layout(self) -> QHBoxLayout:
        """Create config path display and button layout.

        Returns:
            QHBoxLayout with path label and Load/Save/Save As buttons
        """
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Config:"))

        # Path label
        self._regime_config_path_label = QLabel("Not loaded")
        self._regime_config_path_label.setStyleSheet("color: #888;")
        path_layout.addWidget(self._regime_config_path_label, 1)

        # Load button
        self._regime_config_load_btn = QPushButton(get_icon("folder_open"), "Load")
        self._regime_config_load_btn.setToolTip("Load Regime Config from JSON file")
        self._regime_config_load_btn.clicked.connect(self._on_load_regime_config_clicked)
        path_layout.addWidget(self._regime_config_load_btn)

        # Save button
        self._regime_config_save_btn = QPushButton(get_icon("save"), "Save")
        self._regime_config_save_btn.setToolTip("Save changes to current JSON file")
        self._regime_config_save_btn.clicked.connect(self._on_save_regime_config)
        self._regime_config_save_btn.setEnabled(False)
        path_layout.addWidget(self._regime_config_save_btn)

        # Save As button
        self._regime_config_save_as_btn = QPushButton(get_icon("download"), "Save As...")
        self._regime_config_save_as_btn.setToolTip("Save as new JSON file")
        self._regime_config_save_as_btn.clicked.connect(self._on_save_regime_config_as)
        self._regime_config_save_as_btn.setEnabled(False)
        path_layout.addWidget(self._regime_config_save_as_btn)

        return path_layout

    def _create_config_table(self) -> QTableWidget:
        """Create wide 52-column config editing table.

        Table structure:
        - Column 0: Type (Indicator/Regime)
        - Column 1: ID (name)
        - Columns 2-51: [P1 Name, P1 Val, P1 Min, P1 Max, P1 Step] × 10 parameters

        Returns:
            QTableWidget configured for config editing
        """
        table = QTableWidget()
        table.setColumnCount(52)

        # Build header labels
        headers = ["Type", "ID"]
        for i in range(1, 11):
            headers.extend([f"P{i} Name", f"P{i} Val", f"P{i} Min", f"P{i} Max", f"P{i} Step"])
        table.setHorizontalHeaderLabels(headers)

        # Configure column resize modes
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # ID
        for col in range(2, 52):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        # Table appearance
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setMinimumHeight(250)  # +30% higher than default

        # Track changes for dirty flag
        self._regime_config_dirty = False
        table.cellChanged.connect(self._on_regime_config_cell_changed)

        return table
