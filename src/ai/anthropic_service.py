"""Anthropic Claude Service for OrderPilot-AI Trading Application.

Implements Anthropic API integration with structured outputs,
inheriting from BaseAIService for code reuse and consistency.
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from src.config.loader import AIConfig

# Import base class
from .base_service import BaseAIService

# Import shared models
from .openai_models import SchemaValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class AnthropicService(BaseAIService):
    """Anthropic Claude service implementation.

    Inherits common functionality from BaseAIService and provides
    Anthropic-specific implementations for abstract methods.
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
        # Initialize base class
        super().__init__(config, api_key, telemetry_callback)

        # Anthropic-specific settings
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,  # Anthropic uses x-api-key instead of Authorization
            "anthropic-version": "2023-06-01",  # Required header
            "Content-Type": "application/json"
        }
        self.default_model = "claude-sonnet-4-5-20250929"

    # ==================== Abstract Method Implementations ====================

    def _build_request_body(
        self,
        prompt: str,
        response_model: type[T],
        model: str,
        temperature: float,
    ) -> dict[str, Any]:
        """Build Anthropic-specific request body.

        Args:
            prompt: The prompt text
            response_model: Pydantic model for response validation
            model: Model name
            temperature: Temperature for generation (0.0-1.0)

        Returns:
            Anthropic API request dictionary
        """
        return {
            "model": model,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\n"
                        f"IMPORTANT: Respond with valid JSON matching this schema:\n"
                        f"{response_model.model_json_schema()}"
                    ),
                }
            ],
        }

    def _extract_text_content(self, response_data: dict[str, Any]) -> str:
        """Extract text content from Anthropic response.

        Args:
            response_data: Raw JSON response from Anthropic API

        Returns:
            Extracted text content

        Raises:
            SchemaValidationError: If content cannot be extracted
        """
        content_blocks = response_data.get("content", [])
        if not content_blocks:
            raise SchemaValidationError("No content in Anthropic response")
        return content_blocks[0].get("text", "")

    def _extract_token_counts(self, response_data: dict[str, Any]) -> tuple[int, int]:
        """Extract token counts from Anthropic response.

        Args:
            response_data: Raw API response

        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        usage = response_data.get("usage", {})
        return (usage.get("input_tokens", 0), usage.get("output_tokens", 0))

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for Anthropic API call.

        Args:
            model: Model name (not used, Anthropic has fixed pricing)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Note:
            Claude Sonnet 4 pricing: $3/1M input tokens, $15/1M output tokens
        """
        return (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)

    def _get_provider_name(self) -> str:
        """Get provider name for logging.

        Returns:
            Provider name
        """
        return "Anthropic"

    def _get_endpoint(self) -> str:
        """Get Anthropic API endpoint URL.

        Returns:
            Full endpoint URL
        """
        return f"{self.base_url}/messages"
