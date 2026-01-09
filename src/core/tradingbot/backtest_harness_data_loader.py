"""Backtest Harness Data Loader - Historical Data Loading.

Refactored from backtest_harness.py.

Contains:
- load_data: Load historical data for backtest using data provider or default HistoryManager
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .backtest_harness import BacktestHarness

logger = logging.getLogger(__name__)


class BacktestHarnessDataLoader:
    """Helper for loading historical data."""

    def __init__(self, parent: "BacktestHarness"):
        self.parent = parent

    def load_data(self) -> pd.DataFrame:
        """Load historical data for backtest.

        Returns:
            DataFrame with OHLCV data
        """
        if self.parent._data_provider:
            self.parent._data = self.parent._data_provider(
                self.parent.backtest_config.symbol,
                self.parent.backtest_config.start_date,
                self.parent.backtest_config.end_date,
                self.parent.backtest_config.timeframe
            )
        else:
            # Try to load from default provider
            try:
                from src.core.market_data.history_provider import HistoryManager
                from src.core.market_data.types import DataRequest, Timeframe, AssetClass

                manager = HistoryManager()
                request = DataRequest(
                    symbol=self.parent.backtest_config.symbol,
                    start_date=self.parent.backtest_config.start_date,
                    end_date=self.parent.backtest_config.end_date,
                    timeframe=Timeframe.MINUTE_1,
                    asset_class=AssetClass.STOCK
                )
                self.parent._data = manager.fetch_data(request)
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
                raise ValueError(f"No data provider and default load failed: {e}")

        if self.parent._data is None or self.parent._data.empty:
            raise ValueError("No data loaded for backtest")

        logger.info(f"Loaded {len(self.parent._data)} bars for backtest")
        return self.parent._data
