"""Data Loading Series - Chart series building.

Refactored from 498 LOC monolith using composition pattern.

Module 3/6 of data_loading_mixin.py split.

Contains:
- prepare_chart_data(): Clean and store data
- build_chart_series(): Convert DataFrame to candles + volume
- update_chart_series(): Send data to JavaScript chart
- finalize_chart_load(): Update UI after load
"""

from __future__ import annotations

import json
import logging
import pandas as pd  # Runtime import - used in build_chart_series()
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)


class DataLoadingSeries:
    """Helper für DataLoadingMixin chart series building."""

    def __init__(self, parent):
        """
        Args:
            parent: DataLoadingMixin Instanz
        """
        self.parent = parent

    def prepare_chart_data(self, data: "pd.DataFrame") -> "pd.DataFrame":
        """Clean bad ticks and store data."""
        data = self.parent._cleaning.clean_bad_ticks(data)
        self.parent.data = data
        if len(data) > 0 and 'close' in data.columns:
            self.parent._last_price = float(data['close'].iloc[-1])
            logger.debug(f"Set _last_price from data: {self.parent._last_price}")
        return data

    def build_chart_series(self, data: "pd.DataFrame") -> tuple[list[dict], list[dict]]:
        """Convert DataFrame to candle + volume series.

        Returns:
            Tuple of (candle_data, volume_data)
        """
        from .data_loading_utils import get_local_timezone_offset_seconds

        candle_data = []
        volume_data = []
        local_offset = get_local_timezone_offset_seconds()
        logger.debug(
            f"Local timezone offset: {local_offset} seconds ({local_offset // 3600}h)"
        )

        for timestamp, row in data.iterrows():
            # Skip rows with NaN values
            if any(pd.isna(x) for x in [row['open'], row['high'], row['low'], row['close']]):
                continue

            unix_time = int(timestamp.timestamp()) + local_offset
            candle_data.append({
                'time': unix_time,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
            })
            volume_data.append({
                'time': unix_time,
                'value': float(row.get('volume', 0)),
                'color': '#26a69a' if row['close'] >= row['open'] else '#ef5350',
            })

        return candle_data, volume_data

    def update_chart_series(self, candle_data: list[dict]) -> None:
        """Send candle data to JavaScript chart."""
        skip_fit = getattr(self.parent, '_skip_fit_content', False)

        if skip_fit:
            logger.info("📌 Setting suppressFitContent=true in JavaScript")
            self.parent._execute_js("window.chartAPI.setSuppressFitContent(true);")

        candle_json = json.dumps(candle_data)
        if skip_fit:
            self.parent._execute_js(f"window.chartAPI.setData({candle_json}, true);")
            logger.info("Loaded data with skipFit=true - state restoration pending")
        else:
            self.parent._execute_js(f"window.chartAPI.setData({candle_json});")

        if not skip_fit:
            self.parent._execute_js("window.chartAPI.fitContent();")

    def finalize_chart_load(self, data: "pd.DataFrame", candle_data: list[dict]) -> None:
        """Update UI and emit signals after chart load."""
        self.parent._update_indicators()

        first_date = data.index[0].strftime('%Y-%m-%d %H:%M')
        last_date = data.index[-1].strftime('%Y-%m-%d %H:%M')

        self.parent.info_label.setText(
            f"Loaded {len(candle_data)} bars | "
            f"From: {first_date} | To: {last_date}"
        )
        self.parent.market_status_label.setText("✓ Chart Loaded")
        self.parent.market_status_label.setStyleSheet(
            "color: #00FF00; font-weight: bold; padding: 5px;"
        )

        if not self.parent.update_timer.isActive():
            self.parent.update_timer.start()

        logger.info(f"Loaded {len(candle_data)} bars into embedded chart")
        self.parent.data_loaded.emit()
