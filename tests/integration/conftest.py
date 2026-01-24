"""Integration test configuration and shared fixtures.

Provides:
- Session-level fixtures for E2E tests
- Test data generation
- Output directory management
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_fixtures():
    """Setup test fixtures before any integration tests run."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    regime_dir = fixtures_dir / "regime_optimization"
    indicator_dir = fixtures_dir / "indicator_optimization"

    # Create fixture data if not present
    if not (regime_dir / "regime_optimization_results_BTCUSDT_5m.json").exists():
        try:
            from tests.fixtures.generate_test_data import create_test_fixtures

            create_test_fixtures()
        except Exception as e:
            pytest.skip(f"Could not generate fixtures: {e}")


@pytest.fixture(scope="session")
def fixtures_root() -> Path:
    """Root fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="session")
def integration_tests_root() -> Path:
    """Root integration tests directory."""
    return Path(__file__).parent


@pytest.fixture
def tmp_integration_output(tmp_path: Path) -> Path:
    """Temporary output directory for integration test results."""
    output_dir = tmp_path / "integration_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# ============================================================================
# Markers
# ============================================================================


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "ui: mark test as UI integration test (requires PyQt6)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (takes >10s)"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )
    config.addinivalue_line(
        "markers", "stage1: mark test as Stage 1 regime optimization"
    )
    config.addinivalue_line(
        "markers", "stage2: mark test as Stage 2 indicator optimization"
    )
