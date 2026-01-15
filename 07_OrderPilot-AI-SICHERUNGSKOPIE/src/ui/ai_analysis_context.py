"""AI Analysis Context - Context and chat integration.

Refactored from 822 LOC monolith using composition pattern.

Module 4/5 of ai_analysis_window.py split.

Contains:
- update_chat_context(): Update AI Chat Tab with MarketContext
- connect_chat_draw_signal(): Connect chat draw signal
- on_chat_draw_zone(): Handle draw zone request from AI Chat
- update_regime_info(): Update regime info panel
- detect_and_update_regime(): Detect and update regime
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

analysis_logger = logging.getLogger('ai_analysis')


class AIAnalysisContext:
    """Helper für AIAnalysisWindow Context (Chat, Regime, Drawing)."""

    def __init__(self, parent):
        """
        Args:
            parent: AIAnalysisWindow Instanz
        """
        self.parent = parent

    def update_chat_context(self) -> None:
        """Update AI Chat Tab with MarketContext (Phase 5.8)."""
        try:
            if not hasattr(self.parent.parent(), 'chart_widget'):
                return

            chart_widget = self.parent.parent().chart_widget

            # Get chart data
            df = getattr(chart_widget, 'data', None)
            symbol = getattr(chart_widget, 'symbol', getattr(chart_widget, 'current_symbol', self.parent.symbol))
            timeframe = getattr(chart_widget, 'current_timeframe', '1H')

            if df is None or df.empty:
                analysis_logger.debug("No chart data available for chat context")
                return

            # Build MarketContext
            from src.core.trading_bot.market_context_builder import MarketContextBuilder

            builder = MarketContextBuilder()
            context = builder.build(
                symbol=symbol,
                timeframe=timeframe,
                df=df,
            )

            # Update chat tab
            if hasattr(self.parent, 'deep_analysis_tab') and hasattr(self.parent.deep_analysis_tab, 'set_market_context'):
                self.parent.deep_analysis_tab.set_market_context(context)
                analysis_logger.info(f"Chat context updated: {symbol} {timeframe}")

            # Connect draw signal to chart (Phase 5.9)
            self.connect_chat_draw_signal()

        except Exception as e:
            analysis_logger.warning(f"Failed to update chat context: {e}")

    def connect_chat_draw_signal(self) -> None:
        """Connect AI Chat draw signal to chart widget (Phase 5.9)."""
        try:
            if not hasattr(self.parent, 'deep_analysis_tab'):
                return

            draw_signal = self.parent.deep_analysis_tab.get_draw_zone_signal()
            if draw_signal is None:
                return

            # Disconnect existing connection if any
            try:
                draw_signal.disconnect(self.on_chat_draw_zone)
            except TypeError:
                pass  # Not connected yet

            # Connect to chart draw handler
            draw_signal.connect(self.on_chat_draw_zone)
            analysis_logger.debug("Chat draw signal connected")

        except Exception as e:
            analysis_logger.warning(f"Failed to connect chat draw signal: {e}")

    def on_chat_draw_zone(self, zone_type: str, top: float, bottom: float, label: str) -> None:
        """Handle draw zone request from AI Chat (Phase 5.9).

        Args:
            zone_type: "support" or "resistance"
            top: Zone top price
            bottom: Zone bottom price
            label: Zone label
        """
        try:
            if not hasattr(self.parent.parent(), 'chart_widget'):
                return

            chart_widget = self.parent.parent().chart_widget

            # Use the chart's add_zone method if available
            if hasattr(chart_widget, 'add_zone'):
                import time
                start_time = int(time.time()) - 86400 * 7  # Last 7 days
                end_time = int(time.time()) + 86400  # Tomorrow

                # Map zone type to color
                color_map = {
                    "support": "rgba(46, 125, 50, 0.25)",
                    "resistance": "rgba(198, 40, 40, 0.25)",
                }
                color = color_map.get(zone_type.lower(), "rgba(100, 100, 100, 0.25)")

                zone_id = f"ai_chat_{zone_type}_{int(time.time())}"

                chart_widget.add_zone(
                    start_time=start_time,
                    end_time=end_time,
                    top_price=top,
                    bottom_price=bottom,
                    zone_type=zone_type,
                    label=f"AI: {label}",
                    color=color,
                    zone_id=zone_id,
                )
                analysis_logger.info(f"Chat zone drawn: {zone_type} {bottom:.2f}-{top:.2f}")

        except Exception as e:
            analysis_logger.error(f"Failed to draw chat zone: {e}")

    def update_regime_info(self, result) -> None:
        """
        Update the regime info panel with detection results.

        Args:
            result: RegimeResult from RegimeDetectorService
        """
        if hasattr(self.parent, "_regime_panel") and self.parent._regime_panel:
            self.parent._regime_panel.set_regime_result(result)

    def detect_and_update_regime(self, df) -> None:
        """
        Detect regime from DataFrame and update panel.

        Args:
            df: DataFrame with OHLCV data
        """
        if df is None or df.empty:
            return

        try:
            from src.core.trading_bot.regime_detector import get_regime_detector

            detector = get_regime_detector()
            result = detector.detect(df)
            self.update_regime_info(result)
        except Exception as e:
            analysis_logger.warning(f"Failed to detect regime: {e}")
