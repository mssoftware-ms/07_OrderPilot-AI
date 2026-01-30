"""
Backtest Engine.

Executes generic JSON-based strategies against historical data.
"""

import logging
import time
import tracemalloc
from collections import defaultdict
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass

from .schema_types import TradingBotConfig, Condition, ConditionGroup, RegimeDef, StrategyDef, RiskSettings
from .data_loader import DataLoader
from .errors import DataLoadError, ConfigurationError, IndicatorError
from .types import Trade
from .phases import SetupPhase, SimulationPhase, TeardownPhase

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, enable_caching: bool = True, cache_max_size: int = 100):
        """Initialize BacktestEngine.

        Args:
            enable_caching: Enable indicator caching for performance (7.3.2)
            cache_max_size: Maximum number of cached indicator results
        """
        self.data_loader = DataLoader()
        self.indicators_cache = {}  # Cache computed indicators
        self.enable_caching = enable_caching
        self.cache_max_size = cache_max_size
        self.cache_hits = 0
        self.cache_misses = 0

        # Initialize phases
        self.setup_phase = SetupPhase(
            data_loader=self.data_loader,
            indicator_calculator=self._calculate_indicators
        )
        self.simulation_phase = SimulationPhase(
            regime_evaluator=self._evaluate_regimes,
            strategy_evaluator=self._evaluate_conditions
        )
        self.teardown_phase = TeardownPhase(
            stats_calculator=self._calculate_stats
        )

    def run(self, config: TradingBotConfig, symbol: str, start_date=None, end_date=None, initial_capital=10000.0, chart_data: pd.DataFrame = None, data_timeframe: str = None) -> Dict[str, Any]:
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


    def _calculate_indicators(self, df: pd.DataFrame, indicators: List, tf_suffix: str):
        """Calculate indicators using pandas_ta with caching (7.3.2).

        Columns will be named: "{indicator_id}_{field}" (e.g. "rsi14_value")
        If HTF, they get prefixed later.

        Args:
            df: DataFrame with OHLCV data
            indicators: List of indicator definitions
            tf_suffix: Timeframe suffix for cache key
        """
        for ind in indicators:
            # Generate cache key based on indicator params + data hash
            cache_key = self._get_indicator_cache_key(df, ind, tf_suffix)

            # Check cache
            if self.enable_caching and cache_key in self.indicators_cache:
                self.cache_hits += 1
                # Restore cached columns
                cached_columns = self.indicators_cache[cache_key]
                for col_name, col_data in cached_columns.items():
                    df[col_name] = col_data
                continue

            self.cache_misses += 1

            # Calculate indicator (store result for caching)
            calculated_columns = {}

            if ind.type.upper() == "RSI":
                length = ind.params.get("period", 14)
                # pandas_ta returns a Series
                rsi = ta.rsi(df['close'], length=length)
                col_name = f"{ind.id}_value"
                df[col_name] = rsi
                calculated_columns[col_name] = rsi.copy()  # Copy for cache

            elif ind.type.upper() == "SMA":
                length = ind.params.get("period", 14)
                sma = ta.sma(df['close'], length=length)
                col_name = f"{ind.id}_value"
                df[col_name] = sma
                calculated_columns[col_name] = sma.copy()

            elif ind.type.upper() == "ADX":
                length = ind.params.get("period", 14)
                # ADX returns a DataFrame [ADX, DMP, DMN]
                adx_df = ta.adx(df['high'], df['low'], df['close'], length=length)
                if adx_df is not None:
                    # Column names usually ADX_14, DMP_14, DMN_14
                    # Map to generic fields
                    col_name = f"{ind.id}_value"
                    df[col_name] = adx_df.iloc[:, 0]  # Main ADX
                    calculated_columns[col_name] = adx_df.iloc[:, 0].copy()

            # Add more indicators here as needed...

            # Cache the calculated columns
            if self.enable_caching and calculated_columns:
                # Evict oldest entry if cache is full
                if len(self.indicators_cache) >= self.cache_max_size:
                    oldest_key = next(iter(self.indicators_cache))
                    del self.indicators_cache[oldest_key]

                self.indicators_cache[cache_key] = calculated_columns

    def _get_indicator_cache_key(self, df: pd.DataFrame, ind: Any, tf_suffix: str) -> str:
        """Generate cache key for indicator calculation (7.3.2).

        Args:
            df: DataFrame with OHLCV data
            ind: Indicator definition
            tf_suffix: Timeframe suffix

        Returns:
            Unique cache key string
        """
        import hashlib
        import json

        # Create key from indicator params + data characteristics
        key_data = {
            'indicator_id': ind.id,
            'indicator_type': ind.type,
            'params': ind.params,
            'timeframe': tf_suffix,
            'data_len': len(df),
            'data_start': str(df.index[0]) if len(df) > 0 else '',
            'data_end': str(df.index[-1]) if len(df) > 0 else '',
            # Hash of first/last few rows for uniqueness
            'data_hash': hashlib.md5(
                f"{df.head(5).to_json()}{df.tail(5).to_json()}".encode()
            ).hexdigest()[:8]
        }

        # Generate deterministic key
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _evaluate_regimes(self, regimes: List[RegimeDef], row: pd.Series, indicators: List) -> List[RegimeDef]:
        active = []
        for reg in regimes:
            if self._evaluate_conditions(reg.conditions, row, indicators):
                active.append(reg)
        return active


    def _evaluate_conditions(self, group: ConditionGroup, row: pd.Series, indicators: List) -> bool:
        if not group:
            return False
            
        # Evaluate 'all' (AND)
        if group.all:
            for cond in group.all:
                if not self._check_condition(cond, row, indicators):
                    return False
        
        # Evaluate 'any' (OR) - if 'any' exists, at least one must be true
        if group.any:
            if not any(self._check_condition(c, row, indicators) for c in group.any):
                return False
                
        return True

    def _check_condition(self, cond: Condition, row: pd.Series, indicators: List) -> bool:
        # Resolve Left
        left_val = self._resolve_operand(cond.left, row, indicators)
        
        # Resolve Right
        right_val = None
        right_min = None
        right_max = None
        
        if cond.op == "between":
            if cond.right.min is not None:
                right_min = cond.right.min
                right_max = cond.right.max
            else:
                # Could be dynamic between? Unlikely for min/max
                pass
        else:
            right_val = self._resolve_operand(cond.right, row, indicators)
            
        if left_val is None: return False
        
        # Comparison
        if cond.op == "gt":
            return left_val > right_val
        elif cond.op == "lt":
            return left_val < right_val
        elif cond.op == "eq":
            return left_val == right_val
        elif cond.op == "between":
            return right_min <= left_val <= right_max
            
        return False

    def _resolve_operand(self, op, row: pd.Series, indicators: List) -> float:
        if op.value is not None:
            return op.value
        
        if op.indicator_id:
            # Find indicator definition to get timeframe
            ind_def = next((i for i in indicators if i.id == op.indicator_id), None)
            col_name = f"{op.indicator_id}_{op.field}"
            
            if ind_def and ind_def.timeframe and ind_def.timeframe != "1m":
                # It's an HTF indicator, so it has a prefix in the combined_df
                col_name = f"{ind_def.timeframe}_{op.indicator_id}_{op.field}"
            
            val = row.get(col_name)
            if pd.isna(val):
                return None
            return float(val)
            
        return None

    def _calculate_stats(self, trades: List[Trade], initial_capital: float, final_equity: float, regime_history: List[Dict[str, Any]], data_timeframe: str = None, start_date=None, end_date=None, total_candles: int = 0) -> Dict[str, Any]:
        # Build data source metadata
        data_source_metadata = {
            "timeframe": data_timeframe or "1m",
            "start_date": start_date.strftime("%Y-%m-%d %H:%M") if start_date else "Unknown",
            "end_date": end_date.strftime("%Y-%m-%d %H:%M") if end_date else "Unknown",
            "total_candles": total_candles,
            "source": "Chart Data" if data_timeframe else "Database/API"
        }

        if not trades:
            return {
                "total_trades": 0,
                "net_profit": 0.0,
                "win_rate": 0.0,
                "final_equity": final_equity,
                "trades": [],
                "regime_history": regime_history,
                "data_source": data_source_metadata
            }
            
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        
        # Convert trades to dicts for UI
        trade_list = []
        for t in trades:
            trade_list.append({
                "entry_time": t.entry_time.strftime("%Y-%m-%d %H:%M"),
                "exit_time": t.exit_time.strftime("%Y-%m-%d %H:%M") if t.exit_time else "OPEN",
                "side": t.side,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "reason": t.exit_reason
            })

        return {
            "total_trades": len(trades),
            "net_profit": final_equity - initial_capital,
            "net_profit_pct": (final_equity - initial_capital) / initial_capital,
            "win_rate": len(wins) / len(trades),
            "final_equity": final_equity,
            "max_drawdown": 0.0, # TODO: implement
            "profit_factor": (sum(t.pnl for t in wins) / abs(sum(t.pnl for t in losses))) if losses else float('inf'),
            "trades": trade_list,
            "regime_history": regime_history,
            "data_source": data_source_metadata
        }
