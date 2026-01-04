"""OpenAI Service for OrderPilot-AI Trading Application."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

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
from .openai_service_analysis_mixin import OpenAIServiceAnalysisMixin
from .openai_service_client_mixin import OpenAIServiceClientMixin
from .openai_service_prompt_mixin import OpenAIServicePromptMixin

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
    OpenAIServiceClientMixin,
    OpenAIServiceAnalysisMixin,
    OpenAIServicePromptMixin,
):
    """Main OpenAI service for structured outputs."""

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
        self.config = config
        self.api_key = api_key
        self.telemetry_callback = telemetry_callback

        # Default model (can be overridden by factory)
        self.default_model: str | None = None

        # Initialize components
        self.cost_tracker = CostTracker(
            monthly_budget=config.cost_limit_monthly,
            warn_threshold=config.cost_limit_monthly * 0.8  # Warn at 80%
        )
        self.cache_manager = CacheManager(
            ttl_seconds=config.cache_ttl if hasattr(config, 'cache_ttl') else 3600
        )

        # API settings
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Session for connection pooling
        self._session: aiohttp.ClientSession | None = None


async def get_openai_service(
    config: AIConfig,
    api_key: str
) -> OpenAIService:
    """Get or create OpenAI service instance.

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
