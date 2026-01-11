"""Entry Analysis Copilot - AI-Powered Trading Insights.

Provides AI-powered analysis and recommendations for entry signals:
- Entry quality assessment
- Risk/reward analysis
- Market context interpretation
- Trade improvement suggestions

Phase 5: KI-Copilot Integration
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .types import AnalysisResult, EntryEvent, EntrySide, IndicatorSet, RegimeType
from .validation import ValidationResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Response Models (Pydantic for structured AI output)
# ─────────────────────────────────────────────────────────────────


class SignalQuality(str, Enum):
    """Quality rating for entry signals."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    AVOID = "avoid"


class EntryAssessment(BaseModel):
    """AI assessment of a single entry signal."""

    quality: SignalQuality = Field(description="Overall quality rating")
    confidence_adjustment: float = Field(
        description="Suggested adjustment to confidence (-0.2 to +0.2)",
        ge=-0.2,
        le=0.2,
    )
    strengths: list[str] = Field(
        description="Key strengths of this entry (2-4 items)",
        max_length=4,
    )
    weaknesses: list[str] = Field(
        description="Key weaknesses or risks (2-4 items)",
        max_length=4,
    )
    trade_suggestion: str = Field(
        description="Specific suggestion for this trade (1-2 sentences)"
    )


class AnalysisSummary(BaseModel):
    """AI summary of the overall analysis."""

    market_assessment: str = Field(
        description="Brief assessment of current market conditions (2-3 sentences)"
    )
    regime_confidence: float = Field(
        description="Confidence in detected regime (0-1)",
        ge=0,
        le=1,
    )
    best_entry_idx: int = Field(
        description="Index of the best entry (0-based), -1 if none recommended"
    )
    overall_bias: str = Field(
        description="Overall market bias: bullish, bearish, or neutral"
    )
    key_levels: list[float] = Field(
        description="Key price levels to watch (support/resistance)",
        max_length=4,
    )
    risk_warning: str | None = Field(
        description="Important risk warning if any, otherwise null",
        default=None,
    )


class CopilotResponse(BaseModel):
    """Complete copilot response for entry analysis."""

    summary: AnalysisSummary = Field(description="Overall analysis summary")
    entry_assessments: list[EntryAssessment] = Field(
        description="Assessment for each entry signal",
        max_length=10,
    )
    recommended_action: str = Field(
        description="Recommended action: trade, wait, or avoid"
    )
    reasoning: str = Field(
        description="Brief reasoning for the recommendation (2-3 sentences)"
    )


class ValidationReview(BaseModel):
    """AI review of validation results."""

    is_reliable: bool = Field(description="Whether the validation results are reliable")
    concerns: list[str] = Field(
        description="Concerns about the validation (if any)",
        max_length=4,
    )
    suggestions: list[str] = Field(
        description="Suggestions for improvement",
        max_length=4,
    )
    overfitting_risk: str = Field(
        description="Overfitting risk level: low, medium, or high"
    )
    production_ready: bool = Field(
        description="Whether this setup is ready for live trading"
    )


# ─────────────────────────────────────────────────────────────────
# Copilot Configuration
# ─────────────────────────────────────────────────────────────────


@dataclass
class CopilotConfig:
    """Configuration for the Entry Copilot.

    Attributes:
        temperature: AI temperature (0.0-1.0, lower = more deterministic).
        max_entries_to_analyze: Maximum entries to send to AI.
        use_cache: Whether to cache AI responses.
        timeout_seconds: Request timeout.
        include_validation: Include validation results in analysis.
        language: Response language (en, de).
    """

    temperature: float = 0.2
    max_entries_to_analyze: int = 5
    use_cache: bool = True
    timeout_seconds: float = 30.0
    include_validation: bool = True
    language: str = "en"


# ─────────────────────────────────────────────────────────────────
# Entry Copilot
# ─────────────────────────────────────────────────────────────────


