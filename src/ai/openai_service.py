"""OpenAI Service for OrderPilot-AI Trading Application.

Implements OpenAI API integration with Structured Outputs,
Assistants API (optional), and Realtime API (stub).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, TypeVar

import aiohttp
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate
from pydantic import BaseModel, Field
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.common.logging_setup import log_ai_request
from src.config.loader import AIConfig

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


# ==================== Exception Classes ====================

class OpenAIError(Exception):
    """Base exception for OpenAI service errors."""
    pass


class RateLimitError(OpenAIError):
    """Raised when rate limit is exceeded."""
    pass


class QuotaExceededError(OpenAIError):
    """Raised when monthly budget is exceeded."""
    pass


class SchemaValidationError(OpenAIError):
    """Raised when response doesn't match schema."""
    pass


# ==================== Response Models ====================

class OrderAnalysis(BaseModel):
    """Structured output for order analysis."""
    approved: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

    # Risk assessment
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)

    # Suggestions
    suggested_adjustments: dict[str, Any] = Field(default_factory=dict)

    # Fees and costs
    fee_impact: str
    estimated_total_cost: float

    # Metadata
    analysis_version: str = "1.0"


class AlertTriageResult(BaseModel):
    """Structured output for alert triage."""
    priority_score: float = Field(ge=0.0, le=1.0)
    action_required: bool

    # Reasoning
    reasoning: str
    key_factors: list[str]

    # Suggested actions
    suggested_actions: list[str]
    estimated_urgency: str  # immediate, high, medium, low

    # Context
    related_positions: list[str] = Field(default_factory=list)
    market_context: dict[str, Any] = Field(default_factory=dict)


class BacktestReview(BaseModel):
    """Structured output for backtest review."""
    overall_assessment: str
    performance_rating: float = Field(ge=0.0, le=10.0)

    # Key insights
    strengths: list[str]
    weaknesses: list[str]

    # Improvements
    suggested_improvements: list[dict[str, Any]]
    parameter_recommendations: dict[str, Any]

    # Risk analysis
    risk_assessment: str
    max_drawdown_analysis: str

    # Market conditions
    market_conditions_analysis: str
    adaptability_score: float = Field(ge=0.0, le=1.0)


class StrategySignalAnalysis(BaseModel):
    """Structured output for strategy signal post-analysis."""
    signal_quality: float = Field(ge=0.0, le=1.0)
    proceed: bool

    # Analysis
    technical_analysis: str
    market_conditions: str

    # Contra indicators
    warning_signals: list[str]
    confirming_signals: list[str]

    # Timing
    timing_assessment: str  # excellent, good, neutral, poor
    suggested_delay_minutes: int | None = None


# ==================== Cost Tracking ====================

class CostTracker:
    """Tracks AI API costs and enforces budget limits."""

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00}
    }

    def __init__(self, monthly_budget: float, warn_threshold: float):
        """Initialize cost tracker.

        Args:
            monthly_budget: Monthly budget in EUR
            warn_threshold: Warning threshold in EUR
        """
        self.monthly_budget = monthly_budget
        self.warn_threshold = warn_threshold
        self.current_month_cost = 0.0
        self.current_month = datetime.utcnow().month
        self._lock = asyncio.Lock()

    async def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Track API usage and calculate cost.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in EUR

        Raises:
            QuotaExceededError: If budget exceeded
        """
        async with self._lock:
            # Reset monthly tracking if new month
            current_month = datetime.utcnow().month
            if current_month != self.current_month:
                self.current_month = current_month
                self.current_month_cost = 0.0

            # Calculate cost
            model_base = model.split("-2024")[0]  # Remove date suffix
            pricing = self.PRICING.get(model_base, self.PRICING["gpt-4o-mini"])

            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            total_cost = input_cost + output_cost

            # Check budget
            if self.current_month_cost + total_cost > self.monthly_budget:
                raise QuotaExceededError(
                    f"Monthly budget of €{self.monthly_budget} would be exceeded"
                )

            # Update tracking
            self.current_month_cost += total_cost

            # Log warning if threshold reached
            if self.current_month_cost > self.warn_threshold:
                logger.warning(
                    f"AI cost warning: €{self.current_month_cost:.2f} "
                    f"of €{self.monthly_budget:.2f} budget used"
                )

            return total_cost


# ==================== Cache Manager ====================

class CacheManager:
    """Manages caching of AI responses."""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize cache manager.

        Args:
            ttl_seconds: Cache TTL in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._memory_cache: dict[str, Any] = {}

    def _generate_key(self, prompt: str, model: str, schema: dict[str, Any]) -> str:
        """Generate cache key from request parameters."""
        content = f"{prompt}:{model}:{json.dumps(schema, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get(
        self,
        prompt: str,
        model: str,
        schema: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Get cached response if available.

        Args:
            prompt: The prompt
            model: Model name
            schema: Response schema

        Returns:
            Cached response or None
        """
        key = self._generate_key(prompt, model, schema)

        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if datetime.utcnow() < entry['expires_at']:
                logger.debug(f"Cache hit for key {key[:8]}...")
                return entry['response']

        return None

    async def set(
        self,
        prompt: str,
        model: str,
        schema: dict[str, Any],
        response: dict[str, Any]
    ) -> None:
        """Cache a response.

        Args:
            prompt: The prompt
            model: Model name
            schema: Response schema
            response: The response to cache
        """
        key = self._generate_key(prompt, model, schema)
        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)

        self._memory_cache[key] = {
            'response': response,
            'expires_at': expires_at
        }

        # Clean up expired entries
        await self._cleanup_expired()

    async def _cleanup_expired(self) -> None:
        """Remove expired entries from memory cache."""
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if now >= v['expires_at']
        ]
        for key in expired_keys:
            del self._memory_cache[key]


