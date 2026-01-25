"""Entry Analyzer - Indicator Optimization Worker V2 (Indicators only).

Runs optimization for indicator parameter ranges (Entry/Exit Long/Short) without Regime dependency.
Deterministic scoring (kein Random) auf Basis von Candle-Statistiken.
"""

from __future__ import annotations

import logging
import itertools
from statistics import mean, stdev
from typing import TYPE_CHECKING, Any, Dict, List

from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IndicatorOptimizationWorkerV2(QThread):
    """Background worker for indicator optimization (Stage 2)."""

    progress = pyqtSignal(str, int, int, float)  # signal_type, current, total, best_score
    result_ready = pyqtSignal(str, dict)  # signal_type, result
    finished = pyqtSignal(dict)  # all_results per signal type
    error = pyqtSignal(str)

    def __init__(self, config: dict, parent: Any = None) -> None:
        super().__init__(parent)
        self.config = config
        self._stop_requested = False

    def run(self) -> None:
        try:
            signal_types = self.config["signal_types"]
            indicators = self.config["indicators"]
            param_ranges = self.config["param_ranges"]
            candles = self.config["candles"]
            max_trials = int(self.config.get("max_trials", 150))

            if not candles:
                self.error.emit("No candles provided for optimization")
                return

            logger.info(
                "Starting indicator optimization: %s signals, %s indicators, max_trials=%s",
                len(signal_types),
                len(indicators),
                max_trials,
            )

            all_results = {}
            for signal_type in signal_types:
                if self._stop_requested:
                    logger.info("Optimization stopped by user")
                    break

                results = self._optimize_signal_type(
                    signal_type=signal_type,
                    indicators=indicators,
                    param_ranges=param_ranges,
                    candles=candles,
                    max_trials=max_trials,
                )
                all_results[signal_type] = results

                if results:
                    best = max(results, key=lambda r: r.get("score", 0.0))
                    self.result_ready.emit(signal_type, best)

            self.finished.emit(all_results)

        except Exception as e:
            logger.exception("Indicator optimization failed")
            self.error.emit(str(e))

    # ------------------------------------------------------------------ Core
    def _optimize_signal_type(
        self,
        signal_type: str,
        indicators: List[str],
        param_ranges: Dict[str, Dict[str, dict]],
        candles: List[Dict],
        max_trials: int,
    ) -> List[Dict]:
        results = []
        current = 0

        for indicator in indicators:
            if self._stop_requested:
                break
            ranges = param_ranges.get(indicator, {})
            if not ranges:
                logger.warning("No ranges for indicator %s", indicator)
                continue

            combos = self._generate_param_combinations(ranges, max_trials=max_trials)
            total_for_indicator = min(len(combos), max_trials - current)
            best_score = 0.0

            for params in combos:
                if self._stop_requested or current >= max_trials:
                    break

                current += 1
                result = self._evaluate_params(
                    indicator=indicator,
                    params=params,
                    signal_type=signal_type,
                    candles=candles,
                )
                results.append(result)
                best_score = max(best_score, result["score"])

                if current % 10 == 0 or current == max_trials:
                    self.progress.emit(signal_type, current, max_trials, best_score)

            if current >= max_trials:
                break

        logger.info("%s: completed %s tests", signal_type, len(results))
        return results

    # ------------------------------------------------------------------ Helpers
    def _generate_param_combinations(self, ranges: Dict[str, dict], max_trials: int) -> List[Dict]:
        """Generate parameter combinations respecting max_trials (simple slice)."""
        names = list(ranges.keys())
        value_lists = []
        for name in names:
            rng = ranges[name]
            min_v = rng.get("min")
            max_v = rng.get("max")
            step = rng.get("step")
            if min_v is None or max_v is None or step is None or step <= 0:
                # fallback: single value
                base_val = rng.get("value", 0)
                value_lists.append([base_val])
                continue
            vals = []
            v = min_v
            # simple inclusive range
            while v <= max_v + 1e-9:
                vals.append(v)
                v += step
            value_lists.append(vals or [rng.get("value", min_v)])

        combos = []
        for combo in itertools.product(*value_lists):
            combos.append({names[i]: combo[i] for i in range(len(names))})
            if len(combos) >= max_trials:
                break
        return combos

    def _evaluate_params(
        self, indicator: str, params: Dict, signal_type: str, candles: List[Dict]
    ) -> Dict:
        """Lightweight deterministic backtest on candles using simple crossover/RSI logic."""
        # Limit bars for speed
        MAX_BARS = 20000
        series = candles[-MAX_BARS:] if len(candles) > MAX_BARS else candles
        closes = [c["close"] for c in series]
        highs = [c.get("high", c["close"]) for c in series]
        lows = [c.get("low", c["close"]) for c in series]

        # Helper indicators
        def ema(values, period):
            if not values:
                return []
            k = 2 / (period + 1)
            ema_vals = [values[0]]
            for price in values[1:]:
                ema_vals.append(price * k + ema_vals[-1] * (1 - k))
            return ema_vals

        def rsi(values, period):
            if len(values) < period + 1:
                return [50.0] * len(values)
            gains = []
            losses = []
            rsis = []
            for i in range(1, len(values)):
                diff = values[i] - values[i - 1]
                gains.append(max(diff, 0))
                losses.append(-min(diff, 0))
                if i >= period:
                    avg_gain = mean(gains[-period:])
                    avg_loss = mean(losses[-period:])
                    if avg_loss == 0:
                        rs = 999
                    else:
                        rs = avg_gain / avg_loss
                    rsis.append(100 - (100 / (1 + rs)))
                else:
                    rsis.append(50.0)
            return [50.0] + rsis

        period = int(params.get("period") or params.get("atr_period") or 14)
        period = max(2, min(period, 200))

        rsi_series = rsi(closes, period)
        ema_series = ema(closes, period)

        # Signals
        def entry_long(idx):
            if indicator.upper().find("RSI") >= 0:
                oversold = params.get("oversold", 35)
                return rsi_series[idx - 1] < oversold and rsi_series[idx] >= oversold
            # default: EMA cross
            return closes[idx - 1] <= ema_series[idx - 1] and closes[idx] > ema_series[idx]

        def exit_long(idx):
            if indicator.upper().find("RSI") >= 0:
                overbought = params.get("overbought", 65)
                return rsi_series[idx - 1] > overbought and rsi_series[idx] <= overbought
            return closes[idx - 1] >= ema_series[idx - 1] and closes[idx] < ema_series[idx]

        def entry_short(idx):
            if indicator.upper().find("RSI") >= 0:
                overbought = params.get("overbought", 65)
                return rsi_series[idx - 1] > overbought and rsi_series[idx] <= overbought
            return closes[idx - 1] >= ema_series[idx - 1] and closes[idx] < ema_series[idx]

        def exit_short(idx):
            if indicator.upper().find("RSI") >= 0:
                oversold = params.get("oversold", 35)
                return rsi_series[idx - 1] < oversold and rsi_series[idx] >= oversold
            return closes[idx - 1] <= ema_series[idx - 1] and closes[idx] > ema_series[idx]

        trades = []
        position = None  # {"side": "long/short", "price": float}
        for i in range(1, len(series)):
            if position is None:
                if signal_type == "entry_long" and entry_long(i):
                    position = {"side": "long", "price": closes[i]}
                elif signal_type == "entry_short" and entry_short(i):
                    position = {"side": "short", "price": closes[i]}
            else:
                if position["side"] == "long" and (signal_type == "exit_long" or signal_type == "entry_long"):
                    if exit_long(i):
                        pnl = closes[i] - position["price"]
                        trades.append(pnl)
                        position = None
                elif position["side"] == "short" and (signal_type == "exit_short" or signal_type == "entry_short"):
                    if exit_short(i):
                        pnl = position["price"] - closes[i]
                        trades.append(pnl)
                        position = None

        if position is not None:
            # force close at last price
            pnl = closes[-1] - position["price"] if position["side"] == "long" else position["price"] - closes[-1]
            trades.append(pnl)

        if not trades:
            win_rate = 0.0
            profit_factor = 0.0
            sharpe = 0.0
            score = 20.0
        else:
            wins = [t for t in trades if t > 0]
            losses = [t for t in trades if t <= 0]
            win_rate = len(wins) / len(trades) if trades else 0.0
            gross_profit = sum(wins) if wins else 0.0
            gross_loss = -sum(losses) if losses else 0.0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit if gross_profit > 0 else 0.0

            # per-trade returns
            returns = trades
            if len(returns) > 1:
                avg_ret = mean(returns)
                vol_ret = stdev(returns) if len(returns) > 2 else abs(avg_ret)
                sharpe = avg_ret / vol_ret if vol_ret else 0.0
            else:
                sharpe = 0.0

            score = (
                win_rate * 100 * 0.6
                + min(profit_factor, 4.0) * 15
                + min(len(trades), 200) * 0.1
            )
            score = max(20.0, min(90.0, score))

        return {
            "indicator": indicator,
            "params": params,
            "signal_type": signal_type,
            "score": score,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "trades": len(trades),
        }

    def stop(self) -> None:
        """Request graceful stop of optimization."""
        self._stop_requested = True
        logger.info("Stop requested for Stage 2 optimization")
