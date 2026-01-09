"""AI Validator Validation - Validierungs-Flows (Quick, Hierarchical, Deep).

Refactored from 852 LOC monolith using composition pattern.

Module 4/5 of ai_validator.py split.

Contains:
- validate_signal(): Quick Validation Flow
- validate_signal_hierarchical(): Hierarchische Validierung (Quick -> Deep)
- _run_deep_analysis(): Deep Analysis Execution
- _parse_response(): Parse LLM JSON Response
- _create_bypass_validation(): Bypass-Validation
- _create_fallback_validation(): Fallback-Validation
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import pandas as pd

from .ai_validator_config import AIValidation, ValidationLevel

if TYPE_CHECKING:
    from .signal_generator import TradeSignal
    from .trade_logger import IndicatorSnapshot, MarketContext

logger = logging.getLogger(__name__)


class AIValidatorValidation:
    """Validierungs-Flows für AI Signal Validator."""

    def __init__(self, parent):
        """
        Args:
            parent: AISignalValidator Instanz
        """
        self.parent = parent

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
        if not self.parent.enabled:
            return self.create_bypass_validation("AI validation disabled")

        try:
            # Prompt erstellen
            prompt = self.parent._prompts_helper.build_prompt(signal, indicators, market_context)

            # LLM aufrufen
            response = await self.parent._providers_helper.call_llm(prompt)

            # Response parsen
            validation = self.parse_response(response)

            logger.info(
                f"AI validation complete: "
                f"Approved={validation.approved}, "
                f"Confidence={validation.confidence_score}%, "
                f"Setup={validation.setup_type}"
            )

            return validation

        except Exception as e:
            logger.error(f"AI validation failed: {e}")

            if self.parent.fallback_to_technical:
                logger.info("Falling back to technical signal (AI error)")
                return self.create_fallback_validation(str(e))
            else:
                return AIValidation(
                    approved=False,
                    confidence_score=0,
                    setup_type=None,
                    reasoning="AI validation failed",
                    provider=self.parent.provider,
                    model=self.parent.model,
                    timestamp=datetime.now(timezone.utc),
                    error=str(e),
                )

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
        if not self.parent.enabled:
            return self.create_bypass_validation("AI validation disabled")

        # Step 1: Quick Validation
        logger.info(
            f"[Hierarchical] Step 1: Quick validation for {signal.direction.value} "
            f"(Confluence: {signal.confluence_score})"
        )

        quick_result = await self.validate_signal(signal, indicators, market_context)
        quick_result.validation_level = ValidationLevel.QUICK

        # Step 2: Evaluate Quick Result
        if quick_result.confidence_score >= self.parent.confidence_threshold_trade:
            # High confidence -> Trade
            logger.info(
                f"[Hierarchical] Quick confidence {quick_result.confidence_score}% "
                f">= {self.parent.confidence_threshold_trade}% -> TRADE APPROVED"
            )
            quick_result.approved = True
            return quick_result

        elif quick_result.confidence_score >= self.parent.confidence_threshold_deep:
            # Medium confidence -> Deep Analysis
            if not self.parent.deep_analysis_enabled:
                logger.info(
                    f"[Hierarchical] Confidence {quick_result.confidence_score}% in range "
                    f"[{self.parent.confidence_threshold_deep}-{self.parent.confidence_threshold_trade}], "
                    f"but Deep Analysis disabled -> Using quick result"
                )
                quick_result.approved = quick_result.confidence_score >= self.parent.confidence_threshold_trade
                return quick_result

            logger.info(
                f"[Hierarchical] Step 2: Deep Analysis triggered "
                f"(Confidence {quick_result.confidence_score}% in range "
                f"[{self.parent.confidence_threshold_deep}-{self.parent.confidence_threshold_trade}])"
            )

            # Deep Analysis durchführen
            deep_result = await self.run_deep_analysis(
                signal, indicators, market_context, ohlcv_data
            )
            deep_result.deep_analysis_triggered = True
            deep_result.validation_level = ValidationLevel.DEEP

            # Deep Result entscheidet
            if deep_result.confidence_score >= self.parent.confidence_threshold_trade:
                logger.info(
                    f"[Hierarchical] Deep confidence {deep_result.confidence_score}% "
                    f">= {self.parent.confidence_threshold_trade}% -> TRADE APPROVED"
                )
                deep_result.approved = True
            else:
                logger.info(
                    f"[Hierarchical] Deep confidence {deep_result.confidence_score}% "
                    f"< {self.parent.confidence_threshold_trade}% -> TRADE REJECTED"
                )
                deep_result.approved = False

            return deep_result

        else:
            # Low confidence -> Skip
            logger.info(
                f"[Hierarchical] Quick confidence {quick_result.confidence_score}% "
                f"< {self.parent.confidence_threshold_deep}% -> SIGNAL SKIPPED"
            )
            quick_result.approved = False
            quick_result.reasoning = (
                f"Signal skipped: Confidence {quick_result.confidence_score}% "
                f"below threshold {self.parent.confidence_threshold_deep}%. "
                f"Original: {quick_result.reasoning}"
            )
            return quick_result

    async def run_deep_analysis(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None",
        market_context: "MarketContext | None",
        ohlcv_data: pd.DataFrame | None,
    ) -> AIValidation:
        """
        Führt Deep Analysis durch.

        Verwendet einen ausführlicheren Prompt mit mehr Kontext.
        Das Model wird aus den QSettings geholt.
        """
        # Model aus Settings holen (gleiche wie Quick, Settings entscheiden)
        current_model = self.parent.model
        current_provider = self.parent.provider

        try:
            # Detaillierterer Prompt für Deep Analysis
            prompt = self.parent._prompts_helper.build_deep_prompt(signal, indicators, market_context, ohlcv_data)

            response = await self.parent._providers_helper.call_llm(prompt)
            validation = self.parse_response(response)
            validation.model = current_model

            logger.info(
                f"[Deep Analysis] Complete: Confidence={validation.confidence_score}%, "
                f"Setup={validation.setup_type}, Model={current_model}"
            )

            return validation

        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            # Fallback: Signal abgelehnt
            return AIValidation(
                approved=False,
                confidence_score=40,
                setup_type=None,
                reasoning=f"Deep analysis failed: {e}. Signal rejected for safety.",
                provider=current_provider,
                model=current_model,
                timestamp=datetime.now(timezone.utc),
                validation_level=ValidationLevel.DEEP,
                error=str(e),
            )

    def parse_response(self, response: dict[str, Any]) -> AIValidation:
        """Parst die LLM-Antwort."""
        confidence = int(response.get("confidence_score", 0))
        approved = response.get("approved", False)

        # Wenn approved nicht explizit gesetzt, basierend auf Threshold entscheiden
        if "approved" not in response:
            approved = confidence >= self.parent.confidence_threshold

        setup_type = response.get("setup_type", "UNKNOWN")
        if setup_type not in self.parent._prompts_helper.SETUP_TYPES:
            setup_type = "NO_SETUP"

        reasoning = response.get("reasoning", "No reasoning provided")

        return AIValidation(
            approved=approved,
            confidence_score=confidence,
            setup_type=setup_type,
            reasoning=reasoning,
            provider=self.parent.provider,
            model=self.parent.model,
            timestamp=datetime.now(timezone.utc),
        )

    def create_bypass_validation(self, reason: str) -> AIValidation:
        """Erstellt Bypass-Validation (AI deaktiviert)."""
        return AIValidation(
            approved=True,
            confidence_score=100,
            setup_type=None,
            reasoning=reason,
            provider="bypass",
            model="none",
            timestamp=datetime.now(timezone.utc),
            validation_level=ValidationLevel.BYPASS,
        )

    def create_fallback_validation(self, error: str) -> AIValidation:
        """Erstellt Fallback-Validation (API-Fehler, aber Technical OK)."""
        return AIValidation(
            approved=True,
            confidence_score=50,  # Neutral confidence
            setup_type=None,
            reasoning=f"Fallback to technical signal due to AI error: {error}",
            provider="fallback",
            model="technical",
            timestamp=datetime.now(timezone.utc),
            validation_level=ValidationLevel.TECHNICAL,
            error=error,
        )
