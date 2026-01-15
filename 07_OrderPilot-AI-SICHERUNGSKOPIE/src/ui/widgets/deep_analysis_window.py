"""Main Widget for Deep AI Analysis.

Combines the Strategy, Timeframes, Indicators, and Deep Run tabs.
Integrates with the existing "Tab 0" analysis via AnalysisContext.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget
)
from src.core.analysis.context import AnalysisContext
from src.core.analysis.models import InitialAnalysisResult
from src.ui.widgets.analysis_tabs.strategy_tab import StrategyTab
from src.ui.widgets.analysis_tabs.timeframes_tab import TimeframesTab
from src.ui.widgets.analysis_tabs.indicators_tab import IndicatorsTab
from src.ui.widgets.analysis_tabs.deep_run_tab import DeepRunTab
from src.ui.widgets.analysis_tabs.log_viewer_tab import LogViewerTab
from src.ui.widgets.analysis_tabs.ai_chat_tab import AIChatTab
from src.ui.widgets.analysis_tabs.data_overview_tab import DataOverviewTab

class DeepAnalysisWidget(QWidget):
    """Container for the advanced analysis workflow."""

    def __init__(self):
        super().__init__()
        self.context = AnalysisContext()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        
        # Initialize Tabs
        self.tab_strategy = StrategyTab(self.context)
        self.tab_timeframes = TimeframesTab(self.context)
        self.tab_indicators = IndicatorsTab(self.context)
        self.tab_run = DeepRunTab(self.context)
        self.tab_logs = LogViewerTab(self.context)
        self.tab_chat = AIChatTab(self.context)  # Phase 5.8-5.10
        self.tab_data_overview = DataOverviewTab(self.context)  # KI-Datenübersicht

        # Add to TabWidget
        self.tabs.addTab(self.tab_strategy, "1. Strategie")
        self.tabs.addTab(self.tab_timeframes, "2. Timeframes")
        self.tabs.addTab(self.tab_indicators, "3. Indikatoren")
        self.tabs.addTab(self.tab_run, "4. Deep Run")
        self.tabs.addTab(self.tab_data_overview, "5. 📊 Datenübersicht")  # Neuer Tab
        self.tabs.addTab(self.tab_logs, "6. Logs")
        self.tabs.addTab(self.tab_chat, "7. 🤖 AI Chat")  # Phase 5.8-5.10

        layout.addWidget(self.tabs)

    def update_from_initial_analysis(self, result_json: dict):
        """Updates the context with the result from Tab 0.
        
        Args:
            result_json: Dictionary matching the Tab 0 output format.
        """
        try:
            # Validate/Parse
            result = InitialAnalysisResult(**result_json)
            # Update Context
            self.context.set_initial_analysis(result)
            
            # Switch to Strategy tab to show user the new regime status
            self.tabs.setCurrentIndex(0)

        except Exception as e:
            print(f"Error updating deep analysis context: {e}")

    def set_market_context(self, context) -> None:
        """Set MarketContext for AI Chat Tab and Data Overview (Phase 5.8).

        Args:
            context: MarketContext instance
        """
        if hasattr(self, 'tab_chat'):
            self.tab_chat.set_market_context(context)
        if hasattr(self, 'tab_data_overview'):
            self.tab_data_overview.set_market_context(context)

    def get_draw_zone_signal(self):
        """Get the draw_zone_requested signal from AI Chat Tab (Phase 5.9).

        Returns:
            pyqtSignal for draw zone requests
        """
        if hasattr(self, 'tab_chat'):
            return self.tab_chat.draw_zone_requested
        return None
