"""OpenAI Models and Exceptions.

Contains exception classes and Pydantic response models for
structured outputs from OpenAI API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ==================== Exception Classes ====================

class OpenAIError(Exception):
    """Base exception for OpenAI service errors."""
    pass


class RateLimitError(OpenAIError):
    """Raised when rate limit is exceeded."""
    pass


class QuotaExceededError(OpenAIError):
    """Raised when monthly budget is exceeded."""
    pass


class SchemaValidationError(OpenAIError):
    """Raised when response doesn't match schema."""
    pass


# ==================== Response Models ====================

class OrderAnalysis(BaseModel):
    """Structured output for order analysis."""
    approved: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

    # Risk assessment
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)

    # Suggestions
    suggested_adjustments: dict[str, Any] = Field(default_factory=dict)

    # Fees and costs
    fee_impact: str
    estimated_total_cost: float

    # Metadata
    analysis_version: str = "1.0"


class AlertTriageResult(BaseModel):
    """Structured output for alert triage."""
    priority_score: float = Field(ge=0.0, le=1.0)
    action_required: bool

    # Reasoning
    reasoning: str
    key_factors: list[str]

    # Suggested actions
    suggested_actions: list[str]
    estimated_urgency: str  # immediate, high, medium, low

    # Context
    related_positions: list[str] = Field(default_factory=list)
    market_context: dict[str, Any] = Field(default_factory=dict)


class BacktestReview(BaseModel):
    """Structured output for backtest review."""
    overall_assessment: str
    performance_rating: float = Field(ge=0.0, le=10.0)

    # Key insights
    strengths: list[str]
    weaknesses: list[str]

    # Improvements
    suggested_improvements: list[dict[str, Any]]
    parameter_recommendations: dict[str, Any]

    # Risk analysis
    risk_assessment: str
    max_drawdown_analysis: str

    # Market conditions
    market_conditions_analysis: str
    adaptability_score: float = Field(ge=0.0, le=1.0)


class StrategySignalAnalysis(BaseModel):
    """Structured output for strategy signal post-analysis."""
    signal_quality: float = Field(ge=0.0, le=1.0)
    proceed: bool

    # Analysis
    technical_analysis: str
    market_conditions: str

    # Contra indicators
    warning_signals: list[str]
    confirming_signals: list[str]

    # Timing
    timing_assessment: str  # excellent, good, neutral, poor
    suggested_delay_minutes: int | None = None


class StrategyTradeAnalysis(BaseModel):
    """Structured output for strategy trade analysis after Apply Strategy."""
    # Overall assessment
    overall_assessment: str
    strategy_rating: float = Field(ge=0.0, le=10.0)
    win_rate_assessment: str

    # Trade analysis
    winning_patterns: list[str]  # What made winning trades successful
    losing_patterns: list[str]   # Why losing trades failed
    best_entry_conditions: str
    worst_entry_conditions: str

    # Improvements
    parameter_suggestions: dict[str, Any]  # e.g., {"stop_loss": 3.0, "take_profit": 6.0}
    timing_improvements: list[str]
    risk_management_tips: list[str]

    # Optimized strategy suggestion
    optimized_strategy: dict[str, Any]  # Complete suggested strategy params
    expected_improvement: str  # e.g., "Could improve win rate by ~10-15%"

    # Market fit
    market_conditions_fit: str  # trending, ranging, volatile
    recommended_timeframes: list[str]
    avoid_conditions: list[str]
