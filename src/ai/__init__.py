"""AI Package for OrderPilot-AI Trading Application."""

from .openai_service import (
    AlertTriageResult,
    BacktestReview,
    CacheManager,
    CostTracker,
    OpenAIError,
    OpenAIService,
    OrderAnalysis,
    QuotaExceededError,
    RateLimitError,
    SchemaValidationError,
    StrategySignalAnalysis,
    StrategyTradeAnalysis,
    get_openai_service,
)
from .anthropic_service import AnthropicService
from .gemini_service import GeminiService
from .ai_provider_factory import AIProviderFactory
from .prompts import JSONSchemas, PromptBuilder, PromptTemplates, PromptVersion, SchemaValidator


# ==================== Unified AI Service Getter ====================

_unified_service_instance = None


async def get_ai_service(telemetry_callback=None):
    """Get AI service instance based on settings (OpenAI or Anthropic).

    Uses AIProviderFactory to create the appropriate service based on
    user settings in QSettings.

    Args:
        telemetry_callback: Optional callback for telemetry

    Returns:
        AI service instance (OpenAIService or AnthropicService)

    Raises:
        ValueError: If AI is disabled or not configured
    """
    global _unified_service_instance

    if _unified_service_instance is None:
        # Create service using factory
        _unified_service_instance = AIProviderFactory.create_service(
            telemetry_callback=telemetry_callback
        )
        await _unified_service_instance.initialize()

    return _unified_service_instance


def reset_ai_service():
    """Reset the AI service instance (e.g., when settings change)."""
    global _unified_service_instance
    _unified_service_instance = None


__all__ = [
    # Services
    'OpenAIService',
    'AnthropicService',
    'GeminiService',
    'get_openai_service',
    'get_ai_service',  # NEW: Unified multi-provider getter
    'reset_ai_service',
    'AIProviderFactory',
    # Errors
    'OpenAIError',
    'RateLimitError',
    'QuotaExceededError',
    'SchemaValidationError',
    # Response Models
    'OrderAnalysis',
    'AlertTriageResult',
    'BacktestReview',
    'StrategySignalAnalysis',
    # Components
    'CostTracker',
    'CacheManager',
    # Prompts
    'PromptTemplates',
    'JSONSchemas',
    'PromptBuilder',
    'SchemaValidator',
    'PromptVersion'
]