"""AI Analysis Window - Popup window for AI Market Analysis.

REFACTORED: Split into 5 helper modules using composition pattern:
- ai_analysis_worker.py: AnalysisWorker (data fetching + analysis)
- ai_analysis_ui.py: UI setup methods
- ai_analysis_handlers.py: Event handlers and analysis logic
- ai_analysis_context.py: Context and chat integration
- ai_analysis_prompt_editor.py: PromptEditorDialog

Triggered from Chart Window.
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import QSettings

from src.core.ai_analysis.engine import AIAnalysisEngine
from src.config.loader import config_manager

# Import helper modules (composition pattern)
from src.ui.ai_analysis_ui import AIAnalysisUI
from src.ui.ai_analysis_handlers import AIAnalysisHandlers
from src.ui.ai_analysis_context import AIAnalysisContext

# Use dedicated analysis logger
analysis_logger = logging.getLogger('ai_analysis')


class AIAnalysisWindow(QDialog):
    """
    Popup window for AI Market Analysis.
    Triggered from Chart Window.
    """
    def __init__(self, parent=None, symbol: str = ""):
        super().__init__(parent)
        self.symbol = symbol
        self.setWindowTitle(f"AI Analysis - {symbol}")
        self.resize(800, 800)
        self.settings = QSettings("OrderPilot", "TradingApp")

        # Clear Analyse.log for fresh analysis session
        try:
            analyse_log_path = Path("logs/Analyse.log")
            if analyse_log_path.exists():
                analyse_log_path.write_text("")  # Clear the file
                analysis_logger.info("Analyse.log cleared for new analysis session")
        except Exception as e:
            # Don't fail if log clearing fails
            print(f"Warning: Could not clear Analyse.log: {e}")

        self.engine: Optional[AIAnalysisEngine] = None
        try:
            api_key = config_manager.get_credential("openai_api_key")
            self.engine = AIAnalysisEngine(api_key=api_key)
        except Exception:
            self.engine = None

        # Instantiate helper modules (composition pattern)
        self._ui = AIAnalysisUI(parent=self)
        self._handlers = AIAnalysisHandlers(parent=self)
        self._context = AIAnalysisContext(parent=self)

        # Setup
        self._ui.init_ui()
        self._ui.load_settings()

    def showEvent(self, event):
        """Refresh settings when window is shown.

        Delegates to AIAnalysisUI.load_settings() and AIAnalysisContext.update_chat_context().
        """
        super().showEvent(event)
        self._ui.load_settings()
        # Phase 5.8: Update AI Chat Tab with MarketContext
        self._context.update_chat_context()


# Re-export for backward compatibility
__all__ = [
    "AIAnalysisWindow",
]
