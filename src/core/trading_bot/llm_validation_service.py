"""
LLM Validation Service - Unified LLM-based Signal Validation

Phase 4: LLM Validation Service Integration.

Dieser Service:
- Verwendet MarketContext als Single Source of Truth
- Komponiert optimierte Prompts aus Context-Daten
- Gibt strikt JSON-formatierte Validierung zurück
- Agiert NUR als Veto/Boost - führt keine Orders aus
- Unterstützt Quick→Deep Routing

Wichtig:
- LLM kann Trades BLOCKIEREN oder BOOSTEN, aber nicht ausführen
- Bei API-Fehlern: Fallback zu technischer Analyse
- Audit Trail: Jede Validierung wird geloggt
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .market_context import MarketContext
    from .entry_score_engine import EntryScoreResult
    from .level_engine import LevelsResult
    from .regime_detector import RegimeResult

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


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


# =============================================================================
# CONFIG
# =============================================================================


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


# =============================================================================
# RESULT DATACLASS
# =============================================================================


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


# =============================================================================
# LLM VALIDATION SERVICE
# =============================================================================


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

    # Setup types recognized
    SETUP_TYPES = [
        "BREAKOUT",
        "BREAKDOWN",
        "PULLBACK_SUPPORT",
        "PULLBACK_RESISTANCE",
        "SWING_FAILURE_PATTERN",
        "TREND_CONTINUATION",
        "MEAN_REVERSION",
        "MOMENTUM",
        "DIVERGENCE",
        "ABSORPTION",
        "RANGE_PLAY",
        "NO_SETUP",
    ]

    def __init__(self, config: Optional[LLMValidationConfig] = None):
        """Initialize LLM Validation Service."""
        self.config = config or LLMValidationConfig()

        # Lazy-loaded AI validator
        self._ai_validator = None

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
            return self._create_bypass_result("LLM validation disabled")

        try:
            # Build prompt from context
            prompt = self._build_context_prompt(context, entry_score, levels_result)
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()

            # Get AI validator
            validator = self._get_ai_validator()

            # Quick validation first
            quick_result = await self._run_quick_validation(prompt)

            latency = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            # Route based on confidence
            if quick_result["confidence"] >= self.config.quick_approve_threshold:
                # High confidence -> Approve or Boost
                action = LLMAction.BOOST if quick_result["confidence"] >= 85 else LLMAction.APPROVE
                return self._build_result(
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
                deep_result = await self._run_deep_validation(prompt, context)
                deep_latency = int((datetime.now(timezone.utc) - deep_start).total_seconds() * 1000)

                if deep_result["confidence"] >= self.config.deep_approve_threshold:
                    action = LLMAction.APPROVE
                elif deep_result["confidence"] >= self.config.deep_veto_threshold:
                    action = LLMAction.CAUTION
                else:
                    action = LLMAction.VETO

                return self._build_result(
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
                return self._build_result(
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
                return self._create_technical_fallback(str(e), entry_score)
            else:
                return self._create_error_result(str(e))

    def _build_context_prompt(
        self,
        context: "MarketContext",
        entry_score: Optional["EntryScoreResult"],
        levels_result: Optional["LevelsResult"],
    ) -> str:
        """Build optimized prompt from MarketContext."""

        # Symbol and timeframe
        header = f"""## Trading Signal Validation Request
Symbol: {context.symbol}
Timeframe: {context.timeframe}
Current Price: {context.current_price:.2f}
Timestamp: {context.timestamp.isoformat()}
"""

        # Regime info
        regime_section = f"""## Market Regime
Regime: {context.regime.value if hasattr(context.regime, 'value') else context.regime}
Trend Direction: {context.trend_direction.value if hasattr(context.trend_direction, 'value') else context.trend_direction}
"""

        # Entry score info
        score_section = ""
        if entry_score:
            score_section = f"""## Entry Score Analysis
Direction: {entry_score.direction.value}
Raw Score: {entry_score.raw_score:.3f}
Final Score: {entry_score.final_score:.3f}
Quality: {entry_score.quality.value}
Gate Status: {entry_score.gate_result.status.value if entry_score.gate_result else 'N/A'}
"""
            # Add component breakdown
            if entry_score.components:
                score_section += "\nScore Components:\n"
                for comp in entry_score.components:
                    score_section += f"  - {comp.name}: {comp.raw_score:.2f} x {comp.weight:.2f} = {comp.weighted_score:.3f}\n"

        # Indicators
        indicators_section = ""
        if self.config.include_indicators and context.indicators:
            ind = context.indicators
            indicators_section = f"""## Technical Indicators
