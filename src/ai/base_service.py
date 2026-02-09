"""Base AI Service for OrderPilot-AI.

Provides abstract base class for AI provider implementations (OpenAI, Anthropic, Gemini).
Implements Template Method pattern for structured completions.

This class consolidates common patterns across all AI providers:
- Session lifecycle management
- Budget tracking and cost management
- Response caching
- Error handling (rate limits, validation)
- Telemetry logging
- JSON parsing with markdown block removal
"""

from __future__ import annotations

import asyncio
import inspect
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
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

from .openai_models import (
    AlertTriageResult,
    BacktestReview,
    OpenAIError,
    OrderAnalysis,
    RateLimitError,
    SchemaValidationError,
)
from .openai_utils import CacheManager, CostTracker

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseAIService(ABC):
    """Abstract base class for AI provider services.

    Provides common infrastructure for:
    - Session management (async context manager)
    - Budget tracking and cost management
    - Response caching
    - Error handling (rate limits, validation)
    - Telemetry logging
    - JSON parsing with markdown block removal

    Subclasses must implement:
    - _build_request_body(): Provider-specific request formatting
    - _extract_text_content(): Extract text from provider response
    - _extract_token_counts(): Extract token usage from response
    - _calculate_cost(): Calculate cost based on usage
    - _get_provider_name(): Return provider name for logging
    - _get_endpoint(): Return API endpoint URL
    """

    def __init__(
        self,
        config: AIConfig,
        api_key: str,
        telemetry_callback: callable | None = None
    ):
        """Initialize base AI service.

        Args:
            config: AI configuration
            api_key: Provider API key
            telemetry_callback: Optional callback for telemetry
        """
        self.config = config
        self.api_key = api_key
        self.telemetry_callback = telemetry_callback

        # Shared components
        self.cost_tracker = CostTracker(
            monthly_budget=config.cost_limit_monthly,
            warn_threshold=config.cost_limit_monthly * 0.8
        )
        self.cache_manager = CacheManager(
            ttl_seconds=getattr(config, 'cache_ttl', 3600)
        )

        # Session management
        self._session: aiohttp.ClientSession | None = None

        # Subclasses must set these in __init__
        self.base_url: str = ""
        self.headers: dict[str, str] = {}
        self.default_model: str = ""

    # ==================== Abstract Methods ====================

    @abstractmethod
    def _build_request_body(
        self,
        prompt: str,
        response_model: type[T],
        model: str,
        temperature: float,
    ) -> dict[str, Any]:
        """Build provider-specific request body.

        Args:
            prompt: The prompt text
            response_model: Pydantic model for response validation
            model: Model name
            temperature: Temperature for generation (0.0-1.0)

        Returns:
            Provider-specific request dictionary

        Example:
            OpenAI: {"model": "...", "messages": [], "response_format": {...}}
            Anthropic: {"model": "...", "messages": [], "max_tokens": 4096}
            Gemini: {"contents": [], "generationConfig": {...}}
        """
        pass

    @abstractmethod
    def _extract_text_content(self, response_data: dict[str, Any]) -> str:
        """Extract text content from provider-specific response.

        Args:
            response_data: Raw JSON response from API

        Returns:
            Extracted text content

        Raises:
            SchemaValidationError: If content cannot be extracted

        Example:
            OpenAI: response_data["choices"][0]["message"]["content"]
            Anthropic: response_data["content"][0]["text"]
            Gemini: response_data["candidates"][0]["content"]["parts"][0]["text"]
        """
        pass

    @abstractmethod
    def _extract_token_counts(self, response_data: dict[str, Any]) -> tuple[int, int]:
        """Extract token counts from provider response.

        Args:
            response_data: Raw API response

        Returns:
            Tuple of (input_tokens, output_tokens)

        Example:
            OpenAI: (usage["prompt_tokens"], usage["completion_tokens"])
            Anthropic: (usage["input_tokens"], usage["output_tokens"])
            Gemini: (usageMetadata["promptTokenCount"], usageMetadata["candidatesTokenCount"])
        """
        pass

    @abstractmethod
    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for this API call.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Example:
            OpenAI: Use CostTracker.PRICING dict
            Anthropic: Fixed rate $3/$15 per 1M tokens
            Gemini: Model-dependent (Pro vs Flash)
        """
        pass

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Get provider name for logging.

        Returns:
            Provider name (e.g., "OpenAI", "Anthropic", "Gemini")
        """
        pass

    @abstractmethod
    def _get_endpoint(self) -> str:
        """Get API endpoint URL.

        Returns:
            Full endpoint URL

        Example:
            OpenAI: "https://api.openai.com/v1/chat/completions"
            Anthropic: "https://api.anthropic.com/v1/messages"
            Gemini: "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        """
        pass

    # ==================== Lifecycle Management ====================

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize the service."""
        if self._session:
            return

        # Check for running event loop (required for Qt integration)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            logger.debug("No running event loop; deferring session creation")
            return

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

    # ==================== Core Request Flow (Template Method) ====================

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
        """Get structured completion from AI provider.

        Template Method Pattern: Orchestrates the request flow.

        Args:
            prompt: The prompt to send
            response_model: Pydantic model for response validation
            model: Model to use (defaults to self.default_model)
            temperature: Temperature for generation (0.0-1.0)
            use_cache: Whether to use caching
            context: Additional context for telemetry

        Returns:
            Validated response as Pydantic model instance

        Raises:
            RateLimitError: If rate limited by API
            QuotaExceededError: If monthly budget exceeded
            SchemaValidationError: If response doesn't match schema
        """
        # 1. Budget Check
        logger.debug(f"Current monthly cost: ${self.cost_tracker.current_month_cost:.2f}")

        # 2. Cache Lookup
        model_to_use = model or self.default_model
        cache_key = self._build_cache_key(prompt, response_model, model_to_use, use_cache)
        cached = await self._try_cache_hit(cache_key, prompt, model_to_use, response_model)
        if cached is not None:
            return cached

        # 3. Build Request
        request_body = self._build_request_body(
            prompt, response_model, model_to_use, temperature
        )

        # 4. Ensure Session
        if not self._session or self._session.closed:
            await self.initialize()

        # 5. Execute Request
        start_time = time.time()

        try:
            response_data = await self._execute_request(request_body)

            # 6. Parse Response
            text_content = self._extract_text_content(response_data)
            json_data = self._parse_json_response(text_content)
            result = self._validate_response(response_model, json_data)

            # 7. Track Costs
            input_tokens, output_tokens = self._extract_token_counts(response_data)
            cost = self._calculate_cost(model_to_use, input_tokens, output_tokens)

            # Use async track_usage method
            await self.cost_tracker.track_usage(model_to_use, input_tokens, output_tokens)

            # 8. Log Telemetry
            elapsed_ms = (time.time() - start_time) * 1000
            self._log_ai_request(
                model_to_use,
                input_tokens + output_tokens,
                cost,
                elapsed_ms
            )

            # 9. Cache Result
            if use_cache and cache_key:
                await self.cache_manager.set(
                    prompt,
                    model_to_use,
                    response_model.model_json_schema(),
                    result.model_dump()
                )

            return result

        except aiohttp.ClientError as e:
            logger.error(f"{self._get_provider_name()} API connection error: {e}")
            raise OpenAIError(f"Connection error: {e}")

    async def _execute_request(self, request_body: dict[str, Any]) -> dict[str, Any]:
        """Execute HTTP request to provider API.

        Args:
            request_body: Request payload

        Returns:
            Response JSON

        Raises:
            RateLimitError: If rate limited
            OpenAIError: For other API errors
        """
        endpoint = self._get_endpoint()

        response_ctx = self._session.post(endpoint, json=request_body)
        if inspect.isawaitable(response_ctx):
            response_ctx = await response_ctx

        async with response_ctx as response:
            # Handle rate limiting
            if response.status == 429:
                logger.warning(f"{self._get_provider_name()} rate limit hit")
                raise RateLimitError("Rate limit exceeded")

            # Handle errors
            if response.status >= 400:
                error_text = await response.text()
                logger.error(
                    f"{self._get_provider_name()} API error "
                    f"({response.status}): {error_text}"
                )
                raise OpenAIError(f"API error {response.status}: {error_text}")

            return await response.json()

    # ==================== Helper Methods ====================

    def _build_cache_key(
        self,
        prompt: str,
        response_model: type[T],
        model: str,
        use_cache: bool,
    ) -> str | None:
        """Build cache key from request parameters.

        IMPORTANT: Includes provider name to avoid cross-provider cache collisions.

        Args:
            prompt: The prompt text
            response_model: Pydantic model for response
            model: Model name
            use_cache: Whether to use caching

        Returns:
            Cache key or None if caching disabled
        """
        if not use_cache:
            return None
        content = (
            f"{self._get_provider_name()}:"
            f"{prompt}:"
            f"{response_model.__name__}:"
            f"{model}"
        )
        return hashlib.md5(content.encode()).hexdigest()

    async def _try_cache_hit(
        self,
        cache_key: str | None,
        prompt: str,
        model: str,
        response_model: type[T]
    ) -> T | None:
        """Try to get cached response.

        Args:
            cache_key: Cache key to lookup
            prompt: The prompt (for CacheManager.get signature)
            model: Model name (for CacheManager.get signature)
            response_model: Pydantic model for validation

        Returns:
            Cached response or None if miss
        """
        if not cache_key:
            return None

        # CacheManager uses different signature - call with required params
        cached = await self.cache_manager.get(
            prompt,
            model,
            response_model.model_json_schema()
        )

        if cached:
            logger.debug(f"Cache hit for {response_model.__name__}")
            return response_model.model_validate(cached)

        return None

    def _parse_json_response(self, text_content: str) -> dict[str, Any]:
        """Parse JSON response, removing markdown code blocks if present.

        Common pattern across Anthropic and Gemini.

        Args:
            text_content: Raw text content

        Returns:
            Parsed JSON dictionary

        Raises:
            SchemaValidationError: If JSON parsing fails
        """
        try:
            # Remove markdown code blocks
            if "```json" in text_content:
                text_content = text_content.split("```json")[1].split("```")[0].strip()
            elif "```" in text_content:
                text_content = text_content.split("```")[1].split("```")[0].strip()

            return json.loads(text_content)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse {self._get_provider_name()} response as JSON: {e}"
            )
            logger.debug(f"Raw content: {text_content[:500]}")
            raise SchemaValidationError(f"Invalid JSON in response: {e}")

    def _validate_response(
        self,
        response_model: type[T],
        json_data: dict[str, Any]
    ) -> T:
        """Validate response against Pydantic model.

        Args:
            response_model: Pydantic model class
            json_data: Parsed JSON data

        Returns:
            Validated model instance

        Raises:
            SchemaValidationError: If validation fails
        """
        try:
            return response_model.model_validate(json_data)
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise SchemaValidationError(f"Response doesn't match schema: {e}")

    def _log_ai_request(
        self,
        model: str,
        tokens_used: int,
        cost: float,
        elapsed_ms: float,
    ) -> None:
        """Log AI request for telemetry.

        Args:
            model: Model name
            tokens_used: Total tokens used
            cost: Cost in USD
            elapsed_ms: Request latency in milliseconds
        """
        log_ai_request(
            provider=self._get_provider_name(),
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
        return {
            "current_month_cost": self.cost_tracker.current_month_cost,
            "monthly_budget": self.cost_tracker.monthly_budget,
            "warn_threshold": self.cost_tracker.warn_threshold,
            "remaining_budget": self.cost_tracker.monthly_budget - self.cost_tracker.current_month_cost,
            "budget_used_pct": (self.cost_tracker.current_month_cost / self.cost_tracker.monthly_budget) * 100
        }

    def reset_costs(self) -> None:
        """Reset cost tracking (e.g., at start of new month)."""
        self.cost_tracker.current_month_cost = 0.0
        logger.info("Cost tracking reset")

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self.cache_manager._memory_cache.clear()
        logger.info("Response cache cleared")
