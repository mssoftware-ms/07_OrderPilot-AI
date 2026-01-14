"""Test suite for Heatmap feature.

This package contains comprehensive unit and integration tests for the Binance
BTCUSDT Liquidation Heatmap feature.

Test Modules:
    conftest: Shared fixtures and test data generators
    test_ws_parse: WebSocket parsing and connection handling tests
    test_sqlite_store: Database schema and operation tests
    test_grid_builder: Grid building and normalization tests
    test_integration: End-to-end integration tests

Running Tests:
    # Run all tests
    pytest Heatmap/tests/

    # Run specific test file
    pytest Heatmap/tests/test_ws_parse.py

    # Run with coverage
    pytest Heatmap/tests/ --cov=Heatmap

    # Run specific test class
    pytest Heatmap/tests/test_grid_builder.py::TestPriceToRowMapping

    # Run with verbose output
    pytest Heatmap/tests/ -v

Test Coverage:
    - WebSocket: Connection lifecycle, payload parsing, reconnect logic
    - Database: Schema, inserts, queries, retention, WAL mode
    - Grid Building: Price/time mapping, normalization, resolution
    - Integration: End-to-end flows, toggles, window switching

Fixtures:
    See conftest.py for all available fixtures, including:
    - Binance payload generators
    - Event model fixtures
    - Database fixtures
    - Window and settings parameters
"""

__all__ = [
    "conftest",
    "test_ws_parse",
    "test_sqlite_store",
    "test_grid_builder",
    "test_integration",
]
