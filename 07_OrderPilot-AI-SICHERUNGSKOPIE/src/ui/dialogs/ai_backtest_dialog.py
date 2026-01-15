"""Enhanced Backtest Dialog with AI Analysis (REFACTORED).

Provides AI-powered backtest review and recommendations.

REFACTORED: Split into focused helper modules using composition pattern.
- ai_backtest_dialog_ui_tabs.py: All 4 tab creation methods
- ai_backtest_dialog_execution.py: Backtest runner + mock result generator
- ai_backtest_dialog_display.py: Results display + chart popup
- ai_backtest_dialog_ai_review.py: AI review execution + API key check
- ai_backtest_dialog_ai_display.py: AI analysis formatting (5 methods)
"""

import logging

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
)

# Import helpers
from .ai_backtest_dialog_ui_tabs import AIBacktestDialogUITabs
from .ai_backtest_dialog_execution import AIBacktestDialogExecution
from .ai_backtest_dialog_display import AIBacktestDialogDisplay
from .ai_backtest_dialog_ai_review import AIBacktestDialogAIReview
from .ai_backtest_dialog_ai_display import AIBacktestDialogAIDisplay

logger = logging.getLogger(__name__)


class AIBacktestDialog(QDialog):
    """Enhanced backtest dialog with AI analysis (REFACTORED)."""

    def __init__(self, parent=None, current_symbol: str = None):
        """Initialize AI Backtest Dialog.

        Args:
            parent: Parent widget
            current_symbol: Currently selected symbol from chart (optional)
        """
        super().__init__(parent)
        self.setWindowTitle("AI-Powered Backtest")
        self.setModal(True)
        self.setMinimumSize(900, 700)

        self.last_result = None
        self.last_review = None
        self.current_symbol = current_symbol

        # Create helpers (composition pattern)
        self._ui_tabs = AIBacktestDialogUITabs(self)
        self._execution = AIBacktestDialogExecution(self)
        self._display = AIBacktestDialogDisplay(self)
        self._ai_review = AIBacktestDialogAIReview(self)
        self._ai_display = AIBacktestDialogAIDisplay(self)

        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # Tab 1: Configuration
        config_widget = self._ui_tabs.create_config_tab()
        tabs.addTab(config_widget, "⚙️ Configuration")

        # Tab 2: Results
        self.results_widget = self._ui_tabs.create_results_tab()
        tabs.addTab(self.results_widget, "📊 Results")

        # Tab 3: AI Analysis
        self.ai_widget = self._ui_tabs.create_ai_tab()
        tabs.addTab(self.ai_widget, "🤖 AI Analysis")

        # Tab 4: Chart Visualization
        self.chart_widget = self._ui_tabs.create_chart_tab()
        tabs.addTab(self.chart_widget, "📈 Chart")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        self.run_btn = QPushButton("🚀 Run Backtest")
        self.run_btn.clicked.connect(self.run_backtest)
        button_layout.addWidget(self.run_btn)

        self.ai_review_btn = QPushButton("🤖 AI Review")
        self.ai_review_btn.clicked.connect(self.run_ai_review)
        self.ai_review_btn.setEnabled(False)
        button_layout.addWidget(self.ai_review_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.tabs = tabs

    # === Execution (Delegiert) ===

    async def run_backtest(self):
        """Run the backtest (delegiert)."""
        return await self._execution.run_backtest()

    # === AI Review (Delegiert) ===

    async def run_ai_review(self):
        """Run AI analysis on backtest results (delegiert)."""
        return await self._ai_review.run_ai_review()
