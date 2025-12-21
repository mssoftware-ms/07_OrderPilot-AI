"""OpenAI Service for OrderPilot-AI Trading Application.

Implements OpenAI API integration with Structured Outputs,
Assistants API (optional), and Realtime API (stub).

REFACTORED: Split into multiple files to meet 600 LOC limit.
- openai_models.py: Exception classes and response models
- openai_utils.py: CostTracker and CacheManager
- openai_service.py: Main service class (this file)
"""

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

# Re-export models for backward compatibility
__all__ = [
    "OpenAIError",
    "RateLimitError",
    "QuotaExceededError",
    "SchemaValidationError",
    "OrderAnalysis",
    "AlertTriageResult",
    "BacktestReview",
    "StrategySignalAnalysis",
    "StrategyTradeAnalysis",
    "CostTracker",
    "CacheManager",
    "OpenAIService",
    "get_openai_service",
]

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class OpenAIService:
    """Main OpenAI service for structured outputs."""

    def __init__(
        self,
        config: AIConfig,
        api_key: str,
        telemetry_callback: callable | None = None
    ):
        """Initialize OpenAI service.

        Args:
            config: AI configuration
            api_key: OpenAI API key
            telemetry_callback: Optional callback for telemetry
        """
        self.config = config
        self.api_key = api_key
        self.telemetry_callback = telemetry_callback

        # Initialize components
        self.cost_tracker = CostTracker(
            monthly_budget=config.cost_limit_monthly,
            warn_threshold=config.cost_limit_monthly * 0.8  # Warn at 80%
        )
        self.cache_manager = CacheManager(
            ttl_seconds=config.cache_ttl if hasattr(config, 'cache_ttl') else 3600
        )

        # API settings
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Session for connection pooling
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize the service."""
        if not self._session:
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeouts.get("read_ms", 15000) / 1000,
                connect=self.config.timeouts.get("connect_ms", 5000) / 1000
            )
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )

    async def close(self) -> None:
        """Close the service."""
        if self._session:
            await self._session.close()
            self._session = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, RateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def structured_completion(
        self,
        prompt: str,
        response_model: type[T],
        model: str | None = None,
        temperature: float = 0.2,
        use_cache: bool = True,
        context: dict[str, Any] | None = None
    ) -> T:
        """Get structured completion from OpenAI.

        Args:
            prompt: The prompt
            response_model: Pydantic model for response structure
            model: Model to use (defaults to config)
            temperature: Temperature for generation
            use_cache: Whether to use caching
            context: Additional context for telemetry

        Returns:
            Parsed response as Pydantic model instance

        Raises:
            Various OpenAI errors
        """
        model = model or self.config.model
        schema = response_model.model_json_schema()

        # Check cache
        if use_cache:
            cached = await self.cache_manager.get(prompt, model, schema)
            if cached:
                return response_model(**cached)

        # Ensure session is initialized
        if not self._session:
            await self.initialize()

        # Prepare request
        request_data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": schema
                }
            }
        }

        start_time = time.monotonic()

        try:
            # Make API request
            async with self._session.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            ) as response:
                response_data = await response.json()

                # Handle errors
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    raise OpenAIError(f"API error ({response.status}): {error_msg}")

                # Extract content
                content = response_data["choices"][0]["message"]["content"]

                # Check for refusal
                if refusal := response_data["choices"][0]["message"].get("refusal"):
                    logger.warning(f"Request refused: {refusal}")
                    raise OpenAIError(f"Request refused: {refusal}")

                # Parse JSON response
                parsed_content = json.loads(content)

                # Validate against schema
                try:
                    validate(instance=parsed_content, schema=schema)
                except JsonSchemaValidationError as e:
                    raise SchemaValidationError(f"Response validation failed: {e}")

                # Track usage and costs
                usage = response_data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

                cost = await self.cost_tracker.track_usage(
                    model, input_tokens, output_tokens
                )

                # Log telemetry
                latency_ms = int((time.monotonic() - start_time) * 1000)

                log_ai_request(
                    model=model,
                    tokens=input_tokens + output_tokens,
                    cost=cost,
                    latency=latency_ms / 1000,
                    prompt_version="1.0",
                    request_type=response_model.__name__,
                    details=context
                )

                if self.telemetry_callback:
                    self.telemetry_callback(
                        tokens=input_tokens + output_tokens,
                        cost=cost,
                        latency_ms=latency_ms,
                        feature="structured_completion"
                    )

                # Cache response
                if use_cache:
                    await self.cache_manager.set(prompt, model, schema, parsed_content)

                # Return parsed model
                return response_model(**parsed_content)

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def analyze_order(
        self,
        order_details: dict[str, Any],
        market_context: dict[str, Any]
    ) -> OrderAnalysis:
        """Analyze an order before placement."""
        prompt = self._build_order_analysis_prompt(order_details, market_context)

        return await self.structured_completion(
            prompt=prompt,
            response_model=OrderAnalysis,
            model=self.config.model_critical,
            context={"type": "order_analysis", **order_details}
        )

    async def triage_alert(
        self,
        alert: dict[str, Any],
        portfolio_context: dict[str, Any]
    ) -> AlertTriageResult:
        """Triage an alert for priority and action."""
        prompt = self._build_alert_triage_prompt(alert, portfolio_context)

        return await self.structured_completion(
            prompt=prompt,
            response_model=AlertTriageResult,
            model=self.config.model,
            context={"type": "alert_triage", "alert_type": alert.get("type")}
        )

    async def review_backtest(
        self,
        result: "BacktestResult"
    ) -> BacktestReview:
        """Review backtest results with AI analysis."""
        from src.ai.prompts import PromptBuilder

        # Extract strategy info
        strategy_name = result.strategy_name or "Unnamed Strategy"
        test_period = f"{result.start.strftime('%Y-%m-%d')} to {result.end.strftime('%Y-%m-%d')}"
        market_conditions = f"{result.duration_days:.1f} days, {result.symbol} on {result.timeframe} timeframe"

        # Build performance metrics dict
        performance_metrics = {
            "total_return": f"{result.metrics.total_return_pct:.2f}%",
            "sharpe_ratio": f"{result.metrics.sharpe_ratio:.2f}" if result.metrics.sharpe_ratio else "N/A",
            "sortino_ratio": f"{result.metrics.sortino_ratio:.2f}" if result.metrics.sortino_ratio else "N/A",
            "max_drawdown": f"{result.metrics.max_drawdown_pct:.2f}%",
            "annual_return": f"{result.metrics.annual_return_pct:.2f}%" if result.metrics.annual_return_pct else "N/A",
            "profit_factor": f"{result.metrics.profit_factor:.2f}",
            "recovery_factor": f"{result.metrics.recovery_factor:.2f}" if result.metrics.recovery_factor else "N/A",
            "initial_capital": f"${result.initial_capital:,.2f}",
            "final_capital": f"${result.final_capital:,.2f}",
            "total_pnl": f"${result.total_pnl:,.2f}"
        }

        # Build trade statistics dict
        trade_statistics = {
            "total_trades": result.metrics.total_trades,
            "winning_trades": result.metrics.winning_trades,
            "losing_trades": result.metrics.losing_trades,
            "win_rate": f"{result.metrics.win_rate * 100:.1f}%",
            "avg_win": f"${result.metrics.avg_win:,.2f}",
            "avg_loss": f"${result.metrics.avg_loss:,.2f}",
            "largest_win": f"${result.metrics.largest_win:,.2f}",
            "largest_loss": f"${result.metrics.largest_loss:,.2f}",
            "avg_r_multiple": f"{result.metrics.avg_r_multiple:.2f}" if result.metrics.avg_r_multiple else "N/A",
            "avg_trade_duration": f"{result.metrics.avg_trade_duration_minutes:.1f} minutes" if result.metrics.avg_trade_duration_minutes else "N/A",
            "max_consecutive_wins": result.metrics.max_consecutive_wins,
            "max_consecutive_losses": result.metrics.max_consecutive_losses,
            "expectancy": f"${result.metrics.expectancy:.2f}" if result.metrics.expectancy else "N/A"
        }

        # Build prompt using PromptBuilder
        prompt = PromptBuilder.build_backtest_prompt(
            strategy_name=strategy_name,
            test_period=test_period,
            market_conditions=market_conditions,
            performance_metrics=performance_metrics,
            trade_statistics=trade_statistics
        )

        return await self.structured_completion(
            prompt=prompt,
            response_model=BacktestReview,
            model=self.config.model,
            context={
                "type": "backtest_review",
                "strategy": strategy_name,
                "symbol": result.symbol,
                "total_return": result.metrics.total_return_pct
            }
        )

    async def analyze_signal(
        self,
        signal: dict[str, Any],
        indicators: dict[str, Any]
    ) -> StrategySignalAnalysis:
        """Analyze a strategy signal."""
        prompt = self._build_signal_analysis_prompt(signal, indicators)

        return await self.structured_completion(
            prompt=prompt,
            response_model=StrategySignalAnalysis,
            model=self.config.model,
            context={"type": "signal_analysis", "signal_type": signal.get("type")}
        )

    async def analyze_strategy_trades(
        self,
        strategy_name: str,
        symbol: str,
        trades: list[dict[str, Any]],
        stats: dict[str, Any],
        strategy_params: dict[str, Any]
    ) -> StrategyTradeAnalysis:
        """Analyze strategy trades and provide improvement suggestions."""
        prompt = self._build_strategy_trade_analysis_prompt(
            strategy_name, symbol, trades, stats, strategy_params
        )

        return await self.structured_completion(
            prompt=prompt,
            response_model=StrategyTradeAnalysis,
            model=self.config.model,
            context={
                "type": "strategy_trade_analysis",
                "strategy": strategy_name,
                "symbol": symbol,
                "total_trades": len(trades)
            }
        )

    # ==================== Prompt Builders ====================

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


# ==================== Singleton Instance ====================

_service_instance: OpenAIService | None = None


async def get_openai_service(
    config: AIConfig,
    api_key: str
) -> OpenAIService:
    """Get or create OpenAI service instance.

    Args:
        config: AI configuration
        api_key: OpenAI API key

    Returns:
        OpenAI service instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = OpenAIService(config, api_key)
        await _service_instance.initialize()

    return _service_instance
