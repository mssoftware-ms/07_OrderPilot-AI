"""Data Loading Resolution - Resolution helpers.

Refactored from 498 LOC monolith using composition pattern.

Module 4/6 of data_loading_mixin.py split.

Contains:
- resolve_asset_class(): Determine if crypto or stock from symbol
- resolve_timeframe(): Map timeframe string to enum
- resolve_provider_source(): Map provider string to DataSource enum
- resolve_lookback_days(): Map period string to days
- calculate_date_range(): Calculate start/end dates with market hours logic
- bars_to_dataframe(): Convert bars to DataFrame
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import pytz

# Runtime imports - used for enum comparisons and return values
from src.core.market_data.history_provider import DataSource, Timeframe
from src.core.market_data.types import AssetClass

logger = logging.getLogger(__name__)


class DataLoadingResolution:
    """Helper für DataLoadingMixin resolution methods."""

    def __init__(self, parent):
        """
        Args:
            parent: DataLoadingMixin Instanz
        """
        self.parent = parent

    def resolve_asset_class(self, symbol: str) -> AssetClass:
        """Determine asset class from symbol format.

        Args:
            symbol: Trading symbol

        Returns:
            AssetClass enum value
        """
        # Bitunix symbols: BTCUSDT, ETHUSDT, etc. (crypto futures)
        # Alpaca crypto: BTC/USD, ETH/USD (spot with slash)
        # Stocks: AAPL, MSFT, etc.
        if "USDT" in symbol or "USDC" in symbol:
            # Bitunix perpetual futures (BTCUSDT, ETHUSDT)
            return AssetClass.CRYPTO
        elif "/" in symbol:
            # Alpaca crypto spot (BTC/USD, ETH/USD)
            return AssetClass.CRYPTO
        else:
            # Traditional stocks (AAPL, MSFT)
            return AssetClass.STOCK

    def resolve_timeframe(self) -> Timeframe:
        """Map timeframe string to Timeframe enum.

        Returns:
            Timeframe enum value
        """
        timeframe_map = {
            "1S": Timeframe.SECOND_1,  # Issue #42: Added 1-second mapping
            "1T": Timeframe.MINUTE_1,
            "5T": Timeframe.MINUTE_5,
            "10T": Timeframe.MINUTE_10,
            "15T": Timeframe.MINUTE_15,
            "30T": Timeframe.MINUTE_30,
            "1H": Timeframe.HOUR_1,
            "2H": Timeframe.HOUR_2,  # Issue #42: Added 2-hour mapping
            "4H": Timeframe.HOUR_4,
            "8H": Timeframe.HOUR_8,  # Issue #42: Added 8-hour mapping
            "1D": Timeframe.DAY_1,
        }
        return timeframe_map.get(self.parent.current_timeframe, Timeframe.MINUTE_1)

    def resolve_provider_source(
        self,
        data_provider: Optional[str],
        asset_class: AssetClass,
    ) -> Optional[DataSource]:
        """Map provider string to DataSource enum.

        Args:
            data_provider: Provider name string
            asset_class: Asset class enum value

        Returns:
            DataSource enum value or None
        """
        if data_provider:
            if data_provider == "alpaca":
                return DataSource.ALPACA_CRYPTO if asset_class == AssetClass.CRYPTO else DataSource.ALPACA
            elif data_provider == "bitunix":
                return DataSource.BITUNIX

            provider_map = {
                "database": DataSource.DATABASE,
                "yahoo": DataSource.YAHOO,
                "alpha_vantage": DataSource.ALPHA_VANTAGE,
                "ibkr": DataSource.IBKR,
                "finnhub": DataSource.FINNHUB,
            }
            return provider_map.get(data_provider)

        # Auto-detect provider based on symbol pattern when no provider specified
        if asset_class == AssetClass.CRYPTO:
            # Issue #44: Better symbol pattern detection
            # Bitunix: BTCUSDT, ETHUSDT (no slash, USDT/USDC suffix)
            # Alpaca: BTC/USD, ETH/USD, SOL/USDT (has slash)
            symbol = self.parent.current_symbol if hasattr(self.parent, 'current_symbol') else ""

            if "/" in symbol:
                # Has slash → Alpaca Crypto (BTC/USD, ETH/USD, SOL/USDT)
                logger.info(f"🔍 Alpaca crypto symbol detected ({symbol}), using Alpaca Crypto")
                return DataSource.ALPACA_CRYPTO
            elif "USDT" in symbol or "USDC" in symbol:
                # No slash but has USDT/USDC → Bitunix (BTCUSDT, ETHUSDT)
                logger.info(f"🔍 Bitunix symbol detected ({symbol}), using Bitunix provider")
                return DataSource.BITUNIX
            else:
                # Fallback for other crypto symbols
                logger.info(f"🔍 Unknown crypto symbol ({symbol}), defaulting to Alpaca Crypto")
                return DataSource.ALPACA_CRYPTO

        logger.info("🔍 Stock symbol detected, using Alpaca Stock")
        return DataSource.ALPACA

    def resolve_lookback_days(self) -> int:
        """Map period string to days.

        Returns:
            Number of days to look back
        """
        period_to_days = {
            "1H": 1,      # Issue #42: 1 hour (use 1 day for API call, filter later)
            "2H": 1,      # Issue #42: 2 hours (use 1 day for API call, filter later)
            "4H": 1,      # Issue #42: 4 hours (use 1 day for API call, filter later)
            "8H": 1,      # Issue #42: 8 hours (use 1 day for API call, filter later)
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
        return period_to_days.get(self.parent.current_period, 30)

    def calculate_date_range(
        self,
        asset_class: AssetClass,
        lookback_days: int,
    ) -> tuple[datetime, datetime]:
        """Calculate start/end dates with market hours logic.

        For crypto: Simple lookback from now
        For stocks: Adjust for weekends and market hours

        Args:
            asset_class: Asset class enum value
            lookback_days: Number of days to look back

        Returns:
            Tuple of (start_date, end_date) in NY timezone
        """
        ny_tz = pytz.timezone('America/New_York')
        now_ny = datetime.now(ny_tz)
        end_date = now_ny

        # Crypto: 24/7 trading, simple lookback
        if asset_class == AssetClass.CRYPTO:
            start_date = end_date - timedelta(days=lookback_days)
            logger.info("Crypto asset: Using current time (24/7 trading)")
            return start_date, end_date

        # Stocks: Complex market hours logic
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

        # Weekend adjustments
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

        # Intraday period: Use full trading day (4:00-20:00 EST)
        if self.parent.current_period == "1D" and use_previous_trading_day:
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

    @staticmethod
    def bars_to_dataframe(bars) -> pd.DataFrame:
        """Convert bars to DataFrame.

        Args:
            bars: List of HistoricalBar objects

        Returns:
            DataFrame with timestamp index
        """
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
