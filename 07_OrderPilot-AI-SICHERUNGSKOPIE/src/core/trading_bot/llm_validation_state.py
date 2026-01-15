"""LLM Validation State - Enums and Dataclasses.

Refactored from 727 LOC monolith using composition pattern.

Module 1/4 of llm_validation_service.py split.

Contains:
- LLMAction enum (APPROVE, BOOST, VETO, CAUTION, DEFER)
- ValidationTier enum (QUICK, DEEP, TECHNICAL, BYPASS, ERROR)
- LLMValidationConfig dataclass (thresholds, modifiers, prompt settings)
- LLMValidationResult dataclass (validation result with analysis)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class LLMAction(str, Enum):
    """Action taken by LLM validation."""
    APPROVE = "approve"       # Signal approved, proceed
    BOOST = "boost"          # Signal boosted (increase position/confidence)
    VETO = "veto"            # Signal vetoed, do not trade
    CAUTION = "caution"      # Signal allowed but with caution (reduced size)
    DEFER = "defer"          # Defer to technical (LLM uncertain)


class ValidationTier(str, Enum):
    """Validation tier used."""
    QUICK = "quick"          # Quick validation (fast model)
    DEEP = "deep"            # Deep analysis (slower, more thorough)
    TECHNICAL = "technical"  # Technical only (no LLM)
    BYPASS = "bypass"        # LLM bypassed (disabled)
    ERROR = "error"          # LLM error occurred


@dataclass
class LLMValidationConfig:
    """Configuration for LLM Validation Service."""

    # Enable/Disable
    enabled: bool = True
    fallback_to_technical: bool = True

    # Thresholds for Quick→Deep routing
    quick_approve_threshold: int = 75     # >= 75 -> approve
    quick_deep_threshold: int = 50        # 50-74 -> deep analysis
    quick_veto_threshold: int = 50        # < 50 -> veto

    # Deep analysis thresholds
    deep_approve_threshold: int = 70
    deep_veto_threshold: int = 40

    # Score modifiers
    boost_score_modifier: float = 0.15    # +15% on boost
    caution_score_modifier: float = -0.10 # -10% on caution
    veto_score_modifier: float = -1.0     # Block entry

    # Prompt settings
    include_levels: bool = True
    include_indicators: bool = True
    include_candles: int = 10             # Last N candles
    max_prompt_tokens: int = 2000

    # Timeout
    timeout_seconds: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "fallback_to_technical": self.fallback_to_technical,
            "thresholds": {
                "quick_approve": self.quick_approve_threshold,
                "quick_deep": self.quick_deep_threshold,
                "quick_veto": self.quick_veto_threshold,
                "deep_approve": self.deep_approve_threshold,
                "deep_veto": self.deep_veto_threshold,
            },
            "modifiers": {
                "boost": self.boost_score_modifier,
                "caution": self.caution_score_modifier,
                "veto": self.veto_score_modifier,
            },
            "prompt": {
                "include_levels": self.include_levels,
                "include_indicators": self.include_indicators,
                "include_candles": self.include_candles,
                "max_tokens": self.max_prompt_tokens,
            },
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMValidationConfig":
        config = cls()

        config.enabled = data.get("enabled", config.enabled)
        config.fallback_to_technical = data.get("fallback_to_technical", config.fallback_to_technical)

        if "thresholds" in data:
            t = data["thresholds"]
            config.quick_approve_threshold = t.get("quick_approve", config.quick_approve_threshold)
            config.quick_deep_threshold = t.get("quick_deep", config.quick_deep_threshold)
            config.quick_veto_threshold = t.get("quick_veto", config.quick_veto_threshold)
            config.deep_approve_threshold = t.get("deep_approve", config.deep_approve_threshold)
            config.deep_veto_threshold = t.get("deep_veto", config.deep_veto_threshold)

        if "modifiers" in data:
            m = data["modifiers"]
            config.boost_score_modifier = m.get("boost", config.boost_score_modifier)
            config.caution_score_modifier = m.get("caution", config.caution_score_modifier)
            config.veto_score_modifier = m.get("veto", config.veto_score_modifier)

        if "prompt" in data:
            p = data["prompt"]
            config.include_levels = p.get("include_levels", config.include_levels)
            config.include_indicators = p.get("include_indicators", config.include_indicators)
            config.include_candles = p.get("include_candles", config.include_candles)
            config.max_prompt_tokens = p.get("max_tokens", config.max_prompt_tokens)

        config.timeout_seconds = data.get("timeout_seconds", config.timeout_seconds)

        return config


@dataclass
class LLMValidationResult:
    """Result of LLM validation."""

    # Core result
    action: LLMAction
    confidence: int  # 0-100
    tier: ValidationTier

    # Score modification
    score_modifier: float  # Applied to entry score
    modified_score: Optional[float] = None

    # Analysis
    setup_type: Optional[str] = None
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    invalidation_level: Optional[float] = None

    # Meta
    provider: str = ""
    model: str = ""
    prompt_hash: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: int = 0
    error: Optional[str] = None

    # Deep analysis flag
    deep_triggered: bool = False

    @property
    def allows_entry(self) -> bool:
        """Check if validation allows entry."""
        return self.action in (LLMAction.APPROVE, LLMAction.BOOST, LLMAction.CAUTION, LLMAction.DEFER)

    @property
    def is_boost(self) -> bool:
        return self.action == LLMAction.BOOST

    @property
    def is_veto(self) -> bool:
        return self.action == LLMAction.VETO

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "confidence": self.confidence,
            "tier": self.tier.value,
            "allows_entry": self.allows_entry,
            "score_modifier": round(self.score_modifier, 3),
            "modified_score": round(self.modified_score, 4) if self.modified_score else None,
            "analysis": {
                "setup_type": self.setup_type,
                "reasoning": self.reasoning,
                "key_factors": self.key_factors,
                "risks": self.risks,
                "invalidation_level": self.invalidation_level,
            },
            "meta": {
                "provider": self.provider,
                "model": self.model,
                "prompt_hash": self.prompt_hash[:16] if self.prompt_hash else "",
                "timestamp": self.timestamp.isoformat(),
                "latency_ms": self.latency_ms,
                "deep_triggered": self.deep_triggered,
            },
            "error": self.error,
        }

    def get_summary(self) -> str:
        """Get human-readable summary."""
        emoji = {
            LLMAction.APPROVE: "✅",
            LLMAction.BOOST: "🚀",
            LLMAction.VETO: "❌",
            LLMAction.CAUTION: "⚠️",
            LLMAction.DEFER: "🔄",
        }.get(self.action, "❓")

        return (
            f"{emoji} {self.action.value.upper()} ({self.confidence}%) | "
            f"Setup: {self.setup_type or 'N/A'} | "
            f"Modifier: {self.score_modifier:+.0%}"
        )
