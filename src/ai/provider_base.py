"""AI Provider Base Types and Abstract Base Class.

Contains:
- AIProvider enum
- ReasoningMode enum
- ProviderConfig model
- AIProviderBase abstract base class
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncIterator, TypeVar

import aiohttp
from pydantic import BaseModel

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
