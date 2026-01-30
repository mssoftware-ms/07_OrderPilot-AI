"""
Setup Phase - Data Loading and Preparation.

Handles:
- Performance tracking initialization
- Data loading/validation
- Timeframe validation
- Indicator calculation
"""

import time
import tracemalloc
from collections import defaultdict
from typing import Dict, Any, Set
import pandas as pd
import logging

from ..schema_types import TradingBotConfig
from ..data_loader import DataLoader
from ..errors import DataLoadError

logger = logging.getLogger(__name__)


class SetupPhase:
    """Setup phase for backtest execution."""

    def __init__(self, data_loader: DataLoader, indicator_calculator):
        """Initialize setup phase.

        Args:
            data_loader: DataLoader instance
            indicator_calculator: Function to calculate indicators
        """
        self.data_loader = data_loader
        self.indicator_calculator = indicator_calculator

    def execute(
        self,
        config: TradingBotConfig,
        symbol: str,
        start_date,
        end_date,
        chart_data: pd.DataFrame = None,
        data_timeframe: str = None
    ) -> Dict[str, Any]:
        """Execute setup phase.

        Args:
            config: Trading bot configuration
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            chart_data: Pre-loaded chart data (optional)
            data_timeframe: Timeframe of chart data

        Returns:
            Dictionary with setup results:
            - datasets: Dict[timeframe, DataFrame]
            - perf_timings: Dict[phase, time]
            - perf_counters: Dict[metric, count]
            - mem_start: Memory at start
            - base_timeframe: Base timeframe used
            - error: Error message if failed (optional)
        """
        # Performance profiling setup
        perf_start = time.time()
        perf_timings = {}
        perf_counters = defaultdict(int)

        # Start memory tracking
        tracemalloc.start()
        mem_start = tracemalloc.get_traced_memory()[0]

        # 1. Load Data
        phase_start = time.time()
        df_1m, actual_start, actual_end = self._load_data(
            symbol, start_date, end_date, chart_data, data_timeframe
        )

        if df_1m is None:
            error = DataLoadError.no_data_found(
                symbol=symbol,
                start_date=str(start_date),
                end_date=str(end_date),
                db_path=str(self.data_loader.db_path)
            )
            logger.error(str(error))
            return {"error": str(error)}

        perf_timings['data_loading'] = time.time() - phase_start
        perf_counters['candles_loaded'] = len(df_1m)

        # 2. Determine Required Timeframes
        phase_start = time.time()
        required_timeframes = self._get_required_timeframes(config)

        # 3. Validate Timeframe Compatibility
        if data_timeframe and chart_data is not None:
            error = self._validate_timeframes(data_timeframe, required_timeframes)
            if error:
                logger.error(str(error))
                return {"error": str(error)}

        # 4. Calculate Indicators for All Timeframes
        base_timeframe = data_timeframe if data_timeframe else "1m"
        datasets = self._calculate_all_indicators(
            df_1m, base_timeframe, required_timeframes, config
        )

        perf_timings['indicator_calculation'] = time.time() - phase_start
        perf_counters['indicators_calculated'] = len(config.indicators)
        perf_counters['timeframes_processed'] = len(required_timeframes)

        return {
            'datasets': datasets,
            'perf_timings': perf_timings,
            'perf_counters': perf_counters,
            'mem_start': mem_start,
            'base_timeframe': base_timeframe,
            'start_date': actual_start,
            'end_date': actual_end,
            'total_candles': len(df_1m)
        }

    def _load_data(
        self, symbol: str, start_date, end_date,
        chart_data: pd.DataFrame, data_timeframe: str
    ) -> tuple:
        """Load OHLCV data.

        Returns:
            Tuple of (DataFrame, actual_start, actual_end)
        """
        if chart_data is not None and not chart_data.empty:
            df_1m = chart_data.copy()
            logger.info(
                f"Using pre-loaded chart data: {len(df_1m)} candles, "
                f"timeframe={data_timeframe or 'unknown'}"
            )

            actual_start = df_1m.index[0] if not start_date else start_date
            actual_end = df_1m.index[-1] if not end_date else end_date

            return df_1m, actual_start, actual_end
        else:
            df_1m = self.data_loader.load_data(symbol, start_date, end_date)
            if df_1m.empty:
                return None, start_date, end_date

            return df_1m, start_date, end_date

    def _get_required_timeframes(self, config: TradingBotConfig) -> Set[str]:
        """Get all required timeframes from indicators.

        Args:
            config: Trading bot configuration

        Returns:
            Set of timeframe strings
        """
        required_timeframes = set()
        for ind in config.indicators:
            tf = ind.timeframe or "1m"
            required_timeframes.add(tf)
        return required_timeframes

    def _validate_timeframes(
        self, data_timeframe: str, required_timeframes: Set[str]
    ) -> Any:
        """Validate timeframe compatibility.

        Args:
            data_timeframe: Chart data timeframe
            required_timeframes: Required timeframes from indicators

        Returns:
            Error if incompatible, None otherwise
        """
        chart_tf_minutes = self._timeframe_to_minutes(data_timeframe)

        for req_tf in required_timeframes:
            req_tf_minutes = self._timeframe_to_minutes(req_tf)
            if req_tf_minutes < chart_tf_minutes:
                return DataLoadError.timeframe_incompatible(
                    chart_tf=data_timeframe,
                    required_tf=req_tf
                )

        return None

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes.

        Args:
            timeframe: e.g. "1m", "5m", "15m", "1h", "1d"

        Returns:
            Minutes as integer
        """
        tf_map = {
            '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360,
            '8h': 480, '12h': 720, '1d': 1440, '1w': 10080
        }
        return tf_map.get(timeframe, 1)

    def _calculate_all_indicators(
        self,
        df_1m: pd.DataFrame,
        base_timeframe: str,
        required_timeframes: Set[str],
        config: TradingBotConfig
    ) -> Dict[str, pd.DataFrame]:
        """Calculate indicators for all timeframes.

        Args:
            df_1m: Base OHLCV data
            base_timeframe: Base timeframe
            required_timeframes: Set of required timeframes
            config: Trading bot configuration

        Returns:
            Dict mapping timeframe to DataFrame with indicators
        """
        datasets = {}

        for tf in required_timeframes:
            if tf == base_timeframe:
                df_tf = df_1m.copy()
            else:
                df_tf = self.data_loader.resample_data(df_1m, tf)

            # Calculate indicators for this timeframe
            self.indicator_calculator(df_tf, config.indicators, tf)
            datasets[tf] = df_tf

        return datasets
