"""Shared fixtures and test configuration for Heatmap tests."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest


# ============================================================================
# BINANCE PAYLOAD FIXTURES
# ============================================================================


@pytest.fixture
def sample_binance_forceorder_payload() -> dict[str, Any]:
    """
    Sample Binance forceOrder WebSocket payload for BTCUSDT.

    Represents a liquidation event from Binance USD-M Futures stream.
    """
    return {
        "e": "forceOrder",
        "E": 1704067200000,  # milliseconds timestamp
        "o": {
            "s": "BTCUSDT",
            "S": "SELL",  # Side: BUY or SELL (liquidating position type)
            "o": "LIMIT",
            "f": "IOC",
            "q": 1.5,  # Quantity
            "p": 42500.50,  # Price
            "ap": 42500.50,  # Average price
            "X": "FILLED",
            "l": 1.5,
            "z": 1.5,
            "T": 1704067200000,
        },
    }


@pytest.fixture
def sample_binance_forceorder_buy() -> dict[str, Any]:
    """Buy-side liquidation event."""
    return {
        "e": "forceOrder",
        "E": 1704067300000,
        "o": {
            "s": "BTCUSDT",
            "S": "BUY",
            "o": "LIMIT",
            "f": "IOC",
            "q": 2.0,
            "p": 42600.00,
            "ap": 42600.00,
            "X": "FILLED",
            "l": 2.0,
            "z": 2.0,
            "T": 1704067300000,
        },
    }


@pytest.fixture
def malformed_payload_missing_fields() -> dict[str, Any]:
    """Malformed payload with missing required fields."""
    return {
        "e": "forceOrder",
        "E": 1704067200000,
        "o": {
            "s": "BTCUSDT",
            "S": "SELL",
            # Missing 'q', 'p', 'ap'
        },
    }


@pytest.fixture
def malformed_payload_invalid_json() -> str:
    """Invalid JSON string that cannot be parsed."""
    return '{"e": "forceOrder", "E": 1704067200000, "o": {"s": "BTCUSDT" INVALID'


@pytest.fixture
def malformed_payload_wrong_event() -> dict[str, Any]:
    """Valid JSON but wrong event type (not forceOrder)."""
    return {
        "e": "kline",
        "E": 1704067200000,
        "k": {
            "s": "BTCUSDT",
        },
    }


@pytest.fixture
def bulk_forceorder_payloads(
    sample_binance_forceorder_payload, sample_binance_forceorder_buy
) -> list[dict[str, Any]]:
    """Generate 100 realistic liquidation events with varying timestamps and prices."""
    base_time = 1704067200000
    base_price = 42500.0
    payloads = []

    for i in range(100):
        ts = base_time + (i * 500)  # 500ms apart
        price = base_price + (i * 0.5)  # Slight price drift
        qty = (i % 5) + 0.5  # Vary quantities

        payloads.append(
            {
                "e": "forceOrder",
                "E": ts,
                "o": {
                    "s": "BTCUSDT",
                    "S": "SELL" if i % 2 == 0 else "BUY",
                    "o": "LIMIT",
                    "f": "IOC",
                    "q": qty,
                    "p": price,
                    "ap": price,
                    "X": "FILLED",
                    "l": qty,
                    "z": qty,
                    "T": ts,
                },
            }
        )

    return payloads


# ============================================================================
# EVENT MODEL FIXTURES
# ============================================================================


@pytest.fixture
def sample_liq_event() -> dict[str, Any]:
    """Sample liquidation event as internal model."""
    return {
        "ts_ms": 1704067200000,
        "symbol": "BTCUSDT",
        "side": "SELL",
        "price": 42500.50,
        "qty": 1.5,
        "notional": 63750.75,
        "source": "BINANCE_USDM",
    }


@pytest.fixture
def bulk_liq_events(sample_liq_event) -> list[dict[str, Any]]:
    """Generate 50 realistic liquidation events."""
    events = []
    base_time = 1704067200000
    base_price = 42500.0

    for i in range(50):
        ts = base_time + (i * 1000)  # 1 second apart
        price = base_price + (i * 0.25)
        qty = (i % 8) + 0.1
        notional = price * qty

        events.append(
            {
                "ts_ms": ts,
                "symbol": "BTCUSDT",
                "side": "SELL" if i % 2 == 0 else "BUY",
                "price": price,
                "qty": qty,
                "notional": notional,
                "source": "BINANCE_USDM",
            }
        )

    return events


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Temporary SQLite database path for testing."""
    db_file = tmp_path / "test_heatmap.db"
    return db_file


