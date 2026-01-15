"""Schema Validator for OrderPilot-AI Trading Application.

Refactored from prompts.py monolith.

Module 4/5 of prompts.py split.

Contains:
- SchemaValidator class for validating AI responses
"""

from typing import Any

from .prompts_schemas import JSONSchemas


class SchemaValidator:
    """Utility for validating AI responses against schemas."""

    @staticmethod
    def validate_order_analysis(response: dict[str, Any]) -> bool:
        """Validate order analysis response."""
        return SchemaValidator._validate_against_schema(
            response,
            JSONSchemas.ORDER_ANALYSIS_SCHEMA
        )

    @staticmethod
    def validate_alert_triage(response: dict[str, Any]) -> bool:
        """Validate alert triage response."""
        return SchemaValidator._validate_against_schema(
            response,
            JSONSchemas.ALERT_TRIAGE_SCHEMA
        )

    @staticmethod
    def validate_backtest_review(response: dict[str, Any]) -> bool:
        """Validate backtest review response."""
        return SchemaValidator._validate_against_schema(
            response,
            JSONSchemas.BACKTEST_REVIEW_SCHEMA
        )

    @staticmethod
    def validate_signal_analysis(response: dict[str, Any]) -> bool:
        """Validate signal analysis response."""
        return SchemaValidator._validate_against_schema(
            response,
            JSONSchemas.SIGNAL_ANALYSIS_SCHEMA
        )

    @staticmethod
    def _validate_against_schema(data: dict[str, Any], schema: dict[str, Any]) -> bool:
        """Validate data against a JSON schema."""
        from jsonschema import ValidationError, validate

        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            print(f"Schema validation failed: {e}")
            return False
