"""Result processing for indicator optimization.

Handles:
- Indicator scoring for regimes
- Signal generation (delegates to signal registry)
- Performance metrics calculation
- Proximity scoring
- Composite score calculation

Separated from main thread to improve maintainability.
Pure logic - no PyQt6 signal emissions (handled by core thread).
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .indicator_optimization_core import IndicatorOptimizationThread

logger = logging.getLogger(__name__)


class OptimizationResultsProcessor:
    """Processes optimization results and calculates scores.

    Pure logic class with no signal emissions - delegates to parent thread for signals.
    """

    def __init__(self, thread: 'IndicatorOptimizationThread'):
        """Initialize with reference to parent thread.

        Args:
            thread: Parent IndicatorOptimizationThread (for config access)
        """
        self.thread = thread

    def score_indicator(
        self, df: pd.DataFrame, indicator_type: str, params: Dict[str, int], regime: str
    ) -> Optional[Dict[str, any]]:
        """Score indicator performance for given regime.

        Scoring based on:
        - Entry Long: Low RSI values (<30), bullish signals
        - Entry Short: High RSI values (>70), bearish signals
        - Exit Long: High RSI values (>70), overbought
        - Exit Short: Low RSI values (<30), oversold
        - Proximity to extremes: Closer to lows (long) or highs (short) = higher score

        Args:
            df: DataFrame with price and indicator data
            indicator_type: Indicator type (e.g., 'RSI', 'MACD')
            params: Indicator parameters
            regime: Regime name (e.g., 'STRONG_UPTREND')

        Returns:
            Dict with score (0-100), win_rate, profit_factor, total_trades, etc.
            None if indicator has no valid data or signals
        """
        if 'indicator_value' not in df.columns or df['indicator_value'].isna().all():
            return None

        # Generate signals using signal registry (delegates)
        signals = self.generate_signals(
            df, indicator_type, self.thread.test_type, self.thread.trade_side
        )

        if signals.sum() == 0:
            return None

        # Calculate performance metrics
        metrics = self.calculate_metrics(df, signals)

        if metrics['total_trades'] == 0:
            return None

        # Calculate proximity to extremes (for entry signals)
        proximity_score = 0.0
        if self.thread.test_type == 'entry':
            proximity_score = self.calculate_proximity_score(
                df, signals, self.thread.trade_side
            )
            metrics['proximity_score'] = proximity_score

        # Calculate composite score (0-100)
        score = self.calculate_composite_score(metrics)

        return {
            'indicator': indicator_type,
            'params': params,
            'regime': regime,
            'score': int(score),  # No decimal places
            'win_rate': metrics['win_rate'],
            'profit_factor': metrics['profit_factor'],
            'total_trades': metrics['total_trades'],
            'proximity_score': proximity_score,
            'test_type': self.thread.test_type,
            'trade_side': self.thread.trade_side
        }

    def generate_signals(
        self, df: pd.DataFrame, indicator_type: str, test_type: str, trade_side: str
    ) -> pd.Series:
        """Generate trading signals using Strategy Pattern.

        DELEGATES to SignalGeneratorRegistry with 20 focused generators.
        This method is a thin wrapper around the registry.

        Args:
            df: DataFrame with price and indicator data
            indicator_type: Indicator type (e.g., 'RSI', 'MACD', 'SMA')
            test_type: 'entry' or 'exit'
            trade_side: 'long' or 'short'

        Returns:
            Boolean Series with signals (True = signal fired)

        Complexity: CC = 1 (single delegation call)
        """
        return self.thread._signal_registry.generate_signals(
            df, indicator_type, test_type, trade_side
        )

    def calculate_metrics(
        self, df: pd.DataFrame, signals: pd.Series
    ) -> Dict[str, float]:
        """Calculate performance metrics for signals.

        Args:
            df: DataFrame with price data
            signals: Boolean Series with trading signals

        Returns:
            Dict with metrics:
            - total_trades: Number of trades
            - win_rate: Percentage of winning trades (0-1)
            - profit_factor: Total wins / total losses
            - avg_return: Average return per trade
            - sharpe_ratio: Risk-adjusted return
        """
        # Simple forward returns calculation
        forward_returns = df['close'].pct_change().shift(-1)  # Next bar return

        # Get returns where signals fired
        signal_returns = forward_returns[signals]

        if len(signal_returns) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_return': 0.0,
                'sharpe_ratio': 0.0
            }

        # Calculate metrics
        wins = signal_returns[signal_returns > 0]
        losses = signal_returns[signal_returns <= 0]

        win_rate = len(wins) / len(signal_returns) if len(signal_returns) > 0 else 0.0

        total_wins = wins.sum() if len(wins) > 0 else 0.0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

        avg_return = signal_returns.mean()
        sharpe_ratio = (
            signal_returns.mean() / signal_returns.std()
            if signal_returns.std() > 0 else 0.0
        )

        return {
            'total_trades': len(signal_returns),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe_ratio
        }

    def calculate_proximity_score(
        self, df: pd.DataFrame, signals: pd.Series, trade_side: str
    ) -> float:
        """Calculate proximity score based on distance to price extremes.

        For LONG signals: Higher score if signal is closer to local lows
        For SHORT signals: Higher score if signal is closer to local highs

        Uses a 20-bar window to find local extremes and measures distance
        in bars (not price).

        Args:
            df: DataFrame with price data
            signals: Boolean Series with trading signals
            trade_side: 'long' or 'short'

        Returns:
            Score 0-1 (higher = better proximity)
            1.0 = signal at the exact extreme
            0.0 = signal 20 bars away from extreme
        """
        if signals.sum() == 0:
            return 0.0

        # Get signal indices
        signal_indices = df[signals].index

        proximity_scores = []

        for idx in signal_indices:
            try:
                # Get position in dataframe
                pos = df.index.get_loc(idx)

                # Define lookback/forward window (e.g., 20 bars each side)
                window = 20
                start = max(0, pos - window)
                end = min(len(df), pos + window + 1)

                window_df = df.iloc[start:end]

                if trade_side == 'long':
                    # For LONG: Find nearest low
                    low_price = window_df['low'].min()
                    signal_price = df.loc[idx, 'close']

                    # Calculate distance in bars to the low
                    low_idx = window_df['low'].idxmin()
                    low_pos = df.index.get_loc(low_idx)
                    distance_bars = abs(pos - low_pos)

                    # Score: Closer = better (inverse relationship)
                    # 0 bars distance = 1.0 score, 20 bars = 0.0 score
                    proximity = 1.0 - (distance_bars / window)
                    proximity = max(0.0, proximity)

                else:  # short
                    # For SHORT: Find nearest high
                    high_price = window_df['high'].max()
                    signal_price = df.loc[idx, 'close']

                    # Calculate distance in bars to the high
                    high_idx = window_df['high'].idxmax()
                    high_pos = df.index.get_loc(high_idx)
                    distance_bars = abs(pos - high_pos)

                    # Score: Closer = better (inverse relationship)
                    proximity = 1.0 - (distance_bars / window)
                    proximity = max(0.0, proximity)

                proximity_scores.append(proximity)

            except Exception as e:
                logger.warning(
                    f"Failed to calculate proximity for signal at {idx}: {e}"
                )
                continue

        if not proximity_scores:
            return 0.0

        # Return average proximity score
        return sum(proximity_scores) / len(proximity_scores)

    def calculate_composite_score(self, metrics: Dict[str, float]) -> float:
        """Calculate composite score (0-100) from metrics.

        Weighting:
        - Win Rate: 25%
        - Profit Factor: 25%
        - Sharpe Ratio: 20%
        - Total Trades: 10% (more trades = better)
        - Proximity to Extremes: 20% (closer to lows/highs = better)

        Args:
            metrics: Dict with performance metrics

        Returns:
            Composite score 0-100
        """
        # Normalize metrics to 0-1
        win_rate_score = min(metrics['win_rate'], 1.0)  # Already 0-1

        # Profit factor: 2.0 = 100%, capped at 5.0
        profit_factor_score = min(metrics['profit_factor'] / 5.0, 1.0)

        # Sharpe: 2.0 = 100%, capped at 3.0
        sharpe_score = min(max(metrics['sharpe_ratio'], 0) / 3.0, 1.0)

        # Trades: 50 trades = 100%, capped at 100
        trades_score = min(metrics['total_trades'] / 50.0, 1.0)

        # Proximity score (0-1, already normalized)
        proximity_score = metrics.get('proximity_score', 0.0)

        # Weighted composite
        composite = (
            win_rate_score * 0.25 +
            profit_factor_score * 0.25 +
            sharpe_score * 0.20 +
            trades_score * 0.10 +
            proximity_score * 0.20
        )

        return composite * 100  # Convert to 0-100 scale
