"""Regime Optimization - Initialization Mixin.

Handles UI setup and widget initialization for the regime optimization tab.

Agent: CODER-013
Task: 3.1.3 - Split regime_optimization_mixin
File: 1/5 - Initialization (250 LOC)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon
from src.ui.threads.regime_optimization_thread import RegimeOptimizationThread

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RegimeOptimizationInitMixin:
    """Initialization and UI setup for regime optimization tab.

    Provides:
        - Tab layout creation
        - Widget initialization
        - Control button setup
        - Progress bar and status labels
        - Results table configuration
        - Action button setup
    """

    # Type hints for parent class attributes
    _regime_opt_start_btn: QPushButton
    _regime_opt_stop_btn: QPushButton
    _regime_opt_max_trials: QSpinBox
    _regime_opt_progress_bar: QProgressBar
    _regime_opt_status_label: QLabel
    _regime_opt_eta_label: QLabel
    _regime_opt_top5_table: QTableWidget
    _regime_opt_thread: RegimeOptimizationThread | None
    _regime_opt_all_results: list[dict]
    _regime_opt_start_time: datetime | None
    _regime_opt_current_score_label: QLabel
    _regime_opt_components_label: QLabel
    _regime_opt_export_btn: QPushButton
    _regime_opt_save_history_btn: QPushButton
    _regime_opt_draw_btn: QPushButton
    _regime_opt_apply_selected_btn: QPushButton
    _regime_opt_continue_btn: QPushButton

    def _setup_regime_optimization_tab(self, tab: QWidget) -> None:
        """Setup Regime Optimization tab with controls and live results.

        Args:
            tab: QWidget to populate with regime optimization UI
        """
        layout = QVBoxLayout(tab)

        # Header with help button
        header_layout = QHBoxLayout()
        header = QLabel("Regime Optimization (TPE)")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        # Help button for RegimeScore
        help_btn = QPushButton(get_icon("help"), "")
        help_btn.setToolTip("Open RegimeScore Help")
        help_btn.setFixedSize(28, 28)
        help_btn.clicked.connect(self._on_regime_score_help_clicked)
        header_layout.addWidget(help_btn)
        layout.addLayout(header_layout)

        # Current Regime Score Display
        current_score_layout = QHBoxLayout()
        current_score_layout.addWidget(QLabel("Current Regime Score:"))
        self._regime_opt_current_score_label = QLabel("--")
        self._regime_opt_current_score_label.setStyleSheet(
            "font-weight: bold; font-size: 12pt; color: #3b82f6;"
        )
        self._regime_opt_current_score_label.setToolTip(
            "RegimeScore (0-100): Measures quality of regime detection"
        )
        current_score_layout.addWidget(self._regime_opt_current_score_label)

        # Component details label (compact)
        self._regime_opt_components_label = QLabel("")
        self._regime_opt_components_label.setStyleSheet("color: #888; font-size: 9pt;")
        current_score_layout.addWidget(self._regime_opt_components_label)

        current_score_layout.addStretch()

        refresh_score_btn = QPushButton(get_icon("refresh"), "Calculate Current Score")
        refresh_score_btn.setToolTip(
            "Calculate RegimeScore for currently active regime parameters"
        )
        refresh_score_btn.clicked.connect(self._on_calculate_current_regime_score)
        current_score_layout.addWidget(refresh_score_btn)
        layout.addLayout(current_score_layout)

        # Control Buttons
        control_layout = QHBoxLayout()
        self._regime_opt_start_btn = QPushButton(get_icon("play_arrow"), "Start Optimization")
        self._regime_opt_start_btn.setProperty("class", "success")
        self._regime_opt_start_btn.clicked.connect(self._on_regime_opt_start)
        control_layout.addWidget(self._regime_opt_start_btn)

        self._regime_opt_stop_btn = QPushButton(get_icon("stop"), "Stop")
        self._regime_opt_stop_btn.setProperty("class", "danger")
        self._regime_opt_stop_btn.setEnabled(False)
        self._regime_opt_stop_btn.clicked.connect(self._on_regime_opt_stop)
        control_layout.addWidget(self._regime_opt_stop_btn)

        # Max Trials SpinBox
        control_layout.addSpacing(20)
        control_layout.addWidget(QLabel("Max Trials:"))
        self._regime_opt_max_trials = QSpinBox()
        self._regime_opt_max_trials.setRange(10, 9999)
        self._regime_opt_max_trials.setValue(150)
        self._regime_opt_max_trials.setSingleStep(10)
        self._regime_opt_max_trials.setToolTip("Maximum number of optimization trials (10-9999)")
        self._regime_opt_max_trials.setMinimumWidth(100)
        control_layout.addWidget(self._regime_opt_max_trials)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Progress Bar
        progress_layout = QVBoxLayout()
        progress_label = QLabel("Progress:")
        progress_layout.addWidget(progress_label)

        self._regime_opt_progress_bar = QProgressBar()
        self._regime_opt_progress_bar.setRange(0, 100)
        self._regime_opt_progress_bar.setValue(0)
        progress_layout.addWidget(self._regime_opt_progress_bar)

        layout.addLayout(progress_layout)

        # Status and ETA
        status_layout = QHBoxLayout()
        self._regime_opt_status_label = QLabel(
            "Ready. Configure parameters in 'Regime Setup' tab and click 'Start'."
        )
        self._regime_opt_status_label.setWordWrap(True)
        status_layout.addWidget(self._regime_opt_status_label, stretch=1)

        self._regime_opt_eta_label = QLabel("ETA: --")
        self._regime_opt_eta_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self._regime_opt_eta_label)

        layout.addLayout(status_layout)

        # Live Results Table (filtered by score)
        results_label = QLabel("Live Results (Score > 50 or Best 10):")
        results_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(results_label)

        self._regime_opt_top5_table = QTableWidget()
        # Dynamic columns - will be set when first result arrives
        # Initial headers: Rank, Score, Trial # (parameters added dynamically)
        self._regime_opt_top5_table.setColumnCount(3)
        self._regime_opt_top5_table.setHorizontalHeaderLabels(["Rank", "Score", "Trial #"])
        # Make table sortable
        self._regime_opt_top5_table.setSortingEnabled(True)
        self._regime_opt_top5_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self._regime_opt_top5_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._regime_opt_top5_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._regime_opt_top5_table.setMinimumHeight(600)  # Increased from 200 to 600 (+200%)
        self._regime_opt_top5_table.setMaximumHeight(800)  # Allow scrolling beyond 600
        layout.addWidget(self._regime_opt_top5_table)

        layout.addStretch()

        # Selection Info
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(
            QLabel("💡 Tip: Select a row, then click 'Apply Selected' or 'Save to History'")
        )
        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        # Action Buttons
        action_layout = QHBoxLayout()

        # Export Button
        self._regime_opt_export_btn = QPushButton(get_icon("save"), "Export Results (JSON)")
        self._regime_opt_export_btn.setEnabled(False)
        self._regime_opt_export_btn.setToolTip(
            "Export optimization results with parameter ranges to JSON file"
        )
        self._regime_opt_export_btn.clicked.connect(self._on_regime_opt_export)
        action_layout.addWidget(self._regime_opt_export_btn)

        # Save Selected to History Button
        self._regime_opt_save_history_btn = QPushButton(
            get_icon("history"), "Save Selected to History"
        )
        self._regime_opt_save_history_btn.setEnabled(False)
        self._regime_opt_save_history_btn.setToolTip(
            "Save selected result to optimization_results[] in JSON\n"
            "Keeps top 10 results in history for future reference"
        )
        self._regime_opt_save_history_btn.clicked.connect(self._on_save_selected_to_history)
        action_layout.addWidget(self._regime_opt_save_history_btn)

        # Draw on Chart Button
        self._regime_opt_draw_btn = QPushButton(get_icon("show_chart"), "Draw on Chart")
        self._regime_opt_draw_btn.setEnabled(False)
        self._regime_opt_draw_btn.setToolTip(
            "Draw selected regime periods on chart\n" "Clears all existing regime lines first"
        )
        self._regime_opt_draw_btn.clicked.connect(self._on_regime_opt_draw_selected)
        action_layout.addWidget(self._regime_opt_draw_btn)

        # Save & Load in Regime Button
        self._regime_opt_apply_selected_btn = QPushButton(
            get_icon("check_circle"), "Save && Load in Regime"
        )
        self._regime_opt_apply_selected_btn.setEnabled(False)
        self._regime_opt_apply_selected_btn.setProperty("class", "success")
        self._regime_opt_apply_selected_btn.setToolTip(
            "Save SELECTED result as new regime config file\n"
            "Updates indicator parameters and regime thresholds\n"
            "Clears tables and loads config in Regime tab"
        )
        self._regime_opt_apply_selected_btn.clicked.connect(
            self._on_apply_selected_to_regime_config
        )
        action_layout.addWidget(self._regime_opt_apply_selected_btn)

        action_layout.addStretch()

        # Continue Button
        self._regime_opt_continue_btn = QPushButton(get_icon("arrow_forward"), "View All Results →")
        self._regime_opt_continue_btn.setEnabled(False)
        self._regime_opt_continue_btn.clicked.connect(self._on_regime_opt_continue)
        action_layout.addWidget(self._regime_opt_continue_btn)
        layout.addLayout(action_layout)

        # Initialize state
        self._regime_opt_thread = None
        self._regime_opt_all_results = []
        self._regime_opt_start_time = None