class EntryCopilot:
    """AI-powered copilot for entry signal analysis.

    Uses the configured AI provider (OpenAI, Anthropic, Gemini)
    to provide intelligent analysis and recommendations.

    Usage:
        copilot = EntryCopilot()
        response = await copilot.analyze_entries(analysis_result, symbol, timeframe)
    """

    def __init__(self, config: CopilotConfig | None = None) -> None:
        """Initialize the copilot.

        Args:
            config: Copilot configuration.
        """
        self.config = config or CopilotConfig()
        self._service = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the AI service.

        Returns:
            True if initialization successful, False otherwise.
        """
        if self._initialized:
            return True

        try:
            from src.ai.ai_provider_factory import AIProviderFactory

            # Check if AI is enabled
            if not AIProviderFactory.is_ai_enabled():
                logger.warning("AI features are disabled in settings")
                return False

            # Create service
            self._service = AIProviderFactory.create_service()
            await self._service.initialize()
            self._initialized = True

            provider = AIProviderFactory.get_provider()
            model = AIProviderFactory.get_model(provider)
            logger.info("EntryCopilot initialized: %s / %s", provider, model)

            return True

        except Exception as e:
            logger.error("Failed to initialize EntryCopilot: %s", e)
            return False

    async def close(self) -> None:
        """Close the AI service."""
        if self._service:
            await self._service.close()
            self._service = None
            self._initialized = False

    async def analyze_entries(
        self,
        analysis: AnalysisResult,
        symbol: str,
        timeframe: str,
        validation: ValidationResult | None = None,
        candles: list[dict] | None = None,
    ) -> CopilotResponse | None:
        """Analyze entries and provide AI recommendations.

        Args:
            analysis: Analysis result with entries.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            validation: Optional validation results.
            candles: Optional recent candle data for context.

        Returns:
            CopilotResponse or None on error.
        """
        if not self._initialized:
            success = await self.initialize()
            if not success:
                return None

        if not analysis.entries:
            logger.info("No entries to analyze")
            return None

        # Build prompt
        prompt = self._build_analysis_prompt(
            analysis=analysis,
            symbol=symbol,
            timeframe=timeframe,
            validation=validation,
            candles=candles,
        )

        try:
            response = await self._service.structured_completion(
                prompt=prompt,
                response_model=CopilotResponse,
                temperature=self.config.temperature,
                use_cache=self.config.use_cache,
            )

            logger.info(
                "Copilot analysis complete: %s, best_entry=%d",
                response.recommended_action,
                response.summary.best_entry_idx,
            )

            return response

        except Exception as e:
            logger.error("Copilot analysis failed: %s", e)
            return None

    async def review_validation(
        self,
        validation: ValidationResult,
        symbol: str,
    ) -> ValidationReview | None:
        """Review validation results for reliability.

        Args:
            validation: Validation results to review.
            symbol: Trading symbol.

        Returns:
            ValidationReview or None on error.
        """
        if not self._initialized:
            success = await self.initialize()
            if not success:
                return None

        prompt = self._build_validation_prompt(validation, symbol)

        try:
            response = await self._service.structured_completion(
                prompt=prompt,
                response_model=ValidationReview,
                temperature=self.config.temperature,
                use_cache=self.config.use_cache,
            )

            logger.info(
                "Validation review: reliable=%s, production_ready=%s",
                response.is_reliable,
                response.production_ready,
            )

            return response

        except Exception as e:
            logger.error("Validation review failed: %s", e)
            return None

    async def get_quick_assessment(
        self,
        entry: EntryEvent,
        regime: RegimeType,
        symbol: str,
    ) -> EntryAssessment | None:
        """Get quick assessment of a single entry.

        Args:
            entry: Entry to assess.
            regime: Current market regime.
            symbol: Trading symbol.

        Returns:
            EntryAssessment or None on error.
        """
        if not self._initialized:
            success = await self.initialize()
            if not success:
                return None

        prompt = self._build_quick_assessment_prompt(entry, regime, symbol)

        try:
            response = await self._service.structured_completion(
                prompt=prompt,
                response_model=EntryAssessment,
                temperature=self.config.temperature,
                use_cache=self.config.use_cache,
            )

            logger.debug(
                "Quick assessment: %s quality, conf_adj=%.2f",
                response.quality.value,
                response.confidence_adjustment,
            )

            return response

        except Exception as e:
            logger.error("Quick assessment failed: %s", e)
            return None

    # ─────────────────────────────────────────────────────────────────
    # Prompt Builders
    # ─────────────────────────────────────────────────────────────────

    def _build_analysis_prompt(
        self,
        analysis: AnalysisResult,
        symbol: str,
        timeframe: str,
        validation: ValidationResult | None,
        candles: list[dict] | None,
    ) -> str:
        """Build prompt for full entry analysis."""
        # Limit entries
        entries = analysis.entries[: self.config.max_entries_to_analyze]

        # Format entries
        entries_text = self._format_entries(entries)

        # Format indicator set
        indicator_text = self._format_indicator_set(analysis.best_set)

        # Format validation if available
        validation_text = ""
        if validation and self.config.include_validation:
            validation_text = self._format_validation(validation)

        # Format recent candles for context
        candles_text = ""
        if candles and len(candles) > 0:
            candles_text = self._format_candles(candles[-10:])

        lang_note = ""
        if self.config.language == "de":
            lang_note = "\n\nPlease respond in German (Deutsch)."

        return f"""You are an expert trading analyst assistant. Analyze these entry signals and provide recommendations.