# ==================== OpenAI Service ====================

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
        self.cache_manager = CacheManager(ttl_seconds=config.cache_ttl if hasattr(config, 'cache_ttl') else 3600)

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

    async def __aexit__(self, exc_type, exc_val, exc_tb):
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
        model = model or self.config.model_default
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
        """Analyze an order before placement.

        Args:
            order_details: Order information
            market_context: Current market context

        Returns:
            Structured order analysis
        """
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
        """Triage an alert for priority and action.

        Args:
            alert: Alert information
            portfolio_context: Current portfolio context

        Returns:
            Structured triage result
        """
        prompt = self._build_alert_triage_prompt(alert, portfolio_context)

        return await self.structured_completion(
            prompt=prompt,
            response_model=AlertTriageResult,
            model=self.config.model_default,
            context={"type": "alert_triage", "alert_type": alert.get("type")}
        )

    async def review_backtest(
        self,
        results: dict[str, Any],
        strategy_params: dict[str, Any]
    ) -> BacktestReview:
        """Review backtest results.

        Args:
            results: Backtest results
            strategy_params: Strategy parameters used

        Returns:
            Structured backtest review
        """
        prompt = self._build_backtest_review_prompt(results, strategy_params)

        return await self.structured_completion(
            prompt=prompt,
            response_model=BacktestReview,
            model=self.config.model_default,
            context={"type": "backtest_review", "strategy": strategy_params.get("name")}
        )

    async def analyze_signal(
        self,
        signal: dict[str, Any],
        indicators: dict[str, Any]
    ) -> StrategySignalAnalysis:
        """Analyze a strategy signal.

        Args:
            signal: Signal information
            indicators: Current indicator values

        Returns:
            Structured signal analysis
        """
        prompt = self._build_signal_analysis_prompt(signal, indicators)

        return await self.structured_completion(
            prompt=prompt,
            response_model=StrategySignalAnalysis,
            model=self.config.model_default,
            context={"type": "signal_analysis", "signal_type": signal.get("type")}
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

    def _build_backtest_review_prompt(
        self,
        results: dict[str, Any],
        strategy_params: dict[str, Any]
    ) -> str:
        """Build prompt for backtest review."""
        return f"""Review the following backtest results:

Strategy: {strategy_params.get('name')}
Parameters: {json.dumps(strategy_params, indent=2)}

Results:
- Total Return: {results.get('total_return')}%
- Sharpe Ratio: {results.get('sharpe_ratio')}
- Max Drawdown: {results.get('max_drawdown')}%
- Win Rate: {results.get('win_rate')}%
- Total Trades: {results.get('total_trades')}

Provide a comprehensive review including strengths, weaknesses, suggested improvements,
and parameter recommendations. Focus on actionable insights."""

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