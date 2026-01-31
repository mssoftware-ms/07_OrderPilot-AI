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
        """Prepare and store data for chart display.

        NOTE: No cleaning/filtering here - data must be clean in database!
        Forward-fill gaps for 1-second candles if requested by user.
        Issue #42: Filter to specific hour ranges for short periods (1H, 2H, 4H, 8H).
        """
        # Forward-fill gaps for 1-second candles (user request 2026-01-13)
        if hasattr(self.parent, 'current_timeframe') and self.parent.current_timeframe == "1S":
            data = self._fill_one_second_gaps(data)

        # Issue #42: Filter data to last N hours for short period selections
        if hasattr(self.parent, 'current_period'):
            period = self.parent.current_period
            if period in ["1H", "2H", "4H", "8H"] and not data.empty:
                hours_map = {"1H": 1, "2H": 2, "4H": 4, "8H": 8}
                hours = hours_map.get(period, 1)
                data = self._filter_to_last_hours(data, hours)

        self.parent.data = data
        if len(data) > 0 and 'close' in data.columns:
            # Only set _last_price if not already streaming (prevents overwriting live price)
            # Issue: Setting _last_price from historical data was overwriting live stream prices
            # causing the Current Position "Current" price to jump between old and new values
            existing_price = getattr(self.parent, '_last_price', 0.0)
            if existing_price <= 0:
                self.parent._last_price = float(data['close'].iloc[-1])
                logger.debug(f"Set _last_price from data (initial): {self.parent._last_price}")
            else:
                logger.debug(f"Keeping live _last_price: {existing_price} (data would set: {data['close'].iloc[-1]})")
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

    def _filter_to_last_hours(self, data: "pd.DataFrame", hours: int) -> "pd.DataFrame":
        """Filter DataFrame to show only the last N hours.

        Issue #42: For short periods (1H, 2H, 4H, 8H), we fetch 1 day of data
        but only display the last N hours.

        Args:
            data: OHLCV DataFrame with DatetimeIndex
            hours: Number of hours to keep

        Returns:
            Filtered DataFrame
        """
        if data.empty:
            return data

        try:
            from datetime import timedelta
            cutoff = data.index[-1] - timedelta(hours=hours)
            filtered = data[data.index >= cutoff]
            logger.info(f"Filtered to last {hours}h: {len(data)} → {len(filtered)} candles")
            return filtered
        except Exception as exc:
            logger.error(f"Failed to filter to last {hours}h: {exc}")
            return data  # Return original data on error

    def build_chart_series(self, data: "pd.DataFrame") -> tuple[list[dict], list[dict]]:
        """Convert DataFrame to candle + volume series.

        Issue #40: Volume colors now match user's candle color settings.

        TradingView Lightweight Charts expects Unix timestamps in seconds (UTC).
        timestamp.timestamp() already returns correct Unix timestamp for both
        timezone-aware and naive datetime objects, so NO offset adjustment needed.

        Returns:
            Tuple of (candle_data, volume_data)
        """
        candle_data = []
        volume_data = []

        # Issue #40: Get volume colors from settings
        vol_colors = _get_volume_colors()

        for timestamp, row in data.iterrows():
            # Skip rows with NaN values
            if any(pd.isna(x) for x in [row['open'], row['high'], row['low'], row['close']]):
                continue

            # TradingView expects Unix timestamps in seconds (UTC)
            # timestamp.timestamp() already returns correct value - NO offset needed!
            unix_time = int(timestamp.timestamp())
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

        # Issue #26: Update statistics labels after data load
        if hasattr(self.parent, 'update_all_stats_labels'):
            try:
                self.parent.update_all_stats_labels(data)
            except Exception as e:
                logger.warning(f"Failed to update stats labels: {e}")
