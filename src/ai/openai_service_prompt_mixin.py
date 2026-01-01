from __future__ import annotations

import json
import logging
import time
from typing import Any, TypeVar

import aiohttp
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.common.logging_setup import log_ai_request
from src.config.loader import AIConfig

from .openai_models import (
    AlertTriageResult,
    BacktestReview,
    OpenAIError,
    OrderAnalysis,
    QuotaExceededError,
    RateLimitError,
    SchemaValidationError,
    StrategySignalAnalysis,
    StrategyTradeAnalysis,
)
from .openai_utils import CacheManager, CostTracker

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class OpenAIServicePromptMixin:
    """OpenAIServicePromptMixin extracted from OpenAIService."""
    def _build_order_analysis_prompt(
        self,
        order_details: dict[str, Any],
        market_context: dict[str, Any]
    ) -> str:
        """Build prompt for order analysis."""
        return f"""Analyze the following trading order for risk and opportunity:

    Order Details:
    - Symbol: {order_details.get('symbol')}
    - Side: {order_details.get('side')}
    - Type: {order_details.get('order_type')}
    - Quantity: {order_details.get('quantity')}
    - Price: {order_details.get('price', 'Market')}

    Market Context:
    - Current Price: {market_context.get('current_price')}
    - Bid/Ask Spread: {market_context.get('spread')}
    - Daily Volume: {market_context.get('volume')}
    - Daily Range: {market_context.get('range')}

    Current Position (if any): {order_details.get('current_position', 'None')}

    Provide a comprehensive analysis including approval recommendation, risk assessment,
    opportunities, fee impact, and any suggested adjustments. Be specific and quantitative."""
    def _build_alert_triage_prompt(
        self,
        alert: dict[str, Any],
        portfolio_context: dict[str, Any]
    ) -> str:
        """Build prompt for alert triage."""
        return f"""Triage the following trading alert:

    Alert Information:
    - Type: {alert.get('type')}
    - Symbol: {alert.get('symbol')}
    - Condition: {alert.get('condition')}
    - Current Value: {alert.get('current_value')}
    - Threshold: {alert.get('threshold')}

    Portfolio Context:
    - Open Positions: {portfolio_context.get('positions', [])}
    - Cash Available: {portfolio_context.get('cash')}
    - Daily P&L: {portfolio_context.get('daily_pnl')}

    Assess the priority (0-1), determine if action is required, provide reasoning,
    and suggest specific actions. Consider the portfolio context and market conditions."""
    def _build_signal_analysis_prompt(
        self,
        signal: dict[str, Any],
        indicators: dict[str, Any]
    ) -> str:
        """Build prompt for signal analysis."""
        return f"""Analyze the following trading signal:

    Signal:
    - Type: {signal.get('type')}
    - Strength: {signal.get('strength')}
    - Direction: {signal.get('direction')}

    Technical Indicators:
    {json.dumps(indicators, indent=2)}

    Evaluate signal quality, identify confirming and warning signals,
    assess timing, and provide a proceed/wait recommendation."""
    def _build_strategy_trade_analysis_prompt(
        self,
        strategy_name: str,
        symbol: str,
        trades: list[dict[str, Any]],
        stats: dict[str, Any],
        strategy_params: dict[str, Any]
    ) -> str:
        """Build prompt for strategy trade analysis."""
        # Format trades for prompt (limit to prevent token overflow)
        trade_summaries = []
        for i, t in enumerate(trades[:20]):  # Max 20 trades for context
            trade_summaries.append(
                f"  Trade {i+1}: Entry ${t.get('entry_price', 0):.2f} -> "
                f"Exit ${t.get('exit_price', 0):.2f} | "
                f"{t.get('exit_reason', 'N/A')} | "
                f"P&L: {t.get('pnl_pct', 0):+.2f}%"
            )
        trades_text = "\n".join(trade_summaries)

        return f"""Analyze this trading strategy's performance and suggest improvements:

    STRATEGY: {strategy_name}
    SYMBOL: {symbol}

    CURRENT PARAMETERS:
    - Stop Loss: {strategy_params.get('stop_loss_pct', 'N/A')}%
    - Take Profit: {strategy_params.get('take_profit_pct', 'N/A')}%
    - Position Size: {strategy_params.get('position_size_pct', 'N/A')}%

    PERFORMANCE STATISTICS:
    - Total Trades: {stats.get('wins', 0) + stats.get('losses', 0)}
    - Winning Trades: {stats.get('wins', 0)}
    - Losing Trades: {stats.get('losses', 0)}
    - Win Rate: {stats.get('win_rate', 0):.1f}%
    - Average P&L per Trade: {stats.get('avg_pnl', 0):+.2f}%
    - Total P&L: {stats.get('total_pnl', 0):+.2f}%

    TRADE DETAILS:
    {trades_text}

    Please analyze:
    1. What patterns made winning trades successful?
    2. Why did losing trades fail?
    3. What parameter adjustments would improve performance?
    4. Suggest an optimized version of this strategy with specific parameters
    5. What market conditions is this strategy best/worst suited for?

    Be specific with numbers and percentages. Focus on actionable improvements."""
