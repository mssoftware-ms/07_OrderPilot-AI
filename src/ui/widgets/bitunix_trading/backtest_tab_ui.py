"""Backtest Tab UI - Main Orchestrator (Refactored).

Main UI setup that delegates to specialized builder modules:
- BacktestTabUIToolbar: Button toolbar creation
- BacktestTabUISetup: Setup and Execution tabs
- BacktestTabUIResults: Results and Batch/WF tabs

Refactored from 875 LOC monolith using composition pattern.

Module 4/4 of backtest_tab_ui.py split (Main Orchestrator).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QTextEdit,
    QTabWidget,
    QWidget,
)

from .backtest_tab_ui_toolbar import BacktestTabUIToolbar
from .backtest_tab_ui_setup import BacktestTabUISetup
from .backtest_tab_ui_results import BacktestTabUIResults

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestTabUI:
    """Main UI orchestrator for Backtest Tab using composition pattern.

    Delegates all UI creation to specialized builder classes:
    - BacktestTabUIToolbar: Toolbar with buttons
    - BacktestTabUISetup: Setup + Execution tabs
    - BacktestTabUIResults: Results + Batch/WF tabs
    """

    def __init__(self, parent: QWidget):
        """
        Args:
            parent: BacktestTab Widget
        """
        self.parent = parent

        # Initialize helper builders (composition pattern)
        self._toolbar_builder = BacktestTabUIToolbar(parent)
        self._setup_builder = BacktestTabUISetup(parent)
        self._results_builder = BacktestTabUIResults(parent)

    def setup_ui(self) -> None:
        """Erstellt das UI Layout (delegates to helper builders)."""
        # Global theme handles styling now
        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # --- Kompakte Button-Leiste (delegated to toolbar builder) ---
        button_row = self._toolbar_builder.create_compact_button_row()
        layout.addLayout(button_row)

        # --- Sub-Tabs ---
        self.parent.sub_tabs = QTabWidget()
        # Theme handles styling

        # Tab 1: Setup (delegated to setup builder)
        self.parent.sub_tabs.addTab(self._setup_builder.create_setup_tab(), "📁 Setup")

        # Tab 2: Execution Settings (delegated to setup builder)
        self.parent.sub_tabs.addTab(self._setup_builder.create_execution_tab(), "⚙️ Execution")

        # Tab 3: Results (delegated to results builder)
        self.parent.sub_tabs.addTab(self._results_builder.create_results_tab(), "📊 Results")

        # Tab 4: Batch/Walk-Forward (delegated to results builder)
        self.parent.sub_tabs.addTab(self._results_builder.create_batch_tab(), "🔄 Batch/WF")

        layout.addWidget(self.parent.sub_tabs)

        # --- Log Section ---
        log_group = QGroupBox("📜 Log")
        log_layout = QVBoxLayout(log_group)

        self.parent.log_text = QTextEdit()
        self.parent.log_text.setReadOnly(True)
        self.parent.log_text.setMaximumHeight(120)
        # Theme handles styling
        log_layout.addWidget(self.parent.log_text)

        layout.addWidget(log_group)

    # =========================================================================
    # DELEGATED METHODS (for backward compatibility)
    # =========================================================================

    def create_compact_button_row(self):
        """Create button toolbar (delegated to toolbar builder)."""
        return self._toolbar_builder.create_compact_button_row()

    def create_setup_tab(self):
        """Create setup tab (delegated to setup builder)."""
        return self._setup_builder.create_setup_tab()

    def create_execution_tab(self):
        """Create execution tab (delegated to setup builder)."""
        return self._setup_builder.create_execution_tab()

    def create_results_tab(self):
        """Create results tab (delegated to results builder)."""
        return self._results_builder.create_results_tab()

    def create_batch_tab(self):
        """Create batch/WF tab (delegated to results builder)."""
        return self._results_builder.create_batch_tab()

    def create_kpi_card(self, title: str, value: str, color: str):
        """Create KPI card (delegated to results builder)."""
        return self._results_builder.create_kpi_card(title, value, color)
