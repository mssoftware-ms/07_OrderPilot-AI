"""Signal generation for strategy simulation."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from .strategy_params import StrategyName
from .simulation_signal_utils import calculate_obv, calculate_rsi, true_range
from .simulation_signals_bollinger_squeeze import bollinger_squeeze_signals
from .simulation_signals_breakout import breakout_signals
from .simulation_signals_mean_reversion import mean_reversion_signals
from .simulation_signals_momentum import momentum_signals
from .simulation_signals_opening_range import opening_range_signals
from .simulation_signals_regime_hybrid import regime_hybrid_signals
from .simulation_signals_scalping import scalping_signals
from .simulation_signals_trend_following import trend_following_signals
from .simulation_signals_trend_pullback import trend_pullback_signals

logger = logging.getLogger(__name__)


class StrategySignalGenerator:
    """Generates trading signals for supported strategies."""

    def __init__(self, data: pd.DataFrame):
        self.data = data

    def generate(
        self,
        strategy_name: StrategyName,
        parameters: dict[str, Any],
    ) -> pd.DataFrame:
        """Generate trading signals based on strategy logic.

        Returns DataFrame with 'signal' column: 1=buy, -1=sell, 0=hold
        """
        df = self.data.copy()

        if strategy_name == StrategyName.BREAKOUT:
            signals = self._breakout_signals(df, parameters)
        elif strategy_name == StrategyName.MOMENTUM:
            signals = self._momentum_signals(df, parameters)
        elif strategy_name == StrategyName.MEAN_REVERSION:
            signals = self._mean_reversion_signals(df, parameters)
        elif strategy_name == StrategyName.TREND_FOLLOWING:
            signals = self._trend_following_signals(df, parameters)
        elif strategy_name == StrategyName.SCALPING:
            signals = self._scalping_signals(df, parameters)
        elif strategy_name == StrategyName.BOLLINGER_SQUEEZE:
            signals = self._bollinger_squeeze_signals(df, parameters)
        elif strategy_name == StrategyName.TREND_PULLBACK:
            signals = self._trend_pullback_signals(df, parameters)
        elif strategy_name == StrategyName.OPENING_RANGE:
            signals = self._opening_range_signals(df, parameters)
        elif strategy_name == StrategyName.REGIME_HYBRID:
            signals = self._regime_hybrid_signals(df, parameters)
        else:
            logger.warning(f"Unknown strategy: {strategy_name}, no signals generated")
            signals = pd.Series(0, index=df.index)

        df["signal"] = signals
        return df

    def _breakout_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return breakout_signals(df, params, true_range=true_range)

    def _momentum_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return momentum_signals(df, params, calculate_rsi=calculate_rsi, calculate_obv=calculate_obv)

    def _mean_reversion_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return mean_reversion_signals(df, params, calculate_rsi=calculate_rsi)

    def _trend_following_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return trend_following_signals(df, params, calculate_rsi=calculate_rsi)

    def _scalping_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return scalping_signals(df, params, calculate_rsi=calculate_rsi)

    def _bollinger_squeeze_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return bollinger_squeeze_signals(df, params, calculate_rsi=calculate_rsi)

    def _trend_pullback_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return trend_pullback_signals(df, params, calculate_rsi=calculate_rsi)

    def _opening_range_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return opening_range_signals(df, params)

    def _regime_hybrid_signals(self, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        return regime_hybrid_signals(
            df,
            params,
            calculate_rsi=calculate_rsi,
            calculate_obv=calculate_obv,
            true_range=true_range,
        )

    def _true_range(self, df: pd.DataFrame) -> pd.Series:
        return true_range(df)

    def _calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        return calculate_rsi(series, period)

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        return calculate_obv(df)