## Market Context
- **Symbol:** {symbol}
- **Timeframe:** {timeframe}
- **Detected Regime:** {analysis.regime.value}
- **Analysis Time:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

## Entry Signals ({len(entries)} entries)
{entries_text}

## Indicator Configuration
{indicator_text}

{candles_text}

{validation_text}

## Your Task
1. Assess the quality of each entry signal
2. Identify the best entry opportunity (if any)
3. Provide specific, actionable recommendations
4. Highlight any risks or concerns

Consider:
- Entry timing relative to regime
- Confidence levels and reason tags
- Risk/reward potential
- Current market conditions{lang_note}"""

    def _build_validation_prompt(
        self,
        validation: ValidationResult,
        symbol: str,
    ) -> str:
        """Build prompt for validation review."""
        folds_text = ""
        for fold in validation.folds:
            folds_text += f"""
- Fold {fold.fold_idx}: Train={fold.train_score:.3f}, Test={fold.test_score:.3f}, Ratio={fold.train_test_ratio:.2f}, Overfit={fold.is_overfit}"""

        return f"""You are an expert in trading system validation. Review these walk-forward validation results.

## Validation Summary
- **Symbol:** {symbol}
- **Folds:** {len(validation.folds)}
- **Average Train Score:** {validation.avg_train_score:.3f}
- **Average Test Score (OOS):** {validation.avg_test_score:.3f}
- **Train/Test Ratio:** {validation.avg_train_test_ratio:.2f}
- **OOS Win Rate:** {validation.oos_win_rate:.1%}
- **OOS Profit Factor:** {validation.oos_profit_factor:.2f}
- **Total OOS Trades:** {validation.total_oos_trades}
- **Validation Passed:** {validation.is_valid}
- **Seed Used:** {validation.seed_used}

## Fold Details
{folds_text}

## Failure Reasons
{chr(10).join(f"- {r}" for r in validation.failure_reasons) if validation.failure_reasons else "None"}

## Your Task
1. Assess if these results are statistically reliable
2. Identify any concerns (overfitting, data snooping, etc.)
3. Determine if this setup is production-ready
4. Suggest improvements if needed

