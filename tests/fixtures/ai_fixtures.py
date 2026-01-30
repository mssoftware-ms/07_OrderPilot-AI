"""
Shared Fixtures für AI Service Tests

Provides:
- Mocked API clients (Anthropic, Gemini, OpenAI)
- Sample responses
- Test data (OHLCV, market data)
- Validation helpers
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, patch


# ============================================================================
# MOCK API CLIENTS
# ============================================================================

@pytest.fixture
def mock_anthropic_client():
    """
    Provides mocked Anthropic client

    Returns:
        MagicMock: Mocked anthropic.Anthropic instance
    """
    with patch('anthropic.Anthropic') as mock:
        # Mock successful response
        mock_response = Mock()
        mock_response.content = [
            Mock(text='{"analysis": "bullish", "confidence": 0.85}')
        ]
        mock_response.id = "msg_test123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.role = "assistant"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock.return_value.messages.create.return_value = mock_response
        yield mock


@pytest.fixture
def mock_gemini_client():
    """
    Provides mocked Gemini client

    Returns:
        MagicMock: Mocked google.generativeai.GenerativeModel instance
    """
    with patch('google.generativeai.GenerativeModel') as mock:
        # Mock successful response
        mock_response = Mock()
        mock_response.text = '{"analysis": "bearish", "confidence": 0.75}'
        mock_response.prompt_feedback = Mock(block_reason=None)

        mock.return_value.generate_content.return_value = mock_response
        yield mock


@pytest.fixture
def mock_openai_client():
    """
    Provides mocked OpenAI client

    Returns:
        MagicMock: Mocked openai.OpenAI instance
    """
    with patch('openai.OpenAI') as mock:
        # Mock successful response
        mock_message = Mock()
        mock_message.content = '{"analysis": "neutral", "confidence": 0.60}'
        mock_message.role = "assistant"

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.id = "chatcmpl-test123"
        mock_response.model = "gpt-4"
        mock_response.usage = Mock(
            prompt_tokens=80,
            completion_tokens=40,
            total_tokens=120
        )

        mock.return_value.chat.completions.create.return_value = mock_response
        yield mock


# ============================================================================
# SAMPLE RESPONSES
# ============================================================================

@pytest.fixture
def sample_ai_responses() -> Dict[str, Dict[str, Any]]:
    """
    Provides sample AI responses for all providers

    Returns:
        Dict: Responses for Anthropic, Gemini, OpenAI
    """
    return {
        "anthropic": {
            "success": {
                "content": [{"text": '{"analysis": "bullish", "confidence": 0.9}'}],
                "id": "msg_test",
                "model": "claude-3-opus-20240229",
                "role": "assistant"
            },
            "rate_limit": {
                "error": {"type": "rate_limit_error", "message": "Rate limit exceeded"},
                "status_code": 429
            },
            "invalid_key": {
                "error": {"type": "authentication_error", "message": "Invalid API key"},
                "status_code": 401
            }
        },
        "gemini": {
            "success": {
                "text": '{"analysis": "bearish", "confidence": 0.8}',
                "prompt_feedback": {"block_reason": None}
            },
            "safety_block": {
                "text": None,
                "prompt_feedback": {"block_reason": "SAFETY"}
            }
        },
        "openai": {
            "success": {
                "choices": [
                    {
                        "message": {
                            "content": '{"analysis": "neutral", "confidence": 0.7}',
                            "role": "assistant"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "id": "chatcmpl_test",
                "model": "gpt-4"
            },
            "context_length": {
                "error": {
                    "code": "context_length_exceeded",
                    "message": "Maximum context length exceeded"
                }
            }
        }
    }


@pytest.fixture
def sample_analysis_results() -> List[Dict[str, Any]]:
    """
    Provides sample analysis results for testing

    Returns:
        List[Dict]: Various analysis scenarios
    """
    return [
        {
            "scenario": "strong_bullish",
            "analysis": "bullish",
            "confidence": 0.95,
            "indicators": {
                "rsi": 35,
                "macd": "positive_crossover",
                "volume": "increasing"
            },
            "recommendation": "buy"
        },
        {
            "scenario": "weak_bearish",
            "analysis": "bearish",
            "confidence": 0.55,
            "indicators": {
                "rsi": 65,
                "macd": "negative_divergence",
                "volume": "decreasing"
            },
            "recommendation": "hold"
        },
        {
            "scenario": "neutral_consolidation",
            "analysis": "neutral",
            "confidence": 0.60,
            "indicators": {
                "rsi": 50,
                "macd": "flat",
                "volume": "stable"
            },
            "recommendation": "wait"
        }
    ]


# ============================================================================
# TEST DATA (OHLCV)
# ============================================================================

@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """
    Provides sample OHLCV data for chart testing

    Returns:
        pd.DataFrame: 100 bars of realistic price data
    """
    np.random.seed(42)  # Reproducible results

    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')

    # Generate realistic price movement
    returns = np.random.randn(100) * 0.02  # 2% volatility
    price = 100 * np.exp(returns.cumsum())

    # OHLC from close prices
    open_prices = price
    high_prices = price * (1 + np.abs(np.random.randn(100)) * 0.01)
    low_prices = price * (1 - np.abs(np.random.randn(100)) * 0.01)
    close_prices = np.roll(price, -1)
    close_prices[-1] = price[-1]  # Fix last value

    volume = np.random.randint(10000, 100000, 100)

    return pd.DataFrame({
        'timestamp': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volume
    })


@pytest.fixture
def sample_market_data() -> Dict[str, pd.DataFrame]:
    """
    Provides sample market data for multiple symbols

    Returns:
        Dict[str, pd.DataFrame]: OHLCV data for AAPL, MSFT, TSLA
    """
    symbols = ['AAPL', 'MSFT', 'TSLA']
    data = {}

    for i, symbol in enumerate(symbols):
        np.random.seed(42 + i)  # Different seed per symbol

        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        returns = np.random.randn(100) * 0.02
        price = (100 + i * 50) * np.exp(returns.cumsum())  # Different base price

        data[symbol] = pd.DataFrame({
            'timestamp': dates,
            'open': price,
            'high': price * 1.01,
            'low': price * 0.99,
            'close': np.roll(price, -1),
            'volume': np.random.randint(50000, 200000, 100)
        })

    return data


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

@pytest.fixture
def json_schema_validator():
    """
    Provides JSON schema validator

    Returns:
        Callable: Validator function
    """
    from jsonschema import validate, ValidationError

    def validator(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validates data against JSON schema

        Args:
            data: Data to validate
            schema: JSON schema

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            raise ValidationError(f"Schema validation failed: {e.message}")

    return validator


@pytest.fixture
def response_validator():
    """
    Provides AI response validator

    Returns:
        Callable: Validator function for AI responses
    """
    def validator(response: Dict[str, Any], required_fields: List[str] = None) -> bool:
        """
        Validates AI response structure

        Args:
            response: AI response to validate
            required_fields: List of required field names

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails
        """
        if required_fields is None:
            required_fields = ["analysis", "confidence"]

        missing = [field for field in required_fields if field not in response]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Validate confidence range
        if "confidence" in response:
            conf = response["confidence"]
            if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
                raise ValueError(f"Invalid confidence value: {conf}")

        return True

    return validator


# ============================================================================
# HTTP MOCK HELPERS
# ============================================================================

@pytest.fixture
def mock_http_response():
    """
    Provides factory for creating mock HTTP responses

    Returns:
        Callable: Factory function for Mock responses
    """
    def factory(status_code: int, json_body: Dict[str, Any] = None,
                headers: Dict[str, str] = None) -> Mock:
        """
        Creates mock HTTP response

        Args:
            status_code: HTTP status code
            json_body: Response JSON body
            headers: Response headers

        Returns:
            Mock: Mocked response object
        """
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_body or {}
        mock_response.headers = headers or {}
        mock_response.text = str(json_body) if json_body else ""
        mock_response.ok = 200 <= status_code < 300

        return mock_response

    return factory


# ============================================================================
# ASYNC HELPERS
# ============================================================================

@pytest.fixture
def async_test_helper():
    """
    Provides helper for async tests

    Returns:
        Object with async utilities
    """
    import asyncio
    from typing import Callable, Any

    class AsyncHelper:
        @staticmethod
        async def wait_for_condition(
            condition: Callable[[], bool],
            timeout: float = 5.0,
            interval: float = 0.1
        ) -> bool:
            """
            Waits for condition to become True

            Args:
                condition: Callable that returns bool
                timeout: Maximum wait time in seconds
                interval: Check interval in seconds

            Returns:
                bool: True if condition met, False if timeout

            Raises:
                TimeoutError: If condition not met within timeout
            """
            end_time = asyncio.get_event_loop().time() + timeout

            while asyncio.get_event_loop().time() < end_time:
                if condition():
                    return True
                await asyncio.sleep(interval)

            raise TimeoutError(f"Condition not met within {timeout}s")

        @staticmethod
        def create_mock_coroutine(return_value: Any):
            """Creates mock coroutine for testing"""
            async def mock_coro():
                return return_value
            return mock_coro()

    return AsyncHelper()


# ============================================================================
# PERFORMANCE TEST HELPERS
# ============================================================================

@pytest.fixture
def performance_monitor():
    """
    Provides performance monitoring utilities

    Returns:
        Object with timing and memory utilities
    """
    import time
    import tracemalloc
    from typing import Callable, Any

    class PerformanceMonitor:
        @staticmethod
        def measure_time(func: Callable, *args, **kwargs) -> tuple[Any, float]:
            """
            Measures function execution time

            Args:
                func: Function to measure
                *args: Function arguments
                **kwargs: Function keyword arguments

            Returns:
                tuple: (result, elapsed_time_ms)
            """
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            return result, elapsed

        @staticmethod
        def measure_memory(func: Callable, *args, **kwargs) -> tuple[Any, int]:
            """
            Measures function memory usage

            Args:
                func: Function to measure
                *args: Function arguments
                **kwargs: Function keyword arguments

            Returns:
                tuple: (result, memory_used_bytes)
            """
            tracemalloc.start()
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return result, peak

    return PerformanceMonitor()


# ============================================================================
# CLEANUP HELPERS
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Auto-cleanup after each test

    Yields to test, then cleans up resources
    """
    # Setup (before test)
    yield

    # Teardown (after test)
    # Add cleanup logic here if needed
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    Provides test configuration

    Returns:
        Dict: Test configuration settings
    """
    return {
        "api_timeout": 30,
        "max_retries": 3,
        "retry_delay": 1,
        "test_api_key": "test-key-12345",
        "test_model": "test-model-v1",
        "coverage_threshold": 80,
        "performance_threshold_ms": 1000,
    }
