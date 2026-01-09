"""AI Validator Config - Settings, Enums und Dataclasses.

Refactored from 852 LOC monolith using composition pattern.

Module 1/5 of ai_validator.py split.

Contains:
- get_model_from_settings(): Model aus QSettings laden
- get_provider_from_settings(): Provider aus QSettings laden
- ValidationLevel: Enum für Validierungsstufen
- AIValidation: Dataclass für Validierungsergebnisse
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


def get_model_from_settings(provider: str) -> str:
    """
    Holt das konfigurierte Model aus den QSettings basierend auf Provider.

    Die Models werden in der AI Analysis UI konfiguriert und entsprechen
    den in src/ai/model_constants.py definierten Modellen:
    - OpenAI: gpt-5.2, gpt-5.1, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
    - Anthropic: claude-sonnet-4-5-20250929, claude-sonnet-4-5
    - Gemini: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash

    Args:
        provider: "openai", "anthropic", oder "gemini"

    Returns:
        Model ID (z.B. "gpt-4.1-mini", "claude-sonnet-4-5")
    """
    try:
        from PyQt6.QtCore import QSettings
        settings = QSettings("OrderPilot", "OrderPilot-AI")

        # Settings Keys pro Provider
        model_keys = {
            "openai": "openai_model",
            "anthropic": "anthropic_model",
            "gemini": "gemini_model",
        }

        # Defaults müssen mit model_constants.py übereinstimmen!
        # KEINE hardcodierten alten Modelle wie gpt-4o!
        defaults = {
            "openai": "gpt-4.1-mini",      # Schnell und günstig
            "anthropic": "claude-sonnet-4-5",  # Aktuelles Modell
            "gemini": "gemini-1.5-flash",  # Schnelles Modell
        }

        provider_lower = provider.lower()
        key = model_keys.get(provider_lower, "openai_model")
        default = defaults.get(provider_lower, "gpt-4.1-mini")

        # Settings Wert holen (Format: "gpt-5.1 (GPT-5.1 Full)" oder "claude-sonnet-4-5 (Latest)")
        model_display = settings.value(key, default)

        if model_display:
            # Extract model ID from display name (before space or parenthesis)
            model_id = model_display.split(" ")[0].split("(")[0].strip()
            if model_id:
                logger.debug(f"Model from settings for {provider}: {model_id}")
                return model_id

        logger.debug(f"Using default model for {provider}: {default}")
        return default

    except Exception as e:
        logger.warning(f"Could not load model from settings: {e}, using default")
        # Fallback defaults
        defaults = {
            "openai": "gpt-4.1-mini",
            "anthropic": "claude-sonnet-4-5",
            "gemini": "gemini-1.5-flash",
        }
        return defaults.get(provider.lower(), "gpt-4.1-mini")


def get_provider_from_settings() -> str:
    """
    Holt den konfigurierten AI Provider aus den QSettings.

    Returns:
        Provider name ("openai", "anthropic", "gemini")
    """
    try:
        from PyQt6.QtCore import QSettings
        settings = QSettings("OrderPilot", "OrderPilot-AI")
        provider = settings.value("ai_provider", "OpenAI")
        # Normalize to lowercase
        return provider.lower() if provider else "openai"
    except Exception as e:
        logger.warning(f"Could not load provider from settings: {e}, using openai")
        return "openai"


class ValidationLevel(str, Enum):
    """Validierungsstufe."""
    QUICK = "quick"      # Schnelle Validierung (Model aus Settings)
    DEEP = "deep"        # Tiefe Analyse (Model aus Settings)
    TECHNICAL = "technical"  # Nur technisch (keine AI)
    BYPASS = "bypass"    # Übersprungen


@dataclass
class AIValidation:
    """Ergebnis der AI-Validierung."""

    approved: bool
    confidence_score: int  # 0-100
    setup_type: str | None  # z.B. "PULLBACK_EMA20", "BREAKOUT", "MEAN_REVERSION"
    reasoning: str
    provider: str
    model: str
    timestamp: datetime
    validation_level: ValidationLevel = ValidationLevel.QUICK
    deep_analysis_triggered: bool = False
    error: str | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "approved": self.approved,
            "confidence_score": self.confidence_score,
            "setup_type": self.setup_type,
            "reasoning": self.reasoning,
            "provider": self.provider,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "validation_level": self.validation_level.value,
            "deep_analysis_triggered": self.deep_analysis_triggered,
            "error": self.error,
        }
