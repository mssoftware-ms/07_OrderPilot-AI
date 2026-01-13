"""Fast Optimizer for Indicator Parameters.

Implements the fast optimization logic using the CandidateSpace.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any

from src.analysis.entry_signals.entry_signal_engine import (
    OptimParams,
    calculate_features,
    detect_regime,
    generate_entries,
    EntryEvent,
    EntrySide,
)
from src.analysis.indicator_optimization.candidate_space import CandidateSpace

logger = logging.getLogger(__name__)


class FastOptimizer:
    """Fast random search optimizer."""

    def __init__(self, candidate_space: CandidateSpace | None = None) -> None:
        """Initialize the optimizer.
        
        Args:
            candidate_space: Optional custom candidate space.
        """
        self.space = candidate_space or CandidateSpace()

    def optimize(
        self,
        candles: list[dict[str, Any]],
        base_params: OptimParams,
        budget_ms: int = 1200,
        seed: int | None = None,
    ) -> OptimParams:
        """Run fast optimization.

        Args:
            candles: Candle data.
            base_params: Starting parameters.
            budget_ms: Time budget in ms.
            seed: Random seed.

        Returns:
            Optimized parameters.
        """
        if seed is not None:
            random.seed(seed)

        t_end = time.time() + (budget_ms / 1000.0)
        best_params = base_params
        best_score = -1e9

        trials = 0
        while time.time() < t_end:
            trials += 1
            # Sample new params
            p = self.space.sample_params(base_params)

            # Calculate and evaluate
            # Note: Features depend on params (e.g. periods), so we must recalc
            feats = calculate_features(candles, p)
            reg = detect_regime(feats, p)
            ents = generate_entries(candles, feats, reg, p)
            score = self._evaluate_entries(candles, feats, ents, p)

            if score > best_score:
                best_score = score
                best_params = p

        logger.debug(
            "FastOptimizer: %d trials, best score: %.3f", 
            trials, 
            best_score
        )
        return best_params

    def _evaluate_entries(
        self,
        candles: list[dict[str, Any]],
        features: dict[str, list[float]],
        entries: list[EntryEvent],
        params: OptimParams,
    ) -> float:
        """Proxy objective function.
        
        Copy of the evaluation logic from entry_signal_engine to keep it self-contained
        or we could import it if exposed. For now, reproducing it here to decouple
        optimization logic from the engine.
        """
        if not entries:
            return -9999.0  # Hard penalty

        highs = features.get("highs", [])
        lows = features.get("lows", [])
        closes = features.get("closes", [])
        atr = features.get("atr", [])

        # Timestamp map
        ts_to_idx: dict[Any, int] = {}
        for i, c in enumerate(candles):
            ts_to_idx[c.get("timestamp")] = i

        wins = 0
        resolved = 0

        for e in entries:
            idx = ts_to_idx.get(e.timestamp)
            if idx is None or idx >= len(closes):
                continue
            
            a = max(1e-12, atr[idx])
            tp = params.eval_tp_atr * a
            sl = params.eval_sl_atr * a
            entry_price = closes[idx]

            end = min(len(closes) - 1, idx + params.eval_horizon_bars)
            hit = None
            
            for j in range(idx + 1, end + 1):
                if e.side == EntrySide.LONG:
                    if j < len(lows) and lows[j] <= entry_price - sl:
                        hit = False
                        break
                    if j < len(highs) and highs[j] >= entry_price + tp:
                        hit = True
                        break
                else:
                    if j < len(highs) and highs[j] >= entry_price + sl:
                        hit = False
                        break
                    if j < len(lows) and lows[j] <= entry_price - tp:
                        hit = True
                        break

            if hit is not None:
                resolved += 1
                if hit:
                    wins += 1

        if resolved < max(3, int(params.min_trades_gate * 0.6)):
            return -5000.0

        hit_rate = wins / max(1, resolved)
        
        # Soft trade-count shaping
        tc = len(entries)
        target = max(1, params.target_trades_soft)
        trade_penalty = abs(tc - target) / target

        avg_conf = sum(e.confidence for e in entries) / max(1, len(entries))

        score = (hit_rate * 2.0) + (avg_conf * 0.5) - (trade_penalty * 0.7)

        # Diversity bonus
        has_long = any(e.side == EntrySide.LONG for e in entries)
        has_short = any(e.side == EntrySide.SHORT for e in entries)
        if has_long and has_short:
            score += 0.05

        return score
