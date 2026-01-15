"""Chart Chat Service - Orchestrates the chat functionality.

Manages conversations, coordinates between components, and handles
symbol/timeframe switching.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .analyzer import ChartAnalyzer
from .context_builder import ChartContext, ChartContextBuilder
from .history_store import HistoryStore
from .markings_manager import MarkingsManager
from .models import (
    ChatMessage,
    ChartAnalysisResult,
    MessageRole,
    QuickAnswerResult,
)

if TYPE_CHECKING:
    from src.ai.providers import AnthropicProvider, OpenAIProvider
    from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

logger = logging.getLogger(__name__)


class ChartChatService:
    """Main service for chart analysis chatbot.

    Orchestrates the conversation flow, manages history persistence,
    and coordinates between the analyzer and context builder.
    """

    def __init__(
        self,
        chart_widget: "EmbeddedTradingViewChart",
        ai_service: "OpenAIProvider | AnthropicProvider | Any",
        history_store: HistoryStore | None = None,
    ):
        """Initialize the chat service.

        Args:
            chart_widget: The chart widget to analyze
            ai_service: AI provider instance from AIProviderFactory
            history_store: Optional history store (creates default if None)
        """
        self.chart_widget = chart_widget
        self.ai_service = ai_service
        self.history_store = history_store or HistoryStore()
        self.analyzer = ChartAnalyzer(ai_service)
        self.context_builder = ChartContextBuilder(chart_widget)
        self.markings_manager = MarkingsManager(chart_widget)

        # Current conversation state
        self._current_symbol: str = ""
        self._current_timeframe: str = ""
        self._conversation: list[ChatMessage] = []
        self._lookback_bars: int = 100  # Default lookback period

        # Load history for current chart
        self._sync_with_chart()

    @property
    def current_symbol(self) -> str:
        """Get current symbol."""
        return self._current_symbol

    @property
    def current_timeframe(self) -> str:
        """Get current timeframe."""
        return self._current_timeframe

    @property
    def model_name(self) -> str:
        """Return the underlying AI model name, if available."""
        if hasattr(self.ai_service, "config") and getattr(self.ai_service, "config", None):
            return getattr(self.ai_service.config, "model", "") or ""
        return getattr(self.ai_service, "model", "") or ""

    @property
    def conversation_history(self) -> list[ChatMessage]:
        """Get current conversation history."""
        return self._conversation.copy()

    def _sync_with_chart(self) -> None:
        """Synchronize service with current chart state.

        Loads history if symbol/timeframe changed.
        """
        symbol = getattr(self.chart_widget, "current_symbol", "") or ""
        timeframe = getattr(self.chart_widget, "current_timeframe", "") or "1T"

        if symbol != self._current_symbol or timeframe != self._current_timeframe:
            # Save current history before switching
            if self._current_symbol and self._conversation:
                self._save_current_history()

            # Update current state
            self._current_symbol = symbol
            self._current_timeframe = timeframe

            # Load history for new symbol/timeframe
            self._conversation = self.history_store.load_history(symbol, timeframe)
            logger.debug(
                "Synced with chart: %s %s, loaded %d messages",
                symbol, timeframe, len(self._conversation)
            )

    def _save_current_history(self) -> None:
        """Save current conversation to storage."""
        if self._current_symbol and self._conversation:
            self.history_store.save_history(
                self._current_symbol,
                self._current_timeframe,
                self._conversation,
            )

    def _add_message(self, role: MessageRole, content: str) -> ChatMessage:
        """Add a message to the conversation.

        Args:
            role: Message role (user/assistant)
            content: Message content

        Returns:
            Created ChatMessage
        """
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
        )
        self._conversation.append(message)

        # Auto-save after each message
        self._save_current_history()

        return message

    def get_chart_context(self, lookback_bars: int = 100) -> ChartContext:
        """Get current chart context.

        Args:
            lookback_bars: Number of bars to include

        Returns:
            ChartContext with current chart data
        """
        self._sync_with_chart()
        return self.context_builder.build_context(lookback_bars)

    def set_lookback_bars(self, bars: int) -> None:
        """Set the number of bars for analysis.

        Args:
            bars: Number of bars to analyze (20-500)
        """
        # Clamp to valid range
        self._lookback_bars = max(20, min(500, bars))
        logger.info(f"Lookback bars set to {self._lookback_bars}")

    async def analyze_chart(self) -> ChartAnalysisResult:
        """Perform comprehensive chart analysis.

        Returns:
            ChartAnalysisResult with full analysis
        """
        self._sync_with_chart()

        # Build context with current lookback setting (markings kept for prompt completeness)
        context = self.context_builder.build_context(self._lookback_bars)
        context.markings = self.markings_manager.get_current_markings()

        # Perform full structured analysis
        result = await self.analyzer.analyze_chart(context)

        # Add to conversation
        self._add_message(
            MessageRole.USER,
            f"[Vollständige Chartanalyse für {context.symbol} {context.timeframe}]"
        )
        self._add_message(
            MessageRole.ASSISTANT,
            result.to_markdown()
        )

        return result

    async def ask_question(self, question: str) -> QuickAnswerResult:
        """Ask a question about the current chart.

        Args:
            question: User's question

        Returns:
            QuickAnswerResult with answer
        """
        self._sync_with_chart()

        # Get current markings
        markings_state = self.markings_manager.get_current_markings()

        # Build context with current lookback setting and markings
        context = self.context_builder.build_context(self._lookback_bars)
        context.markings = markings_state

        # Add user question to history
        self._add_message(MessageRole.USER, question)

        # Get answer with markings support
        result = await self.analyzer.answer_question_with_markings(
            question=question,
            context=context,
            conversation_history=self._conversation[:-1],  # Exclude just-added question
        )

        # Add assistant response to history
        self._add_message(MessageRole.ASSISTANT, result.answer)

        return result

    def clear_history(self) -> bool:
        """Clear conversation history for current chart.

        Returns:
            True if cleared successfully
        """
        self._sync_with_chart()

        # Clear in-memory
        self._conversation.clear()

        # Clear stored
        return self.history_store.clear_history(
            self._current_symbol,
            self._current_timeframe,
        )

    def get_quick_actions(self) -> list[dict[str, str]]:
        """Get list of quick action buttons for the UI.

        Returns:
            List of action dictionaries with 'label' and 'action' keys
        """
        return [
            {
                "label": "📊 Vollanalyse",
                "action": "full_analysis",
                "tooltip": "Führt eine vollständige Chartanalyse durch",
            },
            {
                "label": "📈 Trend?",
                "action": "ask",
                "question": "Was ist der aktuelle Trend?",
                "tooltip": "Fragt nach dem aktuellen Trend",
            },
            {
                "label": "🎯 Support/Widerstand?",
                "action": "ask",
                "question": "Wo liegen die wichtigsten Support- und Widerstandszonen?",
                "tooltip": "Fragt nach wichtigen Preisniveaus",
            },
            {
                "label": "⚡ Einstieg?",
                "action": "ask",
                "question": "Ist jetzt ein guter Zeitpunkt für einen Einstieg?",
                "tooltip": "Fragt nach Einstiegsmöglichkeiten",
            },
            {
                "label": "⚠️ Risiken?",
                "action": "ask",
                "question": "Welche Risiken gibt es aktuell zu beachten?",
                "tooltip": "Fragt nach aktuellen Risiken",
            },
        ]

    def get_session_info(self) -> dict[str, Any]:
        """Get information about the current chat session.

        Returns:
            Dictionary with session metadata
        """
        history_info = self.history_store.get_history_info(
            self._current_symbol,
            self._current_timeframe,
        )

        return {
            "symbol": self._current_symbol,
            "timeframe": self._current_timeframe,
            "message_count": len(self._conversation),
            "has_stored_history": history_info is not None,
            "last_updated": history_info.get("updated_at") if history_info else None,
            "ai_provider": type(self.ai_service).__name__,
        }

    def on_chart_changed(self) -> None:
        """Handle chart symbol/timeframe change.

        Call this when the chart switches to a different symbol or timeframe.
        """
        self._sync_with_chart()

    def shutdown(self) -> None:
        """Clean up resources and save state.

        Call this when closing the chat widget.
        """
        self._save_current_history()
        logger.info("ChartChatService shutdown complete")
