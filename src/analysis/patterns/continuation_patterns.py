"""Continuation pattern detectors: Triangle and Flag/Pennant (simplified)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from .named_patterns import Pattern, PatternDetector
from .pivot_engine import Pivot


@dataclass
class TriangleParams:
    max_slope_diff: float = 5.0  # pragmatic: allow steep slopes, focus on range shrink
    min_points: int = 4  # number of pivots required


class TriangleDetector(PatternDetector):
    """Detects contracting triangles from alternating pivots."""

    def __init__(self, params: TriangleParams | None = None):
        self.params = params or TriangleParams()

    def detect(self, pivots: List[Pivot]) -> List[Pattern]:
        if len(pivots) < self.params.min_points:
            return []
        patterns: List[Pattern] = []
        # sliding window of 4 pivots: high-low-high-low or low-high-low-high
        for i in range(len(pivots) - 3):
            seq = pivots[i : i + 4]
            types = [p.type for p in seq]
            if types not in (["high", "low", "high", "low"], ["low", "high", "low", "high"]):
                continue
            upper = [p for p in seq if p.type == "high"]
            lower = [p for p in seq if p.type == "low"]
            if len(upper) < 2 or len(lower) < 2:
                continue
            # contracting condition: highs falling, lows rising OR range shrink > 20%
            contracting = upper[1].price <= upper[0].price and lower[1].price >= lower[0].price
            upper_slope = (upper[1].price - upper[0].price) / max(1, (upper[1].idx - upper[0].idx))
            lower_slope = (lower[1].price - lower[0].price) / max(1, (lower[1].idx - lower[0].idx))
            range0 = upper[0].price - lower[0].price
            range1 = upper[1].price - lower[1].price
            shrink = (range0 - range1) / max(range0, 1e-9)
            if (contracting or shrink >= 0.2) and abs(upper_slope - lower_slope) <= self.params.max_slope_diff:
                score = self.score_raw(upper_slope, lower_slope)
                patterns.append(
                    Pattern("Triangle", seq, score, {"upper_slope": upper_slope, "lower_slope": lower_slope})
                )
        return patterns

    def score_raw(self, upper_slope: float, lower_slope: float) -> float:
        opening = abs(upper_slope - lower_slope)
        return max(10.0, 100.0 - opening * 1000)

    def score(self, pattern: Pattern) -> float:
        return pattern.score

    def lines(self, pattern: Pattern) -> Dict[str, list]:
        hi = [p for p in pattern.pivots if p.type == "high"]
        lo = [p for p in pattern.pivots if p.type == "low"]
        return {
            "upper": [(hi[0].idx, hi[0].price), (hi[-1].idx, hi[-1].price)],
            "lower": [(lo[0].idx, lo[0].price), (lo[-1].idx, lo[-1].price)],
        }


@dataclass
class FlagParams:
    max_channel_slope: float = 2.0  # allow steeper pullback slope pragmatisch
    min_length: int = 3
    max_retrace: float = 1.0


class FlagDetector(PatternDetector):
    """Detect simple flags: impulsive move followed by small channel pullback."""

    def __init__(self, params: FlagParams | None = None):
        self.params = params or FlagParams()

    def detect(self, pivots: List[Pivot]) -> List[Pattern]:
        patterns: List[Pattern] = []
        if len(pivots) < 3:
            return patterns
        for i in range(len(pivots) - 2):
            p1, p2, p3 = pivots[i : i + 3]
            move = p2.price - p1.price
            pull = p3.price - p2.price
            if abs(move) < 1e-6:
                continue
            # Require impulse then smaller corrective move opposite sign
            if move > 0 and pull < 0 or move < 0 and pull > 0:
                slope = pull / max(1, (p3.idx - p2.idx))
                retrace = abs(pull) / max(abs(move), 1e-9)
                if retrace <= self.params.max_retrace:
                    score = self.score_raw(move, pull, slope)
                    patterns.append(Pattern("Flag", [p1, p2, p3], score, {"slope": slope, "retrace": retrace}))
        return patterns

    def score_raw(self, move: float, pull: float, slope: float) -> float:
        retrace = abs(pull) / max(abs(move), 1e-9)
        base = (1 - min(retrace, 1)) * 70
        penalty = abs(slope) * 10
        return max(5.0, min(100.0, base - penalty + 30))

    def score(self, pattern: Pattern) -> float:
        return pattern.score

    def lines(self, pattern: Pattern) -> Dict[str, list]:
        piv = pattern.pivots
        return {
            "impulse": [(piv[0].idx, piv[0].price), (piv[1].idx, piv[1].price)],
            "flag": [(piv[1].idx, piv[1].price), (piv[2].idx, piv[2].price)],
        }
