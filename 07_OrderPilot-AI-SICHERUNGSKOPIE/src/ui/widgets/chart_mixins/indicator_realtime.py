"""Indicator Realtime - Real-time indicator updates.

Refactored from 676 LOC monolith using composition pattern.

Module 6/7 of indicator_mixin.py split.

Contains:
- update_indicators_realtime(): Main realtime method
- should_skip_realtime_update(): Skip check
- build_realtime_row(): Build new row from candle
- update_realtime_row(): Update data with new row
- update_indicator_realtime(): Update single indicator
- update_macd_realtime(): MACD realtime update
- update_multi_series_realtime(): Multi-series realtime update
- update_single_series_realtime(): Single-series realtime update
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .indicator_utils import IndicatorInstance

from src.core.indicators.engine import IndicatorConfig
from .data_loading_utils import get_local_timezone_offset_seconds
from .indicator_utils import _ts_to_local_unix

logger = logging.getLogger(__name__)


class IndicatorRealtime:
    """Helper für IndicatorMixin real-time updates."""

    def __init__(self, parent):
        """
        Args:
            parent: IndicatorMixin Instanz
        """
        self.parent = parent

    def update_indicators_realtime(self, candle: dict):
        """Update indicators in real-time with new candle data.

        Args:
            candle: New candle dict with time, open, high, low, close
        """
        if self.should_skip_realtime_update():
            return

        try:
            new_row = self.build_realtime_row(candle)
            self.update_realtime_row(new_row)

            # Update all active indicators
            for inst in self.parent.active_indicators.values():
                self.update_indicator_realtime(inst)

        except Exception as e:
            logger.error(f"Error updating indicators in real-time: {e}", exc_info=True)

    def should_skip_realtime_update(self) -> bool:
        """Check if realtime update should be skipped.

        Returns:
            True if update should be skipped
        """
        if self.parent.data is None or not self.parent.active_indicators:
            return True
        if not (self.parent.page_loaded and self.parent.chart_initialized):
            return True
        return self.parent._updating_indicators

    def build_realtime_row(self, candle: dict) -> pd.DataFrame:
        """Build new DataFrame row from candle data.

        Args:
            candle: Candle dict with time, open, high, low, close

        Returns:
            DataFrame with single row
        """
        # FIXED: Removed local_offset - not needed, timestamps stay in UTC
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

    def update_realtime_row(self, new_row: pd.DataFrame) -> None:
        """Update data with new row (update or append).

        Args:
            new_row: DataFrame with single row to add/update
        """
        if new_row.index[0] in self.parent.data.index:
            self.parent.data.loc[new_row.index[0]] = new_row.iloc[0]
        else:
            self.parent.data = pd.concat([self.parent.data, new_row])

    def update_indicator_realtime(self, inst: "IndicatorInstance") -> None:
        """Update single indicator in realtime.

        Args:
            inst: IndicatorInstance to update
        """
        config = IndicatorConfig(indicator_type=inst.ind_type, params=inst.params)
        result = self.parent.indicator_engine.calculate(self.parent.data, config)

        if isinstance(result.values, pd.DataFrame):
            if inst.ind_id == "MACD":
                self.update_macd_realtime(inst.instance_id, result)
            else:
                self.update_multi_series_realtime(inst.instance_id, inst.is_overlay, inst.display_name, result)
        else:
            self.update_single_series_realtime(inst.instance_id, inst.is_overlay, inst.display_name, result)

    def update_macd_realtime(self, instance_id: str, result) -> None:
        """Update MACD indicator in realtime (all 3 series).

        Args:
            instance_id: Instance ID
            result: IndicatorResult with DataFrame values
        """
        last_idx = result.values.index[-1]
        time_unix = _ts_to_local_unix(last_idx)
        panel_id = instance_id.lower()

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
            self.parent._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {hist_point});")

        if macd_col:
            macd_val = float(result.values.loc[last_idx, macd_col])
            macd_point = json.dumps({'time': time_unix, 'value': macd_val})
            self.parent._execute_js(
                f"window.chartAPI.updatePanelSeriesData('{panel_id}', 'macd', {macd_point});"
            )

        if signal_col:
            signal_val = float(result.values.loc[last_idx, signal_col])
            signal_point = json.dumps({'time': time_unix, 'value': signal_val})
            self.parent._execute_js(
                f"window.chartAPI.updatePanelSeriesData('{panel_id}', 'signal', {signal_point});"
            )

    def update_multi_series_realtime(
        self, instance_id: str, is_overlay: bool, display_name: str, result
    ) -> None:
        """Update multi-series indicator in realtime.

        Args:
            instance_id: Instance ID
            is_overlay: True if overlay, False if oscillator
            display_name: Display name
            result: IndicatorResult with DataFrame values
        """
        last_idx = result.values.index[-1]
        time_unix = _ts_to_local_unix(last_idx)
        main_val = float(result.values.iloc[-1, 0])
        point = json.dumps({'time': time_unix, 'value': main_val})

        if is_overlay:
            self.parent._execute_js(f"window.chartAPI.updateIndicator('{display_name}', {point});")
        else:
            panel_id = instance_id.lower()
            self.parent._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {point});")

    def update_single_series_realtime(
        self, instance_id: str, is_overlay: bool, display_name: str, result
    ) -> None:
        """Update single-series indicator in realtime.

        Args:
            instance_id: Instance ID
            is_overlay: True if overlay, False if oscillator
            display_name: Display name
            result: IndicatorResult with Series values
        """
        last_idx = result.values.index[-1]
        value = float(result.values.iloc[-1])
        time_unix = _ts_to_local_unix(last_idx)
        point = json.dumps({'time': time_unix, 'value': value})

        if is_overlay:
            self.parent._execute_js(f"window.chartAPI.updateIndicator('{display_name}', {point});")
        else:
            panel_id = instance_id.lower()
            self.parent._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {point});")
