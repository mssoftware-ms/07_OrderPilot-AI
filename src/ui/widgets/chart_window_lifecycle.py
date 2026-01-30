"""Chart Window Lifecycle - Close event handling and cleanup.

Refactored from 706 LOC monolith using composition pattern.

Module 5/6 of chart_window.py split.

Contains:
- handle_close_event(): Main close event orchestration
- cleanup_simulation_on_close(): Stop simulation worker
- finalize_close(): Final cleanup and emit signal
- stop_live_stream_on_close(): Disconnect live stream
- save_optional_state(): Save signal history, simulator state
- cleanup_chat(): Cleanup chat resources
- cleanup_bitunix_trading(): Cleanup Bitunix resources
- request_close_state(): Request chart state before closing
- load_chart(): Load chart data async
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class ChartWindowLifecycle:
    """Helper für ChartWindow Lifecycle (Close event, Cleanup, State saving)."""

    def __init__(self, parent):
        """
        Args:
            parent: ChartWindow Instanz
        """
        self.parent = parent

    def handle_close_event(self, event: QCloseEvent):
        """Handle window close event with async state saving."""
        self.cleanup_simulation_on_close()

        if not isinstance(self.parent.chart_widget, QWidget):
            self.parent._ready_to_close = True
            event.accept()
            return

        if self.parent._ready_to_close:
            self.finalize_close(event)
            return

        self.request_close_state(event)

    def cleanup_simulation_on_close(self) -> None:
        """Stop simulation worker if running."""
        if not hasattr(self.parent, "_cleanup_simulation_worker"):
            return
        try:
            self.parent._cleanup_simulation_worker(cancel=True, wait_ms=500)
        except Exception as e:
            logger.debug("Failed to stop simulation worker during close: %s", e)

    def finalize_close(self, event: QCloseEvent) -> None:
        """Finalize window close - cleanup and emit signal."""
        logger.info(f"Closing ChartWindow for {self.parent.symbol}...")
        self.stop_live_stream_on_close()
        self.parent._unsubscribe_events()
        self.save_optional_state()
        self.save_enhanced_session_state()  # Phase 6: Enhanced persistence
        self.parent._save_window_state()
        self.cleanup_chat()
        self.cleanup_trading_bot_window()
        self.cleanup_bitunix_trading()
        self.parent.window_closed.emit(self.parent.symbol)
        event.accept()
    
    def save_enhanced_session_state(self) -> None:
        """Save enhanced session state (Phase 6: UI Refactoring).
        
        Saves:
        - Dock visibility states (Watchlist, Activity Log)
        - Active timeframe
        - Active period
        - Crosshair sync status
        """
        try:
            settings_key = self.parent._get_settings_key() if hasattr(self.parent, '_get_settings_key') else f"ChartWindow/{self.parent.symbol}"
            
            # Save Watchlist dock visibility
            if hasattr(self.parent, '_watchlist_dock'):
                self.parent.settings.setValue(
                    f"{settings_key}/watchlist_visible",
                    self.parent._watchlist_dock.isVisible()
                )
            
            # Save Activity Log dock visibility
            if hasattr(self.parent, '_activity_log_dock'):
                self.parent.settings.setValue(
                    f"{settings_key}/activity_log_visible",
                    self.parent._activity_log_dock.isVisible()
                )
            
            # Save current timeframe
            if hasattr(self.parent, 'chart_widget') and hasattr(self.parent.chart_widget, 'current_timeframe'):
                self.parent.settings.setValue(
                    f"{settings_key}/timeframe",
                    self.parent.chart_widget.current_timeframe
                )
            
            # Save current period
            if hasattr(self.parent, 'chart_widget') and hasattr(self.parent.chart_widget, 'current_period'):
                self.parent.settings.setValue(
                    f"{settings_key}/period",
                    self.parent.chart_widget.current_period
                )
            
            # Save crosshair sync status
            if hasattr(self.parent, 'chart_widget') and hasattr(self.parent.chart_widget, 'crosshair_sync_enabled'):
                self.parent.settings.setValue(
                    f"{settings_key}/crosshair_sync",
                    self.parent.chart_widget.crosshair_sync_enabled
                )
            
            logger.debug(f"Saved enhanced session state for {self.parent.symbol}")
            
        except Exception as e:
            logger.error(f"Error saving enhanced session state: {e}")


    def stop_live_stream_on_close(self) -> None:
        """Disconnect live stream if active."""
        if not (hasattr(self.parent.chart_widget, 'live_streaming_enabled') and self.parent.chart_widget.live_streaming_enabled):
            return
        try:
            self.parent.chart_widget.live_streaming_enabled = False
            if hasattr(self.parent.chart_widget, 'live_stream_button'):
                self.parent.chart_widget.live_stream_button.setChecked(False)
            if hasattr(self.parent.chart_widget, '_stop_live_stream_async'):
                asyncio.ensure_future(self.parent.chart_widget._stop_live_stream_async())
                logger.info(f"Disconnecting live stream for {self.parent.symbol}")
        except Exception as e:
            logger.debug(f"Error stopping live stream: {e}")

    def save_optional_state(self) -> None:
        """Save optional state (signal history, simulator state)."""
        if hasattr(self.parent, '_save_signal_history'):
            try:
                self.parent._save_signal_history()
            except Exception as e:
                logger.debug(f"Error saving signal history: {e}")

        if hasattr(self.parent, '_save_simulator_splitter_state'):
            try:
                self.parent._save_simulator_splitter_state()
            except Exception as e:
                logger.debug(f"Error saving simulator splitter state: {e}")

    def cleanup_chat(self) -> None:
        """Cleanup chart chat resources."""
        if hasattr(self.parent, 'cleanup_chart_chat'):
            try:
                self.parent.cleanup_chart_chat()
            except Exception as e:
                logger.debug(f"Error cleaning up chart chat: {e}")

    def cleanup_bitunix_trading(self) -> None:
        """Clean up Bitunix trading resources."""
        if hasattr(self.parent, 'cleanup_bitunix_trading'):
            try:
                self.parent.cleanup_bitunix_trading()
            except Exception as e:
                logger.debug(f"Error cleaning up Bitunix trading: {e}")

    def cleanup_trading_bot_window(self) -> None:
        """Clean up Trading Bot window resources."""
        if hasattr(self.parent, '_trading_bot_window') and self.parent._trading_bot_window:
            try:
                # Save state and close properly
                self.parent._trading_bot_window._save_window_state()
                self.parent._trading_bot_window.close()
                self.parent._trading_bot_window = None
                logger.debug("Trading Bot window cleaned up")
            except Exception as e:
                logger.debug(f"Error cleaning up Trading Bot window: {e}")

    def save_chart_state_snapshot(self) -> None:
        """Save current chart state (like on close) without closing the window."""
        try:
            settings_key = self.parent._get_settings_key()

            def on_range_received(visible_range):
                try:
                    if visible_range:
                        self.parent.settings.setValue(f"{settings_key}/visibleRange", json.dumps(visible_range))
                        logger.info(f"Saved visible range snapshot for {self.parent.symbol}")
                except Exception as e:
                    logger.error(f"Error saving visible range snapshot: {e}")

            def on_complete_state_received(complete_state):
                try:
                    if complete_state and complete_state.get('version'):
                        self.parent.settings.setValue(f"{settings_key}/chartState", json.dumps(complete_state))
                        logger.info(f"Saved complete chart state snapshot for {self.parent.symbol}")
                    else:
                        # Fallback: at least save visible range
                        self.parent.chart_widget.get_visible_range(on_range_received)
                except Exception as e:
                    logger.error(f"Error saving chart state snapshot: {e}")

            def on_layout_received(layout):
                try:
                    if layout:
                        layout_json = json.dumps(layout)
                        self.parent.settings.setValue(f"{settings_key}/paneLayout", layout_json)
                        logger.info(f"Saved pane layout snapshot for {self.parent.symbol}")
                except Exception as e:
                    logger.error(f"Error saving pane layout snapshot: {e}")

                try:
                    self.parent.chart_widget.get_chart_state(on_complete_state_received)
                except Exception as e:
                    logger.warning(f"Comprehensive state snapshot failed: {e}")
                    self.parent.chart_widget.get_visible_range(on_range_received)

            self.parent.chart_widget.get_pane_layout(on_layout_received)

        except Exception as e:
            logger.error(f"Failed to save chart state snapshot: {e}")

    def request_close_state(self, event: QCloseEvent) -> None:
        """Request chart state before closing."""
        logger.info(f"Requesting chart state before closing {self.parent.symbol}...")
        event.ignore()

        def on_complete_state_received(complete_state):
            try:
                if complete_state and complete_state.get('version'):
                    settings_key = self.parent._get_settings_key()
                    self.parent.settings.setValue(f"{settings_key}/chartState", json.dumps(complete_state))
                    logger.info(f"Saved complete chart state for {self.parent.symbol}")
                else:
                    _save_individual_components()
                    return
            except Exception as e:
                logger.error(f"Error saving complete chart state: {e}")
                _save_individual_components()
                return

            self.parent._ready_to_close = True
            QTimer.singleShot(0, self.parent.close)

        def on_range_received(visible_range):
            try:
                if visible_range:
                    settings_key = self.parent._get_settings_key()
                    self.parent.settings.setValue(f"{settings_key}/visibleRange", json.dumps(visible_range))
                    logger.info(f"Saved visible range for {self.parent.symbol}")
            except Exception as e:
                logger.error(f"Error saving visible range: {e}")

            self.parent._ready_to_close = True
            QTimer.singleShot(0, self.parent.close)

        def _save_individual_components():
            logger.info("Falling back to individual component saving")
            self.parent.chart_widget.get_visible_range(on_range_received)

        def on_layout_received(layout):
            try:
                if layout:
                    settings_key = self.parent._get_settings_key()
                    layout_json = json.dumps(layout)
                    self.parent.settings.setValue(f"{settings_key}/paneLayout", layout_json)
                    logger.info(f"Saved pane layout for {self.parent.symbol}")
            except Exception as e:
                logger.error(f"Error saving pane layout: {e}")

            try:
                self.parent.chart_widget.get_chart_state(on_complete_state_received)
            except Exception as e:
                logger.warning(f"Comprehensive state saving failed: {e}")
                _save_individual_components()

        def force_close():
            if not self.parent._ready_to_close:
                logger.warning("Chart state fetch timed out, forcing close")
                self.parent._ready_to_close = True
                self.parent.close()

        QTimer.singleShot(2000, force_close)
        self.parent.chart_widget.get_pane_layout(on_layout_received)

    async def load_chart(self, data_provider: Optional[str] = None):
        """Load chart data for the symbol.

        Args:
            data_provider: Optional data provider to use
        """
        try:
            logger.info(f"Loading chart for {self.parent.symbol} in popup window")
            await self.parent.chart_widget.load_symbol(self.parent.symbol, data_provider)
        except Exception as e:
            logger.error(f"Error loading chart in popup window: {e}", exc_info=True)