Be critical and thorough - trader's capital is at risk."""

    def _build_quick_assessment_prompt(
        self,
        entry: EntryEvent,
        regime: RegimeType,
        symbol: str,
    ) -> str:
        """Build prompt for quick single-entry assessment."""
        dt = datetime.fromtimestamp(entry.timestamp, tz=timezone.utc)

        return f"""Quickly assess this trading entry signal:

- **Symbol:** {symbol}
- **Regime:** {regime.value}
- **Side:** {entry.side.value.upper()}
- **Time:** {dt.strftime("%Y-%m-%d %H:%M UTC")}
- **Price:** {entry.price:.4f}
- **Confidence:** {entry.confidence:.1%}
- **Reasons:** {", ".join(entry.reason_tags) if entry.reason_tags else "None"}

Provide a concise assessment with quality rating, strengths, weaknesses, and one actionable suggestion."""

    # ─────────────────────────────────────────────────────────────────
    # Formatters
    # ─────────────────────────────────────────────────────────────────

    def _format_entries(self, entries: list[EntryEvent]) -> str:
        """Format entries for prompt."""
        lines = []
        for i, entry in enumerate(entries):
            dt = datetime.fromtimestamp(entry.timestamp, tz=timezone.utc)
            reasons = ", ".join(entry.reason_tags[:3]) if entry.reason_tags else "N/A"
            lines.append(
                f"{i}. **{entry.side.value.upper()}** @ {entry.price:.4f} "
                f"({entry.confidence:.0%}) - {dt.strftime('%H:%M')} - [{reasons}]"
            )
        return "\n".join(lines)

    def _format_indicator_set(self, indicator_set: IndicatorSet | None) -> str:
        """Format indicator set for prompt."""
        if not indicator_set:
            return "No optimized indicator set available."

        lines = [f"**Set:** {indicator_set.name} (Score: {indicator_set.score:.3f})"]

        for ind in indicator_set.indicators[:3]:
            name = ind.get("name", "Unknown")
            params = ind.get("params", {})
            param_str = ", ".join(f"{k}={v}" for k, v in list(params.items())[:3])
            lines.append(f"- {name}: {param_str}")

        return "\n".join(lines)

    def _format_validation(self, validation: ValidationResult) -> str:
        """Format validation results for prompt."""
        status = "PASSED" if validation.is_valid else "FAILED"
        return f"""## Validation Results ({status})
- OOS Score: {validation.avg_test_score:.3f}
- OOS Win Rate: {validation.oos_win_rate:.1%}
- Train/Test Ratio: {validation.avg_train_test_ratio:.2f}
- Total OOS Trades: {validation.total_oos_trades}
"""

    def _format_candles(self, candles: list[dict]) -> str:
        """Format recent candles for context."""
        lines = ["## Recent Price Action (last 10 candles)"]
        for c in candles[-5:]:
            dt = datetime.fromtimestamp(c["timestamp"], tz=timezone.utc)
            change = ((c["close"] - c["open"]) / c["open"]) * 100
            direction = "▲" if change > 0 else "▼"
            lines.append(
                f"- {dt.strftime('%H:%M')}: {direction} {c['close']:.4f} ({change:+.2f}%)"
            )
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────────


async def get_entry_analysis(
    analysis: AnalysisResult,
    symbol: str,
    timeframe: str,
    validation: ValidationResult | None = None,
) -> CopilotResponse | None:
    """Convenience function for getting entry analysis.

    Args:
        analysis: Analysis result.
        symbol: Trading symbol.
        timeframe: Chart timeframe.
        validation: Optional validation results.

    Returns:
        CopilotResponse or None.
    """
    copilot = EntryCopilot()
    try:
        return await copilot.analyze_entries(analysis, symbol, timeframe, validation)
    finally:
        await copilot.close()


def run_entry_analysis_sync(
    analysis: AnalysisResult,
    symbol: str,
    timeframe: str,
    validation: ValidationResult | None = None,
) -> CopilotResponse | None:
    """Synchronous wrapper for entry analysis.

    Args:
        analysis: Analysis result.
        symbol: Trading symbol.
        timeframe: Chart timeframe.
        validation: Optional validation results.

    Returns:
        CopilotResponse or None.
    """
    return asyncio.run(get_entry_analysis(analysis, symbol, timeframe, validation))