RSI(14): {ind.rsi_14:.1f if ind.rsi_14 else 'N/A'} ({ind.rsi_state or 'N/A'})
MACD: {ind.macd_line:.4f if ind.macd_line else 'N/A'} / Signal: {ind.macd_signal:.4f if ind.macd_signal else 'N/A'} ({ind.macd_crossover or 'N/A'})
EMA20: {ind.ema_20:.2f if ind.ema_20 else 'N/A'} (Distance: {ind.ema_20_distance_pct:.2f}% if ind.ema_20_distance_pct else 'N/A')
EMA50: {ind.ema_50:.2f if ind.ema_50 else 'N/A'}
EMA200: {ind.ema_200:.2f if ind.ema_200 else 'N/A'}
ADX(14): {ind.adx_14:.1f if ind.adx_14 else 'N/A'}
ATR(14): {ind.atr_14:.2f if ind.atr_14 else 'N/A'} ({ind.atr_percent:.2f}% if ind.atr_percent else 'N/A')
BB %B: {ind.bb_pct_b:.2f if ind.bb_pct_b else 'N/A'}
Volume Ratio: {ind.volume_ratio:.2f if ind.volume_ratio else 'N/A'}x
"""

        # Levels
        levels_section = ""
        if self.config.include_levels and levels_result:
            levels_section = "## Support/Resistance Levels\n"
            for level in levels_result.get_top_n(5):
                level_type = level.level_type.value if hasattr(level.level_type, 'value') else str(level.level_type)
                strength = level.strength.value if hasattr(level.strength, 'value') else str(level.strength)
                levels_section += f"  - {level_type.upper()} @ {level.price_low:.2f}-{level.price_high:.2f} ({strength})\n"

        # Candles summary
        candles_section = ""
        if context.candles and len(context.candles) > 0:
            candles_section = f"""## Recent Price Action
Last {len(context.candles)} candles summary available in context.
Latest candle: O={context.candles[-1].open:.2f} H={context.candles[-1].high:.2f} L={context.candles[-1].low:.2f} C={context.candles[-1].close:.2f}
"""

        # Instructions
        instructions = f"""## Your Task
1. Evaluate the signal quality for a {entry_score.direction.value if entry_score else 'potential'} trade
2. Identify the setup type
3. Assess key risk factors
4. Provide a confidence score (0-100)
5. Determine: APPROVE, BOOST, CAUTION, or VETO

## Response Format (JSON only)
{{
    "confidence": <0-100>,
    "action": "<approve|boost|caution|veto>",
    "setup_type": "<one of: {', '.join(self.SETUP_TYPES)}>",
    "reasoning": "<1-2 sentence explanation>",
    "key_factors": ["<factor1>", "<factor2>"],
    "risks": ["<risk1>", "<risk2>"],
    "invalidation_level": <price level that invalidates the setup, or null>
}}

IMPORTANT:
- You are a VALIDATOR, not an executor. Your job is to assess signal quality.
- Be conservative: when in doubt, VETO or CAUTION.
- BOOST only for high-quality setups with strong confluence.
- Response MUST be valid JSON only, no markdown."""

        return header + regime_section + score_section + indicators_section + levels_section + candles_section + instructions

    async def _run_quick_validation(self, prompt: str) -> Dict[str, Any]:
        """Run quick validation."""
        validator = self._get_ai_validator()

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

    async def _run_deep_validation(
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

        validator = self._get_ai_validator()
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

    def _build_result(
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
            modifier = self.config.boost_score_modifier
        elif action == LLMAction.CAUTION:
            modifier = self.config.caution_score_modifier
        elif action == LLMAction.VETO:
            modifier = self.config.veto_score_modifier
        else:
            modifier = 0.0

        # Calculate modified score
        modified_score = None
        if entry_score:
            modified_score = min(1.0, max(0.0, entry_score.final_score + modifier))

        # Get validator info
        validator = self._get_ai_validator()

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

    def _create_bypass_result(self, reason: str) -> LLMValidationResult:
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

    def _create_technical_fallback(
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

    def _create_error_result(self, error: str) -> LLMValidationResult:
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
