"""Google Gemini Service for OrderPilot-AI Trading Application.

Implements Gemini API integration with structured outputs,
inheriting from BaseAIService for code reuse and consistency.

Supports:
- gemini-2.0-flash-exp (Latest, experimental)
- gemini-1.5-pro (Most capable)
- gemini-1.5-flash (Fast and efficient)
"""

from __future__ import annotations

import json
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


class GeminiService(BaseAIService):
    """Google Gemini service implementation.

    Inherits common functionality from BaseAIService and provides
    Gemini-specific implementations for abstract methods.
    """

    def __init__(
        self,
        config: AIConfig,
        api_key: str,
        telemetry_callback: callable | None = None
    ):
        """Initialize Gemini service.

        Args:
            config: AI configuration
            api_key: Gemini API key
            telemetry_callback: Optional callback for telemetry
        """
        # Initialize base class
        super().__init__(config, api_key, telemetry_callback)

        # Gemini-specific settings
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        # Gemini uses API key in URL params, not headers
        self.headers = {"Content-Type": "application/json"}
        self.default_model = "gemini-2.0-flash-exp"

    # ==================== Abstract Method Implementations ====================

    def _build_request_body(
        self,
        prompt: str,
        response_model: type[T],
        model: str,
        temperature: float,
    ) -> dict[str, Any]:
        """Build Gemini-specific request body.

        Args:
            prompt: The prompt text
            response_model: Pydantic model for response validation
            model: Model name
            temperature: Temperature for generation (0.0-1.0)

        Returns:
            Gemini API request dictionary
        """
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)
        enhanced_prompt = f"""{prompt}

IMPORTANT: Respond with valid JSON matching this exact schema:

{schema_str}

Do not include any explanation, markdown formatting, or code blocks. Only output the raw JSON object."""

        return {
            "contents": [{"parts": [{"text": enhanced_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json",
            },
        }

    def _extract_text_content(self, response_data: dict[str, Any]) -> str:
        """Extract text content from Gemini response.

        Args:
            response_data: Raw JSON response from Gemini API

        Returns:
            Extracted text content

        Raises:
            SchemaValidationError: If content cannot be extracted
        """
        candidates = response_data.get("candidates", [])
        if not candidates:
            # Check for safety filter blocking
            if "promptFeedback" in response_data:
                feedback = response_data["promptFeedback"]
                block_reason = feedback.get("blockReason", "Unknown")
                raise SchemaValidationError(f"Response blocked by safety filter: {block_reason}")
            raise SchemaValidationError("No candidates in Gemini response")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise SchemaValidationError("No content parts in Gemini response")

        return parts[0].get("text", "")

    def _extract_token_counts(self, response_data: dict[str, Any]) -> tuple[int, int]:
        """Extract token counts from Gemini response.

        Args:
            response_data: Raw API response

        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        usage_metadata = response_data.get("usageMetadata", {})
        return (
            usage_metadata.get("promptTokenCount", 0),
            usage_metadata.get("candidatesTokenCount", 0)
        )

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for Gemini API call.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Note:
            Gemini pricing varies by model:
            - Pro models: $1.25/1M input, $5.00/1M output
            - Flash models: $0.10/1M input, $0.30/1M output
        """
        if "pro" in model.lower():
            return (input_tokens * 1.25 / 1_000_000) + (output_tokens * 5.0 / 1_000_000)
        # Flash model (default)
        return (input_tokens * 0.10 / 1_000_000) + (output_tokens * 0.30 / 1_000_000)

    def _get_provider_name(self) -> str:
        """Get provider name for logging.

        Returns:
            Provider name
        """
        return "Gemini"

    def _get_endpoint(self) -> str:
        """Get Gemini API endpoint URL.

        Gemini uses API key in URL params instead of headers.

        Returns:
            Full endpoint URL with API key
        """
        # Model is set in structured_completion, so we use default here
        # The actual model will be used in the POST request
        return f"{self.base_url}/models/{self.default_model}:generateContent?key={self.api_key}"
