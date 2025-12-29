"""Bot Test Types and Helpers.

Contains test result types and mock data generators for bot testing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .models import (
    FeatureVector,
    RegimeState,
    RegimeType,
    VolatilityLevel,
)


class TestResult(str, Enum):
    """Test result status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """Individual test case result."""
    name: str
    description: str
    result: TestResult
    duration_ms: float = 0.0
    error_message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuiteResult:
    """Result of a test suite run."""
    suite_name: str
    test_cases: list[TestCase] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.errors == 0

    def add_result(self, test_case: TestCase) -> None:
        """Add a test case result."""
        self.test_cases.append(test_case)
        self.total_duration_ms += test_case.duration_ms

        if test_case.result == TestResult.PASSED:
            self.passed += 1
        elif test_case.result == TestResult.FAILED:
            self.failed += 1
        elif test_case.result == TestResult.SKIPPED:
            self.skipped += 1
        else:
            self.errors += 1

    def summary(self) -> str:
        """Get summary string."""
        total = len(self.test_cases)
        return (
            f"{self.suite_name}: {self.passed}/{total} passed, "
            f"{self.failed} failed, {self.errors} errors "
            f"({self.total_duration_ms:.0f}ms)"
        )


def generate_mock_features(
    symbol: str = "TEST",
    close: float = 100.0,
    trend: str = "up",
    volatility: str = "normal"
) -> FeatureVector:
    """Generate mock feature vector for testing.

    Args:
        symbol: Symbol name
        close: Close price
        trend: "up", "down", or "range"
        volatility: "low", "normal", "high"

    Returns:
        FeatureVector with realistic values
    """
    # Base values
    rng = random.Random(42)

    # Price-based features
    open_price = close * (1 + rng.uniform(-0.01, 0.01))
    high = max(open_price, close) * (1 + rng.uniform(0.001, 0.02))
    low = min(open_price, close) * (1 - rng.uniform(0.001, 0.02))

    # Trend-dependent indicators
    if trend == "up":
        sma_20 = close * 0.98
        sma_50 = close * 0.95
        rsi = rng.uniform(55, 70)
        adx = rng.uniform(25, 40)
        macd_hist = rng.uniform(0.1, 0.5)
    elif trend == "down":
        sma_20 = close * 1.02
        sma_50 = close * 1.05
        rsi = rng.uniform(30, 45)
        adx = rng.uniform(25, 40)
        macd_hist = rng.uniform(-0.5, -0.1)
    else:  # range
        sma_20 = close * rng.uniform(0.99, 1.01)
        sma_50 = close * rng.uniform(0.99, 1.01)
        rsi = rng.uniform(45, 55)
        adx = rng.uniform(15, 25)
        macd_hist = rng.uniform(-0.1, 0.1)

    # Volatility-dependent
    if volatility == "low":
        atr = close * 0.005
        bb_width = 0.02
    elif volatility == "high":
        atr = close * 0.03
        bb_width = 0.08
    else:  # normal
        atr = close * 0.015
        bb_width = 0.04

    return FeatureVector(
        symbol=symbol,
        timestamp=datetime.utcnow(),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=rng.randint(10000, 100000),
        sma_20=sma_20,
        sma_50=sma_50,
        ema_12=close * (1 + rng.uniform(-0.01, 0.01)),
        ema_26=close * (1 + rng.uniform(-0.02, 0.02)),
        rsi_14=rsi,
        macd_line=rng.uniform(-0.5, 0.5),
        macd_signal=rng.uniform(-0.5, 0.5),
        macd_histogram=macd_hist,
        bb_upper=close * (1 + bb_width / 2),
        bb_middle=close,
        bb_lower=close * (1 - bb_width / 2),
        atr_14=atr,
        adx_14=adx,
        plus_di=rng.uniform(15, 35),
        minus_di=rng.uniform(15, 35),
        stoch_k=rng.uniform(20, 80),
        stoch_d=rng.uniform(20, 80),
        cci_20=rng.uniform(-100, 100),
        mfi_14=rng.uniform(30, 70),
    )


def generate_mock_regime(
    regime_type: RegimeType = RegimeType.TREND_UP,
    volatility: VolatilityLevel = VolatilityLevel.NORMAL
) -> RegimeState:
    """Generate mock regime state.

    Args:
        regime_type: Type of regime
        volatility: Volatility level

    Returns:
        RegimeState
    """
    return RegimeState(
        regime=regime_type,
        volatility=volatility,
        regime_confidence=0.8,
        volatility_confidence=0.75
    )
