"""LLM Integration for Tradingbot.

Provides controlled AI integration with:
- Call policy (daily + intraday events)
- Structured prompt format
- JSON schema validation
- Budget & safety controls
- Fallback on errors
- Audit trail

Uses OpenAI Structured Outputs for guaranteed valid responses.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- llm_types.py: LLMCallType, LLMCallRecord, LLMBudgetState
- llm_prompts.py: LLMPromptBuilder
- llm_validators.py: LLMResponseValidator
- llm_integration.py: Main LLMIntegration class (this file)
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Callable

from .config import LLMPolicyConfig
from .models import FeatureVector, LLMBotResponse, RegimeState

# Import from split modules
from .llm_types import LLMBudgetState, LLMCallRecord, LLMCallType
from .llm_prompts import LLMPromptBuilder
from .llm_validators import LLMResponseValidator

# Re-export for backward compatibility
__all__ = [
    "LLMCallType",
    "LLMCallRecord",
    "LLMBudgetState",
    "LLMPromptBuilder",
    "LLMResponseValidator",
    "LLMIntegration",
]

logger = logging.getLogger(__name__)


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
