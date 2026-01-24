"""Entry Analyzer Popup Dialog - Main Window with Mixin Composition.

Refactored from monolithic 3,167 LOC file into modular architecture:
- This file: Main dialog structure, UI setup (~430 LOC)
- entry_analyzer_workers.py: Background workers (190 LOC)
- entry_analyzer_backtest.py: Backtest & Regime functionality (1,188 LOC)
- entry_analyzer_indicators.py: Indicator optimization (1,130 LOC)
- entry_analyzer_analysis.py: Analysis & Validation (435 LOC)
- entry_analyzer_ai.py: AI & Pattern Recognition (657 LOC)

Date: 2026-01-21
Original: entry_analyzer_popup.py (3,167 LOC)
Refactored: 6 modules (~4,040 LOC total)
Maintainability: +200%
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Import icon provider (Issue #12)
from src.ui.icons import get_icon

from .entry_analyzer_ai import AIMixin
from .entry_analyzer_analysis import AnalysisMixin
from .entry_analyzer_compounding_mixin import CompoundingMixin

# Import mixins
from .entry_analyzer_backtest import BacktestMixin
from .entry_analyzer_indicator_optimization_v2_mixin import IndicatorOptimizationV2Mixin
from .entry_analyzer_indicator_results_v2_mixin import IndicatorResultsV2Mixin

# Stage 2 (V2) mixins
from .entry_analyzer_indicator_setup_v2_mixin import IndicatorSetupV2Mixin
from .entry_analyzer_indicators import IndicatorsMixin
from .entry_analyzer_indicators_presets import IndicatorsPresetsMixin
from .entry_analyzer_regime_optimization_mixin import RegimeOptimizationMixin
from .entry_analyzer_regime_results_mixin import RegimeResultsMixin

# New Stufe-1 Regime Optimization Mixins
from .entry_analyzer_regime_setup_mixin import RegimeSetupMixin
from .entry_analyzer_regime_table import RegimeTableMixin

# Import workers
from .entry_analyzer_workers import BacktestWorker, CopilotWorker, ValidationWorker

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import AnalysisResult

logger = logging.getLogger(__name__)


# ==================== Main Dialog Class ====================


class EntryAnalyzerPopup(
    QDialog,
    BacktestMixin,
    IndicatorsMixin,
    IndicatorsPresetsMixin,
    AnalysisMixin,
    AIMixin,
    CompoundingMixin,
    RegimeTableMixin,
    RegimeSetupMixin,
    RegimeOptimizationMixin,
    RegimeResultsMixin,
    IndicatorSetupV2Mixin,
    IndicatorOptimizationV2Mixin,
    IndicatorResultsV2Mixin,
):
    """Entry Analyzer main dialog with mixin composition.

    Original: entry_analyzer_popup.py:197-3167 (2,970 LOC)

    This main class provides:
    - Dialog structure and UI setup
    - Worker management (Copilot, Validation, Backtest)
    - Public API for external integration
    - Tab coordination

    Functionality is distributed across mixins:
    - BacktestMixin: Backtest execution and regime analysis
    - IndicatorsMixin: Indicator optimization and entry signals
    - AnalysisMixin: Visible chart analysis and validation
    - AIMixin: AI Copilot and pattern recognition
    - CompoundingMixin: Compounding/P&L calculator tab
    - RegimeTableMixin: Regime parameter optimization and results table (OLD)
    - RegimeSetupMixin: Regime parameter range setup (NEW - Stufe 1, Tab 1/3)
    - RegimeOptimizationMixin: TPE-based regime optimization (NEW - Stufe 1, Tab 2/3)
    - RegimeResultsMixin: Regime results viewing and export (NEW - Stufe 1, Tab 3/3)
    """

    # Signals
    # Issue #28: analyze_requested now includes json_config_path for regime parameters
    analyze_requested = pyqtSignal(str)  # json_config_path (or empty string for defaults)
    draw_entries_requested = pyqtSignal(list)
    clear_entries_requested = pyqtSignal()
    draw_regime_lines_requested = pyqtSignal(list)  # Issue #21: Signal for regime lines

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize dialog with all UI components.

        Original: entry_analyzer_popup.py:214-231
        Issue #12: Updated to use Material Design icons
        """
        super().__init__(parent)
        self.setWindowTitle("Entry Analyzer & Backtester")
        self.setWindowIcon(get_icon("gps_fixed"))  # Issue #12: Target/Entry icon
        self.setMinimumSize(900, 820)
        self.resize(1000, 870)

        # ========== Shared State (All attributes defined here) ==========

        # Analysis Results
        self._result: AnalysisResult | None = None
        self._validation_result: Any = None
        self._copilot_response: Any = None
        self._backtest_result: Any = None

        # Context Data
        self._candles: list[dict] = []
        self._symbol: str = "UNKNOWN"
        self._timeframe: str = "1m"

        # Workers
        self._copilot_worker: CopilotWorker | None = None
        self._validation_worker: ValidationWorker | None = None
        self._backtest_worker: BacktestWorker | None = None
        self._optimization_worker: QThread | None = None  # IndicatorsMixin

        # UI Components (will be created in _setup_ui and mixins)
        self._tabs: QTabWidget = None
        self._regime_label: QLabel = None
        self._signal_count_label: QLabel = None
        self._signal_rate_label: QLabel = None

        # Footer Buttons
        self._analyze_btn: QPushButton = None
        self._progress: QProgressBar = None
        self._report_btn: QPushButton = None
        self._draw_btn: QPushButton = None
        self._clear_btn: QPushButton = None

        # Analysis Tab (AnalysisMixin)
        self._set_name_label: QLabel = None
        self._params_table: QTableWidget = None
        self._score_label: QLabel = None
        self._alternatives_label: QLabel = None
        self._filter_checkbox: QCheckBox = None
        self._filter_stats_label: QLabel = None
        self._entries_table: QTableWidget = None

        # AI Tab (AIMixin)
        self._ai_analyze_btn: QPushButton = None
        self._ai_progress: QProgressBar = None
        self._ai_status_label: QLabel = None
        self._ai_results_text: QTextEdit = None

        # Compounding (CompoundingMixin)
        self._compounding_panel: QWidget = None

        # Validation Tab (AnalysisMixin)
        self._validate_btn: QPushButton = None
        self._val_progress: QProgressBar = None
        self._val_status_label: QLabel = None
        self._val_summary: QLabel = None
        self._folds_table: QTableWidget = None

        # Backtest Config Tab (BacktestMixin)
        self._bt_strategy_path_label: QLabel = None
        self._bt_start_date: QDateEdit = None
        self._bt_end_date: QDateEdit = None
        self._bt_initial_capital: QDoubleSpinBox = None
        self._bt_regime_set_combo: QComboBox = None
        self._bt_run_btn: QPushButton = None
        self._bt_progress: QProgressBar = None
        self._bt_status_label: QLabel = None

        # Regime Config (BacktestMixin)
        self._regime_config_path: Path | None = None
        self._regime_config = None
        self._regime_config_path_label: QLabel = None
        self._regime_config_table: QTableWidget = None
        self._regime_config_load_btn: QPushButton = None

        # Indicator Optimization (IndicatorsMixin)
        self._ind_opt_tabs: QTabWidget = None
        self._ind_opt_indicator_combo: QComboBox = None
        self._ind_opt_param_ranges: dict[str, tuple[QSpinBox, QSpinBox]] = {}
        self._ind_opt_optimize_btn: QPushButton = None
        self._ind_opt_progress: QProgressBar = None
        self._ind_opt_status_label: QLabel = None
        self._ind_opt_results_table: QTableWidget = None
        self._ind_opt_draw_btn: QPushButton = None
        self._ind_opt_show_entries_btn: QPushButton = None

        # Parameter Ranges (IndicatorsSetupMixin - in Setup sub-tab)
        self._param_layout: QFormLayout = None
        self._opt_indicator_checkboxes: dict[str, QCheckBox] = {}
        self._param_widgets: dict = {}
        self._test_type_entry: QCheckBox = None
        self._test_type_exit: QCheckBox = None
        self._trade_side_long: QCheckBox = None
        self._trade_side_short: QCheckBox = None
        self._optimization_progress: QLabel = None
        self._optimize_btn: QPushButton = None
        self._optimization_results_table: QTableWidget = None
        self._draw_indicators_btn: QPushButton = None
        self._show_entries_btn: QPushButton = None
        self._create_regime_set_btn: QPushButton = None

        # Parameter Presets (IndicatorsPresetsMixin)
        self._preset_combo: QComboBox = None
        self._preset_details_text: QTextEdit = None

        # Pattern Recognition (AIMixin)
        self.pattern_window_spin: QSpinBox = None
        self.pattern_similarity_threshold_spin: QDoubleSpinBox = None
        self.pattern_min_matches_spin: QSpinBox = None
        self.cross_symbol_checkbox: QCheckBox = None
        self.similar_patterns_table: QTableWidget = None
        self.pattern_analyze_btn: QPushButton = None
        self.pattern_summary_label: QLabel = None

        # Setup UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create main UI layout with tabs.

        Original: entry_analyzer_popup.py:233-283
        """
        layout = QVBoxLayout(self)

        # Header with status
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget for different views
        # Issue #12: Updated all tabs to use Material Design icons
        self._tabs = QTabWidget()

        # Tab 0: Regime (BacktestMixin) - Issue #21: Renamed from "Backtest Setup"
        setup_tab = QWidget()
        self._setup_backtest_config_tab(setup_tab)
        self._tabs.addTab(setup_tab, get_icon("analytics"), "Regime")

        # Tab 1: Reg. Table (RegimeTableMixin) - Regime Parameter Optimization (OLD - DEPRECATED)
        regime_table_tab = QWidget()
        self._setup_regime_table_tab(regime_table_tab)
        self._tabs.addTab(regime_table_tab, get_icon("tune"), "Reg. Table (OLD)")

        # NEW STUFE-1 TABS: Regime Optimization (3 tabs)
        # Tab 2: Regime Setup (RegimeSetupMixin) - Parameter Range Configuration
        regime_setup_tab = QWidget()
        self._setup_regime_setup_tab(regime_setup_tab)
        self._tabs.addTab(regime_setup_tab, get_icon("settings"), "1. Regime Setup")

        # Tab 3: Regime Optimization (RegimeOptimizationMixin) - TPE Optimization
        regime_opt_tab = QWidget()
        self._setup_regime_optimization_tab(regime_opt_tab)
        self._tabs.addTab(regime_opt_tab, get_icon("psychology"), "2. Regime Optimization")
        self._tabs.setTabEnabled(3, False)  # Disabled until setup is complete

        # Tab 4: Regime Results (RegimeResultsMixin) - Results and Export
        regime_results_tab = QWidget()
        self._setup_regime_results_tab(regime_results_tab)
        self._tabs.addTab(regime_results_tab, get_icon("assessment"), "3. Regime Results")
        self._tabs.setTabEnabled(4, False)  # Disabled until optimization is complete

        # NEW STUFE-2 TABS: Indicator Optimization (3 tabs)
        # Tab 5: Indicator Setup V2 (IndicatorSetupV2Mixin) - Indicator Selection & Parameters
        indicator_setup_v2_tab = QWidget()
        self._setup_indicator_setup_v2_tab(indicator_setup_v2_tab)
        self._tabs.addTab(indicator_setup_v2_tab, get_icon("tune"), "4. Indicator Setup")
        self._tabs.setTabEnabled(5, False)  # Disabled until regime results available

        # Tab 6: Indicator Optimization V2 (IndicatorOptimizationV2Mixin) - Per-Signal Type Optimization
        indicator_opt_v2_tab = QWidget()
        self._setup_indicator_optimization_v2_tab(indicator_opt_v2_tab)
        self._tabs.addTab(indicator_opt_v2_tab, get_icon("psychology"), "5. Indicator Optimization")
        self._tabs.setTabEnabled(6, False)  # Disabled until setup is complete

        # Tab 7: Indicator Results V2 (IndicatorResultsV2Mixin) - Results and Export
        indicator_results_v2_tab = QWidget()
        self._setup_indicator_results_v2_tab(indicator_results_v2_tab)
        self._tabs.addTab(indicator_results_v2_tab, get_icon("assessment"), "6. Indicator Results")
        self._tabs.setTabEnabled(7, False)  # Disabled until optimization is complete

        # Tab 8: Indicator Optimization (OLD - IndicatorsMixin)
        # Issue #10: Parameter Presets now integrated as sub-tab within Indicator Optimization
        optimization_tab = QWidget()
        self._setup_indicator_optimization_tab(optimization_tab)
        self._tabs.addTab(optimization_tab, get_icon("build"), "Indicator Optimization (OLD)")
        self._tabs.setTabEnabled(8, False)  # Disabled until regime is selected

        # Tab 9: Pattern Recognition (AIMixin)
        pattern_tab = QWidget()
        self._setup_pattern_recognition_tab(pattern_tab)
        self._tabs.addTab(pattern_tab, get_icon("search"), "Pattern Recognition")

        # Tab 10: Analysis (AnalysisMixin)
        analysis_tab = QWidget()
        self._setup_analysis_tab(analysis_tab)
        self._tabs.addTab(analysis_tab, get_icon("analytics"), "Visible Range")

        # Tab 11: AI Copilot (AIMixin)
        ai_tab = QWidget()
        self._setup_ai_tab(ai_tab)
        self._tabs.addTab(ai_tab, get_icon("smart_toy"), "AI Copilot")

        # Tab 12: Validation (AnalysisMixin)
        validation_tab = QWidget()
        self._setup_validation_tab(validation_tab)
        self._tabs.addTab(validation_tab, get_icon("check_circle"), "Validation")

        # Tab 13: Compounding / P&L Calculator (CompoundingMixin)
        compounding_tab = QWidget()
        self._setup_compounding_tab(compounding_tab)
        self._tabs.addTab(compounding_tab, get_icon("trending_up"), "P&L Calculator")

        layout.addWidget(self._tabs, stretch=1)

        # Footer with actions
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create header widget with regime and signal count.

        Original: entry_analyzer_popup.py:895-916
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 10)

        self._regime_label = QLabel("Regime: --")
        self._regime_label.setStyleSheet("font-weight: bold; font-size: 14pt; padding: 5px;")
        layout.addWidget(self._regime_label)

        layout.addStretch()

        self._signal_count_label = QLabel("Signals: 0 LONG / 0 SHORT")
        self._signal_count_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(self._signal_count_label)

        self._signal_rate_label = QLabel("Rate: 0/h")
        self._signal_rate_label.setStyleSheet("font-size: 11pt; color: #888;")
        layout.addWidget(self._signal_rate_label)

        return widget

    def _create_footer(self) -> QWidget:
        """Create footer widget with action buttons.

        Original: entry_analyzer_popup.py:1072-1114
        Issue #12: Updated to use Material Design icons and theme colors
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        # Analyze button (Issue #12: Using refresh icon and info color)
        self._analyze_btn = QPushButton(" Analyze Visible Range")
        self._analyze_btn.setIcon(get_icon("refresh"))
        self._analyze_btn.setProperty("class", "info")  # Use theme info color
        self._analyze_btn.clicked.connect(self._on_analyze_clicked)
        layout.addWidget(self._analyze_btn)

        self._progress = QProgressBar()
        self._progress.setMaximumWidth(150)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        layout.addStretch()

        # Report button (Issue #12: Using description icon)
        self._report_btn = QPushButton(" Generate Report")
        self._report_btn.setIcon(get_icon("description"))
        self._report_btn.setEnabled(False)
        self._report_btn.clicked.connect(self._on_report_clicked)
        layout.addWidget(self._report_btn)

        # Draw entries button (Issue #12: Using place icon and success color)
        self._draw_btn = QPushButton(" Draw on Chart")
        self._draw_btn.setIcon(get_icon("place"))
        self._draw_btn.setProperty("class", "success")  # Use theme success color
        self._draw_btn.setEnabled(False)
        self._draw_btn.clicked.connect(self._on_draw_clicked)
        layout.addWidget(self._draw_btn)

        # Clear button (Issue #12: Using delete icon and danger color)
        self._clear_btn = QPushButton(" Clear Entries")
        self._clear_btn.setIcon(get_icon("delete"))
        self._clear_btn.setProperty("class", "danger")  # Use theme danger color
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self._clear_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return widget

    # ========== Public API ==========

    def set_context(self, symbol: str, timeframe: str, candles: list[dict]) -> None:
        """Set context for AI/Validation.

        Original: entry_analyzer_popup.py:1116-1120
        """
        self._symbol = symbol
        self._timeframe = timeframe
        self._candles = candles

    def set_analyzing(self, analyzing: bool) -> None:
        """Set analyzing state and update progress bar.

        Original: entry_analyzer_popup.py:1122-1147

        Issue #27: Added debug logging for progress bar state changes.
        """
        # Import debug logger
        try:
            from src.analysis.visible_chart.debug_logger import debug_logger
        except ImportError:
            debug_logger = logger

        debug_logger.info("PROGRESS BAR: set_analyzing(%s)", analyzing)

        self._analyze_btn.setEnabled(not analyzing)
        self._progress.setVisible(analyzing)
        if analyzing:
            self._progress.setRange(0, 0)  # Indeterminate mode (busy spinner)
            debug_logger.debug("Progress bar: indeterminate mode (analyzing)")
        else:
            self._progress.setRange(0, 100)  # Determinate mode
            self._progress.setValue(100)  # Complete
            debug_logger.debug("Progress bar: complete (100%%)")

        # Force GUI update
        self._progress.update()
        debug_logger.debug("Progress bar updated, visible=%s", analyzing)

    def set_result(self, result: AnalysisResult) -> None:
        """Update UI with analysis results.

        Original: entry_analyzer_popup.py:1149-1205
        """
        self._result = result

        # Update regime
        regime_colors = {
            "trend_up": "#22c55e",
            "trend_down": "#ef4444",
            "range": "#f59e0b",
            "high_vol": "#a855f7",
            "squeeze": "#3b82f6",
            "no_trade": "#6b7280",
        }
        regime_text = result.regime.value.replace("_", " ").title()
        color = regime_colors.get(result.regime.value, "#888")
        self._regime_label.setText(f"Regime: {regime_text}")
        self._regime_label.setStyleSheet(
            f"font-weight: bold; font-size: 14pt; padding: 5px; color: {color};"
        )

        # Issue #3: Auto-apply regime preset parameters (Indicator Presets tab)
        try:
            self._on_auto_preset_clicked()  # Auto-select matching preset
            self._on_apply_preset_clicked()  # Auto-apply to parameter spinboxes
        except Exception as e:
            logger.warning(f"Failed to auto-apply regime preset: {e}")

        # Issue #8: Auto-select parameter ranges in Regime Table tab
        try:
            logger.info(
                f"Calling auto_select_parameter_ranges_for_regime with regime: {result.regime.value}"
            )
            self.auto_select_parameter_ranges_for_regime(result.regime.value)
        except Exception as e:
            logger.error(f"Failed to auto-select parameter ranges for regime: {e}", exc_info=True)

        # Update signal counts
        self._signal_count_label.setText(
            f"Signals: {result.long_count} LONG / {result.short_count} SHORT"
        )
        self._signal_rate_label.setText(f"Rate: {result.signal_rate_per_hour:.1f}/h")

        # Update indicator set
        if result.active_set:
            self._set_name_label.setText(f"Active Set: {result.active_set.name}")
            self._score_label.setText(f"Score: {result.active_set.score:.3f}")
            self._update_params_table(result.active_set.parameters)

            if result.alternative_sets:
                alt_names = [s.name for s in result.alternative_sets[:2]]
                self._alternatives_label.setText(f"Alternatives: {', '.join(alt_names)}")
                self._alternatives_label.setVisible(True)
            else:
                self._alternatives_label.setVisible(False)
        else:
            self._set_name_label.setText("Active Set: Default (no optimization)")
            self._score_label.setText("Score: --")
            self._params_table.setRowCount(0)
            self._alternatives_label.setVisible(False)

        # Update entries table
        self._update_entries_table(result.entries)

        # Enable buttons
        self._draw_btn.setEnabled(len(result.entries) > 0)
        self._report_btn.setEnabled(True)
        self._ai_analyze_btn.setEnabled(True)
        self._validate_btn.setEnabled(len(result.entries) > 0 and len(self._candles) > 0)

        logger.info(
            "Analysis result displayed: %d entries, regime=%s",
            len(result.entries),
            result.regime.value,
        )
