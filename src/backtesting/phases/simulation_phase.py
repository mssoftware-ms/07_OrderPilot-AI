"""
Simulation Phase - Main Trading Logic.

Handles:
- Regime evaluation and routing
- Strategy evaluation
- Trade entry/exit logic
- Position management
"""

import time
from collections import defaultdict
from typing import Dict, List, Any
import pandas as pd
import logging

from ..schema_types import TradingBotConfig, RegimeDef, StrategyDef
from ..types import Trade

logger = logging.getLogger(__name__)


class SimulationPhase:
    """Simulation phase for backtest execution."""

    def __init__(self, regime_evaluator, strategy_evaluator):
        """Initialize simulation phase.

        Args:
            regime_evaluator: Function to evaluate regimes
            strategy_evaluator: Strategy evaluation logic
        """
        self.regime_evaluator = regime_evaluator
        self.strategy_evaluator = strategy_evaluator

    def execute(
        self,
        datasets: Dict[str, pd.DataFrame],
        config: TradingBotConfig,
        symbol: str,
        initial_capital: float,
        perf_counters: Dict[str, int]
    ) -> Dict[str, Any]:
        """Execute simulation phase.

        Args:
            datasets: Dict of timeframe -> DataFrame
            config: Trading bot configuration
            symbol: Trading symbol
            initial_capital: Starting capital
            perf_counters: Performance counters dict (will be updated)

        Returns:
            Dictionary with simulation results:
            - trades: List of Trade objects
            - final_equity: Final equity value
            - regime_history: List of regime changes
            - combined_df: Combined DataFrame with all indicators
            - phase_timing: Time taken for simulation
        """
        phase_start = time.time()

        # Pre-align data to 1m index (forward fill HTF data)
        combined_df = self._align_timeframe_data(datasets)

        # Initialize simulation state
        trades: List[Trade] = []
        active_trade: Trade = None
        equity = initial_capital

        # Track regime changes for visualization
        regime_history: List[Dict[str, Any]] = []
        prev_regime_ids: List[str] = []

        # Import RegimeEngine for fallback
        from src.core.tradingbot.regime_engine import RegimeEngine, FeatureVector
        regime_engine = RegimeEngine()

        # Main simulation loop
        for i in range(len(combined_df)):
            row = combined_df.iloc[i]
            timestamp = combined_df.index[i]

            # 1. Evaluate Regimes
            active_regimes, regime_ids = self._evaluate_regimes_with_fallback(
                config, row, symbol, timestamp, regime_engine, perf_counters
            )

            # Track regime changes
            if regime_ids != prev_regime_ids:
                regime_history.append({
                    'timestamp': timestamp,
                    'regime_ids': regime_ids.copy(),
                    'regimes': [{'id': r.id, 'name': r.name} for r in active_regimes]
                })
                prev_regime_ids = regime_ids.copy()

            # 2. Route to Strategy Set
            strategy_set = self._route_to_strategy_set(
                config, regime_ids, perf_counters
            )

            if not strategy_set:
                continue

            # 3. Evaluate Strategies
            active_trade, equity = self._evaluate_strategies(
                strategy_set, config, row, timestamp,
                active_trade, equity, trades, perf_counters
            )

        perf_counters['total_candles_processed'] = len(combined_df)

        return {
            'trades': trades,
            'final_equity': equity,
            'regime_history': regime_history,
            'combined_df': combined_df,
            'phase_timing': time.time() - phase_start
        }

    def _align_timeframe_data(
        self, datasets: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Align all timeframes to 1m index using forward fill.

        Args:
            datasets: Dict of timeframe -> DataFrame

        Returns:
            Combined DataFrame with all indicators
        """
        # Start with 1m base
        df_1m = datasets.get("1m")
        if df_1m is None:
            # Use first available dataset as base
            df_1m = list(datasets.values())[0]

        combined_df = df_1m.copy()

        # Merge HTF data
        for tf, df_tf in datasets.items():
            if tf == "1m":
                continue

            # Prefix columns
            df_tf_renamed = df_tf.add_prefix(f"{tf}_")

            # Reindex to 1m (ffill)
            aligned = df_tf_renamed.reindex(combined_df.index, method='ffill')
            combined_df = pd.concat([combined_df, aligned], axis=1)

        return combined_df

    def _evaluate_regimes_with_fallback(
        self,
        config: TradingBotConfig,
        row: pd.Series,
        symbol: str,
        timestamp,
        regime_engine,
        perf_counters: Dict[str, int]
    ) -> tuple:
        """Evaluate regimes with RegimeEngine fallback.

        Args:
            config: Trading bot configuration
            row: Current data row
            symbol: Trading symbol
            timestamp: Current timestamp
            regime_engine: RegimeEngine instance for fallback
            perf_counters: Performance counters dict

        Returns:
            Tuple of (active_regimes, regime_ids)
        """
        perf_counters['regime_evaluations'] += 1

        # Try JSON regimes first
        active_regimes = self.regime_evaluator(config.regimes, row, config.indicators)
        regime_ids = [r.id for r in active_regimes]

        # Fallback to RegimeEngine if no JSON regimes active
        if not regime_ids and len(row) >= 5:
            try:
                from src.core.tradingbot.models import FeatureVector

                # Convert timestamp
                from datetime import datetime
                if hasattr(timestamp, 'to_pydatetime'):
                    dt_timestamp = timestamp.to_pydatetime()
                elif isinstance(timestamp, datetime):
                    dt_timestamp = timestamp
                else:
                    dt_timestamp = datetime.now()

                # Build FeatureVector
                feature_vector = FeatureVector(
                    timestamp=dt_timestamp,
                    symbol=symbol,
                    close=float(row.get('close', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    open=float(row.get('open', 0)),
                    volume=float(row.get('volume', 0)),
                    rsi=float(row.get('rsi14_value', row.get('1m_rsi14_value', 50))),
                    macd_line=float(row.get('macd12_26_value', row.get('1m_macd12_26_value', 0))),
                    macd_signal=float(row.get('macd12_26_signal', row.get('1m_macd12_26_signal', 0))),
                    adx=float(row.get('adx14_value', row.get('1m_adx14_value', 25))),
                    atr=float(row.get('atr14_value', row.get('1m_atr14_value', 0)))
                )

                # Classify regime
                regime_state = regime_engine.classify(feature_vector)

                # Create synthetic regime IDs
                regime_ids = [
                    f"regime_{regime_state.regime.name.lower()}",
                    f"volatility_{regime_state.volatility.name.lower()}"
                ]

                # Create regime objects
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
                active_regimes = []

        return active_regimes, regime_ids

    def _route_to_strategy_set(
        self,
        config: TradingBotConfig,
        regime_ids: List[str],
        perf_counters: Dict[str, int]
    ):
        """Route regimes to strategy set.

        Args:
            config: Trading bot configuration
            regime_ids: Active regime IDs
            perf_counters: Performance counters dict

        Returns:
            StrategySet or None
        """
        perf_counters['strategy_routings'] += 1

        # Find matching routing rule
        for rule in config.routing:
            match = True

            # Check all_of
            if rule.match.all_of:
                for req in rule.match.all_of:
                    if req not in regime_ids:
                        match = False
                        break

            if not match:
                continue

            # Check any_of
            if rule.match.any_of:
                if not any(r in regime_ids for r in rule.match.any_of):
                    match = False

            if not match:
                continue

            # Check none_of
            if rule.match.none_of:
                if any(r in regime_ids for r in rule.match.none_of):
                    match = False

            if match:
                # Find strategy set
                strategy_set = next(
                    (s for s in config.strategy_sets if s.id == rule.strategy_set_id),
                    None
                )
                return strategy_set

        return None

    def _evaluate_strategies(
        self,
        strategy_set,
        config: TradingBotConfig,
        row: pd.Series,
        timestamp,
        active_trade: Trade,
        equity: float,
        trades: List[Trade],
        perf_counters: Dict[str, int]
    ) -> tuple:
        """Evaluate all strategies in the set.

        Args:
            strategy_set: Current strategy set
            config: Trading bot configuration
            row: Current data row
            timestamp: Current timestamp
            active_trade: Current active trade or None
            equity: Current equity
            trades: List of completed trades
            perf_counters: Performance counters dict

        Returns:
            Tuple of (active_trade, equity)
        """
        for strat_ref in strategy_set.strategies:
            strategy_def = next(
                (s for s in config.strategies if s.id == strat_ref.strategy_id),
                None
            )

            if not strategy_def:
                continue

            # Apply overrides (simple replacement for now)
            current_risk = strategy_def.risk
            if strat_ref.strategy_overrides and strat_ref.strategy_overrides.risk:
                current_risk = strat_ref.strategy_overrides.risk

            # Entry Logic
            if active_trade is None:
                active_trade = self._check_entry(
                    strategy_def, config, row, timestamp,
                    equity, current_risk, perf_counters
                )

            # Exit Logic
            elif active_trade:
                active_trade, equity = self._check_exit(
                    strategy_def, config, row, timestamp,
                    active_trade, equity, current_risk,
                    trades, perf_counters
                )

        return active_trade, equity

    def _check_entry(
        self,
        strategy_def: StrategyDef,
        config: TradingBotConfig,
        row: pd.Series,
        timestamp,
        equity: float,
        current_risk,
        perf_counters: Dict[str, int]
    ) -> Trade:
        """Check entry conditions.

        Returns:
            Trade object if entered, None otherwise
        """
        perf_counters['entry_evaluations'] += 1

        if not self.strategy_evaluator(strategy_def.entry, row, config.indicators):
            return None

        # Enter trade
        perf_counters['trades_entered'] += 1
        price = row['close']
        risk_pct = current_risk.risk_per_trade_pct or 1.0
        size = (equity * risk_pct / 100.0) / price

        return Trade(
            entry_time=timestamp,
            entry_price=price,
            side='long',
            size=size
        )

    def _check_exit(
        self,
        strategy_def: StrategyDef,
        config: TradingBotConfig,
        row: pd.Series,
        timestamp,
        active_trade: Trade,
        equity: float,
        current_risk,
        trades: List[Trade],
        perf_counters: Dict[str, int]
    ) -> tuple:
        """Check exit conditions (SL/TP/Signal).

        Returns:
            Tuple of (active_trade, equity)
        """
        perf_counters['exit_evaluations'] += 1
        price = row['close']

        # Check Stop Loss
        sl_hit = False
        if current_risk and current_risk.stop_loss_pct:
            sl_price = active_trade.entry_price * (1 - current_risk.stop_loss_pct / 100.0)
            if row['low'] <= sl_price:
                active_trade.exit_price = sl_price
                active_trade.exit_reason = "SL"
                sl_hit = True

        # Check Take Profit
        tp_hit = False
        if not sl_hit and current_risk and current_risk.take_profit_pct:
            tp_price = active_trade.entry_price * (1 + current_risk.take_profit_pct / 100.0)
            if row['high'] >= tp_price:
                active_trade.exit_price = tp_price
                active_trade.exit_reason = "TP"
                tp_hit = True

        # Check Strategy Exit Signal
        signal_exit = False
        if not sl_hit and not tp_hit and strategy_def.exit:
            if self.strategy_evaluator(strategy_def.exit, row, config.indicators):
                active_trade.exit_price = price
                active_trade.exit_reason = "Signal"
                signal_exit = True

        # Close trade if any exit condition met
        if sl_hit or tp_hit or signal_exit:
            active_trade.exit_time = timestamp
            active_trade.pnl = (active_trade.exit_price - active_trade.entry_price) * active_trade.size
            active_trade.pnl_pct = (active_trade.exit_price - active_trade.entry_price) / active_trade.entry_price
            trades.append(active_trade)
            equity += active_trade.pnl
            return None, equity

        return active_trade, equity
