"""LLM Validation Service - Unified LLM-based Signal Validation (Refactored).

Refactored from 727 LOC monolith using composition pattern.

Main Orchestrator (Module 4/4).

Delegates to 3 specialized helper modules:
- LLMValidationPrompt: Prompt building from MarketContext
- LLMValidationRouter: Quick→Deep routing and result building
- LLMValidationState: Enums and dataclasses (imported from state module)

Provides:
- LLMValidationService: Main orchestration class with delegation
- Global singleton factory
- Config load/save utilities
- Re-exports all state types for backward compatibility
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from src.core.trading_bot.llm_validation_prompt import LLMValidationPrompt
from src.core.trading_bot.llm_validation_router import LLMValidationRouter
from src.core.trading_bot.llm_validation_state import (
    LLMAction,
    LLMValidationConfig,
    LLMValidationResult,
    ValidationTier,
)

if TYPE_CHECKING:
    from .market_context import MarketContext
    from .entry_score_engine import EntryScoreResult
    from .level_engine import LevelsResult

logger = logging.getLogger(__name__)


class LLMValidationService:
    """
    Unified LLM Validation Service.

    Key principles:
    1. Uses MarketContext as single source of truth
    2. Returns strict JSON validation results
    3. Acts ONLY as veto/boost - never executes trades
    4. Supports Quick→Deep routing for efficiency
    5. Full audit trail for every validation

    Usage:
        service = LLMValidationService()
        result = await service.validate(market_context, entry_score)

        if result.is_veto:
            # Don't trade
        elif result.is_boost:
            # Increase confidence/position
    """

    def __init__(self, config: Optional[LLMValidationConfig] = None):
        """Initialize LLM Validation Service."""
        self.config = config or LLMValidationConfig()

        # Lazy-loaded AI validator
        self._ai_validator = None

        # Instantiate helper modules (composition pattern)
        self._prompt = LLMValidationPrompt(parent=self)
        self._router = LLMValidationRouter(parent=self)

        logger.info(
            f"LLMValidationService initialized. "
            f"Enabled: {self.config.enabled}, "
            f"Thresholds: approve>={self.config.quick_approve_threshold}, "
            f"deep>={self.config.quick_deep_threshold}"
        )

    async def validate(
        self,
        context: "MarketContext",
        entry_score: Optional["EntryScoreResult"] = None,
        levels_result: Optional["LevelsResult"] = None,
    ) -> LLMValidationResult:
        """
        Validate a trading signal using LLM.

        Args:
            context: MarketContext with all analysis data
            entry_score: Optional entry score result
            levels_result: Optional detected levels

        Returns:
            LLMValidationResult with action and modifiers
        """
        start_time = datetime.now(timezone.utc)

        if not self.config.enabled:
            return self._router.create_bypass_result("LLM validation disabled")

        try:
            # Build prompt from context (delegates to _prompt)
            prompt = self._prompt.build_context_prompt(context, entry_score, levels_result)
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()

            # Get AI validator
            validator = self._get_ai_validator()

            # Quick validation first (delegates to _router)
            quick_result = await self._router.run_quick_validation(prompt)

            latency = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            # Route based on confidence
            if quick_result["confidence"] >= self.config.quick_approve_threshold:
                # High confidence -> Approve or Boost
                action = LLMAction.BOOST if quick_result["confidence"] >= 85 else LLMAction.APPROVE
                return self._router.build_result(
                    action=action,
                    llm_response=quick_result,
                    tier=ValidationTier.QUICK,
                    prompt_hash=prompt_hash,
                    latency_ms=latency,
                    entry_score=entry_score,
                )

            elif quick_result["confidence"] >= self.config.quick_deep_threshold:
                # Medium confidence -> Deep analysis
                logger.info(f"Quick confidence {quick_result['confidence']}% -> triggering deep analysis")

                deep_start = datetime.now(timezone.utc)
                deep_result = await self._router.run_deep_validation(prompt, context)
                deep_latency = int((datetime.now(timezone.utc) - deep_start).total_seconds() * 1000)

                if deep_result["confidence"] >= self.config.deep_approve_threshold:
                    action = LLMAction.APPROVE
                elif deep_result["confidence"] >= self.config.deep_veto_threshold:
                    action = LLMAction.CAUTION
                else:
                    action = LLMAction.VETO

                return self._router.build_result(
                    action=action,
                    llm_response=deep_result,
                    tier=ValidationTier.DEEP,
                    prompt_hash=prompt_hash,
                    latency_ms=latency + deep_latency,
                    entry_score=entry_score,
                    deep_triggered=True,
                )

            else:
                # Low confidence -> Veto
                return self._router.build_result(
                    action=LLMAction.VETO,
                    llm_response=quick_result,
                    tier=ValidationTier.QUICK,
                    prompt_hash=prompt_hash,
                    latency_ms=latency,
                    entry_score=entry_score,
                )

        except Exception as e:
            logger.error(f"LLM validation failed: {e}", exc_info=True)

            if self.config.fallback_to_technical:
                return self._router.create_technical_fallback(str(e), entry_score)
            else:
                return self._router.create_error_result(str(e))

    def _get_ai_validator(self):
        """Get or create AI validator instance."""
        if self._ai_validator is None:
            from .ai_validator import AISignalValidator
            self._ai_validator = AISignalValidator(
                enabled=True,
                confidence_threshold_trade=self.config.quick_approve_threshold,
                confidence_threshold_deep=self.config.quick_deep_threshold,
                deep_analysis_enabled=True,
                fallback_to_technical=self.config.fallback_to_technical,
                timeout_seconds=self.config.timeout_seconds,
            )
        return self._ai_validator

    def update_config(self, config: LLMValidationConfig) -> None:
        """Update service configuration."""
        self.config = config
        self._ai_validator = None  # Reset validator
        logger.info("LLMValidationService config updated")


# =============================================================================
# GLOBAL SINGLETON & FACTORY
# =============================================================================

_global_service: Optional[LLMValidationService] = None
_service_lock = threading.Lock()


def get_llm_validation_service(config: Optional[LLMValidationConfig] = None) -> LLMValidationService:
    """Get global LLMValidationService singleton."""
    global _global_service

    with _service_lock:
        if _global_service is None:
            _global_service = LLMValidationService(config)
            logger.info("Global LLMValidationService created")
        return _global_service


async def validate_signal(
    context: "MarketContext",
    entry_score: Optional["EntryScoreResult"] = None,
) -> LLMValidationResult:
    """Convenience function to validate a signal."""
    service = get_llm_validation_service()
    return await service.validate(context, entry_score)


def load_llm_validation_config(path: Optional[Path] = None) -> LLMValidationConfig:
    """Load config from JSON file."""
    if path is None:
        path = Path("config/llm_validation_config.json")

    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return LLMValidationConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load LLM validation config: {e}")

    return LLMValidationConfig()


def save_llm_validation_config(config: LLMValidationConfig, path: Optional[Path] = None) -> bool:
    """Save config to JSON file."""
    if path is None:
        path = Path("config/llm_validation_config.json")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"LLM validation config saved to {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save LLM validation config: {e}")
        return False


# Re-export für backward compatibility
__all__ = [
    "LLMValidationService",
    "LLMValidationConfig",
    "LLMValidationResult",
    "LLMAction",
    "ValidationTier",
    "get_llm_validation_service",
    "validate_signal",
    "load_llm_validation_config",
    "save_llm_validation_config",
]
