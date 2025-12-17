"""LLM Integration for Tradingbot.

Provides controlled AI integration with:
- Call policy (daily + intraday events)
- Structured prompt format
- JSON schema validation
- Budget & safety controls
- Fallback on errors
- Audit trail

Uses OpenAI Structured Outputs for guaranteed valid responses.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from pydantic import BaseModel, Field, ValidationError

from .config import KIMode, LLMPolicyConfig
from .models import (
    BotAction,
    BotDecision,
    FeatureVector,
    LLMBotResponse,
    RegimeState,
    TradeSide,
)

if TYPE_CHECKING:
    from .strategy_catalog import StrategyDefinition

logger = logging.getLogger(__name__)


class LLMCallType(str, Enum):
    """Types of LLM calls."""
    DAILY_STRATEGY = "daily_strategy"
    REGIME_FLIP = "regime_flip"
    EXIT_CANDIDATE = "exit_candidate"
    SIGNAL_CHANGE = "signal_change"
    MANUAL = "manual"


@dataclass
class LLMCallRecord:
    """Record of an LLM call for audit trail."""
    call_id: str
    call_type: LLMCallType
    timestamp: datetime
    prompt_hash: str
    response_hash: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    success: bool = True
    error_message: str | None = None
    fallback_used: bool = False


@dataclass
class LLMBudgetState:
    """Budget tracking state."""
    date: datetime = field(default_factory=datetime.utcnow)
    calls_today: int = 0
    tokens_today: int = 0
    cost_today_usd: float = 0.0
    daily_calls_by_type: dict[str, int] = field(default_factory=dict)
    last_call_time: datetime | None = None
    consecutive_errors: int = 0


class LLMPromptBuilder:
    """Builds structured prompts for LLM calls.

    Formats features, state, and constraints into a consistent
    prompt format that the LLM can process reliably.
    """

    # Prompt templates
    DAILY_STRATEGY_TEMPLATE = """# Daily Strategy Selection

## Current Market State
{market_state}

## Available Strategies
{strategies}

## Constraints
- Must select a strategy that matches the current regime
- Consider walk-forward validation results
- Optimize for risk-adjusted returns

## Task
Select the best strategy for today and provide reasoning.
Return a JSON response with the following structure:
- strategy_id: string (ID of selected strategy)
- confidence: float (0.0-1.0)
- reason_codes: array of strings (max 3)
- adjustments: object with optional parameter tweaks
"""

    TRADE_DECISION_TEMPLATE = """# Trade Decision Request

## Current State
{state}

## Features
{features}

## Position
{position}

## Regime
{regime}

## Constraints
{constraints}

## Task
Analyze the current situation and recommend an action.
Return a JSON response with:
- action: HOLD | EXIT | ADJUST_STOP
- confidence: float (0.0-1.0)
- reason_codes: array of strings (max 3)
- stop_adjustment: float | null (new stop price if adjusting)
"""

    @staticmethod
    def build_daily_strategy_prompt(
        features: FeatureVector,
        regime: RegimeState,
        strategies: list[dict],
        constraints: dict | None = None
    ) -> str:
        """Build prompt for daily strategy selection.

        Args:
            features: Current feature vector
            regime: Current regime state
            strategies: List of available strategies with scores
            constraints: Optional constraints dict

        Returns:
            Formatted prompt string
        """
        market_state = f"""- Symbol: {features.symbol}
- Timestamp: {features.timestamp}
- Price: {features.close:.4f}
- Regime: {regime.regime.value}
- Volatility: {regime.volatility.value}
- Regime Confidence: {regime.regime_confidence:.2f}
- RSI(14): {features.rsi_14:.2f}
- ADX(14): {features.adx_14:.2f}
- ATR%: {(features.atr_14 / features.close * 100):.2f}%"""

        strategies_text = ""
        for s in strategies:
            strategies_text += f"""
### {s['name']} (ID: {s['id']})
- Type: {s['type']}
- Applicable Regimes: {', '.join(s.get('regimes', []))}
- Walk-Forward PF: {s.get('oos_pf', 0):.2f}
- Win Rate: {s.get('win_rate', 0):.1%}
- Score: {s.get('score', 0):.2f}
"""

        prompt = LLMPromptBuilder.DAILY_STRATEGY_TEMPLATE.format(
            market_state=market_state,
            strategies=strategies_text
        )
        return prompt

    @staticmethod
    def build_trade_decision_prompt(
        features: FeatureVector,
        regime: RegimeState,
        position: dict | None,
        state: str,
        strategy: dict | None,
        constraints: dict | None = None
    ) -> str:
        """Build prompt for trade decision.

        Args:
            features: Current feature vector
            regime: Current regime state
            position: Current position dict or None
            state: Bot state (FLAT, SIGNAL, MANAGE, etc.)
            strategy: Active strategy dict
            constraints: Risk constraints

        Returns:
            Formatted prompt string
        """
        # Format features (normalized)
        features_dict = features.to_dict_normalized()
        features_text = "\n".join([
            f"- {k}: {v:.4f}" if isinstance(v, float) else f"- {k}: {v}"
            for k, v in features_dict.items()
        ])

        # Format position
        if position:
            position_text = f"""- Side: {position.get('side', 'N/A')}
