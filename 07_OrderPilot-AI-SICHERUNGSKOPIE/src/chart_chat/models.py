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
        """Convert analysis result to readable Markdown (refactored)."""
        var_lines = self._build_variable_format_summary()
        lines = self._build_markdown_report(var_lines)
        return "\n".join(lines)

    def _build_variable_format_summary(self) -> list[str]:
        """Build variable-format summary for UI parsing."""
        var_lines = []

        # Trend
        direction = self._get_enum_value(self.trend_direction)
        strength = self._get_enum_value(self.trend_strength)
        var_lines.append(f"[#Trend; {direction}]")
        var_lines.append(f"[#Trend-Stärke; {strength}]")

        # Support / Resistance
        for level in self.support_levels:
            strength_txt = self._get_enum_value(level.strength)
            var_lines.append(f"[#Support; {level.price:.2f} ({strength_txt})]")
        for level in self.resistance_levels:
            strength_txt = self._get_enum_value(level.strength)
            var_lines.append(f"[#Resistance; {level.price:.2f} ({strength_txt})]")

        # Risk markers
        if self.risk_assessment.stop_loss:
            var_lines.append(f"[#Stop Loss; {self.risk_assessment.stop_loss:.2f}]")
        if self.risk_assessment.take_profit:
            var_lines.append(f"[#Take Profit; {self.risk_assessment.take_profit:.2f}]")

        # Recommendation
        var_lines.append(f"[#Aktion; {self.recommendation.action}]")
        var_lines.append(f"[#Konfidenz; {self.recommendation.confidence:.0%}]")

        return var_lines

    def _build_markdown_report(self, var_lines: list[str]) -> list[str]:
        """Build full markdown report."""
        lines = [
            "\n".join(var_lines),
            "",
            f"# Chart Analysis: {self.symbol} ({self.timeframe})",
            f"*Generated: {self.analysis_timestamp.strftime('%Y-%m-%d %H:%M')}*",
            "",
        ]

        self._add_trend_section(lines)
        self._add_key_levels_section(lines)
        self._add_recommendation_section(lines)
        self._add_risk_assessment_section(lines)
        self._add_patterns_section(lines)
        self._add_indicators_section(lines)
        self._add_warnings_section(lines)

        return lines

    def _add_trend_section(self, lines: list[str]) -> None:
        """Add trend section to markdown."""
        direction = self._get_enum_value(self.trend_direction).upper()
        strength = self._get_enum_value(self.trend_strength)
        lines.extend([
            "## Trend",
            f"**Direction:** {direction} ({strength})",
            f"{self.trend_description}",
            "",
        ])

    def _add_key_levels_section(self, lines: list[str]) -> None:
        """Add support/resistance levels to markdown."""
        lines.append("## Key Levels")

        if self.support_levels:
            lines.append("**Support:**")
            for level in self.support_levels:
                strength = self._get_enum_value(level.strength)
                lines.append(f"- {level.price:.2f} ({strength})")

        if self.resistance_levels:
            lines.append("**Resistance:**")
            for level in self.resistance_levels:
                strength = self._get_enum_value(level.strength)
                lines.append(f"- {level.price:.2f} ({strength})")

        lines.append("")

    def _add_recommendation_section(self, lines: list[str]) -> None:
        """Add recommendation section to markdown."""
        lines.extend([
            "## Recommendation",
            f"**Action:** {self.recommendation.action.replace('_', ' ').title()}",
            f"**Confidence:** {self.recommendation.confidence:.0%}",
            f"**Reasoning:** {self.recommendation.reasoning}",
            "",
        ])

    def _add_risk_assessment_section(self, lines: list[str]) -> None:
        """Add risk assessment to markdown."""
        lines.append("## Risk Assessment")

        if self.risk_assessment.stop_loss:
            lines.append(f"- Stop Loss: {self.risk_assessment.stop_loss:.2f}")
        if self.risk_assessment.take_profit:
            lines.append(f"- Take Profit: {self.risk_assessment.take_profit:.2f}")
        if self.risk_assessment.risk_reward_ratio:
            lines.append(f"- Risk/Reward: {self.risk_assessment.risk_reward_ratio:.2f}")

        lines.append("")

    def _add_patterns_section(self, lines: list[str]) -> None:
        """Add identified patterns to markdown."""
        if self.patterns_identified:
            lines.append("## Patterns")
            for pattern in self.patterns_identified:
                lines.append(
                    f"- **{pattern.name}** ({pattern.confidence:.0%}) - {pattern.implication}"
                )
            lines.append("")

    def _add_indicators_section(self, lines: list[str]) -> None:
        """Add indicators summary to markdown."""
        lines.extend([
            "## Indicators",
            self.indicator_summary,
            "",
            f"**Overall Confidence:** {self.confidence_score:.0%}",
        ])

    def _add_warnings_section(self, lines: list[str]) -> None:
        """Add warnings to markdown if present."""
        if self.warnings:
            lines.append("")
            lines.append("## Warnings")
            for warning in self.warnings:
                lines.append(f"- {warning}")

    @staticmethod
    def _get_enum_value(value):
        """Get enum value or return as-is."""
        return value.value if hasattr(value, 'value') else value


class QuickAnswerResult(BaseModel):
    """Quick answer for conversational queries."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    markings_response: Any | None = None  # CompactAnalysisResponse from chart_markings
