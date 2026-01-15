"""Prompt Builder for OrderPilot-AI Trading Application.

Refactored from prompts.py monolith.

Module 3/5 of prompts.py split.

Contains:
- PromptBuilder class with prompt building utilities
"""

from typing import Any

from .prompts_templates import PromptTemplates


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
