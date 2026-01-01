"""Data Loading Mixin for EmbeddedTradingViewChart.

Contains data loading methods (load_data, load_symbol).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import pytz

logger = logging.getLogger(__name__)


def get_local_timezone_offset_seconds() -> int:
    """Get local timezone offset in seconds (positive for east of UTC).

    This accounts for DST automatically.
    """
    # time.timezone is seconds west of UTC (negative for CET)
    # time.daylight tells if DST is observed, time.altzone is DST offset
    if time.daylight and time.localtime().tm_isdst > 0:
        return -time.altzone
    return -time.timezone


class DataLoadingMixin:
    """Mixin providing data loading functionality for EmbeddedTradingViewChart."""

    def _clean_bad_ticks(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Bereinige Bad Ticks in historischen OHLCV-Daten.

        Bad Ticks erzeugen extreme Wicks (High/Low weit vom Körper entfernt).
        Diese Funktion korrigiert solche Ausreißer.

        Args:
            data: OHLCV DataFrame

        Returns:
            Bereinigter DataFrame
        """
        if data.empty:
            return data

        # Arbeite mit Kopie
        df = data.copy()

        # Maximale erlaubte Wick-Größe als % vom Kerzenkörper
        max_wick_pct = 10.0  # 10% vom Preis

        for i in range(len(df)):
            row = df.iloc[i]
            body_high = max(row['open'], row['close'])
            body_low = min(row['open'], row['close'])
            mid_price = (body_high + body_low) / 2 if body_high > 0 else row['close']

            if mid_price <= 0:
                continue

            # Prüfe High - ist es unrealistisch hoch?
            if row['high'] > body_high:
                wick_up_pct = ((row['high'] - body_high) / mid_price) * 100
                if wick_up_pct > max_wick_pct:
                    # Bad tick - korrigiere High auf body_high + kleiner Puffer
                    new_high = body_high * 1.005  # 0.5% über Body
                    df.iloc[i, df.columns.get_loc('high')] = new_high
                    logger.debug(
                        f"Bad tick corrected: High {row['high']:.2f} -> {new_high:.2f} "
                        f"(was {wick_up_pct:.1f}% above body)"
                    )

            # Prüfe Low - ist es unrealistisch tief?
            if row['low'] < body_low:
                wick_down_pct = ((body_low - row['low']) / mid_price) * 100
                if wick_down_pct > max_wick_pct:
                    # Bad tick - korrigiere Low auf body_low - kleiner Puffer
                    new_low = body_low * 0.995  # 0.5% unter Body
                    df.iloc[i, df.columns.get_loc('low')] = new_low
                    logger.debug(
                        f"Bad tick corrected: Low {row['low']:.2f} -> {new_low:.2f} "
                        f"(was {wick_down_pct:.1f}% below body)"
                    )

        return df

    def load_data(self, data: pd.DataFrame):
        """Load market data into chart.

        Args:
            data: OHLCV DataFrame with DatetimeIndex
        """
        # Wait for page + chart initialization before setting data
        if not (self.page_loaded and self.chart_initialized):
            logger.info("Chart not ready yet, deferring data load")
            self.pending_data_load = data
            return

        try:
            data = self._prepare_chart_data(data)
            candle_data, volume_data = self._build_chart_series(data)
            self._update_chart_series(candle_data)
            self.volume_data = volume_data
            self._finalize_chart_load(data, candle_data)

        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

    def _prepare_chart_data(self, data: pd.DataFrame) -> pd.DataFrame:
        data = self._clean_bad_ticks(data)
        self.data = data
        if len(data) > 0 and 'close' in data.columns:
            self._last_price = float(data['close'].iloc[-1])
            logger.debug(f"Set _last_price from data: {self._last_price}")
        return data

    def _build_chart_series(self, data: pd.DataFrame) -> tuple[list[dict], list[dict]]:
        candle_data = []
        volume_data = []
        local_offset = get_local_timezone_offset_seconds()
        logger.debug(
            f"Local timezone offset: {local_offset} seconds ({local_offset // 3600}h)"
        )
        for timestamp, row in data.iterrows():
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

    def _update_chart_series(self, candle_data: list[dict]) -> None:
        skip_fit = getattr(self, '_skip_fit_content', False)
        if skip_fit:
            logger.info("📌 Setting suppressFitContent=true in JavaScript")
            self._execute_js("window.chartAPI.setSuppressFitContent(true);")

        candle_json = json.dumps(candle_data)
        if skip_fit:
            self._execute_js(f"window.chartAPI.setData({candle_json}, true);")
            logger.info("Loaded data with skipFit=true - state restoration pending")
        else:
            self._execute_js(f"window.chartAPI.setData({candle_json});")

        if not skip_fit:
            self._execute_js("window.chartAPI.fitContent();")

    def _finalize_chart_load(self, data: pd.DataFrame, candle_data: list[dict]) -> None:
        self._update_indicators()
        first_date = data.index[0].strftime('%Y-%m-%d %H:%M')
        last_date = data.index[-1].strftime('%Y-%m-%d %H:%M')
        self.info_label.setText(
            f"Loaded {len(candle_data)} bars | "
            f"From: {first_date} | To: {last_date}"
        )
        self.market_status_label.setText("✓ Chart Loaded")
        self.market_status_label.setStyleSheet(
            "color: #00FF00; font-weight: bold; padding: 5px;"
        )
        if not self.update_timer.isActive():
            self.update_timer.start()
        logger.info(f"Loaded {len(candle_data)} bars into embedded chart")
        self.data_loaded.emit()

    async def load_symbol(self, symbol: str, data_provider: Optional[str] = None):
        """Load symbol data and display chart.

        Args:
            symbol: Trading symbol
            data_provider: Data provider (alpaca, yahoo, etc.)
        """
        try:
            if not self.history_manager:
                logger.warning("No history manager available")
                self.market_status_label.setText("⚠ No data source")
                return

            self.current_symbol = symbol
            self.current_data_provider = data_provider
            self.symbol_combo.setCurrentText(symbol)

            self.market_status_label.setText(f"Loading {symbol}...")
            self.market_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")

            # Import required classes
            from src.core.market_data.history_provider import DataRequest, DataSource, Timeframe
            from src.core.market_data.types import AssetClass

            # Detect asset class from symbol
            # Crypto symbols contain "/" (e.g., BTC/USD, ETH/USD)
            # Stock symbols don't (e.g., AAPL, MSFT)
            asset_class = self._resolve_asset_class(symbol, AssetClass)

            # Map timeframe
            timeframe = self._resolve_timeframe(Timeframe)

            # Map provider (single Alpaca option auto-selects crypto vs stocks)
            provider_source = self._resolve_provider_source(
                data_provider, asset_class, DataSource, AssetClass
            )

            # Determine lookback period based on selected time period
            lookback_days = self._resolve_lookback_days()
            start_date, end_date = self._calculate_date_range(
                asset_class, lookback_days, AssetClass
            )

            logger.info(f"Loading {symbol} - Candles: {self.current_timeframe}, Period: {self.current_period} ({lookback_days} days)")
            logger.info(f"Date range: {start_date.strftime('%Y-%m-%d %H:%M:%S %Z')} to {end_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")


            # Fetch data
            request = DataRequest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                asset_class=asset_class,  # Important: Set asset class for proper routing
                source=provider_source
            )

            # CRITICAL DEBUG: Log the actual date range being requested
            self._log_request_details(symbol, start_date, end_date, asset_class, provider_source)

            bars, source_used = await self.history_manager.fetch_data(request)

            # Log fetched data range
            if bars:
                first_bar = bars[0].timestamp
                last_bar = bars[-1].timestamp
                logger.info(f"📊 Fetched {len(bars)} bars from {source_used}")
                logger.info(f"   First bar: {first_bar.strftime('%Y-%m-%d %H:%M:%S') if hasattr(first_bar, 'strftime') else first_bar}")
                logger.info(f"   Last bar:  {last_bar.strftime('%Y-%m-%d %H:%M:%S') if hasattr(last_bar, 'strftime') else last_bar}")

            if not bars:
                logger.warning(f"No data for {symbol}")
                self.market_status_label.setText(f"⚠ No data for {symbol}")
                return

            # Convert to DataFrame
            df = self._bars_to_dataframe(bars)

            # Load into chart
            self.load_data(df)

            # Update status with data source info (only if not live streaming)
            if not self.live_streaming_enabled:
                self._set_loaded_status(source_used)

            logger.info(f"Loaded {len(bars)} bars for {symbol} from {source_used}")

            # Restart live stream if enabled (with proper cleanup)
            if self.live_streaming_enabled:
                await self._restart_live_stream(symbol)

        except Exception as e:
            logger.error(f"Error loading symbol: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold;")

    def _resolve_asset_class(self, symbol: str, AssetClass) -> AssetClass:
        return AssetClass.CRYPTO if "/" in symbol else AssetClass.STOCK

    def _resolve_timeframe(self, Timeframe) -> Timeframe:
        timeframe_map = {
            "1T": Timeframe.MINUTE_1,
            "5T": Timeframe.MINUTE_5,
            "15T": Timeframe.MINUTE_15,
            "30T": Timeframe.MINUTE_30,
            "1H": Timeframe.HOUR_1,
            "4H": Timeframe.HOUR_4,
            "1D": Timeframe.DAY_1,
        }
        return timeframe_map.get(self.current_timeframe, Timeframe.MINUTE_1)

    def _resolve_provider_source(self, data_provider, asset_class, DataSource, AssetClass):
        if data_provider:
            if data_provider == "alpaca":
                return DataSource.ALPACA_CRYPTO if asset_class == AssetClass.CRYPTO else DataSource.ALPACA
            provider_map = {
                "database": DataSource.DATABASE,
                "yahoo": DataSource.YAHOO,
                "alpha_vantage": DataSource.ALPHA_VANTAGE,
                "ibkr": DataSource.IBKR,
                "finnhub": DataSource.FINNHUB,
            }
            return provider_map.get(data_provider)

        if asset_class == AssetClass.CRYPTO:
            logger.info("No provider specified, using Alpaca Crypto for live data")
            return DataSource.ALPACA_CRYPTO
        logger.info("No provider specified, using Alpaca for live data")
        return DataSource.ALPACA

    def _resolve_lookback_days(self) -> int:
        period_to_days = {
            "1D": 1,      # Intraday (today)
            "2D": 2,      # 2 days
            "5D": 5,      # 5 days
            "1W": 7,      # 1 week
            "2W": 14,     # 2 weeks
            "1M": 30,     # 1 month
            "3M": 90,     # 3 months
            "6M": 180,    # 6 months
            "1Y": 365,    # 1 year
        }
        return period_to_days.get(self.current_period, 30)

    def _calculate_date_range(self, asset_class, lookback_days: int, AssetClass):
        ny_tz = pytz.timezone('America/New_York')
        now_ny = datetime.now(ny_tz)
        end_date = now_ny

        if asset_class == AssetClass.CRYPTO:
            start_date = end_date - timedelta(days=lookback_days)
            logger.info("Crypto asset: Using current time (24/7 trading)")
            return start_date, end_date

        market_open_hour = 9
        market_open_minute = 30
        use_previous_trading_day = False

        weekday = end_date.weekday()
        current_hour = end_date.hour
        current_minute = end_date.minute
        is_before_market_open = (
            current_hour < market_open_hour
            or (current_hour == market_open_hour and current_minute < market_open_minute)
        )

        if weekday == 5:  # Saturday
            end_date = end_date - timedelta(days=1)
            use_previous_trading_day = True
            logger.info("Weekend detected (Saturday), using Friday's data")
        elif weekday == 6:  # Sunday
            end_date = end_date - timedelta(days=2)
            use_previous_trading_day = True
            logger.info("Weekend detected (Sunday), using Friday's data")
        elif weekday == 0 and is_before_market_open:  # Monday before market open
            end_date = end_date - timedelta(days=3)
            use_previous_trading_day = True
            logger.info(
                f"Monday pre-market ({current_hour:02d}:{current_minute:02d} EST), using Friday's data"
            )
        elif weekday < 5 and is_before_market_open:
            end_date = end_date - timedelta(days=1)
            use_previous_trading_day = True
            logger.info(
                f"Pre-market hours ({current_hour:02d}:{current_minute:02d} EST), using previous trading day"
            )

        if self.current_period == "1D" and use_previous_trading_day:
            last_trading_day = end_date.date()
            start_date = ny_tz.localize(datetime.combine(last_trading_day, datetime.min.time())).replace(
                hour=4, minute=0
            )
            end_date = ny_tz.localize(datetime.combine(last_trading_day, datetime.max.time())).replace(
                hour=20, minute=0
            )
            logger.info(
                f"Intraday non-trading period: fetching data for {last_trading_day} (4:00 - 20:00 EST)"
            )
        else:
            start_date = end_date - timedelta(days=lookback_days)
        return start_date, end_date

    def _log_request_details(self, symbol: str, start_date, end_date, asset_class, provider_source) -> None:
        logger.info(f"📅 Requesting data: {symbol}")
        logger.info(f"   Start: {start_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"   End:   {end_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(
            f"   Asset: {asset_class.value}, Source: {provider_source.value if provider_source else 'auto'}"
        )

    def _bars_to_dataframe(self, bars) -> pd.DataFrame:
        data_dict = {
            'timestamp': [bar.timestamp for bar in bars],
            'open': [float(bar.open) for bar in bars],
            'high': [float(bar.high) for bar in bars],
            'low': [float(bar.low) for bar in bars],
            'close': [float(bar.close) for bar in bars],
            'volume': [bar.volume for bar in bars]
        }
        df = pd.DataFrame(data_dict)
        df.set_index('timestamp', inplace=True)
        return df

    def _set_loaded_status(self, source_used: str) -> None:
        self.market_status_label.setText(f"✓ Loaded from {source_used}")
        self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")

    async def _restart_live_stream(self, symbol: str) -> None:
        logger.info(f"Restarting live stream for symbol: {symbol}")
        await self._stop_live_stream()
        await asyncio.sleep(0.5)
        await self._start_live_stream()

    async def refresh_data(self):
        """Public method to refresh chart data (called by main app)."""
        if self.current_symbol:
            await self.load_symbol(self.current_symbol, self.current_data_provider)
        else:
            logger.warning("No symbol loaded to refresh")

    def _on_symbol_change(self, symbol: str):
        """Handle symbol change."""
        # Ignore separator line
        if symbol == "───────" or not symbol.strip():
            # Revert to previous symbol
            self.symbol_combo.setCurrentText(self.current_symbol)
            return

        self.current_symbol = symbol
        self.symbol_changed.emit(symbol)
        logger.info(f"Symbol changed to: {symbol}")

    def _on_timeframe_change(self, timeframe: str):
        """Handle timeframe (candle size) change."""
        self.current_timeframe = timeframe
        self.timeframe_changed.emit(timeframe)
        logger.info(f"Candle size changed to: {timeframe}")

    def _on_period_change(self, period: str):
        """Handle time period change."""
        self.current_period = period
        logger.info(f"Time period changed to: {period}")

    def _on_load_chart(self):
        """Load chart data for current symbol."""
        try:
            # Schedule async task without blocking UI
            asyncio.ensure_future(self._load_chart_async())
        except Exception as e:
            logger.error(f"Failed to schedule chart load: {e}")

    async def _load_chart_async(self):
        """Async implementation of chart loading."""
        try:
            await self.load_symbol(self.current_symbol, self.current_data_provider)
        except Exception as e:
            logger.error(f"Failed to load chart: {e}")

    def _on_refresh(self):
        """Refresh current chart."""
        if self.data is not None:
            self.load_data(self.data)
        else:
            self._on_load_chart()
