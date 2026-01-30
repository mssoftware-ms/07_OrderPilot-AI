"""
Teardown Phase - Cleanup and Results.

Handles:
- Memory cleanup
- Statistics calculation
- Performance metrics finalization
"""

import time
import tracemalloc
from typing import Dict, List, Any
import logging

from ..types import Trade

logger = logging.getLogger(__name__)


class TeardownPhase:
    """Teardown phase for backtest execution."""

    def __init__(self, stats_calculator):
        """Initialize teardown phase.

        Args:
            stats_calculator: Function to calculate statistics
        """
        self.stats_calculator = stats_calculator

    def execute(
        self,
        trades: List[Trade],
        initial_capital: float,
        final_equity: float,
        regime_history: List[Dict[str, Any]],
        datasets: Dict,
        combined_df,
        perf_timings: Dict[str, float],
        perf_counters: Dict[str, int],
        mem_start: int,
        cache_hits: int,
        cache_misses: int,
        cache_size: int,
        cache_max_size: int,
        enable_caching: bool,
        data_timeframe: str,
        start_date,
        end_date,
        total_candles: int
    ) -> Dict[str, Any]:
        """Execute teardown phase.

        Args:
            trades: List of completed trades
            initial_capital: Starting capital
            final_equity: Final equity
            regime_history: List of regime changes
            datasets: Dict of timeframe datasets
            combined_df: Combined DataFrame
            perf_timings: Performance timings dict
            perf_counters: Performance counters dict
            mem_start: Starting memory
            cache_hits: Cache hit count
            cache_misses: Cache miss count
            cache_size: Current cache size
            cache_max_size: Maximum cache size
            enable_caching: Whether caching is enabled
            data_timeframe: Data timeframe
            start_date: Start date
            end_date: End date
            total_candles: Total candles processed

        Returns:
            Complete backtest results dictionary
        """
        phase_start = time.time()

        # Memory cleanup
        del combined_df
        for tf in list(datasets.keys()):
            del datasets[tf]
        datasets.clear()

        # Calculate statistics
        stats_result = self.stats_calculator(
            trades, initial_capital, final_equity,
            regime_history, data_timeframe,
            start_date, end_date, total_candles
        )

        perf_timings['stats_calculation'] = time.time() - phase_start

        # Finalize memory tracking
        mem_current, mem_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Add performance metrics
        cache_hit_rate = (
            cache_hits / (cache_hits + cache_misses)
            if (cache_hits + cache_misses) > 0
            else 0
        )

        stats_result['performance'] = {
            'timings': perf_timings,
            'counters': dict(perf_counters),
            'memory': {
                'start_mb': mem_start / 1024 / 1024,
                'current_mb': mem_current / 1024 / 1024,
                'peak_mb': mem_peak / 1024 / 1024,
                'delta_mb': (mem_current - mem_start) / 1024 / 1024
            },
            'rates': {
                'candles_per_sec': (
                    perf_counters['total_candles_processed'] /
                    perf_timings.get('simulation_loop', 1)
                    if perf_timings.get('simulation_loop', 0) > 0
                    else 0
                ),
                'regime_evals_per_sec': (
                    perf_counters['regime_evaluations'] /
                    perf_timings.get('simulation_loop', 1)
                    if perf_timings.get('simulation_loop', 0) > 0
                    else 0
                )
            },
            'cache': {
                'enabled': enable_caching,
                'hits': cache_hits,
                'misses': cache_misses,
                'hit_rate': cache_hit_rate,
                'size': cache_size,
                'max_size': cache_max_size
            }
        }

        total_execution = sum(perf_timings.values())
        perf_timings['total_execution'] = total_execution

        logger.info(
            f"Backtest completed in {total_execution:.2f}s "
            f"({perf_counters['total_candles_processed']} candles, "
            f"{perf_counters.get('trades_entered', 0)} trades)"
        )

        return stats_result
