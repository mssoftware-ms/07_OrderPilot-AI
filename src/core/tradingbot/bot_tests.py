"""Bot Tests and Validation.

Provides:
- Unit tests for bot components
- Integration tests
- Chaos/failure tests
- Regression tests

REFACTORED: Split into multiple files to meet 600 LOC limit.
- bot_test_types.py: TestResult, TestCase, TestSuiteResult, mock generators
- bot_test_suites.py: BotUnitTests, BotIntegrationTests, ChaosTests
- bot_tests.py: run_all_tests() and re-exports (this file)
"""

from __future__ import annotations

import logging

# Re-export types for backward compatibility
from .bot_test_types import (
    TestCase,
    TestResult,
    TestSuiteResult,
    generate_mock_features,
    generate_mock_regime,
)

# Re-export test suites
from .bot_test_suites import (
    BotIntegrationTests,
    BotUnitTests,
    ChaosTests,
)

__all__ = [
    "TestResult",
    "TestCase",
    "TestSuiteResult",
    "generate_mock_features",
    "generate_mock_regime",
    "BotUnitTests",
    "BotIntegrationTests",
    "ChaosTests",
    "run_all_tests",
]

logger = logging.getLogger(__name__)


def run_all_tests() -> dict[str, TestSuiteResult]:
    """Run all test suites.

    Returns:
        Dict of suite name to results
    """
    results = {}

    # Unit tests
    unit_tests = BotUnitTests()
    results["unit"] = unit_tests.run_all()
    logger.info(results["unit"].summary())

    # Integration tests
    integration_tests = BotIntegrationTests()
    results["integration"] = integration_tests.run_all()
    logger.info(results["integration"].summary())

    # Chaos tests
    chaos_tests = ChaosTests()
    results["chaos"] = chaos_tests.run_all()
    logger.info(results["chaos"].summary())

    # Summary
    total_passed = sum(r.passed for r in results.values())
    total_failed = sum(r.failed for r in results.values())
    total_errors = sum(r.errors for r in results.values())

    logger.info(
        f"All tests: {total_passed} passed, {total_failed} failed, "
        f"{total_errors} errors"
    )

    return results
