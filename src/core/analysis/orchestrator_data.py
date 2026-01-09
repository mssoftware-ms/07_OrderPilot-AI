"""Orchestrator Data - Data collection and conversion.

Refactored from 666 LOC monolith using composition pattern.

Module 2/6 of orchestrator.py split.

Contains:
- collect_data(): Fetch data for all timeframes
- bars_to_dataframe(): Convert bars to DataFrame
- map_timeframe(): Map string to Timeframe enum
- get_duration_minutes(): Calculate duration for lookback
"""

from __future__ import annotations

import logging
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.market_data.types import DataRequest, Timeframe

logger = logging.getLogger(__name__)


class OrchestratorData:
    """Helper für AnalysisWorker data collection."""

    def __init__(self, parent):
        """
        Args:
            parent: AnalysisWorker Instanz
        """
        self.parent = parent

    async def collect_data(self, tfs: list, symbol: str, hm) -> dict[str, pd.DataFrame]:
        """Collect data for all configured timeframes.

        Args:
            tfs: List of TimeframeConfig objects
            symbol: Trading symbol
            hm: HistoryManager instance

        Returns:
            Dict mapping timeframe string to DataFrame
        """
        from src.core.market_data.types import DataRequest

        fetched_data = {}
        total_steps = len(tfs)

        for i, tf_config in enumerate(tfs):
            self.parent.status_update.emit(f"Lade {tf_config.tf} ({tf_config.role})...")

            # Resolve timeframe enum
            tf_enum = self.map_timeframe(tf_config.tf)

            # Calculate dates
            duration_min = self.get_duration_minutes(tf_config.tf)
            total_minutes = tf_config.lookback * duration_min * 1.5  # Buffer

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(minutes=total_minutes)

            # Fetch
            request = DataRequest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=tf_enum,
                asset_class=self.parent.context.asset_class,
                source=self.parent.context.data_source
            )

            # Async call
            bars, source = await hm.fetch_data(request)

            if not bars:
                logger.warning(f"No data for {tf_config.tf}")
                continue

            # Convert to DataFrame
            df = self.bars_to_dataframe(bars)
            fetched_data[tf_config.tf] = df

            # Update Progress (10% to 60%)
            progress = 10 + int((i + 1) / total_steps * 50)
            self.parent.progress_update.emit(progress)

        return fetched_data

    @staticmethod
    def bars_to_dataframe(bars) -> pd.DataFrame:
        """Convert bars to DataFrame.

        Args:
            bars: List of HistoricalBar objects

        Returns:
            DataFrame with time index
        """
        data = []
        for bar in bars:
            data.append({
                'time': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': float(bar.volume)
            })
        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index('time', inplace=True)
        return df

    @staticmethod
    def map_timeframe(tf_str: str) -> "Timeframe":
        """Maps config string (1m, 1h) to Timeframe enum.

        Args:
            tf_str: Timeframe string (1m, 5m, 1h, etc.)

        Returns:
            Timeframe enum value
        """
        from src.core.market_data.types import Timeframe

        mapping = {
            "1m": Timeframe.MINUTE_1,
            "5m": Timeframe.MINUTE_5,
            "15m": Timeframe.MINUTE_15,
            "30m": Timeframe.MINUTE_30,
            "1h": Timeframe.HOUR_1,
            "4h": Timeframe.HOUR_4,
            "1D": Timeframe.DAY_1,
            "1W": Timeframe.WEEK_1,
            "1M": Timeframe.MONTH_1,
        }
        return mapping.get(tf_str, Timeframe.MINUTE_1)  # Fallback

    @staticmethod
    def get_duration_minutes(tf_str: str) -> int:
        """Helper to calculate lookback duration.

        Args:
            tf_str: Timeframe string (1m, 1h, etc.)

        Returns:
            Number of minutes per bar
        """
        if "m" in tf_str:
            return int(tf_str.replace("m", ""))
        if "h" in tf_str:
            return int(tf_str.replace("h", "")) * 60
        if "D" in tf_str:
            return 1440
        if "W" in tf_str:
            return 10080
        if "M" in tf_str:
            return 43200
        return 1
