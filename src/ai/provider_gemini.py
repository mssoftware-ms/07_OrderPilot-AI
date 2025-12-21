"""Google Gemini AI Provider Implementation.

Supports:
- gemini-2.0-flash-exp (Latest, fast)
- gemini-1.5-pro (Most capable)
- gemini-1.5-flash (Fast and efficient)
"""

from __future__ import annotations

import json
import logging
import os
from typing import AsyncIterator, TypeVar

from pydantic import BaseModel

from .provider_base import AIProviderBase, ProviderConfig

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class GeminiProvider(AIProviderBase):
    """Google Gemini AI provider.

    Supports:
    - gemini-2.0-flash-exp (Latest, fast)
    - gemini-1.5-pro (Most capable)
    - gemini-1.5-flash (Fast and efficient)
    """

    def __init__(self, config: ProviderConfig):
        """Initialize Gemini provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        # Set defaults
        if not config.api_key:
            config.api_key = os.getenv("GEMINI_API_KEY")
        if not config.base_url:
            config.base_url = "https://generativelanguage.googleapis.com/v1beta"

        if not config.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        self.headers = {
            "Content-Type": "application/json"
        }

    async def structured_completion(
        self,
        prompt: str,
        response_model: type[T],
        **kwargs
    ) -> T:
        """Get structured completion from Gemini.

        Args:
            prompt: Input prompt
            response_model: Pydantic model for response structure
            **kwargs: Additional parameters

        Returns:
            Parsed response as Pydantic model instance
        """
        if not self._session:
            await self.initialize()

        # Gemini uses JSON mode via response_mime_type
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        enhanced_prompt = f"""{prompt}

Please respond with ONLY a valid JSON object matching this schema:

{schema_str}

Do not include any explanation, markdown formatting, or code blocks. Only output the raw JSON object."""

        request_data = {
            "contents": [{"parts": [{"text": enhanced_prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
                "responseMimeType": "application/json"
            }
        }

        url = f"{self.config.base_url}/models/{self.config.model}:generateContent?key={self.config.api_key}"

        logger.debug(f"Gemini request: model={self.config.model}")

        async with self._session.post(url, json=request_data, headers=self.headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Gemini API error ({response.status}): {error_text}")

            data = await response.json()

            # Extract content from Gemini response
            try:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                raise RuntimeError(f"Unexpected Gemini response format: {data}") from e

            # Clean up response (remove any markdown if present)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Parse JSON and create model
            parsed = json.loads(content)
            return response_model(**parsed)

    async def stream_completion(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion from Gemini.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Yields:
            Text chunks from the streaming response
        """
        if not self._session:
            await self.initialize()

        request_data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens)
            }
        }

        url = f"{self.config.base_url}/models/{self.config.model}:streamGenerateContent?key={self.config.api_key}&alt=sse"

        async with self._session.post(url, json=request_data, headers=self.headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Gemini streaming error ({response.status}): {error_text}")

            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if not line_str or not line_str.startswith("data: "):
                    continue

                data_str = line_str[6:]  # Remove "data: " prefix
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    if candidates := data.get("candidates", []):
                        if content := candidates[0].get("content", {}):
                            if parts := content.get("parts", []):
                                if text := parts[0].get("text"):
                                    yield text
                except json.JSONDecodeError:
                    continue
