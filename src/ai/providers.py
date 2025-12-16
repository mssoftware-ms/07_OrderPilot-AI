"""AI Provider Abstraction for Multiple AI Services.

Supports:
- OpenAI (GPT-5.1, GPT-5.1 Thinking)
- Anthropic (Claude Sonnet 4.5)

Handles streaming, reasoning modes, and structured outputs across providers.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, TypeVar

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class ReasoningMode(str, Enum):
    """Reasoning modes for AI models."""
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""
    provider: AIProvider
    model: str
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.2
    reasoning_mode: ReasoningMode = ReasoningMode.MEDIUM
    streaming: bool = False


class AIProviderBase(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, config: ProviderConfig):
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._session: aiohttp.ClientSession | None = None

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        """Close the provider."""
        if self._session:
            await self._session.close()
            self._session = None

    @abstractmethod
    async def structured_completion(
        self,
        prompt: str,
        response_model: type[T],
        **kwargs
    ) -> T:
        """Get structured completion from the AI model.

        Args:
            prompt: Input prompt
            response_model: Pydantic model for response structure
            **kwargs: Additional provider-specific parameters

        Returns:
            Parsed response as Pydantic model instance
        """
        pass

    @abstractmethod
    async def stream_completion(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion from the AI model.

        Args:
            prompt: Input prompt
            **kwargs: Additional provider-specific parameters

        Yields:
            Text chunks from the streaming response
        """
        pass


