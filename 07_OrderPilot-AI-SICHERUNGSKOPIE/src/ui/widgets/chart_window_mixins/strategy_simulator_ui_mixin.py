from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit, QProgressBar, QPushButton, QRadioButton, QScrollArea, QSpinBox, QSplitter, QTableWidget, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)

class StrategySimulatorUIMixin:
    """StrategySimulatorUIMixin extracted from StrategySimulatorMixin."""
    def _create_strategy_simulator_tab(self) -> QWidget:
        """Create the Strategy Simulator tab widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Splitter for controls and results
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)  # Prevent collapse
        splitter.setHandleWidth(6)  # Make handle visible and draggable
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555;
            }
            QSplitter::handle:hover {
                background-color: #777;
            }
            QSplitter::handle:pressed {
                background-color: #999;
            }
        """)

        # Left: Controls (20% wider: 336*1.2=403, 264*1.2=317)
        controls = self._create_simulator_controls()
        controls.setMaximumWidth(600)  # Allow wider for drag
        controls.setMinimumWidth(320)  # 20% wider minimum
        splitter.addWidget(controls)

        # Right: Results
        results = self._create_simulator_results()
        splitter.addWidget(results)

        # Store reference for state save/restore
        self._simulator_splitter = splitter

        # Set initial sizes (20% wider: 403px for controls)
        splitter.setSizes([403, 600])

        # Restore saved splitter state if available
        self._restore_simulator_splitter_state()

        layout.addWidget(splitter)

        # Initialize
        self._simulation_results = []
        self._last_optimization_run = None
        self._current_sim_strategy_name = None
        self._current_sim_strategy_index = None
        self._current_sim_strategy_total = None
        self._current_sim_strategy_side = None
        self._current_simulation_mode = None
        self._current_objective_metric = None
        self._current_entry_only = False
        self._all_run_active = False
        self._all_run_restore_index = None
        self._on_simulator_strategy_changed(0)

        return widget
    def _create_simulator_controls(self) -> QWidget:
        """Create control panel (strategy selection, parameters, buttons)."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll, layout = self._build_simulator_scroll_container()
        layout.addWidget(self._build_strategy_group())
        layout.addWidget(self._build_params_group())
        layout.addWidget(self._build_opt_group())
        layout.addLayout(self._build_action_buttons())
        layout.addWidget(self._build_progress_bar())
        layout.addWidget(self._build_status_label())
        layout.addWidget(self._build_log_view())
        layout.addStretch()

        main_layout.addWidget(scroll)
        return widget

    def _build_simulator_scroll_container(self) -> tuple[QScrollArea, QVBoxLayout]:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)
        return scroll, layout

    def _build_strategy_group(self) -> QGroupBox:
        strategy_group = QGroupBox("Strategy")
        strategy_layout = QVBoxLayout(strategy_group)

        self.simulator_strategy_combo = QComboBox()
        # Load strategies from StrategyCatalog for consistency with trading bot
        self.simulator_strategy_combo.addItems(self._get_catalog_strategy_names())
        self.simulator_strategy_combo.currentIndexChanged.connect(
            self._on_simulator_strategy_changed
        )
        strategy_layout.addWidget(self.simulator_strategy_combo)
        return strategy_group

    def _get_catalog_strategy_names(self) -> list[str]:
        """Get strategy names from StrategyCatalog + ALL option."""
        try:
            from src.core.tradingbot.strategy_catalog import StrategyCatalog
            catalog = StrategyCatalog()
            strategies = catalog.list_strategies()
            # Sort alphabetically and add ALL at the end
            return sorted(strategies) + ["ALL"]
        except Exception as e:
            logger.warning(f"Failed to load catalog strategies: {e}")
            # Fallback to hardcoded list
            return [
                "breakout_momentum",
                "breakout_volatility",
                "mean_reversion_bb",
                "mean_reversion_rsi",
                "momentum_macd",
                "scalping_range",
                "sideways_range_bounce",
                "trend_following_aggressive",
                "trend_following_conservative",
                "ALL",
            ]

    def _build_params_group(self) -> QGroupBox:
        self.simulator_params_group = QGroupBox("Parameters")
        params_main_layout = QVBoxLayout(self.simulator_params_group)
        self.simulator_params_layout = QFormLayout()
        self._simulator_param_widgets = {}
        params_main_layout.addLayout(self.simulator_params_layout)
        params_main_layout.addLayout(self._build_params_buttons())
        return self.simulator_params_group

    def _build_params_buttons(self) -> QHBoxLayout:
        params_btn_row1 = QHBoxLayout()
        params_btn_row1.setSpacing(4)

        self.simulator_reset_params_btn = QPushButton("Reset")
        self.simulator_reset_params_btn.setToolTip(
            "Parameter auf Standardwerte zurücksetzen"
        )
        self.simulator_reset_params_btn.clicked.connect(self._on_reset_simulator_params)
        params_btn_row1.addWidget(self.simulator_reset_params_btn)

        self.simulator_save_to_bot_btn = QPushButton("Save")
        self.simulator_save_to_bot_btn.setToolTip(
            "Parameter für produktiven Bot speichern"
        )
        self.simulator_save_to_bot_btn.clicked.connect(self._on_save_params_to_bot)
        params_btn_row1.addWidget(self.simulator_save_to_bot_btn)

        self.simulator_load_from_bot_btn = QPushButton("Load")
        self.simulator_load_from_bot_btn.setToolTip("Gespeicherte Parameter laden")
        self.simulator_load_from_bot_btn.clicked.connect(self._on_load_params_from_bot)
        params_btn_row1.addWidget(self.simulator_load_from_bot_btn)

        # New button: Apply to Active Strategy
        self.simulator_apply_active_btn = QPushButton("→ Apply")
        self.simulator_apply_active_btn.setToolTip(
            "Parameter auf aktive Trading-Strategie anwenden\n"
            "(synchronisiert mit Strategy Catalog)"
        )
        self.simulator_apply_active_btn.setStyleSheet(
            "QPushButton { background-color: #2d5a27; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #3d7a37; }"
        )
        self.simulator_apply_active_btn.clicked.connect(self._on_apply_to_active_strategy)
        params_btn_row1.addWidget(self.simulator_apply_active_btn)

        return params_btn_row1

    def _build_opt_group(self) -> QGroupBox:
        opt_group = QGroupBox("Mode")
        opt_layout = QVBoxLayout(opt_group)

        self.simulator_opt_mode_group = QButtonGroup()
        self.simulator_opt_manual = QRadioButton("Manual (Single Run)")
        self.simulator_opt_grid = QRadioButton("Grid Search")
        self.simulator_opt_bayesian = QRadioButton("Bayesian Optimization")
        self.simulator_opt_manual.setChecked(True)

        self.simulator_opt_mode_group.addButton(self.simulator_opt_manual, 0)
        self.simulator_opt_mode_group.addButton(self.simulator_opt_grid, 1)
        self.simulator_opt_mode_group.addButton(self.simulator_opt_bayesian, 2)

        opt_layout.addWidget(self.simulator_opt_manual)
        opt_layout.addWidget(self.simulator_opt_grid)
        opt_layout.addWidget(self.simulator_opt_bayesian)

        opt_layout.addLayout(self._build_objective_layout())
        opt_layout.addWidget(self._build_entry_only_checkbox())
        opt_layout.addWidget(self._build_auto_strategy_checkbox())
        opt_layout.addLayout(self._build_time_range_layout())
        opt_layout.addLayout(self._build_trials_layout())

        self.simulator_trials_hint_label = QLabel("")
        self.simulator_trials_hint_label.setWordWrap(True)
        opt_layout.addWidget(self.simulator_trials_hint_label)
        return opt_group

    def _build_objective_layout(self) -> QHBoxLayout:
        objective_layout = QHBoxLayout()
        objective_layout.addWidget(QLabel("Optimize:"))
        self.simulator_opt_metric_combo = QComboBox()
        self.simulator_opt_metric_combo.addItem("Score (P&L)", "score")
        self.simulator_opt_metric_combo.addItem("Entry Score", "entry_score")
        self.simulator_opt_metric_combo.addItem("P&L %", "total_pnl_pct")
        self.simulator_opt_metric_combo.addItem("Profit Factor", "profit_factor")
        self.simulator_opt_metric_combo.addItem("Sharpe Ratio", "sharpe_ratio")
        self.simulator_opt_metric_combo.addItem("Win Rate", "win_rate")
        self.simulator_opt_metric_combo.addItem("Max Drawdown", "max_drawdown_pct")
        objective_layout.addWidget(self.simulator_opt_metric_combo)
        return objective_layout

    def _build_entry_only_checkbox(self) -> QCheckBox:
        self.simulator_entry_only_checkbox = QCheckBox("Entry Only (Long+Short)")
        self.simulator_entry_only_checkbox.setToolTip(
            "Simuliert nur Einstiege basierend auf dem Zeitraum."
        )
        self.simulator_entry_only_checkbox.toggled.connect(self._on_entry_only_toggled)
        return self.simulator_entry_only_checkbox

    def _build_auto_strategy_checkbox(self) -> QCheckBox:
        self.simulator_auto_strategy_checkbox = QCheckBox("Auto-Strategy (beste pro Signal)")
        self.simulator_auto_strategy_checkbox.setToolTip(
            "Ermittelt für jedes Entry-Signal die beste Strategie.\n"
            "Testet alle Strategien und wählt die mit dem besten Score.\n"
            "Erhöht die Rechenzeit deutlich!"
        )
        self.simulator_auto_strategy_checkbox.toggled.connect(self._on_auto_strategy_toggled)
        return self.simulator_auto_strategy_checkbox

    def _build_time_range_layout(self) -> QHBoxLayout:
        """Build the time range selector layout.

        Time range options consider the chart's candle timeframe.
        For crypto (24/7 market), no session-based options.
        """
        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(QLabel("Zeitraum:"))
        self.simulator_time_range_combo = QComboBox()

        # Time range options with data values (in hours)
        # The actual number of bars will be calculated based on candle timeframe
        self.simulator_time_range_combo.addItem("Chart-Ansicht (sichtbar)", "visible")
        self.simulator_time_range_combo.addItem("Intraday (24h)", 24)
        self.simulator_time_range_combo.addItem("2 Tage", 48)
        self.simulator_time_range_combo.addItem("5 Tage", 120)
        self.simulator_time_range_combo.addItem("1 Woche", 168)
        self.simulator_time_range_combo.addItem("2 Wochen", 336)
        self.simulator_time_range_combo.addItem("1 Monat", 720)
        self.simulator_time_range_combo.addItem("3 Monate", 2160)
        self.simulator_time_range_combo.addItem("6 Monate", 4320)
        self.simulator_time_range_combo.addItem("1 Jahr", 8760)
        self.simulator_time_range_combo.addItem("Alle Daten", "all")

        self.simulator_time_range_combo.setToolTip(
            "Zeitraum für die Simulation.\n"
            "Die Anzahl Kerzen wird basierend auf dem Chart-Timeframe berechnet.\n"
            "'Chart-Ansicht' nutzt die aktuell sichtbaren Kerzen."
        )
        time_range_layout.addWidget(self.simulator_time_range_combo)
        return time_range_layout

    def _build_trials_layout(self) -> QHBoxLayout:
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Trials:"))
        self.simulator_opt_trials_spin = QSpinBox()
        self.simulator_opt_trials_spin.setRange(10, 2_147_483_647)
        self.simulator_opt_trials_spin.setValue(50)
        trials_layout.addWidget(self.simulator_opt_trials_spin)
        return trials_layout

    def _build_action_buttons(self) -> QHBoxLayout:
        buttons_layout = QHBoxLayout()

        self.simulator_run_btn = QPushButton("Run")
        self.simulator_run_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )
        self.simulator_run_btn.clicked.connect(self._on_run_simulation)
        buttons_layout.addWidget(self.simulator_run_btn)

        self.simulator_stop_btn = QPushButton("Stop")
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_stop_btn.clicked.connect(self._on_stop_simulation)
        buttons_layout.addWidget(self.simulator_stop_btn)

        # Show Parameters button - opens popup with all test parameters
        self.simulator_params_btn = QPushButton("📋 Params")
        self.simulator_params_btn.setToolTip(
            "Zeigt alle aktuellen Testparameter in einem Popup an"
        )
        self.simulator_params_btn.clicked.connect(self._on_show_test_parameters)
        buttons_layout.addWidget(self.simulator_params_btn)

        return buttons_layout

    def _build_progress_bar(self) -> QProgressBar:
        self.simulator_progress = QProgressBar()
        self.simulator_progress.setVisible(False)
        return self.simulator_progress

    def _build_status_label(self) -> QLabel:
        self.simulator_status_label = QLabel("")
        self.simulator_status_label.setWordWrap(True)
        return self.simulator_status_label

    def _build_log_view(self) -> QPlainTextEdit:
        self.simulator_log_view = QPlainTextEdit()
        self.simulator_log_view.setReadOnly(True)
        self.simulator_log_view.setMaximumBlockCount(500)
        self.simulator_log_view.setPlaceholderText("Simulation log...")
        return self.simulator_log_view
    def _create_simulator_results(self) -> QWidget:
        """Create results panel (table + export)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Results Table
        self.simulator_results_table = QTableWidget()
        self.simulator_results_table.setColumnCount(12)
        self.simulator_results_table.setHorizontalHeaderLabels([
            "Strategy",
            "Entry",      # Entry time (HH:MM)
            "Exit",       # Exit time (HH:MM)
            "Trades",
            "Win %",
            "PF",
            "P&L €",
            "P&L %",
            "DD %",
            "Score",
            "Objective",
            "Parameters",
        ])
        # Set column resize modes - last column (Parameters) gets extra space
        header = self.simulator_results_table.horizontalHeader()
        for i in range(11):  # First 11 columns: fixed width
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Parameters column: stretches to fill remaining space
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Stretch)
        self.simulator_results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.simulator_results_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.simulator_results_table.itemSelectionChanged.connect(
            self._on_simulator_result_selected
        )
        self.simulator_results_table.setSortingEnabled(True)
        header.setSortIndicatorShown(True)
        layout.addWidget(self.simulator_results_table)

        # Buttons row
        buttons_layout = QHBoxLayout()

        self.simulator_show_markers_btn = QPushButton("Show Entry/Exit")
        self.simulator_show_markers_btn.clicked.connect(self._on_show_simulation_markers)
        self.simulator_show_markers_btn.setEnabled(False)
        buttons_layout.addWidget(self.simulator_show_markers_btn)

        self.simulator_clear_markers_btn = QPushButton("Clear Markers")
        self.simulator_clear_markers_btn.clicked.connect(self._on_clear_simulation_markers)
        buttons_layout.addWidget(self.simulator_clear_markers_btn)

        self.simulator_show_entry_points_checkbox = QCheckBox("View Points")
        self.simulator_show_entry_points_checkbox.setToolTip(
            "Entry-Only: zeigt Entry-Punkte der ausgewählten Zeile"
        )
        self.simulator_show_entry_points_checkbox.toggled.connect(
            self._on_toggle_entry_points
        )
        buttons_layout.addWidget(self.simulator_show_entry_points_checkbox)

        self.simulator_export_btn = QPushButton("Export Excel")
        self.simulator_export_btn.clicked.connect(self._on_export_simulation_xlsx)
        self.simulator_export_btn.setEnabled(False)
        buttons_layout.addWidget(self.simulator_export_btn)

        self.simulator_clear_results_btn = QPushButton("Clear All")
        self.simulator_clear_results_btn.clicked.connect(self._on_clear_simulation_results)
        buttons_layout.addWidget(self.simulator_clear_results_btn)

        layout.addLayout(buttons_layout)

        return widget
    def _restore_simulator_splitter_state(self) -> None:
        """Restore the Strategy Simulator splitter state from settings."""
        if not hasattr(self, 'settings') or not hasattr(self, '_simulator_splitter'):
            return

        try:
            splitter_state = self.settings.value("StrategySimulator/splitterState")
            if splitter_state:
                self._simulator_splitter.restoreState(splitter_state)
                logger.debug("Restored Strategy Simulator splitter state")
        except Exception as e:
            logger.debug(f"Could not restore splitter state: {e}")
    def _save_simulator_splitter_state(self) -> None:
        """Save the Strategy Simulator splitter state to settings."""
        if not hasattr(self, 'settings') or not hasattr(self, '_simulator_splitter'):
            return

        try:
            self.settings.setValue(
                "StrategySimulator/splitterState",
                self._simulator_splitter.saveState()
            )
            logger.debug("Saved Strategy Simulator splitter state")
        except Exception as e:
            logger.debug(f"Could not save splitter state: {e}")
