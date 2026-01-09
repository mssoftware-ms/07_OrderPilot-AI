"""
Backtest Tab Main - Hauptorchestrator für Backtest Tab (REFACTORED)

Dies ist der Haupteinstiegspunkt für das Backtest Tab Widget.
Orchestriert alle Sub-Module und delegiert an spezialisierte Manager.

Nutzt Composition Pattern mit 9 Helper-Klassen:
- BacktestConfigManager - Engine config collection
- BacktestTabUI - UI setup and layout
- BacktestResultsDisplay - Results display logic
- BacktestTemplateManager - Template save/load/derive
- BacktestTabSettings - Settings persistence (NEW)
- BacktestTabExecution - Single backtest execution (NEW)
- BacktestTabBatchExecution - Batch & WF execution (NEW)
- BacktestTabHandlers - Config & UI handlers (NEW)
- BacktestTabLogging - Logging & progress (NEW)

Architecture Pattern:
- Composition over Inheritance
- Helper classes instantiated in __init__
- Delegation pattern: main methods delegate to helpers
- Thin orchestrator layer

Usage:
    from src.ui.widgets.bitunix_trading import BacktestTab

    tab = BacktestTab(history_manager=hist_mgr)
    tab.show()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

# Import Sub-Modules
from .backtest_config_manager import BacktestConfigManager
from .backtest_tab_ui import BacktestTabUI
from .backtest_results_display import BacktestResultsDisplay
from .backtest_template_manager import BacktestTemplateManager
from .backtest_tab_settings import BacktestTabSettings
from .backtest_tab_execution import BacktestTabExecution
from .backtest_tab_batch_execution import BacktestTabBatchExecution
from .backtest_tab_handlers import BacktestTabHandlers
from .backtest_tab_logging import BacktestTabLogging

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)


class BacktestTab(QWidget):
    """Backtest Tab - Main Orchestrator (REFACTORED via Composition).

    Koordiniert alle Backtest-Funktionalität:
    - Single-Run Backtests
    - Batch-Optimization (Grid/Random/Bayesian Search)
    - Walk-Forward Analysis
    - Engine Config Integration
    - Template Management
    - Results Display

    Architecture:
    - Delegates to specialized manager classes (9 helpers total)
    - Thin orchestration layer
    - Clean separation of concerns
    """

    # Signals
    backtest_started = pyqtSignal()
    backtest_finished = pyqtSignal(object)  # BacktestResult
    progress_updated = pyqtSignal(int, str)  # progress_pct, message
    log_message = pyqtSignal(str)

    def __init__(
        self,
        history_manager: "HistoryManager | None" = None,
        parent: QWidget | None = None,
    ):
        """Initialisiert BacktestTab.

        Args:
            history_manager: History Manager für Datenzugriff
            parent: Parent Widget
        """
        super().__init__(parent)

        self._history_manager = history_manager
        self._is_running = False
        self._current_result = None
        self._current_runner = None

        # Engine configs (collected from Engine Settings tabs)
        self._engine_configs: Dict[str, Any] = {}

        # Instantiate Helper Classes (Original 4)
        self.config_manager = BacktestConfigManager(self)
        self.ui_manager = BacktestTabUI(self)
        self.results_display = BacktestResultsDisplay(self)
        self.template_manager = BacktestTemplateManager(self)

        # Instantiate New Helper Classes (5 additional)
        self._settings = BacktestTabSettings(self)
        self._execution = BacktestTabExecution(self)
        self._batch_execution = BacktestTabBatchExecution(self)
        self._handlers = BacktestTabHandlers(self)
        self._logging = BacktestTabLogging(self)

        # Setup UI (delegates to ui_manager)
        self.ui_manager.setup_ui()

        # Connect signals
        self._connect_signals()

        # Load settings (delegiert)
        self._settings.load_settings()

        logger.info("BacktestTab initialized with modular architecture (REFACTORED)")

    # =========================================================================
    # SIGNAL CONNECTIONS
    # =========================================================================

    def _connect_signals(self) -> None:
        """Verbindet alle Signals mit ihren Slots."""
        # Backtest lifecycle
        self.backtest_finished.connect(self.results_display.on_backtest_finished)
        self.progress_updated.connect(self._logging.on_progress_updated)
        self.log_message.connect(self._logging.on_log_message)

        # Button clicks - delegieren an helper
        self.start_btn.clicked.connect(self._execution.on_start_clicked)
        self.stop_btn.clicked.connect(self._execution.on_stop_clicked)
        self.run_batch_btn.clicked.connect(self._batch_execution.on_batch_clicked)
        self.run_wf_btn.clicked.connect(self._batch_execution.on_wf_clicked)

        # Config Tools - delegieren an handlers
        self.load_config_btn.clicked.connect(self._handlers.on_load_configs_clicked)
        self.auto_gen_btn.clicked.connect(self._handlers.on_auto_generate_clicked)

        # Template Management - delegieren an template_manager
        self.save_template_btn.clicked.connect(self.template_manager.on_save_template_clicked)
        self.load_template_btn.clicked.connect(self.template_manager.on_load_template_clicked)
        self.derive_variant_btn.clicked.connect(self.template_manager.on_derive_variant_clicked)

        # Indicator Set Selection - delegieren an handlers
        self.indicator_set_combo.currentIndexChanged.connect(self._handlers.on_indicator_set_changed)

        logger.debug("Signals connected")

