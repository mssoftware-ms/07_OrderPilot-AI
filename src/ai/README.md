# AI Services - Quick Start

Multi-provider AI service layer with unified API for OrderPilot-AI.

**Version:** 2.0 (Refactored 2026-01-31)

---

## Supported Providers

| Provider | Default Model | Pricing ($/1M tokens) | Features |
|----------|---------------|----------------------|----------|
| **Anthropic** | claude-sonnet-4-5-20250929 | $3/$15 (in/out) | Claude models, system prompts |
| **Google Gemini** | gemini-2.0-flash-exp | $0.10/$0.30 (Flash) | Safety filters, JSON mode |
| **OpenAI** | gpt-4o-mini | $0.15/$0.60 | json_schema, function calling |

---

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

Dependencies:
- `pydantic` - Structured outputs
- `aiohttp` - Async HTTP client
- `tenacity` - Retry logic

---

### 2. Configuration

```python
from src.config.loader import AIConfig

config = AIConfig(
    cost_limit_monthly=100.0,  # Monthly budget in USD
    cache_ttl=3600,  # Cache TTL in seconds (1 hour)
    timeouts={"read_ms": 15000, "connect_ms": 5000}
)
```

---

### 3. Basic Usage

```python
from src.ai.anthropic_service import AnthropicService
from src.config.loader import AIConfig

# Initialize
config = AIConfig(cost_limit_monthly=100.0)
service = AnthropicService(config, api_key="sk-ant-...")

# Use async context manager
async with service:
    # Analyze an order
    analysis = await service.analyze_order({
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 100,
        "order_type": "market"
    })

    print(f"Approved: {analysis.approved}")
    print(f"Confidence: {analysis.confidence:.2%}")
    print(f"Reasoning: {analysis.reasoning}")

    # Check costs
    summary = service.get_cost_summary()
    print(f"Cost: ${summary['current_month_cost']:.2f}")
```

---

### 4. All Providers

```python
from src.ai.anthropic_service import AnthropicService
from src.ai.gemini_service import GeminiService
from src.ai.openai_service import OpenAIService

# Anthropic
async with AnthropicService(config, api_key="sk-ant-...") as service:
    analysis = await service.analyze_order(order_data)

# Gemini
async with GeminiService(config, api_key="AIza...") as service:
    analysis = await service.analyze_order(order_data)

# OpenAI
async with OpenAIService(config, api_key="sk-...") as service:
    analysis = await service.analyze_order(order_data)
```

---

## Features

### Unified API

All providers share the same methods:

```python
# These work with ANY provider
await service.analyze_order(order_data)
await service.triage_alert(alert_data)
await service.review_backtest(backtest_data)
await service.structured_completion(prompt, response_model)
```

---

### Cost Tracking

Built-in budget management:

```python
# Set monthly budget
config = AIConfig(cost_limit_monthly=100.0)

# Get cost summary
summary = service.get_cost_summary()
print(f"Used: ${summary['current_month_cost']:.2f}")
print(f"Remaining: ${summary['remaining_budget']:.2f}")
print(f"Budget used: {summary['budget_used_pct']:.1f}%")

# QuotaExceededError raised automatically if budget exceeded
```

---

### Response Caching

Automatic caching to reduce costs:

```python
# First call: API request
result1 = await service.analyze_order(order_data, use_cache=True)

# Second call: Cache hit (no API request, no cost)
result2 = await service.analyze_order(order_data, use_cache=True)

# Clear cache
service.clear_cache()
```

---

### Structured Outputs

Type-safe responses with Pydantic:

```python
from src.ai.openai_models import OrderAnalysis

analysis = await service.analyze_order(order_data)

# Type-safe access
if analysis.approved:
    print(f"Confidence: {analysis.confidence:.2%}")
    print(f"Risks: {', '.join(analysis.risks)}")
    print(f"Fee impact: {analysis.fee_impact}")
```

---

### Error Handling

Robust error handling with automatic retries:

```python
from src.ai.openai_models import (
    QuotaExceededError,
    RateLimitError,
    SchemaValidationError
)

try:
    result = await service.analyze_order(order_data)
except QuotaExceededError:
    print("Monthly budget exceeded!")
except RateLimitError:
    print("Rate limited (auto-retries 3x)")
except SchemaValidationError as e:
    print(f"Invalid response: {e}")
```

---

## Available Methods

### High-Level Methods

```python
# Order analysis
await service.analyze_order(order_data: dict) -> OrderAnalysis

# Alert triage
await service.triage_alert(alert_data: dict) -> AlertTriageResult

# Backtest review
await service.review_backtest(backtest_data: dict) -> BacktestReview
```

---

### Low-Level Method

