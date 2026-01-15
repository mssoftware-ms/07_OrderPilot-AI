"""AI Backtest Dialog AI Review - AI Analysis Execution.

Refactored from ai_backtest_dialog.py.

Contains:
- run_ai_review: Async method to request AI analysis of backtest results
- _show_no_api_key_message: Display QMessageBox for missing API key
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from .ai_backtest_dialog import AIBacktestDialog

logger = logging.getLogger(__name__)


class AIBacktestDialogAIReview:
    """Helper for AI review execution."""

    def __init__(self, parent: "AIBacktestDialog"):
        self.parent = parent

    @qasync.asyncSlot()
    async def run_ai_review(self):
        """Run AI analysis on backtest results."""
        if not self.parent.last_result:
            QMessageBox.warning(self.parent, "No Results", "Please run a backtest first.")
            return

        # Check for API key
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            self._show_no_api_key_message()
            return

        self.parent.ai_review_btn.setEnabled(False)
        self.parent.ai_review_btn.setText("Analyzing...")

        try:
            # ===== CRITICAL: USE MULTI-PROVIDER AI FACTORY =====
            from src.ai import get_ai_service

            # Get AI service based on user settings (OpenAI or Anthropic)
            try:
                service = await get_ai_service()
            except ValueError as e:
                QMessageBox.warning(
                    self.parent, "AI Not Configured",
                    f"AI service not available:\n{str(e)}\n\n"
                    f"Please configure AI settings in Settings -> AI tab."
                )
                return

            try:
                # Get AI review
                review = await service.review_backtest(self.parent.last_result)
                self.parent.last_review = review

                # Display AI analysis
                self.parent._ai_display.display_ai_analysis(review)

                # Switch to AI tab
                self.parent.tabs.setCurrentIndex(2)

            finally:
                await service.close()

        except Exception as e:
            QMessageBox.critical(self.parent, "AI Analysis Error", f"Failed to analyze:\n{str(e)}")

        finally:
            self.parent.ai_review_btn.setEnabled(True)
            self.parent.ai_review_btn.setText("🤖 AI Review")

    def _show_no_api_key_message(self):
        """Show message when no API key is configured."""
        msg = QMessageBox(self.parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("API Key Required")
        msg.setText("AI Analysis requires an API key.")
        msg.setInformativeText(
            "Please set one of these environment variables:\n\n"
            "• ANTHROPIC_API_KEY (for Claude Sonnet 4.5)\n"
            "• OPENAI_API_KEY (for GPT-5.1)\n\n"
            "Restart the application after setting the key."
        )
        msg.exec()
