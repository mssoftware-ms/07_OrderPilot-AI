"""Prompt Library for OrderPilot-AI Trading Application.

Contains prompt templates and JSON schemas for structured AI outputs.
"""

from typing import Any

# ==================== Prompt Templates ====================

class PromptTemplates:
    """Collection of prompt templates for different AI tasks."""

    # Order Analysis Prompts
    ORDER_ANALYSIS = """As an experienced trading analyst, analyze the following order for risk and opportunity.

Order Details:
{order_details}

Market Context:
{market_context}

Portfolio Context:
{portfolio_context}

Please provide:
1. Approval recommendation with confidence level (0-1)
2. Identified risks (list specific concerns)
3. Identified opportunities (list specific advantages)
4. Fee impact analysis
5. Suggested adjustments if any

Focus on quantitative analysis and specific actionable insights."""

    # Alert Triage Prompts
    ALERT_TRIAGE = """As a trading system monitor, triage the following alert based on urgency and portfolio impact.

Alert Information:
{alert_info}

Current Portfolio:
{portfolio_state}

Market Conditions:
{market_conditions}

Assess:
1. Priority score (0-1, where 1 is most urgent)
2. Whether immediate action is required
3. Key factors driving the priority
4. Suggested actions (specific and actionable)
5. Estimated urgency level (immediate/high/medium/low)

Consider the portfolio risk exposure and current market volatility."""

    # Backtest Review Prompts
    BACKTEST_REVIEW = """As a quantitative trading strategist, review the following backtest results.

Strategy: {strategy_name}
Test Period: {test_period}
Market Conditions: {market_conditions}

Performance Metrics:
{performance_metrics}

Trade Statistics:
{trade_statistics}

Provide:
1. Overall assessment and performance rating (0-10)
2. Key strengths of the strategy
3. Main weaknesses identified
4. Specific improvement suggestions
5. Parameter optimization recommendations
6. Risk assessment
7. Analysis of maximum drawdown periods

Focus on actionable improvements and realistic expectations."""

    # Signal Analysis Prompts
    SIGNAL_ANALYSIS = """As a technical analyst, evaluate the following trading signal.

Signal Information:
{signal_info}

Technical Indicators:
{indicators}

Recent Price Action:
{price_action}

Market Context:
{market_context}

Analyze:
1. Signal quality (0-1)
2. Whether to proceed with the trade
3. Technical analysis summary
4. Current market conditions assessment
5. Warning signals present
6. Confirming signals present
7. Timing assessment (excellent/good/neutral/poor)
8. Suggested delay if timing is suboptimal

Provide objective technical analysis without emotional bias."""

    # Risk Assessment Prompts
    RISK_ASSESSMENT = """Assess the risk profile of the following trading position.

Position Details:
{position_details}

Account Status:
{account_status}

Market Volatility:
{volatility_metrics}

Historical Performance:
{historical_data}

Evaluate:
1. Position risk score (0-1)
2. Portfolio impact if stop loss triggered
3. Correlation with existing positions
4. Volatility-adjusted position sizing recommendation
5. Suggested risk mitigation measures

Use quantitative risk metrics and consider portfolio diversification."""


# ==================== JSON Schemas ====================

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


# ==================== Prompt Builder ====================

class PromptBuilder:
    """Utility class for building prompts with context."""

    @staticmethod
    def build_order_prompt(
        order_details: dict[str, Any],
        market_context: dict[str, Any],
        portfolio_context: dict[str, Any]
    ) -> str:
        """Build order analysis prompt with context."""
        order_str = PromptBuilder._format_dict(order_details)
        market_str = PromptBuilder._format_dict(market_context)
        portfolio_str = PromptBuilder._format_dict(portfolio_context)

        return PromptTemplates.ORDER_ANALYSIS.format(
            order_details=order_str,
            market_context=market_str,
            portfolio_context=portfolio_str
        )

    @staticmethod
    def build_alert_prompt(
        alert_info: dict[str, Any],
        portfolio_state: dict[str, Any],
        market_conditions: dict[str, Any]
    ) -> str:
        """Build alert triage prompt with context."""
        return PromptTemplates.ALERT_TRIAGE.format(
            alert_info=PromptBuilder._format_dict(alert_info),
            portfolio_state=PromptBuilder._format_dict(portfolio_state),
            market_conditions=PromptBuilder._format_dict(market_conditions)
        )

    @staticmethod
    def build_backtest_prompt(
        strategy_name: str,
        test_period: str,
        market_conditions: str,
        performance_metrics: dict[str, Any],
        trade_statistics: dict[str, Any]
    ) -> str:
        """Build backtest review prompt with context."""
        return PromptTemplates.BACKTEST_REVIEW.format(
            strategy_name=strategy_name,
            test_period=test_period,
            market_conditions=market_conditions,
            performance_metrics=PromptBuilder._format_dict(performance_metrics),
            trade_statistics=PromptBuilder._format_dict(trade_statistics)
        )

    @staticmethod
    def build_signal_prompt(
        signal_info: dict[str, Any],
        indicators: dict[str, Any],
        price_action: dict[str, Any],
        market_context: dict[str, Any]
    ) -> str:
        """Build signal analysis prompt with context."""
        return PromptTemplates.SIGNAL_ANALYSIS.format(
            signal_info=PromptBuilder._format_dict(signal_info),
            indicators=PromptBuilder._format_dict(indicators),
            price_action=PromptBuilder._format_dict(price_action),
            market_context=PromptBuilder._format_dict(market_context)
        )

    @staticmethod
    def _format_dict(data: dict[str, Any], indent: int = 0) -> str:
        """Format dictionary for prompt inclusion."""
        if not data:
            return "No data available"

        lines = []
        indent_str = "  " * indent

        for key, value in data.items():
            # Convert key to readable format
            readable_key = key.replace("_", " ").title()

            if isinstance(value, dict):
                lines.append(f"{indent_str}- {readable_key}:")
                lines.append(PromptBuilder._format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}- {readable_key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"{indent_str}- {readable_key}: {value}")

        return "\n".join(lines)


# ==================== Schema Validator ====================

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


# ==================== Prompt Versioning ====================

class PromptVersion:
    """Manages prompt versions for A/B testing and improvements."""

    VERSIONS = {
        "order_analysis": {
            "v1.0": PromptTemplates.ORDER_ANALYSIS,
            "current": "v1.0"
        },
        "alert_triage": {
            "v1.0": PromptTemplates.ALERT_TRIAGE,
            "current": "v1.0"
        },
        "backtest_review": {
            "v1.0": PromptTemplates.BACKTEST_REVIEW,
            "current": "v1.0"
        },
        "signal_analysis": {
            "v1.0": PromptTemplates.SIGNAL_ANALYSIS,
            "current": "v1.0"
        }
    }

    @classmethod
    def get_prompt(cls, prompt_type: str, version: str = None) -> str:
        """Get a specific version of a prompt."""
        if prompt_type not in cls.VERSIONS:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        prompt_versions = cls.VERSIONS[prompt_type]
        version = version or prompt_versions["current"]

        if version not in prompt_versions:
            raise ValueError(f"Unknown version {version} for {prompt_type}")

        return prompt_versions[version]