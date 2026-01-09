"""Indicator Chart Ops - Chart creation, update, and removal.

Refactored from 676 LOC monolith using composition pattern.

Module 4/7 of indicator_mixin.py split.

Contains:
- create_overlay_indicator(): Create overlay on price chart
- create_oscillator_panel(): Create oscillator panel
- add_oscillator_reference_lines(): Add reference lines (RSI, STOCH, CCI)
- update_overlay_data(): Update overlay data
- update_oscillator_data(): Update oscillator data (MACD special case)
- remove_indicator_from_chart(): Remove indicator/panel
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class IndicatorChartOps:
    """Helper für IndicatorMixin chart operations."""

    def __init__(self, parent):
        """
        Args:
            parent: IndicatorMixin Instanz
        """
        self.parent = parent

    def create_overlay_indicator(self, display_name: str, color: str):
        """Create overlay indicator on price chart.

        Args:
            display_name: Display name for the indicator
            color: Color string for the indicator
        """
        self.parent._execute_js(f"window.chartAPI.addIndicator('{display_name}', '{color}');")

    def create_oscillator_panel(
        self, panel_id: str, display_name: str, color: str, min_val: float | None, max_val: float | None
    ):
        """Create oscillator panel with indicator-specific reference lines.

        Args:
            panel_id: Unique panel ID (instance-based)
            display_name: Display name for the panel
            color: Color string for the indicator
            min_val: Minimum value for y-axis (or None)
            max_val: Maximum value for y-axis (or None)
        """
        if panel_id.upper().startswith("MACD"):
            # MACD: Create panel with histogram
            logger.info(f"  📊 Creating MACD panel with ID '{panel_id}'")
            self.parent._execute_js(
                f"window.chartAPI.createPanel('{panel_id}', '{display_name}', 'histogram', '#26a69a', null, null);"
            )
            self.parent._execute_js(f"window.chartAPI.addPanelSeries('{panel_id}', 'macd', 'line', '#2962FF', null);")
            self.parent._execute_js(f"window.chartAPI.addPanelSeries('{panel_id}', 'signal', 'line', '#FF6D00', null);")
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 0, '#888888', 'solid', '0');")
            logger.info(f"  ✓ MACD panel JavaScript calls completed")
        else:
            # Other oscillators
            js_min = 'null' if min_val is None else str(min_val)
            js_max = 'null' if max_val is None else str(max_val)
            self.parent._execute_js(
                f"window.chartAPI.createPanel('{panel_id}', '{display_name}', 'line', '{color}', {js_min}, {js_max});"
            )
            self.add_oscillator_reference_lines(display_name, panel_id)

        logger.info(f"Created panel for {panel_id}")

    def add_oscillator_reference_lines(self, ind_display_name: str, panel_id: str):
        """Add indicator-specific reference lines to oscillator panel.

        Args:
            ind_display_name: Display name (contains type)
            panel_id: Panel ID string
        """
        base = ind_display_name.split("(")[0]
        if base == "RSI":
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 30, '#FF0000', 'dashed', 'Oversold');")
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 70, '#00FF00', 'dashed', 'Overbought');")
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 50, '#888888', 'dotted', 'Neutral');")
        elif base == "STOCH":
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 20, '#FF0000', 'dashed', 'Oversold');")
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 80, '#00FF00', 'dashed', 'Overbought');")
        elif base == "CCI":
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', -100, '#FF0000', 'dashed', '-100');")
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 100, '#00FF00', 'dashed', '+100');")
            self.parent._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 0, '#888888', 'dotted', '0');")

    def update_overlay_data(self, display_name: str, ind_data: list):
        """Update overlay indicator data on price chart.

        Args:
            display_name: Display name of the indicator
            ind_data: List of time/value dicts
        """
        ind_json = json.dumps(ind_data)
        self.parent._execute_js(f"window.chartAPI.setIndicatorData('{display_name}', {ind_json});")

    def update_oscillator_data(self, panel_id: str, ind_data: list | dict):
        """Update oscillator panel data.

        Args:
            panel_id: Panel identifier (instance-based)
            ind_data: Either list of time/value dicts or dict with multiple series
        """
        panel_id = panel_id.lower()

        if isinstance(ind_data, dict) and panel_id.startswith("macd"):
            # MACD: Set data for all 3 series
            macd_json = json.dumps(ind_data['macd'])
            signal_json = json.dumps(ind_data['signal'])
            hist_json = json.dumps(ind_data['histogram'])

            logger.info(f"  📈 Setting MACD data: histogram={len(ind_data['histogram'])} points, macd={len(ind_data['macd'])} points, signal={len(ind_data['signal'])} points")
            self.parent._execute_js(f"window.chartAPI.setPanelData('{panel_id}', {hist_json});")
            self.parent._execute_js(f"window.chartAPI.setPanelSeriesData('{panel_id}', 'macd', {macd_json});")
            self.parent._execute_js(f"window.chartAPI.setPanelSeriesData('{panel_id}', 'signal', {signal_json});")
            logger.info(f"  ✓ MACD data set complete")
        else:
            # Regular oscillator - single series
            ind_json = json.dumps(ind_data)
            self.parent._execute_js(f"window.chartAPI.setPanelData('{panel_id}', {ind_json});")

    def remove_indicator_from_chart(self, panel_or_id: str, display_name: str, is_overlay: bool):
        """Remove indicator from chart.

        Args:
            panel_or_id: Panel/indicator identifier (instance-based)
            display_name: Display name of the indicator
            is_overlay: True if overlay indicator, False if oscillator
        """
        if is_overlay:
            self.parent._execute_js(f"window.chartAPI.removeIndicator('{display_name}');")
        else:
            panel_id = panel_or_id.lower()
            self.parent._execute_js(f"window.chartAPI.removePanel('{panel_id}');")
            logger.info(f"Removed panel {panel_id}")
