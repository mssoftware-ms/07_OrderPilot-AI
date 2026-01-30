"""
Refactored run() method for BacktestEngine.

This is the new phase-based implementation with CC < 10.
"""

from typing import Dict, Any
import pandas as pd


def run_refactored(
    self,
    config,
    symbol: str,
    start_date=None,
    end_date=None,
    initial_capital=10000.0,
    chart_data: pd.DataFrame = None,
    data_timeframe: str = None
) -> Dict[str, Any]:
    """
    Run the backtest using phase-based execution.

    Args:
        config: Trading bot configuration
        symbol: Trading symbol
        start_date: Backtest start date (optional if chart_data provided)
        end_date: Backtest end date (optional if chart_data provided)
        initial_capital: Starting capital
        chart_data: Pre-loaded chart data (DataFrame with OHLCV)
        data_timeframe: Timeframe of chart_data (e.g., "15m", "1h")

    Returns:
        Dictionary with backtest results
    """
    # Phase 1: Setup
    setup_result = self.setup_phase.execute(
        config=config,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        chart_data=chart_data,
        data_timeframe=data_timeframe
    )

    # Check for setup errors
    if "error" in setup_result:
        return setup_result

    # Phase 2: Simulation
    simulation_result = self.simulation_phase.execute(
        datasets=setup_result['datasets'],
        config=config,
        symbol=symbol,
        initial_capital=initial_capital,
        perf_counters=setup_result['perf_counters']
    )

    # Update timings
    setup_result['perf_timings']['simulation_loop'] = simulation_result['phase_timing']

    # Phase 3: Teardown
    final_result = self.teardown_phase.execute(
        trades=simulation_result['trades'],
        initial_capital=initial_capital,
        final_equity=simulation_result['final_equity'],
        regime_history=simulation_result['regime_history'],
        datasets=setup_result['datasets'],
        combined_df=simulation_result['combined_df'],
        perf_timings=setup_result['perf_timings'],
        perf_counters=setup_result['perf_counters'],
        mem_start=setup_result['mem_start'],
        cache_hits=self.cache_hits,
        cache_misses=self.cache_misses,
        cache_size=len(self.indicators_cache),
        cache_max_size=self.cache_max_size,
        enable_caching=self.enable_caching,
        data_timeframe=data_timeframe,
        start_date=setup_result['start_date'],
        end_date=setup_result['end_date'],
        total_candles=setup_result['total_candles']
    )

    return final_result