@pytest.fixture
def exchange_info_response() -> dict[str, Any]:
    """Sample Binance exchangeInfo API response for BTCUSDT."""
    return {
        "timezone": "UTC",
        "serverTime": 1704067200000,
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "status": "TRADING",
                "filters": [
                    {
                        "filterType": "PRICE_FILTER",
                        "minPrice": "0.01",
                        "maxPrice": "1000000",
                        "tickSize": "0.01",
                    },
                    {
                        "filterType": "LOT_SIZE",
                        "minQty": "0.00001",
                        "maxQty": "10000",
                        "stepSize": "0.00001",
                    },
                ],
            }
        ],
    }


# ============================================================================
# GRID & AGGREGATION FIXTURES
# ============================================================================


@pytest.fixture
def sample_window_params() -> dict[str, Any]:
    """Sample window parameters for grid building."""
    return {
        "window_ms": 2 * 3600 * 1000,  # 2 hours
        "low": 41000.0,
        "high": 44000.0,
        "tick_size": 0.01,
        "rows_target": 200,
        "cols_target": 900,
    }


@pytest.fixture
def mock_datetime_now():
    """Mock current time for consistent testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def time_window_2h() -> tuple[int, int]:
    """Time window: 2 hours in milliseconds."""
    end_ms = 1704067200000
    start_ms = end_ms - (2 * 3600 * 1000)
    return (start_ms, end_ms)


@pytest.fixture
def time_window_8h() -> tuple[int, int]:
    """Time window: 8 hours in milliseconds."""
    end_ms = 1704067200000
    start_ms = end_ms - (8 * 3600 * 1000)
    return (start_ms, end_ms)


@pytest.fixture
def time_window_2d() -> tuple[int, int]:
    """Time window: 2 days in milliseconds."""
    end_ms = 1704067200000
    start_ms = end_ms - (2 * 24 * 3600 * 1000)
    return (start_ms, end_ms)


# ============================================================================
# GRID OUTPUT FIXTURES
# ============================================================================


@pytest.fixture
def expected_grid_structure() -> dict[str, Any]:
    """Expected structure of a heatmap grid output."""
    return {
        "rows": 200,
        "cols": 900,
        "cells": [],  # Will contain normalized intensities
        "bounds": {
            "price_min": 41000.0,
            "price_max": 44000.0,
            "price_step": 15.0,
            "time_min_ms": 0,
            "time_max_ms": 7200000,
            "time_step_ms": 8000,
        },
        "metadata": {
            "normalization": "sqrt",
            "total_events": 0,
            "total_notional": 0.0,
        },
    }


# ============================================================================
# NORMALIZATION FIXTURES
# ============================================================================


@pytest.fixture
def raw_intensities() -> list[list[float]]:
    """Sample raw intensity matrix before normalization."""
    return [
        [0.0, 1.0, 5.0, 2.0],
        [1.0, 10.0, 3.0, 0.5],
        [0.0, 2.0, 8.0, 1.5],
        [3.0, 5.0, 2.0, 4.0],
    ]


@pytest.fixture
def normalized_linear() -> list[list[float]]:
    """Expected result of linear normalization (0-1 range)."""
    return [
        [0.0, 0.1, 0.5, 0.2],
        [0.1, 1.0, 0.3, 0.05],
        [0.0, 0.2, 0.8, 0.15],
        [0.3, 0.5, 0.2, 0.4],
    ]


@pytest.fixture
def settings_2h() -> dict[str, Any]:
    """Settings for 2h window."""
    return {
        "enabled": True,
        "window": "2h",
        "opacity": 0.7,
        "palette": "hot",
        "normalization": "sqrt",
        "decay": None,
        "resolution": "auto",
    }


@pytest.fixture
def settings_8h() -> dict[str, Any]:
    """Settings for 8h window."""
    return {
        "enabled": True,
        "window": "8h",
        "opacity": 0.6,
        "palette": "viridis",
        "normalization": "log",
        "decay": "20m",
        "resolution": "auto",
    }


@pytest.fixture
def settings_2d() -> dict[str, Any]:
    """Settings for 2d window."""
    return {
        "enabled": True,
        "window": "2d",
        "opacity": 0.5,
        "palette": "plasma",
        "normalization": "linear",
        "decay": "60m",
        "resolution": "auto",
    }
