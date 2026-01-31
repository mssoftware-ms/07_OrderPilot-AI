# AI Services API Reference

Complete API reference for BaseAIService and all provider implementations.

**Version:** 2.0 (Refactored 2026-01-31)

---

## Table of Contents

1. [BaseAIService](#baseaiservice)
2. [Provider Services](#provider-services)
3. [Response Models](#response-models)
4. [Error Classes](#error-classes)
5. [Utility Classes](#utility-classes)

---

## BaseAIService

Abstract base class providing common AI service functionality.

### Constructor

```python
def __init__(
    self,
    config: AIConfig,
    api_key: str,
    telemetry_callback: callable | None = None
)
```

**Parameters:**
- `config` (AIConfig): Configuration including cost limits and timeouts
- `api_key` (str): Provider API key
- `telemetry_callback` (callable | None): Optional callback for telemetry events

**Attributes:**
- `cost_tracker` (CostTracker): Tracks API costs
- `cache_manager` (CacheManager): Manages response caching
- `config` (AIConfig): Configuration object
- `api_key` (str): Provider API key

---

### High-Level Methods

#### analyze_order

```python
async def analyze_order(
    self,
    order_data: dict[str, Any],
    temperature: float = 0.2,
    model: str | None = None,
    use_cache: bool = True,
    context: dict[str, Any] | None = None
) -> OrderAnalysis
```

Analyze a trading order for risk and approval.

**Parameters:**
- `order_data` (dict): Order details (symbol, side, quantity, price, etc.)
- `temperature` (float): Sampling temperature (0.0-1.0), default: 0.2
- `model` (str | None): Override default model
- `use_cache` (bool): Enable response caching, default: True
- `context` (dict | None): Additional context for telemetry

**Returns:**
- `OrderAnalysis`: Structured analysis with approval decision

**Example:**
```python
async with service:
    analysis = await service.analyze_order({
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 100,
        "order_type": "market",
        "price": 150.25
    })

    print(f"Approved: {analysis.approved}")
    print(f"Confidence: {analysis.confidence}")
    print(f"Reasoning: {analysis.reasoning}")
```

---

#### triage_alert

```python
async def triage_alert(
    self,
    alert_data: dict[str, Any],
    temperature: float = 0.3,
    model: str | None = None,
    use_cache: bool = True,
    context: dict[str, Any] | None = None
) -> AlertTriageResult
```

Triage a trading alert to determine priority and required actions.

**Parameters:**
- `alert_data` (dict): Alert details (type, symbol, change_pct, etc.)
- `temperature` (float): Sampling temperature, default: 0.3
- `model` (str | None): Override default model
- `use_cache` (bool): Enable response caching
- `context` (dict | None): Additional context

**Returns:**
- `AlertTriageResult`: Structured triage result with priority and actions

**Example:**
```python
async with service:
    triage = await service.triage_alert({
        "type": "price_spike",
        "symbol": "TSLA",
        "change_pct": 5.2,
        "volume_change": 3.5
    })

    print(f"Priority: {triage.priority_score}")
    print(f"Action Required: {triage.action_required}")
    print(f"Suggested Actions: {triage.suggested_actions}")
```

---

#### review_backtest

```python
async def review_backtest(
    self,
    backtest_data: dict[str, Any],
    temperature: float = 0.4,
    model: str | None = None,
    use_cache: bool = True,
    context: dict[str, Any] | None = None
) -> BacktestReview
```

Review backtest results and provide improvement suggestions.

**Parameters:**
- `backtest_data` (dict): Backtest metrics (total_return, sharpe_ratio, etc.)
- `temperature` (float): Sampling temperature, default: 0.4
- `model` (str | None): Override default model
- `use_cache` (bool): Enable response caching
- `context` (dict | None): Additional context

**Returns:**
- `BacktestReview`: Structured review with assessment and suggestions

**Example:**
```python
async with service:
    review = await service.review_backtest({
        "total_return": 0.35,
        "sharpe_ratio": 1.8,
        "max_drawdown": -0.15,
        "win_rate": 0.62
    })

    print(f"Rating: {review.performance_rating}/10")
    print(f"Strengths: {review.strengths}")
    print(f"Weaknesses: {review.weaknesses}")
```

---

### Core Method

#### structured_completion

```python
async def structured_completion(
    self,
    prompt: str,
    response_model: type[T],
    model: str | None = None,
    temperature: float = 0.2,
    use_cache: bool = True,
    context: dict[str, Any] | None = None
) -> T
```

Execute a structured completion with Pydantic validation.

**Parameters:**
- `prompt` (str): The prompt text
- `response_model` (type[T]): Pydantic model for response validation
- `model` (str | None): Override default model
- `temperature` (float): Sampling temperature (0.0-1.0)
- `use_cache` (bool): Enable response caching
- `context` (dict | None): Additional context for telemetry

**Returns:**
- `T`: Validated instance of `response_model`

**Raises:**
- `QuotaExceededError`: Monthly budget exceeded
- `RateLimitError`: API rate limit hit (after 3 retries)
- `SchemaValidationError`: Response doesn't match schema
- `OpenAIError`: General API error

**Example:**
```python
from pydantic import BaseModel, Field

class SentimentAnalysis(BaseModel):
    sentiment: str  # positive, negative, neutral
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)

async with service:
    result = await service.structured_completion(
        prompt="Analyze sentiment: 'Great product, highly recommend!'",
        response_model=SentimentAnalysis,
        temperature=0.1
    )

    print(f"Sentiment: {result.sentiment}")
    print(f"Score: {result.score}")
```

---

### Management Methods

#### get_cost_summary

```python
def get_cost_summary(self) -> dict[str, Any]
```

Get current cost tracking summary.

**Returns:**
- `dict` with keys:
  - `current_month_cost` (float): Total cost this month
  - `monthly_budget` (float): Monthly budget limit
  - `warn_threshold` (float): Warning threshold (80% of budget)
  - `remaining_budget` (float): Budget remaining
  - `budget_used_pct` (float): Percentage of budget used

**Example:**
```python
summary = service.get_cost_summary()
print(f"Used: ${summary['current_month_cost']:.2f}")
print(f"Remaining: ${summary['remaining_budget']:.2f}")
print(f"Used: {summary['budget_used_pct']:.1f}%")
```

---

#### reset_costs

```python
def reset_costs(self) -> None
```

Reset monthly cost tracking to zero.

**Example:**
```python
service.reset_costs()
```

---

#### clear_cache

```python
def clear_cache(self) -> None
```

Clear all cached responses.

**Example:**
```python
service.clear_cache()
```

---

### Lifecycle Methods

#### initialize

```python
async def initialize(self) -> None
```

Initialize HTTP session. Called automatically by async context manager.

**Example:**
```python
await service.initialize()
```

---

#### close

```python
async def close(self) -> None
```

Close HTTP session. Called automatically by async context manager.

**Example:**
```python
await service.close()
```

---

#### Context Manager

```python
async with service:
    # Service is initialized
    result = await service.analyze_order(...)
# Service is automatically closed
```

---

### Abstract Methods

These methods must be implemented by provider-specific subclasses.

#### _build_request_body

```python
@abstractmethod
def _build_request_body(
    self,
    prompt: str,
    response_model: type[T],
    model: str,
    temperature: float
) -> dict[str, Any]
```

Build provider-specific HTTP request body.

---

#### _extract_text_content

```python
@abstractmethod
def _extract_text_content(
    self,
    response_data: dict[str, Any]
) -> str
```

Extract text content from provider response.

---

#### _extract_token_counts

```python
@abstractmethod
def _extract_token_counts(
    self,
    response_data: dict[str, Any]
) -> tuple[int, int]
```

Extract (input_tokens, output_tokens) from response.

---

#### _calculate_cost

```python
@abstractmethod
def _calculate_cost(
    self,
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float
```

Calculate cost in USD based on provider pricing.

---

#### _get_provider_name

```python
@abstractmethod
def _get_provider_name(self) -> str
```

Return provider name for logging.

---

#### _get_endpoint

```python
@abstractmethod
def _get_endpoint(self) -> str
```

Return API endpoint URL.

---

## Provider Services

### AnthropicService

```python
from src.ai.anthropic_service import AnthropicService

service = AnthropicService(config, api_key="sk-ant-...")
```

**Default Model:** `claude-sonnet-4-5-20250929`
**Pricing:** $3/$15 per 1M tokens (input/output)

**Provider-Specific Attributes:**
- `base_url`: `https://api.anthropic.com/v1`
- `headers`: `{"x-api-key": "...", "anthropic-version": "2023-06-01"}`

---

### GeminiService

```python
from src.ai.gemini_service import GeminiService

service = GeminiService(config, api_key="AIza...")
```

**Default Model:** `gemini-2.0-flash-exp`
**Pricing:**
- Flash: $0.10/$0.30 per 1M tokens
- Pro: $1.25/$5.00 per 1M tokens

**Provider-Specific Attributes:**
- `base_url`: `https://generativelanguage.googleapis.com/v1beta`
- `headers`: `{"Content-Type": "application/json"}`
- API key passed in URL query parameter

**Special Features:**
- Safety filters may block responses
- Handles `promptFeedback.blockReason`

---

### OpenAIService

```python
from src.ai.openai_service import OpenAIService

service = OpenAIService(config, api_key="sk-...")
```

**Default Model:** `gpt-4o-mini`
**Pricing:**
- GPT-4o: $2.50/$10.00 per 1M tokens
- GPT-4o-mini: $0.15/$0.60 per 1M tokens

**Provider-Specific Attributes:**
- `base_url`: `https://api.openai.com/v1`
- `headers`: `{"Authorization": "Bearer ..."}`

**Special Features:**
- Supports `json_schema` mode for structured outputs
- Handles refusals (`choices[0].message.refusal`)

---

## Response Models

All response models defined in `src/ai/openai_models.py`.

### OrderAnalysis

```python
class OrderAnalysis(BaseModel):
    approved: bool
    confidence: float  # 0.0-1.0
    reasoning: str
    risks: list[str]
    opportunities: list[str]
    suggested_adjustments: dict[str, Any]
    fee_impact: str  # Low, Medium, High
    estimated_total_cost: float
    analysis_version: str = "1.0"
```

**Example:**
```python
OrderAnalysis(
    approved=True,
    confidence=0.85,
    reasoning="Order meets risk parameters",
    risks=["Market volatility"],
    opportunities=["Strong uptrend"],
    suggested_adjustments={"stop_loss": 1.5},
    fee_impact="Low",
    estimated_total_cost=10.25
)
```

---

### AlertTriageResult

```python
class AlertTriageResult(BaseModel):
    priority_score: float  # 0.0-1.0
    action_required: bool
    reasoning: str
    key_factors: list[str]
    suggested_actions: list[str]
    estimated_urgency: str  # immediate, high, medium, low
    related_positions: list[str]
    market_context: dict[str, Any]
```

**Example:**
```python
AlertTriageResult(
    priority_score=0.95,
    action_required=True,
    reasoning="Critical price movement",
    key_factors=["Price drop >5%", "Volume spike"],
    suggested_actions=["Close position", "Review risk limits"],
    estimated_urgency="immediate",
    related_positions=["AAPL-001"],
    market_context={"volatility": "high", "trend": "bearish"}
)
```

---

### BacktestReview

```python
class BacktestReview(BaseModel):
    overall_assessment: str
    performance_rating: float  # 0.0-10.0
    strengths: list[str]
    weaknesses: list[str]
    suggested_improvements: list[dict[str, str]]
    parameter_recommendations: dict[str, Any]
    risk_assessment: str
    max_drawdown_analysis: str
    market_conditions_analysis: str
    adaptability_score: float  # 0.0-1.0
```

**Example:**
```python
BacktestReview(
    overall_assessment="Strong performance",
    performance_rating=8.5,
    strengths=["High win rate", "Good Sharpe ratio"],
    weaknesses=["Large drawdowns"],
    suggested_improvements=[
        {"type": "parameter", "description": "Reduce position size"}
    ],
    parameter_recommendations={"position_size": 0.8},
    risk_assessment="Moderate risk",
    max_drawdown_analysis="15% is acceptable",
    market_conditions_analysis="Works in trending markets",
    adaptability_score=0.75
)
```

---

### StrategySignalAnalysis

```python
class StrategySignalAnalysis(BaseModel):
    signal_quality: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    reasoning: str
    supporting_factors: list[str]
    opposing_factors: list[str]
    suggested_position_size: float
    risk_level: str  # Low, Medium, High
    time_horizon: str
    market_alignment: dict[str, Any]
```

---

### StrategyTradeAnalysis

```python
class StrategyTradeAnalysis(BaseModel):
    trade_quality: float  # 0.0-1.0
    execution_assessment: str
    profitability_analysis: str
    lessons_learned: list[str]
    strategy_alignment: bool
    suggested_strategy_adjustments: list[str]
    risk_management_assessment: str
    market_condition_impact: dict[str, Any]
```

---

## Error Classes

### QuotaExceededError

Raised when monthly cost budget is exceeded.

```python
try:
    result = await service.analyze_order(order_data)
except QuotaExceededError as e:
    print(f"Budget exceeded: {e}")
    # Handle: defer request, notify admin, etc.
```

---

### RateLimitError

Raised when API rate limit is hit (after automatic retries).

```python
try:
    result = await service.analyze_order(order_data)
except RateLimitError as e:
    print(f"Rate limited: {e}")
    # Tenacity already retried 3x with exponential backoff
```

---

### SchemaValidationError

Raised when response doesn't match expected Pydantic schema.

```python
try:
    result = await service.analyze_order(order_data)
except SchemaValidationError as e:
    print(f"Invalid response: {e}")
    # Log for debugging, provider may have changed response format
```

---

### OpenAIError

General API error (HTTP errors, network issues, etc.).

```python
try:
    result = await service.analyze_order(order_data)
except OpenAIError as e:
    print(f"API error: {e}")
    # Check API status, retry later, etc.
```

---

## Utility Classes

### CostTracker

```python
class CostTracker:
    def __init__(
        self,
        monthly_budget: float,
        warn_threshold: float | None = None
    ):
        self.monthly_budget = monthly_budget
        self.warn_threshold = warn_threshold or (monthly_budget * 0.8)
        self.current_month_cost = 0.0

    def add_cost(self, cost: float) -> None:
        """Add cost and check budget."""

    def is_over_budget(self) -> bool:
        """Check if budget exceeded."""

    def is_approaching_budget(self) -> bool:
        """Check if approaching budget (>80%)."""

    def reset(self) -> None:
        """Reset monthly costs."""
```

---

### CacheManager

```python
class CacheManager:
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl  # seconds
        self._memory_cache: dict = {}

    async def get(
        self,
        prompt: str,
        model: str,
        schema: dict
    ) -> Any | None:
        """Get cached response."""

    async def set(
        self,
        prompt: str,
        model: str,
        schema: dict,
        result: Any
    ) -> None:
        """Store response in cache."""

    def clear(self) -> None:
        """Clear all cached responses."""
```

---

## Best Practices

### 1. Always Use Async Context Manager

```python
# ✅ Good
async with service:
    result = await service.analyze_order(order_data)

# ❌ Bad
service = AnthropicService(config, api_key)
await service.initialize()
result = await service.analyze_order(order_data)
# Session not closed → resource leak
```

---

### 2. Handle Exceptions

```python
async with service:
    try:
        result = await service.analyze_order(order_data)
    except QuotaExceededError:
        # Handle budget exceeded
    except RateLimitError:
        # Handle rate limit (already retried 3x)
    except SchemaValidationError:
        # Handle invalid response
    except OpenAIError:
        # Handle general API error
```

---

### 3. Use Type Hints

```python
from src.ai.anthropic_service import AnthropicService
from src.ai.openai_models import OrderAnalysis

async def process_order(
    service: AnthropicService,
    order_data: dict[str, Any]
) -> OrderAnalysis:
    return await service.analyze_order(order_data)
```

---

### 4. Monitor Costs

```python
async with service:
    result = await service.analyze_order(order_data)

    summary = service.get_cost_summary()
    if summary['budget_used_pct'] > 80:
        logger.warning("Approaching budget limit!")
```

---

**Last Updated:** 2026-01-31
**Document Version:** 1.0
