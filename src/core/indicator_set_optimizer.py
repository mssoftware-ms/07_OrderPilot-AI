"""Indicator Set Optimizer for Stage 2.

Optimizes entry/exit signals for each regime using all 7 indicators:
RSI, MACD, STOCH, BB, ATR, EMA, CCI.

Features:
- Regime-specific bar filtering
- TPE optimization (40 trials per indicator)
- Signal backtest with slippage/fees
- Comprehensive metrics (Win Rate, Profit Factor, Sharpe, Drawdown, Expectancy)
- Condition generator for ConditionEvaluator
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import optuna
import pandas as pd
from optuna.pruners import HyperbandPruner
from optuna.samplers import TPESampler

from src.core.indicators.momentum import MomentumIndicators
from src.core.indicators.trend import TrendIndicators
from src.core.indicators.volatility import VolatilityIndicators

logger = logging.getLogger(__name__)


@dataclass
class SignalMetrics:
    """Metrics from signal backtest."""

    signals: int
    trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: float
    expectancy: float
    total_return: float
    wins: int
    losses: int


@dataclass
class OptimizationResult:
    """Result from indicator optimization."""

    signal_type: str
    indicator: str
    params: dict[str, Any]
    conditions: dict[str, Any]
    metrics: SignalMetrics
    score: float
    rank: int


class SignalBacktest:
    """Simulates trades from signals with realistic slippage and fees."""

    def __init__(
        self,
        df: pd.DataFrame,
        slippage_pct: float = 0.05,  # 0.05% slippage
        fee_pct: float = 0.075,  # 0.075% maker/taker fee
    ):
        """Initialize backtest.

        Args:
            df: Price data
            slippage_pct: Slippage percentage
            fee_pct: Trading fee percentage
        """
        self.df = df.copy()
        self.slippage_pct = slippage_pct / 100
        self.fee_pct = fee_pct / 100

    def backtest_entry_long(self, signal: pd.Series, hold_bars: int = 10) -> SignalMetrics:
        """Backtest entry long signals.

        Args:
            signal: Boolean series (True = entry signal)
            hold_bars: How many bars to hold position

        Returns:
            Signal metrics
        """
        trades = []
        i = 0

        while i < len(self.df) - hold_bars:
            if signal.iloc[i]:
                # Entry
                entry_price = self.df["close"].iloc[i] * (1 + self.slippage_pct)
                entry_cost = entry_price * self.fee_pct

                # Exit after hold_bars
                exit_idx = min(i + hold_bars, len(self.df) - 1)
                exit_price = self.df["close"].iloc[exit_idx] * (1 - self.slippage_pct)
                exit_cost = exit_price * self.fee_pct

                # Calculate P&L
                pnl_pct = (exit_price - entry_price) / entry_price - (
                    entry_cost + exit_cost
                ) / entry_price

                trades.append(
                    {
                        "entry_idx": i,
                        "exit_idx": exit_idx,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_pct": pnl_pct,
                    }
                )

                # Skip to next available entry
                i = exit_idx + 1
            else:
                i += 1

        return self._calculate_metrics(trades, signal.sum())

    def backtest_entry_short(self, signal: pd.Series, hold_bars: int = 10) -> SignalMetrics:
        """Backtest entry short signals."""
        trades = []
        i = 0

        while i < len(self.df) - hold_bars:
            if signal.iloc[i]:
                # Entry (short)
                entry_price = self.df["close"].iloc[i] * (1 - self.slippage_pct)
                entry_cost = entry_price * self.fee_pct

                # Exit after hold_bars
                exit_idx = min(i + hold_bars, len(self.df) - 1)
                exit_price = self.df["close"].iloc[exit_idx] * (1 + self.slippage_pct)
                exit_cost = exit_price * self.fee_pct

                # Calculate P&L (inverted for short)
                pnl_pct = (entry_price - exit_price) / entry_price - (
                    entry_cost + exit_cost
                ) / entry_price

                trades.append(
                    {
                        "entry_idx": i,
                        "exit_idx": exit_idx,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_pct": pnl_pct,
                    }
                )

                i = exit_idx + 1
            else:
                i += 1

        return self._calculate_metrics(trades, signal.sum())

    def backtest_exit_timing(self, signal: pd.Series, direction: str = "long") -> SignalMetrics:
        """Evaluate exit signal timing quality.

        For exits, we measure how well the signal captures local extrema.
        """
        if len(signal) == 0 or signal.sum() == 0:
            return self._empty_metrics()

        # Find local extrema in the next N bars after signal
        look_ahead = 5
        trades = []

        for i in range(len(signal) - look_ahead):
            if signal.iloc[i]:
                future_prices = self.df["close"].iloc[i : i + look_ahead]

                if direction == "long":
                    # For long exit, we want to exit near peaks
                    best_exit = future_prices.max()
                    worst_exit = future_prices.min()
                else:
                    # For short exit, we want to exit near troughs
                    best_exit = future_prices.min()
                    worst_exit = future_prices.max()

                current_price = self.df["close"].iloc[i]

                # Score = how close we are to best exit
                if best_exit != worst_exit:
                    timing_score = abs(current_price - best_exit) / abs(best_exit - worst_exit)
                    # Lower is better, so invert: 1.0 - score
                    pnl_pct = (1.0 - timing_score) * 0.02  # Scale to ~2% range
                else:
                    pnl_pct = 0.0

                trades.append(
                    {
                        "entry_idx": i,
                        "exit_idx": i,
                        "entry_price": current_price,
                        "exit_price": current_price,
                        "pnl_pct": pnl_pct,
                    }
                )

        return self._calculate_metrics(trades, signal.sum())

    def _calculate_metrics(self, trades: list[dict], total_signals: int) -> SignalMetrics:
        """Calculate comprehensive metrics from trade list."""
        if not trades:
            return self._empty_metrics()

        # Extract P&L
        pnls = [t["pnl_pct"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        # Basic stats
        n_trades = len(trades)
        n_wins = len(wins)
        n_losses = len(losses)
        win_rate = n_wins / n_trades if n_trades > 0 else 0.0

        # Win/Loss averages
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = abs(np.mean(losses)) if losses else 0.0

        # Profit factor
        total_wins = sum(wins) if wins else 0.0
        total_losses = abs(sum(losses)) if losses else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

        # Drawdown
        cumulative = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0

        # Sharpe ratio (annualized, assuming 5m bars)
        returns = np.array(pnls)
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252 * 24 * 12)  # 5m bars
        else:
            sharpe = 0.0

        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        # Total return
        total_return = sum(pnls)

        return SignalMetrics(
            signals=total_signals,
            trades=n_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            expectancy=expectancy,
            total_return=total_return,
            wins=n_wins,
            losses=n_losses,
        )

    def _empty_metrics(self) -> SignalMetrics:
        """Return empty metrics."""
        return SignalMetrics(
            signals=0,
            trades=0,
            win_rate=0.0,
            profit_factor=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            expectancy=0.0,
            total_return=0.0,
            wins=0,
            losses=0,
        )


class IndicatorSetOptimizer:
    """Optimizes indicator sets for entry/exit signals per regime."""

    INDICATORS = ["RSI", "MACD", "STOCH", "BB", "ATR", "EMA", "CCI"]
    SIGNAL_TYPES = ["entry_long", "entry_short", "exit_long", "exit_short"]

    def __init__(
        self,
        df: pd.DataFrame,
        regime: str,
        regime_indices: list[int],
        symbol: str,
        timeframe: str,
        regime_config_path: str,
    ):
        """Initialize optimizer.

        Args:
            df: Full price dataframe
            regime: Regime name (BULL/BEAR/SIDEWAYS)
            regime_indices: Bar indices for this regime
            symbol: Trading symbol
            timeframe: Timeframe
            regime_config_path: Path to regime config JSON
        """
        self.df = df
        self.regime = regime
        self.regime_indices = regime_indices
        self.symbol = symbol
        self.timeframe = timeframe
        self.regime_config_path = regime_config_path

        # Filter dataframe to regime bars only
        self.regime_df = df.iloc[regime_indices].copy().reset_index(drop=True)

        logger.info(
            f"Initialized IndicatorSetOptimizer for {regime}: "
            f"{len(self.regime_df)} bars out of {len(df)} total"
        )

    def optimize_all_signals(
        self, n_trials_per_indicator: int = 40
    ) -> dict[str, OptimizationResult]:
        """Optimize all 4 signal types.

        Args:
            n_trials_per_indicator: Number of trials per indicator

        Returns:
            Dict mapping signal_type to best result
        """
        results = {}

        for signal_type in self.SIGNAL_TYPES:
            logger.info(f"Optimizing {signal_type} for {self.regime} regime...")

            best_result = self._optimize_signal_type(signal_type, n_trials_per_indicator)

            results[signal_type] = best_result

            logger.info(
                f"  Best: {best_result.indicator} "
                f"(Score: {best_result.score:.2f}, "
                f"Win Rate: {best_result.metrics.win_rate:.2%})"
            )

        return results

    def _optimize_signal_type(
        self, signal_type: str, n_trials_per_indicator: int
    ) -> OptimizationResult:
        """Optimize single signal type across all indicators.

        Args:
            signal_type: entry_long/entry_short/exit_long/exit_short
            n_trials_per_indicator: Number of trials per indicator

        Returns:
            Best optimization result
        """
        all_results = []

        for indicator in self.INDICATORS:
            logger.info(f"    Testing {indicator}...")

            # Create study for this indicator
            study = self._create_study(signal_type, indicator)

            # Optimize
            study.optimize(
                lambda trial: self._objective(trial, signal_type, indicator),
                n_trials=n_trials_per_indicator,
                show_progress_bar=False,
            )

            if len(study.trials) == 0:
                continue

            # Get best trial
            best_trial = study.best_trial
            best_params = best_trial.params

            # Recalculate with best params to get full metrics
            metrics, conditions = self._evaluate_indicator(signal_type, indicator, best_params)

            score = self._calculate_score(metrics, signal_type)

            result = OptimizationResult(
                signal_type=signal_type,
                indicator=indicator,
                params=best_params,
                conditions=conditions,
                metrics=metrics,
                score=score,
                rank=0,  # Will be set later
            )

            all_results.append(result)

        # Rank results by score
        all_results.sort(key=lambda r: r.score, reverse=True)
        for i, result in enumerate(all_results, 1):
            result.rank = i

        # Return best
        return all_results[0] if all_results else self._empty_result(signal_type)

    def _create_study(self, signal_type: str, indicator: str) -> optuna.Study:
        """Create Optuna study with TPE sampler and Hyperband pruner."""
        sampler = TPESampler(n_startup_trials=10, multivariate=True, seed=42)

        pruner = HyperbandPruner(min_resource=1, max_resource=10, reduction_factor=3)

        study = optuna.create_study(
            direction="maximize",
            sampler=sampler,
            pruner=pruner,
            study_name=f"{self.regime}_{signal_type}_{indicator}",
        )

        return study

    def _objective(self, trial: optuna.Trial, signal_type: str, indicator: str) -> float:
        """Optuna objective function.

        Args:
            trial: Optuna trial
            signal_type: Signal type
            indicator: Indicator name

        Returns:
            Score to maximize
        """
        # Suggest parameters based on indicator
        params = self._suggest_params(trial, indicator, signal_type)

        # Evaluate with multi-fidelity pruning
        for fidelity in [20, 50, 100]:
            subset_size = int(len(self.regime_df) * fidelity / 100)
            if subset_size < 100:
                continue

            subset_df = self.regime_df.iloc[:subset_size]
            metrics, _ = self._evaluate_indicator_on_df(subset_df, signal_type, indicator, params)

            score = self._calculate_score(metrics, signal_type)

            trial.report(score, step=fidelity)

            if trial.should_prune():
                raise optuna.TrialPruned()

        return score

    def _suggest_params(
        self, trial: optuna.Trial, indicator: str, signal_type: str
    ) -> dict[str, Any]:
        """Suggest parameters for indicator."""
        params = {}

        if indicator == "RSI":
            params["period"] = trial.suggest_int("period", 7, 21)
            if "entry" in signal_type:
                params["oversold"] = trial.suggest_int("oversold", 20, 35)
                params["overbought"] = trial.suggest_int("overbought", 65, 80)

        elif indicator == "MACD":
            params["fast"] = trial.suggest_int("fast", 8, 16)
            params["slow"] = trial.suggest_int("slow", 20, 30)
            params["signal"] = trial.suggest_int("signal", 7, 11)

        elif indicator == "STOCH":
            params["k_period"] = trial.suggest_int("k_period", 10, 20)
            params["d_period"] = trial.suggest_int("d_period", 2, 5)
            params["smooth"] = trial.suggest_int("smooth", 2, 4)
            if "entry" in signal_type:
                params["oversold"] = trial.suggest_int("oversold", 15, 25)
                params["overbought"] = trial.suggest_int("overbought", 75, 85)

        elif indicator == "BB":
            params["period"] = trial.suggest_int("period", 15, 25)
            params["std_dev"] = trial.suggest_float("std_dev", 1.5, 2.5, step=0.5)

        elif indicator == "ATR":
            params["period"] = trial.suggest_int("period", 10, 20)
            params["multiplier"] = trial.suggest_float("multiplier", 1.5, 3.5, step=0.5)

        elif indicator == "EMA":
            params["period"] = trial.suggest_int("period", 10, 50, step=5)

        elif indicator == "CCI":
            params["period"] = trial.suggest_int("period", 14, 30)
            if "entry" in signal_type:
                params["oversold"] = trial.suggest_int("oversold", -150, -80)
                params["overbought"] = trial.suggest_int("overbought", 80, 150)

        return params

    def _evaluate_indicator(
        self, signal_type: str, indicator: str, params: dict[str, Any]
    ) -> tuple[SignalMetrics, dict[str, Any]]:
        """Evaluate indicator on full regime dataframe."""
        return self._evaluate_indicator_on_df(self.regime_df, signal_type, indicator, params)

    def _evaluate_indicator_on_df(
        self, df: pd.DataFrame, signal_type: str, indicator: str, params: dict[str, Any]
    ) -> tuple[SignalMetrics, dict[str, Any]]:
        """Evaluate indicator on given dataframe.

        Returns:
            (metrics, conditions)
        """
        # Calculate indicator
        indicator_values = self._calculate_indicator(df, indicator, params)

        # Generate signal
        signal, conditions = self._generate_signal(
            df, indicator, indicator_values, signal_type, params
        )

        # Backtest signal
        backtester = SignalBacktest(df)

        if signal_type == "entry_long":
            metrics = backtester.backtest_entry_long(signal)
        elif signal_type == "entry_short":
            metrics = backtester.backtest_entry_short(signal)
        elif signal_type == "exit_long":
            metrics = backtester.backtest_exit_timing(signal, direction="long")
        elif signal_type == "exit_short":
            metrics = backtester.backtest_exit_timing(signal, direction="short")
        else:
            raise ValueError(f"Unknown signal type: {signal_type}")

        return metrics, conditions

    def _calculate_indicator(
        self, df: pd.DataFrame, indicator: str, params: dict[str, Any]
    ) -> pd.DataFrame | pd.Series:
        """Calculate indicator values."""
        if indicator == "RSI":
            result = MomentumIndicators.calculate_rsi(df, params, use_talib=True)
            return result.values

        elif indicator == "MACD":
            result = TrendIndicators.calculate_macd(df, params, use_talib=True)
            values = result.values
            # Normalize pandas_ta column names
            if isinstance(values, pd.DataFrame):
                values = self._normalize_macd_columns(values)
            return values

        elif indicator == "STOCH":
            result = MomentumIndicators.calculate_stoch(df, params, use_talib=True)
            values = result.values
            # Normalize pandas_ta column names
            if isinstance(values, pd.DataFrame):
                values = self._normalize_stoch_columns(values)
            return values

        elif indicator == "BB":
            result = VolatilityIndicators.calculate_bb(df, params, use_talib=True)
            return result.values

        elif indicator == "ATR":
            result = VolatilityIndicators.calculate_atr(df, params, use_talib=True)
            values = result.values
            # Normalize pandas_ta column names
            if isinstance(values, pd.Series) and values.name:
                values = pd.Series(values.values, index=values.index, name="value")
            return values

        elif indicator == "EMA":
            result = TrendIndicators.calculate_ema(df, params, use_talib=True)
            return result.values

        elif indicator == "CCI":
            result = MomentumIndicators.calculate_cci(df, params, use_talib=True)
            return result.values

        else:
            raise ValueError(f"Unknown indicator: {indicator}")

    def _normalize_macd_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize MACD column names from pandas_ta to standard format."""
        cols = df.columns

        # Find columns by prefix
        macd_col = next(
            (c for c in cols if c.startswith("MACD") and "h" not in c and "s" not in c), None
        )
        signal_col = next((c for c in cols if "MACDs" in c), None)
        hist_col = next((c for c in cols if "MACDh" in c), None)

        if macd_col and signal_col and hist_col:
            return pd.DataFrame(
                {"macd": df[macd_col], "signal": df[signal_col], "histogram": df[hist_col]},
                index=df.index,
            )

        return df

    def _normalize_stoch_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize STOCH column names from pandas_ta to standard format."""
        cols = df.columns

        # Find columns by prefix
        k_col = next((c for c in cols if "STOCHk" in c), None)
        d_col = next((c for c in cols if "STOCHd" in c), None)

        if k_col and d_col:
            return pd.DataFrame({"k": df[k_col], "d": df[d_col]}, index=df.index)

        return df

    def _generate_signal(
        self,
        df: pd.DataFrame,
        indicator: str,
        values: pd.DataFrame | pd.Series,
        signal_type: str,
        params: dict[str, Any],
    ) -> tuple[pd.Series, dict[str, Any]]:
        """Generate signal from indicator values.

        Returns:
            (signal series, conditions dict)
        """
        conditions = {"all": []}
        indicator_id = f"{indicator.lower()}_{params.get('period', 14)}"

        if indicator == "RSI":
            if signal_type == "entry_long":
                signal = values < params["oversold"]
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "value"},
                        "op": "lt",
                        "right": {"value": params["oversold"]},
                    }
                )
            elif signal_type == "entry_short":
                signal = values > params["overbought"]
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "value"},
                        "op": "gt",
                        "right": {"value": params["overbought"]},
                    }
                )
            elif signal_type == "exit_long":
                signal = values > params.get("overbought", 70)
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "value"},
                        "op": "gt",
                        "right": {"value": params.get("overbought", 70)},
                    }
                )
            else:  # exit_short
                signal = values < params.get("oversold", 30)
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "value"},
                        "op": "lt",
                        "right": {"value": params.get("oversold", 30)},
                    }
                )

        elif indicator == "MACD":
            macd = values["macd"]
            signal_line = values["signal"]
            histogram = values["histogram"]

            if signal_type == "entry_long":
                signal = (macd > signal_line) & (histogram > 0)
                conditions["all"].extend(
                    [
                        {
                            "left": {"indicator_id": indicator_id, "field": "macd"},
                            "op": "gt",
                            "right": {"indicator_id": indicator_id, "field": "signal"},
                        },
                        {
                            "left": {"indicator_id": indicator_id, "field": "histogram"},
                            "op": "gt",
                            "right": {"value": 0},
                        },
                    ]
                )
            elif signal_type == "entry_short":
                signal = (macd < signal_line) & (histogram < 0)
                conditions["all"].extend(
                    [
                        {
                            "left": {"indicator_id": indicator_id, "field": "macd"},
                            "op": "lt",
                            "right": {"indicator_id": indicator_id, "field": "signal"},
                        },
                        {
                            "left": {"indicator_id": indicator_id, "field": "histogram"},
                            "op": "lt",
                            "right": {"value": 0},
                        },
                    ]
                )
            elif signal_type == "exit_long":
                # Crossover down
                signal = (macd < signal_line) & (macd.shift(1) > signal_line.shift(1))
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "macd"},
                        "op": "crosses_below",
                        "right": {"indicator_id": indicator_id, "field": "signal"},
                    }
                )
            else:  # exit_short
                # Crossover up
                signal = (macd > signal_line) & (macd.shift(1) < signal_line.shift(1))
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "macd"},
                        "op": "crosses_above",
                        "right": {"indicator_id": indicator_id, "field": "signal"},
                    }
                )

        elif indicator == "STOCH":
            k = values["k"]
            d = values["d"]

            if signal_type == "entry_long":
                signal = (k < params["oversold"]) & (k > d)
                conditions["all"].extend(
                    [
                        {
                            "left": {"indicator_id": indicator_id, "field": "k"},
                            "op": "lt",
                            "right": {"value": params["oversold"]},
                        },
                        {
                            "left": {"indicator_id": indicator_id, "field": "k"},
                            "op": "gt",
                            "right": {"indicator_id": indicator_id, "field": "d"},
                        },
                    ]
                )
            elif signal_type == "entry_short":
                signal = (k > params["overbought"]) & (k < d)
                conditions["all"].extend(
                    [
                        {
                            "left": {"indicator_id": indicator_id, "field": "k"},
                            "op": "gt",
                            "right": {"value": params["overbought"]},
                        },
                        {
                            "left": {"indicator_id": indicator_id, "field": "k"},
                            "op": "lt",
                            "right": {"indicator_id": indicator_id, "field": "d"},
                        },
                    ]
                )
            elif signal_type == "exit_long":
                signal = k > params.get("overbought", 80)
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "k"},
                        "op": "gt",
                        "right": {"value": params.get("overbought", 80)},
                    }
                )
            else:  # exit_short
                signal = k < params.get("oversold", 20)
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "k"},
                        "op": "lt",
                        "right": {"value": params.get("oversold", 20)},
                    }
                )

        elif indicator == "BB":
            upper = values["upper"]
            lower = values["lower"]
            percent = values["percent"]

            if signal_type == "entry_long":
                signal = df["close"] < lower
                conditions["all"].append(
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "lt",
                        "right": {"indicator_id": indicator_id, "field": "lower"},
                    }
                )
            elif signal_type == "entry_short":
                signal = df["close"] > upper
                conditions["all"].append(
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "gt",
                        "right": {"indicator_id": indicator_id, "field": "upper"},
                    }
                )
            elif signal_type == "exit_long":
                signal = percent > 0.8  # Near upper band
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "percent"},
                        "op": "gt",
                        "right": {"value": 0.8},
                    }
                )
            else:  # exit_short
                signal = percent < 0.2  # Near lower band
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "percent"},
                        "op": "lt",
                        "right": {"value": 0.2},
                    }
                )

        elif indicator == "ATR":
            # ATR trailing stop
            multiplier = params.get("multiplier", 2.0)

            if signal_type == "exit_long":
                trailing_stop = df["close"] - (values * multiplier)
                signal = df["close"] < trailing_stop
                conditions["all"].append(
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "lt",
                        "right": {"indicator_id": indicator_id, "field": "trailing_stop"},
                    }
                )
            elif signal_type == "exit_short":
                trailing_stop = df["close"] + (values * multiplier)
                signal = df["close"] > trailing_stop
                conditions["all"].append(
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "gt",
                        "right": {"indicator_id": indicator_id, "field": "trailing_stop"},
                    }
                )
            else:
                # ATR not typically used for entries
                signal = pd.Series(False, index=df.index)

        elif indicator == "EMA":
            if signal_type == "entry_long":
                signal = df["close"] > values
                conditions["all"].append(
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "gt",
                        "right": {"indicator_id": indicator_id, "field": "value"},
                    }
                )
            elif signal_type == "entry_short":
                signal = df["close"] < values
                conditions["all"].append(
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "lt",
                        "right": {"indicator_id": indicator_id, "field": "value"},
                    }
                )
            elif signal_type == "exit_long":
                # Cross below EMA
                signal = (df["close"] < values) & (df["close"].shift(1) > values.shift(1))
                conditions["all"].append(
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "crosses_below",
                        "right": {"indicator_id": indicator_id, "field": "value"},
                    }
                )
            else:  # exit_short
                # Cross above EMA
                signal = (df["close"] > values) & (df["close"].shift(1) < values.shift(1))
                conditions["all"].append(
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "crosses_above",
                        "right": {"indicator_id": indicator_id, "field": "value"},
                    }
                )

        elif indicator == "CCI":
            if signal_type == "entry_long":
                signal = values < params["oversold"]
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "value"},
                        "op": "lt",
                        "right": {"value": params["oversold"]},
                    }
                )
            elif signal_type == "entry_short":
                signal = values > params["overbought"]
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "value"},
                        "op": "gt",
                        "right": {"value": params["overbought"]},
                    }
                )
            elif signal_type == "exit_long":
                signal = values > params.get("overbought", 100)
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "value"},
                        "op": "gt",
                        "right": {"value": params.get("overbought", 100)},
                    }
                )
            else:  # exit_short
                signal = values < params.get("oversold", -100)
                conditions["all"].append(
                    {
                        "left": {"indicator_id": indicator_id, "field": "value"},
                        "op": "lt",
                        "right": {"value": params.get("oversold", -100)},
                    }
                )

        else:
            signal = pd.Series(False, index=df.index)

        return signal, conditions

    def _calculate_score(self, metrics: SignalMetrics, signal_type: str) -> float:
        """Calculate composite score from metrics.

        Weighted combination of:
        - Win Rate (30%)
        - Profit Factor (25%)
        - Sharpe Ratio (20%)
        - Expectancy (15%)
        - Max Drawdown penalty (10%)
        """
        if metrics.trades == 0:
            return 0.0

        # Normalize components to 0-100 scale
        win_rate_score = metrics.win_rate * 100

        # Profit factor: 2.0 = 100, 1.0 = 50, 0.5 = 0
        pf = min(metrics.profit_factor, 3.0)
        profit_factor_score = ((pf - 0.5) / 2.5) * 100

        # Sharpe: 2.0 = 100, 0 = 50, -1 = 0
        sharpe_normalized = (metrics.sharpe_ratio + 1) / 3
        sharpe_score = min(max(sharpe_normalized * 100, 0), 100)

        # Expectancy: 2% = 100, 0% = 50, -2% = 0
        expectancy_normalized = (metrics.expectancy + 0.02) / 0.04
        expectancy_score = min(max(expectancy_normalized * 100, 0), 100)

        # Drawdown penalty: 0% = 100, 10% = 0
        drawdown_score = max(100 - (metrics.max_drawdown * 1000), 0)

        # Weighted score
        score = (
            0.30 * win_rate_score
            + 0.25 * profit_factor_score
            + 0.20 * sharpe_score
            + 0.15 * expectancy_score
            + 0.10 * drawdown_score
        )

        # Penalty for low trade count
        if metrics.trades < 10:
            score *= metrics.trades / 10

        return score

    def _empty_result(self, signal_type: str) -> OptimizationResult:
        """Return empty result."""
        return OptimizationResult(
            signal_type=signal_type,
            indicator="NONE",
            params={},
            conditions={},
            metrics=SignalMetrics(
                signals=0,
                trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                expectancy=0.0,
                total_return=0.0,
                wins=0,
                losses=0,
            ),
            score=0.0,
            rank=999,
        )

    def export_to_json(self, results: dict[str, OptimizationResult], output_dir: Path) -> str:
        """Export results to JSON.

        Args:
            results: Optimization results
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine regime color
        regime_colors = {"BULL": "#26a69a", "BEAR": "#ef5350", "SIDEWAYS": "#9e9e9e"}

        # Build JSON structure
        data = {
            "version": "2.0",
            "meta": {
                "stage": "indicator_sets",
                "regime": self.regime,
                "regime_color": regime_colors.get(self.regime, "#ffffff"),
                "created_at": datetime.now().isoformat(),
                "name": f"{self.regime} Indicator Sets - {self.symbol} {self.timeframe}",
                "regime_config_ref": self.regime_config_path,
                "source": {"symbol": self.symbol, "timeframe": self.timeframe},
                "aggregate_metrics": self._calculate_aggregate_metrics(results),
            },
            "signal_sets": {},
        }

        # Add each signal type
        for signal_type, result in results.items():
            enabled = result.score > 30  # Threshold for enabling

            data["signal_sets"][signal_type] = {
                "enabled": enabled,
                "selected_rank": result.rank,
                "score": result.score,
                "indicator": result.indicator,
                "indicator_id": f"{result.indicator.lower()}_{result.params.get('period', 14)}",
                "params": result.params,
                "conditions": result.conditions,
                "metrics": {
                    "signals": result.metrics.signals,
                    "trades": result.metrics.trades,
                    "win_rate": result.metrics.win_rate,
                    "profit_factor": result.metrics.profit_factor,
                    "avg_win": result.metrics.avg_win,
                    "avg_loss": result.metrics.avg_loss,
                    "max_drawdown": result.metrics.max_drawdown,
                    "sharpe_ratio": result.metrics.sharpe_ratio,
                    "expectancy": result.metrics.expectancy,
                },
            }

        # Save to file
        filename = f"indicator_sets_{self.regime}_{self.symbol}_{self.timeframe}.json"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved indicator sets to {filepath}")

        return str(filepath)

    def _calculate_aggregate_metrics(
        self, results: dict[str, OptimizationResult]
    ) -> dict[str, Any]:
        """Calculate aggregate metrics across all signal types."""
        enabled_results = [r for r in results.values() if r.score > 30]

        if not enabled_results:
            return {
                "total_signals_enabled": 0,
                "combined_win_rate": 0.0,
                "combined_profit_factor": 0.0,
            }

        total_trades = sum(r.metrics.trades for r in enabled_results)
        total_wins = sum(r.metrics.wins for r in enabled_results)

        win_rate = total_wins / total_trades if total_trades > 0 else 0.0

        # Weighted average profit factor
        total_pf = sum(r.metrics.profit_factor * r.metrics.trades for r in enabled_results)
        avg_pf = total_pf / total_trades if total_trades > 0 else 0.0

        return {
            "total_signals_enabled": len(enabled_results),
            "combined_win_rate": win_rate,
            "combined_profit_factor": avg_pf,
        }