class OpenAIProvider(AIProviderBase):
    """OpenAI API provider supporting GPT-5.1 and thinking modes."""

    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        # Set defaults
        if not config.api_key:
            config.api_key = os.getenv("OPENAI_API_KEY")
        if not config.base_url:
            config.base_url = "https://api.openai.com/v1"

        if not config.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

    async def structured_completion(
        self,
        prompt: str,
        response_model: type[T],
        **kwargs
    ) -> T:
        """Get structured completion from OpenAI.

        Args:
            prompt: Input prompt
            response_model: Pydantic model for response structure
            **kwargs: Additional parameters

        Returns:
            Parsed response as Pydantic model instance
        """
        if not self._session:
            await self.initialize()

        schema = response_model.model_json_schema()

        # Build request
        request_data = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_completion_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": schema
                }
            }
        }

        # Add reasoning_effort if model supports it (GPT-5.1 Thinking)
        if "gpt-5" in self.config.model and self.config.reasoning_mode != ReasoningMode.NONE:
            request_data["reasoning_effort"] = self.config.reasoning_mode.value

        logger.debug(f"OpenAI request: model={self.config.model}, reasoning={self.config.reasoning_mode}")

        async with self._session.post(
            f"{self.config.base_url}/chat/completions",
            json=request_data,
            headers=self.headers
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"OpenAI API error ({response.status}): {error_text}")

            data = await response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON and create model
            parsed = json.loads(content)
            return response_model(**parsed)

    async def stream_completion(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion from OpenAI.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Yields:
            Text chunks from the streaming response
        """
        if not self._session:
            await self.initialize()

        request_data = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_completion_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True
        }

        # Add reasoning_effort if supported
        if "gpt-5" in self.config.model and self.config.reasoning_mode != ReasoningMode.NONE:
            request_data["reasoning_effort"] = self.config.reasoning_mode.value

        async with self._session.post(
            f"{self.config.base_url}/chat/completions",
            json=request_data,
            headers=self.headers
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"OpenAI API error ({response.status}): {error_text}")

            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix

                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        if choices := data.get("choices", []):
                            if delta := choices[0].get("delta", {}):
                                if content := delta.get("content"):
                                    yield content
                    except json.JSONDecodeError:
                        continue


class AnthropicProvider(AIProviderBase):
    """Anthropic API provider supporting Claude Sonnet 4.5."""

    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        # Set defaults
        if not config.api_key:
            config.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not config.base_url:
            config.base_url = "https://api.anthropic.com/v1"

        if not config.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    async def structured_completion(
        self,
        prompt: str,
        response_model: type[T],
        **kwargs
    ) -> T:
        """Get structured completion from Anthropic.

        Args:
            prompt: Input prompt
            response_model: Pydantic model for response structure
            **kwargs: Additional parameters

        Returns:
            Parsed response as Pydantic model instance
        """
        if not self._session:
            await self.initialize()

        # Anthropic doesn't have native structured output,
        # so we'll request JSON format in the prompt
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        enhanced_prompt = f"""{prompt}

Please respond with ONLY a valid JSON object matching this schema:

{schema_str}

Do not include any explanation, only the JSON object."""

        request_data = {
            "model": self.config.model,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "messages": [{"role": "user", "content": enhanced_prompt}]
        }

        logger.debug(f"Anthropic request: model={self.config.model}")

        async with self._session.post(
            f"{self.config.base_url}/messages",
            json=request_data,
            headers=self.headers
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Anthropic API error ({response.status}): {error_text}")

            data = await response.json()
            content = data["content"][0]["text"]

            # Extract JSON from response (may have code blocks)
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
        """Stream completion from Anthropic.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Yields:
            Text chunks from the streaming response
        """
        if not self._session:
            await self.initialize()

        request_data = {
            "model": self.config.model,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }

        async with self._session.post(
            f"{self.config.base_url}/messages",
            json=request_data,
            headers=self.headers
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Anthropic API error ({response.status}): {error_text}")

            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix

                    try:
                        data = json.loads(data_str)

                        # Handle different event types
                        if data.get("type") == "content_block_delta":
                            if delta := data.get("delta", {}):
                                if text := delta.get("text"):
                                    yield text
                        elif data.get("type") == "message_stop":
                            break
                    except json.JSONDecodeError:
                        continue


# ==================== Gemini Provider ====================

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


# ==================== Provider Factory ====================

def create_provider(
    provider: AIProvider,
    model: str,
    **kwargs
) -> AIProviderBase:
    """Create an AI provider instance.

    Args:
        provider: Provider type
        model: Model name
        **kwargs: Additional configuration

    Returns:
        Provider instance

    Examples:
        >>> # OpenAI GPT-5.1 with thinking
        >>> provider = create_provider(
        ...     AIProvider.OPENAI,
        ...     "gpt-5.1",
        ...     reasoning_mode=ReasoningMode.HIGH
        ... )
        >>>
        >>> # OpenAI GPT-5.1 Instant (no thinking)
        >>> provider = create_provider(
        ...     AIProvider.OPENAI,
        ...     "gpt-5.1-chat-latest",
        ...     reasoning_mode=ReasoningMode.NONE
        ... )
        >>>
        >>> # Anthropic Claude Sonnet 4.5
        >>> provider = create_provider(
        ...     AIProvider.ANTHROPIC,
        ...     "claude-sonnet-4-5-20250929"
        ... )
    """
    config = ProviderConfig(
        provider=provider,
        model=model,
        **kwargs
    )

    if provider == AIProvider.OPENAI:
        return OpenAIProvider(config)
    elif provider == AIProvider.ANTHROPIC:
        return AnthropicProvider(config)
    elif provider == AIProvider.GEMINI:
        return GeminiProvider(config)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


# ==================== Convenience Functions ====================

async def get_openai_gpt51_thinking(**kwargs) -> OpenAIProvider:
    """Get OpenAI GPT-5.1 with thinking mode.

    Args:
        **kwargs: Additional configuration

    Returns:
        Configured OpenAI provider
    """
    return create_provider(
        AIProvider.OPENAI,
        "gpt-5.1",
        reasoning_mode=kwargs.pop("reasoning_mode", ReasoningMode.MEDIUM),
        **kwargs
    )


async def get_openai_gpt51_instant(**kwargs) -> OpenAIProvider:
    """Get OpenAI GPT-5.1 Instant (no thinking).

    Args:
        **kwargs: Additional configuration

    Returns:
        Configured OpenAI provider
    """
    return create_provider(
        AIProvider.OPENAI,
        "gpt-5.1-chat-latest",
        reasoning_mode=ReasoningMode.NONE,
        **kwargs
    )


async def get_anthropic_sonnet45(**kwargs) -> AnthropicProvider:
    """Get Anthropic Claude Sonnet 4.5.

    Args:
        **kwargs: Additional configuration

    Returns:
        Configured Anthropic provider
    """
    return create_provider(
        AIProvider.ANTHROPIC,
        "claude-sonnet-4-5-20250929",
        **kwargs
    )


async def get_gemini_flash(**kwargs) -> GeminiProvider:
    """Get Google Gemini 2.0 Flash (experimental).

    Args:
        **kwargs: Additional configuration

    Returns:
        Configured Gemini provider
    """
    return create_provider(
        AIProvider.GEMINI,
        "gemini-2.0-flash-exp",
        **kwargs
    )


async def get_gemini_pro(**kwargs) -> GeminiProvider:
    """Get Google Gemini 1.5 Pro.

    Args:
        **kwargs: Additional configuration

    Returns:
        Configured Gemini provider
    """
    return create_provider(
        AIProvider.GEMINI,
        "gemini-1.5-pro",
        **kwargs
    )
