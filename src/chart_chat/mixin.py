"""ChartChatMixin - Adds chat functionality to ChartWindow.

Provides seamless integration of the chat widget into the chart window.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

logger = logging.getLogger(__name__)


class ChartChatMixin:
    """Mixin that adds chart chat functionality to a window.

    Usage:
        class ChartWindow(QMainWindow, ChartChatMixin):
            def __init__(self):
                super().__init__()
                self.setup_chart_chat(self.chart_widget)
    """

    _chat_widget: Any = None
    _chat_service: Any = None

    def setup_chart_chat(
        self,
        chart_widget: "EmbeddedTradingViewChart",
        ai_service: Any | None = None,
    ) -> bool:
        """Set up the chart chat functionality.

        Args:
            chart_widget: The chart widget to analyze
            ai_service: Optional AI service (auto-creates if None)

        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from src.chart_chat.chat_service import ChartChatService
            from src.chart_chat.widget import ChartChatWidget

            logger.info("Setting up chart chat...")

            # Get or create AI service
            if ai_service is None:
                logger.info("No AI service provided, attempting to create one...")
                ai_service = self._get_or_create_ai_service()

            if ai_service is None:
                logger.warning(
                    "No AI service available for chart chat. "
                    "Check Settings -> AI tab for configuration."
                )
                # Create a placeholder dock widget with error message
                from PyQt6.QtWidgets import QDockWidget, QLabel, QVBoxLayout, QWidget

                self._chat_service = None
                self._chat_widget = QDockWidget("🤖 AI Chat (Nicht konfiguriert)", self)  # type: ignore

                # Create content widget with error message
                content = QWidget()
                layout = QVBoxLayout(content)
                error_label = QLabel(
                    "⚠️ AI Service nicht verfügbar!\n\n"
                    "Bitte konfiguriere einen AI-Provider:\n"
                    "1. Gehe zu File → Settings → AI Tab\n"
                    "2. Wähle OpenAI oder Anthropic\n"
                    "3. Setze den API-Key\n\n"
                    "Oder setze Umgebungsvariable:\n"
                    "• OPENAI_API_KEY\n"
                    "• ANTHROPIC_API_KEY"
                )
                error_label.setStyleSheet("color: #ff6b6b; padding: 20px;")
                error_label.setWordWrap(True)
                layout.addWidget(error_label)
                layout.addStretch()

                self._chat_widget.setWidget(content)

                if hasattr(self, "addDockWidget"):
                    self.addDockWidget(  # type: ignore
                        Qt.DockWidgetArea.RightDockWidgetArea,
                        self._chat_widget,
                    )
                    self._chat_widget.hide()
                    logger.info("Chat placeholder widget added (AI not configured)")

                return False

            logger.info(f"AI service available: {type(ai_service).__name__}")

            # Create chat service
            self._chat_service = ChartChatService(
                chart_widget=chart_widget,
                ai_service=ai_service,
            )

            # Create chat widget
            self._chat_widget = ChartChatWidget(
                service=self._chat_service,
                parent=self,  # type: ignore
            )

            # Add as dock widget (assumes self is QMainWindow)
            if hasattr(self, "addDockWidget"):
                self.addDockWidget(  # type: ignore
                    Qt.DockWidgetArea.RightDockWidgetArea,
                    self._chat_widget,
                )
                # Start hidden
                self._chat_widget.hide()
                logger.info("Chat widget added as dock widget (initially hidden)")

            # Connect chart change signal if available
            if hasattr(chart_widget, "symbol_changed"):
                chart_widget.symbol_changed.connect(self._on_chart_symbol_changed)

            logger.info("✅ Chart chat setup complete")
            return True

        except ImportError as e:
            logger.error("Failed to import chart chat modules: %s", e)
            self._chat_widget = None
            self._chat_service = None
            return False
        except Exception as e:
            logger.exception("Failed to setup chart chat: %s", e)
            self._chat_widget = None
            self._chat_service = None
            return False

    def _get_or_create_ai_service(self) -> Any | None:
        """Get or create an AI service instance.

        Returns:
            AI service instance or None
        """
        logger.info("🔍 _get_or_create_ai_service called...")

        # Try to get from application-wide service
        if hasattr(self, "ai_service") and self.ai_service is not None:
            logger.info("Using existing ai_service from self")
            return self.ai_service

        # Try to get from parent application
        app = self._get_parent_app()
        if app and hasattr(app, "ai_service") and app.ai_service is not None:
            logger.info("Using ai_service from parent app")
            return app.ai_service

        # Try to create from factory
        logger.info("Attempting to create AI service from factory...")
        try:
            from src.ai.ai_provider_factory import AIProviderFactory

            # Check if AI is enabled
            is_enabled = AIProviderFactory.is_ai_enabled()
            logger.info(f"AIProviderFactory.is_ai_enabled() = {is_enabled}")

            if not is_enabled:
                logger.warning("❌ AI features are disabled in settings! "
                             "Go to File -> Settings -> AI to enable.")
                return None

            logger.info("Calling AIProviderFactory.create_service()...")
            service = AIProviderFactory.create_service()

            if service:
                logger.info("✅ SUCCESS! Created AI service: %s", type(service).__name__)
                return service
            else:
                logger.error("❌ create_service() returned None!")
                return None

        except ValueError as e:
            logger.error(f"❌ ValueError creating AI service: {e}")
            logger.error(f"   This usually means: AI disabled OR no API key")
            return None
        except Exception as e:
            logger.error(f"❌ Exception creating AI service: {type(e).__name__}: {e}")
            logger.exception("Full traceback:")
            return None

    def _get_parent_app(self) -> Any | None:
        """Get the parent TradingApplication.

        Returns:
            TradingApplication instance or None
        """
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app and hasattr(app, "main_window"):
            return app.main_window

        return None

    def _on_chart_symbol_changed(self) -> None:
        """Handle chart symbol change."""
        if self._chat_widget:
            self._chat_widget.on_chart_changed()

    def toggle_chat_widget(self) -> None:
        """Toggle visibility of the chat widget."""
        if self._chat_widget:
            if self._chat_widget.isVisible():
                self._chat_widget.hide()
            else:
                self._chat_widget.show()

    def show_chat_widget(self) -> None:
        """Show the chat widget."""
        if self._chat_widget:
            self._chat_widget.show()
            self._chat_widget.raise_()

    def hide_chat_widget(self) -> None:
        """Hide the chat widget."""
        if self._chat_widget:
            self._chat_widget.hide()

    @property
    def chat_widget(self) -> Any:
        """Get the chat widget."""
        return self._chat_widget

    @property
    def chat_service(self) -> Any:
        """Get the chat service."""
        return self._chat_service

    def request_chart_analysis(self) -> None:
        """Request a full chart analysis.

        Convenience method to trigger analysis programmatically.
        """
        if self._chat_widget:
            self._chat_widget._on_full_analysis()

    def cleanup_chart_chat(self) -> None:
        """Clean up chat resources.

        Call this when closing the window.
        """
        if self._chat_service:
            self._chat_service.shutdown()

        if self._chat_widget:
            self._chat_widget.close()

        self._chat_widget = None
        self._chat_service = None
