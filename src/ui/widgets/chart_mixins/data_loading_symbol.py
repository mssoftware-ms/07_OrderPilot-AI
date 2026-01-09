"""Data Loading Symbol - Main load_symbol orchestration.

Refactored from 498 LOC monolith using composition pattern.

Module 5/6 of data_loading_mixin.py split.

Contains:
- load_symbol(): Main async method to load symbol data
- log_request_details(): Log data request details
- set_loaded_status(): Update status label
- restart_live_stream(): Restart streaming after symbol change
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.market_data.types import AssetClass

logger = logging.getLogger(__name__)


class DataLoadingSymbol:
    """Helper für DataLoadingMixin load_symbol orchestration."""

    def __init__(self, parent):
        """
        Args:
            parent: DataLoadingMixin Instanz
        """
        self.parent = parent

    async def load_symbol(self, symbol: str, data_provider: Optional[str] = None):
        """Load symbol data and display chart.

        Args:
            symbol: Trading symbol
            data_provider: Data provider (alpaca, yahoo, etc.)
        """
        try:
            if not self.parent.history_manager:
                logger.warning("No history manager available")
                self.parent.market_status_label.setText("⚠ No data source")
                return

            self.parent.current_symbol = symbol
            self.parent.current_data_provider = data_provider
            if hasattr(self.parent, 'symbol_combo'):
                self.parent.symbol_combo.setCurrentText(symbol)

            self.parent.market_status_label.setText(f"Loading {symbol}...")
            self.parent.market_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")

            # Import required classes
            from src.core.market_data.history_provider import DataRequest, DataSource, Timeframe
            from src.core.market_data.types import AssetClass

            # Detect asset class from symbol
            asset_class = self.parent._resolution.resolve_asset_class(symbol)

            # Map timeframe
            timeframe = self.parent._resolution.resolve_timeframe()

            # Map provider (single Alpaca option auto-selects crypto vs stocks)
            provider_source = self.parent._resolution.resolve_provider_source(
                data_provider, asset_class
            )

            # Store for AI Analysis and other components
            self.parent.current_asset_class = asset_class
            self.parent.current_data_source = provider_source

            # Determine lookback period based on selected time period
            lookback_days = self.parent._resolution.resolve_lookback_days()
            start_date, end_date = self.parent._resolution.calculate_date_range(
                asset_class, lookback_days
            )

            logger.info(f"Loading {symbol} - Candles: {self.parent.current_timeframe}, Period: {self.parent.current_period} ({lookback_days} days)")
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
            self.log_request_details(symbol, start_date, end_date, asset_class, provider_source)

            bars, source_used = await self.parent.history_manager.fetch_data(request)

            # Log fetched data range
            if bars:
                first_bar = bars[0].timestamp
                last_bar = bars[-1].timestamp
                logger.info(f"📊 Fetched {len(bars)} bars from {source_used}")
                logger.info(f"   First bar: {first_bar.strftime('%Y-%m-%d %H:%M:%S') if hasattr(first_bar, 'strftime') else first_bar}")
                logger.info(f"   Last bar:  {last_bar.strftime('%Y-%m-%d %H:%M:%S') if hasattr(last_bar, 'strftime') else last_bar}")

            if not bars:
                logger.warning(f"No data for {symbol}")
                self.parent.market_status_label.setText(f"⚠ No data for {symbol}")
                return

            # Convert to DataFrame
            df = self.parent._resolution.bars_to_dataframe(bars)

            # Load into chart
            self.parent.load_data(df)

            # Update status with data source info (only if not live streaming)
            if not self.parent.live_streaming_enabled:
                self.set_loaded_status(source_used)

            logger.info(f"Loaded {len(bars)} bars for {symbol} from {source_used}")

            # Restart live stream if enabled (with proper cleanup)
            if self.parent.live_streaming_enabled:
                await self.restart_live_stream(symbol)

        except Exception as e:
            logger.error(f"Error loading symbol: {e}", exc_info=True)
            self.parent.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.parent.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold;")

    def log_request_details(
        self,
        symbol: str,
        start_date,
        end_date,
        asset_class: "AssetClass",
        provider_source
    ) -> None:
        """Log data request details.

        Args:
            symbol: Trading symbol
            start_date: Start datetime
            end_date: End datetime
            asset_class: Asset class enum value
            provider_source: DataSource enum value
        """
        logger.info(f"📅 Requesting data: {symbol}")
        logger.info(f"   Start: {start_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"   End:   {end_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(
            f"   Asset: {asset_class.value}, Source: {provider_source.value if provider_source else 'auto'}"
        )

    def set_loaded_status(self, source_used: str) -> None:
        """Update status label after successful load.

        Args:
            source_used: Data source name
        """
        self.parent.market_status_label.setText(f"✓ Loaded from {source_used}")
        self.parent.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")

    async def restart_live_stream(self, symbol: str) -> None:
        """Restart live stream after symbol change.

        Args:
            symbol: Trading symbol
        """
        logger.info(f"Restarting live stream for symbol: {symbol}")
        await self.parent._stop_live_stream()
        await asyncio.sleep(0.5)
        await self.parent._start_live_stream()
