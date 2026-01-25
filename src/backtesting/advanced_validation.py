"""Advanced validation utilities: OOS split, market phases, walk-forward.

Lightweight implementations to satisfy project plan items without requiring
heavy optimization pipelines. Uses simple candle-based scoring (EMA/RSI) to
derive robustness metrics. Can be swapped with full BacktestEngine later.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Data classes


@dataclass
class WalkForwardWindow:
    idx: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime


@dataclass
class ValidationResult:
    train_score: float
    test_score: float
    degradation_pct: float
    is_overfit: bool
    params: Optional[dict] = None


@dataclass
class MarketPhase:
    start: datetime
    end: datetime
    phase: str  # BULL/BEAR/SIDEWAYS
    confidence: float


# ---------------------------------------------------------------------------
# Shared scoring helper


def _compute_score(candles: pd.DataFrame) -> float:
    """Simple, deterministic score based on EMA/RSI profile.

    Keeps runtime small while providing a monotone metric for comparisons.
    """

    if candles.empty or len(candles) < 20:
        return 0.0

    close = candles["close"].astype(float)
    ema_fast = close.ewm(span=10).mean()
    ema_slow = close.ewm(span=30).mean()
    delta = close.diff().fillna(0)
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean().replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    # Basic features
    trend = (ema_fast > ema_slow).mean()
    momentum = (rsi > 55).mean()
    volatility = close.pct_change().std()

    score = (trend * 50) + (momentum * 30) + (max(0.0, 0.02 - volatility) * 1000)
    return float(np.clip(score, 0, 100))


# ---------------------------------------------------------------------------
# Out-of-sample validation


class OutOfSampleValidator:
    def __init__(self, df: pd.DataFrame, split_ratio: float = 0.7, scorer=_compute_score):
        self.df = df.sort_index()
        self.split_ratio = split_ratio
        self.scorer = scorer

    def validate(self) -> ValidationResult:
        split_idx = int(len(self.df) * self.split_ratio)
        train = self.df.iloc[:split_idx]
        test = self.df.iloc[split_idx:]

        train_score = self.scorer(train)
        test_score = self.scorer(test)
        degradation = 0.0 if train_score == 0 else (train_score - test_score) / train_score

        return ValidationResult(
            train_score=train_score,
            test_score=test_score,
            degradation_pct=degradation * 100,
            is_overfit=degradation > 0.30,
            params=None,
        )


# ---------------------------------------------------------------------------
# Market phase analysis


class MarketPhaseAnalyzer:
    def __init__(self, df: pd.DataFrame, scorer=_compute_score):
        self.df = df.sort_index()
        self.scorer = scorer

    def detect_phases(self, window_days: int = 30) -> List[MarketPhase]:
        phases: List[MarketPhase] = []
        if self.df.empty:
            return phases

        close = self.df["close"].astype(float)
        sma50 = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()
        adx = self._calc_adx(window=14)

        start = self.df.index.min()
        end = self.df.index.max()
        current = start

        while current < end:
            seg_end = min(end, current + timedelta(days=window_days))
            segment = self.df.loc[current:seg_end]
            if segment.empty:
                break
            seg_adx = adx.loc[current:seg_end].mean()
            seg_sma50 = sma50.loc[segment.index].iloc[-1]
            seg_sma200 = sma200.loc[segment.index].iloc[-1]

            if np.isnan(seg_adx) or np.isnan(seg_sma50) or np.isnan(seg_sma200):
                phase_type = "SIDEWAYS"
            elif seg_adx < 20:
                phase_type = "SIDEWAYS"
            elif seg_sma50 > seg_sma200:
                phase_type = "BULL"
            else:
                phase_type = "BEAR"

            confidence = float(min(1.0, max(0.0, (seg_adx or 0) / 50)))
            phases.append(MarketPhase(start=current, end=seg_end, phase=phase_type, confidence=confidence))
            current = seg_end

        return phases

    def analyze(self, params: Optional[dict] = None) -> Dict[str, Dict[str, float]]:
        phases = self.detect_phases()
        results: Dict[str, Dict[str, float]] = {}
        for phase in phases:
            seg = self.df.loc[phase.start:phase.end]
            score = self.scorer(seg)
            results.setdefault(phase.phase, {"score_sum": 0, "count": 0, "trades": 0})
            results[phase.phase]["score_sum"] += score
            results[phase.phase]["count"] += 1
            results[phase.phase]["trades"] += max(1, len(seg) // 50)

        # Average scores
        for phase_type, data in results.items():
            cnt = data["count"] or 1
            data["avg_score"] = data["score_sum"] / cnt
        return results

    def _calc_adx(self, window: int = 14) -> pd.Series:
        df = self.df
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)

        plus_dm = high.diff()
        minus_dm = low.diff().abs()

        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(window).mean()
        plus_di = 100 * (plus_dm.rolling(window).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window).mean() / atr)
        adx = (abs(plus_di - minus_di) / (plus_di + minus_di)).rolling(window).mean() * 100
        return adx


# ---------------------------------------------------------------------------
# Walk-forward analysis (simplified)


class WalkForwardAnalyzer:
    def __init__(self, df: pd.DataFrame, train_days: int = 60, test_days: int = 15, step_days: int = 15, max_trials: int = 50, scorer=_compute_score):
        self.df = df.sort_index()
        self.train_days = train_days
        self.test_days = test_days
        self.step_days = step_days
        self.max_trials = max_trials
        self.scorer = scorer

    def run(self) -> Dict:
        if self.df.empty:
            return {"windows": [], "wfe": 0, "consistency": 0, "robustness": 0}

        windows = self._build_windows()
        results = []
        for w in windows:
            train = self.df.loc[w.train_start:w.train_end]
            test = self.df.loc[w.test_start:w.test_end]
            if train.empty or test.empty:
                continue
            train_score = self.scorer(train)
            test_score = self.scorer(test)
            wfe = test_score / train_score if train_score else 0
            results.append({
                "window": w.idx,
                "period": (w.train_start, w.test_end),
                "train_score": train_score,
                "test_score": test_score,
                "wfe": wfe,
            })

        if not results:
            return {"windows": [], "wfe": 0, "consistency": 0, "robustness": 0}

        wfe_vals = [r["wfe"] for r in results]
        robustness = sum(1 for r in wfe_vals if r > 0.5) / len(wfe_vals) if wfe_vals else 0
        consistency = float(np.std(wfe_vals)) if len(wfe_vals) > 1 else 0.0

        return {
            "windows": results,
            "wfe": float(np.mean(wfe_vals)),
            "consistency": consistency,
            "robustness": robustness,
        }

    def _build_windows(self) -> List[WalkForwardWindow]:
        windows: List[WalkForwardWindow] = []
        start = self.df.index.min()
        end = self.df.index.max()
        idx = 1
        cur_train_start = start

        while cur_train_start < end:
            train_end = cur_train_start + timedelta(days=self.train_days)
            test_end = train_end + timedelta(days=self.test_days)
            if test_end > end:
                break
            windows.append(
                WalkForwardWindow(
                    idx=idx,
                    train_start=cur_train_start,
                    train_end=train_end,
                    test_start=train_end,
                    test_end=test_end,
                )
            )
            idx += 1
            cur_train_start += timedelta(days=self.step_days)

            if idx > self.max_trials:  # safety guard
                break
        return windows


__all__ = [
    "WalkForwardWindow",
    "MarketPhase",
    "ValidationResult",
    "OutOfSampleValidator",
    "MarketPhaseAnalyzer",
    "WalkForwardAnalyzer",
]
