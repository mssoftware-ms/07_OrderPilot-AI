from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from .chat_service import ChartChatService
    from .models import ChartAnalysisResult, QuickAnswerResult

logger = logging.getLogger(__name__)


class ChartChatEventsMixin:
    """ChartChatEventsMixin extracted from ChartChatWidget."""
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        pass
    def _on_bars_changed(self, value: int) -> None:
        """Handle bars spinbox value change.

        Args:
            value: New bars value
        """
        if not self._all_bars_checkbox.isChecked():
            self.service.set_lookback_bars(value)
            logger.info(f"Chart analysis lookback set to {value} bars")
    def _on_all_bars_toggled(self, state: int) -> None:
        """Handle 'all bars' checkbox toggle.

        Args:
            state: Checkbox state (Qt.CheckState)
        """
        is_checked = state == Qt.CheckState.Checked.value

        # Enable/disable spinbox
        self._bars_spinbox.setEnabled(not is_checked)

        if is_checked:
            # Use all available bars from chart
            df = getattr(self.service.chart_widget, "data", None)
            if df is not None and not df.empty:
                all_bars = len(df)
                self.service.set_lookback_bars(all_bars)
                logger.info(f"Using all available bars: {all_bars}")
            else:
                logger.warning("No chart data available for 'all bars'")
        else:
            # Use spinbox value
            self.service.set_lookback_bars(self._bars_spinbox.value())
    def on_chart_changed(self) -> None:
        """Handle chart symbol/timeframe change.

        Call this when the chart switches to a different symbol.
        """
        self.service.on_chart_changed()
        self._update_header()

        # Reload history for new chart
        self._chat_display.clear()
        self._load_existing_history()

        if not self.service.conversation_history:
            self._append_message(
                "assistant",
                f"Willkommen zur Chart-Analyse für "
                f"{self.service.current_symbol} {self.service.current_timeframe}.\n\n"
                f"Klicke auf **Vollständige Analyse** oder stelle eine Frage."
            )
    def closeEvent(self, event) -> None:
        """Handle widget close."""
        self.service.shutdown()
        super().closeEvent(event)
