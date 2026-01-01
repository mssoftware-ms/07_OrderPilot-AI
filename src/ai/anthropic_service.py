"""Anthropic Claude Service for OrderPilot-AI Trading Application.

Implements Anthropic API integration with structured outputs,
mirroring the OpenAI service structure for compatibility.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, TypeVar

import aiohttp
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.common.logging_setup import log_ai_request
from src.config.loader import AIConfig

# Import shared models from OpenAI service
from src.ai.openai_service import (
    OrderAnalysis,
    AlertTriageResult,
    BacktestReview,
    CostTracker,
    CacheManager,
    OpenAIError,  # Reuse as AnthropicError
    RateLimitError,
    QuotaExceededError,
    SchemaValidationError
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class AnthropicService:
    """Main Anthropic service for structured outputs.

    Mirrors OpenAIService structure for drop-in compatibility.
    """

    def __init__(
        self,
        config: AIConfig,
        api_key: str,
        telemetry_callback: callable | None = None
    ):
        """Initialize Anthropic service.

        Args:
            config: AI configuration
            api_key: Anthropic API key
            telemetry_callback: Optional callback for telemetry
        """
        self.config = config
        self.api_key = api_key
        self.telemetry_callback = telemetry_callback

        # Initialize components (shared with OpenAI)
        self.cost_tracker = CostTracker(
            monthly_budget=config.cost_limit_monthly,
            warn_threshold=config.cost_limit_monthly * 0.8  # Warn at 80%
        )
        self.cache_manager = CacheManager(ttl_seconds=config.cache_ttl if hasattr(config, 'cache_ttl') else 3600)

        # API settings for Anthropic
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,  # Anthropic uses x-api-key instead of Authorization
            "anthropic-version": "2023-06-01",  # Required header
            "Content-Type": "application/json"
        }

        # Default model (can be overridden)
        self.default_model = "claude-sonnet-4-5-20250929"

        # Session for connection pooling
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize the service."""
        if not self._session:
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeouts.get("read_ms", 15000) / 1000,
                connect=self.config.timeouts.get("connect_ms", 5000) / 1000
            )
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )

    async def close(self) -> None:
        """Close the service."""
        if self._session:
            await self._session.close()
            self._session = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, RateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def structured_completion(
        self,
        prompt: str,
        response_model: type[T],
        model: str | None = None,
        temperature: float = 0.2,
        use_cache: bool = True,
        context: dict[str, Any] | None = None
    ) -> T:
        """Get structured completion from Anthropic Claude.

        Args:
            prompt: The prompt to send
            response_model: Pydantic model for response validation
            model: Model to use (defaults to self.default_model)
            temperature: Temperature for generation (0.0-1.0)
            use_cache: Whether to use caching
            context: Additional context for the request

        Returns:
            Validated response as Pydantic model instance

        Raises:
            RateLimitError: If rate limited by API
            QuotaExceededError: If monthly budget exceeded
            SchemaValidationError: If response doesn't match schema
        """
        # Check budget
        if not self.cost_tracker.check_budget(estimated_cost=0.01):  # Estimate
            raise QuotaExceededError("Monthly AI budget exceeded")

        cache_key = self._build_cache_key(prompt, response_model, model, use_cache)
        cached = self._try_cache_hit(cache_key, response_model)
        if cached is not None:
            return cached

        # Build request
        model_to_use = model or self.default_model

        request_body = self._build_request_body(prompt, response_model, model_to_use, temperature)

        # Ensure session is initialized
        if not self._session:
            await self.initialize()

        start_time = time.time()

        try:
            # Make API request
            async with self._session.post(
                f"{self.base_url}/messages",
                json=request_body
            ) as response:

                # Handle rate limiting
                if response.status == 429:
                    logger.warning("Anthropic rate limit hit")
                    raise RateLimitError("Rate limit exceeded")

                # Handle errors
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"Anthropic API error ({response.status}): {error_text}")
                    raise OpenAIError(f"API error {response.status}: {error_text}")

                # Parse response
                response_data = await response.json()

                text_content = self._extract_text_content(response_data)
                json_data = self._parse_json_response(text_content)
                result = self._validate_response(response_model, json_data)

                # Track costs
                usage = response_data.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)

                cost = self._calculate_cost(input_tokens, output_tokens)
                self.cost_tracker.add_cost(cost)

                # Log request
                elapsed_ms = (time.time() - start_time) * 1000
                self._log_ai_request(model_to_use, input_tokens + output_tokens, cost, elapsed_ms)

                # Cache result
                if use_cache and cache_key:
                    self.cache_manager.set(cache_key, result.model_dump())

                return result

        except aiohttp.ClientError as e:
            logger.error(f"Anthropic API connection error: {e}")
            raise OpenAIError(f"Connection error: {e}")

    def _build_cache_key(
        self,
        prompt: str,
        response_model: type[T],
        model: str | None,
        use_cache: bool,
    ) -> str | None:
        if not use_cache:
            return None
        return hashlib.md5(
            f"{prompt}:{response_model.__name__}:{model or self.default_model}".encode()
        ).hexdigest()

    def _try_cache_hit(self, cache_key: str | None, response_model: type[T]) -> T | None:
        if not cache_key:
            return None
        cached = self.cache_manager.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {response_model.__name__}")
            return response_model.model_validate(cached)
        return None

    def _build_request_body(
        self,
        prompt: str,
        response_model: type[T],
        model_to_use: str,
        temperature: float,
    ) -> dict[str, Any]:
        return {
            "model": model_to_use,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\nIMPORTANT: Respond with valid JSON matching this schema:\n"
                        f"{response_model.model_json_schema()}"
                    ),
                }
            ],
        }

    def _extract_text_content(self, response_data: dict[str, Any]) -> str:
        content_blocks = response_data.get("content", [])
        if not content_blocks:
            raise SchemaValidationError("No content in Anthropic response")
        return content_blocks[0].get("text", "")

    def _parse_json_response(self, text_content: str) -> dict[str, Any]:
        try:
            if "```json" in text_content:
                text_content = text_content.split("```json")[1].split("```")[0].strip()
            elif "```" in text_content:
                text_content = text_content.split("```")[1].split("```")[0].strip()
            return json.loads(text_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Anthropic response as JSON: {e}")
            logger.debug(f"Raw content: {text_content[:500]}")
            raise SchemaValidationError(f"Invalid JSON in response: {e}")

    def _validate_response(self, response_model: type[T], json_data: dict[str, Any]) -> T:
        try:
            return response_model.model_validate(json_data)
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise SchemaValidationError(f"Response doesn't match schema: {e}")

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)

    def _log_ai_request(
        self,
        model: str,
        tokens_used: int,
        cost: float,
        elapsed_ms: float,
    ) -> None:
        log_ai_request(
            provider="Anthropic",
            model=model,
            tokens_used=tokens_used,
            cost_usd=cost,
            latency_ms=elapsed_ms,
            cache_hit=False,
        )

    # ==================== High-Level Task Methods ====================

    async def analyze_order(self, order_data: dict[str, Any]) -> OrderAnalysis:
        """Analyze an order for risk and approval.

        Args:
            order_data: Order details

        Returns:
            OrderAnalysis with approval recommendation
        """
        prompt = f"""Analyze this trading order for risk and approval:

Order Details:
{json.dumps(order_data, indent=2)}

Provide a structured analysis."""

        return await self.structured_completion(
            prompt=prompt,
            response_model=OrderAnalysis,
            temperature=0.1
        )

    async def triage_alert(self, alert_data: dict[str, Any]) -> AlertTriageResult:
        """Triage an alert to determine priority and actions.

        Args:
            alert_data: Alert details

        Returns:
            AlertTriageResult with priority and suggested actions
        """
        prompt = f"""Triage this trading alert:

Alert Details:
{json.dumps(alert_data, indent=2)}

Provide structured triage analysis."""

        return await self.structured_completion(
            prompt=prompt,
            response_model=AlertTriageResult,
            temperature=0.2
        )

    async def review_backtest(self, backtest_data: dict[str, Any]) -> BacktestReview:
        """Review backtest results and provide insights.

        Args:
            backtest_data: Backtest results and metrics

        Returns:
            BacktestReview with insights and recommendations
        """
        prompt = f"""Review these backtest results:

Backtest Data:
{json.dumps(backtest_data, indent=2)}

Provide structured review and insights."""

        return await self.structured_completion(
            prompt=prompt,
            response_model=BacktestReview,
            temperature=0.3
        )

    # ==================== Utility Methods ====================

    def get_cost_summary(self) -> dict[str, Any]:
        """Get cost tracking summary.

        Returns:
            Dictionary with cost stats
        """
        return self.cost_tracker.get_summary()

    def reset_costs(self) -> None:
        """Reset cost tracking (e.g., at start of new month)."""
        self.cost_tracker.reset()

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self.cache_manager.clear()
