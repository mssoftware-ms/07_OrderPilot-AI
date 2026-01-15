"""Pytest configuration and shared fixtures.

Global fixtures for OrderPilot-AI test suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Return test data directory."""
    return project_root / "tests" / "data"