```python
# Custom structured completions
from src.ai.openai_models import OrderAnalysis

result = await service.structured_completion(
    prompt="Your custom prompt",
    response_model=OrderAnalysis,
    model="gpt-4o-mini",  # Optional, defaults to service.default_model
    temperature=0.2,  # 0.0-1.0
    use_cache=True,  # Enable caching
    context={"feature": "custom"}  # For telemetry
)
```

---

## Response Models

```python
from src.ai.openai_models import (
    OrderAnalysis,         # Order risk analysis
    AlertTriageResult,     # Alert prioritization
    BacktestReview,        # Backtest insights
    StrategySignalAnalysis,  # Signal validation
    StrategyTradeAnalysis,   # Trade post-analysis
)
```

See `src/ai/openai_models.py` for field details.

---

## Architecture

Built on **BaseAIService** using Template Method Pattern:

```
BaseAIService (570 LOC)
├── Common logic: caching, cost tracking, validation
└── Abstract methods: provider-specific format, parsing, pricing

AnthropicService (159 LOC)
├── Inherits from BaseAIService
└── Implements 6 abstract methods (Anthropic-specific)

GeminiService (188 LOC)
├── Inherits from BaseAIService
└── Implements 6 abstract methods (Gemini-specific)

OpenAIService (253 LOC)
├── Inherits from BaseAIService
├── 3 OpenAI-specific mixins
└── Implements 6 abstract methods (OpenAI-specific)
```

**Benefits:**
- ✅ 35% less code (1,170 LOC vs 1,808 LOC)
- ✅ Single source of truth for common logic
- ✅ Easy to add new providers (~150 LOC)
- ✅ 100% backward compatible

---

## Documentation

| Document | Purpose |
|----------|------------|
| [ARCHITECTURE.md](../../docs/ai/ARCHITECTURE.md) | High-level architecture overview |
| [API.md](../../docs/ai/API.md) | Complete API reference |
| [MIGRATION_GUIDE.md](../../docs/ai/MIGRATION_GUIDE.md) | Adding new providers |
| [DEVELOPER_GUIDE.md](../../docs/ai/DEVELOPER_GUIDE.md) | Best practices and patterns |

---

## Examples

### Example 1: Order Analysis

```python
from src.ai.anthropic_service import AnthropicService
from src.config.loader import AIConfig

config = AIConfig(cost_limit_monthly=100.0)
service = AnthropicService(config, api_key="sk-ant-...")

async with service:
    analysis = await service.analyze_order({
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 100,
        "order_type": "market",
        "account_balance": 50000
    })

    if analysis.approved:
        print(f"✅ Order approved (confidence: {analysis.confidence:.2%})")
        print(f"Reasoning: {analysis.reasoning}")

        if analysis.suggested_adjustments:
            print(f"Suggestions: {analysis.suggested_adjustments}")
    else:
        print(f"❌ Order rejected")
        print(f"Risks: {', '.join(analysis.risks)}")
```

---

### Example 2: Alert Triage

```python
async with service:
    triage = await service.triage_alert({
        "type": "price_spike",
        "symbol": "TSLA",
        "current_price": 250.0,
        "change_percent": 8.5,
        "volume_spike": True,
        "position": {"quantity": 100, "avg_cost": 230.0}
    })

    print(f"Priority: {triage.priority_score:.2%}")
    print(f"Urgency: {triage.estimated_urgency}")

    if triage.action_required:
        print("Suggested actions:")
        for action in triage.suggested_actions:
            print(f"  - {action}")
```

---

### Example 3: Provider Comparison

```python
from src.ai.anthropic_service import AnthropicService
from src.ai.gemini_service import GeminiService
from src.ai.openai_service import OpenAIService

providers = [
    AnthropicService(config, api_key="sk-ant-..."),
    GeminiService(config, api_key="AIza..."),
    OpenAIService(config, api_key="sk-...")
]

order_data = {"symbol": "AAPL", "side": "buy", "quantity": 100}

for provider in providers:
    async with provider:
        result = await provider.analyze_order(order_data)
        print(f"{provider._get_provider_name()}: {result.approved}")
```

---

### Example 4: Custom Prompt

```python
from pydantic import BaseModel, Field

class CustomAnalysis(BaseModel):
    score: float = Field(ge=0.0, le=10.0)
    summary: str

async with service:
    result = await service.structured_completion(
        prompt="Rate this strategy from 0-10: ...",
        response_model=CustomAnalysis,
        temperature=0.3
    )

    print(f"Score: {result.score}/10")
    print(f"Summary: {result.summary}")
```

---

## Version

**2.0** (Refactored 2026-01-31)

**Changes from 1.0:**
- ✅ Introduced BaseAIService (Template Method Pattern)
- ✅ Reduced code by 35% (-638 LOC)
- ✅ Unified API across all providers
- ✅ 100% backward compatible
- ✅ Improved testability and maintainability

---

**Last Updated:** 2026-01-31
**Document Version:** 1.0
