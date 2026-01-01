"""Chart Chat Widget - PyQt6 UI for the chatbot."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDockWidget

from .chart_chat_actions_mixin import ChartChatActionsMixin
from .chart_chat_events_mixin import ChartChatEventsMixin
from .chart_chat_export_mixin import ChartChatExportMixin
from .chart_chat_history_mixin import ChartChatHistoryMixin
from .chart_chat_ui_mixin import ChartChatUIMixin
from .chart_chat_worker import AnalysisWorker

if TYPE_CHECKING:
    from .chat_service import ChartChatService
    from .models import ChartAnalysisResult, QuickAnswerResult

logger = logging.getLogger(__name__)


class ChartChatWidget(
    ChartChatUIMixin,
    ChartChatHistoryMixin,
    ChartChatActionsMixin,
    ChartChatExportMixin,
    ChartChatEventsMixin,
    QDockWidget,
):
    """Dockable chat widget for chart analysis."""

    analysis_requested = pyqtSignal(str)

    def __init__(
        self,
        service: "ChartChatService",
        parent: QWidget | None = None,
    ):
        """Initialize the chat widget.

        Args:
            service: ChartChatService instance
            parent: Parent widget
        """
        super().__init__("Chart Analysis", parent)

        self.service = service
        self._worker: AnalysisWorker | None = None

        self._setup_ui()
        self._connect_signals()
        self._load_existing_history()

        # Connect bars controls
        self._bars_spinbox.valueChanged.connect(self._on_bars_changed)
        self._all_bars_checkbox.stateChanged.connect(self._on_all_bars_toggled)
