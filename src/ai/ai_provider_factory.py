"""AI Provider Factory for OrderPilot-AI.

Routes AI requests to the configured provider (OpenAI or Anthropic).
"""

import logging
import os
from typing import Optional

from PyQt6.QtCore import QSettings

from src.config.loader import config_manager, AIConfig

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """Factory for creating AI service instances based on configuration."""

    @staticmethod
    def get_provider() -> str:
        """Get the configured AI provider from QSettings.

        Returns:
            Provider name: "OpenAI" or "Anthropic"
        """
        settings = QSettings("OrderPilot", "TradingApp")
        provider = settings.value("ai_default_provider", "Anthropic")
        logger.info(f"AI Provider selected: {provider}")
        return provider

    @staticmethod
    def is_ai_enabled() -> bool:
        """Check if AI features are enabled.

        Returns:
            True if AI is enabled, False otherwise
        """
        settings = QSettings("OrderPilot", "TradingApp")
        enabled = settings.value("ai_enabled", True, type=bool)
        logger.debug(f"AI enabled: {enabled}")
        return enabled

    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Get API key for the specified provider.

        Args:
            provider: Provider name ("OpenAI" or "Anthropic")

        Returns:
            API key from environment or keyring, None if not found
        """
        if provider == "OpenAI":
            # Try environment variable first
            key = os.getenv("OPENAI_API_KEY")
            if key:
                logger.debug("Using OpenAI API key from environment")
                return key

            # Try secure keyring
            try:
                key = config_manager.get_credential("openai_api_key")
                if key:
                    logger.debug("Using OpenAI API key from keyring")
                    return key
            except Exception as e:
                logger.warning(f"Could not retrieve OpenAI key from keyring: {e}")

        elif provider == "Anthropic":
            # Try environment variable first
            key = os.getenv("ANTHROPIC_API_KEY")
            if key:
                logger.debug("Using Anthropic API key from environment")
                return key

            # Try secure keyring
            try:
                key = config_manager.get_credential("anthropic_api_key")
                if key:
                    logger.debug("Using Anthropic API key from keyring")
                    return key
            except Exception as e:
                logger.warning(f"Could not retrieve Anthropic key from keyring: {e}")

        elif provider == "Gemini":
            # Try environment variable first
            key = os.getenv("GEMINI_API_KEY")
            if key:
                logger.debug("Using Gemini API key from environment")
                return key

            # Try secure keyring
            try:
                key = config_manager.get_credential("gemini_api_key")
                if key:
                    logger.debug("Using Gemini API key from keyring")
                    return key
            except Exception as e:
                logger.warning(f"Could not retrieve Gemini key from keyring: {e}")

        logger.warning(f"No API key found for provider: {provider}")
        return None

    @staticmethod
    def get_model(provider: str) -> str:
        """Get the configured model for the provider.

        Args:
            provider: Provider name ("OpenAI" or "Anthropic")

        Returns:
            Model name/ID
        """
        settings = QSettings("OrderPilot", "TradingApp")

        if provider == "OpenAI":
            model = settings.value("openai_model", "gpt-4o")
            # Extract just the model ID (remove UI-friendly suffixes)
            if "(" in model:
                model = model.split("(")[0].strip()
            logger.debug(f"OpenAI model: {model}")
            return model

        elif provider == "Anthropic":
            model = settings.value("anthropic_model", "claude-sonnet-4-5-20250929")
            # Extract just the model ID
            if "(" in model:
                model = model.split("(")[0].strip()
            logger.debug(f"Anthropic model: {model}")
            return model

        elif provider == "Gemini":
            model = settings.value("gemini_model", "gemini-2.0-flash-exp")
            # Extract just the model ID
            if "(" in model:
                model = model.split("(")[0].strip()
            logger.debug(f"Gemini model: {model}")
            return model

        return "gpt-4o"  # Fallback

    @staticmethod
    def create_service(telemetry_callback=None):
        """Create an AI service instance based on current settings.

        Args:
            telemetry_callback: Optional callback for telemetry

        Returns:
            AI service instance (OpenAIService or AnthropicService)

        Raises:
            ValueError: If AI is disabled or API key is missing
        """
        # Check if AI is enabled
        if not AIProviderFactory.is_ai_enabled():
            raise ValueError("AI features are disabled in settings")

        # Get provider
        provider = AIProviderFactory.get_provider()

        # Get API key
        api_key = AIProviderFactory.get_api_key(provider)
        if not api_key:
            raise ValueError(f"No API key configured for {provider}. "
                           f"Set {provider.upper()}_API_KEY environment variable "
                           f"or configure in Settings -> AI tab.")

        # Get model
        model = AIProviderFactory.get_model(provider)

        # Load AI config
        ai_config = config_manager.get_ai_config()
        if not ai_config:
            # Create default config
            ai_config = AIConfig(
                enabled=True,
                cost_limit_monthly=50.0,
                timeouts={"read_ms": 15000, "connect_ms": 5000}
            )

        # Create service based on provider
        if provider == "OpenAI":
            from src.ai.openai_service import OpenAIService
            logger.info(f"✅ Creating OpenAI service with model: {model}")
            service = OpenAIService(
                config=ai_config,
                api_key=api_key,
                telemetry_callback=telemetry_callback
            )
            # Override default model if specified in settings
            service.default_model = model
            return service

        elif provider == "Anthropic":
            from src.ai.anthropic_service import AnthropicService
            logger.info(f"✅ Creating Anthropic service with model: {model}")
            service = AnthropicService(
                config=ai_config,
                api_key=api_key,
                telemetry_callback=telemetry_callback
            )
            # Override default model if specified in settings
            service.default_model = model
            return service

        elif provider == "Gemini":
            from src.ai.gemini_service import GeminiService
            logger.info(f"✅ Creating Gemini service with model: {model}")
            service = GeminiService(
                config=ai_config,
                api_key=api_key,
                telemetry_callback=telemetry_callback
            )
            # Override default model if specified in settings
            service.default_model = model
            return service

        else:
            raise ValueError(f"Unknown AI provider: {provider}")

    @staticmethod
    def get_monthly_budget() -> float:
        """Get the configured monthly AI budget.

        Returns:
            Monthly budget in EUR
        """
        settings = QSettings("OrderPilot", "TradingApp")
        budget = settings.value("ai_budget", 50.0, type=float)
        logger.debug(f"AI monthly budget: €{budget}")
        return budget
