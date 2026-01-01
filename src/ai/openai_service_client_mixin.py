from __future__ import annotations

import json
import logging
import time
from typing import Any, TypeVar

import aiohttp
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate
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
    QuotaExceededError,
    RateLimitError,
    SchemaValidationError,
    StrategySignalAnalysis,
    StrategyTradeAnalysis,
)
from .openai_utils import CacheManager, CostTracker

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class OpenAIServiceClientMixin:
    """OpenAIServiceClientMixin extracted from OpenAIService."""
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
    def _supports_json_schema(self, model: str) -> bool:
        """Check if model supports json_schema structured outputs.

        Args:
            model: Model name

        Returns:
            True if model supports json_schema, False otherwise
        """
        # Models that support json_schema (as of January 2026)
        supported_models = [
            "gpt-4o",
            "gpt-4o-2024-08-06",
            "gpt-4o-mini",
            "gpt-4o-mini-2024-07-18",
            "gpt-4-turbo",
            "gpt-4-0125-preview",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo",
        ]

        # Check exact match or prefix match
        return any(model.startswith(supported) for supported in supported_models)
    async def structured_completion(
        self,
        prompt: str,
        response_model: type[T],
        model: str | None = None,
        temperature: float = 0.2,
        use_cache: bool = True,
        context: dict[str, Any] | None = None
    ) -> T:
        """Get structured completion from OpenAI.

        Args:
            prompt: The prompt
            response_model: Pydantic model for response structure
            model: Model to use (defaults to config)
            temperature: Temperature for generation
            use_cache: Whether to use caching
            context: Additional context for telemetry

        Returns:
            Parsed response as Pydantic model instance

        Raises:
            Various OpenAI errors
        """
        # Use model priority: parameter > default_model > config.model > "gpt-4o"
        if model is None:
            model = self.default_model or getattr(self.config, 'model', None) or "gpt-4o"

        schema = response_model.model_json_schema()

        # Check cache
        if use_cache:
            cached = await self.cache_manager.get(prompt, model, schema)
            if cached:
                return response_model(**cached)

        # Ensure session is initialized and not closed
        if not self._session or self._session.closed:
            await self.initialize()

        # Check if model supports json_schema
        supports_json_schema = self._supports_json_schema(model)

        if not supports_json_schema:
            logger.warning(
                f"Model '{model}' does not support json_schema. "
                f"Falling back to JSON mode. "
                f"For structured outputs, use gpt-4o or gpt-4o-mini."
            )

        # Prepare request with appropriate response_format
        if supports_json_schema:
            # Use structured outputs (json_schema)
            request_data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "strict": True,
                        "schema": schema
                    }
                }
            }
        else:
            # Fallback to JSON mode with schema in prompt
            schema_prompt = (
                f"{prompt}\n\n"
                f"IMPORTANT: Respond with valid JSON matching this schema:\n"
                f"```json\n{json.dumps(schema, indent=2)}\n```"
            )
            request_data = {
                "model": model,
                "messages": [{"role": "user", "content": schema_prompt}],
                "temperature": temperature,
                "response_format": {"type": "json_object"}
            }

        start_time = time.monotonic()

        try:
            # Make API request
            async with self._session.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            ) as response:
                response_data = await response.json()

                # Handle errors
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    raise OpenAIError(f"API error ({response.status}): {error_msg}")

                # Extract content
                content = response_data["choices"][0]["message"]["content"]

                # Check for refusal
                if refusal := response_data["choices"][0]["message"].get("refusal"):
                    logger.warning(f"Request refused: {refusal}")
                    raise OpenAIError(f"Request refused: {refusal}")

                # Parse JSON response
                parsed_content = json.loads(content)

                # Validate against schema
                try:
                    validate(instance=parsed_content, schema=schema)
                except JsonSchemaValidationError as e:
                    raise SchemaValidationError(f"Response validation failed: {e}")

                # Track usage and costs
                usage = response_data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

                cost = await self.cost_tracker.track_usage(
                    model, input_tokens, output_tokens
                )

                # Log telemetry
                latency_ms = int((time.monotonic() - start_time) * 1000)

                log_ai_request(
                    model=model,
                    tokens=input_tokens + output_tokens,
                    cost=cost,
                    latency=latency_ms / 1000,
                    prompt_version="1.0",
                    request_type=response_model.__name__,
                    details=context
                )

                if self.telemetry_callback:
                    self.telemetry_callback(
                        tokens=input_tokens + output_tokens,
                        cost=cost,
                        latency_ms=latency_ms,
                        feature="structured_completion"
                    )

                # Cache response
                if use_cache:
                    await self.cache_manager.set(prompt, model, schema, parsed_content)

                # Return parsed model
                return response_model(**parsed_content)

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Get chat completion from OpenAI (for conversational responses).

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to config)
            temperature: Temperature for generation

        Returns:
            Response text

        Raises:
            Various OpenAI errors
        """
        # Use model priority: parameter > default_model > config.model > "gpt-5.1"
        if model is None:
            model = self.default_model or getattr(self.config, 'model', None) or "gpt-5.1"

        # Ensure session is initialized and not closed
        if not self._session or self._session.closed:
            await self.initialize()

        # Prepare request (simple chat, no structured output)
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        start_time = time.monotonic()

        try:
            # Make API request
            async with self._session.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            ) as response:
                response_data = await response.json()

                # Handle errors
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    raise OpenAIError(f"API error ({response.status}): {error_msg}")

                # Extract content
                content = response_data["choices"][0]["message"]["content"]

                # Check for refusal
                if refusal := response_data["choices"][0]["message"].get("refusal"):
                    logger.warning(f"Request refused: {refusal}")
                    raise OpenAIError(f"Request refused: {refusal}")

                # Track usage and costs
                usage = response_data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

                cost = await self.cost_tracker.track_usage(
                    model, input_tokens, output_tokens
                )

                # Log telemetry
                latency_ms = int((time.monotonic() - start_time) * 1000)

                log_ai_request(
                    model=model,
                    tokens=input_tokens + output_tokens,
                    cost=cost,
                    latency=latency_ms / 1000,
                    prompt_version="1.0",
                    request_type="chat_completion",
                    details=None
                )

                if self.telemetry_callback:
                    self.telemetry_callback(
                        tokens=input_tokens + output_tokens,
                        cost=cost,
                        latency_ms=latency_ms,
                        feature="chat_completion"
                    )

                return content

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
