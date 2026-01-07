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

        # Add to TabWidget
        self.tabs.addTab(self.tab_strategy, "1. Strategie")
        self.tabs.addTab(self.tab_timeframes, "2. Timeframes")
        self.tabs.addTab(self.tab_indicators, "3. Indikatoren")
        self.tabs.addTab(self.tab_run, "4. Deep Run")
        self.tabs.addTab(self.tab_logs, "5. Logs")

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
