"""Indicator Mixin for EmbeddedTradingViewChart.

Contains indicator calculation, conversion, and update methods.
"""

import json
import logging

import pandas as pd
from PyQt6.QtGui import QAction

from src.core.indicators.engine import IndicatorConfig, IndicatorType
from .data_loading_mixin import get_local_timezone_offset_seconds

logger = logging.getLogger(__name__)


def _ts_to_local_unix(ts) -> int:
    """Convert timestamp to Unix seconds with local timezone offset for chart display."""
    return int(ts.timestamp()) + get_local_timezone_offset_seconds()


class IndicatorMixin:
    """Mixin providing indicator functionality for EmbeddedTradingViewChart."""

    def _get_indicator_configs(self):
        """Get indicator configuration dictionaries.

        Returns:
            Tuple of (overlay_configs, oscillator_configs)
        """
        overlay_configs = {
            "SMA": (IndicatorType.SMA, {'period': 20}, "SMA(20)", None, None),
            "EMA": (IndicatorType.EMA, {'period': 20}, "EMA(20)", None, None),
            "BB": (IndicatorType.BB, {'period': 20, 'std': 2}, "BB(20,2)", None, None),
        }

        oscillator_configs = {
            "RSI": (IndicatorType.RSI, {'period': 14}, "RSI(14)", 0, 100),
            "MACD": (IndicatorType.MACD, {'fast': 12, 'slow': 26, 'signal': 9}, "MACD(12,26,9)", None, None),
            "STOCH": (IndicatorType.STOCH, {'k_period': 14, 'd_period': 3}, "STOCH(14,3)", 0, 100),
            "ATR": (IndicatorType.ATR, {'period': 14}, "ATR(14)", 0, None),
            "ADX": (IndicatorType.ADX, {'period': 14}, "ADX(14)", 0, 100),
            "CCI": (IndicatorType.CCI, {'period': 20}, "CCI(20)", -100, 100),
            "MFI": (IndicatorType.MFI, {'period': 14}, "MFI(14)", 0, 100),
        }

        return overlay_configs, oscillator_configs

    def _convert_macd_data_to_chart_format(self, result):
        """Convert MACD indicator result to chart format.

        Args:
            result: IndicatorResult with DataFrame values

        Returns:
            Dict with 'macd', 'signal', 'histogram' keys
        """
        col_names = result.values.columns.tolist()
        logger.info(f"MACD columns: {col_names}")

        # Find columns (check histogram and signal first to avoid false matches)
        macd_col = signal_col = hist_col = None
        for col in col_names:
            col_lower = col.lower()
            if 'macdh' in col_lower or 'hist' in col_lower:
                hist_col = col
            elif 'macds' in col_lower or 'signal' in col_lower:
                signal_col = col
            elif 'macd' in col_lower:
                macd_col = col

        macd_series = result.values[macd_col] if macd_col else None
        signal_series = result.values[signal_col] if signal_col else None
        hist_series = result.values[hist_col] if hist_col else None

        logger.info(f"MACD column mapping: macd={macd_col}, signal={signal_col}, hist={hist_col}")

        # Convert each series to chart format
        macd_data = [
            {'time': _ts_to_local_unix(ts), 'value': float(val)}
            for ts, val in zip(self.data.index, macd_series.values if macd_series is not None else [])
            if not pd.isna(val)
        ]

        signal_data = [
            {'time': _ts_to_local_unix(ts), 'value': float(val)}
            for ts, val in zip(self.data.index, signal_series.values if signal_series is not None else [])
            if not pd.isna(val)
        ]

        hist_data = [
            {
                'time': _ts_to_local_unix(ts),
                'value': float(val),
                'color': '#26a69a' if float(val) >= 0 else '#ef5350'
            }
            for ts, val in zip(self.data.index, hist_series.values if hist_series is not None else [])
            if not pd.isna(val)
        ]

        logger.info(f"MACD data prepared: macd={len(macd_data)} points, signal={len(signal_data)} points, histogram={len(hist_data)} points")

        return {
            'macd': macd_data,
            'signal': signal_data,
            'histogram': hist_data
        }

    def _convert_multi_series_data_to_chart_format(self, result, ind_id):
        """Convert multi-series indicator result to chart format.

        Args:
            result: IndicatorResult with DataFrame values
            ind_id: Indicator ID string

        Returns:
            List of time/value dicts
        """
        col_names = result.values.columns.tolist()

        # Determine which column to use
        if 'k' in col_names:
            main_col = 'k'
        elif any('STOCHk' in col for col in col_names):
            main_col = [col for col in col_names if 'STOCHk' in col][0]
        elif 'middle' in col_names:  # Bollinger Bands
            main_col = 'middle'
        elif any('BBM' in col for col in col_names):  # pandas_ta BB middle
            main_col = [col for col in col_names if 'BBM' in col][0]
        else:
            main_col = col_names[0]  # Fallback to first column

        series_data = result.values[main_col]
        logger.info(f"Using column '{main_col}' from multi-series indicator {ind_id}")

        return [
            {'time': _ts_to_local_unix(ts), 'value': float(val)}
            for ts, val in zip(self.data.index, series_data.values)
            if not pd.isna(val)
        ]

    def _convert_single_series_data_to_chart_format(self, result):
        """Convert single-series indicator result to chart format.

        Args:
            result: IndicatorResult with Series values

        Returns:
            List of time/value dicts
        """
        return [
            {'time': _ts_to_local_unix(ts), 'value': float(val)}
            for ts, val in zip(self.data.index, result.values.values)
            if not pd.isna(val)
        ]

    def _create_overlay_indicator(self, display_name, color):
        """Create overlay indicator on price chart.

        Args:
            display_name: Display name for the indicator
            color: Color string for the indicator
        """
        self._execute_js(f"window.chartAPI.addIndicator('{display_name}', '{color}');")

    def _create_oscillator_panel(self, ind_id, display_name, color, min_val, max_val):
        """Create oscillator panel with indicator-specific reference lines.

        Args:
            ind_id: Indicator ID string
            display_name: Display name for the panel
            color: Color string for the indicator
            min_val: Minimum value for y-axis (or None)
            max_val: Maximum value for y-axis (or None)
        """
        panel_id = ind_id.lower()

        if ind_id == "MACD":
            # MACD: Create panel with histogram
            logger.info(f"  📊 Creating MACD panel with ID '{panel_id}'")
            self._execute_js(
                f"window.chartAPI.createPanel('{panel_id}', '{display_name}', 'histogram', '#26a69a', null, null);"
            )
            self._execute_js(f"window.chartAPI.addPanelSeries('{panel_id}', 'macd', 'line', '#2962FF', null);")
            self._execute_js(f"window.chartAPI.addPanelSeries('{panel_id}', 'signal', 'line', '#FF6D00', null);")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 0, '#888888', 'solid', '0');")
            logger.info(f"  ✓ MACD panel JavaScript calls completed")
        else:
            # Other oscillators
            js_min = 'null' if min_val is None else str(min_val)
            js_max = 'null' if max_val is None else str(max_val)
            self._execute_js(
                f"window.chartAPI.createPanel('{panel_id}', '{display_name}', 'line', '{color}', {js_min}, {js_max});"
            )
            self._add_oscillator_reference_lines(ind_id, panel_id)

        logger.info(f"Created panel for {ind_id}")

    def _add_oscillator_reference_lines(self, ind_id, panel_id):
        """Add indicator-specific reference lines to oscillator panel.

        Args:
            ind_id: Indicator ID string
            panel_id: Panel ID string
        """
        if ind_id == "RSI":
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 30, '#FF0000', 'dashed', 'Oversold');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 70, '#00FF00', 'dashed', 'Overbought');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 50, '#888888', 'dotted', 'Neutral');")
        elif ind_id == "STOCH":
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 20, '#FF0000', 'dashed', 'Oversold');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 80, '#00FF00', 'dashed', 'Overbought');")
        elif ind_id == "CCI":
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', -100, '#FF0000', 'dashed', '-100');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 100, '#00FF00', 'dashed', '+100');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 0, '#888888', 'dotted', '0');")

    def _update_overlay_data(self, display_name, ind_data):
        """Update overlay indicator data on price chart.

        Args:
            display_name: Display name of the indicator
            ind_data: List of time/value dicts
        """
        ind_json = json.dumps(ind_data)
        self._execute_js(f"window.chartAPI.setIndicatorData('{display_name}', {ind_json});")

    def _update_oscillator_data(self, ind_id, ind_data):
        """Update oscillator panel data.

        Args:
            ind_id: Indicator ID string
            ind_data: Either list of time/value dicts or dict with multiple series
        """
        panel_id = ind_id.lower()

        if isinstance(ind_data, dict) and ind_id == "MACD":
            # MACD: Set data for all 3 series
            macd_json = json.dumps(ind_data['macd'])
            signal_json = json.dumps(ind_data['signal'])
            hist_json = json.dumps(ind_data['histogram'])

            logger.info(f"  📈 Setting MACD data: histogram={len(ind_data['histogram'])} points, macd={len(ind_data['macd'])} points, signal={len(ind_data['signal'])} points")
            self._execute_js(f"window.chartAPI.setPanelData('{panel_id}', {hist_json});")
            self._execute_js(f"window.chartAPI.setPanelSeriesData('{panel_id}', 'macd', {macd_json});")
            self._execute_js(f"window.chartAPI.setPanelSeriesData('{panel_id}', 'signal', {signal_json});")
            logger.info(f"  ✓ MACD data set complete")
        else:
            # Regular oscillator - single series
            ind_json = json.dumps(ind_data)
            self._execute_js(f"window.chartAPI.setPanelData('{panel_id}', {ind_json});")

    def _remove_indicator_from_chart(self, ind_id, display_name, is_overlay):
        """Remove indicator from chart.

        Args:
            ind_id: Indicator ID string
            display_name: Display name of the indicator
            is_overlay: True if overlay indicator, False if oscillator
        """
        if is_overlay:
            self._execute_js(f"window.chartAPI.removeIndicator('{display_name}');")
        else:
            panel_id = ind_id.lower()
            self._execute_js(f"window.chartAPI.removePanel('{panel_id}');")
            logger.info(f"Removed panel for {ind_id}")

    def _update_indicators(self):
        """Update technical indicators on chart."""
        logger.info("🔧 _update_indicators called")

        if self.data is None:
            logger.warning("❌ Cannot update indicators: chart data not loaded yet")
            return

        if self._should_skip_full_update():
            return

        logger.info("✓ Chart ready, processing indicators...")

        try:
            self._updating_indicators = True
            overlay_configs, oscillator_configs = self._get_indicator_configs()

            # Process each indicator
            for ind_id, action in self.indicator_actions.items():
                self._process_indicator_action(
                    ind_id, action, overlay_configs, oscillator_configs
                )

        except Exception as e:
            logger.error(f"Error updating indicators: {e}", exc_info=True)
        finally:
            self._updating_indicators = False

    def _should_skip_full_update(self) -> bool:
        if not (self.page_loaded and self.chart_initialized):
            logger.warning(
                "❌ Cannot update indicators: chart not fully initialized yet (page_loaded=%s, chart_initialized=%s)",
                self.page_loaded,
                self.chart_initialized,
            )
            self._pending_indicator_update = True
            return True
        if self._updating_indicators:
            logger.warning("⏸️ Indicator update already in progress, skipping...")
            return True
        return False

    def _process_indicator_action(self, ind_id, action, overlay_configs, oscillator_configs) -> None:
        is_checked = action.isChecked()
        if is_checked:
            logger.info(f"  → Processing checked indicator: {ind_id}")
        indicator_data = action.data()
        color = indicator_data["color"]

        is_overlay = ind_id in overlay_configs
        is_oscillator = ind_id in oscillator_configs

        if not is_overlay and not is_oscillator:
            if is_checked and ind_id not in self.active_indicators:
                logger.warning(f"Indicator {ind_id} not yet implemented")
            return

        if is_overlay:
            ind_type, params, display_name, _, _ = overlay_configs[ind_id]
            min_val = max_val = None
        else:
            ind_type, params, display_name, min_val, max_val = oscillator_configs[ind_id]

        if is_checked:
            self._add_or_update_indicator(
                ind_id,
                ind_type,
                params,
                display_name,
                is_overlay,
                color,
                min_val,
                max_val,
            )
        elif ind_id in self.active_indicators:
            logger.info(f"  → Removing {ind_id} from chart (is_overlay={is_overlay})")
            self._remove_indicator_from_chart(ind_id, display_name, is_overlay)
            del self.active_indicators[ind_id]
            logger.info(
                f"  ✓ Removed {ind_id} from active indicators. Remaining: {list(self.active_indicators.keys())}"
            )

    def _add_or_update_indicator(
        self,
        ind_id,
        ind_type,
        params,
        display_name,
        is_overlay,
        color,
        min_val,
        max_val,
    ) -> None:
        try:
            logger.info(f"  → Calculating {ind_id} with params: {params}")
            config = IndicatorConfig(indicator_type=ind_type, params=params)
            result = self.indicator_engine.calculate(self.data, config)
            logger.info(
                f"  ✓ Calculated {ind_id}, values shape: "
                f"{result.values.shape if hasattr(result.values, 'shape') else len(result.values)}"
            )

            ind_data = self._convert_indicator_result(ind_id, result)
            logger.info(f"  ✓ Converted {ind_id} to chart format, {len(ind_data)} data points")

            should_create = ind_id not in self.active_indicators
            if should_create:
                logger.info(f"  → Creating new {'overlay' if is_overlay else 'panel'} for {ind_id}")
                if is_overlay:
                    self._create_overlay_indicator(display_name, color)
                else:
                    self._create_oscillator_panel(ind_id, display_name, color, min_val, max_val)
                self.active_indicators[ind_id] = True
                logger.info(f"  ✓ Created and activated {ind_id}")
            else:
                logger.info(f"  → {ind_id} already exists, updating data only")

            if is_overlay:
                self._update_overlay_data(display_name, ind_data)
            else:
                self._update_oscillator_data(ind_id, ind_data)
            logger.info(f"  ✓ Updated data for {ind_id}")

        except Exception as ind_error:
            logger.error(f"  ❌ Error processing indicator {ind_id}: {ind_error}", exc_info=True)

    def _convert_indicator_result(self, ind_id, result):
        if isinstance(result.values, pd.DataFrame) and ind_id == "MACD":
            return self._convert_macd_data_to_chart_format(result)
        if isinstance(result.values, pd.DataFrame):
            return self._convert_multi_series_data_to_chart_format(result, ind_id)
        return self._convert_single_series_data_to_chart_format(result)

    def _update_indicators_realtime(self, candle: dict):
        """Update indicators in real-time with new candle data.

        Args:
            candle: New candle dict with time, open, high, low, close
        """
        if self._should_skip_realtime_update():
            return

        try:
            new_row = self._build_realtime_row(candle)
            self._update_realtime_row(new_row)

            # Get indicator configs
            overlay_configs, oscillator_configs = self._get_indicator_configs()

            # Update each active indicator
            for ind_id in self.active_indicators:
                # Determine if overlay or oscillator
                is_overlay = ind_id in overlay_configs
                is_oscillator = ind_id in oscillator_configs

                if not is_overlay and not is_oscillator:
                    continue

                # Get configuration
                if is_overlay:
                    ind_type, params, display_name, _, _ = overlay_configs[ind_id]
                else:
                    ind_type, params, display_name, min_val, max_val = oscillator_configs[ind_id]

                self._update_indicator_realtime(
                    ind_id,
                    is_overlay,
                    ind_type,
                    params,
                    display_name,
                )

        except Exception as e:
            logger.error(f"Error updating indicators in real-time: {e}", exc_info=True)

    def _should_skip_realtime_update(self) -> bool:
        if self.data is None or not self.active_indicators:
            return True
        if not (self.page_loaded and self.chart_initialized):
            return True
        return self._updating_indicators

    def _build_realtime_row(self, candle: dict) -> pd.DataFrame:
        local_offset = get_local_timezone_offset_seconds()
        utc_timestamp = candle['time'] - local_offset
        new_row = pd.DataFrame([{
            'time': pd.Timestamp.fromtimestamp(utc_timestamp, tz='UTC'),
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close']
        }])
        new_row.set_index('time', inplace=True)
        return new_row

    def _update_realtime_row(self, new_row: pd.DataFrame) -> None:
        if new_row.index[0] in self.data.index:
            self.data.loc[new_row.index[0]] = new_row.iloc[0]
        else:
            self.data = pd.concat([self.data, new_row])

    def _update_indicator_realtime(
        self,
        ind_id: str,
        is_overlay: bool,
        ind_type: IndicatorType,
        params: dict,
        display_name: str,
    ) -> None:
        config = IndicatorConfig(indicator_type=ind_type, params=params)
        result = self.indicator_engine.calculate(self.data, config)
        if isinstance(result.values, pd.DataFrame):
            if ind_id == "MACD":
                self._update_macd_realtime(ind_id, result)
            else:
                self._update_multi_series_realtime(ind_id, is_overlay, display_name, result)
        else:
            self._update_single_series_realtime(ind_id, is_overlay, display_name, result)

    def _update_macd_realtime(self, ind_id: str, result) -> None:
        last_idx = result.values.index[-1]
        time_unix = _ts_to_local_unix(last_idx)
        panel_id = ind_id.lower()
        col_names = result.values.columns.tolist()
        macd_col = signal_col = hist_col = None
        for col in col_names:
            col_lower = col.lower()
            if 'macdh' in col_lower or 'hist' in col_lower:
                hist_col = col
            elif 'macds' in col_lower or 'signal' in col_lower:
                signal_col = col
            elif 'macd' in col_lower:
                macd_col = col

        if hist_col:
            hist_val = float(result.values.loc[last_idx, hist_col])
            hist_point = json.dumps({
                'time': time_unix,
                'value': hist_val,
                'color': '#26a69a' if hist_val >= 0 else '#ef5350'
            })
            self._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {hist_point});")

        if macd_col:
            macd_val = float(result.values.loc[last_idx, macd_col])
            macd_point = json.dumps({'time': time_unix, 'value': macd_val})
            self._execute_js(
                f"window.chartAPI.updatePanelSeriesData('{panel_id}', 'macd', {macd_point});"
            )

        if signal_col:
            signal_val = float(result.values.loc[last_idx, signal_col])
            signal_point = json.dumps({'time': time_unix, 'value': signal_val})
            self._execute_js(
                f"window.chartAPI.updatePanelSeriesData('{panel_id}', 'signal', {signal_point});"
            )

    def _update_multi_series_realtime(self, ind_id: str, is_overlay: bool, display_name: str, result) -> None:
        last_idx = result.values.index[-1]
        time_unix = _ts_to_local_unix(last_idx)
        main_val = float(result.values.iloc[-1, 0])
        point = json.dumps({'time': time_unix, 'value': main_val})

        if is_overlay:
            self._execute_js(f"window.chartAPI.updateIndicator('{display_name}', {point});")
        else:
            panel_id = ind_id.lower()
            self._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {point});")

    def _update_single_series_realtime(self, ind_id: str, is_overlay: bool, display_name: str, result) -> None:
        last_idx = result.values.index[-1]
        value = float(result.values.iloc[-1])
        time_unix = _ts_to_local_unix(last_idx)
        point = json.dumps({'time': time_unix, 'value': value})

        if is_overlay:
            self._execute_js(f"window.chartAPI.updateIndicator('{display_name}', {point});")
        else:
            panel_id = ind_id.lower()
            self._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {point});")

    def _update_indicators_button_badge(self):
        """Update indicators button to show count of active indicators."""
        active_count = sum(1 for action in self.indicator_actions.values() if action.isChecked())

        if active_count > 0:
            self.indicators_button.setText(f"📊 Indikatoren ({active_count})")
            self.indicators_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B00;
                    color: white;
                    font-weight: bold;
                    border: 2px solid #FF8C00;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #FF8C00;
                }
                QPushButton::menu-indicator {
                    subcontrol-origin: padding;
                    subcontrol-position: right center;
                }
            """)
        else:
            self.indicators_button.setText("📊 Indikatoren")
            self.indicators_button.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #aaa;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    color: #fff;
                }
                QPushButton::menu-indicator {
                    subcontrol-origin: padding;
                    subcontrol-position: right center;
                }
            """)

    def _on_indicator_toggled(self, action: QAction):
        """Handle indicator toggle from dropdown menu.

        Args:
            action: The QAction that was toggled
        """
        indicator_data = action.data()
        indicator_id = indicator_data["id"]
        is_checked = action.isChecked()

        logger.info(f"🔄 Indicator {indicator_id} {'enabled' if is_checked else 'disabled'} (currently active: {list(self.active_indicators.keys())})")

        # Update indicators display
        self._update_indicators()

        # Update button style to show how many indicators are active
        self._update_indicators_button_badge()

        logger.info(f"✓ Toggle complete. Active indicators: {list(self.active_indicators.keys())}")
