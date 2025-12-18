"""LLM Response Validator for Tradingbot.

Validates LLM responses against expected schema.
"""

from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from .models import BotAction, FeatureVector, LLMBotResponse

logger = logging.getLogger(__name__)


class LLMResponseValidator:
    """Validates LLM responses against expected schema.

    Provides strict validation with repair attempts and
    fallback to rule-based defaults.
    """

    @staticmethod
    def validate_trade_decision(
        response: dict | str,
        allow_repair: bool = True
    ) -> tuple[LLMBotResponse | None, list[str]]:
        """Validate trade decision response.

        Args:
            response: Raw response dict or JSON string
            allow_repair: Attempt to repair invalid responses

        Returns:
            (Validated response or None, list of validation errors)
        """
        errors = []

        # Parse if string
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as e:
                errors.append(f"JSON parse error: {e}")
                return None, errors

        if not isinstance(response, dict):
            errors.append(f"Expected dict, got {type(response)}")
            return None, errors

        # Attempt Pydantic validation
        try:
            validated = LLMBotResponse(**response)
            return validated, []
        except ValidationError as e:
            for err in e.errors():
                errors.append(f"{err['loc']}: {err['msg']}")

        # Attempt repair if allowed
        if allow_repair and errors:
            repaired = LLMResponseValidator._attempt_repair(response)
            if repaired:
                try:
                    validated = LLMBotResponse(**repaired)
                    errors.append("REPAIRED: Response was auto-corrected")
                    return validated, errors
                except ValidationError:
                    pass

        return None, errors

    @staticmethod
    def _attempt_repair(response: dict) -> dict | None:
        """Attempt to repair an invalid response.

        Args:
            response: Invalid response dict

        Returns:
            Repaired dict or None
        """
        repaired = response.copy()

        # Fix action if invalid
        action = repaired.get("action", "").upper()
        valid_actions = {"HOLD", "EXIT", "ADJUST_STOP", "ENTRY", "SKIP"}
        if action not in valid_actions:
            repaired["action"] = "HOLD"

        # Fix confidence range
        confidence = repaired.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        repaired["confidence"] = max(0.0, min(1.0, float(confidence)))

        # Fix reason_codes
        reason_codes = repaired.get("reason_codes", [])
        if not isinstance(reason_codes, list):
            reason_codes = []
        repaired["reason_codes"] = reason_codes[:3]

        return repaired

    @staticmethod
    def get_fallback_response(
        state: str,
        features: FeatureVector | None = None
    ) -> LLMBotResponse:
        """Get rule-based fallback response.

        Args:
            state: Current bot state
            features: Optional features for context

        Returns:
            Safe fallback response
        """
        # Default to HOLD with low confidence
        return LLMBotResponse(
            action=BotAction.HOLD,
            confidence=0.3,
            reason_codes=["LLM_FALLBACK", "RULE_BASED"],
            side=None,
            stop_adjustment=None
        )