- Entry Price: {position.get('entry_price', 0):.4f}
- Current Stop: {position.get('current_stop', 0):.4f}
- Bars Held: {position.get('bars_held', 0)}
- Unrealized P&L: {position.get('unrealized_pnl', 0):.2f}"""
        else:
            position_text = "No open position"

        # Format regime
        regime_text = f"""- Type: {regime.regime.value}
- Volatility: {regime.volatility.value}
- Confidence: {regime.regime_confidence:.2f}"""

        # Format constraints
        if constraints:
            constraints_text = "\n".join([
                f"- {k}: {v}" for k, v in constraints.items()
            ])
        else:
            constraints_text = "- Standard risk limits apply"

        prompt = LLMPromptBuilder.TRADE_DECISION_TEMPLATE.format(
            state=state,
            features=features_text,
            position=position_text,
            regime=regime_text,
            constraints=constraints_text
        )
        return prompt


class LLMResponseValidator:
    """Validates LLM responses against expected schema.

    Provides strict validation with repair attempts and
    fallback to rule-based defaults.
    """

    @staticmethod
    def validate_trade_decision(
        response: dict | str,
        allow_repair: bool = True
    ) -> tuple[LLMBotResponse | None, list[str]]:
        """Validate trade decision response.

        Args:
            response: Raw response dict or JSON string
            allow_repair: Attempt to repair invalid responses

        Returns:
            (Validated response or None, list of validation errors)
        """
        errors = []

        # Parse if string
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as e:
                errors.append(f"JSON parse error: {e}")
                return None, errors

        if not isinstance(response, dict):
            errors.append(f"Expected dict, got {type(response)}")
            return None, errors

        # Attempt Pydantic validation
        try:
            validated = LLMBotResponse(**response)
            return validated, []
        except ValidationError as e:
            for err in e.errors():
                errors.append(f"{err['loc']}: {err['msg']}")

        # Attempt repair if allowed
        if allow_repair and errors:
            repaired = LLMResponseValidator._attempt_repair(response)
            if repaired:
                try:
                    validated = LLMBotResponse(**repaired)
                    errors.append("REPAIRED: Response was auto-corrected")
                    return validated, errors
                except ValidationError:
                    pass

        return None, errors

    @staticmethod
    def _attempt_repair(response: dict) -> dict | None:
        """Attempt to repair an invalid response.

        Args:
            response: Invalid response dict

        Returns:
            Repaired dict or None
        """
        repaired = response.copy()

        # Fix action if invalid
        action = repaired.get("action", "").upper()
        valid_actions = {"HOLD", "EXIT", "ADJUST_STOP", "ENTRY", "SKIP"}
        if action not in valid_actions:
            repaired["action"] = "HOLD"

        # Fix confidence range
        confidence = repaired.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        repaired["confidence"] = max(0.0, min(1.0, float(confidence)))

        # Fix reason_codes
        reason_codes = repaired.get("reason_codes", [])
        if not isinstance(reason_codes, list):
            reason_codes = []
        repaired["reason_codes"] = reason_codes[:3]

        return repaired

    @staticmethod
    def get_fallback_response(
        state: str,
        features: FeatureVector | None = None
    ) -> LLMBotResponse:
        """Get rule-based fallback response.

        Args:
            state: Current bot state
            features: Optional features for context

        Returns:
            Safe fallback response
        """
        # Default to HOLD with low confidence
        return LLMBotResponse(
            action=BotAction.HOLD,
            confidence=0.3,
            reason_codes=["LLM_FALLBACK", "RULE_BASED"],
            side=None,
            stop_adjustment=None
        )


class LLMIntegration:
    """Main LLM integration class for tradingbot.

    Manages:
    - Call policy enforcement
    - Budget tracking
    - OpenAI API calls with structured outputs
    - Response validation
    - Fallback handling
    - Audit trail
    """

    # Cost estimates (USD per 1K tokens)
    COST_PER_1K_INPUT = 0.0025  # GPT-4o-mini input
    COST_PER_1K_OUTPUT = 0.01   # GPT-4o-mini output

    def __init__(
        self,
        config: LLMPolicyConfig,
        api_key: str | None = None,
        on_call: Callable[[LLMCallRecord], None] | None = None
    ):
        """Initialize LLM integration.

        Args:
            config: LLM policy configuration
            api_key: OpenAI API key (or from env)
            on_call: Callback for call events
        """
        self.config = config
        self._api_key = api_key
        self._on_call = on_call

        self._budget = LLMBudgetState()
        self._call_history: list[LLMCallRecord] = []
        self._client = None

        logger.info(
            f"LLMIntegration initialized: model={config.model}, "
            f"max_calls={config.max_daily_calls}"
        )

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                import os

                api_key = self._api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")

                self._client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openai package not installed")

        return self._client

    def can_call(self, call_type: LLMCallType) -> tuple[bool, str]:
        """Check if an LLM call is allowed.

        Args:
            call_type: Type of call

        Returns:
            (allowed, reason)
        """
        self._check_day_rollover()

        # Budget limits
        if self._budget.calls_today >= self.config.max_daily_calls:
            return False, f"Daily call limit reached ({self.config.max_daily_calls})"

        if self._budget.cost_today_usd >= self.config.daily_budget_usd:
            return False, f"Daily budget exceeded (${self.config.daily_budget_usd:.2f})"

        # Rate limiting
        if self._budget.last_call_time:
            elapsed = (datetime.utcnow() - self._budget.last_call_time).total_seconds()
            min_interval = 60 / self.config.rate_limit_per_minute
            if elapsed < min_interval:
                return False, f"Rate limit: wait {min_interval - elapsed:.1f}s"

        # Type-specific limits
        type_count = self._budget.daily_calls_by_type.get(call_type.value, 0)
        if call_type == LLMCallType.DAILY_STRATEGY and type_count >= 1:
            return False, "Daily strategy call already made"

        # Error backoff
        if self._budget.consecutive_errors >= self.config.max_retries:
            return False, f"Too many consecutive errors ({self._budget.consecutive_errors})"

        return True, "OK"

    def call_for_strategy_selection(
        self,
        features: FeatureVector,
        regime: RegimeState,
        strategies: list[dict]
    ) -> dict | None:
        """Make LLM call for daily strategy selection.

        Args:
            features: Current features
            regime: Current regime
            strategies: Available strategies with scores

        Returns:
            Strategy selection dict or None on failure
        """
        can_call, reason = self.can_call(LLMCallType.DAILY_STRATEGY)
        if not can_call:
            logger.warning(f"Strategy selection call blocked: {reason}")
            return None

        prompt = LLMPromptBuilder.build_daily_strategy_prompt(
            features, regime, strategies
        )

        try:
            response = self._make_call(
                prompt,
                LLMCallType.DAILY_STRATEGY,
                response_format={"type": "json_object"}
            )

            if response:
                return json.loads(response)
            return None

        except Exception as e:
            logger.error(f"Strategy selection call failed: {e}")
            self._budget.consecutive_errors += 1
            return None

    def call_for_trade_decision(
        self,
        features: FeatureVector,
        regime: RegimeState,
        position: dict | None,
        state: str,
        strategy: dict | None,
        call_type: LLMCallType = LLMCallType.SIGNAL_CHANGE
    ) -> LLMBotResponse:
        """Make LLM call for trade decision.

        Args:
            features: Current features
            regime: Current regime
            position: Current position or None
            state: Bot state
            strategy: Active strategy
            call_type: Type of call trigger

        Returns:
            Validated LLMBotResponse (may be fallback)
        """
        can_call, reason = self.can_call(call_type)
        if not can_call:
            logger.warning(f"Trade decision call blocked: {reason}")
            return LLMResponseValidator.get_fallback_response(state, features)

        prompt = LLMPromptBuilder.build_trade_decision_prompt(
            features, regime, position, state, strategy
        )

        try:
            response = self._make_call(
                prompt,
                call_type,
                response_format={"type": "json_object"}
            )

            if response:
                validated, errors = LLMResponseValidator.validate_trade_decision(
                    response
                )

                if validated:
                    if errors:
                        logger.warning(f"Response validated with repairs: {errors}")
                    return validated

                logger.warning(f"Response validation failed: {errors}")

        except Exception as e:
            logger.error(f"Trade decision call failed: {e}")
            self._budget.consecutive_errors += 1

        # Return fallback
        fallback = LLMResponseValidator.get_fallback_response(state, features)
        self._record_fallback_used()
        return fallback

    def _make_call(
        self,
        prompt: str,
        call_type: LLMCallType,
        response_format: dict | None = None
    ) -> str | None:
        """Make actual API call to OpenAI.

        Args:
            prompt: Prompt string
            call_type: Type of call
            response_format: Optional response format spec

        Returns:
            Response text or None
        """
        start_time = datetime.utcnow()
        call_id = hashlib.sha256(
            f"{start_time.isoformat()}{prompt[:100]}".encode()
        ).hexdigest()[:12]

        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        try:
            client = self._get_client()

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a trading assistant. Analyze market data and "
                        "provide structured JSON responses. Be conservative and "
                        "prefer lower-risk recommendations when uncertain."
                    )
                },
                {"role": "user", "content": prompt}
            ]

            kwargs = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(**kwargs)

            # Extract response
            content = response.choices[0].message.content
            response_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            # Calculate costs
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (
                input_tokens * self.COST_PER_1K_INPUT / 1000 +
                output_tokens * self.COST_PER_1K_OUTPUT / 1000
            )

            latency = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Record call
            record = LLMCallRecord(
                call_id=call_id,
                call_type=call_type,
                timestamp=start_time,
                prompt_hash=prompt_hash,
                response_hash=response_hash,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency,
                success=True
            )
            self._record_call(record)

            logger.info(
                f"LLM call success: type={call_type.value}, "
                f"tokens={input_tokens}+{output_tokens}, cost=${cost:.4f}"
            )

            return content

        except Exception as e:
            # Record failed call
            record = LLMCallRecord(
                call_id=call_id,
                call_type=call_type,
                timestamp=start_time,
                prompt_hash=prompt_hash,
                success=False,
                error_message=str(e)
            )
            self._record_call(record)

            raise

    def _record_call(self, record: LLMCallRecord) -> None:
        """Record a call for audit and budget tracking.

        Args:
            record: Call record
        """
        self._call_history.append(record)

        # Update budget
        self._budget.calls_today += 1
        self._budget.tokens_today += record.input_tokens + record.output_tokens
        self._budget.cost_today_usd += record.cost_usd
        self._budget.last_call_time = record.timestamp

        # Track by type
        type_key = record.call_type.value
        self._budget.daily_calls_by_type[type_key] = (
            self._budget.daily_calls_by_type.get(type_key, 0) + 1
        )

        # Reset error count on success
        if record.success:
            self._budget.consecutive_errors = 0

        # Notify callback
        if self._on_call:
            self._on_call(record)

    def _record_fallback_used(self) -> None:
        """Record that a fallback was used."""
        if self._call_history:
            self._call_history[-1].fallback_used = True

    def _check_day_rollover(self) -> None:
        """Check for day rollover and reset budget."""
        now = datetime.utcnow()
        if self._budget.date.date() != now.date():
            self._budget = LLMBudgetState(date=now)
            logger.info("New trading day - LLM budget reset")

    def get_stats(self) -> dict[str, Any]:
        """Get current LLM usage statistics.

        Returns:
            Stats dict
        """
        self._check_day_rollover()

        return {
            "date": self._budget.date.isoformat(),
            "calls_today": self._budget.calls_today,
            "tokens_today": self._budget.tokens_today,
            "cost_today_usd": self._budget.cost_today_usd,
            "calls_by_type": self._budget.daily_calls_by_type.copy(),
            "consecutive_errors": self._budget.consecutive_errors,
            "budget_remaining_usd": max(
                0, self.config.daily_budget_usd - self._budget.cost_today_usd
            ),
            "calls_remaining": max(
                0, self.config.max_daily_calls - self._budget.calls_today
            )
        }

    def get_audit_trail(
        self,
        limit: int = 100,
        call_type: LLMCallType | None = None
    ) -> list[dict]:
        """Get audit trail of LLM calls.

        Args:
            limit: Max records to return
            call_type: Filter by call type

        Returns:
            List of call records as dicts
        """
        records = self._call_history

        if call_type:
            records = [r for r in records if r.call_type == call_type]

        records = records[-limit:]

        return [
            {
                "call_id": r.call_id,
                "call_type": r.call_type.value,
                "timestamp": r.timestamp.isoformat(),
                "prompt_hash": r.prompt_hash,
                "response_hash": r.response_hash,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cost_usd": r.cost_usd,
                "latency_ms": r.latency_ms,
                "success": r.success,
                "error_message": r.error_message,
                "fallback_used": r.fallback_used
            }
            for r in records
        ]
