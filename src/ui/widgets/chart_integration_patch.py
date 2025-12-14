"""Integration Patch for Existing OrderPilot-AI Chart Components.

This module provides seamless integration of the new chart state persistence
system with existing chart components without breaking current functionality.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def patch_embedded_tradingview_chart():
    """Patch existing EmbeddedTradingViewChart with state persistence.

    This function enhances the existing EmbeddedTradingViewChart class
    with state persistence capabilities.
    """
    try:
        from .embedded_tradingview_chart import EmbeddedTradingViewChart
        from .chart_state_integration import TradingViewChartStateMixin

        # Check if already patched
        if hasattr(EmbeddedTradingViewChart, '__chart_state_patched__'):
            logger.debug("EmbeddedTradingViewChart already patched")
            return

        # Create enhanced class with mixin
        class EnhancedEmbeddedTradingViewChart(TradingViewChartStateMixin, EmbeddedTradingViewChart):
            """Enhanced EmbeddedTradingViewChart with state persistence."""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                # Initialize state management
                self.__init_chart_state__()

                # Connect existing signals to state management
                self._connect_state_management_hooks()

                logger.debug("Enhanced EmbeddedTradingViewChart initialized with state persistence")

            def _connect_state_management_hooks(self):
                """Connect existing functionality to state management."""
                # Hook into existing methods to trigger state saves

                # Override _on_symbol_change to load state for new symbol
                original_on_symbol_change = getattr(self, '_on_symbol_change', None)
                if original_on_symbol_change:
                    def enhanced_on_symbol_change(symbol):
                        # Call original method
                        result = original_on_symbol_change(symbol)

                        # Load state for new symbol (with delay to allow chart to initialize)
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(1500, self.load_chart_state_now)

                        return result

                    self._on_symbol_change = enhanced_on_symbol_change

                # Hook into JavaScript execution completion
                original_execute_js = getattr(self, '_execute_js', None)
                if original_execute_js:
                    def enhanced_execute_js(js_code):
                        result = original_execute_js(js_code)

                        # If this was an indicator or layout change, trigger state save
                        if any(keyword in js_code.lower() for keyword in
                               ['indicator', 'pane', 'layout', 'resize', 'stretch']):
                            self._on_indicator_changed()

                        return result

                    self._execute_js = enhanced_execute_js

                # Hook into page load completion
                original_on_page_loaded = getattr(self, '_on_page_loaded', None)
                if original_on_page_loaded:
                    def enhanced_on_page_loaded(ok):
                        result = original_on_page_loaded(ok)

                        # Load saved state after page loads
                        if ok:
                            from PyQt6.QtCore import QTimer
                            QTimer.singleShot(2000, self.load_chart_state_now)

                        return result

                    self._on_page_loaded = enhanced_on_page_loaded

            def closeEvent(self, event):
                """Enhanced close event with state saving."""
                try:
                    # Save state before closing
                    self.save_chart_state_now()
                except Exception as e:
                    logger.error(f"Failed to save state on close: {e}")

                # Call parent close event
                if hasattr(super(), 'closeEvent'):
                    super().closeEvent(event)
                else:
                    event.accept()

        # Mark as patched
        EnhancedEmbeddedTradingViewChart.__chart_state_patched__ = True

        # Replace the original class
        import sys
        module = sys.modules['src.ui.widgets.embedded_tradingview_chart']
        module.EmbeddedTradingViewChart = EnhancedEmbeddedTradingViewChart

        logger.info("Successfully patched EmbeddedTradingViewChart with state persistence")

    except ImportError:
        logger.warning("EmbeddedTradingViewChart not available for patching")
    except Exception as e:
        logger.error(f"Failed to patch EmbeddedTradingViewChart: {e}")


def patch_chart_view():
    """Patch existing ChartView with state persistence."""
    try:
        from .chart_view import ChartView
        from .chart_state_integration import PyQtGraphChartStateMixin

        # Check if already patched
        if hasattr(ChartView, '__chart_state_patched__'):
            logger.debug("ChartView already patched")
            return

        # Create enhanced class
        class EnhancedChartView(PyQtGraphChartStateMixin, ChartView):
            """Enhanced ChartView with state persistence."""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                # Initialize state management
                self.__init_chart_state__()

                # Connect hooks
                self._connect_pyqtgraph_hooks()

                logger.debug("Enhanced ChartView initialized with state persistence")

            def _connect_pyqtgraph_hooks(self):
                """Connect PyQtGraph-specific hooks."""
                # Hook into zoom methods
                if hasattr(self, '_zoom_in'):
                    original_zoom_in = self._zoom_in
                    def enhanced_zoom_in():
                        result = original_zoom_in()
                        self._schedule_state_save()
                        return result
                    self._zoom_in = enhanced_zoom_in

                if hasattr(self, '_zoom_out'):
                    original_zoom_out = self._zoom_out
                    def enhanced_zoom_out():
                        result = original_zoom_out()
                        self._schedule_state_save()
                        return result
                    self._zoom_out = enhanced_zoom_out

                if hasattr(self, '_reset_view'):
                    original_reset_view = self._reset_view
                    def enhanced_reset_view():
                        result = original_reset_view()
                        self._schedule_state_save()
                        return result
                    self._reset_view = enhanced_reset_view

                # Hook into indicator updates
                if hasattr(self, '_draw_indicators'):
                    original_draw_indicators = self._draw_indicators
                    def enhanced_draw_indicators():
                        result = original_draw_indicators()
                        self._schedule_state_save()
                        return result
                    self._draw_indicators = enhanced_draw_indicators

            def _schedule_state_save(self):
                """Schedule state save with debouncing."""
                if not hasattr(self, '_state_save_timer'):
                    from PyQt6.QtCore import QTimer
                    self._state_save_timer = QTimer()
                    self._state_save_timer.setSingleShot(True)
                    self._state_save_timer.timeout.connect(self.save_chart_state_now)

                self._state_save_timer.start(2000)  # 2 second delay

        # Mark as patched
        EnhancedChartView.__chart_state_patched__ = True

        # Replace the original class
        import sys
        module = sys.modules['src.ui.widgets.chart_view']
        module.ChartView = EnhancedChartView

        logger.info("Successfully patched ChartView with state persistence")

    except ImportError:
        logger.warning("ChartView not available for patching")
    except Exception as e:
        logger.error(f"Failed to patch ChartView: {e}")


def patch_chart_window():
    """Patch existing ChartWindow with enhanced state management."""
    try:
        from .chart_window import ChartWindow

        # Check if already patched
        if hasattr(ChartWindow, '__chart_state_patched__'):
            logger.debug("ChartWindow already patched")
            return

        # Store original methods
        original_init = ChartWindow.__init__
        original_close_event = getattr(ChartWindow, 'closeEvent', None)
        original_save_window_state = getattr(ChartWindow, '_save_window_state', None)

        def enhanced_init(self, symbol, history_manager=None, parent=None):
            """Enhanced initialization with state management."""
            # Call original init
            original_init(self, symbol, history_manager, parent)

            # Initialize enhanced state management
            from .chart_state_manager import get_chart_state_manager
            self.state_manager = get_chart_state_manager()

            # Schedule state restoration
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, self._restore_enhanced_state)

        def enhanced_close_event(self, event):
            """Enhanced close event with comprehensive state saving."""
            try:
                # Save enhanced state
                self._save_enhanced_state()

                # Call original close event
                if original_close_event:
                    original_close_event(self, event)
                else:
                    event.accept()

            except Exception as e:
                logger.error(f"Error in enhanced close event: {e}")
                event.accept()

        def _save_enhanced_state(self):
            """Save enhanced state including chart widget state."""
            try:
                # Save original window state if available
                if original_save_window_state:
                    original_save_window_state(self)

                # Save chart widget state if it has state persistence
                if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'save_chart_state_now'):
                    self.chart_widget.save_chart_state_now()

            except Exception as e:
                logger.error(f"Failed to save enhanced state: {e}")

        def _restore_enhanced_state(self):
            """Restore enhanced state including chart widget state."""
            try:
                # Restore chart widget state if available
                if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'load_chart_state_now'):
                    self.chart_widget.load_chart_state_now()

            except Exception as e:
                logger.error(f"Failed to restore enhanced state: {e}")

        # Patch methods
        ChartWindow.__init__ = enhanced_init
        ChartWindow.closeEvent = enhanced_close_event
        ChartWindow._save_enhanced_state = _save_enhanced_state
        ChartWindow._restore_enhanced_state = _restore_enhanced_state

        # Mark as patched
        ChartWindow.__chart_state_patched__ = True

        logger.info("Successfully patched ChartWindow with enhanced state management")

    except ImportError:
        logger.warning("ChartWindow not available for patching")
    except Exception as e:
        logger.error(f"Failed to patch ChartWindow: {e}")


def patch_chart_factory():
    """Patch ChartFactory to create state-enabled charts by default."""
    try:
        from .chart_factory import ChartFactory
        from .chart_state_integration import install_chart_state_persistence

        # Check if already patched
        if hasattr(ChartFactory, '__chart_state_patched__'):
            logger.debug("ChartFactory already patched")
            return

        # Store original methods
        original_create_chart = ChartFactory.create_chart

        @staticmethod
        def enhanced_create_chart(chart_type, symbol="AAPL", enable_state_persistence=True, **kwargs):
            """Enhanced chart creation with optional state persistence."""
            # Create chart using original method
            chart_widget = original_create_chart(chart_type, symbol, **kwargs)

            # Install state persistence if enabled
            if enable_state_persistence:
                chart_widget = install_chart_state_persistence(chart_widget, chart_type="auto")
                logger.debug(f"Created {chart_type} chart for {symbol} with state persistence")
            else:
                logger.debug(f"Created {chart_type} chart for {symbol} without state persistence")

            return chart_widget

        # Patch method
        ChartFactory.create_chart = enhanced_create_chart

        # Mark as patched
        ChartFactory.__chart_state_patched__ = True

        logger.info("Successfully patched ChartFactory to enable state persistence by default")

    except ImportError:
        logger.warning("ChartFactory not available for patching")
    except Exception as e:
        logger.error(f"Failed to patch ChartFactory: {e}")


def apply_all_patches():
    """Apply all available patches to enable state persistence throughout the system."""
    logger.info("Applying chart state persistence patches...")

    patch_embedded_tradingview_chart()
    patch_chart_view()
    patch_chart_window()
    patch_chart_factory()

    logger.info("All chart state persistence patches applied")


def is_patched() -> bool:
    """Check if the system has been patched with state persistence."""
    try:
        from .chart_factory import ChartFactory
        return hasattr(ChartFactory, '__chart_state_patched__')
    except:
        return False


# Auto-patch when module is imported (can be disabled by setting environment variable)
import os
if os.getenv('ORDERPILOT_DISABLE_AUTO_PATCH') != '1':
    try:
        apply_all_patches()
    except Exception as e:
        logger.warning(f"Auto-patching failed: {e}. Use apply_all_patches() manually if needed.")