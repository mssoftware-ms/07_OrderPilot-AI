# AI Services Developer Guide

Best practices, patterns, and tips for working with the AI Services module.

**Version:** 2.0
**Last Updated:** 2026-01-31

---

## Table of Contents

1. [Best Practices](#best-practices)
2. [Common Patterns](#common-patterns)
3. [Performance Optimization](#performance-optimization)
4. [Error Handling](#error-handling)
5. [Testing Strategies](#testing-strategies)
6. [Debugging Tips](#debugging-tips)
7. [Security Considerations](#security-considerations)

---

## Best Practices

### 1. Always Use Async Context Manager

The async context manager (`async with`) ensures proper resource cleanup.

```python
# ✅ GOOD: Automatic session management
async with service:
    result = await service.analyze_order(order_data)
# Session automatically closed

# ❌ BAD: Manual session management (prone to resource leaks)
service = AnthropicService(config, api_key)
await service.initialize()
result = await service.analyze_order(order_data)
# Session not closed → resource leak!
```

---

### 2. Handle All Exception Types

Different exceptions require different handling strategies.

```python
from src.ai.openai_models import (
    QuotaExceededError,
    RateLimitError,
    SchemaValidationError,
    OpenAIError
)

async with service:
    try:
        result = await service.analyze_order(order_data)

    except QuotaExceededError:
        # Budget exceeded - defer request or notify admin
        logger.error("Monthly budget exceeded")
        await notify_admin("AI budget exceeded")

    except RateLimitError:
        # Rate limited (after 3 retries) - log and continue
        logger.warning("Rate limited after retries")
        # Tenacity already retried 3x

    except SchemaValidationError as e:
        # Invalid response - log for debugging
        logger.error(f"Schema validation failed: {e}")
        # Provider may have changed response format

    except OpenAIError as e:
        # General API error - check status, retry later
        logger.error(f"API error: {e}")
```

---

### 3. Use Type Hints

Type hints improve IDE support and catch errors early.

```python
from src.ai.anthropic_service import AnthropicService
from src.ai.openai_models import OrderAnalysis
from typing import Dict, Any

async def process_order(
    service: AnthropicService,
    order_data: Dict[str, Any]
) -> OrderAnalysis:
    """Process order with type-safe interface."""
    return await service.analyze_order(order_data)
```

---

### 4. Monitor Costs Regularly

Check costs periodically to avoid budget surprises.

```python
async with service:
    # Process orders...
    result = await service.analyze_order(order_data)

    # Check costs periodically
    summary = service.get_cost_summary()

    if summary['budget_used_pct'] > 80:
        logger.warning(
            f"Approaching budget limit: {summary['budget_used_pct']:.1f}% used"
        )

    if summary['budget_used_pct'] > 90:
        logger.critical("Critical: 90% of budget used!")
        await notify_admin(summary)
```

---

### 5. Use Caching Wisely

Enable caching for repeated queries, disable for unique data.

```python
# ✅ GOOD: Caching for repeated analysis
async with service:
    # Same order analyzed multiple times → cache beneficial
    for _ in range(10):
        analysis = await service.analyze_order(
            order_data,  # Same data
            use_cache=True  # Cache enabled
        )
# Only 1 API call, 9 cache hits

# ✅ GOOD: No caching for unique data
async with service:
    # Different order each time → no cache benefit
    for unique_order in orders:
        analysis = await service.analyze_order(
            unique_order,
            use_cache=False  # No cache overhead
        )
```

---

## Common Patterns

### Pattern 1: Batch Processing with Concurrency

Process multiple orders concurrently for better performance.

```python
import asyncio
from typing import List, Dict, Any

async def analyze_multiple_orders(
    service: AnthropicService,
    orders: List[Dict[str, Any]]
) -> List[OrderAnalysis]:
    """Analyze multiple orders concurrently."""
    tasks = [
        service.analyze_order(order)
        for order in orders
    ]

    # Run concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle results
    analyses = []
    for order, result in zip(orders, results):
        if isinstance(result, Exception):
            logger.error(f"Failed for {order['symbol']}: {result}")
        else:
            analyses.append(result)

    return analyses

# Usage
async with service:
    analyses = await analyze_multiple_orders(service, orders)
```

---

### Pattern 2: Provider Fallback

Try multiple providers if one fails.

```python
async def analyze_with_fallback(
    order_data: Dict[str, Any],
    config: AIConfig
) -> OrderAnalysis:
    """Analyze order with provider fallback."""
    providers = [
        ("Anthropic", AnthropicService, os.getenv("ANTHROPIC_API_KEY")),
        ("Gemini", GeminiService, os.getenv("GEMINI_API_KEY")),
        ("OpenAI", OpenAIService, os.getenv("OPENAI_API_KEY")),
    ]

    for name, service_class, api_key in providers:
        try:
            async with service_class(config, api_key) as service:
                return await service.analyze_order(order_data)

        except (RateLimitError, OpenAIError) as e:
            logger.warning(f"{name} failed: {e}, trying next provider...")
            continue

    raise RuntimeError("All providers failed")

# Usage
analysis = await analyze_with_fallback(order_data, config)
```

---

### Pattern 3: Cost-Aware Model Selection

Use cheaper models for simple tasks, expensive models for complex tasks.

```python
def select_model(task_complexity: str) -> str:
    """Select model based on task complexity."""
    if task_complexity == "simple":
        return "gpt-4o-mini"  # $0.15/1M input (cheap)
    elif task_complexity == "medium":
        return "gemini-2.0-flash-exp"  # $0.10/1M input
    else:
        return "claude-sonnet-4-5-20250929"  # $3/1M input (expensive, best)

async with service:
    # Simple task: Use cheap model
    result = await service.structured_completion(
        prompt="Summarize this trade",
        response_model=TradeSummary,
        model=select_model("simple")
    )

    # Complex task: Use expensive model
    result = await service.review_backtest(
        backtest_data,
        model=select_model("complex")
    )
```

---

### Pattern 4: Custom High-Level Methods

Extend BaseAIService with domain-specific methods.

```python
# In your custom service wrapper
class TradingAIService(AnthropicService):
    """Trading-specific AI service."""

    async def analyze_market_sentiment(
        self,
        news_items: List[str]
    ) -> MarketSentiment:
        """Analyze market sentiment from news."""
        prompt = f"Analyze market sentiment from these news items:\\n"
        for item in news_items:
            prompt += f"- {item}\\n"

        return await self.structured_completion(
            prompt=prompt,
            response_model=MarketSentiment,
            temperature=0.2
        )

# Define response model
from pydantic import BaseModel, Field

class MarketSentiment(BaseModel):
    overall_sentiment: str  # bullish, bearish, neutral
    confidence: float = Field(ge=0.0, le=1.0)
    key_factors: List[str]

# Usage
async with TradingAIService(config, api_key) as service:
    sentiment = await service.analyze_market_sentiment(news_items)
```

---

## Performance Optimization

### 1. Use Caching for Repeated Queries

```python
# First call: API request
result1 = await service.analyze_order(order_data, use_cache=True)

# Second call: Cache hit (no API call, no cost)
result2 = await service.analyze_order(order_data, use_cache=True)

# Clear cache when data changes
service.clear_cache()
```

---

### 2. Adjust Cache TTL

```python
# Short-lived data → shorter TTL
config = AIConfig(
    cost_limit_monthly=100.0,
    cache_ttl=300  # 5 minutes
)

# Long-lived data → longer TTL
config = AIConfig(
    cost_limit_monthly=100.0,
    cache_ttl=7200  # 2 hours
)
```

---

### 3. Batch Similar Requests

```python
# ❌ BAD: Multiple API calls
for order in orders:
    analysis = await service.analyze_order(order)

# ✅ GOOD: Batch in single prompt
prompt = "Analyze these orders:\\n"
for order in orders:
    prompt += f"- {order}\\n"

class BatchOrderAnalysis(BaseModel):
    analyses: List[OrderAnalysis]

result = await service.structured_completion(
    prompt=prompt,
    response_model=BatchOrderAnalysis
)
```

---

### 4. Use Cheaper Models When Possible

```python
# For simple tasks
simple_result = await service.structured_completion(
    prompt=simple_prompt,
    response_model=SimpleResult,
    model="gpt-4o-mini"  # $0.15/1M input (cheap)
)

# For complex tasks only
complex_result = await service.review_backtest(
    backtest_data,
    model="claude-sonnet-4-5-20250929"  # $3/1M input (expensive)
)
```

---

### 5. Process Concurrently

```python
import asyncio

# Process multiple requests concurrently
tasks = [service.analyze_order(order) for order in orders]
results = await asyncio.gather(*tasks)
```

---

## Error Handling

### HTTP Status Codes

BaseAIService automatically handles common HTTP errors:

- **429 (Rate Limit):** Automatic retry with exponential backoff (3x)
- **500 (Server Error):** Automatic retry (3x)
- **400 (Bad Request):** Raises `OpenAIError` immediately
- **401 (Unauthorized):** Raises `OpenAIError` (invalid API key)

---

### Retry Logic

Powered by `tenacity` library:

```python
# In BaseAIService._execute_request()
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
)
async def _execute_request(self, request_body: dict) -> dict:
    # ...
```

**Retry Strategy:**
- Max 3 attempts
- Exponential backoff: 2s, 4s, 8s
- Only retries network errors and server errors

---

### Provider-Specific Errors

#### Gemini Safety Filters

```python
try:
    result = await gemini_service.analyze_order(order_data)
except SchemaValidationError as e:
    if "safety filter" in str(e).lower():
        # Prompt triggered safety filter
        logger.warning("Prompt blocked by Gemini safety filter")
        # Retry with modified prompt or use different provider
```

---

#### OpenAI Refusals

```python
try:
    result = await openai_service.analyze_order(order_data)
except OpenAIError as e:
    if "refused" in str(e).lower():
        # Model refused to answer
        logger.warning("OpenAI refused request")
        # Check prompt for policy violations
```

---

## Testing Strategies

### Unit Testing: Mock HTTP Responses

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_analyze_order_mocked():
    """Test analyze_order without real API calls."""
    service = AnthropicService(config, api_key="test-key")

    # Mock the HTTP response
    mock_response = {
        "content": [{"text": '{"approved": true, "confidence": 0.9, ...}'}],
        "usage": {"input_tokens": 100, "output_tokens": 50}
    }

    with patch.object(service, '_execute_request', new=AsyncMock(return_value=mock_response)):
        async with service:
            result = await service.analyze_order({"symbol": "AAPL", ...})

            assert result.approved is True
            assert result.confidence == 0.9
```

---

### Integration Testing: Test Provider-Specific Logic

```python
def test_anthropic_extract_text_content():
    """Test Anthropic-specific content extraction."""
    service = AnthropicService(config, api_key="test-key")

    response_data = {
        "content": [{"text": "Test response"}],
        "usage": {"input_tokens": 100, "output_tokens": 50}
    }

    text = service._extract_text_content(response_data)
    assert text == "Test response"

def test_anthropic_extract_text_error():
    """Test error handling."""
    service = AnthropicService(config, api_key="test-key")

    response_data = {"content": []}  # No content

    with pytest.raises(SchemaValidationError):
        service._extract_text_content(response_data)
```

---

### E2E Testing: Test Complete Workflows

```python
@pytest.mark.asyncio
async def test_e2e_order_analysis():
    """Test complete order analysis workflow."""
    service = AnthropicService(config, api_key="test-key")

    # Mock response
    mock_response = create_mock_anthropic_response(...)
    await setup_mock_session(service, mock_response)

    # Execute
    result = await service.analyze_order(order_data)

    # Validate
    assert isinstance(result, OrderAnalysis)
    assert result.approved is True
    assert 0.0 <= result.confidence <= 1.0
```

---

## Debugging Tips

### 1. Enable Debug Logging

```python
import logging

# Enable debug logging for AI services
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or specific logger
logging.getLogger('src.ai').setLevel(logging.DEBUG)
```

**You'll see:**
```
DEBUG - src.ai.base_service - Current monthly cost: $0.05
DEBUG - src.ai.base_service - Cache miss for OrderAnalysis
DEBUG - src.ai.anthropic_service - Building request for claude-sonnet-4-5
DEBUG - src.ai.base_service - API call latency: 1234ms
DEBUG - src.ai.base_service - Cost: $0.0015
```

---

### 2. Inspect Raw Responses

Add temporary logging to see raw API responses:

```python
def _extract_text_content(self, response_data: dict) -> str:
    logger.debug(f"Raw response: {response_data}")  # ADD THIS LINE
    return response_data["content"][0]["text"]
```

---

### 3. Test with Small Models

Use cheap models during development:

```python
if os.getenv("ENV") == "development":
    model = "gpt-4o-mini"  # Cheap for testing
else:
    model = "gpt-4o"  # Production

result = await service.structured_completion(
    prompt=prompt,
    response_model=OrderAnalysis,
    model=model
)
```

---

### 4. Validate Pydantic Schemas

Test schema validation independently:

```python
from src.ai.openai_models import OrderAnalysis

# Valid JSON
valid_json = '{"approved": true, "confidence": 0.9, ...}'
analysis = OrderAnalysis.model_validate_json(valid_json)

# Invalid JSON
invalid_json = '{"approved": "yes", "confidence": 2.0}'  # Wrong types
with pytest.raises(ValidationError):
    OrderAnalysis.model_validate_json(invalid_json)
```

---

## Security Considerations

### 1. Never Log API Keys

```python
# ❌ WRONG
logger.info(f"Using API key: {api_key}")

# ✅ CORRECT
logger.info("Initializing service with API key")
```

---

### 2. Use Environment Variables

```python
import os

# ✅ GOOD
api_key = os.getenv("ANTHROPIC_API_KEY")
service = AnthropicService(config, api_key)

# ❌ BAD
api_key = "sk-ant-1234..."  # Hardcoded!
```

---

### 3. Validate User Input

```python
def validate_order_data(order_data: dict) -> None:
    """Validate order data before sending to AI."""
    required_fields = ["symbol", "side", "quantity", "price"]

    for field in required_fields:
        if field not in order_data:
            raise ValueError(f"Missing required field: {field}")

    if order_data["side"] not in ["buy", "sell"]:
        raise ValueError("Invalid side (must be 'buy' or 'sell')")

    if order_data["quantity"] <= 0:
        raise ValueError("Quantity must be positive")

# Use before AI call
validate_order_data(order_data)
analysis = await service.analyze_order(order_data)
```

---

### 4. Sanitize Prompts

Remove sensitive information from prompts:

```python
def sanitize_prompt(prompt: str) -> str:
    """Remove sensitive info from prompt."""
    # Remove API keys
    prompt = re.sub(r'sk-[a-zA-Z0-9]{48}', '[API_KEY]', prompt)

    # Remove email addresses
    prompt = re.sub(r'[\\w.-]+@[\\w.-]+\\.\\w+', '[EMAIL]', prompt)

    return prompt

# Use before sending
clean_prompt = sanitize_prompt(user_prompt)
result = await service.structured_completion(
    prompt=clean_prompt,
    response_model=ResponseModel
)
```

---

## Tips and Tricks

### 1. Version Your Prompts

Keep track of prompt versions for reproducibility:

```python
PROMPT_VERSIONS = {
    "1.0": "Analyze this order: {order_data}",
    "1.1": "Analyze this order with risk assessment: {order_data}",
    "2.0": "Analyze order considering market conditions: {order_data}"
}

async def analyze_order_v2(service, order_data):
    """Analyze order using prompt v2.0."""
    prompt = PROMPT_VERSIONS["2.0"].format(order_data=order_data)
    return await service.structured_completion(
        prompt=prompt,
        response_model=OrderAnalysis
    )
```

---

### 2. Document Custom Methods

Add clear docstrings for custom methods:

```python
async def custom_analysis(
    self,
    data: dict[str, Any]
) -> CustomResult:
    """Custom analysis method.

    Added for Project X feature (2026-02-15).

    Args:
        data: Custom data format with keys:
            - field1: Description
            - field2: Description

    Returns:
        CustomResult with analysis

    Example:
        >>> result = await service.custom_analysis({"field1": "value"})
        >>> print(result.score)
        0.85

    Note:
        This method uses temperature=0.1 for consistent results.
    """
    prompt = f"Analyze: {data}"
    return await self.structured_completion(
        prompt=prompt,
        response_model=CustomResult,
        temperature=0.1
    )
```

---

### 3. Use Telemetry Callbacks

Track AI usage across your application:

```python
def telemetry_callback(event: dict):
    """Log AI events for monitoring."""
    logger.info(f"AI Event: {event['type']}")
    # Send to monitoring system (Datadog, New Relic, etc.)

service = AnthropicService(config, api_key, telemetry_callback=telemetry_callback)
```

---

## Summary

**Key Takeaways:**
- ✅ Always use async context manager
- ✅ Handle all exception types appropriately
- ✅ Monitor costs regularly
- ✅ Use caching for repeated queries
- ✅ Test with mocked responses
- ✅ Sanitize user input and prompts
- ✅ Log appropriately (no sensitive data)
- ✅ Version your prompts

**Resources:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [API.md](API.md) - Complete API reference
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Adding new providers

---

**Last Updated:** 2026-01-31
**Document Version:** 1.0
