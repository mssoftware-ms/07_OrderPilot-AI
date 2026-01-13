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


def _get_volume_colors() -> dict[str, str]:
    """Get volume colors from QSettings (Issue #40).

    Returns:
        Dictionary with 'bullish' and 'bearish' volume colors.
    """
    try:
        from PyQt6.QtCore import QSettings
        settings = QSettings("OrderPilot", "TradingApp")

        # Use same colors as candles
        bullish = settings.value("chart_bullish_color", "#26a69a")
        bearish = settings.value("chart_bearish_color", "#ef5350")

        return {"bullish": bullish, "bearish": bearish}
    except Exception as exc:
        logger.warning(f"Could not load volume colors from settings: {exc}")
        return {"bullish": "#26a69a", "bearish": "#ef5350"}


class DataLoadingSeries:
    """Helper für DataLoadingMixin chart series building."""

    def __init__(self, parent):
        """
        Args:
            parent: DataLoadingMixin Instanz
        """
        self.parent = parent

    def prepare_chart_data(self, data: "pd.DataFrame") -> "pd.DataFrame":
        """Clean bad ticks and store data.

        New: Forward-fill gaps for 1-second candles if requested by user.
        """
        data = self.parent._cleaning.clean_bad_ticks(data)

        # Forward-fill gaps for 1-second candles (user request 2026-01-13)
        if hasattr(self.parent, 'current_timeframe') and self.parent.current_timeframe == "1S":
            data = self._fill_one_second_gaps(data)

        self.parent.data = data
        if len(data) > 0 and 'close' in data.columns:
            self.parent._last_price = float(data['close'].iloc[-1])
            logger.debug(f"Set _last_price from data: {self.parent._last_price}")
        return data

    def _fill_one_second_gaps(self, data: "pd.DataFrame") -> "pd.DataFrame":
        """Fill missing seconds with previous candle's close (forward-fill).

        For 1-second candles, if a second has no data, use the previous candle:
        - open/high/low/close = previous close
        - volume = 0

        Args:
            data: OHLCV DataFrame with DatetimeIndex

        Returns:
            DataFrame with filled gaps
        """
        if data.empty:
            return data

        try:
            # Resample to 1S frequency, forward-fill OHLC, set volume to 0 for gaps
            data_1s = data.resample('1S').asfreq()

            # Forward-fill OHLC with previous values
            for col in ['open', 'high', 'low', 'close']:
                if col in data_1s.columns:
                    data_1s[col] = data_1s[col].ffill()

            # Fill missing volume with 0
            if 'volume' in data_1s.columns:
                data_1s['volume'] = data_1s['volume'].fillna(0)

            # For newly filled rows, set open=high=low=close (flat candle)
            mask = data_1s['open'].isna()
            if mask.any():
                prev_close = data_1s['close'].ffill()
                data_1s.loc[mask, ['open', 'high', 'low', 'close']] = prev_close[mask].values[:, None]

            # Drop any remaining NaN rows (only at the very start if data doesn't start at second boundary)
            data_1s = data_1s.dropna(subset=['open', 'high', 'low', 'close'])

            logger.info(f"1S gaps filled: {len(data)} → {len(data_1s)} candles")
            return data_1s

        except Exception as exc:
            logger.error(f"Failed to fill 1S gaps: {exc}")
            return data  # Return original data on error

    def build_chart_series(self, data: "pd.DataFrame") -> tuple[list[dict], list[dict]]:
        """Convert DataFrame to candle + volume series.

        Issue #40: Volume colors now match user's candle color settings.

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

        # Issue #40: Get volume colors from settings
        vol_colors = _get_volume_colors()

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
            # Issue #40: Use custom colors from settings
            is_bullish = row['close'] >= row['open']
            volume_data.append({
                'time': unix_time,
                'value': float(row.get('volume', 0)),
                'color': vol_colors['bullish'] if is_bullish else vol_colors['bearish'],
            })

        return candle_data, volume_data

    def update_chart_series(self, candle_data: list[dict], volume_data: list[dict] = None) -> None:
        """Send candle and volume data to JavaScript chart.

        Args:
            candle_data: List of OHLC candle dicts
            volume_data: List of volume bar dicts (Issue #5, #40)
        """
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

        # Issue #5, #40: Create volume panel and set volume data with custom colors
        if volume_data:
            # Issue #40: Use custom bullish color for volume panel
            vol_colors = _get_volume_colors()
            self.parent._execute_js(
                f"window.chartAPI.createPanel('volume', 'Volume', 'histogram', '{vol_colors['bullish']}', null, null);"
            )
            volume_json = json.dumps(volume_data)
            self.parent._execute_js(f"window.chartAPI.setPanelData('volume', {volume_json});")
            logger.info(f"📊 Volume panel created with {len(volume_data)} bars (colors: {vol_colors})")

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
