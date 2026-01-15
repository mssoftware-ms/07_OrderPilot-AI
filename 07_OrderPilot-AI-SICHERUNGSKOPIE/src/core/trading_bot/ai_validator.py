"""AI Signal Validator - LLM-basierte Signal-Validierung.

Refactored from 852 LOC monolith using composition pattern.

Module 5/5 of ai_validator.py split (Main Orchestrator).

Features:
- Multi-Provider Support (OpenAI, Anthropic, Gemini)
- Hierarchische Validierung (Quick -> Deep)
- Confidence Score (0-100)
- Setup-Typ Erkennung
- Reasoning für Nachvollziehbarkeit
- Fallback zu technischer Analyse bei API-Fehlern
- Models werden aus QSettings geladen (AI Analysis Einstellungen)

Hierarchische Validierung (Option A):
1. Confluence >= 4 -> Quick AI Overview (Model aus Settings)
2. Confidence >= 70% -> Trade ausführen
3. Confidence 50-70% -> Deep Analysis (Model aus Settings)
4. Confidence < 50% -> Signal überspringen
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

# Re-export config items
from .ai_validator_config import (
    AIValidation,
    ValidationLevel,
    get_model_from_settings,
    get_provider_from_settings,
)
from .ai_validator_prompts import AIValidatorPrompts
from .ai_validator_providers import AIValidatorProviders
from .ai_validator_validation import AIValidatorValidation

if TYPE_CHECKING:
    from .signal_generator import TradeSignal
    from .trade_logger import IndicatorSnapshot, MarketContext

logger = logging.getLogger(__name__)


class AISignalValidator:
    """
    Validiert Trading-Signale mittels LLM mit hierarchischer Validierung.

    Unterstützt:
    - OpenAI (GPT-5.x, GPT-4.1)
    - Anthropic (Claude Sonnet 4.5)
    - Google (Gemini 2.0, 1.5)

    WICHTIG: Modelle werden NICHT hardcodiert!
    Sie werden aus den QSettings geladen (File -> Settings -> AI).

    Hierarchische Validierung:
    1. Quick Validation bei Confluence >= 4
    2. Confidence >= 70% -> Trade
    3. Confidence 50-70% -> Deep Analysis
    4. Confidence < 50% -> Skip
    """

    def __init__(
        self,
        enabled: bool = True,
        confidence_threshold_trade: int = 70,
        confidence_threshold_deep: int = 50,
        deep_analysis_enabled: bool = True,
        fallback_to_technical: bool = True,
        timeout_seconds: int = 30,
    ):
        """
        Args:
            enabled: AI-Validierung aktiviert
            confidence_threshold_trade: Minimum Confidence für Trade (>=70%)
            confidence_threshold_deep: Minimum Confidence für Deep Analysis (>=50%)
            deep_analysis_enabled: Deep Analysis bei unsicheren Signalen
            fallback_to_technical: Bei API-Fehler technisches Signal verwenden
            timeout_seconds: API Timeout

        HINWEIS: Provider und Model werden aus QSettings geladen!
                 Einstellbar über: File -> Settings -> AI
        """
        self.enabled = enabled
        self.confidence_threshold_trade = confidence_threshold_trade
        self.confidence_threshold_deep = confidence_threshold_deep
        self.confidence_threshold = confidence_threshold_trade  # Backwards compatibility
        self.deep_analysis_enabled = deep_analysis_enabled
        self.fallback_to_technical = fallback_to_technical
        self.timeout_seconds = timeout_seconds

        # Helper modules (composition pattern)
        self._prompts_helper = AIValidatorPrompts(parent=self)
        self._providers_helper = AIValidatorProviders(parent=self)
        self._validation_helper = AIValidatorValidation(parent=self)

        # Log current settings
        provider = self.provider
        model = self.model
        logger.info(
            f"AISignalValidator initialized (Hierarchical). "
            f"Enabled: {enabled}, Provider: {provider}, Model: {model}, "
            f"Trade >= {confidence_threshold_trade}%, Deep >= {confidence_threshold_deep}%"
        )

    @property
    def provider(self) -> str:
        """Holt den aktuellen Provider aus den QSettings."""
        return get_provider_from_settings()

    @property
    def model(self) -> str:
        """Holt das aktuelle Model aus den QSettings basierend auf Provider."""
        return get_model_from_settings(self.provider)

    async def validate_signal(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None" = None,
        market_context: "MarketContext | None" = None,
    ) -> AIValidation:
        """
        Validiert ein Trading-Signal mittels LLM (Quick Validation).

        Args:
            signal: Das zu validierende Signal
            indicators: Indikator-Snapshot
            market_context: Marktkontext

        Returns:
            AIValidation mit Confidence Score und Reasoning
        """
        return await self._validation_helper.validate_signal(signal, indicators, market_context)

    async def validate_signal_hierarchical(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None" = None,
        market_context: "MarketContext | None" = None,
        ohlcv_data: pd.DataFrame | None = None,
    ) -> AIValidation:
        """
        Hierarchische Signal-Validierung (Option A).

        Flow:
        1. Quick AI Overview (Model aus QSettings)
        2. Confidence >= 70% -> Trade genehmigt
        3. Confidence 50-70% -> Deep Analysis (Model aus QSettings)
        4. Confidence < 50% -> Signal abgelehnt

        Args:
            signal: Das zu validierende Signal
            indicators: Indikator-Snapshot
            market_context: Marktkontext
            ohlcv_data: OHLCV DataFrame für Deep Analysis

        Returns:
            AIValidation mit finaler Entscheidung
        """
        return await self._validation_helper.validate_signal_hierarchical(
            signal, indicators, market_context, ohlcv_data
        )

    def update_config(
        self,
        enabled: bool | None = None,
        confidence_threshold: int | None = None,
        confidence_threshold_trade: int | None = None,
        confidence_threshold_deep: int | None = None,
        deep_analysis_enabled: bool | None = None,
    ) -> None:
        """
        Aktualisiert Konfiguration zur Laufzeit.

        HINWEIS: Provider und Model werden aus QSettings geladen!
                 Änderungen an Provider/Model erfolgen über: File -> Settings -> AI
        """
        if enabled is not None:
            self.enabled = enabled
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
            self.confidence_threshold_trade = confidence_threshold
        if confidence_threshold_trade is not None:
            self.confidence_threshold_trade = confidence_threshold_trade
            self.confidence_threshold = confidence_threshold_trade
        if confidence_threshold_deep is not None:
            self.confidence_threshold_deep = confidence_threshold_deep
        if deep_analysis_enabled is not None:
            self.deep_analysis_enabled = deep_analysis_enabled

        # Reset clients wenn Settings geändert wurden
        self._providers_helper.reset_clients()

        logger.info(
            f"AI validator config updated: "
            f"Enabled={self.enabled}, Provider={self.provider}, Model={self.model}, "
            f"Trade>={self.confidence_threshold_trade}%, Deep>={self.confidence_threshold_deep}%"
        )


# Re-export für backward compatibility
__all__ = [
    "AISignalValidator",
    "AIValidation",
    "ValidationLevel",
    "get_model_from_settings",
    "get_provider_from_settings",
]
