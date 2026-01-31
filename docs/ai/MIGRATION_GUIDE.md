# Migration Guide: Adding New AI Providers

Step-by-step guide for adding new AI providers to the OrderPilot-AI system.

**Version:** 2.0
**Last Updated:** 2026-01-31

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Complete Example: Cohere](#complete-example-cohere)
5. [Testing Your Implementation](#testing-your-implementation)
6. [Common Pitfalls](#common-pitfalls)

---

## Overview

Adding a new AI provider requires:
- ~150 LOC of code (implement 6 abstract methods)
- Provider-specific tests (~100 LOC)
- Update pricing configuration

**Time Estimate:** 2-4 hours for experienced developer

**Benefits:**
- Automatic integration with all high-level methods (`analyze_order`, `triage_alert`, etc.)
- Automatic cost tracking and caching
- Automatic error handling and retries
- Type-safe structured outputs

---

## Prerequisites

### 1. Provider API Access

- API key from the provider
- API documentation URL
- Pricing information ($/1M tokens for input and output)

### 2. Understanding Response Format

Example provider API responses:

**Anthropic:**
```json
{
  "content": [{"text": "response text"}],
  "usage": {"input_tokens": 100, "output_tokens": 50}
}
```

**Gemini:**
```json
{
  "candidates": [{
    "content": {"parts": [{"text": "response text"}]}
  }],
  "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 50}
}
```

**OpenAI:**
```json
{
  "choices": [{"message": {"content": "response text"}}],
  "usage": {"prompt_tokens": 100, "completion_tokens": 50}
}
```

---

## Step-by-Step Guide

### Step 1: Create Service Class File

Create `src/ai/new_provider_service.py`:

```python
"""NewProvider Service for OrderPilot-AI Trading Application.

Implements NewProvider API integration with structured outputs,
inheriting from BaseAIService for code reuse and consistency.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from src.config.loader import AIConfig
from .base_service import BaseAIService
from .openai_models import SchemaValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class NewProviderService(BaseAIService):
    """NewProvider service implementation.

    Inherits common functionality from BaseAIService and provides
    NewProvider-specific implementations for abstract methods.
    """

    def __init__(
        self,
        config: AIConfig,
        api_key: str,
        telemetry_callback: callable | None = None
    ):
        """Initialize NewProvider service.

        Args:
            config: AI configuration
            api_key: NewProvider API key
            telemetry_callback: Optional callback for telemetry
        """
        # Initialize base class
        super().__init__(config, api_key, telemetry_callback)

        # NewProvider-specific settings
        self.base_url = "https://api.newprovider.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.default_model = "newprovider-default-model"

    # Implement 6 abstract methods (see below)
```

---

### Step 2: Implement `_build_request_body()`

Build the provider-specific HTTP request body.

```python
def _build_request_body(
    self,
    prompt: str,
    response_model: type[T],
    model: str,
    temperature: float,
) -> dict[str, Any]:
    """Build NewProvider-specific request body.

    Args:
        prompt: The prompt text
        response_model: Pydantic model for response validation
        model: Model name
        temperature: Temperature for generation (0.0-1.0)

    Returns:
        NewProvider API request dictionary
    """
    # Get JSON schema from Pydantic model
    schema = response_model.model_json_schema()
    schema_str = json.dumps(schema, indent=2)

    # Enhance prompt with schema instructions
    enhanced_prompt = f"""{prompt}

IMPORTANT: Respond with valid JSON matching this exact schema:

{schema_str}

Do not include any explanation, markdown formatting, or code blocks. Only output the raw JSON object."""

    # Build provider-specific request format
    return {
        "model": model,
        "messages": [
            {"role": "user", "content": enhanced_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 4096,
        # Add any provider-specific parameters
    }
```

---

### Step 3: Implement `_extract_text_content()`

Extract text content from the provider's response format.

```python
def _extract_text_content(self, response_data: dict[str, Any]) -> str:
    """Extract text content from NewProvider response.

    Args:
        response_data: Raw JSON response from NewProvider API

    Returns:
        Extracted text content

    Raises:
        SchemaValidationError: If content cannot be extracted
    """
    # Adapt this to your provider's response structure
    try:
        # Example for provider with "choices" structure
        choices = response_data.get("choices", [])
        if not choices:
            raise SchemaValidationError("No choices in NewProvider response")

        message = choices[0].get("message", {})
        content = message.get("content")

        if not content:
            # Check for provider-specific error conditions
            if "error" in response_data:
                error = response_data["error"]
                raise SchemaValidationError(f"Provider error: {error}")

            raise SchemaValidationError("No content in NewProvider response")

        return content

    except KeyError as e:
        raise SchemaValidationError(
            f"Unexpected NewProvider response format: missing key {e}"
        )
```

---

### Step 4: Implement `_extract_token_counts()`

Extract token usage from the response.

```python
def _extract_token_counts(self, response_data: dict[str, Any]) -> tuple[int, int]:
    """Extract token counts from NewProvider response.

    Args:
        response_data: Raw API response

    Returns:
        Tuple of (input_tokens, output_tokens)
    """
    # Adapt to your provider's usage format
    usage = response_data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)  # or your provider's key
    output_tokens = usage.get("completion_tokens", 0)  # or your provider's key

    return (input_tokens, output_tokens)
```

---

### Step 5: Implement `_calculate_cost()`

Calculate cost based on provider's pricing.

```python
def _calculate_cost(
    self,
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """Calculate cost for NewProvider API call.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD

    Note:
        NewProvider pricing (example):
        - Standard model: $1.00/1M input, $3.00/1M output
        - Pro model: $5.00/1M input, $15.00/1M output
    """
    # Define pricing per model
    if "pro" in model.lower():
        input_price = 5.0  # $/1M tokens
        output_price = 15.0
    else:
        input_price = 1.0
        output_price = 3.0

    # Calculate cost
    input_cost = (input_tokens * input_price) / 1_000_000
    output_cost = (output_tokens * output_price) / 1_000_000

    return input_cost + output_cost
```

---

### Step 6: Implement `_get_provider_name()`

Return provider name for logging.

```python
def _get_provider_name(self) -> str:
    """Get provider name for logging.

    Returns:
        Provider name
    """
    return "NewProvider"
```

---

### Step 7: Implement `_get_endpoint()`

Return the API endpoint URL.

```python
def _get_endpoint(self) -> str:
    """Get NewProvider API endpoint URL.

    Returns:
        Full endpoint URL
    """
    return f"{self.base_url}/completions"
```

---

### Step 8: Update CostTracker Pricing

Add pricing configuration to `src/ai/base_service.py` or `src/core/cost_tracker.py`:

```python
class CostTracker:
    PRICING = {
        # ... existing providers ...

        # NewProvider pricing
        "newprovider-standard": (1.0, 3.0),  # $/1M tokens (input, output)
        "newprovider-pro": (5.0, 15.0),
    }
```

---

## Complete Example: Cohere

Here's a complete implementation for Cohere API:

```python
"""Cohere Service for OrderPilot-AI Trading Application.

Implements Cohere API integration with structured outputs.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from src.config.loader import AIConfig
from .base_service import BaseAIService
from .openai_models import SchemaValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class CohereService(BaseAIService):
    """Cohere service implementation."""

    def __init__(
        self,
        config: AIConfig,
        api_key: str,
        telemetry_callback: callable | None = None
    ):
        super().__init__(config, api_key, telemetry_callback)

        # Cohere-specific settings
        self.base_url = "https://api.cohere.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.default_model = "command-r-plus"

    def _build_request_body(
        self,
        prompt: str,
        response_model: type[T],
        model: str,
        temperature: float,
    ) -> dict[str, Any]:
        """Build Cohere-specific request body."""
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        enhanced_prompt = f"""{prompt}

IMPORTANT: Respond with valid JSON matching this exact schema:

{schema_str}"""

        return {
            "model": model,
            "message": enhanced_prompt,
            "temperature": temperature,
            "max_tokens": 4096,
        }

    def _extract_text_content(self, response_data: dict[str, Any]) -> str:
        """Extract text from Cohere response."""
        text = response_data.get("text")
        if not text:
            raise SchemaValidationError("No text in Cohere response")
        return text

    def _extract_token_counts(self, response_data: dict[str, Any]) -> tuple[int, int]:
        """Extract token counts from Cohere response."""
        meta = response_data.get("meta", {})
        tokens = meta.get("tokens", {})

        input_tokens = tokens.get("input_tokens", 0)
        output_tokens = tokens.get("output_tokens", 0)

        return (input_tokens, output_tokens)

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate Cohere API cost.

        Cohere Command R+ pricing:
        - Input: $3.00/1M tokens
        - Output: $15.00/1M tokens
        """
        if "command-r-plus" in model.lower():
            return (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)

        # Command R (smaller model)
        return (input_tokens * 0.50 / 1_000_000) + (output_tokens * 1.50 / 1_000_000)

    def _get_provider_name(self) -> str:
        """Return provider name."""
        return "Cohere"

    def _get_endpoint(self) -> str:
        """Return Cohere API endpoint."""
        return f"{self.base_url}/chat"
```

---

## Testing Your Implementation

### Step 1: Create Provider-Specific Tests

Create `tests/ai/test_newprovider_service.py`:

```python
"""Integration tests for NewProviderService."""

import pytest
from unittest.mock import AsyncMock

from src.ai.newprovider_service import NewProviderService
from src.ai.openai_models import SchemaValidationError, OrderAnalysis
from src.config.loader import AIConfig


@pytest.fixture
def config():
    return AIConfig(cost_limit_monthly=100.0)


@pytest.fixture
def service(config):
    return NewProviderService(config, api_key="test-key")


def test_service_initialization(service):
    """Test service initializes correctly."""
    assert service.base_url == "https://api.newprovider.com/v1"
    assert service.default_model == "newprovider-default-model"
    assert "Authorization" in service.headers


def test_build_request_body(service):
    """Test request body building."""
    body = service._build_request_body(
        "test prompt",
        OrderAnalysis,
        "test-model",
        0.5
    )

    assert "model" in body
    assert body["model"] == "test-model"
    assert body["temperature"] == 0.5
    assert "messages" in body or "message" in body  # Depends on your format


def test_extract_text_content(service):
    """Test text extraction."""
    response_data = {
        # Your provider's response format
        "choices": [{"message": {"content": "test response"}}]
    }

    text = service._extract_text_content(response_data)
    assert text == "test response"


def test_extract_text_content_error(service):
    """Test error handling for missing content."""
    response_data = {"choices": []}

    with pytest.raises(SchemaValidationError):
        service._extract_text_content(response_data)


def test_extract_token_counts(service):
    """Test token count extraction."""
    response_data = {
        "usage": {"prompt_tokens": 100, "completion_tokens": 50}
    }

    input_tokens, output_tokens = service._extract_token_counts(response_data)
    assert input_tokens == 100
    assert output_tokens == 50


def test_calculate_cost(service):
    """Test cost calculation."""
    cost = service._calculate_cost("newprovider-standard", 1_000_000, 1_000_000)

    # $1.00 input + $3.00 output = $4.00
    assert cost == 4.0


def test_provider_name(service):
    """Test provider name."""
    assert service._get_provider_name() == "NewProvider"


@pytest.mark.asyncio
async def test_lifecycle(service):
    """Test service lifecycle."""
    await service.initialize()
    assert service._session is not None

    await service.close()
    assert service._session is None
```

---

### Step 2: Run Tests

```bash
# Run provider-specific tests
pytest tests/ai/test_newprovider_service.py -v

# Run integration tests (ensure new provider works with BaseAIService)
pytest tests/ai/test_ai_services_integration.py -v
```

---

### Step 3: Manual Testing

```python
import asyncio
from src.ai.newprovider_service import NewProviderService
from src.config.loader import AIConfig

async def test_manual():
    config = AIConfig(cost_limit_monthly=100.0)
    service = NewProviderService(config, api_key="your-real-key")

    async with service:
        # Test order analysis
        analysis = await service.analyze_order({
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 150.00
        })

        print(f"Approved: {analysis.approved}")
        print(f"Confidence: {analysis.confidence}")
        print(f"Reasoning: {analysis.reasoning}")

        # Check costs
        summary = service.get_cost_summary()
        print(f"Cost: ${summary['current_month_cost']:.2f}")

asyncio.run(test_manual())
```

---

## Common Pitfalls

### 1. Forgetting to Call `super().__init__()`

```python
# ❌ Wrong
def __init__(self, config, api_key):
    self.base_url = "..."  # CostTracker and CacheManager not initialized!

# ✅ Correct
def __init__(self, config, api_key):
    super().__init__(config, api_key)
    self.base_url = "..."
```

---

### 2. Incorrect Token Count Extraction

```python
# ❌ Wrong - using wrong keys
def _extract_token_counts(self, response_data):
    return (
        response_data["input"],  # Wrong key
        response_data["output"]  # Wrong key
    )

# ✅ Correct - matching provider's actual response format
def _extract_token_counts(self, response_data):
    usage = response_data.get("usage", {})
    return (
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0)
    )
```

---

### 3. Not Handling Provider-Specific Errors

```python
# ❌ Wrong - not checking for provider errors
def _extract_text_content(self, response_data):
    return response_data["choices"][0]["message"]["content"]

# ✅ Correct - checking for errors
def _extract_text_content(self, response_data):
    if "error" in response_data:
        raise SchemaValidationError(f"Provider error: {response_data['error']}")

    choices = response_data.get("choices", [])
    if not choices:
        raise SchemaValidationError("No choices in response")

    return choices[0]["message"]["content"]
```

---

### 4. Incorrect Cost Calculation

```python
# ❌ Wrong - using wrong units
def _calculate_cost(self, model, input_tokens, output_tokens):
    # Provider pricing is per 1M tokens, but calculating per token!
    return (input_tokens * 3.0) + (output_tokens * 15.0)

# ✅ Correct - dividing by 1M
def _calculate_cost(self, model, input_tokens, output_tokens):
    return (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)
```

---

### 5. Not Setting Default Model

```python
# ❌ Wrong - no default model
def __init__(self, config, api_key):
    super().__init__(config, api_key)
    self.base_url = "https://api.provider.com"
    # self.default_model not set!

# ✅ Correct
def __init__(self, config, api_key):
    super().__init__(config, api_key)
    self.base_url = "https://api.provider.com"
    self.default_model = "provider-default-model"  # Set default!
```

---

## Checklist

Before submitting your new provider implementation:

- [ ] All 6 abstract methods implemented
- [ ] Provider-specific tests written (>80% coverage)
- [ ] Integration tests pass
- [ ] Manual testing completed with real API key
- [ ] Pricing added to `CostTracker.PRICING`
- [ ] Documentation updated (provider added to README.md, API.md)
- [ ] Error handling tested (rate limits, API errors, invalid responses)
- [ ] Default model set correctly
- [ ] Headers configured correctly (Authorization, Content-Type, etc.)

---

## Summary

**Adding a new provider requires:**
1. Create `src/ai/newprovider_service.py` (~150 LOC)
2. Implement 6 abstract methods
3. Add pricing to CostTracker
4. Write tests (~100 LOC)
5. Update documentation

**Total Time:** 2-4 hours

**Result:** Fully integrated provider with automatic cost tracking, caching, error handling, and type-safe structured outputs!

---

**Last Updated:** 2026-01-31
**Document Version:** 1.0
