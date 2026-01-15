"""Panels Mixin for ChartWindow.

Contains the main panel/tab creation for the dock widget.
Only Bot-related tabs are created here.
"""

import logging

from PyQt6.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

# WhatsApp Widget Import
try:
    from src.ui.widgets.whatsapp_widget import WhatsAppWidget
    HAS_WHATSAPP = True
except ImportError:
    HAS_WHATSAPP = False
    logger.debug("WhatsAppWidget not available")

# Backtesting Widget Import
try:
    from src.ui.widgets.bitunix_trading.backtest_tab import BacktestTab
    HAS_BACKTEST = True
except ImportError:
    HAS_BACKTEST = False
    logger.debug("BacktestTab not available")

# AI Chat Tab Import (Issue #36)
try:
    from src.ui.widgets.analysis_tabs.ai_chat_tab import AIChatTab
    from src.core.analysis.context import AnalysisContext
    HAS_AI_CHAT = True
except ImportError:
    HAS_AI_CHAT = False
    logger.debug("AIChatTab not available")


class PanelsMixin:
    """Mixin providing panel/tab creation for ChartWindow."""

    def _create_bottom_panel(self) -> QWidget:
        """Create bottom panel with Bot tabs only."""
        panel_container = QWidget()
        panel_layout = QVBoxLayout(panel_container)
        panel_layout.setContentsMargins(5, 5, 5, 5)

        self.panel_tabs = QTabWidget()

        # Bot Tabs (from BotPanelsMixin)
        if hasattr(self, '_create_bot_control_tab'):
            # Tab 1: Bot Control
            self.bot_control_tab = self._create_bot_control_tab()
            self.panel_tabs.addTab(self.bot_control_tab, "Bot")

            # Tab 2: Daily Strategy Selection
            self.bot_strategy_tab = self._create_strategy_selection_tab()
            self.panel_tabs.addTab(self.bot_strategy_tab, "Daily Strategy")

            # Tab 3: Signals & Trade Management
            self.bot_signals_tab = self._create_signals_tab()
            self.panel_tabs.addTab(self.bot_signals_tab, "Signals")

            # Tab 4: KI Logs
            self.bot_ki_tab = self._create_ki_logs_tab()
            self.panel_tabs.addTab(self.bot_ki_tab, "KI Logs")

            # Tab 5: Engine Settings
            if hasattr(self, '_create_engine_settings_tab'):
                self.bot_engine_settings_tab = self._create_engine_settings_tab()
                self.panel_tabs.addTab(self.bot_engine_settings_tab, "Engine Settings")

            # Tab 6: Backtesting
            if HAS_BACKTEST:
                try:
                    # BacktestTab braucht einen HistoryManager
                    history_manager = getattr(self, '_history_manager', None)
                    self.backtest_tab = BacktestTab(history_manager=history_manager)
                    self.panel_tabs.addTab(self.backtest_tab, "📊 Backtesting")
                    logger.info("Backtesting Tab added to Trading Bot panel")
                except Exception as e:
                    logger.warning(f"Failed to create Backtesting tab: {e}")

            # Tab 7: WhatsApp Notifications
            if HAS_WHATSAPP:
                try:
                    self.whatsapp_tab = WhatsAppWidget()
                    self.panel_tabs.addTab(self.whatsapp_tab, "📱 WhatsApp")
                    logger.info("WhatsApp Tab added to Trading Bot panel")
                except Exception as e:
                    logger.warning(f"Failed to create WhatsApp tab: {e}")

            # Initialize bot panel state
            if hasattr(self, '_init_bot_panels'):
                self._init_bot_panels()

        # Tab 5: KO-Finder (from KOFinderMixin)
        if hasattr(self, '_create_ko_finder_tab'):
            self.ko_finder_tab = self._create_ko_finder_tab()
            self.panel_tabs.addTab(self.ko_finder_tab, "KO-Finder")

        # Tab 6: Strategy Simulator (from StrategySimulatorMixin)
        if hasattr(self, '_create_strategy_simulator_tab'):
            self.strategy_simulator_tab = self._create_strategy_simulator_tab()
            self.panel_tabs.addTab(self.strategy_simulator_tab, "Strategy Simulator")

        # Tab 7: AI Chat (Issue #36 - moved from AI-Analyse window)
        if HAS_AI_CHAT:
            try:
                # Create a local AnalysisContext for the chat tab
                self._ai_chat_context = AnalysisContext()
                self.ai_chat_tab = AIChatTab(self._ai_chat_context)
                self.panel_tabs.addTab(self.ai_chat_tab, "🤖 AI Chat")
                logger.info("AI Chat Tab added to Trading Bot panel (Issue #36)")

                # Connect draw signals to chart widget if available
                if hasattr(self, 'chart_widget'):
                    self._connect_ai_chat_signals()
            except Exception as e:
                logger.warning(f"Failed to create AI Chat tab: {e}")

        panel_layout.addWidget(self.panel_tabs)
        return panel_container

    def _connect_ai_chat_signals(self) -> None:
        """Connect AI Chat tab signals to chart widget (Issue #36)."""
        if not hasattr(self, 'ai_chat_tab'):
            return

        try:
            # Connect draw_zone_requested signal
            if hasattr(self.ai_chat_tab, 'draw_zone_requested'):
                self.ai_chat_tab.draw_zone_requested.connect(self._on_ai_chat_draw_zone)

            # Connect draw_level_requested signal
            if hasattr(self.ai_chat_tab, 'draw_level_requested'):
                self.ai_chat_tab.draw_level_requested.connect(self._on_ai_chat_draw_level)

            logger.debug("AI Chat signals connected to chart")
        except Exception as e:
            logger.warning(f"Failed to connect AI Chat signals: {e}")

    def _on_ai_chat_draw_zone(self, zone_type: str, top: float, bottom: float, label: str) -> None:
        """Handle draw zone request from AI Chat (Issue #36).

        Args:
            zone_type: Type of zone (support/resistance)
            top: Top price of zone
            bottom: Bottom price of zone
            label: Zone label
        """
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_zone'):
            try:
                color = "#4CAF50" if zone_type == "support" else "#f44336"
                self.chart_widget.add_zone(bottom, top, color, label)
                logger.info(f"Drew {zone_type} zone from AI Chat: {bottom}-{top}")
            except Exception as e:
                logger.warning(f"Failed to draw zone from AI Chat: {e}")

    def _on_ai_chat_draw_level(self, level_type: str, top: float, bottom: float, label: str) -> None:
        """Handle draw level request from AI Chat (Issue #36).

        Args:
            level_type: Type of level
            top: Top price
            bottom: Bottom price (for horizontal line, same as top)
            label: Level label
        """
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_horizontal_line'):
            try:
                price = (top + bottom) / 2
                color = "#4CAF50" if "support" in level_type.lower() else "#f44336"
                self.chart_widget.add_horizontal_line(price, label, color)
                logger.info(f"Drew {level_type} level from AI Chat at {price}")
            except Exception as e:
                logger.warning(f"Failed to draw level from AI Chat: {e}")

    def update_ai_chat_context(self, market_context) -> None:
        """Update AI Chat tab with current MarketContext (Issue #36).

        Args:
            market_context: MarketContext instance from chart
        """
        if hasattr(self, 'ai_chat_tab') and hasattr(self.ai_chat_tab, 'set_market_context'):
            self.ai_chat_tab.set_market_context(market_context)

    def _toggle_bottom_panel(self):
        """Toggle visibility of Trading Bot window."""
        if not hasattr(self.chart_widget, 'toggle_panel_button'):
            return

        button = self.chart_widget.toggle_panel_button
        should_show = button.isChecked()

        # Use TradingBotWindow if available, otherwise fall back to dock_widget
        if hasattr(self, '_trading_bot_window') and self._trading_bot_window is not None:
            if should_show:
                self._trading_bot_window.show()
                self._trading_bot_window.raise_()
                self._trading_bot_window.activateWindow()
            else:
                self._trading_bot_window.hide()
        elif hasattr(self, 'dock_widget') and self.dock_widget is not None:
            self.dock_widget.setVisible(should_show)

        self._update_toggle_button_text()

    def _on_dock_visibility_changed(self, visible: bool):
        """Handle dock visibility changes."""
        if hasattr(self.chart_widget, 'toggle_panel_button'):
            self.chart_widget.toggle_panel_button.setChecked(visible)
            self._update_toggle_button_text()

    def _update_toggle_button_text(self):
        """Update the toggle button text based on state."""
        if hasattr(self.chart_widget, 'toggle_panel_button'):
            button = self.chart_widget.toggle_panel_button
            if button.isChecked():
                button.setText("▼ Trading Bot")
            else:
                button.setText("▶ Trading Bot")
