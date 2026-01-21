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
from .errors import DataLoadError, ConfigurationError, IndicatorError, format_error_for_ui

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    entry_time: pd.Timestamp
    entry_price: float
    side: str # 'long' or 'short'
    size: float
    exit_time: pd.Timestamp = None
    exit_price: float = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""

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

    def run(self, config: TradingBotConfig, symbol: str, start_date=None, end_date=None, initial_capital=10000.0, chart_data: pd.DataFrame = None, data_timeframe: str = None) -> Dict[str, Any]:
        """
        Run the backtest.

        Args:
            config: Trading bot configuration
            symbol: Trading symbol
            start_date: Backtest start date (optional if chart_data provided)
            end_date: Backtest end date (optional if chart_data provided)
            initial_capital: Starting capital
            chart_data: Pre-loaded chart data (DataFrame with OHLCV) - if provided, skips database loading
            data_timeframe: Timeframe of chart_data (e.g., "15m", "1h") - for documentation purposes
        """
        # Performance profiling setup (7.3.1)
        perf_start = time.time()
        perf_timings = {}
        perf_counters = defaultdict(int)

        # Start memory tracking
        tracemalloc.start()
        mem_start = tracemalloc.get_traced_memory()[0]

        # 1. Load Data (1m base or use chart data)
        phase_start = time.time()
        if chart_data is not None and not chart_data.empty:
            # Use pre-loaded chart data
            df_1m = chart_data.copy()
            logger.info(f"Using pre-loaded chart data: {len(df_1m)} candles, timeframe={data_timeframe or 'unknown'}")

            # Extract date range from chart data
            if not start_date:
                start_date = df_1m.index[0]
            if not end_date:
                end_date = df_1m.index[-1]
        else:
            # Fallback to database/API loading
            df_1m = self.data_loader.load_data(symbol, start_date, end_date)
            if df_1m.empty:
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

        # 2. Determine required timeframes from indicators
        phase_start = time.time()
        required_timeframes = set()
        for ind in config.indicators:
            tf = ind.timeframe or "1m" # Default to 1m if not specified
            required_timeframes.add(tf)

        # 2.5. Validate chart data timeframe compatibility
        if data_timeframe and chart_data is not None:
            # Check if any required timeframe is smaller than chart timeframe
            # (Downsampling is not possible: cannot create 5m from 15m data)
            chart_tf_minutes = self._timeframe_to_minutes(data_timeframe)
            for req_tf in required_timeframes:
                req_tf_minutes = self._timeframe_to_minutes(req_tf)
                if req_tf_minutes < chart_tf_minutes:
                    error = DataLoadError.timeframe_incompatible(
                        chart_tf=data_timeframe,
                        required_tf=req_tf
                    )
                    logger.error(str(error))
                    return {"error": str(error)}

        # Always ensure we have the execution timeframe (e.g. 1m or higher)
        # For simplicity, we execute on the lowest granularity available (1m) but evaluate higher TFs

        # 3. Resample & Calculate Indicators
        datasets = {}
        base_timeframe = data_timeframe if data_timeframe else "1m"

        for tf in required_timeframes:
            if tf == base_timeframe:
                # Use base data directly (either 1m from DB/API or chart timeframe)
                df_tf = df_1m.copy()
            else:
                # Resample to higher timeframe
                df_tf = self.data_loader.resample_data(df_1m, tf)
            
            # Calculate indicators for this timeframe
            self._calculate_indicators(df_tf, config.indicators, tf)
            datasets[tf] = df_tf

        perf_timings['indicator_calculation'] = time.time() - phase_start
        perf_counters['indicators_calculated'] = len(config.indicators)
        perf_counters['timeframes_processed'] = len(required_timeframes)

        # 4. Simulation Loop
        phase_start = time.time()
        # We iterate over the 1m dataframe (the base execution timeline)
        # For HTF indicators, we assume we know the value of the LAST closed candle of that timeframe
        # relative to the current 1m time.
        
        # To make it efficient: Merge all indicators into one big DF or look them up.
        # Merging is safer for vectorization, but we need event-driven for complex regimes.
        # Let's do an event-driven loop on the 1m candles for accuracy.
        
        trades: List[Trade] = []
        active_trade: Trade = None
        equity = initial_capital

        # Track regime changes for visualization
        regime_history: List[Dict[str, Any]] = []
        prev_regime_ids: List[str] = []

        # Pre-align data to 1m index (forward fill HTF data)
        combined_df = df_1m.copy()
        
        for tf, df_tf in datasets.items():
            if tf == "1m":
                continue
            
            # Prefix columns
            df_tf_renamed = df_tf.add_prefix(f"{tf}_")
            
            # Reindex to 1m (ffill)
            # Use asof merge or reindex
            aligned = df_tf_renamed.reindex(combined_df.index, method='ffill')
            combined_df = pd.concat([combined_df, aligned], axis=1)

        # Import RegimeEngine for fallback regime detection
        from src.core.tradingbot.regime_engine import RegimeEngine, FeatureVector
        regime_engine = RegimeEngine()

        # Iterate rows
        for i in range(len(combined_df)):
            row = combined_df.iloc[i]
            timestamp = combined_df.index[i]

            # 1. Determine Active Regimes
            regime_eval_start = time.time()
            active_regimes = self._evaluate_regimes(config.regimes, row, config.indicators)
            regime_ids = [r.id for r in active_regimes]
            perf_counters['regime_evaluations'] += 1

            # FALLBACK: If no JSON regimes defined or no regimes active, use RegimeEngine
            if not regime_ids and len(row) >= 5:
                try:
                    # Convert pandas Timestamp to Python datetime if needed
                    from datetime import datetime
                    if hasattr(timestamp, 'to_pydatetime'):
                        dt_timestamp = timestamp.to_pydatetime()
                    elif isinstance(timestamp, datetime):
                        dt_timestamp = timestamp
                    else:
                        dt_timestamp = datetime.now()

                    # Build FeatureVector from row data
                    # Note: This requires OHLCV + indicators to be present
                    feature_vector = FeatureVector(
                        timestamp=dt_timestamp,
                        symbol=symbol,
                        close=float(row.get('close', 0)),
                        high=float(row.get('high', 0)),
                        low=float(row.get('low', 0)),
                        open=float(row.get('open', 0)),
                        volume=float(row.get('volume', 0)),
                        # Try to get indicators from row (RSI, MACD, etc.)
                        rsi=float(row.get('rsi14_value', row.get('1m_rsi14_value', 50))),
                        macd_line=float(row.get('macd12_26_value', row.get('1m_macd12_26_value', 0))),
                        macd_signal=float(row.get('macd12_26_signal', row.get('1m_macd12_26_signal', 0))),
                        adx=float(row.get('adx14_value', row.get('1m_adx14_value', 25))),
                        atr=float(row.get('atr14_value', row.get('1m_atr14_value', 0)))
                    )

                    # Classify regime
                    regime_state = regime_engine.classify(feature_vector)

                    # Create synthetic regime IDs from RegimeEngine result
                    regime_ids = [
                        f"regime_{regime_state.regime.name.lower()}",
                        f"volatility_{regime_state.volatility.name.lower()}"
                    ]

                    # Create regime objects for visualization
                    active_regimes = [
                        type('Regime', (), {
                            'id': f"regime_{regime_state.regime.name.lower()}",
                            'name': regime_state.regime.name
                        })(),
                        type('Regime', (), {
                            'id': f"volatility_{regime_state.volatility.name.lower()}",
                            'name': f"Volatility: {regime_state.volatility.name}"
                        })()
                    ]
                except Exception as e:
                    logger.debug(f"Fallback regime detection failed at {timestamp}: {e}")
                    regime_ids = []

            # Track regime changes for visualization
            if regime_ids != prev_regime_ids:
                regime_history.append({
                    'timestamp': timestamp,
                    'regime_ids': regime_ids.copy(),
                    'regimes': [{'id': r.id, 'name': r.name} for r in active_regimes]
                })
                prev_regime_ids = regime_ids.copy()

            # 2. Routing -> Strategy Set
            active_strategy_set_id = self._route_regimes(config.routing, regime_ids)
            perf_counters['strategy_routings'] += 1
            if not active_strategy_set_id:
                continue # No strategy active
                
            strategy_set = next((s for s in config.strategy_sets if s.id == active_strategy_set_id), None)
            if not strategy_set:
                continue

            # 3. Evaluate Strategies in Set
            for strat_ref in strategy_set.strategies:
                strategy_def = next((s for s in config.strategies if s.id == strat_ref.strategy_id), None)
                if not strategy_def:
                    continue
                
                # Apply Overrides (Merging logic simplified here)
                # Note: Real implementation needs deep merge of overrides
                
                current_risk = strategy_def.risk
                if strat_ref.strategy_overrides and strat_ref.strategy_overrides.risk:
                    current_risk = strat_ref.strategy_overrides.risk # Simple replacement

                # Entry Logic
                if active_trade is None:
                    perf_counters['entry_evaluations'] += 1
                    if self._evaluate_conditions(strategy_def.entry, row, config.indicators):
                        # Enter Trade
                        perf_counters['trades_entered'] += 1
                        price = row['close']
                        size = (equity * (current_risk.risk_per_trade_pct or 1.0) / 100.0) / price # Simplified sizing
                        # Apply Fee?
                        
                        active_trade = Trade(
                            entry_time=timestamp,
                            entry_price=price,
                            side='long', # Assuming long only for MVP unless logic defines side
                            size=size
                        )
                        # logger.debug(f"Entered Long at {price} on {timestamp}")

                # Exit Logic (if in trade)
                elif active_trade:
                    perf_counters['exit_evaluations'] += 1
                    # Check SL/TP
                    price = row['close']
                    
                    # Stop Loss
                    sl_hit = False
                    if current_risk and current_risk.stop_loss_pct:
                        sl_price = active_trade.entry_price * (1 - current_risk.stop_loss_pct / 100.0)
                        if row['low'] <= sl_price: # Check low for SL hit
                            active_trade.exit_price = sl_price
                            active_trade.exit_reason = "SL"
                            sl_hit = True
                    
                    # Take Profit
                    tp_hit = False
                    if not sl_hit and current_risk and current_risk.take_profit_pct:
                        tp_price = active_trade.entry_price * (1 + current_risk.take_profit_pct / 100.0)
                        if row['high'] >= tp_price: # Check high for TP hit
                            active_trade.exit_price = tp_price
                            active_trade.exit_reason = "TP"
                            tp_hit = True
                            
                    # Strategy Exit Signal
                    signal_exit = False
                    if not sl_hit and not tp_hit and strategy_def.exit:
                        if self._evaluate_conditions(strategy_def.exit, row, config.indicators):
                            active_trade.exit_price = price
                            active_trade.exit_reason = "Signal"
                            signal_exit = True
                            
                    if sl_hit or tp_hit or signal_exit:
                        active_trade.exit_time = timestamp
                        active_trade.pnl = (active_trade.exit_price - active_trade.entry_price) * active_trade.size
                        active_trade.pnl_pct = (active_trade.exit_price - active_trade.entry_price) / active_trade.entry_price
                        trades.append(active_trade)
                        equity += active_trade.pnl
                        active_trade = None

        perf_timings['simulation_loop'] = time.time() - phase_start
        perf_counters['total_candles_processed'] = len(combined_df)

        # Memory optimization: Clear large intermediate DataFrames (7.3.2)
        del combined_df
        for tf in list(datasets.keys()):
            del datasets[tf]
        datasets.clear()

        # Calculate stats
        phase_start = time.time()
        stats_result = self._calculate_stats(trades, initial_capital, equity, regime_history, data_timeframe, start_date, end_date, len(df_1m))
        perf_timings['stats_calculation'] = time.time() - phase_start

        # Finalize performance metrics
        perf_timings['total_execution'] = time.time() - perf_start
        mem_current, mem_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Add performance data to results
        cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0

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
                'candles_per_sec': perf_counters['total_candles_processed'] / perf_timings['simulation_loop'] if perf_timings['simulation_loop'] > 0 else 0,
                'regime_evals_per_sec': perf_counters['regime_evaluations'] / perf_timings['simulation_loop'] if perf_timings['simulation_loop'] > 0 else 0
            },
            'cache': {
                'enabled': self.enable_caching,
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': cache_hit_rate,
                'size': len(self.indicators_cache),
                'max_size': self.cache_max_size
            }
        }

        logger.info(f"Backtest completed in {perf_timings['total_execution']:.2f}s ({perf_counters['total_candles_processed']} candles, {perf_counters['trades_entered']} trades)")

        return stats_result

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes for comparison.

        Args:
            timeframe: e.g. "1m", "5m", "15m", "1h", "1d"

        Returns:
            Minutes as integer
        """
        tf_map = {
            '1m': 1,
            '3m': 3,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '2h': 120,
            '4h': 240,
            '6h': 360,
            '8h': 480,
            '12h': 720,
            '1d': 1440,
            '1w': 10080
        }
        return tf_map.get(timeframe, 1)  # Default to 1m if unknown

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

    def _route_regimes(self, routing: List, active_regime_ids: List[str]) -> str:
        for rule in routing:
            match = True
            
            # Check all_of
            if rule.match.all_of:
                for req in rule.match.all_of:
                    if req not in active_regime_ids:
                        match = False
                        break
            if not match: continue
            
            # Check any_of
            if rule.match.any_of:
                if not any(r in active_regime_ids for r in rule.match.any_of):
                    match = False
            if not match: continue
            
            # Check none_of
            if rule.match.none_of:
                if any(r in active_regime_ids for r in rule.match.none_of):
                    match = False
            
            if match:
                return rule.strategy_set_id
        return None

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
