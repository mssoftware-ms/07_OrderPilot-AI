"""JSON Schemas for OrderPilot-AI Trading Application.

Refactored from prompts.py monolith.

Module 2/5 of prompts.py split.

Contains:
- JSONSchemas class with all schema dictionaries
"""


class JSONSchemas:
    """JSON schemas for structured outputs."""

    ORDER_ANALYSIS_SCHEMA = {
        "type": "object",
        "title": "OrderAnalysisSchema",
        "required": [
            "approved",
            "confidence",
            "reasoning",
            "risks",
            "opportunities",
            "fee_impact",
            "estimated_total_cost"
        ],
        "properties": {
            "approved": {
                "type": "boolean",
                "description": "Whether the order should be approved"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence level in the recommendation"
            },
            "reasoning": {
                "type": "string",
                "minLength": 10,
                "description": "Detailed reasoning for the recommendation"
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of identified risks"
            },
            "opportunities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of identified opportunities"
            },
            "suggested_adjustments": {
                "type": "object",
                "properties": {
                    "price": {"type": "number"},
                    "quantity": {"type": "number"},
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"}
                },
                "description": "Suggested order adjustments"
            },
            "fee_impact": {
                "type": "string",
                "description": "Analysis of fee impact on returns"
            },
            "estimated_total_cost": {
                "type": "number",
                "minimum": 0,
                "description": "Total estimated cost including fees"
            }
        }
    }

    ALERT_TRIAGE_SCHEMA = {
        "type": "object",
        "title": "AlertTriageSchema",
        "required": [
            "priority_score",
            "action_required",
            "reasoning",
            "key_factors",
            "suggested_actions",
            "estimated_urgency"
        ],
        "properties": {
            "priority_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Priority score from 0 (low) to 1 (critical)"
            },
            "action_required": {
                "type": "boolean",
                "description": "Whether immediate action is required"
            },
            "reasoning": {
                "type": "string",
                "minLength": 10,
                "description": "Reasoning for the triage decision"
            },
            "key_factors": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Key factors driving the priority"
            },
            "suggested_actions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Suggested actions to take"
            },
            "estimated_urgency": {
                "type": "string",
                "enum": ["immediate", "high", "medium", "low"],
                "description": "Urgency level classification"
            },
            "related_positions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Related position symbols"
            },
            "market_context": {
                "type": "object",
                "description": "Additional market context"
            }
        }
    }

    BACKTEST_REVIEW_SCHEMA = {
        "type": "object",
        "title": "BacktestReviewSchema",
        "required": [
            "overall_assessment",
            "performance_rating",
            "strengths",
            "weaknesses",
            "suggested_improvements",
            "risk_assessment",
            "max_drawdown_analysis"
        ],
        "properties": {
            "overall_assessment": {
                "type": "string",
                "minLength": 20,
                "description": "Overall assessment of the backtest"
            },
            "performance_rating": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 10.0,
                "description": "Performance rating out of 10"
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Strategy strengths"
            },
            "weaknesses": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Strategy weaknesses"
            },
            "suggested_improvements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "improvement": {"type": "string"},
                        "expected_impact": {"type": "string"},
                        "implementation_difficulty": {
                            "type": "string",
                            "enum": ["easy", "medium", "hard"]
                        }
                    }
                },
                "description": "Suggested improvements with details"
            },
            "parameter_recommendations": {
                "type": "object",
                "description": "Recommended parameter adjustments"
            },
            "risk_assessment": {
                "type": "string",
                "minLength": 10,
                "description": "Risk assessment of the strategy"
            },
            "max_drawdown_analysis": {
                "type": "string",
                "minLength": 10,
                "description": "Analysis of maximum drawdown periods"
            },
            "market_conditions_analysis": {
                "type": "string",
                "description": "How strategy performs in different market conditions"
            },
            "adaptability_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "How well strategy adapts to market changes"
            }
        }
    }

    SIGNAL_ANALYSIS_SCHEMA = {
        "type": "object",
        "title": "SignalAnalysisSchema",
        "required": [
            "signal_quality",
            "proceed",
            "technical_analysis",
            "market_conditions",
            "warning_signals",
            "confirming_signals",
            "timing_assessment"
        ],
        "properties": {
            "signal_quality": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Quality score of the signal"
            },
            "proceed": {
                "type": "boolean",
                "description": "Whether to proceed with the trade"
            },
            "technical_analysis": {
                "type": "string",
                "minLength": 10,
                "description": "Technical analysis summary"
            },
            "market_conditions": {
                "type": "string",
                "minLength": 10,
                "description": "Current market conditions assessment"
            },
            "warning_signals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Contradictory or warning signals"
            },
            "confirming_signals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Confirming signals supporting the trade"
            },
            "timing_assessment": {
                "type": "string",
                "enum": ["excellent", "good", "neutral", "poor"],
                "description": "Assessment of entry timing"
            },
            "suggested_delay_minutes": {
                "type": ["integer", "null"],
                "minimum": 0,
                "description": "Suggested delay in minutes if timing is poor"
            }
        }
    }
