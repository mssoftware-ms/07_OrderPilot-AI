"""State Mixin for ChartWindow.

Contains state save/restore functionality.
"""

import json
import logging

from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)


class StateMixin:
    """Mixin providing state save/restore for ChartWindow."""

    def _load_window_state(self):
        """Load window position and size from settings."""
        # IMPORTANT: Use sanitized key to match how state is saved
        settings_key = self._get_settings_key()

        geometry = self.settings.value(f"{settings_key}/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1200, 800)
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

        window_state = self.settings.value(f"{settings_key}/windowState")
        if window_state:
            self.restoreState(window_state)

        # Check if we have saved chart state - if so, skip fitContent() on data load
        chart_state_json = self.settings.value(f"{settings_key}/chartState")
        visible_range_json = self.settings.value(f"{settings_key}/visibleRange")

        logger.info(f"🔍 Checking saved state for {self.symbol} (key: {settings_key})")
        logger.info(f"   chartState exists: {bool(chart_state_json)}")
        logger.info(f"   visibleRange exists: {bool(visible_range_json)}")
        if visible_range_json:
            logger.info(f"   visibleRange value: {visible_range_json}")

        if chart_state_json or visible_range_json:
            logger.info(f"✅ Found saved chart state for {self.symbol} - setting _skip_fit_content=True")
            self.chart_widget._skip_fit_content = True
        else:
            logger.info(f"ℹ️ No saved chart state for {self.symbol} - will use fitContent()")

        if hasattr(self.chart_widget, 'timeframe_combo'):
            timeframe = self.settings.value(f"{settings_key}/timeframe")
            if timeframe:
                self.chart_widget.current_timeframe = timeframe
                index = self.chart_widget.timeframe_combo.findData(timeframe)
                if index >= 0:
                    self.chart_widget.timeframe_combo.setCurrentIndex(index)

        if hasattr(self.chart_widget, 'period_combo'):
            period = self.settings.value(f"{settings_key}/period")
            if period:
                self.chart_widget.current_period = period
                index = self.chart_widget.period_combo.findData(period)
                if index >= 0:
                    self.chart_widget.period_combo.setCurrentIndex(index)

        if hasattr(self.chart_widget, 'indicator_actions'):
            active_indicators = self.settings.value(f"{settings_key}/indicators")
            if active_indicators and isinstance(active_indicators, list):
                logger.info(f"Pre-setting {len(active_indicators)} indicators as checked")
                for indicator_id in active_indicators:
                    if indicator_id in self.chart_widget.indicator_actions:
                        action = self.chart_widget.indicator_actions[indicator_id]
                        action.setChecked(True)

        indicator_params = self.settings.value(f"{settings_key}/indicator_params")
        if indicator_params and isinstance(indicator_params, dict):
            if hasattr(self.chart_widget, 'active_indicator_params'):
                self.chart_widget.active_indicator_params = indicator_params

        logger.debug(f"Loaded window state for {self.symbol}")

    def _get_settings_key(self):
        """Get sanitized settings key for this symbol."""
        safe_symbol = self.symbol.replace("/", "_")
        return f"ChartWindow/{safe_symbol}"

    def _save_window_state(self):
        """Save window position, size, and chart settings."""
        settings_key = self._get_settings_key()

        self.settings.setValue(f"{settings_key}/geometry", self.saveGeometry())
        self.settings.setValue(f"{settings_key}/windowState", self.saveState())

        if hasattr(self.chart_widget, 'current_timeframe'):
            self.settings.setValue(f"{settings_key}/timeframe", self.chart_widget.current_timeframe)
        if hasattr(self.chart_widget, 'current_period'):
            self.settings.setValue(f"{settings_key}/period", self.chart_widget.current_period)

        if hasattr(self.chart_widget, 'indicator_actions'):
            active_indicators = [
                ind_id for ind_id, action in self.chart_widget.indicator_actions.items()
                if action.isChecked()
            ]
            self.settings.setValue(f"{settings_key}/indicators", active_indicators)

        if hasattr(self.chart_widget, 'active_indicator_params'):
            self.settings.setValue(f"{settings_key}/indicator_params",
                                 self.chart_widget.active_indicator_params)

        logger.debug(f"Saved window state for {self.symbol}")

    def _restore_chart_state(self):
        """Restore pane sizes and zoom level from settings.

        IMPORTANT: This is called when data_loaded signal is emitted.
        We use a short delay (100ms) to let the chart render the data first,
        then immediately restore the saved state.
        """
        settings_key = self._get_settings_key()

        def _do_restore():
            logger.info(f"Starting chart state restoration for {self.symbol}")

            # Mark that we're restoring state
            self.chart_widget._restoring_state = True

            try:
                complete_state_json = self.settings.value(f"{settings_key}/chartState")
                if complete_state_json:
                    if isinstance(complete_state_json, str):
                        complete_state = json.loads(complete_state_json)
                    else:
                        complete_state = complete_state_json

                    if complete_state and isinstance(complete_state, dict) and complete_state.get('version'):
                        logger.info(f"Restoring complete chart state for {self.symbol}")
                        self.chart_widget.set_chart_state(complete_state)
                        logger.info("Complete chart state restoration initiated")
                        self._finalize_restoration()
                        return
            except Exception as e:
                logger.warning(f"Error restoring complete chart state: {e}")

            # Fallback: Individual component restoration
            restored_something = False

            try:
                range_json = self.settings.value(f"{settings_key}/visibleRange")
                if range_json:
                    if isinstance(range_json, str):
                        visible_range = json.loads(range_json)
                    else:
                        visible_range = range_json

                    if visible_range and isinstance(visible_range, dict):
                        logger.info(f"Restoring visible range for {self.symbol}: {visible_range}")
                        self.chart_widget.set_visible_range(visible_range)
                        restored_something = True
            except Exception as e:
                logger.error(f"Error restoring visible range: {e}", exc_info=True)

            try:
                layout_json = self.settings.value(f"{settings_key}/paneLayout")
                if layout_json:
                    if isinstance(layout_json, str):
                        layout = json.loads(layout_json)
                    else:
                        layout = layout_json

                    if layout and isinstance(layout, dict):
                        logger.info(f"Restoring pane layout for {self.symbol}")
                        self.chart_widget.set_pane_layout(layout)
                        restored_something = True
            except Exception as e:
                logger.error(f"Error restoring pane layout: {e}", exc_info=True)

            self._finalize_restoration()

        # Delay of 300ms gives chart time to render data before restoring range
        # Too short and setVisibleLogicalRange might fail on empty/unrendered chart
        QTimer.singleShot(300, _do_restore)

    def _finalize_restoration(self):
        """Clean up after state restoration."""
        # Reset flags after a short delay to ensure all JS has executed
        def _reset_flags():
            self.chart_widget._restoring_state = False
            self.chart_widget._skip_fit_content = False

            # Clear the JavaScript suppress flag
            logger.info("📌 Clearing suppressFitContent in JavaScript")
            self.chart_widget._execute_js("window.chartAPI.setSuppressFitContent(false);")

            logger.info(f"✅ Chart state restoration complete for {self.symbol}")

        QTimer.singleShot(300, _reset_flags)

    def _restore_indicators_after_data_load(self):
        """Restore indicators after data has been loaded.

        NOTE: Visible range is restored by _restore_chart_state(), not here.
        This function only handles indicators to avoid duplicate restoration.
        """
        try:
            settings_key = self._get_settings_key()

            logger.info(f"Indicator restoration after data load for {self.symbol}")

            if not hasattr(self.chart_widget, 'page_loaded') or not self.chart_widget.page_loaded:
                QTimer.singleShot(1500, self._restore_indicators_after_data_load)
                return

            if not hasattr(self.chart_widget, 'chart_initialized') or not self.chart_widget.chart_initialized:
                QTimer.singleShot(1500, self._restore_indicators_after_data_load)
                return

            # Only restore indicators - zoom is handled by _restore_chart_state
            self._restore_indicators_now(settings_key)

        except Exception as e:
            logger.error(f"Failed to restore complete chart state after data load: {e}")

    def _restore_zoom_state_now(self, settings_key):
        """Restore zoom/visible range state immediately (no delay)."""
        try:
            range_json = self.settings.value(f"{settings_key}/visibleRange")
            if range_json:
                if isinstance(range_json, str):
                    visible_range = json.loads(range_json)
                else:
                    visible_range = range_json

                if visible_range and isinstance(visible_range, dict):
                    logger.info(f"Restoring zoom/visible range immediately: {visible_range}")
                    # Apply immediately - no delay needed since data is already loaded
                    self.chart_widget.set_visible_range(visible_range)
                    logger.info("Zoom state restoration applied")

        except Exception as e:
            logger.error(f"Failed to restore zoom state: {e}")

    def _restore_pane_layout_now(self, settings_key):
        """Restore pane layout/row heights with minimal delay."""
        try:
            layout_json = self.settings.value(f"{settings_key}/paneLayout")
            if layout_json:
                if isinstance(layout_json, str):
                    layout = json.loads(layout_json)
                else:
                    layout = layout_json

                if layout and isinstance(layout, dict):
                    logger.info(f"Restoring pane layout/row heights: {layout}")

                    def apply_layout():
                        try:
                            self.chart_widget.set_pane_layout(layout)
                            logger.info("Pane layout restoration applied")
                        except Exception as e:
                            logger.error(f"Failed to apply pane layout: {e}")

                    # Reduced delay: 200ms is enough for indicators to be created
                    QTimer.singleShot(200, apply_layout)

        except Exception as e:
            logger.error(f"Failed to restore pane layout: {e}")

    def _restore_indicators_now(self, settings_key):
        """Restore indicators."""
        try:
            active_indicators = self.settings.value(f"{settings_key}/indicators")
            if not active_indicators or not isinstance(active_indicators, list):
                logger.debug(f"No saved indicators found for {self.symbol}")
                return

            logger.info(f"Found {len(active_indicators)} saved indicators to restore")

            if not hasattr(self.chart_widget, 'indicator_actions'):
                logger.warning("Chart widget has no indicator_actions")
                return

            restored_count = 0

            for indicator_id in active_indicators:
                if indicator_id in self.chart_widget.indicator_actions:
                    action = self.chart_widget.indicator_actions[indicator_id]

                    if not action.isChecked():
                        logger.info(f"Setting indicator {indicator_id} as checked")
                        action.setChecked(True)

                    param_key = f"{settings_key}/indicator_params/{indicator_id}"
                    saved_params = self.settings.value(param_key)
                    if saved_params and hasattr(self.chart_widget, 'active_indicator_params'):
                        try:
                            if isinstance(saved_params, str):
                                saved_params = json.loads(saved_params)
                            self.chart_widget.active_indicator_params[indicator_id] = saved_params
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Could not parse saved parameters for {indicator_id}: {e}")

                    if hasattr(self.chart_widget, 'active_indicators'):
                        self.chart_widget.active_indicators[indicator_id] = True

                    restored_count += 1

            if restored_count > 0:
                logger.info(f"Restored {restored_count} indicators, forcing chart update")

                # Update indicators immediately
                QTimer.singleShot(50, self.chart_widget._update_indicators)

                def restore_pane_layout_after_indicators():
                    logger.info("Now restoring pane layout after indicators are created")
                    self._restore_pane_layout_now(self._get_settings_key())

                # Reduced delay: 300ms should be enough for indicators to be created
                QTimer.singleShot(300, restore_pane_layout_after_indicators)

            logger.info(f"Completed indicator restoration for {self.symbol}")

        except Exception as e:
            logger.error(f"Failed to restore indicators: {e}")

    def _sanitize_symbol(self, symbol: str) -> str:
        """Sanitize symbol for use in settings keys."""
        return symbol.replace("/", "_").replace(":", "_").replace("*", "_")

    def load_backtest_result(self, result):
        """Load and display backtest result in chart window."""
        from src.core.models.backtest_models import BacktestResult

        if not isinstance(result, BacktestResult):
            logger.error(f"Invalid backtest result type: {type(result)}")
            return

        logger.info(f"Loading backtest result for {result.symbol} into chart window")

        self.setWindowTitle(f"Backtest Results - {result.symbol} | {result.strategy_name}")

        if hasattr(self.chart_widget, 'load_backtest_result'):
            self.chart_widget.load_backtest_result(result)
        elif hasattr(self.chart_widget, 'bridge'):
            if hasattr(self.chart_widget.bridge, 'loadBacktestResultObject'):
                self.chart_widget.bridge.loadBacktestResultObject(result)
            else:
                logger.warning("ChartBridge doesn't have loadBacktestResultObject method")
        else:
            logger.warning(f"Chart widget doesn't support backtest result display")

        self.show()
        self.raise_()
        self.activateWindow()
