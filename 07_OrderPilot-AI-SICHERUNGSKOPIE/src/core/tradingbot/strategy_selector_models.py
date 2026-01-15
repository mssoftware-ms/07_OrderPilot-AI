"""
Strategy Selector Models - Selection Result Models.

Refactored from strategy_selector.py.

Contains:
- SelectionResult: Result of strategy selection
- SelectionSnapshot: Snapshot of strategy selection for persistence
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .models import DirectionalBias, RegimeType, VolatilityLevel


class SelectionResult(BaseModel):
    """Result of strategy selection.

    NOTE: Daily strategy selection is DISABLED for daytrading.
    Instead uses `daily_bias` for directional guidance only.
    Current signal score can override bias if above threshold.
    """

    selected_strategy: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None

    # Selection context
    regime: RegimeType
    volatility: VolatilityLevel
    selection_date: datetime = Field(default_factory=datetime.utcnow)

    # Candidate info
    candidates_evaluated: int = 0
    candidates_passed: int = 0

    # Scores
    strategy_scores: dict[str, float] = Field(default_factory=dict)

    # Walk-forward summary
    wf_result: dict | None = None

    # Lock info
    locked_until: datetime | None = None

    # Directional bias (replaces fixed daily strategy for daytrading)
    daily_bias: DirectionalBias = Field(
        default=DirectionalBias.NEUTRAL,
        description="Daily directional tendency (long/short/neutral). "
        "Does NOT lock strategy, only suggests preferred direction."
    )
    bias_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in daily bias (0-1)"
    )
    bias_override_threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Signal score threshold to override daily bias (default 80%)"
    )


class SelectionSnapshot(BaseModel):
    """Snapshot of strategy selection for persistence."""

    selection_date: datetime
    symbol: str
    selected_strategy: str
    regime: str
    volatility: str

    # Performance at selection time
    in_sample_pf: float
    in_sample_wr: float
    oos_pf: float | None

    # Scores
    composite_score: float
    robustness_score: float

    # Configuration used
    training_window_days: int
    test_window_days: int
