"""OpenAI Service for OrderPilot-AI Trading Application.

Inherits from BaseAIService and uses mixins for OpenAI-specific functionality.
"""

from __future__ import annotations

import logging
from typing import Any

from src.config.loader import AIConfig

# Import base class
from .base_service import BaseAIService

# Import models
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

# Import utilities
from .openai_utils import CacheManager, CostTracker

# Import mixins (kept for OpenAI-specific functionality)
from .openai_service_analysis_mixin import OpenAIServiceAnalysisMixin
from .openai_service_prompt_mixin import OpenAIServicePromptMixin
from .openai_service_client_mixin import OpenAIServiceClientMixin

# Re-export models for backward compatibility
__all__ = [
    "OpenAIError",
    "RateLimitError",
    "QuotaExceededError",
    "SchemaValidationError",
    "OrderAnalysis",
    "AlertTriageResult",
    "BacktestReview",
    "StrategySignalAnalysis",
    "StrategyTradeAnalysis",
    "CostTracker",
    "CacheManager",
    "OpenAIService",
    "get_openai_service",
]

logger = logging.getLogger(__name__)

# Global singleton instance
_service_instance: OpenAIService | None = None


class OpenAIService(
    OpenAIServiceClientMixin,  # OpenAI-specific client methods (json_schema support, chat_completion)
    OpenAIServicePromptMixin,  # Domain-specific prompt builders
    OpenAIServiceAnalysisMixin,  # High-level analysis methods
    BaseAIService  # Base class with shared functionality
):
    """OpenAI service implementation.

    Inherits from BaseAIService for common functionality and uses mixins
    for OpenAI-specific features (json_schema support, prompt building).
    """

    def __init__(
        self,
        config: AIConfig,
        api_key: str,
        telemetry_callback: callable | None = None
    ):
        """Initialize OpenAI service.

        Args:
            config: AI configuration
            api_key: OpenAI API key
            telemetry_callback: Optional callback for telemetry
        """
        # Initialize base class
        BaseAIService.__init__(self, config, api_key, telemetry_callback)

        # OpenAI-specific settings
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.default_model = "gpt-4o-mini"

    # ==================== Abstract Method Implementations ====================

    def _build_request_body(
        self,
        prompt: str,
        response_model: type,
        model: str,
        temperature: float,
    ) -> dict[str, Any]:
        """Build OpenAI-specific request body.

        OpenAI supports native json_schema for structured outputs.

        Args:
            prompt: The prompt text
            response_model: Pydantic model for response validation
            model: Model name
            temperature: Temperature for generation (0.0-1.0)

        Returns:
            OpenAI API request dictionary
        """
        schema = response_model.model_json_schema()

        # Check if model supports json_schema
        if self._supports_json_schema(model):
            return {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "strict": True,
                        "schema": schema,
                    },
                },
            }

        # Fallback for models without json_schema support
        import json
        schema_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: Respond with valid JSON matching this schema:\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```"
        )
        return {
            "model": model,
            "messages": [{"role": "user", "content": schema_prompt}],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

    def _extract_text_content(self, response_data: dict[str, Any]) -> str:
        """Extract text content from OpenAI response.

        Args:
            response_data: Raw JSON response from OpenAI API

        Returns:
            Extracted text content

        Raises:
            OpenAIError: If refusal or content cannot be extracted
        """
        try:
            content = response_data["choices"][0]["message"]["content"]

            # Check for refusal (OpenAI-specific)
            if refusal := response_data["choices"][0]["message"].get("refusal"):
                logger.warning(f"Request refused: {refusal}")
                raise OpenAIError(f"Request refused: {refusal}")

            return content
        except (KeyError, IndexError) as e:
            raise OpenAIError(f"Failed to extract content from response: {e}")

    def _extract_token_counts(self, response_data: dict[str, Any]) -> tuple[int, int]:
        """Extract token counts from OpenAI response.

        Args:
            response_data: Raw API response

        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        usage = response_data.get("usage", {})
        return (usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for OpenAI API call.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Note:
            Uses CostTracker.PRICING for model-specific pricing
        """
        # Remove date suffix if present (e.g., gpt-4o-2024-08-06 -> gpt-4o)
        model_base = model.split("-202")[0] if "-202" in model else model

        # Get pricing from CostTracker
        pricing = self.cost_tracker.PRICING.get(model_base, self.cost_tracker.PRICING["gpt-4o-mini"])

        return (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])

    def _get_provider_name(self) -> str:
        """Get provider name for logging.

        Returns:
            Provider name
        """
        return "OpenAI"

    def _get_endpoint(self) -> str:
        """Get OpenAI API endpoint URL.

        Returns:
            Full endpoint URL
        """
        return f"{self.base_url}/chat/completions"


async def get_openai_service(
    config: AIConfig,
    api_key: str
) -> OpenAIService:
    """Get or create OpenAI service instance (singleton pattern).

    Args:
        config: AI configuration
        api_key: OpenAI API key

    Returns:
        OpenAI service instance
    """
    global _service_instance

    # Guard against cases where the module globals were cleared (e.g., during reload/shutdown)
    if "_service_instance" not in globals():
        _service_instance = None

    if _service_instance is None:
        _service_instance = OpenAIService(config, api_key)
        await _service_instance.initialize()

    return _service_instance
