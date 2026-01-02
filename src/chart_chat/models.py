"""Data models for Chart Analysis Chatbot.

Contains Pydantic models for chat messages, analysis results,
and AI response structures.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageRole(Enum):
    """Role of a chat message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message in the conversation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class TrendDirection(Enum):
    """Direction of the current trend."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SignalStrength(Enum):
    """Strength of a signal or level."""

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class SupportResistanceLevel(BaseModel):
    """Support or Resistance price level."""

    price: float
    strength: SignalStrength
    level_type: str  # "support" or "resistance"
    touches: int = 0
    description: str = ""


class EntryExitRecommendation(BaseModel):
    """Entry or Exit recommendation from AI analysis."""

    action: str  # "long_entry", "short_entry", "exit_long", "exit_short", "hold"
    price: float | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    urgency: str = "normal"  # "immediate", "normal", "wait"


class RiskAssessment(BaseModel):
    """Risk assessment for a potential trade."""

    stop_loss: float | None = None
    take_profit: float | None = None
    risk_reward_ratio: float | None = None
    position_size_hint: str | None = None  # "small", "normal", "large"
    max_loss_pct: float | None = None
    warnings: list[str] = Field(default_factory=list)


class PatternInfo(BaseModel):
    """Identified chart pattern."""

    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    implication: str  # "bullish", "bearish", "neutral"
    description: str = ""


class ChartAnalysisResult(BaseModel):
    """Comprehensive chart analysis result from AI.

    This is the structured output returned by the AI when performing
    a full chart analysis.
    """

    # Trend Analysis
    trend_direction: TrendDirection
    trend_strength: SignalStrength
    trend_description: str

    # Key Levels
    support_levels: list[SupportResistanceLevel] = Field(default_factory=list)
    resistance_levels: list[SupportResistanceLevel] = Field(default_factory=list)

    # Entry/Exit Recommendation
    recommendation: EntryExitRecommendation

    # Risk Assessment
    risk_assessment: RiskAssessment

    # Pattern Recognition
    patterns_identified: list[PatternInfo] = Field(default_factory=list)

    # Indicator Summary
    indicator_summary: str

    # Overall Assessment
    overall_sentiment: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)

    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str = ""
    timeframe: str = ""

    def to_markdown(self) -> str:
        """Convert analysis result to readable Markdown."""
        lines = [
            f"# Chart Analysis: {self.symbol} ({self.timeframe})",
            f"*Generated: {self.analysis_timestamp.strftime('%Y-%m-%d %H:%M')}*",
            "",
            "## Trend",
            f"**Direction:** {(self.trend_direction.value if hasattr(self.trend_direction, 'value') else self.trend_direction).upper()} "
            f"({self.trend_strength.value if hasattr(self.trend_strength, 'value') else self.trend_strength})",
            f"{self.trend_description}",
            "",
            "## Key Levels",
        ]

        if self.support_levels:
            lines.append("**Support:**")
            for level in self.support_levels:
                strength = level.strength.value if hasattr(level.strength, 'value') else level.strength
                lines.append(f"- {level.price:.2f} ({strength})")

        if self.resistance_levels:
            lines.append("**Resistance:**")
            for level in self.resistance_levels:
                strength = level.strength.value if hasattr(level.strength, 'value') else level.strength
                lines.append(f"- {level.price:.2f} ({strength})")

        lines.extend([
            "",
            "## Recommendation",
            f"**Action:** {self.recommendation.action.replace('_', ' ').title()}",
            f"**Confidence:** {self.recommendation.confidence:.0%}",
            f"**Reasoning:** {self.recommendation.reasoning}",
            "",
            "## Risk Assessment",
        ])

        if self.risk_assessment.stop_loss:
            lines.append(f"- Stop Loss: {self.risk_assessment.stop_loss:.2f}")
        if self.risk_assessment.take_profit:
            lines.append(f"- Take Profit: {self.risk_assessment.take_profit:.2f}")
        if self.risk_assessment.risk_reward_ratio:
            lines.append(f"- Risk/Reward: {self.risk_assessment.risk_reward_ratio:.2f}")

        if self.patterns_identified:
            lines.extend(["", "## Patterns"])
            for pattern in self.patterns_identified:
                lines.append(
                    f"- **{pattern.name}** ({pattern.confidence:.0%}) - "
                    f"{pattern.implication}"
                )

        lines.extend([
            "",
            "## Indicators",
            self.indicator_summary,
            "",
            f"**Overall Confidence:** {self.confidence_score:.0%}",
        ])

        if self.warnings:
            lines.extend(["", "## Warnings"])
            for warning in self.warnings:
                lines.append(f"- {warning}")

        return "\n".join(lines)


class QuickAnswerResult(BaseModel):
    """Quick answer for conversational queries."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    markings_response: Any | None = None  # CompactAnalysisResponse from chart_markings
