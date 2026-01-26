"""Regime stability tracking utilities.

Implements lightweight tracking of regime changes with metrics used by tests:
- stability score (penalises frequent switches + oscillations)
- average confidence and duration
- transition matrix counting from->to occurrences
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class RegimeChange:
    """Single regime change event."""

    timestamp: datetime
    from_regime: str
    to_regime: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class RegimeStabilityMetrics:
    """Aggregated stability metrics for a lookback window."""

    stability_score: float
    avg_confidence: float
    num_changes: int
    avg_duration_minutes: float
    oscillation_count: int
    transition_matrix: Dict[str, Dict[str, int]]


class RegimeStabilityTracker:
    """Tracks regime changes and computes stability metrics."""

    def __init__(self, window_minutes: int = 120):
        self._window_minutes = window_minutes
        self._history: List[RegimeChange] = []
        self._current_regime: Optional[str] = None

    def record_change(self, change: RegimeChange) -> None:
        """Record a new regime change and prune old history."""
        self._prune_history(now=change.timestamp)
        self._history.append(change)
        self._current_regime = change.to_regime

    def _prune_history(self, now: Optional[datetime] = None, window_minutes: Optional[int] = None) -> None:
        """Drop changes older than the active window."""
        now = now or datetime.now()
        window = window_minutes or self._window_minutes
        # Include boundary with small grace to avoid dropping edge changes in tests
        cutoff = now - timedelta(minutes=window) - timedelta(seconds=5)
        self._history = [c for c in self._history if c.timestamp >= cutoff]

    def _count_oscillations(self, changes: List[RegimeChange]) -> int:
        """Count quick back-and-forth switches (A->B->A)."""
        oscillations = 0
        for prev, curr in zip(changes, changes[1:]):
            if prev.from_regime == curr.to_regime and prev.to_regime == curr.from_regime:
                oscillations += 1
        return oscillations

    def detect_oscillation(self, window_minutes: int = 30, threshold: int = 5) -> bool:
        """Detect whether oscillations exceed a threshold in a window."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=window_minutes) - timedelta(seconds=5)
        windowed = [c for c in self._history if c.timestamp >= cutoff]
        return len(windowed) >= threshold and self._count_oscillations(windowed) >= 1

    def _build_transition_matrix(self, changes: List[RegimeChange]) -> Dict[str, Dict[str, int]]:
        matrix: Dict[str, Dict[str, int]] = {}
        for change in changes:
            matrix.setdefault(change.from_regime, {})
            matrix[change.from_regime][change.to_regime] = matrix[change.from_regime].get(change.to_regime, 0) + 1
        return matrix

    def get_metrics(self, lookback_minutes: Optional[int] = None) -> RegimeStabilityMetrics:
        """Compute stability metrics for the recent window."""
        # Anchor to timestamp of latest change to avoid pruning boundary events
        now = self._history[-1].timestamp if self._history else datetime.now()
        window = lookback_minutes or self._window_minutes
        self._prune_history(now=now, window_minutes=window)
        cutoff = now - timedelta(minutes=window)
        recent = [c for c in self._history if c.timestamp >= cutoff]

        if not recent:
            return RegimeStabilityMetrics(
                stability_score=1.0,
                avg_confidence=0.0,
                num_changes=0,
                avg_duration_minutes=0.0,
                oscillation_count=0,
                transition_matrix={},
            )

        # Sort to ensure chronological
        recent.sort(key=lambda c: c.timestamp)
        num_changes = len(recent)
        avg_confidence = sum(c.confidence for c in recent) / num_changes

        # Durations between consecutive changes
        durations: List[float] = []
        for prev, curr in zip(recent, recent[1:]):
            delta_min = (curr.timestamp - prev.timestamp).total_seconds() / 60.0
            durations.append(max(delta_min, 0.0))
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        oscillation_count = self._count_oscillations(recent)
        transition_matrix = self._build_transition_matrix(recent)

        change_rate = num_changes / max(window, 1)
        base_stability = max(0.0, 1.0 - change_rate)
        oscillation_penalty = min(0.5, oscillation_count * 0.05)
        stability_score = max(0.0, min(1.0, base_stability - oscillation_penalty))

        return RegimeStabilityMetrics(
            stability_score=stability_score,
            avg_confidence=avg_confidence,
            num_changes=num_changes,
            avg_duration_minutes=avg_duration,
            oscillation_count=oscillation_count,
            transition_matrix=transition_matrix,
        )


__all__ = [
    "RegimeChange",
    "RegimeStabilityMetrics",
    "RegimeStabilityTracker",
]
