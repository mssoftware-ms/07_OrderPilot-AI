"""AI Provider Factory for OrderPilot-AI.

Routes AI requests to the configured provider (OpenAI or Anthropic).
"""

import logging
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QSettings

from src.config.loader import config_manager, AIConfig

logger = logging.getLogger(__name__)

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Try to load from config/secrets/.env
    env_path = Path(__file__).parent.parent.parent / "config" / "secrets" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded .env from {env_path}")
except ImportError:
    pass  # dotenv not installed, use OS environment variables


class AIProviderFactory:
    """Factory for creating AI service instances based on configuration."""

    @staticmethod
    def get_provider() -> str:
        """Get the configured AI provider from QSettings.

        Returns:
            Provider name: "OpenAI" or "Anthropic"
        """
        settings = QSettings("OrderPilot", "TradingApp")
        provider = settings.value("ai_default_provider", "OpenAI")  # Default to OpenAI
        logger.info(f"🤖 AI Provider from settings: {provider}")

        # Log all available env keys for debugging
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        logger.info(f"🔑 Available API keys - OpenAI: {'✓' if openai_key else '✗'}, "
                    f"Anthropic: {'✓' if anthropic_key else '✗'}, "
                    f"Gemini: {'✓' if gemini_key else '✗'}")

        return provider

    @staticmethod
    def is_ai_enabled() -> bool:
        """Check if AI features are enabled.

        Returns:
            True if AI is enabled, False otherwise
        """
        settings = QSettings("OrderPilot", "TradingApp")
        # Get raw value to see what's actually stored
        raw_value = settings.value("ai_enabled")
        logger.info(f"🔧 AI enabled - raw value from QSettings: {raw_value!r} (type: {type(raw_value).__name__})")

        # Handle various possible stored values
        if raw_value is None:
            # No setting saved - default to True
            logger.info("🔧 AI enabled: No setting found, defaulting to True")
            return True

        # Handle string values (QSettings sometimes stores as string)
        if isinstance(raw_value, str):
            enabled = raw_value.lower() not in ('false', '0', 'no', 'off', '')
        else:
            enabled = bool(raw_value)

        logger.info(f"🔧 AI enabled: {enabled}")
        return enabled

    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Get API key for the specified provider.

        Args:
            provider: Provider name ("OpenAI" or "Anthropic")

        Returns:
            API key from environment or keyring, None if not found
        """
        logger.info(f"Looking for API key for provider: {provider}")

        if provider == "OpenAI":
            # Try environment variable first
            key = os.getenv("OPENAI_API_KEY")
            logger.info(f"OPENAI_API_KEY from env: {'found (' + key[:10] + '...)' if key else 'NOT FOUND'}")
            if key:
                logger.info("Using OpenAI API key from environment")
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
            logger.info(f"ANTHROPIC_API_KEY from env: {'found (' + key[:10] + '...)' if key else 'NOT FOUND'}")
            if key:
                logger.info("Using Anthropic API key from environment")
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
    def _validate_model(provider: str, model: str) -> str:
        """Validate and correct model name if needed.

        Args:
            provider: Provider name
            model: Model name to validate

        Returns:
            Valid model name (original or corrected default)
        """
        # Valid models as of January 2026
        valid_models = {
            "OpenAI": [
                # GPT-5 series (latest) - NOTE: No structured outputs support yet
                "gpt-5.2", "gpt-5.1", "gpt-5",
                "gpt-5-thinking", "gpt-5-mini", "gpt-5-nano",
                # GPT-4 series (gpt-4o supports structured outputs!)
                "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
                "gpt-4o", "gpt-4o-mini",  # Needed for structured outputs
                "gpt-4-turbo", "gpt-4",
                # o-series (reasoning models)
                "o3", "o3-mini", "o3-pro",
                "o4-mini",
                "o1", "o1-pro",
                # Legacy
                "gpt-3.5-turbo"
            ],
            "Anthropic": [
                "claude-sonnet-4-5-20250929",
                "claude-opus-4-5-20251101",
                "claude-3-5-sonnet-20240620"
            ],
            "Gemini": [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ],
        }

        # Check if model is valid
        if provider in valid_models:
            # Exact match
            if model in valid_models[provider]:
                logger.info(f"✅ Model '{model}' is valid for {provider}")
                return model
            # Partial match (e.g., "gpt-4" matches "gpt-4-turbo")
            for valid in valid_models[provider]:
                if model in valid or valid.startswith(model):
                    logger.info(f"Model '{model}' matched to valid model '{valid}'")
                    return valid

            # Unknown model - log warning but still try to use it
            # (OpenAI may have released new models)
            logger.warning(f"⚠️ Unknown model '{model}' for {provider}. Attempting to use it anyway...")
            return model

        return model

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
            model = settings.value("openai_model", "gpt-5.1")  # Default to latest stable GPT-5.1
            # Extract just the model ID (remove UI-friendly suffixes)
            if "(" in model:
                model = model.split("(")[0].strip()
            # Validate model
            model = AIProviderFactory._validate_model("OpenAI", model)
            logger.info(f"✅ OpenAI model: {model}")
            return model

        elif provider == "Anthropic":
            model = settings.value("anthropic_model", "claude-sonnet-4-5-20250929")
            # Extract just the model ID
            if "(" in model:
                model = model.split("(")[0].strip()
            # Validate model
            model = AIProviderFactory._validate_model("Anthropic", model)
            logger.info(f"✅ Anthropic model: {model}")
            return model

        elif provider == "Gemini":
            model = settings.value("gemini_model", "gemini-2.0-flash-exp")
            # Extract just the model ID
            if "(" in model:
                model = model.split("(")[0].strip()
            # Validate model
            model = AIProviderFactory._validate_model("Gemini", model)
            logger.info(f"✅ Gemini model: {model}")
            return model

        return "gpt-5.1"  # Fallback to latest stable GPT-5.1

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
        logger.info("=" * 60)
        logger.info("🚀 AIProviderFactory.create_service() CALLED")
        logger.info("=" * 60)

        # Check if AI is enabled
        is_enabled = AIProviderFactory.is_ai_enabled()
        logger.info(f"Step 1: AI enabled check = {is_enabled}")
        if not is_enabled:
            logger.error("❌ ABORT: AI features are disabled in settings")
            raise ValueError("AI features are disabled in settings")

        # Get provider
        provider = AIProviderFactory.get_provider()
        logger.info(f"Step 2: Provider = {provider}")

        # Get API key
        api_key = AIProviderFactory.get_api_key(provider)
        logger.info(f"Step 3: API key for {provider} = {'FOUND (' + api_key[:15] + '...)' if api_key else 'NOT FOUND'}")
        if not api_key:
            logger.error(f"❌ ABORT: No API key for {provider}")
            raise ValueError(f"No API key configured for {provider}. "
                             f"Set {provider.upper()}_API_KEY environment variable "
                             f"or configure in Settings -> AI tab.")

        # Get model
        model = AIProviderFactory.get_model(provider)
        logger.info(f"Step 4: Model = {model}")

        # Load AI config
        logger.info("Step 5: Creating AI config...")
        # Create default config (config_manager.get_ai_config() doesn't exist yet)
        ai_config = AIConfig(
            enabled=True,
            cost_limit_monthly=50.0,
            timeouts={"read_ms": 15000, "connect_ms": 5000}
        )
        # Ensure the selected model is reflected in the config (so UI can display it)
        ai_config.model = model
        logger.info("Step 5b: AI config created")

        # Create service based on provider
        logger.info(f"Step 6: Creating {provider} service instance...")
        if provider == "OpenAI":
            from src.ai.openai_service import OpenAIService
            logger.info(f"✅ Instantiating OpenAIService with model: {model}")
            try:
                service = OpenAIService(
                    config=ai_config,
                    api_key=api_key,
                    telemetry_callback=telemetry_callback
                )
                # Override default model if specified in settings
                service.default_model = model
                logger.info(f"✅ SUCCESS! OpenAI service created: {service}")
                return service
            except Exception as e:
                logger.error(f"❌ FAILED to create OpenAI service: {e}", exc_info=True)
                raise

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
