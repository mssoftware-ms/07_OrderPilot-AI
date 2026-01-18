"""
Backtest Engine.

Executes generic JSON-based strategies against historical data.
"""

import logging
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass

from .schema_types import TradingBotConfig, Condition, ConditionGroup, RegimeDef, StrategyDef, RiskSettings
from .data_loader import DataLoader

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
    def __init__(self):
        self.data_loader = DataLoader()
        self.indicators_cache = {} # Cache computed indicators

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
        # 1. Load Data (1m base or use chart data)
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
                error_msg = (
                    f"No data found for symbol '{symbol}'\n\n"
                    f"Database: {self.data_loader.db_path}\n"
                    f"Date range: {start_date} to {end_date}\n\n"
                    f"Suggestions:\n"
                    f"1. Check if symbol format is correct (try 'bitunix:BTCUSDT' or 'BTCUSDT')\n"
                    f"2. Verify data exists in the database for this date range\n"
                    f"3. Check database health (main DB might be corrupted)"
                )
                logger.error(error_msg)
                return {"error": error_msg}

        # 2. Determine required timeframes from indicators
        required_timeframes = set()
        for ind in config.indicators:
            tf = ind.timeframe or "1m" # Default to 1m if not specified
            required_timeframes.add(tf)
        
        # Always ensure we have the execution timeframe (e.g. 1m or higher)
        # For simplicity, we execute on the lowest granularity available (1m) but evaluate higher TFs
        
        # 3. Resample & Calculate Indicators
        datasets = {}
        for tf in required_timeframes:
            if tf == "1m":
                df_tf = df_1m.copy()
            else:
                df_tf = self.data_loader.resample_data(df_1m, tf)
            
            # Calculate indicators for this timeframe
            self._calculate_indicators(df_tf, config.indicators, tf)
            datasets[tf] = df_tf

        # 4. Simulation Loop
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

        # Iterate rows
        for i in range(len(combined_df)):
            row = combined_df.iloc[i]
            timestamp = combined_df.index[i]
            
            # 1. Determine Active Regimes
            active_regimes = self._evaluate_regimes(config.regimes, row, config.indicators)
            regime_ids = [r.id for r in active_regimes]

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
                    if self._evaluate_conditions(strategy_def.entry, row, config.indicators):
                        # Enter Trade
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

        return self._calculate_stats(trades, initial_capital, equity, regime_history, data_timeframe, start_date, end_date, len(df_1m))

    def _calculate_indicators(self, df: pd.DataFrame, indicators: List, tf_suffix: str):
        """
        Calculate indicators using pandas_ta and append to df.
        Columns will be named: "{indicator_id}_{field}" (e.g. "rsi14_value")
        If HTF, they get prefixed later.
        """
        for ind in indicators:
            if ind.type.upper() == "RSI":
                length = ind.params.get("period", 14)
                # pandas_ta returns a Series
                rsi = ta.rsi(df['close'], length=length)
                df[f"{ind.id}_value"] = rsi
                
            elif ind.type.upper() == "SMA":
                length = ind.params.get("period", 14)
                sma = ta.sma(df['close'], length=length)
                df[f"{ind.id}_value"] = sma
                
            elif ind.type.upper() == "ADX":
                length = ind.params.get("period", 14)
                # ADX returns a DataFrame [ADX, DMP, DMN]
                adx_df = ta.adx(df['high'], df['low'], df['close'], length=length)
                if adx_df is not None:
                    # Column names usually ADX_14, DMP_14, DMN_14
                    # Map to generic fields
                    df[f"{ind.id}_value"] = adx_df.iloc[:, 0] # Main ADX
            
            # Add more indicators here as needed...

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
