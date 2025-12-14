"""Data Loading Mixin for EmbeddedTradingViewChart.

Contains data loading methods (load_data, load_symbol).
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import pytz

logger = logging.getLogger(__name__)


class DataLoadingMixin:
    """Mixin providing data loading functionality for EmbeddedTradingViewChart."""

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
            self.data = data

            # Prepare candlestick data
            candle_data = []
            volume_data = []

            for timestamp, row in data.iterrows():
                # Skip invalid data
                if any(pd.isna(x) for x in [row['open'], row['high'], row['low'], row['close']]):
                    continue

                unix_time = int(timestamp.timestamp())

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
                    'color': '#26a69a' if row['close'] >= row['open'] else '#ef5350'
                })

            # Check if we should skip fitContent (state restoration pending)
            skip_fit = getattr(self, '_skip_fit_content', False)

            if skip_fit:
                # Suppress ALL fitContent calls in JavaScript during state restoration
                logger.info("📌 Setting suppressFitContent=true in JavaScript")
                self._execute_js("window.chartAPI.setSuppressFitContent(true);")

            # Send candlestick data to chart (with skipFit parameter)
            candle_json = json.dumps(candle_data)
            if skip_fit:
                self._execute_js(f"window.chartAPI.setData({candle_json}, true);")
                logger.info("Loaded data with skipFit=true - state restoration pending")
            else:
                self._execute_js(f"window.chartAPI.setData({candle_json});")

            # Store volume data for external dock widgets
            self.volume_data = volume_data

            # Fit chart ONLY if no state restoration is pending
            if not skip_fit:
                self._execute_js("window.chartAPI.fitContent();")

            # Update indicators (will be handled by dock widgets)
            self._update_indicators()

            # Update UI
            first_date = data.index[0].strftime('%Y-%m-%d %H:%M')
            last_date = data.index[-1].strftime('%Y-%m-%d %H:%M')
            self.info_label.setText(
                f"Loaded {len(candle_data)} bars | "
                f"From: {first_date} | To: {last_date}"
            )
            self.market_status_label.setText("✓ Chart Loaded")
            self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")

            # Start update timer for real-time data
            if not self.update_timer.isActive():
                self.update_timer.start()

            logger.info(f"Loaded {len(candle_data)} bars into embedded chart")

            # Emit signal that data was loaded (for dock widgets)
            self.data_loaded.emit()

        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

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
            asset_class = AssetClass.CRYPTO if "/" in symbol else AssetClass.STOCK

            # Map timeframe
            timeframe_map = {
                "1T": Timeframe.MINUTE_1,
                "5T": Timeframe.MINUTE_5,
                "15T": Timeframe.MINUTE_15,
                "30T": Timeframe.MINUTE_30,
                "1H": Timeframe.HOUR_1,
                "4H": Timeframe.HOUR_4,
                "1D": Timeframe.DAY_1,
            }
            timeframe = timeframe_map.get(self.current_timeframe, Timeframe.MINUTE_1)

            # Map provider (single Alpaca option auto-selects crypto vs stocks)
            provider_source = None
            if data_provider:
                if data_provider == "alpaca":
                    provider_source = (
                        DataSource.ALPACA_CRYPTO
                        if asset_class == AssetClass.CRYPTO
                        else DataSource.ALPACA
                    )
                else:
                    provider_map = {
                        "database": DataSource.DATABASE,
                        "yahoo": DataSource.YAHOO,
                        "alpha_vantage": DataSource.ALPHA_VANTAGE,
                        "ibkr": DataSource.IBKR,
                        "finnhub": DataSource.FINNHUB,
                    }
                    provider_source = provider_map.get(data_provider)
            else:
                # Default: Use appropriate Alpaca provider based on asset class
                if asset_class == AssetClass.CRYPTO:
                    provider_source = DataSource.ALPACA_CRYPTO
                    logger.info("No provider specified, using Alpaca Crypto for live data")
                else:
                    provider_source = DataSource.ALPACA
                    logger.info("No provider specified, using Alpaca for live data")

            # Determine lookback period based on selected time period
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
            lookback_days = period_to_days.get(self.current_period, 30)  # Default: 1 month

            # --- Timezone-aware date calculation ---
            ny_tz = pytz.timezone('America/New_York')
            now_ny = datetime.now(ny_tz)
            end_date = now_ny

            # CRITICAL: Crypto trades 24/7, stocks have market hours
            use_previous_trading_day = False

            if asset_class == AssetClass.CRYPTO:
                # Crypto: Always use current time, no market hours restrictions
                start_date = end_date - timedelta(days=lookback_days)
                logger.info(f"Crypto asset: Using current time (24/7 trading)")
            else:
                # Stocks: Apply market hours logic
                # Market hours: 9:30 AM - 4:00 PM EST
                market_open_hour = 9
                market_open_minute = 30

                # Adjust end_date for weekends AND pre-market hours
                weekday = end_date.weekday()  # Monday=0, Sunday=6
                current_hour = end_date.hour
                current_minute = end_date.minute
                is_before_market_open = (current_hour < market_open_hour or
                                        (current_hour == market_open_hour and current_minute < market_open_minute))

                if weekday == 5:  # Saturday
                    end_date = end_date - timedelta(days=1)
                    use_previous_trading_day = True
                    logger.info("Weekend detected (Saturday), using Friday's data")
                elif weekday == 6:  # Sunday
                    end_date = end_date - timedelta(days=2)
                    use_previous_trading_day = True
                    logger.info("Weekend detected (Sunday), using Friday's data")
                elif weekday == 0 and is_before_market_open:  # Monday before market open
                    end_date = end_date - timedelta(days=3)  # Go back to Friday
                    use_previous_trading_day = True
                    logger.info(f"Monday pre-market ({current_hour:02d}:{current_minute:02d} EST), using Friday's data")
                elif weekday < 5 and is_before_market_open:  # Tuesday-Friday before market open
                    end_date = end_date - timedelta(days=1)  # Go back to previous day
                    use_previous_trading_day = True
                    logger.info(f"Pre-market hours ({current_hour:02d}:{current_minute:02d} EST), using previous trading day")

                # For intraday during non-trading periods, fetch the entire last trading day
                if self.current_period == "1D" and use_previous_trading_day:
                    # Set a specific window for the last trading day in New York time
                    last_trading_day = end_date.date()
                    start_date = ny_tz.localize(datetime.combine(last_trading_day, datetime.min.time())).replace(hour=4, minute=0)
                    end_date = ny_tz.localize(datetime.combine(last_trading_day, datetime.max.time())).replace(hour=20, minute=0)
                    logger.info(f"Intraday non-trading period: fetching data for {last_trading_day} (4:00 - 20:00 EST)")
                else:
                    # Standard lookback calculation
                    start_date = end_date - timedelta(days=lookback_days)

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
            logger.info(f"📅 Requesting data: {symbol}")
            logger.info(f"   Start: {start_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"   End:   {end_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"   Asset: {asset_class.value}, Source: {provider_source.value if provider_source else 'auto'}")

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

            # Load into chart
            self.load_data(df)

            # Update status with data source info (only if not live streaming)
            if not self.live_streaming_enabled:
                self.market_status_label.setText(f"✓ Loaded from {source_used}")
                self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")

            logger.info(f"Loaded {len(bars)} bars for {symbol} from {source_used}")

            # Restart live stream if enabled (with proper cleanup)
            if self.live_streaming_enabled:
                logger.info(f"Restarting live stream for symbol: {symbol}")
                # CRITICAL: Stop existing stream first to prevent deadlock
                await self._stop_live_stream()
                # Small delay to ensure cleanup completes
                await asyncio.sleep(0.5)
                # Now start new stream
                await self._start_live_stream()

        except Exception as e:
            logger.error(f"Error loading symbol: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold;")

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
        # Get or create event loop compatible with Qt
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Try qasync loop if available
            try:
                from qasync import QEventLoop
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    loop = QEventLoop(app)
                    asyncio.set_event_loop(loop)
                else:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except ImportError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        # Create and schedule the task
        asyncio.create_task(self.load_symbol(self.current_symbol, self.current_data_provider))

    def _on_refresh(self):
        """Refresh current chart."""
        if self.data is not None:
            self.load_data(self.data)
        else:
            self._on_load_chart()
