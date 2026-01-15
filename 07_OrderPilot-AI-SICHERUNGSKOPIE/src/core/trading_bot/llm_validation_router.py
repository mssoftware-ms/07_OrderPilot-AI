"""LLM Validation Router - Quick→Deep Routing and Result Building.

Refactored from 727 LOC monolith using composition pattern.

Module 3/4 of llm_validation_service.py split.

Contains:
- _run_quick_validation(): Fast validation with quick model
- _run_deep_validation(): Thorough analysis with slower model
- _build_result(): Construct LLMValidationResult from LLM response
- _create_bypass_result(): Bypass result when LLM disabled
- _create_technical_fallback(): Fallback using technical analysis
- _create_error_result(): Error result when LLM fails
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from src.core.trading_bot.llm_validation_state import (
    LLMAction,
    LLMValidationResult,
    ValidationTier,
)

if TYPE_CHECKING:
    from .market_context import MarketContext
    from .entry_score_engine import EntryScoreResult


class LLMValidationRouter:
    """Helper für LLM Validation Routing (Quick→Deep) und Result Building."""

    def __init__(self, parent):
        """
        Args:
            parent: LLMValidationService Instanz
        """
        self.parent = parent

    async def run_quick_validation(self, prompt: str) -> Dict[str, Any]:
        """Run quick validation."""
        validator = self.parent._get_ai_validator()

        # Use existing AI validator
        from .ai_validator import AIValidation

        # Create a minimal signal for the validator
        response = await validator._call_llm(prompt)

        # Ensure required fields
        return {
            "confidence": int(response.get("confidence", 50)),
            "action": response.get("action", "defer"),
            "setup_type": response.get("setup_type", "NO_SETUP"),
            "reasoning": response.get("reasoning", ""),
            "key_factors": response.get("key_factors", []),
            "risks": response.get("risks", []),
            "invalidation_level": response.get("invalidation_level"),
        }

    async def run_deep_validation(
        self, prompt: str, context: "MarketContext"
    ) -> Dict[str, Any]:
        """Run deep validation with more thorough analysis."""
        # Add deep analysis instructions
        deep_prompt = prompt + """

## DEEP ANALYSIS MODE
This is a secondary validation after quick analysis was uncertain.
Please be MORE THOROUGH:
1. Consider multiple timeframes if mentioned
2. Evaluate risk/reward carefully
3. Check for potential traps or fakeouts
4. Only APPROVE if you have HIGH conviction (>=70% confidence)
5. Default to VETO if uncertain"""

        validator = self.parent._get_ai_validator()
        response = await validator._call_llm(deep_prompt)

        return {
            "confidence": int(response.get("confidence", 40)),
            "action": response.get("action", "veto"),
            "setup_type": response.get("setup_type", "NO_SETUP"),
            "reasoning": response.get("reasoning", "Deep analysis"),
            "key_factors": response.get("key_factors", []),
            "risks": response.get("risks", []),
            "invalidation_level": response.get("invalidation_level"),
        }

    def build_result(
        self,
        action: LLMAction,
        llm_response: Dict[str, Any],
        tier: ValidationTier,
        prompt_hash: str,
        latency_ms: int,
        entry_score: Optional["EntryScoreResult"] = None,
        deep_triggered: bool = False,
    ) -> LLMValidationResult:
        """Build validation result from LLM response."""

        # Determine score modifier
        if action == LLMAction.BOOST:
            modifier = self.parent.config.boost_score_modifier
        elif action == LLMAction.CAUTION:
            modifier = self.parent.config.caution_score_modifier
        elif action == LLMAction.VETO:
            modifier = self.parent.config.veto_score_modifier
        else:
            modifier = 0.0

        # Calculate modified score
        modified_score = None
        if entry_score:
            modified_score = min(1.0, max(0.0, entry_score.final_score + modifier))

        # Get validator info
        validator = self.parent._get_ai_validator()

        return LLMValidationResult(
            action=action,
            confidence=llm_response.get("confidence", 50),
            tier=tier,
            score_modifier=modifier,
            modified_score=modified_score,
            setup_type=llm_response.get("setup_type"),
            reasoning=llm_response.get("reasoning", ""),
            key_factors=llm_response.get("key_factors", []),
            risks=llm_response.get("risks", []),
            invalidation_level=llm_response.get("invalidation_level"),
            provider=validator.provider,
            model=validator.model,
            prompt_hash=prompt_hash,
            latency_ms=latency_ms,
            deep_triggered=deep_triggered,
        )

    def create_bypass_result(self, reason: str) -> LLMValidationResult:
        """Create bypass result when LLM is disabled."""
        return LLMValidationResult(
            action=LLMAction.DEFER,
            confidence=100,
            tier=ValidationTier.BYPASS,
            score_modifier=0.0,
            reasoning=reason,
            provider="bypass",
            model="none",
        )

    def create_technical_fallback(
        self, error: str, entry_score: Optional["EntryScoreResult"]
    ) -> LLMValidationResult:
        """Create fallback result using technical analysis."""
        # Use entry score to determine action
        action = LLMAction.DEFER
        confidence = 50

        if entry_score:
            if entry_score.final_score >= 0.7:
                action = LLMAction.APPROVE
                confidence = 70
            elif entry_score.final_score >= 0.5:
                action = LLMAction.CAUTION
                confidence = 50
            else:
                action = LLMAction.VETO
                confidence = 30

        return LLMValidationResult(
            action=action,
            confidence=confidence,
            tier=ValidationTier.TECHNICAL,
            score_modifier=0.0,
            modified_score=entry_score.final_score if entry_score else None,
            reasoning=f"Technical fallback due to LLM error: {error}",
            provider="technical",
            model="fallback",
            error=error,
        )

    def create_error_result(self, error: str) -> LLMValidationResult:
        """Create error result when LLM fails and no fallback."""
        return LLMValidationResult(
            action=LLMAction.VETO,
            confidence=0,
            tier=ValidationTier.ERROR,
            score_modifier=-1.0,
            reasoning=f"LLM validation failed: {error}",
            provider="error",
            model="none",
            error=error,
        )
