"""Base classes and datatypes for pattern detectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol

from .pivot_engine import Pivot


@dataclass
class Pattern:
    name: str
    pivots: List[Pivot]
    score: float
    metadata: Dict[str, float] | None = None


class PatternDetector(Protocol):
    def detect(self, pivots: List[Pivot]) -> List[Pattern]:
        ...

    def score(self, pattern: Pattern) -> float:
        ...

    def lines(self, pattern: Pattern) -> Dict[str, list]:
        ...

